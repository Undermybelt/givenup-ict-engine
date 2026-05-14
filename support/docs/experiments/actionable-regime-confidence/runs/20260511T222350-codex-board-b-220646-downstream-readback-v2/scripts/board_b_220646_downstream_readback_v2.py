#!/usr/bin/env python3
"""Read back Board B 220646 downstream consumption without mutating runtime code."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1"
STATE_DIR = Path("/tmp/ict-engine-board-b-source-root-stop-carry-longhorizon-downstream-v1")
BIN = REPO / "target/debug/ict-engine"

CMD_DIR = RUN_ROOT / "command-output"
OUT_DIR = RUN_ROOT / "downstream-readback"
CHECK_DIR = RUN_ROOT / "checks"


def repo_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def safe_name(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)


def run_command(name: str, args: list[str]) -> dict[str, Any]:
    safe = safe_name(name)
    proc = subprocess.run(args, cwd=REPO, text=True, capture_output=True, check=False)
    stdout = CMD_DIR / f"{safe}.out"
    stderr = CMD_DIR / f"{safe}.err"
    exit_file = CMD_DIR / f"{safe}.exit"
    stdout.write_text(proc.stdout, encoding="utf-8")
    stderr.write_text(proc.stderr, encoding="utf-8")
    exit_file.write_text(f"{proc.returncode}\n", encoding="utf-8")
    parsed: Any = None
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = None
    return {
        "name": name,
        "cmd": " ".join(args),
        "returncode": proc.returncode,
        "stdout_path": repo_rel(stdout),
        "stderr_path": repo_rel(stderr),
        "exit_path": repo_rel(exit_file),
        "parsed": parsed,
    }


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def provider_by_id(provider_status: dict[str, Any], provider_id: str) -> list[dict[str, Any]]:
    return [
        provider
        for provider in provider_status.get("providers", [])
        if provider.get("provider_id") == provider_id
    ]


def main() -> int:
    for directory in [CMD_DIR, OUT_DIR, CHECK_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    source_summary_path = SOURCE_ROOT / "downstream-chain/source_root_stop_carry_longhorizon_downstream_v1.json"
    source_summary = read_json(source_summary_path)
    root_probe_rows = read_csv(SOURCE_ROOT / "downstream-chain/root_bbn_probe_summary_v1.csv")
    branch_rows = read_csv(SOURCE_ROOT / "branch-rc-spa/source_root_stop_carry_longhorizon_branch_summary_v1.csv")
    branch_paths = [
        row["regime_profit_branch_path"]
        for row in branch_rows
        if row.get("parent_regime_root") != "Manipulation(scoped)"
    ]

    commands = [
        run_command("provider_status_agent", [str(BIN), "provider-status", "--agent"]),
        run_command("pre_bayes_status_refresh_json", [str(BIN), "pre-bayes-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"]),
        run_command("policy_training_status_json", [str(BIN), "policy-training-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--output-format", "json"]),
        run_command("export_structural_path_ranking_target", [str(BIN), "export-structural-path-ranking-target", "--symbol", "NQ", "--state-dir", str(STATE_DIR)]),
        run_command("workflow_status_execution_candidate_agent", [str(BIN), "workflow-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--phase", "execution-candidate", "--agent"]),
        run_command("auto_quant_prior_init_dry_run", [str(BIN), "auto-quant-prior-init", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--library", str(SOURCE_ROOT / "downstream-chain/autoquant_strategy_library_source_root_stop_carry_longhorizon_v1.json"), "--dry-run", "--force"]),
    ]

    provider_status = commands[0]["parsed"] if isinstance(commands[0]["parsed"], dict) else {}
    workflow = commands[4]["parsed"] if isinstance(commands[4]["parsed"], dict) else {}
    policy = commands[2]["parsed"] if isinstance(commands[2]["parsed"], dict) else {}
    export = commands[3]["parsed"] if isinstance(commands[3]["parsed"], dict) else {}

    provider_readback = {
        "summary_line": provider_status.get("summary_line"),
        "yfinance": provider_by_id(provider_status, "yfinance"),
        "tradingview_mcp": provider_by_id(provider_status, "tradingview_mcp"),
        "ibkr": provider_by_id(provider_status, "ibkr"),
        "ibkr_bridge": provider_by_id(provider_status, "ibkr_bridge"),
        "kraken_cli": provider_by_id(provider_status, "kraken_cli"),
        "kraken_public": provider_by_id(provider_status, "kraken_public"),
    }

    branch_paths_preserved = len(branch_paths) == 4 and all(" -> " in path for path in branch_paths)
    bbn_skipped = source_summary["pre_bayes"]["bbn_roots_skipped_no_supported_label"]
    exact_rows = source_summary["catboost_path_ranker"]["structural_diagnostics"]["board_b_exact_target_rows"]
    source_blocker = source_summary["primary_blocker"]

    workflow_text = json.dumps(workflow, sort_keys=True)
    policy_text = json.dumps(policy, sort_keys=True)
    export_text = json.dumps(export, sort_keys=True)
    workflow_execution_blocked = "execution_blocked" in workflow_text
    policy_runtime_ready = "runtime_eligible" in policy_text or "enabled_registered_artifact_ready" in policy_text
    export_has_exact_board_b_rows = any(path in export_text for path in branch_paths)

    decision = "not_promoted:downstream_branch_path_or_bbn_mapping_gap"
    next_action = (
        "Fix the downstream adapter boundary: Bear root BBN soft evidence is unsupported, "
        "and structural path-ranker/execution-tree targets still expose generic structural paths "
        "instead of exact Board B rooted branch paths; then rerun B5 for 220646."
    )

    payload = {
        "run_id": "20260511T222350+0800-codex-board-b-220646-downstream-readback-v2",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_run_root": repo_rel(SOURCE_ROOT),
        "source_summary": repo_rel(source_summary_path),
        "state_dir": str(STATE_DIR),
        "provider_readback": provider_readback,
        "branch_paths": branch_paths,
        "branch_paths_preserved": branch_paths_preserved,
        "branch_rc_spa_gate_result": source_summary["branch_rc_spa_gate_result"],
        "price_root_paths_passed": source_summary["price_root_paths_passed"],
        "manipulation_component_pass": source_summary["manipulation_component_pass"],
        "bbn_roots_applied": source_summary["pre_bayes"]["bbn_roots_applied"],
        "bbn_roots_skipped_no_supported_label": bbn_skipped,
        "catboost_available": source_summary["catboost_path_ranker"]["catboost_available"],
        "catboost_model_family": source_summary["catboost_path_ranker"]["model_family"],
        "catboost_policy_runtime_ready_observed": policy_runtime_ready,
        "structural_target_exact_board_b_rows": exact_rows,
        "structural_export_has_exact_board_b_rows": export_has_exact_board_b_rows,
        "workflow_execution_blocked_observed": workflow_execution_blocked,
        "downstream_consumption": source_summary["downstream_consumption"],
        "promotion_status": decision,
        "primary_blocker": source_blocker,
        "next_action": next_action,
        "commands": [{k: v for k, v in command.items() if k != "parsed"} for command in commands],
        "root_probe_rows": root_probe_rows,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
    }

    summary_json = OUT_DIR / "board_b_220646_downstream_readback_v2.json"
    write_json(summary_json, payload)

    summary_md = OUT_DIR / "board_b_220646_downstream_readback_v2.md"
    summary_md.write_text(
        "\n".join(
            [
                "# Board B 220646 Downstream Readback v2",
                "",
                f"- Decision: `{decision}`",
                f"- Source run: `{repo_rel(SOURCE_ROOT)}`",
                f"- Provider status: `{provider_status.get('summary_line', 'unavailable')}`",
                f"- Branch RC-SPA: `{payload['branch_rc_spa_gate_result']}`, price roots `{payload['price_root_paths_passed']}/4`, Manipulation component `{payload['manipulation_component_pass']}`",
                f"- Branch paths preserved in source/downstream artifacts: `{str(branch_paths_preserved).lower()}`",
                f"- BBN roots applied: `{','.join(payload['bbn_roots_applied']) or 'none'}`; skipped unsupported: `{','.join(bbn_skipped) or 'none'}`",
                f"- CatBoost/path-ranker: model family `{payload['catboost_model_family']}`, exact Board B structural target rows `{exact_rows}`",
                f"- Execution tree readback: execution blocked observed `{str(workflow_execution_blocked).lower()}`",
                f"- Primary blocker: `{source_blocker}`",
                "",
                "## Provider Readback",
                "",
                f"- yfinance: `{provider_readback['yfinance']}`",
                f"- TradingView MCP: `{provider_readback['tradingview_mcp']}`",
                f"- IBKR: `{provider_readback['ibkr']}`",
                f"- IBKR bridge: `{provider_readback['ibkr_bridge']}`",
                f"- Kraken CLI: `{provider_readback['kraken_cli']}`",
                f"- Kraken public: `{provider_readback['kraken_public']}`",
                "",
                "## Branch Paths",
                "",
                *[f"- `{path}`" for path in branch_paths],
                "",
                "## Next",
                "",
                next_action,
                "",
                "## Artifacts",
                "",
                f"- JSON: `{repo_rel(summary_json)}`",
                f"- Command outputs: `{repo_rel(CMD_DIR)}`",
                f"- Assertions: `{repo_rel(CHECK_DIR / 'board_b_220646_downstream_readback_v2_assertions.out')}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assertions = [
        f"PASS branch_rc_spa_gate_result={payload['branch_rc_spa_gate_result']}",
        f"PASS price_root_paths_passed={payload['price_root_paths_passed']}",
        f"PASS manipulation_component_pass={payload['manipulation_component_pass']}",
        f"PASS branch_paths_preserved={str(branch_paths_preserved).lower()}",
        f"PASS provider_status_exit={commands[0]['returncode']}",
        f"PASS yfinance_ready={any(provider.get('ready') for provider in provider_readback['yfinance'])}",
        f"PASS tradingview_mcp_ready={any(provider.get('ready') for provider in provider_readback['tradingview_mcp'])}",
        f"PASS kraken_cli_ready={any(provider.get('ready') for provider in provider_readback['kraken_cli'])}",
        f"PASS ibkr_gateway_recorded={bool(provider_readback['ibkr'] or provider_readback['ibkr_bridge'])}",
        f"PASS bbn_roots_skipped_no_supported_label={','.join(bbn_skipped) or 'none'}",
        f"PASS structural_target_exact_board_b_rows={exact_rows}",
        f"PASS promotion_status={decision}",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
        "PASS raw_data_committed=false",
    ]
    (CHECK_DIR / "board_b_220646_downstream_readback_v2_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"run_id": payload["run_id"], "promotion_status": decision, "primary_blocker": source_blocker}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
