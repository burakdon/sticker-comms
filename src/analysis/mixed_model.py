"""Mixed-effects logistic regression (H2, H3) with crossed random effects.

    correct ~ context * in_group + has_text + (1 | participant) + (1 | sticker)

Fitted with statsmodels' BinomialBayesMixedGLM (variational Bayes), which
supports crossed random intercepts; fixed effects are reported as odds ratios
with 95% intervals from the posterior. Reference levels: context = alone,
in_group = out. "some"-familiarity trials are excluded from this model
(pre-registered: in-group is native vs none).

Also fits a covariate model on out-group trials only (exploratory): does
meme fluency, sticker-use frequency, bilingualism or age predict decoding?

Writes outputs/tables/mixed_model{suffix}.csv and mixed_model_covariates.csv.

Usage:
  python src/analysis/mixed_model.py [--suffix _prereg]
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

ROOT = Path(__file__).resolve().parents[2]
VC = {"participant": "0 + C(participant_id)", "sticker": "0 + C(sticker_id)"}


def fit(formula: str, data: pd.DataFrame, label: str) -> pd.DataFrame:
    m = BinomialBayesMixedGLM.from_formula(formula, VC, data).fit_vb()
    k = len(m.fe_mean)
    out = pd.DataFrame({
        "model": label, "term": m.model.exog_names, "log_odds": m.fe_mean, "sd": m.fe_sd,
    })
    out["OR"] = np.exp(out.log_odds)
    out["OR_low"] = np.exp(out.log_odds - 1.96 * out.sd)
    out["OR_high"] = np.exp(out.log_odds + 1.96 * out.sd)
    out["z"] = out.log_odds / out.sd
    out["p_approx"] = 2 * (1 - __import__("scipy").stats.norm.cdf(abs(out.z)))
    vc = pd.DataFrame({"model": label, "term": ["sd(participant)", "sd(sticker)"],
                       "log_odds": np.exp(m.vcp_mean), "sd": np.nan})
    return pd.concat([out, vc], ignore_index=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--suffix", default="")
    args = ap.parse_args()
    sfx = args.suffix

    t = pd.read_csv(ROOT / "data" / "processed" / f"trials_clean{sfx}.csv")
    d = t[t.in_group.isin(["in", "out"])].copy()
    d["context"] = pd.Categorical(d.context, ["alone", "chat", "text_only"])
    d["in_group"] = pd.Categorical(d.in_group, ["out", "in"])

    main_fit = fit("correct ~ C(context) * C(in_group) + has_text", d, "H2/H3 main")
    # Same model without the interaction, for the context and in-group main effects.
    add_fit = fit("correct ~ C(context) + C(in_group) + has_text", d, "additive")

    # Exploratory covariates on out-group trials (what makes a good outsider decoder?)
    og = t[t.in_group == "out"].copy()
    og["use_daily"] = (og.sticker_use_frequency == "daily").astype(int)
    og["bilingual"] = (og.bilingual == "yes").astype(int)
    og["meme_c"] = og.meme_fluency - og.meme_fluency.mean()
    og["age_c"] = (og.age - og.age.mean()) / 10
    cov_fit = fit("correct ~ C(context) + has_text + meme_c + use_daily + bilingual + age_c", og, "out-group covariates")

    out = pd.concat([main_fit, add_fit, cov_fit], ignore_index=True)
    out_dir = ROOT / "outputs" / "tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_dir / f"mixed_model{sfx}.csv", index=False)

    pd.set_option("display.width", 200)
    print(f"main model: {len(d)} trials, {d.participant_id.nunique()} participants, {d.sticker_id.nunique()} stickers")
    print(out.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
