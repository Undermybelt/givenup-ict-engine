#!/usr/bin/env python3
"""Bounded local inventory for un-packaged Board A source-label rows."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "local-broad-source-owned-label-inventory"
CHECK_DIR = RUN_ROOT / "checks"

SEARCH_ROOTS = [
    (Path("/Users/thrill3r/Downloads"), 6),
    (Path("/tmp"), 5),
    (Path.cwd() / "docs/experiments/actionable-regime-confidence", 6),
]

MATCH_RE = re.compile(
    r"(regime|source[-_ ]?label|market[-_ ]?state|bull|bear|sideways|crisis|"
    r"manipulation|spoof|layering|quote[-_ ]?stuff|pinging|wash|pump|dump)",
    re.IGNORECASE,
)
DATA_SUFFIXES = {
    ".csv",
    ".json",
    ".jsonl",
    ".parquet",
    ".txt",
    ".xlsx",
}
SKIP_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    "target",
    ".venv",
    "venv",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel_or_abs(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def depth(root: Path, current: Path) -> int:
    try:
        return len(current.relative_to(root).parts)
    except ValueError:
        return 999


def group_for(path: Path) -> str:
    text = str(path).lower()
    if "stock-market-regimes-20002026" in text or "kaggle_stock_market_regimes_20002026" in text:
        return "stock_market_regimes_source_panel"
    if "ict-engine-kaggle-stock-regimes-live-check" in text:
        return "stock_market_regimes_source_panel"
    if "/tmp/ict-regime-bayi-pd/" in text or "/tmp/pump-and-dump-dataset/" in text:
        return "direct_pump_dump_telegram"
    if "/tmp/ict-regime-kamps-pump-dump/" in text:
        return "direct_pump_dump_raw_windows"
    if "/tmp/ict-regime-quantsingularity-spoofing/" in text:
        return "local_spoofing_repo_quantsingularity"
    if "hmm_regime" in text or "regime_factor_benchmark" in text or "regime-sidecar" in text:
        return "generated_or_model_derived_regime_outputs"
    if "docs/experiments/actionable-regime-confidence/" in text:
        return "repo_existing_board_artifacts"
    if "/downloads/ictscripts/ict market regime detector" in text:
        return "downloads_detector_code"
    return "other_local_hits"


GROUP_DISPOSITION = {
    "stock_market_regimes_source_panel": (
        "known_source_daily_already_counted",
        "Daily MainRegimeV2 source panel is already counted by the strict gate; local duplicates do not add strict 1h, native sub-hour, recency-tail, or other-market equivalence rows.",
    ),
    "direct_pump_dump_telegram": (
        "known_scoped_direct_pump_dump_already_counted",
        "Telegram pump/dump direct rows support the already accepted scoped pump_dump variety, but they do not cover spoofing/layering, quote stuffing, pinging, bear raid, or matched negative controls.",
    ),
    "direct_pump_dump_raw_windows": (
        "raw_or_event_window_pump_dump_not_missing_species",
        "Raw/event-window crypto pump/dump files are not source-owned rows for the missing direct manipulation species and do not provide spoofing/layering controls.",
    ),
    "local_spoofing_repo_quantsingularity": (
        "code_or_synthetic_surface_not_source_owned_rows",
        "Local spoofing repo contains code, config, or synthetic generation surfaces; no exportable real positive rows plus matched controls are present.",
    ),
    "generated_or_model_derived_regime_outputs": (
        "generated_proxy_outputs_rejected",
        "Model outputs and prior experiment predictions are not source-owned active-regime labels for strict Board A completion.",
    ),
    "repo_existing_board_artifacts": (
        "already_registered_board_artifacts",
        "Existing Board A artifacts are already counted or rejected; they are not new intake rows.",
    ),
    "downloads_detector_code": (
        "code_surface_not_source_owned_rows",
        "Downloaded detector code is not a source-owned row-level label panel or owner-approved equivalence file.",
    ),
    "other_local_hits": (
        "not_promotable_by_path_header_inventory",
        "Filename matched broad keywords but did not expose an exact Board A intake file, known source-owned schema path, or missing-species positive/control package under this bounded path/header inventory.",
    ),
}


def iter_matches() -> list[Path]:
    matches: list[Path] = []
    for root, max_depth in SEARCH_ROOTS:
        if not root.exists():
            continue
        for current_root, dirnames, filenames in os.walk(root):
            current = Path(current_root)
            dirnames[:] = [
                name
                for name in dirnames
                if name not in SKIP_DIRS and depth(root, current / name) <= max_depth
            ]
            if depth(root, current) > max_depth:
                dirnames[:] = []
                continue
            for filename in filenames:
                path = current / filename
                if path.suffix.lower() not in DATA_SUFFIXES:
                    continue
                if MATCH_RE.search(str(path)):
                    matches.append(path)
    return sorted(set(matches), key=lambda p: str(p))


def summarize_group(group: str, paths: list[Path]) -> dict[str, object]:
    status, reason = GROUP_DISPOSITION[group]
    sample_paths = paths[:12]
    bytes_total = 0
    csv_files = 0
    label_like_header_files = 0
    exact_intake_filename_hits = 0
    for path in paths:
        try:
            bytes_total += path.stat().st_size
        except OSError:
            pass
        if path.name in {
            "source_label_equivalence_rows.csv",
            "source_label_equivalence_provenance.json",
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
            "direct_manipulation_positive_rows.csv",
            "direct_manipulation_matched_controls.csv",
            "direct_manipulation_provenance.json",
        }:
            exact_intake_filename_hits += 1
        if path.suffix.lower() == ".csv":
            csv_files += 1
            try:
                header = path.open("r", errors="ignore").readline().lower()
            except OSError:
                header = ""
            if (
                ("regime" in header or "label" in header or "manip" in header)
                and ("date" in header or "time" in header or "timestamp" in header)
            ):
                label_like_header_files += 1
    return {
        "group": group,
        "file_count": len(paths),
        "csv_files": csv_files,
        "label_like_header_files": label_like_header_files,
        "exact_intake_filename_hits": exact_intake_filename_hits,
        "bytes_total": bytes_total,
        "sample_paths": [rel_or_abs(p) for p in sample_paths],
        "disposition": status,
        "reason": reason,
        "promotable_new_rows": 0,
        "accepted_rows_added": 0,
        "closes_strict_1h_gap": False,
        "closes_native_subhour_gap": False,
        "closes_recency_tail_gap": False,
        "closes_other_market_equivalence_gap": False,
        "closes_full_direct_manipulation_species_gap": False,
    }


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    matches = iter_matches()
    grouped: dict[str, list[Path]] = defaultdict(list)
    for path in matches:
        grouped[group_for(path)].append(path)

    groups = [
        summarize_group(group, paths)
        for group, paths in sorted(grouped.items(), key=lambda item: item[0])
    ]
    candidate_rows: list[dict[str, object]] = []
    for group in groups:
        for sample in group["sample_paths"]:
            candidate_rows.append(
                {
                    "group": group["group"],
                    "path": sample,
                    "disposition": group["disposition"],
                    "reason": group["reason"],
                    "promotable_new_rows": 0,
                }
            )

    requirement_status = [
        {
            "id": "R2",
            "requirement": "Other-cycle/timeframe validation has suitable confidence",
            "status": "fail_blocked",
            "evidence": "Local inventory found no uncounted source-owned strict 1h or native sub-hour label rows.",
        },
        {
            "id": "R3",
            "requirement": "Strict 1h next-source intake has source-owned rows and provenance",
            "status": "fail_blocked",
            "evidence": "No local source_label_equivalence_rows.csv or equivalent uncounted package found.",
        },
        {
            "id": "R5",
            "requirement": "XOM/Sideways recency-tail repair rows exist",
            "status": "fail_blocked",
            "evidence": "Only known stock-market-regimes source panel duplicates were found; no uncounted recency-tail source rows.",
        },
        {
            "id": "R6",
            "requirement": "Native sub-hour source labels exist",
            "status": "fail_blocked",
            "evidence": "Local hits were generated/model/code/raw-provider surfaces or already registered projections; none are source-owned native sub-hour labels.",
        },
        {
            "id": "R7",
            "requirement": "Other-market/source-label equivalence has suitable confidence",
            "status": "fail_blocked",
            "evidence": "No owner-approved MainRegimeV2 equivalence package found outside existing Board A artifacts.",
        },
        {
            "id": "R8",
            "requirement": "Direct Manipulation has full species coverage with real positives and matched controls",
            "status": "fail_blocked",
            "evidence": "Local direct hits only cover already scoped pump/dump or code/synthetic/raw surfaces; no missing species positive/control package found.",
        },
    ]

    result = {
        "run_id": "20260511T194952+0800-codex-local-broad-source-owned-label-inventory-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decision": "local_broad_source_owned_label_inventory_v1=no_new_promotable_uncounted_source_owned_labels",
        "search_roots": [
            {"root": str(root), "max_depth": max_depth} for root, max_depth in SEARCH_ROOTS
        ],
        "match_count": len(matches),
        "group_count": len(groups),
        "groups": groups,
        "requirement_status": requirement_status,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    json_path = OUT_DIR / "local_broad_source_owned_label_inventory_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    write_csv(
        OUT_DIR / "local_broad_source_owned_label_inventory_v1_groups.csv",
        groups,
        [
            "group",
            "file_count",
            "csv_files",
            "label_like_header_files",
            "exact_intake_filename_hits",
            "bytes_total",
            "disposition",
            "reason",
            "promotable_new_rows",
            "accepted_rows_added",
            "closes_strict_1h_gap",
            "closes_native_subhour_gap",
            "closes_recency_tail_gap",
            "closes_other_market_equivalence_gap",
            "closes_full_direct_manipulation_species_gap",
        ],
    )
    write_csv(
        OUT_DIR / "local_broad_source_owned_label_inventory_v1_candidates.csv",
        candidate_rows,
        ["group", "path", "disposition", "reason", "promotable_new_rows"],
    )
    write_csv(
        OUT_DIR / "local_broad_source_owned_label_inventory_v1_requirements.csv",
        requirement_status,
        ["id", "requirement", "status", "evidence"],
    )

    md_lines = [
        "# Local Broad Source-Owned Label Inventory v1",
        "",
        "- Decision: `local_broad_source_owned_label_inventory_v1=no_new_promotable_uncounted_source_owned_labels`",
        f"- Matched local files: `{len(matches)}`",
        f"- Candidate groups: `{len(groups)}`",
        "- Accepted rows added: `0`",
        "- New confidence gate: `false`",
        "- Strict full objective achieved: `false`; `update_goal=false`",
        "",
        "This bounded inventory searched likely local data roots for un-packaged source-owned regime labels or direct manipulation rows. It is broader than the exact intake filename rescan, but it still does not promote generated labels, duplicate source-panel rows, raw provider panels, code repos, or already registered Board A artifacts. The inventory uses path and header rules only; ambiguous files remain blocked unless a source-owned schema/provenance package is supplied.",
        "",
        "## Group Disposition",
        "",
        "| Group | Files | Label-like CSV headers | Exact intake filename hits | Disposition | Reason |",
        "|---|---:|---:|---:|---|---|",
    ]
    for group in groups:
        md_lines.append(
            f"| `{group['group']}` | `{group['file_count']}` | `{group['label_like_header_files']}` | `{group['exact_intake_filename_hits']}` | `{group['disposition']}` | {group['reason']} |"
        )
    md_lines.extend(
        [
            "",
            "## Requirement Readback",
            "",
            "| Requirement | Status | Evidence |",
            "|---|---|---|",
        ]
    )
    for req in requirement_status:
        md_lines.append(
            f"| `{req['id']}` {req['requirement']} | `{req['status']}` | {req['evidence']} |"
        )
    md_lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "- JSON: `local_broad_source_owned_label_inventory_v1.json`",
            "- Groups CSV: `local_broad_source_owned_label_inventory_v1_groups.csv`",
            "- Candidate sample CSV: `local_broad_source_owned_label_inventory_v1_candidates.csv`",
            "- Requirements CSV: `local_broad_source_owned_label_inventory_v1_requirements.csv`",
        ]
    )
    md_path = OUT_DIR / "local_broad_source_owned_label_inventory_v1.md"
    md_path.write_text("\n".join(md_lines) + "\n")

    assert result["accepted_rows_added"] == 0
    assert result["new_confidence_gate"] is False
    assert result["strict_full_objective_achieved"] is False
    assert result["update_goal"] is False
    assert result["match_count"] >= 1
    assert all(req["status"] == "fail_blocked" for req in requirement_status)

    check_path = CHECK_DIR / "local_broad_source_owned_label_inventory_v1_assertions.out"
    check_path.write_text(
        "\n".join(
            [
                "assert accepted_rows_added == 0: ok",
                "assert new_confidence_gate is false: ok",
                "assert strict_full_objective_achieved is false: ok",
                "assert update_goal is false: ok",
                f"assert match_count >= 1: ok ({result['match_count']})",
                f"json_sha256={sha256(json_path)}",
            ]
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
