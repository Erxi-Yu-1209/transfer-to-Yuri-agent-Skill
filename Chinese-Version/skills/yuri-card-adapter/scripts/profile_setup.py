#!/usr/bin/env python3
"""Present three localized profile choices; write a new validated profile."""
import argparse
import copy
import json
import sys
from pathlib import Path

import yuri_workbench as w

BUNDLE = Path(__file__).resolve().parents[1]


def catalog():
    return w.load(BUNDLE / "assets/interaction.json")


def display_choices(profile, output=print):
    text = catalog()
    for question in text["questions"]:
        output(question["prompt"])
        current = w.resolve(profile, question["pointer"])
        for index, option in enumerate(question["options"], 1):
            suffix = text["default_marker"] if option["value"] == current else ""
            output(f"  {index}. {option['label']}{suffix}")


def collect(profile, ask=input, output=print):
    result = copy.deepcopy(profile)
    text = catalog()
    for question in text["questions"]:
        output(question["prompt"])
        current = w.resolve(result, question["pointer"])
        options = question["options"]
        for index, option in enumerate(options, 1):
            suffix = text["default_marker"] if option["value"] == current else ""
            output(f"  {index}. {option['label']}{suffix}")
        while True:
            answer = ask(text["answer_prompt"]).strip()
            if not answer and current in [item["value"] for item in options]:
                chosen = current
                break
            if answer.isascii() and answer.isdigit() and 1 <= int(answer) <= len(options):
                chosen = options[int(answer) - 1]["value"]
                break
            output(text["invalid_answer"])
        parent, leaf = question["pointer"].rsplit("/", 1)
        w.resolve(result, parent)[leaf] = chosen
        if chosen == "custom" and not result["definition"]["custom_criteria"].strip():
            while not result["definition"]["custom_criteria"].strip():
                result["definition"]["custom_criteria"] = ask(text["custom_prompt"]).strip()
        elif question["pointer"] == "/definition/womanhood_policy" and chosen != "custom":
            result["definition"]["custom_criteria"] = ""
        # A changed selection rule must not silently reuse another rule's card IDs.
        if chosen != current and question["pointer"] == "/transformation/scope":
            result["transformation"]["selected_character_ids"] = []
        if chosen != current and question["pointer"] == "/relationships/outcome_policy":
            result["relationships"]["pairing_targets"] = []
    result["status"] = "ready"
    return w.validate_profile(result, require_ready=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, help="complete existing profile; defaults to bundled ready template")
    parser.add_argument("--show", action="store_true", help="display choices without asking or writing")
    parser.add_argument("--defaults", action="store_true", help="save the selected base unchanged without asking")
    parser.add_argument("--output", type=Path, help="new profile path; existing files are refused")
    args = parser.parse_args(argv)
    messages = catalog()
    try:
        profile = w.load(args.base or BUNDLE / "assets/preferences.default.json")
        w.validate_profile(profile)
        if args.show:
            if args.output or args.defaults:
                parser.error("--show cannot be combined with --output or --defaults")
            display_choices(profile)
            return 0
        if args.output is None:
            parser.error("--output is required unless --show is selected")
        if args.output.exists():
            raise ValueError(messages["exists_error"])
        profile = w.validate_profile(profile, require_ready=True) if args.defaults else collect(profile)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation also protects against a race after the existence check.
        with args.output.open("x", encoding="utf-8") as target:
            target.write(json.dumps(profile, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
        print(messages["saved"].format(path=args.output))
        return 0
    except (OSError, ValueError, EOFError, KeyboardInterrupt) as exc:
        print(messages["error"].format(detail=str(exc)), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
