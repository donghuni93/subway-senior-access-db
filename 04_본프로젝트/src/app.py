"""서울 지하철 고령 이용·승강기 정보 대시보드 (Streamlit).

실행: uv run streamlit run 04_본프로젝트/src/app.py
모든 조회는 src/db.py의 매개변수 질의(삽입 SQL)를 거친다. 색·글꼴·간격은 src/theme.py 토큰을 쓴다.
화면 선택 컨트롤로 고른 화면 하나만 실행한다(탭은 세 화면을 매번 모두 실행).
"""

from __future__ import annotations

from datetime import datetime

import altair as alt
import db
import pandas as pd
import streamlit as st
import theme

st.set_page_config(page_title="지하철 고령 이용·승강기 정보", page_icon="🛗", layout="wide")

TTL = 600  # 수집은 매시 1회. 10분 캐시면 새 스냅샷이 늦어도 10분 안에 반영된다
VIEWS = ["교통약자", "역 관리자", "데이터·수집 현황"]
KIND = {"EV": "엘리베이터", "ES": "에스컬레이터"}
STATUS_ICON = {"사용가능": "✅ 사용가능", "보수중": "⛔ 보수중"}
SLOT_ORDER = [db.slot_label(s) for s in range(5, 25)]
MOVES = "승차+하차 합계(이동 횟수)이며 사람 수가 아니다"

# ───────────────────────── 캐시된 조회(같은 인자는 TTL 동안 DB에 다시 묻지 않음)
stations = st.cache_data(ttl=TTL)(db.stations)
profile = st.cache_data(ttl=TTL)(db.profile)
elevators = st.cache_data(ttl=TTL)(db.elevators)
closures = st.cache_data(ttl=TTL)(db.closures)
down_now = st.cache_data(ttl=TTL)(db.down_now)
period = st.cache_data(ttl=TTL)(db.collect_period)
cluster = st.cache_data(ttl=TTL)(db.cluster_latest)
cluster_run = st.cache_data(ttl=TTL)(db.cluster_run_latest)
complex_outage = st.cache_data(ttl=TTL)(db.complex_outage)
outage_summary = st.cache_data(ttl=TTL)(db.outage_summary)
outage_daily = st.cache_data(ttl=TTL)(db.outage_daily)
exposure = st.cache_data(ttl=TTL)(db.complex_exposure)
history = st.cache_data(ttl=TTL)(db.elevator_history)
collect_gap = st.cache_data(ttl=TTL)(db.collect_gap)
hourly_total = st.cache_data(ttl=TTL)(db.hourly_total)
load_log = st.cache_data(ttl=TTL)(db.load_log)


# ───────────────────────── 표시 도우미
def fmt_ts(ts, fmt: str = "%m/%d %H:%M") -> str:
    return "-" if ts is None or pd.isna(ts) else pd.Timestamp(ts).strftime(fmt)


def status_label(s: str) -> str:
    return STATUS_ICON.get(s, f"⛔ {s}")


def start_label(known) -> str:
    return "모름(처음 확인 때 이미 멈춤·공백 직후)" if known == 0 else "확인"


# ───────────────────────── 화면을 오가도 선택 유지
# Streamlit은 이번 실행에서 그리지 않은 위젯의 상태를 지운다. 그래서 화면을 바꿨다 돌아오면 검색어·역 선택이
# 처음 값으로 돌아간다. 위젯 키와 별도인 'keep_<키>'에 값을 보관했다가 위젯을 만들기 전에 되살린다.
def restore(key: str, default, options: list | None = None) -> None:
    """위젯을 만들기 전에 호출: 지워진 위젯 상태를 보관값으로 채우고, 선택지에 없는 값이면 기본값으로 둔다."""
    if key not in st.session_state:
        st.session_state[key] = st.session_state.get(f"keep_{key}", default)
    if options is not None and st.session_state[key] not in options:
        st.session_state[key] = default


def keep(key: str):
    """위젯을 만든 뒤 호출: 현재 값을 보관하고 그대로 돌려준다."""
    st.session_state[f"keep_{key}"] = st.session_state[key]
    return st.session_state[key]


def metric_row(items: list[tuple]) -> None:
    """지표 타일 줄: (이름, 값, 도움말[, 경고 문구]). 고정 폭 타일이 화면 폭에 맞춰 줄바꿈된다(좁은 화면에서 한 줄에 하나).

    경고 문구는 색만으로 구분하지 않도록 아이콘·글자로 쓰고, 화살표는 끈다.
    """
    with st.container(horizontal=True, gap="medium"):
        for label, value, help_, *alert in items:
            st.metric(label, value, delta=alert[0] if alert else None, delta_color="red", delta_arrow="off",
                      help=help_, border=True, width=260)


def csv_button(df: pd.DataFrame, name: str, key: str) -> None:
    """CSV 내려받기. 승강기 이름 등 원본 문자열이 수식으로 실행되지 않게 db.csv_safe를 거친다."""
    data = db.csv_safe(df).to_csv(index=False).encode("utf-8-sig")
    st.download_button("CSV 내려받기", data, file_name=f"{name}.csv",
                       mime="text/csv", key=key, on_click="ignore", icon=":material/download:")


def hour_chart(prof: pd.DataFrame, day_type: str, highlight: int | None) -> alt.Chart:
    """시간대별 평균 이동: 노인 / 그 외를 쌓은 막대(같은 단위, 축 하나). 지금 시간대는 위에 표시."""
    t = theme.tokens()
    p = prof[prof.day_type == day_type].copy()
    p["시간대"] = p.hour_slot.astype(int).map(db.slot_label)
    p["노인"] = p.avg_senior.astype(float).round()
    p["그 외"] = (p.avg_all.astype(float) - p.avg_senior.astype(float)).clip(lower=0).round()
    p["노인 비중(%)"] = p.senior_pct.astype(float)
    long = p.melt(id_vars=["시간대", "hour_slot", "노인 비중(%)"], value_vars=["노인", "그 외"],
                  var_name="구분", value_name="평균 이동")
    bars = alt.Chart(long).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, stroke=t["surface"],
                                    strokeWidth=1.5).encode(
        x=alt.X("시간대:N", sort=SLOT_ORDER, axis=theme.axis(None, labelAngle=0, labelOverlap="greedy")),
        y=alt.Y("평균 이동:Q", stack="zero", axis=theme.axis("하루 평균 이동 횟수(승차+하차)")),
        color=alt.Color("구분:N", scale=alt.Scale(domain=["노인", "그 외"], range=[t["senior"], t["others"]]),
                        legend=theme.legend_top()),
        order=alt.Order("구분:N", sort="descending"),  # 노인을 기준선 쪽에
        tooltip=["시간대", "구분", alt.Tooltip("평균 이동:Q", title="평균 이동(회)", format=",.0f"), "노인 비중(%)"],
    )
    if highlight is None or highlight not in set(p.hour_slot.astype(int)):
        return bars.properties(height=280)
    tops = p[p.hour_slot == highlight].assign(합계=lambda d: d["노인"] + d["그 외"])
    mark = alt.Chart(tops).mark_text(dy=-8, fontSize=theme.CHART_FONT, fontWeight="bold", color=t["text"]).encode(
        x=alt.X("시간대:N", sort=SLOT_ORDER), y="합계:Q", text=alt.value("▼ 지금"))
    return (bars + mark).properties(height=280)


# ───────────────────────── 공통: 수집 신선도
def freshness_banner() -> None:
    p = period()
    now = datetime.now()
    if p.get("last_at") is None or pd.isna(p.get("last_at")):
        st.warning("⚠️ 승강기 가동현황 수집 기록이 아직 없습니다. 승강기 상태는 표시되지 않거나 비어 있을 수 있습니다.")
    elif db.is_stale(p["last_at"], now):
        h = db.hours_since(p["last_at"], now)
        st.warning(f"⚠️ 마지막 수집이 {fmt_ts(p['last_at'])}({h:,.1f}시간 전)입니다. 매시 수집이 멈춰 있어 "
                   "'지금' 상태가 실제와 다를 수 있습니다. 역에 도착하면 안내를 다시 확인하세요.")


# ───────────────────────── 화면 1: 교통약자
def pick_station(sts: pd.DataFrame) -> tuple[pd.Series, str]:
    """역 검색(글자) 또는 호선·역 선택 → (역 행, 요일구분)."""
    restore("station_q", "")
    st.text_input("역 이름으로 찾기", placeholder="예: 충무로", key="station_q")
    q = keep("station_q").strip()
    cand = sts[sts.station_nm.str.contains(q, regex=False)] if q else sts.iloc[0:0]
    if q and cand.empty:
        st.warning(f"'{q}'(이)가 들어간 역이 없습니다. 아래에서 호선과 역을 골라 주세요.")
    c1, c2, c3 = st.columns(3)
    if not cand.empty:
        found = cand.index.tolist()
        restore("station_pick", found[0], found)
        c1.selectbox(f"검색 결과 {len(cand)}곳", found, key="station_pick",
                     format_func=lambda i: f"{cand.at[i, 'station_nm']} ({cand.at[i, 'line_no']}호선)")
        row = cand.loc[keep("station_pick")]
        c2.caption("호선별로 고르려면 검색어를 지우세요.")
    else:
        line_opts = sorted(sts.line_no.unique())
        restore("station_line", line_opts[0], line_opts)
        c1.selectbox("호선", line_opts, format_func=lambda x: f"{x}호선", key="station_line")
        opts = sts[sts.line_no == keep("station_line")]
        names = opts.station_nm.tolist()
        restore("station_name", names[0], names)
        c2.selectbox("역", names, key="station_name")
        row = opts[opts.station_nm == keep("station_name")].iloc[0]
    restore("rider_day", db.day_type_of(datetime.now()), ["평일", "주말"])
    c3.radio("요일", ["평일", "주말"], horizontal=True, key="rider_day")
    return row, keep("rider_day")


def stopped_notice(ev: pd.DataFrame) -> None:
    down = ev[ev.status_now != "사용가능"]
    if down.empty:
        return
    lines = [f"### ⛔ 지금 멈춘 승강기 {len(down)}대", "다른 승강기나 출입구를 이용하세요."]
    for r in down.itertuples():
        since = (f"{fmt_ts(r.down_since)} 이전부터(처음 확인 때 이미 멈춤·공백 직후)" if r.down_start_known == 0
                 else f"{fmt_ts(r.down_since)}부터")
        where = " · ".join(str(x) for x in (r.location, r.section) if x and not pd.isna(x))
        lines.append(f"- **{KIND.get(r.kind, r.kind)}** {r.line_no}호선 {where} ({r.status_now}, {since})")
    st.error("\n".join(lines))


def closure_notice(cl: pd.DataFrame) -> None:
    if cl.empty:
        return
    lines = [f"### 🚧 폐쇄된 출입구 {len(cl)}곳"]
    for r in cl.itertuples():
        until = f"~{fmt_ts(r.end_date, '%m/%d')}" if r.end_date is not None and not pd.isna(r.end_date) else ""
        detour = r.detour if r.detour and not pd.isna(r.detour) else "안내 없음(역 직원에게 문의)"
        lines.append(f"- **{r.place}** 폐쇄{until} → 대체 경로: **{detour}**")
    st.warning("\n".join(lines))


def page_rider() -> None:
    st.subheader("역을 고르면 승강기 상태, 폐쇄 출입구, 시간대별 혼잡 정도를 보여 줍니다")
    sts = stations()
    if sts.empty:
        st.info("역 정보가 없습니다. 데이터 적재(load_db.py)를 먼저 실행하세요.")
        return
    row, day_type = pick_station(sts)
    cid = int(row.complex_id)
    lines = sts[sts.complex_id == cid].line_no.tolist()
    ev = elevators(cid)
    cl = closures(cid)
    prof = profile(cid)
    p = period()
    now = datetime.now()

    st.markdown(f"## {row.complex_nm} 역사 · {', '.join(f'{x}호선' for x in sorted(set(lines)))}")
    st.caption(f"승강기 상태는 {fmt_ts(p.get('last_at'), '%m월 %d일 %H:%M')} 수집 기준(매시 갱신). "
               "환승역은 호선별 승강기를 함께 보여 줍니다.")

    slot = db.hour_slot_of(now)
    cur = prof[(prof.day_type == day_type) & (prof.hour_slot == slot)]
    items = []
    for kind, label in (("EV", "엘리베이터"), ("ES", "에스컬레이터")):
        n = int((ev.kind == kind).sum())
        ok = int(((ev.kind == kind) & (ev.status_now == "사용가능")).sum())
        items.append((f"{label} 사용가능", f"{ok} / {n}대", None, f"⛔ {n - ok}대 멈춤" if ok < n else None))
    items.append(("폐쇄 출입구", f"{len(cl)}곳", None))
    senior_now = "-" if cur.empty or pd.isna(cur.avg_senior.iloc[0]) else f"{float(cur.avg_senior.iloc[0]):,.0f}회"
    items.append((f"지금({db.slot_label(slot)}) 평소 노인 이동", senior_now,
                  f"2025년 {day_type} 같은 시간대 하루 평균. {MOVES}."))
    metric_row(items)

    if ev.empty:
        st.info("이 역사에는 등록된 승강기(엘리베이터·에스컬레이터) 정보가 없습니다. 이동이 어려우면 역 직원 호출을 이용하세요.")
    stopped_notice(ev)
    closure_notice(cl)
    if not ev.empty and (ev.status_now == "사용가능").all() and cl.empty:
        st.success("✅ 지금 멈춘 승강기와 폐쇄된 출입구가 없습니다.")

    if not ev.empty:
        st.markdown("#### 승강기 목록")
        show = ev.assign(상태=ev.status_now.map(status_label), 종류=ev.kind.map(KIND))
        st.dataframe(show[["상태", "종류", "line_no", "location", "section", "elevator_nm"]].rename(
            columns={"line_no": "호선", "location": "위치", "section": "구간", "elevator_nm": "이름"}),
            hide_index=True, width="stretch", height=min(38 + 35 * len(show), 400))
    if not cl.empty:
        st.markdown("#### 출입구 임시폐쇄")
        st.dataframe(cl.rename(columns={"station_nm": "역", "line_no": "호선", "place": "폐쇄 장소", "start_date": "시작일",
                                        "end_date": "종료일", "reason": "사유", "detour": "대체 경로"}),
                     hide_index=True, width="stretch")

    st.markdown(f"#### 시간대별 평소 이동({day_type}, 2025년 평균)")
    day_prof = prof[prof.day_type == day_type]
    if day_prof.empty:
        st.info("이 역사의 2025년 승하차 기록이 없어 시간대별 혼잡 정도를 보여 드릴 수 없습니다.")
        return
    st.altair_chart(hour_chart(prof, day_type, slot), width="stretch")
    st.caption(f"파란색 계열이 노인, 회색이 그 외 이동입니다. 막대 값은 {MOVES}.")
    quiet = day_prof[day_prof.hour_slot.between(9, 18)].sort_values("avg_all").head(3)
    if not quiet.empty:
        st.info("🕘 낮 시간대 중 덜 붐비는 때: **" + ", ".join(db.slot_label(int(s)) for s in quiet.hour_slot) + "**")


# ───────────────────────── 화면 2: 역 관리자
def page_manager() -> None:
    st.subheader("비가동 승강기 영향과 우선 관리 역사")
    t = theme.tokens()
    now = datetime.now()
    c1, c2 = st.columns(2)
    restore("mgr_day", db.day_type_of(now), ["평일", "주말"])
    c1.radio("기준 요일", ["평일", "주말"], horizontal=True, key="mgr_day")
    day_type = keep("mgr_day")
    restore("mgr_slot", db.hour_slot_of(now), list(range(5, 25)))
    c2.select_slider("기준 시간대", options=list(range(5, 25)), format_func=db.slot_label, key="mgr_slot")
    slot = keep("mgr_slot")
    dn = down_now(day_type, slot)
    p = period()
    summ = outage_summary()
    hours = db.hours_since(p.get("first_at"), p.get("last_at"))
    n_ev = int((dn.kind == "EV").sum())
    metric_row([
        ("지금 비가동 승강기", f"{len(dn)}대", f"엘리베이터 {n_ev}대 · 에스컬레이터 {len(dn) - n_ev}대"),
        ("그중 엘리베이터", f"{n_ev}대", None),
        ("비가동이 있는 역사", f"{dn.complex_id.nunique()}곳", None),
        ("시작 시각 모름(누적)", f"{summ['n_unknown']}건",
         ("처음 확인했을 때 이미 멈춰 있었거나 수집 공백 직후에 확인되어 실제 시작 시각을 모르는 비가동 구간. "
          "통계·추이·누적에서 뺀다.")),
        ("승강기 수집 기간", "-" if hours is None else f"{hours:,.0f}시간", f"매시 스냅샷 {p.get('n_snapshots', 0)}회"),
    ])
    st.caption(f"비가동 구간 {summ['n_all']}건 중 시작 시각을 아는 {summ['n_known']}건만 통계(추이·누적·영향 추정)에 씁니다. "
               f"모르는 {summ['n_unknown']}건은 처음 확인했을 때 이미 멈춰 있었거나 수집 공백 직후에 확인된 것으로, "
               "지속 시간이 실제보다 짧게(하한값) 잡혀 "
               "통계에 넣으면 편향됩니다. 현재 상태(지금 비가동)에는 모두 포함합니다.")

    # ① 지금 비가동
    st.markdown(f"#### ① 지금 비가동인 승강기 — {day_type} {db.slot_label(slot)} 역사 평균 노인 이동 순")
    if dn.empty:
        st.success("✅ 지금 비가동인 승강기가 없습니다.")
    else:
        t1 = pd.DataFrame({
            "역사": dn.complex_nm, "종류": dn.kind.map(KIND), "위치": dn.location, "승강기": dn.elevator_nm,
            "비가동 확인 시각": dn.down_since, "시작 시각": dn.down_start_known.map(start_label),
            "지속(시간)": dn.down_hours, "해당 시간대 역사 노인 이동(회)": dn.senior_at_hour.astype(float).round(),
        })
        st.dataframe(t1, hide_index=True, width="stretch", height=320)
        st.caption("노인 이동은 2025년 같은 요일구분·시간대의 역사 전체 평균(승차+하차)으로, 이 승강기를 실제로 이용한 "
                   "인원이 아니라 영향 규모를 비교하는 추정치입니다. 시작 시각이 '모름'인 구간의 지속 시간은 하한값입니다.")
        csv_button(t1, "지금_비가동_승강기", "dl_down")

    # ② 영향 규모 추정
    st.markdown("#### ② 역사별 비가동 영향 규모(노출) 추정 — 시작 시각을 아는 비가동만")
    ex = exposure(20)
    if ex.empty:
        st.info("시작 시각을 아는 비가동 기록이 아직 없습니다.")
    else:
        ex_show = ex.rename(columns={"complex_nm": "역사", "n_outage": "비가동(건)", "n_outage_ev": "그중 엘리베이터(건)",
                                     "outage_slot_hours": "비가동 시간대 수(시간)",
                                     "senior_exposed": "노출 추정(노인 이동 횟수)"}).drop(columns="complex_id")
        chart = alt.Chart(ex.head(15)).mark_bar(color=t["senior"], cornerRadiusTopRight=4,
                                                cornerRadiusBottomRight=4).encode(
            x=alt.X("senior_exposed:Q", axis=theme.axis("노출 추정(비가동 시간대의 노인 이동 합, 회)")),
            y=alt.Y("complex_nm:N", sort="-x", axis=theme.axis(None, labelOverlap=False)),
            tooltip=[alt.Tooltip("complex_nm", title="역사"),
                     alt.Tooltip("senior_exposed", title="노출 추정(회)", format=",.0f"),
                     alt.Tooltip("n_outage", title="비가동(건)"), alt.Tooltip("outage_slot_hours", title="시간대 수")],
        ).properties(height=26 * min(len(ex), 15) + 40)
        st.altair_chart(chart, width="stretch")
        st.dataframe(ex_show, hide_index=True, width="stretch")
        st.caption("추정 방법: 비가동 구간을 1시간 단위로 펼쳐, 각 시각의 요일구분·시간대에 해당하는 역사 평균 노인 이동"
                   "(승차+하차)을 더했습니다. 이용 프로필은 2025년, 비가동은 2026년 자료라 시기가 다르고, 승강기별이 아니라 "
                   f"역사 전체 이동이므로 실제 영향 인원이 아닌 상대 비교용입니다. {summ['n_known_gap_overlap']}건은 "
                   "수집 공백과 겹쳐 시각이 공백 길이만큼 부정확할 수 있습니다.")
        csv_button(ex_show, "역사별_노출_추정", "dl_exposure")

    # ③ 일별 추이
    st.markdown("#### ③ 비가동 발생 일별 추이 — 시작 시각을 아는 비가동, 시작일 기준")
    daily = outage_daily()
    if daily.empty:
        st.info("시작 시각을 아는 비가동 기록이 아직 없습니다.")
    else:
        daily = daily.assign(날짜=pd.to_datetime(daily.day).dt.strftime("%m/%d"), 종류=daily.kind.map(KIND))
        trend = alt.Chart(daily).mark_bar(stroke=t["surface"], strokeWidth=1.5, cornerRadiusTopLeft=4,
                                          cornerRadiusTopRight=4).encode(
            x=alt.X("날짜:O", axis=theme.axis(None, labelAngle=0)),
            y=alt.Y("n_outage:Q", stack="zero", axis=theme.axis("새로 시작된 비가동(건)")),
            color=alt.Color("종류:N", scale=theme.categorical(list(KIND.values()), t), legend=theme.legend_top()),
            tooltip=["날짜", "종류", alt.Tooltip("n_outage", title="건수"), alt.Tooltip("hours", title="누적 시간")],
        ).properties(height=240)
        st.altair_chart(trend, width="stretch")
        n_days = daily.day.nunique()
        st.caption(f"수집 {n_days}일치입니다." + (" 아직 기간이 짧아 추세를 판단하기 이릅니다." if n_days < 7 else "")
                   + " 수집 공백 직후 처음 관측된 비가동은 공백 동안 언제 시작했는지 정확히 모릅니다.")

    # ④ 역사별 누적
    st.markdown("#### ④ 역사별 비가동 누적 — 시작 시각을 아는 비가동만")
    co = complex_outage(20)
    if co.empty:
        st.info("시작 시각을 아는 비가동 기록이 아직 없습니다.")
    else:
        bar = alt.Chart(co).mark_bar(color=t["accent"], cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
            x=alt.X("outage_hours:Q", axis=theme.axis("비가동 누적(시간)")),
            y=alt.Y("complex_nm:N", sort="-x", axis=theme.axis(None, labelOverlap=False)),
            tooltip=[alt.Tooltip("complex_nm", title="역사"), alt.Tooltip("outage_hours", title="누적(시간)"),
                     alt.Tooltip("n_outage", title="건수"), alt.Tooltip("n_outage_unknown_start", title="시작 모름(건, 제외)"),
                     alt.Tooltip("n_elevator", title="승강기 수")],
        ).properties(height=26 * len(co) + 40)
        st.altair_chart(bar, width="stretch")
        co_show = co.rename(columns={
            "complex_nm": "역사", "n_elevator": "승강기(대)", "n_ev": "엘리베이터(대)", "n_es": "에스컬레이터(대)",
            "n_outage": "비가동(건)", "outage_hours": "비가동 누적(시간)", "n_down_now": "지금 비가동(대)",
            "hours_per_elevator": "승강기당 비가동(시간)", "n_outage_unknown_start": "시작 모름(건, 제외)",
            "n_outage_ev": "엘리베이터 비가동(건)", "outage_hours_ev": "엘리베이터 비가동(시간)"})
        with st.expander("표로 보기"):
            st.dataframe(co_show, hide_index=True, width="stretch")
        st.caption("매시 수집이라 1시간 단위 근사치입니다. 처음 확인 때 이미 멈춰 있었거나 수집 공백 직후에 확인된 구간은 "
                   "실제 시작을 몰라 "
                   "건수·시간 모두에서 뺐습니다('시작 모름' 열에 따로 표시).")
        csv_button(co_show, "역사별_비가동_누적", "dl_outage")

    # ⑤ 승강기 단위 이력
    st.markdown("#### ⑤ 승강기별 비가동 이력")
    complexes = stations().drop_duplicates("complex_id").sort_values("complex_nm")
    ids = complexes.complex_id.astype(int).tolist()
    names = dict(zip(ids, complexes.complex_nm, strict=True))
    first = int(ex.complex_id.iloc[0]) if not ex.empty else (ids[0] if ids else None)
    if first is None:
        st.info("역사 정보가 없습니다.")
    else:
        restore("hist_cid", first, ids)
        st.selectbox("역사 선택", ids, format_func=lambda i: names[i], key="hist_cid")
        cid = keep("hist_cid")
        h = history(cid)
        if h.empty:
            st.info(f"{names[cid]} 역사는 수집 기간 동안 비가동 기록이 없습니다.")
        else:
            h_show = pd.DataFrame({
                "승강기": h.elevator_nm, "종류": h.kind.map(KIND), "호선": h.line_no, "위치": h.location,
                "상태": h.status, "시작": h.start_at,
                "종료": h.end_at.map(lambda x: "진행 중" if x is None or pd.isna(x) else fmt_ts(x)),
                "지속(시간)": h.hours, "시작 시각": h.start_known.map(start_label),
                "수집 공백 겹침": h.gap_overlap.map({1: "예", 0: "아니오"}),
            })
            st.dataframe(h_show, hide_index=True, width="stretch")
            st.caption("'시작 시각: 모름'이면 시작은 표시보다 이르고 지속 시간은 하한값입니다. '수집 공백 겹침: 예'이면 "
                       "공백(PC 꺼짐 등) 동안의 변화를 관측하지 못해 시각이 부정확할 수 있습니다.")
            csv_button(h_show, f"승강기_비가동_이력_{names[cid]}", "dl_history")

    # ⑥ 군집과 우선 관리
    st.markdown("#### ⑥ 역사 유형(군집 분석)과 우선 관리 역사")
    cr = cluster()
    run = cluster_run()
    if cr.empty or run is None:
        st.info("군집 결과가 없습니다. `python src/analysis.py`를 실행하세요.")
        return
    st.caption(f"분석 회차 {run['run_id']} · {fmt_ts(run['run_at'])} · k={run['k']} · 실루엣 {float(run['silhouette']):.3f} · "
               f"입력 지표: {run['features']}. 우선 관리 점수 = 노인 이용·수직 이동·비가동의 백분위 가중합"
               + ("" if "비가동" in run["features"]
                  else " (이 회차는 비가동 지표를 뺐습니다: 수집 기간이 3일 미만이거나 역사 간 값 차이가 없음)"))
    groups = cr.drop_duplicates("cluster_no").sort_values("cluster_no")
    domain = [f"유형 {r.cluster_no}: {r.cluster_nm}" for r in groups.itertuples()]
    colors = dict(zip(domain, t["series"][: len(domain)], strict=True))
    cr = cr.assign(유형=[f"유형 {r.cluster_no}: {r.cluster_nm}" for r in cr.itertuples()])
    counts = cr.유형.value_counts()
    st.markdown(theme.legend_html([(f"{d} ({counts.get(d, 0)}곳)", colors[d]) for d in domain], t["text_muted"]),
                unsafe_allow_html=True)
    cluster_map(cr.dropna(subset=["lat", "lng"]), colors, t["text_muted"])
    if len(domain) > 3:
        st.caption("유형이 4개 이상이면 일부 색이 비슷해 보일 수 있습니다. 툴팁과 아래 표의 '유형' 열로 확인하세요.")
    top = cr.head(20)[["priority_rank", "complex_nm", "유형", "priority_score", "senior_weekday", "vertical_m", "n_ev",
                       "n_down_now"]].rename(columns={
        "priority_rank": "순위", "complex_nm": "역사", "priority_score": "점수(0~1)",
        "senior_weekday": "평일 노인 이동(회/일)", "vertical_m": "수직 이동(m)", "n_ev": "엘리베이터(대)",
        "n_down_now": "지금 비가동(대)"})
    st.markdown("**우선 관리 역사 상위 20**")
    st.dataframe(top, hide_index=True, width="stretch")
    csv_button(top, "우선_관리_역사_상위20", "dl_priority")
    summary = cr.groupby("유형").agg(역사수=("complex_id", "size"), 평일노인=("senior_weekday", "mean"),
                                     노인비중=("senior_pct", "mean"), 수직이동=("vertical_m", "mean"),
                                     환승초=("max_transfer_sec", "mean")).round(1).reset_index()
    st.markdown("**유형별 평균**")
    st.dataframe(summary.rename(columns={"역사수": "역사(곳)", "평일노인": "평일 노인 이동(회/일)", "노인비중": "노인 비중(%)",
                                         "수직이동": "수직 이동(m)", "환승초": "최대 환승(초)"}),
                 hide_index=True, width="stretch")
    st.caption(f"평일 노인 이동은 {MOVES}.")


def cluster_map(df: pd.DataFrame, colors: dict[str, str], stroke: str) -> None:
    """역사 위치 지도: 점 색 = 유형, 크기 = 평일 노인 이동. pydeck이 없으면 st.map으로 대신한다.
    배경 대비가 낮은 범주 색도 경계가 보이도록 점 테두리는 stroke(text_muted 토큰)로 그린다."""
    if df.empty:
        st.info("위치 정보가 있는 역사가 없습니다.")
        return
    senior = df.senior_weekday.astype(float).fillna(0)
    peak = float(senior.max()) or 1.0
    m = df.assign(radius=150 + 650 * (senior / peak) ** 0.5, color=df.유형.map(colors),
                  label=df.유형, senior_txt=senior.map(lambda v: f"{v:,.0f}"))
    try:
        import pydeck as pdk
    except ImportError:
        st.map(m, latitude="lat", longitude="lng", color="color", size="radius", height=440)
        return
    m["rgba"] = m.color.map(lambda h: [int(h[i: i + 2], 16) for i in (1, 3, 5)] + [220])
    layer = pdk.Layer("ScatterplotLayer", data=m[["lat", "lng", "radius", "rgba", "complex_nm", "label",
                                                  "priority_rank", "senior_txt"]],
                      get_position="[lng, lat]", get_radius="radius", get_fill_color="rgba",
                      stroked=True, get_line_color=[int(stroke[i: i + 2], 16) for i in (1, 3, 5)],
                      line_width_min_pixels=1,
                      radius_min_pixels=3, pickable=True)
    view = pdk.ViewState(latitude=float(m.lat.mean()), longitude=float(m.lng.mean()), zoom=10)
    tip = {"text": "{complex_nm}\n{label}\n우선 순위 {priority_rank}위\n평일 노인 이동 {senior_txt}회/일"}
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view, tooltip=tip, map_style=None), height=440)
    st.caption("점 크기는 평일 하루 노인 이동(승차+하차), 색은 유형입니다. 점에 마우스를 올리면 역사 이름과 순위가 보입니다.")


# ───────────────────────── 화면 3: 데이터·수집 현황
def page_data() -> None:
    st.subheader("데이터와 수집 현황")
    p = period()
    gaps = collect_gap()
    now = datetime.now()
    ago = db.hours_since(p.get("last_at"), now)
    metric_row([
        ("승강기 수집 시작", fmt_ts(p.get("first_at")), None),
        ("마지막 수집", fmt_ts(p.get("last_at")), None if ago is None else f"{ago:,.1f}시간 전"),
        ("스냅샷 수", f"{p.get('n_snapshots', 0)}회", None),
        ("수집 공백(70분 초과)", f"{len(gaps)}곳", None),
    ])
    if ago is not None:
        st.caption(f"마지막 수집은 {ago:,.1f}시간 전입니다. {db.STALE_HOURS:.0f}시간을 넘으면 모든 화면 위에 경고가 뜹니다.")
    st.markdown("#### 수집 공백")
    if gaps.empty:
        st.success("✅ 수집 공백(스냅샷 간격 70분 초과)이 없습니다.")
    else:
        g = pd.DataFrame({"마지막 수집": gaps.prev_at, "수집 재개": gaps.run_at,
                          "공백 길이": gaps.gap_min.map(lambda m: f"{int(m) // 60}시간 {int(m) % 60}분")})
        st.dataframe(g, hide_index=True, width="stretch")
        st.caption("공백 동안(PC 꺼짐 등)은 승강기 상태 변화를 관측하지 못했습니다. 이 구간과 겹친 비가동은 시작·종료 시각이 "
                   "공백 길이만큼 부정확할 수 있어 '역 관리자' 화면의 이력에 '수집 공백 겹침'으로 표시합니다.")

    st.markdown("#### 시간대별 노인 이동 비중 (2025년, 1~8호선 전체)")
    ht = hourly_total()
    if ht.empty:
        st.info("승하차 이용 프로필이 없습니다.")
    else:
        t = theme.tokens()
        ht = ht.assign(시간대=ht.hour_slot.astype(int).map(db.slot_label))
        line = alt.Chart(ht).mark_line(point=alt.OverlayMarkDef(size=64), strokeWidth=2).encode(
            x=alt.X("시간대:N", sort=SLOT_ORDER, axis=theme.axis(None, labelAngle=0, labelOverlap="greedy")),
            y=alt.Y("senior_pct:Q", axis=theme.axis("노인 비중(%)")),
            color=alt.Color("day_type:N", scale=theme.categorical(["평일", "주말"], t), legend=theme.legend_top()),
            tooltip=[alt.Tooltip("day_type", title="요일"), "시간대", alt.Tooltip("senior_pct", title="노인 비중(%)"),
                     alt.Tooltip("senior", title="노인 이동(회)", format=",.0f"),
                     alt.Tooltip("total", title="전체 이동(회)", format=",.0f")],
        ).properties(height=280)
        st.altair_chart(line, width="stretch")
        st.caption(f"비중 = 노인 이동 ÷ 전체 이동. 이동은 {MOVES}.")

    st.markdown("#### 최근 적재 기록 (LOAD_LOG)")
    log = load_log(30).rename(columns={"source": "출처", "run_at": "적재 시각", "row_cnt": "행 수", "result": "결과",
                                       "message": "메시지"})
    st.dataframe(log, hide_index=True, width="stretch")
    st.caption("출처: 서울 열린데이터광장·공공데이터포털 서울교통공사 데이터(노인·전체 승하차 2025, 승강기 가동현황, "
               "출입구 임시폐쇄, 역사심도, 환승 거리, 역 정보).")


PAGES = {"교통약자": page_rider, "역 관리자": page_manager, "데이터·수집 현황": page_data}


def main() -> None:
    theme.inject_css()
    st.title("🛗 지하철 고령 이용·승강기 정보")
    freshness_banner()
    view = st.segmented_control("화면 선택", VIEWS, default=VIEWS[0], required=True, key="view")
    PAGES[view or VIEWS[0]]()


main()
