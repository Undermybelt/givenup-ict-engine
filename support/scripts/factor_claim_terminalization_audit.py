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
from typing import Any


DEFAULT_CLAIMS_DIR = Path("/tmp/ict-engine-agent-claims/board-b-factor-refinement")
SUMMARY_CANDIDATES = (
    "summaries/terminal_decision_summary.md",
    "checks/terminal_metrics.json",
)
LIVE_FACTOR_PROCESS_MARKERS = (
    "run_tomac",
    "run_local_nq_csv_regime_rooted",
    "run_local_xau_csv_regime_rooted",
    "run_ibkr_",
    "run_bybit_",
    "run_yf_",
    "run_binance_",
    "run_kraken_",
    "run_external_",
    "tomac_session_seasonality_scan.py",
    "tomac_tod_portfolio_density_repair_scan.py",
    "tomac_tod_portfolio_aq.py",
    "auto-quant-agent-material",
    "fetch_external.py",
    "prepare_external.py",
)
RUN_ROOT_SENTINELS = {"none", "pending", "n/a", "na", "null", "-"}
TMP_RUN_ROOT_SUBDIRS = {"full", "out", "output", "checks", "summaries", "scripts", "state", "command-output", "materials"}
ACTIVE_CLAIM_REQUIRED_FIELDS = (
    "agent_name",
    "owner",
    "scope",
    "active_task",
    "non_goals",
    "write_surface",
    "status",
)


def repo_root(anchor: Path) -> Path:
    for candidate in [anchor, *anchor.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "src").exists():
            return candidate
    return Path.cwd()


def parse_claim_text(text: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    summary_parts: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith(("- ", "* ")):
            line = line[2:].strip()
        if not line or line.startswith("#"):
            continue
        separator = _first_separator(line)
        if separator is None:
            summary_parts.append(line)
            continue
        key, value = line.split(separator, 1)
        key = key.strip().lower().replace("-", "_")
        value = _normalize_scalar(value)
        if not key:
            continue
        if key == "run_root" and key in fields and _is_absolute_path_text(fields[key]) and not _is_absolute_path_text(value):
            continue
        fields[key] = value
        if key in {"summary", "terminal_summary"}:
            summary_parts.append(value)

    search_text = "\n".join([text, *summary_parts])
    fields["promotion_allowed"] = _extract_bool("promotion_allowed", search_text)
    fields["trade_usable"] = _extract_bool("trade_usable", search_text)
    return fields


def _first_separator(line: str) -> str | None:
    colon = line.find(":")
    equals = line.find("=")
    candidates = [idx for idx in [colon, equals] if idx >= 0]
    if not candidates:
        return None
    return line[min(candidates)]


def _normalize_scalar(value: object) -> object:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'`', '"', "'"}:
        return text[1:-1].strip()
    return text


def _is_absolute_path_text(value: object) -> bool:
    return isinstance(value, str) and Path(value).expanduser().is_absolute()


def _extract_bool(name: str, text: str) -> bool | None:
    match = re.search(rf"\b{re.escape(name)}\s*[:=]\s*(true|false)\b", text, re.IGNORECASE)
    if not match:
        return None
    return match.group(1).lower() == "true"


def _resolved_run_root(value: str | None, root: Path) -> Path | None:
    if not value:
        return None
    normalized = str(value).strip().lower()
    if normalized in RUN_ROOT_SENTINELS or normalized.startswith("pending_"):
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path


def _status(fields: dict[str, Any]) -> str:
    status = str(fields.get("status", "")).lower()
    if (
        fields.get("terminalized_at")
        or fields.get("terminal_at")
        or fields.get("terminal_status")
        or status.startswith("terminal")
        or "terminalized" in status
    ):
        return "terminalized"
    if fields.get("decision") or fields.get("terminal_decision"):
        return "terminalized"
    return "active"


def _load_summary_flags(run_root: Path | None) -> dict[str, Any]:
    if run_root is None or not run_root.exists():
        return {}
    evidence: dict[str, Any] = {}
    for rel_path in SUMMARY_CANDIDATES:
        path = run_root / rel_path
        if not path.exists() or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        evidence.setdefault("summary_files", []).append(rel_path)
        if path.suffix == ".json":
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict):
                for key in ("promotion_allowed", "trade_usable"):
                    value = _find_key(parsed, key)
                    if isinstance(value, bool):
                        evidence[key] = value
        for key in ("promotion_allowed", "trade_usable"):
            value = _extract_bool(key, text)
            if value is not None:
                evidence[key] = value
    return evidence


def _find_key(value: object, target: str) -> object:
    if isinstance(value, dict):
        if target in value:
            return value[target]
        for nested in value.values():
            found = _find_key(nested, target)
            if found is not None:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = _find_key(nested, target)
            if found is not None:
                return found
    return None


def read_claim(path: Path, root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    fields = _parse_claim_file(path, text)
    claim_root = _claim_repo_root(fields, root)
    run_root = _resolved_run_root(fields.get("run_root"), claim_root)
    tmp_root = _resolved_run_root(fields.get("tmp_root"), claim_root)
    summary_flags = _load_summary_flags(run_root)
    promotion_allowed = fields.get("promotion_allowed")
    trade_usable = fields.get("trade_usable")
    if promotion_allowed is None:
        promotion_allowed = summary_flags.get("promotion_allowed")
    if trade_usable is None:
        trade_usable = summary_flags.get("trade_usable")
    status = _status(fields)
    missing_identity_fields = _missing_active_claim_identity_fields(fields) if status != "terminalized" else []

    return {
        "claim_file": path.name,
        "claim_path": str(path),
        "status": status,
        "agent_name": fields.get("agent_name"),
        "owner": fields.get("owner") or fields.get("owner_id"),
        "scope": fields.get("scope") or fields.get("task") or fields.get("lane"),
        "active_task": fields.get("active_task"),
        "non_goals": fields.get("non_goals"),
        "write_surface": fields.get("write_surface"),
        "decision": fields.get("decision") or fields.get("terminal_decision") or fields.get("terminal_status"),
        "terminalized_at": fields.get("terminalized_at") or fields.get("terminal_at"),
        "run_root": str(run_root) if run_root else None,
        "run_root_exists": bool(run_root and run_root.exists()),
        "tmp_root": str(tmp_root) if tmp_root else None,
        "tmp_root_exists": bool(tmp_root and tmp_root.exists()),
        "missing_identity_fields": missing_identity_fields,
        "promotion_allowed": promotion_allowed,
        "trade_usable": trade_usable,
        "summary_files": summary_flags.get("summary_files", []),
    }


def _missing_active_claim_identity_fields(fields: dict[str, Any]) -> list[str]:
    missing = [
        field
        for field in ACTIVE_CLAIM_REQUIRED_FIELDS
        if not str(fields.get(field) or "").strip()
    ]
    if not str(fields.get("run_root") or "").strip() and not str(fields.get("tmp_root") or "").strip():
        missing.append("run_root_or_tmp_root")
    return missing


def _claim_repo_root(fields: dict[str, Any], fallback: Path) -> Path:
    for key in ("repo", "repo_root"):
        raw_value = fields.get(key)
        if not isinstance(raw_value, str) or not raw_value.strip():
            continue
        candidate = Path(raw_value).expanduser()
        if candidate.is_absolute() and candidate.exists():
            return candidate
    return fallback


def _parse_claim_file(path: Path, text: str) -> dict[str, Any]:
    if path.suffix == ".json":
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            fields = {str(key): _normalize_scalar(value) for key, value in parsed.items() if isinstance(value, (str, int, float, bool))}
            serialized = json.dumps(parsed, sort_keys=True)
            fields["promotion_allowed"] = _extract_bool("promotion_allowed", serialized)
            fields["trade_usable"] = _extract_bool("trade_usable", serialized)
            return fields
    return parse_claim_text(text)


def summarize(claims: list[dict[str, Any]], live_processes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    live_processes = live_processes or []
    active_claims = sum(1 for claim in claims if claim.get("status") != "terminalized")
    invalid_active_claims = sum(
        1
        for claim in claims
        if claim.get("status") != "terminalized" and claim.get("missing_identity_fields")
    )
    valid_active_claims = active_claims - invalid_active_claims
    missing_run_roots = sum(1 for claim in claims if claim.get("run_root") and not claim.get("run_root_exists"))
    trade_usable_true = sum(1 for claim in claims if claim.get("trade_usable") is True)
    promotion_allowed_true = sum(1 for claim in claims if claim.get("promotion_allowed") is True)
    live_factor_processes = len(live_processes)
    needs_attention = bool(
        active_claims
        or invalid_active_claims
        or missing_run_roots
        or trade_usable_true
        or promotion_allowed_true
        or live_factor_processes
    )
    blocking_reasons: list[str] = []
    next_actions: list[str] = []
    if active_claims:
        blocking_reasons.append("active_claims")
        next_actions.append("terminalize or externalize active claims")
    if invalid_active_claims:
        blocking_reasons.append("invalid_active_claims")
        next_actions.append("repair active claims with agent_name, exact task, non_goals, write_surface, and run/tmp root")
    if live_factor_processes:
        blocking_reasons.append("live_factor_processes")
        next_actions.append("wait for live factor processes to exit or claim them before closure")
    if missing_run_roots:
        blocking_reasons.append("missing_run_roots")
        next_actions.append("restore or terminalize missing run roots")
    if trade_usable_true:
        blocking_reasons.append("trade_usable_true")
        next_actions.append("review positive trade/promotion flags")
    if promotion_allowed_true:
        blocking_reasons.append("promotion_allowed_true")
        if "review positive trade/promotion flags" not in next_actions:
            next_actions.append("review positive trade/promotion flags")
    return {
        "status": "needs_attention" if needs_attention else "pass",
        "total_claims": len(claims),
        "terminalized_claims": sum(1 for claim in claims if claim.get("status") == "terminalized"),
        "active_claims": active_claims,
        "valid_active_claims": valid_active_claims,
        "invalid_active_claims": invalid_active_claims,
        "live_factor_processes": live_factor_processes,
        "missing_run_roots": missing_run_roots,
        "trade_usable_true": trade_usable_true,
        "promotion_allowed_true": promotion_allowed_true,
        "blocking_reasons": blocking_reasons,
        "next_action": "; ".join(next_actions) if next_actions else "no claim terminalization blockers found",
    }


def build_report(
    claims_dir: Path,
    repo_root: Path,
    live_processes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    claim_paths = sorted(path for path in claims_dir.glob("*") if path.is_file() and _is_claim_artifact(path))
    claims = [read_claim(path, repo_root) for path in claim_paths]
    live_processes = live_processes or []
    return {
        "schema_version": "factor-claim-terminalization-audit/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "claims_dir": str(claims_dir),
        "repo_root": str(repo_root),
        "summary": summarize(claims, live_processes=live_processes),
        "claims": claims,
        "live_factor_processes": live_processes,
    }


def _is_claim_artifact(path: Path) -> bool:
    name = path.name
    if name.startswith("terminalization_audit_"):
        return False
    if name.endswith((".summary.json", ".summary.json.check", ".claim.pretty", ".json.pretty", ".exit")):
        return False
    if path.suffix != ".json":
        return True
    return not name.endswith("_audit.json")


def detect_live_factor_processes() -> list[dict[str, Any]]:
    try:
        completed = subprocess.run(
            ["ps", "-axo", "pid,ppid,etime,command"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    if completed.returncode != 0:
        return []

    current_pid = os.getpid()
    processes: list[dict[str, Any]] = []
    for line in completed.stdout.splitlines()[1:]:
        parts = line.strip().split(None, 3)
        if len(parts) != 4:
            continue
        pid_text, ppid_text, elapsed, command = parts
        try:
            pid = int(pid_text)
            ppid = int(ppid_text)
        except ValueError:
            continue
        if pid == current_pid or "factor_claim_terminalization_audit.py" in command:
            continue
        if not _is_live_factor_command(command):
            continue
        run_root = _extract_run_root(command)
        exit_file = _infer_exit_file(run_root, command)
        processes.append(
            {
                "pid": pid,
                "ppid": ppid,
                "elapsed": elapsed,
                "run_root": str(run_root) if run_root else None,
                "exit_file": str(exit_file) if exit_file else None,
                "exit_file_exists": bool(exit_file and exit_file.exists()),
                "command_excerpt": _command_excerpt(command),
            }
        )
    return _dedupe_live_processes(_attribute_parent_run_roots(processes))


def _is_live_factor_command(command: str) -> bool:
    if _looks_like_readback_command(command):
        return False
    return any(marker in command for marker in LIVE_FACTOR_PROCESS_MARKERS)


def _looks_like_readback_command(command: str) -> bool:
    if re.match(r"^(?:\S*/)?(?:rg|grep|egrep|fgrep)\s", command.strip()):
        return True
    if ("ps -axo" in command or "ps auxww" in command) and (
        "| rg" in command or " rg " in command or "| grep" in command
    ):
        return True
    if re.search(r"(?:^|\s|['\"])(?:\S*/)?sed\s+-n\s+", command):
        return True
    readback_markers = ("ps -axo", "ps auxww", " rg ", " tail -n", " find ")
    if not any(marker in command for marker in readback_markers):
        return False
    return "python" not in command and "auto-quant-agent-material" not in command


def _extract_run_root(command: str) -> Path | None:
    assignment = re.search(r"\bRUN_ROOT=([^\s;]+)", command)
    if assignment:
        return _normalize_tmp_run_root(Path(assignment.group(1).strip("'\"")))

    out_arg = re.search(r"--(?:out|run-root|run_root)\s+([^\s;]+)", command)
    if out_arg:
        return _normalize_tmp_run_root(Path(out_arg.group(1).strip("'\"")))

    state_dir_arg = re.search(r"--state-dir\s+([^\s;]+)", command)
    if state_dir_arg:
        return _normalize_tmp_run_root(Path(state_dir_arg.group(1).strip("'\"")))

    output_arg = re.search(r"--output\s+([^\s;]+)", command)
    if output_arg:
        run_root = _run_root_from_artifact_path(Path(output_arg.group(1).strip("'\"")))
        if run_root:
            return run_root

    tmp_match = re.search(r"(/(?:private/)?tmp/ict-engine-[^\s;'\"`]+)", command)
    if tmp_match:
        return _normalize_tmp_run_root(Path(tmp_match.group(1)))
    return None


def _normalize_tmp_run_root(path: Path) -> Path:
    current = path
    if current.suffix:
        current = current.parent
    tmp_lane_root = _tmp_ict_engine_lane_root(current)
    if tmp_lane_root:
        return tmp_lane_root
    if current.name in TMP_RUN_ROOT_SUBDIRS:
        return current.parent
    return current


def _tmp_ict_engine_lane_root(path: Path) -> Path | None:
    for candidate in [path, *path.parents]:
        if not candidate.name.startswith("ict-engine-"):
            continue
        parent = candidate.parent
        if str(parent) in {"/tmp", "/private/tmp"}:
            return candidate
    return None


def _run_root_from_artifact_path(path: Path) -> Path | None:
    for candidate in [path, *path.parents]:
        if candidate.parent.name == "runs":
            return candidate
    return None


def _infer_exit_file(run_root: Path | None, command: str) -> Path | None:
    if run_root is None:
        return None
    if "01_full_repair" in command or "run_tomac_psar_arooncci" in command:
        return run_root / "checks" / "01_full_repair.exit"
    checks_dir = run_root / "checks"
    fetch_exit = _infer_fetch_exit_file(checks_dir, command)
    if fetch_exit:
        return fetch_exit
    if checks_dir.exists():
        exit_files = sorted(checks_dir.glob("*.exit"))
        if exit_files:
            return exit_files[0]
    return None


def _infer_fetch_exit_file(checks_dir: Path, command: str) -> Path | None:
    output_arg = re.search(r"--output\s+([^\s;]+)", command)
    if not output_arg:
        return None
    stem = Path(output_arg.group(1).strip("'\"")).stem
    parts = stem.split("_")
    if len(parts) < 3:
        return None
    return checks_dir / f"fetch_{parts[-2]}_{parts[-1]}.exit"


def _command_excerpt(command: str, limit: int = 240) -> str:
    compact = " ".join(command.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _attribute_parent_run_roots(processes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_pid = {int(process["pid"]): process for process in processes if process.get("pid") is not None}
    for child in processes:
        run_root = child.get("run_root")
        ppid = child.get("ppid")
        if not run_root and ppid is not None:
            try:
                parent = by_pid.get(int(ppid))
            except (TypeError, ValueError):
                parent = None
            if parent and parent.get("run_root"):
                child["run_root"] = parent.get("run_root")
                child["run_root_attribution"] = "parent_process"
                child["run_root_attribution_pid"] = parent.get("pid")
            continue
        if not run_root or ppid is None:
            continue
        try:
            parent = by_pid.get(int(ppid))
        except (TypeError, ValueError):
            continue
        if not parent or parent.get("run_root"):
            continue
        parent["run_root"] = run_root
        parent["run_root_attribution"] = "child_process"
        parent["run_root_attribution_pid"] = child.get("pid")
    return processes


def _dedupe_live_processes(processes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for process in processes:
        key = str(process.get("run_root") or process.get("pid"))
        current = by_key.get(key)
        if current is None or _process_rank(process) > _process_rank(current):
            by_key[key] = process
    return sorted(by_key.values(), key=lambda item: int(item.get("pid") or 0))


def _process_rank(process: dict[str, Any]) -> int:
    command = str(process.get("command_excerpt") or "")
    if "/bin/zsh -lc" in command or "/bin/bash -lc" in command:
        return 0
    if "python" in command or command.endswith(".py"):
        return 2
    return 1


def format_report(report: dict[str, Any], compact: bool = False) -> dict[str, Any]:
    if not compact:
        return report

    claims = report.get("claims", [])
    root = str(report.get("repo_root") or "")
    attention_claims = [_compact_claim(claim, root) for claim in claims if _claim_needs_attention(claim)]
    live_processes = [_compact_live_process(process, root) for process in report.get("live_factor_processes", [])]
    return {
        "schema_version": report.get("schema_version"),
        "generated_at": report.get("generated_at"),
        "claims_dir": report.get("claims_dir"),
        "summary": report.get("summary"),
        "attention_claim_count": len(attention_claims),
        "attention_live_process_count": len(live_processes),
        "attention_groups": _attention_groups(attention_claims),
        "attention_claims": attention_claims,
        "attention_live_processes": live_processes,
    }


def _claim_needs_attention(claim: dict[str, Any]) -> bool:
    return bool(
        claim.get("status") != "terminalized"
        or (claim.get("run_root") and not claim.get("run_root_exists"))
        or claim.get("promotion_allowed") is True
        or claim.get("trade_usable") is True
    )


def _compact_text(value: object, root: str) -> object:
    if not isinstance(value, str):
        return value
    result = value
    if root:
        result = result.replace(root + "/", "")
        result = result.replace(root, ".")
    return re.sub(r"/Users/[^\s,;:)]+", "[local-path]", result)


def _compact_claim(claim: dict[str, Any], root: str) -> dict[str, Any]:
    run_root_state = "none"
    if claim.get("run_root"):
        run_root_state = "present" if claim.get("run_root_exists") else "missing"
    return {
        "claim_file": _compact_text(claim.get("claim_file"), root),
        "status": _compact_text(claim.get("status"), root),
        "agent_name": _compact_text(claim.get("agent_name"), root),
        "owner": _compact_text(claim.get("owner"), root),
        "scope": _compact_text(claim.get("scope"), root),
        "decision": _compact_text(claim.get("decision"), root),
        "run_root_state": run_root_state,
        "missing_identity_fields": claim.get("missing_identity_fields", []),
        "promotion_allowed": claim.get("promotion_allowed"),
        "trade_usable": claim.get("trade_usable"),
        "summary_files": claim.get("summary_files", []),
    }


def _compact_live_process(process: dict[str, Any], root: str) -> dict[str, Any]:
    run_root_state = "none"
    if process.get("run_root"):
        run_root_state = "present"
    exit_file_state = "none"
    if process.get("exit_file"):
        exit_file_state = "present" if process.get("exit_file_exists") else "missing"
    return {
        "pid": process.get("pid"),
        "ppid": process.get("ppid"),
        "elapsed": process.get("elapsed"),
        "run_root_state": run_root_state,
        "exit_file_state": exit_file_state,
        "run_root": _compact_text(process.get("run_root"), root),
        "exit_file": _compact_text(process.get("exit_file"), root),
        "command_excerpt": _compact_text(process.get("command_excerpt"), root),
    }


def _attention_groups(claims: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return {
        "by_owner": _count_by(claims, "owner"),
        "by_run_root_state": _count_by(claims, "run_root_state"),
        "by_status": _count_by(claims, "status"),
    }


def _count_by(claims: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for claim in claims:
        raw_value = claim.get(key)
        value = str(raw_value) if raw_value not in (None, "") else "unknown"
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Board B factor claim terminalization state.")
    parser.add_argument("--claims-dir", type=Path, default=DEFAULT_CLAIMS_DIR)
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--compact", action="store_true", help="write token-friendly attention summary JSON")
    parser.add_argument("--skip-live-processes", action="store_true", help="skip ps-based live factor process readback")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = args.repo_root.resolve() if args.repo_root else repo_root(Path(__file__).resolve())
    claims_dir = args.claims_dir.expanduser()
    if not claims_dir.exists():
        report = {
            "schema_version": "factor-claim-terminalization-audit/v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "claims_dir": str(claims_dir),
            "repo_root": str(root),
            "summary": {
                "status": "needs_attention",
                "total_claims": 0,
                "terminalized_claims": 0,
                "active_claims": 0,
                "valid_active_claims": 0,
                "invalid_active_claims": 0,
                "live_factor_processes": 0,
                "missing_run_roots": 0,
                "trade_usable_true": 0,
                "promotion_allowed_true": 0,
                "error": "claims_dir_missing",
            },
            "claims": [],
            "live_factor_processes": [],
        }
    else:
        live_processes = [] if args.skip_live_processes else detect_live_factor_processes()
        report = build_report(claims_dir=claims_dir, repo_root=root, live_processes=live_processes)

    output_report = format_report(report, compact=args.compact)
    indent = None if args.compact else 2
    output_text = json.dumps(output_report, indent=indent, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_text, encoding="utf-8")
    else:
        sys.stdout.write(output_text)
    return 1 if report["summary"]["status"] == "needs_attention" else 0


if __name__ == "__main__":
    raise SystemExit(main())
