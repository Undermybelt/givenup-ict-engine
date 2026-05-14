#!/usr/bin/env python3
"""Bounded local search for R6 owner-export/control files."""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import time
from pathlib import Path


RUN_ID = "20260512T060032-codex-r6-local-owner-export-intake-search-v1"
GATE = "r6_local_owner_export_intake_search_v1=no_local_owner_export_or_control_rows_no_promotion"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "command-output"
PACKET = ROOT / "r6-local-owner-export-intake-search-v1"
CHECKS = ROOT / "checks"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
TARGET_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]

SEARCH_ROOTS = [
    Path.home() / "Downloads",
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path("/tmp"),
    Path("/private/tmp"),
    Path("docs/experiments/actionable-regime-confidence/runs"),
]

NAME_TERMS = [
    "oystacher",
    "cme",
    "cboe",
    "cfe",
    "market_depth",
    "market-depth",
    "market by order",
    "mbo",
    "normal_control",
    "normal-control",
    "owner_export",
    "owner-export",
    "verifier",
    "spoof",
    "layer",
    "flip",
]

CONTENT_TERMS = [
    "oystacher",
    "spoof",
    "layering",
    "cme",
    "cboe",
    "cfe",
    "market depth",
    "market by order",
    "normal control",
    "non-manipulation",
    "order lifecycle",
    "ticket",
    "license",
    "export",
]

TEXT_EXTENSIONS = {
    ".csv",
    ".json",
    ".jsonl",
    ".md",
    ".txt",
    ".tsv",
    ".eml",
    ".log",
    ".out",
    ".stderr",
    ".stdout",
    ".cmd",
    ".html",
    ".xml",
}


def run_cmd(key: str, command: list[str]) -> dict[str, object]:
    stdout_path = OUT / f"{key}.stdout"
    stderr_path = OUT / f"{key}.stderr"
    cmd_path = OUT / f"{key}.cmd"
    exit_path = OUT / f"{key}.exit"
    cmd_path.write_text(" ".join(command) + "\n", encoding="utf-8")
    proc = subprocess.run(command, text=True, capture_output=True, check=False)
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    return {
        "key": key,
        "command": command,
        "exit_code": proc.returncode,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "stdout_bytes": stdout_path.stat().st_size,
        "stderr_bytes": stderr_path.stat().st_size,
    }


def normalized(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower())


def name_matches(path: Path) -> list[str]:
    text = normalized(path.name)
    hits = []
    for term in NAME_TERMS:
        term_norm = normalized(term)
        if term_norm and term_norm in text:
            hits.append(term)
    return hits


def content_matches(path: Path, size: int) -> list[str]:
    if path.suffix.lower() not in TEXT_EXTENSIONS or size > 5_000_000:
        return []
    try:
        data = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    text = normalized(data[:1_000_000])
    hits = []
    for term in CONTENT_TERMS:
        term_norm = normalized(term)
        if term_norm and term_norm in text:
            hits.append(term)
    return hits


def classify(path: Path, name_hits: list[str], content_hits: list[str]) -> str:
    lower_path = str(path).lower()
    all_hits = set(name_hits + content_hits)
    if path.suffix.lower() == ".eml" or "dispatch" in lower_path or "request" in lower_path:
        return "request_or_dispatch_draft_only"
    if {"normal control", "non-manipulation"} & all_hits and {"market depth", "market by order", "order lifecycle"} & all_hits:
        return "possible_control_file_needs_manual_review"
    if "oystacher" in all_hits and ({"spoof", "layering"} & all_hits):
        return "positive_or_case_material_needs_control_policy"
    if {"cme", "cboe", "cfe"} & all_hits and {"ticket", "license", "export"} & all_hits:
        return "possible_owner_correspondence_needs_manual_review"
    return "keyword_candidate_not_sufficient"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    PACKET.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    commands = [run_cmd("board_sha256_before", ["shasum", "-a", "256", str(BOARD)])]
    roots_before = {str(path): path.exists() for path in TARGET_ROOTS}

    rows: list[dict[str, object]] = []
    visited = 0
    max_files = 25_000
    max_candidates = 500
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        max_depth = 8 if str(root).endswith("runs") else 5
        root_parts = len(root.resolve().parts)
        for dirpath, dirnames, filenames in os.walk(root):
            current = Path(dirpath)
            depth = len(current.resolve().parts) - root_parts
            if depth >= max_depth:
                dirnames[:] = []
            dirnames[:] = [name for name in dirnames if name not in {".git", "node_modules", "target", ".venv", "__pycache__"}]
            for name in filenames:
                if visited >= max_files or len(rows) >= max_candidates:
                    break
                path = current / name
                visited += 1
                try:
                    stat = path.stat()
                except OSError:
                    continue
                n_hits = name_matches(path)
                if not n_hits:
                    continue
                c_hits = content_matches(path, stat.st_size)
                if not n_hits and not c_hits:
                    continue
                rows.append(
                    {
                        "path": str(path),
                        "size_bytes": stat.st_size,
                        "mtime_epoch": int(stat.st_mtime),
                        "extension": path.suffix.lower(),
                        "name_hits": ";".join(n_hits),
                        "content_hits": ";".join(c_hits),
                        "classification": classify(path, n_hits, c_hits),
                    }
                )
            if visited >= max_files or len(rows) >= max_candidates:
                break

    roots_after = {str(path): path.exists() for path in TARGET_ROOTS}
    usable_rows = [
        row
        for row in rows
        if row["classification"] in {"possible_control_file_needs_manual_review", "possible_owner_correspondence_needs_manual_review"}
    ]
    owner_export_rows = [
        row
        for row in rows
        if row["classification"] == "possible_control_file_needs_manual_review"
    ]

    csv_path = PACKET / "r6_local_owner_export_intake_search_candidates_v1.csv"
    fieldnames = ["path", "size_bytes", "mtime_epoch", "extension", "name_hits", "content_hits", "classification"]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "run_id": RUN_ID,
        "generated_at_epoch": int(time.time()),
        "gate_result": GATE,
        "scope": "bounded local search for existing R6 owner-export/control evidence outside the absent target root",
        "commands": commands,
        "search_roots": [str(path) for path in SEARCH_ROOTS],
        "target_roots_before": roots_before,
        "target_roots_after": roots_after,
        "counts": {
            "files_visited": visited,
            "keyword_candidates": len(rows),
            "manual_review_candidates": len(usable_rows),
            "possible_control_files": len(owner_export_rows),
        },
        "candidates_csv": str(csv_path),
        "sample_candidates": rows[:30],
        "assertions": {
            "accepted_rows_added": 0,
            "source_control_evidence_acquired": False,
            "target_root_mutated": roots_before != roots_after,
            "canonical_merge_allowed_now": False,
            "downstream_rerun_allowed_now": False,
            "strict_full_objective_achieved": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "decision": (
            "No local file was promoted into the R6 owner-export target root. Keyword hits are either "
            "existing request/dispatch/case-material artifacts or require explicit manual/source-owner "
            "approval before they can be treated as controls."
        ),
        "next_action": (
            "Use an approved operator mail path for the existing v5 .eml drafts, or place source-owner/"
            "user-approved verifier-native rows under /tmp/ict-engine-board-a-r6-owner-export-v1."
        ),
    }

    json_path = PACKET / "r6_local_owner_export_intake_search_v1.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_path = PACKET / "r6_local_owner_export_intake_search_v1.md"
    md_path.write_text(
        "\n".join(
            [
                "# R6 Local Owner Export Intake Search v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{GATE}`",
                "",
                "## Scope",
                "",
                "Bounded local search for existing CME/Cboe/CFE/Oystacher owner-export or normal-control files. This run does not send email, copy files into target roots, approve controls, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Counts",
                "",
                f"- Files visited: `{visited}`.",
                f"- Keyword candidates: `{len(rows)}`.",
                f"- Manual-review candidates: `{len(usable_rows)}`.",
                f"- Possible control files: `{len(owner_export_rows)}`.",
                "",
                "## Decision",
                "",
                "No local file was promoted into the R6 owner-export target root. Any candidate that looks relevant is only a manual-review/source-approval candidate, not accepted source/control evidence.",
                "",
                "Required roots remain absent unless the JSON says otherwise:",
                "",
                "- `/tmp/ict-engine-board-a-r6-owner-export-v1`",
                "- `/tmp/ict-engine-native-subhour-source-label-intake`",
                "- `/tmp/ict-engine-source-panel-recency-extension`",
                "",
                "Promotion remains blocked: accepted rows added `0`, source/control evidence acquired `false`, target root mutated `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.",
                "",
                "## Next",
                "",
                "Dispatch the existing v5 `.eml` drafts only through an approved operator mail path, preserving ticket/export/license/order/support identifiers in provenance; otherwise continue only after explicit source/control approval or verifier-native R6 owner-export rows with valid controls unlock a required target root.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = {
        "gate_result": GATE,
        "accepted_rows_added": 0,
        "source_control_evidence_acquired": False,
        "target_root_mutated": roots_before != roots_after,
        "canonical_merge_allowed_now": False,
        "downstream_rerun_allowed_now": False,
        "strict_full_objective_achieved": False,
        "trade_usable": False,
        "update_goal": False,
    }
    (CHECKS / "r6_local_owner_export_intake_search_v1_assertions.out").write_text(
        "\n".join(f"{key}={str(value).lower() if isinstance(value, bool) else value}" for key, value in assertions.items()) + "\n",
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
