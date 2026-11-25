"""승강기 가동현황·출입구 임시폐쇄 API 원본 수집기.

API 응답을 가공하지 않고 시각별 JSON 파일로 저장한다. DB 적재(OUTAGE, EXIT_CLOSURE 변환)는
설계 확정 후 이 파일들을 다시 읽어 수행한다. 표준 라이브러리만 사용한다.

사용:
    python 05_코드/collect.py                 # 모든 소스 수집
    python 05_코드/collect.py elevator_status # 일부 소스만

저장 위치:
    07_데이터/snapshots/{source}/YYYYMMDD_HHMM.json.gz  (gzip 압축 JSON. 읽기: gzip.open(p, "rt", encoding="utf-8"))
    07_데이터/snapshots/collect_log.csv  (수집 시각, 소스, 결과, 행 수, API 전체 건수, 메시지)

인증키는 환경변수 SEOUL_API_KEY 또는 프로젝트 폴더 또는 저장소 루트의 .env에서 읽으며, 로그에 남기지 않는다.
"""

from __future__ import annotations

import csv
import gzip
import json
import os
import sys
import time
import urllib.request
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]  # 03_본프로젝트
REPO_ROOT = PROJECT_DIR.parent
SNAPSHOT_DIR = PROJECT_DIR / "07_데이터" / "snapshots"
LOG_PATH = SNAPSHOT_DIR / "collect_log.csv"

BASE_URL = "http://openapi.seoul.go.kr:8088"
PAGE_SIZE = 1000  # 서울 열린데이터광장 1회 최대 조회 건수
RETRIES = 3

# source 이름 → (서비스명, 데이터셋 ID, 응답 형식)
SOURCES: dict[str, tuple[str, str, str]] = {
    "elevator_status": ("SeoulMetroFaciInfo", "OA-15994", "seoul"),  # 승강기 전체, 사용가능/보수중
    "elevator_ev": ("getWksnElvtr", "OA-22740", "gokr"),  # 엘리베이터, 시설번호·역번호 포함
    "exit_closure": ("TbSubwayLineDetail", "OA-22122", "seoul"),  # 출입구 임시폐쇄
}

LOG_FIELDS = ["collected_at", "source", "dataset", "result", "row_count", "api_total", "message"]

FetchJson = Callable[[str], dict]


class ApiError(RuntimeError):
    pass


def load_api_key() -> str:
    key = os.environ.get("SEOUL_API_KEY", "").strip()
    env_file = REPO_ROOT / ".env"
    if not key and env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("SEOUL_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        raise SystemExit("SEOUL_API_KEY가 없습니다. 저장소 루트 .env에 넣어 주세요.")
    return key


def http_get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_page(fmt: str, service: str, payload: dict) -> tuple[list[dict], int]:
    """응답 한 페이지에서 (행 목록, API가 알려 준 전체 건수)를 꺼낸다."""
    if fmt == "seoul":
        if service not in payload:
            result = payload.get("RESULT", {})
            if result.get("CODE") == "INFO-200":  # 해당하는 데이터가 없음
                return [], 0
            if not result:
                raise ApiError(f"예상하지 못한 응답 형식: 최상위 키 {list(payload)[:5]}")
            raise ApiError(f"{result.get('CODE')} {result.get('MESSAGE')}")
        block = payload[service]
        code = block.get("RESULT", {}).get("CODE")
        if code != "INFO-000":
            raise ApiError(f"{code} {block.get('RESULT', {}).get('MESSAGE')}")
        return list(block.get("row", [])), int(block["list_total_count"])

    if fmt == "gokr":
        resp = payload.get("response")
        if resp is None:
            result = payload.get("RESULT", {})
            raise ApiError(f"{result.get('CODE')} {result.get('MESSAGE')}")
        code = resp.get("header", {}).get("resultCode")
        if code != "00":
            raise ApiError(f"{code} {resp.get('header', {}).get('resultMsg')}")
        body = resp.get("body", {})
        items = body.get("items") or {}
        rows = items.get("item", []) if isinstance(items, dict) else []
        if isinstance(rows, dict):
            rows = [rows]
        return list(rows), int(body.get("totalCount", 0))

    raise ValueError(f"unknown format: {fmt}")


def fetch_all(fetch_json: FetchJson, key: str, service: str, fmt: str) -> tuple[list[dict], int]:
    """전체 페이지를 받아 합친다. 받은 행 수가 전체 건수와 다르면 ApiError."""
    rows: list[dict] = []
    start = 1
    total = 0
    while True:
        end = start + PAGE_SIZE - 1
        page, total = parse_page(fmt, service, fetch_json(f"{BASE_URL}/{key}/json/{service}/{start}/{end}/"))
        rows.extend(page)
        if end >= total or not page:
            break
        start = end + 1
    if len(rows) != total:
        raise ApiError(f"행 수 불일치: 받은 {len(rows)}건, API 전체 {total}건")
    return rows, total


def fetch_with_retry(fetch_json: FetchJson, key: str, service: str, fmt: str) -> tuple[list[dict], int]:
    last: Exception | None = None
    for attempt in range(RETRIES):
        try:
            return fetch_all(fetch_json, key, service, fmt)
        except Exception as e:  # noqa: BLE001 - 네트워크·API 오류 모두 재시도
            last = e
            if attempt < RETRIES - 1:
                time.sleep(10 * (attempt + 1))
    assert last is not None
    raise last


def write_snapshot(source: str, dataset: str, service: str, collected_at: datetime, rows: list[dict], total: int) -> Path:
    out_dir = SNAPSHOT_DIR / source
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{collected_at:%Y%m%d_%H%M}.json.gz"
    doc = {
        "source": source,
        "dataset": dataset,
        "service": service,
        "collected_at": collected_at.isoformat(timespec="seconds"),
        "api_total": total,
        "rows": rows,
    }
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:  # 원본 약 1MB/회 → 압축 후 약 1/10
        json.dump(doc, f, ensure_ascii=False)
    tmp.replace(path)
    return path


def append_log(record: dict) -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    new = not LOG_PATH.exists()
    with LOG_PATH.open("a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if new:
            w.writeheader()
        w.writerow(record)


def collect(sources: list[str], fetch_json: FetchJson = http_get_json) -> int:
    key = load_api_key()
    failures = 0
    for source in sources:
        service, dataset, fmt = SOURCES[source]
        collected_at = datetime.now().astimezone()
        record = {"collected_at": collected_at.isoformat(timespec="seconds"), "source": source, "dataset": dataset}
        try:
            rows, total = fetch_with_retry(fetch_json, key, service, fmt)
            path = write_snapshot(source, dataset, service, collected_at, rows, total)
            record.update(result="ok", row_count=len(rows), api_total=total, message=path.name)
        except Exception as e:  # noqa: BLE001
            failures += 1
            record.update(result="error", row_count=0, api_total="", message=str(e).replace(key, "***")[:300])
        append_log(record)
        print(f"{record['collected_at']} {source}: {record['result']} {record['row_count']} {record['message']}")
    return failures


def main(argv: list[str]) -> int:
    sources = argv or list(SOURCES)
    unknown = [s for s in sources if s not in SOURCES]
    if unknown:
        print(f"알 수 없는 소스: {unknown}. 가능한 값: {list(SOURCES)}", file=sys.stderr)
        return 2
    return 1 if collect(sources) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
