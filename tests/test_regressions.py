"""Regression checks for history eligibility and read-only border screening."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]


def character(identifier="new", suffix=""):
    return {
        "id": identifier, "theme": "moon" + suffix,
        "hair_style": "bob" + suffix, "hair_color": "brown" + suffix,
        "outfit_silhouette": "cape" + suffix, "signature_prop": "book" + suffix,
        "pose": "standing" + suffix, "expression": "smile" + suffix,
        "palette_id": "blue" + suffix,
    }


class RegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def run_script(self, name, *args):
        result = subprocess.run(
            [sys.executable, "-B", str(ROOT / "scripts" / name), *map(str, args)],
            capture_output=True, text=True, check=False,
        )
        self.assertTrue(result.stdout, result.stderr)
        return result.returncode, json.loads(result.stdout)

    def check_plan(self, characters=None, history=None, mode="new_character"):
        plan = self.directory / "plan.json"
        plan.write_text(json.dumps({"mode": mode, "characters": characters or [character()]}), encoding="utf-8")
        args = ["--plan", plan]
        if history is not None:
            history_path = self.directory / "history.jsonl"
            history_path.write_text(history, encoding="utf-8")
            args.extend(["--history", history_path])
        return self.run_script("check_diversity.py", *args)

    def test_unreviewed_and_conflicting_history_is_skipped(self):
        markers = [
            {}, {"visual_review": "not_reviewed"},
            {"quality_status": "passed", "visual_review": "failed"},
            {"quality_status": "failed", "visual_review": {"status": "passed"}},
            {"quality_status": "passed", "quality": {"status": "failed"}},
            {"quality_status": "passed", "quality": "not_reviewed"},
            {"quality_status": "passed", "visual_review": {}},
            {"client_status": "accepted"},
        ]
        for marker in markers:
            with self.subTest(marker=marker):
                code, result = self.check_plan(history=json.dumps({**character("old"), **marker}))
                self.assertEqual(code, 0)
                self.assertEqual(result["history_records_used"], 0)
                self.assertEqual(result["history_records_skipped"], 1)
                self.assertIsNone(result["diversity_checks_passed"])
                self.assertEqual(result["history_coverage"], "no_eligible_records")

    def test_visual_pass_is_not_client_acceptance(self):
        history = {**character("old"), "quality_status": "passed"}
        code, result = self.check_plan(history=json.dumps(history))
        self.assertEqual(code, 1)  # A genuinely colliding visual-history record.
        self.assertEqual(result["history_records_used"], 1)
        self.assertEqual(result["history_records_client_accepted"], 0)
        self.assertEqual(result["history_client_status_counts"]["unknown"], 1)

    def test_batch_and_history_coverage_are_separate(self):
        history = {**character("old", "history"), "visual_review": {"status": "passed"}, "client_status": "accepted"}
        code, result = self.check_plan([character("one"), character("two", "other")], json.dumps(history))
        self.assertEqual(code, 0)
        self.assertEqual(result["batch_pairs_checked"], 1)
        self.assertEqual(result["history_pairs_checked"], 2)
        self.assertEqual(result["pairs_checked"], 3)
        self.assertEqual(result["history_records_client_accepted"], 1)
        self.assertEqual(result["comparison_coverage"], "exact_strings_only")

    def test_distinct_history_revisions_are_all_compared(self):
        versions = [
            {**character("old"), "quality_status": "passed", "revision_id": "v1"},
            {**character(" OLD "), "quality_status": "passed", "revision_id": "v2"},
        ]
        code, result = self.check_plan(history="\n".join(map(json.dumps, versions)))
        self.assertEqual(code, 1)  # Both versions collide with the new design.
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["history_records_used"], 2)
        self.assertEqual(result["history_pairs_checked"], 2)
        self.assertEqual({item["second_revision_id"] for item in result["collisions"]}, {"v1", "v2"})

    def test_repeated_history_ids_need_nonempty_unique_revisions(self):
        invalid_versions = [
            ({}, {"revision_id": "v2"}),
            ({"revision_id": "v1"}, {"revision_id": " "}),
            ({"revision_id": "v1"}, {"revision_id": 2}),
            ({"revision_id": "v1"}, {"revision_id": " V1 "}),
        ]
        for first, second in invalid_versions:
            with self.subTest(first=first, second=second):
                versions = [{**character("old"), "quality_status": "passed", **marker}
                            for marker in (first, second)]
                code, result = self.check_plan(history="\n".join(map(json.dumps, versions)))
                self.assertEqual(code, 2)
                self.assertEqual(result["status"], "error")
                self.assertIn("revision_id", result["error"])

    def test_revisions_do_not_allow_duplicate_plan_or_reused_character_ids(self):
        versions = [
            {**character("old"), "quality_status": "passed", "revision_id": "v1"},
            {**character("old"), "quality_status": "passed", "revision_id": "v2"},
        ]
        code, result = self.check_plan(characters=versions)
        self.assertEqual(code, 2)
        self.assertIn("Duplicate id in plan", result["error"])
        code, result = self.check_plan(characters=[character("old", "new design")],
                                       history="\n".join(map(json.dumps, versions)))
        self.assertEqual(code, 2)
        self.assertIn("already exists in history", result["error"])

    def test_explicit_missing_history_errors(self):
        self.check_plan()
        code, result = self.run_script("check_diversity.py", "--plan", self.directory / "plan.json", "--history", self.directory / "missing.jsonl")
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "error")

    def test_bad_history_line_errors_with_line_number(self):
        code, result = self.check_plan(history="\n{bad json}")
        self.assertEqual(code, 2)
        self.assertIn("line 2", result["error"])

    def test_invalid_client_status_does_not_crash(self):
        code, result = self.check_plan(history=json.dumps({**character("old"), "quality_status": "passed", "client_status": []}))
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "error")

    def test_edit_needs_no_new_character_axes_or_history(self):
        self.check_plan([{"id": "existing"}], mode="edit")
        code, result = self.run_script("check_diversity.py", "--plan", self.directory / "plan.json", "--history", self.directory / "missing.jsonl")
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "not_applicable")
        self.assertEqual(result["history_status"], "not_applicable")
        self.assertIsNone(result["diversity_checks_passed"])

    def test_single_character_has_no_pairwise_evidence(self):
        code, result = self.check_plan()
        self.assertEqual(code, 0)
        self.assertEqual(result["comparison_coverage"], "none")
        self.assertEqual(result["history_coverage"], "not_requested")
        self.assertIsNone(result["diversity_checks_passed"])

    def image_fixture(self, background=(255, 255, 255)):
        path = self.directory / "image.png"
        image = Image.new("RGB", (100, 100), background)
        ImageDraw.Draw(image).rectangle((30, 20, 70, 80), fill=(160, 100, 90))
        image.save(path)
        return path, image

    def test_near_white_remains_compatible_but_fails_exact_check(self):
        path, _ = self.image_fixture((252, 252, 252))
        before = path.read_bytes()
        code, result = self.run_script("check_image.py", path)
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "needs_visual_review")
        code, result = self.run_script("check_image.py", path, "--require-exact-white-border")
        self.assertEqual(code, 1)
        self.assertIn("border_not_exact_white", result["issues"])
        self.assertEqual(path.read_bytes(), before)

    def test_exact_border_requires_every_pixel_and_never_claims_visual_pass(self):
        path, image = self.image_fixture()
        code, result = self.run_script("check_image.py", path, "--require-exact-white-border")
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "needs_visual_review")
        self.assertEqual(result["border_exact_white_fraction"], 1.0)
        image.putpixel((0, 0), (254, 254, 254))
        image.save(path)
        code, result = self.run_script("check_image.py", path, "--require-exact-white-border")
        self.assertEqual(code, 1)
        self.assertIn("border_not_exact_white", result["issues"])


if __name__ == "__main__":
    unittest.main()
