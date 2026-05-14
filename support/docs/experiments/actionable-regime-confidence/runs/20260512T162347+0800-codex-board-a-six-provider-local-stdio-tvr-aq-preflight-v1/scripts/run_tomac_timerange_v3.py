from __future__ import annotations

import csv
import json
import re
import subprocess
from pathlib import Path


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T162347+0800-codex-board-a-six-provider-local-stdio-tvr-aq-preflight-v1"
)
UNIT_ROOT = RUN_ROOT / "state_iso_v2/auto-quant/agent_material_units"
AUTO_QUANT_PYTHON = Path("/Users/thrill3r/Auto-Quant/.venv/bin/python")
TIMERANGE = "20260101-20260513"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def run_unit(index: int, workspace: Path) -> dict[str, object]:
    config_path = workspace / "config.tomac.json"
    config = json.loads(config_path.read_text())
    original_timerange = config.get("timerange", "")
    config["timerange"] = TIMERANGE
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")

    label = f"13_run_tomac_timerange_v3_group_{index}"
    args = [str(AUTO_QUANT_PYTHON), "run_tomac.py"]
    write_text(RUN_ROOT / f"command-output/{label}.cmd", f"cd {workspace} && {' '.join(args)}\n")
    try:
        proc = subprocess.run(
            args,
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + "\nTIMEOUT after 600s\n"
        code = 124
    write_text(RUN_ROOT / f"command-output/{label}.out", stdout)
    write_text(RUN_ROOT / f"command-output/{label}.err", stderr)
    write_text(RUN_ROOT / f"checks/{label}.exit", f"{code}\n")

    def metric(name: str) -> str:
        m = re.search(rf"^{re.escape(name)}:\s+(.+)$", stdout, flags=re.MULTILINE)
        return m.group(1).strip() if m else ""

    return {
        "group_index": index,
        "workspace": str(workspace),
        "original_timerange": original_timerange,
        "timerange": TIMERANGE,
        "exit": code,
        "succeeded": "Done: 1 succeeded, 0 failed." in stdout and code == 0,
        "strategy": metric("strategy"),
        "sharpe": metric("sharpe"),
        "total_profit_pct": metric("total_profit_pct"),
        "trade_count": metric("trade_count"),
        "win_rate_pct": metric("win_rate_pct"),
        "profit_factor": metric("profit_factor"),
        "error_msg": metric("error_msg"),
    }


def main() -> int:
    workspaces = sorted(UNIT_ROOT.glob("*/aq_workspace"))
    rows = [run_unit(index, workspace) for index, workspace in enumerate(workspaces)]

    csv_path = RUN_ROOT / "summaries/direct_run_tomac_timerange_v3.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "group_index",
        "workspace",
        "original_timerange",
        "timerange",
        "exit",
        "succeeded",
        "strategy",
        "sharpe",
        "total_profit_pct",
        "trade_count",
        "win_rate_pct",
        "profit_factor",
        "error_msg",
    ]
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary = json.loads((RUN_ROOT / "summaries/final_preflight_summary_v2.json").read_text())
    summary.update(
        {
            "timerange_repair_v3": True,
            "timerange_v3": TIMERANGE,
            "direct_run_tomac_rows": rows,
            "direct_run_tomac_succeeded_jobs": sum(1 for row in rows if row["succeeded"]),
            "direct_run_tomac_failed_jobs": sum(1 for row in rows if not row["succeeded"]),
            "accepted_95_contexts_added": 0,
            "pre_bayes_bbn_catboost_execution_tree_ran": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
        }
    )
    (RUN_ROOT / "summaries/final_preflight_summary_v3.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    assertions = [
        ("workspaces_seen_6", len(workspaces) == 6),
        ("direct_run_successes_6", sum(1 for row in rows if row["succeeded"]) == 6),
        ("promotion_allowed_false", not summary["promotion_allowed"]),
        ("trade_usable_false", not summary["trade_usable"]),
        ("update_goal_false", not summary["update_goal"]),
    ]
    write_text(
        RUN_ROOT / "checks/final_preflight_assertions_timerange_v3.out",
        "\n".join(f"{'PASS' if ok else 'FAIL'} {name}" for name, ok in assertions) + "\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
