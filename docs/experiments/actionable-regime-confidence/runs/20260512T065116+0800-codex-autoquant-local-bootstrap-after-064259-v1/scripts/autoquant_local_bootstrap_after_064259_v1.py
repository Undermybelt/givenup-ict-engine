#!/usr/bin/env python3
"""Summarize isolated Auto-Quant local bootstrap attempt after 064259."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T065116+0800-codex-autoquant-local-bootstrap-after-064259-v1"
GATE = "autoquant_local_bootstrap_after_064259_v1=dependency_bootstrapped_prepare_dns_blocked_no_board_a_promotion"
RUN_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = RUN_ROOT / "autoquant-local-bootstrap-after-064259-v1"
CHECK_DIR = RUN_ROOT / "checks"
COMMAND_DIR = RUN_ROOT / "command-output"


def read_text(name: str) -> str:
    path = COMMAND_DIR / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def read_json(name: str) -> dict:
    text = read_text(name)
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        return {}


def read_exit(name: str) -> str:
    return read_text(name).strip()


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    bootstrap = read_json("auto_quant_bootstrap_local.stdout")
    status_bootstrap = read_json("auto_quant_status_after_bootstrap.stdout")
    status_prepare = read_json("auto_quant_status_after_prepare.stdout")
    prepare_stderr = read_text("auto_quant_prepare.stderr")
    prepare_blocker = "unknown"
    if "Could not contact DNS servers" in prepare_stderr or "api.binance.com" in prepare_stderr:
        prepare_blocker = "binance_dns_or_network_unavailable"
    elif "TA-Lib" in prepare_stderr:
        prepare_blocker = "ta_lib_dependency"

    result = {
        "run_id": RUN_ID,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": GATE,
        "state_dir": "/tmp/ict-engine-board-a-064259-runtime-v1",
        "commands": {
            "bootstrap_exit": read_exit("auto_quant_bootstrap_local.exit"),
            "status_after_bootstrap_exit": read_exit("auto_quant_status_after_bootstrap.exit"),
            "prepare_exit": read_exit("auto_quant_prepare.exit"),
            "status_after_prepare_exit": read_exit("auto_quant_status_after_prepare.exit"),
        },
        "bootstrap": {
            "repo_url": bootstrap.get("repo_url"),
            "managed_dir": bootstrap.get("managed_dir"),
            "current_commit": bootstrap.get("current_commit"),
            "healthy": bootstrap.get("healthy"),
            "bootstrap_needed": bootstrap.get("bootstrap_needed"),
            "update_available": bootstrap.get("update_available"),
        },
        "status_after_bootstrap": {
            "status": status_bootstrap.get("status"),
            "healthy": status_bootstrap.get("healthy"),
            "bootstrap_needed": status_bootstrap.get("bootstrap_needed"),
            "dependency_healthy": status_bootstrap.get("dependency_healthy"),
            "data_ready": status_bootstrap.get("data_ready"),
        },
        "status_after_prepare": {
            "status": status_prepare.get("status"),
            "healthy": status_prepare.get("healthy"),
            "bootstrap_needed": status_prepare.get("bootstrap_needed"),
            "dependency_healthy": status_prepare.get("dependency_healthy"),
            "data_ready": status_prepare.get("data_ready"),
        },
        "prepare_blocker": prepare_blocker,
        "board_a_accounting": {
            "accepted_rows_added": 0,
            "source_control_evidence_acquired": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "next_action": (
            "Treat this as runtime dependency improvement only. Auto-Quant dependency is now bootstrapped "
            "from the local checkout in the isolated state, but data preparation is blocked by Binance DNS/network. "
            "Board A still requires a real R3/R5/R6 source/control unlock before canonical merge or downstream promotion."
        ),
    }

    json_path = ARTIFACT_DIR / "autoquant_local_bootstrap_after_064259_v1.json"
    md_path = ARTIFACT_DIR / "autoquant_local_bootstrap_after_064259_v1.md"
    assertions = CHECK_DIR / "autoquant_local_bootstrap_after_064259_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_path.write_text(
        "\n".join(
            [
                "# AutoQuant Local Bootstrap After 064259 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{GATE}`",
                "",
                "## Readback",
                "",
                f"- Bootstrap exit: `{result['commands']['bootstrap_exit']}`.",
                f"- Bootstrap repo URL: `{result['bootstrap']['repo_url']}`.",
                f"- Managed dir: `{result['bootstrap']['managed_dir']}`.",
                f"- Dependency healthy after bootstrap: `{result['status_after_bootstrap']['dependency_healthy']}`.",
                f"- Status after bootstrap: `{result['status_after_bootstrap']['status']}`.",
                f"- Prepare exit: `{result['commands']['prepare_exit']}`.",
                f"- Prepare blocker: `{prepare_blocker}`.",
                f"- Status after prepare: `{result['status_after_prepare']['status']}`.",
                "",
                "## Accounting",
                "",
                "- This improves the isolated Auto-Quant dependency state from `missing_dependency` to `dependency_ready_data_missing`.",
                "- It does not acquire Board A source/control evidence and does not permit canonical merge or downstream promotion.",
                "- Accepted rows added: `0`; strict full objective: `false`; trade usable: `false`; `update_goal=false`.",
                "",
                "## Next",
                "",
                result["next_action"],
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions.write_text(
        "\n".join(
            [
                f"gate_result={GATE}",
                f"bootstrap_exit={result['commands']['bootstrap_exit']}",
                f"prepare_exit={result['commands']['prepare_exit']}",
                f"dependency_healthy_after_bootstrap={str(result['status_after_bootstrap']['dependency_healthy']).lower()}",
                f"data_ready_after_prepare={str(result['status_after_prepare']['data_ready']).lower()}",
                f"prepare_blocker={prepare_blocker}",
                "accepted_rows_added=0",
                "source_control_evidence_acquired=false",
                "canonical_merge=false",
                "downstream_promotion_rerun=false",
                "strict_full_objective=false",
                "trade_usable=false",
                "update_goal=false",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
