#!/usr/bin/env python3
"""Replay Board A AQ rank positives and negatives into ict-engine feedback.

This runner is intentionally narrow: it does not open a new profit-factor lane.
It converts existing Board A regime/subclass Auto-Quant rank rows into
structural feedback so positive rows strengthen rooted branch evidence and
zero/negative rows remain explicit boundary samples.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_SOURCE_RUN = (
    REPO_ROOT
    / "support/docs/experiments/actionable-regime-confidence/runs"
    / "20260518T123234+0800-codex-board-a-yf-insurance-defensive-range-reclaim-1m-mtf-v1"
)
DEFAULT_RANK_JSON = (
    DEFAULT_SOURCE_RUN
    / "state/auto-quant/BOARD_A_YF_INSURANCE_DEFENSIVE_RANGE_RECLAIM_1M_MTF"
    / "auto_quant_agent_material_rank.20260518T043709.770Z.json"
)
HELPER = REPO_ROOT / "support/scripts/auto_quant_external/structural_feedback_trade_enricher.py"
DEFAULT_SYMBOL = "BOARD_A_YF_INSURANCE_DEFENSIVE_RANGE_RECLAIM_1M_MTF"
DEFAULT_CANDIDATE_SET_ID = "board-a-positive-negative-feedback-ingress-v1"


def utc_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_rank_rows(rank_json: Path) -> list[dict[str, Any]]:
    payload = json.loads(rank_json.read_text(encoding="utf-8"))
    rows = payload.get("ranking")
    if not isinstance(rows, list):
        raise ValueError(f"rank artifact has no ranking array: {rank_json}")
    return [row for row in rows if isinstance(row, dict)]


def load_rank_rows_with_source(rank_jsons: list[Path]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for source_index, rank_json in enumerate(rank_jsons, start=1):
        for source_row_index, row in enumerate(load_rank_rows(rank_json), start=1):
            enriched = dict(row)
            enriched["source_rank_json"] = str(rank_json)
            enriched["source_rank_file_index"] = source_index
            enriched["source_rank_row_index"] = source_row_index
            out.append(enriched)
    return out


def row_float(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def row_int(row: dict[str, Any], key: str, default: int = 0) -> int:
    try:
        return int(float(row.get(key, default) or default))
    except (TypeError, ValueError):
        return default


def path_id_for(row: dict[str, Any], index: int) -> str:
    package_id = str(row.get("package_id") or f"rank-row-{index}")
    branch_path = str(row.get("regime_profit_branch_path") or row.get("branch_path") or "unrooted")
    source_index = row.get("source_rank_file_index")
    if source_index is None:
        return f"path:board-a-feedback:{branch_path}:{package_id}"
    return f"path:board-a-feedback:source{source_index}:{branch_path}:{package_id}"


def rooted_branch_path_for(row: dict[str, Any]) -> str:
    branch_path = str(row.get("regime_profit_branch_path") or row.get("branch_path") or "").strip()
    return branch_path if " -> " in branch_path else ""


def normalize_target_rows(rows: list[dict[str, Any]], *, symbol: str, candidate_set_id: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        total_profit = row_float(row, "total_profit_pct")
        trade_count = row_int(row, "trade_count")
        win_rate = row_float(row, "win_rate_pct")
        branch_path = rooted_branch_path_for(row)
        positive = bool(branch_path) and trade_count > 0 and total_profit > 0.0
        boundary = bool(branch_path) and not positive
        feedback_class = (
            "positive_bayesian_evidence"
            if positive
            else "negative_boundary_sample" if boundary else "unrooted_observation_negative"
        )
        raw_score = min(0.99, max(0.01, 0.5 + (total_profit / 10.0)))
        if not positive:
            raw_score = min(raw_score, 0.49)
        out.append(
            {
                "rank": idx,
                "path_id": path_id_for(row, idx),
                "path_label": row.get("package_id") or row.get("unit_label") or f"rank-row-{idx}",
                "candidate_set_id": candidate_set_id,
                "candidate_set_size": len(rows),
                "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "symbol": symbol,
                "direction": "Observe",
                "raw_path_score": raw_score,
                "current_posterior": raw_score,
                "behavior_policy_probability": raw_score,
                "branch_path": branch_path,
                "regime_profit_branch_path": branch_path,
                "main_regime": row.get("main_regime") or "",
                "sub_regime": row.get("sub_regime") or "",
                "sub_sub_regime_or_profit_factor": row.get("sub_sub_regime_or_profit_factor") or "",
                "profit_factor": row.get("profit_factor") or "",
                "provider_provenance": row.get("provider_provenance") or "",
                "source_rank_json": row.get("source_rank_json") or "",
                "source_rank_file_index": row.get("source_rank_file_index") or "",
                "source_rank_row_index": row.get("source_rank_row_index") or "",
                "unit_label": row.get("unit_label") or "",
                "package_id": row.get("package_id") or "",
                "trade_count": trade_count,
                "win_rate_pct": win_rate,
                "total_profit_pct": total_profit,
                "feedback_class": feedback_class,
                "realized_outcome": "win" if positive else "loss" if boundary else "blocked",
                "realized_pnl": total_profit / 100.0 if positive else min(total_profit / 100.0, -0.001),
                "exit_reason": (
                    "positive_branch_evidence"
                    if positive
                    else "negative_boundary_sample" if boundary else "unrooted_observation_negative"
                ),
            }
        )
    return out


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("no target rows to write")
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_cmd(command: list[str], *, cwd: Path, output_dir: Path, name: str) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"{name}.cmd").write_text(" ".join(command) + "\n", encoding="utf-8")
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    (output_dir / f"{name}.out").write_text(proc.stdout, encoding="utf-8")
    (output_dir / f"{name}.err").write_text(proc.stderr, encoding="utf-8")
    (output_dir / f"{name}.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
    return proc.returncode


def emit_feedback_files(
    *,
    target_csv: Path,
    target_rows: list[dict[str, Any]],
    feedback_dir: Path,
    command_output: Path,
    max_positive: int,
    max_negative: int,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    positives = [row for row in target_rows if row["feedback_class"] == "positive_bayesian_evidence"][:max_positive]
    negatives = [row for row in target_rows if row["feedback_class"] == "negative_boundary_sample"][:max_negative]
    for sequence, row in enumerate(positives + negatives, start=1):
        feedback_path = feedback_dir / f"{sequence:02d}-{row['feedback_class']}-{row['package_id']}.json"
        cmd = [
            "python3",
            str(HELPER),
            "emit-probe",
            "--target-csv",
            str(target_csv),
            "--output",
            str(feedback_path),
            "--path-id",
            str(row["path_id"]),
            "--realized-outcome",
            str(row["realized_outcome"]),
            "--pnl",
            str(row["realized_pnl"]),
            "--exit-reason",
            str(row["exit_reason"]),
            "--notes",
            f"Board A feedback ingress: {row['feedback_class']} from existing AQ rank row; no trade promotion.",
        ]
        exit_code = run_cmd(cmd, cwd=REPO_ROOT, output_dir=command_output, name=f"10_emit_feedback_{sequence:02d}")
        selected.append({**row, "feedback_path": str(feedback_path), "emit_exit": exit_code})
    return selected


def run_updates(*, selected: list[dict[str, Any]], state_dir: Path, command_output: Path, symbol: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for sequence, row in enumerate(selected, start=1):
        cmd = [
            "cargo",
            "run",
            "--quiet",
            "--",
            "update",
            "--symbol",
            symbol,
            "--state-dir",
            str(state_dir),
            "--outcome",
            str(row["realized_outcome"]),
            "--entry-signal",
            "structural_feedback",
            "--feedback-file",
            str(row["feedback_path"]),
            f"--pnl={row['realized_pnl']}",
            "--regime",
            str(row["main_regime"]),
            "--direction",
            "observe",
        ]
        exit_code = run_cmd(cmd, cwd=REPO_ROOT, output_dir=command_output, name=f"20_update_feedback_{sequence:02d}")
        results.append({"path_id": row["path_id"], "feedback_class": row["feedback_class"], "update_exit": exit_code})
    return results


def run_readbacks(*, state_dir: Path, command_output: Path, symbol: str) -> dict[str, int]:
    commands = {
        "30_workflow_status": [
            "cargo",
            "run",
            "--quiet",
            "--",
            "workflow-status",
            "--symbol",
            symbol,
            "--state-dir",
            str(state_dir),
            "--refresh",
            "--output-format",
            "json",
        ],
        "31_pre_bayes_status": [
            "cargo",
            "run",
            "--quiet",
            "--",
            "pre-bayes-status",
            "--symbol",
            symbol,
            "--state-dir",
            str(state_dir),
            "--refresh",
            "--output-format",
            "json",
        ],
        "32_policy_training_status": [
            "cargo",
            "run",
            "--quiet",
            "--",
            "policy-training-status",
            "--symbol",
            symbol,
            "--state-dir",
            str(state_dir),
            "--output-format",
            "json",
        ],
        "33_export_structural_path_ranking_target": [
            "cargo",
            "run",
            "--quiet",
            "--",
            "export-structural-path-ranking-target",
            "--symbol",
            symbol,
            "--state-dir",
            str(state_dir),
            "--output-format",
            "json",
        ],
    }
    return {name: run_cmd(cmd, cwd=REPO_ROOT, output_dir=command_output, name=name) for name, cmd in commands.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rank-json", type=Path, action="append")
    parser.add_argument("--source-run", type=Path, default=DEFAULT_SOURCE_RUN)
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--candidate-set-id", default=DEFAULT_CANDIDATE_SET_ID)
    parser.add_argument("--max-positive", type=int, default=3)
    parser.add_argument("--max-negative", type=int, default=6)
    args = parser.parse_args()

    run_root = args.run_root or (
        REPO_ROOT
        / "support/docs/experiments/actionable-regime-confidence/runs"
        / f"{utc_slug()}-codex-board-a-positive-negative-feedback-ingress-v1"
    )
    state_dir = run_root / "state/ict-engine-feedback"
    command_output = run_root / "command-output"
    feedback_dir = run_root / "feedback"
    checks_dir = run_root / "checks"
    summaries_dir = run_root / "summaries"

    rank_jsons = args.rank_json or [DEFAULT_RANK_JSON]
    rows = load_rank_rows_with_source(rank_jsons)
    target_rows = normalize_target_rows(rows, symbol=args.symbol, candidate_set_id=args.candidate_set_id)
    target_csv = run_root / "targets/board_a_positive_negative_feedback_targets.csv"
    write_csv(target_csv, target_rows)

    selected = emit_feedback_files(
        target_csv=target_csv,
        target_rows=target_rows,
        feedback_dir=feedback_dir,
        command_output=command_output,
        max_positive=args.max_positive,
        max_negative=args.max_negative,
    )
    update_results = run_updates(selected=selected, state_dir=state_dir, command_output=command_output, symbol=args.symbol)
    readback_exits = run_readbacks(state_dir=state_dir, command_output=command_output, symbol=args.symbol)

    summary = {
        "run_root": str(run_root),
        "source_run": str(args.source_run),
        "rank_json": [str(path) for path in rank_jsons],
        "rank_json_count": len(rank_jsons),
        "symbol": args.symbol,
        "candidate_set_id": args.candidate_set_id,
        "branch_path": target_rows[0].get("regime_profit_branch_path") if target_rows else None,
        "branch_paths": sorted({str(row.get("regime_profit_branch_path") or row.get("branch_path") or "") for row in target_rows}),
        "target_rows": len(target_rows),
        "positive_target_rows": sum(1 for row in target_rows if row["feedback_class"] == "positive_bayesian_evidence"),
        "negative_boundary_target_rows": sum(1 for row in target_rows if row["feedback_class"] == "negative_boundary_sample"),
        "unrooted_observation_negative_rows": sum(
            1 for row in target_rows if row["feedback_class"] == "unrooted_observation_negative"
        ),
        "selected_feedback_rows": len(selected),
        "selected_positive_rows": sum(1 for row in selected if row["feedback_class"] == "positive_bayesian_evidence"),
        "selected_negative_boundary_rows": sum(1 for row in selected if row["feedback_class"] == "negative_boundary_sample"),
        "emit_exits": {Path(row["feedback_path"]).name: row["emit_exit"] for row in selected},
        "update_exits": update_results,
        "readback_exits": readback_exits,
        "promotion_allowed": False,
        "trade_usable": False,
        "terminal_decision": "feedback_ingress_repaired_observation_only",
    }
    checks_dir.mkdir(parents=True, exist_ok=True)
    summaries_dir.mkdir(parents=True, exist_ok=True)
    (checks_dir / "terminal_metrics.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (summaries_dir / "terminal_decision_summary.md").write_text(
        "# Board A Positive/Negative Feedback Ingress v1\n\n"
        f"- run_root: `{run_root}`\n"
        f"- source_run: `{args.source_run}`\n"
        f"- rank_json_count: `{len(rank_jsons)}`\n"
        f"- symbol: `{args.symbol}`\n"
        f"- candidate_set_id: `{args.candidate_set_id}`\n"
        f"- target_rows: `{summary['target_rows']}`\n"
        f"- positive_target_rows: `{summary['positive_target_rows']}`\n"
        f"- negative_boundary_target_rows: `{summary['negative_boundary_target_rows']}`\n"
        f"- unrooted_observation_negative_rows: `{summary['unrooted_observation_negative_rows']}`\n"
        f"- selected_feedback_rows: `{summary['selected_feedback_rows']}`\n"
        f"- terminal_decision: `{summary['terminal_decision']}`\n"
        "- promotion_allowed: `false`\n"
        "- trade_usable: `false`\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0 if all(code == 0 for code in readback_exits.values()) and all(item["update_exit"] == 0 for item in update_results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
