# Sticker Comms

**Can people tell what a WhatsApp sticker means when it comes from a culture they're not part of, and does seeing it inside a chat help?**

Module Project 2 (Statistical Analysis), Duke AIPI 510. A within-subject experiment: participants judge the intended sentiment (positive / negative / sarcastic) of 30 Turkish, Chinese and English/American stickers. Each sticker is shown alone, in a mock chat, or as the chat line only (sticker hidden), with the condition counterbalanced by a Latin square.

The full design, hypotheses, analysis plan and timeline are in [PROJECT_BRIEF.md](PROJECT_BRIEF.md).

## Repository layout

```
data/
  stimuli.csv           one row per sticker: answer key (intended_sentiment), chat line, metadata
  sticker_sets.csv      generated: Latin-square set (A/B/C) per sticker
  raw/                  exported responses (participants.csv, trials.csv, freetext.csv, starts.csv)
  processed/            cleaned data
stimuli/                sticker images (placeholders until the real ones are dropped in)
web/                    the task page (vanilla HTML/JS, hosted on GitHub Pages)
backend/Code.gs         Google Apps Script that writes responses to a Google Sheet
src/
  collection/           placeholder stickers, condition assignment, response export
  cleaning/             cleaning script
  analysis/             power analysis, hypothesis tests, mixed model
  viz/                  figures
outputs/                figures/ and tables/ produced by the scripts
report/                 report draft
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Pipeline

```bash
# 1. Power analysis -> outputs/tables/power_*.csv, outputs/figures/power_curve.png
python src/analysis/power_analysis.py

# 2. Placeholder sticker images -> stimuli/*.svg (skips files that already exist)
python src/collection/make_placeholder_stickers.py

# 3. Latin-square assignment -> data/sticker_sets.csv, web/conditions.json
#    Re-run after ANY edit to data/stimuli.csv.
python src/collection/assign_conditions.py

# 4. Export responses from the Google Sheet -> data/raw/*.csv
python src/collection/export_responses.py --url "<Apps Script URL>" --token "<EXPORT_TOKEN>"
```

Cleaning and analysis steps will be added here as the scripts land.

## Running the study

### Try it locally

```bash
python -m http.server 8765
```

Open <http://localhost:8765/web/>. With `ENDPOINT_URL` empty in `web/config.js` the page runs in **local mode**: nothing is sent anywhere, and the thank-you screen offers a JSON download. Those files can be turned into the raw CSVs with

```bash
python src/collection/export_responses.py --from-local path/to/json/folder
```

### Set up the response backend (once, ~5 min)

1. Create a blank Google Sheet.
2. Extensions → Apps Script. Replace the default code with [backend/Code.gs](backend/Code.gs).
3. Set `EXPORT_TOKEN` to a long random string (keep it private). `SECRET` must match `web/config.js`.
4. Deploy → New deployment → Web app. *Execute as:* Me. *Who has access:* Anyone. Authorize, copy the web app URL.
5. Paste the URL into `ENDPOINT_URL` in `web/config.js`, commit, push.
6. Complete the task once and check that rows appear in the `participants`, `trials` and `freetext` tabs.

If you later edit `Code.gs`, redeploy (Deploy → Manage deployments → edit → New version).

### Deploy the task page

The page is served by GitHub Pages from the repository root, so the link is
`https://burakdon.github.io/sticker-comms/web/`. Pushing to the Pages branch updates it within a minute or so.

### How the page collects data

- Every participant gets a random `participant_id` and a random rotation (0–2). The rotation maps sticker sets A/B/C to the three contexts, so across the sample each sticker appears equally often alone, in chat and text-only.
- Trial order is shuffled. One attention check (`ATTN_01`) is inserted in the middle third and always shown alone.
- Per trial: `response`, `confidence` (1–5) and `rt_ms` (stimulus shown → sentiment tapped).
- Submissions are sent once at the end. The payload is kept in the browser until the server confirms it, and re-sent on the next visit if the upload failed. The server ignores duplicate `participant_id`s, so retries are safe.
- A "start" ping on survey completion lets us count drop-outs.

## Replacing the placeholder stickers

The images in `stimuli/` are emoji stand-ins so the pipeline can be tested. To swap in a real sticker:

1. Save the image as `stimuli/<sticker_id>.png` (or `.webp`) — or host it elsewhere and use the full URL.
2. In `data/stimuli.csv`, update `file`, `description`, `intended_sentiment` and `chat_line`. Set `in_repo = 0` for licensed characters and host those outside the repo.
3. Run `python src/collection/assign_conditions.py` and push.

Don't add stickers with real faces of friends, classmates or children, or anything offensive.

## Data

- `data/stimuli.csv` is written by hand by the sticker authors (Burak: Turkish, teammate: Chinese, both: English/American). `intended_sentiment` is the sender-intent answer key. It is deliberately **not** included in `web/conditions.json`, so participants can't read it from the page.
- Responses are anonymous: random participant ID, demographics in brackets, no names or contact details.
- **Giveaway entries** (name + contact) live in a separate `giveaway` tab of the sheet, linked only by participant ID. The default export never pulls them; `python src/collection/export_responses.py --giveaway` writes them to `data/private/` (gitignored) and reports duplicate contacts. Delete the tab after the draw.

## Contributing

`main` ← `dev` ← personal branches (`dev-burak`, `dev-<teammate>`). Open PRs into `dev`; every PR is reviewed by the other team member before merging.
