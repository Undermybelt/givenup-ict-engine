#!/usr/bin/env python3
"""Board A latest completion audit after 075009.

Read-only prompt-to-artifact audit for the active Board A goal. It includes
the latest settled source-route evidence through the 075009 arrival poll and
the 074844 Databento GC raw recency disposition.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


RUN_ID = "20260512T075413+0800-codex-board-a-latest-completion-audit-after-075009-v1"
GATE = "board_a_latest_completion_audit_after_075009_v1=not_complete_no_required_root_unlock_no_downstream_promotion"

SCRIPT = Path(__file__).resolve()
RUN_ROOT = SCRIPT.parents[1]
REPO = RUN_ROOT.parents[4]
OUT = RUN_ROOT / "board-a-latest-completion-audit-after-075009-v1"
CHECKS = RUN_ROOT / "checks"
RUNS = REPO / "docs/experiments/actionable-regime-confidence/runs"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

FILES = {
    "audit_074341": RUNS / "20260512T074341+0800-codex-current-objective-audit-after-074116-v1/current-objective-audit-after-074116-v1/current_objective_audit_after_074116_v1.json",
    "r3_074116": RUNS / "20260512T074116+0800-codex-r3-possible-file-manual-review-after-073755-v1/r3-possible-file-manual-review-after-073755-v1/r3_possible_file_manual_review_after_073755_v1.json",
    "codehost_074424": RUNS / "20260512T074424+0800-codex-public-codehost-source-route-probe-after-074116-v1/public-codehost-source-route-probe-after-074116-v1/public_codehost_source_route_probe_after_074116_v1.json",
    "opendata_074447": RUNS / "20260512T074447+0800-codex-open-data-catalog-source-route-probe-after-074116-v1/open-data-catalog-source-route-probe-after-074116-v1/open_data_catalog_source_route_probe_after_074116_v1.json",
    "databento_074844": RUNS / "20260512T074844+0800-codex-databento-gc-raw-recency-disposition-after-074424-v1/databento-gc-raw-recency-disposition-after-074424-v1/databento_gc_raw_recency_disposition_after_074424_v1.json",
    "arrival_075009": RUNS / "20260512T075009+0800-codex-source-control-arrival-poll-after-074700-v1/source-control-arrival-poll-after-074700-v1/source_control_arrival_poll_after_074700_v1.json",
}

ASSERTION_FILES = {
    "arrival_075009": RUNS / "20260512T075009+0800-codex-source-control-arrival-poll-after-074700-v1/checks/source_control_arrival_poll_after_074700_v1_assertions.out",
    "databento_074844": RUNS / "20260512T074844+0800-codex-databento-gc-raw-recency-disposition-after-074424-v1/checks/databento_gc_raw_recency_disposition_after_074424_v1_assertions.out",
}

APPROVAL = Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid")
R6_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
R5_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
R3_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_json(path: Path) -> dict:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError(f"{path} is not a JSON object")
    return data


def assertions(path: Path) -> dict[str, str]:
    text = path.read_text(errors="replace") if path.exists() else ""
    out: dict[str, str] = {}
    for line in text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def truth(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


def approval_readback() -> dict:
    data = load_json(APPROVAL) if APPROVAL.exists() else {}
    nested = data.get("assertions", {}) if isinstance(data.get("assertions"), dict) else {}
    rows = data.get("row_counts", {}) if isinstance(data.get("row_counts"), dict) else {}
    return {
        "exists": APPROVAL.exists(),
        "approval_present": truth(data.get("approval_present") or nested.get("approval_present")),
        "canonical_merge_allowed_now": truth(data.get("canonical_merge_allowed_now") or nested.get("canonical_merge_allowed_now")),
        "downstream_rerun_allowed_now": truth(data.get("downstream_rerun_allowed_now") or nested.get("downstream_rerun_allowed_now")),
        "flip_controls_accepted_under_current_contract": truth(data.get("flip_controls_accepted_under_current_contract") or nested.get("flip_controls_accepted_under_current_contract")),
        "positive_spoof_rows": rows.get("positive_spoof_rows"),
        "flip_rows": rows.get("flip_rows"),
        "matched_groups": rows.get("matched_groups"),
    }


def row(req: str, status: str, evidence: str, artifact: str, blocker: str) -> dict[str, str]:
    return {
        "requirement": req,
        "status": status,
        "evidence": evidence,
        "artifact": artifact,
        "blocker": blocker,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    loaded = {name: load_json(path) for name, path in FILES.items()}
    parsed_assertions = {name: assertions(path) for name, path in ASSERTION_FILES.items()}
    board_text = BOARD.read_text(errors="replace")
    approval = approval_readback()

    board_hash = sha(BOARD)
    audit = loaded["audit_074341"]
    arrival = parsed_assertions["arrival_075009"]
    databento = parsed_assertions["databento_074844"]
    valid_unlock = truth(arrival.get("valid_required_root_unlock")) or truth(audit.get("valid_required_root_unlock"))
    source_control = truth(arrival.get("source_control_evidence_acquired")) or truth(audit.get("source_control_evidence_acquired"))

    checklist = [
        row("Use Board A markdown as authoritative plan", "covered", f"exists={BOARD.exists()} sha256={board_hash}", str(BOARD.relative_to(REPO)), ""),
        row("Every active regime/root reaches 95%+ calibrated confidence", "blocked", "accepted_rows_added=0; valid_required_root_unlock=false", str(FILES["arrival_075009"].relative_to(REPO)), "R6 approval/controls absent, R5 source-panel rows absent, R3 Crisis-capable labels absent."),
        row("Validate across other markets and periods/timeframes", "blocked", "074424/074447 found zero required source exports; 074844 raw GC OHLCV is unlabeled", str(FILES["databento_074844"].relative_to(REPO)), "No accepted cross-context MainRegimeV2 source export exists."),
        row("Use IBKR/TradingViewRemix/yfinance/Kraken where available", "partial", f"provider_summary={audit.get('provider_summary')}", str(FILES["audit_074341"].relative_to(REPO)), "Provider readback is partial and non-promoting."),
        row("Operate AutoQuant", "partial", f"auto_quant_status={audit.get('auto_quant_status')}", str(FILES["audit_074341"].relative_to(REPO)), "Selected-data AutoQuant promotion is blocked by missing source/control unlock."),
        row("Operate filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution tree", "blocked", f"workflow_blocking_reason={audit.get('workflow_blocking_reason')}; path_ranking={audit.get('path_ranking')}", str(FILES["audit_074341"].relative_to(REPO)), "Downstream promotion remains forbidden before source/control unlock and canonical merge."),
        row("Acquire R6 owner/export controls or explicit approval", "blocked", f"r6_root_exists={R6_ROOT.exists()}; approval={approval}", str(APPROVAL), "Approval package is non-approving and owner/export root is absent."),
        row("Acquire post-2026-01-30 R5 source-panel rows", "blocked", f"r5_root_exists={R5_ROOT.exists()}; databento_post_cutoff={databento.get('post_2026_01_30_raw_ohlcv_present')}; source_label_columns={databento.get('source_label_columns_present')}", str(FILES["databento_074844"].relative_to(REPO)), "Post-cutoff raw OHLCV is not source-owned MainRegimeV2 labels."),
        row("Acquire verifier-native Crisis-capable R3 native-subhour labels", "blocked", f"r3_root_exists={R3_ROOT.exists()}; r3_gate={loaded['r3_074116'].get('gate_result')}", str(FILES["r3_074116"].relative_to(REPO)), "Existing TSIE-derived root is Crisis-incomplete and non-promoting."),
        row("Preserve multi-agent board work", "covered", "this run is additive; Current Cursor is not edited; target roots are not mutated", str(RUN_ROOT.relative_to(REPO)), ""),
        row("Only call update_goal when the whole objective is complete", "blocked", "strict_full_objective=false; update_goal=false", str(RUN_ROOT.relative_to(REPO)), "Blocked requirements remain."),
    ]

    result = {
        "run_id": RUN_ID,
        "gate_result": GATE,
        "board_sha256": board_hash,
        "artifact_inputs": {k: str(v.relative_to(REPO)) for k, v in FILES.items()},
        "assertion_inputs": {k: str(v.relative_to(REPO)) for k, v in ASSERTION_FILES.items()},
        "approval_readback": approval,
        "checklist": checklist,
        "accepted_rows_added": 0,
        "r6_owner_export_unlock": False,
        "r5_recency_unlock": False,
        "r3_native_subhour_unlock": False,
        "valid_required_root_unlock": valid_unlock,
        "source_control_evidence_acquired": source_control,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
        "latest_update_goal_mentions": len(re.findall(r"update_goal=false", board_text)),
    }

    json_path = OUT / "board_a_latest_completion_audit_after_075009_v1.json"
    csv_path = OUT / "prompt_to_artifact_checklist_after_075009_v1.csv"
    md_path = OUT / "board_a_latest_completion_audit_after_075009_v1.md"
    assertions_path = CHECKS / "board_a_latest_completion_audit_after_075009_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(checklist[0].keys()))
        writer.writeheader()
        writer.writerows(checklist)

    blocked = [item for item in checklist if item["status"] == "blocked"]
    partial = [item for item in checklist if item["status"] == "partial"]
    lines = [
        "# Board A Latest Completion Audit After 075009 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE}`",
        "",
        "## Objective Restatement",
        "",
        "Board A must get every active regime/root to 95%+ calibrated confidence, validate across other markets and periods/timeframes, and only then push the real chain through AutoQuant, ict-engine filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution tree while preserving multi-agent append-only board work.",
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence | Blocker |",
        "|---|---|---|---|",
    ]
    for item in checklist:
        lines.append(f"| {item['requirement']} | `{item['status']}` | {item['evidence']} | {item['blocker']} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Blocked requirements: `{len(blocked)}`; partial requirements: `{len(partial)}`.",
            "- `075009` confirms no new required root arrived after the corrected open-data readback.",
            "- `074844` confirms real post-cutoff Databento GC raw OHLCV exists, but it has no source-label or order-lifecycle control columns and cannot unlock R5/R3/R6.",
            "- R6 approval remains false; R6 owner/export root absent; R5 recency root absent; R3 remains TSIE-derived and Crisis-incomplete.",
            "- Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.",
            "",
            "## Next",
            "",
            "Continue source/control acquisition only. Do not run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion until explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows, verifier-native Crisis-capable R3 labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export exists.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines))

    checks = [
        f"gate_result={GATE}",
        f"blocked_requirements={len(blocked)}",
        f"partial_requirements={len(partial)}",
        "accepted_rows_added=0",
        f"valid_required_root_unlock={str(valid_unlock).lower()}",
        f"source_control_evidence_acquired={str(source_control).lower()}",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    if valid_unlock or source_control:
        assertions_path.write_text("FAIL unexpected source/control unlock\n")
        return 1
    assertions_path.write_text("\n".join(checks) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
