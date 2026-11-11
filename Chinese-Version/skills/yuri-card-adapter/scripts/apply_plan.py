#!/usr/bin/env python3
"""Apply reviewed narrative spans to a new card; never guess global substitutions."""
import argparse
import copy
import html
import json
import re
import sys
from pathlib import Path

import yuri_workbench as w

VERSION = "1.1.0"


def protected_syntax(text):
    tokens = re.findall(r"\{\{[^{}]*\}\}|<%[\s\S]*?%>|\$\{[^{}]*\}|\$\d+|</?[A-Za-z!][^>]*>|\[[A-Za-z][A-Za-z0-9_]*\|", text)
    blocks = [m.group(0) for m in re.finditer(r"<(script|style)\b[^>]*>[\s\S]*?</\1\s*>", text, re.I)]
    comments = re.findall(r"<!--[\s\S]*?-->", text)
    fences = re.findall(r"^\s*```[^\r\n]*", text, re.M)
    return tokens, blocks, comments, fences


def replace_spans(value, edits):
    previous_end = -1
    previous_start = -1
    for edit in sorted(edits, key=lambda e: e["start"]):
        start, end = edit["start"], edit["end"]
        if start < previous_end or start == previous_start or end < start or end > len(value):
            raise ValueError("overlapping or out-of-range edits")
        if value[start:end] != edit["expected"]:
            raise ValueError("expected span differs from source")
        previous_start, previous_end = start, end
    result = value
    for edit in sorted(edits, key=lambda e: e["start"], reverse=True):
        result = result[:edit["start"]] + edit["replacement"] + result[edit["end"]:]
    if result == value:
        raise ValueError("patch has no effect")
    if protected_syntax(value) != protected_syntax(result):
        raise ValueError("patch changes protected markup, template tokens, code/style, comments, or fences")
    return result


def set_existing(document, pointer, value):
    parent_pointer, token = pointer.rsplit("/", 1)
    parent = w.resolve(document, parent_pointer)
    token = token.replace("~1", "/").replace("~0", "~")
    if isinstance(parent, list):
        parent[int(token)] = value
    else:
        parent[token] = value


def plan_conversion(run_dir, plan):
    meta, inv, extracted, _ = w.check_extraction(run_dir)
    if extracted["review_status"] != "agent_reviewed":
        raise ValueError("source extraction must be agent_reviewed before applying a plan")
    profile = w.validate_profile(meta["effective_profile"], require_ready=True)
    errors = w.schema_errors(plan, "conversion.schema.json")
    if errors:
        raise ValueError("plan schema: " + "; ".join(errors))
    if plan["source_sha256"] != meta["source"]["sha256"] or plan["profile_sha256"] != meta["profile_sha256"]:
        raise ValueError("plan is stale: source or effective profile hash differs")
    entities = {e["id"]: e for e in extracted["entities"]}
    claims = {c["id"] for c in extracted["claims"]}
    selected = set(plan["selected_entity_ids"])
    scope = profile["transformation"]["scope"]
    for identity in selected:
        entity = entities.get(identity)
        if not entity or entity["kind"] != "character":
            raise ValueError("selected ID is not an extracted character")
        if identity in profile["transformation"]["excluded_character_ids"]:
            raise ValueError("selected character is explicitly excluded")
        if entity["role"] == "player" and profile["transformation"]["player_persona"] == "preserve":
            raise ValueError("player persona is protected")
        if scope == "main_cast" and entity["role"] not in ("main",):
            raise ValueError("main-cast scope cannot silently include a supporting or uncertain character")
        if scope == "named_characters" and identity not in profile["transformation"]["selected_character_ids"]:
            raise ValueError("selected ID is absent from the named-character profile selection")
    if profile["relationships"]["outcome_policy"] == "explicit_pairing_targets" and not profile["relationships"]["pairing_targets"]:
        raise ValueError("explicit pairing policy needs card-specific targets")
    source = w.load(Path(run_dir) / "source.snapshot.json")
    result = copy.deepcopy(source)
    regions = {r["pointer"]: r for r in inv["regions"]}
    pointers = [p["pointer"] for p in plan["patches"]]
    if len(set(pointers)) != len(pointers) or len({p["id"] for p in plan["patches"]}) != len(pointers):
        raise ValueError("duplicate patch pointer or patch ID")
    changes = []
    expected_changed = set()
    for patch in plan["patches"]:
        pointer = patch["pointer"]
        region = regions.get(pointer)
        if not region or region["role"] not in ("narrative_candidate", "authoring_instruction", "author_note"):
            raise ValueError(f"unsupported write region: {pointer}")
        if not set(patch["entity_ids"]).issubset(selected) or not set(patch["source_claim_ids"]).issubset(claims):
            raise ValueError("patch has unselected entities or missing source claims")
        value = w.resolve(source, pointer)
        if not isinstance(value, str) or w.sha(w.canonical(value)) != patch["expected_value_sha256"]:
            raise ValueError("field preimage hash differs")
        replacement = replace_spans(value, patch["edits"])
        set_existing(result, pointer, replacement)
        expected_changed.add(pointer)
        record = {"id": patch["id"], "pointer": pointer, "entity_ids": patch["entity_ids"], "source_claim_ids": patch["source_claim_ids"],
                  "reason": patch["reason"], "before_sha256": w.sha(w.canonical(value)), "after_sha256": w.sha(w.canonical(replacement)),
                  "edits": patch["edits"], "synchronized_mirrors": []}
        # Some exports carry both v2/v3 data and legacy top-level copies. Keep exact mirrors synchronized.
        if pointer.startswith("/data/") and pointer.count("/") == 2:
            key = pointer.rsplit("/", 1)[-1]
            if key in source:
                alias = "/" + key
                if source[key] != value:
                    raise ValueError(f"divergent legacy mirror needs an explicit source decision: {alias}")
                result[key] = replacement
                expected_changed.add(alias)
                record["synchronized_mirrors"].append(alias)
        changes.append(record)
    for pointer in plan["protected_pointers"]:
        if w.canonical(w.resolve(source, pointer)) != w.canonical(w.resolve(result, pointer)):
            raise ValueError(f"protected region changed: {pointer}")
    old_leaves, new_leaves = dict(w.walk(source)), dict(w.walk(result))
    actual_changed = {p for p in set(old_leaves) | set(new_leaves) if p not in old_leaves or p not in new_leaves or old_leaves[p] != new_leaves[p]}
    if actual_changed != expected_changed:
        raise ValueError("actual change scope differs from the authorized patch and synchronized mirrors")
    return result, changes, meta, sorted(actual_changed)


def apply(run_dir, plan_path, output_dir):
    plan = w.load(plan_path)
    result, changes, meta, paths = plan_conversion(run_dir, plan)
    out = Path(output_dir).resolve()
    if out.exists():
        raise ValueError("output already exists; choose a new conversion directory")
    out.mkdir(parents=True, exist_ok=False)
    card = out / "converted-card.review.json"
    w.dump(card, result)
    if w.canonical(w.load(card)) != w.canonical(result):
        raise ValueError("written artifact failed semantic round-trip")
    (out / "changes.jsonl").write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in changes), encoding="utf-8")
    validation = {"schema_version": "1.0", "engine_version": VERSION, "status": "offline_validated_review_candidate",
        "source_sha256": meta["source"]["sha256"], "profile_sha256": meta["profile_sha256"], "output_sha256": w.sha(card.read_bytes()),
        "plan_sha256": w.sha(Path(plan_path).read_bytes()), "changed_pointers": paths, "patch_fields": len(changes),
        "span_edits": sum(len(c["edits"]) for c in changes), "protected_pointers_checked": plan["protected_pointers"],
        "checks": ["source/extraction integrity", "ready effective profile", "selected-character scope", "field and span preimages", "markup/token/code preservation", "legacy mirror synchronization", "protected regions", "exact change scope", "export round-trip"],
        "semantic_quality": "author_review_pending", "import": "not_run", "roleplay": "not_run", "review_notes": plan["review_notes"]}
    w.dump(out / "conversion-validation.json", validation)
    lines = ["# Conversion review candidate", "", f"Engine: {VERSION}", f"Changed fields including synchronized legacy mirrors: {len(paths)}", f"Reviewed span edits: {validation['span_edits']}",
             "", "Offline source-preservation checks passed. This is not an import or roleplay result; author review remains pending.", "", "## Field changes", ""]
    for c in changes:
        lines.append(f"- `{c['pointer']}`: {html.escape(c['reason'])}")
    lines += ["", "## Review notes", "", *["- " + html.escape(n) for n in plan["review_notes"]], ""]
    (out / "conversion-report.md").write_text("\n".join(lines), encoding="utf-8")
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspection", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        print("REVIEW_CANDIDATE: " + str(apply(args.inspection, args.plan, args.output)))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
