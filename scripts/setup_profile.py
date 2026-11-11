#!/usr/bin/env python3
"""Run the edition's self-contained localized profile setup."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/yuri-card-adapter/scripts"))
from profile_setup import main

if __name__ == "__main__":
    sys.exit(main())
