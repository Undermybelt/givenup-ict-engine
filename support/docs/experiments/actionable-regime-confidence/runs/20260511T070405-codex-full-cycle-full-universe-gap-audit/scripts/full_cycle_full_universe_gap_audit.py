#!/usr/bin/env python3
"""Audit Board A against the stricter full-cycle/full-universe requirement."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T070405+0800-codex-full-cycle-full-universe-gap-audit"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T070405-codex-full-cycle-full-universe-gap-audit"
OUT_DIR = RUN_ROOT / "coverage-audit"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

MIN_LCB = 0.95
MIN_COVERAGE = 0.03


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


def metric_sets(metric: dict[str, Any]) -> dict[str, set[str]]:
    return {
        "instruments": set(metric.get("validation_instruments", [])),
        "market_contexts": set(metric.get("validation_market_contexts", [])),
        "timeframes": set(metric.get("validation_timeframes", [])),
    }


def bar_root(root: str, artifact: Path, item: dict[str, Any]) -> dict[str, Any]:
    cal = item["calibration"]
    test = item["test"]
    cal_sets = metric_sets(cal)
    test_sets = metric_sets(test)
    return {
        "root": root,
        "artifact": rel(artifact),
        "rule": item.get("rule"),
        "accepted_95": bool(item.get("accepted_95", item.get("state") == "accepted_95")),
        "evidence_kind": "bar",
        "calibration": {
            "wilson95_lcb": cal.get("precision_wilson_lcb_95"),
            "coverage": cal.get("coverage"),
            "support": cal.get("support"),
            "instruments": sorted(cal_sets["instruments"]),
            "market_contexts": sorted(cal_sets["market_contexts"]),
            "timeframes": sorted(cal_sets["timeframes"]),
        },
        "test": {
            "wilson95_lcb": test.get("precision_wilson_lcb_95"),
            "coverage": test.get("coverage"),
            "support": test.get("support"),
            "instruments": sorted(test_sets["instruments"]),
            "market_contexts": sorted(test_sets["market_contexts"]),
            "timeframes": sorted(test_sets["timeframes"]),
        },
        "test_sets": test_sets,
        "sampled_95_passed": (
            bool(item.get("accepted_95", item.get("state") == "accepted_95"))
            and test.get("precision_wilson_lcb_95", 0.0) >= MIN_LCB
            and test.get("coverage", 0.0) >= MIN_COVERAGE
        ),
    }


def direct_event_root(artifact: Path, report: dict[str, Any]) -> dict[str, Any]:
    splits = {row["split"]: row for row in report["split_summaries"]}
    test = splits["test"]
    return {
        "root": "Manipulation",
        "artifact": rel(artifact),
        "rule": report["rule"],
        "accepted_95": bool(report["accepted_95"]),
        "evidence_kind": "direct_event",
        "calibration": {
            "wilson95_lcb": splits["calibration"]["wilson95_lcb"],
            "coverage": splits["calibration"]["coverage"],
            "support": splits["calibration"]["support"],
            "coins": splits["calibration"]["unique_coins_predicted_positive"],
            "channels": splits["calibration"]["unique_channels_predicted_positive"],
        },
        "test": {
            "wilson95_lcb": test["wilson95_lcb"],
            "coverage": test["coverage"],
            "support": test["support"],
            "coins": test["unique_coins_predicted_positive"],
            "channels": test["unique_channels_predicted_positive"],
        },
        "sampled_95_passed": bool(report["accepted_95"]) and test["wilson95_lcb"] >= MIN_LCB and test["coverage"] >= MIN_COVERAGE,
        "full_universe_gap": [
            "Only crypto Telegram pump-attempt direct events are accepted.",
            "Other direct manipulation varieties remain unaccepted or blocked: wash trading, NFT wash, sequence/ranking pump target prediction, SystemsLab event-rank, raw-message prediction.",
            "No bar-timeframe product exists for this event feed; it uses chronological event periods instead.",
        ],
    }


def build_report() -> dict[str, Any]:
    bull_path = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T035045-codex-kaggle-bull-coverage-buffer-gate/kaggle-bull-gate/kaggle_bull_coverage_buffer_gate_report.json"
    yahoo_path = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T041923-codex-yahoo-sourcebacked-parent-root-gate/yahoo-parent-root-gate/yahoo_sourcebacked_parent_root_gate_report.json"
    crisis_path = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T235220-codex-broader-root-v2-probe/root-v2-broader/main_regime_v2_broader_root_calibration_report.json"
    manipulation_path = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T045102-codex-mehrnoom-telegram-direct-manipulation-gate/direct-event-gate/mehrnoom_telegram_direct_manipulation_gate_report.json"

    bull = load_json(bull_path)
    yahoo = load_json(yahoo_path)
    crisis = load_json(crisis_path)
    manipulation = load_json(manipulation_path)
    crisis_item = next(row for row in crisis["root_reports"] if row["root_class"] == "Crisis")
    crisis_selected = crisis_item["selected_candidate"]

    bar_roots = [
        bar_root("Bull", bull_path, bull),
        bar_root("Bear", yahoo_path, yahoo["root_reports"]["Bear"]),
        bar_root("Sideways", yahoo_path, yahoo["root_reports"]["Sideways"]),
        bar_root(
            "Crisis",
            crisis_path,
            {
                "accepted_95": crisis_item["state"] == "accepted_95",
                "state": crisis_item["state"],
                "rule": crisis_selected["rule"],
                "calibration": crisis_selected["calibration"],
                "test": crisis_selected["test"],
            },
        ),
    ]
    manipulation_root = direct_event_root(manipulation_path, manipulation)

    observed_timeframes = sorted(set().union(*(row["test_sets"]["timeframes"] for row in bar_roots)))
    observed_contexts = sorted(set().union(*(row["test_sets"]["market_contexts"] for row in bar_roots)))
    observed_instruments = sorted(set().union(*(row["test_sets"]["instruments"] for row in bar_roots)))

    bar_root_gaps = []
    for row in bar_roots:
        missing_timeframes = sorted(set(observed_timeframes) - row["test_sets"]["timeframes"])
        missing_contexts = sorted(set(observed_contexts) - row["test_sets"]["market_contexts"])
        row["full_universe_gap"] = {
            "missing_observed_timeframes": missing_timeframes,
            "missing_observed_market_contexts": missing_contexts,
            "missing_observed_instrument_count": len(set(observed_instruments) - row["test_sets"]["instruments"]),
        }
        if missing_timeframes or missing_contexts or row["full_universe_gap"]["missing_observed_instrument_count"]:
            bar_root_gaps.append(row["root"])
        del row["test_sets"]

    checklist = [
        {
            "id": "named_board_contract",
            "requirement": "Named TODO board remains the active contract",
            "evidence": rel(BOARD),
            "passed": BOARD.exists() and "Actionable Regime Confidence TODO Board" in BOARD.read_text(),
        },
        {
            "id": "sampled_95_evidence_preserved",
            "requirement": "Previously accepted sampled 95% root evidence still exists",
            "evidence": "Accepted root artifacts",
            "passed": all(row["sampled_95_passed"] for row in [*bar_roots, manipulation_root]),
        },
        {
            "id": "full_cycle_all_observed_timeframes",
            "requirement": "Each bar root is validated on every observed accepted bar timeframe",
            "evidence": f"observed_timeframes={observed_timeframes}",
            "passed": all(not row["full_universe_gap"]["missing_observed_timeframes"] for row in bar_roots),
        },
        {
            "id": "full_universe_all_observed_contexts",
            "requirement": "Each bar root is validated on every observed accepted market context/instrument family",
            "evidence": f"observed_contexts={observed_contexts}",
            "passed": all(not row["full_universe_gap"]["missing_observed_market_contexts"] for row in bar_roots),
        },
        {
            "id": "manipulation_all_varieties",
            "requirement": "Direct-input-gated Manipulation is accepted across direct manipulation varieties, not only one crypto Telegram event feed",
            "evidence": "Mehrnoom accepted; SystemsLab/Mendeley/Bayi/Kaggle NFT/raw-message/Twitter social diagnostics remain blocked or caveat-only",
            "passed": False,
        },
    ]

    full_goal_achieved = all(item["passed"] for item in checklist)
    return {
        "run_id": RUN_ID,
        "objective": str(BOARD) + " every active regime >=95 and try all cycles/all varieties",
        "interpretation": {
            "full_cycle": "not just two timeframes; every observed accepted bar timeframe in the current evidence universe",
            "full_universe": "not just two market contexts; every observed accepted market context/instrument family plus direct manipulation varieties",
            "scope_limit": "This audit does not claim the literal global market universe is exhaustively enumerable from current repo artifacts.",
        },
        "observed_current_evidence_universe": {
            "bar_timeframes": observed_timeframes,
            "bar_market_contexts": observed_contexts,
            "bar_instruments": observed_instruments,
            "direct_manipulation_accepted_feed": "Mehrnoom/Mirtaheri Telegram pump-attempt events",
        },
        "prompt_to_artifact_checklist": checklist,
        "bar_root_results": bar_roots,
        "direct_event_root_result": manipulation_root,
        "sampled_95_roots_preserved": [row["root"] for row in [*bar_roots, manipulation_root] if row["sampled_95_passed"]],
        "full_cycle_full_universe_blockers": {
            "bar_roots_missing_full_matrix": bar_root_gaps,
            "manipulation_missing_direct_varieties": True,
            "why_not_complete": [
                "Prior audits prove at least two market/timeframe contexts, not all observed contexts/timeframes.",
                "Bull/Bear/Sideways/Crisis accepted packets use different context/timeframe slices and are not cross-product complete.",
                "Manipulation is accepted only for a crypto Telegram direct-event feed; other direct manipulation varieties are blocked or diagnostic-only.",
            ],
        },
        "goal_achieved": full_goal_achieved,
        "next_action": "Run a bounded full-matrix batch across available providers/instruments/timeframes, then keep Manipulation split by direct evidence variety; do not report full-cycle/full-universe completion until the matrix is accepted.",
        "artifacts": {
            "audit_json": rel(OUT_DIR / "full_cycle_full_universe_gap_audit.json"),
            "audit_md": rel(OUT_DIR / "full_cycle_full_universe_gap_audit.md"),
            "assertions": rel(CHECK_DIR / "full_cycle_full_universe_gap_audit_assertions.out"),
            "script": rel(Path(__file__)),
        },
    }


def write_report(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "full_cycle_full_universe_gap_audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    lines = [
        "# Full-Cycle Full-Universe Gap Audit",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Goal achieved: `{str(report['goal_achieved']).lower()}`",
        "",
        "## Checklist",
        "",
        "| Requirement | Evidence | Status |",
        "|---|---|---|",
    ]
    for item in report["prompt_to_artifact_checklist"]:
        lines.append(f"| {item['requirement']} | `{item['evidence']}` | {'PASS' if item['passed'] else 'FAIL'} |")
    lines.extend([
        "",
        "## Observed Evidence Universe",
        "",
        f"- Bar timeframes: `{', '.join(report['observed_current_evidence_universe']['bar_timeframes'])}`",
        f"- Bar market contexts: `{', '.join(report['observed_current_evidence_universe']['bar_market_contexts'])}`",
        f"- Bar instruments: `{len(report['observed_current_evidence_universe']['bar_instruments'])}` observed accepted instruments.",
        f"- Direct manipulation accepted feed: `{report['observed_current_evidence_universe']['direct_manipulation_accepted_feed']}`.",
        "",
        "## Root Gaps",
        "",
        "| Root | Sampled 95 Preserved | Missing Observed Timeframes | Missing Observed Contexts | Missing Instrument Count |",
        "|---|---:|---|---|---:|",
    ])
    for row in report["bar_root_results"]:
        gap = row["full_universe_gap"]
        lines.append(
            f"| `{row['root']}` | `{str(row['sampled_95_passed']).lower()}` | "
            f"`{', '.join(gap['missing_observed_timeframes']) or 'none'}` | "
            f"`{', '.join(gap['missing_observed_market_contexts']) or 'none'}` | "
            f"{gap['missing_observed_instrument_count']} |"
        )
    direct = report["direct_event_root_result"]
    lines.extend([
        "",
        "## Direct Manipulation Gap",
        "",
        f"- Sampled accepted feed remains 95% accepted: `{str(direct['sampled_95_passed']).lower()}`.",
        "- Full-universe gap: accepted feed is only crypto Telegram event confirmation; other direct manipulation varieties remain blocked or diagnostic-only.",
        "",
        "## Next Action",
        "",
        f"- {report['next_action']}",
        "",
    ])
    (OUT_DIR / "full_cycle_full_universe_gap_audit.md").write_text("\n".join(lines))

    assertion_lines = [
        f"goal_achieved={str(report['goal_achieved']).lower()}",
        f"sampled_95_roots_preserved={','.join(report['sampled_95_roots_preserved'])}",
    ]
    for item in report["prompt_to_artifact_checklist"]:
        assertion_lines.append(f"{'PASS' if item['passed'] else 'FAIL'} checklist.{item['id']}")
    for root in report["full_cycle_full_universe_blockers"]["bar_roots_missing_full_matrix"]:
        assertion_lines.append(f"BLOCKED full_matrix.{root}")
    assertion_lines.append("BLOCKED manipulation.direct_varieties")
    (CHECK_DIR / "full_cycle_full_universe_gap_audit_assertions.out").write_text("\n".join(assertion_lines) + "\n")


def main() -> None:
    report = build_report()
    write_report(report)
    print(json.dumps({"goal_achieved": report["goal_achieved"], "blockers": report["full_cycle_full_universe_blockers"]}, indent=2))


if __name__ == "__main__":
    main()
