"""Environment-backed settings with repository-scoped artifact defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _artifact_path(name: str, relative: str) -> Path:
    configured = os.getenv(name)
    path = Path(configured).expanduser() if configured else REPOSITORY_ROOT / relative
    return path.resolve()


@dataclass(frozen=True)
class APISettings:
    database_url: str
    cors_origins: tuple[str, ...]
    phase9_states_path: Path
    phase10_evidence_path: Path
    phase11_states_path: Path
    phase12_plans_path: Path
    environment: str = "development"

    @classmethod
    def from_environment(cls) -> "APISettings":
        default_db = REPOSITORY_ROOT / "data/application/mcp_ri.sqlite3"
        origins_raw = os.getenv("MCP_RI_CORS_ORIGINS", "http://localhost:3000")
        origins = tuple(origin.strip() for origin in origins_raw.split(",") if origin.strip())
        return cls(
            database_url=os.getenv("MCP_RI_DATABASE_URL", f"sqlite:///{default_db}"),
            cors_origins=origins,
            phase9_states_path=_artifact_path(
                "MCP_RI_PHASE9_STATES_PATH",
                "results/reports/phase9-learner-state-20261106T081823Z/validation_learner_states.jsonl",
            ),
            phase10_evidence_path=_artifact_path(
                "MCP_RI_PHASE10_EVIDENCE_PATH",
                "results/reports/phase10-evidence-20261106T101321Z/interaction_evidence.jsonl",
            ),
            phase11_states_path=_artifact_path(
                "MCP_RI_PHASE11_STATES_PATH",
                "results/reports/phase11-cognitive-state-20261106T104113Z/cognitive_states.jsonl",
            ),
            phase12_plans_path=_artifact_path(
                "MCP_RI_PHASE12_PLANS_PATH",
                "results/reports/phase12-representation-20261106T112420Z/representation_plans.jsonl",
            ),
            environment=os.getenv("MCP_RI_ENVIRONMENT", "development"),
        )

    def artifact_paths(self) -> dict[str, Path]:
        return {
            "phase9_states": self.phase9_states_path,
            "phase10_evidence": self.phase10_evidence_path,
            "phase11_states": self.phase11_states_path,
            "phase12_plans": self.phase12_plans_path,
        }
