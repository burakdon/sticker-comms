"""Record the fake WhatsApp "wrong screen" cold open to an MP4 for slide 1.

Opens whatsapp_fake.html in headless Chrome at 1920x1080, records ~21 s of
video with Playwright, then transcodes the WebM to H.264 MP4 (PowerPoint-friendly)
with the ffmpeg bundled in imageio-ffmpeg.

Usage:
  python report/coldopen/record.py          -> report/coldopen/coldopen.mp4
"""

import shutil
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
PAGE = HERE / "whatsapp_fake.html"
OUT = HERE / "coldopen.mp4"
SECONDS = 21


def ffmpeg_exe() -> str:
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def main() -> None:
    tmp = HERE / "_video"
    shutil.rmtree(tmp, ignore_errors=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, record_video_dir=str(tmp),
                                  record_video_size={"width": 1920, "height": 1080}, device_scale_factor=1)
        page = ctx.new_page()
        page.goto(PAGE.as_uri())
        page.wait_for_timeout(SECONDS * 1000)
        page.screenshot(path=str(HERE / "coldopen_lastframe.png"))
        ctx.close()
        browser.close()
    webm = next(tmp.glob("*.webm"))
    cmd = [ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(webm), "-t", str(SECONDS - 0.5),
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
           "-movflags", "+faststart", "-an", str(OUT)]
    subprocess.run(cmd, check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print("wrote", OUT, f"({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    sys.exit(main())
