import csv
import hashlib
import json
import unittest
from collections import Counter
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SENTIMENTS = {"positive", "negative", "sarcastic"}


class StudyIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "data" / "stimuli.csv").open(encoding="utf-8-sig", newline="") as f:
            cls.rows = list(csv.DictReader(f))
        with (ROOT / "data" / "sticker_sets.csv").open(encoding="utf-8", newline="") as f:
            cls.sets = list(csv.DictReader(f))
        cls.conditions = json.loads((ROOT / "web" / "conditions.json").read_text(encoding="utf-8"))

    def test_expected_stimulus_counts(self):
        experimental = [r for r in self.rows if r["culture"] != "ATTN"]
        self.assertEqual(len(experimental), 36)
        self.assertEqual(Counter(r["culture"] for r in experimental), {"CN": 12, "TR": 12, "EN": 12})
        self.assertEqual(len([r for r in self.rows if r["culture"] == "ATTN"]), 1)
        self.assertEqual(len({r["sticker_id"] for r in self.rows}), 37)

    def test_each_culture_text_cell_is_reasonably_balanced(self):
        for culture in ("CN", "TR", "EN"):
            for has_text in ("0", "1"):
                cell = [r for r in self.rows if r["culture"] == culture and r["has_text"] == has_text]
                counts = Counter(r["intended_sentiment"] for r in cell)
                self.assertEqual(len(cell), 6, (culture, has_text))
                self.assertEqual(set(counts), SENTIMENTS)
                if culture == "CN":
                    self.assertEqual(counts, {s: 2 for s in SENTIMENTS})

    def test_all_referenced_assets_exist_and_decode(self):
        for row in self.rows:
            file = row["file"]
            self.assertTrue(file, row["sticker_id"])
            if file.startswith(("http://", "https://")):
                continue
            path = ROOT / file
            self.assertTrue(path.is_file(), path)
            if path.suffix.lower() == ".svg":
                text = path.read_text(encoding="utf-8")
                self.assertIn("<svg", text)
                self.assertIn("</svg>", text)
            else:
                with Image.open(path) as image:
                    image.verify()

    def test_chinese_assets_match_handoff_manifest(self):
        manifest_path = ROOT.parent / "handoff" / "metadata" / "ASSET_SHA256.csv"
        if not manifest_path.exists():
            self.skipTest("private handoff manifest is not present")
        with manifest_path.open(encoding="utf-8-sig", newline="") as f:
            expected = {r["sticker_id"]: r["webp_sha256"] for r in csv.DictReader(f)}
        for sticker_id, digest in expected.items():
            data = (ROOT / "stimuli" / f"{sticker_id}.webp").read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), digest, sticker_id)

    def test_no_duplicate_chinese_files_or_placeholder_references(self):
        cn_files = list((ROOT / "stimuli").glob("CN_*"))
        self.assertEqual(len(cn_files), 12)
        self.assertTrue(all(p.suffix == ".webp" for p in cn_files))
        self.assertFalse(any(r["file"].endswith(".svg") for r in self.rows if r["culture"] == "CN"))

    def test_sets_and_rotations(self):
        self.assertEqual(Counter(r["set"] for r in self.sets), {"A": 12, "B": 12, "C": 12})
        set_by_id = {r["sticker_id"]: r["set"] for r in self.sets}
        experimental_ids = {r["sticker_id"] for r in self.rows if r["culture"] != "ATTN"}
        self.assertEqual(set(set_by_id), experimental_ids)
        for rotation in self.conditions["rotations"].values():
            context_by_set = {set_name: context for context, set_name in rotation.items()}
            contexts = [context_by_set[set_by_id[sticker_id]] for sticker_id in experimental_ids]
            self.assertEqual(Counter(contexts), {"alone": 12, "chat": 12, "text_only": 12})
        for sticker_id in experimental_ids:
            seen = {
                {set_name: context for context, set_name in rotation.items()}[set_by_id[sticker_id]]
                for rotation in self.conditions["rotations"].values()
            }
            self.assertEqual(seen, {"alone", "chat", "text_only"})

    def test_public_conditions_are_complete_and_do_not_leak_answers(self):
        stickers = self.conditions["stickers"]
        self.assertEqual(len(stickers), 37)
        self.assertEqual({s["sticker_id"] for s in stickers}, {r["sticker_id"] for r in self.rows})
        forbidden = {"intended_sentiment", "description", "notes"}
        self.assertFalse(any(forbidden.intersection(s) for s in stickers))


if __name__ == "__main__":
    unittest.main()
