# Persistent profile policy

The project profile currently chooses author-designated women, including virtual/nonhuman characters; main-cast transformation while preserving background characters; and relationship changes supported by altered circumstances. Keep identity, embodiment, presentation, orientation and agency independent. Preserve the player persona and narrative language under the editable project defaults.

The qualitative `minimal-change` preset remains the initial engineering default, not a newly confirmed preference about every future card. A pairing-, character-, or world-focused preset can change planning priority without changing the genre definition or bypassing validation.

For each run, load a complete selected profile (project default or named alternate), then apply explicit run overrides. A named profile must be complete; sparse named-profile inheritance is not implemented. Overrides may be partial nested objects. Unknown keys and object-shape changes fail. Arrays replace; false and empty arrays are real values. Validate the complete merged result and record it plus changed keys. A null required decision is invalid in a ready profile.

Resolve a named profile explicitly with `--profile`. To inspect a per-card override, add `--override path.json`. To validate readiness, use:

```bash
python <skill-dir>/scripts/yuri_workbench.py resolve-profile --profile <profile.json> --require-ready
```

Readiness validates preferences, not format support or run-specific cast/pairing IDs. A named-character scope needs an explicit nonempty selection before later conversion. A pairing-target policy needs matching targets. These per-card selections do not require a new genre-definition interview. Do not force authors to make high-impact unresolved choices for a read-only inspection.

For later adaptation, document the changed attribute, the established individual motive/world rule it affects, and the resulting bounded consequence. Gender alone is not a causal explanation for passivity, reconciliation, rivalry, attraction, or hostility. If protected anchors conflict with the requested result, surface the specific conflict rather than silently changing either.
