"""질문 3: 역사 유형 군집 분석과 우선 관리 순위 → CLUSTER_RUN, CLUSTER_TYPE, CLUSTER_RESULT 저장 (삽입 SQL).

입력: v_complex_features (역사 단위 지표, 03_sql/04_views.sql)
지표: 노인 이용 규모(평일 하루 평균, 로그), 노인 비중(%), 수직 이동 거리(|정거장 깊이| m),
      최대 환승 소요시간(초, 환승 없으면 0), 승강기 1대당 비가동 시간(수집 기간, 로그)
방법: 표준화 → K-means. k = 2~6을 모두 평가하고, 유형 분석 목적상 k >= 3 중 실루엣 최대를 고른다
      (k = 2는 '두 덩어리로 갈리는가'를 보는 기준선으로만 기록) → 군집 중심으로 이름 붙이기
타당성 점검: 시드 반복·부분표본(80%) 재군집의 ARI, 계층 군집(Ward)과의 ARI·실루엣, 입력 지표 상관(|r| > 0.8 표시)
우선 관리 점수: 노인 규모·수직 이동·비가동의 백분위 순위 가중합(0.4 / 0.3 / 0.3). 가중치를 바꿔 본 민감도는
      상위 20위 겹침(Jaccard)으로 따로 저장한다(점수 자체는 바꾸지 않음).

사용: python 05_코드/analysis.py
결과: 04_결과/csv/군집/cluster_k_selection.csv, cluster_summary.csv, priority_ranking.csv,
      cluster_diagnostics.csv(k별 타당성), cluster_feature_corr.csv(입력 지표 상관), priority_sensitivity.csv(가중치 민감도)
"""

from __future__ import annotations

from datetime import datetime
from itertools import product
from pathlib import Path

import db
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import adjusted_rand_score, calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

OUT = Path(__file__).resolve().parents[1] / "04_결과"


def csv_path(name: str) -> Path:
    """결과 CSV 위치: 04_결과/csv/우선순위/(priority_*) 또는 04_결과/csv/군집/(cluster_*)."""
    return OUT / "csv" / ("우선순위" if name.startswith("priority_") else "군집") / name
K_RANGE = range(2, 7)  # 평가하는 k
K_MIN_CHOICE = 3  # 고르는 k의 하한. k = 2는 환승역/비환승역 구분 수준이라 유형 분석에는 거칠다(평가·기록만 한다)
SEED = 42
MIN_DAYS = 100  # 승하차 자료가 이보다 적은 역사(관리 구간 밖 등)는 제외
STABILITY_SEEDS = range(10)  # 시드 안정성: 같은 설정으로 시드만 바꿔 다시 군집
N_SUBSAMPLE = 30  # 부분표본 안정성: 반복 횟수
SUBSAMPLE_FRAC = 0.8  # 부분표본 비율(비복원 추출)
HIGH_CORR = 0.8  # 입력 지표 간 |r|이 이보다 크면 중복 지표로 표시
WEAK_SILHOUETTE = 0.5  # 실루엣이 이보다 낮으면 '약한 구조'로 기록(Kaufman & Rousseeuw: 0.26~0.50 약함)
TOP_N = 20  # 민감도 분석에서 비교하는 상위 순위 수
WEIGHT_GRID = (0.2, 0.3, 0.4, 0.5)  # 민감도 분석: 각 가중치 후보(합이 1이 되게 정규화)

FEATURES = {
    "log_senior": "노인 이용 규모",
    "senior_pct": "노인 비중",
    "vertical_m": "수직 이동 거리",
    "transfer_sec": "환승 소요시간",
    "log_outage": "승강기 비가동",
}
WEIGHTS = {"senior_weekday": 0.4, "vertical_m": 0.3, "outage_hours_per_elevator": 0.3}


def prepare(f: pd.DataFrame) -> pd.DataFrame:
    f = f[(f.min_days >= MIN_DAYS) & (f.n_elevator > 0)].copy()
    num = ["senior_weekday", "senior_pct", "vertical_m", "max_transfer_sec", "outage_hours_per_elevator"]
    f[num] = f[num].astype(float)
    f["vertical_m"] = f.vertical_m.fillna(f.vertical_m.median())
    f["transfer_sec"] = f.max_transfer_sec.fillna(0)
    f["outage_hours_per_elevator"] = f.outage_hours_per_elevator.fillna(0)
    f["log_senior"] = np.log1p(f.senior_weekday)
    f["log_outage"] = np.log1p(f.outage_hours_per_elevator)
    return f.reset_index(drop=True)


MIN_COLLECT_HOURS = 72  # 승강기 수집이 3일 미만이면 비가동 지표는 '지금 고장 중인지'만 반영하므로 쓰지 않는다


def collected_hours(period: dict) -> float:
    if not period.get("first_at") or not period.get("last_at"):
        return 0.0
    return (period["last_at"] - period["first_at"]).total_seconds() / 3600


def usable_features(f: pd.DataFrame, hours: float) -> list[str]:
    """분산이 0인 지표와, 수집 기간이 짧을 때의 비가동 지표는 군집 입력에서 뺀다."""
    cols = [c for c in FEATURES if f[c].std() > 1e-9]
    if hours < MIN_COLLECT_HOURS:
        cols = [c for c in cols if c != "log_outage"]
    return cols


def excluded_features(f: pd.DataFrame, hours: float) -> dict[str, str]:
    """usable_features가 뺀 지표와 그 이유. 비가동은 72시간 규칙과 분산 0 중 실제로 해당하는 이유를 모두 적는다."""
    out = {}
    for c in FEATURES:
        why = []
        if not f[c].std() > 1e-9:
            why.append("역사 간 값 차이 없음(분산 0)")
        if c == "log_outage" and hours < MIN_COLLECT_HOURS:
            why.append(f"수집 {hours:.1f}h < {MIN_COLLECT_HOURS}h")
        if why:
            out[c] = " · ".join(why)
    return out


# ───────────────────────── 군집 타당성
def kmeans_labels(x: np.ndarray, k: int, seed: int = SEED, n_init: int = 20) -> np.ndarray:
    return KMeans(n_clusters=k, n_init=n_init, random_state=seed).fit_predict(x)


def seed_stability(x: np.ndarray, labels: np.ndarray, k: int, seeds=STABILITY_SEEDS) -> np.ndarray:
    """시드만 바꿔 다시 군집했을 때 기준 해와의 ARI(1이면 같은 분할)."""
    return np.array([adjusted_rand_score(labels, kmeans_labels(x, k, seed=s)) for s in seeds])


def subsample_stability(x: np.ndarray, labels: np.ndarray, k: int, n_rep: int = N_SUBSAMPLE,
                        frac: float = SUBSAMPLE_FRAC, seed: int = SEED) -> np.ndarray:
    """역사의 frac만 뽑아(비복원) 다시 군집했을 때, 뽑힌 역사에서 기준 해와의 ARI."""
    rng = np.random.default_rng(seed)
    m = round(frac * len(x))
    out = []
    for i in range(n_rep):
        idx = rng.choice(len(x), m, replace=False)
        out.append(adjusted_rand_score(labels[idx], kmeans_labels(x[idx], k, seed=seed + i, n_init=10)))
    return np.array(out)


def ward_comparison(x: np.ndarray, labels: np.ndarray, k: int) -> dict:
    """같은 k의 계층 군집(Ward)과 비교: K-means 해와의 ARI, Ward 해의 실루엣."""
    ward = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(x)
    return {"ward_ari": adjusted_rand_score(labels, ward), "ward_silhouette": silhouette_score(x, ward)}


def diagnose(x: np.ndarray, k_range=K_RANGE) -> pd.DataFrame:
    """k마다 K-means(n_init=20, SEED)를 적합하고 실루엣·CH·DB 지수, 안정성, Ward 비교를 한 행으로 모은다."""
    rows = []
    for k in k_range:
        labels = kmeans_labels(x, k)
        seeds = seed_stability(x, labels, k)
        subs = subsample_stability(x, labels, k)
        rows.append({
            "k": k,
            "silhouette": silhouette_score(x, labels),
            "calinski_harabasz": calinski_harabasz_score(x, labels),
            "davies_bouldin": davies_bouldin_score(x, labels),
            "min_cluster_size": int(np.bincount(labels).min()),
            "seed_ari_mean": seeds.mean(),
            "seed_ari_min": seeds.min(),
            "subsample_ari_mean": subs.mean(),
            "subsample_ari_min": subs.min(),
            **ward_comparison(x, labels, k),
        })
    return pd.DataFrame(rows)


def choose_k(table: pd.DataFrame, k_min: int = K_MIN_CHOICE) -> int:
    """선정 규칙: k >= k_min 중 실루엣 최대. (k < k_min은 기록만 한다)"""
    eligible = table[table.k >= k_min]
    return int(eligible.loc[eligible.silhouette.idxmax(), "k"])


def feature_corr(f: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    return f[cols].astype(float).corr()


def high_corr_pairs(corr: pd.DataFrame, threshold: float = HIGH_CORR) -> list[tuple[str, str, float]]:
    cols = list(corr.columns)
    return [(a, b, float(corr.loc[a, b])) for i, a in enumerate(cols) for b in cols[i + 1:]
            if abs(corr.loc[a, b]) > threshold]


def name_clusters(centers_z: pd.DataFrame) -> dict[int, str]:
    """군집 중심(표준화 값)에서 두드러진 지표 두 개로 이름을 만든다. 예: '노인 비중 높음·수직 이동 거리 큼'"""
    words = {
        "log_senior": ("노인 이용 많음", "노인 이용 적음"),
        "senior_pct": ("노인 비중 높음", "노인 비중 낮음"),
        "vertical_m": ("깊은 역", "얕은 역"),
        "transfer_sec": ("환승 부담 큼", "환승 부담 작음"),
        "log_outage": ("비가동 잦음", "비가동 적음"),
    }
    names = {}
    for c, row in centers_z.iterrows():
        top = row.abs().sort_values(ascending=False)
        parts = [words[f][0] if row[f] > 0 else words[f][1] for f in top.index[:2] if abs(row[f]) >= 0.4]
        names[c] = "·".join(parts) if parts else "평균형"
    # 같은 이름이 생기면 번호를 붙여 구분
    seen: dict[str, int] = {}
    for c in sorted(names):
        n = names[c]
        seen[n] = seen.get(n, 0) + 1
        if seen[n] > 1:
            names[c] = f"{n} {seen[n]}"
    return names


# ───────────────────────── 우선 관리 점수
def effective_weights(use_outage: bool, weights: dict | None = None) -> dict[str, float]:
    """실제로 쓰는 가중치. 비가동을 쓰지 않을 때는 나머지 가중치를 합이 1이 되게 키운다."""
    weights = dict(WEIGHTS if weights is None else weights)
    if not use_outage:
        weights.pop("outage_hours_per_elevator", None)
    total = sum(weights.values())
    return {c: w / total for c, w in weights.items()}


def priority(f: pd.DataFrame, use_outage: bool, weights: dict | None = None) -> pd.Series:
    """백분위 순위 가중합(기본 가중치 WEIGHTS = 0.4 / 0.3 / 0.3)."""
    score = sum(w * f[c].rank(pct=True) for c, w in effective_weights(use_outage, weights).items())
    return score.round(3)


def priority_rank(f: pd.DataFrame) -> pd.Series:
    """저장할 순위(1부터). 동점은 평일 노인 이용이 많은 쪽, 그다음 complex_id가 작은 쪽을 앞에 두어
    입력 행 순서와 관계없이 같은 순위가 나온다."""
    order = f.sort_values(["priority_score", "senior_weekday", "complex_id"], ascending=[False, False, True]).index
    return pd.Series(range(1, len(f) + 1), index=order).reindex(f.index)


def top_set(score: pd.Series, n: int = TOP_N) -> set:
    """점수 상위 n개 행 인덱스(동점은 행 순서로. 입력은 complex_id 순이며, 저장 순위는 priority_rank의 보조 기준을 쓴다)."""
    rank = score.rank(ascending=False, method="first")
    return set(rank[rank <= n].index)


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a | b else 1.0


def sensitivity(f: pd.DataFrame, use_outage: bool, grid=WEIGHT_GRID, n: int = TOP_N) -> pd.DataFrame:
    """가중치 조합마다 상위 n위가 기준 가중치(WEIGHTS)와 얼마나 겹치는지. 같은 비율의 조합은 한 번만 남긴다."""
    base = priority(f, use_outage)
    base_top = top_set(base, n)
    base_eff = effective_weights(use_outage)
    keys = list(WEIGHTS)
    rows, seen = [], set()
    for combo in product(grid, repeat=len(keys)):
        eff = effective_weights(use_outage, dict(zip(keys, combo)))
        sig = tuple(round(eff.get(c, 0.0), 3) for c in keys)
        if sig in seen:
            continue
        seen.add(sig)
        s = priority(f, use_outage, dict(zip(keys, combo)))
        top = top_set(s, n)
        rows.append({
            "w_senior": sig[0], "w_vertical": sig[1], "w_outage": sig[2],
            "is_baseline": int(all(abs(eff.get(c, 0.0) - base_eff.get(c, 0.0)) < 1e-9 for c in keys)),
            f"top{n}_overlap": len(top & base_top),
            f"jaccard_top{n}": round(jaccard(top, base_top), 3),
            "spearman": round(float(s.corr(base, method="spearman")), 3),
            "outage_in_score": int(use_outage),
        })
    return pd.DataFrame(rows).sort_values(f"jaccard_top{n}", ascending=False).reset_index(drop=True)


def weights_label(use_outage: bool) -> str:
    names = {"senior_weekday": "노인", "vertical_m": "수직", "outage_hours_per_elevator": "비가동"}
    eff = effective_weights(use_outage)
    text = " ".join(f"{names[c]}{w:.2f}" for c, w in eff.items())
    return text if use_outage else text + " (비가동 제외 회차: 비가동 포함 회차와 순위 직접 비교 불가)"


# ───────────────────────── 저장·실행 (DB 접근은 여기서만)
OUTPUT_FILES = ("cluster_k_selection.csv", "cluster_diagnostics.csv", "cluster_feature_corr.csv",
                "priority_sensitivity.csv", "cluster_summary.csv", "priority_ranking.csv")


def check_writable(names=OUTPUT_FILES) -> None:
    """DB 저장 전에 결과 CSV를 쓸 수 있는지 확인한다. 엑셀 등으로 열려 잠긴 파일이 있으면 DB를 바꾸기 전에 멈춰,
    DB에는 새 회차가 있는데 CSV는 옛 회차로 남는 어긋남을 막는다."""
    for d in {csv_path(n).parent for n in names}:
        d.mkdir(parents=True, exist_ok=True)
    locked = []
    for n in names:
        try:
            with open(csv_path(n), "a"):
                pass
        except PermissionError:
            locked.append(n)
    if locked:
        raise SystemExit(f"결과 파일이 다른 프로그램에서 열려 있어 쓸 수 없습니다: {', '.join(locked)}. "
                         "닫은 뒤 다시 실행하세요(DB는 바꾸지 않았습니다).")


def save(f: pd.DataFrame, k: int, sil: float, used: list[str], data_until) -> int:
    conn = db.connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO cluster_run (run_at, k, silhouette, data_until) VALUES (%s, %s, %s, %s)",
                (datetime.now().replace(microsecond=0), k, round(sil, 4), data_until),
            )
            run_id = cur.lastrowid
            cur.executemany(
                "INSERT INTO run_feature (run_id, feature_nm) VALUES (%s, %s)",
                [(run_id, FEATURES[c]) for c in used],
            )
            types = f[["cluster_no", "cluster_nm"]].drop_duplicates().sort_values("cluster_no")
            cur.executemany(
                "INSERT INTO cluster_type (run_id, cluster_no, cluster_nm) VALUES (%s, %s, %s)",
                [(run_id, int(r.cluster_no), r.cluster_nm) for r in types.itertuples()],
            )
            cur.executemany(
                "INSERT INTO cluster_result (run_id, complex_id, cluster_no, priority_rank, priority_score) "
                "VALUES (%s, %s, %s, %s, %s)",
                [(run_id, int(r.complex_id), int(r.cluster_no), int(r.priority_rank), float(r.priority_score))
                 for r in f.itertuples()],
            )
        conn.commit()
        return run_id
    finally:
        conn.close()


def run() -> dict:
    f = prepare(db.features())
    period = db.collect_period()
    hours = collected_hours(period)
    used = usable_features(f, hours)
    dropped = excluded_features(f, hours)
    use_outage = "log_outage" in used
    x = StandardScaler().fit_transform(f[used])
    diag = diagnose(x)
    k = choose_k(diag)
    km = KMeans(n_clusters=k, n_init=20, random_state=SEED).fit(x)
    labels = km.labels_

    # 군집 번호를 노인 이용 규모 평균 순으로 1부터 다시 매긴다(실행마다 번호가 뒤섞이지 않게)
    order = pd.Series(f.log_senior.values).groupby(labels).mean().sort_values(ascending=False).index
    remap = {old: new for new, old in enumerate(order, start=1)}
    f["cluster_no"] = [remap[c] for c in labels]
    centers = pd.DataFrame(km.cluster_centers_, columns=used).rename(index=remap).sort_index()
    names = name_clusters(centers)
    f["cluster_nm"] = f.cluster_no.map(names)
    f["priority_score"] = priority(f, use_outage)
    f["priority_rank"] = priority_rank(f)

    # 입력 지표 상관: 분산이 있는 후보 지표 전부(군집에서 뺀 비가동도 참고로 포함)
    corr = feature_corr(f, [c for c in FEATURES if f[c].std() > 1e-9])
    pairs = high_corr_pairs(corr)
    sens = sensitivity(f, use_outage)

    sil = float(diag.loc[diag.k == k, "silhouette"].iloc[0])
    check_writable()  # CSV가 잠겨 있으면 DB 저장 전에 멈춘다
    run_id = save(f, k, sil, used, period["last_at"])
    print(f"승강기 수집 {hours:.1f}시간 → 비가동 지표 {'사용' if use_outage else '제외(' + dropped['log_outage'] + ')'}")
    try:
        write_outputs(f, diag, k, sil, use_outage, dropped, corr, pairs, sens, run_id)
    except PermissionError as e:  # 확인과 쓰기 사이에 파일이 열린 경우
        print(f"!! run_id={run_id}는 DB에 저장됐지만 {e.filename}을 쓰지 못했습니다. 파일을 닫고 analysis.py를 "
              "다시 실행하면 새 회차로 DB와 CSV가 함께 갱신됩니다(대시보드는 가장 최근 회차를 씁니다).")
        raise
    return {"run_id": run_id, "k": k, "n": len(f)}


def write_outputs(f, diag, k, sil, use_outage, dropped, corr, pairs, sens, run_id) -> None:
    """결과 CSV 6종(OUTPUT_FILES)을 쓰고 요약을 출력한다. 기존 컬럼은 그대로 두고 새 컬럼은 끝에 붙인다."""
    for d in {csv_path(n).parent for n in OUTPUT_FILES}:
        d.mkdir(parents=True, exist_ok=True)
    k_table = diag[["k", "silhouette"]].assign(eligible=(diag.k >= K_MIN_CHOICE).astype(int),
                                              chosen=(diag.k == k).astype(int))
    k_table.to_csv(csv_path("cluster_k_selection.csv"), index=False, encoding="utf-8-sig")

    best_any = int(diag.loc[diag.silhouette.idxmax(), "k"])
    chosen = diag[diag.k == k].iloc[0]
    notes = [f"k={k} 실루엣 {sil:.3f}" + (" (0.5 미만: 약한 군집 구조, 유형은 경향 요약으로만 해석)"
                                         if sil < WEAK_SILHOUETTE else "")]
    if best_any != k:
        notes.append(f"실루엣 최대는 k={best_any}({diag.silhouette.max():.3f})이나 규칙상 k>={K_MIN_CHOICE}에서 선정")
    notes.append(f"시드 ARI {chosen.seed_ari_mean:.2f} / 부분표본 ARI {chosen.subsample_ari_mean:.2f}"
                 f"(최소 {chosen.subsample_ari_min:.2f}) / Ward ARI {chosen.ward_ari:.2f}")
    notes.append("비가동 포함" if use_outage else f"비가동 제외({dropped['log_outage']})")
    others = [f"{FEATURES[c]}({why})" for c, why in dropped.items() if c != "log_outage"]
    if others:
        notes.append("입력 제외: " + ", ".join(others))
    if pairs:
        notes.append("상관 높은 지표: " + ", ".join(f"{a}~{b} r={r:.2f}" for a, b, r in pairs))
    run_note = " · ".join(notes)

    diag.assign(run_id=run_id, chosen=(diag.k == k).astype(int),
                outage_in_input=int(use_outage), n_complex=len(f)).round(4).to_csv(
        csv_path("cluster_diagnostics.csv"), index=False, encoding="utf-8-sig")
    corr.round(3).rename_axis("feature").to_csv(csv_path("cluster_feature_corr.csv"), encoding="utf-8-sig")
    sens.to_csv(csv_path("priority_sensitivity.csv"), index=False, encoding="utf-8-sig")

    summary = f.groupby(["cluster_no", "cluster_nm"]).agg(
        n_complex=("complex_id", "size"),
        senior_weekday=("senior_weekday", "mean"),
        senior_pct=("senior_pct", "mean"),
        vertical_m=("vertical_m", "mean"),
        transfer_sec=("transfer_sec", "mean"),
        outage_h_per_elev=("outage_hours_per_elevator", "mean"),
        priority_score=("priority_score", "mean"),
    ).round(2).reset_index()
    summary = summary.assign(run_id=run_id, outage_in_input=int(use_outage), run_note=run_note)
    summary.to_csv(csv_path("cluster_summary.csv"), index=False, encoding="utf-8-sig")

    # 정보용 컬럼(점수에는 반영하지 않음): 엘리베이터 1대뿐인 역사(단일 장애점), 노선 수(환승 부담)
    f["single_ev"] = (f.n_ev == 1).astype(int)
    ranking = f.sort_values("priority_rank")[
        ["priority_rank", "complex_nm", "cluster_nm", "priority_score", "senior_weekday", "senior_pct", "vertical_m",
         "transfer_sec", "n_elevator", "outage_hours_per_elevator", "n_ev", "single_ev", "n_lines"]
    ].assign(outage_in_score=int(use_outage), score_weights=weights_label(use_outage), run_id=run_id)
    ranking.to_csv(csv_path("priority_ranking.csv"), index=False, encoding="utf-8-sig")

    print(f"run_id={run_id}  역사 {len(f)}개  k={k}  실루엣={sil:.3f}  지표={[c for c in FEATURES if c not in dropped]}")
    print(diag.round(3).to_string(index=False))
    if best_any != k:
        print(f"!! 주의: 실루엣 최대는 k={best_any}({diag.silhouette.max():.3f}). 선정 규칙(k>={K_MIN_CHOICE})에 따라 k={k}")
    if sil < WEAK_SILHOUETTE:
        print(f"!! 한계: 실루엣 {sil:.3f} < {WEAK_SILHOUETTE} → 군집 구조가 약하다. 유형은 경향 요약으로만 쓴다")
    print(f"입력 지표 상관(|r| > {HIGH_CORR}): {pairs or '없음'}")
    print(corr.round(2).to_string())
    print(summary.drop(columns="run_note").to_string(index=False))
    print(f"민감도: 가중치 조합 {len(sens)}개, 상위 {TOP_N}위 Jaccard {sens[f'jaccard_top{TOP_N}'].min():.2f}"
          f"~{sens[f'jaccard_top{TOP_N}'].max():.2f}, 겹침 {sens[f'top{TOP_N}_overlap'].min()}"
          f"~{sens[f'top{TOP_N}_overlap'].max()}개")
    top = ranking.head(TOP_N)
    print(f"상위 {TOP_N}위 중 엘리베이터 1대 역사 {int(top.single_ev.sum())}곳, 환승역 {int((top.n_lines > 1).sum())}곳")
    print(ranking.head(10)[["priority_rank", "complex_nm", "cluster_nm", "priority_score", "single_ev"]]
          .to_string(index=False))
    if not use_outage:
        print("!! 이 회차의 우선 관리 점수는 비가동을 뺀 값이다(" + weights_label(use_outage) + ")")


if __name__ == "__main__":
    run()
