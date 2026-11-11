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
