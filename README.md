# Sticker Comms

**Can people tell what a WhatsApp sticker means when it comes from a culture they're not part of, and does seeing it inside a chat help?**

Module Project 2 (Statistical Analysis), Duke AIPI 510. A within-subject experiment: participants judge the intended sentiment (positive / negative / sarcastic) of 30 Turkish, Chinese and English/American stickers. Each sticker is shown alone, in a mock chat, or as the chat line only (sticker hidden), with the condition counterbalanced by a Latin square.

The full design, hypotheses, analysis plan and timeline are in [PROJECT_BRIEF.md](PROJECT_BRIEF.md).

## Repository layout

```
data/
  stimuli.csv           one row per sticker: answer key (intended_sentiment), chat line, metadata
  sticker_sets.csv      generated: Latin-square set (A/B/C) per sticker
  raw/                  exported responses (participants.csv, trials.csv, freetext.csv)
  processed/            cleaned data
stimuli/                sticker images that can be redistributed (in_repo = 1)
web/                    task page (GitHub Pages) + generated conditions.json
src/
  collection/           condition assignment, response export
  cleaning/             cleaning script
  analysis/             power analysis, hypothesis tests, mixed model
  viz/                  figures
outputs/                figures/ and tables/ produced by the scripts
report/                 report draft
```

## Reproducing

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. Power analysis -> outputs/tables/power_*.csv, outputs/figures/power_curve.png
python src/analysis/power_analysis.py

# 2. Latin-square assignment -> data/sticker_sets.csv, web/conditions.json
python src/collection/assign_conditions.py
```

Cleaning and analysis steps will be added here as the scripts land.

## Data

- `data/stimuli.csv` is written by hand by the sticker authors (Burak: Turkish, teammate: Chinese, both: English/American). `intended_sentiment` is the sender-intent answer key.
- Licensed characters (e.g. Shrek, Hello Kitty) are shown on the task page but not committed (`in_repo = 0`); they are described in `stimuli.csv` instead.
- Responses are anonymous: a random participant ID, demographics in brackets, no names or contact details.

## Contributing

`main` ← `dev` ← personal branches (`dev-burak`, `dev-<teammate>`). Open PRs into `dev`; every PR is reviewed by the other team member before merging.
