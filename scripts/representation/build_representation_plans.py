#!/usr/bin/env python3
"""Build bounded Phase 12 plans from existing Phase 11 JSONL states."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from mcp_ri.representation import (  # noqa: E402
    EdNetContentCatalog,
    RepresentationAvailabilityRegistry,
    build_representation_plan,
    validate_representation_plan,
)
from mcp_ri.cognitive_state.state_schema import validate_cognitive_state  # noqa: E402


DEFAULT_INPUT = ROOT / "results/reports/phase11-cognitive-state-20261106T104113Z/cognitive_states.jsonl"
DEFAULT_CONTENT = ROOT / "data/raw/ednet/ednet-content.zip"


def run(input_path: Path, output_dir: Path, content_archive: Path, max_plans: int) -> dict[str, Any]:
    started = time.perf_counter()
    output_dir.mkdir(parents=True, exist_ok=False)
    catalog = EdNetContentCatalog.from_zip(content_archive) if content_archive.is_file() else EdNetContentCatalog()
    registry = RepresentationAvailabilityRegistry()
    latest_plans: dict[tuple[str, str], dict[str, Any]] = {}
    counts: Counter[str] = Counter()
    plans_path = output_dir / "representation_plans.jsonl"
    plans_built = 0
    state_count = 0

    with input_path.open("r", encoding="utf-8") as source, plans_path.open("x", encoding="utf-8") as destination:
        for line in source:
            if not line.strip():
                continue
            state = json.loads(line)
            validate_cognitive_state(state)
            state_count += 1
            for estimate in state["concept_estimates"]:
                if plans_built >= max_plans:
                    break
                concept_id = estimate["concept_id"]
                key = (state["learner_id"], concept_id)
                prior = latest_plans.get(key)
                grounding = catalog.ground(concept_id)
                plan = build_representation_plan(
                    state,
                    concept_id,
                    registry=registry,
                    grounding=grounding,
                    prior_plan=prior,
                    teaching_context={} if prior is None else None,
                    _state_prevalidated=True,
                )
                validate_representation_plan(plan)
                latest_plans[key] = plan
                destination.write(json.dumps(plan, ensure_ascii=False, separators=(",", ":")) + "\n")
                plans_built += 1
                decision = plan["decision"]
                counts[f"action:{decision['selected_action']}"] += 1
                counts[f"representation:{decision['selected_representation'] or 'none'}"] += 1
                counts[f"delivery_status:{decision['delivery_status']}"] += 1
                for rule in decision["policy_trace"]:
                    if rule["conditions_satisfied"]:
                        counts[f"rule:{rule['rule_id']}"] += 1
            if plans_built >= max_plans:
                break

    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
        "input": str(input_path),
        "content_metadata_source": catalog.source,
        "sample_partition": "Phase 11 validation-learner snapshots only; inherited from Phase 11 input",
        "locked_test_partition_evaluated": False,
        "states_read": state_count,
        "plans_built": plans_built,
        "max_plans": max_plans,
        "availability_registry": registry.as_dict(),
        "taxonomy_version": registry.taxonomy_version,
        "counts": dict(sorted(counts.items())),
        "all_selected_capabilities_available": True,
        "plans_are_recommendations_only": True,
        "runtime_seconds": round(time.perf_counter() - started, 3),
        "output": str(plans_path),
        "claims_boundary": "Engineering coverage only; no representation efficacy or learning benefit is measured.",
    }
    (output_dir / "build_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--content-archive", type=Path, default=DEFAULT_CONTENT)
    parser.add_argument("--output-root", type=Path, default=ROOT / "results/reports")
    parser.add_argument("--max-plans", type=int, default=10000)
    args = parser.parse_args()
    if args.max_plans < 1:
        parser.error("--max-plans must be positive")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_root / f"phase12-representation-{stamp}"
    report = run(args.input, output_dir, args.content_archive, args.max_plans)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
