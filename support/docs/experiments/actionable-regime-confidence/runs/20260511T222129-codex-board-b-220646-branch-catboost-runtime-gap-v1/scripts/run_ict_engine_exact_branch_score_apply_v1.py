#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path


def run_command(name: str, cmd: list[str], output_dir: Path) -> dict:
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    stdout_path = output_dir / f"{name}.out"
    stderr_path = output_dir / f"{name}.err"
    exit_path = output_dir / f"{name}.exit"
    stdout_path.write_text(proc.stdout)
    stderr_path.write_text(proc.stderr)
    exit_path.write_text(str(proc.returncode) + "\n")
    return {
        "name": name,
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "exit_path": str(exit_path),
    }


def load_json(path: Path) -> dict | None:
    try:
        text = path.read_text().strip()
        if not text or text == "null":
            return None
        return json.loads(text)
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--scores-file", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ict = repo_root / "target/debug/ict-engine"

    commands = []
    commands.append(
        run_command(
            "01_apply_exact_branch_path_scores",
            [
                str(ict),
                "apply-structural-path-ranking-external-scores",
                "--symbol",
                args.symbol,
                "--state-dir",
                args.state_dir,
                "--scores-file",
                args.scores_file,
            ],
            output_dir,
        )
    )
    commands.append(
        run_command(
            "02_export_after_exact_branch_apply",
            [
                str(ict),
                "export-structural-path-ranking-target",
                "--symbol",
                args.symbol,
                "--state-dir",
                args.state_dir,
            ],
            output_dir,
        )
    )
    commands.append(
        run_command(
            "03_policy_training_status_after_exact_branch_apply",
            [
                str(ict),
                "policy-training-status",
                "--symbol",
                args.symbol,
                "--state-dir",
                args.state_dir,
                "--output-format",
                "json",
            ],
            output_dir,
        )
    )
    commands.append(
        run_command(
            "04_workflow_execution_candidate_after_exact_branch_apply",
            [
                str(ict),
                "workflow-status",
                "--symbol",
                args.symbol,
                "--state-dir",
                args.state_dir,
                "--phase",
                "execution-candidate",
                "--agent",
            ],
            output_dir,
        )
    )
    commands.append(
        run_command(
            "05_pre_bayes_status_after_exact_branch_apply",
            [
                str(ict),
                "pre-bayes-status",
                "--symbol",
                args.symbol,
                "--state-dir",
                args.state_dir,
                "--refresh",
                "--output-format",
                "json",
            ],
            output_dir,
        )
    )

    export_json = load_json(output_dir / "02_export_after_exact_branch_apply.out") or {}
    policy_json = load_json(output_dir / "03_policy_training_status_after_exact_branch_apply.out") or {}
    workflow_json = load_json(output_dir / "04_workflow_execution_candidate_after_exact_branch_apply.out")
    pre_bayes_json = load_json(output_dir / "05_pre_bayes_status_after_exact_branch_apply.out") or {}
    apply_stderr = (output_dir / "01_apply_exact_branch_path_scores.err").read_text().strip()
    apply_returncode = commands[0]["returncode"]

    summary = {
        "schema_version": "board-b-ict-engine-exact-branch-score-apply/v1",
        "symbol": args.symbol,
        "state_dir": args.state_dir,
        "scores_file": args.scores_file,
        "commands": commands,
        "all_commands_exit_zero": all(c["returncode"] == 0 for c in commands),
        "exact_branch_apply_returncode": apply_returncode,
        "exact_branch_apply_error": apply_stderr,
        "export_rows": export_json.get("rows"),
        "export_rows_with_raw_path_score": export_json.get("rows_with_raw_path_score"),
        "export_rows_with_calibrated_path_prob": export_json.get("rows_with_calibrated_path_prob"),
        "export_rows_with_execution_gate_status": export_json.get("rows_with_execution_gate_status"),
        "export_summary_line": export_json.get("summary_line"),
        "policy_runtime_ready": (
            policy_json.get("structural_path_ranking_runtime", {}).get("ready")
            if isinstance(policy_json, dict)
            else None
        ),
        "policy_runtime_summary": (
            policy_json.get("structural_path_ranking_runtime", {}).get("summary_line")
            if isinstance(policy_json, dict)
            else None
        ),
        "policy_validation_summary": (
            policy_json.get("structural_path_ranking_validation", {}).get("summary_line")
            if isinstance(policy_json, dict)
            else None
        ),
        "workflow_execution_candidate_observed": workflow_json is not None,
        "pre_bayes_gate_status": pre_bayes_json.get("latest_gate_status"),
        "pre_bayes_policy_version": pre_bayes_json.get("latest_policy_version"),
        "promotion_status": "not_promoted:exact_regime_profit_branch_paths_not_consumed_by_runtime_target"
        if apply_returncode != 0 or "no structural path ranking target rows matched" in apply_stderr
        else "needs_manual_audit",
    }
    summary_path = output_dir / "ict_engine_exact_branch_score_apply_summary_v1.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    md_path = output_dir / "ict_engine_exact_branch_score_apply_summary_v1.md"
    md_path.write_text(
        "\n".join(
            [
                "# ict-engine Exact Branch Score Apply Summary v1",
                "",
                f"- Commands exit zero: `{summary['all_commands_exit_zero']}`.",
                f"- Export rows with raw path score: `{summary['export_rows_with_raw_path_score']}`.",
                f"- Policy runtime ready: `{summary['policy_runtime_ready']}`.",
                f"- Workflow execution candidate observed: `{summary['workflow_execution_candidate_observed']}`.",
                f"- Pre-Bayes gate: `{summary['pre_bayes_gate_status']}`.",
                f"- Promotion status: `{summary['promotion_status']}`.",
                "",
                f"Export summary: `{summary['export_summary_line']}`",
                f"Policy runtime: `{summary['policy_runtime_summary']}`",
                f"Policy validation: `{summary['policy_validation_summary']}`",
                "",
            ]
        )
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
