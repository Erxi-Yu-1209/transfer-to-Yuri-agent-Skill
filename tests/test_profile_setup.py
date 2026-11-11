import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/yuri-card-adapter"
sys.path.insert(0, str(SKILL / "scripts"))
import profile_setup as setup
import yuri_workbench as w


class ProfileSetupTests(unittest.TestCase):
    def setUp(self):
        self.profile = w.load(ROOT / "config/preferences.json")

    def choose(self, answers, profile=None):
        iterator = iter(answers)
        return setup.collect(profile or self.profile, ask=lambda _: next(iterator), output=lambda _: None)

    def test_enter_keeps_saved_choices_and_other_settings(self):
        self.profile["workflow"] = "world-focused"
        self.profile["transformation"]["protected_anchors"] = ["Keep the old archive"]
        original = copy.deepcopy(self.profile)
        self.assertEqual(self.choose(["", "", ""]), original)
        self.assertEqual(self.profile, original)

    def test_all_alternative_values_remain_canonical(self):
        result = self.choose(["2", "3", "2"])
        self.assertEqual(result["definition"]["womanhood_policy"], "human_explicitly_female")
        self.assertEqual(result["transformation"]["scope"], "entire_cast")
        self.assertEqual(result["relationships"]["outcome_policy"], "preserve_outcomes")
        result = self.choose(["1", "2", "3"])
        self.assertEqual(result["transformation"]["scope"], "named_characters")
        self.assertEqual(result["relationships"]["outcome_policy"], "explicit_pairing_targets")
        self.assertEqual(result["transformation"]["selected_character_ids"], [])

    def test_custom_criteria_are_collected_without_translating(self):
        result = self.choose(["3", "", "作者明确指定的女性意识体", "", ""])
        self.assertEqual(result["definition"]["womanhood_policy"], "custom")
        self.assertEqual(result["definition"]["custom_criteria"], "作者明确指定的女性意识体")

    def test_invalid_choice_reprompts(self):
        self.assertEqual(self.choose(["bad", "0", "4", "1", "1", "1"]), self.profile)

    def test_new_file_is_valid_and_existing_profile_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "preferences.local.json"
            args = [sys.executable, str(SKILL / "scripts/profile_setup.py"), "--defaults", "--output", str(target)]
            first = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(w.load(target), self.profile)
            before = target.read_bytes()
            second = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(second.returncode, 1)
            self.assertEqual(target.read_bytes(), before)

    def test_cancelled_interactive_setup_leaves_no_profile(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "profile.json"
            run = subprocess.run([sys.executable, str(SKILL / "scripts/profile_setup.py"), "--output", str(target)], input="", capture_output=True, text=True)
            self.assertEqual(run.returncode, 1)
            self.assertFalse(target.exists())

    def test_show_contains_three_questions_and_current_labels(self):
        lines = []
        setup.display_choices(self.profile, output=lines.append)
        cat = setup.catalog()
        self.assertEqual(len(cat["questions"]), 3)
        for q in cat["questions"]:
            self.assertIn(q["prompt"], lines)
            default = w.resolve(self.profile, q["pointer"])
            option = next(o for o in q["options"] if o["value"] == default)
            self.assertTrue(any(option["label"] + cat["default_marker"] in s for s in lines))

    def test_bundled_default_matches_project_template(self):
        self.assertEqual(w.load(SKILL / "assets/preferences.default.json"), self.profile)


if __name__ == "__main__":
    unittest.main()
