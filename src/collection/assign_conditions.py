"""Latin-square assignment of stickers to context conditions.

Splits the 30 experimental stickers into three sets (A, B, C) of 10, balanced on
culture x has_text and spread across intended sentiment. Each participant gets one
of three rotations, so across the sample every sticker appears equally often in
every context condition (alone / chat / text_only).

Outputs:
    data/sticker_sets.csv   sticker_id -> set
    web/conditions.json     sets, rotations, stimulus metadata for the task page

Usage:
    python src/collection/assign_conditions.py
"""

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SETS = ["A", "B", "C"]
CONDITIONS = ["alone", "chat", "text_only"]
SENTIMENT_ORDER = {"positive": 0, "negative": 1, "sarcastic": 2}

# Rotation r: set SETS[(i + r) % 3] is shown in CONDITIONS[i].
ROTATIONS = {
    r: {CONDITIONS[i]: SETS[(i + r) % 3] for i in range(3)} for r in range(3)
}


def assign_sets(stimuli: pd.DataFrame) -> pd.DataFrame:
    """Deal each culture x has_text cell of 5 stickers across sets A/B/C.

    Each cell contributes 2/2/1 stickers; which set receives the single sticker
    rotates across cells, so every set ends up with exactly 10. Within a cell,
    stickers are sorted by intended sentiment before dealing so each set gets a
    spread of sentiments rather than a cluster.
    """
    exp = stimuli[stimuli["culture"] != "ATTN"].copy()
    exp["_sent"] = exp["intended_sentiment"].map(SENTIMENT_ORDER).fillna(9)

    assigned = []
    cells = exp.groupby(["culture", "has_text"], sort=True)
    for cell_idx, (_, cell) in enumerate(cells):
        cell = cell.sort_values(["_sent", "sticker_id"])
        short_set = SETS[(2 - cell_idx) % 3]  # set receiving only 1 from this cell
        order = [s for s in SETS if s != short_set] * 2 + [short_set]
        # Dealing round-robin over `order` gives 2/2/1.
        for sticker_id, set_name in zip(cell["sticker_id"], order):
            assigned.append({"sticker_id": sticker_id, "set": set_name})

    sets = pd.DataFrame(assigned)
    counts = sets["set"].value_counts()
    expected = len(exp) // 3
    if len(exp) % 3 or not (counts == expected).all():
        raise ValueError(f"Unbalanced sets: {counts.to_dict()}")
    return sets


def check_completeness(stimuli: pd.DataFrame) -> list[str]:
    """Return warnings for stickers still missing fields the task page needs."""
    warnings = []
    exp = stimuli[stimuli["culture"] != "ATTN"]
    for col in ["intended_sentiment", "chat_line", "file"]:
        missing = exp.loc[exp[col].isna() | (exp[col] == ""), "sticker_id"]
        if len(missing):
            warnings.append(f"{len(missing)} stickers missing `{col}`")
    bad = exp.loc[
        exp["intended_sentiment"].notna()
        & ~exp["intended_sentiment"].isin(SENTIMENT_ORDER),
        "sticker_id",
    ]
    if len(bad):
        warnings.append(f"invalid intended_sentiment for: {', '.join(bad)}")
    return warnings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--stimuli", default=ROOT / "data" / "stimuli.csv")
    parser.add_argument("--sets-out", default=ROOT / "data" / "sticker_sets.csv")
    parser.add_argument("--json-out", default=ROOT / "web" / "conditions.json")
    args = parser.parse_args()

    stimuli = pd.read_csv(args.stimuli, dtype={"has_text": "Int64"})
    stimuli = stimuli.fillna("")
    stimuli["intended_sentiment"] = stimuli["intended_sentiment"].replace("", pd.NA)

    for w in check_completeness(stimuli):
        print(f"WARNING: {w}")

    sets = assign_sets(stimuli)
    sets.to_csv(args.sets_out, index=False)

    meta = stimuli.merge(sets, on="sticker_id", how="left")
    payload = {
        "conditions": CONDITIONS,
        "rotations": {str(r): rot for r, rot in ROTATIONS.items()},
        "stickers": [
            {
                "sticker_id": row.sticker_id,
                "culture": row.culture,
                "has_text": int(row.has_text),
                "set": row.set if isinstance(row.set, str) else None,
                "chat_line": row.chat_line or None,
                "file": row.file or None,
            }
            for row in meta.itertuples()
        ],
    }
    # Answer key stays out of the JSON so participants can't read it from the page.
    Path(args.json_out).write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    summary = sets.merge(stimuli, on="sticker_id").pivot_table(
        index=["culture", "has_text"], columns="set", values="sticker_id", aggfunc="count"
    )
    print(summary.to_string())
    print(f"Wrote {args.sets_out} and {args.json_out}")


if __name__ == "__main__":
    main()
