#!/usr/bin/env python3
"""Audit futures rows rejected by blanket bps stress but alive under real costs.

This helper is deliberately read-only. It does not promote a strategy, launch
AutoQuant, or mark anything trade usable. Its job is narrower: normalize legacy
Gate-1 rows into a small rescue queue so futures candidates killed only by a
blanket ``fixed-cost`` stress can be replayed with the verified per-contract
instrument-cost model.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import instrument_cost_model as cost_model


@dataclass(frozen=True)
class RescueRow:
    factor_id: str
    branch_path: str | None
    symbol: str | None
    timeframe: str | None
    side: str | None
    variant: str | None
    trade_count: int
    source_path: str
    source_table: str
    source_index: int
    instrument_cost_total_pct: float | None
    legacy_fixed_cost_total_pct: float | None
    gross_total_pct: float | None
    profit_factor: float | None
    win_rate: float | None
    avg_net_bps: float | None
    positive_years: int | None
    years: int | None
    survives_instrument_cost: bool
    survives_legacy_fixed_cost: bool
    session_scope: str | None
    rth_filter_applied: bool | None
    eth_full_retained_session_evidence: bool
    minimum_trade_sample_floor_met: bool
    density_target_1_to_3_per_day: bool
    reason_codes: list[str]
    rescue_class: str
    promotion_allowed: bool = False
    trade_usable: bool = False
    update_goal: bool = False


def normalize_row(row: dict[str, Any], source_path: str, source_table: str, source_index: int) -> RescueRow | None:
    """Normalize one artifact row into a futures real-cost rescue verdict."""
    factor_id = _first_text(
        row,
        "factor_id",
        "strategy_id",
        "package_id",
        "label",
        "id",
    )
    symbol = _first_text(row, "symbol", "root", "contract", "pair")
    timeframe = _first_text(row, "timeframe", "base_timeframe", "tf")
    side = _first_text(row, "side", "direction")
    variant = _first_text(row, "variant", "variant_id", "params_label")
    trade_count = _intish(_first_present(row, "trade_count", "trades", "n_trades")) or 0

    if not factor_id and not symbol:
        return None
    factor_id = factor_id or str(symbol)

    instrument_cost_total_pct = _first_float(
        row,
        "instrument_cost_total_profit_pct",
        "instrument_cost_total_ret_pct",
        "instrument_cost_total_pct",
        "net_after_instrument_cost_pct",
        "real_cost_total_profit_pct",
        "current_fee_total_profit_pct",
    )
    legacy_fixed_cost_total_pct = _first_float(
        row,
        "5bps_per_side_total_profit_pct",
        "legacy_fixed_cost_total_pct",
        "stress_5bps_total_pct",
        "net_after_5bps_side_pct",
        "net_after_5bps_per_side_pct",
        "legacy_5bps_total_profit_pct",
        "cost_5bps_side_pct",
    )
    gross_total_pct = _first_float(
        row,
        "gross_total_profit_pct",
        "raw_total_profit_pct",
        "0bps_per_side_total_profit_pct",
        "total_profit_pct",
    )
    legacy_reprice_realistic_cost_survival = _legacy_reprice_realistic_cost_survival(
        row,
        symbol=symbol,
        trade_count=trade_count,
        gross_total_pct=gross_total_pct,
    )

    if instrument_cost_total_pct is not None:
        survives_instrument_cost = instrument_cost_total_pct > 0.0
    else:
        survives_instrument_cost = _truthy(row.get("survives_instrument_cost"))
    if legacy_fixed_cost_total_pct is not None:
        survives_legacy_fixed_cost = legacy_fixed_cost_total_pct > 0.0
    else:
        survives_legacy_fixed_cost = _truthy(row.get("survives_5bps_per_side")) or _truthy(
            row.get("survives_5bps_density")
        )

    session_scope = _first_text(row, "session_scope", "session", "data_session_scope")
    rth_filter_applied = _boolish(row.get("rth_filter_applied"))
    eth_evidence = _truthy(row.get("eth_full_retained_session_evidence")) or _session_scope_is_eth(session_scope)
    sample_floor = _truthy(row.get("minimum_trade_sample_floor_met")) or trade_count >= 30
    density_ok = _truthy(row.get("density_target_1_to_3_per_day")) or _truthy(row.get("density_floor_met"))
    positive_years = _intish(_first_present(row, "positive_years", "positive_year_count"))
    years = _intish(_first_present(row, "years", "year_count", "total_years"))
    year_coverage_ok = _year_coverage_ok(positive_years, years, row)
    reason_codes = _reason_codes(
        instrument_cost_total_pct=instrument_cost_total_pct,
        legacy_fixed_cost_total_pct=legacy_fixed_cost_total_pct,
        survives_instrument_cost=survives_instrument_cost,
        survives_legacy_fixed_cost=survives_legacy_fixed_cost,
        trade_count=trade_count,
        eth_evidence=eth_evidence,
        rth_filter_applied=rth_filter_applied,
        sample_floor=sample_floor,
        density_ok=density_ok,
        year_coverage_ok=year_coverage_ok,
        legacy_reprice_realistic_cost_survival=legacy_reprice_realistic_cost_survival,
    )

    rescue_class = _classify_rescue(
        gross_total_pct=gross_total_pct,
        instrument_cost_total_pct=instrument_cost_total_pct,
        legacy_fixed_cost_total_pct=legacy_fixed_cost_total_pct,
        survives_instrument_cost=survives_instrument_cost,
        survives_legacy_fixed_cost=survives_legacy_fixed_cost,
        trade_count=trade_count,
        eth_evidence=eth_evidence,
        rth_filter_applied=rth_filter_applied,
        sample_floor=sample_floor,
        density_ok=density_ok,
        year_coverage_ok=year_coverage_ok,
        legacy_reprice_realistic_cost_survival=legacy_reprice_realistic_cost_survival,
    )

    return RescueRow(
        factor_id=str(factor_id),
        branch_path=_first_text(row, "branch_path", "regime_profit_branch_path", "rooted_branch_path"),
        symbol=symbol,
        timeframe=timeframe,
        side=side,
        variant=variant,
        trade_count=trade_count,
        source_path=source_path,
        source_table=source_table,
        source_index=source_index,
        instrument_cost_total_pct=instrument_cost_total_pct,
        legacy_fixed_cost_total_pct=legacy_fixed_cost_total_pct,
        gross_total_pct=gross_total_pct,
        profit_factor=_first_float(row, "instrument_cost_profit_factor", "profit_factor", "pf"),
        win_rate=_first_float(row, "win_rate", "win_rate_pct"),
        avg_net_bps=_first_float(row, "avg_net_bps", "average_net_bps", "avg_trade_net_bps"),
        positive_years=positive_years,
        years=years,
        survives_instrument_cost=survives_instrument_cost,
        survives_legacy_fixed_cost=survives_legacy_fixed_cost,
        session_scope=session_scope,
        rth_filter_applied=rth_filter_applied,
        eth_full_retained_session_evidence=eth_evidence,
        minimum_trade_sample_floor_met=sample_floor,
        density_target_1_to_3_per_day=density_ok,
        reason_codes=reason_codes,
        rescue_class=rescue_class,
    )


def build_report(
    sources: Iterable[Path],
    *,
    report_path: Path | None = None,
    csv_path: Path | None = None,
) -> dict[str, Any]:
    """Build and optionally write a compact real-cost rescue report."""
    rows = _dedupe_best(_iter_normalized_rows(sources))
    rescued = [row for row in rows if row.rescue_class == "rescued_for_exact_aq"]
    fee_cleared_but_blocked = [row for row in rows if row.rescue_class == "fee_cleared_but_blocked_non_cost"]
    replay = [row for row in rows if row.rescue_class == "needs_reprice_replay"]
    eth_replay = [row for row in rows if row.rescue_class == "needs_eth_full_session_replay"]
    already_stress_alive = [row for row in rows if row.rescue_class == "already_survives_legacy_fixed_cost"]
    not_rescued = [row for row in rows if row.rescue_class.startswith("not_rescued")]
    known_classes = {
        "rescued_for_exact_aq",
        "fee_cleared_but_blocked_non_cost",
        "needs_reprice_replay",
        "needs_eth_full_session_replay",
        "already_survives_legacy_fixed_cost",
    }
    other = [row for row in rows if row.rescue_class not in known_classes and not row.rescue_class.startswith("not_rescued")]
    class_counts: dict[str, int] = {}
    for row in rows:
        class_counts[row.rescue_class] = class_counts.get(row.rescue_class, 0) + 1

    report = {
        "schema_version": "futures-real-cost-rescue-audit/v1",
        "inputs": [str(path) for path in sources],
        "row_count": len(rows),
        "class_counts": dict(sorted(class_counts.items())),
        "strict_rescue_count": len(rescued),
        "fee_cleared_but_blocked_count": len(fee_cleared_but_blocked),
        "needs_reprice_replay_count": len(replay),
        "needs_eth_full_session_replay_count": len(eth_replay),
        "already_survives_legacy_fixed_cost_count": len(already_stress_alive),
        "not_rescued_count": len(not_rescued),
        "other_class_count": len(other),
        "rescued_for_exact_aq": [asdict(row) for row in rescued],
        "fee_cleared_but_blocked": [asdict(row) for row in fee_cleared_but_blocked],
        "needs_reprice_replay": [asdict(row) for row in replay],
        "needs_eth_full_session_replay": [asdict(row) for row in eth_replay],
        "already_survives_legacy_fixed_cost": [asdict(row) for row in already_stress_alive],
        "not_rescued": [asdict(row) for row in not_rescued],
        "other_classes": [asdict(row) for row in other],
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if csv_path is not None:
        _write_rows_csv(csv_path, rescued)
    return report


def _classify_rescue(
    *,
    gross_total_pct: float | None,
    instrument_cost_total_pct: float | None,
    legacy_fixed_cost_total_pct: float | None,
    survives_instrument_cost: bool,
    survives_legacy_fixed_cost: bool,
    trade_count: int,
    eth_evidence: bool,
    rth_filter_applied: bool | None,
    sample_floor: bool,
    density_ok: bool,
    year_coverage_ok: bool,
    legacy_reprice_realistic_cost_survival: bool | None,
) -> str:
    if trade_count <= 0:
        return "not_rescued_zero_trades"
    if instrument_cost_total_pct is not None:
        if not survives_instrument_cost:
            return "not_rescued_cost_negative"
        if legacy_fixed_cost_total_pct is None:
            return "not_rescued_no_cost_wall_evidence"
        if survives_legacy_fixed_cost:
            return "already_survives_legacy_fixed_cost"
        if not eth_evidence or rth_filter_applied is not False:
            return "needs_eth_full_session_replay"
        if not sample_floor or not density_ok or not year_coverage_ok:
            return "fee_cleared_but_blocked_non_cost"
        return "rescued_for_exact_aq"

    legacy_failed = legacy_fixed_cost_total_pct is not None and legacy_fixed_cost_total_pct <= 0.0
    gross_positive = gross_total_pct is None or gross_total_pct > 0.0
    if legacy_failed and gross_positive and legacy_reprice_realistic_cost_survival is False:
        return "not_rescued_zero_edge_churn_realistic_cost_negative"
    if legacy_failed and gross_positive:
        return "needs_reprice_replay"
    return "not_rescued_no_cost_wall_evidence"


def _legacy_reprice_realistic_cost_survival(
    row: dict[str, Any],
    *,
    symbol: str | None,
    trade_count: int,
    gross_total_pct: float | None,
) -> bool | None:
    if not symbol or trade_count <= 0 or gross_total_pct is None:
        return None
    representative_price = _first_float(
        row,
        "representative_price",
        "representative_entry_price",
        "last_close",
        "entry_price",
        "avg_entry_price",
        "close",
    )
    if representative_price is None or representative_price <= 0:
        return None
    profile = cost_model.futures_cost_profile(symbol)
    if profile is None or not profile.verified_for_promotion:
        return None
    realistic_total_pct = gross_total_pct - trade_count * profile.round_trip_cost_pct(representative_price)
    return realistic_total_pct > 0.0


def _year_coverage_ok(positive_years: int | None, years: int | None, row: dict[str, Any]) -> bool:
    explicit = _boolish(_first_present(row, "year_coverage_ok", "positive_year_coverage_met", "year_stability_met"))
    if explicit is not None:
        return explicit
    if positive_years is None or years is None:
        return True
    if years >= 5:
        return positive_years >= 3
    return positive_years >= max(1, years - 1)


def _reason_codes(
    *,
    instrument_cost_total_pct: float | None,
    legacy_fixed_cost_total_pct: float | None,
    survives_instrument_cost: bool,
    survives_legacy_fixed_cost: bool,
    trade_count: int,
    eth_evidence: bool,
    rth_filter_applied: bool | None,
    sample_floor: bool,
    density_ok: bool,
    year_coverage_ok: bool,
    legacy_reprice_realistic_cost_survival: bool | None,
) -> list[str]:
    reasons: list[str] = []
    if trade_count <= 0:
        reasons.append("zero_trades")
    if instrument_cost_total_pct is None:
        reasons.append("missing_instrument_cost_net")
    elif not survives_instrument_cost:
        reasons.append("survives_instrument_cost_false")
    if legacy_fixed_cost_total_pct is not None and legacy_fixed_cost_total_pct <= 0.0 and survives_instrument_cost:
        reasons.append("old_fixed_cost_false_negative_real_cost_positive")
    if legacy_reprice_realistic_cost_survival is False:
        reasons.append("gross_edge_below_realistic_all_in_cost")
    if survives_legacy_fixed_cost:
        reasons.append("already_survives_legacy_fixed_cost")
    if not eth_evidence:
        reasons.append("eth_full_retained_session_unverified")
    if rth_filter_applied is not False:
        reasons.append("rth_filter_not_false")
    if not sample_floor:
        reasons.append("sample_floor_not_met")
    if not density_ok:
        reasons.append("density_floor_not_met")
    if not year_coverage_ok:
        reasons.append("positive_year_coverage_too_weak_or_missing")
    return reasons


def _iter_normalized_rows(sources: Iterable[Path]) -> list[RescueRow]:
    normalized: list[RescueRow] = []
    for source in sources:
        if source.suffix.lower() == ".csv":
            for index, row in enumerate(_read_csv_rows(source)):
                item = normalize_row(row, str(source), "csv", index)
                if item is not None:
                    normalized.append(item)
            continue
        for table_name, rows in _read_json_tables(source):
            for index, row in enumerate(rows):
                item = normalize_row(row, str(source), table_name, index)
                if item is not None:
                    normalized.append(item)
    return normalized


def _read_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_json_tables(path: Path) -> list[tuple[str, list[dict[str, Any]]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [("json", [row for row in payload if isinstance(row, dict)])]
    if not isinstance(payload, dict):
        return []
    tables: list[tuple[str, list[dict[str, Any]]]] = []
    for key, value in payload.items():
        if isinstance(value, list):
            rows = [row for row in value if isinstance(row, dict)]
            if rows:
                tables.append((str(key), rows))
        elif isinstance(value, dict) and _looks_like_candidate_row(value):
            tables.append((str(key), [value]))
    if _looks_like_candidate_row(payload):
        tables.append(("json", [payload]))
    return tables


def _looks_like_candidate_row(value: dict[str, Any]) -> bool:
    return any(
        key in value
        for key in (
            "factor_id",
            "strategy_id",
            "package_id",
            "trade_count",
            "5bps_per_side_total_profit_pct",
            "legacy_fixed_cost_total_pct",
            "instrument_cost_total_profit_pct",
            "instrument_cost_total_ret_pct",
            "instrument_cost_total_pct",
        )
    )


def _dedupe_best(rows: list[RescueRow]) -> list[RescueRow]:
    best: dict[tuple[str, str | None, str | None, str | None, str | None], RescueRow] = {}
    for row in rows:
        key = (row.factor_id, row.symbol, row.timeframe, row.side, row.variant)
        incumbent = best.get(key)
        if incumbent is None or _row_score(row) > _row_score(incumbent):
            best[key] = row
    return sorted(
        best.values(),
        key=lambda row: (
            _rescue_rank(row.rescue_class),
            -(row.instrument_cost_total_pct if row.instrument_cost_total_pct is not None else -999999.0),
            row.factor_id,
        ),
    )


def _row_score(row: RescueRow) -> tuple[int, float, int]:
    return (
        -_rescue_rank(row.rescue_class),
        row.instrument_cost_total_pct if row.instrument_cost_total_pct is not None else -999999.0,
        row.trade_count,
    )


def _rescue_rank(rescue_class: str) -> int:
    order = {
        "rescued_for_exact_aq": 0,
        "fee_cleared_but_blocked_non_cost": 1,
        "needs_reprice_replay": 2,
        "needs_eth_full_session_replay": 3,
        "not_rescued_cost_negative": 4,
    }
    return order.get(rescue_class, 9)


def _write_rows_csv(path: Path, rows: list[RescueRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(RescueRow.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def _first_text(row: dict[str, Any], *keys: str) -> str | None:
    value = _first_present(row, *keys)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first_float(row: dict[str, Any], *keys: str) -> float | None:
    return _floatish(_first_present(row, *keys))


def _first_present(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return None


def _floatish(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def _intish(value: Any) -> int | None:
    parsed = _floatish(value)
    if parsed is None:
        return None
    return int(parsed)


def _boolish(value: Any) -> bool | None:
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


def _truthy(value: Any) -> bool:
    return _boolish(value) is True


def _session_scope_is_eth(value: str | None) -> bool:
    if not value:
        return False
    normalized = value.strip().lower()
    return "eth" in normalized or "full_retained" in normalized or "all_session" in normalized


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--csv", dest="csv_path", type=Path)
    parser.add_argument("--compact", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_report(args.sources, report_path=args.report_json, csv_path=args.csv_path)
    if args.compact:
        print(
            json.dumps(
                {
                    "schema_version": report["schema_version"],
                    "row_count": report["row_count"],
                    "class_counts": report["class_counts"],
                    "strict_rescue_count": report["strict_rescue_count"],
                    "fee_cleared_but_blocked_count": report["fee_cleared_but_blocked_count"],
                    "needs_reprice_replay_count": report["needs_reprice_replay_count"],
                    "needs_eth_full_session_replay_count": report["needs_eth_full_session_replay_count"],
                    "already_survives_legacy_fixed_cost_count": report["already_survives_legacy_fixed_cost_count"],
                    "promotion_allowed": False,
                    "trade_usable": False,
                    "update_goal": False,
                },
                sort_keys=True,
            )
        )
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
