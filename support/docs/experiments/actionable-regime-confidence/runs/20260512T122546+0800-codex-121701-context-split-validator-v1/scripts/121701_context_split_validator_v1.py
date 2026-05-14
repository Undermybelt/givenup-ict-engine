from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T122546+0800-codex-121701-context-split-validator-v1"
SOURCE_GAP_RUN_ID = "20260512T121701+0800-codex-120630-regime-confidence-gap-map-v1"
SOURCE_LAYERED_RUN_ID = "20260512T121542+0800-codex-120630-115700-layered-postchain-validator-v1"
SOURCE_FEEDBACK_RUN_ID = "20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1"
SOURCE_DOWNSTREAM_RUN_ID = "20260512T120630+0800-codex-115700-six-provider-1h-downstream-chain-v1"
SOURCE_AQ_RUN_ID = "20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
REPORT_DIR = ROOT / "121701-context-split-validator-v1"
CHECK_DIR = ROOT / "checks"

LAYERED_ROWS_PATH = (
    RUNS
    / SOURCE_LAYERED_RUN_ID
    / "derived"
    / "115700_layered_postchain_rows.jsonl"
)
GAP_JSON_PATH = (
    RUNS
    / SOURCE_GAP_RUN_ID
    / "120630-regime-confidence-gap-map-v1"
    / "120630_regime_confidence_gap_map_v1.json"
)
FEEDBACK_JSON_PATH = (
    RUNS
    / SOURCE_FEEDBACK_RUN_ID
    / "120630-bbn-negative-feedback-packet-v1"
    / "120630_bbn_negative_feedback_packet_v1.json"
)

MIN_CONTEXT_ROWS = 30
TARGET_CONFIDENCE = 0.95


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def pct(value: float | None) -> float:
    if value is None:
        return 0.0
    return round(float(value), 6)


def iso_ms(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(float(value) / 1000.0, tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return None


def load_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in LAYERED_ROWS_PATH.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def wilson_interval(wins: int, total: int, z: float = 1.959963984540054) -> dict[str, float]:
    if total <= 0:
        return {"low": 0.0, "high": 0.0}
    phat = wins / total
    denom = 1.0 + z * z / total
    center = (phat + z * z / (2.0 * total)) / denom
    spread = z * math.sqrt((phat * (1.0 - phat) + z * z / (4.0 * total)) / total) / denom
    return {"low": pct(max(0.0, center - spread)), "high": pct(min(1.0, center + spread))}


def provider_class(provider: str) -> str:
    if provider.startswith(("binance", "bybit", "kraken")):
        return "crypto_exchange_public"
    if provider.startswith("ibkr"):
        return "broker_crypto_midpoint"
    if provider.startswith("tvr"):
        return "tradingview_relay"
    if provider.startswith("yfinance"):
        return "public_aggregator"
    return "unknown"


def source_key(row: dict[str, Any]) -> str:
    provenance = row.get("provider_provenance") or {}
    return str(provenance.get("source_provider_key") or row.get("source_provider") or "unknown")


def source_csv(row: dict[str, Any]) -> str:
    provenance = row.get("provider_provenance") or {}
    return str(provenance.get("source_csv") or "")


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    outcomes = Counter(str(row.get("realized_outcome", "unknown")) for row in rows)
    wins = outcomes.get("win", 0)
    losses = outcomes.get("loss", 0)
    breakeven = outcomes.get("breakeven", 0)
    pnl_values = [float(row.get("pnl") or 0.0) for row in rows]
    open_values = [int(row["open_ts_ms"]) for row in rows if row.get("open_ts_ms") is not None]
    providers = sorted({str(row.get("source_provider", "unknown")) for row in rows})
    branches = sorted({str(row.get("regime_profit_branch_path", "unknown")) for row in rows})
    symbols = sorted({str(row.get("symbol", "unknown")) for row in rows})
    timeframes = sorted({str(row.get("source_timeframe") or row.get("aq_timeframe") or "unknown") for row in rows})
    provider_keys = sorted({source_key(row) for row in rows})
    source_csvs = sorted({source_csv(row) for row in rows if source_csv(row)})
    entry_regimes = dict(sorted(Counter(str(row.get("regime_at_entry", "unknown")) for row in rows).items()))
    model_selected = dict(
        sorted(
            Counter(
                str((row.get("model_probabilities_before_trade") or {}).get("selected_direction", "unknown"))
                for row in rows
            ).items()
        )
    )
    ci = wilson_interval(wins, total)
    return {
        "rows": total,
        "wins": wins,
        "losses": losses,
        "breakeven": breakeven,
        "win_rate": pct(wins / total) if total else 0.0,
        "loss_rate": pct(losses / total) if total else 0.0,
        "wilson_95_low": ci["low"],
        "wilson_95_high": ci["high"],
        "total_pnl": pct(sum(pnl_values)),
        "avg_pnl": pct(sum(pnl_values) / total) if total else 0.0,
        "open_start_ms": min(open_values) if open_values else None,
        "open_end_ms": max(open_values) if open_values else None,
        "open_start_utc": iso_ms(min(open_values)) if open_values else None,
        "open_end_utc": iso_ms(max(open_values)) if open_values else None,
        "providers": providers,
        "provider_count": len(providers),
        "provider_classes": sorted({provider_class(provider) for provider in providers}),
        "provider_keys": provider_keys,
        "source_csvs": source_csvs,
        "branch_paths": branches,
        "branch_count": len(branches),
        "symbols": symbols,
        "symbol_count": len(symbols),
        "source_timeframes": timeframes,
        "source_timeframe_count": len(timeframes),
        "entry_regime_counts": entry_regimes,
        "model_selected_direction_counts": model_selected,
    }


def split_chronologically(rows: list[dict[str, Any]], buckets: int = 4) -> list[dict[str, Any]]:
    sorted_rows = sorted(rows, key=lambda row: (int(row.get("open_ts_ms") or 0), str(row.get("trade_id", ""))))
    total = len(sorted_rows)
    base, extra = divmod(total, buckets)
    splits: list[dict[str, Any]] = []
    cursor = 0
    for idx in range(buckets):
        size = base + (1 if idx < extra else 0)
        bucket = sorted_rows[cursor : cursor + size]
        cursor += size
        summary = summarize(bucket)
        summary["split_id"] = f"chronological_q{idx + 1}"
        summary["split_index"] = idx + 1
        summary["meets_min_context_rows"] = summary["rows"] >= MIN_CONTEXT_ROWS
        splits.append(summary)
    return splits


def grouped(rows: list[dict[str, Any]], keys: list[str]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        values: list[str] = []
        for key in keys:
            if key == "provider_class":
                values.append(provider_class(str(row.get("source_provider", "unknown"))))
            else:
                values.append(str(row.get(key, "unknown")))
        buckets[tuple(values)].append(row)
    output: list[dict[str, Any]] = []
    for key_values, bucket in sorted(buckets.items()):
        item = {key: value for key, value in zip(keys, key_values)}
        item.update(summarize(bucket))
        item["meets_min_context_rows"] = item["rows"] >= MIN_CONTEXT_ROWS
        output.append(item)
    return output


def chronological_matrix(rows: list[dict[str, Any]], splits: list[dict[str, Any]], keys: list[str]) -> list[dict[str, Any]]:
    bounds: list[tuple[str, int | None, int | None]] = [
        (str(item["split_id"]), item.get("open_start_ms"), item.get("open_end_ms")) for item in splits
    ]
    rows_by_split: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        ts = int(row.get("open_ts_ms") or 0)
        for split_id, start, end in bounds:
            if start is not None and end is not None and start <= ts <= end:
                rows_by_split[split_id].append(row)
                break
    output: list[dict[str, Any]] = []
    for split_id in sorted(rows_by_split):
        for item in grouped(rows_by_split[split_id], keys):
            item["split_id"] = split_id
            output.append(item)
    return sorted(output, key=lambda item: tuple(str(item.get(k, "")) for k in ["split_id", *keys]))


def regime_confidence_readback(gap: dict[str, Any]) -> list[dict[str, Any]]:
    probs = gap.get("regime_probabilities") or {}
    output: list[dict[str, Any]] = []
    for regime in ["trend", "range", "stress", "transition"]:
        probability = float(probs.get(regime, 0.0) or 0.0)
        output.append(
            {
                "regime": regime,
                "probability": pct(probability),
                "gap_to_95": pct(max(0.0, TARGET_CONFIDENCE - probability)),
                "meets_95": probability >= TARGET_CONFIDENCE,
                "is_active": regime == gap.get("active_regime"),
            }
        )
    return output


def csv_write(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")
    (ROOT / "source_gap_run_id.txt").write_text(SOURCE_GAP_RUN_ID + "\n")
    (ROOT / "source_layered_run_id.txt").write_text(SOURCE_LAYERED_RUN_ID + "\n")

    rows = load_rows()
    gap = read_json(GAP_JSON_PATH)
    feedback = read_json(FEEDBACK_JSON_PATH)

    overall = summarize(rows)
    chrono = split_chronologically(rows, 4)
    by_provider = grouped(rows, ["source_provider"])
    by_provider_class = grouped(rows, ["provider_class"])
    by_branch = grouped(rows, ["regime_profit_branch_path"])
    by_entry_regime = grouped(rows, ["regime_at_entry"])
    provider_period = chronological_matrix(rows, chrono, ["source_provider"])
    branch_period = chronological_matrix(rows, chrono, ["regime_profit_branch_path"])
    provider_branch_period = chronological_matrix(rows, chrono, ["source_provider", "regime_profit_branch_path"])
    regime_readback = regime_confidence_readback(gap)

    row_bbn_posteriors: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        posterior = ((row.get("bbn_posterior") or {}).get("posterior") or {})
        for key, value in posterior.items():
            try:
                row_bbn_posteriors[str(key)].append(float(value))
            except (TypeError, ValueError):
                pass
    row_bbn_means = {
        key: pct(sum(values) / len(values)) for key, values in sorted(row_bbn_posteriors.items()) if values
    }

    provider_period_low_rows = [
        item
        for item in provider_period
        if int(item.get("rows") or 0) < MIN_CONTEXT_ROWS
    ]
    branch_period_low_rows = [
        item
        for item in branch_period
        if int(item.get("rows") or 0) < MIN_CONTEXT_ROWS
    ]
    contexts_with_positive_lower_bound = [
        item
        for item in [*by_provider, *by_branch, *by_entry_regime, *provider_period, *branch_period]
        if int(item.get("rows") or 0) >= MIN_CONTEXT_ROWS and float(item.get("wilson_95_low") or 0.0) > 0.5
    ]

    coverage = {
        "source_rows": len(rows),
        "chronological_splits": len(chrono),
        "chronological_min_rows": min((int(item.get("rows") or 0) for item in chrono), default=0),
        "cross_provider_available": overall["provider_count"] >= 2,
        "provider_count": overall["provider_count"],
        "provider_classes": overall["provider_classes"],
        "cross_provider_period_min_rows_met": len(provider_period_low_rows) == 0,
        "cross_branch_period_min_rows_met": len(branch_period_low_rows) == 0,
        "cross_instrument_available": overall["symbol_count"] >= 2,
        "symbol_count": overall["symbol_count"],
        "symbols": overall["symbols"],
        "cross_timeframe_available": overall["source_timeframe_count"] >= 2,
        "source_timeframe_count": overall["source_timeframe_count"],
        "source_timeframes": overall["source_timeframes"],
        "row_branch_regimes": sorted((overall["entry_regime_counts"] or {}).keys()),
        "model_selected_direction_counts": overall["model_selected_direction_counts"],
        "regime_95_met": any(item["meets_95"] for item in regime_readback),
        "active_confidence": gap.get("active_confidence"),
        "active_regime": gap.get("active_regime"),
        "range_probability": (gap.get("regime_probabilities") or {}).get("range"),
        "contexts_with_positive_wilson_lower_bound_gt_0_5": len(contexts_with_positive_lower_bound),
    }

    blockers = []
    if not coverage["regime_95_met"]:
        blockers.append("no_regime_probability_meets_95")
    if not coverage["cross_instrument_available"]:
        blockers.append("cross_instrument_validation_missing_single_symbol_namespace")
    if not coverage["cross_timeframe_available"]:
        blockers.append("cross_timeframe_validation_missing_single_aq_timeframe")
    if not coverage["cross_provider_period_min_rows_met"]:
        blockers.append("provider_chronological_cells_below_min_context_rows")
    if not coverage["cross_branch_period_min_rows_met"]:
        blockers.append("branch_chronological_cells_below_min_context_rows")
    if not contexts_with_positive_lower_bound:
        blockers.append("no_context_has_positive_wilson_lower_bound_above_0_5")
    if gap.get("execution", {}).get("ready") is not True:
        blockers.append("execution_not_ready")
    if gap.get("execution", {}).get("actionable") is not True:
        blockers.append("execution_not_actionable")
    if gap.get("execution", {}).get("review_status") == "observe":
        blockers.append("execution_review_observe")

    result = {
        "run_id": RUN_ID,
        "source_gap_run_id": SOURCE_GAP_RUN_ID,
        "source_layered_run_id": SOURCE_LAYERED_RUN_ID,
        "source_feedback_run_id": SOURCE_FEEDBACK_RUN_ID,
        "source_downstream_run_id": SOURCE_DOWNSTREAM_RUN_ID,
        "source_aq_run_id": SOURCE_AQ_RUN_ID,
        "input_artifacts": {
            "layered_rows": str(LAYERED_ROWS_PATH),
            "gap_map_json": str(GAP_JSON_PATH),
            "feedback_json": str(FEEDBACK_JSON_PATH),
        },
        "overall": overall,
        "coverage": coverage,
        "chronological_splits": chrono,
        "by_provider": by_provider,
        "by_provider_class": by_provider_class,
        "by_branch": by_branch,
        "by_entry_regime": by_entry_regime,
        "provider_period_contexts": provider_period,
        "branch_period_contexts": branch_period,
        "provider_branch_period_contexts": provider_branch_period,
        "regime_confidence_readback": regime_readback,
        "row_bbn_legacy_posterior_mean": row_bbn_means,
        "bbn_feedback_candidate_readback": feedback.get("bbn_cpd_update_candidate"),
        "blockers": blockers,
        "gate": "121701_context_split_validator_v1=context_split_validation_failed_no_promotion",
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }

    write_json(REPORT_DIR / "121701_context_split_validator_v1.json", result)

    csv_write(
        REPORT_DIR / "121701_context_split_validator_v1_chronological.csv",
        chrono,
        [
            "split_id",
            "rows",
            "wins",
            "losses",
            "win_rate",
            "wilson_95_low",
            "wilson_95_high",
            "total_pnl",
            "avg_pnl",
            "open_start_utc",
            "open_end_utc",
            "provider_count",
            "branch_count",
            "source_timeframe_count",
            "symbol_count",
            "meets_min_context_rows",
        ],
    )
    csv_write(
        REPORT_DIR / "121701_context_split_validator_v1_provider_period.csv",
        provider_period,
        [
            "split_id",
            "source_provider",
            "rows",
            "wins",
            "losses",
            "win_rate",
            "wilson_95_low",
            "wilson_95_high",
            "total_pnl",
            "avg_pnl",
            "open_start_utc",
            "open_end_utc",
            "meets_min_context_rows",
        ],
    )
    csv_write(
        REPORT_DIR / "121701_context_split_validator_v1_branch_period.csv",
        branch_period,
        [
            "split_id",
            "regime_profit_branch_path",
            "rows",
            "wins",
            "losses",
            "win_rate",
            "wilson_95_low",
            "wilson_95_high",
            "total_pnl",
            "avg_pnl",
            "open_start_utc",
            "open_end_utc",
            "meets_min_context_rows",
        ],
    )
    csv_write(
        REPORT_DIR / "121701_context_split_validator_v1_regime_confidence.csv",
        regime_readback,
        ["regime", "probability", "gap_to_95", "meets_95", "is_active"],
    )

    md_lines = [
        "# 121701 Context Split Validator v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source gap map: `{SOURCE_GAP_RUN_ID}`",
        f"Source layered rows: `{SOURCE_LAYERED_RUN_ID}`",
        f"Source feedback packet: `{SOURCE_FEEDBACK_RUN_ID}`",
        "",
        "## Readback",
        f"- Rows: `{overall['rows']}` from `{overall['provider_count']}` providers, `{overall['symbol_count']}` symbol namespace, `{overall['source_timeframe_count']}` AQ/source timeframe.",
        f"- Chronological splits: `{coverage['chronological_splits']}`; minimum split rows `{coverage['chronological_min_rows']}`.",
        f"- Active regime: `{gap.get('active_regime')}` active confidence `{gap.get('active_confidence')}`; range probability `{coverage.get('range_probability')}`.",
        f"- Row-level legacy BBN posterior mean: `{row_bbn_means}`.",
        f"- Execution readback: ready `{gap.get('execution', {}).get('ready')}`, actionable `{gap.get('execution', {}).get('actionable')}`, review `{gap.get('execution', {}).get('review_status')}`.",
        "",
        "## Context Coverage",
        f"- Cross-provider available: `{coverage['cross_provider_available']}` with classes `{coverage['provider_classes']}`.",
        f"- Cross-provider chronological min-row coverage: `{coverage['cross_provider_period_min_rows_met']}`; low-row cells `{len(provider_period_low_rows)}`.",
        f"- Cross-branch chronological min-row coverage: `{coverage['cross_branch_period_min_rows_met']}`; low-row cells `{len(branch_period_low_rows)}`.",
        f"- Cross-instrument available: `{coverage['cross_instrument_available']}`; symbols `{coverage['symbols']}`.",
        f"- Cross-timeframe available: `{coverage['cross_timeframe_available']}`; timeframes `{coverage['source_timeframes']}`.",
        f"- Contexts with Wilson 95% lower bound above 0.5: `{coverage['contexts_with_positive_wilson_lower_bound_gt_0_5']}`.",
        "",
        "## Per-Regime Confidence",
    ]
    for item in regime_readback:
        md_lines.append(
            f"- `{item['regime']}` probability `{item['probability']}`, gap_to_95 `{item['gap_to_95']}`, meets_95 `{item['meets_95']}`."
        )
    md_lines.extend(
        [
            "",
            "## Decision",
            f"- Gate: `{result['gate']}`.",
            f"- Blockers: `{blockers}`.",
            "- This packet adds chronological/provider/context validation over the existing negative/neutral rows; it does not mutate BBN likelihoods or production priors.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Next",
            "- Need additional instrument and timeframe evidence before any cross-context regime claim.",
            "- Need a real BBN evidence node that moves at least one regime probability to `>=0.95` without relaxing thresholds.",
            "- Need execution to leave `observe` through evidence, not through assertion.",
            "",
        ]
    )
    (REPORT_DIR / "121701_context_split_validator_v1.md").write_text("\n".join(md_lines))

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_gap_run_id={SOURCE_GAP_RUN_ID}",
        f"PASS rows={len(rows)}",
        f"PASS providers={overall['provider_count']}",
        f"PASS chronological_splits={len(chrono)}",
        f"PASS chronological_min_rows={coverage['chronological_min_rows']}",
        f"FAIL_CLOSED regime_95_met={coverage['regime_95_met']}",
        f"FAIL_CLOSED cross_instrument_available={coverage['cross_instrument_available']}",
        f"FAIL_CLOSED cross_timeframe_available={coverage['cross_timeframe_available']}",
        f"FAIL_CLOSED execution_ready={gap.get('execution', {}).get('ready')} actionable={gap.get('execution', {}).get('actionable')} review={gap.get('execution', {}).get('review_status')}",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "121701_context_split_validator_v1_assertions.out").write_text("\n".join(assertions) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
