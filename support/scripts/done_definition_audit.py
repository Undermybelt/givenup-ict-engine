#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from path_defaults import resolve_repo_root

ROOT = resolve_repo_root(__file__)
MAIN_RS_GUARDRAILS_PATH = ROOT / "support" / "docs" / "main-rs-guardrails.md"
MAIN_RS_PATH = ROOT / "src" / "main.rs"
AGENT_ENTRY_PATH = ROOT / "AGENT.md"
README_PATH = ROOT / "README.md"
CONSUMER_QUICKSTART_PATH = ROOT / "support" / "docs" / "consumer-quickstart.md"
CONTRIBUTOR_QUICKSTART_PATH = ROOT / "support" / "docs" / "contributor-quickstart.md"
SCRIPTS_GUIDE_PATH = ROOT / "support" / "scripts" / "SCRIPTS.md"
SCRIPT_MANIFEST_PATH = ROOT / "support" / "scripts" / "script_manifest.json"
HELP_AUDIT_PATH = ROOT / "support" / "scripts" / "help_audit.py"
SMOKE_SCRIPT_PATH = ROOT / "support" / "scripts" / "smoke_acceptance.sh"
PRACTICAL_ADMISSION_SOURCE_CHECK_PATH = (
    ROOT / "support" / "scripts" / "research" / "downstream_practical_admission_source_check.py"
)
PRACTICAL_ADMISSION_WRAPPER_ROOT = (
    ROOT / "support" / "docs" / "experiments" / "actionable-regime-confidence" / "scripts"
)
DEFAULT_SMOKE_STATE_PREFIX = "/tmp/ict-engine-done-definition-audit-smoke"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _gate(gate_id: str, status: str, details: dict, *, heavy: bool = False) -> dict:
    return {
        "id": gate_id,
        "status": status,
        "heavy": heavy,
        "details": details,
    }


def parse_main_rs_baseline(guardrails_text: str) -> int:
    match = re.search(r"`src/main\.rs`:\s*([0-9][0-9,]*)\s+lines", guardrails_text)
    if not match:
        raise ValueError("main.rs baseline not found in guardrails doc")
    return int(match.group(1).replace(",", ""))


def count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def evaluate_main_rs_guardrail(
    guardrails_text: str,
    current_main_rs_lines: int,
) -> dict:
    baseline = parse_main_rs_baseline(guardrails_text)
    delta = current_main_rs_lines - baseline
    status = "pass" if delta <= 0 else "fail"
    return _gate(
        "main_rs_line_guardrail",
        status,
        {
            "baseline_lines": baseline,
            "current_lines": current_main_rs_lines,
            "delta_lines": delta,
            "rule": "current_lines <= baseline_lines",
        },
    )


def evaluate_quickstart_surface() -> dict:
    if not README_PATH.exists():
        return _gate(
            "quickstart_surface",
            "fail",
            {"error": f"missing file: {README_PATH.relative_to(ROOT)}"},
        )

    readme_text = README_PATH.read_text(encoding="utf-8")
    required_links = [
        "support/docs/consumer-quickstart.md",
        "support/docs/contributor-quickstart.md",
    ]
    missing_links = [link for link in required_links if link not in readme_text]
    missing_files = [
        str(path.relative_to(ROOT))
        for path in [AGENT_ENTRY_PATH, CONSUMER_QUICKSTART_PATH, CONTRIBUTOR_QUICKSTART_PATH]
        if not path.exists()
    ]
    command_blocks = {
        str(AGENT_ENTRY_PATH.relative_to(ROOT)): (
            "cargo run --quiet -- provider-status --compact\n"
            "cargo run --quiet -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-first-run --human\n"
            "cargo run --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --refresh --agent"
        ),
        str(CONSUMER_QUICKSTART_PATH.relative_to(ROOT)): (
            "cargo run --quiet -- provider-status --compact\n"
            "cargo run --quiet -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-first-run --human\n"
            "cargo run --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --refresh --agent\n"
            "cargo run --quiet -- pre-bayes-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --refresh --output-format json\n"
            "cargo run --quiet -- policy-training-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --output-format agent"
        ),
        str(README_PATH.relative_to(ROOT)): (
            "cargo run -- provider-status --compact\n"
            "cargo run -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-first-run --human\n"
            "cargo run -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --refresh --agent"
        ),
    }
    command_order_drift: list[str] = []
    if not missing_files:
        for rel_path, expected_block in command_blocks.items():
            text = (ROOT / rel_path).read_text(encoding="utf-8")
            if expected_block not in text:
                command_order_drift.append(rel_path)

    status = (
        "pass"
        if not missing_links and not missing_files and not command_order_drift
        else "fail"
    )
    return _gate(
        "quickstart_surface",
        status,
        {
            "missing_readme_links": missing_links,
            "missing_quickstart_files": missing_files,
            "command_order_drift": command_order_drift,
        },
    )


def evaluate_script_governance() -> dict:
    missing = [
        str(path.relative_to(ROOT))
        for path in [SCRIPTS_GUIDE_PATH, SCRIPT_MANIFEST_PATH]
        if not path.exists()
    ]
    status = "pass" if not missing else "fail"
    return _gate(
        "script_governance_surface",
        status,
        {"missing_required_files": missing},
    )


def _completed_stream_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def run_command(
    cmd: list[str],
    *,
    cwd: Path,
    timeout: int,
    env: dict[str, str] | None = None,
) -> tuple[str, dict]:
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
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
        return "fail", {
            "command": cmd,
            "timeout_seconds": timeout,
            "error": "timeout",
            "stdout": _completed_stream_text(stdout or exc.stdout).strip(),
            "stderr": _completed_stream_text(stderr or exc.stderr).strip(),
        }

    return (
        "pass" if process.returncode == 0 else "fail",
        {
            "command": cmd,
            "returncode": process.returncode,
            "stdout": stdout.strip(),
            "stderr": stderr.strip(),
        },
    )


def evaluate_help_audit_policy(timeout_seconds: int) -> dict:
    if not HELP_AUDIT_PATH.exists():
        return _gate(
            "help_audit_none_output_policy",
            "fail",
            {"error": f"missing file: {HELP_AUDIT_PATH.relative_to(ROOT)}"},
        )

    env = dict(os.environ)
    env["ICT_ENGINE_HELP_AUDIT_BUILD_TIMEOUT_SECONDS"] = str(timeout_seconds)
    status, details = run_command(
        [sys.executable, str(HELP_AUDIT_PATH)],
        cwd=ROOT,
        timeout=timeout_seconds,
        env=env,
    )
    if status == "fail":
        return _gate("help_audit_none_output_policy", "fail", details)

    try:
        report = json.loads(details["stdout"])
    except json.JSONDecodeError as exc:
        return _gate(
            "help_audit_none_output_policy",
            "fail",
            {
                "command": details["command"],
                "error": f"invalid_help_audit_json: {exc}",
                "stdout": details["stdout"],
            },
        )

    summary = report.get("summary", {})
    policy = report.get("none_output_mode_policy", {})
    policy_ok = bool(summary.get("none_output_mode_policy_matches_expected"))
    return _gate(
        "help_audit_none_output_policy",
        "pass" if policy_ok else "fail",
        {
            "summary": {
                "command_count": summary.get("command_count"),
                "commands_with_no_output_modes": summary.get(
                    "commands_with_no_output_modes"
                ),
                "none_output_mode_policy_matches_expected": summary.get(
                    "none_output_mode_policy_matches_expected"
                ),
                "status": summary.get("status"),
            },
            "policy": {
                "unclassified_none_commands": policy.get(
                    "unclassified_none_commands", []
                ),
                "missing_expected_commands": policy.get(
                    "missing_expected_commands", []
                ),
            },
        },
    )


def _rel_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def tracked_wrapper_file_set(wrapper_files: list[Path], timeout_seconds: int) -> set[Path]:
    if not wrapper_files:
        return set()
    status, details = run_command(
        ["git", "ls-files", "--", *[str(path.relative_to(ROOT)) for path in wrapper_files]],
        cwd=ROOT,
        timeout=timeout_seconds,
    )
    if status != "pass":
        return set(wrapper_files)
    tracked: set[Path] = set()
    for line in str(details.get("stdout") or "").splitlines():
        rel_path = line.strip()
        if rel_path:
            tracked.add((ROOT / rel_path).resolve())
    return tracked


def _summarize_practical_admission_scan(reports: list[dict], *, tracked_files: set[Path]) -> dict:
    tracked_file_paths = {path.resolve() for path in tracked_files}
    violations: list[dict] = []
    violating_files: set[str] = set()
    by_type: Counter[str] = Counter()
    tracked_reports = 0
    untracked_reports = 0
    tracked_violations: list[dict] = []
    untracked_violations: list[dict] = []
    tracked_violating_files: set[str] = set()
    untracked_violating_files: set[str] = set()
    for report in reports:
        file_path = str(report.get("file") or "")
        resolved_path = Path(file_path).resolve() if file_path else None
        is_tracked = bool(resolved_path and resolved_path in tracked_file_paths)
        if is_tracked:
            tracked_reports += 1
        else:
            untracked_reports += 1
        for violation in report.get("violations") or []:
            normalized = dict(violation)
            if file_path:
                normalized["file"] = _repo_relative_text(file_path, str(ROOT))
            violations.append(normalized)
            if is_tracked:
                tracked_violations.append(normalized)
            else:
                untracked_violations.append(normalized)
            if file_path:
                violating_files.add(file_path)
                if is_tracked:
                    tracked_violating_files.add(file_path)
                else:
                    untracked_violating_files.add(file_path)
            by_type[str(violation.get("violation") or "unknown")] += 1

    return {
        "scanned_files": len(reports),
        "violating_files": len(violating_files),
        "violation_count": len(violations),
        "tracked_scanned_files": tracked_reports,
        "tracked_violating_files": len(tracked_violating_files),
        "tracked_violation_count": len(tracked_violations),
        "untracked_scanned_files": untracked_reports,
        "untracked_violating_files": len(untracked_violating_files),
        "untracked_violation_count": len(untracked_violations),
        "violations_by_type": dict(sorted(by_type.items())),
        "sample_violations": tracked_violations[:10] or untracked_violations[:10],
    }


def evaluate_practical_admission_source_gate(timeout_seconds: int) -> dict:
    if not PRACTICAL_ADMISSION_SOURCE_CHECK_PATH.exists():
        return _gate(
            "practical_admission_source_surface",
            "fail",
            {"error": f"missing file: {_rel_path(PRACTICAL_ADMISSION_SOURCE_CHECK_PATH)}"},
        )
    if not PRACTICAL_ADMISSION_WRAPPER_ROOT.exists():
        return _gate(
            "practical_admission_source_surface",
            "fail",
            {"error": f"missing wrapper root: {_rel_path(PRACTICAL_ADMISSION_WRAPPER_ROOT)}"},
        )

    wrapper_files = sorted(PRACTICAL_ADMISSION_WRAPPER_ROOT.glob("run_*.py"))
    if not wrapper_files:
        return _gate(
            "practical_admission_source_surface",
            "fail",
            {"error": f"no run_*.py wrappers found under {_rel_path(PRACTICAL_ADMISSION_WRAPPER_ROOT)}"},
        )

    status, details = run_command(
        [sys.executable, str(PRACTICAL_ADMISSION_SOURCE_CHECK_PATH), *map(str, wrapper_files)],
        cwd=ROOT,
        timeout=timeout_seconds,
    )
    try:
        reports = json.loads(details.get("stdout") or "[]")
    except json.JSONDecodeError as exc:
        failed_details = dict(details)
        failed_details["error"] = f"invalid_practical_admission_scan_json: {exc}"
        return _gate("practical_admission_source_surface", "fail", failed_details)

    if not isinstance(reports, list):
        failed_details = dict(details)
        failed_details["error"] = "invalid_practical_admission_scan_shape"
        return _gate("practical_admission_source_surface", "fail", failed_details)

    tracked_files = tracked_wrapper_file_set(wrapper_files, timeout_seconds)
    summary = _summarize_practical_admission_scan(reports, tracked_files=tracked_files)
    summary["scanner_returncode"] = details.get("returncode")
    summary["rule"] = (
        "all tracked downstream/gate wrappers must keep practical flags behind "
        "practical_admission_flags(..., extension_complete=...) and avoid 2bps/density fail-open gates"
    )
    if status == "fail" and summary["violation_count"] == 0:
        summary["stderr"] = details.get("stderr", "")
        return _gate("practical_admission_source_surface", "fail", summary)
    return _gate(
        "practical_admission_source_surface",
        "pass" if summary["tracked_violation_count"] == 0 else "fail",
        summary,
    )


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _fresh_smoke_state_dir() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{DEFAULT_SMOKE_STATE_PREFIX}-{timestamp}-{os.getpid()}"


def build_smoke_environment(
    args: argparse.Namespace,
    *,
    base_env: dict[str, str] | None = None,
) -> dict[str, str]:
    env = dict(base_env if base_env is not None else os.environ)
    state_dir = str(getattr(args, "smoke_state_dir", "") or "").strip()
    if not state_dir:
        state_dir = _fresh_smoke_state_dir()
    env["STATE_DIR"] = state_dir
    env.setdefault("OUT_DIR", f"{state_dir}-out")
    return env


def evaluate_heavy_checks(args: argparse.Namespace) -> list[dict]:
    run_all_heavy = args.run_all_heavy or _env_flag(
        "ICT_ENGINE_DONE_DEFINITION_RUN_HEAVY"
    )
    run_cargo_check = args.run_cargo_check or _env_flag(
        "ICT_ENGINE_DONE_DEFINITION_RUN_CARGO_CHECK"
    )
    run_cargo_clippy = args.run_cargo_clippy or _env_flag(
        "ICT_ENGINE_DONE_DEFINITION_RUN_CARGO_CLIPPY"
    )
    run_cargo_test = args.run_cargo_test or _env_flag(
        "ICT_ENGINE_DONE_DEFINITION_RUN_CARGO_TEST"
    )
    run_smoke = args.run_smoke or _env_flag("ICT_ENGINE_DONE_DEFINITION_RUN_SMOKE")

    gates: list[dict] = []
    checks = [
        (
            "cargo_check_all_targets",
            run_all_heavy or run_cargo_check,
            ["cargo", "check", "--all-targets"],
        ),
        (
            "cargo_clippy_all_targets_deny_warnings",
            run_all_heavy or run_cargo_clippy,
            ["cargo", "clippy", "--all-targets", "--", "-D", "warnings"],
        ),
        ("cargo_test", run_all_heavy or run_cargo_test, ["cargo", "test"]),
    ]
    for gate_id, should_run, cmd in checks:
        if not should_run:
            enable_flag_map = {
                "cargo_check_all_targets": "--run-cargo-check",
                "cargo_clippy_all_targets_deny_warnings": "--run-cargo-clippy",
                "cargo_test": "--run-cargo-test",
            }
            gates.append(
                _gate(
                    gate_id,
                    "skip",
                    {
                        "reason": "heavy_check_not_enabled",
                        "enable_with": enable_flag_map[gate_id],
                    },
                    heavy=True,
                )
            )
            continue
        status, details = run_command(
            cmd,
            cwd=ROOT,
            timeout=args.heavy_timeout_seconds,
        )
        gates.append(_gate(gate_id, status, details, heavy=True))

    smoke_gate_id = "smoke_acceptance_tmp_state"
    if not (run_all_heavy or run_smoke):
        gates.append(
            _gate(
                smoke_gate_id,
                "skip",
                {
                    "reason": "heavy_check_not_enabled",
                    "enable_with": "--run-smoke",
                },
                heavy=True,
            )
        )
    else:
        env = build_smoke_environment(args)
        status, details = run_command(
            ["bash", str(SMOKE_SCRIPT_PATH)],
            cwd=ROOT,
            timeout=args.heavy_timeout_seconds,
            env=env,
        )
        gates.append(_gate(smoke_gate_id, status, details, heavy=True))

    return gates


def summarize(gates: list[dict]) -> dict:
    pass_count = sum(1 for gate in gates if gate["status"] == "pass")
    fail_count = sum(1 for gate in gates if gate["status"] == "fail")
    skip_count = sum(1 for gate in gates if gate["status"] == "skip")
    status = "pass" if fail_count == 0 else "needs_fix"
    unresolved = [gate["id"] for gate in gates if gate["status"] == "fail"]
    skipped = [gate["id"] for gate in gates if gate["status"] == "skip"]
    completion_ready = fail_count == 0 and skip_count == 0
    if fail_count:
        evidence_level = "failing_gates"
        next_action = "fix failing gates, then rerun done-definition audit"
    elif skip_count:
        evidence_level = "partial_skipped_gates"
        next_action = "rerun with --run-all-heavy before treating done-definition as completion proof"
    else:
        evidence_level = "full_enabled_gate_coverage"
        next_action = "done-definition gates have full enabled coverage"
    return {
        "status": status,
        "completion_ready": completion_ready,
        "evidence_level": evidence_level,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "skip_count": skip_count,
        "skipped_gates": skipped,
        "total_gates": len(gates),
        "unresolved": unresolved,
        "next_action": next_action,
    }


def _repo_relative_text(value: str, root: str) -> str:
    if not root:
        return value
    replacements = (root + "/", root)
    result = value
    result = result.replace(replacements[0], "")
    result = result.replace(replacements[1], ".")
    return result


def _compact_value(value, root: str):
    if isinstance(value, str):
        return _repo_relative_text(value, root)
    if isinstance(value, list):
        return [_compact_value(item, root) for item in value]
    if isinstance(value, dict):
        return {key: _compact_value(nested, root) for key, nested in value.items()}
    return value


def _compact_gate(gate: dict, root: str) -> dict:
    compact = {
        "id": gate.get("id"),
        "status": gate.get("status"),
        "heavy": gate.get("heavy", False),
    }
    if gate.get("status") != "pass":
        compact["details"] = _compact_value(gate.get("details", {}), root)
    return compact


def format_report(report: dict, *, compact: bool = False) -> str:
    if not compact:
        return json.dumps(report, indent=2) + "\n"

    root = str(report.get("repo_root") or "")
    gates = report.get("gates", [])
    compact_report = {
        "timestamp_utc": report.get("timestamp_utc"),
        "summary": report.get("summary"),
        "gate_count": len(gates),
        "gates": [_compact_gate(gate, root) for gate in gates],
    }
    return json.dumps(compact_report, sort_keys=True, separators=(",", ":")) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit Done Definition gates with zero-config lightweight checks by default. "
            "Heavy compile/lint/test/smoke gates are opt-in."
        )
    )
    parser.add_argument(
        "--run-all-heavy",
        action="store_true",
        help="Run all heavy checks: cargo check/clippy/test and smoke script.",
    )
    parser.add_argument(
        "--run-cargo-check",
        action="store_true",
        help="Run `cargo check --all-targets`.",
    )
    parser.add_argument(
        "--run-cargo-clippy",
        action="store_true",
        help="Run `cargo clippy --all-targets -- -D warnings`.",
    )
    parser.add_argument(
        "--run-cargo-test",
        action="store_true",
        help="Run `cargo test`.",
    )
    parser.add_argument(
        "--run-smoke",
        action="store_true",
        help="Run `support/scripts/smoke_acceptance.sh` with a `/tmp` state dir.",
    )
    parser.add_argument(
        "--smoke-state-dir",
        default="",
        help=(
            "STATE_DIR for smoke script. Defaults to a fresh /tmp path per audit run; "
            "set explicitly only when debugging a chosen state directory."
        ),
    )
    parser.add_argument(
        "--help-audit-timeout-seconds",
        type=int,
        default=180,
        help="Timeout for `support/scripts/help_audit.py`.",
    )
    parser.add_argument(
        "--practical-admission-source-timeout-seconds",
        type=int,
        default=180,
        help="Timeout for downstream practical-admission wrapper source scan.",
    )
    parser.add_argument(
        "--heavy-timeout-seconds",
        type=int,
        default=900,
        help="Timeout for each heavy check command.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional output JSON file path. Always prints JSON to stdout.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print token-friendly JSON without repo-local absolute paths.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    gates: list[dict] = []

    if not MAIN_RS_GUARDRAILS_PATH.exists():
        gates.append(
            _gate(
                "main_rs_line_guardrail",
                "fail",
                {"error": f"missing file: {MAIN_RS_GUARDRAILS_PATH.relative_to(ROOT)}"},
            )
        )
    elif not MAIN_RS_PATH.exists():
        gates.append(
            _gate(
                "main_rs_line_guardrail",
                "fail",
                {"error": f"missing file: {MAIN_RS_PATH.relative_to(ROOT)}"},
            )
        )
    else:
        guardrails_text = MAIN_RS_GUARDRAILS_PATH.read_text(encoding="utf-8")
        current_lines = count_lines(MAIN_RS_PATH)
        try:
            gates.append(evaluate_main_rs_guardrail(guardrails_text, current_lines))
        except ValueError as exc:
            gates.append(_gate("main_rs_line_guardrail", "fail", {"error": str(exc)}))

    gates.append(evaluate_quickstart_surface())
    gates.append(evaluate_script_governance())
    gates.append(
        evaluate_practical_admission_source_gate(
            args.practical_admission_source_timeout_seconds
        )
    )
    gates.append(evaluate_help_audit_policy(args.help_audit_timeout_seconds))
    gates.extend(evaluate_heavy_checks(args))

    summary = summarize(gates)
    report = {
        "timestamp_utc": _utc_now(),
        "repo_root": str(ROOT),
        "summary": summary,
        "gates": gates,
    }

    output_text = format_report(report, compact=args.compact)
    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_text, encoding="utf-8")

    sys.stdout.write(output_text)
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
