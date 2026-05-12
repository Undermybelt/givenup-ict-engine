#!/usr/bin/env python3
"""Rescan exact Board A intake filenames without modifying intake roots."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T193804-codex-board-a-intake-file-presence-rescan-v1"
)
OUT_DIR = RUN_ROOT / "intake-file-presence-rescan"
CHECK_DIR = RUN_ROOT / "checks"

SEARCH_ROOTS = [Path("/tmp"), Path("/Users/thrill3r/Downloads")]
MAX_DEPTH = 6

REQUIRED = [
    {
        "package": "external_bundle_price_root_equivalence",
        "canonical_path": "/tmp/ict-engine-board-a-external-intake-bundle-v1/price_root_equivalence_rows.csv",
        "filename": "price_root_equivalence_rows.csv",
    },
    {
        "package": "external_bundle_price_root_equivalence",
        "canonical_path": "/tmp/ict-engine-board-a-external-intake-bundle-v1/price_root_equivalence_provenance.json",
        "filename": "price_root_equivalence_provenance.json",
    },
    {
        "package": "external_bundle_source_panel_recency_extension",
        "canonical_path": "/tmp/ict-engine-board-a-external-intake-bundle-v1/source_panel_recency_extension_rows.csv",
        "filename": "source_panel_recency_extension_rows.csv",
    },
    {
        "package": "external_bundle_source_panel_recency_extension",
        "canonical_path": "/tmp/ict-engine-board-a-external-intake-bundle-v1/source_panel_recency_extension_provenance.json",
        "filename": "source_panel_recency_extension_provenance.json",
    },
    {
        "package": "external_bundle_direct_manipulation_species",
        "canonical_path": "/tmp/ict-engine-board-a-external-intake-bundle-v1/direct_manipulation_positive_rows.csv",
        "filename": "direct_manipulation_positive_rows.csv",
    },
    {
        "package": "external_bundle_direct_manipulation_species",
        "canonical_path": "/tmp/ict-engine-board-a-external-intake-bundle-v1/direct_manipulation_matched_controls.csv",
        "filename": "direct_manipulation_matched_controls.csv",
    },
    {
        "package": "external_bundle_direct_manipulation_species",
        "canonical_path": "/tmp/ict-engine-board-a-external-intake-bundle-v1/direct_manipulation_provenance.json",
        "filename": "direct_manipulation_provenance.json",
    },
    {
        "package": "strict_1h_source_label_equivalence",
        "canonical_path": "/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_rows.csv",
        "filename": "source_label_equivalence_rows.csv",
    },
    {
        "package": "strict_1h_source_label_equivalence",
        "canonical_path": "/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_provenance.json",
        "filename": "source_label_equivalence_provenance.json",
    },
    {
        "package": "direct_manipulation_row_intake",
        "canonical_path": "/tmp/ict-engine-direct-manipulation-row-intake/positive_spoofing_layering_rows.csv",
        "filename": "positive_spoofing_layering_rows.csv",
    },
    {
        "package": "direct_manipulation_row_intake",
        "canonical_path": "/tmp/ict-engine-direct-manipulation-row-intake/matched_negative_normal_activity_rows.csv",
        "filename": "matched_negative_normal_activity_rows.csv",
    },
    {
        "package": "direct_manipulation_row_intake",
        "canonical_path": "/tmp/ict-engine-direct-manipulation-row-intake/provenance_manifest.json",
        "filename": "provenance_manifest.json",
    },
]


def depth(root: Path, path: Path) -> int:
    try:
        return len(path.relative_to(root).parts)
    except ValueError:
        return 0


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_candidate_paths() -> list[Path]:
    names = {item["filename"] for item in REQUIRED}
    found: list[Path] = []
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for cur, dirs, files in os.walk(root):
            cur_path = Path(cur)
            if depth(root, cur_path) >= MAX_DEPTH:
                dirs[:] = []
            for file_name in files:
                if file_name in names:
                    found.append(cur_path / file_name)
    return sorted(set(found))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    scan_started_at = datetime.now(timezone.utc).isoformat()
    candidate_paths = iter_candidate_paths()

    canonical_rows = []
    for item in REQUIRED:
        canonical = Path(item["canonical_path"])
        canonical_rows.append(
            {
                **item,
                "exists": canonical.exists(),
                "size_bytes": canonical.stat().st_size if canonical.exists() else 0,
                "sha256": sha256_file(canonical) if canonical.exists() and canonical.is_file() else "",
            }
        )

    candidate_rows = []
    required_by_name = {}
    for item in REQUIRED:
        required_by_name.setdefault(item["filename"], []).append(item["canonical_path"])
    for candidate in candidate_paths:
        is_canonical = any(candidate == Path(item["canonical_path"]) for item in REQUIRED)
        candidate_rows.append(
            {
                "path": str(candidate),
                "filename": candidate.name,
                "size_bytes": candidate.stat().st_size if candidate.exists() else 0,
                "sha256": sha256_file(candidate) if candidate.exists() and candidate.is_file() else "",
                "matches_canonical_path": is_canonical,
                "canonical_paths_for_name": "|".join(required_by_name.get(candidate.name, [])),
            }
        )

    required_present = sum(1 for row in canonical_rows if row["exists"])
    exact_filename_candidates = len(candidate_rows)
    complete_packages = sorted(
        {
            row["package"]
            for row in canonical_rows
            if all(
                other["exists"]
                for other in canonical_rows
                if other["package"] == row["package"]
            )
        }
    )
    incomplete_packages = sorted({row["package"] for row in canonical_rows} - set(complete_packages))

    decision = "board_a_intake_file_presence_rescan_v1=no_required_intake_files_present"
    if required_present:
        decision = "board_a_intake_file_presence_rescan_v1=partial_required_intake_files_present_fail_closed"
    if len(complete_packages) == len({row["package"] for row in canonical_rows}):
        decision = "board_a_intake_file_presence_rescan_v1=all_required_intake_files_present_needs_verifier"

    summary = {
        "scan_started_at": scan_started_at,
        "search_roots": [str(root) for root in SEARCH_ROOTS],
        "max_depth": MAX_DEPTH,
        "required_file_count": len(REQUIRED),
        "required_present_count": required_present,
        "required_missing_count": len(REQUIRED) - required_present,
        "exact_filename_candidate_count": exact_filename_candidates,
        "complete_packages": complete_packages,
        "incomplete_packages": incomplete_packages,
        "decision": decision,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "notes": [
            "This is a presence rescan only and does not modify intake roots.",
            "Provider candles, generated labels, and projected rows are not promoted.",
            "Unregistered concurrent v23 run directories are not edited or registered here.",
        ],
    }

    with (OUT_DIR / "board_a_intake_file_presence_rescan_v1_required_files.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(canonical_rows[0].keys()))
        writer.writeheader()
        writer.writerows(canonical_rows)

    with (OUT_DIR / "board_a_intake_file_presence_rescan_v1_candidates.csv").open("w", newline="") as fh:
        fieldnames = [
            "path",
            "filename",
            "size_bytes",
            "sha256",
            "matches_canonical_path",
            "canonical_paths_for_name",
        ]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(candidate_rows)

    json_path = OUT_DIR / "board_a_intake_file_presence_rescan_v1.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    report = [
        "# Board A Intake File Presence Rescan v1",
        "",
        f"- Decision: `{decision}`",
        f"- Search roots: `{', '.join(str(root) for root in SEARCH_ROOTS)}`",
        f"- Max depth: `{MAX_DEPTH}`",
        f"- Required files present: `{required_present}/{len(REQUIRED)}`",
        f"- Exact filename candidates found: `{exact_filename_candidates}`",
        f"- Complete intake packages: `{len(complete_packages)}`",
        f"- Incomplete intake packages: `{len(incomplete_packages)}`",
        "- Accepted rows added: `0`",
        "- New confidence gate: `false`",
        "- Strict full objective achieved: `false`; `update_goal=false`",
        "",
        "This artifact is a readback only. It does not create intake files, edit",
        "other run roots, or register concurrent in-progress completion audits.",
    ]
    (OUT_DIR / "board_a_intake_file_presence_rescan_v1.md").write_text("\n".join(report) + "\n")

    assertions = [
        f"decision={decision}",
        f"required_present_count={required_present}",
        f"required_missing_count={len(REQUIRED) - required_present}",
        f"exact_filename_candidate_count={exact_filename_candidates}",
        "strict_full_objective_achieved=false",
        "update_goal=false",
    ]
    (CHECK_DIR / "board_a_intake_file_presence_rescan_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
