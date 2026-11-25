"""읽기 가이드(guide_catalog, build_guide_html) 검사. DB 없이 실행된다."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "05_코드"))

import build_guide_html as bg
from guide_catalog import DOCS, Doc


def test_slug_is_ascii_and_unique():
    slugs = [d.slug for d in DOCS]
    assert all(s.isascii() and re.fullmatch(r"[A-Za-z0-9_]+", s) for s in slugs)
    assert len(set(slugs)) == len(slugs)


def test_every_doc_file_exists():
    assert [d.path for d in DOCS if not d.file.exists()] == []


def test_every_internal_link_has_a_section():
    page = bg.build()
    ids = set(re.findall(r'<section id="([^"]+)"', page))
    targets = set(re.findall(r'href="#([^"]+)"', page))
    assert targets <= ids


def test_list_after_paragraph_becomes_html_list():
    out = bg.render_md("**구현**\n- a\n- b")
    assert "<ul>" in out and out.count("<li>") == 2


def test_table_after_paragraph_becomes_html_table():
    assert "<table>" in bg.render_md("설명\n| a | b |\n|---|---|\n| 1 | 2 |")


def test_code_block_content_is_untouched():
    src = "```\n문장\n- 코드 안의 줄\n```"
    assert bg.prep_md(src) == src


def test_empty_csv_does_not_break_build(tmp_path, monkeypatch):
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    doc = Doc("5. 결과", "빈 표", "04_결과/empty.csv", "csv", "테스트")
    monkeypatch.setattr(Doc, "file", property(lambda self: empty))
    assert "빈 파일" in bg.render_doc(doc)
