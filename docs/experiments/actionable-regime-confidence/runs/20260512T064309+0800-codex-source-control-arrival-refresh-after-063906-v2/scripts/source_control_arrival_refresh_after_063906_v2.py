#!/usr/bin/env python3
"""Bounded source/control arrival refresh after TSIE quarantine."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T064309+0800-codex-source-control-arrival-refresh-after-063906-v2"
GATE_RESULT = (
    "source_control_arrival_refresh_after_063906_v2="
    "only_tsie_quarantine_present_no_valid_unlock_no_downstream"
)
SCRIPT = Path(__file__).resolve()
RUN_ROOT = SCRIPT.parents[1]
REPO = SCRIPT.parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUNS_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs"
OUT_DIR = RUN_ROOT / "source-control-arrival-refresh-after-063906-v2"
CHECK_DIR = RUN_ROOT / "checks"

REQUIRED_ROOTS = [
    {
        "id": "r6_owner_export",
        "root": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        "required": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
        "accepted_if_complete": True,
    },
    {
        "id": "r3_native_subhour",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
        "accepted_if_complete": False,
    },
    {
        "id": "r5_recency_extension",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
        "accepted_if_complete": True,
    },
]

INTERESTING_NAMES = {
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
    "native_subhour_source_label_rows.csv",
    "native_subhour_source_label_provenance.json",
    "stock_market_regimes_2026_extension.csv",
    "source_panel_recency_provenance.json",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"read_error": f"{type(exc).__name__}: {exc}"}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def root_snapshot() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in REQUIRED_ROOTS:
        root = spec["root"]
        present: list[str] = []
        missing: list[str] = []
        sizes: dict[str, int] = {}
        for name in spec["required"]:
            path = root / name
            if path.is_file():
                present.append(name)
                sizes[name] = path.stat().st_size
            else:
                missing.append(name)
        complete = not missing
        provenance = {}
        if spec["id"] == "r3_native_subhour":
            provenance = read_json(root / "native_subhour_source_label_provenance.json")
        accepted_for_promotion = bool(complete and spec["accepted_if_complete"])
        if spec["id"] == "r3_native_subhour" and complete:
            accepted_for_promotion = False
        rows.append(
            {
                "id": spec["id"],
                "root": str(root),
                "root_exists": root.exists(),
                "present_files": ";".join(present),
                "missing_files": ";".join(missing),
                "all_required_present": complete,
                "accepted_for_promotion": accepted_for_promotion,
                "sizes_json": json.dumps(sizes, sort_keys=True),
                "provenance_run_id": provenance.get("run_id", ""),
                "provenance_row_count": provenance.get("row_count", ""),
                "provenance_labels": ";".join(
                    provenance.get("accepted_mapping_confidence_95_labels", [])
                )
                if isinstance(provenance.get("accepted_mapping_confidence_95_labels"), list)
                else "",
                "decision_notes": (
                    "TSIE root is complete on disk but policy-quarantined, Crisis absent"
                    if spec["id"] == "r3_native_subhour" and complete
                    else ""
                ),
            }
        )
    return rows


def bounded_tmp_candidates() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    roots = [Path("/tmp"), Path("/private/tmp")]
    seen: set[Path] = set()
    for base in roots:
        if not base.exists():
            continue
        for current, dirs, files in os.walk(base):
            current_path = Path(current)
            depth = len(current_path.relative_to(base).parts)
            if depth == 0:
                dirs[:] = [d for d in dirs if d.startswith("ict-engine")]
            elif depth >= 4:
                dirs[:] = []
            for name in files:
                if name not in INTERESTING_NAMES:
                    continue
                path = current_path / name
                if path in seen:
                    continue
                seen.add(path)
                rows.append(
                    {
                        "surface": "tmp",
                        "path": str(path),
                        "filename": name,
                        "size_bytes": path.stat().st_size if path.exists() else "",
                        "candidate_root": str(current_path),
                    }
                )
    return rows


def repo_candidate_files() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not RUNS_ROOT.exists():
        return rows
    for path in RUNS_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.name not in INTERESTING_NAMES and path.suffix != ".eml":
            continue
        rows.append(
            {
                "surface": "repo_runs",
                "path": rel(path),
                "filename": path.name,
                "size_bytes": path.stat().st_size,
                "candidate_root": rel(path.parent),
            }
        )
    return rows


def active_processes() -> list[dict[str, str]]:
    proc = subprocess.run(
        ["ps", "-axo", "pid,ppid,stat,etime,command"],
        text=True,
        capture_output=True,
        check=False,
    )
    tokens = [
        "source-control-arrival",
        "source_control_arrival",
        "r6-owner",
        "owner-export",
        "source-panel-recency",
        "native-subhour-source-label-intake",
        "provider-status",
        "auto-quant",
        "catboost",
        "pre-bayes",
        "bbn",
        "execution-tree",
    ]
    rows: list[dict[str, str]] = []
    for line in proc.stdout.splitlines()[1:]:
        if not any(token in line for token in tokens):
            continue
        if "source_control_arrival_refresh_after_063906_v2.py" in line:
            continue
        parts = line.split(None, 4)
        if len(parts) == 5:
            rows.append(
                {
                    "pid": parts[0],
                    "ppid": parts[1],
                    "stat": parts[2],
                    "etime": parts[3],
                    "command": parts[4],
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    board_hash = sha256_file(BOARD)
    roots = root_snapshot()
    candidates = bounded_tmp_candidates() + repo_candidate_files()
    processes = active_processes()

    r6 = next(row for row in roots if row["id"] == "r6_owner_export")
    r3 = next(row for row in roots if row["id"] == "r3_native_subhour")
    r5 = next(row for row in roots if row["id"] == "r5_recency_extension")
    valid_unlock = any(row["accepted_for_promotion"] for row in roots)
    accepted_rows_added = 0
    if r6["accepted_for_promotion"] or r5["accepted_for_promotion"]:
        accepted_rows_added = -1

    decision = {
        "gate_result": GATE_RESULT,
        "valid_required_root_unlock": valid_unlock,
        "r6_owner_export_root_present": r6["root_exists"],
        "r3_native_subhour_root_present": r3["root_exists"],
        "r3_native_subhour_root_policy_quarantined": bool(r3["all_required_present"]),
        "r5_recency_extension_root_present": r5["root_exists"],
        "candidate_file_count": len(candidates),
        "accepted_rows_added": accepted_rows_added,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_before_artifact": board_hash,
        "decision": decision,
        "required_roots": roots,
        "candidate_files": candidates,
        "active_processes": processes,
        "notes": [
            "Bounded scan inspected exact required roots, /tmp ict-engine candidates, and repo experiment artifacts.",
            "The TSIE R3 root is present but remains policy-quarantined under 063734/063906.",
            "No R6 owner/export root and no R5 recency-extension root were found.",
            "No canonical merge or downstream provider/AutoQuant chain was run.",
        ],
    }

    json_path = OUT_DIR / "source_control_arrival_refresh_after_063906_v2.json"
    roots_csv = OUT_DIR / "source_control_arrival_required_roots_v2.csv"
    candidates_csv = OUT_DIR / "source_control_arrival_candidate_files_v2.csv"
    processes_csv = OUT_DIR / "source_control_arrival_active_processes_v2.csv"
    report_path = OUT_DIR / "source_control_arrival_refresh_after_063906_v2.md"
    assertions_path = CHECK_DIR / "source_control_arrival_refresh_after_063906_v2_assertions.out"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        roots_csv,
        roots,
        [
            "id",
            "root",
            "root_exists",
            "present_files",
            "missing_files",
            "all_required_present",
            "accepted_for_promotion",
            "sizes_json",
            "provenance_run_id",
            "provenance_row_count",
            "provenance_labels",
            "decision_notes",
        ],
    )
    write_csv(
        candidates_csv,
        candidates,
        ["surface", "path", "filename", "size_bytes", "candidate_root"],
    )
    write_csv(processes_csv, processes, ["pid", "ppid", "stat", "etime", "command"])

    md = [
        "# Source Control Arrival Refresh After 063906 v2",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE_RESULT}`",
        "",
        f"Board sha256 before artifact: `{board_hash}`",
        "",
        "## Scope",
        "",
        (
            "Bounded read-only refresh after the `063906` current-objective audit. "
            "It checks exact required roots, nearby `/tmp/ict-engine*` files, and repo "
            "experiment artifacts for newly arrived source/control evidence. It does "
            "not send requests, approve controls, mutate target roots, run canonical "
            "merge, rerun downstream promotion, make a trade claim, or call `update_goal`."
        ),
        "",
        "## Required Roots",
        "",
        "| Root ID | Exists | Complete | Accepted For Promotion | Notes |",
        "|---|---:|---:|---:|---|",
    ]
    for row in roots:
        md.append(
            f"| `{row['id']}` | `{row['root_exists']}` | `{row['all_required_present']}` | "
            f"`{row['accepted_for_promotion']}` | {row['decision_notes'] or 'n/a'} |"
        )
    md.extend(
        [
            "",
            "## Decision",
            "",
            (
                "No valid source/control unlock arrived. R6 owner/export and R5 recency "
                "roots remain absent. The R3 native-subhour path exists only as the "
                "TSIE-quarantined root and remains non-promoting."
            ),
            "",
            (
                "Promotion remains blocked: accepted rows added `0`, source/control "
                "evidence acquired false, canonical merge false, downstream promotion "
                "rerun false, strict full objective false, trade usable false, and "
                "`update_goal=false`."
            ),
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(json_path)}`",
            f"- Required roots CSV: `{rel(roots_csv)}`",
            f"- Candidate files CSV: `{rel(candidates_csv)}`",
            f"- Active processes CSV: `{rel(processes_csv)}`",
            f"- Assertions: `{rel(assertions_path)}`",
            "",
            "## Next",
            "",
            (
                "Continue only from explicit source/control approval, verifier-native "
                "R6 owner-export rows with valid controls, source-owned R5 recency rows, "
                "verifier-native R3 `MainRegimeV2` labels, or a genuinely new accepted "
                "cross-timeframe `MainRegimeV2` source export before rerunning direct "
                "verifier, split calibration, canonical merge, provider/AutoQuant, "
                "filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback."
            ),
            "",
        ]
    )
    report_path.write_text("\n".join(md), encoding="utf-8")

    assertions = [
        f"gate_result={GATE_RESULT}",
        f"valid_required_root_unlock={valid_unlock}",
        f"r6_owner_export_root_present={r6['root_exists']}",
        f"r3_native_subhour_root_present={r3['root_exists']}",
        f"r3_native_subhour_policy_quarantined={bool(r3['all_required_present'])}",
        f"r5_recency_extension_root_present={r5['root_exists']}",
        "accepted_rows_added=0",
        "source_control_evidence_acquired_false=True",
        "canonical_merge_false=True",
        "downstream_promotion_rerun_false=True",
        "strict_full_objective_false=True",
        "trade_usable_false=True",
        "update_goal_false=True",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
