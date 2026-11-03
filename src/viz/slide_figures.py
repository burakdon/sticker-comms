"""Presentation figures: one insight per chart, sized for 16:9 slides.

Reads data/processed and outputs/tables; writes outputs/figures/slides/*.png.
Keeps the deck palette (off-white, slate, WhatsApp green) so figures and
slides read as one system. Run after the analysis scripts.

Usage:
  python src/viz/slide_figures.py
"""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.patches import FancyBboxPatch, Rectangle
from PIL import Image
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "figures" / "slides"
OUT.mkdir(parents=True, exist_ok=True)

BG, INK, INK2, MUTED, GRID = "#FBFBF9", "#3A4048", "#5C6670", "#9AA0A8", "#E3E4E0"
GREEN, GREEN_DK, GREEN_LT = "#25D366", "#128C7E", "#BFF0D2"
ORANGE, BLUE, PURPLE = "#EB6834", "#2A78D6", "#6250D6"
CULTURE = {"TR": BLUE, "CN": ORANGE, "EN": PURPLE}
CULTURE_NAME = {"TR": "Turkish", "CN": "Chinese", "EN": "English"}

matplotlib.rcParams.update({
    "font.family": "Avenir Next", "font.size": 12, "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": GRID, "figure.facecolor": BG,
    "axes.facecolor": BG, "savefig.facecolor": BG,
})


def clean_axes(ax, left=False, bottom=True):
    for s in ["top", "right"] + ([] if left else ["left"]) + ([] if bottom else ["bottom"]):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)


def save(fig, name):
    fig.savefig(OUT / name, dpi=220, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print("wrote", name)


def thumb(sticker_id, zoom):
    im = Image.open(ROOT / "stimuli" / f"{sticker_id}.webp").convert("RGBA")
    im.thumbnail((160, 160))
    return OffsetImage(np.asarray(im), zoom=zoom)


# ---------------------------------------------------------------- data
t = pd.read_csv(ROOT / "data" / "processed" / "trials_clean.csv")
p = pd.read_csv(ROOT / "data" / "processed" / "participants_clean.csv")
s = pd.read_csv(ROOT / "data" / "stimuli.csv").set_index("sticker_id")
key = pd.read_csv(ROOT / "outputs" / "tables" / "answer_key_validation.csv").set_index("sticker_id")
tests = pd.read_csv(ROOT / "outputs" / "tables" / "primary_tests.csv").set_index("test")
acc = t.pivot_table(index="participant_id", columns="context", values="correct", aggfunc="mean")


def ci95(x):
    x = pd.Series(x).dropna()
    return stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))


# ---------------------------------------------------------------- 1. who took part (waffle)
def fig_sample():
    def native_of(r):
        for c, col in [("TR", "fam_turkish"), ("CN", "fam_chinese"), ("EN", "fam_american")]:
            if r[col] == "native":
                return c
        return "other"
    p["native"] = p.apply(native_of, axis=1)
    order = ["TR", "CN", "EN", "other"]
    counts = p.native.value_counts().reindex(order).fillna(0).astype(int)
    colors = {**CULTURE, "other": "#C9CDD2"}
    names = {**CULTURE_NAME, "other": "Neither"}

    fig, ax = plt.subplots(figsize=(10, 4.6))
    cols, k = 14, 0
    for c in order:
        for _ in range(counts[c]):
            r, col = divmod(k, cols)
            ax.add_patch(FancyBboxPatch((col * 1.0, -r * 1.0), 0.82, 0.82, boxstyle="round,pad=0.02,rounding_size=0.18",
                                        fc=colors[c], ec="none"))
            k += 1
    ax.set_xlim(-0.2, cols); ax.set_ylim(-(k // cols) - 0.5, 1.2); ax.set_aspect("equal"); ax.axis("off")
    x = cols + 0.9
    for i, c in enumerate(order):
        y = 0.6 - i * 1.25
        ax.add_patch(FancyBboxPatch((x, y - 0.35), 0.7, 0.7, boxstyle="round,pad=0.02,rounding_size=0.15", fc=colors[c], ec="none"))
        ax.text(x + 1.0, y, f"{counts[c]}", fontsize=22, fontweight="bold", va="center", color=INK)
        ax.text(x + 2.4, y, f"{names[c]} native", fontsize=13, va="center", color=INK2)
    ax.set_xlim(-0.2, cols + 7.5)
    multi = int((p[["fam_turkish", "fam_chinese", "fam_american"]].eq("native").sum(axis=1) > 1).sum())
    ax.text(0, 1.0, f"{len(p)} participants · one square each · {multi} people native to two cultures are counted under the first",
            fontsize=11, color=MUTED, va="bottom")
    save(fig, "s03_sample_waffle.png")


# ---------------------------------------------------------------- 2. power
def fig_power():
    sim = pd.read_csv(ROOT / "outputs" / "tables" / "power_simulation.csv")
    fig, ax = plt.subplots(figsize=(9, 4.6))
    shades = [GREEN_LT, GREEN, GREEN_DK]
    for col, (lift, g) in zip(shades, sim.groupby("lift")):
        b = g.baseline.iloc[0]
        ax.plot(g.n, g.power, color=col, lw=3, marker="o", ms=6, mec=BG, mew=1.5,
                label=f"accuracy {b:.0%} to {b + lift:.0%}  (d_z about {g.implied_d_z.mean():.2f})")
    ax.axhline(0.8, color=MUTED, lw=1.2, ls="--"); ax.text(12, 0.815, "80% power", color=MUTED, fontsize=11)
    ax.axvline(52, color=INK2, lw=1.2, ls=":"); ax.text(50.8, 0.05, "planned n = 52", color=INK2, fontsize=11, fontweight="bold", ha="right", va="bottom")
    ax.axvline(70, color=GREEN_DK, lw=1.2, ls=":"); ax.text(71.2, 0.05, "collected n = 70", color=GREEN_DK, fontsize=11, fontweight="bold", ha="left", va="bottom")
    ax.set_xlabel("Participants"); ax.set_ylabel("Power"); ax.set_ylim(0, 1.02); ax.set_xlim(8, 122)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True); clean_axes(ax)
    fig.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.08), ncol=3, fontsize=10.5, labelcolor=INK2)
    save(fig, "s08_power.png")


# ---------------------------------------------------------------- 3. context pictogram
def fig_context_pictogram():
    rows = [("Sticker alone", "alone", "#C9CDD2"), ("Sticker in chat", "chat", GREEN), ("Message only", "text_only", "#8ED6AC")]
    fig, ax = plt.subplots(figsize=(11, 4.4))
    for i, (label, ctx, col) in enumerate(rows):
        m, e = acc[ctx].mean(), ci95(acc[ctx]); y = -i * 1.3
        ax.text(-0.4, y + 0.4, f"{m:.0%}", fontsize=34, fontweight="bold", ha="right", va="center",
                color=GREEN_DK if ctx == "chat" else INK)
        ax.text(-0.4, y - 0.15, label, fontsize=13, ha="right", va="center", color=INK2)
        for j in range(10):
            fill = min(max(m * 10 - j, 0), 1)
            ax.add_patch(FancyBboxPatch((j * 1.0, y - 0.1), 0.86, 0.86, boxstyle="round,pad=0.02,rounding_size=0.2", fc="#ECEDEA", ec="none"))
            if fill > 0:
                ax.add_patch(Rectangle((j * 1.0 + 0.02, y - 0.08), 0.82 * fill, 0.82, fc=col, ec="none",
                                       clip_path=FancyBboxPatch((j * 1.0, y - 0.1), 0.86, 0.86, boxstyle="round,pad=0.02,rounding_size=0.2", transform=ax.transData)))
        ax.text(10.4, y + 0.33, f"95% CI ±{e:.0%}", fontsize=11, color=MUTED, va="center")
    ax.plot([3.33, 3.33], [-2.9, 1.05], color=MUTED, lw=1.2, ls="--"); ax.text(3.4, 1.05, "chance 33%", color=MUTED, fontsize=10, va="bottom")
    ax.set_xlim(-4.2, 12.3); ax.set_ylim(-3.1, 1.4); ax.set_aspect("equal"); ax.axis("off")
    save(fig, "s09_context_pictogram.png")


# ---------------------------------------------------------------- 4. interaction
def fig_interaction():
    d = t[t.in_group.isin(["in", "out"])]
    a = d.pivot_table(index=["participant_id", "in_group"], columns="context", values="correct", aggfunc="mean").reset_index()
    order = ["alone", "chat", "text_only"]; names = ["Sticker alone", "Sticker in chat", "Message only"]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for g, lab, col in [("in", "Natives reading their own culture", GREEN_DK), ("out", "Outsiders", ORANGE)]:
        sub = a[a.in_group == g]; m = [sub[c].mean() for c in order]; e = [ci95(sub[c]) for c in order]
        ax.errorbar(range(3), m, yerr=e, color=col, lw=3, marker="o", ms=10, mec=BG, mew=2, capsize=4, label=f"{lab} (n = {sub.participant_id.nunique()})")
        for i, v in enumerate(m):
            ax.text(i + (0.08 if i < 2 else 0.09), v + (0.035 if g == "in" else -0.05), f"{v:.0%}", color=col, fontsize=12, fontweight="bold", va="center")
    ax.annotate("hide the sticker and\nthe advantage disappears", xy=(2, 0.69), xytext=(1.25, 0.43), fontsize=11, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=1), ha="left")
    ax.axhline(1 / 3, color=MUTED, lw=1, ls="--"); ax.text(-0.3, 0.345, "chance", color=MUTED, fontsize=10)
    ax.set_xticks(range(3), names, fontsize=12); ax.set_ylim(0.3, 0.95); ax.set_xlim(-0.35, 2.55)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True); clean_axes(ax)
    ax.legend(frameon=False, fontsize=11, labelcolor=INK2, loc="upper left")
    save(fig, "s10_interaction.png")


# ---------------------------------------------------------------- 5. outsiders vs chance (every dot a person)
def fig_chance_swarm():
    og = t[(t.in_group == "out") & (t.has_text == 0) & (t.context != "text_only")]
    per = og.groupby("participant_id").correct.mean().sort_values().values
    rng = np.random.default_rng(1)
    fig, ax = plt.subplots(figsize=(9, 3.2))
    # simple beeswarm: stack points with the same rounded value
    xs, ys = [], []
    bins = {}
    for v in per:
        b = round(v * 20) / 20; k = bins.get(b, 0); bins[b] = k + 1
        xs.append(b + rng.uniform(-0.008, 0.008)); ys.append((k - 0) * 0.16 * (1 if k % 2 == 0 else -1) + (0.08 if k % 2 else 0))
    ax.scatter(xs, ys, s=110, color=ORANGE, edgecolor=BG, linewidth=1.2, zorder=3)
    top = max(abs(v) for v in ys) + 0.35
    ax.axvline(1 / 3, color=MUTED, lw=1.5, ls="--", zorder=1); ax.text(1 / 3, top + 0.05, "chance 33%", ha="center", color=MUTED, fontsize=11, va="bottom")
    m = og.correct.mean()  # pooled over trials, the H4 binomial figure
    ax.axvline(m, color=GREEN_DK, lw=2.5, zorder=2); ax.text(m, top + 0.05, f"overall {m:.0%}", ha="center", color=GREEN_DK, fontsize=12, fontweight="bold", va="bottom")
    ax.set_xlim(-0.02, 1.02); ax.set_ylim(-top, top + 0.55); ax.set_yticks([])
    ax.set_xlabel(f"Accuracy on other cultures' no-text stickers · one dot per outsider (n = {len(per)})", color=INK2, fontsize=11)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    clean_axes(ax); ax.spines["left"].set_visible(False)
    save(fig, "s11_chance_swarm.png")


# ---------------------------------------------------------------- 6. flagged stickers (with thumbnails)
def fig_flagged():
    f = key[key.flagged].sort_values("insider_agreement")
    fig, ax = plt.subplots(figsize=(11, 5.0))
    y = np.arange(len(f))[::-1]
    ax.barh(y, f.insider_agreement, color=[CULTURE[c] for c in f.sticker_culture], height=0.6, zorder=2)
    ax.barh(y, 1 - f.insider_agreement, left=f.insider_agreement, color="#ECEDEA", height=0.6, zorder=1)
    for yi, (sid, r) in zip(y, f.iterrows()):
        ax.add_artist(AnnotationBbox(thumb(sid, 0.42), (-0.075, yi), frameon=False, xycoords="data", box_alignment=(0.5, 0.5)))
        ax.text(r.insider_agreement + 0.015, yi, f"{r.insider_agreement:.0%} agree", va="center", fontsize=12, color=INK, fontweight="bold")
        ax.text(1.02, yi, f"author: {r.key}\nnatives: {r.insider_modal}", va="center", fontsize=11, color=INK2)
    ax.axvline(0.5, color="#D64545", lw=1.5, ls="--", zorder=3); ax.text(0.505, len(f) - 0.45, "pre-registered flag line: 50%", color="#D64545", fontsize=10)
    ax.set_xlim(-0.16, 1.3); ax.set_ylim(-0.7, len(f) - 0.3); ax.set_yticks([])
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}" if 0 <= v <= 1 else ""))
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0]); clean_axes(ax); ax.spines["left"].set_visible(False)
    for c, col in CULTURE.items():
        ax.bar([0], [0], color=col, label=CULTURE_NAME[c])
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0.0, 1.0), fontsize=10, labelcolor=INK2, ncol=3)
    save(fig, "s12_flagged.png")


# ---------------------------------------------------------------- 7. all 36 stickers ranked (appendix)
def fig_ranking():
    vis = t[(t.context != "text_only") & (t.in_group != "in")]
    r = vis.groupby("sticker_id").agg(acc=("correct", "mean"), n=("correct", "size"), culture=("sticker_culture", "first")).sort_values("acc")
    fig, ax = plt.subplots(figsize=(14, 6.2))
    x = np.arange(len(r))
    ax.bar(x, r.acc, color=[CULTURE[c] for c in r.culture], width=0.7, zorder=2)
    for xi, (sid, row) in zip(x, r.iterrows()):
        ax.add_artist(AnnotationBbox(thumb(sid, 0.15), (xi, -0.07), frameon=False, xycoords="data", box_alignment=(0.5, 0.5), clip_on=False))
    ax.axhline(1 / 3, color=MUTED, lw=1.2, ls="--"); ax.text(len(r) - 0.5, 0.345, "chance", color=MUTED, fontsize=10, ha="right")
    ax.set_xticks([]); ax.set_ylim(-0.14, 1.05); ax.set_xlim(-0.8, len(r) - 0.2)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0]); ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}" if v >= 0 else ""))
    ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True); clean_axes(ax); ax.spines["bottom"].set_visible(False)
    ax.set_ylabel("Non-native readers correct (sticker visible)")
    for c, col in CULTURE.items():
        ax.bar([0], [0], color=col, label=CULTURE_NAME[c])
    ax.legend(frameon=False, loc="upper left", fontsize=11, labelcolor=INK2, ncol=3)
    save(fig, "s15_ranking.png")
    return r


# ---------------------------------------------------------------- 8. calibration (appendix)
def fig_calibration():
    g = t.groupby("confidence").correct.agg(["mean", "size"])
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(g.index, g["mean"], color=GREEN_DK, lw=3, marker="o", ms=10, mec=BG, mew=2)
    for c, (m, n) in g.iterrows():
        ax.text(c, m + 0.04, f"{m:.0%}", ha="center", color=INK, fontsize=12, fontweight="bold")
        ax.text(c, m - 0.06, f"n={int(n)}", ha="center", color=MUTED, fontsize=9)
    ax.axhline(1 / 3, color=MUTED, lw=1, ls="--")
    ax.set_xticks([1, 2, 3, 4, 5], ["1\njust guessing", "2", "3", "4", "5\nvery sure"]); ax.set_ylim(0.25, 1.0)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}")); ax.set_ylabel("Accuracy")
    ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True); clean_axes(ax)
    save(fig, "s16_calibration.png")


if __name__ == "__main__":
    fig_sample(); fig_power(); fig_context_pictogram(); fig_interaction(); fig_chance_swarm(); fig_flagged()
    r = fig_ranking(); fig_calibration()
    # numbers the deck needs
    live = t[(t.in_group != "in") & t.sticker_id.isin(["TR_NOTXT_02", "CN_TXT_05"])]
    print("\nlive-round stickers, non-native accuracy by context:")
    print(live.pivot_table(index="sticker_id", columns="context", values="correct", aggfunc=["mean", "size"]).round(2))
    print("\nhardest three:", r.head(3).round(2).to_dict("index"))
