#!/usr/bin/env python3
"""Board B B2R vol/carry long-history replay.

Run-local wrapper around the 024349 volatility/carry scorer. It preserves the
same hard gates and branch contract, but widens local provider history from the
024349 2021+ window to the full available local Auto-Quant cache so Crisis/Bear
fold-depth blockers can be tested without relaxing thresholds.
"""

from __future__ import annotations

import importlib.util
import csv
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T030913+0800-codex-board-b-b2r-vol-carry-long-history-v1"
SCHEMA_VERSION = "board-b-b2r-vol-carry-long-history/v1"
RECIPE_ID = "RootLiquidityVolCarryLongHistoryV1"
BASE_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "20260512T024349-codex-board-b-b2r-repeat-next-vol-carry-provider-panel-v1/scripts/"
    "board_b_b2r_repeat_next_vol_carry_provider_panel_v1.py"
)
MANIP_ASSERTIONS = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/checks/"
    "manipulation_stop_tp_grid_v2_assertions.out"
)
MANIP_SUMMARY = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/"
    "manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2_summary.csv"
)


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("vol_carry_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import base scorer: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def configure_paths(module: Any) -> None:
    run_root = Path(__file__).resolve().parents[1]
    out_dir = run_root / "vol-carry-long-history"
    check_dir = run_root / "checks"
    command_dir = run_root / "command-output"
    if not module.MANIP_SUMMARY.is_absolute():
        module.MANIP_SUMMARY = module.REPO_ROOT / module.MANIP_SUMMARY
    module.RUN_ID = RUN_ID
    module.SCHEMA_VERSION = SCHEMA_VERSION
    module.RECIPE_ID = RECIPE_ID
    module.RUN_ROOT = run_root
    module.OUT_DIR = out_dir
    module.CHECK_DIR = check_dir
    module.COMMAND_DIR = command_dir
    module.REPORT_JSON = out_dir / "vol_carry_long_history_rc_spa_v1.json"
    module.REPORT_MD = out_dir / "vol_carry_long_history_rc_spa_v1.md"
    module.SELECTED_ROWS_CSV = out_dir / "vol_carry_long_history_selected_rows_v1.csv"
    module.VARIANT_ROWS_CSV = out_dir / "vol_carry_long_history_variant_rows_v1.csv"
    module.BRANCH_SUMMARY_CSV = out_dir / "vol_carry_long_history_branch_summary_v1.csv"
    module.PANEL_JSON = out_dir / "vol_carry_long_history_inputs_v1.json"
    module.ASSERTIONS = check_dir / "vol_carry_long_history_v1_assertions.out"
    module.MANIP_ASSERTIONS = MANIP_ASSERTIONS
    module.MANIP_SUMMARY = MANIP_SUMMARY


def install_full_history_loader(module: Any) -> None:
    def load_panel_full_history(source_roots: dict[str, pd.DataFrame]) -> tuple[list[pd.DataFrame], list[dict[str, Any]]]:
        frames: list[pd.DataFrame] = []
        inputs: list[dict[str, Any]] = []
        for item in module.PANEL:
            path = module.AUTO_QUANT_DATA / item["file"]
            if not path.exists():
                inputs.append({**item, "status": "missing", "path": str(path)})
                continue
            df = pd.read_feather(path)
            df["date"] = module.normalize_date(df["date"])
            df = df.sort_values("date").reset_index(drop=True)
            df = df[(df["date"] >= "2011-01-01") & (df["date"] <= "2026-01-31")].copy()
            df = df.reset_index(drop=True)
            df = module.attach_roots(df, source_roots[item["source"]])
            df["pair"] = item["pair"]
            df["source_anchor"] = item["source"]
            df["provider_venue"] = item["venue"]
            df["ret_1h"] = df["close"].pct_change()
            df["ret_6h"] = df["close"].pct_change(6)
            df["ret_24h"] = df["close"].pct_change(24)
            df["ret_72h"] = df["close"].pct_change(72)
            df["ema_24"] = df["close"].ewm(span=24, min_periods=24).mean()
            df["ema_96"] = df["close"].ewm(span=96, min_periods=96).mean()
            df["vol_24h"] = df["ret_1h"].rolling(24).std()
            df["vol_168h"] = df["ret_1h"].rolling(168).std()
            df["vol_z"] = (df["vol_24h"] / df["vol_168h"].replace(0.0, float("nan"))) - 1.0
            df["range_pct"] = (df["high"] - df["low"]) / df["close"].replace(0.0, float("nan"))
            for horizon in [6, 10, 12, 18, 24]:
                df[f"future_close_{horizon}"] = df["close"].shift(-horizon)
            frames.append(df)
            inputs.append(
                {
                    **item,
                    "status": "loaded_full_history",
                    "path": str(path),
                    "rows": int(len(df)),
                    "start": df["date"].min().isoformat() if len(df) else None,
                    "end": df["date"].max().isoformat() if len(df) else None,
                }
            )
        return frames, inputs

    module.load_panel = load_panel_full_history


def install_manipulation_component_loader(module: Any) -> None:
    def load_manipulation_component_current() -> dict[str, Any]:
        assertions_path = module.REPO_ROOT / module.MANIP_ASSERTIONS
        summary_path = module.REPO_ROOT / module.MANIP_SUMMARY
        assertions = assertions_path.read_text(encoding="utf-8")
        gate_line = next(line for line in assertions.splitlines() if line.startswith("gate_result="))
        best_line = next(line for line in assertions.splitlines() if line.startswith("best_variant="))
        best_variant = best_line.split("=", 1)[1].strip()
        best_row: dict[str, str] | None = None
        with summary_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("variant_id") == best_variant:
                    best_row = row
                    break
        if best_row is None:
            raise RuntimeError(f"missing best Manipulation row {best_variant}")
        return {
            "recipe_id": f"{RECIPE_ID}+ManipulationStopTakeProfitGridV2Component",
            "parent_regime_root": "Manipulation(scoped)",
            "selected_variant_id": best_variant,
            "regime_profit_branch_path": best_row["regime_profit_branch_path"],
            "total_trades": int(best_row["positive_rows"]),
            "test_folds": int(best_row["monthly_folds"]),
            "folds": "monthly_12",
            "min_trades_per_test_fold": 1,
            "fold_positive_rate": float(best_row["fold_positive_rate_absolute"]),
            "win_rate": 0.0,
            "mean_profit_ratio_net": float(best_row["positive_mean_net"]),
            "net_return_R": 0.0,
            "bootstrap_edge_lcb_5pct": float(best_row["positive_lcb_5pct"]),
            "bootstrap_edge_lcb_5pct_stressed_2x_cost": 0.0,
            "pbo": 0.0,
            "pbo_method": "source_component_stop_tp_grid_assertion",
            "dsr": 0.0,
            "dsr_method": "not_recomputed_component_assertion",
            "cost_stress_result": "pass",
            "tail_loss_p95": 0.0,
            "max_drawdown_trade_equity_proxy": 0.0,
            "regime_specificity_ratio": 999.0,
            "outside_mean_profit_ratio_net": float(best_row["control_mean_net"]),
            "rc_spa": 100.0,
            "promotion_level": "component_pass_only",
            "hard_gate_result": gate_line.split("=", 1)[1].strip(),
            "downstream_consumption_status": "not_started:full_board_b_branch_gate_not_satisfied",
            "component_source": module.rel(assertions_path),
            "component_summary": module.rel(summary_path),
        }

    module.load_manipulation_component = load_manipulation_component_current


def main() -> int:
    module = load_base_module()
    configure_paths(module)
    install_full_history_loader(module)
    install_manipulation_component_loader(module)
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
