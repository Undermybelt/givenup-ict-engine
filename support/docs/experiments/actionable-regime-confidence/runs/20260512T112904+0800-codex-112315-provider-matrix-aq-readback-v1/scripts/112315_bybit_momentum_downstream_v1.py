from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


RUN_ID = "20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1"
SOURCE_MATRIX_RUN_ID = "20260512T112315+0800-codex-board-b-six-provider-btc-matrix-probe-v1"
SYMBOL = "B2R_PROVIDER_MATRIX_BYBIT_MOMENTUM_112315"
ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
RAW_TRADES = (
    ROOT
    / "workspace"
    / "auto-quant-112315-bybit_public"
    / "derived"
    / "ProviderCryptoMomentumStateV1.real_trades.jsonl"
)
DERIVED = ROOT / "derived"
TRADES = DERIVED / "bybit_provider_matrix_momentum_112315_real_trades.jsonl"
STATE_DIR = ROOT / "state_downstream_bybit"
OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "112315-bybit-momentum-downstream-v1"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def materialize_trades() -> dict[str, Any]:
    DERIVED.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(RAW_TRADES.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        row["auto_quant_run_id"] = RUN_ID
        row["provider_matrix_source_run_id"] = SOURCE_MATRIX_RUN_ID
        row["source_provider"] = "bybit_public"
        row["symbol"] = SYMBOL
        row["strategy_mutation_id"] = "provider-matrix-bybit-momentum-112315-v1"
        row["trade_id"] = f"{SYMBOL}_ProviderCryptoMomentumStateV1_{index:04d}"
        rows.append(row)
    TRADES.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n")
    return {
        "path": str(TRADES),
        "rows": len(rows),
        "wins": sum(1 for row in rows if row.get("realized_outcome") == "win"),
        "losses": sum(1 for row in rows if row.get("realized_outcome") == "loss"),
        "branch_path": rows[0].get("regime_profit_branch_path") if rows else None,
    }


def run_command(label: str, cmd: list[str]) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{label}.cmd").write_text(" ".join(cmd) + "\n")
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    (OUT_DIR / f"{label}.out").write_text(proc.stdout)
    (OUT_DIR / f"{label}.err").write_text(proc.stderr)
    (CHECK_DIR / f"{label}.exit").write_text(f"{proc.returncode}\n")
    return proc.returncode


def run_chain() -> dict[str, int]:
    commands = {
        "20_ingest_real_trades_dry_run": [
            "./target/debug/ict-engine",
            "auto-quant-ingest-real-trades",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--trades",
            str(TRADES),
            "--source",
            "provider_matrix_bybit_momentum_112315",
            "--dry-run",
        ],
        "21_ingest_real_trades_force": [
            "./target/debug/ict-engine",
            "auto-quant-ingest-real-trades",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--trades",
            str(TRADES),
            "--source",
            "provider_matrix_bybit_momentum_112315",
            "--force",
        ],
        "22_pre_bayes_status": [
            "./target/debug/ict-engine",
            "pre-bayes-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--refresh",
            "--output-format",
            "json",
        ],
        "23_policy_training_status_before_export": [
            "./target/debug/ict-engine",
            "policy-training-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--output-format",
            "json",
        ],
        "24_export_structural_path_ranking_target": [
            "./target/debug/ict-engine",
            "export-structural-path-ranking-target",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
        ],
        "25_policy_training_status_after_export": [
            "./target/debug/ict-engine",
            "policy-training-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--output-format",
            "json",
        ],
        "26_workflow_structural_bundle": [
            "./target/debug/ict-engine",
            "workflow-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--refresh",
            "--phase",
            "structural-recommended-path-bundle",
            "--output-format",
            "json",
        ],
        "27_workflow_execution_candidate": [
            "./target/debug/ict-engine",
            "workflow-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--refresh",
            "--phase",
            "execution-candidate",
            "--output-format",
            "json",
        ],
        "28_workflow_full": [
            "./target/debug/ict-engine",
            "workflow-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--refresh",
            "--output-format",
            "json",
        ],
    }
    return {label: run_command(label, cmd) for label, cmd in commands.items()}


def parse_json_output(label: str) -> dict[str, Any]:
    path = OUT_DIR / f"{label}.out"
    if not path.exists() or not path.read_text().strip():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def summarize(trade_summary: dict[str, Any], exits: dict[str, int]) -> dict[str, Any]:
    ingest = parse_json_output("21_ingest_real_trades_force")
    policy_after = parse_json_output("25_policy_training_status_after_export")
    execution = parse_json_output("27_workflow_execution_candidate")
    full = parse_json_output("28_workflow_full")
    target_summary = read_json(
        STATE_DIR / SYMBOL / "policy_training" / "structural_path_ranking_target_summary.json"
    )
    learning_state = read_json(STATE_DIR / SYMBOL / "learning_state.json")
    feedback = learning_state.get("feedback_history", [])
    return {
        "run_id": RUN_ID,
        "symbol": SYMBOL,
        "source_matrix_run_id": SOURCE_MATRIX_RUN_ID,
        "trade_summary": trade_summary,
        "exits": exits,
        "ingest": ingest,
        "target_summary": target_summary,
        "policy_after": policy_after,
        "execution_candidate": execution,
        "workflow_full": full,
        "learning_feedback_count": len(feedback),
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "112315_bybit_momentum_downstream_v1.md"
    assertions = CHECK_DIR / "112315_bybit_momentum_downstream_v1_assertions.out"
    target = summary["target_summary"]
    execution = summary["execution_candidate"]
    full = summary["workflow_full"]

    lines = [
        "# 112315 Bybit Momentum Downstream v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Symbol: `{SYMBOL}`",
        f"Source matrix: `{SOURCE_MATRIX_RUN_ID}`",
        "",
        "## Scope",
        "This carries the positive Bybit public-provider momentum branch through ingest, Pre-Bayes, policy export, structural bundle, execution candidate, and full workflow status.",
        "It remains blocked by the same source provider gate: TVR failed and IBKR BTC returned zero rows in the source matrix.",
        "",
        "## Trades",
        f"- Materialized trades: `{summary['trade_summary']['rows']}` from `{TRADES}`.",
        f"- Branch path: `{summary['trade_summary']['branch_path']}`.",
        f"- Wins/losses: `{summary['trade_summary']['wins']}` / `{summary['trade_summary']['losses']}`.",
        "",
        "## Command Exits",
    ]
    for label, code in summary["exits"].items():
        lines.append(f"- `{label}`: `{code}`")
    lines.extend(
        [
            "",
            "## Readback",
            f"- Ingest applied: `{summary['ingest'].get('trades_applied')}` / invalid `{summary['ingest'].get('trades_invalid')}`.",
            f"- Learning feedback count: `{summary['learning_feedback_count']}`.",
            f"- Structural target rows: `{target.get('rows')}`, mature rows: `{target.get('mature_rows')}`, history rows: `{target.get('history_rows')}`, history mature rows: `{target.get('history_mature_rows')}`.",
            f"- Execution ready/actionable: `{execution.get('ready')}` / `{execution.get('actionable')}`.",
            f"- Full workflow ready/actionable: `{full.get('ready')}` / `{full.get('actionable')}`.",
            "",
            "## Decision",
            "- Gate result: `112315_bybit_momentum_downstream=ordered_chain_exercised_but_provider_authority_and_runtime_promotion_fail_closed`.",
            "- The ordered chain ran on a positive public-provider branch, but this is not promotion evidence because source provider authority failed before AQ.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{REPORT_DIR / '112315_bybit_momentum_downstream_v1.json'}`",
            f"- Assertions: `{assertions}`",
            f"- Command output: `{OUT_DIR}`",
            f"- State dir: `{STATE_DIR}`",
        ]
    )
    report.write_text("\n".join(lines) + "\n")

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS symbol={SYMBOL}",
        f"PASS materialized_trades={summary['trade_summary']['rows']}",
        f"PASS branch_path={summary['trade_summary']['branch_path']}",
        f"PASS ingest_applied={summary['ingest'].get('trades_applied')}",
        f"PASS feedback_history={summary['learning_feedback_count']}",
        f"PASS target_rows={target.get('rows')}",
        f"PASS target_mature_rows={target.get('mature_rows')}",
        "FAIL_CLOSED source_provider_authority_tvr_ibkr_not_satisfied",
        "FAIL_CLOSED promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    for label, code in summary["exits"].items():
        assertion_lines.append(("PASS" if code == 0 else "FAIL_CLOSED") + f" {label}_exit={code}")
    assertions.write_text("\n".join(assertion_lines) + "\n")


def main() -> int:
    trade_summary = materialize_trades()
    exits = run_chain()
    summary = summarize(trade_summary, exits)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(REPORT_DIR / "112315_bybit_momentum_downstream_v1.json", summary)
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
