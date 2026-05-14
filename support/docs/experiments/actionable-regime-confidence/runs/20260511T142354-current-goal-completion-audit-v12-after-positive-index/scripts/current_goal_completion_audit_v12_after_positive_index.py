#!/usr/bin/env python3
"""Audit the current Board A goal against real artifacts after the positive index."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T142354+0800-current-goal-completion-audit-v12-after-positive-index"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T142354-current-goal-completion-audit-v12-after-positive-index"
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
POSITIVE_INDEX = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T140042-codex-positive-regime-factor-index-v1/"
    "positive-factor-index/positive_regime_factor_index_v1.json"
)
NDX_PROBE = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T140846-codex-ndx-source-label-availability-probe-v1/"
    "ndx-source-label-probe/ndx_source_label_availability_probe_v1.json"
)
SOURCE_RESET = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T140304-codex-source-taxonomy-strategy-reset-v1/"
    "source-taxonomy-reset/source_taxonomy_strategy_reset_v1.json"
)
CROSSWALK_TRACKING = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T135908-codex-crosswalk-tracking-source-attachment-v1/"
    "crosswalk-attachment/crosswalk_tracking_source_attachment_v1.json"
)
ES_NQ_CROSSWALK = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T135932-codex-es-nq-source-crosswalk-calibration-v1/"
    "crosswalk-calibration/es_nq_source_crosswalk_calibration_v1.json"
)
EXACT_INTRADAY = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T134756-codex-daily-to-intraday-source-attachment-v1/"
    "daily-intraday-attachment/daily_to_intraday_source_attachment_v1.json"
)
ACQUISITION_V12 = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T133453-codex-post-axiswise-acquisition-request-v12/"
    "acquisition-request/post_axiswise_acquisition_request_v12.json"
)
DIRECT_MATRIX = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T131311-codex-direct-manipulation-variety-matrix-v1/"
    "direct-manipulation/direct_manipulation_variety_matrix_v1.json"
)
FINRA_SCHEMA = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T133337-codex-finra-manipulation-acquisition-schema-v1/"
    "acquisition-schema/finra_manipulation_acquisition_schema_v1.json"
)
SPOOFING_CASES = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T130457-codex-spoofing-appendix-direct-case-inventory/"
    "direct-case-inventory/spoofing_appendix_direct_case_inventory.json"
)

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def current_cursor_lines() -> list[str]:
    lines = BOARD.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "## Current Cursor")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## 2026-"))
    return lines[start:end]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    positive = load_json(POSITIVE_INDEX)
    ndx = load_json(NDX_PROBE)
    source_reset = load_json(SOURCE_RESET)
    crosswalk_tracking = load_json(CROSSWALK_TRACKING)
    es_nq = load_json(ES_NQ_CROSSWALK)
    exact = load_json(EXACT_INTRADAY)
    acquisition = load_json(ACQUISITION_V12)
    direct = load_json(DIRECT_MATRIX)
    finra = load_json(FINRA_SCHEMA)
    spoofing_cases = load_json(SPOOFING_CASES)

    positive_supply = positive["positive_supply"]
    acquisition_decision = acquisition["decision"]
    direct_rollup = direct["rollup"]

    checklist: list[dict[str, Any]] = [
        {
            "requirement": "Each MainRegimeV2 price root has its own 95% calibrated factor",
            "status": "pass_scoped",
            "evidence": f"daily parent-root accepted roots={positive_supply['daily_parent_price_roots_accepted']}",
            "artifact": repo_rel(POSITIVE_INDEX),
            "gap": "Scoped daily US equity/index panel; not full-universe/full-timeframe completion.",
        },
        {
            "requirement": "Validate roots across other timeframes",
            "status": "partial",
            "evidence": (
                f"same-source weekly/monthly accepted={positive_supply['same_source_weekly_monthly_cells_accepted_count']}/8; "
                f"exact intraday parent context={positive_supply['exact_intraday_parent_context_rows_accepted']}/48"
            ),
            "artifact": repo_rel(POSITIVE_INDEX),
            "gap": "Exact intraday Crisis remains support-short; parent-day context is not intraday micro-regime timing.",
        },
        {
            "requirement": "Validate roots across other markets/species",
            "status": "partial",
            "evidence": (
                "SPY/DIA tracking crosswalk accepted "
                f"{crosswalk_tracking['decision']['accepted_95_crosswalk_source_attachment_rows']} rows; "
                "ES/NQ crosswalk accepted "
                f"{es_nq['decision']['accepted_95_source_label_crosswalk_attachment_rows']} rows."
            ),
            "artifact": f"{repo_rel(CROSSWALK_TRACKING)}; {repo_rel(ES_NQ_CROSSWALK)}",
            "gap": "NQ/QQQ blocked without NDX labels; many ETF/futures/index rows unresolved; full species not closed.",
        },
        {
            "requirement": "Run full-cycle/full-species accounting instead of reporting a scoped win",
            "status": "fail_open",
            "evidence": (
                f"active post-axiswise source-label requests={acquisition_decision['active_source_label_requests_after_axiswise']}; "
                f"superseded by axiswise={acquisition_decision['superseded_by_axiswise_rows']}"
            ),
            "artifact": repo_rel(ACQUISITION_V12),
            "gap": "556 source-label request rows remain active; this is not all-cycle/all-species complete.",
        },
        {
            "requirement": "Manipulation uses direct event/order-flow/order-lifecycle/on-chain/social rows, not OHLCV proxy",
            "status": "partial",
            "evidence": (
                "accepted scoped varieties="
                f"{direct_rollup['accepted_scoped_varieties']}; full variety coverage="
                f"{direct_rollup['full_direct_manipulation_variety_coverage']}"
            ),
            "artifact": repo_rel(DIRECT_MATRIX),
            "gap": "Spoofing/layering matched negatives, quote stuffing, pinging, bear raid, and painting-the-tape remain open.",
        },
        {
            "requirement": "Spoofing/layering has matched positive and negative direct rows before 95 claim",
            "status": "fail_open",
            "evidence": (
                f"FINRA schema ready but rows not acquired; positive case inventory rows="
                f"{spoofing_cases['inventory']['positive_case_rows']}; accepted_95_direct_gate_added="
                f"{spoofing_cases['decision']['accepted_95_direct_gate_added']}"
            ),
            "artifact": f"{repo_rel(FINRA_SCHEMA)}; {repo_rel(SPOOFING_CASES)}",
            "gap": "Case inventory is positive-only; no matched negative order-book/order-lifecycle rows.",
        },
        {
            "requirement": "Do not use proxy labels, HMM state ids, future returns, or provider bars as regime labels",
            "status": "pass_guardrail",
            "evidence": (
                f"source reset gate={source_reset['gate']['gate_result']}; "
                f"NDX probe gate={ndx['decision']['gate_result']}; "
                f"exact intraday gate={exact['decision']['gate_result']}"
            ),
            "artifact": f"{repo_rel(SOURCE_RESET)}; {repo_rel(NDX_PROBE)}; {repo_rel(EXACT_INTRADAY)}",
            "gap": "Guardrail preserved; it blocks completion where labels/rows are absent.",
        },
    ]

    missing = [row for row in checklist if row["status"] in {"partial", "fail_open"}]
    pass_scoped = [row for row in checklist if row["status"] == "pass_scoped"]
    pass_guardrail = [row for row in checklist if row["status"] == "pass_guardrail"]

    result = {
        "run_id": RUN_ID,
        "artifact_type": "current_goal_completion_audit_v12_after_positive_index",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": repo_rel(BOARD),
        "board_sha256_at_run": sha256(BOARD),
        "current_cursor": current_cursor_lines(),
        "objective_restated": {
            "price_roots": ROOTS,
            "direct_class_or_overlay": "Manipulation",
            "success_criteria": [
                "each price root has a regime-specific 95%-99% calibrated packet",
                "evidence survives other market/species and timeframe/period checks",
                "full-cycle/full-species accounting is not blocked",
                "Manipulation uses direct event/order-flow/order-lifecycle/on-chain/social rows with controls",
                "no OHLCV/HMM/generated/future-return proxy labels are promoted",
            ],
        },
        "checklist": checklist,
        "decision": {
            "pass_scoped_count": len(pass_scoped),
            "pass_guardrail_count": len(pass_guardrail),
            "missing_or_incomplete_count": len(missing),
            "full_objective_achieved": False,
            "call_update_goal": False,
            "gate_result": "completion_audit_v12_positive_supply_present_full_objective_still_blocked",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Do not rerun broad negative/proxy sweeps. Acquire either an NDX/QQQ/NQ source-label panel or matched direct "
            "spoofing/layering positive-negative order-lifecycle rows; otherwise keep the full objective blocked."
        ),
    }

    json_path = OUT_DIR / "current_goal_completion_audit_v12_after_positive_index.json"
    csv_path = OUT_DIR / "current_goal_completion_audit_v12_checklist.csv"
    md_path = OUT_DIR / "current_goal_completion_audit_v12_after_positive_index.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(csv_path, checklist, ["requirement", "status", "evidence", "artifact", "gap"])

    lines = [
        "# Current Goal Completion Audit v12 After Positive Index",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Objective Restated",
        "",
        "- Every active `MainRegimeV2` price root (`Bull`, `Bear`, `Sideways`, `Crisis`) needs its own 95%-99% calibrated packet.",
        "- Evidence must survive other market/species and timeframe/period checks.",
        "- Direct `Manipulation` must use direct event/order-flow/order-lifecycle/on-chain/social rows with controls.",
        "- OHLCV bars, HMM states, generated labels, future returns, and child/sub-regime packets do not complete parent roots.",
        "",
        "## Checklist",
        "",
        "| Requirement | Status | Evidence | Gap |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        lines.append(
            f"| {row['requirement']} | `{row['status']}` | {row['evidence']} | {row['gap']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Positive supply is real but scoped.",
            f"- Missing or incomplete requirements: `{len(missing)}`.",
            "- Full objective achieved: `false`.",
            "- `update_goal`: `false`.",
            "- Gate result: `completion_audit_v12_positive_supply_present_full_objective_still_blocked`.",
            "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
            "",
            "## Next",
            "",
            "Acquire either an NDX/QQQ/NQ source-label panel or matched direct spoofing/layering positive-negative order-lifecycle rows. Do not rerun provider-bar proxy sweeps.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={result['board_sha256_at_run']}",
        f"price_roots={','.join(ROOTS)}",
        f"daily_parent_price_roots_accepted_count={positive_supply['daily_parent_price_roots_accepted_count']}",
        f"same_source_weekly_monthly_cells_accepted_count={positive_supply['same_source_weekly_monthly_cells_accepted_count']}",
        f"exact_intraday_parent_context_rows_accepted={positive_supply['exact_intraday_parent_context_rows_accepted']}",
        f"direct_manipulation_full_variety_coverage={direct_rollup['full_direct_manipulation_variety_coverage']}",
        f"active_source_label_requests={acquisition_decision['active_source_label_requests_after_axiswise']}",
        f"missing_or_incomplete_count={len(missing)}",
        "full_objective_achieved=false",
        "call_update_goal=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
    ]
    checks_ok = (
        positive_supply["daily_parent_price_roots_accepted_count"] == 4
        and positive_supply["same_source_weekly_monthly_cells_accepted_count"] == 8
        and not direct_rollup["full_direct_manipulation_variety_coverage"]
        and acquisition_decision["active_source_label_requests_after_axiswise"] > 0
        and len(missing) > 0
        and not result["decision"]["full_objective_achieved"]
    )
    assertions.append(f"assertion_status={'PASS' if checks_ok else 'FAIL'}")
    (CHECK_DIR / "current_goal_completion_audit_v12_after_positive_index_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 0 if checks_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
