#!/usr/bin/env python3
"""Run isolated Auto-Quant strategy seeds against the local-cache workspace.

This consumes the data-ready `/tmp` workspace from the 022826 probe, writes
only active strategy wrappers inside that isolated workspace, and records
the `run.py` output as non-promoting Board A runtime evidence.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T023540-codex-autoquant-isolated-seeded-btc-run-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "autoquant-isolated-seeded-btc-run-v1"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
WORKSPACE = Path(
    "/tmp/ict-engine-board-a-autoquant-local-cache-20260512T022826"
    "/auto-quant/.deps/auto-quant"
)
STRATEGIES = WORKSPACE / "user_data/strategies"
DATA_DIR = WORKSPACE / "user_data/data"

WRAPPERS = {
    "BTCLeaderBreakV4BTCOnly.py": '''from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "versions/0.4.0/strategies"))
from BTCLeaderBreakV4 import BTCLeaderBreakV4 as _BTCLeaderBreakV4


class BTCLeaderBreakV4BTCOnly(_BTCLeaderBreakV4):
    pair_basket = ["BTC/USDT"]
''',
    "MTFTrendStackBTCOnly.py": '''from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "versions/0.3.0/strategies"))
from MTFTrendStack import MTFTrendStack as _MTFTrendStack


class MTFTrendStackBTCOnly(_MTFTrendStack):
    pair_basket = ["BTC/USDT"]
''',
    "MomentumMTFConfluenceBTCOnly.py": '''from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "versions/0.4.0/strategies"))
from MomentumMTFConfluence import MomentumMTFConfluence as _MomentumMTFConfluence


class MomentumMTFConfluenceBTCOnly(_MomentumMTFConfluence):
    pair_basket = ["BTC/USDT"]
''',
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def root_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "present": False, "kind": "absent", "file_count": 0}
    if path.is_dir():
        return {
            "path": str(path),
            "present": True,
            "kind": "dir",
            "file_count": sum(1 for child in path.iterdir() if child.is_file()),
        }
    return {"path": str(path), "present": True, "kind": "file", "file_count": 1}


def write_wrappers() -> list[dict[str, Any]]:
    STRATEGIES.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, content in WRAPPERS.items():
        path = STRATEGIES / name
        path.write_text(content, encoding="utf-8")
        rows.append(
            {
                "filename": name,
                "path": str(path),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
        )
    return rows


def run_autoquant() -> dict[str, Any]:
    cmd = ["uv", "run", "--with", "ta-lib", "run.py"]
    env = dict(os.environ)
    script_dir = Path(__file__).resolve().parent
    old_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        str(script_dir) if not old_pythonpath else f"{script_dir}{os.pathsep}{old_pythonpath}"
    )
    proc = subprocess.run(
        cmd,
        cwd=WORKSPACE,
        env=env,
        text=True,
        capture_output=True,
        timeout=480,
        check=False,
    )
    (CMD / "autoquant_seeded_run.cmd").write_text(
        f"PYTHONPATH={env['PYTHONPATH']} " + " ".join(cmd) + "\n",
        encoding="utf-8",
    )
    (CMD / "autoquant_seeded_run.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (CMD / "autoquant_seeded_run.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    (CMD / "autoquant_seeded_run.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
    return {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def parse_blocks(stdout: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    blocks: list[dict[str, Any]] = []
    for block in stdout.split("---"):
        if "strategy:" not in block:
            continue
        row: dict[str, Any] = {}
        for line in block.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key in {
                "strategy",
                "commit",
                "config",
                "pairs",
                "status",
                "error_type",
                "error_msg",
            }:
                row[key] = value
            elif key in {
                "sharpe",
                "sortino",
                "calmar",
                "total_profit_pct",
                "max_drawdown_pct",
                "win_rate_pct",
                "profit_factor",
                "robust_sharpe",
            }:
                try:
                    row[key] = float(value)
                except ValueError:
                    row[key] = value
            elif key in {"trade_count"}:
                try:
                    row[key] = int(float(value))
                except ValueError:
                    row[key] = value
        if row.get("strategy"):
            blocks.append(row)
    done_match = re.search(
        r"Done:\s+(\d+)\s+(?:backtests\s+)?succeeded,\s+(\d+)\s+failed\.",
        stdout,
    )
    if done_match:
        done = {"succeeded": int(done_match.group(1)), "failed": int(done_match.group(2))}
    else:
        done = {"succeeded": 0, "failed": -1}
    return blocks, done


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    for path in (OUT, CHECKS, CMD):
        path.mkdir(parents=True, exist_ok=True)

    wrapper_rows = write_wrappers()
    data_files = sorted(path.name for path in DATA_DIR.glob("*.feather"))
    command = run_autoquant()
    blocks, done = parse_blocks(command["stdout"])
    trade_blocks = [row for row in blocks if "trade_count" in row]
    robust_blocks = [row for row in blocks if "robust_sharpe" in row]
    success = command["returncode"] == 0 and done["succeeded"] >= 1 and done["failed"] == 0
    if success:
        gate_result = "autoquant_isolated_seeded_btc_run_v1=seeded_btc_strategy_backtests_succeeded_non_promoting_source_control_blocked"
    else:
        gate_result = "autoquant_isolated_seeded_btc_run_v1=seeded_btc_strategy_backtests_failed_non_promoting_source_control_blocked"

    roots = {
        "r6_owner_export": root_status(Path("/tmp/ict-engine-board-a-r6-owner-export-v1")),
        "r3_native_subhour": root_status(Path("/tmp/ict-engine-native-subhour-source-label-intake")),
        "r5_recency_extension": root_status(Path("/tmp/ict-engine-source-panel-recency-extension")),
        "source_label_equivalence": root_status(Path("/tmp/ict-engine-source-label-equivalence-intake")),
        "legacy_direct_intake": root_status(Path("/tmp/ict-engine-direct-manipulation-row-intake")),
    }

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_generation": sha256(BOARD),
        "gate_result": gate_result,
        "workspace": str(WORKSPACE),
        "data_dir": str(DATA_DIR),
        "data_files": data_files,
        "wrapper_strategies": wrapper_rows,
        "command": "uv run --with ta-lib run.py",
        "command_exit": command["returncode"],
        "done": done,
        "strategy_results": blocks,
        "trade_result_rows": trade_blocks,
        "robust_summary_rows": robust_blocks,
        "root_status": roots,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r3_r5_r6_roots_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    json_path = OUT / "autoquant_isolated_seeded_btc_run_v1.json"
    report_path = OUT / "autoquant_isolated_seeded_btc_run_v1.md"
    metrics_csv = OUT / "autoquant_isolated_seeded_btc_metrics_v1.csv"
    wrappers_csv = OUT / "seeded_strategy_wrappers_v1.csv"
    assertions_path = CHECKS / "autoquant_isolated_seeded_btc_run_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        metrics_csv,
        trade_blocks,
        [
            "strategy",
            "status",
            "error_type",
            "error_msg",
            "pairs",
            "sharpe",
            "sortino",
            "calmar",
            "total_profit_pct",
            "max_drawdown_pct",
            "trade_count",
            "win_rate_pct",
            "profit_factor",
            "robust_sharpe",
        ],
    )
    write_csv(wrappers_csv, wrapper_rows, ["filename", "path", "sha256", "bytes"])

    strategy_lines = []
    for row in trade_blocks:
        if row.get("status") == "ERROR":
            strategy_lines.append(
                f"- `{row.get('strategy')}` failed: `{row.get('error_type')}` `{row.get('error_msg')}`."
            )
        else:
            strategy_lines.append(
                "- `{strategy}` pair basket `BTC/USDT` trades `{trade_count}` profit `{profit:.4f}%` "
                "Sharpe `{sharpe:.4f}` win rate `{win:.4f}%` PF `{pf:.4f}`.".format(
                    strategy=row.get("strategy"),
                    trade_count=row.get("trade_count"),
                    profit=float(row.get("total_profit_pct") or 0.0),
                    sharpe=float(row.get("sharpe") or 0.0),
                    win=float(row.get("win_rate_pct") or 0.0),
                    pf=float(row.get("profit_factor") or 0.0),
                )
            )

    report_path.write_text(
        "\n".join(
            [
                "# Auto-Quant Isolated Seeded BTC Run v1",
                "",
                f"Run id: `{RUN_ID}`",
                f"Gate result: `{gate_result}`",
                f"Board sha256 at generation: `{result['board_sha256_at_generation']}`",
                "",
                "Scope:",
                "- Used the already data-ready 022826 isolated Auto-Quant workspace under `/tmp`.",
                "- Seeded three active BTC-only wrapper strategies into that isolated workspace only.",
                "- Ran Auto-Quant `run.py`; no source/control roots, canonical intake, or repo runtime code were mutated.",
                "",
                "Seeded wrappers:",
                *[f"- `{row['filename']}` sha256 `{row['sha256']}`." for row in wrapper_rows],
                "",
                "Command result:",
                f"- Command: `uv run --with ta-lib run.py`.",
                f"- Exit: `{command['returncode']}`.",
                f"- Done line: succeeded `{done['succeeded']}`, failed `{done['failed']}`.",
                "",
                "Strategy results:",
                *(strategy_lines or ["- No parsable strategy result blocks."]),
                "",
                "Robust summaries:",
                *[
                    f"- `{row.get('strategy')}` robust_sharpe `{row.get('robust_sharpe')}`."
                    for row in robust_blocks
                ],
                "",
                "Decision:",
                "- Accepted rows added: `0`.",
                "- New confidence gate: `false`.",
                "- Canonical merge allowed: `false`.",
                "- Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion rerun allowed: `false`.",
                "- Strict full objective achieved: `false`.",
                "- `update_goal=false`.",
                "",
                "Why non-promoting:",
                "- This is isolated Auto-Quant runtime/backtest evidence only.",
                "- It does not provide source-owned `MainRegimeV2` labels, R6 owner/control rows, explicit `FLIP` approval, per-regime qualifying conditions, cross-market/cycle validation, or canonical merge.",
                "",
                "Artifacts:",
                f"- JSON: `{json_path.relative_to(REPO)}`.",
                f"- Metrics CSV: `{metrics_csv.relative_to(REPO)}`.",
                f"- Wrapper CSV: `{wrappers_csv.relative_to(REPO)}`.",
                f"- Command stdout: `{(CMD / 'autoquant_seeded_run.stdout.txt').relative_to(REPO)}`.",
                f"- Command stderr: `{(CMD / 'autoquant_seeded_run.stderr.txt').relative_to(REPO)}`.",
                f"- Assertions: `{assertions_path.relative_to(REPO)}`.",
                "",
                "Next:",
                "- Preserve the Current Cursor next action for R6. Continue from owner/operator R6 export delivery, explicit `FLIP` approval, or genuinely source-owned cross-timeframe `MainRegimeV2` exports before canonical merge and downstream promotion.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assertions = [
        ("workspace_present", WORKSPACE.exists()),
        ("data_files_ge_3", len(data_files) >= 3),
        ("three_wrappers_seeded", len(wrapper_rows) == 3),
        ("autoquant_run_exit_zero", command["returncode"] == 0),
        ("autoquant_done_all_succeeded", done["succeeded"] == 3 and done["failed"] == 0),
        ("three_trade_result_rows", len(trade_blocks) == 3),
        ("accepted_rows_added_zero", result["accepted_rows_added"] == 0),
        ("canonical_merge_allowed_false", result["canonical_merge_allowed"] is False),
        ("downstream_chain_rerun_allowed_false", result["downstream_chain_rerun_allowed"] is False),
        ("strict_full_objective_achieved_false", result["strict_full_objective_achieved"] is False),
        ("update_goal_false", result["update_goal"] is False),
    ]
    assertions_path.write_text(
        "\n".join(f"{name}={'PASS' if passed else 'FAIL'}" for name, passed in assertions) + "\n",
        encoding="utf-8",
    )
    return 0 if all(passed for _, passed in assertions) else 2


if __name__ == "__main__":
    raise SystemExit(main())
