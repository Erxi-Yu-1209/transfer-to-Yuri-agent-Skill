# Run-log contract

Inspection runs and conversion outputs use separate new directories. Real inputs and derivatives remain private; the project code can be public. Implemented files, rather than an aspirational log list, are described below.

## Inspection evidence

`source.original.json` preserves source bytes; `source.snapshot.json` preserves the parsed tree. `run.json` records source identity and effective profile, `inventory.json` indexes the full structure, `extracted.json` holds source-linked semantic claims, and `validation.json` plus `report.md` record extraction checks. An inspection-only run marks conversion, import and roleplay as not run.

## Conversion and casework

The exact-span converter creates `converted-card.review.json`, `changes.jsonl`, `conversion-validation.json` and `conversion-report.md` in a new directory. Retain the authored `conversion-plan.json` and delivered `extracted.json` with those outputs. `CASE_MANIFEST.json` lists relative file paths and byte hashes. Preserve the parent inspection separately so reconstruction can verify source, inventory, effective profile and extraction.

Change records contain selected entity IDs, supporting claim IDs, exact original Unicode-codepoint spans, replacements, field preimage/output hashes and synchronized legacy mirrors. A prose report cannot replace this full diff. Rebuild from original plus plan; do not patch exported JSON afterward.

## Semantic evidence

`semantic-review.json` follows the mirrored semantic-review schema and binds findings to source and candidate byte hashes. Separate open blockers, author decisions, implemented corrections and notes. Include category, pointers, concise summary and concrete resolution. Agent review is a separate outcome from offline integrity and human acceptance. An agent cannot mark acceptance for the user.

The maintained `scripts/verify_casework.py` checks file manifests, independent reconstruction, exact changes and recorded validation metadata. It accepts an optional separate review root. Default success asserts offline integrity, with semantic status reported separately. `--require-semantic-clear` also requires a current agent review with no open blockers/decisions. Neither mode runs a host or grants human acceptance. Invalid review records fail even in default mode.

## Host feedback

Label each observation as actual_user_observation, actual_host_import, actual_live_model_roleplay, agent_simulation or offline_check. Never merge simulated success into live-host results. Acceptance for trial is distinct from final acceptance. Record exact candidate hash, host/model/preset/version when known, selected greeting, active entries, test action, observed result and any visible prompt evidence. Distinguish import, rendering, prompt delivery and portrayal. Record cue-absent, cue-present and cue-recovery scenes where conditional portrayal matters. Use short sanitized excerpts and pointers. Unknown metadata stays unknown; do not invent seeds, token counts or version numbers.

## Explanations and sharing

Use concise decision summaries: what changed, which source/configuration supports it, consequences checked and remaining uncertainty. Do not request or store hidden chain-of-thought. A model's explanation is an assertion to review, not proof of correctness.

Keep private absolute paths, credentials and full source bodies out of public checks. Public check records may contain anonymous case IDs, counts, hashes, commands and limitations. Private feedback stays under the ignored `private-casework/` tree. Held unsafe source material is represented by non-graphic findings, not redistributed excerpts or derivatives.

## 1.1 text-source projects

Source-media projects contain sources.json, frozen sources/<id>.txt and source-extraction schema 2.0 records. They retain the raw input hash and explicit excerpt coverage without copying a full novel. card.md is a concise source-faithful draft. plan.json binds source manifest, extraction, draft and profile hashes. Outputs include both source and yuri JSON, a worldbook, adaptation decisions/field provenance, exact span changes and an output hash. This is distinct from the existing JSON inspection-run layout. The agent maintains these records and stores conversational corrections without requiring a human-completed Markdown file.
