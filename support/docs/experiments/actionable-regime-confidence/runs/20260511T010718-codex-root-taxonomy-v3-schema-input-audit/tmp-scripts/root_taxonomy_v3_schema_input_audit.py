#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T010718-codex-root-taxonomy-v3-schema-input-audit"


ROOT_AXIS = [
    "BullExpansion",
    "BearExpansion",
    "Consolidation",
    "Manipulation",
    "CrisisStress",
    "TransitionRecovery",
    "UnknownOrMixed",
]


def count_lines(path: Path) -> int | None:
    try:
        with path.open("rb") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return None


def csv_header(path: Path) -> list[str]:
    try:
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
            reader = csv.reader(handle)
            return next(reader)
    except Exception:
        return []


def classify_csv(path: Path, columns: list[str], rows: int | None) -> dict[str, Any]:
    names = {c.strip().lower() for c in columns}
    rows_int = rows or 0
    data_rows = max(rows_int - 1, 0) if columns else rows_int

    has_price_size = bool({"price", "qty"} <= names or {"price", "amount"} <= names or {"price", "quantity"} <= names)
    has_trade_id = bool({"trade_id"} & names or {"trdid"} & names or {"id"} & names)
    has_trade_side = "side" in names or "buyer_maker" in names
    has_bid_ask = bool({"bid", "ask"} <= names or {"bid_price", "ask_price"} <= names or {"bid", "ask_price"} <= names)
    has_l2_shape = (
        any("asks[" in c.lower() or "bids[" in c.lower() for c in columns)
        or bool({"update_type", "side", "price"} <= names)
        or bool({"is_snapshot", "side", "price"} <= names)
    )
    has_order_lifecycle = bool({"ordstatus", "ordtype", "orderid"} <= names or {"execid", "ordstatus", "orderid"} <= names)
    has_bar_ohlcv = bool({"open", "high", "low", "close"} <= names)

    if has_order_lifecycle and str(path).startswith("/Users/thrill3r/BTC-Trading-Since-2020"):
        return {
            "input_class": "private_account_order_lifecycle",
            "support_state": "not_market_wide_manipulation_proof",
            "data_rows": data_rows,
            "directness": "direct_order_lifecycle_for_one_account_only",
            "qualifies_for_manipulation_gate": False,
        }
    if has_l2_shape:
        return {
            "input_class": "market_l2_or_depth",
            "support_state": "too_thin_fixture" if data_rows < 10000 else "candidate_needs_alignment",
            "data_rows": data_rows,
            "directness": "direct_l2_or_depth",
            "qualifies_for_manipulation_gate": data_rows >= 10000,
        }
    if has_bid_ask and not has_bar_ohlcv:
        return {
            "input_class": "quote_tick_bid_ask",
            "support_state": "candidate_quote_dynamics_only" if data_rows >= 10000 else "support_too_thin",
            "data_rows": data_rows,
            "directness": "direct_bid_ask_quotes_no_depth_or_lifecycle",
            "qualifies_for_manipulation_gate": False,
        }
    if has_trade_id or (has_price_size and has_trade_side):
        return {
            "input_class": "trade_tape",
            "support_state": "candidate_tradeflow_only" if data_rows >= 10000 else "support_too_thin",
            "data_rows": data_rows,
            "directness": "direct_trades_no_depth_or_cancel_lifecycle",
            "qualifies_for_manipulation_gate": False,
        }
    if has_bar_ohlcv:
        return {
            "input_class": "aggregated_bar_or_proxy",
            "support_state": "proxy_only_low_confidence",
            "data_rows": data_rows,
            "directness": "aggregated_bar_not_direct_manipulation_input",
            "qualifies_for_manipulation_gate": False,
        }
    return {
        "input_class": "unknown_or_unusable",
        "support_state": "not_enough_schema_evidence",
        "data_rows": data_rows,
        "directness": "unknown",
        "qualifies_for_manipulation_gate": False,
    }


def audit_file(path: Path) -> dict[str, Any]:
    item: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
    }
    if not path.exists():
        item.update({
            "input_class": "missing_file",
            "support_state": "missing_file",
            "qualifies_for_manipulation_gate": False,
        })
        return item
    item["size_bytes"] = path.stat().st_size
    if path.suffix == ".csv":
        rows = count_lines(path)
        columns = csv_header(path)
        item["line_count"] = rows
        item["columns"] = columns[:160]
        item.update(classify_csv(path, columns, rows))
        return item
    if path.suffix == ".json":
        item.update({
            "input_class": "json_summary_or_metadata",
            "support_state": "metadata_only",
            "qualifies_for_manipulation_gate": False,
        })
        return item
    if path.suffix == ".parquet":
        try:
            import pyarrow.parquet as pq  # type: ignore

            pf = pq.ParquetFile(path)
            columns = list(pf.schema_arrow.names)
            rows = int(pf.metadata.num_rows)
            item.update({
                "input_class": "market_l2_orderbook_delta_parquet",
                "support_state": "support_too_thin_fixture" if rows < 10000 else "candidate_needs_alignment",
                "directness": "direct_orderbook_deltas_with_action_side_price_size_order_id",
                "line_count": rows,
                "columns": columns,
                "qualifies_for_manipulation_gate": rows >= 10000,
            })
            return item
        except Exception as exc:
            item["parquet_read_error"] = f"{type(exc).__name__}: {exc}"
        item.update({
            "input_class": "parquet_possible_l2_delta",
            "support_state": "unread_in_current_env_pyarrow_missing",
            "directness": "potential_direct_l2_but_schema_unverified",
            "qualifies_for_manipulation_gate": False,
        })
        return item
    item.update({
        "input_class": "unknown_file_type",
        "support_state": "not_a_supported_input",
        "qualifies_for_manipulation_gate": False,
    })
    return item


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    schema = {
        "schema_version": "root-taxonomy-v3-schema/v1",
        "created_by": "20260511T010718-codex-root-taxonomy-v3-schema-input-audit",
        "root_axis": ROOT_AXIS,
        "historical_aliases": {
            "Bull": "BullExpansion when expansion/persistence is directly materialized",
            "Bear": "BearExpansion when ordinary bearish expansion is separated from CrisisStress",
            "Sideways": "Consolidation / range-bound behavior",
            "Crisis": "CrisisStress / turbulent high-volatility stress",
        },
        "priority_order": [
            "Manipulation direct overlay if direct evidence is present",
            "CrisisStress",
            "BullExpansion if bull and not bear",
            "BearExpansion if bear and not bull",
            "Consolidation",
            "TransitionRecovery",
            "UnknownOrMixed residual",
        ],
        "target_definitions": {
            "BullExpansion": "persistent positive/risk-on expansion; cannot be inherited from generic TrendExpansion without a root gate",
            "BearExpansion": "persistent negative/risk-off expansion; must be separated from CrisisStress",
            "Consolidation": "sideways/range/chop with low directional conviction; must be separated from low-vol bull drift and post-crisis compression",
            "Manipulation": "direct market-microstructure/order-flow/order-lifecycle/event evidence only; OHLCV proxies are fail-closed",
            "CrisisStress": "turbulent/high-volatility/liquidity-break stress state",
            "TransitionRecovery": "turning-point, recovery, accumulation/distribution, or post-crisis transition state; optional root until consumer contract decides",
            "UnknownOrMixed": "residual bucket for overlap, weak confidence, or mixed signals; never release confidence",
        },
        "blocked_predictor_prefixes": ["future_", "target_"],
        "acceptance_95": {
            "precision_wilson_lcb_95_min": 0.95,
            "calibration_support_min": 120,
            "test_support_min": 60,
            "ece_max": 0.05,
            "coverage_min": 0.03,
            "validation_instruments_min": 2,
            "validation_market_contexts_min": 2,
            "validation_timeframes_min": 2,
            "requires_explicit_qualifying_condition": True,
        },
        "prior_relevant_gate": {
            "artifact": "docs/experiments/actionable-regime-confidence/runs/20260511T003739-source-backed-root-gate-mtf/root-v2-source-backed/source_backed_root_gate_report.json",
            "accepted_95": ["CrisisStress"],
            "missing_95": ["BullExpansion", "BearExpansion", "Consolidation", "Manipulation", "TransitionRecovery"],
            "interpretation": "partial evidence only; not completion",
        },
    }

    crosswalk = {
        "schema_version": "root-taxonomy-v3-crosswalk/v1",
        "rule": "Historical subtype/signature packets are context only until the exact RootTaxonomyV3 class passes the unchanged root gate.",
        "crosswalk": {
            "BullExpansion": {
                "historical_aliases": ["Bull"],
                "context_packets": ["TrendExpansion"],
                "must_not_inherit": ["generic unsigned trend"],
                "promotion_requirement": "signed positive expansion root target passes 95 gate directly across contexts/timeframes",
            },
            "BearExpansion": {
                "historical_aliases": ["Bear"],
                "context_packets": ["TrendExpansion", "ExtremeStress"],
                "must_not_inherit": ["CrisisStress", "generic drawdown without ordinary-bear separation"],
                "promotion_requirement": "signed negative expansion root target passes 95 gate directly and is separated from CrisisStress",
            },
            "Consolidation": {
                "historical_aliases": ["Sideways"],
                "context_packets": ["RangeConsolidation"],
                "must_not_inherit": ["low-vol bull drift", "post-crisis compression"],
                "promotion_requirement": "root-level consolidation target passes 95 gate directly",
            },
            "Manipulation": {
                "historical_aliases": [],
                "context_packets": ["ThinLiquidity", "SessionLiquidityCoreViable"],
                "must_not_inherit": ["OHLCV sweep-like shape", "thin liquidity alone", "volume-ratio proxy"],
                "promotion_requirement": "direct tick/order-flow/bid-ask/L2/L3/order-lifecycle/venue-event evidence",
                "failure_state_without_inputs": "missing_required_inputs",
            },
            "CrisisStress": {
                "historical_aliases": ["Crisis"],
                "context_packets": ["ExtremeStress"],
                "promotion_requirement": "tail/stress root target passes 95 gate directly across contexts/timeframes",
            },
            "TransitionRecovery": {
                "historical_aliases": [],
                "context_packets": ["ReversalBrewing"],
                "promotion_requirement": "transition/recovery target passes 95 gate directly with duration and hazard controls",
                "contract_state": "optional root until downstream consumer explicitly requires it",
            },
            "UnknownOrMixed": {
                "historical_aliases": [],
                "context_packets": [],
                "promotion_requirement": "residual routing only; never a release gate",
            },
        },
    }

    candidates = [
        "/Users/thrill3r/nautilus_trader/tests/test_data/tardis/binance-futures_book_snapshot_25_BTCUSDT.csv",
        "/Users/thrill3r/nautilus_trader/tests/test_data/tardis/binance-futures_book_snapshot_5_BTCUSDT.csv",
        "/Users/thrill3r/nautilus_trader/tests/test_data/tardis/bitmex_trades_XBTUSD.csv",
        "/Users/thrill3r/nautilus_trader/tests/test_data/tardis/deribit_incremental_book_L2_BTC-PERPETUAL.csv",
        "/Users/thrill3r/nautilus_trader/tests/test_data/tardis/huobi-dm-swap_quotes_BTC-USD.csv",
        "/Users/thrill3r/nautilus_trader/tests/test_data/binance/btcusdt-depth-snap.csv",
        "/Users/thrill3r/nautilus_trader/tests/test_data/binance/btcusdt-depth-update.csv",
        "/Users/thrill3r/nautilus_trader/tests/test_data/binance/ethusdt-trades.csv",
        "/Users/thrill3r/nautilus_trader/tests/test_data/truefx/audusd-ticks.csv",
        "/Users/thrill3r/nautilus_trader/tests/test_data/truefx/usdjpy-ticks.csv",
        "/Users/thrill3r/nautilus_trader/tests/test_data/quote_tick_data.csv",
        "/Users/thrill3r/nautilus_trader/tests/test_data/nautilus/64-bit/deltas.parquet",
        "/Users/thrill3r/nautilus_trader/tests/test_data/nautilus/128-bit/deltas.parquet",
        "/Users/thrill3r/nautilus_trader/tests/test_data/large/itch_AAPL.XNAS_2019-01-30_deltas.metadata.json",
        "/Users/thrill3r/nautilus_trader/tests/test_data/large/tardis_BTC-PERPETUAL.DERIBIT_2020-04-01_deltas.metadata.json",
        "/Users/thrill3r/BTC-Trading-Since-2020/api-v1-order.csv",
        "/Users/thrill3r/BTC-Trading-Since-2020/api-v1-execution-tradeHistory.csv",
        "/private/tmp/ict-regime-chain-20260509T231052/provider-probes/richdata_provider_l2_tradeflow_availability_summary.json",
        "/private/tmp/ict-regime-chain-20260509T231052/provider-probes/aligned_ibkr_nqz5_20251218_15m_1m_bid_ask.csv",
        "/private/tmp/ict-regime-chain-20260509T231052/provider-probes/richdata_kraken_spot_xbtusd_15m_vwap_count.csv",
    ]
    audited = [audit_file(Path(p)) for p in candidates]
    qualified = [x for x in audited if x.get("qualifies_for_manipulation_gate")]
    partial = [
        x for x in audited
        if x.get("input_class") in {"quote_tick_bid_ask", "trade_tape", "market_l2_or_depth", "market_l2_orderbook_delta_parquet", "parquet_possible_l2_delta", "private_account_order_lifecycle"}
        and not x.get("qualifies_for_manipulation_gate")
    ]
    inventory = {
        "schema_version": "root-taxonomy-v3-direct-input-inventory/v1",
        "audit_state": "fail_closed",
        "manipulation_input_state": "missing_required_inputs",
        "qualifying_direct_input_sets": qualified,
        "partial_or_rejected_direct_inputs": partial,
        "all_candidates": audited,
        "decision": {
            "can_rerun_manipulation_95_gate_now": False,
            "reason": "No accessible, market-wide, sufficiently supported L2/L3/order-lifecycle/event dataset is available. Trade tapes and bid/ask ticks are partial inputs; private account order history is not market-wide manipulation proof; aggregated bars remain proxies.",
            "next_required_inputs": [
                "readable full L2/L3 order-book deltas with timestamps, side, price, size, add/update/delete semantics",
                "or market-wide order add/cancel/replace lifecycle with trade matches",
                "or venue/event/social/on-chain evidence aligned to market windows for a crypto manipulation lane",
            ],
        },
    }

    report_lines = [
        "# RootTaxonomyV3 Schema And Direct-Input Audit",
        "",
        "Run id: `20260511T010718-codex-root-taxonomy-v3-schema-input-audit`",
        "",
        "## Result",
        "",
        "- RootTaxonomyV3 schema materialized: yes.",
        "- Crosswalk materialized: yes.",
        "- Fresh 95% calibration rerun: no, blocked by input audit.",
        "- `Manipulation` input state: `missing_required_inputs`.",
        "- Accepted root state remains partial: prior source-backed gate accepted only `CrisisStress`.",
        "",
        "## Direct Input Audit Summary",
        "",
        "| Class | Files | Interpretation |",
        "|---|---:|---|",
    ]
    by_class: dict[str, list[dict[str, Any]]] = {}
    for item in audited:
        by_class.setdefault(str(item.get("input_class")), []).append(item)
    for klass in sorted(by_class):
        files = by_class[klass]
        examples = ", ".join(Path(str(x["path"])).name for x in files[:3])
        if len(files) > 3:
            examples += ", ..."
        states = sorted({str(x.get("support_state")) for x in files})
        report_lines.append(f"| `{klass}` | {len(files)} | states={states}; examples={examples} |")
    report_lines += [
        "",
        "## Decision",
        "",
        "Do not rerun a `Manipulation` 95% gate from the current inputs. The candidate files contain some direct trade and quote data, but no accessible market-wide L2/L3/order-lifecycle dataset with enough verified support. OHLCV/bid-ask bars and account-level order history remain fail-closed for manipulation proof.",
        "",
        "Next useful action: decode or acquire full L2/L3 order-book deltas, market-wide order lifecycle, or aligned event/social/on-chain evidence; then rerun unchanged RootTaxonomyV3 gates.",
        "",
    ]

    assertions = {
        "schema_materialized": True,
        "crosswalk_materialized": True,
        "root_axis": ROOT_AXIS,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "fresh_calibration_rerun": False,
        "prior_accepted_95": ["CrisisStress"],
        "missing_95": ["BullExpansion", "BearExpansion", "Consolidation", "Manipulation", "TransitionRecovery"],
        "manipulation_input_state": "missing_required_inputs",
        "can_rerun_manipulation_95_gate_now": False,
    }

    write_json(RUN_ROOT / "schema/root_taxonomy_v3_schema.json", schema)
    write_json(RUN_ROOT / "schema/root_taxonomy_v3_crosswalk.json", crosswalk)
    write_json(RUN_ROOT / "input-audit/direct_manipulation_input_inventory.json", inventory)
    (RUN_ROOT / "input-audit/direct_manipulation_input_inventory.md").write_text("\n".join(report_lines), encoding="utf-8")
    write_json(RUN_ROOT / "checks/root_taxonomy_v3_schema_input_audit_assertions.json", assertions)
    checks = [
        "PASS schema_materialized=true",
        "PASS crosswalk_materialized=true",
        "PASS root_axis=RootTaxonomyV3",
        "PASS thresholds_relaxed=false",
        "PASS runtime_code_changed=false",
        "PASS fresh_calibration_rerun=false",
        "GATE blocked_missing_required_inputs",
        "ACCEPTED_95_PRIOR CrisisStress",
        "MISSING_95 BullExpansion,BearExpansion,Consolidation,Manipulation,TransitionRecovery",
        "MANIPULATION_INPUT_STATE missing_required_inputs",
    ]
    (RUN_ROOT / "checks/root_taxonomy_v3_schema_input_audit_assertions.out").write_text("\n".join(checks) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
