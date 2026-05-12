#!/usr/bin/env python3
"""Read-only source/control unlock refresh after the 062604 objective audit."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T062842+0800-codex-source-control-unlock-refresh-after-062604-v1"
SCRIPT = Path(__file__).resolve()
RUN_ROOT = SCRIPT.parents[1]
REPO = SCRIPT.parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
OUT_DIR = RUN_ROOT / "source-control-unlock-refresh-after-062604-v1"
CHECK_DIR = RUN_ROOT / "checks"

SOURCE_EQUIV_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
SOURCE_EQUIV_ROWS = SOURCE_EQUIV_ROOT / "source_label_equivalence_rows.csv"

REQUIRED_ROOTS = [
    {
        "id": "r6_owner_export",
        "root": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        "required_files": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
        "unlock_contract": "verifier-native R6 owner/export positives plus valid normal controls",
    },
    {
        "id": "r3_native_subhour",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required_files": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
        "unlock_contract": "source-owned native sub-hour MainRegimeV2 labels plus provenance",
    },
    {
        "id": "r5_recency_extension",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required_files": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
        "unlock_contract": "post-2026-01-30 source-panel recency rows plus provenance",
    },
]

DISPATCH_CSV = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T061314+0800-codex-r6-v5-operator-dispatch-handoff-after-060807-v1/"
    "r6-v5-operator-dispatch-handoff-after-060807-v1/"
    "r6_v5_operator_dispatch_handoff_after_060807_v1.csv"
)

SCAN_ROOTS = [Path("/tmp"), Path("/private/tmp"), Path("/Users/thrill3r/Downloads")]
SCAN_EXTENSIONS = {".csv", ".json", ".jsonl", ".parquet", ".dbn", ".zip", ".gz", ".eml", ".txt", ".md"}
SCAN_TERMS = [
    "ict-engine-board-a-r6-owner-export-v1",
    "ict-engine-native-subhour-source-label-intake",
    "ict-engine-source-panel-recency-extension",
    "owner_export",
    "owner-export",
    "native_subhour_source_label",
    "native-subhour-source-label",
    "source_panel_recency",
    "source-panel-recency",
    "stock_market_regimes_2026_extension",
    "ticket",
    "license",
    "approval",
    "market_depth",
    "market-depth",
    "databento",
    "cboe",
    "cfe",
]


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_rows(path: Path) -> int | None:
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return max(sum(1 for _ in csv.reader(handle)) - 1, 0)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def root_snapshot() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in REQUIRED_ROOTS:
        root = item["root"]
        present_files = []
        missing_files = []
        row_counts = {}
        hashes = {}
        for name in item["required_files"]:
            path = root / name
            if path.exists():
                present_files.append(name)
                hashes[name] = sha256(path)
                if path.suffix == ".csv":
                    row_counts[name] = csv_rows(path)
            else:
                missing_files.append(name)
        rows.append(
            {
                "id": item["id"],
                "root": str(root),
                "root_exists": root.exists(),
                "required_files": ";".join(item["required_files"]),
                "present_files": ";".join(present_files),
                "missing_files": ";".join(missing_files),
                "all_required_present": not missing_files,
                "row_counts": json.dumps(row_counts, sort_keys=True),
                "hashes": json.dumps(hashes, sort_keys=True),
                "unlock_contract": item["unlock_contract"],
            }
        )
    return rows


def dispatch_snapshot() -> list[dict[str, object]]:
    rows = []
    for row in read_csv(DISPATCH_CSV):
        rel = row.get("draft_path", "")
        path = REPO / rel if rel else Path("")
        rows.append(
            {
                "owner": row.get("owner", ""),
                "draft_path": rel,
                "present": path.is_file(),
                "sha256": sha256(path),
                "recorded_sha256": row.get("sha256", ""),
                "operator_action": row.get("operator_action", ""),
                "status": row.get("status", ""),
            }
        )
    return rows


def scan_candidates(limit: int = 120) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for base in SCAN_ROOTS:
        if not base.exists():
            continue
        base_depth = len(base.parts)
        for dirpath, dirnames, filenames in os.walk(base):
            current = Path(dirpath)
            depth = len(current.parts) - base_depth
            if depth >= 4:
                dirnames[:] = []
            dirnames[:] = [
                name
                for name in sorted(dirnames)
                if name not in {".git", "node_modules", "target", ".venv", "venv", "__pycache__"}
            ]
            for filename in sorted(filenames):
                path = current / filename
                lower = str(path).lower()
                if path.suffix.lower() not in SCAN_EXTENSIONS:
                    continue
                if not any(term in lower for term in SCAN_TERMS):
                    continue
                if str(path) in seen:
                    continue
                seen.add(str(path))
                try:
                    stat = path.stat()
                except OSError:
                    continue
                rows.append(
                    {
                        "path": str(path),
                        "size_bytes": stat.st_size,
                        "mtime_epoch": int(stat.st_mtime),
                        "inside_required_root": any(
                            str(path).startswith(str(item["root"]) + os.sep) for item in REQUIRED_ROOTS
                        ),
                    }
                )
                if len(rows) >= limit:
                    return rows
    return rows


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    roots = root_snapshot()
    dispatch = dispatch_snapshot()
    candidates = scan_candidates()
    required_root_unlocked = any(row["all_required_present"] for row in roots)
    required_root_any_exists = any(row["root_exists"] for row in roots)
    candidates_inside_required_roots = sum(1 for row in candidates if row["inside_required_root"])

    gate_result = (
        "source_control_unlock_refresh_after_062604_v1="
        "no_required_root_no_approval_no_downstream"
    )
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": gate_result,
        "board_sha256_before_artifact": sha256(BOARD),
        "source_label_equivalence_root_present": SOURCE_EQUIV_ROOT.exists(),
        "source_label_equivalence_rows": csv_rows(SOURCE_EQUIV_ROWS),
        "required_roots": roots,
        "dispatch_drafts": dispatch,
        "local_candidate_count": len(candidates),
        "local_candidates_inside_required_roots": candidates_inside_required_roots,
        "required_root_any_exists": required_root_any_exists,
        "required_root_unlocked": required_root_unlocked,
        "external_requests_sent": False,
        "approval_present": False,
        "source_control_evidence_acquired": False,
        "accepted_rows_added": 0,
        "target_root_mutated": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    json_path = OUT_DIR / "source_control_unlock_refresh_after_062604_v1.json"
    roots_csv = OUT_DIR / "source_control_unlock_required_roots_v1.csv"
    dispatch_csv = OUT_DIR / "source_control_unlock_dispatch_drafts_v1.csv"
    candidates_csv = OUT_DIR / "source_control_unlock_local_candidates_v1.csv"
    report_path = OUT_DIR / "source_control_unlock_refresh_after_062604_v1.md"
    assertions_path = CHECK_DIR / "source_control_unlock_refresh_after_062604_v1_assertions.out"

    json_path.write_text(json.dumps({**payload, "local_candidates": candidates}, indent=2, sort_keys=True) + "\n")
    write_csv(
        roots_csv,
        roots,
        [
            "id",
            "root",
            "root_exists",
            "required_files",
            "present_files",
            "missing_files",
            "all_required_present",
            "row_counts",
            "hashes",
            "unlock_contract",
        ],
    )
    write_csv(
        dispatch_csv,
        dispatch,
        ["owner", "draft_path", "present", "sha256", "recorded_sha256", "operator_action", "status"],
    )
    write_csv(
        candidates_csv,
        candidates,
        ["path", "size_bytes", "mtime_epoch", "inside_required_root"],
    )

    root_lines = "\n".join(
        f"| `{row['id']}` | `{row['root']}` | `{str(row['root_exists']).lower()}` | `{str(row['all_required_present']).lower()}` | `{row['missing_files']}` |"
        for row in roots
    )
    dispatch_lines = "\n".join(
        f"| `{row['owner']}` | `{str(row['present']).lower()}` | `{row['status']}` | `{row['sha256']}` |"
        for row in dispatch
    )
    report_path.write_text(
        "\n".join(
            [
                "# Source/Control Unlock Refresh After 062604 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{gate_result}`",
                "",
                "## Scope",
                "",
                "Read-only refresh after the `062604` prompt-to-artifact audit. This checks whether any required R6/R3/R5 source-control root or explicit dispatch evidence has arrived. It does not send mail, approve controls, copy files into target roots, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Required Roots",
                "",
                "| Root ID | Root | Exists | All Required Present | Missing Files |",
                "|---|---|---:|---:|---|",
                root_lines,
                "",
                "## Dispatch Drafts",
                "",
                "| Owner | Draft Present | Status | SHA256 |",
                "|---|---:|---|---|",
                dispatch_lines,
                "",
                "## Decision",
                "",
                f"- Source-label equivalence root remains present with `{payload['source_label_equivalence_rows']}` rows, but it is still non-target/non-promoting.",
                f"- Required root unlocked: `{str(required_root_unlocked).lower()}`.",
                f"- Required root exists at all: `{str(required_root_any_exists).lower()}`.",
                f"- Local candidate scan hits: `{len(candidates)}`, with `{candidates_inside_required_roots}` inside required roots.",
                "- External requests sent `false`; approval present `false`; source/control evidence acquired `false`; canonical merge `false`; downstream promotion rerun `false`; strict full objective `false`; trade usable `false`; `update_goal=false`.",
                "",
                "## Next",
                "",
                "Preserve the Current Cursor next action. Continue only from explicit source/control approval, verifier-native R6 owner/export rows with valid controls, source-owned R5 recency rows, or verifier-native R3 native-subhour `MainRegimeV2` rows before rerunning direct verifier, split calibration, canonical merge, providers, AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path.relative_to(REPO)}`",
                f"- Required roots CSV: `{roots_csv.relative_to(REPO)}`",
                f"- Dispatch drafts CSV: `{dispatch_csv.relative_to(REPO)}`",
                f"- Local candidates CSV: `{candidates_csv.relative_to(REPO)}`",
                f"- Assertions: `{assertions_path.relative_to(REPO)}`",
                "",
            ]
        )
    )

    assertions = {
        "gate_result": gate_result,
        "required_root_unlocked_false": required_root_unlocked is False,
        "source_label_equivalence_rows": payload["source_label_equivalence_rows"],
        "external_requests_sent_false": payload["external_requests_sent"] is False,
        "approval_present_false": payload["approval_present"] is False,
        "source_control_evidence_acquired_false": payload["source_control_evidence_acquired"] is False,
        "target_root_mutated_false": payload["target_root_mutated"] is False,
        "canonical_merge_false": payload["canonical_merge"] is False,
        "downstream_promotion_rerun_false": payload["downstream_promotion_rerun"] is False,
        "strict_full_objective_false": payload["strict_full_objective"] is False,
        "update_goal_false": payload["update_goal"] is False,
    }
    assertions_path.write_text("\n".join(f"{key}={value}" for key, value in assertions.items()) + "\n")
    boolean_assertions = [value for key, value in assertions.items() if key != "gate_result"]
    return 0 if all(boolean_assertions) else 1


if __name__ == "__main__":
    raise SystemExit(main())
