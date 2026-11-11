#!/usr/bin/env python3
"""Project entry point for the shared yuri source pipeline."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "shared"))
from yuri_sources import main
if __name__ == "__main__":
    sys.exit(main())
