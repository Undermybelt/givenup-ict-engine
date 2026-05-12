#!/usr/bin/env python3
"""Dispositon readback for local Databento GC raw OHLCV package."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


RUN_ID = "20260512T074844+0800-codex-databento-gc-raw-recency-disposition-after-074424-v1"
GATE_RESULT = "databento_gc_raw_recency_disposition_after_074424_v1=raw_ohlcv_post_cutoff_no_source_label_or_control_unlock"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = RUN_ROOT / "databento-gc-raw-recency-disposition-after-074424-v1"
CHECK_ROOT = RUN_ROOT / "checks"
LOCAL_ROOT = Path("/Users/thrill3r/Downloads/Tomac/gc future 2021-2025")


def read_json(path: Path):
    with path.open() as handle:
        return json.load(handle)


def csv_profile(path: Path, max_sample: int = 2) -> dict:
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "rows": 0,
            "columns": [],
            "first_row": None,
            "last_row": None,
            "sample_rows": [],
        }

    first_row = None
    last_row = None
    sample_rows = []
    rows = 0
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        for row in reader:
            if first_row is None:
                first_row = dict(row)
            if len(sample_rows) < max_sample:
                sample_rows.append(dict(row))
            last_row = dict(row)
            rows += 1
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": path.stat().st_size,
        "rows": rows,
        "columns": columns,
        "first_row": first_row,
        "last_row": last_row,
        "sample_rows": sample_rows,
    }


def has_any(columns: list[str], names: set[str]) -> bool:
    lowered = {c.lower() for c in columns}
    return bool(lowered.intersection(names))


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    CHECK_ROOT.mkdir(parents=True, exist_ok=True)

    manifest_path = LOCAL_ROOT / "manifest.json"
    metadata_path = LOCAL_ROOT / "metadata.json"
    condition_path = LOCAL_ROOT / "condition.json"
    gc_continuous = LOCAL_ROOT / "gc_201101_202604.csv"
    glbx_ohlcv = LOCAL_ROOT / "glbx-mdp3-20210106-20260105.ohlcv-1m.csv"
    symbology = LOCAL_ROOT / "symbology.csv"
    archive = LOCAL_ROOT / "databento.rar"

    manifest = read_json(manifest_path) if manifest_path.exists() else {}
    metadata = read_json(metadata_path) if metadata_path.exists() else {}
    condition = read_json(condition_path) if condition_path.exists() else []

    profiles = {
        "gc_continuous": csv_profile(gc_continuous),
        "glbx_ohlcv": csv_profile(glbx_ohlcv),
        "symbology": csv_profile(symbology),
    }

    label_columns = {
        "main_regime_v2_label",
        "regime_label",
        "source_confidence",
        "direct_label",
        "matched_negative_group_id",
        "event_species",
    }
    order_lifecycle_columns = {
        "order_id",
        "action",
        "side",
        "price",
        "size",
        "sequence",
        "ts_recv",
        "ts_in_delta",
    }
    candidate_columns = {
        name: {
            "has_source_label_columns": has_any(profile.get("columns", []), label_columns),
            "has_order_lifecycle_columns": has_any(profile.get("columns", []), order_lifecycle_columns),
        }
        for name, profile in profiles.items()
    }

    manifest_files = manifest.get("files", [])
    manifest_filenames = [f.get("filename") for f in manifest_files]
    glbx_manifest_entry = next(
        (f for f in manifest_files if f.get("filename") == glbx_ohlcv.name),
        {},
    )

    result = {
        "run_id": RUN_ID,
        "gate_result": GATE_RESULT,
        "local_root": str(LOCAL_ROOT),
        "archive": {
            "path": str(archive),
            "exists": archive.exists(),
            "size_bytes": archive.stat().st_size if archive.exists() else None,
        },
        "manifest": {
            "path": str(manifest_path),
            "exists": manifest_path.exists(),
            "job_id": manifest.get("job_id"),
            "filenames": manifest_filenames,
            "glbx_ohlcv_manifest_entry": glbx_manifest_entry,
        },
        "metadata": {
            "path": str(metadata_path),
            "exists": metadata_path.exists(),
            "query": metadata.get("query", {}),
            "customizations": metadata.get("customizations", {}),
        },
        "condition": {
            "path": str(condition_path),
            "exists": condition_path.exists(),
            "rows": len(condition) if isinstance(condition, list) else None,
            "first": condition[0] if isinstance(condition, list) and condition else None,
            "last": condition[-1] if isinstance(condition, list) and condition else None,
        },
        "profiles": profiles,
        "candidate_columns": candidate_columns,
        "contract_readback": {
            "r5_source_panel_recency": "blocked_no_stock_market_regimes_2026_extension_csv_no_source_panel_recency_provenance_json",
            "r3_native_subhour": "blocked_raw_ohlcv_has_native_minutes_but_no_verifier_native_mainregimev2_labels_or_crisis_taxonomy",
            "r6_owner_export": "blocked_no_order_lifecycle_positive_rows_no_matched_normal_controls_no_flip_approval",
        },
        "assertions": {
            "local_root_present": LOCAL_ROOT.exists(),
            "post_2026_01_30_raw_ohlcv_present": (
                profiles["gc_continuous"].get("last_row", {}).get("ts_event", "") > "2026-01-30"
            ),
            "source_label_columns_present": any(v["has_source_label_columns"] for v in candidate_columns.values()),
            "order_lifecycle_columns_present": any(v["has_order_lifecycle_columns"] for v in candidate_columns.values()),
            "r5_recency_unlock": False,
            "r3_native_subhour_unlock": False,
            "r6_owner_export_unlock": False,
            "valid_required_root_unlock": False,
            "source_control_evidence_acquired": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "next": "Continue source/control acquisition only; do not convert Databento raw OHLCV into source-owned MainRegimeV2 labels or R6 controls.",
    }

    json_path = OUT_ROOT / "databento_gc_raw_recency_disposition_after_074424_v1.json"
    csv_path = OUT_ROOT / "databento_gc_raw_recency_files_v1.csv"
    md_path = OUT_ROOT / "databento_gc_raw_recency_disposition_after_074424_v1.md"
    assertions_path = CHECK_ROOT / "databento_gc_raw_recency_disposition_after_074424_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "candidate",
                "path",
                "exists",
                "size_bytes",
                "rows",
                "first_ts_event",
                "last_ts_event",
                "columns",
                "has_source_label_columns",
                "has_order_lifecycle_columns",
                "disposition",
            ],
        )
        writer.writeheader()
        for name, profile in profiles.items():
            writer.writerow(
                {
                    "candidate": name,
                    "path": profile.get("path"),
                    "exists": profile.get("exists"),
                    "size_bytes": profile.get("size_bytes"),
                    "rows": profile.get("rows"),
                    "first_ts_event": (profile.get("first_row") or {}).get("ts_event"),
                    "last_ts_event": (profile.get("last_row") or {}).get("ts_event"),
                    "columns": "|".join(profile.get("columns", [])),
                    "has_source_label_columns": candidate_columns[name]["has_source_label_columns"],
                    "has_order_lifecycle_columns": candidate_columns[name]["has_order_lifecycle_columns"],
                    "disposition": "raw_ohlcv_or_symbology_only_non_promoting",
                }
            )

    md_path.write_text(
        "\n".join(
            [
                "# Databento GC Raw Recency Disposition After 074424 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{GATE_RESULT}`",
                "",
                "## Scope",
                "",
                "Bounded disposition of the local Databento/Tomac GC futures package found under Downloads after the post-074116 source-route probes. This packet does not mutate R3/R5/R6 target roots, derive labels, approve controls, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Readback",
                "",
                f"- Local root: `{LOCAL_ROOT}`.",
                f"- Manifest job id: `{manifest.get('job_id')}`; dataset `{metadata.get('query', {}).get('dataset')}`; schema `{metadata.get('query', {}).get('schema')}`; symbols `{metadata.get('query', {}).get('symbols')}`.",
                f"- Continuous GC candidate rows: `{profiles['gc_continuous'].get('rows')}`; first timestamp `{(profiles['gc_continuous'].get('first_row') or {}).get('ts_event')}`; last timestamp `{(profiles['gc_continuous'].get('last_row') or {}).get('ts_event')}`.",
                f"- GLBX OHLCV manifest candidate rows: `{profiles['glbx_ohlcv'].get('rows')}`; first timestamp `{(profiles['glbx_ohlcv'].get('first_row') or {}).get('ts_event')}`; last timestamp `{(profiles['glbx_ohlcv'].get('last_row') or {}).get('ts_event')}`.",
                f"- Archive present: `{archive.exists()}`; archive size bytes `{archive.stat().st_size if archive.exists() else None}`.",
                "- Candidate CSV columns are OHLCV/symbology fields only. No `main_regime_v2_label`, `regime_label`, `source_confidence`, `direct_label`, `matched_negative_group_id`, or order-lifecycle control columns are present.",
                "",
                "## Decision",
                "",
                "The package is real local raw market data and the continuous GC file extends past `2026-01-30`, but it is not source-owned `MainRegimeV2` label evidence and not R6 owner-export control evidence. It cannot fill `/tmp/ict-engine-source-panel-recency-extension`, `/tmp/ict-engine-native-subhour-source-label-intake`, or `/tmp/ict-engine-board-a-r6-owner-export-v1` under the current Board A contract.",
                "",
                "Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.",
                "",
                "## Next",
                "",
                "Continue source/control acquisition only. Do not convert Databento raw OHLCV into source-owned labels or matched controls; wait for explicit source-owned post-cutoff label rows, verifier-native R3 labels, R6 controls, or explicit `FLIP` approval before downstream promotion.",
                "",
            ]
        )
        + "\n"
    )

    checks = result["assertions"]
    failures = []
    for key in [
        "local_root_present",
        "post_2026_01_30_raw_ohlcv_present",
    ]:
        if not checks[key]:
            failures.append(f"{key}=false")
    for key in [
        "source_label_columns_present",
        "order_lifecycle_columns_present",
        "r5_recency_unlock",
        "r3_native_subhour_unlock",
        "r6_owner_export_unlock",
        "valid_required_root_unlock",
        "source_control_evidence_acquired",
        "canonical_merge",
        "downstream_promotion_rerun",
        "strict_full_objective",
        "trade_usable",
        "update_goal",
    ]:
        if checks[key]:
            failures.append(f"{key}=true")

    if failures:
        assertions_path.write_text("FAIL " + "; ".join(failures) + "\n")
        return 1
    assertions_path.write_text(
        "\n".join(
            [
                "PASS databento_gc_raw_recency_disposition_after_074424_v1",
                f"gate_result={GATE_RESULT}",
                "post_2026_01_30_raw_ohlcv_present=true",
                "source_label_columns_present=false",
                "order_lifecycle_columns_present=false",
                "valid_required_root_unlock=false",
                "update_goal=false",
                "",
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
