"""Preserve inherited card data while authoring new prose or approved presentation.

Workbench integration; the Foreverse serializer remains unmodified. Workflow
references: TavernWeave embedded-ui and render-regex-pipeline (see notices).
No embedded code, regular expressions, or remote assets are executed here.
"""
import copy
import re
from collections import Counter
from pathlib import Path

import card_io
from source_core import canonical, digest, dump, load, validate_schema
from spans import protected_syntax


def read_card(path):
    path = Path(path)
    if path.suffix.lower() == ".png":
        return card_io.read_png(path)
    if path.suffix.lower() in (".md", ".markdown"):
        return card_io.from_markdown(path)
    card = load(path)
    if card.get("spec") not in ("chara_card_v2", "chara_card_v3") or not isinstance(card.get("data"), dict):
        raise ValueError("rebuild requires a wrapped JSON/PNG card or Markdown draft")
    return card


def strings(value, pointer=""):
    if isinstance(value, str):
        yield pointer, value
    elif isinstance(value, dict):
        for key, item in value.items():
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            yield from strings(item, pointer + "/" + escaped)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from strings(item, pointer + "/" + str(i))


def audit(path):
    card = read_card(path)
    extensions = card["data"].get("extensions", {})
    assets, rich, status = [], [], []
    if Path(path).suffix.lower() == ".png":
        assets.append({"kind": "primary_png", "location": str(path), "visual_review": "not_performed"})
    for pointer, text in strings(card):
        if re.search(r"<(?:html|style|div|section|details|img|iframe)\b", text, re.I):
            rich.append(pointer)
        if re.search(r"status[_ -]?(?:panel|bar)|状态栏|狀態欄|<status", text, re.I):
            status.append(pointer)
        found = re.findall(r"<img\b[^>]*\bsrc\s*=\s*['\"]([^'\"]+)['\"]", text, re.I)
        found += re.findall(r"!\[[^\]]*\]\(([^\s)]+)", text)
        found += re.findall(r"url\(\s*['\"]?([^)'\"\s]+)", text, re.I)
        found += re.findall(r"https?://[^\s<>'\"]+\.(?:png|jpe?g|gif|webp|avif)(?:\?[^\s<>'\"]*)?", text, re.I)
        for reference in dict.fromkeys(found):
            row = {"kind": "embedded_or_linked_reference", "pointer": pointer, "visual_review": "not_performed"}
            if reference.startswith("data:"):
                row.update(location="inline data asset; inspect at source pointer", reference_sha256=digest(reference.encode("utf-8")), reference_characters=len(reference))
            else:
                row["location"] = reference
            assets.append(row)
    return {"source_sha256": digest(Path(path).read_bytes()),
            "extension_keys": sorted(extensions),
            "extensions_sha256": digest(canonical(extensions)),
            "regex_scripts_sha256": digest(canonical(extensions.get("regex_scripts"))),
            "rich_text_fields": rich, "status_protocol_candidates": status, "image_assets": assets,
            "image_alignment": "agent_visual_review_required; URL/name alone is not visual evidence",
            "host_validation": "not_run"}


def resolve(card, pointer):
    value = card
    for key in pointer.strip("/").split("/"):
        key = key.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def put(card, pointer, value):
    if pointer.startswith("/data/extensions/"):
        card["data"].setdefault("extensions", {})
    parent, key = pointer.rsplit("/", 1)
    target = resolve(card, parent)
    if isinstance(target, list):
        target[int(key)] = value
    else:
        target[key] = value


def preserve_markup(before, after):
    """Permit new prose without losing inherited render code or template tokens."""
    if isinstance(before, list) and isinstance(after, list):
        if len(after) < len(before):
            raise ValueError("preservation cannot silently drop alternate greetings")
        for a, b in zip(before, after):
            preserve_markup(a, b)
    elif isinstance(before, str) and isinstance(after, str):
        a, b = protected_syntax(before), protected_syntax(after)
        html = lambda tokens: [t for t in tokens if t.startswith("<")]
        if html(a[0]) != html(b[0]) or a[1:] != b[1:]:
            raise ValueError("keep styling requires inherited markup/code; graft prose into it or obtain redesign authorization")
        if Counter(a[0]) - Counter(b[0]):
            raise ValueError("rebuild removed inherited macros or protocol tokens")


ALLOWED = re.compile(r"^/data/(?:name|description|personality|scenario|first_mes|mes_example|system_prompt|post_history_instructions|alternate_greetings(?:/\d+)?|character_book(?:/entries/\d+/content)?|extensions/regex_scripts)$")


def bind(source, draft, plan_path, output):
    plan = load(plan_path)
    plan.update(source_sha256=digest(Path(source).read_bytes()), draft_sha256=digest(Path(draft).read_bytes()))
    validate_schema(plan, "card-rebuild.schema.json")
    card_io.write_new(output, plan)
    return {"output": str(output), "replacements": len(plan["replacements"])}


def rebuild(source_path, draft_path, plan_path, output):
    output = Path(output)
    if output.exists():
        raise ValueError("output exists; use a new result directory")
    plan = load(plan_path)
    validate_schema(plan, "card-rebuild.schema.json")
    for key, path in (("source_sha256", source_path), ("draft_sha256", draft_path)):
        if plan[key] != digest(Path(path).read_bytes()):
            raise ValueError("stale rebuild binding: " + key)
    if plan["presentation_choice"] == "redesign" and not plan.get("presentation_authorization", "").strip():
        raise ValueError("redesign requires the user's recorded instruction")
    source, draft = read_card(source_path), read_card(draft_path)
    result, seen, changes = copy.deepcopy(source), set(), []
    for change in plan["replacements"]:
        pointer = change["pointer"]
        if not ALLOWED.fullmatch(pointer) or pointer in seen or any(pointer.startswith(p + "/") or p.startswith(pointer + "/") for p in seen):
            raise ValueError("unsupported, duplicate or overlapping rebuild field")
        if pointer == "/data/extensions/regex_scripts" and plan["presentation_choice"] != "redesign":
            raise ValueError("renderer replacement requires redesign authorization")
        if pointer == "/data/character_book" and not plan.get("structure_authorization", "").strip():
            raise ValueError("whole-worldbook replacement requires explicit structure authorization; edit entry content to preserve activation settings")
        try:
            before = resolve(source, pointer)
        except KeyError:
            before = None
        if digest(canonical(before)) != change["expected_value_sha256"]:
            raise ValueError("rebuild field preimage differs: " + pointer)
        after = copy.deepcopy(resolve(draft, change["draft_pointer"]))
        if before == after:
            raise ValueError("rebuild replacement has no effect")
        direct_key = pointer.removeprefix("/data/")
        if "/" not in direct_key and direct_key in source and source[direct_key] != source["data"].get(direct_key):
            raise ValueError("conflicting legacy mirror: " + direct_key)
        if plan["presentation_choice"] == "keep":
            preserve_markup(before, after)
        put(result, pointer, after)
        seen.add(pointer)
        changes.append({**change, "output_value_sha256": digest(canonical(after))})
    for key in source:
        if key != "data" and key in result["data"] and source[key] == source["data"].get(key):
            result[key] = copy.deepcopy(result["data"][key])
    if not result["data"].get("name") or not result["data"].get("first_mes"):
        raise ValueError("a named card and playable greeting are required")
    # Unknown fields, extensions, depth_prompt, talkativeness and activation metadata
    # survive because only explicit fields in a deep copy are replaced.
    output.mkdir(parents=True)
    dump(output / "source-card.json", source)
    dump(output / "yuri-card.json", result)
    dump(output / "worldbook.json", result["data"].get("character_book", {"entries": []}))
    receipt = {"mode": "authored_rebuild", "source_sha256": plan["source_sha256"],
               "draft_sha256": plan["draft_sha256"], "plan_sha256": digest(Path(plan_path).read_bytes()),
               "output_sha256": digest((output / "yuri-card.json").read_bytes()),
               "presentation_choice": plan["presentation_choice"], "changes": changes,
               "preserved_unknown_data": True, "semantic_review": "required", "host_import": "not_run"}
    dump(output / "adaptation.json", receipt)
    return {"output": str(output), "changed_fields": len(changes), "host_import": "not_run"}
