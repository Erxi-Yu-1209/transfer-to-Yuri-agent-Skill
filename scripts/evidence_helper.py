#!/usr/bin/env python3
"""Deterministic helpers for authoring exact-span conversion plans.

Commands:
  field-hash RUN_DIR POINTER        sha256 of the canonical JSON encoding of
                                    the string at POINTER in source.snapshot.json
                                    (the value conversion plans use for
                                    expected_value_sha256), plus its length.
  spans RUN_DIR POINTER NEEDLE [N]  code-point (start, end) offsets of every
                                    occurrence of NEEDLE in the string at
                                    POINTER; N selects a 1-based occurrence.
  diff RUN_DIR CARD                 leaf pointers whose values differ between
                                    source.snapshot.json and CARD, grouped as
                                    changed/added/removed.

Offsets use Python Unicode code points in the ORIGINAL string, matching the
conversion plan schema. No card content is executed or interpreted.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/yuri-card-adapter/scripts"))
import yuri_workbench as w


def load_doc(path):
    return w.load(path)


def find_spans(value, needle, overlapping=False):
    """Return original Unicode-code-point intervals; empty needles are ambiguous."""
    if not isinstance(value, str) or not isinstance(needle, str) or not needle:
        raise ValueError("value and nonempty needle must be strings")
    hits, start = [], 0
    while True:
        found = value.find(needle, start)
        if found < 0:
            return hits
        hits.append((found, found + len(needle)))
        start = found + (1 if overlapping else len(needle))


def leaf_diff(source, converted):
    """Compare JSON encodings so booleans/numbers and numeric types stay distinct."""
    old, new = dict(w.walk(source)), dict(w.walk(converted))
    return {
        "changed": sorted(p for p in old.keys() & new.keys() if w.canonical(old[p]) != w.canonical(new[p])),
        "added": sorted(new.keys() - old.keys()),
        "removed": sorted(old.keys() - new.keys()),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    field = sub.add_parser("field-hash")
    field.add_argument("run_dir", type=Path)
    field.add_argument("pointer")
    spans = sub.add_parser("spans")
    spans.add_argument("run_dir", type=Path)
    spans.add_argument("pointer")
    spans.add_argument("needle")
    spans.add_argument("occurrence", nargs="?", type=int)
    spans.add_argument("--overlapping", action="store_true", help="include overlapping matches; default matches remain nonoverlapping")
    diff = sub.add_parser("diff")
    diff.add_argument("run_dir", type=Path)
    diff.add_argument("card", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "field-hash":
            value = w.resolve(load_doc(args.run_dir / "source.snapshot.json"), args.pointer)
            if not isinstance(value, str):
                raise ValueError("value at pointer is not a string")
            print("sha256=" + w.sha(w.canonical(value)))
            print("length=" + str(len(value)))
        elif args.command == "spans":
            value = w.resolve(load_doc(args.run_dir / "source.snapshot.json"), args.pointer)
            if not isinstance(value, str):
                raise ValueError("value at pointer is not a string")
            hits = find_spans(value, args.needle, args.overlapping)
            if args.occurrence is not None and not (1 <= args.occurrence <= len(hits)):
                raise ValueError("requested occurrence does not exist")
            print("occurrences=" + str(len(hits)))
            for i, (begin, end) in enumerate(hits, start=1):
                mark = " <--" if args.occurrence == i else ""
                print(f"#{i} start={begin} end={end}{mark}")
        elif args.command == "diff":
            source = load_doc(args.run_dir / "source.snapshot.json")
            converted = w.load(args.card)
            differences = leaf_diff(source, converted)
            changed, added, removed = (differences[k] for k in ("changed", "added", "removed"))
            print("changed=" + str(len(changed)) + " added=" + str(len(added)) + " removed=" + str(len(removed)))
            for p in changed:
                print("changed: " + p)
            for p in added:
                print("added: " + p)
            for p in removed:
                print("removed: " + p)
        return 0
    except (OSError, ValueError, RecursionError, KeyError, TypeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
