"""MySQL information_schema에서 테이블·열·키·외래키를 읽어 ERD를 그린다 (matplotlib).

출력: design/ERD.png
사용: python src/draw_erd.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import myloginpath
import pymysql
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

PROJECT_DIR = Path(__file__).resolve().parents[1]
OUT = PROJECT_DIR / "design" / "ERD.png"
DB = "subway_access_db"

# 표시 위치 (열, 행): 부모를 가운데에 둔다
LAYOUT = {
    # 윗줄: 분석 회차 · 역사 · 역 · 승강기 · 비가동
    "cluster_run": (0, 0),
    "cluster_type": (0, 0.55),  # 회차 아래, 결과 위
    "station_complex": (1, 0),
    "station": (2, 0),
    "elevator": (3, 0),
    "line": (3, 0.62),  # 승강기 아래 빈 자리
    "outage": (4, 0),
    "load_log": (4, 0.5),  # 관계 없는 관리용 테이블
    # 아랫줄: 각 부모 바로 아래에 자식을 둔다
    "cluster_result": (0, 1),
    "ridership_profile": (1, 1),
    "transfer": (2, 1),
    "ridership": (3, 1),
    "exit_closure": (4, 1),
}
COL_W, ROW_H, LINE_H, BOX_W = 4.6, 6.2, 0.33, 4.0


def set_korean_font() -> None:
    for name in ("Malgun Gothic", "AppleGothic", "NanumGothic"):
        if any(f.name == name for f in font_manager.fontManager.ttflist):
            plt.rcParams["font.family"] = name
            break
    plt.rcParams["axes.unicode_minus"] = False


def read_schema():
    conn = pymysql.connect(**myloginpath.parse("endb"), database="information_schema", charset="utf8mb4")
    with conn.cursor() as cur:
        cur.execute(
            "SELECT table_name, column_name, column_type, column_key, is_nullable FROM columns "
            "WHERE table_schema=%s ORDER BY table_name, ordinal_position",
            (DB,),
        )
        cols = cur.fetchall()
        cur.execute(
            "SELECT table_name, column_name, referenced_table_name FROM key_column_usage "
            "WHERE table_schema=%s AND referenced_table_name IS NOT NULL",
            (DB,),
        )
        fks = cur.fetchall()
    conn.close()
    tables: dict[str, list[tuple]] = {}
    for t, c, typ, key, nullable in cols:
        tables.setdefault(t, []).append((c, typ, key, nullable))
    return tables, fks


def main() -> None:
    set_korean_font()
    tables, fks = read_schema()
    fk_cols = {(t, c) for t, c, _ in fks}

    fig, ax = plt.subplots(figsize=(23, 11))
    boxes = {}
    for t, (cx, cy) in LAYOUT.items():
        if t not in tables:
            continue
        rows = tables[t]
        h = (len(rows) + 1) * LINE_H + 0.2
        x, y_top = cx * COL_W, -cy * ROW_H
        ax.add_patch(FancyBboxPatch((x, y_top - h), BOX_W, h, boxstyle="round,pad=0.02", fc="white", ec="#334155", lw=1.4))
        ax.add_patch(FancyBboxPatch((x, y_top - LINE_H - 0.1), BOX_W, LINE_H + 0.1, boxstyle="round,pad=0.02",
                                    fc="#1e3a5f", ec="#1e3a5f"))
        ax.text(x + BOX_W / 2, y_top - LINE_H / 2 - 0.05, t.upper(), ha="center", va="center", color="white",
                fontsize=11, fontweight="bold")
        for i, (c, typ, key, nullable) in enumerate(rows):
            y = y_top - (i + 1.5) * LINE_H - 0.1
            tags = []
            if key == "PRI":
                tags.append("PK")
            if (t, c) in fk_cols:
                tags.append("FK")
            if key == "UNI":
                tags.append("UK")
            weight = "bold" if key == "PRI" else "normal"
            ax.text(x + 0.12, y, ("·".join(tags)).ljust(5), fontsize=8, color="#b45309", va="center", family="monospace")
            ax.text(x + 0.75, y, c, fontsize=9, va="center", fontweight=weight)
            ax.text(x + BOX_W - 0.1, y, typ.replace(" unsigned", "") + ("" if nullable == "NO" else " ?"),
                    fontsize=7.5, va="center", ha="right", color="#64748b")
        boxes[t] = (x, y_top, h)

    # 외래키 선: 자식 상자 → 부모 상자 (부모 쪽 1, 자식 쪽 N)
    seen = set()
    for child, _, parent in fks:
        if (child, parent) in seen or child not in boxes or parent not in boxes:
            continue
        seen.add((child, parent))
        cx, cy, _ = boxes[child]
        px, py, ph = boxes[parent]
        c_pt = (cx + BOX_W / 2, cy) if cy < py - ph else (cx if cx > px else cx + BOX_W, cy - 0.5)
        p_pt = (px + BOX_W / 2, py - ph) if cy < py - ph else (px + BOX_W if cx > px else px, py - 0.5)
        ax.annotate("", xy=p_pt, xytext=c_pt, arrowprops={"arrowstyle": "-|>", "color": "#0f766e", "lw": 1.3,
                                                          "connectionstyle": "arc3,rad=0.08"})
        ax.text(c_pt[0], c_pt[1] + 0.12, "N", fontsize=9, color="#0f766e", fontweight="bold")
        ax.text(p_pt[0], p_pt[1] - 0.3, "1", fontsize=9, color="#0f766e", fontweight="bold")

    ax.set_xlim(-0.4, 5 * COL_W)
    ax.set_ylim(min(y - h for _, y, h in boxes.values()) - 0.5, 0.6)
    ax.axis("off")
    ax.set_title(f"{DB} ERD  (PK 기본키 · FK 외래키 · UK 유일키 · ? NULL 허용, 화살표는 자식→부모 N:1)", fontsize=13)
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=150, facecolor="white")
    print(OUT)


if __name__ == "__main__":
    main()
