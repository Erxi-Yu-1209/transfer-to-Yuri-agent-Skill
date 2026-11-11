#!/usr/bin/env python3
"""Validate one complete saved profile. This does not inspect or convert cards."""

import argparse
import json
import sys
from pathlib import Path


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate object key: {key}")
        result[key] = value
    return result


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=no_duplicate_keys)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print("DEPENDENCY_MISSING: install requirements-dev.txt", file=sys.stderr)
        return 2
    root = Path(__file__).resolve().parents[1]
    try:
        schema = load_json(root / "schemas" / "preferences.schema.json")
        profile = load_json(args.profile)
        workflows = load_json(root / "config" / "workflows.json")
        Draft202012Validator.check_schema(schema)
        errors = sorted(Draft202012Validator(schema).iter_errors(profile), key=lambda e: str(list(e.path)))
        if errors:
            for error in errors:
                location = "/" + "/".join(str(part) for part in error.path)
                print(f"INVALID {location}: {error.message}", file=sys.stderr)
            return 1
        if profile["workflow"] not in workflows["presets"]:
            print("INVALID: workflow has no matching preset", file=sys.stderr)
            return 1
        selected = set(profile["transformation"]["selected_character_ids"])
        excluded = set(profile["transformation"]["excluded_character_ids"])
        if selected & excluded:
            print("INVALID: selected and excluded characters overlap", file=sys.stderr)
            return 1
        if args.require_ready and profile["status"] != "ready":
            print("NOT_READY: resolve saved-profile decisions before conversion", file=sys.stderr)
            return 1
        if profile["status"] == "draft":
            print("DRAFT_VALID: inspection is permitted; conversion requires a ready profile")
        else:
            print("PROFILE_READY: profile valid; run-specific targets and format support still need checks")
        return 0
    except (OSError, ValueError) as error:
        print(f"INVALID: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
