"""대시보드 디자인 토큰과 차트 도우미.

기준: 공공·접근성 정보 서비스(고령·교통약자 이용자, 역 관리자).
- 색은 여기서 한 번만 정의하고 화면(CSS)과 Altair 차트가 같이 쓴다. 밝은·어두운 화면은 같은 색상 계열의 단계를 따로 고른다.
- 대비 기준(WCAG 2.x): 글자 4.5:1 이상, 차트 표식·큰 글자 3:1 이상. tests/test_app.py가 contrast_ratio로 검증한다.
- 상태(멈춤·폐쇄)는 색만으로 구분하지 않고 아이콘과 글자를 같이 쓴다.
- 범주 색은 dataviz 기준 팔레트의 고정 순서를 따른다(순환 금지, 8색 이내).
"""

from __future__ import annotations

import html

import altair as alt
import streamlit as st
from palette import SERIES, SERIES_DARK  # 범주 팔레트 원본(visualize.py와 공유, streamlit 없이 import 가능)

# surface는 Streamlit 기본 배경(밝음 #ffffff, 어두움 #0e1117)
LIGHT = {
    "surface": "#ffffff",
    "text": "#0b0b0b",
    "text_muted": "#52514e",
    "senior": "#1c5cab",  # 노인 이동(강조 계열, 진한 파랑)
    "others": "#8a8984",  # 그 외 이동(중립 회색, 이전 #cde2fb는 흰 배경 대비 1.3:1이라 교체)
    "accent": "#d95926",  # 단일 계열 막대(비가동 누적)
    "series": SERIES,
}
DARK = {
    "surface": "#0e1117",
    "text": "#f0efec",
    "text_muted": "#c3c2b7",
    "senior": "#5598e7",
    "others": "#6f6e69",
    "accent": "#eb6834",
    "series": SERIES_DARK,
}
# 대비 검증 대상: 글자 토큰(4.5:1)과 그래픽 토큰(3:1)
TEXT_TOKENS = ("text", "text_muted")
GRAPHIC_TOKENS = ("senior", "others", "accent")
FOCUS = "#2a78d6"  # 키보드 초점 테두리(두 화면 모두 3:1 이상)

CHART_FONT = 13  # 축 글자 크기(px)


# ───────────────────────── 대비 계산 (WCAG 2.x 상대 휘도)
def _luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    rgb = [int(h[i: i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast_ratio(a: str, b: str) -> float:
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


# ───────────────────────── 화면 테마
def tokens() -> dict:
    """현재 화면 테마(밝음·어두움)에 맞는 토큰. 테마를 알 수 없으면 밝은 화면."""
    return DARK if st.context.theme.type == "dark" else LIGHT


CSS = f"""
<style>
/* 큰 기본 글자와 넉넉한 줄 간격(고령 이용자) */
html {{ font-size: 17px; }}
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {{ line-height: 1.65; }}
[data-testid="stCaptionContainer"] {{ font-size: 0.95rem; line-height: 1.55; }}
[data-testid="stMetricLabel"] p {{ font-size: 1rem; }}
[data-testid="stMetricValue"] {{ font-size: 1.9rem; }}
/* 키보드 초점이 분명히 보이게 */
:focus-visible {{ outline: 3px solid {FOCUS} !important; outline-offset: 2px; }}
[data-testid="stMainBlockContainer"], .block-container {{ max-width: 1240px; padding-top: 2.25rem; }}
/* 지도 범례: 색 원 + 글자 */
.legend {{ display: flex; flex-wrap: wrap; gap: 0.35rem 1.25rem; margin: 0.25rem 0 0.75rem; }}
.legend .sw {{ display: inline-block; width: 0.9em; height: 0.9em; border-radius: 50%;
              margin-right: 0.4em; vertical-align: -0.08em; }}
/* 좁은 화면(휴대전화): 좌우 여백 16px, 제목 축소 */
@media (max-width: 640px) {{
  [data-testid="stMainBlockContainer"], .block-container {{ padding-left: 16px; padding-right: 16px; }}
  h1 {{ font-size: 1.6rem !important; }}
}}
</style>
"""


def inject_css() -> None:
    """정적 스타일만 주입한다(데이터 값을 넣지 않음)."""
    st.markdown(CSS, unsafe_allow_html=True)


# ───────────────────────── 차트 도우미
def axis(title: str | None = None, **kw) -> alt.Axis:
    return alt.Axis(title=title, labelFontSize=CHART_FONT, titleFontSize=CHART_FONT, labelLimit=180, **kw)


def legend_top() -> alt.Legend:
    return alt.Legend(orient="top", title=None, labelFontSize=CHART_FONT, symbolSize=140)


def categorical(domain: list[str], t: dict) -> alt.Scale:
    """범주 색: 고정 순서로 앞에서부터 배정(최대 8)."""
    return alt.Scale(domain=domain, range=t["series"][: len(domain)])


def legend_html(items: list[tuple[str, str]], border: str = LIGHT["text_muted"]) -> str:
    """색 원 + 이름 범례(지도처럼 범례가 없는 차트용). 이름은 이스케이프한다.

    밝은 화면의 범주 색 일부(#1baf7a·#eda100·#e87ba4)는 흰 배경 대비 3:1 미만이라 원에 1px 테두리(text_muted)를 둘러
    경계를 보이게 하고, 유형 구분은 옆 글자로도 한다."""
    spans = "".join(f'<span><span class="sw" style="background:{c};border:1px solid {border}"></span>'
                    f'{html.escape(label)}</span>' for label, c in items)
    return f'<div class="legend">{spans}</div>'
