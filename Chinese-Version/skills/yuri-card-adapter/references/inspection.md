# Inspection scope

Recognize legacy flat character JSON (name plus a traditional narrative field), `chara_card_v2` and `chara_card_v3` wrappers with named `data`, standalone `entries` dictionaries/lists, and generation presets with `prompts` plus `prompt_order` or `temperature`. Recognition is structural, not certification against the full upstream schema. Ambiguous roots and unknown variants receive a complete leaf inventory but no narrative-format support claim.

Index known character prose, example dialogue, greetings, alternate greetings, and embedded character-book entries. Keep notes and prompting instructions distinguishable. Preserve all other values in the original and snapshot. Index inactive worldbook entries, stable entry metadata, and unknown text. Conflicting `enabled` and `disable` flags remain conflicts; do not invent precedence.

Technical-field, executable-text, UI, URL, and template indicators are conservative heuristics. They do not interpret arbitrary scripts, verify a dependency, scan for every threat, or authorize execution. Unknown fields may still carry relevant narrative material; triage them manually before claiming coverage. A dependency is only an unverified text reference unless independently checked.

The input limit is 64 MiB UTF-8 JSON. Reject malformed JSON, duplicate keys, nonstandard numbers, and unsupported non-JSON inputs. Extremely deep inputs may hit the Python recursion limit and fail explicitly. Do not modify input files or reuse an existing output directory.

Run files are private by default: `source.original.json` preserves the exact received bytes; `source.snapshot.json` preserves JSON values and ordering after parsing; `inventory.json` maps all leaf values, including empty containers. Pretty-printed JSON is not byte-identical to its input. Canonical hashes compare parsed semantics. These are consistency checks, not authenticated provenance.

Use the root convenience command `python scripts/workbench.py inspect input.json --output runs/<id>` only from a complete project checkout. The standalone skill command always receives the profile path explicitly, so copying the skill folder does not lose runtime code or schema dependencies. Root schemas and workflow definitions are mirrored in bundled assets; the test suite checks parity.
