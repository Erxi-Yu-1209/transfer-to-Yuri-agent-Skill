#!/usr/bin/env python3
"""Verify private case manifests and reconstruct candidates. Never grant semantic acceptance."""
import argparse
import datetime
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/yuri-card-adapter/scripts"))
import yuri_workbench as w
import apply_plan as engine

REQUIRED = {"extracted.json", "conversion-plan.json", "converted-card.review.json", "changes.jsonl", "conversion-validation.json"}


def verify_manifest(case):
    case = Path(case).resolve()
    manifest = w.load(case / "CASE_MANIFEST.json")
    items = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(items, list):
        raise ValueError("case manifest must contain a files array")
    seen = set()
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ValueError("invalid manifest record")
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts or not relative.parts or "\\" in item["path"]:
            raise ValueError("unsafe manifest path")
        normalized = relative.as_posix()
        if normalized in seen:
            raise ValueError("duplicate manifest path")
        seen.add(normalized)
        path = (case / relative).resolve()
        if not path.is_relative_to(case) or not path.is_file():
            raise ValueError("manifest target missing or outside case directory")
        raw = path.read_bytes()
        if w.sha(raw) != item.get("sha256") or ("bytes" in item and len(raw) != item["bytes"]):
            raise ValueError(f"manifest mismatch: {normalized}")
    if not REQUIRED.issubset(seen):
        raise ValueError("manifest omits required case artifacts")
    return len(items)


def semantic_status(review_path, source_hash, candidate_hash, case_id=None):
    if review_path is None or not Path(review_path).is_file():
        return {"status": "not_recorded", "author_acceptance": "pending", "live_trial": "not_assessed"}
    review = w.load(review_path)
    errors = w.schema_errors(review, "semantic-review.schema.json")
    if errors:
        raise ValueError("semantic review schema: " + "; ".join(errors))
    if review["source_sha256"] != source_hash or review["candidate_sha256"] != candidate_hash:
        raise ValueError("semantic review describes a different source or candidate")
    if case_id is not None and review["case_id"] != case_id:
        raise ValueError("semantic review describes a different case")
    issues = review["issues"]
    if len({i["id"] for i in issues}) != len(issues):
        raise ValueError("duplicate semantic issue ID")
    if any(i["status"] == "open" and i["severity"] == "blocker" for i in issues):
        state = "needs_fix"
    elif any(i["status"] == "open" and i["severity"] == "decision" for i in issues):
        state = "needs_author_decision"
    else:
        state = "agent_review_complete_author_pending"
    return {"status": state, "author_acceptance": "pending", "live_trial": "not_assessed",
            "open_issues": [i["id"] for i in issues if i["status"] == "open"],
            "review_sha256": w.sha(Path(review_path).read_bytes())}


def verify_case(case_dir, inspection_dir, review_path=None):
    case = Path(case_dir)
    result = {"case_id": case.name, "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "offline_integrity": "fail", "semantic_review": {"status": "not_recorded", "author_acceptance": "pending"},
              "runtime_validation": "not_performed_by_this_verifier", "checks": []}
    def passed(name, details=None):
        result["checks"].append({"id": name, "outcome": "pass", **({"details": details} if details is not None else {})})
    try:
        count = verify_manifest(case)
        passed("case-manifest", {"files": count})
        candidate_raw = (case / "converted-card.review.json").read_bytes()
        candidate = w.load(case / "converted-card.review.json")
        plan = w.load(case / "conversion-plan.json")
        validation = w.load(case / "conversion-validation.json")
        recorded_changes = [w.loads(line) for line in (case / "changes.jsonl").read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        # Original runs may have a pending extraction. Use the delivered extraction in an isolated copy.
        with tempfile.TemporaryDirectory(prefix="yuri-case-verify-") as temporary:
            staging = Path(temporary)
            for name in ("run.json", "inventory.json", "source.original.json", "source.snapshot.json"):
                shutil.copyfile(Path(inspection_dir) / name, staging / name)
            shutil.copyfile(case / "extracted.json", staging / "extracted.json")
            reconstructed, changes, meta, paths = engine.plan_conversion(staging, plan)
        passed("source-and-extraction-integrity")
        if w.canonical(reconstructed) != w.canonical(candidate):
            raise ValueError("candidate differs from independently reconstructed plan result")
        passed("source-plus-plan-reconstruction")
        if w.canonical(changes) != w.canonical(recorded_changes):
            raise ValueError("change log differs from reconstructed engine changes")
        passed("change-records-match-reconstruction")
        checks = {
            "source_sha256": meta["source"]["sha256"], "profile_sha256": meta["profile_sha256"],
            "output_sha256": w.sha(candidate_raw), "plan_sha256": w.sha((case / "conversion-plan.json").read_bytes()),
            "changed_pointers": paths, "patch_fields": len(changes), "span_edits": sum(len(c["edits"]) for c in changes),
            "protected_pointers_checked": plan["protected_pointers"],
        }
        for key, expected in checks.items():
            if w.canonical(validation.get(key)) != w.canonical(expected):
                raise ValueError(f"conversion validation metadata mismatch: {key}")
        passed("recorded-hashes-counts-and-write-scope")
        result.update(offline_integrity="pass", source_sha256=meta["source"]["sha256"], candidate_sha256=w.sha(candidate_raw),
                      patch_fields=len(changes), span_edits=checks["span_edits"])
        try:
            result["semantic_review"] = semantic_status(review_path, result["source_sha256"], result["candidate_sha256"], case.name)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            result["semantic_review"] = {"status": "invalid_review", "author_acceptance": "pending", "error": str(exc)}
        result["limitations"] = ["Reconstruction verifies the authored plan, not its narrative meaning.", "No human acceptance or host behavior is inferred from these checks."]
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as exc:
        result["checks"].append({"id": "case-verification", "outcome": "fail", "details": str(exc)})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--inspection-root", type=Path, required=True)
    parser.add_argument("--case", action="append", help="card-NNN; repeat for explicit subset, otherwise discover all card-NNN directories")
    parser.add_argument("--review-root", type=Path, help="optional separate directory containing card-NNN/semantic-review.json")
    parser.add_argument("--output", type=Path, help="write a new report; existing report paths are refused")
    parser.add_argument("--require-semantic-clear", action="store_true", help="also fail when a current semantic review is missing or has blockers/decisions")
    args = parser.parse_args(argv)
    try:
        if args.output and args.output.exists():
            raise ValueError("output already exists; choose a new report path")
        names = args.case or sorted(p.name for p in args.case_root.iterdir() if p.is_dir() and re.fullmatch(r"card-[0-9]{3}", p.name))
        if not names or len(names) != len(set(names)) or any(not re.fullmatch(r"card-[0-9]{3}", n) for n in names):
            raise ValueError("select a nonempty unique set of card-NNN directories")
        rows = []
        for name in names:
            review = (args.review_root or args.case_root) / name / "semantic-review.json"
            rows.append(verify_case(args.case_root / name, args.inspection_root / ("inspect-" + name[5:]), review))
        report = {"schema_version": "1.0", "cases_verified": len(rows), "offline_passed": sum(r["offline_integrity"] == "pass" for r in rows),
                  "semantic_acceptance_granted": False, "results": rows}
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            w.dump(args.output, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        success = all(r["offline_integrity"] == "pass" and r["semantic_review"]["status"] != "invalid_review" for r in rows)
        if args.require_semantic_clear:
            success = success and all(r["semantic_review"]["status"] == "agent_review_complete_author_pending" for r in rows)
        return 0 if success else 1
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
