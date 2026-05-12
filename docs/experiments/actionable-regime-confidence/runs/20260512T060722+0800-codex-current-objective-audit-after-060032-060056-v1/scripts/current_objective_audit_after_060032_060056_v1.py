#!/usr/bin/env python3
"""Audit Board A objective coverage after 060032 and 060056 evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T060722+0800-codex-current-objective-audit-after-060032-060056-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
ART_DIR = RUN_ROOT / "current-objective-audit-after-060032-060056-v1"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")

REQUIRED_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]

ARTIFACTS = {
    "hgb_per_regime_fields": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T053852-codex-hgb-per-regime-field-materialization-v1/"
        "checks/hgb_per_regime_field_materialization_v1_assertions.out"
    ),
    "hgb_axis_audit": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T053856-codex-hgb-validation-axis-audit-after-051844-v1/"
        "checks/hgb_validation_axis_audit_after_051844_v1_assertions.out"
    ),
    "readonly_runtime_chain": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T054116-codex-readonly-runtime-chain-after-053933-v1/"
        "checks/readonly_runtime_chain_after_053933_v1_assertions.out"
    ),
    "autoquant_reuse": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T055200-codex-autoquant-local-reuse-readiness-after-054116-v1/"
        "checks/autoquant_local_reuse_readiness_after_054116_v1_assertions.out"
    ),
    "autoquant_cache_backtest": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T060056-codex-autoquant-local-cache-isolated-backtest-after-055200-v1/"
        "checks/autoquant_local_cache_isolated_backtest_after_055200_v1_assertions.out"
    ),
    "r6_dispatch_feasibility": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T055516-codex-r6-owner-export-dispatch-feasibility-readback-v1/"
        "checks/r6_owner_export_dispatch_feasibility_readback_v1_assertions.out"
    ),
    "r6_local_intake_search": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T060032-codex-r6-local-owner-export-intake-search-v1/"
        "checks/r6_local_owner_export_intake_search_v1_assertions.out"
    ),
    "r3_r5_public_search": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T055829+0800-codex-r3-r5-public-source-live-search-rerun-v2/"
        "checks/r3_r5_public_source_live_search_rerun_v2_assertions.out"
    ),
    "latest_completion_audit": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T055930-codex-current-objective-audit-after-055658-v1/"
        "checks/current_objective_audit_after_055658_v1_assertions.out"
    ),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def assertion_contains(path: Path, pattern: str) -> bool:
    return bool(re.search(pattern, read_text(path)))


def row(requirement: str, evidence_key: str, evidence: str, status: str, gap: str) -> dict[str, str]:
    return {
        "requirement": requirement,
        "evidence_key": evidence_key,
        "evidence": evidence,
        "status": status,
        "gap": gap,
    }


def main() -> int:
    ART_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    board_text = read_text(BOARD)
    root_state = {str(path): path.exists() for path in REQUIRED_ROOTS}
    artifact_state = {key: path.exists() for key, path in ARTIFACTS.items()}

    hgb_complete = artifact_state["hgb_per_regime_fields"] and assertion_contains(
        ARTIFACTS["hgb_per_regime_fields"],
        r"all_hgb_labels_field_complete|field_complete",
    )
    axis_daily_only = "timeframe_counts=1d:248440" in board_text or assertion_contains(
        ARTIFACTS["hgb_axis_audit"],
        r"daily|1d",
    )
    r6_no_rows = assertion_contains(ARTIFACTS["r6_local_intake_search"], r"source_control_evidence_acquired=false")
    autoquant_nonpromoting = assertion_contains(ARTIFACTS["autoquant_cache_backtest"], r"no_promotion|update_goal=false")
    public_search_nonpromoting = assertion_contains(ARTIFACTS["r3_r5_public_search"], r"compatible_source_rows_found=false")
    roots_absent = not any(root_state.values())

    checklist = [
        row(
            "Every active regime has field-complete >=95% diagnostic confidence.",
            "053852",
            str(ARTIFACTS["hgb_per_regime_fields"]),
            "met_diagnostic_only" if hgb_complete else "missing_or_unverified",
            "Diagnostic confidence cannot promote without source/control unlock.",
        ),
        row(
            "Confidence is validated across other markets and cycles/timeframes.",
            "053856",
            str(ARTIFACTS["hgb_axis_audit"]),
            "not_met" if axis_daily_only else "uncertain",
            "Latest axis evidence remains daily-only for HGB labels; native cross-timeframe source labels are absent.",
        ),
        row(
            "R3 native sub-hour source-owned labels exist for required intake.",
            "R3 root",
            "/tmp/ict-engine-native-subhour-source-label-intake",
            "not_met" if not root_state[str(REQUIRED_ROOTS[1])] else "present_needs_verifier",
            "Required intake root is absent.",
        ),
        row(
            "R5 post-cutoff source-owned MainRegimeV2 recency rows exist.",
            "R5 root",
            "/tmp/ict-engine-source-panel-recency-extension",
            "not_met" if not root_state[str(REQUIRED_ROOTS[2])] else "present_needs_verifier",
            "Required intake root is absent.",
        ),
        row(
            "R6 verifier-native owner/export rows and valid normal controls exist.",
            "060032",
            str(ARTIFACTS["r6_local_intake_search"]),
            "not_met" if r6_no_rows and not root_state[str(REQUIRED_ROOTS[0])] else "present_needs_verifier",
            "060032 found no local owner-export/control rows and did not mutate target root.",
        ),
        row(
            "Provider/AutoQuant evidence is real and current.",
            "055200/060056",
            f"{ARTIFACTS['autoquant_reuse']} | {ARTIFACTS['autoquant_cache_backtest']}",
            "partial_non_promoting" if autoquant_nonpromoting else "missing_or_unverified",
            "Local-cache backtests are runtime evidence only; canonical status/data and source/control gates remain blocked.",
        ),
        row(
            "Filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback reran after source/control unlock.",
            "054116",
            str(ARTIFACTS["readonly_runtime_chain"]),
            "not_met",
            "Read-only runtime chain is non-promoting and predates source/control unlock; no canonical merge/downstream rerun is allowed.",
        ),
        row(
            "No proxy signal is accepted as completion by itself.",
            "055829/055930",
            f"{ARTIFACTS['r3_r5_public_search']} | {ARTIFACTS['latest_completion_audit']}",
            "met_fail_closed" if public_search_nonpromoting else "uncertain",
            "Metadata searches, provider bars, and cache backtests remain non-promoting.",
        ),
    ]

    missing_requirements = [item for item in checklist if item["status"] in {"not_met", "missing_or_unverified", "uncertain"}]
    gate_result = "current_objective_audit_after_060032_060056_v1=not_complete_source_control_roots_absent_no_downstream_rerun"

    result: dict[str, Any] = {
        "run_id": RUN_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gate_result": gate_result,
        "board_hash_before_artifact": sha256_file(BOARD) if BOARD.exists() else None,
        "target_roots": root_state,
        "artifact_state": artifact_state,
        "checklist": checklist,
        "missing_requirement_count": len(missing_requirements),
        "missing_requirements": missing_requirements,
        "decision": {
            "objective_complete": False,
            "source_control_evidence_acquired": False,
            "required_roots_absent": roots_absent,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
    }

    json_path = ART_DIR / "current_objective_audit_after_060032_060056_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checklist_path = ART_DIR / "prompt_to_artifact_checklist_after_060032_060056_v1.csv"
    with checklist_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["requirement", "evidence_key", "evidence", "status", "gap"])
        writer.writeheader()
        writer.writerows(checklist)

    md_path = ART_DIR / "current_objective_audit_after_060032_060056_v1.md"
    md_path.write_text(
        "\n".join(
            [
                "# Current Objective Audit After 060032/060056 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{gate_result}`",
                "",
                "## Objective Restatement",
                "",
                "Every active regime must have >=95% calibrated confidence, survive validation on other markets/cycles/timeframes, and then pass the ordered provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree chain after real source/control unlock.",
                "",
                "## Decision",
                "",
                "The objective is not complete. Diagnostic HGB evidence exists, but source/control roots remain absent, cross-timeframe source-label validation is missing, canonical merge is not allowed, and downstream promotion has not rerun.",
                "",
                "## Required Roots",
                "",
                *[f"- `{path}`: `{exists}`" for path, exists in root_state.items()],
                "",
                "## Missing Requirements",
                "",
                *[f"- `{item['requirement']}`: {item['gap']}" for item in missing_requirements],
                "",
                "## Next",
                "",
                "Continue only after explicit source/control approval, verifier-native R6 owner/export rows with valid controls, source-owned R5 recency rows, or source-owned R3 native sub-hour labels unlock a required target root. Then rerun direct verifier, split calibration, canonical merge, providers, AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback in order.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = [
        f"gate_result={gate_result}",
        f"json_exists={json_path.exists()}",
        f"md_exists={md_path.exists()}",
        f"checklist_exists={checklist_path.exists()}",
        f"missing_requirement_count={len(missing_requirements)}",
        f"required_roots_absent={str(roots_absent).lower()}",
        "objective_complete=false",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    (CHECK_DIR / "current_objective_audit_after_060032_060056_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({"run_id": RUN_ID, "gate_result": gate_result, "missing_requirement_count": len(missing_requirements)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
