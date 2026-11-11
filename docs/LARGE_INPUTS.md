# Whole-work scope and bounded reading

All supplied novel chapters are processed by default. Estimate cost first, then read the entire supplied work through resumable units. Context or token pressure changes batch size and continuation timing, never silently changes chapter coverage. If a session ends early, checkpoint incomplete progress and resume; do not deliver that subset as the complete conversion.

```bash
python scripts/source_pipeline.py ingest novel.epub --kind novel --source-id book --project private-casework/book --chunk-chars 6000
python scripts/source_pipeline.py next-unit --project private-casework/book
python scripts/source_pipeline.py review-unit --project private-casework/book --unit book-000001
```

The CLI defaults to full ingestion for posts and novels; `--all` remains an explicit synonym. The agent reads every unit, updates extraction, validates quotes and marks only actually reviewed units. A frozen file does not prove reading. `units.json` records coverage and enables resumption. Complete interval coverage and all review flags are necessary, not proof of semantic quality.

Only a user's explicit subset request permits `--excerpt --scope-note "<actual user instruction>"` and optional `--chapter` / `--max-chars`. Cost conservation alone is not a subset request. Builds from novel excerpts need `partial_source_authorization` with basis `explicit_user_request` and the actual instruction. A partial ledger also needs `allow_partial_source` and reviewed `coverage_unit_ids`. Old excerpt projects cannot silently pass as full-work projects.

`--chunk-chars` controls reading-unit size, not dataset size. `--max-file-mib` controls the input-byte guard (64 MiB default, independently adjustable). Each EPUB XML member retains a 16 MiB parser guard. All readable non-navigation spine members are included; these need not equal literary chapters, and visual artwork is outside textual coverage. Report unsupported or missing material instead of pretending it was read.

Existing JSON-card inspection reads the complete file under its own byte guard and has no max-chars truncation. Thousands of characters, hundreds of chapters and model context size are separate concerns. Source libraries retain provenance and story stages; a complete source read does not require copying chapters into the card or revealing later-story spoilers in an opening.
