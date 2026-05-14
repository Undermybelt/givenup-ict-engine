#!/usr/bin/env python3
"""Materialize a downstream-facing market_regime_context packet.

This consumes existing accepted exact-source positives and packages only the
market-context consumer unit. It does not claim ticker-specific execution
signals or direct Manipulation completion.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


RUN_ID = "20260511T150209+0800-codex-market-regime-context-packet-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T150209-codex-market-regime-context-packet-v1"
)
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
DAILY_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T125122-codex-stock-market-regimes-parent-root-abstain/"
    "parent-root-abstain/stock_market_regimes_parent_root_abstain.json"
)
AXISWISE_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T131922-codex-source-consensus-axiswise-timeframe-gate-v1/"
    "source-consensus-axiswise/source_consensus_axiswise_timeframe_gate_v1.json"
)
EXACT_1H_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T141910-codex-exact-1h-source-universe-expansion-v1/"
    "exact-1h-universe/exact_1h_source_universe_expansion_v1.json"
)
PIVOT_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T143344-codex-regime-consumer-unit-pivot-v1/"
    "consumer-unit-pivot/regime_consumer_unit_pivot_v1.json"
)
OUT_JSON = RUN_ROOT / "market-regime-context/market_regime_context_packet_v1.json"
OUT_MD = RUN_ROOT / "market-regime-context/market_regime_context_packet_v1.md"
OUT_CSV = RUN_ROOT / "market-regime-context/market_regime_context_packet_v1_roots.csv"
OUT_ASSERT = RUN_ROOT / "checks/market_regime_context_packet_v1_assertions.out"

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
MIN_LCB = 0.95


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def min_lcb(stats: dict) -> float:
    values = []
    for value in stats.values():
        if isinstance(value, dict) and "wilson95_lcb" in value:
            values.append(float(value["wilson95_lcb"]))
    return min(values) if values else 0.0


def main() -> int:
    board_sha = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    daily = read_json(DAILY_JSON)
    axiswise = read_json(AXISWISE_JSON)
    exact_1h = read_json(EXACT_1H_JSON)
    pivot = read_json(PIVOT_JSON)

    daily_by_root = {gate["regime"]: gate for gate in daily["gates"]}
    cells_by_root_tf = {(cell["regime"], cell["timeframe"]): cell for cell in axiswise["cells"]}
    pooled_1h = exact_1h["pooled_panel_context"]

    root_rows = []
    packet_roots = {}
    for root in ROOTS:
        daily_gate = daily_by_root[root]
        cell_1w = cells_by_root_tf[(root, "1w")]
        cell_1mo = cells_by_root_tf[(root, "1mo")]
        one_hour = pooled_1h[root]
        daily_lcb = min_lcb(daily_gate["stats"])
        weekly_lcb = min_lcb(cell_1w["stats"])
        monthly_lcb = min_lcb(cell_1mo["stats"])
        one_hour_lcb = min(
            float(one_hour["calibration_2024"]["wilson95_lcb"]),
            float(one_hour["heldout_time_2025"]["wilson95_lcb"]),
        )
        context_ready = all(v >= MIN_LCB for v in [daily_lcb, weekly_lcb, monthly_lcb, one_hour_lcb])
        row = {
            "root": root,
            "consumer_unit": "market_regime_context_gate",
            "context_ready_95": context_ready,
            "daily_min_wilson95_lcb": daily_lcb,
            "weekly_min_wilson95_lcb": weekly_lcb,
            "monthly_min_wilson95_lcb": monthly_lcb,
            "one_hour_panel_context_min_wilson95_lcb": one_hour_lcb,
            "daily_gate_id": daily_gate["gate_id"],
            "weekly_gate_id": cell_1w["gate_id"],
            "monthly_gate_id": cell_1mo["gate_id"],
            "one_hour_gate_id": "exact_1h_source_universe_expansion_v1_pooled_panel_context",
            "allowed_consumer_use": "emit_market_regime_context_only",
            "forbidden_consumer_use": "ticker_specific_signal_or_trade_entry_or_direct_manipulation_completion",
        }
        root_rows.append(row)
        packet_roots[root] = row

    root_df = pd.DataFrame(root_rows)
    ready_roots = root_df[root_df["context_ready_95"]]["root"].tolist()
    context_ready = ready_roots == ROOTS

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD),
        "board_sha256_at_run": board_sha,
        "inputs": {
            "daily_parent_root_gate": str(DAILY_JSON),
            "axiswise_1w_1mo_gate": str(AXISWISE_JSON),
            "exact_1h_universe_expansion": str(EXACT_1H_JSON),
            "consumer_unit_pivot": str(PIVOT_JSON),
        },
        "consumer_unit": {
            "id": "market_regime_context_gate",
            "status": "context_ready_not_full_completion" if context_ready else "blocked",
            "active_taxonomy": "MainRegimeV2",
            "price_roots": ROOTS,
            "ready_roots": ready_roots,
            "scope": [
                "daily same-source parent-root context",
                "same-source 1w and 1mo rollup context",
                "exact-source yfinance 1h panel parent-day context",
            ],
            "explicit_non_scope": [
                "ticker-specific signal claim",
                "intraday transition timing claim",
                "trade entry permission",
                "direct Manipulation full-variety completion",
            ],
        },
        "roots": packet_roots,
        "downstream_contract": {
            "emit_field": "market_regime_context",
            "emit_allowed_roots": ready_roots,
            "confidence_floor": 0.95,
            "abstain_if": [
                "requested root is not one of Bull/Bear/Sideways/Crisis",
                "consumer requires ticker-specific root evidence",
                "consumer requires intraday transition timing rather than parent-day context",
                "consumer tries to treat Manipulation as an OHLCV root",
            ],
            "route_manipulation_to": "direct_manipulation_gate",
        },
        "decision": {
            "accepted_context_roots": ready_roots,
            "accepted_context_roots_count": len(ready_roots),
            "accepted_gate": "market_regime_context_packet_v1=roots4_context_ready_not_full_objective",
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_objective_achieved": False,
            "runtime_code_changed": False,
            "raw_data_committed": False,
            "thresholds_relaxed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Run a completion audit against the objective using market_regime_context as context-ready, "
            "ticker_specific_signal as partial, and direct_manipulation as partial/blocked. Do not call "
            "update_goal unless the audit proves all explicit objective requirements are covered."
        ),
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_ASSERT.parent.mkdir(parents=True, exist_ok=True)
    root_df.to_csv(OUT_CSV, index=False)
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Market Regime Context Packet v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This packet materializes the downstream-facing `market_regime_context_gate` from existing exact-source positives.",
        "It is explicitly not a ticker-specific signal, trade-entry permission, or direct Manipulation completion packet.",
        "",
        "## Result",
        "",
        f"- Consumer unit: `market_regime_context_gate`.",
        f"- Context-ready roots: `{', '.join(ready_roots)}`.",
        f"- Context-ready root count: `{len(ready_roots)}/4`.",
        "- Full objective achieved: `false`.",
        "- Runtime code changed: `false`.",
        "- Thresholds relaxed: `false`.",
        "- Raw data committed: `false`.",
        "- Trade usable: `false`.",
        "- Gate result: `market_regime_context_packet_v1=roots4_context_ready_not_full_objective`.",
        "",
        "## Root Context Evidence",
        "",
        "| Root | Ready | Daily Min LCB | 1w Min LCB | 1mo Min LCB | 1h Panel Min LCB |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in root_rows:
        lines.append(
            "| `{root}` | `{ready}` | {daily:.6f} | {weekly:.6f} | {monthly:.6f} | {hourly:.6f} |".format(
                root=row["root"],
                ready=str(row["context_ready_95"]).lower(),
                daily=row["daily_min_wilson95_lcb"],
                weekly=row["weekly_min_wilson95_lcb"],
                monthly=row["monthly_min_wilson95_lcb"],
                hourly=row["one_hour_panel_context_min_wilson95_lcb"],
            )
        )
    lines.extend(
        [
            "",
            "## Downstream Contract",
            "",
            "- Emit only `market_regime_context` for `Bull`, `Bear`, `Sideways`, and `Crisis`.",
            "- Abstain when a consumer asks for ticker-specific evidence or intraday transition timing.",
            "- Route `Manipulation` to the direct manipulation gate; never represent it with OHLCV/proxy roots.",
            "- Keep full-objective completion blocked until ticker-specific/full-species requirements and direct manipulation varieties are audited separately.",
            "",
            "## Next",
            "",
            "- Run a completion audit against the objective using this packet as context-ready evidence only.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    failures = []
    if ready_roots != ROOTS:
        failures.append(f"expected_ready_roots_{','.join(ROOTS)}_got_{','.join(ready_roots)}")
    if result["decision"]["full_objective_achieved"]:
        failures.append("full_objective_should_remain_false")
    if pivot.get("decision", {}).get("full_objective_achieved"):
        failures.append("pivot_claimed_full_objective_unexpected")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={board_sha}",
        f"context_ready_roots={','.join(ready_roots)}",
        f"context_ready_root_count={len(ready_roots)}",
        "consumer_unit=market_regime_context_gate",
        "ticker_specific_signal_claim=false",
        "direct_manipulation_completion_claim=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "full_objective_achieved=false",
        "assertion_status=PASS" if not failures else "assertion_status=FAIL",
    ]
    assertions.extend(f"FAIL {failure}" for failure in failures)
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    if failures:
        raise RuntimeError("; ".join(failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
