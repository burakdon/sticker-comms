"""Generate placeholder sticker images (SVG) for every sticker in data/stimuli.csv.

The real stickers are WhatsApp images we cannot redistribute in all cases. Until
the authors drop in the real files, this script draws a stand-in for each sticker:
a white rounded card with one or two large emoji and, for `has_text` stickers, a
meme-style caption. Emoji render with the viewer's own emoji font, so no image
assets are needed.

To replace a placeholder, put the real image in `stimuli/` (or host it elsewhere
and use a full URL) and update the `file` column in data/stimuli.csv. Then re-run
`assign_conditions.py` so web/conditions.json picks up the new path.

Usage:
    python src/collection/make_placeholder_stickers.py
"""

import argparse
import csv
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]

# sticker_id -> (emoji, caption). Caption None for no-text stickers.
SPEC = {
    "TR_TXT_01": ("😔", "üzdün"),
    "TR_TXT_02": ("🌸", "ÜZÜLME AL ÇİÇEK"),
    "TR_TXT_03": ("😱", "Bu ne ahlaksızlık"),
    "TR_TXT_04": ("🥹", "Duygulandırdın panpa"),
    "TR_TXT_05": ("😭", "AĞLAMA ODASI"),
    "TR_NOTXT_01": ("😁🍦", None),
    "TR_NOTXT_02": ("🐱🎀", None),
    "TR_NOTXT_03": ("😭", None),
    "TR_NOTXT_04": ("🥰💕", None),
    "TR_NOTXT_05": ("😒🍵", None),
    "CN_TXT_01": ("✊", "加油"),
    "CN_TXT_02": ("🙉", "我不听我不听"),
    "CN_TXT_03": ("🚶", "告辞"),
    "CN_TXT_04": ("😩", "心累"),
    "CN_TXT_05": ("🥳", "好耶"),
    "CN_NOTXT_01": ("🐼👍", None),
    "CN_NOTXT_02": ("🐼💦", None),
    "CN_NOTXT_03": ("🐼😏", None),
    "CN_NOTXT_04": ("🐱🔪", None),
    "CN_NOTXT_05": ("🐷🛏️", None),
    "EN_TXT_01": ("🔥🐶", "This is fine"),
    "EN_TXT_02": ("🎉", "LET'S GOOO"),
    "EN_TXT_03": ("👮📞", "I'm calling the police"),
    "EN_TXT_04": ("😩", "big mood"),
    "EN_TXT_05": ("💪", "you got this"),
    "EN_NOTXT_01": ("🐱💃", None),
    "EN_NOTXT_02": ("🐶🥺", None),
    "EN_NOTXT_03": ("🙄", None),
    "EN_NOTXT_04": ("🦭👍", None),
    "EN_NOTXT_05": ("😢", None),
    "ATTN_01": ("👉", "Please select POSITIVE"),
}

EMOJI_FONT = "'Apple Color Emoji','Segoe UI Emoji','Noto Color Emoji',sans-serif"
CAPTION_FONT = "Impact,'Arial Black','PingFang SC','Noto Sans CJK SC',sans-serif"


def caption_size(text: str) -> int:
    """Shrink the caption so long lines still fit the 512px card."""
    n = len(text)
    if n <= 6:
        return 72
    if n <= 12:
        return 56
    if n <= 18:
        return 44
    return 36


def render(emoji: str, caption: str | None) -> str:
    glyphs = [c for c in emoji if not c.isspace()]
    # Variation selectors / ZWJ sequences count as one glyph for sizing purposes.
    n = sum(1 for c in glyphs if c not in ("️", "‍"))
    size = 230 if n <= 1 else 170
    emoji_y = 290 if caption is None else 250
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">',
        '<rect x="8" y="8" width="496" height="496" rx="72" fill="#ffffff" stroke="#d8d6cf" stroke-width="6"/>',
        f'<text x="256" y="{emoji_y}" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="{EMOJI_FONT}" font-size="{size}">{escape(emoji)}</text>',
    ]
    if caption:
        fs = caption_size(caption)
        parts.append(
            f'<text x="256" y="430" text-anchor="middle" font-family="{CAPTION_FONT}" '
            f'font-size="{fs}" font-weight="900" fill="#ffffff" stroke="#000000" '
            f'stroke-width="{max(3, fs // 10)}" paint-order="stroke" '
            f'stroke-linejoin="round">{escape(caption)}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--stimuli", default=ROOT / "data" / "stimuli.csv")
    parser.add_argument("--out-dir", default=ROOT / "stimuli")
    parser.add_argument("--force", action="store_true",
                        help="overwrite files that already exist (e.g. real stickers)")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(args.stimuli, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    written, skipped = 0, 0
    for row in rows:
        sid = row["sticker_id"]
        if sid not in SPEC:
            print(f"no placeholder spec for {sid}; skipping")
            continue
        if row["file"] and not row["file"].endswith(".svg"):
            continue  # a real sticker has replaced this placeholder
        target = out_dir / f"{sid}.svg"
        if target.exists() and not args.force:
            skipped += 1
            continue
        target.write_text(render(*SPEC[sid]), encoding="utf-8")
        written += 1
    print(f"wrote {written} placeholder stickers to {out_dir} ({skipped} already present)")


if __name__ == "__main__":
    main()
