#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from path_defaults import resolve_repo_root

SCRIPTS_DIR = Path(__file__).resolve().parent
RESEARCH_DIR = SCRIPTS_DIR / "research"
if str(RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(RESEARCH_DIR))

from same_tree_practical_closure import REQUIRED_COMMAND_RESULT_STAGES  # noqa: E402

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
DEFAULT_DONE_LIGHT_CHILD_TIMEOUT_SECONDS = 240


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
    return 300


def effective_done_child_timeout_seconds(parent_timeout_seconds: int) -> int:
    return max(
        1,
        min(
            parent_timeout_seconds,
            DEFAULT_DONE_LIGHT_CHILD_TIMEOUT_SECONDS,
            max(30, parent_timeout_seconds - 60),
        ),
    )


def run_command(argv: list[str], cwd: Path, timeout: int = 60) -> dict[str, Any]:
    process = subprocess.Popen(
        argv,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except PermissionError:
            process.kill()
        stdout, stderr = process.communicate()
        return {
            "argv": argv,
            "returncode": None,
            "error": "timeout",
            "timeout_seconds": timeout,
            "stdout": _text(stdout or exc.stdout),
            "stderr": _text(stderr or exc.stderr),
        }
    return {
        "argv": argv,
        "returncode": process.returncode,
        "stdout": stdout,
        "stderr": stderr,
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
    done_child_timeout_seconds: int = DEFAULT_DONE_LIGHT_CHILD_TIMEOUT_SECONDS,
) -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}

    done_output = output_dir / "done_definition_audit.compact.json" if output_dir else None
    done_cmd = [sys.executable, str(DONE_AUDIT), "--compact"]
    done_cmd.extend(
        [
            "--practical-admission-source-timeout-seconds",
            str(done_child_timeout_seconds),
            "--help-audit-timeout-seconds",
            str(done_child_timeout_seconds),
        ]
    )
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
    practical_admission_source_surface = None
    await_launch_source_surface = None
    if isinstance(gates, list):
        for gate in gates:
            if not isinstance(gate, dict):
                continue
            if gate.get("id") == "quickstart_surface":
                quickstart_status = gate.get("status")
            elif gate.get("id") == "practical_admission_source_surface":
                practical_admission_source_surface = _source_debt_surface(gate)
            elif gate.get("id") == "await_launch_source_surface":
                await_launch_source_surface = _source_debt_surface(gate)
    return {
        "head": report.get("head"),
        "tracked_worktree_fingerprint": report.get("tracked_worktree_fingerprint"),
        "report_timestamp": report.get("timestamp_utc"),
        "status": summary.get("status"),
        "completion_ready": bool(summary.get("completion_ready")),
        "evidence_level": summary.get("evidence_level"),
        "pass_count": summary.get("pass_count"),
        "fail_count": summary.get("fail_count"),
        "skip_count": summary.get("skip_count"),
        "total_gates": summary.get("total_gates"),
        "quickstart_surface": quickstart_status,
        "practical_admission_source_surface": practical_admission_source_surface,
        "await_launch_source_surface": await_launch_source_surface,
        "unresolved": summary.get("unresolved", []),
        "skipped_gates": summary.get("skipped_gates", []),
        "next_action": summary.get("next_action"),
    }


def _source_debt_surface(gate: dict[str, Any]) -> dict[str, Any]:
    details = gate.get("details", {})
    if not isinstance(details, dict):
        details = {}
    return {
        "status": gate.get("status"),
        "tracked_violation_count": details.get("tracked_violation_count"),
        "tracked_violating_files": details.get("tracked_violating_files"),
        "untracked_violation_count": details.get("untracked_violation_count"),
        "untracked_violating_files": details.get("untracked_violating_files"),
        "violation_count": details.get("violation_count"),
        "violating_files": details.get("violating_files"),
        "debt_manifest_file": details.get("debt_manifest_file"),
        "quarantine": details.get("quarantine"),
        "sample_violations": details.get("sample_violations", []),
        "scanner_error": details.get("scanner_error"),
        "scanner_timeout_seconds": details.get("scanner_timeout_seconds"),
        "scanner_returncode": details.get("scanner_returncode"),
        "scanner_command": details.get("scanner_command"),
        "command": details.get("command"),
        "stdout": details.get("stdout"),
        "stderr": details.get("stderr"),
    }


def _done_definition_proof_status(
    proof: dict[str, Any] | None,
    *,
    output_dir: Path | None,
    current_done_surface: dict[str, Any],
) -> dict[str, Any] | None:
    if proof is None:
        return None
    report = proof.get("report")
    if not isinstance(report, dict):
        return {
            "proof_applied": False,
            "proof_rejected_reason": "proof_report_missing",
        }
    surface = _done_surface(report)
    proof_path = proof.get("path")
    if isinstance(proof_path, Path):
        surface["proof_source"] = _portable_path(proof_path, output_dir=output_dir)
    surface["proof_applied"] = False
    proof_head = surface.get("head")
    current_head = current_done_surface.get("head")
    if proof_head is None or current_head is None:
        surface["proof_rejected_reason"] = "proof_head_missing"
        return surface
    if proof_head != current_head:
        surface["proof_rejected_reason"] = "proof_head_mismatch"
        return surface
    proof_fingerprint = surface.get("tracked_worktree_fingerprint")
    current_fingerprint = current_done_surface.get("tracked_worktree_fingerprint")
    if current_fingerprint is not None and proof_fingerprint is None:
        surface["proof_rejected_reason"] = "proof_worktree_fingerprint_missing"
        surface["tracked_worktree_fingerprint"] = current_fingerprint
        return surface
    if proof_fingerprint is not None and current_fingerprint is not None and proof_fingerprint != current_fingerprint:
        surface["proof_rejected_reason"] = "proof_worktree_fingerprint_mismatch"
        surface["proof_worktree_fingerprint"] = proof_fingerprint
        surface["tracked_worktree_fingerprint"] = current_fingerprint
        return surface
    if not surface.get("completion_ready"):
        surface["proof_rejected_reason"] = "proof_not_completion_ready"
        return surface
    skipped_gates = surface.get("skipped_gates")
    if isinstance(skipped_gates, list) and skipped_gates:
        surface["proof_rejected_reason"] = "proof_has_skipped_gates"
        return surface
    surface["proof_applied"] = True
    return surface


def _apply_done_definition_proof(
    done_surface: dict[str, Any],
    proof_status: dict[str, Any] | None,
) -> dict[str, Any]:
    if proof_status is None:
        return done_surface
    if proof_status.get("proof_applied") is True:
        merged = dict(done_surface)
        for key in (
            "status",
            "completion_ready",
            "evidence_level",
            "unresolved",
            "skipped_gates",
            "next_action",
            "proof_source",
            "proof_applied",
            "tracked_worktree_fingerprint",
        ):
            if key in proof_status:
                merged[key] = proof_status[key]
        return merged
    merged = dict(done_surface)
    for key in (
        "proof_source",
        "proof_applied",
        "proof_rejected_reason",
        "proof_worktree_fingerprint",
        "tracked_worktree_fingerprint",
    ):
        if key in proof_status:
            merged[key] = proof_status[key]
    return merged


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
        "coordination_only_active_claims": summary.get("coordination_only_active_claims"),
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
        "same_tree_practical_closure": summary.get(
            "same_tree_practical_closure",
            report.get("same_tree_practical_closure"),
        ),
        "next_action": summary.get("next_action"),
        "attention_claim_count": report.get("attention_claim_count"),
        "attention_live_process_count": report.get("attention_live_process_count"),
        "attention_by_owner": by_owner,
        "attention_by_actionability": by_actionability,
        "attention_action_queue": attention_action_queue if isinstance(attention_action_queue, dict) else {},
    }


def _same_tree_practical_closure_detail(factor_surface: dict[str, Any]) -> dict[str, Any] | None:
    packet = factor_surface.get("same_tree_practical_closure")
    if not isinstance(packet, dict):
        return None
    if packet.get("status") != "pass":
        return None
    if packet.get("promotion_allowed") is not True:
        return None
    if packet.get("trade_usable") is not True:
        return None
    if packet.get("provider_execution_feedback_chain") != "pass":
        return None
    evidence_packet = packet.get("evidence_packet")
    if not isinstance(evidence_packet, str) or not evidence_packet.strip():
        return None
    if packet.get("evidence_packet_validated") is not True:
        return None
    return packet


def _practical_closure_blocker_detail(factor_surface: dict[str, Any]) -> dict[str, Any]:
    promotion_allowed = factor_surface.get("promotion_allowed_true")
    trade_usable = factor_surface.get("trade_usable_true")
    raw_flags_positive = any(
        isinstance(value, int) and value > 0
        for value in (promotion_allowed, trade_usable)
    )
    same_tree_practical_closure = factor_surface.get("same_tree_practical_closure")
    reason = (
        "raw_factor_claim_flags_are_not_validated_practical_closure"
        if raw_flags_positive
        else "validated_same_tree_practical_closure_packet_missing"
    )
    if (
        isinstance(same_tree_practical_closure, dict)
        and same_tree_practical_closure.get("evidence_packet_validated") is not True
    ):
        reason = "same_tree_practical_closure_evidence_not_validated"
    detail = {
        "reason": reason,
        "promotion_allowed_true": promotion_allowed,
        "trade_usable_true": trade_usable,
        "same_tree_practical_closure": same_tree_practical_closure,
        "missing_practical_chain_stages": _missing_practical_chain_stages(
            same_tree_practical_closure
        ),
        "blocking_context": _same_tree_blocking_context(factor_surface),
    }
    present_stages = _present_practical_chain_stages(same_tree_practical_closure)
    if present_stages:
        detail["present_practical_chain_stages"] = present_stages
    return detail


def _present_practical_chain_stages(packet: object) -> list[str]:
    if not isinstance(packet, dict):
        return []
    raw_value = packet.get("validated_stage_coverage")
    if raw_value is None:
        raw_value = packet.get("present_practical_chain_stages")
    if raw_value is None:
        raw_value = packet.get("command_result_stages")
    if not isinstance(raw_value, list):
        return []
    normalized = {normalized_stage for item in raw_value for normalized_stage in [_normalize_stage(item)] if normalized_stage}
    return [stage for stage in REQUIRED_COMMAND_RESULT_STAGES if stage in normalized]


def _missing_practical_chain_stages(packet: object) -> list[str]:
    present = set(_present_practical_chain_stages(packet))
    return [stage for stage in REQUIRED_COMMAND_RESULT_STAGES if stage not in present]


def _normalize_stage(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    return normalized or None


def _same_tree_blocking_context(factor_surface: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": factor_surface.get("status"),
        "blocking_reasons": factor_surface.get("blocking_reasons", []),
        "active_claims": factor_surface.get("active_claims"),
        "fresh_active_claims_without_live_process": factor_surface.get(
            "fresh_active_claims_without_live_process"
        ),
        "wait_only_active_claims_without_live_process": factor_surface.get(
            "wait_only_active_claims_without_live_process"
        ),
        "live_factor_processes": factor_surface.get("live_factor_processes"),
        "stale_safe_takeover_candidates": factor_surface.get("stale_safe_takeover_candidates"),
    }


def _factor_closure_blocker_detail(factor_surface: dict[str, Any]) -> dict[str, Any]:
    action_queue = factor_surface.get("attention_action_queue")
    return {
        "status": factor_surface.get("status"),
        "active_claims": factor_surface.get("active_claims"),
        "coordination_only_active_claims": factor_surface.get("coordination_only_active_claims"),
        "invalid_active_claims": factor_surface.get("invalid_active_claims"),
        "live_factor_processes": factor_surface.get("live_factor_processes"),
        "blocking_reasons": factor_surface.get("blocking_reasons", []),
        "attention_claim_count": factor_surface.get("attention_claim_count"),
        "attention_live_process_count": factor_surface.get("attention_live_process_count"),
        "attention_by_owner": factor_surface.get("attention_by_owner", {}),
        "attention_by_actionability": factor_surface.get("attention_by_actionability", {}),
        "action_queue": action_queue if isinstance(action_queue, dict) else {},
        "next_action": factor_surface.get("next_action"),
    }


def _compact_remote_details(remote_details: object) -> dict[str, Any] | None:
    if not isinstance(remote_details, dict):
        return None
    compact: dict[str, Any] = {}
    for key in (
        "enabled",
        "failed_sides",
        "origin_status",
        "release_mirror_status",
        "next_action",
    ):
        if key in remote_details:
            compact[key] = remote_details[key]
    return compact or None


def _release_readiness_blocker_detail(release_surface: dict[str, Any]) -> dict[str, Any]:
    detail = {
        "head": release_surface.get("head"),
        "report_timestamp": release_surface.get("report_timestamp"),
        "status": release_surface.get("status"),
        "unresolved": release_surface.get("unresolved", []),
        "pass_count": release_surface.get("pass_count"),
        "fail_count": release_surface.get("fail_count"),
        "skip_count": release_surface.get("skip_count"),
        "skipped_remote_gates": release_surface.get("skipped_remote_gates", []),
        "unresolved_next_actions": release_surface.get("unresolved_next_actions", {}),
    }
    remote_details = release_surface.get("remote_details")
    if isinstance(remote_details, dict):
        detail["remote_details"] = remote_details
    for key in ("proof_source", "proof_applied", "proof_rejected_reason"):
        if key in release_surface:
            detail[key] = release_surface[key]
    return detail


def _release_surface(report: dict[str, Any]) -> dict[str, Any]:
    summary = report.get("summary", {})
    gates = report.get("gates", [])
    unresolved_next_actions: dict[str, str] = {}
    skipped_remote_gates: list[str] = []
    if isinstance(gates, list):
        for gate in gates:
            if not isinstance(gate, dict):
                continue
            gate_id = gate.get("id")
            if not isinstance(gate_id, str):
                continue
            if gate.get("status") == "skip":
                details = gate.get("details", {})
                if (
                    isinstance(details, dict)
                    and details.get("enable_with") == "--check-remotes"
                    and details.get("reason") == "network_check_not_enabled"
                ):
                    skipped_remote_gates.append(gate_id)
            details = gate.get("details", {})
            if not isinstance(details, dict):
                continue
            next_action = details.get("next_action")
            if isinstance(next_action, str) and next_action:
                unresolved_next_actions[gate_id] = next_action
    return {
        "head": report.get("head"),
        "report_timestamp": report.get("timestamp_utc"),
        "status": summary.get("status"),
        "unresolved": summary.get("unresolved", []),
        "pass_count": summary.get("pass_count"),
        "fail_count": summary.get("fail_count"),
        "skip_count": summary.get("skip_count"),
        "skipped_remote_gates": skipped_remote_gates,
        "unresolved_next_actions": {
            gate_id: unresolved_next_actions[gate_id]
            for gate_id in summary.get("unresolved", [])
            if gate_id in unresolved_next_actions
        },
        "remote_details": _compact_remote_details(report.get("remote_details")),
    }


def _gate_status(report: dict[str, Any], gate_id: str) -> str | None:
    gates = report.get("gates", [])
    if not isinstance(gates, list):
        return None
    for gate in gates:
        if isinstance(gate, dict) and gate.get("id") == gate_id:
            status = gate.get("status")
            return status if isinstance(status, str) else None
    return None


def _release_skip_count(report: dict[str, Any], surface: dict[str, Any]) -> int | None:
    skip_count = surface.get("skip_count")
    if isinstance(skip_count, int):
        return skip_count
    gates = report.get("gates", [])
    if isinstance(gates, list):
        return sum(1 for gate in gates if isinstance(gate, dict) and gate.get("status") == "skip")
    return None


def _release_readiness_proof_status(
    proof: dict[str, Any] | None,
    *,
    output_dir: Path | None,
    check_remotes: bool,
    current_release_surface: dict[str, Any],
) -> dict[str, Any] | None:
    if proof is None:
        return None
    report = proof.get("report")
    if not isinstance(report, dict):
        return {
            "proof_applied": False,
            "proof_rejected_reason": "proof_report_missing",
        }
    surface = _release_surface(report)
    proof_path = proof.get("path")
    if isinstance(proof_path, Path):
        surface["proof_source"] = _portable_path(proof_path, output_dir=output_dir)
    surface["proof_applied"] = False
    if not check_remotes:
        surface["proof_rejected_reason"] = "snapshot_remote_checks_not_enabled"
        return surface

    proof_head = surface.get("head")
    current_head = current_release_surface.get("head")
    if proof_head != current_head:
        surface["proof_rejected_reason"] = "proof_head_mismatch"
        return surface

    remote_details = report.get("remote_details", {})
    remote_enabled = isinstance(remote_details, dict) and remote_details.get("enabled") is True
    if not remote_enabled or surface.get("skipped_remote_gates"):
        surface["proof_rejected_reason"] = "proof_remote_checks_not_enabled"
        return surface

    skip_count = _release_skip_count(report, surface)
    if isinstance(skip_count, int) and skip_count > 0:
        surface["proof_rejected_reason"] = "proof_has_skipped_gates"
        return surface

    worktree_status = _gate_status(report, "worktree_clean_for_release")
    if worktree_status is None:
        surface["proof_rejected_reason"] = "proof_worktree_clean_gate_missing"
        return surface
    if worktree_status != "pass":
        surface["proof_rejected_reason"] = "proof_worktree_not_clean"
        return surface

    surface["proof_applied"] = True
    return surface


def _apply_release_readiness_proof(
    release_surface: dict[str, Any],
    proof_status: dict[str, Any] | None,
) -> dict[str, Any]:
    if proof_status is None:
        return release_surface
    if proof_status.get("proof_applied") is True:
        return dict(proof_status)
    merged = dict(release_surface)
    for key in ("proof_source", "proof_applied", "proof_rejected_reason"):
        if key in proof_status:
            merged[key] = proof_status[key]
    return merged


def _source_debt_detail(source_surface: dict[str, Any]) -> dict[str, Any]:
    detail = {
        "tracked_violation_count": source_surface.get("tracked_violation_count"),
        "tracked_violating_files": source_surface.get("tracked_violating_files"),
        "untracked_violation_count": source_surface.get("untracked_violation_count"),
        "untracked_violating_files": source_surface.get("untracked_violating_files"),
        "violation_count": source_surface.get("violation_count"),
        "violating_files": source_surface.get("violating_files"),
    }
    debt_manifest_file = source_surface.get("debt_manifest_file")
    if debt_manifest_file is not None:
        detail["debt_manifest_file"] = debt_manifest_file
    return detail


def _source_surface_failure_detail(source_surface: dict[str, Any]) -> dict[str, Any]:
    detail = _source_debt_detail(source_surface)
    for key in (
        "status",
        "scanner_error",
        "scanner_timeout_seconds",
        "scanner_returncode",
        "scanner_command",
        "command",
        "stdout",
        "stderr",
    ):
        value = source_surface.get(key)
        if value not in (None, "", [], {}):
            detail[key] = value
    return detail


def _add_source_debt_blocker(
    blockers: list[str],
    blocker_details: dict[str, Any],
    source_surface: dict[str, Any] | None,
    *,
    blocker_key: str,
    quarantined_key: str | None = None,
) -> tuple[bool, bool]:
    if not isinstance(source_surface, dict):
        return False, False
    untracked_count = source_surface.get("untracked_violation_count")
    tracked_count = source_surface.get("tracked_violation_count")
    has_debt = any(isinstance(value, int) and value > 0 for value in (tracked_count, untracked_count))
    if not has_debt:
        return False, False
    quarantine = source_surface.get("quarantine")
    quarantine_matched = isinstance(quarantine, dict) and quarantine.get("matched") is True
    detail_key = quarantined_key if quarantine_matched and quarantined_key else blocker_key
    if not quarantine_matched:
        blockers.append(blocker_key)
    detail = _source_debt_detail(source_surface)
    if quarantine_matched:
        detail["quarantine_manifest_file"] = quarantine.get("manifest_file")
    blocker_details[detail_key] = detail
    return True, quarantine_matched


def _stage_source_debt_manifest(
    source_surface: dict[str, Any] | None,
    *,
    output_dir: Path | None,
    staged_name: str,
    evidence_key: str,
    evidence_files: dict[str, Any],
) -> None:
    if not output_dir or not isinstance(source_surface, dict):
        return
    debt_manifest_file = source_surface.get("debt_manifest_file")
    if not isinstance(debt_manifest_file, str) or not debt_manifest_file:
        return
    source_path = Path(debt_manifest_file).expanduser()
    if not source_path.exists():
        return
    staged_path = output_dir / staged_name
    if source_path.resolve() != staged_path.resolve():
        shutil.copyfile(source_path, staged_path)
    source_surface["debt_manifest_file"] = _portable_path(staged_path, output_dir=output_dir)
    evidence_files[evidence_key] = _portable_path(staged_path, output_dir=output_dir)


def _done_definition_blocker_detail(done_surface: dict[str, Any]) -> dict[str, Any]:
    detail = {
        "head": done_surface.get("head"),
        "tracked_worktree_fingerprint": done_surface.get("tracked_worktree_fingerprint"),
        "report_timestamp": done_surface.get("report_timestamp"),
        "status": done_surface.get("status"),
        "completion_ready": done_surface.get("completion_ready"),
        "evidence_level": done_surface.get("evidence_level"),
        "pass_count": done_surface.get("pass_count"),
        "fail_count": done_surface.get("fail_count"),
        "skip_count": done_surface.get("skip_count"),
        "total_gates": done_surface.get("total_gates"),
        "quickstart_surface": done_surface.get("quickstart_surface"),
        "unresolved": done_surface.get("unresolved", []),
        "skipped_gates": done_surface.get("skipped_gates", []),
        "next_action": done_surface.get("next_action"),
    }
    for key in (
        "proof_source",
        "proof_applied",
        "proof_rejected_reason",
        "proof_worktree_fingerprint",
    ):
        if key in done_surface:
            detail[key] = done_surface[key]
    for source_key in ("practical_admission_source_surface", "await_launch_source_surface"):
        source_surface = done_surface.get(source_key)
        if not isinstance(source_surface, dict):
            continue
        if source_surface.get("status") == "fail" or source_surface.get("scanner_error"):
            detail[source_key] = _source_surface_failure_detail(source_surface)
    return detail


def summarize_snapshot(
    done_surface: dict[str, Any],
    factor_surface: dict[str, Any],
    release_surface: dict[str, Any],
    *,
    snapshot_timestamp: str | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    blocker_details: dict[str, Any] = {}
    if not done_surface.get("completion_ready"):
        blockers.append("done_definition_not_completion_ready")
        blocker_details["done_definition_not_completion_ready"] = _done_definition_blocker_detail(
            done_surface
        )
    if done_surface.get("quickstart_surface") != "pass":
        blockers.append("quickstart_surface_drift")
    practical_source = done_surface.get("practical_admission_source_surface")
    _add_source_debt_blocker(
        blockers,
        blocker_details,
        practical_source,
        blocker_key="practical_admission_source_debt",
        quarantined_key="quarantined_practical_admission_source_debt",
    )
    await_launch_source = done_surface.get("await_launch_source_surface")
    await_launch_has_debt, await_launch_quarantined = _add_source_debt_blocker(
        blockers,
        blocker_details,
        await_launch_source,
        blocker_key="await_launch_source_debt",
        quarantined_key="quarantined_await_launch_source_debt",
    )
    if factor_surface.get("status") != "pass":
        blockers.append("factor_closure_blocked")
        blocker_details["factor_closure_blocked"] = _factor_closure_blocker_detail(
            factor_surface
        )
    practical_closure = _same_tree_practical_closure_detail(factor_surface)
    practical_closure_gap = (
        _practical_closure_blocker_detail(factor_surface) if practical_closure is None else None
    )
    if practical_closure_gap is not None:
        blocker_details["same_tree_practical_closure_unproven"] = practical_closure_gap
    if _same_tree_gap_should_block(factor_surface) and practical_closure is None:
        blockers.append("same_tree_practical_closure_unproven")
    if release_surface.get("status") != "pass":
        blockers.append("release_readiness_blocked")
        blocker_details["release_readiness_blocked"] = _release_readiness_blocker_detail(
            release_surface
        )
    skipped_remote_gates = release_surface.get("skipped_remote_gates")
    if isinstance(skipped_remote_gates, list) and skipped_remote_gates:
        blockers.append("release_remote_checks_not_run")
        blocker_details["release_remote_checks_not_run"] = {
            "skipped_gates": skipped_remote_gates,
        }

    manual_requirements_remaining = ["truthful_completion_commit"]
    if practical_closure is None:
        manual_requirements_remaining.insert(0, "same_tree_practical_closure_packet")
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
    if isinstance(done_next, str) and done_next and not done_surface.get("completion_ready"):
        prioritized_next_actions.append(
            {
                "surface": "done_definition",
                "reason": "completion_proof_gap",
                "action": done_next,
            }
        )
    if isinstance(practical_source, dict):
        untracked_count = practical_source.get("untracked_violation_count")
        quarantine = practical_source.get("quarantine")
        quarantine_matched = isinstance(quarantine, dict) and quarantine.get("matched") is True
        if isinstance(untracked_count, int) and untracked_count > 0 and not quarantine_matched:
            prioritized_next_actions.append(
                {
                    "surface": "done_definition",
                    "reason": "practical_admission_source_debt",
                    "action": "retire, quarantine, or track unsafe untracked practical-admission wrappers before objective closure",
                }
            )
    if await_launch_has_debt and not await_launch_quarantined:
        prioritized_next_actions.append(
            {
                "surface": "done_definition",
                "reason": "await_launch_source_debt",
                "action": "retire, quarantine, or track await-launch wrappers that can launch with active/fresh claims present",
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
            missing_run_root_claims = factor_queue.get("missing_run_root_claims", [])
            if isinstance(missing_run_root_claims, list) and missing_run_root_claims:
                for item in missing_run_root_claims:
                    if not isinstance(item, dict):
                        continue
                    claim_file = item.get("claim_file")
                    if isinstance(claim_file, str) and claim_file:
                        prioritized_next_actions.append(
                            {
                                "surface": "factor_closure",
                                "reason": "missing_run_root_claim",
                                "action": f"restore run root for {claim_file} or terminalize the claim with explicit evidence",
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
        if factor_surface.get("status") != "pass":
            prioritized_next_actions.append(
                {
                    "surface": "factor_closure",
                    "reason": "practical_closure_blocked",
                    "action": factor_next,
                }
            )
    if "same_tree_practical_closure_unproven" in blockers:
        prioritized_next_actions.append(
            {
                "surface": "factor_closure",
                "reason": "same_tree_practical_closure_unproven",
                "action": "produce or locate a validated same_tree_practical_closure packet; do not use raw promotion_allowed_true/trade_usable_true claim counters as proof",
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
    if "release_remote_checks_not_run" in blockers:
        prioritized_next_actions.append(
            {
                "surface": "release_readiness",
                "reason": "release_remote_checks_not_run",
                "action": "rerun objective closure with --check-remotes before treating release readiness as closed",
            }
        )
    return {
        "status": status,
        "completion_proven": False,
        "surface_green": surface_green,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "blocker_details": blocker_details,
        "manual_requirements_remaining": manual_requirements_remaining,
        "next_action": next_action,
        "child_next_actions": child_next_actions,
        "child_report_timestamps": child_report_timestamps,
        "child_report_age_seconds": child_report_age_seconds,
        "prioritized_next_actions": prioritized_next_actions,
    }


def _same_tree_gap_should_block(factor_surface: dict[str, Any]) -> bool:
    if factor_surface.get("status") == "pass":
        return True
    if isinstance(factor_surface.get("same_tree_practical_closure"), dict):
        return True
    return "promotion_allowed_true" in factor_surface or "trade_usable_true" in factor_surface


def build_snapshot(
    audit_results: dict[str, dict[str, Any]],
    *,
    run_all_heavy: bool,
    check_remotes: bool,
    output_dir: Path | None,
    done_definition_proof: dict[str, Any] | None = None,
    release_readiness_proof: dict[str, Any] | None = None,
) -> dict[str, Any]:
    done_report = audit_results["done_definition"]["report"]
    factor_report = audit_results["factor_closure"]["report"]
    release_report = audit_results["release_readiness"]["report"]

    snapshot_timestamp = _utc_now()
    current_done_surface = _done_surface(done_report)
    proof_status = _done_definition_proof_status(
        done_definition_proof,
        output_dir=output_dir,
        current_done_surface=current_done_surface,
    )
    done_surface = _apply_done_definition_proof(current_done_surface, proof_status)
    factor_surface = _factor_surface(factor_report)
    current_release_surface = _release_surface(release_report)
    release_proof_status = _release_readiness_proof_status(
        release_readiness_proof,
        output_dir=output_dir,
        check_remotes=check_remotes,
        current_release_surface=current_release_surface,
    )
    release_surface = _apply_release_readiness_proof(
        current_release_surface,
        release_proof_status,
    )

    evidence_files = {
        name: _portable_path(spec.get("output_path"), output_dir=output_dir)
        for name, spec in audit_results.items()
    }
    _stage_source_debt_manifest(
        done_surface.get("practical_admission_source_surface"),
        output_dir=output_dir,
        staged_name="practical_admission_source_debt_manifest.json",
        evidence_key="practical_admission_source_debt_manifest",
        evidence_files=evidence_files,
    )
    _stage_source_debt_manifest(
        done_surface.get("await_launch_source_surface"),
        output_dir=output_dir,
        staged_name="await_launch_source_debt_manifest.json",
        evidence_key="await_launch_source_debt_manifest",
        evidence_files=evidence_files,
    )
    summary = summarize_snapshot(
        done_surface,
        factor_surface,
        release_surface,
        snapshot_timestamp=snapshot_timestamp,
    )
    if done_definition_proof is not None:
        proof_path = done_definition_proof.get("path")
        evidence_files["done_definition_proof"] = (
            _portable_path(proof_path, output_dir=output_dir)
            if isinstance(proof_path, Path)
            else None
        )
    if release_readiness_proof is not None:
        proof_path = release_readiness_proof.get("path")
        evidence_files["release_readiness_proof"] = (
            _portable_path(proof_path, output_dir=output_dir)
            if isinstance(proof_path, Path)
            else None
        )

    return {
        "schema_version": "objective-closure-snapshot/v1",
        "timestamp_utc": snapshot_timestamp,
        "repo_root": _portable_repo_root(output_dir),
        "quickstart_chain": QUICKSTART_CHAIN,
        "options": {
            "run_all_heavy": run_all_heavy,
            "check_remotes": check_remotes,
            "output_dir": _portable_output_dir(output_dir),
            "done_definition_proof": evidence_files.get("done_definition_proof"),
            "release_readiness_proof": evidence_files.get("release_readiness_proof"),
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
        help="per-child timeout in seconds; defaults to 300",
    )
    parser.add_argument(
        "--done-definition-proof",
        type=Path,
        help="optional prior done_definition_audit JSON to apply when it proves full enabled gate coverage",
    )
    parser.add_argument(
        "--release-readiness-proof",
        type=Path,
        help="optional prior release_readiness_audit JSON from a clean selected export with remote checks enabled",
    )
    return parser.parse_args()


def read_done_definition_proof(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    resolved = path.resolve()
    parsed = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("done_definition_proof_must_be_object")
    return {"path": resolved, "report": parsed}


def stage_done_definition_proof(
    proof: dict[str, Any] | None,
    *,
    output_dir: Path | None,
) -> dict[str, Any] | None:
    if proof is None or output_dir is None:
        return proof
    report = proof.get("report")
    if not isinstance(report, dict):
        return proof
    staged_path = output_dir / "done_definition_proof.compact.json"
    staged_path.write_text(
        json.dumps(report, ensure_ascii=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return {"path": staged_path, "report": report}


def read_release_readiness_proof(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    resolved = path.resolve()
    parsed = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("release_readiness_proof_must_be_object")
    return {"path": resolved, "report": parsed}


def stage_release_readiness_proof(
    proof: dict[str, Any] | None,
    *,
    output_dir: Path | None,
) -> dict[str, Any] | None:
    if proof is None or output_dir is None:
        return proof
    report = proof.get("report")
    if not isinstance(report, dict):
        return proof
    staged_path = output_dir / "release_readiness_proof.compact.json"
    staged_path.write_text(
        json.dumps(report, ensure_ascii=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return {"path": staged_path, "report": report}


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.resolve() if args.output_dir else None
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    timeout_seconds = effective_timeout_seconds(
        args.timeout_seconds,
        run_all_heavy=args.run_all_heavy,
    )
    try:
        done_definition_proof = stage_done_definition_proof(
            read_done_definition_proof(args.done_definition_proof),
            output_dir=output_dir,
        )
    except Exception as exc:  # pragma: no cover - exercised via CLI failures
        failure_report = build_failure_report(
            failed_audit="done_definition_proof",
            error=str(exc),
            command_result={"argv": ["read", str(args.done_definition_proof)]},
            run_all_heavy=args.run_all_heavy,
            check_remotes=args.check_remotes,
            output_dir=output_dir,
        )
        write_report_file(failure_report, output_dir)
        sys.stdout.write(format_report(failure_report, compact=args.compact))
        return 2
    try:
        release_readiness_proof = stage_release_readiness_proof(
            read_release_readiness_proof(args.release_readiness_proof),
            output_dir=output_dir,
        )
    except Exception as exc:  # pragma: no cover - exercised via CLI failures
        failure_report = build_failure_report(
            failed_audit="release_readiness_proof",
            error=str(exc),
            command_result={"argv": ["read", str(args.release_readiness_proof)]},
            run_all_heavy=args.run_all_heavy,
            check_remotes=args.check_remotes,
            output_dir=output_dir,
        )
        write_report_file(failure_report, output_dir)
        sys.stdout.write(format_report(failure_report, compact=args.compact))
        return 2

    specs = build_audit_specs(
        output_dir=output_dir,
        run_all_heavy=args.run_all_heavy,
        check_remotes=args.check_remotes,
        done_child_timeout_seconds=effective_done_child_timeout_seconds(timeout_seconds),
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
        done_definition_proof=done_definition_proof,
        release_readiness_proof=release_readiness_proof,
    )
    write_report_file(snapshot, output_dir)
    sys.stdout.write(format_report(snapshot, compact=args.compact))
    return snapshot_exit_code(snapshot)


if __name__ == "__main__":
    raise SystemExit(main())
