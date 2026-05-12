#!/usr/bin/env python3
"""Post-083618 Board A completion audit.

This is an evidence readback only. It does not mutate source/control roots or
run downstream promotion.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T084654+0800-codex-current-objective-audit-after-083618-v1"
SLUG = "current-objective-audit-after-083618-v1"
GATE = (
    "current_objective_audit_after_083618_v1="
    "not_complete_source_control_selected_history_downstream_blocked"
)

SCRIPT = Path(__file__).resolve()
RUN_ROOT = SCRIPT.parents[1]
REPO = SCRIPT.parents[6]
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"


ASSERTION_FILES = {
    "082430_runtime_readiness": REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T082430+0800-codex-runtime-readiness-after-082215-v1/checks/"
    / "runtime_readiness_after_082215_v1_assertions.out",
    "083108_source_control_arrival": REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T083108+0800-codex-source-control-arrival-poll-after-082720-v1/checks/"
    / "source_control_arrival_poll_after_082720_v1_assertions.out",
    "083450_tomac_schema_classifier": REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T083450+0800-codex-tomac-local-schema-classifier-after-083108-v1/checks/"
    / "tomac_local_schema_classifier_after_083108_v1_assertions.out",
    "083618_tomac_futures_headers": REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T083618+0800-codex-tomac-futures-header-inventory-after-083108-v1/checks/"
    / "tomac_futures_header_inventory_after_083108_v1_assertions.out",
}

APPROVAL_PACKAGE = Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid")
TARGET_ROOTS = {
    "r6_owner_export_tmp": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r6_owner_export_private_tmp": Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r5_recency_tmp": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "r5_recency_private_tmp": Path("/private/tmp/ict-engine-source-panel-recency-extension"),
    "r3_native_subhour_tmp": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "r3_native_subhour_private_tmp": Path("/private/tmp/ict-engine-native-subhour-source-label-intake"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_assertions(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return {"missing": "true"}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def bool_text(value: Any) -> str:
    return str(bool(value)).lower()


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    board_hash = sha256(BOARD)
    assertions = {name: parse_assertions(path) for name, path in ASSERTION_FILES.items()}
    approval = read_json(APPROVAL_PACKAGE)
    approval_assertions = approval.get("assertions") if isinstance(approval.get("assertions"), dict) else {}

    target_roots = [
        {
            "root": name,
            "path": str(path),
            "exists": path.exists(),
            "sampled_files": sum(1 for _ in path.rglob("*")) if path.exists() and path.is_dir() else 0,
        }
        for name, path in TARGET_ROOTS.items()
    ]

    r6_roots_present = any(row["exists"] for row in target_roots if row["root"].startswith("r6_"))
    r5_roots_present = any(row["exists"] for row in target_roots if row["root"].startswith("r5_"))
    r3_roots_present = any(row["exists"] for row in target_roots if row["root"].startswith("r3_"))
    approval_present = bool(approval_assertions.get("approval_present"))
    flip_approved = bool(approval_assertions.get("flip_controls_accepted_under_current_contract"))

    checklist = [
        {
            "requirement": "authoritative_board_a_file",
            "status": "covered",
            "evidence": f"{BOARD.relative_to(REPO)} hash {board_hash}",
            "gap": "",
        },
        {
            "requirement": "every_regime_95_confidence",
            "status": "blocked",
            "evidence": "Latest counted assertions keep accepted_rows_added=0 and strict_full_objective=false.",
            "gap": "No accepted 95% packet for every regime/root under the current source/control contract.",
        },
        {
            "requirement": "cross_market_cross_cycle_validation",
            "status": "blocked",
            "evidence": "083108/083450/083618 are arrival or local-schema inventory only; they do not add cross-market accepted packets.",
            "gap": "Validation across other markets and cycles cannot promote until source/control roots unlock.",
        },
        {
            "requirement": "r6_r5_r3_source_control_unlock",
            "status": "blocked",
            "evidence": (
                f"r6_roots_present={bool_text(r6_roots_present)}; "
                f"r5_roots_present={bool_text(r5_roots_present)}; "
                f"r3_roots_present={bool_text(r3_roots_present)} but non-promoting; "
                f"approval_present={bool_text(approval_present)}; flip_approved={bool_text(flip_approved)}"
            ),
            "gap": "No owner/export root, R5 recency root, accepted R3 native-subhour root, or explicit FLIP approval.",
        },
        {
            "requirement": "provider_surfaces_ibkr_tradingviewremix_yfinance_kraken",
            "status": "partial_non_promoting",
            "evidence": "082430 runtime readiness records provider/runtime surfaces and required provider names.",
            "gap": "Provider visibility is not source/control evidence and cannot promote regimes.",
        },
        {
            "requirement": "autoquant_filter_prebayes_bbn_catboost_execution_tree_chain",
            "status": "blocked",
            "evidence": "082430 observed readiness/status surfaces; latest gates keep selected_data_autoquant_promotion=false and downstream_promotion_rerun=false.",
            "gap": "Do not rerun promotion chain until source/control and selected-history gates unlock.",
        },
        {
            "requirement": "selected_history_gate",
            "status": "blocked",
            "evidence": "Latest current-objective audit after 083108 reports explicit selected history false.",
            "gap": "No explicit user-selected HTF/MTF/LTF path after source/control unlock.",
        },
        {
            "requirement": "local_tomac_archive_not_proxy_unlock",
            "status": "covered_fail_closed",
            "evidence": "083450 found no verifier-native package; 083618 found OHLCV/symbology headers only.",
            "gap": "Local Tomac files remain market context, not source/control rows.",
        },
        {
            "requirement": "multi_agent_append_only_coordination",
            "status": "covered",
            "evidence": "This artifact records board hash before writeback and only creates a new run root.",
            "gap": "",
        },
        {
            "requirement": "completion_or_update_goal",
            "status": "blocked",
            "evidence": "strict_full_objective=false; trade_usable=false; promotion_allowed=false; update_goal=false.",
            "gap": "Objective is not complete.",
        },
    ]

    status_counts: dict[str, int] = {}
    for row in checklist:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1

    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": GATE,
        "board_hash_before_writeback": board_hash,
        "objective": (
            "Every regime must reach 95% confidence, validate across other markets and cycles, "
            "and only then run the AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree chain "
            "with provider coverage while preserving multi-agent board safety."
        ),
        "checklist": checklist,
        "status_counts": status_counts,
        "assertions_readback": assertions,
        "approval_package": {
            "path": str(APPROVAL_PACKAGE),
            "exists": APPROVAL_PACKAGE.exists(),
            "approval_present": approval_present,
            "flip_controls_accepted": flip_approved,
            "gate_result": approval.get("gate_result"),
        },
        "target_roots": target_roots,
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
        "next": (
            "Continue source/control acquisition only, or wait for explicit user selection of exactly one "
            "historical path for non-promotional factor research. Do not run selected-data AutoQuant or "
            "downstream promotion until both source/control and selected-history gates are satisfied."
        ),
    }

    (OUT / "current_objective_audit_after_083618_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_csv(
        OUT / "prompt_to_artifact_checklist_after_083618_v1.csv",
        checklist,
        ["requirement", "status", "evidence", "gap"],
    )
    write_csv(
        OUT / "target_roots_after_083618_v1.csv",
        target_roots,
        ["root", "path", "exists", "sampled_files"],
    )

    lines = [
        "# Current Objective Audit After 083618 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE}`",
        "",
        f"Board A sha256 before artifact: `{board_hash}`",
        "",
        "## Objective Restatement",
        "",
        payload["objective"],
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence | Gap |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        lines.append(
            f"| `{row['requirement']}` | `{row['status']}` | {row['evidence']} | {row['gap']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Covered requirements: `{status_counts.get('covered', 0)}`.",
            f"- Covered fail-closed requirements: `{status_counts.get('covered_fail_closed', 0)}`.",
            f"- Partial/non-promoting requirements: `{status_counts.get('partial_non_promoting', 0)}`.",
            f"- Blocked requirements: `{status_counts.get('blocked', 0)}`.",
            "- Accepted rows added: `0`.",
            "- Valid required-root unlock: `false`.",
            "- Source/control evidence acquired: `false`.",
            "- Explicit user-selected history: `false`.",
            "- Canonical merge: `false`.",
            "- Selected-data AutoQuant promotion: `false`.",
            "- Downstream promotion rerun: `false`.",
            "- Strict full objective: `false`.",
            "- Trade usable: `false`.",
            "- Promotion allowed: `false`.",
            "- `update_goal=false`.",
            "",
            "## Next",
            "",
            payload["next"],
        ]
    )
    (OUT / "current_objective_audit_after_083618_v1.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    assertions_out = [
        f"gate_result={GATE}",
        f"covered_requirements={status_counts.get('covered', 0)}",
        f"covered_fail_closed_requirements={status_counts.get('covered_fail_closed', 0)}",
        f"partial_requirements={status_counts.get('partial_non_promoting', 0)}",
        f"blocked_requirements={status_counts.get('blocked', 0)}",
        "accepted_rows_added=0",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "explicit_user_selected_history=false",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "promotion_allowed=false",
        "update_goal=false",
    ]
    (CHECKS / "current_objective_audit_after_083618_v1_assertions.out").write_text(
        "\n".join(assertions_out) + "\n", encoding="utf-8"
    )
    print(json.dumps({"gate_result": GATE, "blocked": status_counts.get("blocked", 0)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
