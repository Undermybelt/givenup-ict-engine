#!/usr/bin/env python3
"""Summarize Auto-Quant bootstrap/prepare readiness command outputs."""

from __future__ import annotations

import csv
import json
from pathlib import Path


RUN_ID = "20260512T021808-codex-autoquant-bootstrap-prepare-readiness-v1"
ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
CMD = ROOT / "command-output"
OUT = ROOT / "autoquant-bootstrap-prepare-readiness-v1"
CHECKS = ROOT / "checks"


def read_text(path: Path) -> str:
    return path.read_text() if path.exists() else ""


def read_json(path: Path) -> dict[str, object]:
    text = read_text(path)
    return json.loads(text) if text.strip() else {}


def read_exit(name: str) -> int | None:
    path = CMD / f"{name}.exit"
    if not path.exists():
        return None
    return int(path.read_text().strip())


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    before = read_json(CMD / "00_auto_quant_status_before.stdout.txt")
    bootstrap = read_json(CMD / "01_auto_quant_bootstrap.stdout.txt")
    after_bootstrap = read_json(CMD / "02_auto_quant_status_after_bootstrap.stdout.txt")
    after_prepare = read_json(CMD / "04_auto_quant_status_after_prepare.stdout.txt")
    prepare_stderr = read_text(CMD / "03_auto_quant_prepare.stderr.txt")

    command_rows = []
    for name in [
        "00_auto_quant_status_before",
        "01_auto_quant_bootstrap",
        "02_auto_quant_status_after_bootstrap",
        "03_auto_quant_prepare",
        "04_auto_quant_status_after_prepare",
    ]:
        command_rows.append(
            {
                "command_id": name,
                "exit": read_exit(name),
                "cmd": read_text(CMD / f"{name}.cmd").strip(),
                "stdout_bytes": (CMD / f"{name}.stdout.txt").stat().st_size if (CMD / f"{name}.stdout.txt").exists() else 0,
                "stderr_bytes": (CMD / f"{name}.stderr.txt").stat().st_size if (CMD / f"{name}.stderr.txt").exists() else 0,
            }
        )

    prepare_error = "Markets were not loaded" if "Markets were not loaded" in prepare_stderr else "unknown"
    payload = {
        "run_id": RUN_ID,
        "gate_result": "autoquant_bootstrap_prepare_readiness_v1=dependency_ready_prepare_failed_data_missing_no_promotion",
        "state_dir": "/tmp/ict-engine-board-a-autoquant-bootstrap-20260512T021808",
        "managed_dir": after_prepare.get("managed_dir"),
        "before_status": before.get("status"),
        "after_bootstrap_status": after_bootstrap.get("status"),
        "after_prepare_status": after_prepare.get("status"),
        "bootstrap_exit": read_exit("01_auto_quant_bootstrap"),
        "prepare_exit": read_exit("03_auto_quant_prepare"),
        "final_dependency_healthy": after_prepare.get("dependency_healthy"),
        "final_bootstrap_needed": after_prepare.get("bootstrap_needed"),
        "final_data_ready": after_prepare.get("data_ready"),
        "final_healthy": after_prepare.get("healthy"),
        "pinned_ref": (bootstrap or {}).get("pinned_ref") or (after_prepare.get("dependency_status") or {}).get("pinned_ref"),
        "prepare_error_summary": prepare_error,
        "prepare_error_contains_binance_exchange_info": "api.binance.com/api/v3/exchangeInfo" in prepare_stderr,
        "command_summary": command_rows,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_promotion_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r3_r5_r6_roots_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    write_csv(
        OUT / "autoquant_bootstrap_prepare_command_summary_v1.csv",
        command_rows,
        ["command_id", "exit", "cmd", "stdout_bytes", "stderr_bytes"],
    )
    (OUT / "autoquant_bootstrap_prepare_readiness_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )

    report = f"""# Auto-Quant Bootstrap Prepare Readiness v1

Run id: `{RUN_ID}`

Gate result: `{payload['gate_result']}`.

## Command Result

- Before bootstrap: `{payload['before_status']}`.
- Bootstrap exit: `{payload['bootstrap_exit']}`; dependency pinned ref `{payload['pinned_ref']}`.
- After bootstrap: `{payload['after_bootstrap_status']}`.
- Prepare exit: `{payload['prepare_exit']}`.
- After prepare: `{payload['after_prepare_status']}`, dependency healthy `{payload['final_dependency_healthy']}`, data ready `{payload['final_data_ready']}`.
- Prepare failure summary: `{payload['prepare_error_summary']}`; stderr references Binance exchangeInfo `{payload['prepare_error_contains_binance_exchange_info']}`.

## Decision

This improves Auto-Quant dependency readiness from `missing_dependency` to `dependency_ready_data_missing`, but it is not a promoting Auto-Quant run. Data readiness is still false because prepare failed while loading Binance markets. No accepted Board A source/control rows, confidence gates, canonical merge, or downstream rerun are created by this packet.

Accepted rows added: `0`.
New confidence gate: false.
Canonical merge allowed: false.
Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion rerun allowed: false.
Strict full objective achieved: false.
`update_goal=false`.

## Next

Preserve the Current Cursor next action for R6. If Auto-Quant readiness is continued, use the already bootstrapped `/tmp` state and solve data readiness without treating dependency readiness as Board A acceptance evidence.
"""
    (OUT / "autoquant_bootstrap_prepare_readiness_v1.md").write_text(report)

    assertions = {
        "bootstrap_exit_zero": payload["bootstrap_exit"] == 0,
        "prepare_exit_one": payload["prepare_exit"] == 1,
        "dependency_healthy_true": payload["final_dependency_healthy"] is True,
        "bootstrap_needed_false": payload["final_bootstrap_needed"] is False,
        "data_ready_false": payload["final_data_ready"] is False,
        "status_dependency_ready_data_missing": payload["after_prepare_status"] == "dependency_ready_data_missing",
        "prepare_error_detected": payload["prepare_error_summary"] != "unknown",
        "accepted_rows_zero": payload["accepted_rows_added"] == 0,
        "new_confidence_gate_false": payload["new_confidence_gate"] is False,
        "canonical_merge_false": payload["canonical_merge_allowed"] is False,
        "downstream_rerun_false": payload["downstream_promotion_rerun_allowed"] is False,
        "strict_objective_false": payload["strict_full_objective_achieved"] is False,
        "update_goal_false": payload["update_goal"] is False,
    }
    (CHECKS / "autoquant_bootstrap_prepare_readiness_v1_assertions.out").write_text(
        "\n".join(f"{name}={'PASS' if ok else 'FAIL'}" for name, ok in assertions.items()) + "\n"
    )
    if not all(assertions.values()):
        raise SystemExit("Auto-Quant readiness assertions failed")


if __name__ == "__main__":
    main()
