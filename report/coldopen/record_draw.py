"""Render the squishy-draw animation (draw.html) to an MP4.

Winner names are passed on the command line so they never live in the repo.

Usage:
  python report/coldopen/record_draw.py "Winner One" "Winner Two" [--entries 45]
  -> report/coldopen/draw.mp4
"""

import argparse
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent


def ffmpeg_exe() -> str:
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("winners", nargs="+")
    ap.add_argument("--entries", type=int, default=45)
    ap.add_argument("--names", default=str(HERE.parents[1] / "data" / "private" / "giveaway.csv"),
                    help="CSV with a name column; real names roll past on the reels (default: the giveaway export)")
    ap.add_argument("--out", default=str(HERE / "draw.mp4"))
    a = ap.parse_args()

    q = {"w": "|".join(a.winners), "n": a.entries}
    names_path = Path(a.names)
    if names_path.exists():
        import csv
        with open(names_path, newline="", encoding="utf-8") as f:
            names = sorted({row["name"].strip() for row in csv.DictReader(f) if row.get("name", "").strip()})
        q["names"] = "|".join(names)
        q["n"] = a.entries or len(names)
    url = (HERE / "draw.html").as_uri() + "?" + urlencode(q)
    tmp = HERE / "_video"
    shutil.rmtree(tmp, ignore_errors=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, record_video_dir=str(tmp),
                                  record_video_size={"width": 1920, "height": 1080})
        page = ctx.new_page()
        page.goto(url)
        page.wait_for_function("window.__done === true", timeout=60_000)
        page.wait_for_timeout(2500)
        ctx.close()
        browser.close()
    webm = next(tmp.glob("*.webm"))
    subprocess.run([ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(webm), "-c:v", "libx264", "-preset", "medium",
                    "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-movflags", "+faststart", "-an", a.out], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print("wrote", a.out, f"({Path(a.out).stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
