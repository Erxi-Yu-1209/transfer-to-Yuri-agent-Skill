# Source-grounded extraction

Read `assets/extraction.schema.json` for the full record shape. Use stable IDs across entities, claims, relationships, world constraints, events, and unresolved questions. Never invent an extracted fact to satisfy the schema. Empty lists mean no recorded findings yet, not absence of source material.

For an entity, supply `id`, `label`, `kind`, `role`, `classification_basis`, and one or more evidence items. Roles are `main`, `background`, `player`, `unknown`, or `not_applicable`. Use `unknown` for uncertain cast importance, not automatic inclusion in the main cast. Classification explanations must separate an explicit source designation from an agent inference.

For a claim, supply `id`, `kind`, `status` (`extracted` or `inference`), `statement`, `entity_ids`, and evidence. Each evidence item is an RFC 6901 `pointer` and a nonempty exact `quote` from the string at that pointer. Escape `/` as `~1` and `~` as `~0` in pointer segments. Use inference status for plausible implications; a quotation can support only part of an inference, so explain the distinction in the statement or report. Contradictory claims may both be extracted. Preserve them and add an unresolved question.

Record a relationship with directed `from_id` and `to_id`, one or more dynamics, and supporting `claim_ids`. Record both directions only if the source supports both; do not turn one person's attraction or resentment into reciprocity. Friendship, trust, dependence, rivalry and hostility may coexist. Unknown romantic intent remains unknown.

Constraints and events carry an ID, statement, and supporting claim IDs. Keep institutional access rules and chronology visible because later gender adaptation may affect them. A temporary condition is not a permanent personality trait. For an intermittent experience, distinguish baseline, relevant cue, usual intensity/duration, expression, and recovery only where the source establishes them.

Unresolved questions carry an ID, question, and relevant source pointers; an empty pointer list is appropriate for missing information with no exact location. Avoid treating absent source information as a defect that must be creatively filled during extraction.

After reading every narrative candidate region, list its pointer in `reviewed_region_pointers`. Triage unclassified and mixed technical/prose regions as well, but do not claim to have interpreted arbitrary code. `agent_reviewed` is a self-report. Automated validation checks schemas, hashes, pointers, exact quote inclusion, review coverage acknowledgments and referential integrity. It does not grade entailment, completeness, literary quality, or truthful acknowledgment. Keep those limitations in the handoff.
