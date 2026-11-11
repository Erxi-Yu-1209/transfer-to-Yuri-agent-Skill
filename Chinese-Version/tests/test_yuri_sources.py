"""Focused yuri-policy checks; upstream export code is not independently re-tested."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))
import source_core as c
import yuri_sources as y
import card_io


class YuriSourcesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.project = self.root / "project"
        source = self.root / "source.txt"
        source.write_text("The narrator admires Nora. Nora is a woman. Otto is a background man. The narrator wants to protect the archive.")
        c.ingest(source, self.project, "sample", "post", max_chars=1000)
        def ev(quote):
            text = source.read_text(); start = text.index(quote)
            return {"source_id":"sample","start":start,"end":start+len(quote),"quote":quote}
        entities = []
        for id, label, role, gender in [("narrator","narrator","main","unknown"),("nora","Nora","main","woman"),("otto","Otto","background","man")]:
            entities.append({"id":id,"label":label,"kind":"character","role":role,"gender":gender,"nature":"human","aliases":[],"evidence":[ev(label)]})
        self.ext = {"schema_version":"2.0","review_status":"agent_reviewed","entities":entities,
            "claims":[{"id":"bond","kind":"relationship","status":"extracted","statement":"Narrator admires Nora.","entity_ids":["narrator","nora"],"asserted_by":"source narrator","evidence":[ev("The narrator admires Nora.")]},
                      {"id":"goal","kind":"motivation","status":"extracted","statement":"Narrator wants to protect the archive.","entity_ids":["narrator"],"asserted_by":"source narrator","evidence":[ev("The narrator wants to protect the archive.")]}],
            "relationships":[{"id":"r","from_id":"narrator","to_id":"nora","dynamics":["unknown"],"outcome":"open","claim_ids":["bond"]}],"constraints":[],"events":[],"unresolved":[]}
        c.dump(self.project / "extracted.json", self.ext)
        self.draft = self.project / "card.md"
        self.draft.write_text("---\nname: Archive\n---\n## Description\nThe narrator has unknown gender; Nora is a woman. Otto is a background man.\n## First Message\nNora looks up from the archive. {{user}} may decide what to do.\n")
        card = card_io.from_markdown(self.draft); self.original = card["data"]["description"]
        start = self.original.index("unknown gender")
        self.plan = {"schema_version":"1.0","mode":"yuri","target_entity_ids":["narrator","nora"],
            "decisions":[{"id":"g","kind":"gender","entity_ids":["narrator"],"source_claim_ids":["bond"],"before":"unknown","after":"woman","rationale":"Authorial designation for a fictional yuri adaptation; original narrator stays unknown."}],
            "patches":[{"pointer":"/data/description","expected_value_sha256":c.digest(c.canonical(self.original)),"entity_ids":["narrator"],"decision_ids":["g"],"edits":[{"start":start,"end":start+len("unknown gender"),"expected":"unknown gender","replacement":"a woman's identity"}]}],
            "field_sources":{"/data/description":{"claim_ids":["bond"],"creative_ids":[]},"/data/first_mes":{"claim_ids":[],"creative_ids":["opening"]}},
            "creative_additions":[{"id":"opening","statement":"A playable archive opening.","reason":"Framing only; not an extracted event."}]}
        self.profile = copy.deepcopy(y.profile_at(ROOT / "config/preferences.json"))

    def build(self):
        profile = self.root / "profile.json"; c.dump(profile, self.profile)
        unbound, bound = self.root / "unbound.json", self.root / "bound.json"
        c.dump(unbound, self.plan)
        y.bind_plan(self.project, self.draft, unbound, bound, profile)
        return y.adapt(self.project, self.draft, bound, self.root / "output", profile)

    def test_unknown_gender_is_designated_only_in_adaptation_branch(self):
        before = (self.project / "extracted.json").read_bytes()
        result = self.build()
        self.assertEqual(result["effective_genders"]["narrator"], "woman")
        self.assertEqual((self.project / "extracted.json").read_bytes(), before)
        sidecar = c.load(self.root / "output/adaptation.json")
        self.assertEqual(sidecar["source_genders"]["narrator"], "unknown")
        self.assertEqual(sidecar["live_roleplay"], "not_run")

    def test_unknown_gender_without_decision_is_not_already_yuri(self):
        self.plan["decisions"] = []; self.plan["patches"] = []
        with self.assertRaisesRegex(ValueError, "unknown source gender"):
            self.build()

    def test_already_women_can_preserve_open_relationship_without_edits(self):
        self.ext["entities"][0]["gender"] = "woman"; c.dump(self.project / "extracted.json", self.ext)
        self.plan["decisions"] = []; self.plan["patches"] = []
        self.assertEqual(self.build()["changed_fields"], 0)
        self.assertEqual(c.load(self.root / "output/source-card.v2.json"), c.load(self.root / "output/yuri-card.v2.json"))

    def test_background_identity_cannot_be_silently_selected(self):
        self.plan["target_entity_ids"].append("otto")
        with self.assertRaisesRegex(ValueError, "main-cast"):
            self.build()

    def test_main_cast_cannot_silently_omit_another_protagonist(self):
        self.plan["target_entity_ids"] = ["narrator"]
        with self.assertRaisesRegex(ValueError, "main-cast"):
            self.build()

    def test_gender_alone_does_not_authorize_a_relationship_outcome(self):
        self.plan["decisions"].append({"id":"rchange","kind":"relationship","entity_ids":["narrator","nora"],"source_claim_ids":["bond"],"before":"open","after":"dating","relationship_id":"r","rationale":"They are women now.","cause_decision_ids":["g"]})
        with self.assertRaisesRegex(ValueError, "gender alone"):
            self.build()

    def test_preserved_outcome_policy_rejects_new_pairing(self):
        self.profile["relationships"]["outcome_policy"] = "preserve_outcomes"
        self.plan["decisions"].append({"id":"rchange","kind":"relationship","entity_ids":["narrator","nora"],"source_claim_ids":["bond"],"before":"open","after":"dating","relationship_id":"r","rationale":"An unsupported new ending."})
        with self.assertRaisesRegex(ValueError, "protects relationship outcomes"):
            self.build()

    def test_fictional_gender_before_value_must_match_source(self):
        self.plan["decisions"][0]["before"] = "man"
        with self.assertRaisesRegex(ValueError, "match source identity"):
            self.build()

    def test_new_opening_needs_a_provenance_or_creative_record(self):
        self.plan["field_sources"]["/data/first_mes"]["creative_ids"] = []
        with self.assertRaisesRegex(ValueError, "unmapped card prose"):
            self.build()

    def test_source_quote_tampering_is_rejected(self):
        self.ext["claims"][0]["evidence"][0]["quote"] = "invented"
        c.dump(self.project / "extracted.json", self.ext)
        with self.assertRaisesRegex(ValueError, "quote differs"):
            self.build()

    def test_stale_draft_cannot_use_old_adaptation_plan(self):
        unbound, bound = self.root / "unbound.json", self.root / "bound.json"
        c.dump(unbound, self.plan)
        y.bind_plan(self.project, self.draft, unbound, bound)
        self.draft.write_text(self.draft.read_text() + "\nchanged\n")
        with self.assertRaisesRegex(ValueError, "stale plan binding"):
            y.adapt(self.project, self.draft, bound, self.root / "output")

    def test_source_gender_records_remain_reusable_across_cards(self):
        self.build()
        manifest, ext = c.validate_extraction(self.project)
        self.assertEqual(ext["entities"][0]["gender"], "unknown")
        self.assertEqual(len(manifest["sources"]), 1)

    def prepare_player_binding(self):
        self.profile["transformation"]["player_persona"] = "explicitly_authorized"
        self.draft.write_text(self.draft.read_text().replace("The narrator has", "{{user}} has"))
        value = card_io.from_markdown(self.draft)["data"]["description"]
        self.plan["patches"][0]["expected_value_sha256"] = c.digest(c.canonical(value))
        start = value.index("unknown gender")
        self.plan["patches"][0]["edits"][0].update(start=start, end=start+len("unknown gender"))
        self.plan["player_binding"] = {"entity_id":"narrator", "macro":"{{user}}", "source_name":None,
            "authority":"explicit_user_request", "forbidden_runtime_aliases":["narrator"]}

    def test_player_binding_preserves_original_unknown_identity(self):
        self.prepare_player_binding(); self.build()
        sidecar = c.load(self.root / "output/adaptation.json")
        self.assertEqual(sidecar["player_binding"]["macro"], "{{user}}")
        self.assertEqual(sidecar["source_genders"]["narrator"], "unknown")

    def test_player_binding_rejects_mixed_lorebook_alias(self):
        self.prepare_player_binding()
        self.draft.write_text(self.draft.read_text()+"\n## Lorebook\n### Background | keys: archive\nThe narrator lives here.\n")
        self.plan["field_sources"]["/data/character_book/entries/0/content"] = {"claim_ids":["bond"],"creative_ids":[]}
        with self.assertRaisesRegex(ValueError,"unresolved narrator/poster"):
            self.build()

    def test_player_binding_requires_scoped_authorization(self):
        self.prepare_player_binding(); self.profile["transformation"]["player_persona"]="preserve"
        with self.assertRaisesRegex(ValueError,"scoped explicit authorization"):
            self.build()

    def test_single_brace_player_token_is_rejected(self):
        self.prepare_player_binding()
        self.draft.write_text(self.draft.read_text().replace("{{user}} may", "{user} may"))
        with self.assertRaisesRegex(ValueError,"bound player"):
            self.build()

    def test_full_source_registration_is_not_limited_by_excerpt_cap(self):
        large = self.root / "large.txt"
        text = "\n".join(f"第{i}章\n" + "原文"*1100 for i in range(1,61))
        large.write_text(text)
        project = self.root / "large-project"
        c.ingest(large, project, "large", "novel", max_chars=100, all_text=True, chunk_chars=1000)
        manifest=c.load(project/"sources.json")
        self.assertEqual((project/manifest["sources"][0]["text_path"]).read_text(),text)
        units=c.load(project/"units.json")["units"]
        self.assertEqual(units[0]["start"],0); self.assertEqual(units[-1]["end"],len(text))
        self.assertTrue(all(b["start"]==a["end"] for a,b in zip(units,units[1:])))
        self.assertTrue(all(u["end"]-u["start"]<=1000 for u in units))
        self.assertFalse(c.source_coverage(project)["complete_work_claimed"])

    def test_unit_progress_resumes_without_claiming_unread_material(self):
        large=self.root/"large.txt";large.write_text("source text\n"*100)
        project=self.root/"large-project"
        c.ingest(large,project,"large","novel",all_text=True,chunk_chars=200)
        first=c.read_unit(project);c.review_unit(project,first["id"])
        second=c.read_unit(project)
        self.assertNotEqual(first["id"],second["id"])
        self.assertFalse(c.source_coverage(project)["complete_work_claimed"])

    def test_omitted_reading_unit_is_detected(self):
        large=self.root/"large.txt";large.write_text("source text\n"*100)
        project=self.root/"large-project"
        c.ingest(large,project,"large","novel",all_text=True,chunk_chars=200)
        ledger=c.load(project/"units.json");ledger["units"].pop(1);c.dump(project/"units.json",ledger)
        with self.assertRaisesRegex(ValueError,"gap"):
            c.source_coverage(project)

    def test_partial_source_export_keeps_unit_hash_for_safe_resumption(self):
        large=self.root/"large.txt";large.write_text("source text\n"*100)
        c.ingest(large,self.project,"large","novel",all_text=True,chunk_chars=200)
        self.ext["review_status"]="agent_reviewed";c.dump(self.project/"extracted.json",self.ext)
        first=c.read_unit(self.project);c.review_unit(self.project,first["id"])
        self.plan["allow_partial_source"]=True;self.plan["coverage_unit_ids"]=[first["id"]]
        self.plan["partial_source_authorization"]={"basis":"explicit_user_request","instruction":"For this trial, use only the first reading unit."}
        self.build();meta=c.load(self.root/"output/adaptation.json")
        self.assertEqual(meta["units_sha256"],c.digest((self.project/"units.json").read_bytes()))
        self.assertFalse(meta["source_coverage"]["complete_work_claimed"])

    def test_partial_flags_without_a_user_scope_instruction_are_not_authorization(self):
        large=self.root/"large.txt";large.write_text("source text\n"*100)
        c.ingest(large,self.project,"large","novel",all_text=True,chunk_chars=200)
        self.ext["review_status"]="agent_reviewed";c.dump(self.project/"extracted.json",self.ext)
        first=c.read_unit(self.project);c.review_unit(self.project,first["id"])
        self.plan["allow_partial_source"]=True;self.plan["coverage_unit_ids"]=[first["id"]]
        with self.assertRaisesRegex(ValueError,"unread units"):self.build()

    def test_unit_review_cli_returns_bounded_progress_counts(self):
        import contextlib, io
        large=self.root/"large.txt";large.write_text("source text\n"*100)
        project=self.root/"large-project"
        c.ingest(large,project,"large","novel",all_text=True,chunk_chars=200)
        first=c.read_unit(project);stream=io.StringIO()
        with contextlib.redirect_stdout(stream):
            self.assertEqual(y.main(["review-unit","--project",str(project),"--unit",first["id"]]),0)
        result=json.loads(stream.getvalue())
        self.assertEqual(result["reviewed_units"],1)
        self.assertNotIn("reviewed_unit_ids",result)


if __name__ == "__main__":
    unittest.main()
