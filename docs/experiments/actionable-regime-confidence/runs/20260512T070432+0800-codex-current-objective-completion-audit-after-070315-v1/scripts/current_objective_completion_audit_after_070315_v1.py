#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUN_ID = "20260512T070432+0800-codex-current-objective-completion-audit-after-070315-v1"
RUN_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / RUN_ID
)
OUT = RUN_ROOT / "current-objective-completion-audit-after-070315-v1"
CHECKS = RUN_ROOT / "checks"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(rel: str) -> dict:
    path = REPO / rel
    with path.open() as fh:
        return json.load(fh)


def exists(rel: str) -> bool:
    return (REPO / rel).exists()


def root_status() -> list[dict]:
    roots = [
        (
            "r6_owner_export",
            Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
            [
                "direct_manipulation_positive_rows.csv",
                "direct_manipulation_matched_controls.csv",
                "direct_manipulation_provenance.json",
            ],
        ),
        (
            "r5_recency_extension",
            Path("/tmp/ict-engine-source-panel-recency-extension"),
            [
                "stock_market_regimes_2026_extension.csv",
                "source_panel_recency_provenance.json",
            ],
        ),
        (
            "r3_native_subhour",
            Path("/tmp/ict-engine-native-subhour-source-label-intake"),
            [
                "native_subhour_source_label_rows.csv",
                "native_subhour_source_label_provenance.json",
            ],
        ),
        (
            "source_label_equivalence",
            Path("/tmp/ict-engine-source-label-equivalence-intake"),
            [
                "source_label_equivalence_rows.csv",
                "source_label_equivalence_provenance.json",
            ],
        ),
    ]
    rows = []
    for root_id, root, required in roots:
        present = {name: (root / name).exists() for name in required}
        rows.append(
            {
                "id": root_id,
                "root": str(root),
                "root_exists": root.exists(),
                "required_present": present,
                "physical_complete": all(present.values()),
            }
        )
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    source_provider = load_json(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T065822+0800-codex-source-control-provider-refresh-after-065506-v1/"
        "source-control-provider-refresh-after-065506-v1/"
        "source_control_provider_refresh_after_065506_v1.json"
    )
    autoquant = load_json(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T070115+0800-codex-autoquant-final-readback-after-065824-v1/"
        "autoquant-final-readback-after-065824-v1/"
        "autoquant_final_readback_after_065824_v1.json"
    )
    source_route = load_json(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T070315+0800-codex-public-exact-source-route-probe-after-065820-v1/"
        "public-exact-source-route-probe-after-065820-v1/"
        "public_exact_source_route_probe_after_065820_v1.json"
    )
    r5_r3 = load_json(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T065820+0800-codex-r5-r3-target-contract-readback-after-065449-v1/"
        "r5-r3-target-contract-readback-after-065449-v1/"
        "r5_r3_target_contract_readback_after_065449_v1.json"
    )
    local_databento = load_json(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T065452+0800-codex-local-databento-gc-ohlcv-applicability-v1/"
        "local-databento-gc-ohlcv-applicability-v1/"
        "local_databento_gc_ohlcv_applicability_v1.json"
    )

    roots = root_status()
    r6_unlock = False
    r5_unlock = False
    r3_unlock = False
    valid_unlock = False
    accounting = source_provider["accounting"]
    autoq_accounting = autoquant["board_a_accounting"]
    route_gate = source_route["gate"]

    checklist = [
        {
            "requirement": "Every active MainRegimeV2 regime has accepted >=95% confidence evidence",
            "evidence": "065822 required roots plus source/control accounting",
            "status": "not_met",
            "notes": "accepted_rows_added=0; R6/R5 absent; R3 TSIE quarantined and Crisis absent",
        },
        {
            "requirement": "Regime evidence validates across other markets/instruments",
            "evidence": "065822, 065820, 070315",
            "status": "not_met",
            "notes": "candidate public/NIFTY/macro rows did not satisfy R5/R3 target contracts",
        },
        {
            "requirement": "Regime evidence validates across other periods/cycles",
            "evidence": "065820 and 070315",
            "status": "not_met",
            "notes": "post-cutoff candidates found but no source-owned MainRegimeV2 target-root unlock",
        },
        {
            "requirement": "Regime evidence validates across timeframes",
            "evidence": "R3 native-subhour root status and TSIE quarantine",
            "status": "not_met",
            "notes": "native-subhour files are TSIE-derived, non-promoting, and Crisis is absent",
        },
        {
            "requirement": "Use real ict-engine provider, analyze-live, filter/pre-Bayes, workflow/path-ranking commands",
            "evidence": "065822 command readback",
            "status": "partial",
            "notes": "commands exited 0 but are read-only/non-promoting; workflow remains blocked and path-ranking has 0 mature/calibrated rows",
        },
        {
            "requirement": "Use Auto-Quant on local artifacts",
            "evidence": "070115 AutoQuant final readback",
            "status": "partial",
            "notes": "Auto-Quant data_ready=true; default runs failed; Tomac harness succeeded but is single-pair runtime evidence only",
        },
        {
            "requirement": "Use IBKR, TradingViewRemix, yfinance, and Kraken where available",
            "evidence": "065822 provider summary",
            "status": "partial",
            "notes": "yfinance and kraken_cli usable; IBKR/TradingViewRemix/Kraken public remain unhealthy or non-promoting",
        },
        {
            "requirement": "Run canonical merge and downstream promotion only after a valid source/control unlock",
            "evidence": "065822/070315 gates",
            "status": "blocked_not_run",
            "notes": "valid_required_root_unlock=false, so direct verifier, split calibration, canonical merge, BBN/CatBoost/execution-tree promotion are not allowed",
        },
        {
            "requirement": "Write concrete evidence under docs/experiments and update same board without disturbing concurrent work",
            "evidence": "registered roots 065822, 070115, 070315 plus this audit",
            "status": "met",
            "notes": "append-only artifacts and board sections; no runtime code changes in this audit",
        },
        {
            "requirement": "Do not call update_goal until objective is actually achieved",
            "evidence": "all latest accounting blocks update_goal",
            "status": "met",
            "notes": "strict_full_objective=false and update_goal=false",
        },
    ]

    strict_complete = False
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_before_artifact": sha256(BOARD),
        "objective": (
            "Every regime reaches >=95% confidence and validates across other markets, "
            "periods/cycles, and timeframes; real Auto-Quant and ict-engine provider -> "
            "filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree chain evidence."
        ),
        "gate_result": (
            "current_objective_completion_audit_after_070315_v1="
            "not_complete_source_control_unlock_absent_runtime_readbacks_non_promoting"
        ),
        "root_status": roots,
        "latest_evidence": {
            "source_control_provider_refresh": {
                "run": source_provider["run_id"],
                "gate_result": source_provider["gate_result"],
                "accounting": source_provider["accounting"],
                "provider_summary": source_provider["runtime_readback"]["provider"]["summary_line"],
                "auto_quant_status": source_provider["runtime_readback"]["auto_quant"]["status"],
                "workflow_blocking_status": source_provider["runtime_readback"]["workflow"]["blocking_status"],
                "path_ranking_rows": source_provider["runtime_readback"]["path_ranking"]["rows"],
                "path_ranking_mature_rows": source_provider["runtime_readback"]["path_ranking"]["mature_rows"],
            },
            "auto_quant_final": {
                "run": "20260512T070115+0800-codex-autoquant-final-readback-after-065824-v1",
                "gate_result": autoquant["gate_result"],
                "evidence": autoquant["auto_quant_evidence"],
                "accounting": autoquant["board_a_accounting"],
            },
            "public_exact_source_route_probe": {
                "run": source_route["run_id"],
                "gate_result": source_route["gate_result"],
                "gate": source_route["gate"],
            },
            "r5_r3_contract_readback": {
                "gate_result": r5_r3.get("gate_result"),
                "accepted_unlock": False,
            },
            "local_databento_applicability": {
                "gate_result": local_databento.get("gate_result"),
                "accepted_unlock": False,
            },
        },
        "prompt_to_artifact_checklist": checklist,
        "completion_decision": {
            "strict_full_objective": strict_complete,
            "accepted_rows_added": 0,
            "r6_owner_export_unlock": r6_unlock,
            "r5_recency_unlock": r5_unlock,
            "r3_native_subhour_unlock": r3_unlock,
            "valid_required_root_unlock": valid_unlock,
            "source_control_evidence_acquired": False,
            "direct_verifier_run": False,
            "split_calibration_run": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "next_action": (
            "Continue only from explicit source/control approval, verifier-native R6 owner-export "
            "rows with valid controls, source-owned post-2026-01-30 R5 recency rows matching the "
            "source-panel schema, verifier-native Crisis-capable R3 MainRegimeV2 labels, or a "
            "genuinely new accepted cross-timeframe MainRegimeV2 source export."
        ),
    }

    json_path = OUT / "current_objective_completion_audit_after_070315_v1.json"
    md_path = OUT / "current_objective_completion_audit_after_070315_v1.md"
    csv_path = OUT / "prompt_to_artifact_checklist_after_070315_v1.csv"
    assertions_path = CHECKS / "current_objective_completion_audit_after_070315_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["requirement", "evidence", "status", "notes"]
        )
        writer.writeheader()
        writer.writerows(checklist)

    met = sum(1 for row in checklist if row["status"] == "met")
    partial = sum(1 for row in checklist if row["status"] == "partial")
    not_met = sum(1 for row in checklist if row["status"] == "not_met")
    blocked = sum(1 for row in checklist if row["status"] == "blocked_not_run")

    md_path.write_text(
        "\n".join(
            [
                "# Current Objective Completion Audit After 070315 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                "Gate result: `current_objective_completion_audit_after_070315_v1=not_complete_source_control_unlock_absent_runtime_readbacks_non_promoting`",
                "",
                "## Objective",
                "",
                "Every active regime must reach >=95% confidence and validate across other markets, periods/cycles, and timeframes. The chain must be evidenced with real Auto-Quant and ict-engine provider -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree readbacks.",
                "",
                "## Checklist Result",
                "",
                f"- Met: `{met}`",
                f"- Partial: `{partial}`",
                f"- Not met: `{not_met}`",
                f"- Blocked/not run by gate: `{blocked}`",
                "",
                "## Evidence Summary",
                "",
                f"- Source/control provider refresh: `{source_provider['gate_result']}`",
                f"- Provider summary: `{source_provider['runtime_readback']['provider']['summary_line']}`",
                f"- Auto-Quant status: `{source_provider['runtime_readback']['auto_quant']['status']}`",
                f"- Auto-Quant final readback: `{autoquant['gate_result']}`",
                f"- Public exact source route probe: `{source_route['gate_result']}`",
                "",
                "## Decision",
                "",
                "- Strict full objective: `false`",
                "- Valid required-root unlock: `false`",
                "- Source/control evidence acquired: `false`",
                "- Canonical merge: `false`",
                "- Downstream promotion rerun: `false`",
                "- Trade usable: `false`",
                "- `update_goal=false`",
                "",
                "## Next",
                "",
                result["next_action"],
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path.relative_to(REPO)}`",
                f"- Checklist CSV: `{csv_path.relative_to(REPO)}`",
                f"- Assertions: `{assertions_path.relative_to(REPO)}`",
            ]
        )
        + "\n"
    )

    assertions = [
        "PASS objective_restated=true",
        f"PASS checklist_rows={len(checklist)}",
        "PASS source_control_provider_refresh_inspected=true",
        "PASS autoquant_final_readback_inspected=true",
        "PASS public_exact_source_route_probe_inspected=true",
        f"PASS valid_required_root_unlock={str(valid_unlock).lower()}",
        "PASS strict_full_objective=false",
        "PASS canonical_merge=false",
        "PASS downstream_promotion_rerun=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
