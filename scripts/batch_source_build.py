#!/usr/bin/env python3
"""Apply already-authored yuri plans with per-item status and safe resumption."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "shared"))
import source_core as c
import yuri_sources as y


def run(jobs_path, report_path):
    jobs_path, report_path = Path(jobs_path), Path(report_path)
    if report_path.exists():
        raise ValueError("choose a new batch report path")
    jobs = c.load(jobs_path)
    if not isinstance(jobs, list) or not jobs or len(jobs) > 100 or len({j["id"] for j in jobs}) != len(jobs):
        raise ValueError("provide 1–100 unique named jobs")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {"version": "1.1.0", "results": [], "host_import": "not_run", "live_roleplay": "not_run"}
    for job in jobs:
        row = {"id": job["id"], "status": "failed"}
        try:
            paths = {key: (jobs_path.parent / job[key]).resolve() for key in ("project", "draft", "plan", "output")}
            profile = (jobs_path.parent / job["profile"]).resolve() if job.get("profile") else None
            if paths["output"].exists():
                meta = c.load(paths["output"] / "adaptation.json")
                current = y.bindings(paths["project"], paths["draft"], y.profile_at(profile))
                c.validate_extraction(paths["project"])
                if any(meta.get(key) != value for key, value in current.items()) or meta.get("plan_sha256") != c.digest(paths["plan"].read_bytes()) or meta["output_sha256"] != c.digest((paths["output"] / "yuri-card.v2.json").read_bytes()):
                    raise ValueError("existing output is stale; use a new output directory")
                row["status"] = "already_completed"
            else:
                row.update(y.adapt(paths["project"], paths["draft"], paths["plan"], paths["output"], profile))
                row["status"] = "completed"
        except (OSError, ValueError, KeyError, TypeError) as exc:
            row["error"] = str(exc)
        report["results"].append(row)
        # The report was created for this invocation; update it after each item.
        c.dump(report_path, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=Path, required=True); parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run(args.jobs, args.report)
        failed = sum(r["status"] == "failed" for r in report["results"])
        print(f"Processed {len(report['results'])} jobs; failed: {failed}; report: {args.report}")
        return 1 if failed else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
