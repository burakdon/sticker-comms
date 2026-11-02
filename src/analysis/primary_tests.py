"""Confirmatory tests on per-person accuracy (H1, H5, context RM-ANOVA, H4).

H1   chat vs alone          paired t-test (Wilcoxon if differences non-normal), d_z, 95% CI
H5   chat vs text_only      same
ctx  alone/chat/text_only   one-way repeated-measures ANOVA, Mauchly sphericity,
                            Greenhouse-Geisser if violated, partial eta^2,
                            Holm-corrected pairwise post hocs, Friedman fallback
H4   out-group, no-text,    exact binomial test vs 1/3 (pooled) and per-person
     sticker visible        one-sample t vs 1/3; Cohen's h

Reads data/processed/trials_clean{suffix}.csv; writes outputs/tables/primary_tests{suffix}.csv.

Usage:
  python src/analysis/primary_tests.py
  python src/analysis/primary_tests.py --suffix _prereg      # sensitivity: pre-registered exclusions
  python src/analysis/primary_tests.py --suffix _noflag      # sensitivity: flagged stickers removed
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pingouin as pg
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
CHANCE = 1 / 3


def paired(a: pd.Series, b: pd.Series, label: str) -> dict:
    d = (a - b).dropna()
    n = len(d)
    sw_p = stats.shapiro(d).pvalue if n >= 3 else np.nan
    tt = stats.ttest_rel(a[d.index], b[d.index])
    ci = stats.t.interval(0.95, n - 1, loc=d.mean(), scale=d.std(ddof=1) / np.sqrt(n))
    wil = stats.wilcoxon(d) if (d != 0).any() else None
    return {
        "test": label, "n": n, "mean_a": a[d.index].mean(), "mean_b": b[d.index].mean(),
        "mean_diff": d.mean(), "ci_low": ci[0], "ci_high": ci[1],
        "d_z": d.mean() / d.std(ddof=1), "t": tt.statistic, "p_t": tt.pvalue,
        "shapiro_p": sw_p, "wilcoxon_p": wil.pvalue if wil else np.nan,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--suffix", default="")
    args = ap.parse_args()
    sfx = args.suffix

    t = pd.read_csv(ROOT / "data" / "processed" / f"trials_clean{sfx}.csv")
    acc = t.pivot_table(index="participant_id", columns="context", values="correct", aggfunc="mean").dropna()
    rows = []

    # --- H1 / H5 ------------------------------------------------------------
    rows.append(paired(acc["chat"], acc["alone"], "H1 chat - alone"))
    rows.append(paired(acc["chat"], acc["text_only"], "H5 chat - text_only"))
    rows.append(paired(acc["alone"], acc["text_only"], "alone - text_only"))

    # --- RM-ANOVA over context ---------------------------------------------
    long = acc.reset_index().melt(id_vars="participant_id", var_name="context", value_name="acc")
    # pingouin renamed its columns across versions (p-unc vs p_unc etc.); normalise.
    norm = lambda df: df.rename(columns=lambda c: c.replace("-", "_").replace("(", "_").replace(")", ""))
    sph = pg.sphericity(long, dv="acc", within="context", subject="participant_id")
    aov = norm(pg.rm_anova(long, dv="acc", within="context", subject="participant_id", correction=True, effsize="np2"))
    post = norm(pg.pairwise_tests(long, dv="acc", within="context", subject="participant_id",
                                  padjust="holm", effsize="cohen"))
    fried = norm(pg.friedman(long, dv="acc", within="context", subject="participant_id"))
    a = aov.iloc[0]
    rows.append({"test": "RM-ANOVA context", "n": acc.shape[0], "F": a["F"], "p_t": a["p_unc"],
                 "p_GG": a.get("p_GG_corr", np.nan), "eps": a.get("eps", np.nan),
                 "partial_eta2": a["np2"], "mauchly_W": sph.W, "mauchly_p": sph.pval,
                 "friedman_p": fried["p_unc"].iloc[0]})
    for _, r in post.iterrows():
        rows.append({"test": f"post hoc {r.A} vs {r.B} (Holm)", "n": acc.shape[0], "mean_a": r.get("mean_A", np.nan),
                     "mean_b": r.get("mean_B", np.nan), "t": r["T"], "p_t": r["p_unc"], "p_holm": r["p_corr"],
                     "d_z": r["cohen"]})

    # --- H4: out-group, no text, sticker visible ----------------------------
    og = t[(t.in_group == "out") & (t.has_text == 0) & (t.context != "text_only")]
    k, n = int(og.correct.sum()), len(og)
    bt = stats.binomtest(k, n, CHANCE, alternative="greater")
    ci = bt.proportion_ci(0.95)
    h = 2 * np.arcsin(np.sqrt(k / n)) - 2 * np.arcsin(np.sqrt(CHANCE))
    per = og.groupby("participant_id").correct.mean()
    t1 = stats.ttest_1samp(per, CHANCE, alternative="greater")
    rows.append({"test": "H4 out-group no-text vs chance (pooled binomial)", "n": n, "mean_a": k / n,
                 "ci_low": ci.low, "ci_high": ci.high, "p_t": bt.pvalue, "cohen_h": h})
    rows.append({"test": "H4 per-person accuracy vs 1/3 (one-sample t)", "n": len(per), "mean_a": per.mean(),
                 "t": t1.statistic, "p_t": t1.pvalue, "d_z": (per.mean() - CHANCE) / per.std(ddof=1)})

    out = pd.DataFrame(rows)
    out_dir = ROOT / "outputs" / "tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_dir / f"primary_tests{sfx}.csv", index=False)

    pd.set_option("display.width", 200)
    print(f"participants with all three contexts: {acc.shape[0]}")
    print("mean accuracy by context:", acc.mean().round(3).to_dict(), "\n")
    print(out.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
