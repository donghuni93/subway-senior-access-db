"""기준 정보·승하차 이력 API를 한 번에 내려받아 원본 그대로 저장한다 (1회성).

저장: 07_데이터/raw/api/{name}.json.gz  ({"service", "dataset", "fetched_at", "api_total", "rows"})
사용: python 05_코드/fetch_reference.py [name ...]   # 생략 시 전체
"""

from __future__ import annotations

import gzip
import json
import sys
from datetime import datetime

from collect import PROJECT_DIR, fetch_with_retry, http_get_json, load_api_key

RAW_API_DIR = PROJECT_DIR / "07_데이터" / "raw" / "api"

# name → (서비스명, 데이터셋 ID)
DATASETS: dict[str, tuple[str, str]] = {
    "station_line": ("SearchSTNBySubwayLineInfo", "OA-15442"),  # 노선별 지하철역 정보 (역코드·외부코드)
    "station_master": ("subwayStationMaster", "OA-21232"),  # 역사마스터 (역사ID·위경도)
    "station_coord": ("subwayStationCoordinateInfo", "OA-22534"),  # 1~8호선 역사 좌표
    "station_building": ("MetroStnBuildingInfo", "OA-11572"),  # 역사건축정보 (형식·준공연도)
    "station_depth": ("subStaDept", "OA-13305"),  # 역사심도정보
    "elevator_size": ("SmrtScnFcltsInfo", "OA-12514"),  # 승강기 길이·높이
    "transfer": ("subwayTrans", "OA-13290"),  # 환승역 거리·소요시간
    "ridership_senior": ("trfcSubwDayTimeSnctzPwdbs", "OA-22483"),  # 노인 승하차 (2025)
    "ridership_all": ("subwSttn", "OA-12921"),  # 전체 승하차 (2024~2025)
}


def fetch(name: str, key: str) -> None:
    service, dataset = DATASETS[name]
    started = datetime.now().astimezone()
    try:
        rows, total = fetch_with_retry(http_get_json, key, service, "seoul")
    except Exception as e:  # noqa: BLE001
        print(f"{name}: 실패 - {str(e).replace(key, '***')[:200]}", flush=True)
        return
    if total == 0:
        print(f"{name}: API가 0건을 반환 (저장하지 않음)", flush=True)
        return
    RAW_API_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_API_DIR / f"{name}.json.gz"
    doc = {
        "name": name,
        "service": service,
        "dataset": dataset,
        "fetched_at": started.isoformat(timespec="seconds"),
        "api_total": total,
        "rows": rows,
    }
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False)
    print(f"{name}: {len(rows)}건 저장 → {path.name}", flush=True)


def main(argv: list[str]) -> int:
    names = argv or list(DATASETS)
    key = load_api_key()
    for name in names:
        fetch(name, key)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
