# Sticker Comms

**Can people tell what a WhatsApp sticker means when it comes from a culture they're not part of, and does seeing it inside a chat help?**

Duke AIPI 510, Module Project 2 (Statistical Analysis). Burak Dönbekci and Canyang Xu.

- **Written report:** <https://burakdon.github.io/sticker-comms/report/>
- **The study itself** (still live): <https://burakdon.github.io/sticker-comms/web/>
- **Design and analysis plan**, written before data collection: [PROJECT_BRIEF.md](PROJECT_BRIEF.md)

## The experiment

A within-subject online experiment. 70 participants judged the intended sentiment (positive / negative / sarcastic) of 36 stickers: 12 Turkish, 12 Chinese and 12 English/American, half with text on the sticker and half without. Each sticker appeared once per person in one of three conditions, assigned by a Latin square so every sticker got every condition equally often across the sample:

| Condition | What the participant saw |
|---|---|
| alone | the sticker by itself |
| chat | the sticker as a reply to a one-line message in a mock chat |
| text-only | the same chat with the sticker hidden (control: how much does the message alone give away?) |

The answer key is sender intent: the author of each culture's set labeled what they mean when they send it, and native participants' agreement with those labels was checked afterwards.

## Main results

| | Result |
|---|---|
| Chat vs alone (H1, primary) | +11.3 points, 95% CI [6.6, 16.0], d_z = 0.58, p < .0001 (paired t, n = 70) |
| Chat vs text-only (H5) | +7.5 points, 95% CI [2.9, 12.1], p = .002: the sticker adds meaning beyond the message |
| In-group advantage (H2) | OR 1.51 [1.26, 1.81], mixed logistic regression with participant and sticker random intercepts |
| Context × in-group (H3) | not supported; hiding the sticker removes the native advantage instead (OR 0.65 [0.48, 0.88]) |
| Outsiders vs chance (H4) | 67% correct on no-text stickers with no context, chance 33%, p < .0001 |

The context effect holds under the pre-registered attention-check exclusion, with the six low-agreement stickers removed, and with both applied together. Full numbers are in `outputs/tables/`.

## Repository layout

```
data/
  stimuli.csv           one row per sticker: answer key, chat line, metadata
  sticker_sets.csv      Latin-square set (A/B/C) per sticker, generated
  raw/                  exported responses: participants, trials, freetext, starts
  processed/            cleaned data and per-participant summaries
stimuli/                sticker images
web/                    the task page (vanilla HTML/JS on GitHub Pages)
backend/Code.gs         Google Apps Script that writes responses to a Google Sheet
src/
  collection/           condition assignment, response export, placeholder stickers
  cleaning/             clean_trials.py (logged exclusions)
  analysis/             power analysis, answer-key check, confirmatory tests, mixed model
  viz/                  report and slide figures
outputs/                figures/ and tables/ produced by the scripts
flyer/                  recruitment flyer with a QR code (channel-tagged link)
report/                 written report (index.html), presentation deck and its build scripts
tests/                  integrity checks for the stimulus set and task page
```

## Reproducing the analysis

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python src/analysis/power_analysis.py            # a priori power: analytic + simulation
python src/cleaning/clean_trials.py              # data/raw -> data/processed, with outputs/tables/cleaning_log.csv
python src/analysis/validate_answer_key.py       # insider agreement per sticker; flags < 50%
python src/analysis/primary_tests.py             # H1, H5, RM-ANOVA + Holm post hocs, H4
python src/analysis/mixed_model.py               # H2, H3: crossed random-effects logistic regression
python src/viz/figures.py                        # report figures

# Sensitivity analyses
python src/cleaning/clean_trials.py --exclude-attention-failures --suffix _prereg && python src/analysis/primary_tests.py --suffix _prereg
python src/cleaning/clean_trials.py --drop-flagged outputs/tables/flagged_stickers.csv --suffix _noflag && python src/analysis/primary_tests.py --suffix _noflag
python src/cleaning/clean_trials.py --exclude-attention-failures --drop-flagged outputs/tables/flagged_stickers.csv --suffix _both && python src/analysis/primary_tests.py --suffix _both
```

Everything runs offline from the committed `data/raw/` files. Re-exporting from the Google Sheet (`src/collection/export_responses.py`) needs the private token in `.env` (see `.env.example`) and is not required.

Slide figures and the deck: `python src/viz/slide_figures.py`, then `node report/build_deck.js` (needs `pptxgenjs`).

## Data and privacy

- Responses are anonymous: a random participant ID, age, familiarity ratings and language, no names or contact details. `data/raw/` and `data/processed/` are committed in full.
- The two authors are retained as participants only for stickers they did not author (`src/cleaning/clean_trials.py`, `AUTHORS`).
- Giveaway entries (name + contact) sit in a separate sheet tab that the default export never pulls, and are kept out of the repository. The end-of-study course-grade question (`extra.csv`) is likewise kept local.
- Stickers are reproduced for non-commercial research. Several contain profanity or licensed characters, which is noted in the report's limitations.

## Running the study again

The task page works as-is: open `web/` on any static host, or `python -m http.server 8765` and visit <http://localhost:8765/web/>. With `ENDPOINT_URL` empty in `web/config.js` it runs in local mode and offers a JSON download at the end, which `export_responses.py --from-local` turns into the raw CSVs.

To collect centrally, paste [backend/Code.gs](backend/Code.gs) into a Google Sheet's Apps Script, set `EXPORT_TOKEN`, deploy it as a web app ("execute as me", "anyone"), and put the web-app URL in `web/config.js`. Rotation, trial order and the attention check are all handled client-side; submissions are retried until the server confirms and deduplicated by participant ID.

## Branching

`main` ← `dev` ← personal branches. All work went through pull requests reviewed by the other author.
