#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
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


def _parse_iso_datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


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


def _portable_repo_root(output_dir: Path | None) -> str:
    if output_dir:
        return ROOT.name
    return str(ROOT)


def _portable_output_dir(output_dir: Path | None) -> str | None:
    if not output_dir:
        return None
    return "."


def _portable_path(path: Path | None, *, output_dir: Path | None) -> str | None:
    if path is None:
        return None
    if output_dir is not None:
        try:
            return str(path.resolve().relative_to(output_dir.resolve()))
        except ValueError:
            pass
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def _portable_argv(argv: list[str], *, output_dir: Path | None) -> list[str]:
    portable: list[str] = []
    for item in argv:
        try:
            path = Path(item)
        except TypeError:
            portable.append(str(item))
            continue
        if not path.is_absolute():
            portable.append(str(item))
            continue
        relative = _portable_path(path, output_dir=output_dir)
        if relative and relative != str(path):
            portable.append(relative)
            continue
        basename = path.name or str(item)
        if re.fullmatch(r"python(?:3(?:\.\d+)*)?", basename):
            portable.append("python3")
            continue
        portable.append(basename)
    return portable


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
    if output_dir:
        factor_cmd.append("--portable-paths")
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
        "next_action": summary.get("next_action"),
    }


def _factor_surface(report: dict[str, Any]) -> dict[str, Any]:
    summary = report.get("summary", {})
    attention_groups = report.get("attention_groups", {})
    attention_action_queue = report.get("attention_action_queue", {})
    by_owner = {}
    by_actionability = {}
    if isinstance(attention_groups, dict):
        maybe_by_owner = attention_groups.get("by_owner", {})
        if isinstance(maybe_by_owner, dict):
            by_owner = maybe_by_owner
        maybe_by_actionability = attention_groups.get("by_actionability", {})
        if isinstance(maybe_by_actionability, dict):
            by_actionability = maybe_by_actionability
    return {
        "report_timestamp": report.get("generated_at"),
        "status": summary.get("status"),
        "active_claims": summary.get("active_claims"),
        "invalid_active_claims": summary.get("invalid_active_claims"),
        "live_factor_processes": summary.get("live_factor_processes"),
        "active_claims_without_live_process": summary.get("active_claims_without_live_process"),
        "wait_only_active_claims_without_live_process": summary.get(
            "wait_only_active_claims_without_live_process"
        ),
        "fresh_active_claims_without_live_process": summary.get(
            "fresh_active_claims_without_live_process"
        ),
        "fresh_wait_only_active_claims_without_live_process": summary.get(
            "fresh_wait_only_active_claims_without_live_process"
        ),
        "stale_wait_only_active_claims_without_live_process": summary.get(
            "stale_wait_only_active_claims_without_live_process"
        ),
        "stale_safe_takeover_candidates": summary.get("stale_safe_takeover_candidates"),
        "blocking_reasons": summary.get("blocking_reasons", []),
        "promotion_allowed_true": summary.get("promotion_allowed_true"),
        "trade_usable_true": summary.get("trade_usable_true"),
        "next_action": summary.get("next_action"),
        "attention_claim_count": report.get("attention_claim_count"),
        "attention_live_process_count": report.get("attention_live_process_count"),
        "attention_by_owner": by_owner,
        "attention_by_actionability": by_actionability,
        "attention_action_queue": attention_action_queue if isinstance(attention_action_queue, dict) else {},
    }


def _release_surface(report: dict[str, Any]) -> dict[str, Any]:
    summary = report.get("summary", {})
    gates = report.get("gates", [])
    unresolved_next_actions: dict[str, str] = {}
    if isinstance(gates, list):
        for gate in gates:
            if not isinstance(gate, dict):
                continue
            gate_id = gate.get("id")
            if not isinstance(gate_id, str):
                continue
            details = gate.get("details", {})
            if not isinstance(details, dict):
                continue
            next_action = details.get("next_action")
            if isinstance(next_action, str) and next_action:
                unresolved_next_actions[gate_id] = next_action
    return {
        "report_timestamp": report.get("timestamp_utc"),
        "status": summary.get("status"),
        "unresolved": summary.get("unresolved", []),
        "pass_count": summary.get("pass_count"),
        "fail_count": summary.get("fail_count"),
        "skip_count": summary.get("skip_count"),
        "unresolved_next_actions": {
            gate_id: unresolved_next_actions[gate_id]
            for gate_id in summary.get("unresolved", [])
            if gate_id in unresolved_next_actions
        },
    }


def summarize_snapshot(
    done_surface: dict[str, Any],
    factor_surface: dict[str, Any],
    release_surface: dict[str, Any],
    *,
    snapshot_timestamp: str | None = None,
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
    child_next_actions = {
        "done_definition": done_surface.get("next_action"),
        "factor_closure": factor_surface.get("next_action"),
        "release_readiness": release_surface.get("unresolved_next_actions", {}),
    }
    child_report_timestamps = {
        "done_definition": done_surface.get("report_timestamp"),
        "factor_closure": factor_surface.get("report_timestamp"),
        "release_readiness": release_surface.get("report_timestamp"),
    }
    child_report_age_seconds: dict[str, int] = {}
    snapshot_dt = _parse_iso_datetime(snapshot_timestamp)
    if snapshot_dt is not None:
        for name, timestamp in child_report_timestamps.items():
            child_dt = _parse_iso_datetime(timestamp)
            if child_dt is None:
                continue
            child_report_age_seconds[name] = max(
                0, int((snapshot_dt - child_dt).total_seconds())
            )
    prioritized_next_actions: list[dict[str, str]] = []
    done_next = done_surface.get("next_action")
    if isinstance(done_next, str) and done_next:
        prioritized_next_actions.append(
            {
                "surface": "done_definition",
                "reason": "completion_proof_gap",
                "action": done_next,
            }
        )
    factor_next = factor_surface.get("next_action")
    if isinstance(factor_next, str) and factor_next:
        factor_queue = factor_surface.get("attention_action_queue", {})
        surfaced_factor_claims: set[str] = set()
        if isinstance(factor_queue, dict):
            fresh_claims = factor_queue.get("fresh_active_claims_without_live_process", [])
            if isinstance(fresh_claims, list) and fresh_claims:
                for item in fresh_claims:
                    if not isinstance(item, dict):
                        continue
                    claim_file = item.get("claim_file")
                    if isinstance(claim_file, str) and claim_file:
                        surfaced_factor_claims.add(claim_file)
                        prioritized_next_actions.append(
                            {
                                "surface": "factor_closure",
                                "reason": "fresh_active_claim_without_live_runtime",
                                "action": f"wait for owner progress or inspect fresh active claim {claim_file} before terminalizing",
                            }
                        )
            wait_only_claims = factor_queue.get("externalize_wait_only_claims", [])
            if isinstance(wait_only_claims, list) and wait_only_claims:
                for item in wait_only_claims:
                    if not isinstance(item, dict):
                        continue
                    claim_file = item.get("claim_file")
                    if isinstance(claim_file, str) and claim_file:
                        surfaced_factor_claims.add(claim_file)
                        stale_safe = bool(item.get("stale_safe_takeover_candidate"))
                        reason = (
                            "wait_only_stale_safe_takeover_candidate"
                            if stale_safe
                            else "wait_only_fresh_claim_without_live_runtime"
                        )
                        action = (
                            f"externalize or terminalize stale-safe {claim_file}"
                            if stale_safe
                            else f"wait for owner progress or stale-safe timeout on {claim_file}"
                        )
                        prioritized_next_actions.append(
                            {
                                "surface": "factor_closure",
                                "reason": reason,
                                "action": action,
                            }
                        )
            stale_claims = factor_queue.get("stale_safe_takeover_claims", [])
            if isinstance(stale_claims, list) and stale_claims:
                for item in stale_claims:
                    if not isinstance(item, dict):
                        continue
                    claim_file = item.get("claim_file")
                    if isinstance(claim_file, str) and claim_file:
                        if claim_file in surfaced_factor_claims:
                            continue
                        surfaced_factor_claims.add(claim_file)
                        prioritized_next_actions.append(
                            {
                                "surface": "factor_closure",
                                "reason": "stale_safe_takeover_queue_head",
                                "action": f"review takeover ownership of {claim_file}",
                            }
                        )
            live_roots = factor_queue.get("live_runtime_run_roots", [])
            if isinstance(live_roots, list) and live_roots:
                for item in live_roots:
                    if not isinstance(item, dict):
                        continue
                    pid = item.get("pid")
                    run_root = item.get("run_root")
                    if run_root:
                        pid_prefix = f"pid {pid} " if pid is not None else ""
                        prioritized_next_actions.append(
                            {
                                "surface": "factor_closure",
                                "reason": "live_runtime_queue_head",
                                "action": f"wait for {pid_prefix}run_root {run_root} to exit or claim it explicitly",
                            }
                        )
        prioritized_next_actions.append(
            {
                "surface": "factor_closure",
                "reason": "practical_closure_blocked",
                "action": factor_next,
            }
        )
    release_next_actions = release_surface.get("unresolved_next_actions", {})
    if isinstance(release_next_actions, dict):
        for gate_id, action in release_next_actions.items():
            if isinstance(action, str) and action:
                prioritized_next_actions.append(
                    {
                        "surface": "release_readiness",
                        "reason": gate_id,
                        "action": action,
                    }
                )
    return {
        "status": status,
        "completion_proven": False,
        "surface_green": surface_green,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "manual_requirements_remaining": manual_requirements_remaining,
        "next_action": next_action,
        "child_next_actions": child_next_actions,
        "child_report_timestamps": child_report_timestamps,
        "child_report_age_seconds": child_report_age_seconds,
        "prioritized_next_actions": prioritized_next_actions,
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

    snapshot_timestamp = _utc_now()
    done_surface = _done_surface(done_report)
    factor_surface = _factor_surface(factor_report)
    release_surface = _release_surface(release_report)
    summary = summarize_snapshot(
        done_surface,
        factor_surface,
        release_surface,
        snapshot_timestamp=snapshot_timestamp,
    )

    evidence_files = {
        name: _portable_path(spec.get("output_path"), output_dir=output_dir)
        for name, spec in audit_results.items()
    }

    return {
        "schema_version": "objective-closure-snapshot/v1",
        "timestamp_utc": snapshot_timestamp,
        "repo_root": _portable_repo_root(output_dir),
        "quickstart_chain": QUICKSTART_CHAIN,
        "options": {
            "run_all_heavy": run_all_heavy,
            "check_remotes": check_remotes,
            "output_dir": _portable_output_dir(output_dir),
        },
        "audit_commands": {
            name: _portable_argv(spec["command"]["argv"], output_dir=output_dir)
            for name, spec in audit_results.items()
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
        "repo_root": _portable_repo_root(output_dir),
        "quickstart_chain": QUICKSTART_CHAIN,
        "options": {
            "run_all_heavy": run_all_heavy,
            "check_remotes": check_remotes,
            "output_dir": _portable_output_dir(output_dir),
        },
        "summary": {
            "status": "snapshot_failed",
            "failed_audit": failed_audit,
            "error": error,
        },
        "command": {
            **command_result,
            "argv": _portable_argv(command_result.get("argv", []), output_dir=output_dir),
        },
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


def snapshot_exit_code(report: dict[str, Any]) -> int:
    summary = report.get("summary", {})
    if isinstance(summary, dict) and summary.get("status") == "snapshot_failed":
        return 2
    if isinstance(summary, dict) and summary.get("completion_proven") is True:
        return 0
    return 1


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
    return snapshot_exit_code(snapshot)


if __name__ == "__main__":
    raise SystemExit(main())
