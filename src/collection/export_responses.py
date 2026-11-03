"""Export collected responses to data/raw/*.csv.

Two sources:
  * the Apps Script backend (GET with the export token), the normal case
  * local JSON files downloaded from the task page in local mode or after a
    failed upload (`--from-local <dir>`)

Writes data/raw/participants.csv, trials.csv, freetext.csv and starts.csv with a
fixed column order. Existing files are overwritten; the sheet is the source of
truth, so re-running is always safe.

Usage:
    python src/collection/export_responses.py --url "<web app url>" --token "<EXPORT_TOKEN>"
    python src/collection/export_responses.py --from-local data/raw/local_json/

    # or put STICKER_EXPORT_URL and STICKER_EXPORT_TOKEN in a .env file at the repo
    # root (gitignored) and just run
    python src/collection/export_responses.py
"""

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"


def load_dotenv(path: Path = ROOT / ".env") -> None:
    """Read KEY=VALUE lines from .env (gitignored) into os.environ, without overriding."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv()

COLUMNS = {
    "starts": ["participant_id", "started_at", "device", "user_agent", "received_at", "source"],  # source derived from UA
    "participants": [
        "participant_id", "rotation", "fam_turkish", "fam_chinese", "fam_american",
        "meme_fluency", "native_language", "bilingual", "other_languages",
        "age_bracket", "sticker_use_frequency",
        "device", "user_agent", "screen_width", "started_at", "finished_at",
        "passed_attention_check", "n_trials", "received_at", "source",
    ],
    "trials": [
        "participant_id", "sticker_id", "trial_order", "context", "is_attention_check",
        "response", "confidence", "rt_ms", "changed_answer",
    ],
    "freetext": ["participant_id", "sticker_id", "text"],
    "extra": ["participant_id", "aipi_cohort", "aipi520_midterm", "aipi510_project1", "received_at"],
}


def fetch_from_backend(url: str, token: str) -> dict[str, list[dict]]:
    req = Request(f"{url}?{urlencode({'token': token})}", headers={"User-Agent": "sticker-comms-export"})
    with urlopen(req, timeout=60) as resp:
        payload = json.load(resp)
    if not payload.get("ok"):
        sys.exit(f"backend error: {payload.get('error')}")
    return payload["sheets"]


def load_local(dir_path: Path) -> dict[str, list[dict]]:
    """Merge payloads downloaded from the task page (one JSON file per participant)."""
    sheets: dict[str, list[dict]] = {name: [] for name in COLUMNS}
    seen = set()
    files = sorted(dir_path.glob("*.json"))
    if not files:
        sys.exit(f"no .json files in {dir_path}")
    for f in files:
        payload = json.loads(f.read_text(encoding="utf-8"))
        if payload.get("type") != "complete":
            continue
        pid = payload["participant"]["participant_id"]
        if pid in seen:
            print(f"duplicate participant {pid} in {f.name}; skipping")
            continue
        seen.add(pid)
        sheets["participants"].append(payload["participant"])
        sheets["trials"].extend(payload.get("trials", []))
        sheets["freetext"].extend(payload.get("freetext", []))
    return sheets


def write_csvs(sheets: dict[str, list[dict]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, cols in COLUMNS.items():
        df = pd.DataFrame(sheets.get(name, []))
        if "user_agent" in df:
            # The page appends " src=<channel>" to the UA (no backend column needed).
            ua = df["user_agent"].astype(str)
            df["source"] = ua.str.extract(r" src=([a-z0-9_-]+)$")[0].fillna("direct")
            df["user_agent"] = ua.str.replace(r" src=[a-z0-9_-]+$", "", regex=True)
        df = df.reindex(columns=cols)
        if name == "trials" and len(df):
            df = df.sort_values(["participant_id", "trial_order"])
        df.to_csv(out_dir / f"{name}.csv", index=False)
        print(f"{name:13s} {len(df):5d} rows -> {out_dir / f'{name}.csv'}")

    p = pd.DataFrame(sheets.get("participants", []))
    if len(p):
        n = len(p)
        passed = pd.to_numeric(p.get("passed_attention_check"), errors="coerce").fillna(0).astype(int).sum()
        print(f"\n{n} completed participants, {int(passed)} passed the attention check")
        for col in ["fam_turkish", "fam_chinese", "fam_american"]:
            if col in p:
                natives = int((p[col] == "native").sum())
                print(f"  {col}: {natives} native")


def export_giveaway(url: str, token: str) -> None:
    """Pull giveaway entries (identifying) to data/private/, which git ignores.

    Prints one row per distinct contact with the number of participant_ids that
    used it, so duplicate participation is easy to spot before the draw.
    """
    req = Request(f"{url}?{urlencode({'token': token, 'sheet': 'giveaway'})}",
                  headers={"User-Agent": "sticker-comms-export"})
    with urlopen(req, timeout=60) as resp:
        payload = json.load(resp)
    if not payload.get("ok"):
        sys.exit(f"backend error: {payload.get('error')}")
    df = pd.DataFrame(payload["sheets"].get("giveaway", []),
                      columns=["participant_id", "name", "contact", "received_at"])
    out = ROOT / "data" / "private"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "giveaway.csv", index=False)
    print(f"{len(df)} entries -> {out / 'giveaway.csv'} (gitignored)")
    if len(df):
        key = df["contact"].astype(str).str.strip().str.lower()
        dupes = df.assign(_k=key).groupby("_k")["participant_id"].agg(["count", list])
        dupes = dupes[dupes["count"] > 1]
        print(f"{key.nunique()} unique contacts, {len(dupes)} entered more than once")
        if len(dupes):
            print(dupes.to_string())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default=os.environ.get("STICKER_EXPORT_URL"), help="Apps Script web app URL")
    parser.add_argument("--token", default=os.environ.get("STICKER_EXPORT_TOKEN"), help="EXPORT_TOKEN from Code.gs")
    parser.add_argument("--from-local", type=Path, help="directory of downloaded JSON payloads instead of the backend")
    parser.add_argument("--out", type=Path, default=RAW_DIR)
    parser.add_argument("--giveaway", action="store_true",
                        help="instead of study data, pull giveaway entries to data/private/ (gitignored)")
    args = parser.parse_args()

    if args.giveaway:
        if not (args.url and args.token):
            sys.exit("--giveaway needs --url and --token (or the .env variables)")
        export_giveaway(args.url, args.token)
        return

    if args.from_local:
        sheets = load_local(args.from_local)
    elif args.url and args.token:
        sheets = fetch_from_backend(args.url, args.token)
    else:
        sys.exit("give --url and --token (or STICKER_EXPORT_URL / STICKER_EXPORT_TOKEN), or --from-local DIR")

    write_csvs(sheets, args.out)


if __name__ == "__main__":
    main()
