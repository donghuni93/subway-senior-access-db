"""analysis.py 단위 테스트: DB 없이 순수 DataFrame·배열로 검증한다."""

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "05_코드"))
import analysis as a


def raw(n=6, **over):
    """v_complex_features 모양의 작은 입력."""
    d = {
        "complex_id": list(range(1, n + 1)),
        "complex_nm": [f"역{i}" for i in range(1, n + 1)],
        "min_days": [365] * n,
        "n_elevator": [2] * n,
        "n_ev": [1] * n,
        "n_lines": [1] * n,
        "senior_weekday": [float(100 * (i + 1)) for i in range(n)],
        "senior_pct": [10.0 + i for i in range(n)],
        "vertical_m": [float(10 + i) for i in range(n)],
        "max_transfer_sec": [None] * n,
        "outage_hours_per_elevator": [None] * n,
    }
    d.update(over)
    return pd.DataFrame(d)


def blobs(k=3, per=30, seed=0):
    """서로 멀리 떨어진 k개 덩어리(정답 라벨 포함)."""
    rng = np.random.default_rng(seed)
    centers = np.array([[0, 0], [10, 0], [0, 10], [10, 10]])[:k]
    x = np.vstack([c + rng.normal(scale=0.3, size=(per, 2)) for c in centers])
    return x, np.repeat(np.arange(k), per)


# ───────────────────────── prepare
def test_prepare_filters_short_records_and_no_elevator():
    f = a.prepare(raw(min_days=[365, 50, 365, 365, 365, 365], n_elevator=[2, 2, 0, 2, 2, 2]))
    assert list(f.complex_id) == [1, 4, 5, 6]
    assert list(f.index) == [0, 1, 2, 3]


def test_prepare_fills_missing_and_adds_logs():
    f = a.prepare(raw(vertical_m=[10.0, None, 30.0, 40.0, None, 60.0],
                      max_transfer_sec=[None, 120, None, None, None, None],
                      outage_hours_per_elevator=[None, 2.0, None, None, None, None]))
    assert f.vertical_m.tolist() == [10.0, 35.0, 30.0, 40.0, 35.0, 60.0]  # 결측은 중앙값(35)
    assert f.transfer_sec.tolist() == [0, 120, 0, 0, 0, 0]
    assert f.outage_hours_per_elevator.tolist() == [0, 2.0, 0, 0, 0, 0]
    assert f.log_senior.iloc[0] == pytest.approx(np.log1p(100))
    assert f.log_outage.iloc[1] == pytest.approx(np.log1p(2.0))


# ───────────────────────── 72시간 규칙
def test_collected_hours():
    assert a.collected_hours({"first_at": datetime(2026, 11, 17, 0), "last_at": datetime(2026, 11, 18, 12)}) == 36
    assert a.collected_hours({"first_at": None, "last_at": None}) == 0.0


def test_usable_features_drops_outage_before_72_hours():
    f = a.prepare(raw(outage_hours_per_elevator=[0, 1, 0, 3, 0, 5]))
    assert "log_outage" not in a.usable_features(f, a.MIN_COLLECT_HOURS - 0.1)
    assert "log_outage" in a.usable_features(f, a.MIN_COLLECT_HOURS)


def test_usable_features_drops_zero_variance():
    f = a.prepare(raw())  # 환승·비가동이 모두 0
    assert a.usable_features(f, 1000) == ["log_senior", "senior_pct", "vertical_m"]


# ───────────────────────── 군집 이름
def test_name_clusters_top_two_and_average():
    centers = pd.DataFrame(
        {"log_senior": [1.2, 0.1, 0.1], "senior_pct": [0.0, 0.2, 0.0], "vertical_m": [-0.8, 0.0, 0.0],
         "transfer_sec": [0.1, -0.3, 0.0]}, index=[1, 2, 3])
    names = a.name_clusters(centers)
    assert names[1] == "노인 이용 많음·얕은 역"
    assert names[2] == "평균형"  # |z| >= 0.4인 지표가 없음
    assert names[3] == "평균형 2"  # 같은 이름은 번호로 구분


def test_name_clusters_skips_weak_second_feature():
    centers = pd.DataFrame({"log_senior": [-1.0], "vertical_m": [0.3]}, index=[1])
    assert a.name_clusters(centers) == {1: "노인 이용 적음"}


# ───────────────────────── 우선 관리 점수
def test_priority_baseline_weights_with_outage():
    f = pd.DataFrame({"senior_weekday": [1, 2, 3, 4], "vertical_m": [4, 3, 2, 1],
                      "outage_hours_per_elevator": [1, 2, 3, 4]})
    s = a.priority(f, use_outage=True)
    pct = np.array([0.25, 0.5, 0.75, 1.0])
    expected = 0.4 * pct + 0.3 * pct[::-1] + 0.3 * pct
    assert s.tolist() == pytest.approx(np.round(expected, 3).tolist())


def test_priority_without_outage_renormalizes_and_ignores_outage():
    f = pd.DataFrame({"senior_weekday": [1, 2, 3, 4], "vertical_m": [4, 3, 2, 1],
                      "outage_hours_per_elevator": [100, 0, 50, 7]})
    s = a.priority(f, use_outage=False)
    pct = np.array([0.25, 0.5, 0.75, 1.0])
    expected = (0.4 / 0.7) * pct + (0.3 / 0.7) * pct[::-1]
    assert s.tolist() == pytest.approx(np.round(expected, 3).tolist())
    assert a.priority(f.assign(outage_hours_per_elevator=0), use_outage=False).equals(s)


def test_priority_rank_is_independent_of_row_order():
    # 점수 동점(0.5)이 여럿: 평일 노인 이용 많은 쪽 → complex_id 작은 쪽 순
    f = pd.DataFrame({"complex_id": [10, 11, 12, 13, 14, 15],
                      "priority_score": [0.5, 0.9, 0.5, 0.5, 0.1, 0.5],
                      "senior_weekday": [100.0, 50.0, 300.0, 100.0, 10.0, 100.0]})
    base = dict(zip(f.complex_id, a.priority_rank(f)))
    assert base == {11: 1, 12: 2, 10: 3, 13: 4, 15: 5, 14: 6}
    for seed in range(5):
        g = f.sample(frac=1, random_state=seed).reset_index(drop=True)
        assert dict(zip(g.complex_id, a.priority_rank(g))) == base


def test_excluded_features_reports_reason():
    f = a.prepare(raw())  # 환승·비가동이 모두 0
    d = a.excluded_features(f, 10)
    assert set(d) == {"transfer_sec", "log_outage"}
    assert "분산 0" in d["transfer_sec"] and "72h" not in d["transfer_sec"]
    assert "분산 0" in d["log_outage"] and "72h" in d["log_outage"]
    g = a.prepare(raw(outage_hours_per_elevator=[0, 1, 0, 3, 0, 5]))
    assert a.excluded_features(g, 10)["log_outage"] == "수집 10.0h < 72h"  # 분산은 있음: 72시간 규칙만
    assert "log_outage" not in a.excluded_features(g, 100)
    used = a.usable_features(g, 10)
    assert set(used) | set(a.excluded_features(g, 10)) == set(a.FEATURES) and not set(used) & set(a.excluded_features(g, 10))


def test_effective_weights_sum_to_one():
    assert sum(a.effective_weights(True).values()) == pytest.approx(1)
    eff = a.effective_weights(False)
    assert set(eff) == {"senior_weekday", "vertical_m"} and sum(eff.values()) == pytest.approx(1)
    assert a.WEIGHTS == {"senior_weekday": 0.4, "vertical_m": 0.3, "outage_hours_per_elevator": 0.3}  # D5: 가중치 유지


def test_weights_label_marks_runs_without_outage():
    assert "비가동 제외" in a.weights_label(False)
    assert a.weights_label(True) == "노인0.40 수직0.30 비가동0.30"


# ───────────────────────── 민감도
def test_top_set_and_jaccard():
    s = pd.Series([0.9, 0.1, 0.8, 0.5])
    assert a.top_set(s, 2) == {0, 2}
    assert a.jaccard({1, 2}, {2, 3}) == pytest.approx(1 / 3)
    assert a.jaccard(set(), set()) == 1.0


def test_sensitivity_baseline_row_and_columns():
    rng = np.random.default_rng(1)
    f = pd.DataFrame({"senior_weekday": rng.random(60), "vertical_m": rng.random(60),
                      "outage_hours_per_elevator": rng.random(60)})
    t = a.sensitivity(f, use_outage=True, n=10)
    base = t[t.is_baseline == 1]
    assert len(base) == 1
    assert base.iloc[0][["top10_overlap", "jaccard_top10", "spearman"]].tolist() == [10, 1.0, 1.0]
    assert t.jaccard_top10.between(0, 1).all()
    assert (t.outage_in_score == 1).all()
    # 같은 비율의 가중치 조합은 한 번만
    assert not t.duplicated(["w_senior", "w_vertical", "w_outage"]).any()


def test_sensitivity_without_outage_has_zero_outage_weight():
    rng = np.random.default_rng(2)
    f = pd.DataFrame({"senior_weekday": rng.random(40), "vertical_m": rng.random(40),
                      "outage_hours_per_elevator": rng.random(40)})
    t = a.sensitivity(f, use_outage=False, n=10)
    assert (t.w_outage == 0).all() and (t.outage_in_score == 0).all()
    assert (t.w_senior + t.w_vertical).round(2).eq(1).all()
    assert t.is_baseline.sum() == 1


# ───────────────────────── 군집 타당성
def test_stability_helpers_on_clear_clusters():
    x, _ = blobs(3)
    labels = a.kmeans_labels(x, 3)
    assert a.seed_stability(x, labels, 3, seeds=range(3)).min() == pytest.approx(1.0)
    subs = a.subsample_stability(x, labels, 3, n_rep=5)
    assert len(subs) == 5 and subs.min() == pytest.approx(1.0)
    w = a.ward_comparison(x, labels, 3)
    assert w["ward_ari"] == pytest.approx(1.0) and w["ward_silhouette"] > 0.8


def test_diagnose_and_choose_k():
    x, _ = blobs(3)
    t = a.diagnose(x, k_range=range(2, 5))
    assert t.k.tolist() == [2, 3, 4]
    assert {"silhouette", "seed_ari_mean", "subsample_ari_mean", "ward_ari", "ward_silhouette"} <= set(t.columns)
    assert a.choose_k(t) == 3


def test_choose_k_respects_minimum():
    t = pd.DataFrame({"k": [2, 3, 4], "silhouette": [0.40, 0.30, 0.35]})
    assert a.choose_k(t) == 4  # k = 2가 최대여도 k >= 3에서 고른다
    assert a.choose_k(t, k_min=2) == 2


def test_feature_corr_flags_high_pairs():
    f = pd.DataFrame({"p": [1, 2, 3, 4, 5], "q": [2, 4, 6, 8, 11], "r": [5, 1, 4, 2, 3]})
    pairs = a.high_corr_pairs(a.feature_corr(f, ["p", "q", "r"]))
    assert [(p, q) for p, q, _ in pairs] == [("p", "q")]
    assert pairs[0][2] > 0.99
