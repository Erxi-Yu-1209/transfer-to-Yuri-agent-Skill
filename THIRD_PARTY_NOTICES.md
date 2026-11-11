# Third-party implementation and method attribution

## Foreverse serializer and PNG writer — code reuse

- Upstream: https://github.com/foreverse-app/character-card-skills
- File: `tools/card_md_to_st.py`
- Retrieved source URL: https://github.com/foreverse-app/character-card-skills/blob/main/tools/card_md_to_st.py
- Git blob: `6cfd4efb3d0645627a21202520547fda1a4249ad`
- Retrieval date: 2026-11-10
- Local canonical copy: `shared/vendor/card_md_to_st.py`, unmodified.
- License: MIT, copyright (c) 2026 Foreverse (foreverse.app). Complete upstream license and code/content scope note: `shared/vendor/FOREVERSE_LICENSE.txt`.
- Reused: card.md parsing, v2 card construction, lorebook construction, v3 wrapper and PNG chara/ccv3 embedding.
- Workbench wrapper: corrects generated-card creator/source attribution, binds yuri decisions, adds bounded PNG reading and explicit structured-worldbook copying. These changes are outside the vendored file.

The same code and license are included in the generated standalone skill bundles and Chinese runtime. No Foreverse character cards, skills prose, calibrated aesthetic scores or cover art are copied. Those repository components have separate terms and are not needed here. General exporter behavior was not subjected to a new exhaustive benchmark; only the Workbench wrapper received an integration smoke check.

## TavernWeave — method reference

- Repository: https://github.com/LiarMTTT/TavernWeave
- Reviewed snapshot: `f9863d2b05305457fe9ed8b0c5688d52aca400a5`
- References: `skills/build-work-library/SKILL.md`, its `references/data-and-commands.md`, and `skills/tavern-card-builder/SKILL.md`.
- Applied design ideas: immutable source IDs, frozen text hashes and character offsets; source facts separated from inference and adaptation; a source-library stage separate from card authoring.
- No TavernWeave implementation or skill text is copied into this release. Its project-wide plugin/runtime orchestration and mandatory staging are not dependencies.

## Existing Workbench reuse

`shared/spans.py` copies the unchanged protected-syntax and exact-span functions from Workbench v0.5.0 `apply_plan.py`. Existing JSON inspection, profiles, guarded conversion and private case verification remain in place. These are project-owned implementation reuse, not a third-party license grant.

Original Workbench files still have no selected project-wide license. This notice does not impose an inferred upstream license on them.

## Additional method references reviewed for 1.2.0

TavernWeave (LiarMTTT): `sillytavern-embedded-ui` (file Git blob cfcaaada98a90bb88164308f2aae9b11210fc128), `sillytavern-render-regex-pipeline` (bbb616c35e9b9589daf0a79752bb89a626fdccaf), `tavern-card-builder` (f7934771885bf4f326f8fa3a29795f2e84e13a14), and `build-work-library` (e0b2b96cfa2aebad83f9dd633040f839de797863), reviewed 2026-11-11. References informed separation of authoring/presentation, preservation inventories, fixture-based regex review, provenance and resumable reading. No code or templates from these modules are copied. TavernWeave original material is under PolyForm Noncommercial 1.0.0; these references do not relicense it or imply affiliation. Workbench whole-work default follows the user requirement rather than adopting TavernWeave targeted-reading scope. Foreverse MIT code and its license remain unchanged.
