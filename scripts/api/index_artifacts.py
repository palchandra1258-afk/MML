#!/usr/bin/env python3
"""Create/update application database offsets for Phase 9–12 JSONL outputs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402

from mcp_ri.api.artifact_index import ARTIFACT_KEYS, index_artifact  # noqa: E402
from mcp_ri.api.persistence import Database  # noqa: E402
from mcp_ri.api.settings import APISettings  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", choices=ARTIFACT_KEYS, action="append", dest="artifacts")
    args = parser.parse_args()
    settings = APISettings.from_environment()
    db = Database(settings.database_url)
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))
    command.upgrade(config, "head")
    selected = args.artifacts or list(ARTIFACT_KEYS)
    try:
        with db.session_factory.begin() as session:
            for name in selected:
                path = settings.artifact_paths()[name]
                if not path.is_file():
                    print(f"SKIP {name}: configured artifact is unavailable")
                    continue
                print(f"Indexing {name}...")
                count = index_artifact(
                    session,
                    name,
                    path,
                    on_progress=lambda done, key=name: print(f"  {key}: {done:,} records read"),
                )
                print(f"Indexed {name}: {count:,} records")
    finally:
        db.dispose()


if __name__ == "__main__":
    main()
