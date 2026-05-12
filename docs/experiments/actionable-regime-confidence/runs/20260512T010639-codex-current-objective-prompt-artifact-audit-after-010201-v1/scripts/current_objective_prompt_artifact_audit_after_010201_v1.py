#!/usr/bin/env python3
"""Audit the active Board A objective against concrete artifacts after 010201."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


RUN_ID = "20260512T010639-codex-current-objective-prompt-artifact-audit-after-010201-v1"
REPO = Path(".")
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "current-objective-prompt-artifact-audit-after-010201-v1"
CHECKS = RUN_ROOT / "checks"

ARTIFACTS = {
    "r6_owner_route_entitlement": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T010127-codex-r6-owner-route-entitlement-readback-v1/r6-owner-route-entitlement-readback/r6_owner_route_entitlement_readback_v1.json",
    "non_r6_outbound_requests": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T010201-codex-non-r6-source-intake-outbound-request-messages-v1/non-r6-source-intake-outbound-request-messages-v1/non_r6_source_intake_outbound_request_messages_v1.json",
    "r6_sendable_requests": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T005913-codex-r6-owner-export-sendable-requests-v3/r6-owner-export-sendable-requests-v3/r6_owner_export_sendable_requests_v3.json",
    "provider_autoquant_refresh": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T005248-codex-v71-provider-autoquant-readonly-refresh-v1/v71-provider-autoquant-readonly-refresh/v71_provider_autoquant_readonly_refresh_v1.json",
}

INTAKE_ROOTS = {
    "r6_owner_export": {
        "root": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        "required": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
    },
    "source_label_equivalence": {
        "root": Path("/tmp/ict-engine-source-label-equivalence-intake"),
        "required": [
            "source_label_equivalence_rows.csv",
            "source_label_equivalence_provenance.json",
        ],
    },
    "r3_native_subhour": {
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
    },
    "r5_source_panel_recency": {
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required": [
            "stock_market_regimes_2026_extension.csv",
            "stock_market_regimes_2026_extension_provenance.json",
        ],
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def current_cursor() -> dict[str, str]:
    text = BOARD.read_text()
    section = text.split("## Current Cursor", 1)[1].split("\n## ", 1)[0]
    rows: dict[str, str] = {}
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 3 or parts[0] in {"Field", "---"}:
            continue
        rows[parts[0]] = parts[1]
    return rows


def root_status() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for root_id, spec in INTAKE_ROOTS.items():
        root = spec["root"]
        required = spec["required"]
        existing = [name for name in required if (root / name).exists()]
        rows.append(
            {
                "root_id": root_id,
                "root": str(root),
                "root_exists": root.exists(),
                "required_files": ";".join(required),
                "present_required_files": ";".join(existing),
                "missing_required_files": ";".join(name for name in required if name not in existing),
                "file_count_maxdepth4": sum(1 for p in root.glob("**/*") if p.is_file()) if root.exists() else 0,
                "ready": root.exists() and len(existing) == len(required),
            }
        )
    return rows


def bool_text(value: object) -> str:
    return str(bool(value)).lower()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    cursor = current_cursor()
    artifacts = {name: load_json(path) for name, path in ARTIFACTS.items()}
    artifact_presence = [
        {"artifact_id": name, "path": str(path), "exists": path.exists(), "sha256": sha256(path) if path.exists() else ""}
        for name, path in ARTIFACTS.items()
    ]
    roots = root_status()
    all_required_roots_ready = all(row["ready"] for row in roots)

    r6 = artifacts["r6_owner_route_entitlement"]
    non_r6 = artifacts["non_r6_outbound_requests"]
    sendable = artifacts["r6_sendable_requests"]
    provider = artifacts["provider_autoquant_refresh"]

    board_state_blocked = cursor.get("board_state") == "blocked"
    r6_controls = r6.get("valid_source_owned_normal_controls_acquired", 0) or 0
    flip_approval = bool(r6.get("flip_as_control_approval"))
    non_r6_rows = non_r6.get("source_rows_acquired", 0) or 0
    provider_gate = provider.get("gate_result") or provider.get("status") or "present"

    checklist = [
        {
            "requirement": "Use the named Board A markdown as the authoritative task board.",
            "evidence": f"board_hash={sha256(BOARD)}; last_loop_id={cursor.get('last_loop_id')}",
            "status": "covered",
            "gap": "",
        },
        {
            "requirement": "Do not disrupt multi-agent work or overwrite another cursor.",
            "evidence": "This audit writes a new run root only and does not edit Current Cursor or canonical intake.",
            "status": "covered",
            "gap": "",
        },
        {
            "requirement": "Every active regime/root has calibrated confidence >=95%.",
            "evidence": f"cursor board_state={cursor.get('board_state')}; confidence_lane={cursor.get('confidence_lane')}; accepted_gate={cursor.get('accepted_gate')}",
            "status": "blocked",
            "gap": "Current cursor is blocked and full_objective_gate remains none; strict active-root completion is not achieved.",
        },
        {
            "requirement": "Validate accepted regimes across other markets, timeframes, and periods.",
            "evidence": f"source_rows_acquired={non_r6_rows}; intake_roots_ready={bool_text(all_required_roots_ready)}",
            "status": "blocked",
            "gap": "Source-label equivalence, R3 native sub-hour, and R5 recency roots do not contain required files.",
        },
        {
            "requirement": "R6 DirectOverlay::Manipulation has source-owned normal controls or explicit FLIP-control approval.",
            "evidence": f"required_cells={sendable.get('required_oystacher_control_cells')}; controls_acquired={r6_controls}; flip_approval={bool_text(flip_approval)}",
            "status": "blocked",
            "gap": "0 valid source-owned controls and no same-exhibit FLIP approval.",
        },
        {
            "requirement": "Use provider surfaces including IBKR, TradingViewRemix/MCP, yfinance, and Kraken.",
            "evidence": f"provider_artifact={ARTIFACTS['provider_autoquant_refresh']}; gate={provider_gate}",
            "status": "partial",
            "gap": "Provider/Auto-Quant refresh is read-only/non-promoting; promotion rerun is blocked until source controls arrive.",
        },
        {
            "requirement": "Run Auto-Quant and ict-engine filter/pre-Bayes/BBN/CatBoost/path-ranking/execution-tree in order.",
            "evidence": f"downstream_allowed_r6={bool_text(r6.get('downstream_chain_rerun_allowed'))}; downstream_allowed_non_r6={bool_text(non_r6.get('downstream_chain_rerun_allowed'))}",
            "status": "blocked",
            "gap": "Downstream promotion rerun is explicitly not allowed without source-owned inputs and canonical merge.",
        },
        {
            "requirement": "Do not accept proxy or OHLCV-only evidence for direct manipulation/source-label gates.",
            "evidence": f"cursor_blocker={cursor.get('blocker')}",
            "status": "covered",
            "gap": "",
        },
        {
            "requirement": "Do not call update_goal until strict completion is proven.",
            "evidence": f"strict_full_objective_achieved=false; r6_update_goal={r6.get('update_goal')}; non_r6_update_goal={non_r6.get('update_goal')}",
            "status": "covered",
            "gap": "",
        },
    ]

    unmet = [row for row in checklist if row["status"] in {"blocked", "partial"}]
    result = {
        "run_id": RUN_ID,
        "board": str(BOARD),
        "board_hash": sha256(BOARD),
        "cursor": cursor,
        "artifact_presence": artifact_presence,
        "intake_roots": roots,
        "checklist": checklist,
        "unmet_requirements": unmet,
        "gate_result": "current_objective_prompt_artifact_audit_after_010201_v1=blocked_source_inputs_absent_no_completion",
        "accepted_rows_added": 0,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
    }

    (OUT / "current_objective_prompt_artifact_audit_after_010201_v1.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    write_csv(
        OUT / "prompt_to_artifact_checklist_after_010201_v1.csv",
        checklist,
        ["requirement", "evidence", "status", "gap"],
    )
    write_csv(
        OUT / "unmet_requirements_after_010201_v1.csv",
        unmet,
        ["requirement", "evidence", "status", "gap"],
    )
    write_csv(
        OUT / "intake_root_presence_after_010201_v1.csv",
        roots,
        [
            "root_id",
            "root",
            "root_exists",
            "required_files",
            "present_required_files",
            "missing_required_files",
            "file_count_maxdepth4",
            "ready",
        ],
    )
    write_csv(OUT / "artifact_presence_after_010201_v1.csv", artifact_presence, ["artifact_id", "path", "exists", "sha256"])

    report = [
        "# Current Objective Prompt-to-Artifact Audit After 010201 v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Current cursor observed: `{cursor.get('last_loop_id')}`.",
        f"- Board state: `{cursor.get('board_state')}`.",
        f"- Gate result: `{result['gate_result']}`.",
        "- Strict full objective achieved: false. `update_goal=false`.",
        "- Canonical merge allowed: false. Downstream promotion rerun allowed: false.",
        "- Accepted rows added: `0`; source rows acquired: `0`; external requests sent: false.",
        "",
        "## Blocking Evidence",
        "",
        f"- R6 source-owned controls acquired: `{r6_controls}`; same-exhibit `FLIP` approval: `{bool_text(flip_approval)}`.",
        f"- Non-R6 source rows acquired: `{non_r6_rows}`.",
        f"- Intake roots ready: `{bool_text(all_required_roots_ready)}`.",
        f"- Provider/Auto-Quant evidence remains read-only/non-promoting: `{provider_gate}`.",
        "",
        "## Files",
        "",
        f"- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/current-objective-prompt-artifact-audit-after-010201-v1/current_objective_prompt_artifact_audit_after_010201_v1.json`",
        f"- Prompt-to-artifact checklist: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/current-objective-prompt-artifact-audit-after-010201-v1/prompt_to_artifact_checklist_after_010201_v1.csv`",
        f"- Unmet requirements: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/current-objective-prompt-artifact-audit-after-010201-v1/unmet_requirements_after_010201_v1.csv`",
        f"- Intake root presence: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/current-objective-prompt-artifact-audit-after-010201-v1/intake_root_presence_after_010201_v1.csv`",
        f"- Artifact presence: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/current-objective-prompt-artifact-audit-after-010201-v1/artifact_presence_after_010201_v1.csv`",
        f"- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/current_objective_prompt_artifact_audit_after_010201_v1_assertions.out`",
    ]
    (OUT / "current_objective_prompt_artifact_audit_after_010201_v1.md").write_text("\n".join(report) + "\n")

    assertions = [
        f"run_id={RUN_ID}",
        f"gate_result={result['gate_result']}",
        f"board_state={cursor.get('board_state')}",
        f"current_cursor={cursor.get('last_loop_id')}",
        f"r6_controls_acquired={r6_controls}",
        f"flip_approval={bool_text(flip_approval)}",
        f"source_rows_acquired={non_r6_rows}",
        f"all_required_roots_ready={bool_text(all_required_roots_ready)}",
        "accepted_rows_added=0",
        "canonical_merge_allowed=false",
        "downstream_chain_rerun_allowed=false",
        "new_confidence_gate=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        "runtime_code_changed=false",
        "shared_intake_mutated=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "external_requests_sent=false",
    ]
    (CHECKS / "current_objective_prompt_artifact_audit_after_010201_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )


if __name__ == "__main__":
    main()
