"""질의·분석 결과 시각화 → output/*.png (보고서·발표용 정적 그림)

q1_hourly_senior_pct.png  시간대별 노인 비중(평일·주말)
q1_top_complexes.png      평일 노인 이용 상위 15개 역사
q2_outage_top.png         역사별 승강기 비가동 누적 시간 상위 15 (수집 기간)
q3_cluster_map.png        역사 유형 지도(위경도 산점도, 크기 = 노인 이용)
q3_cluster_profile.png    유형별 평균 지표(작은 그림 여러 개)

사용: python src/visualize.py
"""

from __future__ import annotations

from pathlib import Path

import db
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from palette import SERIES  # 대시보드(theme.py)와 같은 범주 팔레트

OUT = Path(__file__).resolve().parents[1] / "output"

# 색: 기준 팔레트(dataviz reference palette, light mode)
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"


def setup() -> None:
    for name in ("Malgun Gothic", "AppleGothic", "NanumGothic"):
        if any(f.name == name for f in font_manager.fontManager.ttflist):
            plt.rcParams["font.family"] = name
            break
    plt.rcParams.update({
        "axes.unicode_minus": False,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": AXIS,
        "axes.labelcolor": INK2,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlecolor": INK,
        "axes.titlelocation": "left",
        "axes.axisbelow": True,  # 격자선은 막대 뒤로
    })


def save(fig, name: str) -> None:
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(OUT / name)


def q1_hourly() -> None:
    df = db.hourly_total()
    fig, ax = plt.subplots(figsize=(9, 4.2))
    for i, day in enumerate(["평일", "주말"]):
        g = df[df.day_type == day].sort_values("hour_slot")
        x, y = g.hour_slot.astype(int), g.senior_pct.astype(float)
        ax.plot(x, y, color=SERIES[i], lw=2, marker="o", ms=4, label=day)
        # 이른 새벽은 이용객이 적어 비중이 부풀려지므로 낮 시간대(9~18시) 최고점을 표시
        day_g = g[g.hour_slot.between(9, 18)]
        peak = day_g.loc[day_g.senior_pct.astype(float).idxmax()]
        ax.annotate(f"{day} 낮 최고 {float(peak.senior_pct):.1f}% ({db.slot_label(int(peak.hour_slot))})",
                    (int(peak.hour_slot), float(peak.senior_pct)), xytext=(8, 8 if i == 0 else -26),
                    textcoords="offset points", fontsize=9, color=INK2)
    ax.set_xticks(range(5, 25))
    ax.set_xticklabels([db.slot_label(s).replace("시", "") if s not in (5, 24) else ("~6" if s == 5 else "24~")
                        for s in range(5, 25)], fontsize=8)
    ax.set_ylabel("노인 비중(%)")
    ax.set_xlabel("시간대")
    ax.set_ylim(0, None)
    ax.legend(frameon=False, loc="upper right")
    ax.set_title("시간대별 노인 이용 비중 (2025년, 1~8호선 전체, 승차+하차)")
    save(fig, "q1_hourly_senior_pct.png")


def q1_top() -> None:
    df = db.query(
        "SELECT c.complex_nm, d.senior_weekday, d.senior_pct FROM v_complex_demand d "
        "JOIN station_complex c USING (complex_id) WHERE d.min_days >= 100 ORDER BY d.senior_weekday DESC LIMIT 15"
    ).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 5.6))
    vals = df.senior_weekday.astype(float)
    ax.barh(df.complex_nm, vals, color=SERIES[0], height=0.62)
    for y, (v, p) in enumerate(zip(vals, df.senior_pct.astype(float))):
        ax.text(v, y, f" {v:,.0f}명 (비중 {p:.0f}%)", va="center", fontsize=8.5, color=INK2)
    ax.set_xlim(0, vals.max() * 1.32)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("평일 하루 평균 노인 승차+하차(명)")
    ax.set_title("평일 노인 이용이 많은 역사 상위 15")
    save(fig, "q1_top_complexes.png")


def q2_outage() -> None:
    df = db.complex_outage(15).iloc[::-1]
    period = db.collect_period()
    fig, ax = plt.subplots(figsize=(8, 5.6))
    if df.empty:
        ax.text(0.5, 0.5, "수집 기간 중 비가동 기록 없음", ha="center", va="center", transform=ax.transAxes)
    else:
        vals = df.outage_hours.astype(float)
        ax.barh(df.complex_nm, vals, color=SERIES[1], height=0.62)
        for y, (v, n, t) in enumerate(zip(vals, df.n_outage, df.n_elevator)):
            ax.text(v, y, f" {v:,.1f}시간 · {n}건 / 승강기 {t}대", va="center", fontsize=8.5, color=INK2)
        ax.set_xlim(0, max(vals.max(), 0.1) * 1.45)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("비가동 누적 시간(시간, 매시 수집 기준 근사치)")
    ax.set_title(f"역사별 승강기 비가동 누적 시간 상위 15\n수집 {period['first_at']:%m/%d %H시} ~ {period['last_at']:%m/%d %H시}",
                 fontsize=12)
    save(fig, "q2_outage_top.png")


def q3_map() -> None:
    df = db.cluster_latest().dropna(subset=["lat", "lng"])
    if df.empty:
        print("군집 결과 없음: src/analysis.py를 먼저 실행")
        return
    fig, ax = plt.subplots(figsize=(8.5, 7.5))
    for no, g in df.groupby("cluster_no"):
        size = 12 + 160 * np.sqrt(g.senior_weekday.astype(float) / df.senior_weekday.astype(float).max())
        ax.scatter(g.lng.astype(float), g.lat.astype(float), s=size, color=SERIES[int(no) - 1], alpha=0.85,
                   edgecolor=SURFACE, linewidth=1.2, label=f"유형 {no}: {g.cluster_nm.iloc[0]} ({len(g)}곳)")
    # 도심에 몰린 라벨이 겹치지 않도록 순위에 따라 좌우·상하로 번갈아 둔다
    offsets = [(6, 6), (-6, -12), (6, -12), (-6, 6)]
    for i, r in enumerate(df.nsmallest(10, "priority_rank").itertuples()):
        dx, dy = offsets[i % 4]
        ax.annotate(f"{int(r.priority_rank)}. {r.complex_nm}", (float(r.lng), float(r.lat)), xytext=(dx, dy),
                    textcoords="offset points", fontsize=8.5, color=INK, ha="left" if dx > 0 else "right",
                    bbox={"boxstyle": "round,pad=0.15", "fc": SURFACE, "ec": "none", "alpha": 0.8})
    ax.set_aspect(1 / np.cos(np.radians(37.55)))
    ax.set_xlabel("경도")
    ax.set_ylabel("위도")
    ax.legend(frameon=False, loc="lower left", fontsize=9)
    ax.set_title("역사 유형 지도 (원 크기 = 평일 노인 이용, 숫자 = 우선 관리 순위 상위 10)")
    save(fig, "q3_cluster_map.png")


def q3_profile() -> None:
    df = db.cluster_latest()
    if df.empty:
        return
    metrics = [
        ("senior_weekday", "평일 노인 이용(명/일)"),
        ("senior_pct", "노인 비중(%)"),
        ("vertical_m", "수직 이동 거리(m)"),
        ("max_transfer_sec", "최대 환승 시간(초)"),
    ]
    g = df.astype({m: float for m, _ in metrics}).fillna({"max_transfer_sec": 0}).groupby(
        ["cluster_no", "cluster_nm"])[[m for m, _ in metrics]].mean().reset_index()
    fig, axes = plt.subplots(1, len(metrics), figsize=(13, 3.6))
    for ax, (m, label) in zip(axes, metrics):
        colors = [SERIES[int(c) - 1] for c in g.cluster_no]
        ax.bar([f"유형 {c}" for c in g.cluster_no], g[m], color=colors, width=0.6)
        for x, v in enumerate(g[m]):
            ax.text(x, v, f"{v:,.0f}" if v >= 100 else f"{v:.1f}", ha="center", va="bottom", fontsize=8.5, color=INK2)
        ax.set_title(label, fontsize=10.5)
        ax.grid(axis="x", visible=False)
    fig.suptitle("유형별 평균 지표   " + "   ".join(f"유형 {r.cluster_no}: {r.cluster_nm}" for r in g.itertuples()),
                 x=0.01, ha="left", fontsize=11, color=INK)
    fig.tight_layout()
    save(fig, "q3_cluster_profile.png")


def main() -> None:
    setup()
    q1_hourly()
    q1_top()
    q2_outage()
    q3_map()
    q3_profile()


if __name__ == "__main__":
    main()
