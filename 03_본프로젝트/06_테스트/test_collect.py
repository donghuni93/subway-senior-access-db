import gzip
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "05_코드"))
import collect


def seoul_page(rows, total):
    return {"S": {"list_total_count": total, "RESULT": {"CODE": "INFO-000", "MESSAGE": "ok"}, "row": rows}}


def gokr_page(rows, total):
    return {"response": {"header": {"resultCode": "00"}, "body": {"items": {"item": rows}, "totalCount": total}}}


def fake_fetch(pages):
    calls = []

    def fetch(url):
        calls.append(url)
        return pages[len(calls) - 1]

    return fetch, calls


def test_fetch_all_pages_until_total(monkeypatch):
    monkeypatch.setattr(collect, "PAGE_SIZE", 2)
    fetch, calls = fake_fetch([seoul_page([{"a": 1}, {"a": 2}], 3), seoul_page([{"a": 3}], 3)])
    rows, total = collect.fetch_all(fetch, "KEY", "S", "seoul")
    assert total == 3 and [r["a"] for r in rows] == [1, 2, 3]
    assert calls[0].endswith("/S/1/2/") and calls[1].endswith("/S/3/4/")


def test_fetch_all_raises_on_count_mismatch(monkeypatch):
    monkeypatch.setattr(collect, "PAGE_SIZE", 2)
    fetch, _ = fake_fetch([seoul_page([{"a": 1}, {"a": 2}], 5), seoul_page([], 5)])
    with pytest.raises(collect.ApiError, match="불일치"):
        collect.fetch_all(fetch, "KEY", "S", "seoul")


def test_seoul_no_data_is_empty():
    assert collect.parse_page("seoul", "S", {"RESULT": {"CODE": "INFO-200", "MESSAGE": "없음"}}) == ([], 0)


def test_seoul_error_code_raises():
    with pytest.raises(collect.ApiError, match="INFO-100"):
        collect.parse_page("seoul", "S", {"RESULT": {"CODE": "INFO-100", "MESSAGE": "인증키 오류"}})


def test_gokr_single_item_dict_becomes_list():
    rows, total = collect.parse_page("gokr", "G", gokr_page({"fcltNo": "1"}, 1))
    assert rows == [{"fcltNo": "1"}] and total == 1


def test_gokr_error_code_raises():
    payload = {"response": {"header": {"resultCode": "99", "resultMsg": "ERR"}, "body": {}}}
    with pytest.raises(collect.ApiError, match="99"):
        collect.parse_page("gokr", "G", payload)


def test_collect_writes_snapshot_and_log_without_key(monkeypatch, tmp_path):
    monkeypatch.setattr(collect, "SNAPSHOT_DIR", tmp_path)
    monkeypatch.setattr(collect, "LOG_PATH", tmp_path / "collect_log.csv")
    monkeypatch.setattr(collect, "RETRIES", 1)
    monkeypatch.setenv("SEOUL_API_KEY", "SECRETKEY123")

    def fetch(url):
        if "TbSubwayLineDetail" in url:
            raise OSError(f"connection failed for {url}")
        return {"SeoulMetroFaciInfo": seoul_page([{"x": 1}], 1)["S"]}

    failures = collect.collect(["elevator_status", "exit_closure"], fetch_json=fetch)
    assert failures == 1
    snaps = list((tmp_path / "elevator_status").glob("*.json.gz"))
    assert len(snaps) == 1
    with gzip.open(snaps[0], "rt", encoding="utf-8") as f:
        doc = json.load(f)
    assert doc["rows"] == [{"x": 1}] and doc["api_total"] == 1
    log = (tmp_path / "collect_log.csv").read_text(encoding="utf-8-sig")
    assert "ok" in log and "error" in log
    assert "SECRETKEY123" not in log
