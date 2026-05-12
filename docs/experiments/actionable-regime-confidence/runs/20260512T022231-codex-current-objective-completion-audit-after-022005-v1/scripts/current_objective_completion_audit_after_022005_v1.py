#!/usr/bin/env python3
"""Completion audit after the TSIE full-parquet dry run.

This is an evidence-mapping artifact only. It must not promote source labels,
move the board cursor, or mark the objective complete.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


RUN_ID = "20260512T022231-codex-current-objective-completion-audit-after-022005-v1"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T022231-codex-current-objective-completion-audit-after-022005-v1"
)
ARTIFACT_DIR = RUN_ROOT / "current-objective-completion-audit-after-022005-v1"
CHECK_DIR = RUN_ROOT / "checks"

LATEST_AUDIT_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T021256-codex-current-objective-completion-audit-after-020037-v1/"
    "current-objective-completion-audit-after-020037-v1/"
    "current_objective_completion_audit_after_020037_v1.json"
)
PROVIDER_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T021456-codex-required-provider-status-readback-v1/"
    "required-provider-status-readback-v1/"
    "required_provider_status_readback_v1.json"
)
TSIE_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T022005-codex-tsie-source-label-intake-dryrun-v1/"
    "tsie-source-label-intake-dryrun-v1/"
    "tsie_source_label_intake_dryrun_v1.json"
)
AUTOQUANT_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T021808-codex-autoquant-bootstrap-prepare-readiness-v1/"
    "autoquant-bootstrap-prepare-readiness-v1/"
    "autoquant_bootstrap_prepare_readiness_v1.json"
)

ROOTS = {
    "r6_owner_export": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r3_native_subhour": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "r5_recency_extension": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "source_label_equivalence": Path("/tmp/ict-engine-source-label-equivalence-intake"),
    "legacy_direct_intake": Path("/tmp/ict-engine-direct-manipulation-row-intake"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def root_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "present": False, "kind": "absent", "file_count": 0}
    if path.is_file():
        return {"path": str(path), "present": True, "kind": "file", "file_count": 1}
    files = [item for item in path.rglob("*") if item.is_file()]
    return {"path": str(path), "present": True, "kind": "dir", "file_count": len(files)}


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    latest_audit = load_json(LATEST_AUDIT_JSON)
    provider = load_json(PROVIDER_JSON)
    tsie = load_json(TSIE_JSON)
    autoquant = load_json(AUTOQUANT_JSON)
    roots = {name: root_status(path) for name, path in ROOTS.items()}
    board_hash = sha256(BOARD)

    provider_decisions = provider.get("decisions", {})
    provider_runtime = provider.get("runtime_chain_readback", {})
    tsie_counts = tsie.get("mapped_counts", {})

    checklist = [
        {
            "requirement": "Use the named Board A markdown and preserve multi-agent coordination",
            "status": "pass",
            "evidence": f"{BOARD}; sha256_at_generation={board_hash}",
            "gap": "none",
        },
        {
            "requirement": "Every MainRegimeV2 regime reaches accepted calibrated confidence >=95%",
            "status": "blocked",
            "evidence": (
                "021256 audit and 022005 TSIE dry run both report accepted_rows_added=0, "
                "new_confidence_gate=false, strict_full_objective_achieved=false"
            ),
            "gap": "No accepted Bull/Bear/Sideways/Crisis packet at >=95%; TSIE is candidate-only.",
        },
        {
            "requirement": "Each accepted regime has its own qualifying condition",
            "status": "blocked",
            "evidence": "022005 maps Bear/Bull/Sideways support but does not create accepted rows; Crisis absent",
            "gap": "No accepted per-regime qualifying_condition packet exists.",
        },
        {
            "requirement": "Validate accepted confidence across other markets",
            "status": "blocked",
            "evidence": (
                "022005 provides IDX support only and explicitly requires cross-market transfer; "
                "R6 owner-export controls remain absent"
            ),
            "gap": "No accepted cross-market transfer/calibration artifact.",
        },
        {
            "requirement": "Validate accepted confidence across other cycles/timeframes",
            "status": "blocked",
            "evidence": (
                f"r3={roots['r3_native_subhour']}; "
                f"r5={roots['r5_recency_extension']}; TSIE hours are hourly/session only"
            ),
            "gap": "Native sub-hour and recency-extension roots remain absent; no accepted cross-timeframe packet.",
        },
        {
            "requirement": "Record IBKR/TradingViewRemix/yfinance/Kraken provider context",
            "status": "partial",
            "evidence": (
                "021456 maps providers: yfinance ready, TradingViewRemix/MCP not ready, "
                "IBKR not ready as market-data provider, Kraken partial"
            ),
            "gap": "Provider context is read-only/non-promoting and does not supply source/control roots.",
        },
        {
            "requirement": "Operate Auto-Quant on real artifacts",
            "status": "partial",
            "evidence": (
                "021808 Auto-Quant readiness: "
                f"bootstrap_exit={autoquant.get('bootstrap_exit')}, "
                f"prepare_exit={autoquant.get('prepare_exit')}, "
                f"after_prepare_status={autoquant.get('after_prepare_status')}, "
                f"data_ready={autoquant.get('final_data_ready')}"
            ),
            "gap": "Dependency readiness improved, but prepare failed and data_ready=false; no promotion evidence.",
        },
        {
            "requirement": "Operate filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution tree",
            "status": "partial",
            "evidence": (
                "021456 runtime chain: "
                f"pre_bayes_confidence={provider_runtime.get('pre_bayes_structural_confidence')}, "
                f"policy_matched_rows={provider_runtime.get('policy_training_matched_rows')}, "
                f"execution_actionable={provider_runtime.get('execution_candidate_actionable')}, "
                f"export_mature_rows={provider_runtime.get('export_mature_rows')}"
            ),
            "gap": "Surfaces are callable/read-only only; no accepted downstream promotion rerun is allowed.",
        },
        {
            "requirement": "R6 has source-owned normal controls or explicit FLIP approval",
            "status": "blocked",
            "evidence": f"r6={roots['r6_owner_export']}; legacy_direct={roots['legacy_direct_intake']}",
            "gap": "Owner-export root absent; legacy direct rows are explicitly non-promoting; FLIP approval false.",
        },
        {
            "requirement": "Canonical merge and downstream promotion rerun are allowed",
            "status": "blocked",
            "evidence": (
                f"latest_audit canonical={latest_audit.get('canonical_merge_allowed')}; "
                f"tsie canonical={tsie.get('canonical_merge_allowed')}; "
                f"provider canonical={provider_decisions.get('canonical_merge_allowed')}"
            ),
            "gap": "Canonical merge and downstream rerun remain false across current evidence.",
        },
        {
            "requirement": "Goal can be marked complete",
            "status": "blocked",
            "evidence": "strict_full_objective_achieved=false and update_goal=false in current evidence",
            "gap": "Objective is not achieved.",
        },
    ]

    counts = {"pass": 0, "partial": 0, "blocked": 0}
    for item in checklist:
        counts[item["status"]] += 1

    gate_result = (
        "current_objective_completion_audit_after_022005_v1="
        "not_complete_r6_source_controls_autoquant_data_cross_validation_and_downstream_blocked"
    )
    result = {
        "run_id": RUN_ID,
        "gate_result": gate_result,
        "board_sha256_at_generation": board_hash,
        "objective_restatement": [
            "Every MainRegimeV2 regime must have accepted calibrated confidence >=95%.",
            "Each accepted regime needs its own qualifying condition.",
            "Confidence must validate across other markets and cycles/timeframes.",
            "Provider context must include IBKR, TradingViewRemix, yfinance, and Kraken where available.",
            "Auto-Quant -> filter/Pre-Bayes/BBN -> CatBoost/path-ranking -> execution-tree must be operated on real artifacts.",
            "No proxy signal can substitute for source/control roots, canonical merge, and downstream promotion evidence.",
        ],
        "prompt_to_artifact_checklist": checklist,
        "checklist_counts": counts,
        "root_status": roots,
        "evidence_refs": {
            "latest_completion_audit": str(LATEST_AUDIT_JSON),
            "provider_readback": str(PROVIDER_JSON),
            "tsie_full_parquet_dryrun": str(TSIE_JSON),
            "autoquant_bootstrap_prepare_readiness": str(AUTOQUANT_JSON),
        },
        "tsie_mapped_counts": tsie_counts,
        "autoquant_readiness": {
            "gate_result": autoquant.get("gate_result"),
            "bootstrap_exit": autoquant.get("bootstrap_exit"),
            "prepare_exit": autoquant.get("prepare_exit"),
            "after_prepare_status": autoquant.get("after_prepare_status"),
            "final_dependency_healthy": autoquant.get("final_dependency_healthy"),
            "final_data_ready": autoquant.get("final_data_ready"),
            "final_healthy": autoquant.get("final_healthy"),
        },
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r3_r5_r6_roots_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    json_path = ARTIFACT_DIR / "current_objective_completion_audit_after_022005_v1.json"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    write_csv(
        ARTIFACT_DIR / "current_objective_prompt_to_artifact_checklist_after_022005_v1.csv",
        checklist,
        ["requirement", "status", "evidence", "gap"],
    )
    write_csv(
        ARTIFACT_DIR / "current_objective_root_status_after_022005_v1.csv",
        [{"root": key, **value} for key, value in roots.items()],
        ["root", "path", "present", "kind", "file_count"],
    )
    evidence_rows = []
    for name, path in result["evidence_refs"].items():
        p = Path(path)
        evidence_rows.append({"evidence": name, "path": path, "present": p.exists(), "kind": "file" if p.is_file() else "missing"})
    write_csv(
        ARTIFACT_DIR / "current_objective_evidence_presence_after_022005_v1.csv",
        evidence_rows,
        ["evidence", "path", "present", "kind"],
    )

    md = f"""# Current Objective Completion Audit After 022005 v1

Run id: `{RUN_ID}`
Gate result: `{gate_result}`
Board sha256 at generation: `{board_hash}`

Objective restatement:
- Every `MainRegimeV2` regime must have accepted calibrated confidence `>=95%`.
- Each accepted regime needs its own qualifying condition.
- Confidence must validate across other markets and cycles/timeframes.
- Provider context must cover IBKR, TradingViewRemix, yfinance, and Kraken where available.
- Auto-Quant -> filter/Pre-Bayes/BBN -> CatBoost/path-ranking -> execution-tree must be operated on real artifacts.
- Proxy signals, callability, sample mappings, and public sidecar labels are not completion evidence by themselves.

Prompt-to-artifact checklist:
- Counts: pass `{counts['pass']}`, partial `{counts['partial']}`, blocked `{counts['blocked']}`.
- Checklist CSV: `current_objective_prompt_to_artifact_checklist_after_022005_v1.csv`.

Current evidence:
- Latest completion audit: `{LATEST_AUDIT_JSON}`.
- Required-provider readback: `{PROVIDER_JSON}`.
- TSIE full-parquet dry run: `{TSIE_JSON}`.
- Auto-Quant bootstrap/prepare readiness: `{AUTOQUANT_JSON}`.

TSIE readback:
- Gate result: `{tsie.get('gate_result')}`.
- Mapped counts: Bear `{tsie_counts.get('Bear')}`, Bull `{tsie_counts.get('Bull')}`, Sideways `{tsie_counts.get('Sideways')}`, ABSTAIN_TRAP `{tsie_counts.get('ABSTAIN_TRAP')}`.
- Decision: candidate support is large but not accepted; no Crisis class, no canonical intake mutation, no downstream rerun.

Provider/runtime readback:
- Provider gate result: `{provider.get('gate_result')}`.
- Prior Auto-Quant status in provider readback: `{provider_runtime.get('auto_quant_status')}`; healthy `{provider_runtime.get('auto_quant_healthy')}`.
- Pre-Bayes structural confidence: `{provider_runtime.get('pre_bayes_structural_confidence')}`.
- Policy/CatBoost matched rows: `{provider_runtime.get('policy_training_matched_rows')}`.
- Execution candidate actionable: `{provider_runtime.get('execution_candidate_actionable')}`.
- Export mature rows: `{provider_runtime.get('export_mature_rows')}`.

Auto-Quant readiness after 021808:
- Gate result: `{autoquant.get('gate_result')}`.
- Bootstrap exit: `{autoquant.get('bootstrap_exit')}`.
- Prepare exit: `{autoquant.get('prepare_exit')}`.
- After prepare status: `{autoquant.get('after_prepare_status')}`.
- Dependency healthy: `{autoquant.get('final_dependency_healthy')}`.
- Data ready: `{autoquant.get('final_data_ready')}`.
- Final healthy: `{autoquant.get('final_healthy')}`.

Root status:
- R6 owner-export: `{roots['r6_owner_export']}`.
- R3 native sub-hour: `{roots['r3_native_subhour']}`.
- R5 recency extension: `{roots['r5_recency_extension']}`.
- Source-label equivalence: `{roots['source_label_equivalence']}`.
- Legacy direct intake: `{roots['legacy_direct_intake']}`.

Decision:
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Canonical merge allowed: `false`.
- Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree rerun allowed: `false`.
- Strict full objective achieved: `false`.
- `update_goal=false`.

No mutation claims:
- Runtime code changed: `false`.
- Shared intake mutated: `false`.
- R3/R5/R6 roots mutated: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.

Next:
- Preserve the Current Cursor next action for R6. Continue only from owner/operator R6 export delivery, explicit `FLIP` approval, or genuinely source-owned cross-timeframe `MainRegimeV2` exports before canonical merge and downstream rerun.
"""
    (ARTIFACT_DIR / "current_objective_completion_audit_after_022005_v1.md").write_text(md, encoding="utf-8")

    assertions = [
        f"gate_result={gate_result}",
        f"checklist_pass={counts['pass']}",
        f"checklist_partial={counts['partial']}",
        f"checklist_blocked={counts['blocked']}",
        f"r6_owner_export_present={roots['r6_owner_export']['present']}",
        f"r3_native_subhour_present={roots['r3_native_subhour']['present']}",
        f"r5_recency_extension_present={roots['r5_recency_extension']['present']}",
        "accepted_rows_added=0",
        "new_confidence_gate=false",
        "canonical_merge_allowed=false",
        "downstream_chain_rerun_allowed=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
    ]
    (CHECK_DIR / "current_objective_completion_audit_after_022005_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "run_id": RUN_ID,
        "gate_result": gate_result,
        "checklist_counts": counts,
        "accepted_rows_added": 0,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
    }, indent=2))


if __name__ == "__main__":
    main()
