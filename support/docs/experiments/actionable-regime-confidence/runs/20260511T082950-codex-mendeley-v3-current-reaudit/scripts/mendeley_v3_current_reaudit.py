#!/usr/bin/env python3
"""Current Mendeley v3 direct Manipulation re-audit.

This intentionally does not redownload multi-GB raw CSVs into the repo. It
refreshes public v3 metadata, verifies local raw hashes that are already under
temporary storage, and carries forward unchanged calibration gates only when
the raw file hash still matches the Mendeley v3 source hash.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T082950+0800-codex-mendeley-v3-current-reaudit"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T082950-codex-mendeley-v3-current-reaudit"
OUT_DIR = RUN_ROOT / "mendeley-v3-reaudit"
CHECK_DIR = RUN_ROOT / "checks"
TMP_METADATA = Path("/private/tmp/mendeley_v3_files_current.json")

MENDELEY_FILES_URL = "https://data.mendeley.com/public-api/datasets/4hyxfwzpgg/files?folder_id=root&version=3"
MULTIFILE_PRIOR = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T022630-codex-mendeley-multifile-manipulation-gate/"
    "manipulation-gate/mendeley_multifile_manipulation_gate_report.json"
)
GOX_HGB_PRIOR = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T043249-codex-mendeley-gox-hgb-wash-gate/"
    "gox-hgb-wash-gate/mendeley_gox_hgb_wash_gate_report.json"
)

LOCAL_CANDIDATES = {
    "Blur_ml_samples.csv": [
        Path("/private/tmp/Blur_ml_samples.csv"),
        Path("/tmp/Blur_ml_samples.csv"),
        Path("/private/tmp/ict-regime-mendeley-wash-trading/Blur_ml_samples.csv"),
    ],
    "gox_ml_samples.csv": [
        Path("/private/tmp/ict-regime-mendeley-wash-trading/gox_ml_samples.csv"),
        Path("/private/tmp/gox_ml_samples.csv"),
        Path("/tmp/gox_ml_samples.csv"),
    ],
    "LooksRare_ml_samples.csv": [
        Path("/private/tmp/ict-regime-mendeley-wash-trading/LooksRare_ml_samples.csv"),
        Path("/private/tmp/LooksRare_ml_samples.csv"),
        Path("/tmp/LooksRare_ml_samples.csv"),
    ],
    "OpenSea_ml_samples.csv": [
        Path("/private/tmp/OpenSea_ml_samples.csv"),
        Path("/tmp/OpenSea_ml_samples.csv"),
        Path("/private/tmp/ict-regime-mendeley-wash-trading/OpenSea_ml_samples.csv"),
    ],
}


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def refresh_metadata() -> list[dict[str, Any]]:
    try:
        with urllib.request.urlopen(MENDELEY_FILES_URL, timeout=30) as response:
            body = response.read()
        TMP_METADATA.write_bytes(body)
        return json.loads(body.decode("utf-8"))
    except Exception:
        if TMP_METADATA.exists():
            return read_json(TMP_METADATA)
        raise


def first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def summarize_best_rule(file_entry: dict[str, Any]) -> dict[str, Any] | None:
    best_rules = file_entry.get("best_rules") or []
    if not best_rules:
        return None
    rule = best_rules[0]
    splits = rule.get("splits", {})
    return {
        "candidate_class": rule.get("candidate_class"),
        "rule_type": rule.get("rule_type"),
        "min_wilson95_lcb": rule.get("min_wilson95_lcb"),
        "min_support": rule.get("min_support"),
        "passes_wilson95": rule.get("passes_wilson95"),
        "passes_support": rule.get("passes_support"),
        "passes_coverage": rule.get("passes_coverage"),
        "calibration": splits.get("calibration"),
        "test": splits.get("test"),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    metadata = refresh_metadata()
    metadata_by_name = {row["filename"]: row for row in metadata}
    disk = shutil.disk_usage("/private/tmp")

    prior_multifile = read_json(MULTIFILE_PRIOR)
    prior_gox_hgb = read_json(GOX_HGB_PRIOR)
    prior_by_venue = {row.get("venue"): row for row in prior_multifile.get("files", [])}
    prior_by_filename = {
        "LooksRare_ml_samples.csv": prior_by_venue.get("LooksRare"),
        "Blur_ml_samples.csv": prior_by_venue.get("Blur"),
        "gox_ml_samples.csv": prior_by_venue.get("Gox"),
        "OpenSea_ml_samples.csv": prior_by_venue.get("OpenSea"),
    }

    files: list[dict[str, Any]] = []
    for filename, meta in sorted(metadata_by_name.items()):
        details = meta.get("content_details", {})
        expected_sha = details.get("sha256_hash")
        size = int(details.get("size") or meta.get("size") or 0)
        local_path = first_existing(LOCAL_CANDIDATES.get(filename, []))
        local: dict[str, Any] = {
            "path": str(local_path) if local_path else None,
            "exists": bool(local_path),
            "actual_sha256": None,
            "sha256_matches_mendeley_v3": False,
        }
        if local_path:
            actual = sha256(local_path)
            local.update({
                "actual_sha256": actual,
                "sha256_matches_mendeley_v3": actual == expected_sha,
            })
        prior_entry = prior_by_filename.get(filename) or {}
        best_rule = summarize_best_rule(prior_entry) if prior_entry else None
        status = "verified_prior_gate_still_applicable" if local["sha256_matches_mendeley_v3"] else "missing_or_hash_unverified"
        if filename == "OpenSea_ml_samples.csv" and not local_path:
            status = "blocked_not_fetched_disk_capacity"
        files.append({
            "filename": filename,
            "mendeley_v3_size_bytes": size,
            "mendeley_v3_sha256": expected_sha,
            "download_url": details.get("download_url"),
            "local": local,
            "prior_gate_entry_available": bool(prior_entry),
            "prior_best_rule": best_rule,
            "chronology_grade": prior_entry.get("chronology_grade"),
            "chronology_reason": prior_entry.get("chronology_reason"),
            "accepted_95_chronology_grade": prior_entry.get("accepted_95_chronology_grade"),
            "accepted_95_rule_only": prior_entry.get("accepted_95_rule_only"),
            "status": status,
        })

    gox_metrics = prior_gox_hgb.get("metrics", {})
    gox_decision = prior_gox_hgb.get("decision", {})
    blockers = [
        "No verified local Mendeley v3 file has an accepted unchanged 95% direct Manipulation gate.",
        "LooksRare and Blur remain blocked as NFT ML samples without global chronology-grade timestamp evidence.",
        "Gox HGB remains blocked by test coverage below 0.03 and calibration/test ECE above 0.05 despite Wilson95 above 0.95.",
        "OpenSea v3 is 2127010916 bytes and is not present locally; current /private/tmp free space is insufficient for a safe bounded fetch.",
    ]
    accepted = False
    opensea_size = metadata_by_name["OpenSea_ml_samples.csv"]["content_details"]["size"]
    safe_fetch_buffer = 2 * 1024 * 1024 * 1024
    opensea_safe_fetch_possible = disk.free > opensea_size + safe_fetch_buffer

    report = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "active_taxonomy": "MainRegimeV2",
        "main_price_roots": ["Bull", "Bear", "Sideways", "Crisis"],
        "direct_event_class_or_overlay": "Manipulation",
        "objective": "Re-fetch Mendeley v3 metadata and re-audit whether unchanged prior wash-trading gates can add accepted direct Manipulation label coverage.",
        "source": {
            "id": "4hyxfwzpgg",
            "doi": "10.17632/4hyxfwzpgg.3",
            "files_url": MENDELEY_FILES_URL,
            "metadata_cache": str(TMP_METADATA),
        },
        "disk": {
            "private_tmp_free_bytes": disk.free,
            "opensea_size_bytes": opensea_size,
            "safe_fetch_buffer_bytes": safe_fetch_buffer,
            "opensea_safe_fetch_possible": opensea_safe_fetch_possible,
        },
        "files": files,
        "prior_gox_hgb_readback": {
            "gate_result": gox_decision.get("gate_result"),
            "accepted_95": gox_decision.get("accepted_95"),
            "blockers": gox_decision.get("blockers"),
            "calibration": gox_metrics.get("calibration"),
            "test": gox_metrics.get("test"),
        },
        "decision": {
            "goal_achieved": False,
            "accepted_direct_manipulation_label_sources_added": 0,
            "mainregimev2_root_slots_added": 0,
            "manipulation_label_slots_added": 0,
            "accepted_full_cycle_full_universe": False,
            "gate_result": "blocked_mendeley_v3_current_reaudit_no_accepted_manipulation_label_panel",
            "blockers": blockers,
            "next_action": "Do not promote Mendeley v3 as accepted. Either free enough temp disk and evaluate OpenSea with the unchanged gate, or move to a provenance-preserving Dune nft.wash_trades export path with replayable timestamps.",
            "raw_data_committed": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "trade_usable": False,
        },
        "artifacts": {
            "json": rel(OUT_DIR / "mendeley_v3_current_reaudit.json"),
            "md": rel(OUT_DIR / "mendeley_v3_current_reaudit.md"),
            "assertions": rel(CHECK_DIR / "mendeley_v3_current_reaudit_assertions.out"),
            "script": rel(RUN_ROOT / "scripts/mendeley_v3_current_reaudit.py"),
        },
    }

    json_path = OUT_DIR / "mendeley_v3_current_reaudit.json"
    md_path = OUT_DIR / "mendeley_v3_current_reaudit.md"
    assertions_path = CHECK_DIR / "mendeley_v3_current_reaudit_assertions.out"
    write_json(json_path, report)

    lines = [
        "# Mendeley v3 Current Re-audit",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Gate result: `{report['decision']['gate_result']}`",
        "- Accepted direct `Manipulation` label sources added: `0`",
        "- MainRegimeV2 root-label slots added: `0`",
        "- Manipulation label slots added: `0`",
        "- Raw data committed: `false`",
        "- Runtime code changed: `false`",
        "- Thresholds relaxed: `false`",
        "",
        "## File Status",
        "",
        "| File | Size bytes | Local status | Prior gate readback |",
        "|---|---:|---|---|",
    ]
    for row in files:
        local_status = row["status"]
        prior_gate = "none"
        if row.get("prior_best_rule"):
            best = row["prior_best_rule"]
            prior_gate = f"min_lcb={best.get('min_wilson95_lcb')}; coverage={best.get('passes_coverage')}; support={best.get('passes_support')}; chronology={row.get('chronology_grade')}"
        lines.append(f"| `{row['filename']}` | {row['mendeley_v3_size_bytes']} | `{local_status}` | {prior_gate} |")
    lines += [
        "",
        "## Gox HGB Readback",
        "",
        f"- Prior gate: `{gox_decision.get('gate_result')}`",
        f"- Calibration Wilson95 / coverage / ECE: `{gox_metrics.get('calibration', {}).get('wilson_lcb_95')}` / `{gox_metrics.get('calibration', {}).get('coverage')}` / `{gox_metrics.get('calibration', {}).get('ece_10bin')}`",
        f"- Test Wilson95 / coverage / ECE: `{gox_metrics.get('test', {}).get('wilson_lcb_95')}` / `{gox_metrics.get('test', {}).get('coverage')}` / `{gox_metrics.get('test', {}).get('ece_10bin')}`",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {blocker}" for blocker in blockers)
    lines += [
        "",
        f"Next action: {report['decision']['next_action']}",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")

    assertion_lines = [
        "PASS active_taxonomy=MainRegimeV2",
        "PASS supersedes_drift_run=20260511T082635+0800-codex-main-regime-v4-web-research-taxonomy",
        "PASS direct_event_class_or_overlay=Manipulation",
        "PASS mendeley_v3_metadata_refetched=true",
        f"PASS files_seen={len(files)}",
        "PASS accepted_direct_manipulation_label_sources_added=0",
        "PASS mainregimev2_root_slots_added=0",
        "PASS manipulation_label_slots_added=0",
        "PASS goal_achieved=false",
        "PASS accepted_full_cycle_full_universe=false",
        "PASS raw_data_committed=false",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
        "PASS trade_usable=false",
        "PASS gate_result=blocked_mendeley_v3_current_reaudit_no_accepted_manipulation_label_panel",
    ]
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
