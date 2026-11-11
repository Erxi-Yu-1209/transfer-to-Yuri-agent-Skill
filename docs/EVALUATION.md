# Lightweight community iteration

Extensive matched roleplay studies are optional. Run focused yuri-policy checks and one wrapper smoke when integration changes; do not re-benchmark established generic export components. The agent reports source coverage and decisions in conversation and stores records automatically.

## Evidence layers

1. Format inspection and extraction correctness.
2. Narrative transformation quality and preservation.
3. Export validity and source/artifact parity.
4. Actual SillyTavern import and active prompt delivery.
5. Roleplay behavior and human literary judgment.

Do not mark a later layer passed because an earlier layer passed. When the environment is unavailable, report `not_run`, not a simulated pass.

## Pilot set

Use 6–8 varied cards when available, starting with one representative JSON card. Cover text profiles, embedded worldbooks, inactive entries, conditional templates, stateful variables, ambiguous identity, nonhuman/virtual characters, and a neutral or hostile relationship. Keep runtime-heavy material out of initial writable support until an adapter is tested.

Maintain several small, original synthetic fixtures for deterministic edge cases. Private real-world cards remain local. Separate development cases from held-out cases and never tune on every evaluation item.

## Baseline comparison

Use the same input, definition, requested result, model, and relevant generation settings for a simple conversion prompt and the skill-assisted workflow. Record differences in tools and orchestration; do not disguise these as equal conditions. A second comparison can isolate instruction changes with matched tools.

Repeat a few representative cases to expose variation. Where a seed or token count is unavailable, say so. Human reviewers should compare anonymized outputs when practical. Agent explanations or self-scores alone are insufficient evidence of improvement.

## Measures

- Hard checks: parseable output; required schema fields; source-pointer resolution; protected technical content unchanged; no unrelated field deletion; referential integrity; correct effective configuration.
- Extraction: manually checked required facts recovered; unsupported claims introduced; contradictions and unknowns preserved. Report counts and denominators, not unsupported precision claims.
- Adaptation: definition adherence, recognizable personalities, relationship consistency, causal coherence, preservation of protected anchors, and usefulness for the intended roleplay.
- Efficiency: observed wall time, tool calls, retries, and token/cost data only when available.
- Human effort: corrections needed and whether the author prefers the result to baseline.

All mandatory structural checks must pass before presenting an artifact as validated for the declared format. Semantic acceptance thresholds require calibration against actual samples; no percentage success rate is claimed now.

## Portrayal probes

For conditional experiences, compare an unrelated scene, a relevant cue, and a later scene after the cue fades. Check for unwanted constant repetition or unjustified escalation. For relationships, include cooperation, conflict, and an open decision; distinguish the model following a forced outcome from plausible characterization.

## Revision loop

Bring the Markdown report, source-addressed changes, relevant generated output, and human comments to this conversation. Identify whether a failure belongs to extraction, saved preferences, transformation, technical export, prompt delivery, or roleplay. Change the smallest supported layer; rerun the failing case and existing regression cases. Keep earlier successful cases and held-out evaluation evidence.

## Frozen semantic probes for the next comparison

`evaluation/semantic-probes.json` contains eight original, non-graphic source/profile scenarios derived from failure classes, without private card text. Compare the previous and current skill instructions with the same model/tools and anonymized outputs. Score required invariants and unsupported changes separately; include the actual proposed adaptation and review record. Do not award points for an explanation that contradicts its artifact. This set is frozen for the next comparison, not a measured release result. Use additional held-out real cases before claiming general task improvement.

Current release evidence is recorded in RELEASE_NOTES.md. A reported real import and an agent-simulated roleplay are separate observations. Neither historical batch volume nor a simulation provides a live-model success rate. Old private cases are not public evaluation targets.
