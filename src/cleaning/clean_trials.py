"""Clean the raw export into analysis-ready tables, logging every exclusion.

Rules (in order):
  1. incomplete sessions          participant did not finish all trials
  2. authored trials              each author is kept as a participant but their
                                  trials on stickers they authored are dropped
                                  (they wrote the answer key for those)
  3. attention-check trial        the ATTN_01 trial itself is never analysed
  4. reaction-time bounds         rt < 300 ms or > 30 s
  5. attention-check failures     OFF by default (the check proved ambiguous;
                                  see report); --exclude-attention-failures
                                  turns the pre-registered rule on for the
                                  sensitivity analysis
  6. flagged stickers             optional, from validate_answer_key.py

Derived columns: correct, sticker_culture, has_text, intended_sentiment,
in_group (in / out / some), source (flyer / direct).

Outputs:
  data/processed/trials_clean.csv
  data/processed/participants_clean.csv
  data/processed/participant_summary.csv     accuracy per participant x context
  outputs/tables/cleaning_log.csv

Usage:
  python src/cleaning/clean_trials.py
  python src/cleaning/clean_trials.py --exclude-attention-failures --suffix _prereg
  python src/cleaning/clean_trials.py --drop-flagged outputs/tables/flagged_stickers.csv
"""

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW, PROC, TABLES = ROOT / "data" / "raw", ROOT / "data" / "processed", ROOT / "outputs" / "tables"

# participant_id -> cultures whose answer key that person wrote
AUTHORS = {
    "wghp9dshc9": ["TR", "EN"],   # Burak
    "4k8a26ymt5": ["CN"],         # Canyang
}
RT_MIN, RT_MAX = 300, 30_000
FAM_COL = {"TR": "fam_turkish", "CN": "fam_chinese", "EN": "fam_american"}
GROUP = {"native": "in", "none": "out", "some": "some"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--exclude-attention-failures", action="store_true")
    ap.add_argument("--drop-flagged", type=Path, help="CSV with a sticker_id column to exclude")
    ap.add_argument("--suffix", default="", help="appended to output file names, e.g. _prereg")
    args = ap.parse_args()

    p = pd.read_csv(RAW / "participants.csv")
    t = pd.read_csv(RAW / "trials.csv")
    s = pd.read_csv(ROOT / "data" / "stimuli.csv")
    log = []

    def note(rule, before, after, unit):
        log.append({"rule": rule, "dropped": before - after, "remaining": after, "unit": unit})

    # --- participants -------------------------------------------------------
    n0 = len(p)
    n_expected = int((s.culture != "ATTN").sum()) + 1
    p = p[p.n_trials >= n_expected]
    note("incomplete session", n0, len(p), "participants")

    if args.exclude_attention_failures:
        n0 = len(p)
        p = p[p.passed_attention_check == 1]
        note("failed attention check (pre-registered rule)", n0, len(p), "participants")

    p["is_author"] = p.participant_id.isin(AUTHORS)
    p["source"] = p["source"].fillna("direct")

    # --- trials -------------------------------------------------------------
    t = t[t.participant_id.isin(p.participant_id)]
    t = t.merge(s[["sticker_id", "culture", "has_text", "intended_sentiment"]], on="sticker_id", how="left")
    t = t.rename(columns={"culture": "sticker_culture"})

    n0 = len(t)
    t = t[t.is_attention_check == 0]
    note("attention-check trial itself", n0, len(t), "trials")

    n0 = len(t)
    authored = t.apply(lambda r: r.sticker_culture in AUTHORS.get(r.participant_id, []), axis=1)
    t = t[~authored]
    note("trials on stickers the participant authored", n0, len(t), "trials")

    n0 = len(t)
    t = t[(t.rt_ms >= RT_MIN) & (t.rt_ms <= RT_MAX)]
    note(f"reaction time outside {RT_MIN} ms - {RT_MAX // 1000} s", n0, len(t), "trials")

    if args.drop_flagged and args.drop_flagged.exists():
        flagged = set(pd.read_csv(args.drop_flagged).sticker_id)
        n0 = len(t)
        t = t[~t.sticker_id.isin(flagged)]
        note(f"flagged stickers ({len(flagged)}; insiders disagreed with the key)", n0, len(t), "trials")

    # --- derived columns ----------------------------------------------------
    t = t.merge(p[["participant_id", "fam_turkish", "fam_chinese", "fam_american", "source",
                   "meme_fluency", "sticker_use_frequency", "bilingual", "age_bracket", "native_language"]],
                on="participant_id", how="left").rename(columns={"age_bracket": "age"})
    t["familiarity"] = [r[FAM_COL[c]] for c, r in zip(t.sticker_culture, t.to_dict("records"))]
    t["in_group"] = t.familiarity.map(GROUP)
    t["correct"] = (t.response == t.intended_sentiment).astype(int)
    t["changed_answer"] = t.changed_answer.fillna(0).astype(int)

    # --- outputs ------------------------------------------------------------
    PROC.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    sfx = args.suffix
    cols = ["participant_id", "sticker_id", "sticker_culture", "has_text", "intended_sentiment", "trial_order",
            "context", "response", "correct", "confidence", "rt_ms", "changed_answer", "familiarity", "in_group",
            "source", "meme_fluency", "sticker_use_frequency", "bilingual", "age", "native_language"]
    t[cols].to_csv(PROC / f"trials_clean{sfx}.csv", index=False)

    p_out = p[p.participant_id.isin(t.participant_id)].copy()
    p_out = p_out.drop(columns=["user_agent"]).rename(columns={"age_bracket": "age"})
    p_out.to_csv(PROC / f"participants_clean{sfx}.csv", index=False)

    summary = t.pivot_table(index="participant_id", columns="context", values="correct", aggfunc="mean")
    summary["n_trials"] = t.groupby("participant_id").size()
    summary = summary.join(t.pivot_table(index="participant_id", columns="in_group", values="correct", aggfunc="mean")
                           .add_prefix("acc_"))
    summary.reset_index().to_csv(PROC / f"participant_summary{sfx}.csv", index=False)

    pd.DataFrame(log).to_csv(TABLES / f"cleaning_log{sfx}.csv", index=False)

    print(pd.DataFrame(log).to_string(index=False))
    print(f"\nkept: {t.participant_id.nunique()} participants, {len(t)} trials")
    print("natives per culture:", {c: int((p_out[FAM_COL[c]] == "native").sum()) for c in FAM_COL})
    print("by source:", p_out.source.value_counts().to_dict())
    print(f"wrote {PROC / f'trials_clean{sfx}.csv'} and friends")


if __name__ == "__main__":
    main()
