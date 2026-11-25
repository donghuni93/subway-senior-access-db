"""정제 CSV(07_데이터/clean) → MySQL subway_access_db 적재 (삽입 SQL, pymysql).

- 접속 정보는 MySQL login-path 'endb'(%APPDATA%/MySQL/.mylogin.cnf)에서 읽는다. 코드·.env에 비밀번호를 두지 않는다.
- 같은 CSV를 다시 적재해도 결과가 같다(INSERT ... ON DUPLICATE KEY UPDATE).
- OUTAGE는 스냅샷 전체로부터 다시 계산한 결과이므로 테이블을 비우고 새로 넣는다(start_known 포함).
- 테이블별 적재 결과와 수집 스냅샷 기록을 LOAD_LOG에 남긴다.

사용: python 05_코드/load_db.py [table ...]   # 생략 시 전체
"""

from __future__ import annotations

import sys
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

import myloginpath
import pandas as pd
import pymysql

PROJECT_DIR = Path(__file__).resolve().parents[1]
CLEAN = PROJECT_DIR / "07_데이터" / "clean"
DB = "subway_access_db"
BATCH = 5000

# 테이블 → (CSV, 열 목록, 갱신할 열). 부모 → 자식 순서.
TABLES: dict[str, tuple[str, list[str], list[str]]] = {
    "line": ("line", ["line_no", "line_nm"], ["line_nm"]),
    "station_complex": ("station_complex", ["complex_id", "complex_nm"], ["complex_nm"]),
    "station": (
        "station",
        ["station_no", "fr_code", "line_no", "station_nm", "lat", "lng", "platform_type", "floors", "built_year",
         "depth_m", "complex_id"],
        ["fr_code", "line_no", "station_nm", "lat", "lng", "platform_type", "floors", "built_year", "depth_m",
         "complex_id"],
    ),
    "transfer": ("transfer", ["station_no", "to_line", "distance_m", "transfer_sec"], ["distance_m", "transfer_sec"]),
    "elevator": (
        "elevator",
        ["station_no", "kind", "elevator_nm", "location", "section", "fclt_no"],
        ["kind", "location", "section", "fclt_no"],
    ),
    "ridership": (
        "ridership",
        ["station_no", "ride_date", "hour_slot", "board_all", "alight_all", "board_senior", "alight_senior"],
        ["board_all", "alight_all", "board_senior", "alight_senior"],
    ),
    "exit_closure": (
        "exit_closure",
        ["station_no", "place", "start_date", "end_date", "reason", "detour", "first_seen_at", "last_seen_at"],
        ["end_date", "reason", "last_seen_at"],
    ),
    "load_log": ("snapshot_log", ["source", "run_at", "row_cnt", "result", "message"], ["row_cnt", "result", "message"]),
}


def connect() -> pymysql.connections.Connection:
    return pymysql.connect(**myloginpath.parse("endb"), database=DB, charset="utf8mb4", autocommit=False)


def records(df: pd.DataFrame, cols: list[str]) -> Iterable[tuple]:
    df = df[cols].astype(object).where(df[cols].notna(), None)
    return (tuple(r) for r in df.itertuples(index=False, name=None))


def upsert(cur, table: str, cols: list[str], update: list[str], rows: Iterable[tuple]) -> int:
    col_sql = ", ".join(cols)
    ph = ", ".join(["%s"] * len(cols))
    upd = ", ".join(f"{c} = VALUES({c})" for c in update) or f"{cols[0]} = {cols[0]}"
    sql = f"INSERT INTO {table} ({col_sql}) VALUES ({ph}) ON DUPLICATE KEY UPDATE {upd}"
    n, batch = 0, []
    for r in rows:
        batch.append(r)
        if len(batch) == BATCH:
            cur.executemany(sql, batch)
            n += len(batch)
            batch = []
    if batch:
        cur.executemany(sql, batch)
        n += len(batch)
    return n


def log(cur, source: str, row_cnt: int, result: str, message: str = "") -> None:
    cur.execute(
        "INSERT INTO load_log (source, run_at, row_cnt, result, message) VALUES (%s, %s, %s, %s, %s)",
        (source, datetime.now().replace(microsecond=0), row_cnt, result, message[:300]),
    )


def read(name: str) -> pd.DataFrame:
    return pd.read_csv(CLEAN / f"{name}.csv", encoding="utf-8-sig", dtype={"fr_code": str, "fclt_no": str})


def load_outage(cur) -> int:
    """(역번호, 승강기명) → elevator_no로 바꾼 뒤 OUTAGE를 다시 채운다."""
    df = read("outage")
    cur.execute("SELECT station_no, elevator_nm, elevator_no FROM elevator")
    ids = {(s, n): e for s, n, e in cur.fetchall()}
    df["elevator_no"] = [ids.get((s, n)) for s, n in zip(df.station_no, df.elevator_nm)]
    missing = df.elevator_no.isna().sum()
    if missing:
        raise ValueError(f"OUTAGE {missing}건의 승강기를 ELEVATOR에서 찾지 못함")
    cur.execute("DELETE FROM outage")
    cols = ["elevator_no", "seq", "status", "start_at", "end_at", "start_known"]
    return upsert(cur, "outage", cols, ["status", "end_at", "start_known"], records(df, cols))


# 2025년 공휴일(대체·임시공휴일 포함). 요일 구분에서 주말과 같이 '주말'(휴일)로 본다.
HOLIDAYS_2025 = [
    "2025-01-01", "2025-01-27", "2025-01-28", "2025-01-29", "2025-01-30", "2025-03-03", "2025-05-05",
    "2025-05-06", "2025-06-03", "2025-06-06", "2025-08-15", "2025-10-03", "2025-10-06", "2025-10-07",
    "2025-10-08", "2025-10-09", "2025-12-25",
]

PROFILE_SQL = """
INSERT INTO ridership_profile (complex_id, day_type, hour_slot, avg_all, avg_senior, n_days)
SELECT d.complex_id, d.day_type, d.hour_slot,
       ROUND(SUM(d.n_all) / n.n_days, 1), ROUND(SUM(d.n_senior) / n.n_days, 1), n.n_days
FROM (
    SELECT s.complex_id, r.ride_date, r.hour_slot,
           IF(DAYOFWEEK(r.ride_date) IN (1, 7) OR r.ride_date IN ({holidays}), '주말', '평일') AS day_type,
           SUM(COALESCE(r.board_all, 0) + COALESCE(r.alight_all, 0)) AS n_all,
           SUM(COALESCE(r.board_senior, 0) + COALESCE(r.alight_senior, 0)) AS n_senior
    FROM ridership r JOIN station s USING (station_no)
    GROUP BY s.complex_id, r.ride_date, r.hour_slot
) d
JOIN (  -- 역사·요일구분별 자료가 있는 날 수
    SELECT s.complex_id,
           IF(DAYOFWEEK(r.ride_date) IN (1, 7) OR r.ride_date IN ({holidays}), '주말', '평일') AS day_type,
           COUNT(DISTINCT r.ride_date) AS n_days
    FROM ridership r JOIN station s USING (station_no)
    GROUP BY s.complex_id, day_type
) n ON n.complex_id = d.complex_id AND n.day_type = d.day_type
GROUP BY d.complex_id, d.day_type, d.hour_slot, n.n_days
"""


def refresh_profile(cur) -> int:
    """RIDERSHIP → 역사 × 요일구분 × 시간대 평균(RIDERSHIP_PROFILE)을 다시 계산한다."""
    cur.execute("DELETE FROM ridership_profile")
    holidays = ", ".join(f"'{d}'" for d in HOLIDAYS_2025)
    return cur.execute(PROFILE_SQL.format(holidays=holidays))


LIVE = ["elevator", "exit_closure", "outage", "load_log"]  # 매시 수집분만 반영


def main(argv: list[str]) -> int:
    # outage를 load_log(수집 기록)보다 먼저 넣는다. outage 갱신이 실패했는데 새 수집 기록만 남으면
    # 대시보드의 '자료가 오래됨' 안내가 꺼진 채 지난 비가동 상태를 보여 주게 된다.
    order = [t for t in TABLES if t != "load_log"] + ["outage", "load_log", "ridership_profile"]
    targets = LIVE if "--live" in argv else ([a for a in argv if not a.startswith("--")] or order)
    conn = connect()
    try:
        with conn.cursor() as cur:
            for table in [t for t in order if t in targets]:
                try:
                    if table == "outage":
                        n = load_outage(cur)
                    elif table == "ridership_profile":
                        n = refresh_profile(cur)
                    else:
                        csv, cols, update = TABLES[table]
                        n = upsert(cur, table, cols, update, records(read(csv), cols))
                    if table != "load_log":
                        log(cur, f"file:{table}", n, "ok")
                    conn.commit()
                    print(f"{table:13s} {n:>9,d} rows")
                except Exception as e:  # noqa: BLE001 - 실패도 LOAD_LOG에 남긴 뒤 중단
                    conn.rollback()
                    log(cur, f"file:{table}", 0, "error", str(e))
                    conn.commit()
                    print(f"{table:13s} ERROR {e}")
                    return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
