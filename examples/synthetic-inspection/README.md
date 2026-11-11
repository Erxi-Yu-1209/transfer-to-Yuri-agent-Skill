# Synthetic inspection example

This example was produced by a separate agent context given only the skill, saved profile, and synthetic input fixture. It was not given expected answers or diagnostic conclusions and did not read the automated test implementation.

The agent reported reading all 24 structural leaf regions, including 10 narrative candidates and all 3 worldbook entries, one of which is disabled. Its extraction contains 14 entities, 18 claims, 2 directed relationships, 3 constraints, 3 staged events, and 11 unresolved questions. Exact quote, source-pointer, hash, schema and reference checks passed. The interpretation was reviewed for explicit cast roles, nonhuman identity, uncertain romance, contradictory charts, and separate greeting branches.

A stale next-action message after completed extraction was observed during the trial, fixed in the generator, covered by an automated assertion, and regenerated here. Run-level failure status and readable failure reports are also checked to avoid stale success messages.

The input is original synthetic material. No real-user-card conversion, model baseline comparison, SillyTavern import, or roleplay test occurred. Agent-review acknowledgments and passing evidence checks do not establish semantic completeness, generalization, or human acceptance. The inspector itself does not call a model; the semantic pass was performed separately by the agent, whose exact model version is not available in this record.

Run `python scripts/workbench.py validate-extraction examples/synthetic-inspection` from the project root to recheck the evidence. This command rewrites generated validation metadata and the report; it does not modify the synthetic source originals.
