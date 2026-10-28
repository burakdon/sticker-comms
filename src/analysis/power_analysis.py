"""Power analysis for the primary hypothesis (H1: chat > alone).

Two approaches:
  1. Analytic: paired t-test on per-person accuracy, statsmodels TTestPower.
  2. Simulation of the actual trial structure: each participant answers 10 binary
     trials per condition on a rotating third of 30 stickers, with participant and
     sticker random effects on the logit scale. Per-person accuracy is then
     compared with a paired t-test, exactly as planned for the real data.

The simulation translates an assumed accuracy lift (e.g. 55% -> 65%) into power,
and reports the d_z that lift implies, which links the two approaches.

Outputs:
    outputs/tables/power_analytic.csv
    outputs/tables/power_simulation.csv
    outputs/figures/power_curve.png

Usage:
    python src/analysis/power_analysis.py
    python src/analysis/power_analysis.py --baseline 0.6 --sd-participant 0.4 --sims 2000
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import expit, logit
from statsmodels.stats.power import TTestPower

ROOT = Path(__file__).resolve().parents[2]
ALPHA = 0.05
TARGET_POWER = 0.80
N_STICKERS = 30
TRIALS_PER_CONDITION = 10

# Chart tokens (light surface).
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]


def analytic_power(effect_sizes, n_grid):
    solver = TTestPower()
    rows = []
    for d in effect_sizes:
        n_needed = solver.solve_power(effect_size=d, alpha=ALPHA, power=TARGET_POWER,
                                      alternative="two-sided")
        for n in n_grid:
            rows.append({
                "d_z": d,
                "n": n,
                "power": solver.power(effect_size=d, nobs=n, alpha=ALPHA,
                                      alternative="two-sided"),
                "n_for_80pct": int(np.ceil(n_needed)),
            })
    return pd.DataFrame(rows)


def simulate_power(n, baseline, lift, sd_participant, sd_sticker, sims, rng):
    """Return (power, mean d_z) for one (n, lift) combination."""
    # Sticker effects are redrawn per simulated study; sets A/B/C are stickers 0-9, 10-19, 20-29.
    sticker_fx = rng.normal(0, sd_sticker, size=(sims, 1, N_STICKERS))
    person_fx = rng.normal(0, sd_participant, size=(sims, n, 1))
    rotation = rng.integers(0, 3, size=(sims, n, 1))

    set_idx = np.arange(TRIALS_PER_CONDITION)
    # Rotation r shows set r alone and set (r+1)%3 in chat (text_only not needed for H1).
    alone_ids = rotation * TRIALS_PER_CONDITION + set_idx
    chat_ids = ((rotation + 1) % 3) * TRIALS_PER_CONDITION + set_idx

    sticker_fx = np.broadcast_to(sticker_fx, (sims, n, N_STICKERS))
    b0 = logit(baseline)
    b1 = logit(baseline + lift) - b0
    p_alone = expit(b0 + person_fx + np.take_along_axis(sticker_fx, alone_ids, axis=2))
    p_chat = expit(b0 + b1 + person_fx + np.take_along_axis(sticker_fx, chat_ids, axis=2))

    acc_alone = (rng.random(p_alone.shape) < p_alone).mean(axis=2)
    acc_chat = (rng.random(p_chat.shape) < p_chat).mean(axis=2)
    diff = acc_chat - acc_alone

    t, p = stats.ttest_rel(acc_chat, acc_alone, axis=1)
    sd = diff.std(axis=1, ddof=1)
    d_z = np.divide(diff.mean(axis=1), sd, out=np.zeros(sims), where=sd > 0)
    return float(np.mean((p < ALPHA) & (t > 0))), float(np.mean(d_z))


def simulation_power(lifts, n_grid, baseline, sd_participant, sd_sticker, sims, seed):
    rng = np.random.default_rng(seed)
    rows = []
    for lift in lifts:
        for n in n_grid:
            power, d_z = simulate_power(n, baseline, lift, sd_participant, sd_sticker, sims, rng)
            rows.append({"baseline": baseline, "lift": lift, "n": n,
                         "power": power, "implied_d_z": d_z})
    return pd.DataFrame(rows)


def style_axis(ax, title):
    ax.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", color=INK, fontsize=11, pad=10)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ["top", "right", "left"]:
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=MUTED, length=0, labelsize=9)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Participants (n)", color=INK_2, fontsize=9)
    ax.axhline(TARGET_POWER, color=MUTED, linewidth=1, linestyle="--")
    ax.text(0.01, TARGET_POWER + 0.015, "80% power",
            transform=ax.get_yaxis_transform(), color=MUTED, fontsize=8)


def plot(analytic, sim, out_path):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True, facecolor=SURFACE)

    ax = axes[0]
    for color, (d, grp) in zip(SERIES, analytic.groupby("d_z")):
        n80 = grp["n_for_80pct"].iloc[0]
        ax.plot(grp["n"], grp["power"], color=color, linewidth=2,
                label=f"d_z = {d:.1f}  (n = {n80} for 80%)")
    style_axis(ax, "Analytic: paired t-test, α = .05")
    ax.set_ylabel("Power", color=INK_2, fontsize=9)
    ax.legend(frameon=False, fontsize=8, labelcolor=INK_2, loc="lower right")

    ax = axes[1]
    baseline = sim["baseline"].iloc[0]
    for color, (lift, grp) in zip(SERIES, sim.groupby("lift")):
        d_mid = grp["implied_d_z"].mean()
        ax.plot(grp["n"], grp["power"], color=color, linewidth=2, marker="o",
                markersize=5, markeredgecolor=SURFACE, markeredgewidth=1.5,
                label=f"{baseline:.0%} → {baseline + lift:.0%}  (d_z ≈ {d_mid:.2f})")
    style_axis(ax, "Simulated: 10 trials per condition, random effects")
    ax.legend(frameon=False, fontsize=8, labelcolor=INK_2, loc="lower right")

    fig.tight_layout()
    fig.savefig(out_path, dpi=200, facecolor=SURFACE)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--baseline", type=float, default=0.55,
                        help="assumed accuracy in the alone condition (pilot to refine)")
    parser.add_argument("--lifts", type=float, nargs="+", default=[0.05, 0.10, 0.15],
                        help="assumed accuracy gains from chat context")
    parser.add_argument("--sd-participant", type=float, default=0.5,
                        help="SD of participant random intercepts (logit scale)")
    parser.add_argument("--sd-sticker", type=float, default=0.8,
                        help="SD of sticker random intercepts (logit scale)")
    parser.add_argument("--sims", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=510)
    args = parser.parse_args()

    n_grid = list(range(10, 125, 5))
    analytic = analytic_power([0.3, 0.4, 0.5], n_grid)
    sim = simulation_power(args.lifts, list(range(10, 125, 10)), args.baseline,
                           args.sd_participant, args.sd_sticker, args.sims, args.seed)

    tables = ROOT / "outputs" / "tables"
    figures = ROOT / "outputs" / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    analytic.to_csv(tables / "power_analytic.csv", index=False)
    sim.to_csv(tables / "power_simulation.csv", index=False)
    plot(analytic, sim, figures / "power_curve.png")

    print("Analytic (paired t, two-sided, alpha = .05, power = .80):")
    print(analytic.drop_duplicates("d_z")[["d_z", "n_for_80pct"]].to_string(index=False))
    print("\nSimulation: smallest n reaching 80% power")
    for lift, grp in sim.groupby("lift"):
        hit = grp[grp["power"] >= TARGET_POWER]
        n80 = int(hit["n"].min()) if len(hit) else None
        print(f"  {args.baseline:.0%} -> {args.baseline + lift:.0%}: "
              f"n = {n80 if n80 else '> ' + str(grp['n'].max())}, "
              f"implied d_z ≈ {grp['implied_d_z'].mean():.2f}")


if __name__ == "__main__":
    main()
