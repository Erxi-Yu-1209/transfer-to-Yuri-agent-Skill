#!/usr/bin/env python3
"""Generate Chinese runtime and export an allowlisted public folder or ZIP."""
import argparse
import fnmatch
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "PACKAGE_MANIFEST.json"
EXCLUDED_PARTS = {"private-inputs", "private-casework", "feedback-private", "runs", "dist", "build", ".git", ".venv", "venv", "__pycache__"}
RUNTIME_EXCLUSIONS = {"release-files.json", "scripts/build_release.py", "scripts/sync_source_skills.py", "tests/test_release.py"}


def safe_path(root, relative):
    parts = PurePosixPath(relative).parts
    if not relative or "\\" in relative or ":" in relative or not parts or relative.startswith("/") or any(p in ("..", ".", "") for p in relative.split("/")):
        raise ValueError(f"unsafe public path: {relative}")
    if any(p in EXCLUDED_PARTS or p == ".env" or p.startswith(".env.") for p in parts):
        raise ValueError(f"private path in public allowlist: {relative}")
    if any(fnmatch.fnmatch(parts[-1], pattern) for pattern in ("*.local.json", "*.pem", "*.key", "*.pyc", "*.log")):
        raise ValueError(f"private file in public allowlist: {relative}")
    path = root.joinpath(*parts)
    if any(p.is_symlink() for p in (path, *path.parents) if p != root.parent):
        raise ValueError(f"symlink in public path: {relative}")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"public path escapes root: {relative}")
    return path


def read_sources(root):
    names = json.loads((root / "release-files.json").read_text(encoding="utf-8"))["files"]
    if not isinstance(names, list) or not names or any(not isinstance(n, str) for n in names) or len(set(names)) != len(names):
        raise ValueError("allowlist must be a nonempty unique list of public paths")
    result = {}
    for name in names:
        if name == MANIFEST or name.startswith("Chinese-Version/"):
            raise ValueError("allowlist contains generated paths")
        result[name] = safe_path(root, name).read_bytes()
    return result


def chinese_files(sources):
    result = {name: data for name, data in sources.items() if name not in RUNTIME_EXCLUSIONS and not name.startswith("locales/")}
    result["README.md"] = sources["locales/zh-CN/README.md"]
    result["templates/TRIAL_FEEDBACK.md"] = sources["locales/zh-CN/TRIAL_FEEDBACK.md"]
    result["skills/yuri-card-adapter/assets/interaction.json"] = sources["locales/zh-CN/interaction.json"]
    for name in ("post-to-yuri-card", "novel-excerpt-to-yuri-card", "card-presentation"):
        path = f"skills/{name}/assets/interaction.json"
        if path in result:
            result[path] = sources["locales/zh-CN/interaction.json"]
    return result


def manifest(files, version):
    return (json.dumps({"project": "yuri-card-workbench", "version": version,
                       "scope": "public distribution only; manifest excludes itself",
                       "files": [{"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()} for name, data in sorted(files.items())]},
                      ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def expected_files(root):
    sources = read_sources(root)
    version = sources["VERSION"].decode().strip()
    chinese = chinese_files(sources)
    chinese[MANIFEST] = manifest(chinese, version)
    combined = dict(sources)
    combined.update({"Chinese-Version/" + name: data for name, data in chinese.items()})
    return combined, manifest(combined, version)


def sync_chinese(root):
    combined, metadata = expected_files(root)
    for name, data in combined.items():
        if not name.startswith("Chinese-Version/"):
            continue
        destination = safe_path(root, name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    (root / MANIFEST).write_bytes(metadata)


def check(root):
    combined, metadata = expected_files(root)
    for name, data in combined.items():
        if safe_path(root, name).read_bytes() != data:
            raise ValueError(f"generated edition differs: {name}; regenerate Chinese runtime")
    if (root / MANIFEST).read_bytes() != metadata:
        raise ValueError("public manifest is stale; regenerate before packaging")
    return combined, metadata


def build(root, output):
    files, metadata = check(root)
    output = Path(output)
    if output.exists():
        raise ValueError("archive already exists; choose a new path")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted({**files, MANIFEST: metadata}.items()):
            info = zipfile.ZipInfo("yuri-card-workbench/" + name, date_time=(2026, 11, 10, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return len(files) + 1


def main(argv=None, root=ROOT):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--sync-chinese", action="store_true", help="regenerate runtime files and both public manifests")
    modes.add_argument("--check", action="store_true", help="check generated parity and public-file hashes")
    modes.add_argument("--output", type=Path, help="write a new ZIP using only allowlisted public files")
    modes.add_argument("--folder", type=Path, help="write a new public folder; preferred delivery format")
    args = parser.parse_args(argv)
    try:
        if args.sync_chinese:
            sync_chinese(root)
            print("Generated Chinese runtime and public manifests.")
        elif args.check:
            files, _ = check(root)
            print(f"PASS: {len(files)} public files match the allowlist and language manifests.")
        elif args.folder:
            files, metadata = check(root)
            if args.folder.exists():
                raise ValueError("folder already exists; choose a new export path")
            for name, data in {**files, MANIFEST: metadata}.items():
                destination = args.folder / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
            print(f"Created public folder {args.folder} ({len(files) + 1} files).")
        else:
            count = build(root, args.output)
            print(f"Created {args.output} ({count} public files).")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
