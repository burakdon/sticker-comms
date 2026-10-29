# Sticker Sentiment Experiment — Project Brief

**Course:** Duke AIPI 510 — Module Project 2: Statistical Analysis
**Team:** Burak (github: burakdon) + teammate
**Presentation:** Mon Nov 3, 2026 (8 min max, in class)
**Brief last revised:** Wed Oct 28, 2026

This file is the single source of truth for the study design. Read it before touching code.

---

## 1. Assignment requirements

### 1.1 Written report (submitted via Byline link)
Title & Abstract · Background & Motivation · Null and Alternative Hypotheses · Experimental Design (IVs/DVs, control conditions, randomization) · Power Analysis (assumptions, calculations or software used) · Data Collection & Cleaning Procedures · Statistical Analysis (tests, rationale, assumptions checked, p-values, CIs, effect sizes, post hoc tests if appropriate) · Interpretation · Limitations · Conclusion & Recommendations · References.

### 1.2 GitHub repository
- All code for collection, cleaning, analysis — **scripts, not notebooks**
- README with reproduction instructions
- Branches + PRs; **each member makes at least one PR**, with real PR reviews
- Raw and cleaned data (or clear description if sensitive)

### 1.3 Presentation (8 min)
Motivation · research question & hypothesis · the experiment · key results & visualizations · takeaways & limitations.

---

## 2. Research question

**Can people tell what a WhatsApp sticker means when it comes from a culture they are not part of — and does seeing it inside a chat help?**

Motivation: our group chat runs on stickers, many of them culture-specific (Turkish politicians, Turkish text memes, Chinese stickers). People outside that culture react to them anyway. Do they actually get the meaning, or are they guessing?

Framing for the report: the in-group advantage in cross-cultural emotion recognition (Elfenbein & Ambady, 2002), applied to a modern communication channel.

---

## 3. Experimental design

One online session, ~4 minutes on a phone, one link for everyone. No separate stimulus-collection phase.

### 3.1 Stimuli — 30 stickers + 1 attention check

| | text on sticker | no text | author (writes answer key + chat line) |
|---|---|---|---|
| **Turkish (TR)** | 5 | 5 | Burak |
| **Chinese (CN)** | 5 | 5 | teammate |
| **English / American (EN)** | 5 | 5 | both, checked by an American classmate |

For every sticker the author records, **before launch**:
- `intended_sentiment` — positive / negative / sarcastic. This is the answer key (**sender intent**).
- `chat_line` — a realistic message, **written in English**, that the sticker would be sent in reply to. English so that the context is readable by everyone; the sticker's own text stays in its original language.

Sentiment roughly balanced within each culture (~4/3/3 across the three options).

**Exclude:** any sticker showing the face of a classmate, friend, or child. Profanity is allowed (it is part of how these stickers are used); say so in the report's limitations/ethics note.
**Licensing:** licensed characters (Shrek, Hello Kitty, etc.) may be shown on the task page but are **not committed to the repo** (`in_repo = 0` in `data/stimuli.csv`; describe them in text).

### 3.2 Variables

| Role | Variable | Levels | How set |
|---|---|---|---|
| **Randomized IV** | `context` | `alone` · `chat` · `text_only` | Latin square on participant (§3.4) |
| Stimulus factor | `sticker_culture` | TR · CN · EN | fixed by stimulus set |
| Stimulus factor | `has_text` | 0 · 1 | fixed by stimulus set |
| **Measured (quasi-experimental)** | `in_group` | 0 · 1 | 1 if participant reports `native` familiarity with the sticker's culture |
| **Primary DV** | `correct` | 0 · 1 | response == `intended_sentiment` |
| Secondary DVs | `confidence` (1–5), `rt_ms` | | logged per trial |

Context conditions:
- **alone** — the sticker by itself.
- **chat** — the sticker shown as "You" replying to the friend's `chat_line` in a mock chat.
- **text_only** — the same mock chat, but the sticker is hidden ("You: [ ? ]"). Measures how much the chat line alone gives away; the sticker's added value is `chat − text_only`.

### 3.3 Session flow

1. **Consent + pre-survey (~30 s):** familiarity with Turkish / Chinese / American culture (none · some · native each) · meme fluency (1–5) · native language · age bracket · sticker-use frequency (daily · weekly · rarely) · device (auto-detected).
2. **30 trials + 1 attention check, random order.** Each sticker appears exactly once, in one context condition. Question: *"What does the sender mean?"* (positive · negative · sarcastic) then *"How confident are you?"* (1–5).
3. **Bonus block (optional):** 3 stickers shown alone — *"What message would you send this after?"* (free text). Placed last so it cannot influence the main trials.
4. Thank-you screen.

### 3.4 Randomization (Latin square)

`src/collection/assign_conditions.py` splits the 30 stickers into three sets **A, B, C** of 10, balanced on culture × has_text (and spread across sentiment as far as possible). Each participant is assigned one of three rotations:

| rotation | alone | chat | text_only |
|---|---|---|---|
| 0 | A | B | C |
| 1 | B | C | A |
| 2 | C | A | B |

Across the sample, every sticker appears equally often in every condition. Rotation is drawn at random on the client when the participant ID is generated; trial order is shuffled independently per participant.

### 3.5 Answer-key validation (pre-registered rule)

For each sticker, take in-group participants' trials where the sticker is visible (alone + chat). If **< 50%** of them agree with the author's `intended_sentiment`, the sticker is flagged and excluded from confirmatory analyses (reported separately). With 15 natives per culture this is ~10 responses per sticker. Per-sticker in-group agreement is itself a figure (where do insiders disagree — likely the sarcastic ones).

---

## 4. Hypotheses

| | H₀ | H₁ |
|---|---|---|
| **H1** (primary, randomized) | Accuracy is equal in `chat` and `alone` | `chat` > `alone` |
| **H2** | No in-group advantage | in-group > out-group |
| **H3** | The context effect is equal for in-group and out-group | context helps out-group more (`context × in_group`) |
| **H4** | Out-group accuracy on culture-specific no-text stickers (TR, CN) = chance (1/3) | above chance |
| **H5** | Accuracy is equal in `chat` and `text_only` | `chat` > `text_only` (the sticker adds information beyond the line) |

**Exploratory (label as such):** text vs. no-text by script (Latin vs. Chinese characters); confidence–accuracy calibration; whether outsiders' free-text lines imply the same sentiment as insiders'.

---

## 5. Statistical analysis plan

| Hypothesis | Test | Effect size |
|---|---|---|
| H1, H5 | Paired t-test on per-person accuracy; Wilcoxon signed-rank if Shapiro–Wilk on differences fails | Cohen's d_z, 95% CI of mean difference |
| context overall | One-way repeated-measures ANOVA (3 levels); Mauchly sphericity, Greenhouse–Geisser if violated; **Holm-corrected paired post hocs**; Friedman as non-parametric fallback | partial η² |
| H2, H3 | Mixed-effects logistic regression: `correct ~ context * in_group + has_text + (1 | participant) + (1 | sticker)` | odds ratios, 95% CI |
| H4 | Exact binomial test vs. p = 1/3 on out-group trials | exact CI, Cohen's h |

Assumptions to check and report: normality of paired differences (Shapiro–Wilk + QQ plot), sphericity (Mauchly), and why the mixed model is needed (30 non-independent trials per person, stickers as a random sample).

---

## 6. Power analysis

- Primary test: paired t-test (H1), α = 0.05, power = 0.80, two-sided.
- d_z = 0.4 → **n ≈ 52**; d_z = 0.5 → n ≈ 34.
- **Target 70–100 participants, including ≥ 15 natives per culture** (TR from Burak's network, CN from teammate's, US from class).
- H3 (interaction) is adequately powered only for medium-to-large effects — say so.
- `src/analysis/power_analysis.py` does it two ways: (1) analytic (`statsmodels` `TTestPower`), (2) simulation of the actual trial structure (10 binary trials per condition per person, participant and sticker random effects) to show what accuracy lift d_z = 0.4 corresponds to.
- Pilot (5 people) re-estimates baseline accuracy and the SD of per-person differences.

---

## 7. Data schema

### `data/stimuli.csv` — one row per sticker (hand-edited by authors)
`sticker_id` · `culture` (TR/CN/EN/ATTN) · `has_text` (0/1) · `author` · `description` · `intended_sentiment` · `chat_line` · `in_repo` (0/1) · `file` · `notes`

### `data/sticker_sets.csv` — generated by `assign_conditions.py`
`sticker_id` · `set` (A/B/C)

### `data/raw/participants.csv` — one row per person
`participant_id` · `rotation` · `fam_turkish` · `fam_chinese` · `fam_american` · `meme_fluency` · `native_language` · `bilingual` (yes/no) · `other_languages` (free text) · `age_bracket` · `sticker_use_frequency` · `device` · `started_at` · `finished_at` · `passed_attention_check`

### `data/raw/trials.csv` — one row per trial
`participant_id` · `sticker_id` · `trial_order` · `context` (alone/chat/text_only) · `response` · `confidence` · `rt_ms`

### `data/raw/freetext.csv` — bonus block
`participant_id` · `sticker_id` · `text`

### Derived by the cleaning script
- `data/processed/trials_clean.csv` — adds `correct`, `in_group`, `sticker_culture`, `has_text`; drops failed attention checks, rt < 300 ms or > 30 s, incomplete sessions, flagged stickers.
- `data/processed/participant_summary.csv` — accuracy per participant × context (× in_group).

Cleaning rules are logged with counts dropped per rule.

---

## 8. Repo structure

```
sticker-comms/
├── README.md
├── PROJECT_BRIEF.md
├── requirements.txt
├── data/
│   ├── stimuli.csv
│   ├── sticker_sets.csv          (generated)
│   ├── raw/
│   └── processed/
├── stimuli/                      (only in_repo = 1 images)
├── web/                          (task page, GitHub Pages)
├── src/
│   ├── collection/
│   │   ├── assign_conditions.py
│   │   └── export_responses.py
│   ├── cleaning/clean_trials.py
│   ├── analysis/
│   │   ├── power_analysis.py
│   │   ├── validate_answer_key.py
│   │   ├── primary_tests.py      (H1, H4, H5, RM-ANOVA + post hocs)
│   │   └── mixed_model.py        (H2, H3)
│   └── viz/figures.py
├── outputs/{figures,tables}/
└── report/
```

**Collection backend:** static page on GitHub Pages, vanilla JS; responses POSTed to a Google Sheet via Apps Script; `export_responses.py` pulls the sheet to `data/raw/`.

**Branching:** `main` ← `dev` ← feature branches (`dev-burak`, `dev-<teammate>`). Every merge into `dev` goes through a PR reviewed by the other member.

---

## 9. Timeline

| Day | Work |
|---|---|
| **Wed Oct 28** | Repo scaffold. Burak writes TR stickers + lines; teammate writes CN. Build task page + backend. |
| **Thu Oct 29** | 5-person pilot in the morning, fix bugs, **launch in the evening**. |
| **Fri–Sat Oct 30 – Nov 1** | Data collection. Write cleaning + analysis scripts against pilot/test data. |
| **Sun Nov 2** | Final analysis, figures, report to Byline, slides. |
| **Mon Nov 3** | Present. |

**Presentation hook:** show the class three stickers (one per culture) alone — vote — then the same ones in chat — vote again.

### Figures to plan for
- Accuracy by context × in_group (grouped bars with CIs) — the headline
- Context lift for in-group vs. out-group (interaction plot)
- Per-sticker decodability ranking, colored by culture
- In-group agreement with the author per sticker
- Power curve
- Calibration: confidence vs. accuracy

---

## 10. Open items
- [ ] American classmate to write/check the 10 EN lines.
- [ ] Teammate confirms they can reach ~15 Chinese-native participants.
- [ ] Confirm with instructor that a one-line consent note is sufficient (anonymous, non-sensitive data).

## 11. Known limitations to write up
- Convenience sample (classmates/friends), skews young and online.
- `in_group` is measured, not randomized → quasi-experimental for that factor.
- Answer key is sender intent from one author per culture; validated by in-group agreement but sarcasm is inherently ambiguous.
- EN stickers authored by non-native speakers unless the classmate check happens.
- Chat lines are in English for all cultures — less authentic for TR/CN, deliberately chosen so context is accessible.
- 30 trials per person → mixed model handles non-independence.
- Interaction underpowered for small effects.
- Stickers shown outside the WhatsApp UI.
