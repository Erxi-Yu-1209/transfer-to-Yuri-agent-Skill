# One-time profile choices

The three choices have now been resolved in config/preferences.json: author_defined_inclusive, main_cast, and rederive_if_causal. This reference describes available alternatives for later edits. Use scripts/setup_profile.py for localized one-time setup. These remain independent choices.

## Who qualifies under this profile?

- `author_defined_inclusive`: characters designated as women by the user or source, including virtual and nonhuman characters. Appearance or an emotional-service role is insufficient evidence. Conflicting source identity claims remain explicit.
- `human_explicitly_female`: restrict this profile's women-in-scope category to human characters explicitly described as female. Do not infer anatomy or medical history. This is a fictional-cast selection convention, not a statement about real people.
- `custom`: write the user's operational criteria in `custom_criteria`. Keep identity, embodiment, and presentation separable; do not replace the user's criteria with stereotypes.

This setting defines the target category. The conversion scope separately selects which characters may be changed to fit that category. Excluded characters remain excluded.

## Which cast members should be transformed by default?

- `named_characters`: use the selected character IDs supplied for this card. Require a nonempty run-specific selection before conversion.
- `main_cast`: identify principal characters from the source, show the selected set in the report, and resolve material uncertainty before applying high-impact changes. Do not infer that every mentioned person is a principal character.
- `entire_cast`: include all identified characters except explicit exclusions. Unsupported or unresolved regions prevent a claim of complete-cast coverage.

The player persona is preserved by default under every option. Changing it requires explicit scope. Users can override the saved cast-selection policy for a particular card without redefining the genre.

## How freely may relationships change?

- `preserve_outcomes`: preserve established pairings, nonromantic relationships, hostility, and outcomes wherever compatible with the requested changes. Surface a genuine incompatibility rather than disguising it.
- `rederive_if_causal`: permit altered dynamics or outcomes only when a specific authorized change alters a relevant character or world constraint. Gender stereotypes alone are insufficient.
- `explicit_pairing_targets`: use named pairings and target dynamics supplied for the card. Preserve unrelated relationships and surface conflicts with protected anchors. Require targets before conversion.

All options allow the configured positive, neutral, and negative dynamics. None assumes that every woman should fall in love, that every hostile bond is romantic, or that a different gender entails a different personality.

## Preset and overrides

The included ready template uses `minimal-change`. The other available presets are `pairing-focused`, `character-focused`, and `world-focused`; these can be selected later without repeating the definition interview. A creative-priority preset and a relationship-outcome policy are independent.

A run override modifies the selected complete profile. The project wrapper selects config/preferences.json when --profile is omitted; named profiles do not inherit sparse values from it. Arrays replace rather than append. Validate the final effective profile and log the override keys. A ready saved profile may still need card-specific IDs; those are input selections, not a repeat of one-time setup.
