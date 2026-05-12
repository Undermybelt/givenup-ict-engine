#!/usr/bin/env python3
"""Bounded read-only screen for local R5 MainRegimeV2 candidates."""

from __future__ import annotations

import csv
import json
from pathlib import Path


RUN = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T091236+0800-codex-r5-mainregimev2-local-candidate-screen-after-090725-v1"
)
OUT = RUN / "r5-mainregimev2-local-candidate-screen-after-090725-v1"
CHECKS = RUN / "checks"

SCAN_ROOTS = [
    ("r5_required_tmp", Path("/tmp/ict-engine-source-panel-recency-extension")),
    ("r5_required_private_tmp", Path("/private/tmp/ict-engine-source-panel-recency-extension")),
    ("r3_native_subhour_tmp", Path("/tmp/ict-engine-native-subhour-source-label-intake")),
    ("r3_native_subhour_private_tmp", Path("/private/tmp/ict-engine-native-subhour-source-label-intake")),
    ("board_a_runs", Path("docs/experiments/actionable-regime-confidence/runs")),
]
PATTERNS = ["MainRegimeV2", "main_regime_v2", "main_regime_v2_label"]
MAX_BYTES = 256 * 1024


def read_prefix(path: Path) -> str:
    try:
        if path.name == "native_subhour_source_label_rows.csv":
            with path.open("r", encoding="utf-8", errors="ignore") as handle:
                return handle.readline()
        if path.stat().st_size > MAX_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def classify(root_name: str, path: Path, content: str) -> tuple[str, bool]:
    lower = content.lower()
    has_post_cutoff = "2026-01-30" in content or "2026-01-31" in content or "2026-02-" in content
    if root_name.startswith("r5_required"):
        return ("required_r5_root_candidate", has_post_cutoff)
    if root_name.startswith("r3_"):
        return ("r3_native_subhour_not_r5", False)
    if "current_objective" in path.name or path.suffix in {".md", ".out"}:
        return ("documentation_or_assertion_only", False)
    if "target_roots" in path.name or "readback" in path.name:
        return ("readback_metadata_only", False)
    if "main_regime_v2" in lower or "mainregimev2" in lower:
        return ("local_candidate_not_required_r5_root", has_post_cutoff)
    return ("no_candidate", False)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    root_rows = []
    candidate_rows = []
    seen_realpaths: set[str] = set()
    files_scanned = 0

    for root_name, root in SCAN_ROOTS:
        exists = root.exists()
        realpath = str(root.resolve()) if exists else ""
        duplicate_realpath = bool(realpath and realpath in seen_realpaths)
        if realpath:
            seen_realpaths.add(realpath)
        files = []
        if exists and not duplicate_realpath:
            files = [
                path
                for path in root.rglob("*")
                if path.is_file()
                and path.suffix.lower() in {".csv", ".json", ".md", ".out", ".txt"}
                and "20260512T091236+0800-codex-r5-mainregimev2-local-candidate-screen-after-090725-v1" not in str(path)
            ]
        root_rows.append(
            {
                "root_name": root_name,
                "path": str(root),
                "exists": exists,
                "realpath": realpath,
                "duplicate_realpath": duplicate_realpath,
                "file_count_scanned": len(files),
            }
        )
        for path in sorted(files):
            content = read_prefix(path)
            files_scanned += 1
            hits = [pattern for pattern in PATTERNS if pattern.lower() in content.lower()]
            if not hits:
                continue
            disposition, has_post_cutoff = classify(root_name, path, content)
            candidate_rows.append(
                {
                    "root_name": root_name,
                    "path": str(path),
                    "suffix": path.suffix,
                    "hits": "|".join(hits),
                    "disposition": disposition,
                    "post_20260130_hint": has_post_cutoff,
                    "accepted_r5_source_control_rows": 0,
                }
            )

    r5_roots_present = any(row["exists"] for row in root_rows if row["root_name"].startswith("r5_required"))
    required_r5_candidates = [row for row in candidate_rows if row["disposition"] == "required_r5_root_candidate"]
    accepted_rows = 0
    gate_result = "r5_mainregimev2_local_candidate_screen_after_090725_v1=no_required_r5_mainregimev2_source_rows"
    assertions = {
        "gate_result": gate_result,
        "files_scanned": files_scanned,
        "mainregimev2_candidate_files": len(candidate_rows),
        "r5_required_roots_present": r5_roots_present,
        "required_r5_candidate_files": len(required_r5_candidates),
        "source_owned_post_20260130_r5_mainregimev2_rows": accepted_rows,
        "accepted_rows_added": 0,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
    }

    with (OUT / "r5_mainregimev2_local_candidate_screen_after_090725_v1.json").open("w", encoding="utf-8") as handle:
        json.dump({"assertions": assertions, "roots": root_rows, "candidates": candidate_rows}, handle, indent=2, sort_keys=True)

    with (OUT / "r5_mainregimev2_target_roots_after_090725_v1.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["root_name", "path", "exists", "realpath", "duplicate_realpath", "file_count_scanned"])
        writer.writeheader()
        writer.writerows(root_rows)

    with (OUT / "r5_mainregimev2_candidate_files_after_090725_v1.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["root_name", "path", "suffix", "hits", "disposition", "post_20260130_hint", "accepted_r5_source_control_rows"],
        )
        writer.writeheader()
        writer.writerows(candidate_rows)

    md = [
        "# R5 MainRegimeV2 Local Candidate Screen After 090725 v1",
        "",
        f"Gate result: `{gate_result}`",
        "",
        "## Scope",
        "",
        "Read-only local candidate screen for source-owned post-2026-01-30 R5 `MainRegimeV2` rows. This artifact does not copy files, populate roots, approve local candidates, run selected-data AutoQuant, run verifier, Pre-Bayes, BBN, CatBoost, path-ranking, execution-tree promotion, trade claims, or `update_goal`.",
        "",
        "## Readback",
        "",
        f"- Files scanned: `{files_scanned}`.",
        f"- MainRegimeV2 candidate files: `{len(candidate_rows)}`.",
        f"- R5 required roots present: `{str(r5_roots_present).lower()}`.",
        f"- Required R5 candidate files: `{len(required_r5_candidates)}`.",
        f"- Source-owned post-2026-01-30 R5 MainRegimeV2 rows: `{accepted_rows}`.",
        "",
        "## Decision",
        "",
        "No source-owned post-2026-01-30 R5 `MainRegimeV2` rows were found in the required R5 roots. Any local MainRegimeV2 hits remain R3 native-subhour context, documentation/assertion text, or metadata, not accepted R5 source/control evidence.",
        "",
        "Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed false; `update_goal=false`.",
        "",
        "## Next",
        "",
        "Continue source/control acquisition only. Do not run selected-data AutoQuant, verifier, Pre-Bayes/BBN, CatBoost/path-ranking, execution-tree promotion, trade claims, or `update_goal` until both valid required-root unlock and selected-history gates pass.",
        "",
    ]
    (OUT / "r5_mainregimev2_local_candidate_screen_after_090725_v1.md").write_text("\n".join(md), encoding="utf-8")

    with (CHECKS / "r5_mainregimev2_local_candidate_screen_after_090725_v1_assertions.out").open("w", encoding="utf-8") as handle:
        for key, value in assertions.items():
            rendered = str(value).lower() if isinstance(value, bool) else str(value)
            handle.write(f"{key}={rendered}\n")


if __name__ == "__main__":
    main()
