# Input size, context size and coverage

There are three separate limits.

| Setting | Applies to | Meaning |
| --- | --- | --- |
| Existing JSON inspector byte guard | Character-card JSON files | Full structural inspection; no max-chars truncation. The current guard is 64 MiB, far above ordinary tens-of-thousands-character cards. |
| --max-chars | Text/EPUB excerpt mode | Intentionally selects a bounded scene for quick work; the record says partial when material is omitted. |
| --all with --chunk-chars | Complete text/EPUB ingestion | Freezes full supported readable text, then creates bounded reading units with complete interval coverage. Per-unit size is independent of dataset length. |

Text-source input bytes default to 64 MiB and can be raised with --max-file-mib. --all and --chapter are separate modes. EPUB full mode includes readable non-navigation spine text, including short members; images remain outside textual extraction. Individual XML members retain a 16 MiB parser guard. Not every EPUB reading-order member is a literary chapter.

The agent requests next-unit, reads the returned text with global frozen-source offsets, updates extraction, validates exact quotes and marks review-unit. Progress is saved in units.json. Adding a new source uses a new immutable ID. A source snapshot is not evidence that an agent read it. Acknowledgments do not establish semantic completeness. The builder binds ledger hashes and rejects unread source scope unless the plan explicitly declares reviewed partial units. No infinite automatic model loop or closed-session background execution is supplied.

For the GL correction, the initial 2,939-character scene ended before the first surname mention at offset 3,278 in the normalized first narrative member. A new immutable excerpt extends the evidence; it confirms surname 島村, not an invented given name. The card uses {{user}} for that role.
