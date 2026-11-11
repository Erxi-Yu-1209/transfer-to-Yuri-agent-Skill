"""Regression cases for authored openings, inherited renderers and full-book scope."""
import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))
import card_presentation as p
import card_io
import source_core as c
import yuri_sources as y


class PresentationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "original.json"
        self.original = {"spec":"chara_card_v3", "spec_version":"3.0", "unknown_root":{"keep":True},
            "data":{"name":"Nora", "first_mes":"<div class='card'><style>.card{color:red}</style>Old greeting. {{user}}</div>",
                    "extensions":{"regex_scripts":[{"findRegex":"/status:(.*)/s","replaceString":"<span>$1</span>","placement":[2]}],
                                  "depth_prompt":{"prompt":"status: quiet","depth":4},"talkativeness":0.7,"unknown":{"x":3}},
                    "alternate_greetings":["An old alternate."],
                    "character_book":{"entries":[{"content":"Nora guards the library.","keys":["library"],"extensions":{"depth":7},"enabled":False}]}}}
        c.dump(self.source,self.original)
        self.draft = self.root / "draft.md"
        self.draft.write_text("---\nname: Nora\n---\n## First Message\n<div class='card'><style>.card{color:red}</style>Nora opens the archive and offers {{user}} a seat.</div>\n")
        self.plan = {"schema_version":"1.0","presentation_choice":"keep","replacements":[{
            "pointer":"/data/first_mes","draft_pointer":"/data/first_mes",
            "expected_value_sha256":c.digest(c.canonical(self.original['data']['first_mes'])),
            "kind":"creative_opening","reason":"Author requested a new archive opening.","source_refs":["inspection:character-library-goal"]}]}

    def run_build(self):
        unbound,bound=self.root/'unbound.json',self.root/'plan.json'
        c.dump(unbound,self.plan);p.bind(self.source,self.draft,unbound,bound)
        return p.rebuild(self.source,self.draft,bound,self.root/'result')

    def test_new_opening_keeps_renderer_unknown_fields_and_worldbook_settings(self):
        self.run_build();out=c.load(self.root/'result/yuri-card.json')
        self.assertIn('offers {{user}} a seat',out['data']['first_mes'])
        self.assertEqual(out['data']['extensions'],self.original['data']['extensions'])
        self.assertEqual(out['data']['character_book'],self.original['data']['character_book'])
        self.assertEqual(out['unknown_root'],self.original['unknown_root'])
        self.assertEqual(out['spec'],'chara_card_v3')
        self.assertEqual(c.load(self.root/'result/adaptation.json')['output_sha256'],c.digest((self.root/'result/yuri-card.json').read_bytes()))

    def test_plain_text_fallback_cannot_silently_strip_html(self):
        self.draft.write_text('---\nname: Nora\n---\n## First Message\nNora greets {{user}}.\n')
        with self.assertRaisesRegex(ValueError,'inherited markup'):self.run_build()
        self.assertFalse((self.root/'result').exists())

    def test_authorized_redesign_can_replace_greeting_but_keeps_unrelated_extensions(self):
        self.plan.update(presentation_choice='redesign',presentation_authorization='Please redesign the opening as plain text.')
        self.draft.write_text('---\nname: Nora\n---\n## First Message\nNora greets {{user}}.\n')
        self.run_build();out=c.load(self.root/'result/yuri-card.json')
        self.assertEqual(out['data']['extensions'],self.original['data']['extensions'])

    def test_redesign_without_a_user_instruction_is_rejected(self):
        self.plan['presentation_choice']='redesign'
        with self.assertRaisesRegex(ValueError,"user's recorded instruction"):self.run_build()

    def test_renderer_cannot_be_replaced_under_keep_styling(self):
        self.draft=self.root/'draft.json';c.dump(self.draft,self.original)
        self.plan['replacements']=[{'pointer':'/data/extensions/regex_scripts','draft_pointer':'/data/extensions/regex_scripts',
            'expected_value_sha256':c.digest(c.canonical(self.original['data']['extensions']['regex_scripts'])),
            'kind':'presentation','reason':'Change renderer','source_refs':['renderer']}]
        with self.assertRaisesRegex(ValueError,'redesign authorization'):self.run_build()

    def test_worldbook_content_edit_preserves_activation_metadata(self):
        self.draft=self.root/'draft.json';out=copy.deepcopy(self.original);out['data']['character_book']['entries'][0]['content']='Nora and {{user}} guard the library.';c.dump(self.draft,out)
        self.plan['replacements']=[{'pointer':'/data/character_book/entries/0/content','draft_pointer':'/data/character_book/entries/0/content',
            'expected_value_sha256':c.digest(c.canonical(self.original['data']['character_book']['entries'][0]['content'])),
            'kind':'adaptation','reason':'Bind the player.','source_refs':['library']}]
        self.run_build();entry=c.load(self.root/'result/yuri-card.json')['data']['character_book']['entries'][0]
        self.assertEqual(entry['extensions'],{'depth':7});self.assertFalse(entry['enabled'])

    def test_stale_draft_is_rejected_before_output(self):
        a,b=self.root/'a.json',self.root/'b.json';c.dump(a,self.plan);p.bind(self.source,self.draft,a,b)
        self.draft.write_text(self.draft.read_text()+'changed')
        with self.assertRaisesRegex(ValueError,'stale rebuild'):p.rebuild(self.source,self.draft,b,self.root/'result')

    def test_conflicting_legacy_mirror_is_not_silently_left_stale(self):
        self.original['first_mes']='An incompatible old greeting.';c.dump(self.source,self.original)
        with self.assertRaisesRegex(ValueError,'conflicting legacy mirror'):self.run_build()

    def test_matching_legacy_mirror_follows_the_authored_greeting(self):
        self.original['first_mes']=self.original['data']['first_mes'];c.dump(self.source,self.original)
        self.run_build();out=c.load(self.root/'result/yuri-card.json')
        self.assertEqual(out['first_mes'],out['data']['first_mes'])

    def test_assets_include_regex_and_worldbook_images_without_claiming_inspection(self):
        self.original['data']['extensions']['regex_scripts'][0]['replaceString']='<img src="https://example.invalid/ui.png">'
        self.original['data']['character_book']['entries'][0]['content']='![Map](local-map.png)'
        c.dump(self.source,self.original);result=p.audit(self.source)
        refs={x['location'] for x in result['image_assets']}
        self.assertIn('https://example.invalid/ui.png',refs);self.assertIn('local-map.png',refs)
        self.assertTrue(all(x['visual_review']=='not_performed' for x in result['image_assets']))


class WholeNovelDefaultTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.book=self.root/'book.txt';self.text='\n'.join('Chapter '+str(i)+'\n'+('chapter text '*800) for i in range(1,4));self.book.write_text(self.text)

    def call(self,extra):
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            return y.main(['ingest',str(self.book),'--kind','novel','--source-id','book','--project',str(self.root/'project'),*extra])

    def test_default_ingestion_retains_every_chapter_and_makes_units(self):
        self.assertEqual(self.call([]),0)
        self.assertEqual((self.root/'project/sources/book.txt').read_text(),self.text)
        self.assertGreater(len(c.load(self.root/'project/units.json')['units']),1)

    def test_small_cap_cannot_implicitly_select_an_excerpt(self):
        self.assertEqual(self.call(['--max-chars','100']),1)
        self.assertFalse((self.root/'project').exists())

    def test_excerpt_needs_the_users_actual_instruction(self):
        self.assertEqual(self.call(['--excerpt','--chapter','1']),1)
        self.assertEqual(self.call(['--excerpt','--chapter','1','--max-chars','100','--scope-note','Convert only chapter one for this request.']),0)
        info=c.load(self.root/'project/sources.json')['sources'][0]['coverage']
        self.assertEqual(info['scope_authority'],'explicit_user_request')
        self.assertTrue(info['partial'])

    def test_direct_api_also_defaults_novels_to_full_work(self):
        c.ingest(self.book,self.root/'project','book','novel')
        self.assertEqual((self.root/'project/sources/book.txt').read_text(),self.text)


if __name__=='__main__':unittest.main()
