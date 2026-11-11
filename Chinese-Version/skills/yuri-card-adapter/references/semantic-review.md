# Semantic review before author testing

Exact replay proves that the engine followed a plan, not that the plan means the right thing. Read source, saved profile and raw candidate together. When a separate reviewer is available, give it those artifacts before showing the conversion reasons or earlier self-review. Record concise evidence summaries, never hidden chain-of-thought.

## Review obligations

1. Resolve each changed expression to its referent AND to the holder of the belief, preference or projection. A sentence about a selected character may attribute an ideal to the player or a maxim to an unchanged parent. Main-cast scope does not authorize changing that holder's beliefs. A transformed woman can still imitate a player-attributed male ideal.
2. Check cardinality and kinship across entries. Only son can become an ordinary daughter with a sister; only daughter would falsely remove the sibling. Do not blindly exchange gendered exclusivity words. Preserve uncertainty where the source is contradictory.
3. Resolve relative categories before and after transformation. Opposite gender relative to a source man can identify women; leaving that expression unchanged after adapting him to a woman can silently retarget it. Use explicit source-supported target groups when preserving a directed reaction. A different occurrence relative to the unchanged player may need to stay intact. This does not define a complete orientation label.
4. Close affected world constraints over the new character facts: access, room assignment, family succession, marriage rules, social titles and event prerequisites. Prefer a minimal compatible solution already supported by the world. Preserve institutional capacities unless an actual current census justifies changing them. Record genuine author choices rather than inventing an exception to keep a contradictory label.
5. Read prose in every language, examples, greetings and inactive/conditional entries. English pronouns in authoring text remain meaningful prose; macros, protocol keys and tags remain technical tokens. Preserved HTML comments can still reach a model in raw prompt text. If a protected region contains a material contradiction, report the limitation and hold that candidate when necessary; do not call it harmless or relax the guard globally.
6. Keep source identity, embodiment, presentation and orientation independently evidenced. For conflicting supplied masculine sexual anatomy, apply the standing yuri output rule silently: non-graphic woman-consistent or anatomy-neutral wording, without preservation options or explicit commentary. Do not add sexual detail. Keep source evidence, nonsexual background facts and age boundaries intact. This is a requested output adaptation, not a claim about original anatomy or womanhood.
7. Distinguish new adaptation defects, inherited source discrepancies, author decisions and unobserved runtime behavior. Minimal or incomplete source material is a limited test; a valid lexical repair does not supply missing worldbuilding or playable openings.
8. Review ages and branch scope before producing derivatives. Nonsexual childhood scenes can remain separate and protective. Where a source explicitly sexualizes a minor, hold full-card genre transformation and distribution, record non-graphic pointers, and require safe source remediation. Preserving the unsafe text unchanged does not clear the candidate. A blanket adult label does not resolve contradictory childhood material.

## Structured record

Use `assets/semantic-review.schema.json`. Bind the record to the original byte hash and exact exported candidate byte hash. Give each issue a unique ID, source/candidate JSON pointers, category, severity, status, summary and resolution. Do not copy extensive source passages.

- `blocker` + `open`: a defect or delivery hold; do not progress to an author roleplay trial.
- `decision` + `open`: a material source/creative question needing the author's choice.
- `resolved_by_patch`: state the implemented resolution and verify it in the current raw artifact.
- `note` + `recorded_note`: an inherited or informational limitation that does not assert a fixed defect.

Keep `author_acceptance` as `pending`, and import/roleplay as `not_run` in this offline audit record. Actual human/runtime observations belong in separate candidate-hash-specific feedback. A new candidate invalidates an old review, even when the filename is the same.

In the full project, `scripts/verify_casework.py` validates this record and reconstructs casework from original inspection evidence. The standalone skill folder contains the schema and this checklist; it does not include the project's batch-verifier wrapper. Do not confuse a reviewer model's approval with author acceptance or measured task improvement.
