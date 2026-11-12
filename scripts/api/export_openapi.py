#!/usr/bin/env python3
"""Export the live FastAPI application's generated OpenAPI contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from mcp_ri.api.main import app  # noqa: E402


def main() -> None:
    target = ROOT / "shared/api-contracts/openapi.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote generated OpenAPI contract: {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
