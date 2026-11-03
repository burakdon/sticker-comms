"""Figures for the report and slides. Reads data/processed and outputs/tables.

  fig1_accuracy_by_context.png      headline: per-person accuracy by context (mean, 95% CI)
  fig2_context_by_group.png         context x in-group / out-group interaction
  fig3_sticker_ranking.png          out-group accuracy per sticker, coloured by culture
  fig4_insider_agreement.png        insider agreement with the author's key, per sticker
  fig5_calibration.png              accuracy by confidence rating
  fig6_text_vs_notext.png           text / no-text by reader group and culture

Usage:
  python src/viz/figures.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "outputs" / "figures"

SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
CULTURE_COL = {"TR": "#2a78d6", "CN": "#eb6834", "EN": "#1baf7a"}
CULTURE_NAME = {"TR": "Turkish", "CN": "Chinese", "EN": "English"}
CTX_NAME = {"alone": "Sticker alone", "chat": "Sticker in chat", "text_only": "Message only"}
GROUP_COL = {"in": "#2a78d6", "out": "#eb6834", "some": "#898781"}


def style(ax, title, ylabel=None):
    ax.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", color=INK, fontsize=11, pad=10)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=MUTED, length=0, labelsize=9)
    if ylabel:
        ax.set_ylabel(ylabel, color=INK2, fontsize=9)


def ci95(x):
    x = pd.Series(x).dropna()
    if len(x) < 2:
        return 0.0
    return stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=200, facecolor=SURFACE)
    plt.close(fig)
    print("wrote", name)


def fig1(t):
    acc = t.pivot_table(index="participant_id", columns="context", values="correct", aggfunc="mean")
    order = ["alone", "chat", "text_only"]
    m = acc[order].mean(); e = [ci95(acc[c]) for c in order]
    fig, ax = plt.subplots(figsize=(6.4, 4), facecolor=SURFACE)
    ax.bar(range(3), m, yerr=e, width=0.62, color=[CULTURE_COL["TR"], "#5a97e0", "#9fc1ec"],
           capsize=4, error_kw={"ecolor": INK2, "lw": 1})
    for i, v in enumerate(m):
        ax.text(i, v + e[i] + 0.015, f"{v:.0%}", ha="center", color=INK, fontsize=10, fontweight="bold")
    ax.axhline(1 / 3, color=MUTED, lw=1, ls="--"); ax.text(2.42, 1 / 3 + 0.01, "chance", color=MUTED, fontsize=8, ha="right")
    ax.set_xticks(range(3), [CTX_NAME[c] for c in order]); ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    style(ax, f"Accuracy by context (n = {len(acc)} participants, mean ± 95% CI)", "Accuracy")
    save(fig, "fig1_accuracy_by_context.png")


def fig2(t):
    d = t[t.in_group.isin(["in", "out"])]
    acc = d.pivot_table(index=["participant_id", "in_group"], columns="context", values="correct", aggfunc="mean").reset_index()
    order = ["alone", "chat", "text_only"]
    fig, ax = plt.subplots(figsize=(6.4, 4), facecolor=SURFACE)
    for g, lab in [("in", "In-group (native)"), ("out", "Out-group")]:
        sub = acc[acc.in_group == g]
        m = [sub[c].mean() for c in order]; e = [ci95(sub[c]) for c in order]
        ax.errorbar(range(3), m, yerr=e, color=GROUP_COL[g], lw=2, marker="o", ms=7, mec=SURFACE, mew=1.5,
                    capsize=3, label=f"{lab} (n = {sub.participant_id.nunique()})")
        ax.text(2.08, m[2], f"{m[2]:.0%}", color=GROUP_COL[g], fontsize=9, va="center")
    ax.axhline(1 / 3, color=MUTED, lw=1, ls="--")
    ax.set_xticks(range(3), [CTX_NAME[c] for c in order]); ax.set_ylim(0.2, 1); ax.set_xlim(-0.3, 2.5)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="lower left")
    style(ax, "Does context help outsiders more? (per-person means ± 95% CI)", "Accuracy")
    save(fig, "fig2_context_by_group.png")


def fig3(t, s):
    # Non-native readers (none + some familiarity): "none" alone leaves only a
    # handful of readers for English stickers, since almost everyone has some
    # exposure to American culture.
    vis = t[(t.context != "text_only") & (t.in_group != "in")]
    r = vis.groupby("sticker_id").agg(acc=("correct", "mean"), n=("correct", "size"), culture=("sticker_culture", "first"))
    r = r.join(s.set_index("sticker_id")[["description", "intended_sentiment"]])
    r["label"] = [f"{d[:38]}…" if len(d) > 38 else d for d in r.description]
    r = r.sort_values("acc")
    fig, ax = plt.subplots(figsize=(8, 10), facecolor=SURFACE)
    y = np.arange(len(r))
    ax.barh(y, r.acc, color=[CULTURE_COL[c] for c in r.culture], height=0.72)
    for yi, (a, sent, n) in enumerate(zip(r.acc, r.intended_sentiment, r.n)):
        ax.text(a + 0.01, yi, f"{a:.0%}  ({sent[:3]}, n={int(n)})", va="center", color=INK2, fontsize=7.5)
    ax.axvline(1 / 3, color=MUTED, lw=1, ls="--")
    ax.set_yticks(y, r.label, fontsize=7.5); ax.set_xlim(0, 1.15)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.grid(axis="x", color=GRID, lw=0.6); ax.grid(axis="y", visible=False)
    for c, col in CULTURE_COL.items():
        ax.bar([0], [0], color=col, label=CULTURE_NAME[c])
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="lower right")
    style(ax, "How decodable is each sticker to non-native readers? (sticker visible)")
    ax.spines["left"].set_visible(False); ax.tick_params(axis="y", colors=INK)
    save(fig, "fig3_sticker_ranking.png")


def fig4(tab):
    r = tab.sort_values("insider_agreement")
    fig, ax = plt.subplots(figsize=(8, 10), facecolor=SURFACE)
    y = np.arange(len(r))
    ax.barh(y, r.insider_agreement, color=[CULTURE_COL[c] for c in r.sticker_culture], height=0.72)
    for yi, (a, n, modal, key) in enumerate(zip(r.insider_agreement, r.insider_n, r.insider_modal, r.key)):
        note = f"{a:.0%} (n={int(n)})" + (f"  insiders say: {modal}" if a < 0.5 else "")
        ax.text(a + 0.01, yi, note, va="center", color=INK2, fontsize=7.5)
    ax.axvline(0.5, color="#e34948", lw=1, ls="--"); ax.text(0.505, len(r) - 0.5, "flag threshold", color="#e34948", fontsize=8)
    labels = [f"{d[:38]}…" if len(d) > 38 else d for d in r.description]
    ax.set_yticks(y, labels, fontsize=7.5); ax.set_xlim(0, 1.3)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.grid(axis="x", color=GRID, lw=0.6); ax.grid(axis="y", visible=False)
    for c, col in CULTURE_COL.items():
        ax.bar([0], [0], color=col, label=CULTURE_NAME[c])
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="lower right")
    style(ax, "Do insiders agree with the author's label? (native readers)")
    ax.spines["left"].set_visible(False); ax.tick_params(axis="y", colors=INK)
    save(fig, "fig4_insider_agreement.png")


def fig5(t):
    g = t.groupby("confidence").correct.agg(["mean", "size"])
    fig, ax = plt.subplots(figsize=(6.4, 3.8), facecolor=SURFACE)
    ax.plot(g.index, g["mean"], color=CULTURE_COL["TR"], lw=2, marker="o", ms=8, mec=SURFACE, mew=1.5)
    for c, (m, n) in g.iterrows():
        ax.text(c, m + 0.03, f"{m:.0%}\n(n={int(n)})", ha="center", color=INK2, fontsize=8)
    ax.axhline(1 / 3, color=MUTED, lw=1, ls="--")
    ax.set_xticks([1, 2, 3, 4, 5], ["1\njust guessing", "2", "3", "4", "5\nvery sure"]); ax.set_ylim(0.2, 1.05)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    style(ax, "Calibration: people know when they are guessing", "Accuracy")
    save(fig, "fig5_calibration.png")


def fig6(t):
    d = t[(t.context != "text_only") & t.in_group.isin(["in", "out"])]
    g = d.groupby(["sticker_culture", "in_group", "has_text"]).correct.mean().unstack("has_text")
    fig, axes = plt.subplots(1, 3, figsize=(9, 3.6), sharey=True, facecolor=SURFACE)
    for ax, c in zip(axes, ["TR", "CN", "EN"]):
        sub = g.loc[c]
        x = np.arange(2)
        for i, grp in enumerate(["in", "out"]):
            if grp in sub.index:
                ax.bar(x + (i - 0.5) * 0.36, [sub.loc[grp, 0], sub.loc[grp, 1]], width=0.34,
                       color=GROUP_COL[grp], label={"in": "In-group", "out": "Out-group"}[grp])
        ax.set_xticks(x, ["No text", "Text"]); ax.set_ylim(0, 1)
        style(ax, f"{CULTURE_NAME[c]} stickers")
    axes[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=9, labelcolor=INK2, loc="upper right", ncol=2,
               bbox_to_anchor=(0.99, 1.0))
    fig.suptitle("Accuracy by sticker text and reader group (sticker visible)", x=0.01, ha="left",
                 color=INK, fontsize=11)
    save(fig, "fig6_text_vs_notext.png")


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    t = pd.read_csv(ROOT / "data" / "processed" / "trials_clean.csv")
    s = pd.read_csv(ROOT / "data" / "stimuli.csv")
    tab = pd.read_csv(ROOT / "outputs" / "tables" / "answer_key_validation.csv")
    fig1(t); fig2(t); fig3(t, s); fig4(tab); fig5(t); fig6(t)


if __name__ == "__main__":
    main()
