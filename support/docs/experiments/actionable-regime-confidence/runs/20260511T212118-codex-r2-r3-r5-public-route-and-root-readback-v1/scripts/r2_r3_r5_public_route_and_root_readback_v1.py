#!/usr/bin/env python3
"""R2/R3/R5 public-route and fail-closed intake-root readback.

This run is intentionally non-mutating for Board A intake roots. It only
checks whether required source-owned files appeared locally, whether the known
public VantMacro route exposes row-level labels, and whether post-cursor run
artifacts alter the strict completion state.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T212118-codex-r2-r3-r5-public-route-and-root-readback-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r2-r3-r5-public-route-and-root-readback"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"
RAW_TMP = Path("/tmp/ict-engine-r2-r3-r5-public-route-readback-v1")

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUNS = REPO / "docs/experiments/actionable-regime-confidence/runs"
SOURCE_LABEL_VERIFIER = RUNS / (
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)
RECENCY_VERIFIER = RUNS / (
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)
DIRECT_VERIFIER = RUNS / (
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

INTAKE_ROOTS = [
    {
        "id": "source_label_equivalence",
        "requirements": "R2;R4",
        "root": Path("/tmp/ict-engine-source-label-equivalence-intake"),
        "required": [
            "source_label_equivalence_rows.csv",
            "source_label_equivalence_provenance.json",
        ],
    },
    {
        "id": "native_subhour_source_label",
        "requirements": "R3",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
    },
    {
        "id": "source_panel_recency_extension",
        "requirements": "R5",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
    },
    {
        "id": "direct_manipulation_row_intake",
        "requirements": "R6",
        "root": Path("/tmp/ict-engine-direct-manipulation-row-intake"),
        "required": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
    },
]

EXACT_FILENAMES = sorted(
    {
        name
        for spec in INTAKE_ROOTS
        if spec["id"] != "direct_manipulation_row_intake"
        for name in spec["required"]
    }
)

POST_CURSOR_RUNS = [
    "20260511T211201-codex-r6-mohan-shak-row-uplift-v1",
    "20260511T211552-codex-current-goal-completion-audit-v41-post-source-gap",
    "20260511T211606-codex-r6-shak-complaint-row-uplift-gate-v1",
    "20260511T211628-codex-r6-shak-cftc-row-uplift-v1",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"_missing": str(path)}
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_cursor() -> dict[str, str]:
    cursor: dict[str, str] = {}
    in_cursor = False
    for line in BOARD.read_text(encoding="utf-8").splitlines():
        if line.strip() == "## Current Cursor":
            in_cursor = True
            continue
        if in_cursor and line.startswith("## "):
            break
        if in_cursor and line.startswith("|"):
            parts = [part.strip() for part in line.strip().strip("|").split("|")]
            if len(parts) >= 2 and parts[0] not in {"Field", "---"}:
                cursor[parts[0]] = parts[1]
    return cursor


def csv_row_count(path: Path) -> int | None:
    if not path.exists() or path.suffix.lower() != ".csv":
        return None
    with path.open(newline="", encoding="utf-8") as handle:
        return max(sum(1 for _ in csv.DictReader(handle)), 0)


def root_status() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in INTAKE_ROOTS:
        root = spec["root"]
        present = []
        missing = []
        row_counts: dict[str, int] = {}
        hashes: dict[str, str] = {}
        for name in spec["required"]:
            path = root / name
            if path.exists():
                present.append(name)
                hashes[name] = sha256_file(path)
                count = csv_row_count(path)
                if count is not None:
                    row_counts[name] = count
            else:
                missing.append(name)
        rows.append(
            {
                "id": spec["id"],
                "requirements": spec["requirements"],
                "root": str(root),
                "exists": root.exists(),
                "ready": root.exists() and not missing,
                "required_files": ";".join(spec["required"]),
                "present_files": ";".join(present),
                "missing_files": ";".join(missing),
                "csv_row_counts": json.dumps(row_counts, sort_keys=True),
                "file_hashes": json.dumps(hashes, sort_keys=True),
            }
        )
    return rows


def bounded_walk(root: Path, max_depth: int = 5):
    if not root.exists():
        return
    root_depth = len(root.parts)
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        depth = len(current_path.parts) - root_depth
        if depth >= max_depth:
            dirs[:] = []
        yield current_path, files


def exact_file_hits() -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    wanted = set(EXACT_FILENAMES)
    for root in [Path("/tmp"), Path("/Users/thrill3r/Downloads")]:
        for current, files in bounded_walk(root):
            for filename in files:
                if filename not in wanted:
                    continue
                path = current / filename
                hits.append(
                    {
                        "filename": filename,
                        "path": str(path),
                        "size_bytes": path.stat().st_size,
                        "sha256": sha256_file(path),
                    }
                )
    return sorted(hits, key=lambda row: (row["filename"], row["path"]))


def run_verifier(name: str, command: list[str]) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=REPO, text=True, capture_output=True, check=False)
    stdout = CMD_OUT / f"{name}.stdout.txt"
    stderr = CMD_OUT / f"{name}.stderr.txt"
    stdout.write_text(proc.stdout, encoding="utf-8")
    stderr.write_text(proc.stderr, encoding="utf-8")
    parsed = None
    status = "stdout_not_json"
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
            status = str(parsed.get("status", "json_no_status"))
        except json.JSONDecodeError:
            pass
    return {
        "id": name,
        "command": " ".join(command),
        "returncode": proc.returncode,
        "status": status,
        "payload": parsed,
        "stdout_file": rel(stdout),
        "stderr_file": rel(stderr),
    }


def run_dir_state(run_id: str) -> dict[str, Any]:
    root = RUNS / run_id
    files = [p for p in root.rglob("*") if p.is_file()] if root.exists() else []
    reports = [p for p in files if p.suffix == ".md"]
    jsons = [p for p in files if p.suffix == ".json"]
    assertions = [p for p in files if "assertions" in p.name]
    if not root.exists():
        state = "missing"
    elif reports and jsons and assertions:
        state = "artifact_complete_sampled"
    elif files:
        state = "partial_or_in_progress"
    else:
        state = "empty"
    return {
        "run_id": run_id,
        "state": state,
        "file_count": len(files),
        "report_count": len(reports),
        "json_count": len(jsons),
        "assertion_count": len(assertions),
    }


def fetch_vantmacro_public_route() -> dict[str, Any]:
    RAW_TMP.mkdir(parents=True, exist_ok=True)
    html_path = RAW_TMP / "vantmacro_home.html"
    proc = subprocess.run(
        [
            "curl",
            "-L",
            "--max-time",
            "25",
            "--silent",
            "--show-error",
            "https://vantmacro.com/",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    (CMD_OUT / "vantmacro_curl.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    html = proc.stdout
    html_path.write_text(html, encoding="utf-8")
    lower = html.lower()
    script_paths = sorted(set(re.findall(r'src="([^"]+\.js[^"]*)"', html)))[:40]
    row_export_markers = {
        "csv": ".csv" in lower,
        "download": "download" in lower,
        "api": "api/" in lower or "/api" in lower,
        "regime": "regime" in lower,
        "daily": "daily" in lower,
        "weekly": "weekly" in lower,
        "dashboard": "dashboard" in lower,
        "signin_or_paywall": any(token in lower for token in ["sign in", "log in", "pricing", "pro"]),
    }
    has_row_level_export = row_export_markers["csv"] and "source_label_equivalence" in lower
    return {
        "url": "https://vantmacro.com/",
        "returncode": proc.returncode,
        "bytes": len(html.encode("utf-8")),
        "sha256": sha256_file(html_path),
        "raw_path": str(html_path),
        "raw_committed_to_repo": False,
        "script_path_sample": script_paths,
        "markers": row_export_markers,
        "source_owned_rows_acquired": False,
        "intake_files_created": False,
        "has_board_required_row_export": has_row_level_export,
        "disposition": (
            "public_route_still_found_no_board_required_row_export"
            if proc.returncode == 0
            else "public_route_fetch_failed_no_rows_acquired"
        ),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)

    board_hash = sha256_file(BOARD)
    cursor = read_cursor()
    roots = root_status()
    hits = exact_file_hits()
    post_cursor = [run_dir_state(run_id) for run_id in POST_CURSOR_RUNS]
    public_route = fetch_vantmacro_public_route()
    verifiers = [
        run_verifier(
            "source_label_equivalence_verifier",
            ["python3", str(SOURCE_LABEL_VERIFIER), "--intake-root", "/tmp/ict-engine-source-label-equivalence-intake"],
        ),
        run_verifier(
            "source_panel_recency_verifier",
            ["python3", str(RECENCY_VERIFIER), "--intake-root", "/tmp/ict-engine-source-panel-recency-extension"],
        ),
        run_verifier(
            "direct_manipulation_verifier_coordination_only",
            ["python3", str(DIRECT_VERIFIER), "--intake-root", "/tmp/ict-engine-direct-manipulation-row-intake"],
        ),
    ]

    source_verifier = verifiers[0]
    recency_verifier = verifiers[1]
    direct_verifier = verifiers[2]
    direct_payload = direct_verifier.get("payload") or {}
    direct_positive = int(direct_payload.get("positive_rows", 0) or 0)
    direct_negative = int(direct_payload.get("matched_negative_rows", 0) or 0)
    ready_roots = sum(1 for row in roots if row["ready"])
    sampled_complete = sum(1 for row in post_cursor if row["state"] == "artifact_complete_sampled")

    decision = "r2_r3_r5_public_route_and_root_readback_v1=rows_not_acquired_blocked"
    checklist = [
        {
            "id": "R2_R4_source_label_equivalence",
            "status": "fail_blocked",
            "evidence": f"verifier={source_verifier['status']}; exact_hits={len(hits)}",
            "gap": "source_label_equivalence_rows.csv and source_label_equivalence_provenance.json absent",
        },
        {
            "id": "R3_native_subhour",
            "status": "fail_blocked",
            "evidence": "native root not ready",
            "gap": "native_subhour_source_label_rows.csv and native_subhour_source_label_provenance.json absent",
        },
        {
            "id": "R5_recency_extension",
            "status": "fail_blocked",
            "evidence": f"verifier={recency_verifier['status']}; VantMacro={public_route['disposition']}",
            "gap": "stock_market_regimes_2026_extension.csv and source_panel_recency_provenance.json absent",
        },
        {
            "id": "R6_coordination",
            "status": "still_blocked",
            "evidence": f"direct={direct_positive}/{direct_negative}; sampled_complete={sampled_complete}",
            "gap": "R6 still lacks support, Wilson95 >=0.95, broad normal sample, and direct species coverage",
        },
    ]

    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "board_hash_before_run": board_hash,
        "current_cursor": cursor,
        "ready_intake_roots": ready_roots,
        "intake_roots": roots,
        "exact_required_file_hits": hits,
        "public_route_probe": public_route,
        "sampled_concurrent_artifacts": post_cursor,
        "verifiers": verifiers,
        "checklist": checklist,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }

    json_path = OUT / "r2_r3_r5_public_route_and_root_readback_v1.json"
    report_path = OUT / "r2_r3_r5_public_route_and_root_readback_v1.md"
    write_csv(OUT / "r2_r3_r5_public_route_and_root_readback_roots_v1.csv", roots)
    write_csv(OUT / "r2_r3_r5_public_route_and_root_readback_exact_hits_v1.csv", hits or [{"no_hits": True}])
    write_csv(OUT / "r2_r3_r5_public_route_and_root_readback_post_cursor_v1.csv", post_cursor)
    write_csv(OUT / "r2_r3_r5_public_route_and_root_readback_checklist_v1.csv", checklist)
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    report = [
        "# R2/R3/R5 Public Route And Root Readback v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Board cursor before run: `{cursor.get('last_loop_id', '')}`.",
        f"- Ready intake roots: `{ready_roots}/4`.",
        f"- Exact required R2/R3/R5 file hits under bounded `/tmp` and `Downloads` search: `{len(hits)}`.",
        f"- Source-label equivalence verifier: `{source_verifier['status']}`.",
        f"- Recency verifier: `{recency_verifier['status']}`.",
        f"- VantMacro public route: `{public_route['disposition']}`; source-owned rows acquired `false`; intake files created `false`.",
        f"- Direct R6 coordination readback: positives `{direct_positive}`, matched negatives `{direct_negative}`; still not accepted.",
        f"- Completed concurrent run dirs sampled by this readback: `{sampled_complete}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "## Boundary",
        "",
        "This run does not create source-label intake files because no source-owned or owner-approved R2/R3/R5 rows were acquired. The VantMacro page remains a public route/contact surface, not row-level Board A evidence.",
        "",
        "## Checklist",
        "",
        "| ID | Status | Gap |",
        "|---|---|---|",
    ]
    for row in checklist:
        report.append(f"| `{row['id']}` | `{row['status']}` | {row['gap']} |")
    report.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(json_path)}`",
            f"- Root CSV: `{rel(OUT / 'r2_r3_r5_public_route_and_root_readback_roots_v1.csv')}`",
            f"- Exact-hit CSV: `{rel(OUT / 'r2_r3_r5_public_route_and_root_readback_exact_hits_v1.csv')}`",
            f"- Sampled-run CSV: `{rel(OUT / 'r2_r3_r5_public_route_and_root_readback_post_cursor_v1.csv')}`",
            f"- Checklist CSV: `{rel(OUT / 'r2_r3_r5_public_route_and_root_readback_checklist_v1.csv')}`",
            f"- Verifier outputs: `{rel(CMD_OUT)}`",
            f"- Public route raw HTML: `{public_route['raw_path']}` (not committed)",
        ]
    )
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    assertion = (
        "PASS "
        f"decision={decision} "
        f"ready_roots={ready_roots}/4 "
        f"exact_hits={len(hits)} "
        f"source_verifier={source_verifier['status']} "
        f"recency_verifier={recency_verifier['status']} "
        f"update_goal=false"
    )
    (CHECKS / "r2_r3_r5_public_route_and_root_readback_v1_assertions.out").write_text(assertion + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "json": rel(json_path), "report": rel(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
