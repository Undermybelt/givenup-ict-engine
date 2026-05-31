#!/usr/bin/env python3
"""Find futures candidates wrongly killed by fixed bps cost stress.

This is a read-only rehearing tool for historical Gate-1/AQ packets that used
``5bps/side`` or ``10bps`` as if it were the futures commission model. It does
not promote anything by itself. It separates three cases:

* ``bps_stress_false_negative_recheck``: profitable after verified
  per-contract all-in futures cost, but negative under the old fixed bps stress.
* ``zero_edge_churn_not_rescued_by_realistic_cost``: positive gross, but still
  negative after realistic futures all-in cost.
* ``cost_model_unverified``: cannot rehear until the exact futures cost model is
  verified.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import instrument_cost_model as cost_model


ARTIFACT_GLOBS = (
    "terminal_metrics.json",
    "terminal_summary.json",
    "terminal_gate_summary.json",
    "fee_rescue_judgment_ledger.json",
    "exact_replay_rescue_queue.json",
    "*rescue_queue.json",
    "*judgment_ledger.json",
    "*judgment_ledger.csv",
    "*rescued_for_exact_replay.csv",
    "*blocked_after_fee_rejudgment.csv",
    "*fee_cleared_but_blocked_queue.csv",
    "*needs_reprice_replay*.csv",
    "*needs_eth_full_session_replay*.csv",
    "*gate.json",
    "autoquant_clean_*_rows.csv",
    "screen_rows.csv",
    "highfreq_*_rows.csv",
    "*leaderboard.csv",
)
ROW_CONTAINER_KEYS = (
    "rows",
    "cost_row",
    "cost_rows",
    "cost_stress",
    "cost_stress_rows",
    "selected_gate1_row",
    "top_by_instrument_cost",
    "top_by_cost",
    "top_rows",
    "rank_rows",
    "full_window",
    "train_window",
    "oos_window",
    "raw_realistic_cost_survivors_before_session_scope",
    "realistic_cost_survivors_before_gate1",
    "raw_cost_stress_survivors_5bps_before_session_scope",
    "exact_replay_queue",
    "rescued_for_exact_replay",
    "rescued_for_exact_aq",
    "blocked_after_fee_rejudgment",
    "fee_cleared_but_blocked",
    "fee_cleared_but_blocked_queue",
    "needs_reprice_replay",
    "needs_eth_full_session_replay",
    "all_deduped_judgments",
)
GROSS_PCT_KEYS = (
    "raw_total_profit_pct",
    "raw_total_ret_pct",
    "total_profit_pct",
    "gross_total_profit_pct",
    "gross_total_pct",
    "raw_profit_pct",
    "profit_pct",
    "best_raw_total_profit_pct",
)
LEGACY_WALL_NET_PCT_KEYS = (
    "5bps_per_side_total_profit_pct",
    "net5bps_total_ret_pct",
    "net_5bps_total_pct",
    "net_after_5bps_side_pct",
    "net_after_5bps_per_side_pct",
    "stress_5bps_total_pct",
    "cost_5bps_side_pct",
    "five_bps_per_side_pct",
)
LEGACY_WALL_NET_PCT_KEY_RE = re.compile(
    r"^(?:net_|net_after_|stress_)?(?P<bps>\d+(?:\.\d+)?)bps(?:_per_side|_side)?(?:_total)?(?:_profit|_ret)?_pct$"
)
TRADE_COUNT_KEYS = (
    "trade_count",
    "trades",
    "n_distinct_trades",
    "rank_total_trade_count",
)
TRADES_PER_DAY_KEYS = (
    "trades_per_day",
    "trades_per_session",
    "trade_density_per_day",
    "density_trades_per_day",
)
PRICE_KEYS = (
    "representative_entry_price",
    "representative_price",
    "last_close",
    "entry_price",
    "avg_entry_price",
    "close",
)
DEFAULT_REPRESENTATIVE_PRICE = {
    "ES": 5200.0,
    "MES": 5200.0,
    "NQ": 15000.0,
    "MNQ": 15000.0,
    "YM": 39000.0,
    "MYM": 39000.0,
    "RTY": 2200.0,
    "M2K": 2200.0,
    "GC": 2300.0,
    "MGC": 2300.0,
    "XAU": 2300.0,
    "SI": 30.0,
    "SIL": 30.0,
    "HG": 4.5,
    "CL": 75.0,
    "MCL": 75.0,
    "NG": 3.0,
    "ZN": 110.0,
    "ZB": 120.0,
    "ZF": 105.0,
    "ZC": 450.0,
    "ZS": 1200.0,
    "ZW": 550.0,
    "LE": 185.0,
    "6E": 1.08,
    "M6E": 1.08,
    "BRE": 1.08,
}
DEFAULT_LEGACY_WALL_BASIS_POINTS_PER_SIDE = 5.0
FALSE_NEGATIVE_CLASSIFICATION = "bps_stress_false_negative_recheck"


@dataclass(frozen=True)
class LegacyWallNet:
    total_pct: float
    basis_points_per_side: float
    source_key: str


def _safe_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        parsed = float(str(value).strip().replace(",", ""))
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def _safe_int(value: Any) -> int | None:
    parsed = _safe_float(value)
    if parsed is None:
        return None
    return int(parsed)


def _safe_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y"}:
            return True
        if normalized in {"0", "false", "no", "n"}:
            return False
    if isinstance(value, (int, float)):
        return value != 0
    return None


def _first_number(row: dict[str, Any], keys: Iterable[str]) -> float | None:
    for key in keys:
        value = _safe_float(row.get(key))
        if value is not None:
            return value
    return None


def _legacy_wall_net_for_row(
    row: dict[str, Any],
    *,
    default_basis_points_per_side: float = DEFAULT_LEGACY_WALL_BASIS_POINTS_PER_SIDE,
) -> LegacyWallNet | None:
    for key in LEGACY_WALL_NET_PCT_KEYS:
        value = _safe_float(row.get(key))
        if value is not None:
            bps = _legacy_wall_bps_from_key(key, default_basis_points_per_side=default_basis_points_per_side)
            return LegacyWallNet(value, bps, key)
    dynamic: list[LegacyWallNet] = []
    for key, raw_value in row.items():
        match = LEGACY_WALL_NET_PCT_KEY_RE.match(str(key))
        if match is None:
            continue
        value = _safe_float(raw_value)
        if value is None:
            continue
        bps = float(match.group("bps"))
        if bps <= 0.0:
            continue
        dynamic.append(LegacyWallNet(value, bps, str(key)))
    if not dynamic:
        return None
    negative = [item for item in dynamic if item.total_pct <= 0.0]
    if negative:
        return sorted(negative, key=lambda item: (-item.basis_points_per_side, item.source_key))[0]
    return sorted(dynamic, key=lambda item: (item.total_pct, -item.basis_points_per_side, item.source_key))[0]


def _legacy_wall_bps_from_key(key: str, *, default_basis_points_per_side: float) -> float:
    match = re.search(r"(\d+(?:\.\d+)?)bps", key)
    if match is None:
        return float(default_basis_points_per_side)
    return float(match.group(1))


def _row_label(row: dict[str, Any], path: Path) -> str:
    for key in ("label", "factor_id", "strategy_id", "package_id", "strategy_name", "symbol", "pair"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return path.stem


def _row_text(row: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in (
        "label",
        "factor_id",
        "strategy_id",
        "package_id",
        "strategy_name",
        "symbol",
        "pair",
        "contract",
        "root",
        "branch_path",
        "cost_profile_id",
        "market_product_symbol_origin_tf",
    ):
        value = row.get(key)
        if isinstance(value, str) and value:
            parts.append(value)
    return " ".join(parts)


def _root_from_token_text(text: str) -> str | None:
    upper = text.upper().strip()
    if not upper:
        return None
    tokens = [token for token in re.split(r"[^A-Z0-9]+", upper) if token]
    compact = "".join(ch for ch in upper if ch.isalnum())
    if compact:
        tokens.append(compact)
    for root in sorted(cost_model.FUTURES_COST_PROFILES.keys(), key=len, reverse=True):
        for token in tokens:
            if token == root:
                return root
            if not token.startswith(root):
                continue
            suffix = token[len(root):]
            if not suffix:
                return root
            if suffix.startswith("USD") or suffix[0].isdigit():
                return root
            if suffix[0] in "FGHJKMNQUVXZ" and suffix[1:].isdigit():
                return root
    return None


def futures_root_for_row(row: dict[str, Any]) -> str | None:
    for key in ("symbol", "root", "contract", "pair"):
        value = row.get(key)
        if isinstance(value, str) and cost_model.futures_cost_profile(value) is not None:
            return cost_model.normalize_futures_root(value)
    return _root_from_token_text(_row_text(row))


def trade_count_for_row(row: dict[str, Any]) -> int | None:
    for key in TRADE_COUNT_KEYS:
        value = _safe_int(row.get(key))
        if value is not None:
            return value
    return None


def trades_per_day_for_row(row: dict[str, Any]) -> float | None:
    for key in TRADES_PER_DAY_KEYS:
        value = _safe_float(row.get(key))
        if value is not None:
            return value
    return None


def _density_target_1_to_3_per_day(row: dict[str, Any]) -> bool | None:
    for key in ("density_target_1_to_3_per_day", "density_floor_met"):
        value = _safe_bool(row.get(key))
        if value is not None:
            return value
    return None


def _year_coverage_ok(row: dict[str, Any]) -> bool | None:
    for key in ("year_coverage_ok", "positive_year_coverage_met", "year_stability_met"):
        value = _safe_bool(row.get(key))
        if value is not None:
            return value
    positive_years = _safe_int(row.get("positive_years") or row.get("positive_year_count"))
    years = _safe_int(row.get("years") or row.get("year_count") or row.get("total_years"))
    if positive_years is None or years is None:
        return None
    if years >= 5:
        return positive_years >= 3
    return positive_years >= max(1, years - 1)


def _session_gate_fields(row: dict[str, Any], trades: int | None) -> dict[str, Any]:
    trades_per_day = trades_per_day_for_row(row)
    density_ok = _density_target_1_to_3_per_day(row)
    minimum_trade_sample_floor_met = _safe_bool(row.get("minimum_trade_sample_floor_met"))
    if minimum_trade_sample_floor_met is None and trades is not None:
        minimum_trade_sample_floor_met = trades >= 30
    return {
        "factor_id": row.get("factor_id") or row.get("strategy_id") or row.get("package_id") or row.get("label"),
        "branch_path": row.get("branch_path") or row.get("regime_profit_branch_path") or row.get("rooted_branch_path"),
        "timeframe": row.get("timeframe") or row.get("base_timeframe") or row.get("tf"),
        "side": row.get("side") or row.get("direction"),
        "variant": row.get("variant") or row.get("variant_id") or row.get("params_label"),
        "session_scope": row.get("session_scope") or row.get("session") or row.get("data_session_scope"),
        "rth_filter_applied": _safe_bool(row.get("rth_filter_applied")),
        "outside_rth_rows": _safe_int(row.get("outside_rth_rows")),
        "eth_full_retained_session_evidence": _safe_bool(row.get("eth_full_retained_session_evidence")),
        "minimum_trade_sample_floor_met": minimum_trade_sample_floor_met,
        "trades_per_day": trades_per_day,
        "density_target_1_to_3_per_day": density_ok,
        "density_floor_met": _safe_bool(row.get("density_floor_met")) if row.get("density_floor_met") is not None else density_ok,
        "positive_years": _safe_int(row.get("positive_years") or row.get("positive_year_count")),
        "years": _safe_int(row.get("years") or row.get("year_count") or row.get("total_years")),
        "year_coverage_ok": _year_coverage_ok(row),
    }


def _compact_optional_fields(fields: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in fields.items() if value is not None and value != ""}


def gross_pct_for_row(row: dict[str, Any], *, legacy_wall_basis_points_per_side: float) -> float | None:
    gross = _first_number(row, GROSS_PCT_KEYS)
    if gross is not None:
        return gross
    stress_net = _legacy_wall_net_for_row(
        row,
        default_basis_points_per_side=legacy_wall_basis_points_per_side,
    )
    trades = trade_count_for_row(row)
    if stress_net is not None and trades is not None:
        return stress_net.total_pct + trades * legacy_wall_round_turn_pct(stress_net.basis_points_per_side)
    return None


def representative_price_for_root(row: dict[str, Any], root: str) -> float:
    price = _first_number(row, PRICE_KEYS)
    if price is not None and price > 0:
        return price
    return DEFAULT_REPRESENTATIVE_PRICE[root]


def legacy_wall_round_turn_pct(legacy_wall_basis_points_per_side: float) -> float:
    return float(legacy_wall_basis_points_per_side) * 2.0 * 0.01


def _cost_status_verified(profile: cost_model.FuturesCostProfile | None) -> bool:
    return bool(profile and profile.verified_for_promotion)


def classify_row(
    row: dict[str, Any],
    *,
    source_file: Path,
    legacy_wall_basis_points_per_side: float = DEFAULT_LEGACY_WALL_BASIS_POINTS_PER_SIDE,
) -> dict[str, Any] | None:
    root = futures_root_for_row(row)
    if root is None:
        return None
    trades = trade_count_for_row(row)
    gross_pct = gross_pct_for_row(row, legacy_wall_basis_points_per_side=legacy_wall_basis_points_per_side)
    label = _row_label(row, source_file)
    carried_fields = _compact_optional_fields(_session_gate_fields(row, trades))
    profile = cost_model.futures_cost_profile(root)
    if trades is None or trades <= 0 or gross_pct is None:
        return {
            "label": label,
            "source_file": str(source_file),
            "symbol_root": root,
            **carried_fields,
            "classification": "insufficient_trade_or_gross_data",
            "trade_count": trades,
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
        }
    if profile is None or not _cost_status_verified(profile):
        return {
            "label": label,
            "source_file": str(source_file),
            "symbol_root": root,
            **carried_fields,
            "classification": "cost_model_unverified",
            "trade_count": trades,
            "gross_total_profit_pct": round(gross_pct, 6),
            "gross_edge_bps_per_trade": round(gross_pct / trades * 100.0, 6),
            "cost_model_status": profile.status if profile else cost_model.STATUS_UNVERIFIED,
            "cost_profile_id": profile.profile_id if profile else "unknown",
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
        }

    representative_price = representative_price_for_root(row, root)
    legacy_wall_net = _legacy_wall_net_for_row(
        row,
        default_basis_points_per_side=legacy_wall_basis_points_per_side,
    )
    effective_legacy_wall_basis_points_per_side = (
        legacy_wall_net.basis_points_per_side if legacy_wall_net is not None else legacy_wall_basis_points_per_side
    )
    fee_pct = profile.round_trip_fee_pct(representative_price)
    all_in_pct = profile.round_trip_cost_pct(representative_price)
    legacy_wall_pct = legacy_wall_round_turn_pct(effective_legacy_wall_basis_points_per_side)
    legacy_wall_total_pct = legacy_wall_net.total_pct if legacy_wall_net is not None else gross_pct - trades * legacy_wall_pct
    fee_only_total_pct = gross_pct - trades * fee_pct
    all_in_total_pct = gross_pct - trades * all_in_pct
    gross_edge_bps = gross_pct / trades * 100.0
    all_in_bps = all_in_pct * 100.0
    legacy_wall_round_turn_bps = legacy_wall_pct * 100.0

    if gross_pct <= 0:
        classification = "gross_negative_not_cost_rescuable"
    elif all_in_total_pct <= 0:
        classification = "zero_edge_churn_not_rescued_by_realistic_cost"
    elif legacy_wall_total_pct <= 0:
        classification = "bps_stress_false_negative_recheck"
    elif gross_edge_bps >= legacy_wall_round_turn_bps and trades <= 800:
        classification = "large_move_low_turnover_cost_negligible"
    else:
        classification = "realistic_cost_survivor"

    return {
        "label": label,
        "source_file": str(source_file),
        "symbol_root": root,
        **carried_fields,
        "classification": classification,
        "trade_count": trades,
        "representative_price": representative_price,
        "gross_total_profit_pct": round(gross_pct, 6),
        "gross_edge_bps_per_trade": round(gross_edge_bps, 6),
        "legacy_wall_total_profit_pct": round(legacy_wall_total_pct, 6),
        "legacy_wall_basis_points_per_side": round(effective_legacy_wall_basis_points_per_side, 6),
        "legacy_wall_source_key": legacy_wall_net.source_key if legacy_wall_net is not None else "computed_default_wall",
        "instrument_fee_only_total_profit_pct": round(fee_only_total_pct, 6),
        "instrument_all_in_total_profit_pct": round(all_in_total_pct, 6),
        "instrument_fee_only_bps_per_trade": round(fee_pct * 100.0, 6),
        "instrument_all_in_bps_per_trade": round(all_in_bps, 6),
        "legacy_wall_round_turn_basis_points_per_trade": round(legacy_wall_round_turn_bps, 6),
        "cost_profile_id": profile.profile_id,
        "cost_model_status": profile.status,
        "legacy_wall_role": "historical_fixed_bps_wall_not_futures_cost_authority",
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }


def _looks_like_candidate_row(row: dict[str, Any]) -> bool:
    has_trade = any(key in row for key in TRADE_COUNT_KEYS)
    has_economics = any(key in row for key in (*GROSS_PCT_KEYS, *LEGACY_WALL_NET_PCT_KEYS)) or _legacy_wall_net_for_row(row) is not None
    return has_trade and has_economics and futures_root_for_row(row) is not None


def _inherit_context(row: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    inherited = dict(context)
    for key in (
        "symbol",
        "root",
        "contract",
        "pair",
        "factor_id",
        "strategy_id",
        "package_id",
        "label",
        "strategy_name",
        "branch_path",
        "market_product_symbol_origin_tf",
    ):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            inherited[key] = value
    return inherited


def iter_rows(payload: Any, context: dict[str, Any] | None = None) -> Iterable[dict[str, Any]]:
    context = context or {}
    if isinstance(payload, dict):
        row_context = _inherit_context(payload, context)
        merged = {**row_context, **payload}
        if _looks_like_candidate_row(merged):
            yield merged
        for key in ROW_CONTAINER_KEYS:
            value = payload.get(key)
            if isinstance(value, dict):
                yield from iter_rows(value, row_context)
            elif isinstance(value, list):
                for item in value:
                    yield from iter_rows(item, row_context)
    elif isinstance(payload, list):
        for item in payload:
            yield from iter_rows(item, context)


def artifact_files(paths: list[Path], *, max_files: int | None = None) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file():
            files.append(path)
            continue
        if not path.is_dir():
            continue
        seen = set(files)
        for pattern in ARTIFACT_GLOBS:
            for found in sorted(path.rglob(pattern)):
                if found not in seen:
                    files.append(found)
                    seen.add(found)
                if max_files is not None and len(files) >= max_files:
                    return files
    return files[:max_files] if max_files is not None else files


def audit_files(
    files: list[Path],
    *,
    legacy_wall_basis_points_per_side: float = DEFAULT_LEGACY_WALL_BASIS_POINTS_PER_SIDE,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    read_errors: list[dict[str, str]] = []
    seen: set[tuple[str, str, int, float]] = set()
    for path in files:
        if path.suffix.lower() == ".csv":
            try:
                with path.open(newline="", encoding="utf-8") as handle:
                    candidate_rows = list(csv.DictReader(handle))
            except Exception as exc:  # noqa: BLE001 - audit should keep scanning other files.
                read_errors.append({"file": str(path), "error": str(exc)})
                continue
        else:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001 - audit should keep scanning other files.
                read_errors.append({"file": str(path), "error": str(exc)})
                continue
            candidate_rows = list(iter_rows(payload))
        for row in candidate_rows:
            classified = classify_row(
                row,
                source_file=path,
                legacy_wall_basis_points_per_side=legacy_wall_basis_points_per_side,
            )
            if classified is None:
                continue
            key = (
                classified["source_file"],
                classified["label"],
                int(classified.get("trade_count") or 0),
                float(classified.get("gross_total_profit_pct") or 0.0),
            )
            if key in seen:
                continue
            seen.add(key)
            rows.append(classified)
    rows.sort(
        key=lambda item: (
            item["classification"] != "bps_stress_false_negative_recheck",
            -float(item.get("instrument_all_in_total_profit_pct") or -1e12),
            -float(item.get("gross_edge_bps_per_trade") or -1e12),
        )
    )
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1
    unique_revival_candidates = unique_false_negative_candidates(rows)
    return {
        "schema_version": "futures-bps-false-negative-revival/v1",
        "artifact_files_scanned": len(files),
        "candidate_rows_classified": len(rows),
        "classification_counts": counts,
        "revival_recheck_count": counts.get(FALSE_NEGATIVE_CLASSIFICATION, 0),
        "unique_revival_recheck_count": len(unique_revival_candidates),
        "revival_recheck_candidates": [
            row for row in rows if row["classification"] == FALSE_NEGATIVE_CLASSIFICATION
        ],
        "unique_revival_recheck_candidates": unique_revival_candidates,
        "zero_edge_churn_count": counts.get("zero_edge_churn_not_rescued_by_realistic_cost", 0),
        "cost_model_unverified_count": counts.get("cost_model_unverified", 0),
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "rows": rows,
        "read_errors": read_errors,
    }


def unique_false_negative_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        if row.get("classification") != FALSE_NEGATIVE_CLASSIFICATION:
            continue
        grouped.setdefault(_false_negative_identity(row), []).append(row)

    unique_rows: list[dict[str, Any]] = []
    for group_rows in grouped.values():
        group_rows = sorted(group_rows, key=_false_negative_row_sort_key)
        selected = dict(group_rows[0])
        sources: list[str] = []
        for row in group_rows:
            source = str(row.get("source_file") or "")
            if source and source not in sources:
                sources.append(source)
        selected["duplicate_source_count"] = len(group_rows)
        selected["source_examples"] = " | ".join(sources[:4])
        selected["promotion_allowed"] = False
        selected["trade_usable"] = False
        selected["update_goal"] = False
        unique_rows.append(selected)

    return sorted(
        unique_rows,
        key=lambda row: (
            -float(row.get("instrument_all_in_total_profit_pct") or -1e12),
            -float(row.get("gross_edge_bps_per_trade") or -1e12),
            str(row.get("label") or ""),
        ),
    )


def _false_negative_identity(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("label"),
        row.get("symbol_root"),
        row.get("factor_id"),
        row.get("timeframe"),
        row.get("side"),
        row.get("variant"),
        row.get("trade_count"),
        row.get("gross_total_profit_pct"),
        row.get("legacy_wall_total_profit_pct"),
        row.get("instrument_all_in_total_profit_pct"),
    )


def _false_negative_row_sort_key(row: dict[str, Any]) -> tuple[int, str]:
    source = str(row.get("source_file") or "")
    # Prefer terminal packets over duplicate material CSV rows when both exist.
    priority = 0 if source.endswith("terminal_metrics.json") or source.endswith("terminal_summary.json") else 1
    return (priority, source)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="JSON files or directories to scan")
    parser.add_argument("--legacy-wall-basis-points-per-side", type=float, default=DEFAULT_LEGACY_WALL_BASIS_POINTS_PER_SIDE)
    parser.add_argument("--max-files", type=int, default=None)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-csv", type=Path)
    parser.add_argument("--output-unique-csv", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    files = artifact_files(args.paths, max_files=args.max_files)
    report = audit_files(files, legacy_wall_basis_points_per_side=args.legacy_wall_basis_points_per_side)
    text = json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None) + "\n"
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(text, encoding="utf-8")
    if args.output_csv:
        write_csv(args.output_csv, report["rows"])
    if args.output_unique_csv:
        write_csv(args.output_unique_csv, report["unique_revival_recheck_candidates"])
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
