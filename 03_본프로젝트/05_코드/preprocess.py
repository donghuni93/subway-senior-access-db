"""원본(API 응답) → 적재용 CSV 정제.

입력: 07_데이터/raw/api/*.json.gz (fetch_reference.py), 07_데이터/snapshots/*/*.json.gz (collect.py)
출력: 07_데이터/clean/{line,station,transfer,elevator,ridership,exit_closure,outage,snapshot_log}.csv
      07_데이터/clean/unmatched.csv  (역 매칭 실패 목록, 정제 기록용)

역 식별 규칙
- 기준 역 집합: 2025년 노인 승하차 자료의 역번호(서울교통공사 1~8호선)
- 승하차 자료의 역번호 = 역코드(STN_CD)를 정수로 쓴 값 (서울역 0150 → 150, 방화 2511 → 2511).
  승강기 API의 STN_CD와 같은 체계이므로 이것을 station_no로 쓴다.
  외부코드(FR_CODE, 서울역 133·용답 211-1)는 노선별 지하철역 정보(OA-15442)에서 가져와 별도 속성으로 둔다.
- 역명으로만 주어지는 자료(좌표, 건축정보, 환승, 출입구 폐쇄)는 (호선, 정규화한 역명)으로 찾는다
"""

from __future__ import annotations

import gzip
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_API = PROJECT_DIR / "07_데이터" / "raw" / "api"
SNAP = PROJECT_DIR / "07_데이터" / "snapshots"
CLEAN = PROJECT_DIR / "07_데이터" / "clean"

RAW_FILE = PROJECT_DIR / "07_데이터" / "raw" / "file"  # 공공데이터포털에서 내려받은 파일
RIDERSHIP_2025_FILE = RAW_FILE / "OA-12921_승하차_20251231.csv"  # data.go.kr 15048032
DEPTH_FILE = RAW_FILE / "OA-13305_역사심도.csv"  # data.go.kr 15071319

AVAILABLE = "사용가능"
KINDS = ("EV", "ES")  # 휠체어리프트(WL)·무빙워크(MW)는 범위 밖
YEAR = 2025

unmatched: list[dict] = []


def load_raw(name: str) -> list[dict]:
    with gzip.open(RAW_API / f"{name}.json.gz", "rt", encoding="utf-8") as f:
        return json.load(f)["rows"]


def load_snapshots(source: str) -> list[dict]:
    docs = []
    for p in sorted((SNAP / source).glob("*.json.gz")):
        with gzip.open(p, "rt", encoding="utf-8") as f:
            docs.append(json.load(f))
    return docs


def norm_name(name: str) -> str:
    """역명 정규화: 괄호·공백 제거, 끝의 '역' 제거. 예) '서울역(1)' → '서울', '동대문역사문화공원(DDP)' → '동대문역사문화공원'"""
    s = re.sub(r"\(.*?\)|\(.*$", "", str(name))
    s = re.sub(r"\s+", "", s)
    if s.endswith("역") and len(s) > 2:
        s = s[:-1]
    return s


# 역명이 바뀐 역: (호선, 옛 이름) → 현재 이름 (2025 승하차 자료 기준). 같은 이름이 다른 호선에서는 그대로여서 호선별로 둔다.
RENAMED = {
    # 역명 변경
    (4, "당고개"): "불암산",
    (7, "뚝섬유원지"): "자양",
    (7, "총신대입구"): "이수",
    (4, "미아삼거리"): "미아사거리",
    (5, "동대문운동장"): "동대문역사문화공원",
    # 역사심도정보(OA-13305) 파일의 줄임·오기 표기
    (2, "을지3가"): "을지로3가",
    (2, "을지4가"): "을지로4가",
    (2, "구로디지털"): "구로디지털단지",
    (5, "애오게"): "애오개",
    (5, "둔촌"): "둔촌동",
    (6, "DMC"): "디지털미디어시티",
    (7, "숭실대"): "숭실대입구",
    (7, "신대방"): "신대방삼거리",
    (7, "광명"): "광명사거리",
}
# 주의: 8호선 암사(2811)와 암사역사공원(2810)은 서로 다른 역이다(암사역사공원은 2024년 별내선 개통 역).


def station_key(line: int | None, name: str) -> tuple[int | None, str]:
    n = norm_name(name)
    return line, RENAMED.get((line, n), n)


# 역사 묶음에서 호선마다 이름이 다른 같은 역사: (호선, 정규화 이름) → 역사 이름
COMPLEX_ALIAS = {(4, "총신대입구"): "이수"}


def complex_key(line: int, name: str) -> str:
    """같은 역사를 쓰는 호선별 역은 정규화한 이름이 같다(서울역 1·4호선, 충무로 3·4호선 등)."""
    _, n = station_key(line, name)
    return COMPLEX_ALIAS.get((line, n), n)


def line_of(value) -> int | None:
    m = re.search(r"\d+", str(value))
    return int(m.group()) if m else None


def note(source: str, key: str, reason: str) -> None:
    unmatched.append({"source": source, "key": key, "reason": reason})


# ---------------------------------------------------------------- 역
def line_from_code(no: int) -> int:
    """역코드 앞자리로 호선을 정한다. 0150~0159 → 1, 02xx → 2, 03xx → 3, 04xx → 4, 25xx → 5 … 28xx → 8"""
    return no // 100 - 20 if no >= 2500 else max(no // 100, 1)


def build_station() -> tuple[pd.DataFrame, dict[tuple[int, str], int], dict[str, int]]:
    """역 집합 = 2025년 노인 승하차 자료의 역번호. 이 번호는 역코드(STN_CD, 예: 0150·2511)를 정수로 쓴 값이다."""
    names: dict[int, str] = {}
    for r in load_raw("ridership_senior"):
        names.setdefault(int(r["SUBW_NO"]), r["SUBW_NM"])

    line_info = {r["STATION_CD"]: r for r in load_raw("station_line")}

    rows = []
    for no, nm in sorted(names.items()):
        info = line_info.get(f"{no:04d}")
        ln = line_from_code(no)
        if info and line_of(info["LINE_NUM"]) != ln:
            note("station", str(no), f"역코드 규칙 호선 {ln} ≠ 역 정보 호선 {info['LINE_NUM']}")
        if not 1 <= ln <= 8:
            note("station", str(no), "1~8호선 범위 밖")
            continue
        rows.append({
            "station_no": no,
            "fr_code": info["FR_CODE"] if info else None,
            "line_no": ln,
            "station_nm": nm,
        })
        if info is None:
            note("station", f"{no} {nm}", "노선별 역 정보(OA-15442)에 없음 → 외부코드 비움")
    st = pd.DataFrame(rows)
    by_name = {(r.line_no, norm_name(r.station_nm)): r.station_no for r in st.itertuples()}

    # 좌표: (호선, 역명)으로 매칭
    lat, lng = {}, {}
    for r in load_raw("station_coord"):
        key = station_key(int(r["LINE_NUMBER"]), r["STATION_NAME"])
        if key in by_name:
            lat[by_name[key]], lng[by_name[key]] = r["LATITUDE"], r["LONGITUDE"]
        else:
            note("station_coord", f"{key[0]}호선 {r['STATION_NAME']}", "역명 매칭 실패")
    st["lat"] = st.station_no.map(lat)
    st["lng"] = st.station_no.map(lng)

    # 건축정보: (호선, 역명) → 형식·층수·준공연도
    build = {}
    for r in load_raw("station_building"):
        key = station_key(line_of(r["SBWY_ROUT_LN"]), r["SBWY_STNS_NM"])
        if key in by_name:
            build[by_name[key]] = r
        else:
            note("station_building", f"{key[0]}호선 {r['SBWY_STNS_NM']}", "역명 매칭 실패")
    st["platform_type"] = st.station_no.map(lambda n: build.get(n, {}).get("FRM"))
    st["floors"] = st.station_no.map(lambda n: build.get(n, {}).get("BLDG_FLR_CNT"))
    st["built_year"] = st.station_no.map(lambda n: build.get(n, {}).get("CMCN_YR"))

    # 정거장 깊이: 역사심도정보 파일(OA-13305, API는 0건이라 공공데이터포털 파일 사용)
    depth = {}
    if DEPTH_FILE.exists():
        for r in pd.read_csv(DEPTH_FILE, encoding="cp949").itertuples():
            key = station_key(int(r.호선), r.역명)
            if key in by_name:
                depth[by_name[key]] = r.정거장깊이
            else:
                note("station_depth", f"{r.호선}호선 {r.역명}", "역명 매칭 실패")
    st["depth_m"] = st.station_no.map(depth)

    # 역사(驛舍) 묶음: 같은 건물을 쓰는 호선별 역을 하나로 묶는다(환승역 대응)
    keys = {r.station_no: complex_key(r.line_no, r.station_nm) for r in st.itertuples()}
    groups: dict[str, list[int]] = defaultdict(list)
    for no, k in keys.items():
        groups[k].append(no)
    st["complex_id"] = st.station_no.map(lambda n: min(groups[keys[n]]))

    by_code = {f"{n:04d}": n for n in st.station_no}  # 승강기 API의 STN_CD → station_no
    return st, by_name, by_code


def build_complex(st: pd.DataFrame) -> pd.DataFrame:
    """역사 = complex_id(묶음 안 가장 작은 역번호), 이름은 대표 역명에서 괄호를 뺀 값."""
    rows = []
    for cid, g in st.groupby("complex_id"):
        rep = g.sort_values("station_no").iloc[0]
        name = re.sub(r"\(.*?\)|\(.*$", "", rep.station_nm).strip()
        key = complex_key(rep.line_no, rep.station_nm)
        if key != norm_name(rep.station_nm):  # 별칭으로 묶인 경우(총신대입구 → 이수)
            name = key
        rows.append({"complex_id": cid, "complex_nm": name})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- 환승
def to_seconds(v: str) -> int | None:
    m = re.fullmatch(r"(\d+):(\d+)", str(v).strip())
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


def build_transfer(by_name) -> pd.DataFrame:
    rows = []
    for r in load_raw("transfer"):
        key = station_key(line_of(r["LINE"]), r["TRFSTN_NM"])
        if key not in by_name:
            note("transfer", f"{key[0]}호선 {r['TRFSTN_NM']}", "역명 매칭 실패")
            continue
        rows.append({
            "station_no": by_name[key],
            "to_line": r["TRAS_RTE"].strip(),
            "distance_m": int(r["TRAS_DSTNC"]) if str(r["TRAS_DSTNC"]).isdigit() else None,
            "transfer_sec": to_seconds(r["TRAS_REQ_HR"]),
        })
    return pd.DataFrame(rows).drop_duplicates(["station_no", "to_line"])


# ---------------------------------------------------------------- 승강기
def build_elevator(by_code) -> pd.DataFrame:
    """모든 스냅샷에 한 번이라도 나온 승강기를 모은다(같은 승강기는 마지막 관측값). elevator_no는 DB가 부여한다."""
    fclt = {}
    for doc in load_snapshots("elevator_ev"):
        fclt.update({(r["stnCd"], r["fcltNm"]): r["fcltNo"] for r in doc["rows"]})
    rows: dict[tuple, dict] = {}
    for doc in load_snapshots("elevator_status"):
        for r in doc["rows"]:
            if r["ELVTR_SE"] not in KINDS:
                continue
            if r["STN_CD"] not in by_code:
                note("elevator", f"{r['STN_CD']} {r['STN_NM']}", "역코드가 역 목록에 없음")
                continue
            k = (by_code[r["STN_CD"]], r["ELVTR_NM"])
            rows[k] = {
                "station_no": k[0],
                "kind": r["ELVTR_SE"],
                "elevator_nm": r["ELVTR_NM"],
                "location": r["INSTL_PSTN"],
                "section": r["OPR_SEC"],
                "fclt_no": fclt.get((r["STN_CD"], r["ELVTR_NM"])),
            }
    return pd.DataFrame(list(rows.values()))


# ---------------------------------------------------------------- 승하차
def wide_to_long(df: pd.DataFrame, slot_cols: dict[str, int], id_cols: list[str], value: str) -> pd.DataFrame:
    long = df.melt(id_vars=id_cols, value_vars=list(slot_cols), var_name="col", value_name=value)
    long["hour_slot"] = long.col.map(slot_cols)
    long[value] = pd.to_numeric(long[value], errors="coerce")
    return long.drop(columns="col")


def build_ridership(valid_stations: set[int]) -> pd.DataFrame:
    sen = pd.DataFrame(load_raw("ridership_senior"))
    sen_slots = {"BFR6": 5, **{f"T{h:02d}": h for h in range(6, 25)}}
    sen = sen.rename(columns={"YMD": "ride_date", "SUBW_NO": "station_no", "GUBUN": "dir"})
    sen = wide_to_long(sen, sen_slots, ["station_no", "ride_date", "dir"], "n")
    sen = sen.pivot_table(index=["station_no", "ride_date", "hour_slot"], columns="dir", values="n", aggfunc="sum")
    sen = sen.rename(columns={"승차": "board_senior", "하차": "alight_senior"})

    # 전체 승하차: API(OA-12921)는 2023~2024년만 제공하므로 2025년분은 공공데이터포털 파일을 쓴다.
    allr = pd.DataFrame(load_raw("ridership_all"))
    if RIDERSHIP_2025_FILE.exists():
        f = pd.read_csv(RIDERSHIP_2025_FILE, encoding="cp949", dtype=str)
        hour_cols = [c for c in f.columns if "시" in c and c not in ("수송일자", "승하차구분")]
        rename = {"수송일자": "MVMN_YMD", "역번호": "STTN_NO", "승하차구분": "GTNF_SE"}
        rename.update({c: k for c, k in zip(hour_cols, ["HR06_BFR", *[f"HR{h:02d}" for h in range(6, 25)]])})
        f = f.rename(columns=rename)[["MVMN_YMD", "STTN_NO", "GTNF_SE", "HR06_BFR", *[f"HR{h:02d}" for h in range(6, 25)]]]
        allr = pd.concat([allr, f], ignore_index=True)
    allr = allr[allr.MVMN_YMD.astype(str).str.startswith(str(YEAR))]
    if allr.empty:
        note("ridership", f"전체 승하차 {YEAR}", "API에 해당 연도 없음 → board_all·alight_all을 비워 둠")
        sen[["board_all", "alight_all"]] = pd.NA
        df = sen.reset_index()
    else:
        all_slots = {"HR06_BFR": 5, **{f"HR{h:02d}": h for h in range(6, 25)}}
        allr = allr.rename(columns={"MVMN_YMD": "ride_date", "STTN_NO": "station_no", "GTNF_SE": "dir"})
        allr = wide_to_long(allr, all_slots, ["station_no", "ride_date", "dir"], "n")
        allr = allr.pivot_table(index=["station_no", "ride_date", "hour_slot"], columns="dir", values="n", aggfunc="sum")
        allr = allr.rename(columns={"승차": "board_all", "하차": "alight_all"})
        df = allr.join(sen, how="outer").reset_index()
    df["station_no"] = df.station_no.astype(int)
    missing = sorted(set(df.station_no) - valid_stations)
    for no in missing:
        note("ridership", str(no), "역 목록에 없는 역번호 (적재 제외)")
    df = df[df.station_no.isin(valid_stations)]
    cols = ["board_all", "alight_all", "board_senior", "alight_senior"]
    df[cols] = df[cols].round().astype("Int64")
    return df[["station_no", "ride_date", "hour_slot", *cols]].sort_values(["station_no", "ride_date", "hour_slot"])


# ---------------------------------------------------------------- 수집 스냅샷 → 이력
def parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=None)


# 수집 공백 기준(분). 매시 수집이므로 직전 관측과 이보다 더 벌어지면 그 사이 상태를 모른다.
# 03_sql/04_views.sql의 v_collect_gap(> 70분)과 같은 값이어야 한다.
GAP_MINUTES = 70


def outage_intervals(observations: list[tuple[datetime, dict[tuple, str]]]) -> list[dict]:
    """시간순 관측 [(수집 시각, {승강기 키: 상태})]에서 '사용가능'이 아닌 구간을 뽑는다.
    시작 = 비가동이 처음 관측된 시각, 종료 = 다시 사용가능으로 관측된 시각(진행 중이면 None).
    어떤 시각에 승강기가 응답에서 빠지면 상태를 모르므로 구간을 바꾸지 않는다.
    start_known: 실제 시작 시각을 모르면 0 — 승강기를 처음 관측했을 때 이미 비가동이었거나,
    그 승강기의 직전 관측과 GAP_MINUTES분보다 더 벌어진 뒤(수집 공백·응답 누락 직후) 비가동이 처음 보인 경우.
    직전 관측(GAP_MINUTES분 이내)이 가동이었다가 비가동이 된 경우만 1."""
    open_: dict[tuple, dict] = {}
    seq: dict[tuple, int] = defaultdict(int)
    last_ts: dict[tuple, datetime] = {}
    out = []
    for ts, states in observations:
        for k, status in states.items():
            prev = last_ts.get(k)
            last_ts[k] = ts
            down = status != AVAILABLE
            if down and k not in open_:
                # 분 단위 내림 비교: SQL TIMESTAMPDIFF(MINUTE, ...) > 70 과 같은 판정
                known = prev is not None and (ts - prev).total_seconds() // 60 <= GAP_MINUTES
                seq[k] += 1
                open_[k] = {"key": k, "seq": seq[k], "status": status, "start_at": ts, "end_at": None,
                            "start_known": 1 if known else 0}
            elif not down and k in open_:
                rec = open_.pop(k)
                rec["end_at"] = ts
                out.append(rec)
    out.extend(open_.values())
    return sorted(out, key=lambda r: (r["key"], r["seq"]))


def build_outage(elevators: pd.DataFrame, by_code) -> pd.DataFrame:
    known = set(zip(elevators.station_no, elevators.elevator_nm))
    obs = []
    for doc in load_snapshots("elevator_status"):
        states = {}
        for r in doc["rows"]:
            k = (by_code.get(r["STN_CD"]), r["ELVTR_NM"])
            if k in known:
                states[k] = r["USE_YN"]
        obs.append((parse_ts(doc["collected_at"]), states))
    recs = outage_intervals(obs)
    cols = ("seq", "status", "start_at", "end_at", "start_known")
    rows = [{"station_no": r["key"][0], "elevator_nm": r["key"][1], **{c: r[c] for c in cols}} for r in recs]
    return pd.DataFrame(rows, columns=["station_no", "elevator_nm", *cols])


def build_exit_closure(by_name) -> pd.DataFrame:
    # 역명이 잘려 오는 경우("건대입구(")가 있어, 정규화 이름이 같은 호선 역명의 앞부분과 일치하면 매칭한다
    names_by_line = defaultdict(list)
    for (ln, nm), no in by_name.items():
        names_by_line[ln].append((nm, no))

    def find(ln, raw):
        key = station_key(ln, raw)[1]
        exact = [no for nm, no in names_by_line[ln] if nm == key]
        if exact:
            return exact[0]
        pref = [no for nm, no in names_by_line[ln] if nm.startswith(key)]
        return pref[0] if len(pref) == 1 else None

    recs: dict[tuple, dict] = {}
    for doc in load_snapshots("exit_closure"):
        ts = parse_ts(doc["collected_at"])
        for r in doc["rows"]:
            ln = line_of(r["LINE"])
            no = find(ln, r["SBWY_STNS_NM"])
            if no is None:
                note("exit_closure", f"{r['LINE']} {r['SBWY_STNS_NM']}", "역명 매칭 실패")
                continue
            start = r["BGNG_YMD"][:10]
            detour = (r.get("RPLC_PATH") or "").strip()
            k = (no, r["CLSG_PLC"].strip(), start, detour)
            rec = recs.setdefault(k, {
                "station_no": no, "place": k[1], "start_date": start, "reason": r["CLSG_RSN"],
                "detour": detour, "first_seen_at": ts,
            })
            rec["end_date"] = (r.get("END_YMD") or "")[:10] or None  # 종료일 변경은 마지막 관측값으로 갱신
            rec["last_seen_at"] = ts
    cols = ["station_no", "place", "start_date", "end_date", "reason", "detour", "first_seen_at", "last_seen_at"]
    return pd.DataFrame(list(recs.values()), columns=cols)


def build_snapshot_log() -> pd.DataFrame:
    log = pd.read_csv(SNAP / "collect_log.csv", encoding="utf-8-sig")
    log = log[log.message.astype(str).str.endswith(".json.gz") | (log.result != "ok")]
    log["run_at"] = log.collected_at.map(lambda s: parse_ts(s).strftime("%Y-%m-%d %H:%M:%S"))
    return log.rename(columns={"row_count": "row_cnt"})[["source", "run_at", "row_cnt", "result", "message"]]


def station_from_clean() -> tuple[pd.DataFrame, dict, dict]:
    """--live 모드: 이미 만든 station.csv로 역 매칭 표만 다시 만든다(원본 승하차를 읽지 않음)."""
    st = pd.read_csv(CLEAN / "station.csv", encoding="utf-8-sig")
    by_name = {(r.line_no, norm_name(r.station_nm)): r.station_no for r in st.itertuples()}
    by_code = {f"{n:04d}": n for n in st.station_no}
    return st, by_name, by_code


def main(argv: list[str]) -> None:
    """전체 정제. '--live'를 주면 매시 수집분(승강기·비가동·출입구·수집 기록)만 다시 만든다."""
    CLEAN.mkdir(parents=True, exist_ok=True)
    live = "--live" in argv
    outputs: dict[str, pd.DataFrame] = {}
    if live:
        station, by_name, by_code = station_from_clean()
    else:
        station, by_name, by_code = build_station()
        outputs["line"] = pd.DataFrame({"line_no": range(1, 9), "line_nm": [f"{i}호선" for i in range(1, 9)]})
        outputs["station_complex"] = build_complex(station)
        outputs["station"] = station
        outputs["transfer"] = build_transfer(by_name)
        outputs["ridership"] = build_ridership(set(station.station_no))
    elevator = build_elevator(by_code)
    outputs["elevator"] = elevator
    outputs["outage"] = build_outage(elevator, by_code)
    outputs["exit_closure"] = build_exit_closure(by_name)
    outputs["snapshot_log"] = build_snapshot_log()
    if not live:
        outputs["unmatched"] = pd.DataFrame(unmatched, columns=["source", "key", "reason"])

    for name, df in outputs.items():
        df.to_csv(CLEAN / f"{name}.csv", index=False, encoding="utf-8-sig")
        print(f"{name:15s} {len(df):>9,d} rows")


if __name__ == "__main__":
    main(sys.argv[1:])
