"""인수인계 읽기 가이드를 파일 하나짜리 HTML로 만든다 (서버·DB·인터넷 없이 더블클릭으로 열림).

실행: uv run python 04_본프로젝트/src/build_guide_html.py [--open]
결과: 04_본프로젝트/output/guide.html
"""

from __future__ import annotations

import base64
import csv
import html
import io
import re
import sys
import webbrowser

import markdown
from guide_catalog import DOCS, LINKS, READING_ORDER, ROOT

OUT = ROOT / "output" / "guide.html"
TOP = ROOT.parent / "읽기가이드.html"  # 저장소 맨 위: 탐색기에서 바로 더블클릭

CSS = """
:root{--bg:#fff;--fg:#1f2328;--mut:#656d76;--line:#d0d7de;--side:#f6f8fa;--acc:#2a78d6;--code:#f6f8fa}
@media(prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--mut:#8b949e;--line:#30363d;--side:#161b22;--acc:#58a6ff;--code:#161b22}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.7 "Malgun Gothic",system-ui,sans-serif;display:flex;min-height:100vh}
nav{width:300px;flex:none;background:var(--side);border-right:1px solid var(--line);padding:16px;position:sticky;top:0;height:100vh;overflow:auto}
nav h1{font-size:17px;margin:0 0 10px}nav input{width:100%;padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg)}
nav h3{font-size:12px;color:var(--mut);margin:16px 0 4px;text-transform:none}
nav a{display:block;padding:3px 8px;border-radius:6px;color:var(--fg);text-decoration:none;font-size:13.5px}
nav a:hover{background:var(--line)}nav a.on{background:var(--acc);color:#fff}
main{flex:1;min-width:0;max-width:980px;padding:24px 32px 80px}
section{display:none}section.on{display:block}
a{color:var(--acc)}h1,h2,h3{line-height:1.3}
table{border-collapse:collapse;display:block;overflow:auto;margin:12px 0}th,td{border:1px solid var(--line);padding:5px 10px;text-align:left;vertical-align:top}th{background:var(--side)}
pre{background:var(--code);border:1px solid var(--line);border-radius:6px;padding:12px;overflow:auto;font-size:13px;line-height:1.5}
code{background:var(--code);padding:1px 5px;border-radius:4px;font-size:.92em}pre code{background:none;padding:0}
blockquote{margin:12px 0;padding:2px 14px;border-left:4px solid var(--line);color:var(--mut)}
img{max-width:100%;height:auto;border:1px solid var(--line);border-radius:6px}
.cap{color:var(--mut);font-size:13px;margin:-6px 0 16px}
@media(max-width:800px){body{display:block}nav{position:static;width:auto;height:auto;max-height:50vh}main{padding:16px}}
"""

JS = """
const secs=[...document.querySelectorAll('section')],links=[...document.querySelectorAll('nav a[data-s]')];
function show(){const id=(location.hash||'#home').slice(1);let hit=false;
 secs.forEach(s=>{const on=s.id===id;s.classList.toggle('on',on);hit=hit||on});
 if(!hit)document.getElementById('home').classList.add('on');
 links.forEach(a=>a.classList.toggle('on',a.dataset.s===id));scrollTo(0,0)}
addEventListener('hashchange',show);show();
document.getElementById('q').addEventListener('input',e=>{const v=e.target.value.toLowerCase();
 links.forEach(a=>a.style.display=(a.textContent.toLowerCase()+' '+a.dataset.k).includes(v)?'':'none');
 document.querySelectorAll('nav h3').forEach(h=>{let n=h.nextElementSibling,any=false;
  while(n&&n.tagName==='A'){if(n.style.display!=='none')any=true;n=n.nextElementSibling}h.style.display=any?'':'none'})});
"""


LIST_LINE = re.compile(r"\s*([-*+] |\d+\. |\|)")


def prep_md(text: str) -> str:
    """Python-Markdown은 문단 바로 뒤의 목록·표를 문단으로 합친다. GitHub처럼 보이도록 빈 줄을 넣는다(코드 블록 제외)."""
    out: list[str] = []
    fence = False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fence = not fence
        elif not fence and LIST_LINE.match(line) and out and out[-1].strip() and not LIST_LINE.match(out[-1]):
            out.append("")
        out.append(line)
    return "\n".join(out)


def render_md(text: str) -> str:
    return markdown.markdown(prep_md(text), extensions=["tables", "fenced_code", "sane_lists"])


def render_doc(d) -> str:
    if not d.file.exists():
        return "<p>파일이 없습니다.</p>"
    if d.kind == "md":
        return render_md(d.file.read_text(encoding="utf-8-sig"))
    if d.kind in ("code", "sql"):
        return f"<pre><code>{html.escape(d.file.read_text(encoding='utf-8-sig'))}</code></pre>"
    if d.kind == "image":
        b64 = base64.b64encode(d.file.read_bytes()).decode()
        return f'<img alt="{html.escape(d.title)}" src="data:image/png;base64,{b64}">'
    rows = list(csv.reader(io.StringIO(d.file.read_text(encoding="utf-8-sig"))))
    if not rows:
        return "<p>빈 파일입니다.</p>"
    head = "".join(f"<th>{html.escape(c)}</th>" for c in rows[0])
    body = "".join("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
    return f"<table><tr>{head}</tr>{body}</table>"


def home() -> str:
    steps = "".join(f"<li>{html.escape(s)}</li>" for s in READING_ORDER)
    parts = []
    for group in dict.fromkeys(g for g, *_ in LINKS):
        items = "".join(
            f'<li><a href="{html.escape(u)}" target="_blank" rel="noopener">{html.escape(n)}</a> — {html.escape(x)}</li>'
            for g, n, u, x in LINKS if g == group)
        parts.append(f"<h3>{html.escape(group)}</h3><ul>{items}</ul>")
    docs = "".join(
        f'<tr><td>{html.escape(d.group)}</td><td><a href="#{d.slug}">{html.escape(d.title)}</a></td>'
        f"<td><code>{html.escape(d.path)}</code></td><td>{html.escape(d.desc)}</td></tr>" for d in DOCS)
    return (f"<h1>📖 인수인계 읽기 가이드</h1><p class='cap'>지하철 고령 이용·승강기 정보 시스템 (엔지니어링DB 텀프로젝트)</p>"
            f"<h2>읽는 순서</h2><ol>{steps}</ol><h2>자료 링크</h2>{''.join(parts)}"
            f"<h2>전체 문서</h2><table><tr><th>분류</th><th>제목</th><th>파일</th><th>설명</th></tr>{docs}</table>")


def build() -> str:
    nav = ['<a href="#home" data-s="home">🏠 시작하기</a>']
    secs = [f'<section id="home">{home()}</section>']
    last = None
    for d in DOCS:
        if d.group != last:
            nav.append(f"<h3>{html.escape(d.group)}</h3>")
            last = d.group
        nav.append(f'<a href="#{d.slug}" data-s="{d.slug}" data-k="{html.escape(d.path.lower())}">{html.escape(d.title)}</a>')
        try:
            body = render_doc(d)
        except (OSError, UnicodeDecodeError, csv.Error) as e:  # 문서 하나 때문에 전체 빌드가 멈추지 않게 한다
            body = f"<p>이 문서를 읽지 못했습니다: {html.escape(str(e))}</p>"
        secs.append(f'<section id="{d.slug}"><h1>{html.escape(d.title)}</h1>'
                    f'<p class="cap"><code>{html.escape(d.path)}</code> · {html.escape(d.desc)}</p>{body}</section>')
    return ('<!doctype html><html lang="ko"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1"><title>인수인계 읽기 가이드</title>'
            f"<style>{CSS}</style></head><body><nav><h1>📖 읽기 가이드</h1>"
            f'<input id="q" placeholder="제목 검색" aria-label="제목 검색">{"".join(nav)}</nav>'
            f"<main>{''.join(secs)}</main><script>{JS}</script></body></html>")


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    TOP.write_bytes(OUT.read_bytes())
    print(f"만들었습니다: {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")
    print(f"저장소 맨 위 복사본: {TOP}")
    if "--open" in sys.argv:
        webbrowser.open(TOP.as_uri())
