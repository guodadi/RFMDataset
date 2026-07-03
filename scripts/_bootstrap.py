from __future__ import annotations

import sys
from pathlib import Path


def add_repo_root_to_path() -> None:
    root = Path(__file__).resolve().parents[1]
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
