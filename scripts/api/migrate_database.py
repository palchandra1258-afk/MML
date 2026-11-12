#!/usr/bin/env python3
"""Apply Alembic migrations using MCP-RI environment configuration."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from mcp_ri.api.main import _run_migrations  # noqa: E402
from mcp_ri.api.settings import APISettings  # noqa: E402


if __name__ == "__main__":
    _run_migrations(APISettings.from_environment().database_url)
    print("MCP-RI database is at the latest migration.")
