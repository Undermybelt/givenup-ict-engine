#!/usr/bin/env python3
"""Summarize Auto-Quant local run readback after 065116."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


RUN_ID = "20260512T065824+0800-codex-autoquant-local-run-readback-after-065116-v1"
GATE_RESULT = (
    "autoquant_local_run_readback_after_065116_v1="
    "status_data_ready_but_run_dns_blocked_no_promotion"
)
SCRIPT = Path(__file__).resolve()
RUN_ROOT = SCRIPT.parents[1]
REPO = SCRIPT.parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
COMMAND = RUN_ROOT / "command-output"
OUT_DIR = RUN_ROOT / "autoquant-local-run-readback-after-065116-v1"
CHECK_DIR = RUN_ROOT / "checks"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_exit(path: Path) -> int | None:
    try:
        return int(read_text(path).strip())
    except ValueError:
        return None


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    status_064259 = read_json(COMMAND / "00_auto_quant_status_064259_state.stdout.json")
    status_global = read_json(COMMAND / "01_auto_quant_status_global_local.stdout.json")
    run_stdout = read_text(COMMAND / "04_autoquant_run_064259_state.stdout.txt")
    run_stderr = read_text(COMMAND / "04_autoquant_run_064259_state.stderr.txt")
    state_strategies = [
        line.strip()
        for line in read_text(COMMAND / "02_state_strategy_files.txt").splitlines()
        if line.strip()
    ]
    active_state_strategies = [
        path for path in state_strategies if not Path(path).name.startswith("_")
    ]
    tmp_strategies = [
        line.strip()
        for line in read_text(COMMAND / "03_tmp_strategy_files.txt").splitlines()
        if line.strip()
    ]

    run_exit = read_exit(COMMAND / "04_autoquant_run_064259_state.exit")
    status_exit = read_exit(COMMAND / "00_auto_quant_status_064259_state.exit")
    global_exit = read_exit(COMMAND / "01_auto_quant_status_global_local.exit")
    discovered_match = re.search(r"Discovered (\d+) strategies: ([^\n]+)", run_stdout)
    succeeded_match = re.search(r"Done: (\d+) backtests succeeded, (\d+) failed", run_stdout)
    error_type_match = re.search(r"error_type:\s+([A-Za-z0-9_]+)", run_stdout)
    error_msg_match = re.search(r"error_msg:\s+(.+)", run_stdout)

    result = {
        "run_id": RUN_ID,
        "gate_result": GATE_RESULT,
        "board_sha256_before_artifact": sha256_file(BOARD),
        "status_064259_exit": status_exit,
        "status_064259": status_064259.get("status"),
        "status_064259_data_ready": status_064259.get("data_ready"),
        "status_064259_recommended_command": status_064259.get("recommended_next_command"),
        "global_local_status_exit": global_exit,
        "global_local_status": status_global.get("status"),
        "global_local_data_ready": status_global.get("data_ready"),
        "global_local_blocked_reason": (status_global.get("next_step") or {}).get("blocked_reason"),
        "state_strategy_file_count": len(state_strategies),
        "active_state_strategy_count": len(active_state_strategies),
        "state_strategies": state_strategies,
        "active_state_strategies": active_state_strategies,
        "tmp_strategy_count": len(tmp_strategies),
        "tmp_strategy_sample": tmp_strategies[:40],
        "autoquant_run_exit": run_exit,
        "autoquant_discovered_strategy_count": int(discovered_match.group(1)) if discovered_match else None,
        "autoquant_discovered_strategies": discovered_match.group(2) if discovered_match else "",
        "backtests_succeeded": int(succeeded_match.group(1)) if succeeded_match else None,
        "backtests_failed": int(succeeded_match.group(2)) if succeeded_match else None,
        "error_type": error_type_match.group(1) if error_type_match else "",
        "error_msg": error_msg_match.group(1).strip() if error_msg_match else "",
        "dns_error_present": "Could not contact DNS servers" in run_stderr,
        "exchange_info_error_present": "api.binance.com/api/v3/exchangeInfo" in run_stderr,
        "root_cause": (
            "Auto-Quant status can be data_ready=true from local feather files, but run.py "
            "constructs Freqtrade Backtesting with the Binance exchange config. Freqtrade "
            "loads Binance markets through CCXT before backtesting, so DNS failure to "
            "api.binance.com blocks run.py even when local OHLCV feathers and one active "
            "strategy are present."
        ),
        "accepted_rows_added": 0,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    json_path = OUT_DIR / "autoquant_local_run_readback_after_065116_v1.json"
    report_path = OUT_DIR / "autoquant_local_run_readback_after_065116_v1.md"
    command_csv = OUT_DIR / "autoquant_local_run_command_summary_v1.csv"
    strategy_csv = OUT_DIR / "autoquant_strategy_inventory_after_065116_v1.csv"
    assertions_path = CHECK_DIR / "autoquant_local_run_readback_after_065116_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with command_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["command_id", "exit_code", "status", "data_ready", "note"])
        writer.writeheader()
        writer.writerow(
            {
                "command_id": "00_auto_quant_status_064259_state",
                "exit_code": status_exit,
                "status": status_064259.get("status"),
                "data_ready": status_064259.get("data_ready"),
                "note": "current 064259 state status",
            }
        )
        writer.writerow(
            {
                "command_id": "01_auto_quant_status_global_local",
                "exit_code": global_exit,
                "status": status_global.get("status"),
                "data_ready": status_global.get("data_ready"),
                "note": f"global local repo next blocker={(status_global.get('next_step') or {}).get('blocked_reason')}",
            }
        )
        writer.writerow(
            {
                "command_id": "04_autoquant_run_064259_state",
                "exit_code": run_exit,
                "status": result["error_type"] or "unknown",
                "data_ready": status_064259.get("data_ready"),
                "note": result["error_msg"],
            }
        )

    with strategy_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["surface", "path"])
        writer.writeheader()
        for path in state_strategies:
            writer.writerow({"surface": "064259_state", "path": path})
        for path in tmp_strategies[:120]:
            writer.writerow({"surface": "tmp_strategy_inventory_sample", "path": path})

    report = [
        "# Auto-Quant Local Run Readback After 065116 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE_RESULT}`",
        "",
        f"Board sha256 before artifact: `{result['board_sha256_before_artifact']}`",
        "",
        "## Scope",
        "",
        "Read-only runtime follow-up after the `065116` Auto-Quant bootstrap/prepare reconciliation. "
        "This packet checks whether the currently prepared `064259` Auto-Quant state can actually "
        "execute `run.py`. It does not mutate source/control roots, run canonical merge, promote "
        "regime confidence, make a trade claim, or call `update_goal`.",
        "",
        "## Findings",
        "",
        f"- Current `064259` Auto-Quant status exit `{status_exit}` reports "
        f"`{status_064259.get('status')}` with `data_ready={status_064259.get('data_ready')}`.",
        f"- Global local Auto-Quant status exit `{global_exit}` reports "
        f"`{status_global.get('status')}` with `data_ready={status_global.get('data_ready')}` and "
        f"blocked reason `{(status_global.get('next_step') or {}).get('blocked_reason')}`.",
        f"- Current `064259` state has `{len(active_state_strategies)}` active non-underscore strategy file(s): "
        f"`{', '.join(Path(p).name for p in active_state_strategies) or 'none'}` "
        f"(`{len(state_strategies)}` strategy-directory file(s) including templates).",
        f"- Bounded `/tmp` strategy inventory found `{len(tmp_strategies)}` active strategy-file path(s).",
        f"- `run.py` exit code `{run_exit}`; discovered strategy count "
        f"`{result['autoquant_discovered_strategy_count']}`; backtests succeeded "
        f"`{result['backtests_succeeded']}`, failed `{result['backtests_failed']}`.",
        f"- Run failure: `{result['error_type']}` / `{result['error_msg']}`.",
        f"- DNS blocker observed: `dns_error_present={result['dns_error_present']}`, "
        f"`exchange_info_error_present={result['exchange_info_error_present']}`.",
        "",
        "## Root Cause",
        "",
        result["root_cause"],
        "",
        "## Board A Accounting",
        "",
        "This is real Auto-Quant runtime evidence, but it is non-promoting. `data_ready=true` is "
        "not enough to prove executable Auto-Quant completion because the oracle still tries to "
        "load Binance market metadata before backtesting. The earlier `023312` seeded-strategy "
        "Auto-Quant run remains historical non-promoting evidence; this packet records the current "
        "`064259` state behavior.",
        "",
        "Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired "
        "false; canonical merge false; downstream promotion rerun false; strict full objective false; "
        "trade usable false; `update_goal=false`.",
        "",
        "## Next",
        "",
        "Do not treat this Auto-Quant run attempt as Board A promotion evidence. Continue from a valid "
        "source/control unlock first. Separately, if Auto-Quant runtime closure is needed, the next "
        "technical slice should use an offline-safe exchange/market-metadata path or a previously "
        "prepared seeded state known to complete `run.py`, then still keep it non-promoting until "
        "R3/R5/R6 source/control gates unlock.",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = {
        "gate_result": GATE_RESULT,
        "status_064259_data_ready": str(status_064259.get("data_ready")).lower(),
        "autoquant_run_exit": run_exit,
        "active_state_strategy_count": result["active_state_strategy_count"],
        "autoquant_discovered_strategy_count": result["autoquant_discovered_strategy_count"],
        "backtests_succeeded": result["backtests_succeeded"],
        "backtests_failed": result["backtests_failed"],
        "dns_error_present": str(result["dns_error_present"]).lower(),
        "exchange_info_error_present": str(result["exchange_info_error_present"]).lower(),
        "valid_required_root_unlock": "false",
        "source_control_evidence_acquired": "false",
        "canonical_merge": "false",
        "downstream_promotion_rerun": "false",
        "strict_full_objective": "false",
        "trade_usable": "false",
        "update_goal": "false",
    }
    assertions_path.write_text(
        "\n".join(f"{key}={value}" for key, value in assertions.items()) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
