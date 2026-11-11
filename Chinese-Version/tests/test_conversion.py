import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/yuri-card-adapter/scripts"))
import yuri_workbench as w
import apply_plan as a


class ConversionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        desc = "备注：Ari, age 30, is a man. He keeps the archive."
        self.source = {"name": "Ari", "description": desc, "first_mes": "He opens the book.", "spec": "chara_card_v2", "spec_version": "2.0", "data": {"name": "Ari", "description": desc, "first_mes": "He opens the book.", "character_book": {"entries": [{"id": 3, "keys": [], "content": "Ben is a man. He is the courier.", "enabled": True}]}, "extensions": {"opaque": {"script": "return 'unchanged';"}}}}
        self.input = self.folder / "source.json"; w.dump(self.input, self.source)
        self.run = w.inspect_file(self.input, ROOT / "config/preferences.json", self.folder / "inspection")
        ext = w.load(self.run / "extracted.json")
        ext["entities"] = [{"id": "A", "label": "Ari", "kind": "character", "role": "main", "classification_basis": "Primary named card subject.", "evidence": [{"pointer": "/data/description", "quote": "Ari, age 30"}]}, {"id": "B", "label": "Ben", "kind": "character", "role": "background", "classification_basis": "Incidental courier.", "evidence": [{"pointer": "/data/character_book/entries/0/content", "quote": "Ben is a man"}]}]
        ext["claims"] = [{"id": "C", "kind": "identity", "status": "extracted", "statement": "Ari is identified as a man in the source, and the saved profile requests adaptation of the main cast.", "entity_ids": ["A"], "evidence": [{"pointer": "/data/description", "quote": "Ari, age 30, is a man"}]}]
        ext["review_status"] = "agent_reviewed"
        ext["reviewed_region_pointers"] = w.load(self.run / "inventory.json")["narrative_candidate_pointers"]
        w.dump(self.run / "extracted.json", ext)
        meta = w.load(self.run / "run.json")
        edits = []
        for old, new in [("a man", "a woman"), ("He", "She")]:
            start = desc.index(old); edits.append({"start": start, "end": start + len(old), "expected": old, "replacement": new})
        self.plan = {"schema_version": "1.0", "status": "review_candidate", "source_sha256": meta["source"]["sha256"], "profile_sha256": meta["profile_sha256"], "selected_entity_ids": ["A"], "protected_pointers": ["/data/extensions", "/data/character_book"], "review_notes": ["Synthetic test material; no roleplay result."], "patches": [{"id": "P1", "pointer": "/data/description", "expected_value_sha256": w.sha(w.canonical(desc)), "entity_ids": ["A"], "source_claim_ids": ["C"], "reason": "Adapt the primary card character under the saved definition.", "edits": edits}]}

    def test_unicode_spans_and_mirrors(self):
        card, changes, _, paths = a.plan_conversion(self.run, self.plan)
        self.assertEqual(card["description"], card["data"]["description"])
        self.assertIn("a woman. She", card["description"])
        self.assertEqual(paths, ["/data/description", "/description"])
        self.assertEqual(changes[0]["synchronized_mirrors"], ["/description"])
        self.assertEqual(card["data"]["character_book"], self.source["data"]["character_book"])

    def test_artifact_roundtrip_and_original_untouched(self):
        before = self.input.read_bytes(); plan = self.folder / "plan.json"; w.dump(plan, self.plan)
        out = a.apply(self.run, plan, self.folder / "output")
        self.assertEqual(self.input.read_bytes(), before)
        self.assertEqual(w.load(out / "conversion-validation.json")["status"], "offline_validated_review_candidate")
        self.assertEqual(w.load(out / "converted-card.review.json")["data"]["extensions"], self.source["data"]["extensions"])

    def test_stale_source_or_profile(self):
        for key in ["source_sha256", "profile_sha256"]:
            plan = copy.deepcopy(self.plan); plan[key] = '0' * 64
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "stale"):
                a.plan_conversion(self.run, plan)

    def test_wrong_preimage(self):
        self.plan["patches"][0]["expected_value_sha256"] = '0' * 64
        with self.assertRaisesRegex(ValueError, "preimage"):
            a.plan_conversion(self.run, self.plan)

    def test_span_mismatch(self):
        self.plan["patches"][0]["edits"][0]["expected"] = "not the source"
        with self.assertRaisesRegex(ValueError, "span differs"):
            a.plan_conversion(self.run, self.plan)

    def test_overlap_and_invalid_boundaries(self):
        for edits in [[{"start": 0, "end": 2, "expected": "ab", "replacement": "x"}, {"start": 1, "end": 3, "expected": "bc", "replacement": "y"}], [{"start": 3, "end": 2, "expected": "", "replacement": "x"}], [{"start": 0, "end": 9, "expected": "abc", "replacement": "x"}]]:
            with self.subTest(edits=edits), self.assertRaises(ValueError):
                a.replace_spans("abc", edits)

    def test_macro_tag_style_script_and_protocol_preserved(self):
        for text, old in [("Hi {{user}}", "user"), ("<b>He</b>", "b"), ("<style>.a{color:red}</style>", "red"), ("<script>return 1;</script>", "1"), ("[HisThoughts|text]", "HisThoughts")]:
            start = text.index(old)
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "protected"):
                a.replace_spans(text, [{"start": start, "end": start+len(old), "expected": old, "replacement": "changed"}])

    def test_unselected_or_unresolved_character(self):
        self.plan["selected_entity_ids"] = ["unknown"]
        with self.assertRaisesRegex(ValueError, "extracted character"):
            a.plan_conversion(self.run, self.plan)

    def test_background_character_not_silently_selected(self):
        self.plan["selected_entity_ids"] = ["B"]
        with self.assertRaisesRegex(ValueError, "main-cast"):
            a.plan_conversion(self.run, self.plan)

    def test_player_persona_protected(self):
        ext = w.load(self.run / "extracted.json"); ext["entities"][0]["role"] = "player"; w.dump(self.run / "extracted.json", ext)
        with self.assertRaisesRegex(ValueError, "player persona"):
            a.plan_conversion(self.run, self.plan)

    def test_technical_field_not_a_write_region(self):
        self.plan["patches"][0]["pointer"] = "/data/extensions/opaque/script"
        with self.assertRaisesRegex(ValueError, "unsupported write"):
            a.plan_conversion(self.run, self.plan)

    def test_protected_region_change_rejected(self):
        self.plan["protected_pointers"].append("/data/description")
        with self.assertRaisesRegex(ValueError, "protected region"):
            a.plan_conversion(self.run, self.plan)

    def test_divergent_legacy_mirror_not_overwritten(self):
        data = copy.deepcopy(self.source); data["description"] = "A divergent source version."
        p = self.folder / "divergent.json"; w.dump(p, data)
        run = w.inspect_file(p, ROOT / "config/preferences.json", self.folder / "divergent-run")
        ext = w.load(self.run / "extracted.json"); ext["source_sha256"] = w.load(run / "run.json")["source"]["sha256"]; w.dump(run / "extracted.json", ext)
        plan = copy.deepcopy(self.plan); plan["source_sha256"] = ext["source_sha256"]
        with self.assertRaisesRegex(ValueError, "divergent legacy"):
            a.plan_conversion(run, plan)

    def test_missing_source_claim_and_duplicate_patch(self):
        plan = copy.deepcopy(self.plan); plan["patches"][0]["source_claim_ids"] = ["missing"]
        with self.assertRaisesRegex(ValueError, "missing source claims"):
            a.plan_conversion(self.run, plan)
        plan = copy.deepcopy(self.plan); plan["patches"].append(copy.deepcopy(plan["patches"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate patch"):
            a.plan_conversion(self.run, plan)

    def test_pending_extraction_blocks_conversion(self):
        ext = w.load(self.run / "extracted.json"); ext["review_status"] = "pending"; w.dump(self.run / "extracted.json", ext)
        with self.assertRaisesRegex(ValueError, "agent_reviewed"):
            a.plan_conversion(self.run, self.plan)

    def test_existing_output_and_noop_rejected(self):
        plan = self.folder / "plan.json"; w.dump(plan, self.plan)
        existing = self.folder / "existing"; existing.mkdir()
        with self.assertRaisesRegex(ValueError, "already exists"):
            a.apply(self.run, plan, existing)
        with self.assertRaisesRegex(ValueError, "no effect"):
            a.replace_spans("abc", [{"start": 0, "end": 1, "expected": "a", "replacement": "a"}])

    def test_bundled_conversion_schema_parity(self):
        self.assertEqual(w.load(ROOT / "schemas/conversion.schema.json"), w.load(ROOT / "skills/yuri-card-adapter/assets/conversion.schema.json"))


if __name__ == "__main__":
    unittest.main()
