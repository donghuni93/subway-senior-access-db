"""인수인계 읽기 가이드 (Streamlit). DB·인증키 없이 문서·코드·결과를 훑어본다.

실행: uv run streamlit run 03_본프로젝트/05_코드/guide_app.py --server.port 8502
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from guide_catalog import DOCS, LINKS, READING_ORDER

st.set_page_config(page_title="인수인계 읽기 가이드", page_icon="📖", layout="wide")

HOME = "🏠 시작하기"
LANG = {"code": "python", "sql": "sql"}


def read_text(doc) -> str:
    return doc.file.read_text(encoding="utf-8-sig")


def show_home() -> None:
    st.title("📖 인수인계 읽기 가이드")
    st.caption("지하철 고령 이용·승강기 정보 시스템 (엔지니어링DB 텀프로젝트)")
    st.subheader("읽는 순서")
    for i, step in enumerate(READING_ORDER, 1):
        st.markdown(f"{i}. {step}")
    st.subheader("자료 링크")
    for group in dict.fromkeys(g for g, *_ in LINKS):
        with st.expander(group, expanded=group in ("팀", "실행")):
            for g, name, url, desc in LINKS:
                if g == group:
                    st.markdown(f"- [{name}]({url}) — {desc}")
    st.subheader("전체 문서")
    st.dataframe(
        pd.DataFrame([{"분류": d.group, "제목": d.title, "파일": d.path, "설명": d.desc} for d in DOCS]),
        hide_index=True, width="stretch",
    )


def show_doc(doc) -> None:
    st.header(doc.title)
    st.caption(f"`{doc.path}` · {doc.desc}")
    if not doc.file.exists():
        st.warning("파일이 없습니다.")
    elif doc.kind == "md":
        st.markdown(read_text(doc))
    elif doc.kind in LANG:
        st.code(read_text(doc), language=LANG[doc.kind], line_numbers=True)
    elif doc.kind == "image":
        st.image(str(doc.file), width="stretch")
    elif doc.kind == "csv":
        try:
            st.dataframe(pd.read_csv(doc.file, encoding="utf-8-sig"), hide_index=True, width="stretch")
        except pd.errors.EmptyDataError:
            st.warning("빈 파일입니다.")


def main() -> None:
    with st.sidebar:
        st.title("📖 읽기 가이드")
        query = st.text_input("제목·파일명 검색", placeholder="예: 정규화, analysis")
        groups = list(dict.fromkeys(d.group for d in DOCS))
        group = st.selectbox("분류", [HOME, *groups])
        q = query.strip().lower()
        active = bool(q) or group != HOME  # 검색하거나 분류를 고르면 목록을 보인다
        docs = [d for d in DOCS if (group == HOME or d.group == group) and q in f"{d.title}\n{d.path}".lower()]
        doc = None
        if active and docs:
            doc = st.radio("문서", docs, format_func=lambda d: d.title)
        elif active:
            st.info("일치하는 문서가 없습니다.")
    if doc:
        show_doc(doc)
    else:
        show_home()


main()
