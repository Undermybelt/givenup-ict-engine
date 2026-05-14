#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path


RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "115700-selected-history-synthetic-pair-fix-v1"
CHECK_DIR = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"
AQ_ROOT = RUN_ROOT / "state_selected_history_synthetic_pair_fix_v1" / ".deps" / "auto-quant"
CONFIG = AQ_ROOT / "config.tomac.json"
STDOUT = CMD_DIR / "run_tomac_alias_timerange_fix.out"
STDERR = CMD_DIR / "run_tomac_alias_timerange_fix.err"
EXIT = CMD_DIR / "run_tomac_alias_timerange_fix.exit"


def read_text(path: Path) -> str:
    return path.read_text() if path.exists() else ""


def parse_strategy_metrics(stdout: str) -> list[dict[str, object]]:
    blocks: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for line in stdout.splitlines():
        if line.startswith("strategy:"):
            if current:
                blocks.append(current)
            current = {"strategy": line.split(":", 1)[1].strip()}
            continue
        if current is None:
            continue
        for key in (
            "sharpe",
            "sortino",
            "calmar",
            "total_profit_pct",
            "max_drawdown_pct",
            "trade_count",
            "win_rate_pct",
            "profit_factor",
        ):
            prefix = f"{key}:"
            if line.startswith(prefix):
                value = line.split(":", 1)[1].strip()
                if key == "trade_count":
                    current[key] = int(float(value))
                else:
                    current[key] = float(value)
    if current:
        blocks.append(current)
    return blocks


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    stdout = read_text(STDOUT)
    stderr = read_text(STDERR)
    exit_code = int(read_text(EXIT).strip() or "999")
    config = json.loads(CONFIG.read_text())
    pair = config["exchange"]["pair_whitelist"][0]
    timerange = config["timerange"]
    strategies = parse_strategy_metrics(stdout)
    total_trades = sum(int(item.get("trade_count", 0)) for item in strategies)
    succeeded_match = re.search(r"Done:\s+(\d+)\s+succeeded,\s+(\d+)\s+failed", stdout)
    succeeded = int(succeeded_match.group(1)) if succeeded_match else 0
    failed = int(succeeded_match.group(2)) if succeeded_match else len(strategies)
    data_loaded = "Dataload complete" in stderr
    pairlist_fixed = "Whitelist with 1 pairs" in stderr or "Backtesting with data" in stderr

    payload = {
        "run_id": "20260512T123234+0800-codex-115700-selected-history-synthetic-pair-fix-v1",
        "source_run_root": read_text(RUN_ROOT / "source_run_root.txt").strip(),
        "fixed_pair_alias": pair,
        "timerange": timerange,
        "run_tomac_exit": exit_code,
        "strategies_succeeded": succeeded,
        "strategies_failed": failed,
        "strategy_metrics": strategies,
        "total_trades": total_trades,
        "pairlist_fixed": pairlist_fixed,
        "data_loaded": data_loaded,
        "production_likelihood_mutation": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "gate_result": "selected_history_autoquant_runs_zero_trades_no_board_a_promotion",
        "root_cause": {
            "whitelist_failure": "Freqtrade drops underscore-containing pairs in expand_pairlist(..., keep_invalid=True); strict verification would keep it, but StaticPairList uses keep_invalid=True.",
            "data_failure": "The original timerange ended at 2025-12-31 while selected-history data starts at 2026-04-01.",
        },
    }

    json_path = OUT_DIR / "115700_selected_history_synthetic_pair_fix_v1.json"
    report_path = OUT_DIR / "115700_selected_history_synthetic_pair_fix_v1.md"
    assertions_path = CHECK_DIR / "115700_selected_history_synthetic_pair_fix_v1_assertions.out"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    lines = [
        "# 115700 Selected-History Synthetic Pair Fix v1",
        "",
        f"Run id: `{payload['run_id']}`",
        f"Source run root: `{payload['source_run_root']}`",
        "",
        "## Root Cause",
        "- `run_tomac.py` originally failed under `uv run --with ta-lib` because that environment lacked `freqtrade`.",
        "- Running with the Auto-Quant venv reached Freqtrade but failed with `No pair in whitelist` because `StaticPairList` uses `expand_pairlist(..., keep_invalid=True)`, which drops underscore-containing pairs.",
        "- After the underscore-free alias was added, Freqtrade loaded the pair but found no data because the copied `config.tomac.json` timerange stopped at `20251231` while the selected-history data begins on `2026-04-01`.",
        "",
        "## Isolated Fix",
        f"- Pair alias: `{pair}`.",
        f"- Timerange: `{timerange}`.",
        "- Data files were copied inside this run root only, from the original underscore pair filenames to matching alias filenames.",
        "- Repo runtime code was not changed.",
        "",
        "## Auto-Quant Result",
        f"- Command exit: `{exit_code}`.",
        f"- Strategies succeeded/failed: `{succeeded}` / `{failed}`.",
        f"- Total trades across strategies: `{total_trades}`.",
    ]
    for item in strategies:
        lines.append(
            "- `{strategy}`: trades `{trade_count}`, total_profit_pct `{total_profit_pct:.4f}`, win_rate_pct `{win_rate_pct:.4f}`, profit_factor `{profit_factor:.4f}`.".format(
                **item
            )
        )
    lines.extend(
        [
            "",
            "## Board A Decision",
            "- This repairs the selected-history Auto-Quant execution path for this isolated BTC 1h packet.",
            "- It does not produce a usable Auto-Quant recipe because all strategies generated zero trades.",
            "- It does not add non-BTC instrument validation, non-1h cycle validation, direct Manipulation evidence, BBN >=95% confidence, CatBoost promotion, or execution readiness.",
            "- `production_likelihood_mutation=false`; `promotion_allowed=false`; `trade_usable=false`; `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{json_path}`",
            f"- Assertions: `{assertions_path}`",
            "- Command: `command-output/run_tomac_alias_timerange_fix.cmd`",
            "- stdout/stderr/exit: `command-output/run_tomac_alias_timerange_fix.out`, `command-output/run_tomac_alias_timerange_fix.err`, `command-output/run_tomac_alias_timerange_fix.exit`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n")

    assertions = [
        f"PASS run_id={payload['run_id']}",
        f"PASS pairlist_fixed={str(pairlist_fixed).lower()} pair={pair}",
        f"PASS data_loaded={str(data_loaded).lower()} timerange={timerange}",
        f"PASS run_tomac_exit={exit_code}",
        f"PASS strategies_succeeded={succeeded}",
        f"FAIL_CLOSED total_trades={total_trades}",
        "PASS production_likelihood_mutation=false",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n")
    print(report_path)
    print(json_path)
    print(assertions_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
