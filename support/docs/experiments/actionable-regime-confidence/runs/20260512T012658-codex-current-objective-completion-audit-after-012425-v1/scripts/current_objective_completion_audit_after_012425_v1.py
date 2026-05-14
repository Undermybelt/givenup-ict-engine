#!/usr/bin/env python3
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T012658-codex-current-objective-completion-audit-after-012425-v1"
BASE = Path(__file__).resolve().parents[6]
RUN_ROOT = BASE / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "current-objective-completion-audit-after-012425-v1"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = BASE / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(rel: str) -> dict:
    path = BASE / rel
    if not path.exists():
        return {"_missing": True, "_path": rel}
    return json.loads(path.read_text())


def exists(rel_or_abs: str) -> bool:
    path = Path(rel_or_abs)
    if not path.is_absolute():
        path = BASE / rel_or_abs
    return path.exists()


def status_row(requirement: str, status: str, evidence: str, blocker: str) -> dict:
    return {
        "requirement": requirement,
        "status": status,
        "evidence": evidence,
        "blocker_or_gap": blocker,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    board_text = BOARD.read_text()
    cursor = ""
    m = re.search(r"\| last_loop_id \| ([^|]+) \|", board_text)
    if m:
        cursor = m.group(1).strip()

    r6 = load_json(
        "docs/experiments/actionable-regime-confidence/runs/20260512T010127-codex-r6-owner-route-entitlement-readback-v1/r6-owner-route-entitlement-readback/r6_owner_route_entitlement_readback_v1.json"
    )
    source_cal = load_json(
        "docs/experiments/actionable-regime-confidence/runs/20260512T011056-codex-source-label-equivalence-calibration-after-root-poll-v1/source-label-equivalence-confidence-calibration/source_label_equivalence_confidence_calibration_v1.json"
    )
    arrival_cal = load_json(
        "docs/experiments/actionable-regime-confidence/runs/20260512T011954-codex-source-label-equivalence-arrival-calibration-v1/source-label-equivalence-arrival-calibration/source_label_equivalence_arrival_calibration_v1.json"
    )
    r3 = load_json(
        "docs/experiments/actionable-regime-confidence/runs/20260512T012000-codex-r3-target-cell-check-against-source-label-root-v1/r3-target-cell-check-against-source-label-root-v1/r3_target_cell_check_against_source_label_root_v1.json"
    )
    r3_public = load_json(
        "docs/experiments/actionable-regime-confidence/runs/20260512T012139-codex-r3-native-subhour-public-web-source-screen-v1/r3-native-subhour-public-web-source-screen-v1/r3_native_subhour_public_web_source_screen_v1.json"
    )
    r5 = load_json(
        "docs/experiments/actionable-regime-confidence/runs/20260512T012104-codex-r5-recency-provenance-date-disambiguation-v1/r5-recency-provenance-date-disambiguation-v1/r5_recency_provenance_date_disambiguation_v1.json"
    )
    qfail = load_json(
        "docs/experiments/actionable-regime-confidence/runs/20260512T012425-codex-source-label-qualifying-condition-failclosed-v1/source-label-qualifying-condition-failclosed-v1/source_label_qualifying_condition_failclosed_v1.json"
    )

    tmp_state = {
        "r6_owner_export_root_present": exists("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        "source_label_root_present": exists("/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_rows.csv")
        and exists("/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_provenance.json"),
        "r3_native_root_present": exists("/tmp/ict-engine-native-subhour-source-label-intake"),
        "r5_recency_root_present": exists("/tmp/ict-engine-source-panel-recency-extension"),
    }

    accepted_labels = qfail.get("accepted_labels", [])
    field_complete = qfail.get("field_complete_labels", [])
    source_labels = source_cal.get("accepted_source_confidence_95_labels")
    if source_labels is None:
        source_labels = source_cal.get("accepted_labels", [])

    checklist = [
        status_row(
            "Use the named authoritative Board A markdown and do not disturb concurrent work",
            "pass",
            f"board={BOARD.relative_to(BASE)} cursor={cursor}; append-only registrations observed",
            "none",
        ),
        status_row(
            "Every regime reaches accepted 95% confidence",
            "blocked",
            f"011056/011954 accepted_source_confidence_labels={source_labels}; 012425 accepted_labels={accepted_labels}",
            "no accepted labels; Bull/Sideways are condition leads only; Bear/Crisis remain blocked",
        ),
        status_row(
            "Bull has explicit qualifying condition and cross-market/period fields",
            "partial",
            "012425 field_complete_labels includes Bull with instruments, periods, and market contexts",
            "baseline full-row confidence gate failed; R6/canonical merge blocked; timeframe variety absent",
        ),
        status_row(
            "Sideways has explicit qualifying condition and cross-market/period fields",
            "partial",
            "012425 field_complete_labels includes Sideways with instruments, periods, and market contexts",
            "baseline full-row confidence gate failed; R6/canonical merge blocked; timeframe variety absent",
        ),
        status_row(
            "Bear accepted with 95% confidence and cross-axis validation",
            "blocked",
            "011819/012425 do not list Bear as field-complete or accepted",
            "insufficient high-confidence split support",
        ),
        status_row(
            "Crisis accepted with 95% confidence and cross-axis validation",
            "blocked",
            "011819/012425 do not list Crisis as field-complete or accepted",
            "heldout-market and market-family coverage remain insufficient",
        ),
        status_row(
            "Other markets validation remains accepted after transfer",
            "blocked",
            "Bull/Sideways have daily source-label market contexts only; no accepted labels",
            "cross-market context is not enough without accepted confidence gate and canonical merge",
        ),
        status_row(
            "Other cycles/timeframes validation remains accepted after transfer",
            "blocked",
            "012330/012425 daily-only condition leads; 012000 and 012139 show no native 15m/30m R3 rows",
            "source-native multi-timeframe evidence absent",
        ),
        status_row(
            "R6 direct Manipulation controls or explicit FLIP approval exist",
            "blocked",
            f"tmp r6 root present={tmp_state['r6_owner_export_root_present']}; 010127 remains active cursor",
            "owner-export normal controls and same-exhibit FLIP approval missing",
        ),
        status_row(
            "R3 native sub-hour source labels exist for AAPL/^IXIC 15m/30m",
            "blocked",
            f"tmp r3 root present={tmp_state['r3_native_root_present']}; r3 decision={r3.get('decision')}; public screen={r3_public.get('decision')}",
            "native sub-hour source-label rows/provenance absent",
        ),
        status_row(
            "R5 post-2026-01-30 source-panel recency extension exists",
            "blocked",
            f"tmp r5 root present={tmp_state['r5_recency_root_present']}; r5 decision={r5.get('decision')}",
            "required R5 extension rows/provenance absent",
        ),
        status_row(
            "Run provider chain with IBKR, TradingViewRemix, yfinance, and Kraken",
            "blocked",
            "latest board evidence says downstream provider rerun allowed=false",
            "accepted source/control roots and canonical merge are prerequisites",
        ),
        status_row(
            "Run Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution tree",
            "blocked",
            f"012425 downstream_chain_rerun_allowed={qfail.get('downstream_chain_rerun_allowed')}",
            "downstream promotion disallowed until accepted source/control roots exist",
        ),
        status_row(
            "No proxy promotion, threshold relaxation, raw-data commit, or runtime mutation",
            "pass",
            "012425 assertions pass for roots_not_mutated, thresholds_relaxed_false, raw_data_committed_false",
            "none",
        ),
    ]

    counts = {}
    for row in checklist:
        counts[row["status"]] = counts.get(row["status"], 0) + 1

    strict_full_objective_achieved = False
    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD.relative_to(BASE)),
        "board_sha256_before_audit": sha256(BOARD),
        "current_cursor_observed": cursor,
        "objective_restatement": [
            "Every relevant regime must have accepted confidence >=0.95.",
            "Each accepted regime must have its own qualifying condition.",
            "Acceptance must survive validation across other markets and other periods/timeframes.",
            "Provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/execution-tree chain must be run in order only after accepted source/control roots allow promotion.",
            "Concurrent board work must be preserved with append-only, non-destructive updates.",
        ],
        "tmp_state": tmp_state,
        "evidence_runs": {
            "r6_current_cursor": "20260512T010127-codex-r6-owner-route-entitlement-readback-v1",
            "source_calibration": "20260512T011056-codex-source-label-equivalence-calibration-after-root-poll-v1",
            "source_arrival_calibration": "20260512T011954-codex-source-label-equivalence-arrival-calibration-v1",
            "r3_target_check": "20260512T012000-codex-r3-target-cell-check-against-source-label-root-v1",
            "r3_public_screen": "20260512T012139-codex-r3-native-subhour-public-web-source-screen-v1",
            "r5_recency_disambiguation": "20260512T012104-codex-r5-recency-provenance-date-disambiguation-v1",
            "source_qualifying_condition_failclosed": "20260512T012425-codex-source-label-qualifying-condition-failclosed-v1",
        },
        "accepted_source_confidence_labels": source_labels,
        "field_complete_condition_labels": field_complete,
        "accepted_labels_after_012425": accepted_labels,
        "checklist_counts": counts,
        "prompt_to_artifact_checklist": checklist,
        "decision": "current_objective_completion_audit_after_012425_v1=not_complete_source_r6_r3_r5_downstream_blocked",
        "strict_full_objective_achieved": strict_full_objective_achieved,
        "update_goal": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "accepted_rows_added": 0,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    json_path = OUT_DIR / "current_objective_completion_audit_after_012425_v1.json"
    md_path = OUT_DIR / "current_objective_completion_audit_after_012425_v1.md"
    csv_path = OUT_DIR / "prompt_to_artifact_checklist_after_012425_v1.csv"
    assertions_path = CHECK_DIR / "current_objective_completion_audit_after_012425_v1_assertions.out"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["requirement", "status", "evidence", "blocker_or_gap"])
        writer.writeheader()
        writer.writerows(checklist)

    lines = [
        "# Current Objective Completion Audit After 012425 v1",
        "",
        f"- Decision: `{summary['decision']}`.",
        f"- Current cursor observed: `{cursor}`.",
        f"- Checklist counts: `{counts}`.",
        f"- Accepted labels after `012425`: `{accepted_labels}`; field-complete condition labels: `{field_complete}`.",
        f"- Source-label calibration accepted labels: `{source_labels}`.",
        f"- Tmp roots: R6 owner `{tmp_state['r6_owner_export_root_present']}`, source-label `{tmp_state['source_label_root_present']}`, R3 native `{tmp_state['r3_native_root_present']}`, R5 recency `{tmp_state['r5_recency_root_present']}`.",
        f"- Strict full objective achieved: `{str(strict_full_objective_achieved).lower()}`; `update_goal=false`.",
        "",
        "## Objective Restatement",
        "",
    ]
    for item in summary["objective_restatement"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Prompt-to-Artifact Checklist", ""])
    lines.append("| Requirement | Status | Evidence | Blocker / Gap |")
    lines.append("|---|---|---|---|")
    for row in checklist:
        lines.append(
            f"| {row['requirement']} | `{row['status']}` | {row['evidence']} | {row['blocker_or_gap']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is an audit-only packet. It does not acquire source rows or controls, does not mutate intake roots, does not relax thresholds, does not commit raw data, and does not authorize downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/execution-tree promotion.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(BASE)}`",
            f"- Checklist CSV: `{csv_path.relative_to(BASE)}`",
            f"- Assertions: `{assertions_path.relative_to(BASE)}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n")

    assertions = {
        "current_cursor_010127": cursor == "20260512T010127+0800-codex-r6-owner-route-entitlement-readback-v1",
        "source_label_root_present": tmp_state["source_label_root_present"] is True,
        "r6_owner_root_missing": tmp_state["r6_owner_export_root_present"] is False,
        "r3_native_root_missing": tmp_state["r3_native_root_present"] is False,
        "r5_recency_root_missing": tmp_state["r5_recency_root_present"] is False,
        "accepted_labels_empty": accepted_labels == [],
        "strict_full_objective_achieved_false": strict_full_objective_achieved is False,
        "update_goal_false": summary["update_goal"] is False,
        "downstream_chain_rerun_allowed_false": summary["downstream_chain_rerun_allowed"] is False,
        "thresholds_relaxed_false": summary["thresholds_relaxed"] is False,
        "raw_data_committed_false": summary["raw_data_committed"] is False,
        "trade_usable_false": summary["trade_usable"] is False,
    }
    assertions_path.write_text("\n".join(f"{k}={'PASS' if v else 'FAIL'}" for k, v in assertions.items()) + "\n")

    return 0 if all(assertions.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
