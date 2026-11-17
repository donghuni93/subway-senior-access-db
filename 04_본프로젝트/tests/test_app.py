"""대시보드·DB 통합 테스트. 로컬 MySQL(subway_access_db, login-path endb)에 적재된 데이터가 필요하다."""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
import db
import streamlit as st
import theme
from streamlit.testing.v1 import AppTest

VIEWS = ["교통약자", "역 관리자", "데이터·수집 현황"]


def run_app() -> AppTest:
    return AppTest.from_file(str(SRC / "app.py"), default_timeout=120).run()


def pick(at: AppTest, station: pd.Series) -> None:
    """역 이름 검색 후 같은 호선의 결과를 고른다(이름이 겹치는 다른 역을 피함)."""
    at.text_input[0].input(station.station_nm).run()
    label = f"{station.station_nm} ({station.line_no}호선)"
    at.selectbox[0].select_index(at.selectbox[0].options.index(label)).run()
    assert not at.exception


def texts(at: AppTest) -> str:
    """화면의 안내 문구(마크다운·캡션·알림)를 한 문자열로."""
    parts = [e.value for kind in ("markdown", "caption", "info", "warning", "error", "success")
             for e in getattr(at, kind)]
    return "\n".join(str(p) for p in parts)


# ───────────────────────── 순수 함수
def test_hour_slot_and_day_type():
    assert db.hour_slot_of(datetime(2026, 11, 17, 0, 30)) == 24
    assert db.hour_slot_of(datetime(2026, 11, 17, 3, 0)) == 5
    assert db.hour_slot_of(datetime(2026, 11, 17, 14, 59)) == 14
    assert db.day_type_of(datetime(2026, 11, 17)) == "평일"  # 화요일
    assert db.day_type_of(datetime(2026, 11, 22)) == "주말"  # 일요일


def test_stale_banner_rule():
    now = datetime(2026, 11, 17, 14, 0)
    assert not db.is_stale(datetime(2026, 11, 17, 13, 0), now)  # 1시간 전: 정상
    assert not db.is_stale(datetime(2026, 11, 17, 12, 0), now)  # 정확히 2시간: 아직 정상
    assert db.is_stale(datetime(2026, 11, 17, 11, 59), now)  # 2시간 초과: 경고
    assert db.is_stale(datetime(2026, 11, 17, 2, 0), now)  # 실제 있었던 공백 길이
    # 수집 기록이 없으면(None·NaT) 경고
    assert db.is_stale(None, now) and db.is_stale(pd.NaT, now)
    assert db.hours_since(None, now) is None and db.hours_since(pd.NaT, now) is None
    assert db.hours_since(pd.Timestamp("2026-11-17 11:30"), now) == pytest.approx(2.5)


def test_palette_contrast_meets_wcag():
    assert theme.contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0)
    assert theme.contrast_ratio("#cde2fb", "#ffffff") < 3  # 교체 전 '그 외' 색은 기준 미달이었다
    for t in (theme.LIGHT, theme.DARK):
        for k in theme.TEXT_TOKENS:  # 본문 글자 4.5:1
            assert theme.contrast_ratio(t[k], t["surface"]) >= 4.5, (k, t[k])
        for k in theme.GRAPHIC_TOKENS:  # 차트 표식 3:1
            assert theme.contrast_ratio(t[k], t["surface"]) >= 3, (k, t[k])
        assert theme.contrast_ratio(theme.FOCUS, t["surface"]) >= 3
        # 범주 앞 두 색(평일/주말, 엘리베이터/에스컬레이터)은 막대·선 자체로 3:1
        for c in t["series"][:2]:
            assert theme.contrast_ratio(c, t["surface"]) >= 3, c
        # 군집 유형 색은 앞 5색까지 쓴다(k ≤ 6). 3:1 미만인 색은 색만으로 구분하지 않고
        # 범례 원·지도 점의 1px 테두리(text_muted)와 범례 글자·툴팁·표의 '유형' 열로 보완한다 → 테두리 토큰이 3:1 이상이어야 한다
        low = [c for c in t["series"][:5] if theme.contrast_ratio(c, t["surface"]) < 3]
        if low:
            assert theme.contrast_ratio(t["text_muted"], t["surface"]) >= 3
        assert len(t["series"]) <= 8 and len(set(t["series"])) == len(t["series"])
        assert t["senior"] != t["others"]
    # 알려진 저대비 색(밝은 화면): 바뀌면 이 목록과 theme.legend_html 설명을 함께 고친다
    assert [c for c in theme.LIGHT["series"][:5] if theme.contrast_ratio(c, "#ffffff") < 3] == \
        ["#1baf7a", "#eda100", "#e87ba4"]


def test_legend_html_escapes_names():
    out = theme.legend_html([("<b>유형</b>", "#2a78d6")])
    assert "&lt;b&gt;" in out and "<b>" not in out


def test_legend_swatch_has_border():
    out = theme.legend_html([("유형 3", "#eda100")], theme.LIGHT["text_muted"])
    assert f"border:1px solid {theme.LIGHT['text_muted']}" in out


def test_csv_safe_neutralizes_formulas():
    df = pd.DataFrame({"이름": ["=HYPERLINK(\"x\")", "+1", "-2", "@SUM(A1)", "\tx", "\rx", "보통 이름", None],
                       "값": [-1, 2, 3, 4, 5, 6, 7, 8], "실수": [-1.5, 0, 0, 0, 0, 0, 0, 0]})
    out = db.csv_safe(df)
    assert out["이름"].tolist()[:7] == ["'=HYPERLINK(\"x\")", "'+1", "'-2", "'@SUM(A1)", "'\tx", "'\rx", "보통 이름"]
    assert pd.isna(out["이름"].iloc[7])  # 빈 칸은 빈 칸 그대로
    assert out["값"].tolist() == df["값"].tolist() and out["실수"].tolist() == df["실수"].tolist()  # 숫자(음수 포함)는 그대로
    assert df["이름"].iloc[0] == "=HYPERLINK(\"x\")"  # 원본은 바꾸지 않는다


# ───────────────────────── DB 질의
def test_transfer_station_grouped_into_one_complex():
    st_ = db.stations()
    chungmuro = st_[st_.station_nm == "충무로"]
    assert set(chungmuro.line_no) == {3, 4}
    assert chungmuro.complex_id.nunique() == 1
    # 3호선 충무로에는 승강기가 없지만 역사 단위로는 4호선 승강기가 보인다
    assert len(db.elevators(int(chungmuro.complex_id.iloc[0]))) > 0


def test_profile_has_both_day_types_and_20_slots():
    st_ = db.stations()
    cid = int(st_[st_.station_nm == "제기동"].complex_id.iloc[0])
    prof = db.profile(cid)
    assert set(prof.day_type) == {"평일", "주말"}
    assert prof.groupby("day_type").hour_slot.nunique().eq(20).all()
    assert (prof.avg_senior <= prof.avg_all).all()


def test_shared_connection_reused_and_recovers():
    db.query("SELECT 1")
    first = db._shared
    db.query("SELECT 1")
    assert db._shared is first  # 같은 연결 재사용
    first.close()  # 끊긴 연결도 다음 조회에서 다시 연결한다
    assert db.query("SELECT 1 AS x").x.iloc[0] == 1


def test_outage_stats_use_known_start_only():
    s = db.outage_summary()
    assert s["n_all"] == s["n_known"] + s["n_unknown"]
    daily = db.outage_daily()
    assert int(daily.n_outage.sum()) == s["n_known"]
    ex = db.complex_exposure(500)
    # 노출 추정도 시작을 아는 구간만. 마지막 수집 시각에 막 시작한 길이 0 구간은 1시간도 지나지 않아 뺀다
    n_positive = int(db.query(
        "SELECT COUNT(*) AS n FROM v_outage o CROSS JOIN v_collect_period p "
        "WHERE o.start_known = 1 AND o.start_at < COALESCE(o.end_at, p.last_at)").n.iloc[0])
    assert int(ex.n_outage.sum()) == n_positive <= s["n_known"]
    assert (ex.senior_exposed.dropna() >= 0).all()
    gaps = db.collect_gap()
    assert list(gaps.columns) == ["prev_at", "run_at", "gap_min"] and (gaps.gap_min > 70).all()
    assert len(db.load_log(5)) <= 5


# MySQL은 숫자 열과 문자열을 비교할 때 앞쪽 숫자만 읽는다('1 OR 1=1' → 1). 그래서 앞 숫자가 실제 complex_id(150~)와
# 겹치지 않는 값만 쓴다. SQL로 해석됐다면 모든 행이 나오거나 테이블이 지워졌을 것이다.
INJECTION = ["1 OR 1=1", "0; DROP TABLE outage; --", "' OR '1'='1", "-1 UNION SELECT * FROM load_log -- "]


@pytest.mark.parametrize("payload", INJECTION)
def test_parameterized_query_is_not_injectable(payload):
    # 매개변수로 전달된 값은 SQL로 해석되지 않는다: 문자열 그대로 비교되어 0행
    n_outage = int(db.query("SELECT COUNT(*) AS n FROM outage").n.iloc[0])
    assert db.closures(payload).empty
    assert db.elevators(payload).empty
    assert db.profile(payload).empty
    assert db.elevator_history(payload).empty
    # 요일구분에 넣으면 LEFT JOIN 조건만 거짓이 되어 노인 이용이 모두 비어 나온다
    assert db.down_now(payload, 9).senior_at_hour.isna().all()
    # 테이블이 그대로 남아 있다
    assert int(db.query("SELECT COUNT(*) AS n FROM outage").n.iloc[0]) == n_outage


# ───────────────────────── 화면(AppTest)
def test_app_renders_each_view_without_exception():
    at = run_app()
    assert not at.exception
    sc = at.segmented_control[0]
    assert [o.content for o in sc.proto.options] == VIEWS
    assert sc.value == "교통약자" and not at.tabs  # 탭 대신 화면 선택(선택한 화면만 실행)
    at.selectbox[0].select(3).run()
    at.selectbox[1].select("충무로").run()
    assert not at.exception
    assert "충무로 역사" in texts(at)
    assert "이동 횟수" in texts(at)  # 단위 문구: 승차+하차 합계는 사람 수가 아님

    at.segmented_control[0].set_value("역 관리자").run()
    assert not at.exception
    page = texts(at)
    assert "시작 시각을 아는" in page and "추정치" in page and "2025년" in page
    assert any(m.label == "시작 시각 모름(누적)" for m in at.metric)
    assert not at.text_input  # 교통약자 화면 위젯은 실행되지 않았다

    at.segmented_control[0].set_value("데이터·수집 현황").run()
    assert not at.exception
    assert "수집 공백" in texts(at)
    if not db.collect_gap().empty:
        assert len(at.dataframe) >= 2  # 공백 표 + 적재 기록


def test_station_search_and_complex_without_elevators():
    no_elev = db.query(
        "SELECT s.station_nm, s.line_no FROM station s WHERE NOT EXISTS (SELECT 1 FROM station s2 "
        "JOIN elevator e ON e.station_no = s2.station_no WHERE s2.complex_id = s.complex_id) LIMIT 1")
    at = run_app()
    at.text_input[0].input("충무").run()
    assert not at.exception
    assert at.selectbox[0].options == ["충무로 (3호선)", "충무로 (4호선)"]
    at.text_input[0].input("없는역이름").run()
    assert not at.exception and any("없습니다" in w.value for w in at.warning)
    if not no_elev.empty:
        pick(at, no_elev.iloc[0])
        assert any("승강기" in i.value and "정보가 없습니다" in i.value for i in at.info)


def test_selection_survives_view_switch():
    """화면을 바꿨다 돌아와도 검색어·검색 결과 선택·호선/역 선택·요일이 유지된다(Streamlit은 그리지 않은 위젯 상태를 지운다)."""
    at = run_app()
    at.text_input[0].input("충무").run()
    at.selectbox[0].select_index(1).run()  # 충무로 (4호선)
    at.radio[0].set_value("주말").run()
    chosen = at.selectbox[0].value
    assert not at.exception and at.selectbox[0].options == ["충무로 (3호선)", "충무로 (4호선)"]

    at.segmented_control[0].set_value("역 관리자").run()
    assert not at.exception and not at.text_input
    at.radio[0].set_value("주말").run()  # 관리자 화면의 기준 요일
    at.selectbox[0].select_index(1).run()  # 이력 역사 선택
    hist = at.selectbox[0].value
    at.segmented_control[0].set_value("교통약자").run()
    assert not at.exception
    assert at.text_input[0].value == "충무"
    assert at.selectbox[0].value == chosen
    assert at.radio[0].value == "주말"
    assert "충무로 역사" in texts(at)

    # 검색어를 지우고 호선·역으로 고른 경우도 유지
    at.text_input[0].input("").run()
    at.selectbox[0].select(3).run()
    at.selectbox[1].select_index(2).run()
    name = at.selectbox[1].value
    at.segmented_control[0].set_value("데이터·수집 현황").run()
    at.segmented_control[0].set_value("교통약자").run()
    assert not at.exception
    assert at.selectbox[0].value == 3 and at.selectbox[1].value == name and at.selectbox[1].index == 2

    at.segmented_control[0].set_value("역 관리자").run()
    assert at.radio[0].value == "주말" and at.selectbox[0].value == hist


def test_stopped_elevator_is_emphasized():
    dn = db.down_now("평일", 9)
    if dn.empty:
        pytest.skip("지금 비가동 승강기가 없다")
    at = run_app()
    pick(at, db.stations().query("complex_id == @dn.complex_id.iloc[0]").iloc[0])
    assert any("지금 멈춘 승강기" in e.value for e in at.error)
    assert any(m.delta and "멈춤" in m.delta for m in at.metric)  # 색 외에 글자로도 표시


def test_empty_data_guards(monkeypatch):
    """수집 기록 없음(NaT)·빈 프로필·승강기 없음에서도 예외 없이 안내 문구를 낸다."""
    empty_ev = db.elevators(-1)
    monkeypatch.setattr(db, "collect_period", lambda: {"first_at": None, "last_at": None, "n_snapshots": 0})
    monkeypatch.setattr(db, "elevators", lambda cid: empty_ev)
    monkeypatch.setattr(db, "profile", lambda cid: db.query(
        "SELECT day_type, hour_slot, avg_all, avg_senior, avg_senior AS senior_pct FROM ridership_profile WHERE 1 = 0"))
    st.cache_data.clear()
    try:
        at = run_app()
        assert not at.exception
        assert any("수집 기록이 아직 없습니다" in w.value for w in at.warning)
        page = texts(at)
        assert "승강기(엘리베이터·에스컬레이터) 정보가 없습니다" in page
        assert "승하차 기록이 없어" in page
        for v in VIEWS[1:]:
            at.segmented_control[0].set_value(v).run()
            assert not at.exception, v
    finally:
        st.cache_data.clear()  # 가짜 데이터가 다른 테스트 캐시에 남지 않게
