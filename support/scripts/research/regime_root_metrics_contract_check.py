#!/usr/bin/env python3
"""Validate Board B metrics against regime-root and real-cost gate contracts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import regime_factor_tree_normalizer as tree_normalizer


DOWNSTREAM_GATE_KEYS = (
    "downstream_allowed",
    "pre_bayes_allowed",
    "bbn_allowed",
    "catboost_allowed",
    "execution_tree_allowed",
)

EXACT_TIMEFRAMES = (
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "4h",
    "1d",
)

TWO_BPS_SURVIVOR_KEYS = (
    "survivors_2bps",
    "survivors_2",
    "survivors_2bps_per_side",
    "exact_survivors_2bps",
    "origin_survivors_2bps",
    *(f"origin_{timeframe}_survivors_2bps" for timeframe in EXACT_TIMEFRAMES),
    *(f"origin_{timeframe}_survivors_2bps_density" for timeframe in EXACT_TIMEFRAMES),
    *(f"exact_{timeframe}_survivors_2bps" for timeframe in EXACT_TIMEFRAMES),
    *(f"exact_{timeframe}_survivors_2bps_density" for timeframe in EXACT_TIMEFRAMES),
)

FIVE_BPS_SURVIVOR_KEYS = (
    "survivors_5bps",
    "survivors_5",
    "survivors_5bps_per_side",
    "exact_survivors_5bps",
    "origin_survivors_5bps",
    *(f"origin_{timeframe}_survivors_5bps" for timeframe in EXACT_TIMEFRAMES),
    *(f"origin_{timeframe}_survivors_5bps_density" for timeframe in EXACT_TIMEFRAMES),
    *(f"exact_{timeframe}_survivors_5bps" for timeframe in EXACT_TIMEFRAMES),
    *(f"exact_{timeframe}_survivors_5bps_density" for timeframe in EXACT_TIMEFRAMES),
)

COST_ROW_KEYS = (
    "cost_row",
    "cost_stress",
    "cost_stress_rows",
    *(f"exact_{timeframe}_cost_stress" for timeframe in EXACT_TIMEFRAMES),
)

TREND_ROOT_EVIDENCE_PACKET_KEYS = (
    "root_regime_evidence_packet",
    "trend_root_evidence_packet",
    "regime_evidence_packet",
)

TREND_POSTERIOR_KEYS = (
    "trend_posterior",
    "root_regime_posterior",
    "regime_posterior",
    "trend_probability",
)

MSS_CONFIRMATION_KEYS = (
    "mss_confirmed",
    "mss_confirmation",
    "market_structure_shift_confirmed",
    "market_structure_shift",
)

CISD_CONFIRMATION_KEYS = (
    "cisd_confirmed",
    "cisd_confirmation",
    "cisd",
)

MIN_TREND_ROOT_POSTERIOR = 0.60
FUTURES_ROOTS = {
    "ES", "MES", "NQ", "MNQ", "YM", "MYM", "RTY", "M2K",
    "GC", "MGC", "XAU", "SI", "SIL", "HG",
    "CL", "MCL", "NG",
    "ZN", "ZB", "ZF",
    "ZC", "ZS", "ZW", "LE", "BRE",
    "6E", "M6E",
}

TREND_ROOT_BRANCH_KEYWORDS = (
    "cisd",
    "continuation",
    "mss",
    "pullback",
    "reclaim",
)

REQUIRED_TREND_LOSS_BOUNDARY_LABELS = (
    "low_trend_probability_loss",
    "terminal_trend_loss",
    "valid_trend_pullback_loss",
)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def listify(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, False, ""):
        return []
    return [value]


def truthy_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return False


def numeric_value(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def survivor_values(payload: dict[str, Any], keys: tuple[str, ...]) -> list[str]:
    values: list[str] = []
    for key in keys:
        for value in listify(payload.get(key)):
            if isinstance(value, str) and value and value not in values:
                values.append(value)
    return values


def cost_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in COST_ROW_KEYS:
        value = payload.get(key)
        if isinstance(value, dict):
            rows.append(value)
        elif isinstance(value, list):
            rows.extend(row for row in value if isinstance(row, dict))
    return rows


def row_label(row: dict[str, Any]) -> str:
    for key in ("label", "package_id", "strategy_id", "symbol", "contract"):
        value = row.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def row_trade_count(row: dict[str, Any]) -> int | None:
    value = row.get("trade_count")
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def row_trades_per_day(row: dict[str, Any]) -> float | None:
    for key in (
        "trades_per_day",
        "trade_per_day",
        "density_per_day",
        "trades_per_session",
        "trade_density_per_day",
    ):
        value = row.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def row_survives_5bps(row: dict[str, Any]) -> bool:
    if row.get("survives_5bps_per_side") is True:
        return True
    for key in (
        "net_after_5bps_side_pct",
        "net_after_5bps_per_side_pct",
        "5bps_per_side_total_profit_pct",
    ):
        value = row.get(key)
        if value is None:
            continue
        try:
            return float(value) > 0.0
        except (TypeError, ValueError):
            continue
    return False


def known_futures_root(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return futures_root_token_present(value)


def futures_root_token_present(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    text = value.upper().strip()
    if not text:
        return False
    tokens = [token for token in re.split(r"[^A-Z0-9]+", text) if token]
    compact = "".join(ch for ch in text if ch.isalnum())
    if compact:
        tokens.append(compact)
    for root in sorted(FUTURES_ROOTS, key=len, reverse=True):
        for token in tokens:
            if token == root:
                return True
            if not token.startswith(root):
                continue
            suffix = token[len(root):]
            if not suffix:
                return True
            if suffix.startswith("USD") or suffix[0].isdigit():
                return True
            if suffix[0] in "FGHJKMNQUVXZ" and suffix[1:].isdigit():
                return True
    return False


def cost_profile_verified(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    profile_id = value.strip().lower()
    if not profile_id:
        return False
    invalid_tokens = (
        "unknown",
        "missing",
        "unverified",
        "default",
        "assumption",
        "alias",
        "cost_model_unverified",
    )
    if any(token in profile_id for token in invalid_tokens):
        return False
    return "verified" in profile_id


def cost_status_verified(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    status = value.strip().lower()
    if not status:
        return False
    invalid_tokens = ("unverified", "default", "assumption", "alias", "missing", "unknown")
    return status.startswith("verified") and not any(token in status for token in invalid_tokens)


def row_cost_model_verified(row: dict[str, Any], payload: dict[str, Any]) -> bool:
    explicit = row.get("cost_model_verified_for_promotion")
    if explicit is None:
        explicit = row.get("promotion_cost_verified")
    if explicit is False:
        return False
    return bool(
        explicit is True
        or cost_status_verified(row.get("cost_model_status"))
        or cost_profile_verified(row.get("cost_profile_id"))
        or (cost_status_verified(payload.get("cost_model_status")) and payload.get("promotion_cost_verified") is True)
    )


def instrument_cost_survivor_hints(payload: dict[str, Any]) -> set[str]:
    hints: set[str] = set()
    for key in (
        "survivors_instrument_cost",
        "exact_instrument_cost_survivors",
        "survivors_real_cost",
        "exact_real_cost_survivors",
        "exact_cost_survivors",
    ):
        for value in listify(payload.get(key)):
            if isinstance(value, str) and value:
                hints.add(value)
    return hints


def instrument_cost_authority_declared(payload: dict[str, Any]) -> bool:
    authority = payload.get("cost_gate_authority")
    if isinstance(authority, str) and authority.strip().lower() in {"instrument_cost", "real_cost"}:
        return True
    return False


def row_is_futures_instrument_cost(row: dict[str, Any], payload: dict[str, Any]) -> bool:
    class_values = [
        row.get("asset_class"),
        row.get("instrument_class"),
        row.get("security_type"),
        row.get("sec_type"),
        row.get("product_type"),
    ]
    has_futures_class = any(
        isinstance(value, str) and ("future" in value.lower() or value.strip().upper() == "FUT")
        for value in class_values
    )
    has_futures_symbol = any(known_futures_root(row.get(key)) for key in ("label", "symbol", "contract", "root"))
    profile_id = row.get("cost_profile_id")
    profile_points_to_futures = isinstance(profile_id, str) and any(
        token in profile_id.upper() for token in ("CME", "CBOT", "COMEX", "NYMEX", "FUT")
    )
    verified_profile = row_cost_model_verified(row, payload)
    declared_exact_survivor = (
        instrument_cost_authority_declared(payload)
        and row_label(row) in instrument_cost_survivor_hints(payload)
    )
    return verified_profile and (declared_exact_survivor or not instrument_cost_survivor_hints(payload)) and (
        has_futures_class or has_futures_symbol or profile_points_to_futures
    )


def row_is_futures_context(row: dict[str, Any], payload: dict[str, Any]) -> bool:
    class_values = [
        row.get("asset_class"),
        row.get("instrument_class"),
        row.get("security_type"),
        row.get("sec_type"),
        row.get("product_type"),
        row.get("product"),
        row.get("category"),
    ]
    if any(
        isinstance(value, str) and ("future" in value.lower() or value.strip().upper() == "FUT")
        for value in class_values
    ):
        return True
    if any(known_futures_root(row.get(key)) for key in ("symbol", "contract", "root")):
        return True
    profile_id = row.get("cost_profile_id")
    if isinstance(profile_id, str) and any(
        token in profile_id.upper() for token in ("CME", "CBOT", "COMEX", "NYMEX", "FUT")
    ):
        return True
    role = str(row.get("cost_stress_5bps_role") or payload.get("cost_stress_5bps_role") or "").lower()
    row_text = " ".join(
        str(row.get(key) or "")
        for key in ("label", "package_id", "strategy_id", "factor_id", "symbol", "contract", "root")
    )
    if "telemetry_not_futures_hard_gate" in role and futures_root_token_present(row_text):
        return True
    if "tomac" in row_text.lower() and futures_root_token_present(row_text):
        return True
    label = row_label(row)
    return futures_root_token_present(label) and any(separator in label for separator in ("/", "_", "-"))


def label_is_futures_5bps_stress(label: Any, payload: dict[str, Any]) -> bool:
    if not isinstance(label, str) or not label:
        return False
    for row in cost_rows(payload):
        if row_label(row) == label and row_is_futures_context(row, payload):
            return True
    role = str(payload.get("cost_stress_5bps_role") or "").lower()
    if "telemetry_not_futures_hard_gate" in role and futures_root_token_present(label):
        return True
    if "tomac" in label.lower() and futures_root_token_present(label):
        return True
    return futures_root_token_present(label) and any(separator in label for separator in ("/", "_", "-"))


def row_survives_instrument_cost(row: dict[str, Any]) -> bool:
    if row.get("survives_instrument_cost") is True:
        return True
    for key in ("instrument_cost_total_profit_pct", "net_after_instrument_cost_pct"):
        value = numeric_value(row.get(key))
        if value is not None:
            return value > 0.0
    return False


def row_survives_real_cost(row: dict[str, Any], payload: dict[str, Any]) -> bool:
    if row_is_futures_context(row, payload):
        return row_is_futures_instrument_cost(row, payload) and row_survives_instrument_cost(row)
    return row_survives_5bps(row)


def exact_5bps_survivors(payload: dict[str, Any]) -> list[str]:
    explicit = set(survivor_values(payload, FIVE_BPS_SURVIVOR_KEYS))
    survivors: list[str] = []
    for row in cost_rows(payload):
        label = row_label(row)
        trade_count = row_trade_count(row)
        has_trades = trade_count is not None and trade_count > 0
        if row_survives_5bps(row) and has_trades:
            survivors.append(label or "cost_row")

    for value in explicit:
        if value in survivors:
            continue
        for row in cost_rows(payload):
            if row_label(row) != value:
                continue
            trade_count = row_trade_count(row)
            if row_survives_5bps(row) and trade_count is not None and trade_count > 0:
                survivors.append(value)
                break
    return sorted(set(survivors))


def exact_instrument_cost_survivors(payload: dict[str, Any]) -> list[str]:
    survivors: list[str] = []
    for row in cost_rows(payload):
        label = row_label(row)
        trade_count = row_trade_count(row)
        has_trades = trade_count is not None and trade_count > 0
        if row_is_futures_instrument_cost(row, payload) and row_survives_instrument_cost(row) and has_trades:
            survivors.append(label or "cost_row")
    return sorted(set(survivors))


def exact_real_cost_survivors(payload: dict[str, Any]) -> list[str]:
    non_futures_bps_survivors = [
        label for label in exact_5bps_survivors(payload)
        if not label_is_futures_5bps_stress(label, payload)
    ]
    return sorted(set(non_futures_bps_survivors + exact_instrument_cost_survivors(payload)))


def positive_5bps_rows_without_trade_count(payload: dict[str, Any]) -> list[str]:
    rows_without_trade_count: list[str] = []
    for row in cost_rows(payload):
        if not row_survives_5bps(row):
            continue
        trade_count = row_trade_count(row)
        if trade_count is None or trade_count <= 0:
            rows_without_trade_count.append(row_label(row) or "cost_row")
    return sorted(set(rows_without_trade_count))


def downstream_gates_open(payload: dict[str, Any]) -> list[str]:
    return [key for key in DOWNSTREAM_GATE_KEYS if truthy_bool(payload.get(key))]


def evidence_packet(payload: dict[str, Any]) -> dict[str, Any]:
    for key in TREND_ROOT_EVIDENCE_PACKET_KEYS:
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


def evidence_value(
    payload: dict[str, Any],
    packet: dict[str, Any],
    keys: tuple[str, ...],
) -> Any:
    for key in keys:
        if key in packet:
            return packet.get(key)
    for key in keys:
        if key in payload:
            return payload.get(key)
    return None


def branch_requires_trend_root_evidence(normalized: dict[str, Any]) -> bool:
    canonical = str(normalized.get("canonical_branch_path") or "")
    parts = tree_normalizer.split_path(canonical)
    if not parts or parts[0] != "TrendExpansion":
        return False
    lower = canonical.lower()
    return any(keyword in lower for keyword in TREND_ROOT_BRANCH_KEYWORDS)


def trend_loss_boundary_labels(payload: dict[str, Any]) -> set[str]:
    labels: set[str] = set()
    for key in ("loss_boundary_labels", "trend_loss_boundary_labels"):
        for value in listify(payload.get(key)):
            if isinstance(value, str) and value:
                labels.add(value)

    packet = evidence_packet(payload)
    for key in ("loss_boundary_labels", "trend_loss_boundary_labels"):
        for value in listify(packet.get(key)):
            if isinstance(value, str) and value:
                labels.add(value)
    return labels


def trend_root_evidence_violations(
    payload: dict[str, Any],
    normalized: dict[str, Any],
    gates_open: list[str],
) -> list[str]:
    if not gates_open or not branch_requires_trend_root_evidence(normalized):
        return []

    packet = evidence_packet(payload)
    violations: list[str] = []
    if not packet:
        violations.append("trend_root_evidence_packet_missing")

    posterior = numeric_value(evidence_value(payload, packet, TREND_POSTERIOR_KEYS))
    if posterior is None:
        violations.append("trend_root_posterior_missing")
    elif posterior < MIN_TREND_ROOT_POSTERIOR:
        violations.append("trend_root_posterior_below_threshold")

    if not truthy_bool(evidence_value(payload, packet, MSS_CONFIRMATION_KEYS)):
        violations.append("trend_root_mss_confirmation_missing")
    if not truthy_bool(evidence_value(payload, packet, CISD_CONFIRMATION_KEYS)):
        violations.append("trend_root_cisd_confirmation_missing")
    loss_labels = trend_loss_boundary_labels(payload)
    missing_loss_labels = [
        label for label in REQUIRED_TREND_LOSS_BOUNDARY_LABELS if label not in loss_labels
    ]
    if missing_loss_labels:
        violations.append("trend_root_loss_boundary_labels_missing")
    return violations


def feedback_admission_report(gates_open: list[str], violations: list[str]) -> dict[str, Any]:
    has_downstream_claim = bool(gates_open)
    has_contract_violation = bool(violations)
    quarantine_required = has_downstream_claim and has_contract_violation
    allowed = has_downstream_claim and not has_contract_violation
    if quarantine_required:
        decision = "quarantine_downstream_contract_violation"
    elif allowed:
        decision = "feedback_admission_allowed"
    else:
        decision = "not_downstream_admission_candidate"
    return {
        "decision": decision,
        "quarantine_required": quarantine_required,
        "blocking_violations": sorted(set(violations)) if quarantine_required else [],
        "allowed_targets": {
            "pre_bayes_feedback": allowed,
            "bbn_feedback": allowed,
            "catboost_training": allowed,
            "execution_tree_training": allowed,
        },
    }


def practical_admission_violations(payload: dict[str, Any]) -> list[str]:
    extension_complete = truthy_bool(payload.get("extension_complete"))
    violations: list[str] = []
    if truthy_bool(payload.get("promotion_allowed")) and not extension_complete:
        violations.append("promotion_before_extension_complete")
    if truthy_bool(payload.get("trade_usable")) and not extension_complete:
        violations.append("trade_usable_before_extension_complete")
    return violations


def practical_admission_report(payload: dict[str, Any], violations: list[str]) -> dict[str, Any]:
    extension_complete = truthy_bool(payload.get("extension_complete"))
    wants_practical = truthy_bool(payload.get("promotion_allowed")) or truthy_bool(payload.get("trade_usable"))
    if violations:
        decision = "branch_local_only_extension_incomplete"
    elif extension_complete and wants_practical:
        decision = "practical_admission_allowed"
    elif extension_complete:
        decision = "extension_complete_no_practical_claim"
    else:
        decision = "branch_local_only_extension_incomplete"
    allowed = extension_complete and not violations
    return {
        "decision": decision,
        "extension_complete": extension_complete,
        "blocking_violations": sorted(set(violations)),
        "allowed_targets": {
            "promotion_allowed": allowed,
            "trade_usable": allowed,
        },
    }


def check_payload(
    payload: dict[str, Any],
    *,
    path: Path | None = None,
    min_trades_per_day: float | None = None,
) -> dict[str, Any]:
    branch_path = tree_normalizer.metrics_branch_path(payload)
    normalized = tree_normalizer.normalize_branch_path(
        branch_path,
        tree_normalizer.extract_portability_labels(payload),
    )
    gates_open = downstream_gates_open(payload)
    exact_5bps = exact_5bps_survivors(payload)
    exact_instrument_cost = exact_instrument_cost_survivors(payload)
    exact_real_cost = exact_real_cost_survivors(payload)
    five_bps_without_trade_count = positive_5bps_rows_without_trade_count(payload)
    two_bps_survivors = survivor_values(payload, TWO_BPS_SURVIVOR_KEYS)
    five_bps_survivors = survivor_values(payload, FIVE_BPS_SURVIVOR_KEYS)

    violations: list[str] = []
    feedback_blocking_violations: list[str] = []
    if not normalized["canonical_root_ok"]:
        feedback_blocking_violations.extend(
            f"canonical_root_violation:{violation}"
            for violation in normalized["violations"]
        )
    if branch_path != normalized["canonical_branch_path"]:
        feedback_blocking_violations.append("branch_path_not_canonical_regime_root")
    if gates_open and not exact_real_cost:
        feedback_blocking_violations.append("downstream_open_without_exact_real_cost_survivor")
    if gates_open and five_bps_without_trade_count and not exact_real_cost:
        feedback_blocking_violations.append("cost_rows_5bps_positive_without_trade_count_proof")
    if gates_open and two_bps_survivors and not exact_real_cost:
        feedback_blocking_violations.append("survivors_2bps_used_as_downstream_gate")
    if gates_open and five_bps_survivors and not exact_real_cost:
        feedback_blocking_violations.append("survivors_5bps_without_cost_row_used_as_downstream_gate")
    if not payload.get("branch_fields_preserved", bool(branch_path)):
        feedback_blocking_violations.append("branch_fields_not_preserved")
    feedback_blocking_violations.extend(trend_root_evidence_violations(payload, normalized, gates_open))
    practical_violations = practical_admission_violations(payload)
    violations.extend(feedback_blocking_violations)
    violations.extend(practical_violations)

    return {
        "file": str(path) if path else None,
        "ok": not violations,
        "decision": "contract_ok" if not violations else "contract_violation",
        "violations": sorted(set(violations)),
        "branch_path": branch_path,
        "normalized": normalized,
        "downstream_gates_open": gates_open,
        "feedback_admission": feedback_admission_report(gates_open, feedback_blocking_violations),
        "practical_admission": practical_admission_report(payload, practical_violations),
        "survivors": {
            "two_bps": two_bps_survivors,
            "five_bps": five_bps_survivors,
            "exact_5bps": exact_5bps,
            "exact_5bps_density": exact_5bps,
            "instrument_cost": exact_instrument_cost,
            "real_cost": exact_real_cost,
            "five_bps_without_trade_count": five_bps_without_trade_count,
        },
        "density_gate": {
            "min_trades_per_day": None,
            "status": "cancelled",
            "requirement": "trade_count_gt_0_and_positive_exact_real_cost",
        },
        "min_trend_root_posterior": MIN_TREND_ROOT_POSTERIOR,
    }


def check_metrics_file(path: Path, *, min_trades_per_day: float | None = None) -> dict[str, Any]:
    return check_payload(
        load_json(path),
        path=path,
        min_trades_per_day=min_trades_per_day,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path, help="Metrics JSON files to check")
    parser.add_argument(
        "--min-trades-per-day",
        type=float,
        default=None,
        help="Deprecated no-op; daily density no longer blocks exact 5bps feedback admission",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    reports = [
        check_metrics_file(path, min_trades_per_day=args.min_trades_per_day)
        for path in args.files
    ]
    print(json.dumps(reports, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0 if all(report["ok"] for report in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
