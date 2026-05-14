#!/usr/bin/env python3
"""Build a current prompt-to-artifact audit for Board A after 055516."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


RUN_ID = "20260512T055811-codex-current-objective-audit-after-055516-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
ART_DIR = RUN_ROOT / "current-objective-audit-after-055516-v1"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
APPROVAL = Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid")

REQUIRED_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]

EVIDENCE = {
    "hgb_field_materialization": Path(
        "docs/experiments/actionable-regime-confidence/runs/20260512T053852-codex-hgb-per-regime-field-materialization-v1/hgb-per-regime-field-materialization-v1/hgb_per_regime_field_materialization_v1.json"
    ),
    "hgb_field_assertions": Path(
        "docs/experiments/actionable-regime-confidence/runs/20260512T053852-codex-hgb-per-regime-field-materialization-v1/checks/hgb_per_regime_field_materialization_v1_assertions.out"
    ),
    "readonly_runtime_chain": Path(
        "docs/experiments/actionable-regime-confidence/runs/20260512T054116-codex-readonly-runtime-chain-after-053933-v1/readonly-runtime-chain-after-053933-v1/readonly_runtime_chain_after_053933_v1.json"
    ),
    "provider_autoquant_correction": Path(
        "docs/experiments/actionable-regime-confidence/runs/20260512T055129-codex-054718-provider-autoquant-rerun-correction-v1/054718-provider-autoquant-rerun-correction-v1/054718_provider_autoquant_rerun_correction_v1.json"
    ),
    "autoquant_local_reuse": Path(
        "docs/experiments/actionable-regime-confidence/runs/20260512T055200-codex-autoquant-local-reuse-readiness-after-054116-v1/autoquant-local-reuse-readiness-after-054116-v1/autoquant_local_reuse_readiness_after_054116_v1.json"
    ),
    "r3_r5_current_source_search": Path(
        "docs/experiments/actionable-regime-confidence/runs/20260512T055116-codex-r3-r5-current-source-label-search-v1/r3-r5-current-source-label-search-v1/r3_r5_current_source_label_search_v1.json"
    ),
    "r3_r5_crypto_microstructure_screen": Path(
        "docs/experiments/actionable-regime-confidence/runs/20260512T055103-codex-r3-r5-crypto-microstructure-source-screen-v1/r3-r5-crypto-microstructure-source-screen-v1/r3_r5_crypto_microstructure_source_screen_v1.json"
    ),
    "missing_055212_correction": Path(
        "docs/experiments/actionable-regime-confidence/runs/20260512T055509-codex-055212-missing-artifact-correction-v1/055212-missing-artifact-correction-v1/055212_missing_artifact_correction_v1.json"
    ),
    "r6_dispatch_feasibility": Path(
        "docs/experiments/actionable-regime-confidence/runs/20260512T055516-codex-r6-owner-export-dispatch-feasibility-readback-v1/r6-owner-export-dispatch-feasibility-readback-v1/r6_owner_export_dispatch_feasibility_readback_v1.json"
    ),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def evidence_status() -> dict[str, Any]:
    rows = {}
    for name, path in EVIDENCE.items():
        rows[name] = {
            "path": str(path),
            "exists": path.exists(),
            "sha256": sha256_file(path) if path.exists() else None,
        }
    return rows


def checklist_rows(root_status: dict[str, bool], approval: dict[str, Any] | None, evidence: dict[str, Any]) -> list[dict[str, str]]:
    approval_present = bool(approval and approval.get("approval_present") is True)
    canonical_allowed = bool(approval and approval.get("canonical_merge_allowed_now") is True)
    downstream_allowed = bool(approval and approval.get("downstream_rerun_allowed_now") is True)
    all_roots_present = all(root_status.values())
    hgb_present = evidence["hgb_field_materialization"]["exists"] and evidence["hgb_field_assertions"]["exists"]
    runtime_present = evidence["readonly_runtime_chain"]["exists"] and evidence["provider_autoquant_correction"]["exists"]
    source_search_present = (
        evidence["r3_r5_current_source_search"]["exists"]
        and evidence["r3_r5_crypto_microstructure_screen"]["exists"]
        and evidence["r6_dispatch_feasibility"]["exists"]
    )
    return [
        {
            "requirement": "Every active regime reaches calibrated 95% confidence",
            "status": "diagnostic_only_not_promoting",
            "evidence": "053852 HGB field materialization present" if hgb_present else "missing 053852 HGB field materialization",
            "gap": "source/control roots and canonical merge absent",
        },
        {
            "requirement": "Validated across other markets, cycles, and timeframes",
            "status": "partial_diagnostic_only",
            "evidence": "053852 reports instruments/periods/contexts; R3 native sub-hour root absent",
            "gap": "native sub-hour/source-owned cross-timeframe validation root absent",
        },
        {
            "requirement": "Use IBKR, TradingViewRemix, yfinance, Kraken, and Auto-Quant/ict-engine runtime surfaces",
            "status": "diagnostic_runtime_readback_only",
            "evidence": "054116 and 055129 provider/runtime readbacks present" if runtime_present else "runtime readbacks missing",
            "gap": "provider bars and runtime readiness are not source labels or promotion evidence",
        },
        {
            "requirement": "Acquire source/control evidence or valid source-owned R3/R5 rows",
            "status": "blocked",
            "evidence": "required roots: " + ", ".join(f"{k}={v}" for k, v in root_status.items()),
            "gap": "all required roots are absent" if not all_roots_present else "",
        },
        {
            "requirement": "R6 owner/export dispatch or approval path",
            "status": "blocked",
            "evidence": "055516 dispatch feasibility present; approval_present=" + str(approval_present),
            "gap": "drafts not sent; no ticket/export/license ids; no approval",
        },
        {
            "requirement": "R3/R5 source-search does not rely on proxy mappings",
            "status": "screened_no_unlock",
            "evidence": "055116/055103/055509 present" if source_search_present else "one or more source-search artifacts missing",
            "gap": "no exact native sub-hour labels or post-cutoff MainRegimeV2 rows acquired",
        },
        {
            "requirement": "Canonical merge and downstream promotion rerun",
            "status": "not_allowed",
            "evidence": f"canonical_allowed={canonical_allowed}; downstream_allowed={downstream_allowed}",
            "gap": "source/control gate remains closed",
        },
        {
            "requirement": "Trade usability and update_goal",
            "status": "false",
            "evidence": "trade usable false; update_goal=false",
            "gap": "objective not achieved",
        },
    ]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["requirement", "status", "evidence", "gap"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ART_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    board_hash = sha256_file(BOARD) if BOARD.exists() else None
    approval = load_json(APPROVAL)
    root_status = {str(root): root.exists() for root in REQUIRED_ROOTS}
    evidence = evidence_status()
    rows = checklist_rows(root_status, approval, evidence)

    result = {
        "run_id": RUN_ID,
        "gate_result": "current_objective_audit_after_055516_v1=not_complete_source_control_roots_absent_no_downstream_rerun",
        "board_hash_before_artifact": board_hash,
        "objective_restated": {
            "regimes_95_confidence": "all active regimes require calibrated 95% confidence",
            "cross_market_cycle_timeframe": "validated on other markets/cycles/timeframes with source-owned provenance",
            "runtime_chain": "provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree readback after source/control unlock",
            "multi_agent_safety": "append-only board updates; no partial active-writer outputs; no target-root mutation without approval",
        },
        "evidence": evidence,
        "approval": approval,
        "required_root_status": root_status,
        "checklist": rows,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
        "decision": "Board A remains incomplete: diagnostic 95% HGB evidence exists, but source/control roots, approval, canonical merge, downstream promotion rerun, and trade usability are absent.",
        "next": "Continue only after explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned R5 recency rows, or source-owned R3 native sub-hour labels unlock a required target root.",
    }

    json_path = ART_DIR / "current_objective_audit_after_055516_v1.json"
    md_path = ART_DIR / "current_objective_audit_after_055516_v1.md"
    csv_path = ART_DIR / "prompt_to_artifact_checklist_after_055516_v1.csv"
    assertions_path = CHECK_DIR / "current_objective_audit_after_055516_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(csv_path, rows)

    lines = [
        "# Current Objective Audit After 055516 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{result['gate_result']}`",
        "",
        f"Board hash before artifact: `{board_hash}`",
        "",
        "## Objective Restatement",
        "",
        "- Bring every active regime to calibrated 95% confidence.",
        "- Validate the accepted regimes across other markets, cycles, and timeframes.",
        "- Run real provider / Auto-Quant / filter / Pre-Bayes / BBN / CatBoost / path-ranking / execution-tree evidence, but only promote after source/control unlock and canonical merge.",
        "- Preserve multi-agent board safety: append-only, no partial active-writer outputs, and no target-root mutation without approval.",
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence | Gap |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['requirement']} | `{row['status']}` | {row['evidence']} | {row['gap']} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            result["decision"],
            "",
            "Required roots:",
        ]
    )
    for root, exists in root_status.items():
        lines.append(f"- `{root}`: `{exists}`")
    lines.extend(
        [
            "",
            "Promotion status remains unchanged: source/control evidence acquired `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.",
            "",
            "## Next",
            "",
            result["next"],
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")

    assertions = [
        "current_objective_audit_after_055516_v1=not_complete_source_control_roots_absent_no_downstream_rerun",
        "diagnostic_hgb_field_evidence_present=true" if evidence["hgb_field_materialization"]["exists"] else "diagnostic_hgb_field_evidence_present=false",
        "required_roots_absent=true" if not any(root_status.values()) else "required_roots_absent=false",
        "approval_present=false" if not (approval and approval.get("approval_present") is True) else "approval_present=true",
        "canonical_merge=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
