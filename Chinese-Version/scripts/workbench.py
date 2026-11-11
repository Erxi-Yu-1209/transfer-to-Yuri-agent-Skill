#!/usr/bin/env python3
"""Project convenience wrapper; the self-contained skill also works on its own."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/yuri-card-adapter/scripts"))
from yuri_workbench import main

if __name__ == "__main__":
    arguments = sys.argv[1:]
    if arguments and arguments[0] in ("inspect", "resolve-profile") and "--profile" not in arguments and not any(a.startswith("--profile=") for a in arguments):
        arguments += ["--profile", str(ROOT / "config/preferences.json")]
    sys.exit(main(arguments))
