#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_CLAIMS_DIR = Path("/tmp/ict-engine-agent-claims/board-b-factor-refinement")
SUMMARY_CANDIDATES = (
    "summaries/terminal_decision_summary.md",
    "checks/terminal_metrics.json",
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
        if not line or line.startswith("#"):
            continue
        separator = _first_separator(line)
        if separator is None:
            summary_parts.append(line)
            continue
        key, value = line.split(separator, 1)
        key = key.strip()
        value = value.strip()
        if not key:
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


def _extract_bool(name: str, text: str) -> bool | None:
    match = re.search(rf"\b{re.escape(name)}\s*[:=]\s*(true|false)\b", text, re.IGNORECASE)
    if not match:
        return None
    return match.group(1).lower() == "true"


def _resolved_run_root(value: str | None, root: Path) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path


def _status(fields: dict[str, Any]) -> str:
    if fields.get("terminalized_at") or "terminalized" in str(fields.get("status", "")).lower():
        return "terminalized"
    if fields.get("decision"):
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
    run_root = _resolved_run_root(fields.get("run_root"), root)
    summary_flags = _load_summary_flags(run_root)
    promotion_allowed = fields.get("promotion_allowed")
    trade_usable = fields.get("trade_usable")
    if promotion_allowed is None:
        promotion_allowed = summary_flags.get("promotion_allowed")
    if trade_usable is None:
        trade_usable = summary_flags.get("trade_usable")

    return {
        "claim_file": path.name,
        "claim_path": str(path),
        "status": _status(fields),
        "owner": fields.get("owner") or fields.get("owner_id"),
        "scope": fields.get("scope") or fields.get("task") or fields.get("lane"),
        "decision": fields.get("decision"),
        "terminalized_at": fields.get("terminalized_at"),
        "run_root": str(run_root) if run_root else None,
        "run_root_exists": bool(run_root and run_root.exists()),
        "promotion_allowed": promotion_allowed,
        "trade_usable": trade_usable,
        "summary_files": summary_flags.get("summary_files", []),
    }


def _parse_claim_file(path: Path, text: str) -> dict[str, Any]:
    if path.suffix == ".json":
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            fields = {str(key): value for key, value in parsed.items() if isinstance(value, (str, int, float, bool))}
            serialized = json.dumps(parsed, sort_keys=True)
            fields["promotion_allowed"] = _extract_bool("promotion_allowed", serialized)
            fields["trade_usable"] = _extract_bool("trade_usable", serialized)
            return fields
    return parse_claim_text(text)


def summarize(claims: list[dict[str, Any]]) -> dict[str, Any]:
    active_claims = sum(1 for claim in claims if claim.get("status") != "terminalized")
    missing_run_roots = sum(1 for claim in claims if claim.get("run_root") and not claim.get("run_root_exists"))
    trade_usable_true = sum(1 for claim in claims if claim.get("trade_usable") is True)
    promotion_allowed_true = sum(1 for claim in claims if claim.get("promotion_allowed") is True)
    needs_attention = bool(active_claims or missing_run_roots or trade_usable_true or promotion_allowed_true)
    return {
        "status": "needs_attention" if needs_attention else "pass",
        "total_claims": len(claims),
        "terminalized_claims": sum(1 for claim in claims if claim.get("status") == "terminalized"),
        "active_claims": active_claims,
        "missing_run_roots": missing_run_roots,
        "trade_usable_true": trade_usable_true,
        "promotion_allowed_true": promotion_allowed_true,
    }


def build_report(claims_dir: Path, repo_root: Path) -> dict[str, Any]:
    claim_paths = sorted(path for path in claims_dir.glob("*") if path.is_file())
    claims = [read_claim(path, repo_root) for path in claim_paths]
    return {
        "schema_version": "factor-claim-terminalization-audit/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "claims_dir": str(claims_dir),
        "repo_root": str(repo_root),
        "summary": summarize(claims),
        "claims": claims,
    }


def format_report(report: dict[str, Any], compact: bool = False) -> dict[str, Any]:
    if not compact:
        return report

    claims = report.get("claims", [])
    root = str(report.get("repo_root") or "")
    attention_claims = [_compact_claim(claim, root) for claim in claims if _claim_needs_attention(claim)]
    return {
        "schema_version": report.get("schema_version"),
        "generated_at": report.get("generated_at"),
        "claims_dir": report.get("claims_dir"),
        "summary": report.get("summary"),
        "attention_claim_count": len(attention_claims),
        "attention_claims": attention_claims,
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
        "owner": _compact_text(claim.get("owner"), root),
        "scope": _compact_text(claim.get("scope"), root),
        "decision": _compact_text(claim.get("decision"), root),
        "run_root_state": run_root_state,
        "promotion_allowed": claim.get("promotion_allowed"),
        "trade_usable": claim.get("trade_usable"),
        "summary_files": claim.get("summary_files", []),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Board B factor claim terminalization state.")
    parser.add_argument("--claims-dir", type=Path, default=DEFAULT_CLAIMS_DIR)
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--compact", action="store_true", help="write token-friendly attention summary JSON")
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
                "missing_run_roots": 0,
                "trade_usable_true": 0,
                "promotion_allowed_true": 0,
                "error": "claims_dir_missing",
            },
            "claims": [],
        }
    else:
        report = build_report(claims_dir=claims_dir, repo_root=root)

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
