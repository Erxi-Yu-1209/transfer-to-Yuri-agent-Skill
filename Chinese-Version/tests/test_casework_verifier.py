import contextlib
import copy
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import verify_casework as verifier
w, engine = verifier.w, verifier.engine


class CaseworkVerifierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.input = self.folder / "source.json"
        description = "Rin is a man. He keeps an archive."
        w.dump(self.input, {"spec": "chara_card_v3", "data": {"name": "Rin", "description": description}})
        self.inspection = self.folder / "runs/inspect-001"
        w.inspect_file(self.input, ROOT / "config/preferences.json", self.inspection)
        ext = w.load(self.inspection / "extracted.json")
        ext.update(review_status="agent_reviewed", reviewed_region_pointers=w.load(self.inspection / "inventory.json")["narrative_candidate_pointers"])
        ext["entities"] = [{"id": "R", "label": "Rin", "kind": "character", "role": "main", "classification_basis": "Primary named card subject.", "evidence": [{"pointer": "/data/description", "quote": "Rin"}]}]
        ext["claims"] = [{"id": "C", "kind": "identity", "status": "extracted", "statement": "The source identifies Rin as a man.", "entity_ids": ["R"], "evidence": [{"pointer": "/data/description", "quote": "Rin is a man"}]}]
        w.dump(self.inspection / "extracted.json", ext)
        meta = w.load(self.inspection / "run.json")
        edits = []
        for old, new in [("man", "woman"), ("He", "She")]:
            start = description.index(old); edits.append({"start": start, "end": start+len(old), "expected": old, "replacement": new})
        plan = {"schema_version": "1.0", "status": "review_candidate", "source_sha256": meta["source"]["sha256"], "profile_sha256": meta["profile_sha256"], "selected_entity_ids": ["R"], "protected_pointers": [], "review_notes": ["Synthetic fixture"], "patches": [{"id": "P", "pointer": "/data/description", "expected_value_sha256": w.sha(w.canonical(description)), "entity_ids": ["R"], "source_claim_ids": ["C"], "reason": "Synthetic adaptation of the selected main character.", "edits": edits}]}
        self.plan = self.folder / "plan.json"; w.dump(self.plan, plan)
        self.case = self.folder / "cases/card-001"
        engine.apply(self.inspection, self.plan, self.case)
        w.dump(self.case / "conversion-plan.json", plan); w.dump(self.case / "extracted.json", ext)
        self.manifest()

    def manifest(self):
        paths = sorted(p for p in self.case.iterdir() if p.is_file() and p.name != "CASE_MANIFEST.json")
        w.dump(self.case / "CASE_MANIFEST.json", {"files": [{"path": p.name, "bytes": p.stat().st_size, "sha256": w.sha(p.read_bytes())} for p in paths]})

    def review(self, issues=None):
        meta = w.load(self.inspection / "run.json")
        result = {"schema_version": "1.0", "case_id": "card-001", "source_sha256": meta["source"]["sha256"], "candidate_sha256": w.sha((self.case / "converted-card.review.json").read_bytes()), "review_kind": "agent_audit", "scope": "Synthetic review-gate fixture.", "issues": issues or [], "author_acceptance": "pending", "import": "not_run", "roleplay": "not_run"}
        path = self.folder / "reviews/card-001/semantic-review.json"; path.parent.mkdir(parents=True, exist_ok=True); w.dump(path, result)
        return path

    def test_valid_integrity_never_grants_semantic_acceptance(self):
        result = verifier.verify_case(self.case, self.inspection)
        self.assertEqual(result["offline_integrity"], "pass")
        self.assertEqual(result["semantic_review"]["status"], "not_recorded")
        self.assertEqual(result["semantic_review"]["author_acceptance"], "pending")

    def test_checksum_tampering_rejected(self):
        (self.case / "converted-card.review.json").write_text('{}')
        self.assertEqual(verifier.verify_case(self.case, self.inspection)["offline_integrity"], "fail")

    def test_rehashed_wrong_candidate_still_fails_reconstruction(self):
        candidate = w.load(self.case / "converted-card.review.json"); candidate["data"]["name"] = "Wrong"
        w.dump(self.case / "converted-card.review.json", candidate)
        validation = w.load(self.case / "conversion-validation.json"); validation["output_sha256"] = w.sha((self.case / "converted-card.review.json").read_bytes()); w.dump(self.case / "conversion-validation.json", validation)
        self.manifest()
        result = verifier.verify_case(self.case, self.inspection)
        self.assertEqual(result["offline_integrity"], "fail")
        self.assertIn("reconstructed", result["checks"][-1]["details"])

    def test_rehashed_wrong_change_log_fails(self):
        (self.case / "changes.jsonl").write_text('{}\n'); self.manifest()
        self.assertEqual(verifier.verify_case(self.case, self.inspection)["offline_integrity"], "fail")

    def test_rehashed_wrong_validation_counts_fail(self):
        data = w.load(self.case / "conversion-validation.json"); data["span_edits"] = 99; w.dump(self.case / "conversion-validation.json", data); self.manifest()
        self.assertEqual(verifier.verify_case(self.case, self.inspection)["offline_integrity"], "fail")

    def test_manifest_duplicate_missing_and_escape_rejected(self):
        valid = w.load(self.case / "CASE_MANIFEST.json")
        for modified in [valid["files"] + [valid["files"][0]], [], [{"path": "../outside", "sha256": "0"*64}]]:
            w.dump(self.case / "CASE_MANIFEST.json", {"files": modified})
            with self.subTest(modified=modified), self.assertRaises(ValueError):
                verifier.verify_manifest(self.case)

    def test_blocking_story_issue_is_separate_from_integrity(self):
        issue = {"id": "D1", "category": "world_rule", "severity": "blocker", "status": "open", "pointers": ["/data/description"], "summary": "Synthetic conflicting world constraint.", "resolution": ""}
        result = verifier.verify_case(self.case, self.inspection, self.review([issue]))
        self.assertEqual(result["offline_integrity"], "pass")
        self.assertEqual(result["semantic_review"]["status"], "needs_fix")

    def test_author_choice_is_not_automatically_accepted(self):
        issue = {"id": "A1", "category": "identity", "severity": "decision", "status": "open", "pointers": [], "summary": "An unresolved author choice.", "resolution": ""}
        result = verifier.verify_case(self.case, self.inspection, self.review([issue]))
        self.assertEqual(result["semantic_review"]["status"], "needs_author_decision")

    def test_stale_candidate_review_rejected(self):
        p = self.review(); value = w.load(p); value["candidate_sha256"] = "0"*64; w.dump(p, value)
        self.assertEqual(verifier.verify_case(self.case, self.inspection, p)["semantic_review"]["status"], "invalid_review")

    def test_wrong_case_or_duplicate_issue_ids_rejected(self):
        p = self.review(); value = w.load(p); value["case_id"] = "card-002"; w.dump(p, value)
        self.assertEqual(verifier.verify_case(self.case, self.inspection, p)["semantic_review"]["status"], "invalid_review")
        issue = {"id": "D1", "category": "referent", "severity": "blocker", "status": "open", "pointers": [], "summary": "Fixture.", "resolution": ""}
        p = self.review([issue, copy.deepcopy(issue)])
        self.assertEqual(verifier.verify_case(self.case, self.inspection, p)["semantic_review"]["status"], "invalid_review")

    def test_recorded_note_cannot_hide_blocker(self):
        issue = {"id": "D1", "category": "referent", "severity": "blocker", "status": "recorded_note", "pointers": [], "summary": "Fixture.", "resolution": ""}
        self.assertEqual(verifier.verify_case(self.case, self.inspection, self.review([issue]))["semantic_review"]["status"], "invalid_review")

    def test_agent_cannot_claim_human_acceptance(self):
        p = self.review(); value = w.load(p); value["author_acceptance"] = "accepted"; w.dump(p, value)
        self.assertEqual(verifier.verify_case(self.case, self.inspection, p)["semantic_review"]["status"], "invalid_review")

    def test_resolved_issue_needs_resolution_record(self):
        issue = {"id": "D1", "category": "referent", "severity": "blocker", "status": "resolved_by_patch", "pointers": [], "summary": "Fixture.", "resolution": ""}
        self.assertEqual(verifier.verify_case(self.case, self.inspection, self.review([issue]))["semantic_review"]["status"], "invalid_review")

    def test_semantic_clear_cli_gate_and_no_report_overwrite(self):
        report = self.folder / "report.json"
        args = ["--case-root", str(self.case.parent), "--inspection-root", str(self.inspection.parent), "--require-semantic-clear", "--output", str(report)]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(verifier.main(args), 1)
        original = report.read_bytes()
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(verifier.main(args), 1)
        self.assertEqual(report.read_bytes(), original)
        self.review()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(verifier.main(args[:-2] + ["--review-root", str(self.folder / "reviews")]), 0)

    def test_empty_batch_never_passes(self):
        folder = self.folder / "empty"; folder.mkdir()
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(verifier.main(["--case-root", str(folder), "--inspection-root", str(self.inspection.parent)]), 1)

    def test_review_schema_bundle_matches_project_schema(self):
        self.assertEqual(w.load(ROOT / "schemas/semantic-review.schema.json"), w.load(ROOT / "skills/yuri-card-adapter/assets/semantic-review.schema.json"))


if __name__ == "__main__":
    unittest.main()
