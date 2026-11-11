# Agent command reference

The agent maintains plans, extraction and reviews; users give feedback in conversation. Install Python requirements as needed. Choose new output paths.

## Complete post or novel

```bash
python scripts/source_pipeline.py ingest novel.epub --kind novel --source-id book --project private-casework/book --all --chunk-chars 6000
python scripts/source_pipeline.py next-unit --project private-casework/book
python scripts/source_pipeline.py review-unit --project private-casework/book --unit book-000001
```

Repeat semantic reading, extraction updates and review for every unit. Use `--kind post` for a post. Only a user's explicit subset instruction permits `--excerpt --scope-note "<actual instruction>"`, with optional `--chapter` / `--max-chars`. See LARGE_INPUTS.md. A cost estimate is not permission to reduce scope.

Write the source-faithful `card.md`, extraction and adaptation plan, then:

```bash
python scripts/source_pipeline.py validate --project private-casework/book
python scripts/source_pipeline.py bind-plan --project private-casework/book --draft private-casework/book/card.md --plan private-casework/book/plan.unbound.json --profile config/preferences.json --output private-casework/book/plan.json
python scripts/source_pipeline.py build --project private-casework/book --draft private-casework/book/card.md --plan private-casework/book/plan.json --profile config/preferences.json --output private-casework/book/results
```

This source-media path emits `source-card.v2.json`, `yuri-card.v2.json`, worldbook, adaptation receipt and review. Keep source claims, fictional identity decisions and creative additions distinct. A complete read does not require copying full chapters into card fields. Batch already-authored source plans with `scripts/batch_source_build.py --jobs jobs.json --report runs/status.json`.

## Inherited cards and authored rewrites

Inspect/extract through `scripts/workbench.py` or yuri-card-adapter first. Use the original converter for local edits. Use `card-presentation` for newly authored openings or larger rebuilds; never feed an inherited card through a bare Markdown export that resets extensions.

```bash
python scripts/source_pipeline.py presentation-audit original.png --output runs/presentation.json
python scripts/source_pipeline.py bind-rebuild --source original.json --draft adapted.md --plan rebuild.unbound.json --output runs/rebuild.json
python scripts/source_pipeline.py rebuild-card --source original.json --draft adapted.md --plan runs/rebuild.json --output runs/rebuilt
```

The rebuild emits `source-card.json`, `yuri-card.json`, worldbook and an adaptation receipt, retaining the input wrapper and unrelated fields. Its schema is `shared/assets/card-rebuild.schema.json`. Every replacement binds an original canonical-value hash, draft pointer, reason, kind and source references. `keep` retains markup/code and renderer settings. `redesign` needs the user's recorded instruction. Whole-worldbook replacement needs separate structure authorization. These are agent-maintained records, not forms for the user. See PRESENTATION.md.

## PNG and worldbook files

```bash
python scripts/source_pipeline.py unpack-png input.png --output runs/input-card.json
python scripts/source_pipeline.py pack-png runs/rebuilt/yuri-card.json --avatar original.png --output runs/output-card.png
python scripts/source_pipeline.py extract-worldbook runs/rebuilt/yuri-card.json --output runs/worldbook.json
python scripts/source_pipeline.py embed-worldbook runs/rebuilt/yuri-card.json runs/worldbook.json --replace --output runs/card-with-book.json
```

The unmodified upstream exporter embeds chara/ccv3 payloads without redrawing the supplied PNG. The reader supports uncompressed tEXt payloads. File adaptation is not proof of live host behavior. Any packaging or metadata change creates a new final candidate: bind final semantic/presentation checks to that artifact's hash.

## Maintenance

```bash
python scripts/sync_source_skills.py
python scripts/build_release.py --sync-chinese
python scripts/build_release.py --check
python -m unittest discover -s tests -q
python scripts/build_release.py --folder dist/yuri-card-workbench-v1.2.0
```

The root is maintained; Chinese-Version is generated. Core instructions stay English, interaction catalogs and Chinese README are localized. Public allowlists exclude private inputs/casework. Deliver public updates into the designated Drive folder and preserve user-created test folders. Do not restore withdrawn samples or retry refused private uploads.
