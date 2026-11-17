"""DB 접속과 질의 (삽입 SQL 공통 모듈).

모든 질의는 pymysql 매개변수(%s)로 사용자 입력을 전달한다. 문자열을 이어 붙여 SQL을 만들지 않는다.
접속 정보는 MySQL login-path 'endb'에서 읽는다.
조회(query)는 자동 커밋 연결 하나를 잠금으로 보호해 재사용하고, 끊기면 한 번 다시 연결한다.
"""

from __future__ import annotations

import threading
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

import myloginpath
import pandas as pd
import pymysql

DB = "subway_access_db"


def connect() -> pymysql.connections.Connection:
    """새 연결(쓰기용, analysis.py 등). 호출한 쪽이 닫는다."""
    return pymysql.connect(**myloginpath.parse("endb"), database=DB, charset="utf8mb4")


# 조회 전용 공유 연결. autocommit=True여야 오래 열린 연결도 매번 최신 스냅샷을 읽는다(REPEATABLE READ)
_lock = threading.Lock()
_shared: pymysql.connections.Connection | None = None
_RECONNECT_ERRORS = (2003, 2006, 2013, 2055)  # 서버 접속 불가·연결 끊김
# 재귀 CTE 깊이 한도(기본 1000). complex_exposure는 비가동 1시간마다 한 단계씩 내려가므로
# 1000시간(약 42일)을 넘는 구간이 있으면 ERROR 3636이 난다. 연결마다(재연결 포함) 세션 값으로 올려 둔다.
_READER_INIT = "SET SESSION cte_max_recursion_depth = 10000"


def _reader() -> pymysql.connections.Connection:
    global _shared
    if _shared is not None:
        try:
            _shared.ping(reconnect=False)
        except pymysql.err.Error:  # 닫혔거나 끊긴 연결은 버리고 새로 만든다
            _drop_reader()
    if _shared is None:
        _shared = pymysql.connect(**myloginpath.parse("endb"), database=DB, charset="utf8mb4", autocommit=True,
                                  init_command=_READER_INIT)
    return _shared


def _drop_reader() -> None:
    global _shared
    if _shared is not None:
        try:
            _shared.close()
        except pymysql.err.Error:
            pass
    _shared = None


def query(sql: str, params: Sequence | None = None) -> pd.DataFrame:
    """SELECT 실행 → DataFrame. 사용자 입력은 반드시 params(%s)로 넘긴다."""
    with _lock:
        for attempt in (1, 2):
            try:
                with _reader().cursor() as cur:
                    cur.execute(sql, params)
                    cols = [d[0] for d in cur.description]
                    rows = cur.fetchall()
                break
            except (pymysql.err.OperationalError, pymysql.err.InterfaceError) as e:
                lost = isinstance(e, pymysql.err.InterfaceError) or (e.args and e.args[0] in _RECONNECT_ERRORS)
                if lost:
                    _drop_reader()
                if attempt == 2 or not lost:  # SQL 오류는 다시 시도하지 않는다
                    raise
    df = pd.DataFrame(list(rows), columns=cols)
    # MySQL DECIMAL은 Decimal 객체로 오므로 float로 바꾼다(차트·계산용)
    for c in df.columns:
        first = df[c].dropna().head(1)
        if not first.empty and isinstance(first.iloc[0], Decimal):
            df[c] = df[c].astype(float)
    return df


# ───────────────────────── 시간 규칙
def hour_slot_of(ts: datetime) -> int:
    """시각 → 승하차 시간대 번호. 0시대는 24(24시 이후), 1~5시는 5(06시 이전)."""
    h = ts.hour
    if h == 0:
        return 24
    return 5 if h < 6 else h


def day_type_of(ts: datetime) -> str:
    return "주말" if ts.weekday() >= 5 else "평일"


def slot_label(slot: int) -> str:
    if slot == 5:
        return "06시 이전"
    if slot == 24:
        return "24시 이후"
    return f"{slot:02d}시"


STALE_HOURS = 2.0  # 매시 수집이므로 2시간 넘게 새 스냅샷이 없으면 "지금" 상태를 믿기 어렵다


def hours_since(ts, now: datetime) -> float | None:
    """ts부터 now까지 경과 시간(시간). ts가 없으면(None·NaT) None."""
    if ts is None or pd.isna(ts):
        return None
    return (pd.Timestamp(now) - pd.Timestamp(ts)).total_seconds() / 3600


def is_stale(last_at, now: datetime, limit_hours: float = STALE_HOURS) -> bool:
    """마지막 수집이 limit_hours보다 오래됐거나 수집 기록이 없으면 True."""
    h = hours_since(last_at, now)
    return h is None or h > limit_hours


# ───────────────────────── CSV 내보내기
FORMULA_START = ("=", "+", "-", "@", "\t", "\r")  # 스프레드시트가 수식으로 해석하는 첫 글자


def csv_safe(df: pd.DataFrame) -> pd.DataFrame:
    """CSV 수식 주입 방지: 문자열 칸이 = + - @ 탭·CR로 시작하면 앞에 작은따옴표를 붙인다. 숫자·날짜 열은 그대로."""
    def esc(v):
        return "'" + v if isinstance(v, str) and v.startswith(FORMULA_START) else v

    out = df.copy()
    for c in out.columns:
        if out[c].dtype.kind not in "biufcmM":
            out[c] = out[c].map(esc)
    return out


# ───────────────────────── 화면·분석용 질의
def stations() -> pd.DataFrame:
    return query(
        "SELECT station_no, station_nm, line_no, line_nm, complex_id, complex_nm, lat, lng, depth_m "
        "FROM v_station ORDER BY line_no, station_no"
    )


def collect_period() -> dict:
    df = query("SELECT first_at, last_at, n_snapshots FROM v_collect_period")
    return df.iloc[0].to_dict()


def profile(complex_id: int) -> pd.DataFrame:
    """질문 1: 역사의 요일구분·시간대별 평균 이용과 노인 비중."""
    return query(
        "SELECT day_type, hour_slot, avg_all, avg_senior, "
        "ROUND(100 * avg_senior / NULLIF(avg_all, 0), 1) AS senior_pct "
        "FROM ridership_profile WHERE complex_id = %s ORDER BY day_type, hour_slot",
        (complex_id,),
    )


def elevators(complex_id: int) -> pd.DataFrame:
    return query(
        "SELECT station_nm, line_no, kind, elevator_nm, location, section, status_now, down_since, down_hours, "
        "down_start_known FROM v_elevator_now WHERE complex_id = %s "
        "ORDER BY status_now = '사용가능', kind DESC, line_no, elevator_nm",
        (complex_id,),
    )


def closures(complex_id: int) -> pd.DataFrame:
    return query(
        "SELECT station_nm, line_no, place, start_date, end_date, reason, detour "
        "FROM v_closure_now WHERE complex_id = %s ORDER BY start_date",
        (complex_id,),
    )


def all_closures() -> pd.DataFrame:
    return query(
        "SELECT complex_nm, station_nm, line_no, place, start_date, end_date, reason, detour "
        "FROM v_closure_now ORDER BY line_no, station_nm"
    )


def down_now(day_type: str, hour_slot: int) -> pd.DataFrame:
    """질문 2: 현재 비가동 승강기와 선택 시간대의 역사 평균 노인 이용(영향 규모 추정)."""
    return query(
        "SELECT n.complex_id, n.complex_nm, n.station_nm, n.line_no, n.kind, n.elevator_nm, n.location, "
        "n.down_since, n.down_hours, n.down_start_known, p.avg_senior AS senior_at_hour "
        "FROM v_elevator_now n LEFT JOIN ridership_profile p "
        "ON p.complex_id = n.complex_id AND p.day_type = %s AND p.hour_slot = %s "
        "WHERE n.status_now <> '사용가능' "
        "ORDER BY (n.kind = 'EV') DESC, p.avg_senior DESC",
        (day_type, hour_slot),
    )


def complex_outage(limit: int = 20) -> pd.DataFrame:
    """역사별 비가동 누적. n_outage·outage_hours는 시작 시각을 아는 구간(start_known = 1)만 센다."""
    return query(
        "SELECT complex_nm, n_elevator, n_ev, n_es, n_outage, outage_hours, n_down_now, "
        "ROUND(outage_hours / NULLIF(n_elevator, 0), 2) AS hours_per_elevator, "
        "n_outage_unknown_start, n_outage_ev, outage_hours_ev "
        "FROM v_complex_outage WHERE n_outage > 0 ORDER BY outage_hours DESC LIMIT %s",
        (limit,),
    )


def outage_summary() -> dict:
    """비가동 구간 전체 요약: 시작 시각을 아는/모르는 건수, 수집 공백과 겹친 건수."""
    df = query(
        "SELECT COUNT(*) AS n_all, COALESCE(SUM(start_known = 1), 0) AS n_known, "
        "COALESCE(SUM(start_known = 0), 0) AS n_unknown, COALESCE(SUM(gap_overlap), 0) AS n_gap_overlap, "
        "COALESCE(SUM(start_known = 1 AND gap_overlap = 1), 0) AS n_known_gap_overlap FROM v_outage"
    )
    return {k: int(v) for k, v in df.iloc[0].items()}


def outage_daily() -> pd.DataFrame:
    """일별 비가동 발생(시작일 기준, 시작 시각을 아는 구간만)."""
    return query(
        "SELECT DATE(start_at) AS day, kind, COUNT(*) AS n_outage, ROUND(SUM(hours), 1) AS hours "
        "FROM v_outage WHERE start_known = 1 GROUP BY DATE(start_at), kind ORDER BY day, kind"
    )


def complex_exposure(limit: int = 20) -> pd.DataFrame:
    """역사별 비가동 영향 규모 추정(시작 시각을 아는 구간만).

    비가동 구간을 1시간 단위로 펼쳐(재귀 CTE) 각 시각의 요일구분·시간대에 해당하는 역사 평균 노인 이동
    (2025년 승차+하차)을 더한다. 승강기별 이용이 아니라 역사 전체 이동이므로 상대 비교용 추정치다.
    마지막 수집 시각에 막 시작한(길이 0인) 진행 중 구간은 아직 1시간도 지나지 않았으므로 세지 않는다.
    재귀 깊이 한도는 공유 연결의 _READER_INIT(10000시간)이 정한다.
    """
    return query(
        "WITH RECURSIVE hrs AS ("
        " SELECT complex_id, elevator_no, seq, kind, start_at AS h,"
        "  COALESCE(end_at, (SELECT last_at FROM v_collect_period)) AS until_at"
        " FROM v_outage"
        " WHERE start_known = 1 AND start_at < COALESCE(end_at, (SELECT last_at FROM v_collect_period))"
        " UNION ALL"
        " SELECT complex_id, elevator_no, seq, kind, h + INTERVAL 1 HOUR, until_at FROM hrs"
        " WHERE h + INTERVAL 1 HOUR < until_at) "
        "SELECT hrs.complex_id, c.complex_nm, COUNT(DISTINCT hrs.elevator_no, hrs.seq) AS n_outage, "
        "COUNT(DISTINCT IF(hrs.kind = 'EV', hrs.elevator_no, NULL), hrs.seq) AS n_outage_ev, "
        "COUNT(*) AS outage_slot_hours, ROUND(SUM(p.avg_senior), 0) AS senior_exposed "
        "FROM hrs JOIN station_complex c ON c.complex_id = hrs.complex_id "
        "LEFT JOIN ridership_profile p ON p.complex_id = hrs.complex_id "
        " AND p.day_type = IF(DAYOFWEEK(hrs.h) IN (1, 7), '주말', '평일') "
        " AND p.hour_slot = IF(HOUR(hrs.h) < 6, IF(HOUR(hrs.h) = 0, 24, 5), HOUR(hrs.h)) "
        "GROUP BY hrs.complex_id, c.complex_nm ORDER BY senior_exposed DESC LIMIT %s",
        (limit,),
    )


def elevator_history(complex_id: int) -> pd.DataFrame:
    """역사 안 승강기별 비가동 이력(시작 시각을 모르는 구간도 표시)."""
    return query(
        "SELECT station_nm, line_no, kind, elevator_nm, location, status, start_at, end_at, hours, ongoing, "
        "start_known, gap_overlap FROM v_outage WHERE complex_id = %s ORDER BY start_at DESC, elevator_nm",
        (complex_id,),
    )


def features() -> pd.DataFrame:
    return query("SELECT * FROM v_complex_features ORDER BY complex_id")


def cluster_latest() -> pd.DataFrame:
    return query(
        "SELECT r.complex_id, r.complex_nm, r.cluster_no, r.cluster_nm, r.priority_rank, r.priority_score, "
        "f.senior_weekday, f.senior_pct, f.vertical_m, f.max_transfer_sec, f.n_elevator, f.n_ev, "
        "f.outage_hours, f.n_down_now, f.lat, f.lng "
        "FROM v_cluster_latest r JOIN v_complex_features f USING (complex_id) ORDER BY r.priority_rank"
    )


def cluster_run_latest() -> dict | None:
    df = query("SELECT run_id, run_at, k, features, silhouette, data_until FROM cluster_run ORDER BY run_id DESC LIMIT 1")
    return None if df.empty else df.iloc[0].to_dict()


def hourly_total() -> pd.DataFrame:
    """전체 역사 합계 시간대별 노인 비중."""
    return query(
        "SELECT day_type, hour_slot, SUM(avg_senior) AS senior, SUM(avg_all) AS total, "
        "ROUND(100 * SUM(avg_senior) / SUM(avg_all), 1) AS senior_pct "
        "FROM ridership_profile GROUP BY day_type, hour_slot ORDER BY day_type, hour_slot"
    )


def collect_gap() -> pd.DataFrame:
    """수집 공백(스냅샷 간격 70분 초과, 뷰 v_collect_gap)."""
    return query("SELECT prev_at, run_at, gap_min FROM v_collect_gap ORDER BY run_at")


def load_log(limit: int = 30) -> pd.DataFrame:
    """최근 적재 기록."""
    return query(
        "SELECT source, run_at, row_cnt, result, message FROM load_log ORDER BY load_id DESC LIMIT %s",
        (limit,),
    )
