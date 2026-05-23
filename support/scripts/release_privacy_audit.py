#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_PATTERNS = [
    ("maintainer_path", re.compile(r"/Users/(?!example\b)[^\s`'\"):,]+")),
    ("private_tmp_path", re.compile(r"/private/tmp/[^\s`'\"):,]+")),
    ("downloads_path", re.compile(r"(?:^|[\s`'\"(/])Downloads(?:/[^\s`'\"):,]+)?")),
    ("homebrew_path", re.compile(r"/opt/homebrew/[^\s`'\"):,]+")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("openai_key", re.compile(r"(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{20,}(?![A-Za-z0-9_-])")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]+")),
    ("private_key_marker", re.compile(r"BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY")),
]


TEXT_SUFFIXES = {
    "",
    ".bash",
    ".cfg",
    ".csv",
    ".err",
    ".example",
    ".html",
    ".ini",
    ".json",
    ".jsonl",
    ".lock",
    ".md",
    ".out",
    ".py",
    ".rs",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True)
class Hit:
    path: str
    line: int
    kind: str
    classification: str
    excerpt: str


def is_text_candidate(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in TEXT_SUFFIXES


def iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if is_text_candidate(path):
            yield path


def rust_test_lines(text: str) -> set[int]:
    test_lines: set[int] = set()
    in_test = False
    brace_depth = 0
    pending_test_attr = False
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#[test]"):
            pending_test_attr = True
        if pending_test_attr and stripped.startswith("fn "):
            in_test = True
            pending_test_attr = False
        if in_test:
            test_lines.add(line_no)
            brace_depth += line.count("{") - line.count("}")
            if brace_depth <= 0 and "}" in line:
                in_test = False
                brace_depth = 0
    return test_lines


def classify_hit(rel_path: str, line_text: str, kind: str, in_test_context: bool = False) -> str:
    if in_test_context:
        return "test_or_policy_reference"
    if kind in {"aws_access_key", "openai_key", "slack_token", "private_key_marker"}:
        return "release_blocking"
    if rel_path.startswith("support/scripts/tests/") or rel_path.startswith("tests/"):
        return "test_or_policy_reference"
    if "test_" in Path(rel_path).name:
        return "test_or_policy_reference"
    if rel_path in {"AGENT.md", "CLAUDE.md"}:
        return "test_or_policy_reference"
    if rel_path.startswith("support/scripts/"):
        if (
            "assert" in line_text
            or "forbidden" in line_text
            or "redact" in line_text.lower()
            or "pattern" in line_text
            or "re.compile" in line_text
            or "re.sub" in line_text
        ):
            return "test_or_policy_reference"
        if kind in {"homebrew_path", "downloads_path"}:
            return "operator_reference"
    if rel_path.startswith("support/docs/bug/"):
        return "historical_docs"
    if rel_path.startswith("support/docs/plans/"):
        return "historical_docs"
    if rel_path.startswith("support/docs/experiments/"):
        return "historical_docs"
    if rel_path.startswith("support/docs/") and kind in {"maintainer_path", "private_tmp_path", "downloads_path"}:
        return "historical_docs"
    if kind in {"maintainer_path", "private_tmp_path", "downloads_path"}:
        return "release_blocking"
    return "operator_reference"


def scan_root(root: Path) -> list[Hit]:
    hits: list[Hit] = []
    for path in iter_files(root):
        rel_path = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        test_lines = rust_test_lines(text) if path.suffix == ".rs" else set()
        for line_no, line in enumerate(text.splitlines(), start=1):
            for kind, pattern in DEFAULT_PATTERNS:
                if not pattern.search(line):
                    continue
                hits.append(
                    Hit(
                        path=rel_path,
                        line=line_no,
                        kind=kind,
                        classification=classify_hit(rel_path, line, kind, line_no in test_lines),
                        excerpt=redact_excerpt(line),
                    )
                )
    return hits


def redact_excerpt(line: str) -> str:
    redacted = re.sub(r"/Users/[^\s`'\"):,]+", "/Users/<redacted>", line)
    redacted = re.sub(r"/private/tmp/[^\s`'\"):,]+", "/private/tmp/<redacted>", redacted)
    redacted = re.sub(r"AKIA[0-9A-Z]{16}", "AKIA<redacted>", redacted)
    redacted = re.sub(r"sk-[A-Za-z0-9_-]{20,}", "sk-<redacted>", redacted)
    redacted = re.sub(r"xox[baprs]-[A-Za-z0-9-]+", "xox-<redacted>", redacted)
    return redacted.strip()[:240]


def summarize_hits(hits: list[Hit]) -> dict[str, Any]:
    by_class: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    blocking_paths: set[str] = set()
    for hit in hits:
        by_class[hit.classification] = by_class.get(hit.classification, 0) + 1
        by_kind[hit.kind] = by_kind.get(hit.kind, 0) + 1
        if hit.classification == "release_blocking":
            blocking_paths.add(hit.path)
    release_blocking_count = by_class.get("release_blocking", 0)
    return {
        "status": "pass" if release_blocking_count == 0 else "needs_fix",
        "total_hits": len(hits),
        "release_blocking_hits": release_blocking_count,
        "release_blocking_paths": sorted(blocking_paths),
        "by_classification": dict(sorted(by_class.items())),
        "by_kind": dict(sorted(by_kind.items())),
        "next_action": (
            "no release-blocking private path or secret hits found"
            if release_blocking_count == 0
            else "remove or redact release-blocking hits, then rerun release privacy audit"
        ),
    }


def build_report(root: Path, sample_limit: int) -> dict[str, Any]:
    root = root.resolve()
    hits = scan_root(root)
    samples = [hit.__dict__ for hit in hits[:sample_limit]]
    blocking_samples = [
        hit.__dict__ for hit in hits if hit.classification == "release_blocking"
    ][:sample_limit]
    return {
        "schema_version": "release-privacy-audit/v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "root": str(root),
        "summary": summarize_hits(hits),
        "blocking_samples": blocking_samples,
        "samples": samples,
    }


def compact_report(report: dict[str, Any]) -> dict[str, Any]:
    compact = dict(report)
    compact.pop("root", None)
    compact["samples"] = report.get("samples", [])[:10]
    compact["blocking_samples"] = report.get("blocking_samples", [])[:10]
    return compact


def format_report(report: dict[str, Any], compact: bool) -> str:
    payload = compact_report(report) if compact else report
    if compact:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit release export privacy/path hygiene.")
    parser.add_argument("root", nargs="?", default=".", help="Release export or repo root to scan")
    parser.add_argument("--sample-limit", type=int, default=50)
    parser.add_argument("--output", help="Optional JSON output path")
    parser.add_argument("--compact", action="store_true", help="Emit token-friendly JSON")
    args = parser.parse_args()

    report = build_report(Path(args.root), sample_limit=max(args.sample_limit, 0))
    text = format_report(report, compact=args.compact)
    if args.output:
        Path(args.output).write_text(format_report(report, compact=False), encoding="utf-8")
    print(text, end="")
    raise SystemExit(0 if report["summary"]["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
