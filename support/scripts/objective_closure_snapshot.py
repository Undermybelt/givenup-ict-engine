#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from path_defaults import resolve_repo_root

ROOT = resolve_repo_root(__file__)
DONE_AUDIT = ROOT / "support" / "scripts" / "done_definition_audit.py"
FACTOR_AUDIT = ROOT / "support" / "scripts" / "factor_claim_terminalization_audit.py"
RELEASE_AUDIT = ROOT / "support" / "scripts" / "release_readiness_audit.py"
QUICKSTART_CHAIN = [
    "cargo run --quiet -- provider-status --compact",
    "cargo run --quiet -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-first-run --human",
    "cargo run --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --refresh --agent",
    "cargo run --quiet -- pre-bayes-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --refresh --output-format json",
    "cargo run --quiet -- policy-training-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --output-format agent",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def effective_timeout_seconds(requested: int | None, *, run_all_heavy: bool) -> int:
    if requested is not None:
        return requested
    return 300 if run_all_heavy else 90


def run_command(argv: list[str], cwd: Path, timeout: int = 60) -> dict[str, Any]:
    try:
        result = subprocess.run(
            argv,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": argv,
            "returncode": None,
            "error": "timeout",
            "timeout_seconds": timeout,
            "stdout": _text(exc.stdout),
            "stderr": _text(exc.stderr),
        }
    return {
        "argv": argv,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def build_audit_specs(
    *,
    output_dir: Path | None,
    run_all_heavy: bool,
    check_remotes: bool,
) -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}

    done_output = output_dir / "done_definition_audit.compact.json" if output_dir else None
    done_cmd = [sys.executable, str(DONE_AUDIT), "--compact"]
    if run_all_heavy:
        done_cmd.append("--run-all-heavy")
    if done_output:
        done_cmd.extend(["--output", str(done_output)])
    specs["done_definition"] = {"argv": done_cmd, "output_path": done_output}

    factor_output = output_dir / "factor_claim_terminalization_audit.compact.json" if output_dir else None
    factor_cmd = [sys.executable, str(FACTOR_AUDIT), "--compact"]
    if factor_output:
        factor_cmd.extend(["--output", str(factor_output)])
    specs["factor_closure"] = {"argv": factor_cmd, "output_path": factor_output}

    release_output = output_dir / "release_readiness_audit.compact.json" if output_dir else None
    release_cmd = [sys.executable, str(RELEASE_AUDIT), "--compact"]
    if check_remotes:
        release_cmd.append("--check-remotes")
    if release_output:
        release_cmd.extend(["--output", str(release_output)])
    specs["release_readiness"] = {"argv": release_cmd, "output_path": release_output}

    return specs


def _read_json_from_command(result: dict[str, Any], output_path: Path | None) -> dict[str, Any]:
    raw_text = ""
    if output_path and output_path.exists():
        raw_text = output_path.read_text(encoding="utf-8")
    else:
        raw_text = str(result.get("stdout") or "").strip()
    if not raw_text:
        raise ValueError("missing_json_output")
    parsed = json.loads(raw_text)
    if not isinstance(parsed, dict):
        raise ValueError("json_report_must_be_object")
    return parsed


def _done_surface(report: dict[str, Any]) -> dict[str, Any]:
    summary = report.get("summary", {})
    gates = report.get("gates", [])
    quickstart_status = None
    if isinstance(gates, list):
        for gate in gates:
            if isinstance(gate, dict) and gate.get("id") == "quickstart_surface":
                quickstart_status = gate.get("status")
                break
    return {
        "report_timestamp": report.get("timestamp_utc"),
        "status": summary.get("status"),
        "completion_ready": bool(summary.get("completion_ready")),
        "evidence_level": summary.get("evidence_level"),
        "quickstart_surface": quickstart_status,
        "unresolved": summary.get("unresolved", []),
        "skipped_gates": summary.get("skipped_gates", []),
    }


def _factor_surface(report: dict[str, Any]) -> dict[str, Any]:
    summary = report.get("summary", {})
    attention_groups = report.get("attention_groups", {})
    by_owner = {}
    if isinstance(attention_groups, dict):
        maybe_by_owner = attention_groups.get("by_owner", {})
        if isinstance(maybe_by_owner, dict):
            by_owner = maybe_by_owner
    return {
        "report_timestamp": report.get("generated_at"),
        "status": summary.get("status"),
        "active_claims": summary.get("active_claims"),
        "invalid_active_claims": summary.get("invalid_active_claims"),
        "live_factor_processes": summary.get("live_factor_processes"),
        "blocking_reasons": summary.get("blocking_reasons", []),
        "promotion_allowed_true": summary.get("promotion_allowed_true"),
        "trade_usable_true": summary.get("trade_usable_true"),
        "next_action": summary.get("next_action"),
        "attention_claim_count": report.get("attention_claim_count"),
        "attention_live_process_count": report.get("attention_live_process_count"),
        "attention_by_owner": by_owner,
    }


def _release_surface(report: dict[str, Any]) -> dict[str, Any]:
    summary = report.get("summary", {})
    return {
        "report_timestamp": report.get("timestamp_utc"),
        "status": summary.get("status"),
        "unresolved": summary.get("unresolved", []),
        "pass_count": summary.get("pass_count"),
        "fail_count": summary.get("fail_count"),
        "skip_count": summary.get("skip_count"),
    }


def summarize_snapshot(
    done_surface: dict[str, Any],
    factor_surface: dict[str, Any],
    release_surface: dict[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    if not done_surface.get("completion_ready"):
        blockers.append("done_definition_not_completion_ready")
    if done_surface.get("quickstart_surface") != "pass":
        blockers.append("quickstart_surface_drift")
    if factor_surface.get("status") != "pass":
        blockers.append("factor_closure_blocked")
    if release_surface.get("status") != "pass":
        blockers.append("release_readiness_blocked")

    manual_requirements_remaining = [
        "same_tree_practical_closure_packet",
        "truthful_completion_commit",
    ]
    surface_green = not blockers
    status = (
        "surface_green_manual_end_to_end_proof_required"
        if surface_green
        else "not_complete"
    )
    next_action = (
        "prove one same-tree provider->execution->feedback practical closure packet and only then re-evaluate completion"
        if surface_green
        else "rerun the blocked child audits after fixing the named blocker surfaces"
    )
    return {
        "status": status,
        "completion_proven": False,
        "surface_green": surface_green,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "manual_requirements_remaining": manual_requirements_remaining,
        "next_action": next_action,
    }


def build_snapshot(
    audit_results: dict[str, dict[str, Any]],
    *,
    run_all_heavy: bool,
    check_remotes: bool,
    output_dir: Path | None,
) -> dict[str, Any]:
    done_report = audit_results["done_definition"]["report"]
    factor_report = audit_results["factor_closure"]["report"]
    release_report = audit_results["release_readiness"]["report"]

    done_surface = _done_surface(done_report)
    factor_surface = _factor_surface(factor_report)
    release_surface = _release_surface(release_report)
    summary = summarize_snapshot(done_surface, factor_surface, release_surface)

    evidence_files = {
        name: (str(spec["output_path"]) if spec.get("output_path") else None)
        for name, spec in audit_results.items()
    }

    return {
        "schema_version": "objective-closure-snapshot/v1",
        "timestamp_utc": _utc_now(),
        "repo_root": str(ROOT),
        "quickstart_chain": QUICKSTART_CHAIN,
        "options": {
            "run_all_heavy": run_all_heavy,
            "check_remotes": check_remotes,
            "output_dir": str(output_dir) if output_dir else None,
        },
        "audit_commands": {
            name: spec["command"]["argv"] for name, spec in audit_results.items()
        },
        "evidence_files": evidence_files,
        "audits": {
            "done_definition": {
                "returncode": audit_results["done_definition"]["command"]["returncode"],
                "surface": done_surface,
            },
            "factor_closure": {
                "returncode": audit_results["factor_closure"]["command"]["returncode"],
                "surface": factor_surface,
            },
            "release_readiness": {
                "returncode": audit_results["release_readiness"]["command"]["returncode"],
                "surface": release_surface,
            },
        },
        "summary": summary,
    }


def build_failure_report(
    *,
    failed_audit: str,
    error: str,
    command_result: dict[str, Any],
    run_all_heavy: bool,
    check_remotes: bool,
    output_dir: Path | None,
) -> dict[str, Any]:
    return {
        "schema_version": "objective-closure-snapshot/v1",
        "timestamp_utc": _utc_now(),
        "repo_root": str(ROOT),
        "quickstart_chain": QUICKSTART_CHAIN,
        "options": {
            "run_all_heavy": run_all_heavy,
            "check_remotes": check_remotes,
            "output_dir": str(output_dir) if output_dir else None,
        },
        "summary": {
            "status": "snapshot_failed",
            "failed_audit": failed_audit,
            "error": error,
        },
        "command": command_result,
    }


def write_report_file(report: dict[str, Any], output_dir: Path | None) -> None:
    if not output_dir:
        return
    snapshot_path = output_dir / "objective_closure_snapshot.json"
    snapshot_path.write_text(
        json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def format_report(report: dict[str, Any], *, compact: bool) -> str:
    if compact:
        return json.dumps(report, ensure_ascii=True, separators=(",", ":")) + "\n"
    return json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate done-definition, factor-closure, and release-readiness into one compact objective snapshot."
    )
    parser.add_argument("--compact", action="store_true", help="emit single-line JSON")
    parser.add_argument(
        "--run-all-heavy",
        action="store_true",
        help="pass --run-all-heavy through to done_definition_audit.py",
    )
    parser.add_argument(
        "--check-remotes",
        action="store_true",
        help="pass --check-remotes through to release_readiness_audit.py",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="optional directory for child audit JSON outputs and the final snapshot",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        help="per-child timeout in seconds; defaults to 90, or 300 when --run-all-heavy is enabled",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.resolve() if args.output_dir else None
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    timeout_seconds = effective_timeout_seconds(
        args.timeout_seconds,
        run_all_heavy=args.run_all_heavy,
    )

    specs = build_audit_specs(
        output_dir=output_dir,
        run_all_heavy=args.run_all_heavy,
        check_remotes=args.check_remotes,
    )

    audit_results: dict[str, dict[str, Any]] = {}
    for name, spec in specs.items():
        command_result = run_command(spec["argv"], cwd=ROOT, timeout=timeout_seconds)
        try:
            report = _read_json_from_command(command_result, spec.get("output_path"))
        except Exception as exc:  # pragma: no cover - exercised via CLI failures
            failure_report = build_failure_report(
                failed_audit=name,
                error=str(exc),
                command_result=command_result,
                run_all_heavy=args.run_all_heavy,
                check_remotes=args.check_remotes,
                output_dir=output_dir,
            )
            write_report_file(failure_report, output_dir)
            sys.stdout.write(format_report(failure_report, compact=args.compact))
            return 2
        audit_results[name] = {
            "command": command_result,
            "report": report,
            "output_path": spec.get("output_path"),
        }

    snapshot = build_snapshot(
        audit_results,
        run_all_heavy=args.run_all_heavy,
        check_remotes=args.check_remotes,
        output_dir=output_dir,
    )
    write_report_file(snapshot, output_dir)
    sys.stdout.write(format_report(snapshot, compact=args.compact))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
