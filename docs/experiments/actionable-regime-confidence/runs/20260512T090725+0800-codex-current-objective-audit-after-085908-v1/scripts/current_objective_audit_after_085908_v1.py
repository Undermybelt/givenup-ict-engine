#!/usr/bin/env python3
"""Current-objective audit after 085908.

This is a completion-audit slice only. It maps the active objective to current
terminal evidence and keeps the goal fail-closed.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = RUN_ROOT / "current-objective-audit-after-085908-v1"
CHECKS_DIR = RUN_ROOT / "checks"

BOARD_A = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
BOARD_B = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"
OBJECTIVE_FILE = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"

RUN_ID = "20260512T090725+0800-codex-current-objective-audit-after-085908-v1"
GATE = "current_objective_audit_after_085908_v1=not_complete_source_control_absent_no_selected_history_no_downstream_promotion"

EVIDENCE_FILES = {
    "085808": REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T085808+0800-codex-public-case-attachment-route-refresh-after-085131-v1/checks/public_case_attachment_route_refresh_after_085131_v1_assertions.out",
    "085908": REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T085908+0800-codex-r3-r5-required-root-local-sweep-after-085612-v1/checks/r3_r5_required_root_local_sweep_after_085612_v1_assertions.out",
    "085912": REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T085912+0800-codex-current-objective-audit-after-085727-v1/checks/current_objective_audit_after_085727_v1_assertions.out",
    "085950": REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T085950+0800-codex-current-objective-audit-after-085612-v1/checks/current_objective_audit_after_085612_v1_assertions.out",
    "085954": REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T085954+0800-codex-source-control-arrival-poll-after-085612-v1/checks/source_control_arrival_poll_after_085612_v1_assertions.out",
    "090006": REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T090006+0800-codex-current-objective-audit-after-085612-v1/checks/current_objective_audit_after_085612_v1_assertions.out",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_assertions(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(timezone(timedelta(hours=8))).isoformat()
    latest_assertions = {name: read_assertions(path) for name, path in EVIDENCE_FILES.items()}

    checklist = [
        {
            "requirement": "Regime-rooted factor branch path is defined and preserved in authoritative docs",
            "evidence": str(OBJECTIVE_FILE),
            "status": "partial",
            "why": "Objective text and board notes preserve the requirement, but no executed branch evidence is present.",
        },
        {
            "requirement": "Use IBKR / TradingViewRemix / yfinance / Kraken in the loop",
            "evidence": "085950, 090006 assertions",
            "status": "not_complete",
            "why": "Provider surfaces are only diagnostic; no downstream promotion or accepted rows were acquired.",
        },
        {
            "requirement": "Actually run Auto-Quant -> filter / Pre-Bayes -> BBN -> CatBoost -> execution tree",
            "evidence": "085950, 090006 assertions",
            "status": "not_complete",
            "why": "Both audits keep the ordered rerun false and promotion false.",
        },
        {
            "requirement": "Select exactly one historical path (HTF / MTF / LTF) before promotion",
            "evidence": "085912, 085950, 090006 assertions",
            "status": "not_complete",
            "why": "Explicit selected history remains false in the terminal audits.",
        },
        {
            "requirement": "Obtain real source/control unlock rows and matched controls",
            "evidence": "085808, 085908, 085954 assertions",
            "status": "not_complete",
            "why": "Public narrative/context routes and local sweeps remain fail-closed with source/control false.",
        },
        {
            "requirement": "Keep multi-agent edits append-only and do not disturb others",
            "evidence": str(BOARD_A),
            "status": "partial",
            "why": "The ledgers remain append-only, but concurrent writers added overlapping EOF sections.",
        },
        {
            "requirement": "Mark the objective complete only when all gates are satisfied",
            "evidence": "085908, 085912, 085950, 085954, 090006 assertions",
            "status": "not_complete",
            "why": "Every current terminal assertion still reports promotion_allowed=false and update_goal=false.",
        },
    ]

    summary = {
        "run_id": RUN_ID,
        "gate_result": GATE,
        "generated_at": generated_at,
        "board_a_sha256_before_artifact": sha256_file(BOARD_A),
        "board_b_sha256_before_artifact": sha256_file(BOARD_B),
        "objective_file": str(OBJECTIVE_FILE),
        "latest_assertions": latest_assertions,
        "status": "not_complete",
        "accepted_rows_added": 0,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "explicit_user_selected_history": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
    }

    with (ARTIFACT_DIR / "current_objective_audit_after_085908_v1.json").open("w", encoding="utf-8") as handle:
        json.dump({"summary": summary, "checklist": checklist}, handle, indent=2, sort_keys=True)

    with (ARTIFACT_DIR / "prompt_to_artifact_checklist_after_085908_v1.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=["requirement", "evidence", "status", "why"])
        writer.writeheader()
        writer.writerows(checklist)

    with (ARTIFACT_DIR / "counted_assertion_readback_after_085908_v1.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=["root", "path", "gate_result", "source_control_evidence_acquired", "valid_required_root_unlock", "explicit_user_selected_history", "canonical_merge", "selected_data_autoquant_promotion", "downstream_promotion_rerun", "promotion_allowed", "update_goal"])
        writer.writeheader()
        for root, path in EVIDENCE_FILES.items():
            assertions = latest_assertions[root]
            writer.writerow(
                {
                    "root": root,
                    "path": str(path),
                    "gate_result": assertions.get("gate_result", assertions.get("current_objective_audit_after_085612_v1", assertions.get("current_objective_audit_after_085727_v1", assertions.get("source_control_arrival_poll_after_085612_v1", "")))),
                    "source_control_evidence_acquired": assertions.get("source_control_evidence_acquired", "false"),
                    "valid_required_root_unlock": assertions.get("valid_required_root_unlock", "false"),
                    "explicit_user_selected_history": assertions.get("explicit_user_selected_history", "false"),
                    "canonical_merge": assertions.get("canonical_merge", "false"),
                    "selected_data_autoquant_promotion": assertions.get("selected_data_autoquant_promotion", "false"),
                    "downstream_promotion_rerun": assertions.get("downstream_promotion_rerun", "false"),
                    "promotion_allowed": assertions.get("promotion_allowed", "false"),
                    "update_goal": assertions.get("update_goal", "false"),
                }
            )

    report = f"""# Current Objective Audit After 085908 v1

Run id: `{RUN_ID}`

Gate result: `{GATE}`

## Objective

The active objective requires regime-rooted factor branching, real provider-backed Auto-Quant/ict-engine execution through filter / Pre-Bayes / BBN / CatBoost / execution tree, per-regime validation across instruments/timeframes/markets, explicit selected-history selection, and source/control unlock evidence.

## Checklist

See `prompt_to_artifact_checklist_after_085908_v1.csv` for the mapped requirements. The current evidence remains fail-closed across the blockers that matter:

- selected history remains false
- source/control evidence remains false
- canonical merge remains false
- downstream promotion rerun remains false
- promotion allowed remains false

## Evidence

- `085808`: public case-route refresh only, row-level positives false, matched controls false
- `085908`: R3 native-subhour roots present, R5 recency rows zero, Crisis label false
- `085912`: branch contract present, cursor fail-closed, no objective completion
- `085950`: partial audit only, no selection or promotion
- `085954`: no new required root, no unlock
- `090006`: latest audit remains not complete

## Decision

The objective is not achieved. The current state is still fail-closed on source/control unlock, selected-history selection, and downstream promotion. `update_goal=false`.
"""
    (ARTIFACT_DIR / "current_objective_audit_after_085908_v1.md").write_text(report, encoding="utf-8")

    assertions = [
        f"gate_result={GATE}",
        "objective_status=not_complete",
        "selected_history=false",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "promotion_allowed=false",
        "update_goal=false",
    ]
    (CHECKS_DIR / "current_objective_audit_after_085908_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
