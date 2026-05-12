from __future__ import annotations

import csv
import json
import re
from pathlib import Path


RUN_ID = "20260512T092558+0800-codex-board-b-032157-non-promoting-multicadence-feedback-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
RAW = RUN_ROOT / "raw"
CHECKS = RUN_ROOT / "checks"
OUT = RUN_ROOT / "non-promoting-multicadence-rerun-readback-v1"


def read_exit(path: Path) -> int | None:
    if not path.exists():
        return None
    text = path.read_text()
    m = re.search(r"=(\d+)", text)
    return int(m.group(1)) if m else None


def parse_blocks(stdout: str) -> list[dict]:
    blocks: list[dict] = []
    for block in stdout.split("\n---\n"):
        if "strategy:" not in block:
            continue
        row: dict[str, object] = {}
        for line in block.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key in {
                "strategy",
                "commit",
                "status",
                "error_type",
                "error_msg",
                "sharpe",
                "sortino",
                "calmar",
                "total_profit_pct",
                "max_drawdown_pct",
                "trade_count",
                "win_rate_pct",
                "profit_factor",
            }:
                row[key] = value
        if "strategy" not in row:
            continue
        if row.get("status") == "ERROR":
            row["outcome"] = "failed"
            row.setdefault("trade_count", 0)
        else:
            row["outcome"] = "succeeded"
            for key in [
                "sharpe",
                "sortino",
                "calmar",
                "total_profit_pct",
                "max_drawdown_pct",
                "win_rate_pct",
                "profit_factor",
            ]:
                row[key] = float(row.get(key, 0.0))
            row["trade_count"] = int(row.get("trade_count", 0))
        blocks.append(row)
    return blocks


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    stdout = (RAW / "run_tomac_rerun.stdout.txt").read_text()
    stderr = (RAW / "run_tomac_rerun.stderr.txt").read_text()
    rows = parse_blocks(stdout)
    successes = [r for r in rows if r["outcome"] == "succeeded"]
    failures = [r for r in rows if r["outcome"] == "failed"]
    total_trades = sum(int(r.get("trade_count", 0)) for r in successes)
    max_sharpe = max([float(r.get("sharpe", 0.0)) for r in successes], default=0.0)
    max_profit = max([float(r.get("total_profit_pct", 0.0)) for r in successes], default=0.0)

    first_failure = "unknown"
    if failures:
        first_failure = str(failures[0].get("error_msg", "unknown"))

    packet = {
        "run_id": RUN_ID,
        "schema_version": "non-promoting-multicadence-rerun-readback/v1",
        "mode": "incubation_only",
        "feedback_label": "non_promoting_aq_feedback",
        "parent_candidate": "032157/034002-downstream-combined-v1",
        "auto_quant_prepare_exit": read_exit(CHECKS / "auto_quant_prepare.exit.out"),
        "run_tomac_initial_exit": read_exit(CHECKS / "run_tomac.exit.out"),
        "run_tomac_rerun_exit": read_exit(CHECKS / "run_tomac_rerun.exit.out"),
        "normalized_pair": "NQ/USD",
        "strategies_discovered": len(rows),
        "strategies_succeeded": len(successes),
        "strategies_failed": len(failures),
        "successful_strategy_trades_total": total_trades,
        "successful_strategy_max_sharpe": max_sharpe,
        "successful_strategy_max_profit_pct": max_profit,
        "first_failure_reason": first_failure,
        "data_window_observation": {
            "nq_1h_start": "2025-12-15T12:00:00Z",
            "nq_4h_start": "2025-12-15T12:00:00Z",
            "nq_1d_start": "2025-12-15T00:00:00Z",
            "short_window": True,
        },
        "strategies": rows,
        "source_control_evidence_acquired": False,
        "explicit_user_selected_history": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "promotion_allowed": False,
        "update_goal": False,
        "gate_result": "fail_closed:incubation_only_zero_trade_short_window",
        "board_a_feedback": (
            "Synthetic multicadence staging works after NQ/USD normalization, "
            "but this 032157/034002 slice is too short and produced zero "
            "successful-strategy trades; use as negative search feedback only."
        ),
        "next": (
            "Prefer recorded historical replay or a longer explicit historical "
            "path before another Auto-Quant feedback loop; do not run production "
            "promotion from this packet."
        ),
        "source_artifacts": [
            str(RAW / "auto_quant_prepare.stdout.txt"),
            str(RAW / "run_tomac.stdout.txt"),
            str(RAW / "run_tomac.stderr.txt"),
            str(RAW / "run_tomac_rerun.stdout.txt"),
            str(RAW / "run_tomac_rerun.stderr.txt"),
            str(RAW / "pre_bayes_status_json.stdout.txt"),
            str(RAW / "policy_training_status_json.stdout.txt"),
            str(RAW / "workflow_status_execution_candidate_agent.stdout.txt"),
        ],
    }

    json_path = OUT / "non_promoting_multicadence_rerun_readback_v1.json"
    json_path.write_text(json.dumps(packet, indent=2) + "\n")

    csv_path = OUT / "non_promoting_multicadence_rerun_readback_v1.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "strategy",
                "outcome",
                "trade_count",
                "sharpe",
                "total_profit_pct",
                "win_rate_pct",
                "profit_factor",
                "error_msg",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "strategy": row.get("strategy", ""),
                "outcome": row.get("outcome", ""),
                "trade_count": row.get("trade_count", 0),
                "sharpe": row.get("sharpe", ""),
                "total_profit_pct": row.get("total_profit_pct", ""),
                "win_rate_pct": row.get("win_rate_pct", ""),
                "profit_factor": row.get("profit_factor", ""),
                "error_msg": row.get("error_msg", ""),
            })

    md_rows = []
    for row in rows:
        md_rows.append(
            "| `{}` | {} | {} | {} | {} | {} |".format(
                row.get("strategy", ""),
                row.get("outcome", ""),
                row.get("trade_count", 0),
                row.get("sharpe", "N/A"),
                row.get("total_profit_pct", "N/A"),
                row.get("error_msg", ""),
            )
        )

    md_path = OUT / "non_promoting_multicadence_rerun_readback_v1.md"
    md_path.write_text(
        "\n".join([
            "# Non-Promoting Multicadence Rerun Readback v1",
            "",
            f"Run id: `{RUN_ID}`",
            "",
            "Lane labels: `incubation_only`, `non_promoting_aq_feedback`.",
            "",
            "This is a supplemental readback for the clean rerun after Auto-Quant prepare normalized the synthetic pair to `NQ/USD`. It does not edit the current cursor, does not select user history, does not promote selected-data AutoQuant, does not run the production promotion chain, and does not call `update_goal`.",
            "",
            "## Result",
            "",
            f"- `auto_quant_prepare_exit={packet['auto_quant_prepare_exit']}`",
            f"- `run_tomac_initial_exit={packet['run_tomac_initial_exit']}`",
            f"- `run_tomac_rerun_exit={packet['run_tomac_rerun_exit']}`",
            f"- strategies discovered `{len(rows)}`; succeeded `{len(successes)}`; failed `{len(failures)}`",
            f"- successful-strategy trades total `{total_trades}`",
            f"- best successful-strategy Sharpe `{max_sharpe:.4f}`",
            f"- best successful-strategy profit pct `{max_profit:.4f}`",
            "",
            "| Strategy | Outcome | Trades | Sharpe | Profit % | Error |",
            "|---|---:|---:|---:|---:|---|",
            *md_rows,
            "",
            "## Interpretation",
            "",
            "Synthetic multicadence staging is now runnable after `NQ/USD` normalization, but this local `032157/034002` slice is too short for useful Auto-Quant discovery: successful strategies emitted zero trades, and the two higher-startup strategies failed after startup-candle adjustment.",
            "",
            "Gate: `fail_closed:incubation_only_zero_trade_short_window`.",
            "",
            "Promotion allowed: `false`.",
            "",
            "`update_goal=false`.",
            "",
            "## Next",
            "",
            "Use this as negative search feedback only. Prefer recorded historical replay or a longer explicit historical path before another Auto-Quant feedback loop; do not run production promotion from this packet.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- CSV: `{csv_path}`",
            "- Raw rerun stdout/stderr: `raw/run_tomac_rerun.stdout.txt`, `raw/run_tomac_rerun.stderr.txt`",
            "",
        ])
        + "\n"
    )

    assertions = [
        f"run_id={RUN_ID}",
        "mode=incubation_only",
        "feedback_label=non_promoting_aq_feedback",
        f"auto_quant_prepare_exit={packet['auto_quant_prepare_exit']}",
        f"run_tomac_rerun_exit={packet['run_tomac_rerun_exit']}",
        f"strategies_discovered={len(rows)}",
        f"strategies_succeeded={len(successes)}",
        f"strategies_failed={len(failures)}",
        f"successful_strategy_trades_total={total_trades}",
        f"successful_strategy_max_sharpe={max_sharpe:.4f}",
        "source_control_evidence_acquired=false",
        "explicit_user_selected_history=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "promotion_allowed=false",
        "update_goal=false",
        "gate_result=fail_closed:incubation_only_zero_trade_short_window",
    ]
    (CHECKS / "non_promoting_multicadence_rerun_readback_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
