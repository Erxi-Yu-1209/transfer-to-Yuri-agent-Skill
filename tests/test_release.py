import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_release as release


class ReleaseTests(unittest.TestCase):
    def test_chinese_core_is_identical_and_setup_choices_are_localized(self):
        en = ROOT / "skills/yuri-card-adapter"
        zh = ROOT / "Chinese-Version/skills/yuri-card-adapter"
        for source in en.rglob("*"):
            if not source.is_file() or "__pycache__" in source.parts or source.name.endswith(".pyc"):
                continue
            relative = source.relative_to(en)
            if relative.as_posix() != "assets/interaction.json":
                self.assertEqual(source.read_bytes(), (zh / relative).read_bytes(), str(relative))
        english = json.loads((en / "assets/interaction.json").read_text())
        chinese = json.loads((zh / "assets/interaction.json").read_text())
        self.assertEqual(chinese["locale"], "zh-CN")
        for a, b in zip(english["questions"], chinese["questions"]):
            self.assertEqual(a["pointer"], b["pointer"])
            self.assertEqual([o["value"] for o in a["options"]], [o["value"] for o in b["options"]])
            self.assertRegex(b["prompt"], r"[\u4e00-\u9fff]")
            for option in b["options"]:
                self.assertRegex(option["label"], r"[\u4e00-\u9fff]")
        displayed = subprocess.run([sys.executable, str(zh / "scripts/profile_setup.py"), "--show"], capture_output=True, text=True)
        self.assertEqual(displayed.returncode, 0, displayed.stderr)
        self.assertIn("默认转换哪些角色？", displayed.stdout)

    def test_private_or_escaping_allowlist_paths_are_rejected(self):
        for name in ["../outside", "/tmp/outside", "C:/outside", "docs/../outside", "runs/report.json", "nested/private-casework/card.json", ".env", "config/preferences.local.json", "a\\b"]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                release.safe_path(ROOT, name)

    def test_archive_omits_unlisted_secrets_and_is_reproducible(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            for name, data in release.read_sources(ROOT).items():
                destination = root / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
            sentinel = uuid.uuid4().hex.encode("ascii")
            for name in ["private-casework/secret.json", "docs/unlisted-secret.json", ".env", "Chinese-Version/runs/secret.json"]:
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(sentinel)
            release.sync_chinese(root)
            a, b = Path(temporary) / "a.zip", Path(temporary) / "b.zip"
            release.build(root, a)
            release.build(root, b)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            with zipfile.ZipFile(a) as archive:
                self.assertIsNone(archive.testzip())
                for name in archive.namelist():
                    self.assertNotIn(sentinel, archive.read(name), name)
                manifest = json.loads(archive.read("yuri-card-workbench/PACKAGE_MANIFEST.json"))
                for item in manifest["files"]:
                    self.assertEqual(hashlib.sha256(archive.read("yuri-card-workbench/" + item["path"])).hexdigest(), item["sha256"])

    def test_symlinked_public_file_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "real").write_text("data")
            try:
                (root / "link").symlink_to(root / "real")
            except OSError:
                self.skipTest("symlinks unavailable")
            with self.assertRaises(ValueError):
                release.safe_path(root, "link")

    def test_gitignore_covers_nested_private_files_but_keeps_public_assets(self):
        if shutil.which("git") is None:
            self.skipTest("git unavailable")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copyfile(ROOT / ".gitignore", root / ".gitignore")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            private = ["private-inputs/card.json", "private-casework/log.md", "runs/result.json", "feedback-private/trial.md", "config/preferences.local.json", "Chinese-Version/private-casework/card.json", "Chinese-Version/config/preferences.local.json", ".env", "Chinese-Version/.env", ".venv/bin/python", "Chinese-Version/skills/yuri-card-adapter/scripts/__pycache__/x.pyc", "dist/package.zip"]
            public = ["README.md", "Chinese-Version/README.md", "schemas/preferences.schema.json", "config/preferences.json", "skills/yuri-card-adapter/SKILL.md", ".env.example"]
            for name in private + public:
                result = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", name])
                self.assertEqual(result.returncode, 0 if name in private else 1, name)

    def test_previous_review_inventory_is_still_validated(self):
        sys.path.insert(0, str(ROOT / "skills/yuri-card-adapter/scripts"))
        import yuri_workbench as w
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary) / "inspection"
            w.inspect_file(ROOT / "tests/fixtures/synthetic-card-v2.json", ROOT / "config/preferences.json", run)
            inventory = w.load(run / "inventory.json")
            inventory["adapter_version"] = "0.4.0-semantic-review"
            w.dump(run / "inventory.json", inventory)
            # Pending extraction is legitimate evidence, not semantic completion.
            result = w.check_extraction(run)
            self.assertEqual(result[-1]["overall"], "pending_semantic_review")


if __name__ == "__main__":
    unittest.main()
