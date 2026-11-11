# Yuri Card Workbench 1.1.1

Turn character cards, supplied posts and novel excerpts into **yuri roleplay cards under your saved definition**. Source gender, fictional gender designation, embodiment, orientation and relationship outcomes stay separate. Yuri can include friendship, conflict and family bonds; romance is optional.

[中文说明](Chinese-Version/README.md) · [Current sample findings](docs/SAMPLE_RESULTS.md) · [Attribution](THIRD_PARTY_NOTICES.md)

## Start with your agent

Open the project and ask:

> Use post-to-yuri-card / novel-excerpt-to-yuri-card on this source. Reuse config/preferences.json, estimate reading cost, select a bounded sample, and build a yuri card. Keep original facts and adaptation decisions separate. Bring consequential choices into this conversation and maintain the records for me.

For an existing JSON card, use `skills/yuri-card-adapter/SKILL.md`. For a post or novel, use the corresponding new skill folder under `skills/`. Each skill is independently distributable and includes its required code and notices. The source-media skills default to yuri adaptation; their source-faithful branch helps review what changed. They share one maintained implementation in `shared/`.

## Install requirements and saved defaults

Python 3.10+; `python -m pip install -r requirements.txt`. Scripts do not call a model or require an API key. The agent performs interpretation, drafting and source retrieval using tools available in its host.

| Saved choice | Default |
| --- | --- |
| Women in scope | Author-defined women, including virtual and nonhuman characters |
| Cast | Main cast; preserve background identities |
| Relationships | Permit changes supported by specific altered circumstances |

Use `python scripts/setup_profile.py --show`, or save different choices once with `--output config/preferences.local.json`. Select that complete profile explicitly in later commands. The Chinese edition presents these three choices in Chinese; core instructions and code remain English. Player identity and source narrative language are preserved by default.

## Source-to-yuri workflow

```bash
python scripts/source_pipeline.py ingest input.txt --kind post --source-id post-001 --project private-casework/my-post --max-chars 6000
python scripts/source_pipeline.py ingest novel.epub --kind novel --source-id novel-scene --project private-casework/my-novel --chapter 1 --max-chars 3000
```

These are separate example projects. TXT/Markdown and EPUB are supported. For accessible URLs, the agent retrieves the original page, saves a text snapshot and passes `--url` during ingestion; the Python tools do not browse or automate logins. EPUB selection uses narrative spine members, which may differ from chapter boundaries. Coverage and truncation are explicit.

The agent fills `extracted.json`, writes a concise source-faithful `card.md`, then creates a yuri plan. The shared schemas are under `shared/assets/`. Sources may be added with new stable IDs to reuse a library across chapters or cards. Frozen text is immutable; full-book reading is not required.

```bash
python scripts/source_pipeline.py validate --project private-casework/my-post
python scripts/source_pipeline.py bind-plan --project private-casework/my-post --draft private-casework/my-post/card.md --plan private-casework/my-post/plan.unbound.json --profile config/preferences.json --output private-casework/my-post/plan.json
python scripts/source_pipeline.py build --project private-casework/my-post --draft private-casework/my-post/card.md --plan private-casework/my-post/plan.json --profile config/preferences.json --output private-casework/my-post/results
```

Outputs include `source-card.v2.json`, `yuri-card.v2.json`, `worldbook.json`, `adaptation.json` and a short review. The sidecar records original and adapted identities, supporting claims, creative additions and exact changed spans. An unknown original-poster gender remains unknown in extraction even when the fictional counterpart becomes a woman. Already-GL characters may pass unchanged.

New cards use the unmodified MIT Foreverse serializer. Exact-span guards come from our 0.5 engine. New code concentrates on source binding and yuri-policy decisions. Card prose must map to source claims or explicitly recorded creative framing. Do not copy full novel chapters into output fields.

## Existing-card, PNG and worldbook operations

The v0.5 JSON inspector/converter remains available through `scripts/workbench.py`, `scripts/convert_card.py` and the original skill. It uses the original extraction schema; text-source extraction has its own versioned schema, so old private runs are not silently migrated.

```bash
python scripts/source_pipeline.py unpack-png input.png --output runs/input-card.json
python scripts/source_pipeline.py pack-png output-card.json --avatar original.png --output runs/output-card.png
python scripts/source_pipeline.py extract-worldbook output-card.json --output runs/worldbook.json
python scripts/source_pipeline.py embed-worldbook output-card.json runs/worldbook.json --replace --output runs/card-with-book.json
```

All output paths must be new. PNG packaging uses the upstream chara/ccv3 embedding code and preserves the supplied image data. The reader currently supports uncompressed `tEXt` card payloads. Structured worldbook copying preserves entries and settings; extracting lore from prose still requires an authored content plan. This is a SillyTavern **file adapter**, not a live server/API adapter. No real host behavior is inferred from a file round-trip.

## Conversational review and batch use

The agent maintains extraction, decisions, results and progress. You respond in the ongoing conversation; no Markdown form is required. Reuse libraries and ready profiles. Existing per-case checks and new output directories allow completed work to remain usable when another item needs a decision. For already-authored plans, `python scripts/batch_source_build.py --jobs path/to/jobs.json --report runs/batch-status.json` builds each job, records failures and continues. The jobs array supplies `id`, `project`, `draft`, `plan`, `output` and optional `profile`; relative paths resolve from the jobs file. Existing current outputs are recognized by hashes. Automatic background execution after a session ends is not provided.

The three supplied samples are bounded development trials: a full post, one general-novel chapter and one GL scene. See `docs/SAMPLE_RESULTS.md` for the actual scope. Their private evidence and generated cards are under ignored `private-casework/`; they are not public fixtures or publication-cleared source material. No full novels or original EPUB artwork are bundled into the public source.

## Maintenance and folder delivery

```bash
python scripts/sync_source_skills.py
python scripts/build_release.py --sync-chinese
python scripts/build_release.py --check
python -m unittest discover -s tests -p test_yuri_sources.py -q
python scripts/build_release.py --folder dist/yuri-card-workbench-v1.1
```

The explicit public-file allowlist and manifests distinguish reusable source from private casework. `.gitignore` covers private inputs, results, feedback, local profiles and credentials in both editions. The new delivery default is a Google Drive folder, preserving directory structure and file identity in later updates; ZIP output remains optional tooling only. Original project-wide licensing remains undecided; the reused exporter carries its verified MIT license. See `NOTICE.md` and `THIRD_PARTY_NOTICES.md`.

## Player perspective and larger inputs (1.1.1)

A chosen first-person protagonist normally becomes `{{user}}`; the counterpart remains model-controlled. Named source characters keep their identity in provenance, while descriptions, greetings and worldbook use the player macro consistently. The two supplied first-person cards now follow this rule. A scoped `profile.player.json` records the requested casting without changing the three global defaults. Greetings leave current player actions and replies open.

`--max-chars` is only an excerpt selector for source text, not a limit on existing JSON cards or an entire dataset. For a complete novel, including hundreds of chapters:

```bash
python scripts/source_pipeline.py ingest novel.txt --kind novel --source-id book --project private-casework/book --all --chunk-chars 6000
python scripts/source_pipeline.py next-unit --project private-casework/book
python scripts/source_pipeline.py review-unit --project private-casework/book --unit book-000001
```

The agent reads each unit, updates extraction and marks that unit reviewed, then resumes the next one. Registration is local and does not send the entire book to a model. Pending units cannot silently become complete coverage. `--max-file-mib 256` can raise the default 64 MiB input-byte guard when needed, separately from per-unit size. Existing JSON-card inspection accepts full files up to its own byte guard; tens of thousands of characters do not encounter this text excerpt selector. See [large-input guidance](docs/LARGE_INPUTS.md).
