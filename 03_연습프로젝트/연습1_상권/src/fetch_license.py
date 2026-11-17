"""서울시 인허가 데이터(일반음식점·휴게음식점) 전량 내려받기. 원본 그대로 JSON Lines(gzip)로 저장.

저장: data/raw/{service}_YYYYMMDD_HHMM.jsonl.gz  (한 줄 = 업소 1건)
사용: python src/fetch_license.py [service ...]   # 생략 시 전체
인증키는 저장소 루트 .env의 SEOUL_API_KEY. 출력·로그에 키를 남기지 않는다.
"""

import gzip
import json
import sys
import time
from datetime import datetime
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
RAW = HERE / "data" / "raw"
SERVICES = {"LOCALDATA_072404": "일반음식점", "LOCALDATA_072405": "휴게음식점"}
PAGE = 1000


def load_key() -> str:
    for p in HERE.parents:
        env = p / ".env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.startswith("SEOUL_API_KEY="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit("SEOUL_API_KEY를 찾지 못했습니다.")


def get(key: str, svc: str, start: int, end: int) -> dict:
    url = f"http://openapi.seoul.go.kr:8088/{key}/json/{svc}/{start}/{end}/"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))[svc]
        except Exception as e:  # noqa: BLE001
            if attempt == 3:
                raise RuntimeError(str(e).replace(key, "***")) from None
            time.sleep(5 * (attempt + 1))


def fetch(key: str, svc: str) -> None:
    total = int(get(key, svc, 1, 1)["list_total_count"])
    starts = list(range(1, total + 1, PAGE))
    out = RAW / f"{svc}_{datetime.now():%Y%m%d_%H%M}.jsonl.gz"  # 시각별 스냅샷. 덮어쓰지 않는다
    tmp = out.with_suffix(".tmp")
    n = 0
    with gzip.open(tmp, "wt", encoding="utf-8") as f, ThreadPoolExecutor(max_workers=3) as ex:
        pages = ex.map(lambda s: get(key, svc, s, min(s + PAGE - 1, total))["row"], starts)  # 순서 유지
        for rows in pages:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += len(rows)
            if (n // PAGE) % 50 == 0:
                print(f"{svc} {n}/{total}", flush=True)
    if n != total:
        raise SystemExit(f"{svc}: 받은 {n}건, API 전체 {total}건. 불일치")
    tmp.replace(out)
    print(f"{svc} ({SERVICES[svc]}) 완료 {n}건 -> {out.name}", flush=True)


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    key = load_key()
    for svc in sys.argv[1:] or SERVICES:
        fetch(key, svc)
