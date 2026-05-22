#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from path_defaults import resolve_repo_root

ROOT = resolve_repo_root(__file__)
MAIN_RS_GUARDRAILS_PATH = ROOT / "support" / "docs" / "main-rs-guardrails.md"
MAIN_RS_PATH = ROOT / "src" / "main.rs"
README_PATH = ROOT / "README.md"
CONSUMER_QUICKSTART_PATH = ROOT / "support" / "docs" / "consumer-quickstart.md"
CONTRIBUTOR_QUICKSTART_PATH = ROOT / "support" / "docs" / "contributor-quickstart.md"
SCRIPTS_GUIDE_PATH = ROOT / "support" / "scripts" / "SCRIPTS.md"
SCRIPT_MANIFEST_PATH = ROOT / "support" / "scripts" / "script_manifest.json"
HELP_AUDIT_PATH = ROOT / "support" / "scripts" / "help_audit.py"
SMOKE_SCRIPT_PATH = ROOT / "support" / "scripts" / "smoke_acceptance.sh"
DEFAULT_SMOKE_STATE_DIR = "/tmp/ict-engine-done-definition-audit-smoke"


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
        for path in [CONSUMER_QUICKSTART_PATH, CONTRIBUTOR_QUICKSTART_PATH]
        if not path.exists()
    ]
    status = "pass" if not missing_links and not missing_files else "fail"
    return _gate(
        "quickstart_surface",
        status,
        {
            "missing_readme_links": missing_links,
            "missing_quickstart_files": missing_files,
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


def run_command(
    cmd: list[str],
    *,
    cwd: Path,
    timeout: int,
    env: dict[str, str] | None = None,
) -> tuple[str, dict]:
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        return "fail", {
            "command": cmd,
            "timeout_seconds": timeout,
            "error": "timeout",
            "stdout": (exc.stdout or "").strip(),
            "stderr": (exc.stderr or "").strip(),
        }

    return (
        "pass" if result.returncode == 0 else "fail",
        {
            "command": cmd,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        },
    )


def evaluate_help_audit_policy(timeout_seconds: int) -> dict:
    if not HELP_AUDIT_PATH.exists():
        return _gate(
            "help_audit_none_output_policy",
            "fail",
            {"error": f"missing file: {HELP_AUDIT_PATH.relative_to(ROOT)}"},
        )

    status, details = run_command(
        [sys.executable, str(HELP_AUDIT_PATH)],
        cwd=ROOT,
        timeout=timeout_seconds,
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


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


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
        env = os.environ.copy()
        env["STATE_DIR"] = args.smoke_state_dir
        env.setdefault("OUT_DIR", "/tmp/ict-engine-done-definition-audit-smoke-out")
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
    return {
        "status": status,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "skip_count": skip_count,
        "total_gates": len(gates),
        "unresolved": unresolved,
    }


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
        default=DEFAULT_SMOKE_STATE_DIR,
        help=f"STATE_DIR for smoke script (default: {DEFAULT_SMOKE_STATE_DIR}).",
    )
    parser.add_argument(
        "--help-audit-timeout-seconds",
        type=int,
        default=180,
        help="Timeout for `support/scripts/help_audit.py`.",
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
    gates.append(evaluate_help_audit_policy(args.help_audit_timeout_seconds))
    gates.extend(evaluate_heavy_checks(args))

    summary = summarize(gates)
    report = {
        "timestamp_utc": _utc_now(),
        "repo_root": str(ROOT),
        "summary": summary,
        "gates": gates,
    }

    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
