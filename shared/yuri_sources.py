"""Yuri-specific decisions over frozen source records; no model/API calls.

General card serialization and PNG embedding are delegated to the MIT-licensed
Foreverse exporter. Exact-span guards are reused from Workbench 0.5.0.
"""
import argparse
import copy
import json
import re
import sys
from pathlib import Path

from source_core import HERE, canonical, digest, dump, ingest, load, validate_extraction, validate_schema, read_unit, review_unit, source_coverage
from spans import replace_spans
import card_io

VERSION = "1.1.1"


def profile_at(path=None):
    value = load(path or HERE / "assets/preferences.default.json")
    validate_schema(value, "preferences.schema.json")
    if value["status"] != "ready":
        raise ValueError("save the three default choices before adaptation")
    if set(value["transformation"]["selected_character_ids"]) & set(value["transformation"]["excluded_character_ids"]):
        raise ValueError("selected and excluded character IDs overlap")
    return value


def bindings(project, draft, profile):
    root = Path(project)
    result = {"sources_sha256": digest((root / "sources.json").read_bytes()),
            "extraction_sha256": digest((root / "extracted.json").read_bytes()),
            "draft_sha256": digest(Path(draft).read_bytes()), "profile_sha256": digest(canonical(profile))}
    if (root / "units.json").exists():
        result["units_sha256"] = digest((root / "units.json").read_bytes())
    return result


def bind_plan(project, draft, plan_path, output, profile_path=None):
    profile = profile_at(profile_path)
    validate_extraction(project)
    plan = load(plan_path)
    plan.update(bindings(project, draft, profile))
    card_io.write_new(output, plan)
    return plan


def resolve(document, pointer):
    value = document
    for token in pointer.strip("/").split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def set_value(document, pointer, value):
    parent, key = pointer.rsplit("/", 1)
    target = resolve(document, parent)
    if isinstance(target, list):
        target[int(key)] = value
    else:
        target[key] = value


def narrative_fields(card):
    for field in ("description", "personality", "scenario", "first_mes", "mes_example", "system_prompt", "post_history_instructions"):
        if card["data"].get(field):
            yield "/data/" + field
    for i, text in enumerate(card["data"].get("alternate_greetings", [])):
        if text:
            yield f"/data/alternate_greetings/{i}"
    for i, entry in enumerate(card["data"].get("character_book", {}).get("entries", [])):
        if entry.get("content"):
            yield f"/data/character_book/entries/{i}/content"


def adapt(project, draft, plan_path, output, profile_path=None, avatar=None):
    project, output = Path(project), Path(output)
    if output.exists():
        raise ValueError("output exists; use a new result directory")
    manifest, extraction = validate_extraction(project)
    if extraction["review_status"] != "agent_reviewed":
        raise ValueError("source extraction still needs agent review")
    profile, plan = profile_at(profile_path), load(plan_path)
    validate_schema(plan, "yuri-source-plan.schema.json")
    for key, value in bindings(project, draft, profile).items():
        if plan[key] != value:
            raise ValueError("stale plan binding: " + key)
    coverage = source_coverage(project)
    if coverage["mode"] == "segmented_source" and not coverage["complete_work_claimed"]:
        selected_units = set(plan.get("coverage_unit_ids", []))
        if not plan.get("allow_partial_source") or not selected_units or not selected_units.issubset(coverage["reviewed_unit_ids"]):
            raise ValueError("source has unread units; finish them or explicitly bind a reviewed partial scope")
    entities = {e["id"]: e for e in extraction["entities"]}
    claims = {c["id"]: c for c in extraction["claims"]}
    selected = set(plan["target_entity_ids"])
    if not selected or len(selected) != len(plan["target_entity_ids"]):
        raise ValueError("select a nonempty unique target cast")
    scope = profile["transformation"]["scope"]
    if scope == "main_cast":
        expected = {identity for identity, entity in entities.items() if entity["kind"] == "character" and entity["role"] == "main" and identity not in profile["transformation"]["excluded_character_ids"]}
        if selected != expected:
            raise ValueError("main-cast policy requires all extracted principal characters; use an explicit alternate profile for a subset")
    for entity_id in selected:
        entity = entities.get(entity_id)
        if not entity or entity["kind"] != "character" or entity_id in profile["transformation"]["excluded_character_ids"]:
            raise ValueError("target is missing, non-character or excluded")
        if scope == "main_cast" and entity["role"] != "main":
            raise ValueError("main-cast policy protects background, player and uncertain identities")
        if scope == "named_characters" and entity_id not in profile["transformation"]["selected_character_ids"]:
            raise ValueError("target is absent from saved named-character selection")
        if entity["role"] == "player" and profile["transformation"]["player_persona"] == "preserve":
            raise ValueError("player identity is protected")
        if profile["definition"]["womanhood_policy"] == "human_explicitly_female" and entity["nature"] != "human":
            raise ValueError("profile needs a human character; do not invent embodiment")
    decisions = {d["id"]: d for d in plan["decisions"]}
    if len(decisions) != len(plan["decisions"]):
        raise ValueError("duplicate adaptation decision ID")
    effective = {e: entities[e]["gender"] for e in selected}
    gender_decisions = set()
    relationships = {r["id"]: r for r in extraction["relationships"]}
    for decision in decisions.values():
        affected = set(decision["entity_ids"])
        if not affected or not affected.issubset(selected) or not set(decision["source_claim_ids"]).issubset(claims):
            raise ValueError("decision has unselected identities or missing source evidence")
        if decision["kind"] == "gender":
            if len(affected) != 1:
                raise ValueError("gender decisions bind one identity")
            entity_id = next(iter(affected))
            if entity_id in gender_decisions or decision["before"] != entities[entity_id]["gender"] or decision["after"] != "woman":
                raise ValueError("gender decision must match source identity and designate a woman once")
            if decision["before"] == "woman":
                raise ValueError("already-women characters need no invented identity change")
            gender_decisions.add(entity_id)
            effective[entity_id] = "woman"
        elif decision["kind"] == "relationship":
            relation = relationships.get(decision.get("relationship_id"))
            if not relation or relation["outcome"] != decision["before"]:
                raise ValueError("relationship decision differs from source outcome")
            policy = profile["relationships"]["outcome_policy"]
            if policy == "preserve_outcomes" and decision["before"] != decision["after"]:
                raise ValueError("saved policy protects relationship outcomes")
            if policy == "rederive_if_causal":
                causes = decision.get("cause_decision_ids", [])
                reasons = decision.get("causal_claim_ids", [])
                if not causes or not all(c in decisions and decisions[c]["kind"] in ("gender", "world_rule") for c in causes):
                    raise ValueError("relationship change needs explicit adaptation causes")
                if not reasons or not all(c in claims and claims[c]["kind"] in ("motivation", "world_rule", "history") for c in reasons) or not decision.get("changed_circumstance", "").strip():
                    raise ValueError("gender alone cannot justify a changed relationship outcome")
            if policy == "explicit_pairing_targets":
                pair = {relation["from_id"], relation["to_id"]}
                if not any({p["a"], p["b"]} == pair for p in profile["relationships"]["pairing_targets"]):
                    raise ValueError("relationship has no saved pairing target")
    if plan["mode"] == "yuri" and any(gender != "woman" for gender in effective.values()):
        raise ValueError("yuri targets need explicit authorial designation; unknown source gender is not evidence of womanhood")
    if plan["mode"] == "source" and (plan["decisions"] or plan["patches"]):
        raise ValueError("source-only export cannot contain adaptation edits")
    source = card_io.from_markdown(draft)
    if not source["data"].get("name") or not source["data"].get("first_mes"):
        raise ValueError("provide a named card and playable greeting")
    result = copy.deepcopy(source)
    inventions = {item["id"] for item in plan["creative_additions"]}
    if len(inventions) != len(plan["creative_additions"]):
        raise ValueError("duplicate creative-addition ID")
    fields = set(narrative_fields(source))
    for pointer in fields:
        mapping = plan["field_sources"].get(pointer)
        if not mapping or not (mapping["claim_ids"] or mapping["creative_ids"]) or not set(mapping["claim_ids"]).issubset(claims) or not set(mapping["creative_ids"]).issubset(inventions):
            raise ValueError("unmapped card prose or broken provenance: " + pointer)
    if set(plan["field_sources"]) - fields:
        raise ValueError("provenance map names absent narrative fields")
    used, seen, changes = set(), set(), []
    for patch in plan["patches"]:
        pointer = patch["pointer"]
        if pointer not in fields or pointer in seen or not set(patch["entity_ids"]).issubset(selected):
            raise ValueError("unsupported patch scope")
        if not patch["decision_ids"] or not set(patch["decision_ids"]).issubset(decisions):
            raise ValueError("patch lacks adaptation decisions")
        for identity in patch["entity_ids"]:
            if not any(identity in decisions[d]["entity_ids"] for d in patch["decision_ids"]):
                raise ValueError("patch identity is absent from its decision")
        value = resolve(source, pointer)
        if digest(canonical(value)) != patch["expected_value_sha256"]:
            raise ValueError("draft field preimage differs")
        new = replace_spans(value, patch["edits"])
        set_value(result, pointer, new)
        used.update(patch["decision_ids"])
        seen.add(pointer)
        changes.append({"pointer": pointer, "decision_ids": patch["decision_ids"], "edits": patch["edits"]})
    if used != set(decisions):
        raise ValueError("each adaptation decision needs a corresponding artifact edit")
    player_binding = plan.get("player_binding")
    if player_binding:
        identity = entities.get(player_binding["entity_id"])
        if not identity or identity["kind"] != "character":
            raise ValueError("player binding names no source character")
        if profile["transformation"]["player_persona"] != "explicitly_authorized":
            raise ValueError("player binding needs a scoped explicit authorization profile")
        for card in (source, result):
            prose = "\n".join(resolve(card, p) for p in narrative_fields(card))
            entry_labels = [str(entry.get(key, "")) for entry in card["data"].get("character_book", {}).get("entries", []) for key in ("comment", "keys", "secondary_keys")]
            checked_text = prose + "\n" + "\n".join(entry_labels)
            if "{{user}}" not in card["data"]["description"] or "{{user}}" not in card["data"]["first_mes"]:
                raise ValueError("bound player must use {{user}} in description and greeting")
            if any(alias and alias.casefold() in checked_text.casefold() for alias in player_binding["forbidden_runtime_aliases"]):
                raise ValueError("unresolved narrator/poster alias in player-bound card")
            if re.search(r"(?<!\{)\{user\}(?!\})", prose):
                raise ValueError("use the double-brace {{user}} macro")
    output.mkdir(parents=True)
    dump(output / "source-card.v2.json", source)
    dump(output / "yuri-card.v2.json", result)
    dump(output / "adaptation.json", {"version": VERSION, "mode": plan["mode"], "effective_profile": profile,
        "source_genders": {e: entities[e]["gender"] for e in selected}, "adapted_genders": effective,
        "decisions": plan["decisions"], "field_sources": plan["field_sources"], "creative_additions": plan["creative_additions"],
        "changes": changes, "source_records_unchanged": True,
        "player_binding": player_binding, "source_coverage": coverage,
        "sources_sha256": plan["sources_sha256"], "extraction_sha256": plan["extraction_sha256"],
        "draft_sha256": plan["draft_sha256"], "profile_sha256": plan["profile_sha256"], "plan_sha256": digest(Path(plan_path).read_bytes()),
        "units_sha256": plan.get("units_sha256"),
        "output_sha256": digest((output / "yuri-card.v2.json").read_bytes()), "host_import": "not_run", "live_roleplay": "not_run"})
    dump(output / "worldbook.json", result["data"].get("character_book", {"entries": []}))
    if avatar:
        card_io.pack(output / "yuri-card.v2.json", avatar, output / "yuri-card.png")
    (output / "review.md").write_text("# Yuri adaptation review\n\n" +
        f"Targets: {', '.join(plan['target_entity_ids'])}. Decisions: {len(decisions)}. Changed fields: {len(changes)}.\n\n" +
        "Source identity and authorial designation are recorded separately. Existing women can pass unchanged.\n" +
        "Review character-specific causality, referents, ages, kinship, background cast and player agency in conversation.\n" +
        "Evidence checks do not establish literary quality or actual SillyTavern behavior.\n", encoding="utf-8")
    return {"output": str(output), "mode": plan["mode"], "decisions": len(decisions), "changed_fields": len(changes),
            "effective_genders": effective, "host_import": "not_run", "live_roleplay": "not_run"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("ingest")
    p.add_argument("input", type=Path); p.add_argument("--project", type=Path, required=True)
    p.add_argument("--source-id", required=True); p.add_argument("--kind", choices=["post", "novel"], required=True)
    p.add_argument("--chapter", type=int); p.add_argument("--max-chars", type=int, default=6000)
    p.add_argument("--url"); p.add_argument("--encoding", default="utf-8-sig")
    p.add_argument("--all", dest="all_text", action="store_true", help="freeze the full source and plan bounded reading units")
    p.add_argument("--chunk-chars", type=int, default=6000, help="reading unit size in --all mode; not a dataset limit")
    p.add_argument("--max-file-mib", type=int, default=64, help="configurable input byte guard; separate from reading-unit size")
    p = sub.add_parser("next-unit"); p.add_argument("--project", type=Path, required=True); p.add_argument("--unit")
    p = sub.add_parser("review-unit"); p.add_argument("--project", type=Path, required=True); p.add_argument("--unit", required=True)
    p = sub.add_parser("validate"); p.add_argument("--project", type=Path, required=True)
    for command in ("bind-plan", "build"):
        p = sub.add_parser(command)
        for name in ("project", "draft", "plan", "output"):
            p.add_argument("--" + name, type=Path, required=True)
        p.add_argument("--profile", type=Path)
        if command == "build": p.add_argument("--avatar", type=Path)
    p = sub.add_parser("unpack-png"); p.add_argument("input", type=Path); p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("pack-png"); p.add_argument("card", type=Path); p.add_argument("--avatar", type=Path, required=True); p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("extract-worldbook"); p.add_argument("card", type=Path); p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("embed-worldbook"); p.add_argument("card", type=Path); p.add_argument("book", type=Path); p.add_argument("--output", type=Path, required=True); p.add_argument("--replace", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "ingest":
            result = ingest(args.input, args.project, args.source_id, args.kind, args.chapter, args.max_chars, args.url, args.encoding, args.all_text, args.chunk_chars, args.max_file_mib)
        elif args.command == "next-unit": result = read_unit(args.project, args.unit)
        elif args.command == "review-unit":
            stats = review_unit(args.project, args.unit)
            result = {k: v for k, v in stats.items() if k != "reviewed_unit_ids"}
            result["reviewed_units"] = len(stats["reviewed_unit_ids"])
        elif args.command == "validate":
            _, ext = validate_extraction(args.project)
            result = {"evidence": "pass", "agent_review": ext["review_status"], "semantic_correctness": "not_automatically_proven"}
        elif args.command == "bind-plan": result = bind_plan(args.project, args.draft, args.plan, args.output, args.profile)
        elif args.command == "build": result = adapt(args.project, args.draft, args.plan, args.output, args.profile, args.avatar)
        elif args.command == "unpack-png": card_io.write_new(args.output, card_io.read_png(args.input)); result = {"output": str(args.output)}
        elif args.command == "pack-png": card_io.pack(args.card, args.avatar, args.output); result = {"output": str(args.output)}
        elif args.command == "extract-worldbook": card_io.extract_worldbook(args.card, args.output); result = {"output": str(args.output)}
        else: card_io.embed_worldbook(args.card, args.book, args.output, args.replace); result = {"output": str(args.output)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, ETError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1


from xml.etree.ElementTree import ParseError as ETError
if __name__ == "__main__":
    sys.exit(main())
