#!/usr/bin/env python3
"""Fail-closed readback of the latest local Auto-Quant backtest cache."""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any


RUN_ID = "20260512T013904-codex-autoquant-latest-backtest-cache-readback-v1"
REPO = Path(__file__).resolve().parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
AQ_ROOT = Path("/Users/thrill3r/Auto-Quant")
AQ_USER_DATA = AQ_ROOT / "user_data"
BACKTEST_RESULTS = AQ_USER_DATA / "backtest_results"
OUT_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = OUT_ROOT / "autoquant-latest-backtest-cache-readback-v1"
CHECK_DIR = OUT_ROOT / "checks"

R6_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
R3_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
R5_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
SOURCE_LABEL_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def latest_meta() -> Path:
    metas = sorted(BACKTEST_RESULTS.glob("*.meta.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not metas:
        raise FileNotFoundError(f"no Auto-Quant meta files under {BACKTEST_RESULTS}")
    return metas[0]


def load_backtest(meta_path: Path) -> tuple[dict[str, Any], Path, dict[str, Any]]:
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    zip_path = meta_path.with_suffix("").with_suffix(".zip")
    json_name = zip_path.name.replace(".zip", ".json")
    with zipfile.ZipFile(zip_path) as archive:
        data = json.loads(archive.read(json_name))
        names = archive.namelist()
    return meta, zip_path, {"data": data, "zip_names": names}


def active_strategy_files() -> tuple[list[Path], list[Path]]:
    default_dir = AQ_USER_DATA / "strategies"
    external_dir = AQ_USER_DATA / "strategies_external"
    default_files = sorted(
        p for p in default_dir.glob("*.py")
        if not p.name.startswith("_")
    ) if default_dir.exists() else []
    external_files = sorted(
        p for p in external_dir.glob("*.py")
        if not p.name.startswith("_")
    ) if external_dir.exists() else []
    return default_files, external_files


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    meta_path = latest_meta()
    meta, zip_path, loaded = load_backtest(meta_path)
    data = loaded["data"]
    strategies = data.get("strategy", {})
    if len(strategies) != 1:
        raise ValueError(f"expected one strategy in latest backtest, got {list(strategies)}")
    strategy_name, strategy_result = next(iter(strategies.items()))
    trades = strategy_result.get("trades", [])
    default_files, external_files = active_strategy_files()

    strategy_row = {
        "strategy_name": strategy_name,
        "timeframe": strategy_result.get("timeframe"),
        "timerange": strategy_result.get("timerange"),
        "total_trades": strategy_result.get("total_trades"),
        "wins": strategy_result.get("wins"),
        "losses": strategy_result.get("losses"),
        "winrate": strategy_result.get("winrate"),
        "profit_total": strategy_result.get("profit_total"),
        "profit_total_abs": strategy_result.get("profit_total_abs"),
        "sharpe": strategy_result.get("sharpe"),
        "profit_factor": strategy_result.get("profit_factor"),
        "max_drawdown_account": strategy_result.get("max_drawdown_account"),
        "first_trade_open": trades[0].get("open_date") if trades else "",
        "last_trade_close": trades[-1].get("close_date") if trades else "",
        "acceptance_status": "fail_closed_low_trade_count_and_negative_edge",
    }
    inventory_rows = [
        {
            "inventory_type": "active_default_strategy_py",
            "count": len(default_files),
            "files": ";".join(str(p.relative_to(AQ_ROOT)) for p in default_files),
        },
        {
            "inventory_type": "external_strategy_py",
            "count": len(external_files),
            "files": ";".join(str(p.relative_to(AQ_ROOT)) for p in external_files),
        },
        {
            "inventory_type": "latest_backtest_zip_members",
            "count": len(loaded["zip_names"]),
            "files": ";".join(loaded["zip_names"]),
        },
    ]
    roots = [
        {"id": "r6_owner_export", "root": str(R6_ROOT), "present": R6_ROOT.exists()},
        {"id": "r3_native_subhour", "root": str(R3_ROOT), "present": R3_ROOT.exists()},
        {"id": "r5_recency_extension", "root": str(R5_ROOT), "present": R5_ROOT.exists()},
        {"id": "source_label_equivalence", "root": str(SOURCE_LABEL_ROOT), "present": SOURCE_LABEL_ROOT.exists()},
    ]

    summary = {
        "run_id": RUN_ID,
        "board": str(BOARD.relative_to(REPO)),
        "board_sha256_before_artifact": sha256(BOARD),
        "gate_result": "autoquant_latest_backtest_cache_readback_v1=latest_cache_parsed_low_trade_negative_non_promoting",
        "auto_quant_root": str(AQ_ROOT),
        "latest_meta_path": str(meta_path),
        "latest_zip_path": str(zip_path),
        "latest_meta": meta,
        "strategy_row": strategy_row,
        "strategy_inventory": inventory_rows,
        "tmp_roots": roots,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    write_csv(
        OUT_DIR / "autoquant_latest_backtest_strategy_metrics_v1.csv",
        [strategy_row],
        [
            "strategy_name",
            "timeframe",
            "timerange",
            "total_trades",
            "wins",
            "losses",
            "winrate",
            "profit_total",
            "profit_total_abs",
            "sharpe",
            "profit_factor",
            "max_drawdown_account",
            "first_trade_open",
            "last_trade_close",
            "acceptance_status",
        ],
    )
    write_csv(
        OUT_DIR / "autoquant_strategy_inventory_v1.csv",
        inventory_rows,
        ["inventory_type", "count", "files"],
    )
    write_csv(
        OUT_DIR / "autoquant_latest_backtest_tmp_roots_v1.csv",
        roots,
        ["id", "root", "present"],
    )
    (OUT_DIR / "autoquant_latest_backtest_cache_readback_v1.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    inventory_lines = "\n".join(
        f"- `{row['inventory_type']}`: count `{row['count']}`; files `{row['files'] or 'none'}`."
        for row in inventory_rows
    )
    root_lines = "\n".join(
        f"- `{row['id']}` present `{str(row['present']).lower()}`."
        for row in roots
    )
    (OUT_DIR / "autoquant_latest_backtest_cache_readback_v1.md").write_text(
        "\n".join(
            [
                "# Auto-Quant Latest Backtest Cache Readback v1",
                "",
                f"Run id: `{RUN_ID}`",
                f"Gate result: `{summary['gate_result']}`",
                "",
                "Latest cache:",
                f"- Meta: `{meta_path}`",
                f"- Zip: `{zip_path}`",
                f"- Strategy: `{strategy_name}`",
                "",
                "Strategy metrics:",
                f"- timeframe `{strategy_row['timeframe']}`, timerange `{strategy_row['timerange']}`.",
                f"- trades `{strategy_row['total_trades']}`, wins `{strategy_row['wins']}`, losses `{strategy_row['losses']}`, winrate `{strategy_row['winrate']}`.",
                f"- profit_total `{strategy_row['profit_total']}`, profit_total_abs `{strategy_row['profit_total_abs']}`, sharpe `{strategy_row['sharpe']}`, profit_factor `{strategy_row['profit_factor']}`.",
                f"- first/last trade `{strategy_row['first_trade_open']}` -> `{strategy_row['last_trade_close']}`.",
                "",
                "Inventory:",
                inventory_lines,
                "",
                "Tmp root readback:",
                root_lines,
                "",
                "Result:",
                "- The latest local Auto-Quant cache is real and parseable, but it is not Board A promotion evidence.",
                "- Active default strategy source files remain `0`; the latest cached strategy has only `9` trades and negative edge.",
                "- The cache does not contain accepted MainRegimeV2 source labels, R6 controls, R3 native sub-hour labels, or R5 recency rows.",
                "- No canonical merge, downstream promotion rerun, trade usage, or `update_goal` is authorized.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assertions = {
        "latest_meta_present": meta_path.exists(),
        "latest_zip_present": zip_path.exists(),
        "latest_strategy_is_tomac": strategy_name == "TomacNQ_KillzoneBreakout",
        "active_default_strategy_count_zero": len(default_files) == 0,
        "external_strategy_count_positive": len(external_files) > 0,
        "trade_count_low": int(strategy_result.get("total_trades", 0)) < 50,
        "winrate_below_95": float(strategy_result.get("winrate", 0.0)) < 0.95,
        "profit_total_negative": float(strategy_result.get("profit_total", 0.0)) < 0.0,
        "r6_root_absent": not R6_ROOT.exists(),
        "r3_root_absent": not R3_ROOT.exists(),
        "r5_root_absent": not R5_ROOT.exists(),
        "downstream_chain_rerun_allowed_false": summary["downstream_chain_rerun_allowed"] is False,
        "update_goal_false": summary["update_goal"] is False,
    }
    (CHECK_DIR / "autoquant_latest_backtest_cache_readback_v1_assertions.out").write_text(
        "\n".join(f"{key}={value}" for key, value in assertions.items()) + "\n",
        encoding="utf-8",
    )
    return 0 if all(assertions.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
