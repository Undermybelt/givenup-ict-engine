#!/usr/bin/env python3
"""Restore/generate the 021256 Board A completion-audit artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


RUN_ID = "20260512T021256-codex-current-objective-completion-audit-after-020037-v1"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT = ROOT / "current-objective-completion-audit-after-020037-v1"
CHECKS = ROOT / "checks"

EVIDENCE = {
    "020037_runtime_chain": Path("docs/experiments/actionable-regime-confidence/runs/20260512T020037-codex-readonly-runtime-chain-refresh-after-015533-v1/checks/readonly_runtime_chain_refresh_after_015533_v1_assertions.out"),
    "020037_runtime_json": Path("docs/experiments/actionable-regime-confidence/runs/20260512T020037-codex-readonly-runtime-chain-refresh-after-015533-v1/readonly-runtime-chain-refresh-after-015533-v1/readonly_runtime_chain_refresh_after_015533_v1.json"),
    "020104_public_source_screen": Path("docs/experiments/actionable-regime-confidence/runs/20260512T020104-codex-public-source-label-expansion-screen-v1/checks/public_source_label_expansion_screen_v1_assertions.out"),
    "020216_tsie_dry_run": Path("docs/experiments/actionable-regime-confidence/runs/20260512T020216-codex-tsie-public-source-intake-dry-run-v1/checks/tsie_public_source_intake_dry_run_v1_assertions.out"),
    "020235_new_source_search": Path("docs/experiments/actionable-regime-confidence/runs/20260512T020235-codex-new-source-label-web-search-v1/checks/new_source_label_web_search_v1_assertions.out"),
    "020708_coordination": Path("docs/experiments/actionable-regime-confidence/runs/20260512T020708-codex-current-coordination-readback-after-020235-v1/checks/current_coordination_readback_after_020235_v1_assertions.out"),
    "020729_source_poll": Path("docs/experiments/actionable-regime-confidence/runs/20260512T020729-codex-current-source-control-arrival-poll-after-020235-v1/checks/current_source_control_arrival_poll_after_020235_v1_assertions.out"),
    "approval_decision_package": Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid"),
}

ROOTS = {
    "r6_owner_export": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r3_native_subhour": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "r5_recency_extension": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "source_label_equivalence": Path("/tmp/ict-engine-source-label-equivalence-intake"),
    "legacy_direct_intake": Path("/tmp/ict-engine-direct-manipulation-row-intake"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def count_files(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return 1
    return sum(1 for child in path.rglob("*") if child.is_file())


def root_status(path: Path) -> dict[str, object]:
    return {
        "path": str(path),
        "present": path.exists(),
        "kind": "file" if path.is_file() else "dir" if path.is_dir() else "absent",
        "file_count": count_files(path),
    }


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    roots = {name: root_status(path) for name, path in ROOTS.items()}
    evidence = {name: path.exists() and path.stat().st_size > 0 for name, path in EVIDENCE.items()}
    runtime = load_json(EVIDENCE["020037_runtime_json"])
    approval = load_json(EVIDENCE["approval_decision_package"]).get("assertions", {})
    board_hash = sha256(BOARD)

    checklist = [
        {
            "requirement": "Use the named Board A markdown and preserve multi-agent coordination",
            "status": "pass",
            "evidence": f"{BOARD}; sha256={board_hash}",
            "gap": "none",
        },
        {
            "requirement": "Every MainRegimeV2 regime reaches accepted calibrated confidence >=95%",
            "status": "blocked",
            "evidence": "Latest registered packets still add accepted_rows_added=0 and no new confidence gate",
            "gap": "No strict Bull/Bear/Sideways/Crisis accepted packet is present.",
        },
        {
            "requirement": "Each accepted regime has its own qualifying condition",
            "status": "blocked",
            "evidence": "020216 sample mapping and 020104/020235 source screens remain non-promoting",
            "gap": "No accepted per-regime qualifying_condition rows.",
        },
        {
            "requirement": "Validate across other markets",
            "status": "blocked",
            "evidence": "R6 owner-export root absent; source-owned normal controls absent",
            "gap": "No source-owned cross-market accepted packet.",
        },
        {
            "requirement": "Validate across other cycles/timeframes",
            "status": "blocked",
            "evidence": f"R3={roots['r3_native_subhour']}; R5={roots['r5_recency_extension']}",
            "gap": "Native sub-hour and recency-extension roots remain absent.",
        },
        {
            "requirement": "Record IBKR/TradingViewRemix/yfinance/Kraken provider context",
            "status": "partial",
            "evidence": "020037/021008 runtime readbacks record callable but partial provider status",
            "gap": "Provider status is not promotion evidence without source/control roots.",
        },
        {
            "requirement": "Operate Auto-Quant on real artifacts",
            "status": "partial",
            "evidence": f"020037 auto_quant_status={runtime.get('auto_quant_status')}",
            "gap": "Auto-Quant remains non-promoting in this state.",
        },
        {
            "requirement": "Operate filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution tree",
            "status": "partial",
            "evidence": "020037 runtime chain callable; policy matched rows 0; path mature rows 0; execution observe-only",
            "gap": "Callable/read-only surfaces are not accepted downstream promotion.",
        },
        {
            "requirement": "R6 has source-owned normal controls or explicit FLIP approval",
            "status": "blocked",
            "evidence": f"approval_present={approval.get('approval_present')}; flip_controls={approval.get('flip_controls_accepted_under_current_contract')}",
            "gap": "Owner-export root absent and FLIP controls are not approved.",
        },
        {
            "requirement": "Canonical merge and downstream promotion rerun are allowed",
            "status": "blocked",
            "evidence": f"canonical={approval.get('canonical_merge_allowed_now')}; downstream={approval.get('downstream_rerun_allowed_now')}",
            "gap": "Canonical merge and downstream rerun remain false.",
        },
        {
            "requirement": "Goal can be marked complete",
            "status": "blocked",
            "evidence": "strict_full_objective_achieved=false; update_goal=false",
            "gap": "Objective is not achieved.",
        },
    ]

    payload = {
        "run_id": RUN_ID,
        "gate_result": "current_objective_completion_audit_after_020037_v1=not_complete_r6_regime_cross_validation_downstream_blocked",
        "board_sha256_at_generation": board_hash,
        "objective_restatement": [
            "Every MainRegimeV2 regime needs accepted calibrated confidence >=95%.",
            "Each accepted regime needs its own qualifying condition.",
            "Confidence must validate across other markets and cycles/timeframes.",
            "Provider context must cover IBKR, TradingViewRemix, yfinance, and Kraken where available.",
            "Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree evidence must be real and non-proxy.",
        ],
        "prompt_to_artifact_checklist": checklist,
        "checklist_counts": {
            "pass": sum(row["status"] == "pass" for row in checklist),
            "partial": sum(row["status"] == "partial" for row in checklist),
            "blocked": sum(row["status"] == "blocked" for row in checklist),
        },
        "evidence_presence": evidence,
        "root_status": roots,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_promotion_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r3_r5_r6_roots_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    write_csv(OUT / "current_objective_prompt_to_artifact_checklist_after_020037_v1.csv", checklist, ["requirement", "status", "evidence", "gap"])
    write_csv(OUT / "current_objective_evidence_presence_after_020037_v1.csv", [{"artifact": k, "path": str(EVIDENCE[k]), "present": v} for k, v in evidence.items()], ["artifact", "path", "present"])
    write_csv(OUT / "current_objective_root_status_after_020037_v1.csv", [{"root": k, **v} for k, v in roots.items()], ["root", "path", "present", "kind", "file_count"])
    (OUT / "current_objective_completion_audit_after_020037_v1.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    checklist_text = "\n".join(f"- `{row['status']}`: {row['requirement']}. Evidence: {row['evidence']}. Gap: {row['gap']}" for row in checklist)
    (OUT / "current_objective_completion_audit_after_020037_v1.md").write_text(
        f"""# Current Objective Completion Audit After 020037 v1

Run id: `{RUN_ID}`
Gate result: `{payload['gate_result']}`

Objective restatement:
- Every `MainRegimeV2` regime needs accepted calibrated confidence >=95%.
- Each accepted regime needs its own qualifying condition.
- Confidence must validate across other markets and cycles/timeframes.
- Provider context must cover IBKR, TradingViewRemix, yfinance, and Kraken where available.
- Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree evidence must be real and non-proxy.

Prompt-to-artifact checklist:
{checklist_text}

Current root state:
- R6 owner-export: `{roots['r6_owner_export']}`.
- R3 native sub-hour: `{roots['r3_native_subhour']}`.
- R5 recency extension: `{roots['r5_recency_extension']}`.
- Source-label equivalence: `{roots['source_label_equivalence']}`.
- Legacy direct intake: `{roots['legacy_direct_intake']}`; not the active owner-export root.

Decision:
- Objective achieved: `false`.
- `update_goal=false`.

Next:
- Continue only from owner/operator R6 export delivery, explicit `FLIP` approval, or genuinely new source-owned cross-timeframe `MainRegimeV2` exports before canonical merge and downstream rerun.
"""
    )

    assertions = {
        "board_present": BOARD.exists(),
        "evidence_present": all(evidence.values()),
        "r6_owner_export_absent": roots["r6_owner_export"]["present"] is False,
        "r3_native_subhour_absent": roots["r3_native_subhour"]["present"] is False,
        "r5_recency_extension_absent": roots["r5_recency_extension"]["present"] is False,
        "source_label_equivalence_present": roots["source_label_equivalence"]["present"] is True,
        "legacy_direct_intake_present": roots["legacy_direct_intake"]["present"] is True,
        "approval_present_false": approval.get("approval_present") is False,
        "flip_controls_false": approval.get("flip_controls_accepted_under_current_contract") is False,
        "accepted_rows_zero": payload["accepted_rows_added"] == 0,
        "canonical_merge_false": payload["canonical_merge_allowed"] is False,
        "downstream_rerun_false": payload["downstream_promotion_rerun_allowed"] is False,
        "strict_objective_false": payload["strict_full_objective_achieved"] is False,
        "update_goal_false": payload["update_goal"] is False,
    }
    (CHECKS / "current_objective_completion_audit_after_020037_v1_assertions.out").write_text(
        "\n".join(f"{k}={'PASS' if v else 'FAIL'}" for k, v in assertions.items()) + "\n"
    )
    if not all(assertions.values()):
        raise SystemExit("021256 restoration assertions failed")


if __name__ == "__main__":
    main()
