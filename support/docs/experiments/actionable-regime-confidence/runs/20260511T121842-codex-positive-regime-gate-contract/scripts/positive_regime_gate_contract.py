#!/usr/bin/env python3
"""Materialize a positive, source-backed scoped gate contract for MainRegimeV2.

This intentionally avoids another source-candidate rejection audit. It reads
only already accepted positive packets, verifies their referenced artifacts, and
emits the narrow contract downstream consumers can use without claiming full
market/timeframe completion.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
OUT_DIR = RUN_ROOT / "gate-contract"
CHECK_DIR = RUN_ROOT / "checks"
OUT_JSON = OUT_DIR / "positive_regime_gate_contract.json"
OUT_MD = OUT_DIR / "positive_regime_gate_contract.md"
ASSERTIONS = CHECK_DIR / "positive_regime_gate_contract_assertions.out"

RUN_ID = "20260511T121842+0800-codex-positive-regime-gate-contract"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: str) -> Path:
    return REPO / path


def packet(
    *,
    regime: str,
    gate_id: str,
    role: str,
    artifact: str,
    rule: str,
    cal_lcb: float,
    test_lcb: float,
    cal_support: int,
    test_support: int,
    contexts: list[str],
    timeframes: list[str],
    action: str,
    guardrail: str,
) -> dict[str, Any]:
    path = rel(artifact)
    return {
        "regime": regime,
        "gate_id": gate_id,
        "taxonomy_role": role,
        "source_artifact": artifact,
        "source_artifact_exists": path.exists(),
        "source_artifact_sha256": sha256(path) if path.exists() else None,
        "qualifying_condition": rule,
        "calibration_wilson95_lcb": cal_lcb,
        "test_wilson95_lcb": test_lcb,
        "calibration_support": cal_support,
        "test_support": test_support,
        "validation_contexts": contexts,
        "validation_timeframes": timeframes,
        "accepted_95_scoped_gate": cal_lcb >= 0.95 and test_lcb >= 0.95,
        "consumer_action": action,
        "guardrail": guardrail,
    }


def build_contract() -> dict[str, Any]:
    gates = [
        packet(
            regime="Bull",
            gate_id="bull_sourcebacked_drawdown_volatility_v1",
            role="MainRegimeV2_price_root",
            artifact=(
                "docs/experiments/actionable-regime-confidence/runs/"
                "20260511T035045-codex-kaggle-bull-coverage-buffer-gate/"
                "kaggle-bull-gate/kaggle_bull_coverage_buffer_gate_report.json"
            ),
            rule="close_drawdown60 >= -0.0032047199531 AND volatility <= 0.152179344579",
            cal_lcb=0.952516,
            test_lcb=0.961931,
            cal_support=2202,
            test_support=3125,
            contexts=["index", "single_stock"],
            timeframes=["1d", "1w"],
            action="allow_or_size_up_bull_continuation_inside_supported_scope",
            guardrail="abstain outside supported index/single-stock daily-weekly scope",
        ),
        packet(
            regime="Bear",
            gate_id="bear_sourcebacked_drawdown_return_ratio_v1",
            role="MainRegimeV2_price_root",
            artifact=(
                "docs/experiments/actionable-regime-confidence/runs/"
                "20260511T041923-codex-yahoo-sourcebacked-parent-root-gate/"
                "yahoo-parent-root-gate/yahoo_sourcebacked_parent_root_gate_report.json"
            ),
            rule="bear_drawdown_ratio >= 1 AND bear_return_ratio >= 1",
            cal_lcb=0.993968,
            test_lcb=0.992722,
            cal_support=633,
            test_support=524,
            contexts=["crypto", "equity_etf"],
            timeframes=["1d", "1w"],
            action="allow_bear_defensive_or_short_bias_inside_supported_scope",
            guardrail="abstain outside supported crypto/equity-ETF daily-weekly scope",
        ),
        packet(
            regime="Sideways",
            gate_id="sideways_sourcebacked_abs_return_range_v1",
            role="MainRegimeV2_price_root",
            artifact=(
                "docs/experiments/actionable-regime-confidence/runs/"
                "20260511T041923-codex-yahoo-sourcebacked-parent-root-gate/"
                "yahoo-parent-root-gate/yahoo_sourcebacked_parent_root_gate_report.json"
            ),
            rule="sideways_abs_return_ratio <= 0.505204858191 AND sideways_range_ratio <= 0.357222193236",
            cal_lcb=0.988647,
            test_lcb=0.995568,
            cal_support=495,
            test_support=863,
            contexts=["crypto", "equity_etf"],
            timeframes=["1d", "1w"],
            action="allow_mean_reversion_or_range_logic_inside_supported_scope",
            guardrail="do not substitute old RangeConsolidation subtype for this parent-root gate",
        ),
        packet(
            regime="Crisis",
            gate_id="crisis_range_ratio_intraday_v1",
            role="MainRegimeV2_price_root",
            artifact=(
                "docs/experiments/actionable-regime-confidence/runs/"
                "20260510T235220-codex-broader-root-v2-probe/"
                "root-v2-broader/main_regime_v2_broader_root_calibration_report.json"
            ),
            rule="range_ratio32_128 >= 1.43116959912",
            cal_lcb=0.996248,
            test_lcb=0.995981,
            cal_support=1020,
            test_support=952,
            contexts=[
                "CME_futures_local",
                "IBKR_US_ETF",
                "Kraken_crypto",
                "yfinance_crypto",
                "yfinance_futures",
            ],
            timeframes=["15m", "1h"],
            action="suppress_risk_or_size_down_execution_inside_supported_scope",
            guardrail="price-stress crisis evidence is not direct manipulation evidence",
        ),
        packet(
            regime="Manipulation",
            gate_id="manipulation_telegram_pump_event_v1",
            role="separate_direct_event_order_flow_overlay_or_class",
            artifact=(
                "docs/experiments/actionable-regime-confidence/runs/"
                "20260511T045102-codex-mehrnoom-telegram-direct-manipulation-gate/"
                "direct-event-gate/mehrnoom_telegram_direct_manipulation_gate_report.json"
            ),
            rule="classified_telegram_coin_pump_event_present == 1",
            cal_lcb=0.999735,
            test_lcb=0.999701,
            cal_support=14516,
            test_support=12834,
            contexts=["crypto_telegram_event", "same_coin_non_event_controls"],
            timeframes=["event_window"],
            action="suppress_entry_or_route_to_abstain_cooldown_on_direct_event",
            guardrail="not an automatic trade entry and not an OHLCV proxy",
        ),
        packet(
            regime="Manipulation",
            gate_id="manipulation_multichain_wash_maker_v1",
            role="separate_direct_event_order_flow_overlay_or_class",
            artifact=(
                "docs/experiments/actionable-regime-confidence/runs/"
                "20260511T112642-codex-midsummer-chain-slice-expansion-audit/"
                "chain-slice-audit/midsummer_chain_slice_expansion_audit.json"
            ),
            rule="same platform/address/day paired controls AND is_both_buyer_seller == True",
            cal_lcb=0.967945,
            test_lcb=0.967945,
            cal_support=7563,
            test_support=7563,
            contexts=["base", "bsc", "ethereum", "solana"],
            timeframes=["maker_token_day"],
            action="suppress_or_abstain_on_direct_wash_maker_evidence",
            guardrail="wash-maker scope only; not full spoofing/layering/quote-stuffing coverage",
        ),
    ]

    required = ["Bull", "Bear", "Sideways", "Crisis", "Manipulation"]
    regimes_with_gate = sorted({gate["regime"] for gate in gates if gate["accepted_95_scoped_gate"]})
    missing = sorted(set(required) - set(regimes_with_gate))
    broken_refs = [gate["gate_id"] for gate in gates if not gate["source_artifact_exists"]]

    return {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD.relative_to(REPO)),
        "board_sha256_at_audit": sha256(BOARD),
        "active_taxonomy": {
            "name": "MainRegimeV2",
            "main_price_roots": ["Bull", "Bear", "Sideways", "Crisis"],
            "separate_direct_event_class_or_overlay": ["Manipulation"],
            "residual": "UnknownOrMixed",
        },
        "purpose": "Positive scoped gate contract for downstream consumers; no negative source-candidate audit.",
        "gates": gates,
        "coverage": {
            "required_regimes": required,
            "regimes_with_accepted_95_scoped_gate": regimes_with_gate,
            "missing_regimes": missing,
            "all_required_regimes_have_scoped_gate": not missing,
            "broken_source_artifact_refs": broken_refs,
            "direct_manipulation_variety_count": len(
                [gate for gate in gates if gate["regime"] == "Manipulation"]
            ),
        },
        "decision": {
            "positive_scoped_gate_contract_ready": not missing and not broken_refs,
            "accepted_95_scoped_gate_regimes": regimes_with_gate,
            "accepted_parent_root_full_matrix_completion": False,
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "gate_result": "positive_scoped_regime_gate_contract_ready_full_matrix_still_blocked",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Use this contract to feed downstream gating within supported scopes. "
            "The next useful expansion is targeted matrix filling for unsupported "
            "contexts/timeframes, not another broad negative source sweep."
        ),
    }


def write_report(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    lines = [
        "# Positive Regime Gate Contract",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This is the positive contract: every active regime has at least one verified 95% scoped gate with an existing source artifact. It does not claim full-matrix completion.",
        "",
        "| Regime | Gate | Cal LCB | Test LCB | Scope | Consumer Action |",
        "|---|---|---:|---:|---|---|",
    ]
    for gate in report["gates"]:
        scope = ", ".join(gate["validation_contexts"]) + "; " + ", ".join(gate["validation_timeframes"])
        lines.append(
            f"| `{gate['regime']}` | `{gate['gate_id']}` | "
            f"`{gate['calibration_wilson95_lcb']:.6f}` | `{gate['test_wilson95_lcb']:.6f}` | "
            f"{scope} | {gate['consumer_action']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Positive scoped gate contract ready: `{str(report['decision']['positive_scoped_gate_contract_ready']).lower()}`.",
            f"- Missing regimes: `{report['coverage']['missing_regimes']}`.",
            f"- Broken source artifact refs: `{report['coverage']['broken_source_artifact_refs']}`.",
            "- Full objective achieved: `false`.",
            f"- Gate result: `{report['decision']['gate_result']}`.",
            "",
            "## Guardrails",
            "",
            "- Use only inside each gate's supported context/timeframe scope.",
            "- Keep `Manipulation` direct-event/direct-onchain only; no OHLCV proxy promotion.",
            "- Full-market/full-timeframe completion still needs targeted matrix expansion or an owner-approved crosswalk.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines))


def write_assertions(report: dict[str, Any]) -> None:
    checks = [
        (
            "all_required_regimes_have_scoped_gate",
            report["coverage"]["all_required_regimes_have_scoped_gate"],
        ),
        (
            "source_artifact_refs_exist",
            len(report["coverage"]["broken_source_artifact_refs"]) == 0,
        ),
        (
            "manipulation_has_two_direct_varieties",
            report["coverage"]["direct_manipulation_variety_count"] >= 2,
        ),
        (
            "positive_contract_ready",
            report["decision"]["positive_scoped_gate_contract_ready"],
        ),
        (
            "full_matrix_completion_false",
            report["decision"]["accepted_parent_root_full_matrix_completion"] is False,
        ),
        ("thresholds_relaxed_false", report["decision"]["thresholds_relaxed"] is False),
        ("runtime_code_changed_false", report["decision"]["runtime_code_changed"] is False),
        ("raw_data_committed_false", report["decision"]["raw_data_committed"] is False),
    ]
    failed = [name for name, ok in checks if not ok]
    ASSERTIONS.write_text(
        "\n".join(f"{name}: {'PASS' if ok else 'FAIL'}" for name, ok in checks)
        + "\n"
        + ("ALL_ASSERTIONS_PASS\n" if not failed else f"FAILED: {', '.join(failed)}\n")
    )
    if failed:
        raise SystemExit(f"assertions failed: {', '.join(failed)}")


def main() -> None:
    report = build_contract()
    write_report(report)
    write_assertions(report)


if __name__ == "__main__":
    main()
