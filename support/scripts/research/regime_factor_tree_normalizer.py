#!/usr/bin/env python3
"""Normalize profitability-factor branch paths to regime-rooted trees.

Market, product, symbol, timeframe, and provider are labels. They are not tree
nodes. The canonical factor tree starts at the main regime class.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


KNOWN_MAIN_REGIMES = {
    "Crisis",
    "ExtremeStress",
    "MomentumContinuation",
    "Range",
    "RangeConsolidation",
    "RangeReversion",
    "ReversalBrewing",
    "SessionLiquidityCoreViable",
    "ThinLiquidity",
    "Transition",
    "TrendExpansion",
    "WideRange",
}

TIMEFRAME_SUFFIXES = ("m", "h", "d", "D", "w", "W")
TIMEFRAME_LABEL_ORDER = ("1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d", "1D", "1w", "1W")
KNOWN_PROVIDER_LABELS = {
    "binance",
    "bybit",
    "ibkr",
    "interactive_brokers",
    "kraken",
    "tvr",
    "tradingview",
    "tradingviewremix",
    "yahoo",
    "yfinance",
}
KNOWN_MARKET_LABELS = {
    "CryptoLinearPerp",
    "FUTURES",
    "US_EQ",
}
PORTABILITY_LABEL_KEYS = (
    "market",
    "product",
    "provider",
    "symbol",
    "symbols",
    "contract",
    "timeframe",
    "timeframes",
    "base_timeframe",
    "ladder_timeframes",
    "window",
    "duration",
    "category",
    "sec_type",
)

FULL_IDENTITY_LABEL_ORDER = (
    "market",
    "product",
    "symbol",
    "symbols",
    "timeframe",
    "timeframes",
    "base_timeframe",
    "provider",
)


def split_path(path: str) -> list[str]:
    return [part.strip() for part in path.split("->") if part.strip()]


def is_timeframe(value: str) -> bool:
    if not value:
        return False
    if value.endswith(TIMEFRAME_SUFFIXES) and value[:-1].isdigit():
        return True
    return value in {"1min", "3min", "5min", "15min", "30min", "1hour", "4hour", "1day"}


def is_provider_label(value: str) -> bool:
    compact = value.lower().replace(" ", "").replace("-", "_")
    return compact in KNOWN_PROVIDER_LABELS


def looks_like_symbol(value: str) -> bool:
    if not value:
        return False
    alpha = value.replace("/", "").replace("-", "").replace("_", "")
    return alpha.upper() == alpha and any(char.isalpha() for char in alpha)


def first_regime_index(parts: list[str]) -> int | None:
    for index, part in enumerate(parts):
        if part in KNOWN_MAIN_REGIMES:
            return index
    return None


def labels_from_prefix(prefix: list[str]) -> dict[str, str]:
    labels: dict[str, str] = {}
    non_timeframes: list[str] = []
    for part in prefix:
        if is_timeframe(part):
            labels.setdefault("timeframe", part)
        elif is_provider_label(part):
            labels.setdefault("provider", part)
        else:
            non_timeframes.append(part)

    if non_timeframes:
        labels["market"] = non_timeframes[0]
    if len(non_timeframes) == 2 and non_timeframes[0] in KNOWN_MARKET_LABELS and looks_like_symbol(non_timeframes[1]):
        labels["symbol"] = non_timeframes[1]
    elif len(non_timeframes) >= 2:
        labels["product"] = non_timeframes[1]
    if len(non_timeframes) >= 3:
        labels["symbol"] = non_timeframes[2]
    if len(non_timeframes) > 3:
        labels["extra_prefix_labels"] = " -> ".join(non_timeframes[3:])
    return labels


def extract_portability_labels(payload: dict[str, Any]) -> dict[str, str]:
    """Extract portability/provenance labels without treating them as tree nodes."""

    labels: dict[str, str] = {}
    labels.update(cost_stress_row_portability_labels(payload))
    labels.update(provider_rows_portability_labels(payload))
    labels.update(ladder_portability_labels(payload))
    nested = payload.get("labels")
    if isinstance(nested, dict):
        for key in PORTABILITY_LABEL_KEYS:
            value = nested.get(key)
            if isinstance(value, str) and value:
                labels[key] = value
    for key in PORTABILITY_LABEL_KEYS:
        value = payload.get(key)
        if isinstance(value, str) and value:
                labels[key] = value
    return labels


def timeframe_sort_key(value: str) -> tuple[int, str]:
    if value in TIMEFRAME_LABEL_ORDER:
        return (TIMEFRAME_LABEL_ORDER.index(value), value)
    return (len(TIMEFRAME_LABEL_ORDER), value)


def ladder_portability_labels(payload: dict[str, Any]) -> dict[str, str]:
    labels: dict[str, str] = {}
    row_counts = payload.get("row_counts")
    if isinstance(row_counts, dict):
        timeframes = sorted((str(key) for key in row_counts if str(key)), key=timeframe_sort_key)
        if len(timeframes) == 1:
            labels["timeframe"] = timeframes[0]
        elif timeframes:
            labels["timeframes"] = "/".join(timeframes)

    selected_windows = payload.get("selected_windows")
    if isinstance(selected_windows, dict):
        window_parts: list[str] = []
        for timeframe in sorted((str(key) for key in selected_windows if str(key)), key=timeframe_sort_key):
            value = selected_windows.get(timeframe)
            if isinstance(value, str) and value:
                window_parts.append(f"{timeframe}={value}")
        if window_parts:
            labels["window"] = ";".join(window_parts)
    return labels


def cost_stress_row_portability_labels(payload: dict[str, Any]) -> dict[str, str]:
    rows = payload.get("cost_stress_rows")
    if not isinstance(rows, list):
        return {}

    symbols: list[str] = []
    timeframes: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        label = row.get("label")
        if not isinstance(label, str) or "/" not in label:
            continue
        parts = [part.strip() for part in label.split("/") if part.strip()]
        if parts and looks_like_symbol(parts[0]) and parts[0] not in symbols:
            symbols.append(parts[0])
        if len(parts) >= 2 and is_timeframe(parts[1]) and parts[1] not in timeframes:
            timeframes.append(parts[1])

    labels: dict[str, str] = {}
    if len(symbols) == 1:
        labels["symbol"] = symbols[0]
    elif symbols:
        labels["symbols"] = "/".join(symbols)
    if "timeframes" not in labels and "timeframe" not in labels:
        ordered_timeframes = sorted(timeframes, key=timeframe_sort_key)
        if len(ordered_timeframes) == 1:
            labels["timeframe"] = ordered_timeframes[0]
        elif ordered_timeframes:
            labels["timeframes"] = "/".join(ordered_timeframes)
    return labels


def provider_rows_portability_labels(payload: dict[str, Any]) -> dict[str, str]:
    rows = payload.get("provider_rows")
    if not isinstance(rows, list):
        return {}

    values_by_key: dict[str, list[str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        for key in PORTABILITY_LABEL_KEYS:
            value = row.get(key)
            if not isinstance(value, str) or not value:
                continue
            values = values_by_key.setdefault(key, [])
            if value not in values:
                values.append(value)

    labels: dict[str, str] = {}
    for key, values in values_by_key.items():
        if not values:
            continue
        if len(values) == 1:
            labels[key] = values[0]
            continue
        if key == "symbol":
            labels["symbols"] = "/".join(values)
        elif key == "timeframe":
            labels["timeframes"] = "/".join(values)
        else:
            labels[key] = "/".join(values)
    return labels


def canonical_root_violations(canonical_branch_path: str) -> list[str]:
    parts = split_path(canonical_branch_path)
    if not parts:
        return ["missing_known_main_regime"]
    if parts[0] not in KNOWN_MAIN_REGIMES:
        return [f"non_main_regime_root:{parts[0]}"]
    return []


def full_rooted_identity_path(labels: dict[str, str], canonical_branch_path: str) -> str:
    """Return audit identity with provenance labels prefixed to the canonical tree."""

    prefix: list[str] = []
    seen: set[str] = set()
    for key in FULL_IDENTITY_LABEL_ORDER:
        value = labels.get(key)
        if isinstance(value, str) and value and value not in seen:
            prefix.append(value)
            seen.add(value)
    if canonical_branch_path:
        prefix.append(canonical_branch_path)
    return " -> ".join(prefix)


def normalize_branch_path(path: str | None, labels: dict[str, str] | None = None) -> dict[str, Any]:
    parts = split_path(path or "")
    supplied_labels = dict(labels or {})
    warnings: list[str] = []

    regime_index = first_regime_index(parts)
    if regime_index is None:
        canonical = ""
        main_regime = None
        if parts and not is_provider_label(parts[0]) and parts[0] not in KNOWN_MARKET_LABELS and not is_timeframe(parts[0]):
            canonical = " -> ".join(parts)
            main_regime = parts[0]
        violations = canonical_root_violations(canonical)
        return {
            "original_branch_path": path or "",
            "canonical_branch_path": canonical,
            "full_rooted_identity_path": full_rooted_identity_path(supplied_labels, canonical),
            "labels": supplied_labels,
            "main_regime": main_regime,
            "was_normalized": False,
            "canonical_root_ok": False,
            "violations": violations,
            "warnings": violations,
        }

    prefix = parts[:regime_index]
    extracted_labels = labels_from_prefix(prefix)
    merged_labels = {**supplied_labels, **extracted_labels}
    canonical_parts = parts[regime_index:]
    canonical = " -> ".join(canonical_parts)

    if prefix and "legacy_prefix_removed" not in warnings:
        warnings.append("legacy_prefix_removed_to_labels")
    violations = canonical_root_violations(canonical)

    return {
        "original_branch_path": path or "",
        "canonical_branch_path": canonical,
        "full_rooted_identity_path": full_rooted_identity_path(merged_labels, canonical),
        "labels": merged_labels,
        "main_regime": canonical_parts[0],
        "was_normalized": bool(prefix),
        "canonical_root_ok": not violations,
        "violations": violations,
        "warnings": warnings,
    }


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def metrics_branch_path(payload: dict[str, Any]) -> str:
    for key in (
        "branch_path",
        "regime_profit_branch_path",
        "rooted_branch_path",
        "branch_path_template",
    ):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    branch_paths = payload.get("branch_paths")
    if isinstance(branch_paths, list):
        for value in branch_paths:
            if isinstance(value, str) and value:
                return value
    return ""


def normalize_metrics_file(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    branch_path = metrics_branch_path(payload)
    labels = extract_portability_labels(payload)
    normalized = normalize_branch_path(str(branch_path or ""), labels)
    return {
        "file": str(path),
        "decision": payload.get("decision"),
        "promotion_allowed": payload.get("promotion_allowed"),
        "trade_usable": payload.get("trade_usable"),
        **normalized,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path, help="JSON metric files to audit")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    reports = [normalize_metrics_file(path) for path in args.files]
    print(json.dumps(reports, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
