#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


REPO = Path(__file__).resolve().parents[5]
BASE = REPO / "support/docs/experiments/actionable-regime-confidence"
TOMAC_ROOT = Path(os.environ.get("ICT_ENGINE_TOMAC_ROOT", str(Path.home() / "Downloads/Tomac")))
CLAIMS_DIR = Path("/tmp/ict-engine-agent-claims/board-b-factor-refinement")
AQ_WRAPPER = BASE / "scripts/run_tomac_index_futures_clean_aq_v1.py"
STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
DEFAULT_ROOT = Path("/tmp") / f"ict-engine-tomac-compression-breakout-continuation-prep-{STAMP}"
DEFAULT_COMPACT_ROOT = BASE / "runs" / f"{STAMP}-codex-tomac-compression-breakout-continuation-prep-v1"

BRANCH_PATH = (
    "RangeConsolidation -> VolatilityCompression -> "
    "CompressionBreakoutContinuation -> tomac_idxfut_clean_compression_breakout_continuation_1m_v1"
)
FACTOR_ID = "tomac_idxfut_clean_compression_breakout_continuation_1m_v1"
COVERAGE_SCRIPT = REPO / "support/scripts/research/tomac_factor_coverage_matrix.py"
CLAIM_AUDIT = REPO / "support/scripts/factor_claim_terminalization_audit.py"


@dataclass(frozen=True)
class LaunchPlan:
    factor_id: str
    branch_path: str
    run_mode: str
    aq_wrapper: str
    coverage_script: str
    out_root: str
    compact_root: str
    command: list[str]
    coverage_command: list[str]


def run_cmd(name: str, argv: list[str], cwd: Path, output_root: Path) -> dict[str, object]:
    (output_root / "command-output").mkdir(parents=True, exist_ok=True)
    (output_root / "checks").mkdir(parents=True, exist_ok=True)
    (output_root / "command-output" / f"{name}.cmd").write_text(" ".join(argv) + "\n", encoding="utf-8")
    proc = subprocess.run(argv, cwd=cwd, text=True, capture_output=True)
    (output_root / "command-output" / f"{name}.out").write_text(proc.stdout, encoding="utf-8")
    (output_root / "command-output" / f"{name}.err").write_text(proc.stderr, encoding="utf-8")
    (output_root / "checks" / f"{name}.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
    return {"name": name, "exit": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def load_claim_audit() -> dict[str, object]:
    proc = subprocess.run(
        [sys.executable, str(CLAIM_AUDIT), "--portable-paths"],
        cwd=REPO,
        text=True,
        capture_output=True,
    )
    text = (proc.stdout or "").strip()
    if not text:
        return {
            "claims": [],
            "live_factor_processes": [],
            "audit_error": f"empty audit output rc={proc.returncode} stderr={proc.stderr.strip()}",
        }
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        return {
            "claims": [],
            "live_factor_processes": [],
            "audit_error": f"invalid audit json: {exc}",
        }


def _same_root(candidate: object, current_root: Path) -> bool:
    if not isinstance(candidate, str) or not candidate.strip():
        return False
    try:
        path = Path(candidate).expanduser().resolve(strict=False)
    except OSError:
        path = Path(candidate).expanduser().absolute()
    current = current_root.resolve(strict=False)
    return path == current or current in path.parents or path in current.parents


def collision_guard(audit: dict[str, object], current_root: Path) -> dict[str, object]:
    claims = audit.get("claims") if isinstance(audit.get("claims"), list) else audit.get("attention_claims", [])
    live_processes = audit.get("live_factor_processes") if isinstance(audit.get("live_factor_processes"), list) else audit.get("attention_live_processes", [])
    foreign_active_claims: list[str] = []
    for claim in claims if isinstance(claims, list) else []:
        if not isinstance(claim, dict):
            continue
        if claim.get("status") != "active" or claim.get("coordination_only"):
            continue
        root = claim.get("run_root") or claim.get("tmp_root")
        if _same_root(root, current_root):
            continue
        foreign_active_claims.append(str(claim.get("claim_file") or root or "unknown_claim"))

    foreign_live_roots: list[str] = []
    for process in live_processes if isinstance(live_processes, list) else []:
        if not isinstance(process, dict):
            continue
        root = process.get("run_root")
        if _same_root(root, current_root):
            continue
        foreign_live_roots.append(str(root or process.get("pid") or "unknown_live_process"))

    return {
        "ready": not foreign_active_claims and not foreign_live_roots and not audit.get("audit_error"),
        "foreign_active_claims": foreign_active_claims,
        "foreign_live_roots": foreign_live_roots,
        "audit_error": audit.get("audit_error"),
    }


def build_plan(output_root: Path, compact_root: Path, launch: bool) -> LaunchPlan:
    command = [
        sys.executable,
        str(AQ_WRAPPER),
        "--root",
        str(output_root),
        "--compact-root",
        str(compact_root),
        "--symbols",
        "ES",
        "--start",
        "2021-01-01",
        "--end",
        "2025-12-31",
        "--timeframes",
        "1m,5m,15m,30m,1h,4h,1d",
        "--families",
        "compression_breakout_continuation",
        "--aq-smoke-timeframe",
        "1m",
        "--aq-symbol-limit",
        "1",
        "--timeout",
        "1800",
    ]
    if not launch:
        command.append("--clean-only")

    coverage_command = [
        sys.executable,
        str(COVERAGE_SCRIPT),
        "--tomac-root",
        str(TOMAC_ROOT),
        "--claims-dir",
        str(CLAIMS_DIR),
        "--output-json",
        str(output_root / "coverage" / "tomac_factor_coverage.json"),
        "--output-csv",
        str(output_root / "coverage" / "tomac_factor_coverage.csv"),
    ]
    return LaunchPlan(
        factor_id=FACTOR_ID,
        branch_path=BRANCH_PATH,
        run_mode="launch" if launch else "source_prep_no_launch",
        aq_wrapper=str(AQ_WRAPPER),
        coverage_script=str(COVERAGE_SCRIPT),
        out_root=str(output_root),
        compact_root=str(compact_root),
        command=command,
        coverage_command=coverage_command,
    )


def mirror_compact_artifacts(plan: LaunchPlan, summary: dict[str, object], compact_root: Path) -> None:
    (compact_root / "summaries").mkdir(parents=True, exist_ok=True)
    (compact_root / "summaries" / "launch_plan.json").write_text(
        json.dumps(asdict(plan), indent=2) + "\n",
        encoding="utf-8",
    )
    (compact_root / "summaries" / "terminal_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prep or launch the TOMAC compression-breakout continuation packet.")
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    parser.add_argument("--compact-root", default=str(DEFAULT_COMPACT_ROOT))
    parser.add_argument("--launch", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_root = Path(args.root)
    compact_root = Path(args.compact_root)
    output_root.mkdir(parents=True, exist_ok=True)
    compact_root.mkdir(parents=True, exist_ok=True)

    plan = build_plan(output_root, compact_root, launch=args.launch)
    (output_root / "summaries").mkdir(parents=True, exist_ok=True)
    (output_root / "summaries" / "launch_plan.json").write_text(
        json.dumps(asdict(plan), indent=2) + "\n",
        encoding="utf-8",
    )

    coverage_result = run_cmd("build_coverage", plan.coverage_command, REPO, output_root)
    summary = {
        "factor_id": FACTOR_ID,
        "branch_path": BRANCH_PATH,
        "run_mode": plan.run_mode,
        "coverage_exit": coverage_result["exit"],
        "launch_requested": bool(args.launch),
        "status": "source_prep_complete" if not args.launch else "launch_in_progress",
        "scan_executed": False,
        "scan_exit": None,
    }
    summary_path = output_root / "summaries" / "terminal_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    mirror_compact_artifacts(plan, summary, compact_root)
    if args.launch:
        guard = collision_guard(load_claim_audit(), output_root)
        if not guard["ready"]:
            summary["status"] = "launch_blocked_by_collision_guard"
            summary["collision_guard"] = guard
            summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
            mirror_compact_artifacts(plan, summary, compact_root)
            return 1
        scan_result = run_cmd("tomac_clean_aq", plan.command, REPO, output_root)
        summary["scan_executed"] = True
        summary["scan_exit"] = scan_result["exit"]
        summary["status"] = "launch_finished"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    mirror_compact_artifacts(plan, summary, compact_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
