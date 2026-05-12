#!/usr/bin/env python3
import csv
import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "current-objective-audit-after-085612-v1"
CHECK_DIR = RUN_ROOT / "checks"

PUBLIC_TRIAGE_RUN = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T085612+0800-codex-public-spoofing-source-control-route-triage-after-085131-v1"
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def exists(path: Path) -> bool:
    return path.exists()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    board_text = BOARD.read_text()
    board_hash = sha256(BOARD)

    public_report = PUBLIC_TRIAGE_RUN / (
        "public-spoofing-source-control-route-triage-after-085131-v1/"
        "public_spoofing_source_control_route_triage_after_085131_v1.md"
    )
    public_csv = PUBLIC_TRIAGE_RUN / (
        "public-spoofing-source-control-route-triage-after-085131-v1/"
        "public_spoofing_source_control_route_sources_after_085131_v1.csv"
    )
    public_assertions = PUBLIC_TRIAGE_RUN / (
        "checks/public_spoofing_source_control_route_triage_after_085131_v1_assertions.out"
    )

    evidence = {
        "board_path": str(BOARD.relative_to(REPO)),
        "board_sha256_before_artifact": board_hash,
        "public_triage_registered_in_board": "085612" in board_text,
        "public_triage_report_exists": exists(public_report),
        "public_triage_csv_exists": exists(public_csv),
        "public_triage_assertions_exists": exists(public_assertions),
        "latest_board_mentions_source_control_false": "source/control evidence acquired false" in board_text[-20000:],
        "latest_board_mentions_update_goal_false": "update_goal=false" in board_text[-20000:],
        "latest_board_mentions_no_downstream_authorized": (
            "No verifier, split calibration, canonical merge" in board_text[-30000:]
        ),
    }

    checklist = [
        {
            "id": "objective_board",
            "requirement": "Use the named Board A markdown as the live coordination artifact.",
            "required_evidence": "Board file read and current hash captured before audit.",
            "evidence": f"{BOARD.relative_to(REPO)} sha256={board_hash}",
            "status": "covered",
            "blocker": "",
        },
        {
            "id": "multi_agent_safety",
            "requirement": "Do not disrupt other agents' in-progress board work.",
            "required_evidence": "Append-only behavior and count-once treatment for duplicated sections.",
            "evidence": "Board tail contains append-only race de-dup notes; this audit does not rewrite prior sections.",
            "status": "partial",
            "blocker": "Concurrent writers are still a race risk; only append-only registration is safe.",
        },
        {
            "id": "regime_95_confidence",
            "requirement": "Every regime reaches 95% confidence.",
            "required_evidence": "Accepted per-regime packets with qualifying conditions and calibrated confidence >=95%.",
            "evidence": "Latest board keeps accepted_rows_added=0 and source/control evidence acquired false.",
            "status": "blocked",
            "blocker": "Source/control and selected-history gates are not unlocked.",
        },
        {
            "id": "cross_market_validation",
            "requirement": "Validate the regimes on other markets with suitable confidence.",
            "required_evidence": "Cross-market validation instruments and confidence readbacks for each accepted regime.",
            "evidence": "No accepted regime packet is available for cross-market validation.",
            "status": "blocked",
            "blocker": "Regime acceptance is blocked before cross-market validation can be promoted.",
        },
        {
            "id": "cross_timeframe_validation",
            "requirement": "Validate the regimes on other periods/timeframes with suitable confidence.",
            "required_evidence": "Cross-period/timeframe validation and chronological calibration for each accepted regime.",
            "evidence": "No accepted regime packet is available for cross-timeframe validation.",
            "status": "blocked",
            "blocker": "Regime acceptance is blocked before cross-timeframe validation can be promoted.",
        },
        {
            "id": "real_chain_order",
            "requirement": "Operate Auto-Quant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, and execution tree in order.",
            "required_evidence": "Downstream rerun artifacts after source/control and selected-history unlock.",
            "evidence": "Board explicitly says no verifier, canonical merge, selected-data AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, or execution-tree promotion is authorized.",
            "status": "blocked",
            "blocker": "Running the chain now would violate the fail-closed Board A gate.",
        },
        {
            "id": "provider_breadth",
            "requirement": "Remember IBKR, TradingViewRemix, yf/yfinance, and Kraken provider paths.",
            "required_evidence": "Provider readback tied to accepted source/control evidence or allowed non-promotional audit.",
            "evidence": "Prior board text reports provider surface observed, but source/control remains absent.",
            "status": "partial",
            "blocker": "Provider readiness is not source/control evidence and cannot unlock promotion alone.",
        },
        {
            "id": "source_control_unlock",
            "requirement": "Acquire owner-approved/source-owned positives plus matched normal controls or approved FLIP-as-control.",
            "required_evidence": "R6/R5/R3 required-root package with provenance and matched controls.",
            "evidence": "085612 found public/academic methodology hits but official owner-export package hits=0 and verifier-native packages acquired=0.",
            "status": "blocked",
            "blocker": "No owner-approved positive/control/provenance package acquired.",
        },
        {
            "id": "selected_history",
            "requirement": "Have explicit user-selected historical path before selected-data AutoQuant promotion.",
            "required_evidence": "Explicit user-selected HTF/MTF/LTF or equivalent history selection in board.",
            "evidence": "Latest counted audits keep explicit user-selected history false.",
            "status": "blocked",
            "blocker": "No explicit selected-history approval is present.",
        },
        {
            "id": "public_route_triage",
            "requirement": "Search public/paper/open-source routes if source/control is bottlenecked.",
            "required_evidence": "Public route triage artifact after 085131.",
            "evidence": f"{public_report.relative_to(REPO)}; public routes did not unlock source/control.",
            "status": "covered_fail_closed",
            "blocker": "",
        },
        {
            "id": "no_false_completion",
            "requirement": "Do not call update_goal or claim completion until every requirement is covered.",
            "required_evidence": "Audit assertions keep update_goal=false and strict_full_objective=false.",
            "evidence": "This audit is fail-closed and does not authorize update_goal.",
            "status": "covered_fail_closed",
            "blocker": "",
        },
    ]

    counts = {}
    for row in checklist:
        counts[row["status"]] = counts.get(row["status"], 0) + 1

    result = {
        "run_id": RUN_ROOT.name,
        "gate_result": "current_objective_audit_after_085612_v1=not_complete_source_control_absent_no_selected_history_no_downstream_promotion",
        "evidence": evidence,
        "counts": counts,
        "accepted_rows_added": 0,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "explicit_user_selected_history": False,
        "all_regimes_95_cross_market_timeframe": False,
        "autoquant_filter_prebayes_bbn_catboost_execution_tree_rerun": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
        "checklist": checklist,
    }

    json_path = OUT_DIR / "current_objective_audit_after_085612_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    csv_path = OUT_DIR / "prompt_to_artifact_checklist_after_085612_v1.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "requirement", "required_evidence", "evidence", "status", "blocker"],
        )
        writer.writeheader()
        writer.writerows(checklist)

    md_path = OUT_DIR / "current_objective_audit_after_085612_v1.md"
    lines = [
        "# Current Objective Audit After 085612 v1",
        "",
        f"Run id: `{RUN_ROOT.name}`",
        "",
        "Gate result: `current_objective_audit_after_085612_v1=not_complete_source_control_absent_no_selected_history_no_downstream_promotion`",
        "",
        "## Objective Restatement",
        "",
        "Deliver 95% confidence for every regime, validate each accepted regime across other markets and timeframes, and only then report results after the real Auto-Quant -> filter / Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree chain has been operated with provider breadth. Multi-agent board work must stay append-only and fail-closed.",
        "",
        "## Prompt-To-Artifact Checklist",
        "",
        "| ID | Status | Evidence | Blocker |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        lines.append(
            f"| `{row['id']}` | `{row['status']}` | {row['evidence']} | {row['blocker']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Covered requirements: `{counts.get('covered', 0)}`.",
            f"- Covered fail-closed requirements: `{counts.get('covered_fail_closed', 0)}`.",
            f"- Partial requirements: `{counts.get('partial', 0)}`.",
            f"- Blocked requirements: `{counts.get('blocked', 0)}`.",
            "- Accepted rows added `0`.",
            "- Valid required-root unlock false.",
            "- Source/control evidence acquired false.",
            "- Explicit user-selected history false.",
            "- All regimes 95% cross-market/timeframe false.",
            "- Auto-Quant -> filter / Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree rerun false.",
            "- Canonical merge false.",
            "- Selected-data AutoQuant promotion false.",
            "- Downstream promotion rerun false.",
            "- Strict full objective false.",
            "- Trade usable false.",
            "- Promotion allowed false.",
            "- `update_goal=false`.",
            "",
            "## Next",
            "",
            "Continue source/control acquisition only. The live unblocker remains owner-approved/authenticated R6/R5/R3 source-control rows with matched controls and provenance, or explicit same-exhibit `FLIP`-as-control approval, before verifier, split calibration, canonical merge, selected-data AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, execution-tree promotion, trade claims, or `update_goal`.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines))

    assertions_path = CHECK_DIR / "current_objective_audit_after_085612_v1_assertions.out"
    assertions = [
        result["gate_result"],
        f"covered_requirements={counts.get('covered', 0)}",
        f"covered_fail_closed_requirements={counts.get('covered_fail_closed', 0)}",
        f"partial_requirements={counts.get('partial', 0)}",
        f"blocked_requirements={counts.get('blocked', 0)}",
        "accepted_rows_added=0",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "explicit_user_selected_history=false",
        "all_regimes_95_cross_market_timeframe=false",
        "autoquant_filter_prebayes_bbn_catboost_execution_tree_rerun=false",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "promotion_allowed=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n")

    print(md_path)
    print(json_path)
    print(csv_path)
    print(assertions_path)


if __name__ == "__main__":
    main()
