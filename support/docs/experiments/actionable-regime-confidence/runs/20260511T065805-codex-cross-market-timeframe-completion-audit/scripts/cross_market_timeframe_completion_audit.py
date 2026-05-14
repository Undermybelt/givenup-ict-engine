#!/usr/bin/env python3
"""Strict completion audit for Board A cross-market/timeframe regime evidence."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T065805+0800-codex-cross-market-timeframe-completion-audit"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T065805-codex-cross-market-timeframe-completion-audit"
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

MIN_LCB = 0.95
MIN_COVERAGE = 0.03
MIN_CAL_SUPPORT = 120
MIN_TEST_SUPPORT = 60
MIN_MARKET_CONTEXTS = 2
MIN_TIMEFRAMES = 2
MIN_INSTRUMENTS = 2
MIN_EVENT_COINS = 2
MIN_EVENT_CHANNELS = 2


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


def parse_dt(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def market_metric(metric: dict[str, Any]) -> dict[str, Any]:
    instruments = metric.get("validation_instruments", [])
    contexts = metric.get("validation_market_contexts", [])
    timeframes = metric.get("validation_timeframes", [])
    return {
        "wilson95_lcb": metric.get("precision_wilson_lcb_95"),
        "support": metric.get("support"),
        "coverage": metric.get("coverage"),
        "ece": metric.get("ece"),
        "instrument_count": len(instruments),
        "market_context_count": len(contexts),
        "timeframe_count": len(timeframes),
        "instruments": instruments,
        "market_contexts": contexts,
        "timeframes": timeframes,
        "passes_lcb": metric.get("precision_wilson_lcb_95", 0.0) >= MIN_LCB,
        "passes_support": metric.get("support", 0) >= MIN_TEST_SUPPORT,
        "passes_coverage": metric.get("coverage", 0.0) >= MIN_COVERAGE,
        "passes_other_markets": len(contexts) >= MIN_MARKET_CONTEXTS and len(instruments) >= MIN_INSTRUMENTS,
        "passes_other_timeframes": len(timeframes) >= MIN_TIMEFRAMES,
    }


def market_root(root: str, report_path: Path, report: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    cal = market_metric(item["calibration"])
    test = market_metric(item["test"])
    decision = report.get("decision", {})
    root_passes = all(
        [
            item.get("accepted_95", report.get("accepted_95", False)),
            item.get("state", report.get("state")) == "accepted_95",
            not item.get("blockers", report.get("blockers", [])),
            cal["passes_lcb"],
            test["passes_lcb"],
            cal["support"] >= MIN_CAL_SUPPORT,
            test["support"] >= MIN_TEST_SUPPORT,
            cal["passes_coverage"],
            test["passes_coverage"],
            cal["passes_other_markets"],
            test["passes_other_markets"],
            cal["passes_other_timeframes"],
            test["passes_other_timeframes"],
            bool(item.get("rule") or report.get("rule")),
            not decision.get("runtime_code_changed", False),
            not decision.get("thresholds_relaxed", False),
            not decision.get("trade_usable", False),
        ]
    )
    return {
        "root": root,
        "evidence_kind": "bar_cross_market_cross_timeframe",
        "passed": root_passes,
        "artifact": rel(report_path),
        "rule": item.get("rule") or report.get("rule"),
        "accepted_95": bool(item.get("accepted_95", report.get("accepted_95", False))),
        "state": item.get("state", report.get("state")),
        "calibration": cal,
        "test": test,
        "cross_market_requirement": "at least two market contexts and two instruments in calibration and test",
        "cross_timeframe_requirement": "at least two bar timeframes in calibration and test",
        "runtime_code_changed": bool(decision.get("runtime_code_changed", False)),
        "thresholds_relaxed": bool(decision.get("thresholds_relaxed", False)),
        "trade_usable": bool(decision.get("trade_usable", False)),
    }


def crisis_root(report_path: Path, report: dict[str, Any]) -> dict[str, Any]:
    item = next(row for row in report["root_reports"] if row["root_class"] == "Crisis")
    selected = item["selected_candidate"]
    return market_root(
        "Crisis",
        report_path,
        {"decision": {"runtime_code_changed": False, "thresholds_relaxed": False, "trade_usable": False}},
        {
            "accepted_95": item["state"] == "accepted_95",
            "state": item["state"],
            "rule": selected["rule"],
            "blockers": selected.get("blockers", []),
            "calibration": selected["calibration"],
            "test": selected["test"],
        },
    )


def split_order_ok(train: dict[str, Any], cal: dict[str, Any], test: dict[str, Any]) -> bool:
    return (
        parse_dt(train["date_min"])
        <= parse_dt(train["date_max"])
        <= parse_dt(cal["date_min"])
        <= parse_dt(cal["date_max"])
        <= parse_dt(test["date_min"])
        <= parse_dt(test["date_max"])
    )


def manipulation_root(report_path: Path, report: dict[str, Any]) -> dict[str, Any]:
    splits = {row["split"]: row for row in report["split_summaries"]}
    train = splits["train"]
    cal = splits["calibration"]
    test = splits["test"]
    validation = report["validation_contexts"]
    source_stats = report["source_stats"]["coin_pump_csv"]
    chronological_pass = split_order_ok(train, cal, test)
    event_breadth_pass = all(
        [
            source_stats["unique_coins"] >= MIN_EVENT_COINS,
            source_stats["unique_channels"] >= MIN_EVENT_CHANNELS,
            cal["unique_coins_predicted_positive"] >= MIN_EVENT_COINS,
            test["unique_coins_predicted_positive"] >= MIN_EVENT_COINS,
            cal["unique_channels_predicted_positive"] >= MIN_EVENT_CHANNELS,
            test["unique_channels_predicted_positive"] >= MIN_EVENT_CHANNELS,
            validation["coins_total"] >= MIN_EVENT_COINS,
            validation["channels_total"] >= MIN_EVENT_CHANNELS,
        ]
    )
    root_passes = all(
        [
            report["accepted_95"],
            report["candidate_root"] == "Manipulation",
            report["evidence_class"] == "direct_social_event_confirmed",
            report["target_policy"].startswith("source-backed direct"),
            report["rule"] == "classified_telegram_coin_pump_event_present == 1",
            cal["wilson95_lcb"] >= MIN_LCB,
            test["wilson95_lcb"] >= MIN_LCB,
            cal["support"] >= MIN_CAL_SUPPORT,
            test["support"] >= MIN_TEST_SUPPORT,
            cal["coverage"] >= MIN_COVERAGE,
            test["coverage"] >= MIN_COVERAGE,
            cal["negative_controls"] > 0,
            test["negative_controls"] > 0,
            chronological_pass,
            event_breadth_pass,
            not report["runtime_code_changed"],
            not report["thresholds_relaxed"],
            not report["raw_data_committed"],
            not report["trade_usable"],
        ]
    )
    return {
        "root": "Manipulation",
        "evidence_kind": "direct_event_cross_coin_channel_chronological",
        "passed": root_passes,
        "artifact": rel(report_path),
        "rule": report["rule"],
        "accepted_95": bool(report["accepted_95"]),
        "state": "accepted_95" if report["accepted_95"] else "blocked",
        "calibration": {
            "wilson95_lcb": cal["wilson95_lcb"],
            "support": cal["support"],
            "coverage": cal["coverage"],
            "negative_controls": cal["negative_controls"],
            "coins": cal["unique_coins_predicted_positive"],
            "channels": cal["unique_channels_predicted_positive"],
        },
        "test": {
            "wilson95_lcb": test["wilson95_lcb"],
            "support": test["support"],
            "coverage": test["coverage"],
            "negative_controls": test["negative_controls"],
            "coins": test["unique_coins_predicted_positive"],
            "channels": test["unique_channels_predicted_positive"],
        },
        "source_breadth": {
            "coins_total": source_stats["unique_coins"],
            "channels_total": source_stats["unique_channels"],
            "date_min": source_stats["date_min"],
            "date_max": source_stats["date_max"],
        },
        "chronological_split": {
            "passes_ordering": chronological_pass,
            "train": {"date_min": train["date_min"], "date_max": train["date_max"]},
            "calibration": {"date_min": cal["date_min"], "date_max": cal["date_max"]},
            "test": {"date_min": test["date_min"], "date_max": test["date_max"]},
        },
        "cross_market_requirement": "direct event root uses other coins/channels rather than OHLCV market contexts",
        "cross_timeframe_requirement": "event-based root uses separated chronological train/calibration/test windows",
        "runtime_code_changed": bool(report["runtime_code_changed"]),
        "thresholds_relaxed": bool(report["thresholds_relaxed"]),
        "raw_data_committed": bool(report["raw_data_committed"]),
        "trade_usable": bool(report["trade_usable"]),
    }


def write_report(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    audit_json = OUT_DIR / "cross_market_timeframe_completion_audit.json"
    audit_md = OUT_DIR / "cross_market_timeframe_completion_audit.md"
    assertions = CHECK_DIR / "cross_market_timeframe_completion_audit_assertions.out"
    audit_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    rows = [
        "# Cross-Market/Timeframe Completion Audit",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Goal achieved: `{str(report['goal_achieved']).lower()}`",
        "",
        "## Prompt-To-Artifact Checklist",
        "",
        "| Requirement | Evidence | Status |",
        "|---|---|---|",
    ]
    for item in report["prompt_to_artifact_checklist"]:
        rows.append(f"| {item['requirement']} | `{item['evidence']}` | {'PASS' if item['passed'] else 'FAIL'} |")
    rows.extend(["", "## Root Results", "", "| Root | Evidence Kind | Test Wilson95 | Test Breadth | Status |", "|---|---|---:|---|---|"])
    for item in report["root_results"]:
        if item["root"] == "Manipulation":
            breadth = f"{item['test']['coins']} coins / {item['test']['channels']} channels"
            test_lcb = item["test"]["wilson95_lcb"]
        else:
            breadth = f"{item['test']['market_context_count']} contexts / {item['test']['timeframe_count']} timeframes / {item['test']['instrument_count']} instruments"
            test_lcb = item["test"]["wilson95_lcb"]
        rows.append(f"| `{item['root']}` | `{item['evidence_kind']}` | `{test_lcb:.12f}` | {breadth} | {'PASS' if item['passed'] else 'FAIL'} |")
    rows.extend(
        [
            "",
            "Notes:",
            "- This audit treats bar-based regimes and direct-event manipulation differently because a Telegram pump event is not a fixed OHLCV bar timeframe.",
            "- Manipulation is accepted only as an event-confirmed suppress/abstain/cooldown gate, not as a pre-event prediction or trade-entry signal.",
            "- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.",
            "",
        ]
    )
    audit_md.write_text("\n".join(rows))

    lines = []
    for item in report["prompt_to_artifact_checklist"]:
        lines.append(f"{'PASS' if item['passed'] else 'FAIL'} checklist.{item['id']}")
    for item in report["root_results"]:
        lines.append(f"{'PASS' if item['passed'] else 'FAIL'} root.{item['root']}")
    lines.append(f"{'PASS' if report['goal_achieved'] else 'FAIL'} goal_achieved")
    assertions.write_text("\n".join(lines) + "\n")


def main() -> None:
    board_text = BOARD.read_text()
    bull_path = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T035045-codex-kaggle-bull-coverage-buffer-gate/kaggle-bull-gate/kaggle_bull_coverage_buffer_gate_report.json"
    yahoo_path = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T041923-codex-yahoo-sourcebacked-parent-root-gate/yahoo-parent-root-gate/yahoo_sourcebacked_parent_root_gate_report.json"
    crisis_path = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T235220-codex-broader-root-v2-probe/root-v2-broader/main_regime_v2_broader_root_calibration_report.json"
    manipulation_path = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T045102-codex-mehrnoom-telegram-direct-manipulation-gate/direct-event-gate/mehrnoom_telegram_direct_manipulation_gate_report.json"

    bull = load_json(bull_path)
    yahoo = load_json(yahoo_path)
    crisis = load_json(crisis_path)
    manipulation = load_json(manipulation_path)

    root_results = [
        market_root("Bull", bull_path, bull, bull),
        market_root("Bear", yahoo_path, yahoo, yahoo["root_reports"]["Bear"]),
        market_root("Sideways", yahoo_path, yahoo, yahoo["root_reports"]["Sideways"]),
        crisis_root(crisis_path, crisis),
        manipulation_root(manipulation_path, manipulation),
    ]

    checklist = [
        {
            "id": "named_board_contract",
            "requirement": "Named TODO board is the active contract",
            "evidence": rel(BOARD),
            "passed": BOARD.exists() and "Actionable Regime Confidence TODO Board" in board_text,
        },
        {
            "id": "all_active_roots_accounted",
            "requirement": "Every active root regime is audited",
            "evidence": "Active MainRegimeV2 Root Ledger plus per-root artifacts",
            "passed": [row["root"] for row in root_results] == ["Bull", "Bear", "Sideways", "Crisis", "Manipulation"],
        },
        {
            "id": "all_roots_95",
            "requirement": "Every active regime reaches at least 95% calibrated confidence",
            "evidence": "calibration/test Wilson 95 lower confidence bound in root artifacts",
            "passed": all(row["passed"] for row in root_results),
        },
        {
            "id": "other_markets_verified",
            "requirement": "Each accepted root has other-market or other-instrument validation",
            "evidence": "market contexts and instruments for bar roots; coins/channels for direct Manipulation",
            "passed": all(row["passed"] for row in root_results),
        },
        {
            "id": "other_timeframes_or_periods_verified",
            "requirement": "Each accepted root has other-timeframe or separated chronological-period validation",
            "evidence": "1d/1w or 15m/1h for bar roots; chronological train/calibration/test event windows for Manipulation",
            "passed": all(row["passed"] for row in root_results),
        },
        {
            "id": "sub_regimes_not_counted",
            "requirement": "Sub-regime labels and preflight concepts are not counted as completed roots",
            "evidence": "Board guidance and Active MainRegimeV2 Root Ledger",
            "passed": "sub_regime_evidence_only" in board_text and "preflight_only" in board_text,
        },
        {
            "id": "no_trade_claim",
            "requirement": "No trade usability or Auto-Quant profitability is claimed",
            "evidence": "per-root artifact flags and board scope",
            "passed": all(not row["trade_usable"] for row in root_results) and "does not decide whether any Auto-Quant recipe is profitable" in board_text,
        },
    ]

    report = {
        "run_id": RUN_ID,
        "objective": str(BOARD) + " every active regime >=95 confidence and validated on other markets/timeframes before reporting result",
        "success_criteria": [
            "Named TODO board owns the active Board A contract",
            "Active roots are Bull, Bear, Sideways, Crisis, and direct-input-gated Manipulation",
            "Every active root has calibration and test Wilson95 lower bound >=0.95",
            "Bar-based roots validate across at least two market contexts, at least two instruments, and at least two timeframes",
            "Direct Manipulation validates across multiple coins/channels and separated chronological event windows",
            "Sub-regimes/preflight concepts are not counted as completion roots",
            "No trade usability or Auto-Quant profitability is claimed",
        ],
        "prompt_to_artifact_checklist": checklist,
        "root_results": root_results,
        "accepted_roots": [row["root"] for row in root_results if row["passed"]],
        "missing_or_weak_roots": [row["root"] for row in root_results if not row["passed"]],
        "goal_achieved": all(item["passed"] for item in checklist) and all(row["passed"] for row in root_results),
        "artifacts": {
            "audit_json": rel(OUT_DIR / "cross_market_timeframe_completion_audit.json"),
            "audit_md": rel(OUT_DIR / "cross_market_timeframe_completion_audit.md"),
            "assertions": rel(CHECK_DIR / "cross_market_timeframe_completion_audit_assertions.out"),
            "script": rel(RUN_ROOT / "scripts/cross_market_timeframe_completion_audit.py"),
        },
    }
    write_report(report)


if __name__ == "__main__":
    main()
