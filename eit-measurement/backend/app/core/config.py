"""Runtime settings: where the data lives.

During development the data folder is eit-measurement/data/. An installed (packaged) app cannot write next to
its program files, so it sets the environment variable EIT_DATA_ROOT (for example to
Documents/EIT Measurement Studio) and every part of the app reads paths from here.
"""

from __future__ import annotations

import os
from pathlib import Path

from ..eit.config import REPO

DATA_SUBFOLDERS = ("hardware", "protocols", "studies", "sessions", "results")


def data_root() -> Path:
    """Folder that holds hardware/, protocols/, studies/, sessions/ and results/."""
    env = os.environ.get("EIT_DATA_ROOT")
    return Path(env).expanduser() if env else REPO / "data"


def data_path(*parts: str) -> Path:
    return data_root().joinpath(*parts)
