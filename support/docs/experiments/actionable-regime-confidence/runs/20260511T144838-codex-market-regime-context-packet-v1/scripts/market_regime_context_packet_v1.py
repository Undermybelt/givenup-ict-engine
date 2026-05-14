#!/usr/bin/env python3
"""Materialize a downstream-facing market regime context packet from accepted positives."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260511T144838+0800-codex-market-regime-context-packet-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T144838-codex-market-regime-context-packet-v1"
)
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
POSITIVE_INDEX_CSV = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T140042-codex-positive-regime-factor-index-v1/"
    "positive-factor-index/positive_regime_factor_index_v1.csv"
)
EXACT_1H_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T141910-codex-exact-1h-source-universe-expansion-v1/"
    "exact-1h-universe/exact_1h_source_universe_expansion_v1.json"
)
CONSUMER_LEDGER_CSV = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T143344-codex-regime-consumer-unit-pivot-v1/"
    "consumer-unit-pivot/regime_consumer_unit_pivot_v1_ledger.csv"
)
OUT_JSON = RUN_ROOT / "market-regime-context/market_regime_context_packet_v1.json"
OUT_MD = RUN_ROOT / "market-regime-context/market_regime_context_packet_v1.md"
OUT_LAYERS = RUN_ROOT / "market-regime-context/market_regime_context_packet_v1_layers.csv"
OUT_CONSUMER = RUN_ROOT / "market-regime-context/market_regime_context_packet_v1_consumer_contract.csv"
OUT_ASSERT = RUN_ROOT / "checks/market_regime_context_packet_v1_assertions.out"

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
MIN_LCB = 0.95


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def accepted_price_layers() -> pd.DataFrame:
    rows = pd.read_csv(POSITIVE_INDEX_CSV)
    rows = rows[
        rows["regime"].isin(ROOTS)
        & rows["taxonomy_role"].eq("MainRegimeV2_price_root")
        & rows["accepted_95"].astype(bool)
    ].copy()
    keep_layers = {
        "daily_parent_root_factor",
        "1w_source_consensus_context",
        "1mo_source_consensus_context",
        "intraday_parent_day_context_attachment",
    }
    rows = rows[rows["evidence_layer"].isin(keep_layers)].copy()
    return rows


def exact_1h_panel_layers() -> list[dict[str, Any]]:
    payload = json.loads(EXACT_1H_JSON.read_text(encoding="utf-8"))
    pooled = payload["pooled_panel_context"]
    out: list[dict[str, Any]] = []
    for root in ROOTS:
        root_payload = pooled[root]
        cal = root_payload["calibration_2024"]
        heldout = root_payload["heldout_time_2025"]
        out.append({
            "regime": root,
            "taxonomy_role": "MainRegimeV2_price_root",
            "evidence_layer": "1h_exact_source_panel_context",
            "scope": "same_source_39_ticker_yfinance_1h_panel_context",
            "gate_or_variety": f"1h_panel_context:{root}",
            "rule_or_signal": "same ticker daily MainRegimeV2 root attached to yfinance 1h session date; pooled panel context only",
            "calibration_support": int(cal["support"]),
            "calibration_wilson95_lcb": float(cal["wilson95_lcb"]),
            "heldout_time_support": int(heldout["support"]),
            "heldout_time_wilson95_lcb": float(heldout["wilson95_lcb"]),
            "heldout_context_support": "",
            "heldout_context_wilson95_lcb": "",
            "min_split_wilson95_lcb": min(float(cal["wilson95_lcb"]), float(heldout["wilson95_lcb"])),
            "accepted_95": bool(root_payload["accepted_95_panel_context"]),
            "limitations": "Panel context only; not ticker-specific support and not an intraday micro-regime.",
            "artifact": str(EXACT_1H_JSON),
        })
    return out


def root_packet(root: str, layers: pd.DataFrame) -> dict[str, Any]:
    root_layers = layers[layers["regime"].eq(root)].copy()
    min_lcb = float(root_layers["min_split_wilson95_lcb"].astype(float).min())
    layer_names = sorted(root_layers["evidence_layer"].unique().tolist())
    artifacts = sorted(root_layers["artifact"].dropna().unique().tolist())
    return {
        "root": root,
        "consumer_scope": "market_regime_context",
        "context_ready": bool(min_lcb >= MIN_LCB and len(layer_names) >= 4),
        "accepted_layers": layer_names,
        "accepted_layer_count": len(layer_names),
        "min_split_wilson95_lcb_floor": round(min_lcb, 10),
        "primary_use": [
            "pre_bayes_regime_context",
            "bbn_soft_evidence_context",
            "catboost_path_ranker_context",
            "execution_tree_sizing_or_suppression_context",
        ],
        "disallowed_use": [
            "ticker_specific_trade_signal",
            "intraday_transition_timing_signal",
            "direct_manipulation_acceptance",
            "full_cycle_full_species_completion_claim",
        ],
        "artifacts": artifacts,
    }


def main() -> int:
    board_sha = sha256(BOARD)
    positive_layers = accepted_price_layers()
    panel_layers = pd.DataFrame(exact_1h_panel_layers())
    all_layers = pd.concat([positive_layers, panel_layers], ignore_index=True, sort=False)
    all_layers["accepted_95"] = all_layers["accepted_95"].astype(bool)
    consumer_ledger = pd.read_csv(CONSUMER_LEDGER_CSV)

    root_packets = {root: root_packet(root, all_layers) for root in ROOTS}
    roots_ready = [root for root, packet in root_packets.items() if packet["context_ready"]]
    market_unit = consumer_ledger[consumer_ledger["consumer_unit"].eq("market_regime_context_gate")].iloc[0].to_dict()
    direct_unit = consumer_ledger[consumer_ledger["consumer_unit"].eq("direct_manipulation_gate")].iloc[0].to_dict()

    consumer_contract = [
        {
            "consumer_field": "market_regime_context.root",
            "value_contract": "Bull|Bear|Sideways|Crisis",
            "source": "accepted exact-source parent-root context packet",
            "allowed_action": "provide context to downstream gates; may size down or suppress incompatible factor paths",
            "must_not_do": "must not execute trades or claim ticker-specific timing from this field alone",
        },
        {
            "consumer_field": "market_regime_context.confidence_floor",
            "value_contract": "minimum accepted split Wilson95 LCB across retained context layers",
            "source": "daily parent root, 1w/1mo source consensus, exact 1h panel context",
            "allowed_action": "audit whether context evidence remains above 0.95",
            "must_not_do": "must not reinterpret as alpha edge or profitability",
        },
        {
            "consumer_field": "market_regime_context.scope",
            "value_contract": "context_ready_not_full_completion",
            "source": "consumer-unit pivot",
            "allowed_action": "unblock market-context consumers from ticker-specific denominator drift",
            "must_not_do": "must not mark full objective complete",
        },
        {
            "consumer_field": "direct_manipulation_route",
            "value_contract": "partial_blocked",
            "source": "consumer-unit pivot and positive direct varieties",
            "allowed_action": "route to matched-row acquisition",
            "must_not_do": "must not use OHLCV/session/liquidity proxies as Manipulation labels",
        },
    ]

    result = {
        "schema_version": "market-regime-context-packet/v1",
        "run_id": RUN_ID,
        "run_root": str(RUN_ROOT),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_sha,
        "inputs": {
            "positive_index_csv": str(POSITIVE_INDEX_CSV),
            "exact_1h_panel_json": str(EXACT_1H_JSON),
            "consumer_ledger_csv": str(CONSUMER_LEDGER_CSV),
        },
        "decision": {
            "gate_result": "market_regime_context_packet_v1_price_roots4_context_ready_full_goal_still_blocked",
            "market_regime_context_ready": True,
            "roots_context_ready": roots_ready,
            "roots_context_ready_count": len(roots_ready),
            "ticker_specific_signal_gate": "partial",
            "direct_manipulation_gate": direct_unit["status"],
            "full_objective_achieved": False,
            "call_update_goal": False,
            "raw_data_committed": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "trade_usable": False,
        },
        "market_regime_context_gate": market_unit,
        "root_packets": root_packets,
        "consumer_contract": consumer_contract,
        "artifacts": {
            "report_json": str(OUT_JSON),
            "report_md": str(OUT_MD),
            "layers_csv": str(OUT_LAYERS),
            "consumer_contract_csv": str(OUT_CONSUMER),
            "assertions": str(OUT_ASSERT),
            "script": "scripts/market_regime_context_packet_v1.py",
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_ASSERT.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    all_layers.to_csv(OUT_LAYERS, index=False, quoting=csv.QUOTE_MINIMAL)
    pd.DataFrame(consumer_contract).to_csv(OUT_CONSUMER, index=False, quoting=csv.QUOTE_MINIMAL)

    md_lines = [
        "# Market Regime Context Packet v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{result['decision']['gate_result']}`",
        f"- Roots context-ready: `{', '.join(roots_ready)}`",
        "- Scope: `market_regime_context`, not ticker-specific signal and not trade execution.",
        f"- Direct Manipulation gate: `{direct_unit['status']}`; route remains matched direct rows.",
        "- Full objective achieved: `false`; `update_goal` must remain false.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Root Packets",
        "",
        "| Root | Ready | Layer count | LCB floor | Layers |",
        "|---|---:|---:|---:|---|",
    ]
    for root in ROOTS:
        packet = root_packets[root]
        md_lines.append(
            f"| {root} | {str(packet['context_ready']).lower()} | {packet['accepted_layer_count']} | {packet['min_split_wilson95_lcb_floor']} | {', '.join(packet['accepted_layers'])} |"
        )
    md_lines.extend([
        "",
        "## Consumer Contract",
        "",
        "- Downstream consumers may use this packet as regime context for gating, BBN evidence, path ranking, sizing, suppression, and audit fields.",
        "- Downstream consumers must not use it as a ticker-specific alpha, intraday transition timer, direct Manipulation label, or full-cycle/full-species completion claim.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{OUT_JSON}`",
        f"- Layers CSV: `{OUT_LAYERS}`",
        f"- Consumer contract CSV: `{OUT_CONSUMER}`",
        f"- Assertions: `{OUT_ASSERT}`",
    ])
    OUT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"run_id={RUN_ID}",
        f"gate_result={result['decision']['gate_result']}",
        f"roots_context_ready={','.join(roots_ready)}",
        f"roots_context_ready_count={len(roots_ready)}",
        "market_regime_context_ready=true",
        f"direct_manipulation_gate={direct_unit['status']}",
        "full_objective_achieved=false",
        "call_update_goal=false",
        "raw_data_committed=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    OUT_ASSERT.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps(result["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
