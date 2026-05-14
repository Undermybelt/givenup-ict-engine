#!/usr/bin/env python3
"""Audit whether local verifier-native control snapshots satisfy Oystacher R6 cells."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "r6-local-control-applicability-audit"
CHECKS_DIR = RUN_ROOT / "checks"

REQUIRED_CELLS_CSV = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T003627-codex-r6-oystacher-control-contract-request-v1/"
    / "r6-oystacher-control-contract-request/"
    / "r6_oystacher_required_normal_control_cells_v1.csv"
)

BOARD_FILE = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
OWNER_EXPORT_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")

CANDIDATE_ROOTS = [
    Path("/private/tmp/ict-engine-direct-manipulation-row-intake"),
    Path("/private/tmp/ict-engine-r6-direct-intake-reconstruction-v55/intake"),
    Path("/private/tmp/20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1.staging"),
    Path("/private/tmp/ict-engine-r6-direct-intake-v56-clean-readback/intake"),
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260511T234414-codex-r6-direct-intake-reconstruction-v55/"
    / "r6-direct-intake-reconstruction/isolated-direct-intake",
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T000038-codex-r6-isolated-rehydration-split-readback-v1/"
    / "r6-isolated-rehydration-split-readback/isolated-direct-intake",
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260511T235048-codex-r6-jpmorgan-order-positive-row-candidate-screen-v1/"
    / "delta-intake",
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260511T235726-codex-r6-isolated-reconstruction-snapshot-v56/"
    / "r6-isolated-reconstruction-snapshot-v56/isolated-direct-intake",
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260511T235745-codex-r6-active-sidecar-isolated-calibration-v1/"
    / "r6-active-sidecar-isolated-calibration/isolated-direct-intake",
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T000048-codex-r6-isolated-reconstruction-verification-v57/"
    / "isolated-direct-intake",
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260511T235910-codex-r6-live-intake-rehydration-v1/"
    / "r6-live-intake-rehydration",
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1/"
    / "r6-oystacher-exhibit-a-row-materialization/isolated-oystacher-exhibit-a-intake",
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T000345-codex-r6-moncada-species-extension-calibration-v1/"
    / "r6-moncada-species-extension-calibration/isolated-direct-intake",
]

REQUIRED_FILES = [
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
]


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def compact_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def contract_family(row: dict[str, str]) -> str:
    symbol = row.get("symbol", "").lower()
    venue = row.get("venue_or_market_center", "").lower()
    if "crude" in symbol or "natural gas" in symbol:
        return "energy"
    if "copper" in symbol:
        return "metals"
    if "vix" in symbol or "volatility" in symbol:
        return "volatility_index"
    if "e-mini" in symbol or "dow" in symbol or "s&p" in symbol or "equity" in venue:
        return "equity_index"
    if "treasury" in symbol or "cbot" in venue:
        return "rates_or_treasury"
    return "unknown"


def row_bucket(row: dict[str, str], axis: str) -> str:
    if axis == "contract_family":
        return contract_family(row)
    if axis == "venue_exact":
        return row.get("venue_or_market_center", "")
    if axis == "symbol_exact":
        return row.get("symbol", "")
    if axis == "chronological_year":
        return row.get("trade_date", "")[:4]
    return ""


def is_oystacher_flip(row: dict[str, str]) -> bool:
    text = " ".join(
        [
            row.get("source_report", ""),
            row.get("source_section", ""),
            row.get("side", ""),
            row.get("activity_description", ""),
            row.get("source_row_id", ""),
        ]
    ).lower()
    return "oystacher" in text and "flip" in text


def load_required_cells() -> list[dict[str, str]]:
    rows = read_csv(REQUIRED_CELLS_CSV)
    if not rows:
        raise SystemExit(f"required cells missing or empty: {REQUIRED_CELLS_CSV}")
    return rows


def audit_root(root: Path, required_cells: list[dict[str, str]]) -> dict[str, object]:
    files = {name: root / name for name in REQUIRED_FILES}
    missing = [name for name, path in files.items() if not path.exists()]
    negative_rows = read_csv(files["matched_negative_normal_activity_rows.csv"])
    positive_rows = read_csv(files["positive_spoofing_layering_rows.csv"])
    valid_rows = [
        row
        for row in negative_rows
        if row.get("label") == "matched_negative_normal_activity" and not is_oystacher_flip(row)
    ]
    oystacher_flip_rows = [row for row in negative_rows if is_oystacher_flip(row)]

    counts = Counter()
    for row in valid_rows:
        for cell in required_cells:
            axis = cell["axis"]
            bucket = cell["bucket"]
            if row_bucket(row, axis) == bucket:
                counts[(axis, bucket)] += 1

    cells_meeting_threshold = 0
    max_required_cell_count = 0
    for cell in required_cells:
        threshold = int(cell["required_valid_normal_control_support"])
        observed = counts[(cell["axis"], cell["bucket"])]
        max_required_cell_count = max(max_required_cell_count, observed)
        if observed >= threshold:
            cells_meeting_threshold += 1

    source_reports = sorted({row.get("source_report", "") for row in valid_rows if row.get("source_report")})
    disqualifiers = []
    if missing:
        disqualifiers.append("missing_required_files")
    if not valid_rows:
        disqualifiers.append("no_valid_non_flip_control_rows")
    if cells_meeting_threshold < len(required_cells):
        disqualifiers.append("required_oystacher_cells_short")
    if oystacher_flip_rows:
        disqualifiers.append("oystacher_flip_rows_rejected_without_explicit_approval")

    return {
        "candidate_root": compact_path(root),
        "exists": root.exists(),
        "missing_files": missing,
        "positive_rows": len(positive_rows),
        "control_rows_total": len(negative_rows),
        "valid_non_flip_control_rows": len(valid_rows),
        "oystacher_flip_control_rows_rejected": len(oystacher_flip_rows),
        "negative_csv_sha256": sha256_file(files["matched_negative_normal_activity_rows.csv"]),
        "positive_csv_sha256": sha256_file(files["positive_spoofing_layering_rows.csv"]),
        "provenance_sha256": sha256_file(files["provenance_manifest.json"]),
        "source_report_count": len(source_reports),
        "source_reports_sample": source_reports[:5],
        "max_required_cell_count": max_required_cell_count,
        "required_cells_meeting_threshold": cells_meeting_threshold,
        "required_cells_total": len(required_cells),
        "canonical_merge_candidate": False,
        "disqualifiers": disqualifiers,
        "cell_counts": {f"{axis}:{bucket}": count for (axis, bucket), count in counts.items()},
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    required_cells = load_required_cells()
    board_hash = sha256_file(BOARD_FILE)
    owner_approval_files = {
        "target_root_exists": OWNER_EXPORT_ROOT.exists(),
        "validation_contract_approval_json": (OWNER_EXPORT_ROOT / "validation_contract_approval.json").exists(),
        "owner_approval_reference_md": (OWNER_EXPORT_ROOT / "owner_approval_reference.md").exists(),
        "positive_spoofing_layering_rows_csv": (OWNER_EXPORT_ROOT / "positive_spoofing_layering_rows.csv").exists(),
        "matched_negative_normal_activity_rows_csv": (
            OWNER_EXPORT_ROOT / "matched_negative_normal_activity_rows.csv"
        ).exists(),
        "provenance_manifest_json": (OWNER_EXPORT_ROOT / "provenance_manifest.json").exists(),
    }

    root_results = [audit_root(root, required_cells) for root in CANDIDATE_ROOTS]
    unique_control_sets = sorted(
        {
            result["negative_csv_sha256"]
            for result in root_results
            if result["negative_csv_sha256"] is not None
        }
    )

    cell_rows: list[dict[str, object]] = []
    for cell in required_cells:
        axis = cell["axis"]
        bucket = cell["bucket"]
        threshold = int(cell["required_valid_normal_control_support"])
        best_count = 0
        best_root = ""
        for result in root_results:
            count = int(result["cell_counts"].get(f"{axis}:{bucket}", 0))
            if count > best_count:
                best_count = count
                best_root = str(result["candidate_root"])
        cell_rows.append(
            {
                "axis": axis,
                "bucket": bucket,
                "required_valid_normal_control_support": threshold,
                "best_single_root_valid_non_flip_controls": best_count,
                "best_single_root": best_root,
                "shortfall": max(0, threshold - best_count),
                "decision": "pass" if best_count >= threshold else "short",
            }
        )

    all_cells_pass = all(row["decision"] == "pass" for row in cell_rows)
    approval_present = bool(
        owner_approval_files["validation_contract_approval_json"]
        and owner_approval_files["owner_approval_reference_md"]
    )
    verifier_native_owner_package_present = bool(
        owner_approval_files["positive_spoofing_layering_rows_csv"]
        and owner_approval_files["matched_negative_normal_activity_rows_csv"]
        and owner_approval_files["provenance_manifest_json"]
    )

    gate_result = (
        "r6_local_control_applicability_audit_v1="
        "local_candidate_controls_insufficient_no_approval_no_merge"
    )
    summary = {
        "run_id": "20260512T004014-codex-r6-local-control-applicability-audit-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_file_sha256_before_writeback": board_hash,
        "required_cell_source": compact_path(REQUIRED_CELLS_CSV),
        "candidate_roots_checked": len(root_results),
        "unique_control_csv_sets": len(unique_control_sets),
        "required_cells_total": len(required_cells),
        "required_cells_passing_best_single_root": sum(1 for row in cell_rows if row["decision"] == "pass"),
        "best_cell_count_max": max(int(row["best_single_root_valid_non_flip_controls"]) for row in cell_rows),
        "all_required_cells_pass": all_cells_pass,
        "owner_approval_present": approval_present,
        "verifier_native_owner_package_present": verifier_native_owner_package_present,
        "canonical_merge_allowed": False,
        "downstream_rerun_allowed": False,
        "accepted_rows_added": 0,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "gate_result": gate_result,
        "owner_export_root": str(OWNER_EXPORT_ROOT),
        "owner_approval_files": owner_approval_files,
        "candidate_roots": root_results,
        "required_cell_applicability": cell_rows,
    }

    json_path = OUT_DIR / "r6_local_control_applicability_audit_v1.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    write_csv(
        OUT_DIR / "r6_local_candidate_control_roots_v1.csv",
        [
            {
                "candidate_root": result["candidate_root"],
                "exists": result["exists"],
                "positive_rows": result["positive_rows"],
                "control_rows_total": result["control_rows_total"],
                "valid_non_flip_control_rows": result["valid_non_flip_control_rows"],
                "oystacher_flip_control_rows_rejected": result["oystacher_flip_control_rows_rejected"],
                "negative_csv_sha256": result["negative_csv_sha256"] or "",
                "max_required_cell_count": result["max_required_cell_count"],
                "required_cells_meeting_threshold": result["required_cells_meeting_threshold"],
                "required_cells_total": result["required_cells_total"],
                "canonical_merge_candidate": result["canonical_merge_candidate"],
                "disqualifiers": ";".join(result["disqualifiers"]),
            }
            for result in root_results
        ],
        [
            "candidate_root",
            "exists",
            "positive_rows",
            "control_rows_total",
            "valid_non_flip_control_rows",
            "oystacher_flip_control_rows_rejected",
            "negative_csv_sha256",
            "max_required_cell_count",
            "required_cells_meeting_threshold",
            "required_cells_total",
            "canonical_merge_candidate",
            "disqualifiers",
        ],
    )
    write_csv(
        OUT_DIR / "r6_oystacher_local_control_cell_applicability_v1.csv",
        cell_rows,
        [
            "axis",
            "bucket",
            "required_valid_normal_control_support",
            "best_single_root_valid_non_flip_controls",
            "best_single_root",
            "shortfall",
            "decision",
        ],
    )

    md = f"""# R6 Local Control Applicability Audit v1

- Run id: `20260512T004014-codex-r6-local-control-applicability-audit-v1`.
- Required-cell source: `{compact_path(REQUIRED_CELLS_CSV)}`.
- Candidate verifier-native roots checked: `{len(root_results)}`.
- Unique control CSV sets observed: `{len(unique_control_sets)}`.
- Required cells passing from any single local non-FLIP control root: `{summary["required_cells_passing_best_single_root"]}/{len(required_cells)}`.
- Best single-root valid non-FLIP control count for any required cell: `{summary["best_cell_count_max"]}`.
- Owner approval present under `{OWNER_EXPORT_ROOT}`: `{approval_present}`.
- Verifier-native owner package present under `{OWNER_EXPORT_ROOT}`: `{verifier_native_owner_package_present}`.
- Gate result: `{gate_result}`.
- Accepted rows added: `0`; canonical merge allowed: `false`; downstream rerun allowed: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; external requests sent: `false`; trade usable: `false`.

## Decision

The local verifier-native snapshots are not a valid substitute for the missing Oystacher normal controls. Existing non-Oystacher control rows are either duplicated historical seed/control snapshots or fail the required Oystacher exact-cell support threshold. The Oystacher Exhibit A `FLIP` rows are present in the isolated materialization, but remain rejected as normal controls unless the explicit exception is approved.

## Next

Preserve the active V66 next action: choose one approval option from the `003653` decision package, or supply source-owned normal controls for the `17` required cells from `003627`; only then copy verifier-native files under the shared lock and rerun direct verifier, split calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback while keeping R5 and R3 blocked.

## Artifacts

- JSON: `{compact_path(json_path)}`
- Candidate roots CSV: `{compact_path(OUT_DIR / "r6_local_candidate_control_roots_v1.csv")}`
- Cell applicability CSV: `{compact_path(OUT_DIR / "r6_oystacher_local_control_cell_applicability_v1.csv")}`
- Assertions: `{compact_path(CHECKS_DIR / "r6_local_control_applicability_audit_v1_assertions.out")}`
"""
    md_path = OUT_DIR / "r6_local_control_applicability_audit_v1.md"
    md_path.write_text(md, encoding="utf-8")

    assertions = [
        f"gate_result={gate_result}",
        f"candidate_roots_checked={len(root_results)}",
        f"required_cells_total={len(required_cells)}",
        f"required_cells_passing_best_single_root={summary['required_cells_passing_best_single_root']}",
        f"owner_approval_present={approval_present}",
        f"verifier_native_owner_package_present={verifier_native_owner_package_present}",
        "canonical_merge_allowed=false",
        "downstream_rerun_allowed=false",
        "shared_intake_mutated=false",
    ]
    if all_cells_pass:
        assertions.append("ASSERTION_FAILED=unexpected_all_required_cells_pass")
        (CHECKS_DIR / "r6_local_control_applicability_audit_v1_assertions.out").write_text(
            "\n".join(assertions) + "\n", encoding="utf-8"
        )
        return 1
    if approval_present or verifier_native_owner_package_present:
        assertions.append("ASSERTION_FAILED=unexpected_owner_approval_or_package_present")
        (CHECKS_DIR / "r6_local_control_applicability_audit_v1_assertions.out").write_text(
            "\n".join(assertions) + "\n", encoding="utf-8"
        )
        return 1
    assertions.append("ASSERTIONS_PASSED=true")
    (CHECKS_DIR / "r6_local_control_applicability_audit_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
