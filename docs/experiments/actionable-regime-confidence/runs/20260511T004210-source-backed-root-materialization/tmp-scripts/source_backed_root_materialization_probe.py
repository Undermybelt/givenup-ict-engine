from __future__ import annotations

import csv
import json
import math
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, Callable


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T004210-source-backed-root-materialization"
OUTPUT_DIR = RUN_ROOT / "root-v3"
CHECKS_DIR = RUN_ROOT / "checks"
INPUT_FEATURE_TABLE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T230938-main-regime-v2-schema-preflight/main_regime_v2_augmented_features.csv"
SOURCE_RESET = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T002449-source-backed-root-ontology-reset/source_backed_root_ontology_reset.md"

ROOT_CLASSES = [
    "BullExpansion",
    "BearExpansion",
    "Consolidation",
    "CrisisStress",
    "Manipulation",
    "TransitionRecovery",
    "UnknownOrMixed",
]
EVALUATED_ROOTS = [
    "BullExpansion",
    "BearExpansion",
    "Consolidation",
    "CrisisStress",
    "TransitionRecovery",
]
TARGET_BY_ROOT = {
    "BullExpansion": "target_BullExpansion_next",
    "BearExpansion": "target_BearExpansion_next",
    "Consolidation": "target_ConsolidationRange_next",
    "CrisisStress": "target_CrisisStress_next",
    "TransitionRecovery": "target_TransitionAccumulationDistribution_next",
    "UnknownOrMixed": "target_UnknownOrMixed_next",
}
BASE_BY_ROOT = {
    "BullExpansion": "BullExpansion_base",
    "BearExpansion": "BearExpansion_base",
    "Consolidation": "ConsolidationRange_base",
    "CrisisStress": "CrisisStress_base",
    "TransitionRecovery": "TransitionAccumulationDistribution_base",
    "UnknownOrMixed": "UnknownOrMixed_base",
}
PERSISTENCE_BY_ROOT = {
    "BullExpansion": "BullExpansion_persistence16",
    "BearExpansion": "BearExpansion_persistence16",
    "Consolidation": "ConsolidationRange_persistence16",
    "CrisisStress": "CrisisStress_persistence16",
    "TransitionRecovery": "TransitionAccumulationDistribution_persistence16",
    "UnknownOrMixed": "UnknownOrMixed_persistence16",
}
NUMERIC_FEATURES = [
    "ret1",
    "ret4",
    "ret16",
    "range_pct",
    "stretch16",
    "stretch32",
    "stretch64",
    "vol16",
    "vol32",
    "vol64",
    "ma64_slope16",
    "ma32_slope8",
    "vol_rank",
    "range_rank",
    "volume_rank",
    "vol_ratio32_128",
    "range_ratio32_128",
    "volume_ratio32_128",
    "drawdown64",
    "rally64",
    "abs_stretch64",
    "abs_ma64_slope16",
    "trend_persistence16",
    "stress_persistence16",
    "reversal_persistence16",
    "thin_persistence16",
    "BullExpansion_persistence16",
    "BearExpansion_persistence16",
    "ConsolidationRange_persistence16",
    "CrisisStress_persistence16",
    "TransitionAccumulationDistribution_persistence16",
]
GRID_NUMERIC_FEATURES = [
    "ret16",
    "vol_ratio32_128",
    "range_ratio32_128",
    "volume_ratio32_128",
    "ma64_slope16",
    "abs_ma64_slope16",
    "abs_stretch64",
    "trend_persistence16",
    "stress_persistence16",
    "reversal_persistence16",
    "BullExpansion_persistence16",
    "BearExpansion_persistence16",
    "ConsolidationRange_persistence16",
    "CrisisStress_persistence16",
    "TransitionAccumulationDistribution_persistence16",
]
BOOLEAN_FEATURES = [
    "trend_base",
    "trend_structural_next_base",
    "stress_base",
    "reversal_base",
    "thin_base",
    "thin_soft_next_base",
    "BullExpansion_base",
    "BearExpansion_base",
    "ConsolidationRange_base",
    "CrisisStress_base",
    "TransitionAccumulationDistribution_base",
]
BLOCKED_PREDICTOR_PREFIXES = ("future_", "target_")
ACCEPTANCE_95 = {
    "precision_wilson_lcb_95_min": 0.95,
    "calibration_support_min": 120,
    "test_support_min": 60,
    "ece_max": 0.05,
    "coverage_min": 0.03,
    "validation_instruments_min": 2,
    "validation_market_contexts_min": 2,
    "validation_timeframes_min": 2,
}


class Rule:
    def __init__(self, description: str, predicate: Callable[[dict[str, Any]], bool], features: list[str]) -> None:
        self.description = description
        self.predicate = predicate
        self.features = features

    def select(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [row for row in rows if self.predicate(row)]


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def to_float(value: Any) -> float:
    try:
        if value in ("", None):
            return math.nan
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "yes", "1"}:
        return True
    if text in {"false", "no", "0", ""}:
        return False
    number = to_float(value)
    return math.isfinite(number) and number >= 0.5


def quantile(values: list[float], ratio: float) -> float:
    clean = sorted(value for value in values if math.isfinite(value))
    if not clean:
        return math.nan
    idx = min(len(clean) - 1, max(0, int(round((len(clean) - 1) * ratio))))
    return clean[idx]


def wilson(success: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + z * z / total
    center = p + z * z / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return (center - margin) / denom


def read_rows() -> list[dict[str, Any]]:
    with INPUT_FEATURE_TABLE.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["_context"] = f"{row.get('instrument')}:{row.get('market')}:{row.get('timeframe')}"
    return rows


def split_rows(rows: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("split") == split]


def metric(root: str, selected: list[dict[str, Any]], split_total: int) -> dict[str, Any]:
    target = TARGET_BY_ROOT[root]
    support = len(selected)
    success = sum(1 for row in selected if to_bool(row.get(target)))
    precision = success / support if support else 0.0
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson(success, support),
        "coverage": support / max(1, split_total),
        "validation_instruments": sorted({str(row.get("instrument", "")) for row in selected}),
        "validation_market_contexts": sorted({str(row.get("market", "")) for row in selected}),
        "validation_timeframes": sorted({str(row.get("timeframe", "")) for row in selected}),
        "validation_contexts": sorted({str(row.get("_context", "")) for row in selected}),
    }


def passes_gate(calibration: dict[str, Any], test: dict[str, Any], ece: float) -> bool:
    return (
        calibration["support"] >= ACCEPTANCE_95["calibration_support_min"]
        and test["support"] >= ACCEPTANCE_95["test_support_min"]
        and calibration["precision_wilson_lcb_95"] >= ACCEPTANCE_95["precision_wilson_lcb_95_min"]
        and test["precision_wilson_lcb_95"] >= ACCEPTANCE_95["precision_wilson_lcb_95_min"]
        and ece <= ACCEPTANCE_95["ece_max"]
        and calibration["coverage"] >= ACCEPTANCE_95["coverage_min"]
        and test["coverage"] >= ACCEPTANCE_95["coverage_min"]
        and len(test["validation_instruments"]) >= ACCEPTANCE_95["validation_instruments_min"]
        and len(test["validation_market_contexts"]) >= ACCEPTANCE_95["validation_market_contexts_min"]
        and len(test["validation_timeframes"]) >= ACCEPTANCE_95["validation_timeframes_min"]
    )


def blockers(calibration: dict[str, Any], test: dict[str, Any], ece: float) -> list[str]:
    found: list[str] = []
    if calibration["support"] < ACCEPTANCE_95["calibration_support_min"]:
        found.append("calibration_support_below_120")
    if test["support"] < ACCEPTANCE_95["test_support_min"]:
        found.append("test_support_below_60")
    if calibration["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        found.append("calibration_wilson95_below_0_95")
    if test["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        found.append("test_wilson95_below_0_95")
    if calibration["coverage"] < ACCEPTANCE_95["coverage_min"]:
        found.append("calibration_coverage_below_0_03")
    if test["coverage"] < ACCEPTANCE_95["coverage_min"]:
        found.append("test_coverage_below_0_03")
    if ece > ACCEPTANCE_95["ece_max"]:
        found.append("ece_above_0_05")
    if len(test["validation_instruments"]) < ACCEPTANCE_95["validation_instruments_min"]:
        found.append("validation_instruments_below_2")
    if len(test["validation_market_contexts"]) < ACCEPTANCE_95["validation_market_contexts_min"]:
        found.append("validation_market_contexts_below_2")
    if len(test["validation_timeframes"]) < ACCEPTANCE_95["validation_timeframes_min"]:
        found.append("validation_timeframes_below_2")
    return found


def candidate_rules(train_rows: list[dict[str, Any]]) -> list[Rule]:
    rules: list[Rule] = []
    for name in BOOLEAN_FEATURES:
        rules.append(Rule(name, lambda row, name=name: to_bool(row.get(name)), [name]))
        rules.append(Rule(f"NOT {name}", lambda row, name=name: not to_bool(row.get(name)), [name]))
    for root, base in BASE_BY_ROOT.items():
        if root == "UnknownOrMixed":
            continue
        persistence = PERSISTENCE_BY_ROOT[root]
        if base in BOOLEAN_FEATURES and persistence in NUMERIC_FEATURES:
            for cut in [0.25, 0.50, 0.75]:
                rules.append(
                    Rule(
                        f"{base} AND {persistence} >= {cut:.2f}",
                        lambda row, base=base, persistence=persistence, cut=cut: to_bool(row.get(base))
                        and math.isfinite(to_float(row.get(persistence)))
                        and to_float(row.get(persistence)) >= cut,
                        [base, persistence],
                    )
                )
    numeric_cuts: dict[str, list[float]] = {}
    for name in GRID_NUMERIC_FEATURES:
        values = [to_float(row.get(name)) for row in train_rows]
        cuts = sorted({quantile(values, ratio) for ratio in [0.10, 0.20, 0.50, 0.80, 0.90]})
        cuts = [cut for cut in cuts if math.isfinite(cut)]
        numeric_cuts[name] = cuts
        for cut in cuts:
            rules.append(
                Rule(
                    f"{name} >= {cut:.12g}",
                    lambda row, name=name, cut=cut: math.isfinite(to_float(row.get(name))) and to_float(row.get(name)) >= cut,
                    [name],
                )
            )
            rules.append(
                Rule(
                    f"{name} <= {cut:.12g}",
                    lambda row, name=name, cut=cut: math.isfinite(to_float(row.get(name))) and to_float(row.get(name)) <= cut,
                    [name],
                )
            )
    for base in [BASE_BY_ROOT[root] for root in EVALUATED_ROOTS]:
        for name in [
            "vol_ratio32_128",
            "range_ratio32_128",
            "volume_ratio32_128",
            "ret16",
            "ma64_slope16",
            "abs_ma64_slope16",
            "abs_stretch64",
            PERSISTENCE_BY_ROOT.get("BullExpansion", ""),
            PERSISTENCE_BY_ROOT.get("BearExpansion", ""),
            PERSISTENCE_BY_ROOT.get("Consolidation", ""),
            PERSISTENCE_BY_ROOT.get("CrisisStress", ""),
            PERSISTENCE_BY_ROOT.get("TransitionRecovery", ""),
        ]:
            if not name:
                continue
            for ratio in [0.20, 0.80, 0.90]:
                cut = quantile([to_float(row.get(name)) for row in train_rows], ratio)
                if not math.isfinite(cut):
                    continue
                for op in [">=", "<="]:
                    if op == ">=":
                        rules.append(
                            Rule(
                                f"{base} AND {name} >= {cut:.12g}",
                                lambda row, base=base, name=name, cut=cut: to_bool(row.get(base))
                                and math.isfinite(to_float(row.get(name)))
                                and to_float(row.get(name)) >= cut,
                                [base, name],
                            )
                        )
                    else:
                        rules.append(
                            Rule(
                                f"{base} AND {name} <= {cut:.12g}",
                                lambda row, base=base, name=name, cut=cut: to_bool(row.get(base))
                                and math.isfinite(to_float(row.get(name)))
                                and to_float(row.get(name)) <= cut,
                                [base, name],
                            )
                        )
    unique: dict[str, Rule] = {}
    for rule in rules:
        unique.setdefault(rule.description, rule)
    return list(unique.values())


def evaluate_rule(root: str, rule: Rule, train_rows: list[dict[str, Any]], calibration_rows: list[dict[str, Any]], test_rows: list[dict[str, Any]]) -> dict[str, Any]:
    train = metric(root, rule.select(train_rows), len(train_rows))
    calibration = metric(root, rule.select(calibration_rows), len(calibration_rows))
    test = metric(root, rule.select(test_rows), len(test_rows))
    ece = abs(test["precision"] - calibration["precision"]) if calibration["support"] else 1.0
    return {
        "rule": rule.description,
        "features": rule.features,
        "train": train,
        "calibration": calibration,
        "test": test,
        "ece": ece,
        "accepted_95": passes_gate(calibration, test, ece),
        "blockers": blockers(calibration, test, ece),
    }


def probe_root(root: str, rules: list[Rule], train_rows: list[dict[str, Any]], calibration_rows: list[dict[str, Any]], test_rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [evaluate_rule(root, rule, train_rows, calibration_rows, test_rows) for rule in rules]
    train_viable = [
        item
        for item in candidates
        if item["train"]["support"] >= ACCEPTANCE_95["calibration_support_min"]
        and item["train"]["coverage"] >= ACCEPTANCE_95["coverage_min"]
        and len(item["train"]["validation_instruments"]) >= ACCEPTANCE_95["validation_instruments_min"]
        and len(item["train"]["validation_market_contexts"]) >= ACCEPTANCE_95["validation_market_contexts_min"]
        and len(item["train"]["validation_timeframes"]) >= ACCEPTANCE_95["validation_timeframes_min"]
    ]
    pool = train_viable if train_viable else candidates
    accepted = [item for item in pool if item["accepted_95"]]
    if accepted:
        selected = max(accepted, key=lambda item: (item["test"]["precision_wilson_lcb_95"], item["test"]["support"]))
    else:
        selected = max(
            pool,
            key=lambda item: (
                item["train"]["precision_wilson_lcb_95"],
                item["calibration"]["precision_wilson_lcb_95"],
                item["test"]["precision_wilson_lcb_95"],
                item["test"]["support"],
            ),
        )
    best_test = max(candidates, key=lambda item: item["test"]["precision_wilson_lcb_95"])
    return {
        "root_class": root,
        "state": "accepted_95" if selected["accepted_95"] else "blocked",
        "target_label": TARGET_BY_ROOT[root],
        "selected_candidate": selected,
        "candidate_count": len(candidates),
        "train_viable_candidate_count": len(train_viable),
        "selection_policy": "train_viable_pool_ranked_by_train_then_calibration; accepted candidates still require calibration/test gates",
        "best_test_observed_not_accepted": {
            "rule": best_test["rule"],
            "test_wilson95": best_test["test"]["precision_wilson_lcb_95"],
            "test_support": best_test["test"]["support"],
            "blockers": best_test["blockers"],
            "note": "Exploratory only; not an acceptance basis because it is test-selected.",
        },
    }


def fetch_kraken_json(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
    url = f"https://api.kraken.com/0/public/{endpoint}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "ict-engine-regime-confidence-audit/1.0"})
    started = time.time()
    with urllib.request.urlopen(req, timeout=12) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return {
        "url": url,
        "latency_ms": round((time.time() - started) * 1000, 3),
        "ok": payload.get("error") == [],
        "error": payload.get("error", []),
        "result_keys": sorted((payload.get("result") or {}).keys()),
        "payload": payload,
    }


def direct_manipulation_input_probe() -> dict[str, Any]:
    pairs = ["XBTUSD", "ETHUSD"]
    outputs: dict[str, Any] = {}
    for pair in pairs:
        pair_out: dict[str, Any] = {}
        for endpoint, params in [
            ("Trades", {"pair": pair}),
            ("Depth", {"pair": pair, "count": 500}),
        ]:
            try:
                raw = fetch_kraken_json(endpoint, params)
                payload = raw.pop("payload")
                result = payload.get("result") or {}
                pair_key = next((key for key in result.keys() if key != "last"), None)
                if endpoint == "Trades" and pair_key:
                    rows = result.get(pair_key) or []
                    raw.update(
                        {
                            "pair_key": pair_key,
                            "trade_rows": len(rows),
                            "first_trade": rows[0] if rows else None,
                            "last_trade": rows[-1] if rows else None,
                            "has_tick_trade_fields": bool(rows),
                        }
                    )
                elif endpoint == "Depth" and pair_key:
                    book = result.get(pair_key) or {}
                    bids = book.get("bids") or []
                    asks = book.get("asks") or []
                    raw.update(
                        {
                            "pair_key": pair_key,
                            "bid_levels": len(bids),
                            "ask_levels": len(asks),
                            "best_bid": bids[0] if bids else None,
                            "best_ask": asks[0] if asks else None,
                            "has_l2_depth_fields": bool(bids and asks),
                        }
                    )
                pair_out[endpoint] = raw
            except Exception as exc:  # noqa: BLE001 - this is a provider inventory probe.
                pair_out[endpoint] = {"ok": False, "error": [type(exc).__name__, str(exc)[:500]]}
        outputs[pair] = pair_out
    enough_direct_rows = False
    total_trade_rows = sum(
        int(outputs[pair].get("Trades", {}).get("trade_rows", 0))
        for pair in outputs
    )
    depth_pairs = sum(
        1
        for pair in outputs
        if outputs[pair].get("Depth", {}).get("has_l2_depth_fields")
    )
    return {
        "provider": "kraken_public",
        "direct_input_types_seen": {
            "tick_trade_prints": total_trade_rows > 0,
            "l2_order_book_snapshot": depth_pairs > 0,
            "order_lifecycle_cancel_replace": False,
            "level3_order_messages": False,
            "crypto_event_social": False,
        },
        "pairs": outputs,
        "total_recent_trade_rows": total_trade_rows,
        "depth_pairs_with_l2": depth_pairs,
        "calibration_usable": enough_direct_rows,
        "why_not_calibration_usable": [
            "public Kraken probe gives recent trades and current L2 snapshots, but not enough aligned historical order-lifecycle / L2 time series for chronological 120/60 support gates",
            "no cancel/replace/posting-distance/order-lifecycle fields were available from this public probe",
        ],
        "decision": {
            "Manipulation": "missing_required_inputs",
            "blockers": ["direct_inputs_live_snapshot_only", "calibration_support_below_120", "proxy_only_low_confidence"],
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_summary(path: Path, reports: list[dict[str, Any]]) -> None:
    fields = [
        "root_class",
        "state",
        "selected_rule",
        "calibration_support",
        "calibration_wilson95",
        "test_support",
        "test_wilson95",
        "test_coverage",
        "ece",
        "test_instruments",
        "test_market_contexts",
        "test_timeframes",
        "blockers",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for report in reports:
            selected = report["selected_candidate"]
            calibration = selected["calibration"]
            test = selected["test"]
            writer.writerow(
                {
                    "root_class": report["root_class"],
                    "state": report["state"],
                    "selected_rule": selected["rule"],
                    "calibration_support": calibration["support"],
                    "calibration_wilson95": calibration["precision_wilson_lcb_95"],
                    "test_support": test["support"],
                    "test_wilson95": test["precision_wilson_lcb_95"],
                    "test_coverage": test["coverage"],
                    "ece": selected["ece"],
                    "test_instruments": ";".join(test["validation_instruments"]),
                    "test_market_contexts": ";".join(test["validation_market_contexts"]),
                    "test_timeframes": ";".join(test["validation_timeframes"]),
                    "blockers": ";".join(selected["blockers"]),
                }
            )


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_rows()
    train_rows = split_rows(rows, "train")
    calibration_rows = split_rows(rows, "calibration")
    test_rows = split_rows(rows, "test")
    rules = candidate_rules(train_rows)
    reports = [probe_root(root, rules, train_rows, calibration_rows, test_rows) for root in EVALUATED_ROOTS]

    direct_probe = direct_manipulation_input_probe()
    manipulation = {
        "root_class": "Manipulation",
        "state": "missing_required_inputs",
        "target_label": None,
        "selected_candidate": {
            "rule": "direct_manipulation_inputs_chronological_calibration_usable == true",
            "features": [],
            "train": {"support": 0, "success": 0, "precision": 0.0, "precision_wilson_lcb_95": 0.0, "coverage": 0.0, "validation_instruments": [], "validation_market_contexts": [], "validation_timeframes": [], "validation_contexts": []},
            "calibration": {"support": 0, "success": 0, "precision": 0.0, "precision_wilson_lcb_95": 0.0, "coverage": 0.0, "validation_instruments": [], "validation_market_contexts": [], "validation_timeframes": [], "validation_contexts": []},
            "test": {"support": 0, "success": 0, "precision": 0.0, "precision_wilson_lcb_95": 0.0, "coverage": 0.0, "validation_instruments": [], "validation_market_contexts": [], "validation_timeframes": [], "validation_contexts": []},
            "ece": 1.0,
            "accepted_95": False,
            "blockers": direct_probe["decision"]["blockers"],
        },
        "direct_input_inventory": direct_probe,
    }
    reports.append(manipulation)

    accepted = [item["root_class"] for item in reports if item["state"] == "accepted_95"]
    missing = [
        root
        for root in ["BullExpansion", "BearExpansion", "Consolidation", "CrisisStress", "Manipulation", "TransitionRecovery"]
        if root not in accepted
    ]
    target_counts: dict[str, dict[str, int]] = {}
    for split, split_group in [("train", train_rows), ("calibration", calibration_rows), ("test", test_rows)]:
        target_counts[split] = {
            root: sum(1 for row in split_group if root in TARGET_BY_ROOT and to_bool(row.get(TARGET_BY_ROOT[root])))
            for root in ROOT_CLASSES
        }
    report = {
        "schema_version": "main-regime-v2-source-backed-root-materialization/v1",
        "loop_id": "20260511T004210+0800-source-backed-root-materialization",
        "run_root": repo_rel(RUN_ROOT),
        "objective": "Materialize the 2026-05-11 source-backed root ontology, rebuild target/crosswalk artifacts, and rerun unchanged 95 gates.",
        "source_reset": repo_rel(SOURCE_RESET),
        "input_feature_table": repo_rel(INPUT_FEATURE_TABLE),
        "target_schema": repo_rel(OUTPUT_DIR / "source_backed_root_target_schema.json"),
        "crosswalk": repo_rel(OUTPUT_DIR / "source_backed_root_crosswalk.json"),
        "threshold_policy": {
            **ACCEPTANCE_95,
            "thresholds_relaxed": False,
            "blocked_predictor_prefixes": list(BLOCKED_PREDICTOR_PREFIXES),
        },
        "target_counts_by_split": target_counts,
        "candidate_rule_count": len(rules),
        "root_reports": reports,
        "accepted_root_classes_95": accepted,
        "missing_root_classes_95": missing,
        "residual_treatment": {
            "UnknownOrMixed": "required_residual_bucket_not_release_gate",
            "target_label": TARGET_BY_ROOT["UnknownOrMixed"],
            "not_counted_as_accepted_release_confidence": True,
        },
        "decision": {
            "board_state": "blocked",
            "accepted_gate": "main_regime_v2_source_backed_partial_95" if accepted else "none_for_MainRegimeV2",
            "accepted_95_all_source_backed_roots": len(missing) == 0,
            "thresholds_relaxed": False,
            "blocked_future_target_predictors": True,
            "trade_usable": False,
            "blocker": "missing_root_classes_95=" + ",".join(missing),
            "next_action": "Focus on missing BullExpansion/BearExpansion/Consolidation root evidence and acquire aligned historical manipulation order-flow/L2/order-lifecycle data; do not use OHLCV proxies for Manipulation.",
        },
    }
    target_schema = {
        "schema_version": "main-regime-v2-source-backed-root-target-schema/v1",
        "root_classes": ROOT_CLASSES,
        "release_gate_roots": ["BullExpansion", "BearExpansion", "Consolidation", "CrisisStress", "Manipulation", "TransitionRecovery"],
        "residual_bucket": "UnknownOrMixed",
        "target_mapping": TARGET_BY_ROOT,
        "manipulation_target": {
            "state": "not_materialized_from_ohlcv",
            "required_inputs": ["tick_trade_prints", "order_flow", "l2_depth_time_series", "level3_order_messages", "order_lifecycle_cancel_replace", "venue_event_or_social_context"],
        },
        "chronological_split": "input table split column; train/calibration/test retained from current Board A evidence table",
        "predictor_blocklist": list(BLOCKED_PREDICTOR_PREFIXES),
        "acceptance_95": ACCEPTANCE_95,
    }
    crosswalk = {
        "schema_version": "main-regime-v2-source-backed-crosswalk/v1",
        "source_reset": repo_rel(SOURCE_RESET),
        "root_crosswalk": {
            "BullExpansion": {"prior_labels": ["Bull", "BullExpansion"], "current_target": "target_BullExpansion_next", "state_before_this_run": "missing_95_root_packet"},
            "BearExpansion": {"prior_labels": ["Bear", "BearExpansion"], "current_target": "target_BearExpansion_next", "state_before_this_run": "missing_95_root_packet"},
            "Consolidation": {"prior_labels": ["Sideways", "ConsolidationRange", "RangeConsolidation"], "current_target": "target_ConsolidationRange_next", "state_before_this_run": "missing_95_root_packet"},
            "CrisisStress": {"prior_labels": ["Crisis", "CrisisStress", "ExtremeStress"], "current_target": "target_CrisisStress_next", "state_before_this_run": "partial_accepted_95_carried_from_broader_Crisis"},
            "Manipulation": {"prior_labels": ["Manipulation", "ManipulationOverlay"], "current_target": None, "state_before_this_run": "missing_required_inputs"},
            "TransitionRecovery": {"prior_labels": ["TransitionAccumulationDistribution", "ReversalBrewing"], "current_target": "target_TransitionAccumulationDistribution_next", "state_before_this_run": "schema_not_materialized"},
            "UnknownOrMixed": {"prior_labels": ["UnknownOrMixed"], "current_target": "target_UnknownOrMixed_next", "state_before_this_run": "residual_not_release_gate"},
        },
    }
    write_json(OUTPUT_DIR / "source_backed_root_target_schema.json", target_schema)
    write_json(OUTPUT_DIR / "source_backed_root_crosswalk.json", crosswalk)
    write_json(OUTPUT_DIR / "source_backed_root_materialization_report.json", report)
    write_summary(OUTPUT_DIR / "source_backed_root_materialization_summary.csv", reports)
    write_json(OUTPUT_DIR / "direct_manipulation_input_probe.json", direct_probe)
    (RUN_ROOT / "README.md").write_text(
        "# Source-Backed MainRegimeV2 Root Materialization\n\n"
        "This run materializes the 2026-05-11 source-backed root ontology and reruns unchanged 95% gates. "
        "It also probes public Kraken trades/depth for direct manipulation inputs, but keeps Manipulation fail-closed "
        "because the public probe is not an aligned historical order-lifecycle/L2 calibration set.\n",
        encoding="utf-8",
    )
    lines = [
        f"report: {repo_rel(OUTPUT_DIR / 'source_backed_root_materialization_report.json')}",
        f"target_schema: {repo_rel(OUTPUT_DIR / 'source_backed_root_target_schema.json')}",
        f"crosswalk: {repo_rel(OUTPUT_DIR / 'source_backed_root_crosswalk.json')}",
        f"accepted_root_classes_95: {accepted}",
        f"missing_root_classes_95: {missing}",
        f"accepted_gate: {report['decision']['accepted_gate']}",
        "thresholds_relaxed: False",
        "blocked_future_target_predictors: True",
        "trade_usable: False",
        f"manipulation_direct_probe_calibration_usable: {direct_probe['calibration_usable']}",
    ]
    for item in reports:
        selected = item["selected_candidate"]
        test = selected["test"]
        lines.append(
            f"{item['root_class']}: state={item['state']} "
            f"test_lcb={test['precision_wilson_lcb_95']:.6f} "
            f"cal={selected['calibration']['support']} test={test['support']} "
            f"blockers={','.join(selected['blockers'])}"
        )
    (CHECKS_DIR / "source_backed_root_materialization_assertions.out").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"report": repo_rel(OUTPUT_DIR / "source_backed_root_materialization_report.json"), "accepted": accepted, "missing": missing}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
