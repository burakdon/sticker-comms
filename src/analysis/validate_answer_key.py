"""Pre-registered answer-key check: do insiders agree with the author's label?

For each sticker, take in-group participants' trials where the sticker was
visible (alone + chat) and compute agreement with `intended_sentiment`.
Stickers under AGREE_MIN (with at least N_MIN insider ratings) are flagged and
written to outputs/tables/flagged_stickers.csv; the primary analyses are
re-run without them as a robustness check.

Also reports, per sticker, out-group accuracy and the modal insider response,
which is the "which stickers do insiders disagree on" figure.

Usage:
  python src/analysis/validate_answer_key.py
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
AGREE_MIN, N_MIN = 0.50, 5


def main() -> None:
    t = pd.read_csv(ROOT / "data" / "processed" / "trials_clean.csv")
    s = pd.read_csv(ROOT / "data" / "stimuli.csv")[["sticker_id", "description"]]
    vis = t[t.context != "text_only"]

    ins = vis[vis.in_group == "in"].groupby("sticker_id")
    out = vis[vis.in_group == "out"].groupby("sticker_id")
    tab = pd.DataFrame({
        "sticker_culture": vis.groupby("sticker_id").sticker_culture.first(),
        "has_text": vis.groupby("sticker_id").has_text.first(),
        "key": vis.groupby("sticker_id").intended_sentiment.first(),
        "insider_n": ins.size(),
        "insider_agreement": ins.correct.mean(),
        "insider_modal": ins.response.agg(lambda r: r.mode().iloc[0]),
        "outsider_n": out.size(),
        "outsider_accuracy": out.correct.mean(),
    })
    tab["flagged"] = (tab.insider_agreement < AGREE_MIN) & (tab.insider_n >= N_MIN)
    tab = tab.merge(s, left_index=True, right_on="sticker_id").set_index("sticker_id")
    tab = tab.sort_values(["sticker_culture", "insider_agreement"])

    out_dir = ROOT / "outputs" / "tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    tab.round(3).to_csv(out_dir / "answer_key_validation.csv")
    tab[tab.flagged].reset_index()[["sticker_id"]].to_csv(out_dir / "flagged_stickers.csv", index=False)

    pd.set_option("display.width", 160)
    print(tab.drop(columns="description").round(2).to_string())
    print(f"\nflagged (<{AGREE_MIN:.0%} insider agreement, n>={N_MIN}): {list(tab[tab.flagged].index)}")
    print("\nmean insider agreement by culture:", tab.groupby("sticker_culture").insider_agreement.mean().round(2).to_dict())
    print("mean outsider accuracy by culture: ", tab.groupby("sticker_culture").outsider_accuracy.mean().round(2).to_dict())


if __name__ == "__main__":
    main()
