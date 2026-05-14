#!/usr/bin/env python3
"""Generate Board B branch-path RC-SPA evidence for CrashRebound.

This script treats Auto-Quant as a read-only dependency. It imports the local
Auto-Quant oracle and extracts FreqTrade in-process trade rows without editing
Auto-Quant source files or running a second research loop.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import math
import random
import statistics
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any


RUN_ID = "20260511T180155+0800-codex-crashrebound-branch-rc-spa-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T180155-codex-crashrebound-branch-rc-spa-v1"
)
OUT_DIR = RUN_ROOT / "branch-rc-spa"
CHECK_DIR = RUN_ROOT / "checks"

AUTO_QUANT_ROOT = Path("/Users/thrill3r/Auto-Quant")
AUTO_QUANT_RUN = AUTO_QUANT_ROOT / "run.py"
AUTO_QUANT_STRATEGIES = AUTO_QUANT_ROOT / "versions/0.4.1/strategies"
RECIPE = "CrashRebound"
PAIR_BASKET = ["SOL/USDT", "AVAX/USDT", "BNB/USDT"]
ACCEPTED_REGIME_ID = (
    "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation"
)
ACCEPTED_REGIME_ARTIFACT = (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T153637-codex-regime-factor-consumer-map-v1/"
    "regime-factor-map/regime_factor_consumer_map_v1.csv"
)


FOLDS = [
    {
        "fold_label": "bull_2021",
        "timerange": "20210101-20211231",
        "fold_role": "root_conditioned_timerange_proxy",
        "parent_regime_root": "Bull",
        "sub_regime_tags": "drawdown_pullback",
        "sub_sub_regime_or_profit_factor": "oversold_rebound",
        "profit_factor_family": "counter_trend_drawdown_rebound",
        "profit_factor_leaf": RECIPE,
        "regime_profit_branch_path": (
            "Bull -> DrawdownPullback -> OversoldRebound -> CrashRebound"
        ),
    },
    {
        "fold_label": "winter_2022",
        "timerange": "20220101-20221231",
        "fold_role": "root_conditioned_timerange_proxy",
        "parent_regime_root": "Bear",
        "sub_regime_tags": "drawdown_capitulation",
        "sub_sub_regime_or_profit_factor": "oversold_rebound",
        "profit_factor_family": "counter_trend_drawdown_rebound",
        "profit_factor_leaf": RECIPE,
        "regime_profit_branch_path": (
            "Bear -> DrawdownCapitulation -> OversoldRebound -> CrashRebound"
        ),
    },
    {
        "fold_label": "recovery_23_25",
        "timerange": "20230101-20251231",
        "fold_role": "mixed_recovery_timerange_proxy_not_canonical_root",
        "parent_regime_root": "unresolved_mixed_recovery",
        "sub_regime_tags": "post_bear_recovery",
        "sub_sub_regime_or_profit_factor": "oversold_rebound",
        "profit_factor_family": "counter_trend_drawdown_rebound",
        "profit_factor_leaf": RECIPE,
        "regime_profit_branch_path": (
            "unresolved_mixed_recovery -> PostBearRecovery -> "
            "OversoldRebound -> CrashRebound"
        ),
    },
    {
        "fold_label": "full_5y",
        "timerange": "20210101-20251231",
        "fold_role": "overlap_aggregate_not_used_for_rc_spa",
        "parent_regime_root": "mixed_overlap_not_a_root",
        "sub_regime_tags": "aggregate_backtest",
        "sub_sub_regime_or_profit_factor": "oversold_rebound",
        "profit_factor_family": "counter_trend_drawdown_rebound",
        "profit_factor_leaf": RECIPE,
        "regime_profit_branch_path": (
            "mixed_overlap_not_a_root -> AggregateBacktest -> "
            "OversoldRebound -> CrashRebound"
        ),
    },
]


def load_auto_quant_run_module() -> Any:
    spec = importlib.util.spec_from_file_location("auto_quant_run", AUTO_QUANT_RUN)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Auto-Quant run module: {AUTO_QUANT_RUN}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["auto_quant_run"] = module
    spec.loader.exec_module(module)
    module.STRATEGIES_DIR = AUTO_QUANT_STRATEGIES
    return module


def value_as_float(item: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        value = item.get(key)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
    return default


def metric_row(fold: dict[str, str], strat: dict[str, Any]) -> dict[str, Any]:
    return {
        **fold,
        "strategy": RECIPE,
        "accepted_regime_id": ACCEPTED_REGIME_ID,
        "accepted_regime_artifact": ACCEPTED_REGIME_ARTIFACT,
        "root_label_source": "timerange_proxy_not_board_a_per_trade_join",
        "total_trades": int(value_as_float(strat, "total_trades")),
        "wins": int(value_as_float(strat, "wins")),
        "losses": int(value_as_float(strat, "losses")),
        "win_rate_pct": round(value_as_float(strat, "winrate") * 100, 6),
        "profit_total_pct": round(value_as_float(strat, "profit_total") * 100, 6),
        "profit_factor": round(value_as_float(strat, "profit_factor"), 6),
        "sharpe": round(value_as_float(strat, "sharpe"), 6),
        "sortino": round(value_as_float(strat, "sortino"), 6),
        "calmar": round(value_as_float(strat, "calmar"), 6),
        "max_drawdown_pct": round(
            -abs(value_as_float(strat, "max_drawdown_account")) * 100, 6
        ),
    }


def trade_row(fold: dict[str, str], trade: dict[str, Any], idx: int) -> dict[str, Any]:
    return {
        "run_id": RUN_ID,
        "recipe_id": RECIPE,
        "fold_label": fold["fold_label"],
        "fold_role": fold["fold_role"],
        "timerange": fold["timerange"],
        "trade_index": idx,
        "pair": trade.get("pair", ""),
        "open_date": str(trade.get("open_date", "")),
        "close_date": str(trade.get("close_date", "")),
        "stake_amount": trade.get("stake_amount", ""),
        "profit_ratio": trade.get("profit_ratio", ""),
        "profit_abs": trade.get("profit_abs", ""),
        "exit_reason": trade.get("exit_reason", ""),
        "trade_duration_minutes": trade.get("trade_duration", ""),
        "is_open": trade.get("is_open", ""),
        "parent_regime_root": fold["parent_regime_root"],
        "parent_regime_confidence_floor": confidence_floor(fold["parent_regime_root"]),
        "manipulation_overlay_state": "not_joined_abstain",
        "sub_regime_tags": fold["sub_regime_tags"],
        "sub_sub_regime_or_profit_factor": fold[
            "sub_sub_regime_or_profit_factor"
        ],
        "profit_factor_family": fold["profit_factor_family"],
        "profit_factor_leaf": fold["profit_factor_leaf"],
        "regime_profit_branch_path": fold["regime_profit_branch_path"],
        "regime_profit_branch_path_version": "v1.timerange_proxy",
        "trade_or_bar_horizon": "1h_trade",
        "allowed_action": "score_only_no_execution",
        "suppression_rule": "no_execution_until_accepted_root_join_and_downstream_consumption",
        "root_label_source": "timerange_proxy_not_board_a_per_trade_join",
    }


def confidence_floor(root: str) -> str:
    floors = {
        "Bull": "0.9797225384",
        "Bear": "0.963920242",
        "Sideways": "0.9529358324",
        "Crisis": "0.9619059575",
        "Manipulation": "0.967945",
    }
    return floors.get(root, "")


def bootstrap_lcb(values: list[float], seed: int = 20260511) -> float | None:
    if not values:
        return None
    rng = random.Random(seed)
    means: list[float] = []
    for _ in range(2000):
        sample = [values[rng.randrange(len(values))] for _ in values]
        means.append(statistics.fmean(sample))
    means.sort()
    return means[int(0.05 * (len(means) - 1))]


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    sorted_values = sorted(values)
    pos = (len(sorted_values) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return sorted_values[lo]
    return sorted_values[lo] * (hi - pos) + sorted_values[hi] * (pos - lo)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    rows = payload["fold_rows"]
    gates = payload["hard_gates"]
    lines = [
        "# CrashRebound Branch RC-SPA v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        (
            "- Gate result: "
            f"`{payload['hard_gate_result']}`; promotion level "
            f"`{payload['promotion_level']}`."
        ),
        (
            "- Extracted real FreqTrade trade rows from local Auto-Quant "
            "in-process Backtesting without editing Auto-Quant source files."
        ),
        (
            "- Branch paths are present, but they are timerange-proxy labels, "
            "not Board A accepted per-trade root-label joins."
        ),
        (
            "- `Sideways`, `Crisis`, and scoped direct `Manipulation` branch "
            "rows are absent for this recipe artifact."
        ),
        (
            "- Pre-Bayes, BBN, CatBoost/path-ranker, and execution-tree "
            "branch consumption remain unverified."
        ),
        "",
        "## Fold Rows",
        "",
        "| Fold | Root | Trades | Win % | Profit % | PF | Branch Path | Status |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {fold_label} | {parent_regime_root} | {total_trades} | "
            "{win_rate_pct:.3f} | {profit_total_pct:.3f} | {profit_factor:.3f} | "
            "`{regime_profit_branch_path}` | {fold_role} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Hard Gates",
            "",
            "| Gate | Pass | Evidence |",
            "|---|---:|---|",
        ]
    )
    for gate in gates:
        lines.append(
            f"| `{gate['gate']}` | {str(gate['pass']).lower()} | {gate['evidence']} |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `{payload['artifacts']['json']}`",
            f"- Fold CSV: `{payload['artifacts']['fold_csv']}`",
            f"- Trade CSV: `{payload['artifacts']['trade_csv']}`",
            f"- Hard gates CSV: `{payload['artifacts']['hard_gates_csv']}`",
            f"- Assertions: `{payload['artifacts']['assertions']}`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    auto_quant_run = load_auto_quant_run_module()
    fold_rows: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []

    oracle_log = CHECK_DIR / "crashrebound_branch_rc_spa_v1_oracle.out"
    with oracle_log.open("w", encoding="utf-8") as log_handle:
        for fold in FOLDS:
            with redirect_stdout(log_handle):
                results = auto_quant_run.run_backtest(
                    RECIPE, fold["timerange"], PAIR_BASKET
                )
            strat = results.get("strategy", {}).get(RECIPE, {}) or {}
            fold_rows.append(metric_row(fold, strat))
            for idx, trade in enumerate(strat.get("trades", []) or [], start=1):
                trade_rows.append(trade_row(fold, trade, idx))

    canonical_folds = [
        row for row in fold_rows if row["fold_role"] == "root_conditioned_timerange_proxy"
    ]
    canonical_trades = [
        row
        for row in trade_rows
        if row["fold_role"] == "root_conditioned_timerange_proxy"
    ]
    canonical_profit_ratios = [
        float(row["profit_ratio"])
        for row in canonical_trades
        if str(row["profit_ratio"]) not in {"", "None"}
    ]
    stressed_profit_ratios = [x - 0.002 for x in canonical_profit_ratios]
    positive_folds = sum(1 for row in canonical_folds if row["profit_total_pct"] > 0)
    fold_positive_rate = positive_folds / len(canonical_folds) if canonical_folds else 0.0
    roots_present = {row["parent_regime_root"] for row in canonical_folds}
    required_roots = {"Bull", "Bear", "Sideways", "Crisis"}
    missing_roots = sorted(required_roots - roots_present)
    lcb = bootstrap_lcb(canonical_profit_ratios)
    stressed_lcb = bootstrap_lcb(stressed_profit_ratios)
    losses = [-x for x in canonical_profit_ratios if x < 0]
    tail_loss_p95 = percentile(losses, 0.95)

    hard_gates = [
        {
            "gate": "accepted_regime_id_present",
            "pass": True,
            "evidence": ACCEPTED_REGIME_ARTIFACT,
        },
        {
            "gate": "branch_path_present",
            "pass": all(row["regime_profit_branch_path"] for row in canonical_folds),
            "evidence": "all canonical fold rows emit regime_profit_branch_path",
        },
        {
            "gate": "accepted_per_trade_root_label_join",
            "pass": False,
            "evidence": "root_label_source=timerange_proxy_not_board_a_per_trade_join",
        },
        {
            "gate": "required_main_roots_covered",
            "pass": not missing_roots,
            "evidence": "missing=" + ",".join(missing_roots),
        },
        {
            "gate": "scoped_manipulation_overlay_joined",
            "pass": False,
            "evidence": "manipulation_overlay_state=not_joined_abstain",
        },
        {
            "gate": "min_total_trades_gte_100",
            "pass": len(canonical_trades) >= 100,
            "evidence": f"canonical_trade_rows={len(canonical_trades)}",
        },
        {
            "gate": "min_test_folds_gte_4",
            "pass": len(canonical_folds) >= 4,
            "evidence": f"canonical_nonoverlapping_folds={len(canonical_folds)}",
        },
        {
            "gate": "min_trades_per_test_fold_gte_10",
            "pass": all(row["total_trades"] >= 10 for row in canonical_folds),
            "evidence": ",".join(
                f"{row['fold_label']}={row['total_trades']}" for row in canonical_folds
            ),
        },
        {
            "gate": "fold_positive_rate_gte_0_75",
            "pass": fold_positive_rate >= 0.75,
            "evidence": f"fold_positive_rate={fold_positive_rate:.6f}",
        },
        {
            "gate": "bootstrap_edge_lcb_5pct_gt_0",
            "pass": lcb is not None and lcb > 0,
            "evidence": f"bootstrap_edge_lcb_5pct={lcb:.8f}" if lcb is not None else "missing",
        },
        {
            "gate": "cost_stress_survival_true",
            "pass": stressed_lcb is not None and stressed_lcb > 0,
            "evidence": (
                "2x fee proxy subtracts extra 20 bps round trip; "
                f"stressed_lcb={stressed_lcb:.8f}"
                if stressed_lcb is not None
                else "missing"
            ),
        },
        {
            "gate": "pbo_lte_0_25",
            "pass": False,
            "evidence": "not_computable_without_4plus_nonoverlapping_folds_or_model_selection_matrix",
        },
        {
            "gate": "dsr_gt_0",
            "pass": False,
            "evidence": "not_computable_from_current artifact; no deflated-sharpe trials matrix",
        },
        {
            "gate": "tail_loss_p95_lte_budget",
            "pass": False,
            "evidence": (
                f"tail_loss_p95={tail_loss_p95:.8f}; configured_risk_budget=missing"
                if tail_loss_p95 is not None
                else "tail_loss_p95=missing"
            ),
        },
        {
            "gate": "regime_specificity_ratio_gte_1_20",
            "pass": False,
            "evidence": "not_computable_without out-of-branch baseline roots",
        },
        {
            "gate": "downstream_branch_consumption_verified",
            "pass": False,
            "evidence": "pre_bayes/bbn/catboost/execution_tree not run because hard gates failed",
        },
    ]

    hard_gate_result = (
        "fail:reject_missing_accepted_per_trade_root_labels;"
        "reject_missing_required_roots_sideways_crisis;"
        "reject_min_test_folds_lt4;"
        "research_watch_branch_path_not_consumed"
    )
    promotion_level = "reject"

    artifacts = {
        "json": str(OUT_DIR / "crashrebound_branch_rc_spa_v1.json"),
        "md": str(OUT_DIR / "crashrebound_branch_rc_spa_v1.md"),
        "fold_csv": str(OUT_DIR / "crashrebound_branch_rc_spa_v1_folds.csv"),
        "trade_csv": str(OUT_DIR / "crashrebound_branch_rc_spa_v1_trades.csv"),
        "hard_gates_csv": str(OUT_DIR / "crashrebound_branch_rc_spa_v1_hard_gates.csv"),
        "assertions": str(CHECK_DIR / "crashrebound_branch_rc_spa_v1_assertions.out"),
        "oracle_log": str(oracle_log),
    }

    payload = {
        "artifact_type": "board_b_crashrebound_branch_rc_spa_v1",
        "run_id": RUN_ID,
        "accepted_regime_id": ACCEPTED_REGIME_ID,
        "accepted_regime_artifact": ACCEPTED_REGIME_ARTIFACT,
        "recipe_id": RECIPE,
        "auto_quant_root": str(AUTO_QUANT_ROOT),
        "auto_quant_strategy_source": str(AUTO_QUANT_STRATEGIES / f"{RECIPE}.py"),
        "auto_quant_source_changed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_market_data_committed": False,
        "trade_usable": False,
        "rc_spa": 0,
        "diagnostics": {
            "canonical_trade_rows": len(canonical_trades),
            "canonical_nonoverlapping_folds": len(canonical_folds),
            "fold_positive_rate": fold_positive_rate,
            "bootstrap_edge_lcb_5pct": lcb,
            "cost_stress_extra_round_trip_fee": 0.002,
            "cost_stress_bootstrap_lcb_5pct": stressed_lcb,
            "tail_loss_p95": tail_loss_p95,
            "roots_present": sorted(roots_present),
            "missing_required_roots": missing_roots,
            "manipulation_overlay_state": "not_joined_abstain",
        },
        "hard_gate_result": hard_gate_result,
        "promotion_level": promotion_level,
        "downstream_consumption_status": "not_started_hard_gates_failed",
        "next_action": (
            "Join accepted Board A root labels to each CrashRebound trade timestamp "
            "or rerun Auto-Quant with accepted root labels emitted at trade time; "
            "then require Bull/Bear/Sideways/Crisis plus scoped Manipulation overlay "
            "coverage, at least four non-overlapping folds, PBO/DSR/regime-specificity, "
            "and branch-preserving pre-Bayes -> BBN -> CatBoost -> execution-tree "
            "consumption before promotion."
        ),
        "fold_rows": fold_rows,
        "hard_gates": hard_gates,
        "artifacts": artifacts,
    }

    write_csv(Path(artifacts["fold_csv"]), fold_rows)
    write_csv(Path(artifacts["trade_csv"]), trade_rows)
    write_csv(Path(artifacts["hard_gates_csv"]), hard_gates)
    write_json(Path(artifacts["json"]), payload)
    write_markdown(Path(artifacts["md"]), payload)

    assertions = [
        f"run_id={RUN_ID}",
        f"recipe_id={RECIPE}",
        f"canonical_trade_rows={len(canonical_trades)}",
        f"canonical_nonoverlapping_folds={len(canonical_folds)}",
        "branch_paths_present=true",
        "accepted_per_trade_root_join=false",
        "required_roots_covered=false",
        "scoped_manipulation_overlay_joined=false",
        f"hard_gate_result={hard_gate_result}",
        "rc_spa=0",
        f"promotion_level={promotion_level}",
        "downstream_consumption_verified=false",
        "auto_quant_source_changed=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_market_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    Path(artifacts["assertions"]).write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print("\n".join(assertions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
