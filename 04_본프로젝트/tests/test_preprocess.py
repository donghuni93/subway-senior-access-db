import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from preprocess import AVAILABLE, complex_key, line_from_code, norm_name, outage_intervals, station_key, to_seconds

DOWN = "보수중"


def t(h):
    return datetime(2026, 11, 17, h)


def test_outage_open_close_and_reopen():
    a = ("A",)
    obs = [(t(1), {a: AVAILABLE}), (t(2), {a: DOWN}), (t(3), {a: DOWN}), (t(4), {a: AVAILABLE}), (t(5), {a: DOWN})]
    recs = outage_intervals(obs)
    assert [(r["seq"], r["start_at"], r["end_at"]) for r in recs] == [(1, t(2), t(4)), (2, t(5), None)]


def test_outage_missing_observation_keeps_interval_open():
    a = ("A",)
    obs = [(t(1), {a: DOWN}), (t(2), {}), (t(3), {a: DOWN}), (t(4), {a: AVAILABLE})]
    recs = outage_intervals(obs)
    assert len(recs) == 1 and recs[0]["start_at"] == t(1) and recs[0]["end_at"] == t(4)


def test_outage_down_at_first_snapshot_starts_there():
    recs = outage_intervals([(t(1), {("A",): DOWN, ("B",): AVAILABLE})])
    assert len(recs) == 1 and recs[0]["key"] == ("A",) and recs[0]["end_at"] is None


def test_start_known_open_at_first_snapshot_is_unknown():
    a, b = ("A",), ("B",)
    obs = [(t(1), {a: DOWN, b: AVAILABLE}), (t(2), {a: DOWN, b: DOWN}), (t(3), {a: AVAILABLE, b: DOWN})]
    recs = {r["key"]: r for r in outage_intervals(obs)}
    assert recs[a]["start_known"] == 0 and recs[a]["end_at"] == t(3)  # 첫 관측에 이미 비가동 → 시작 모름
    assert recs[b]["start_known"] == 1 and recs[b]["start_at"] == t(2)  # 가동 관측 뒤 시작 → 시작 앎


def test_start_known_reopen_and_late_first_observation():
    a, c = ("A",), ("C",)
    obs = [(t(1), {a: DOWN}), (t(2), {a: AVAILABLE}), (t(3), {a: DOWN, c: DOWN})]
    recs = outage_intervals(obs)
    assert [(r["key"], r["seq"], r["start_known"]) for r in recs] == [(a, 1, 0), (a, 2, 1), (c, 1, 0)]


def test_start_known_after_collection_gap_is_unknown():
    a = ("A",)
    # 02시 → 11시 40분 공백(70분 초과) 직후 처음 보인 비가동은 실제 시작이 공백 안 어딘가이다
    obs = [(t(1), {a: AVAILABLE}), (t(2), {a: AVAILABLE}), (datetime(2026, 11, 17, 11, 40, 29), {a: DOWN})]
    recs = outage_intervals(obs)
    assert len(recs) == 1 and recs[0]["start_known"] == 0


def test_start_known_after_elevator_missing_is_unknown():
    a = ("A",)
    # 수집은 매시 이어졌지만 이 승강기가 응답에서 빠져 있다가 비가동으로 다시 나타남
    obs = [(t(0), {a: AVAILABLE}), (t(1), {}), (t(10), {}), (t(11), {a: DOWN})]
    recs = outage_intervals(obs)
    assert len(recs) == 1 and recs[0]["start_known"] == 0


def test_start_known_normal_hourly_open_is_known():
    a = ("A",)
    obs = [(t(1), {a: AVAILABLE}), (datetime(2026, 11, 17, 2, 0, 30), {a: DOWN})]  # 간격 60분 남짓
    recs = outage_intervals(obs)
    assert len(recs) == 1 and recs[0]["start_known"] == 1


def test_start_known_first_seen_down_still_unknown():
    recs = outage_intervals([(t(1), {("A",): DOWN})])
    assert recs[0]["start_known"] == 0


def test_norm_name():
    assert norm_name("서울역(1)") == "서울"
    assert norm_name("서울역") == "서울"
    assert norm_name("동대문역사문화공원(DDP)") == "동대문역사문화공원"
    assert norm_name("건대입구(") == "건대입구"
    assert norm_name("역삼") == "역삼"


def test_complex_key_groups_transfer_stations():
    assert complex_key(1, "서울역") == complex_key(4, "서울역")
    assert complex_key(3, "충무로") == complex_key(4, "충무로")
    assert complex_key(4, "총신대입구(이수)") == complex_key(7, "이수")  # 호선마다 이름이 다른 역사
    assert complex_key(8, "암사") != complex_key(8, "암사역사공원")  # 다른 역


def test_station_key_renamed_and_abbreviated():
    assert station_key(4, "당고개") == (4, "불암산")
    assert station_key(6, "DMC") == (6, "디지털미디어시티")
    assert station_key(2, "을지3가") == (2, "을지로3가")


def test_line_from_code():
    assert [line_from_code(n) for n in (150, 244, 329, 409, 2511, 2611, 2711, 2811)] == [1, 2, 3, 4, 5, 6, 7, 8]


def test_to_seconds():
    assert to_seconds("2:13") == 133
    assert to_seconds("") is None
