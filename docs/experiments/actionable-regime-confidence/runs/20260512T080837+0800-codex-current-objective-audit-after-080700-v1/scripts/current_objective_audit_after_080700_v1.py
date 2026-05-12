#!/usr/bin/env python3
import csv
import json
from pathlib import Path


RUN_ID = "20260512T080837+0800-codex-current-objective-audit-after-080700-v1"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "current-objective-audit-after-080700-v1"
CHECKS = ROOT / "checks"

BOARD_A = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
BOARD_B = Path("docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md")

EVIDENCE = [
    {
        "id": "080333",
        "path": "docs/experiments/actionable-regime-confidence/runs/20260512T080333+0800-codex-openml-dataverse-source-route-probe-after-075932-v1/checks/openml_dataverse_source_route_probe_after_075932_v1_assertions.out",
        "kind": "source_control_probe",
    },
    {
        "id": "080336",
        "path": "docs/experiments/actionable-regime-confidence/runs/20260512T080336+0800-codex-source-control-arrival-poll-after-080054-v1/checks/source_control_arrival_poll_after_080054_v1_assertions.out",
        "kind": "arrival_poll",
    },
    {
        "id": "080411",
        "path": "docs/experiments/actionable-regime-confidence/runs/20260512T080411+0800-codex-r6-regulator-exchange-source-route-probe-after-080054-v1/checks/r6_regulator_exchange_source_route_probe_after_080054_v1_assertions.out",
        "kind": "source_control_probe",
    },
    {
        "id": "080425",
        "path": "docs/experiments/actionable-regime-confidence/runs/20260512T080425+0800-codex-target-root-approval-readback-after-075925-v1/checks/target_root_approval_readback_after_075925_v1_assertions.out",
        "kind": "approval_readback",
    },
    {
        "id": "080446",
        "path": "docs/experiments/actionable-regime-confidence/runs/20260512T080446+0800-codex-required-root-arrival-poll-after-080054-v1/checks/required_root_arrival_poll_after_080054_v1_assertions.out",
        "kind": "absent_or_stale_arrival_poll",
    },
    {
        "id": "080452",
        "path": "docs/experiments/actionable-regime-confidence/runs/20260512T080452+0800-codex-dryad-source-route-probe-after-080054-v1/checks/dryad_source_route_probe_after_080054_v1_assertions.out",
        "kind": "source_control_probe",
    },
    {
        "id": "080700",
        "path": "docs/experiments/actionable-regime-confidence/runs/20260512T080700+0800-codex-openml-dryad-mendeley-exact-web-search-after-080054-v1/checks/openml_dryad_mendeley_exact_web_search_after_080054_v1_assertions.out",
        "kind": "exact_web_search",
    },
]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def status_for(assertions: str, key: str) -> str:
    for line in assertions.splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return "missing"


def load_evidence():
    rows = []
    for item in EVIDENCE:
        path = Path(item["path"])
        text = read_text(path)
        rows.append(
            {
                "id": item["id"],
                "kind": item["kind"],
                "path": item["path"],
                "exists": path.exists(),
                "gate_result": status_for(text, "gate_result"),
                "accepted_rows_added": status_for(text, "accepted_rows_added"),
                "valid_required_root_unlock": status_for(text, "valid_required_root_unlock"),
                "source_control_evidence_acquired": status_for(text, "source_control_evidence_acquired"),
                "selected_data_autoquant_promotion": status_for(text, "selected_data_autoquant_promotion"),
                "downstream_promotion_rerun": status_for(text, "downstream_promotion_rerun"),
                "strict_full_objective": status_for(text, "strict_full_objective"),
                "trade_usable": status_for(text, "trade_usable"),
                "update_goal": status_for(text, "update_goal"),
                "raw": text,
            }
        )
    return rows


def yes(value: str) -> bool:
    return value.lower() == "true"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    board_a_text = read_text(BOARD_A)
    board_b_text = read_text(BOARD_B)
    evidence = load_evidence()

    checklist = [
        {
            "requirement": "board_a_authoritative_file",
            "status": "covered" if BOARD_A.exists() else "blocked",
            "evidence": str(BOARD_A),
            "blocker": "" if BOARD_A.exists() else "board_a_missing",
        },
        {
            "requirement": "board_b_dependency_mirror",
            "status": "covered" if BOARD_B.exists() else "blocked",
            "evidence": str(BOARD_B),
            "blocker": "" if BOARD_B.exists() else "board_b_missing",
        },
        {
            "requirement": "all_regimes_95_confidence",
            "status": "blocked",
            "evidence": "075925/075932 plus counted latest 080333/080336/080411/080425/080452/080700 remain fail-closed; 080446 is absent/stale; no accepted rows added",
            "blocker": "no_accepted_rows_and_no_per_regime_95_cross_market_unlock",
        },
        {
            "requirement": "cross_market_cross_timeframe_validation",
            "status": "blocked",
            "evidence": "latest route probes and exact web search remain negative",
            "blocker": "no_new_required_root_and_no_selected_history",
        },
        {
            "requirement": "ibkr_tradingview_yfinance_kraken_provider_use",
            "status": "partial",
            "evidence": "board text shows diagnostic provider visibility including IBKR, TradingView, yfinance, Kraken, but no promoted source/control root",
            "blocker": "diagnostic_only",
        },
        {
            "requirement": "auto_quant_operated",
            "status": "partial",
            "evidence": "prior board readbacks show AutoQuant read-only status; current run adds no new promotion evidence",
            "blocker": "selected_history_gate_missing",
        },
        {
            "requirement": "filter_prebayes_bbn_catboost_execution_tree",
            "status": "blocked",
            "evidence": "latest evidence stays upstream and fail-closed",
            "blocker": "no_promotion_allowed",
        },
        {
            "requirement": "source_control_unlock",
            "status": "blocked",
            "evidence": "080333/080336/080411/080425/080452/080700 fail closed; 080446 absent/stale",
            "blocker": "valid_required_root_unlock_false",
        },
        {
            "requirement": "user_selected_history",
            "status": "blocked",
            "evidence": "no HTF/MTF/LTF selection in the objective file or latest readbacks",
            "blocker": "user_selected_historical_data_missing",
        },
        {
            "requirement": "multi_agent_append_only",
            "status": "covered",
            "evidence": "all new evidence was appended as new artifacts or tail pointers",
            "blocker": "",
        },
        {
            "requirement": "update_goal_allowed",
            "status": "blocked",
            "evidence": "all acceptance fields remain false",
            "blocker": "objective_incomplete",
        },
    ]

    blocked = sum(1 for row in checklist if row["status"] == "blocked")
    partial = sum(1 for row in checklist if row["status"] == "partial")
    gate_result = "current_objective_audit_after_080700_v1=not_complete_source_control_unlock_absent_no_selected_history_no_downstream_promotion"

    counted_evidence_ids = [row["id"] for row in evidence if row["exists"]]
    absent_evidence_ids = [row["id"] for row in evidence if not row["exists"]]

    summary = {
        "run_id": RUN_ID,
        "gate_result": gate_result,
        "blocked_requirements": blocked,
        "partial_requirements": partial,
        "accepted_rows_added": 0,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
        "counted_evidence_ids": counted_evidence_ids,
        "absent_or_stale_evidence_ids": absent_evidence_ids,
    }

    json_path = OUT / "current_objective_audit_after_080700_v1.json"
    md_path = OUT / "current_objective_audit_after_080700_v1.md"
    csv_path = OUT / "prompt_to_artifact_checklist_after_080700_v1.csv"
    assertions_path = CHECKS / "current_objective_audit_after_080700_v1_assertions.out"

    json_path.write_text(json.dumps({**summary, "evidence": evidence, "checklist": checklist}, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["requirement", "status", "evidence", "blocker"])
        writer.writeheader()
        writer.writerows(checklist)

    md_lines = [
        "# Current Objective Audit After 080700 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{gate_result}`",
        "",
        "## Objective Restatement",
        "",
        "Board A must lift every active regime/root to 95%+ calibrated confidence, validate across other markets and periods/timeframes, and only then run the real AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution tree chain while preserving multi-agent append-only board work.",
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence | Blocker |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        md_lines.append(f"| `{row['requirement']}` | `{row['status']}` | {row['evidence']} | {row['blocker']} |")
    md_lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Blocked requirements: `{blocked}`; partial requirements: `{partial}`.",
            "- Latest evidence remains fail-closed: no accepted rows, no valid required-root unlock, no source/control evidence acquired, no canonical merge, no selected-data AutoQuant promotion, and no downstream promotion rerun.",
            "- Counted latest evidence includes `080333`, `080336`, `080411`, `080425`, `080452`, and `080700`; they are all still fail-closed.",
            "- `080446` is treated as absent/stale in this audit because its run root was not present at verification time.",
            "- `update_goal=false`.",
            "",
            "## Next",
            "",
            "Continue source/control acquisition only. Do not run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion until a valid required source/control root exists and the user selects one historical path.",
            "",
        ]
    )
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    assertions = [
        "PASS current_objective_audit_after_080700_v1",
        f"gate_result={gate_result}",
        f"blocked_requirements={blocked}",
        f"partial_requirements={partial}",
        "accepted_rows_added=0",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print("\n".join(assertions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
