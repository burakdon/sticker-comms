# Chinese integration: review and launch gates

Status: **DRAFT — not cleared for participant recruitment** (2026-10-31).

## Reported blank trials

The participant-facing box saying `sticker hidden` is intentional, not a failed
image. The user confirmed that this was the box they saw. PROJECT_BRIEF section
3.2 requires `text_only`. Each rotation has 12 text-only trials, 12 chat trials,
12 alone trials, and one attention check shown alone. Trial numbers are shuffled
and cannot identify a fixed sticker. No condition or hidden-box wording changed.

The live site still referenced 12 CN SVG placeholders when audited. Its 37 asset
URLs decoded successfully, but successful loading of a placeholder is not proof
that the final stimulus was deployed. The Pages source was verified separately
as `dev-burak` at repository root. A PR into `dev` does not update that deployment.

## Scope preservation

- Latest `dev` baseline: `6fb1d41f43f4f139c971afa71c8c90c71f9ac42b`.
- All non-CN stimuli.csv rows and conditions.json stimulus entries compare equal
  to that baseline. No TR/EN/ATTN asset changed.
- Chinese assets match the supplied SHA-256 manifest. Existing CN English lines
  and sender-intent labels were retained from the supplied final metadata.
- Twelve Chinese SVG placeholders are replaced by twelve supplied WebPs.
- No generated image, replacement of the green smile, or invented animation.
- The new image-load guard disables answers until the image loads, exposes a
  retry on load error/15-second timeout, and starts reaction timing after load.
  Text-only trials remain answerable without an image. Bonus image failure
  prevents a text response but leaves the optional skip available.

## Executed checks

PASS: seven Python integrity tests; all 37 local assets decoded in Chromium;
three complete 37-trial local/download runs, followed by three participant-style
runs at widths 1280/390/320 using real label/button clicks and seeded shuffles.
The latter cover all three sentiments, all five confidence ratings, change-answer,
required-field/under-18 validation, bilingual fields, attention pass and failure,
one free-text answer plus two skips, giveaway/extra mock posts, failed completion
submission with identical retry and pending-storage removal after acknowledgment.
All 111 captured trial records were checked against actual choices and conditions.
No horizontal overflow was found during those trials; light and dark displays
were exercised. Also passed: mock backend complete/duplicate/cleanup/retry;
blocked-image answer prevention, recovery on the same trial, and syntax checks.

NOT TESTED: real Google Apps Script/Sheets persistence and exported data
reconciliation; interrupted real server writes; actual mobile Safari/Android;
real China-network reachability; all random seeds and every browser. Browser
mock success is not confirmation of actual server persistence. No production
response was submitted by the audit.

## Remaining review gates

1. Research-owner review of the Chinese pairings, particularly context-dependent
   teasing/sarcasm in CN_TXT_06, CN_NOTXT_05 and CN_NOTXT_06. These are sender intent,
   not claims of universally recognized sentiment. Do not relabel to force agreement.
2. CN_NOTXT_05 originated at 66x50 and CN_NOTXT_04 at 144x106. The supplied upscales
   do not create detail. Owner must accept original quality or supply replacements.
3. The user approved image use in chat, but `in_repo=0` files currently live in the
   repository. This does not enforce the brief's external-hosting rule and does
   not establish a license. Resolve permitted hosting/clearance with the owner;
   do not silently change the research brief or claim licensing is verified.
4. Use an isolated test Apps Script deployment and Sheet to verify actual saved
   participant/trial/free-text rows, IDs, retries and CSV export before launch.
5. Burak reviews the PR. Owners decide merge and deployment separately; verify
   the deployed commit and asset paths after deployment. No automated merge or
   production deployment is part of this PR replacement.

## Reproduce the new failure test

Run the local static server at port 8765 from the repository root. Install
Playwright and Chromium in a test environment, then run:

```sh
node tests/browser_image_failure.cjs
node tests/browser_participant.cjs
```

If Playwright is outside the repository, set `PLAYWRIGHT_MODULE` to its module
directory. Set `TEST_OUTPUT_DIR` to an existing temporary output directory to
save participant screenshots and synthetic payloads. The failure test blocks
external requests and all non-GET traffic. The participant test mocks only
`https://test.invalid/submit`, blocking all other external requests. Both override
the local backend configuration. Neither submits to the production backend.
