#!/usr/bin/env python3
"""Offline source inspection and evidence checks; no model calls or card conversion."""

import argparse
import copy
import datetime
import hashlib
import html
import json
import re
import sys
from pathlib import Path

VERSION = "1.1.0"
BUNDLE = Path(__file__).resolve().parents[1]


def fail_constant(value):
    raise ValueError(f"nonstandard JSON number: {value}")


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def loads(raw):
    return json.loads(raw, object_pairs_hook=unique_keys, parse_constant=fail_constant)


def load(path):
    return loads(Path(path).read_text(encoding="utf-8-sig"))


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def segment(value):
    return str(value).replace("~", "~0").replace("/", "~1")


def resolve(document, pointer):
    if pointer == "":
        return document
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError(f"invalid JSON pointer: {pointer!r}")
    value = document
    for item in pointer[1:].split("/"):
        if re.search(r"~(?![01])", item):
            raise ValueError(f"invalid pointer escape: {pointer}")
        token = item.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", token):
                raise ValueError(f"invalid array index: {pointer}")
            try:
                value = value[int(token)]
            except IndexError as exc:
                raise ValueError(f"missing array index: {pointer}") from exc
        elif isinstance(value, dict) and token in value:
            value = value[token]
        else:
            raise ValueError(f"unresolvable source pointer: {pointer}")
    return value


def walk(value, pointer=""):
    if isinstance(value, dict) and value:
        for key, item in value.items():
            yield from walk(item, pointer + "/" + segment(key))
    elif isinstance(value, list) and value:
        for index, item in enumerate(value):
            yield from walk(item, pointer + "/" + str(index))
    else:
        yield pointer, value


def schema_errors(value, schema_name):
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise ValueError("dependency missing: install jsonschema>=4.18,<5") from exc
    schema = load(BUNDLE / "assets" / schema_name)
    Draft202012Validator.check_schema(schema)
    return [f"/{'/'.join(map(str, e.path))}: {e.message}" for e in
            sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: str(list(e.path)))]


def validate_profile(profile, require_ready=False):
    errors = schema_errors(profile, "preferences.schema.json")
    if errors:
        raise ValueError("; ".join(errors))
    chosen = set(profile["transformation"]["selected_character_ids"])
    excluded = set(profile["transformation"]["excluded_character_ids"])
    if chosen & excluded:
        raise ValueError("selected and excluded character IDs overlap")
    if profile["workflow"] not in load(BUNDLE / "assets/workflows.json")["presets"]:
        raise ValueError("workflow has no matching preset")
    if require_ready and profile["status"] != "ready":
        raise ValueError("profile is a draft; resolve decisions before conversion")
    return profile


def merge(base, override, pointer=""):
    if not isinstance(override, dict):
        raise ValueError("override must be an object")
    result, changed = copy.deepcopy(base), []
    for key, value in override.items():
        here = pointer + "/" + segment(key)
        if key not in result:
            raise ValueError(f"unknown override key: {here}")
        if isinstance(result[key], dict):
            if not isinstance(value, dict):
                raise ValueError(f"override must preserve object shape: {here}")
            result[key], nested = merge(result[key], value, here)
            changed.extend(nested)
        else:
            if result[key] != value:
                changed.append(here)
            result[key] = copy.deepcopy(value)
    return result, changed


def effective_profile(profile_path, override_path=None):
    profile = validate_profile(load(profile_path))
    changed = []
    if override_path:
        profile, changed = merge(profile, load(override_path))
    return validate_profile(profile), changed


def detect(document):
    if not isinstance(document, dict):
        return {"kind": "unknown_json", "candidates": [], "card_root": None, "declared_spec": None}
    matches = []
    if isinstance(document.get("prompts"), list) and ("prompt_order" in document or "temperature" in document):
        matches.append("generation_preset")
    if isinstance(document.get("entries"), (dict, list)):
        matches.append("worldbook")
    spec = document.get("spec")
    data = document.get("data")
    if spec in ("chara_card_v2", "chara_card_v3") and isinstance(data, dict) and isinstance(data.get("name"), str):
        matches.append(spec)
    elif spec is None and isinstance(document.get("name"), str) and any(
            isinstance(document.get(k), str) for k in ("description", "personality", "scenario", "first_mes", "mes_example")):
        matches.append("legacy_character_card")
    kind = matches[0] if len(matches) == 1 else "ambiguous_json" if matches else "unknown_json"
    card_root = "/data" if kind in ("chara_card_v2", "chara_card_v3") else "" if kind == "legacy_character_card" else None
    return {"kind": kind, "candidates": matches, "card_root": card_root, "declared_spec": spec}


def entries_at(document, pointer):
    entries = resolve(document, pointer)
    if isinstance(entries, (dict, list)):
        iterable = entries.items() if isinstance(entries, dict) else enumerate(entries)
        for key, value in iterable:
            if isinstance(value, dict):
                yield pointer + "/" + segment(key), value


def inventory(document):
    fmt = detect(document)
    roles, activations, warnings = {}, {}, []
    entry_roots = []
    card_root = fmt["card_root"]
    if card_root is not None:
        card = resolve(document, card_root)
        for key in ("name", "description", "personality", "scenario", "first_mes", "mes_example", "creator_notes"):
            if isinstance(card.get(key), str):
                roles[card_root + "/" + key] = "narrative_candidate" if key != "creator_notes" else "author_note"
        for key in ("system_prompt", "post_history_instructions"):
            if isinstance(card.get(key), str):
                roles[card_root + "/" + key] = "authoring_instruction"
        if isinstance(card.get("alternate_greetings"), list):
            for i, item in enumerate(card["alternate_greetings"]):
                if isinstance(item, str):
                    roles[card_root + f"/alternate_greetings/{i}"] = "narrative_candidate"
        book = card.get("character_book")
        if isinstance(book, dict) and isinstance(book.get("entries"), (dict, list)):
            entry_roots.append(card_root + "/character_book/entries")
    elif fmt["kind"] == "worldbook":
        entry_roots.append("/entries")
    if fmt["kind"] == "generation_preset":
        for i, prompt in enumerate(document["prompts"]):
            if isinstance(prompt, dict) and isinstance(prompt.get("content"), str):
                roles[f"/prompts/{i}/content"] = "authoring_instruction"
        warnings.append("Generation preset: authoring resource, not a character-card conversion target.")
    for entry_root in entry_roots:
        for pointer, entry in entries_at(document, entry_root):
            if isinstance(entry.get("content"), str):
                roles[pointer + "/content"] = "narrative_candidate"
            metadata = {key: entry[key] for key in ("uid", "id", "key", "keys", "comment", "enabled", "disable", "constant", "selective", "position", "order", "insertion_order", "probability", "useProbability") if key in entry}
            active = "unspecified"
            enabled, disabled = entry.get("enabled"), entry.get("disable")
            if type(enabled) is bool and type(disabled) is bool and enabled == disabled:
                active = "conflicting"
                warnings.append(f"Conflicting activation flags at {pointer}; no precedence assumed.")
            elif type(disabled) is bool:
                active = "disabled" if disabled else "enabled"
            elif type(enabled) is bool:
                active = "enabled" if enabled else "disabled"
            activations[pointer] = {"state": active, "metadata": metadata}
    regions, dependencies = [], []
    for pointer, value in walk(document):
        role = roles.get(pointer, "unclassified")
        flags = []
        if isinstance(value, str):
            field = pointer.lower()
            if re.search(r"(?:script|javascript|regex|findregex|replacestring|schema|code)", field):
                flags.append("technical_field_heuristic")
                if role == "unclassified":
                    role = "technical_candidate"
            if re.search(r"<script\b|\b(?:eval|Function)\s*\(", value, re.I):
                flags.append("executable_text_heuristic")
            if "{{" in value or "<%" in value or "${" in value:
                flags.append("template_or_macro")
            if re.search(r"<html\b|<iframe\b|<!doctype", value, re.I):
                flags.append("embedded_ui")
            for url in sorted(set(re.findall(r"https?://[^\s<>\"']+", value))):
                dependencies.append({"pointer": pointer, "locator": url, "status": "text_reference_unverified"})
        entry_pointer = next((p for p in activations if pointer.startswith(p + "/")), None)
        row = {"pointer": pointer, "role": role, "value_type": type(value).__name__, "sha256": sha(canonical(value)), "flags": flags}
        if isinstance(value, str):
            row["characters"] = len(value)
        if entry_pointer:
            row["worldbook_entry"] = entry_pointer
        regions.append(row)
    if fmt["kind"] in ("unknown_json", "ambiguous_json"):
        warnings.append("Unsupported or ambiguous root: structural inventory only; do not claim narrative-format support.")
    if any(r["flags"] for r in regions):
        warnings.append("Technical/template markers are heuristics; no embedded code was executed or fully interpreted.")
    candidates = [r["pointer"] for r in regions if r["role"] == "narrative_candidate"]
    return {"schema_version": "1.0", "adapter_version": VERSION, "format": fmt,
            "structural_inventory": "complete", "semantic_review": "pending", "conversion_implemented": True,
            "regions": regions, "narrative_candidate_pointers": candidates, "worldbook_entries": activations,
            "dependencies": dependencies, "warnings": warnings,
            "unclassified_string_count": sum(r["role"] == "unclassified" and r["value_type"] == "str" for r in regions)}


def empty_extraction(source_hash):
    return {"schema_version": "1.0", "source_sha256": source_hash, "review_status": "pending", "reviewed_region_pointers": [],
            "entities": [], "claims": [], "relationships": [], "constraints": [], "events": [], "unresolved": []}


def report_text(meta, inv, extraction, validation):
    lines = ["# Inspection report", "", f"Project: {VERSION}", f"Input: {html.escape(meta['source']['filename'])}",
             f"Format: {inv['format']['kind']}", f"Source SHA-256: `{meta['source']['sha256']}`", "",
             f"Structural leaf regions indexed: {len(inv['regions'])}", f"Narrative candidate regions: {len(inv['narrative_candidate_pointers'])}",
             f"Worldbook entries indexed, including inactive entries: {len(inv['worldbook_entries'])}",
             f"Unclassified text regions requiring triage: {inv['unclassified_string_count']}",
             f"Semantic review status: {extraction['review_status']}", f"Evidence checks: {validation['overall']}", "",
             "Conversion: not_run (inspection does not invoke the separate reviewed-plan converter)", "SillyTavern import: not_run", "Roleplay: not_run", "",
             "## Effective saved choices", ""]
    p = meta["effective_profile"]
    lines += [f"- Womanhood policy: {p['definition']['womanhood_policy']}", f"- Cast scope: {p['transformation']['scope']}",
              f"- Relationship policy: {p['relationships']['outcome_policy']}", f"- Workflow: {p['workflow']}", "", "## Warnings", ""]
    lines += ["- " + html.escape(w) for w in inv["warnings"]] or ["- None recorded."]
    lines += ["", "## Extracted claim summaries", ""]
    lines += [f"- {html.escape(c['id'])} [{c['status']}]: {html.escape(c['statement'])}" for c in extraction["claims"]] or ["- Pending agent extraction; empty fields do not establish absence of source facts."]
    next_action = ("Review the extracted claims and unresolved questions. Prepare a source-addressed conversion plan for supported fields when adaptation is requested. A synthetic trial alone does not establish real-card coverage. Evidence checks do not establish narrative completeness or human acceptance."
                   if extraction["review_status"] == "agent_reviewed" else
                   "Review source.snapshot.json and the inventoried pointers. Fill extracted.json according to the skill references, then run validate-extraction. A pointer/quote check cannot prove narrative completeness or truth.")
    lines += ["", "## Next action", "", next_action, ""]
    return "\n".join(lines)


def inspect_file(input_path, profile_path, output_path, override_path=None):
    source = Path(input_path).resolve()
    if source.suffix.lower() != ".json":
        raise ValueError("only JSON input is supported in this milestone; PNG ingestion is not implemented")
    raw = source.read_bytes()
    if len(raw) > 64 * 1024 * 1024:
        raise ValueError("input exceeds the current 64 MiB inspection limit")
    document = loads(raw.decode("utf-8-sig"))
    profile, changes = effective_profile(profile_path, override_path)
    inv = inventory(document)
    out = Path(output_path).resolve()
    if out.exists():
        raise ValueError("output already exists; choose a new run directory")
    if source == out:
        raise ValueError("input and output must be distinct")
    out.mkdir(parents=True, exist_ok=False)
    source_hash = sha(raw)
    meta = {"schema_version": "1.0", "run_id": out.name, "project_version": VERSION, "created_at_utc": utc(),
            "source": {"filename": source.name, "sha256": source_hash, "snapshot_semantic_sha256": sha(canonical(document))},
            "effective_profile": profile, "override_keys_changed": changes, "profile_sha256": sha(canonical(profile)),
            "tool": "offline Python inspector", "model": None, "model_note": "No model called by the inspector.",
            "stages": {"inspection": "pass", "semantic_extraction": "not_run", "conversion": "not_run", "import": "not_run", "roleplay": "not_run"}}
    ext = empty_extraction(source_hash)
    validation = {"schema_version": "1.0", "overall": "pending_semantic_review", "checks": [
        {"id": "strict-json-input", "outcome": "pass"}, {"id": "effective-profile", "outcome": "pass"},
        {"id": "semantic-extraction", "outcome": "not_run"}], "limitations": ["Structural checks do not establish narrative fidelity."]}
    (out / "source.original.json").write_bytes(raw)
    for name, value in (("source.snapshot.json", document), ("run.json", meta), ("inventory.json", inv), ("extracted.json", ext), ("validation.json", validation)):
        dump(out / name, value)
    (out / "report.md").write_text(report_text(meta, inv, ext, validation), encoding="utf-8")
    return out


def check_extraction(run_dir, extraction_path=None):
    run = Path(run_dir)
    meta = load(run / "run.json")
    source = load(run / "source.snapshot.json")
    inv = load(run / "inventory.json")
    ext = load(extraction_path or run / "extracted.json")
    errors = schema_errors(ext, "extraction.schema.json")
    if errors:
        raise ValueError("extraction schema: " + "; ".join(errors))
    if sha((run / "source.original.json").read_bytes()) != meta["source"]["sha256"]:
        raise ValueError("original source copy hash mismatch")
    if canonical(load(run / "source.original.json")) != canonical(source):
        raise ValueError("snapshot differs from preserved original")
    if sha(canonical(source)) != meta["source"]["snapshot_semantic_sha256"]:
        raise ValueError("snapshot hash mismatch")
    # Recompute historical structure; ignore only known release metadata differences.
    if inv.get("adapter_version") not in ("0.2.0-inspection", "0.3.0-review", "0.4.0-semantic-review", "0.5.0", VERSION):
        raise ValueError("unsupported inventory adapter version; inspect again with a supported tool")
    volatile = {"adapter_version", "conversion_implemented"}
    expected_inventory = inventory(source)
    if {k: v for k, v in expected_inventory.items() if k not in volatile} != {k: v for k, v in inv.items() if k not in volatile}:
        raise ValueError("inventory differs from source-derived inventory")
    if ext["source_sha256"] != meta["source"]["sha256"]:
        raise ValueError("extraction source hash mismatch")
    validate_profile(meta["effective_profile"])
    if sha(canonical(meta["effective_profile"])) != meta["profile_sha256"]:
        raise ValueError("effective profile hash mismatch")
    ids = [item["id"] for group in ("entities", "claims", "relationships", "constraints", "events", "unresolved") for item in ext[group]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate extraction IDs")
    entities = {item["id"] for item in ext["entities"]}
    claims = {item["id"] for item in ext["claims"]}
    for group in ("entities", "claims"):
        for item in ext[group]:
            for evidence in item["evidence"]:
                value = resolve(source, evidence["pointer"])
                if not isinstance(value, str) or evidence["quote"] not in value:
                    raise ValueError(f"quote does not match source at {evidence['pointer']}")
            for entity in item.get("entity_ids", []):
                if entity not in entities:
                    raise ValueError(f"missing entity: {entity}")
    for rel in ext["relationships"]:
        if rel["from_id"] not in entities or rel["to_id"] not in entities:
            raise ValueError("relationship endpoint is missing")
    for group in ("relationships", "constraints", "events"):
        for item in ext[group]:
            if not set(item["claim_ids"]).issubset(claims):
                raise ValueError(f"missing supporting claim for {item['id']}")
    for item in ext["unresolved"]:
        for pointer in item["source_pointers"]:
            resolve(source, pointer)
    region_pointers = {item["pointer"] for item in inv["regions"]}
    for pointer in ext["reviewed_region_pointers"]:
        if pointer not in region_pointers:
            raise ValueError(f"review acknowledgment is not an inventoried leaf: {pointer}")
    unreviewed = sorted(set(inv["narrative_candidate_pointers"]) - set(ext["reviewed_region_pointers"]))
    if ext["review_status"] == "agent_reviewed" and unreviewed:
        raise ValueError("agent_reviewed requires acknowledging all narrative candidate regions")
    return meta, inv, ext, {"schema_version": "1.0", "overall": "pass" if ext["review_status"] == "agent_reviewed" else "pending_semantic_review",
        "checked_at_utc": utc(), "checks": [{"id": "source-copy-integrity", "outcome": "pass"},
        {"id": "effective-profile", "outcome": "pass"}, {"id": "extraction-schema", "outcome": "pass"},
        {"id": "pointers-and-exact-quotes", "outcome": "pass"}, {"id": "internal-references", "outcome": "pass"},
        {"id": "semantic-review-acknowledgment", "outcome": "pass" if ext["review_status"] == "agent_reviewed" else "not_run"}],
        "unreviewed_narrative_pointers": unreviewed, "unclassified_string_count": inv["unclassified_string_count"],
        "limitations": ["Exact quotes do not prove that a statement follows from its source.",
                       "Review acknowledgments are agent assertions, not measured completeness or human acceptance."]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("input", type=Path)
    inspect.add_argument("--profile", type=Path, required=True)
    inspect.add_argument("--override", type=Path)
    inspect.add_argument("--output", type=Path, required=True)
    profile = commands.add_parser("resolve-profile")
    profile.add_argument("--profile", type=Path, required=True)
    profile.add_argument("--override", type=Path)
    profile.add_argument("--require-ready", action="store_true")
    check = commands.add_parser("validate-extraction")
    check.add_argument("run_dir", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            out = inspect_file(args.input, args.profile, args.output, args.override)
            print(f"INSPECTION_COMPLETE: {out}; semantic extraction is pending")
        elif args.command == "resolve-profile":
            result, changed = effective_profile(args.profile, args.override)
            validate_profile(result, args.require_ready)
            print(json.dumps({"effective_profile": result, "override_keys_changed": changed}, ensure_ascii=False, indent=2))
        else:
            meta, inv, ext, validation = check_extraction(args.run_dir)
            dump(args.run_dir / "validation.json", validation)
            meta["stages"]["semantic_extraction"] = "agent_reviewed" if ext["review_status"] == "agent_reviewed" else "not_run"
            dump(args.run_dir / "run.json", meta)
            (args.run_dir / "report.md").write_text(report_text(meta, inv, ext, validation), encoding="utf-8")
            print(validation["overall"].upper())
        return 0
    except (OSError, ValueError, RecursionError, KeyError, TypeError) as exc:
        message = str(exc)
        if args.command == "validate-extraction" and args.run_dir.is_dir():
            dump(args.run_dir / "validation.json", {"schema_version": "1.0", "overall": "fail", "checked_at_utc": utc(),
                "checks": [{"id": "extraction-evidence", "outcome": "fail", "details": message}]})
            (args.run_dir / "report.md").write_text("# Inspection validation failed\n\n" + html.escape(message) +
                "\n\nRead validation.json. Conversion, import, and roleplay remain not_run. Repair the evidence record before relying on an earlier report.\n", encoding="utf-8")
            try:
                failed_meta = load(args.run_dir / "run.json")
                if isinstance(failed_meta, dict) and isinstance(failed_meta.get("stages"), dict):
                    failed_meta["stages"]["semantic_extraction"] = "fail"
                    dump(args.run_dir / "run.json", failed_meta)
            except (OSError, ValueError):
                pass
        print(f"ERROR: {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
