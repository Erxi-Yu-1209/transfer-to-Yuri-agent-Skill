#!/usr/bin/env python3
"""Bundle one maintained source core into independently usable yuri skills."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
NAMES = ("post-to-yuri-card", "novel-excerpt-to-yuri-card")


def sync():
    for name in NAMES:
        skill = ROOT / "skills" / name
        destination = skill / "scripts/_shared"
        shutil.copytree(ROOT / "shared", destination, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (skill / "assets").mkdir(exist_ok=True)
        for filename, source in (("interaction.json", ROOT / "skills/yuri-card-adapter/assets/interaction.json"),
                                 ("preferences.default.json", ROOT / "config/preferences.json")):
            shutil.copyfile(source, skill / "assets" / filename)
        (skill / "scripts/source_pipeline.py").write_text(
            '#!/usr/bin/env python3\nimport sys\nfrom pathlib import Path\n'
            'sys.path.insert(0, str(Path(__file__).resolve().parent / "_shared"))\n'
            'from yuri_sources import main\nif __name__ == "__main__":\n    sys.exit(main())\n', encoding="utf-8")


if __name__ == "__main__":
    sync()
