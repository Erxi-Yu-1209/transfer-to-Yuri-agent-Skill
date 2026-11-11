import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_helper as helper


class EvidenceHelperTests(unittest.TestCase):
    def test_unicode_offsets_are_not_byte_offsets(self):
        self.assertEqual(helper.find_spans("😀她，😀她", "她"), [(1, 2), (4, 5)])

    def test_repeated_and_overlapping_modes(self):
        self.assertEqual(helper.find_spans("aaaa", "aa"), [(0, 2), (2, 4)])
        self.assertEqual(helper.find_spans("aaaa", "aa", overlapping=True), [(0, 2), (1, 3), (2, 4)])

    def test_empty_needle_rejected(self):
        with self.assertRaises(ValueError):
            helper.find_spans("text", "")

    def test_type_changes_are_not_hidden_by_python_equality(self):
        self.assertEqual(helper.leaf_diff({"flag": True, "n": 1}, {"flag": 1, "n": 1.0})["changed"], ["/flag", "/n"])

    def test_diff_add_remove_and_empty_container_changes(self):
        diff = helper.leaf_diff({"old": "x", "same": [], "kind": []}, {"new": "x", "same": [], "kind": {}})
        self.assertEqual(diff, {"changed": ["/kind"], "added": ["/new"], "removed": ["/old"]})

    def test_invalid_occurrence_reports_error_without_partial_success_output(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td); helper.w.dump(folder / "source.snapshot.json", {"a/b~c": "她她"})
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = helper.main(["spans", str(folder), "/a~1b~0c", "她", "0"])
            self.assertEqual(code, 1); self.assertEqual(out.getvalue(), "")
            self.assertIn("does not exist", err.getvalue())

    def test_field_hash_resolves_escaped_pointer(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td); helper.w.dump(folder / "source.snapshot.json", {"a/b~c": "😀她"})
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = helper.main(["field-hash", str(folder), "/a~1b~0c"])
            self.assertEqual(code, 0)
            self.assertIn(helper.w.sha(helper.w.canonical("😀她")), out.getvalue())
            self.assertIn("length=2", out.getvalue())

    def test_nonstring_field_fails(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td); helper.w.dump(folder / "source.snapshot.json", {"a": []})
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(helper.main(["field-hash", str(folder), "/a"]), 1)


if __name__ == "__main__":
    unittest.main()
