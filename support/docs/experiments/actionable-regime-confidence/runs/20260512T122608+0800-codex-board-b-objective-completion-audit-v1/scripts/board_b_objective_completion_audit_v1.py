#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


RUN_ID = "20260512T122608+0800-codex-board-b-objective-completion-audit-v1"
ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
REPORT_DIR = ROOT / "board-b-objective-completion-audit-v1"
CHECK_DIR = ROOT / "checks"

BOARD = Path("docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md")
ENRICHED_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/"
    "115700-enriched-downstream-chain-v1/115700_enriched_downstream_chain_v1.json"
)
BLOCKER_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T122232+0800-codex-115700-execution-blocker-readback-v1/"
    "115700-execution-blocker-readback-v1/115700_execution_blocker_readback_v1.json"
)
BBN_NEGATIVE_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1/"
    "120630-bbn-negative-feedback-packet-v1/120630_bbn_negative_feedback_packet_v1.json"
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def command_status(exits: dict[str, int], labels: list[str]) -> str:
    if all(exits.get(label) == 0 for label in labels):
        return "covered"
    if any(label in exits for label in labels):
        return "partial"
    return "missing"


def add_row(rows: list[dict[str, str]], requirement: str, status: str, evidence: str, gap: str) -> None:
    rows.append(
        {
            "requirement": requirement,
            "status": status,
            "evidence": evidence,
            "gap": gap,
        }
    )


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n", encoding="utf-8")

    board_text = BOARD.read_text(encoding="utf-8")
    enriched = read_json(ENRICHED_JSON)
    blocker = read_json(BLOCKER_JSON)
    bbn_negative = read_json(BBN_NEGATIVE_JSON)

    chain_exits = enriched.get("chain_exits", {})
    augmented_exits = enriched.get("augmented_catboost", {}).get("exits", {})
    validation = enriched.get("layer_contract_validation", {})
    provider_counts = validation.get("provider_counts", {})
    branch_counts = validation.get("branch_counts", {})
    ranker = enriched.get("augmented_ranker_target", {})
    execution = enriched.get("augmented_execution_candidate", {})
    blocking_truth = blocker.get("blocking_truth", {})

    required_providers = {
        "yfinance": "YF",
        "kraken_public": "Kraken",
        "tvr_default_binance": "TradingViewRemix/TVR",
        "ibkr_paxos_long_midpoint": "IBKR",
    }
    provider_missing = [label for key, label in required_providers.items() if provider_counts.get(key, 0) <= 0]
    branch_contract_ok = (
        validation.get("layer_contract_valid_rows") == validation.get("checked_rows")
        and validation.get("checked_rows", 0) > 0
        and all(" -> " in key for key in branch_counts)
    )
    ordered_core = [
        "20_auto_quant_results_import",
        "21_auto_quant_prior_init",
        "22_ingest_real_trades",
        "23_analyze_provider_data",
        "24_pre_bayes_status",
        "26_export_structural_path_ranking_target",
        "30_register_trainer_artifact",
        "31_enable_runtime",
        "33_workflow_execution_candidate",
        "34_workflow_full",
    ]
    augmented_core = [
        "40_train_catboost_augmented",
        "41_apply_catboost_augmented_history",
        "42_apply_external_scores_augmented",
        "43_register_trainer_artifact_augmented",
        "44_enable_runtime_augmented",
        "46_workflow_execution_candidate_augmented",
        "47_workflow_full_augmented",
    ]

    rows: list[dict[str, str]] = []
    add_row(
        rows,
        "Use the authoritative Board B markdown and preserve multi-agent append-only behavior",
        "covered" if "122232 115700 Execution Blocker Readback v1" in board_text else "partial",
        str(BOARD),
        "No blocker; current audit is append-only and should not rewrite cursor sections.",
    )
    add_row(
        rows,
        "Regime-profit branch path is rooted as main -> sub -> sub_sub_or_profit_factor -> profit_factor",
        "covered" if branch_contract_ok else "missing",
        f"branch_counts={branch_counts}",
        "" if branch_contract_ok else "Layer contract rows or branch delimiters missing.",
    )
    add_row(
        rows,
        "Required provider evidence includes IBKR, TradingViewRemix/TVR, YF, and Kraken",
        "covered" if not provider_missing else "missing",
        f"provider_counts={provider_counts}",
        "" if not provider_missing else f"missing={provider_missing}",
    )
    add_row(
        rows,
        "Operate real chain Auto-Quant -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree",
        "covered" if command_status(chain_exits, ordered_core) == "covered" else "partial",
        f"chain_exits={chain_exits}; bbn_packet_present={bool(bbn_negative)}",
        "Standard CatBoost path failed closed; augmented CatBoost path succeeded.",
    )
    add_row(
        rows,
        "CatBoost/path-ranker is trained/applied/registered and consumed by runtime",
        "covered" if command_status(augmented_exits, augmented_core) == "covered" and ranker.get("runtime_selection_ready") else "missing",
        f"augmented_exits={augmented_exits}; runtime={ranker.get('runtime_selection_status')}; raw={ranker.get('raw_scored_mature_rows')}/{ranker.get('raw_scored_mature_min_rows')}",
        "" if ranker.get("runtime_selection_ready") else "Runtime selection not ready.",
    )
    add_row(
        rows,
        "Execution tree emits non-observe ready/actionable candidate",
        "missing" if not execution.get("ready") or not execution.get("actionable") else "covered",
        f"ready={execution.get('ready')} actionable={execution.get('actionable')} review={execution.get('review_status')} gate={execution.get('execution_gate_status')}",
        "Execution remains observe/blocked, so no promotion or trade claim is allowed.",
    )
    add_row(
        rows,
        "Selected-history/source-control unlock is satisfied before further factor-research reuse",
        "missing" if blocking_truth.get("reason") == "user_selected_historical_data_missing" else "covered",
        f"blocking_truth={blocking_truth}",
        "Workflow explicitly requires ask-user selection of 1h/4h/1d historical data.",
    )
    add_row(
        rows,
        "No live trade or goal completion claim before gates pass",
        "covered" if not enriched.get("promotion_allowed") and not enriched.get("trade_usable") else "missing",
        f"promotion_allowed={enriched.get('promotion_allowed')} trade_usable={enriched.get('trade_usable')} update_goal={enriched.get('update_goal')}",
        "Goal remains active because execution and source-control gates are incomplete.",
    )

    missing = [row for row in rows if row["status"] == "missing"]
    partial = [row for row in rows if row["status"] == "partial"]
    completion_achieved = not missing and not partial
    audit = {
        "run_id": RUN_ID,
        "objective_file": str(BOARD),
        "evidence_roots": {
            "enriched_downstream": "20260512T121347+0800-codex-115700-enriched-downstream-chain-v1",
            "bbn_negative_feedback": "20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1",
            "execution_blocker": "20260512T122232+0800-codex-115700-execution-blocker-readback-v1",
        },
        "completion_achieved": completion_achieved,
        "should_call_update_goal": completion_achieved,
        "missing_requirements": missing,
        "partial_requirements": partial,
        "checklist": rows,
        "next": "User must select or explicitly approve BTC_USD-1h.json, BTC_USD-4h.json, or BTC_USD-1d.json from the 121347 run root before source-control/factor-research unlock.",
    }

    json_path = REPORT_DIR / "board_b_objective_completion_audit_v1.json"
    md_path = REPORT_DIR / "board_b_objective_completion_audit_v1.md"
    csv_path = REPORT_DIR / "prompt_to_artifact_checklist_board_b_objective_completion_audit_v1.csv"
    assertions_path = CHECK_DIR / "board_b_objective_completion_audit_v1_assertions.out"

    write_json(json_path, audit)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["requirement", "status", "evidence", "gap"])
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Board B Objective Completion Audit v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Verdict",
        f"- Completion achieved: `{str(completion_achieved).lower()}`.",
        f"- `update_goal` should be called: `{str(completion_achieved).lower()}`.",
        "",
        "## Missing Or Partial",
    ]
    for row in missing + partial:
        lines.append(f"- `{row['status']}`: {row['requirement']} | gap: {row['gap']}")
    lines.extend(["", "## Checklist"])
    for row in rows:
        lines.append(f"- `{row['status']}`: {row['requirement']} | evidence: `{row['evidence']}`")
    lines.extend(
        [
            "",
            "## Next",
            audit["next"],
            "",
            "## Artifacts",
            f"- JSON: `{json_path}`",
            f"- CSV checklist: `{csv_path}`",
            f"- Assertions: `{assertions_path}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS checklist_rows={len(rows)}",
        ("FAIL_CLOSED" if not completion_achieved else "PASS") + f" completion_achieved={str(completion_achieved).lower()}",
        ("FAIL_CLOSED" if missing else "PASS") + f" missing_requirements={len(missing)}",
        ("FAIL_CLOSED" if partial else "PASS") + f" partial_requirements={len(partial)}",
        "PASS update_goal_not_called=true",
    ]
    for row in rows:
        prefix = "PASS" if row["status"] == "covered" else "FAIL_CLOSED"
        assertions.append(f"{prefix} requirement={row['requirement']} status={row['status']}")
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
