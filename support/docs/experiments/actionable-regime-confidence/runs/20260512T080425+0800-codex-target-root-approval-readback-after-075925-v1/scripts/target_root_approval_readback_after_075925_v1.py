#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T080425+0800-codex-target-root-approval-readback-after-075925-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
ARTIFACT_DIR = RUN_ROOT / "target-root-approval-readback-after-075925-v1"
CHECKS_DIR = RUN_ROOT / "checks"
BOARD_A = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
BOARD_B = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"

ROOTS = [
    {
        "root_id": "r6_owner_export",
        "path": "/tmp/ict-engine-board-a-r6-owner-export-v1",
        "required_files": [
            "direct_manipulation_positive_rows.csv",
            "direct_manipulation_matched_controls.csv",
            "direct_manipulation_provenance.json",
        ],
    },
    {
        "root_id": "r5_recency_extension",
        "path": "/tmp/ict-engine-source-panel-recency-extension",
        "required_files": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
    },
    {
        "root_id": "r3_native_subhour",
        "path": "/tmp/ict-engine-native-subhour-source-label-intake",
        "required_files": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
    },
    {
        "root_id": "r6_direct_manipulation_intake",
        "path": "/tmp/ict-engine-direct-manipulation-row-intake",
        "required_files": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
    },
    {
        "root_id": "source_label_equivalence",
        "path": "/tmp/ict-engine-source-label-equivalence-v1",
        "required_files": [
            "source_label_equivalence_rows.csv",
            "source_label_equivalence_provenance.json",
        ],
    },
]

APPROVAL_FILE = Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def count_csv_rows(path: Path) -> int | None:
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.reader(handle)
            count = sum(1 for _ in reader)
        return max(count - 1, 0)
    except Exception:
        return None


def load_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def root_readback(root: dict[str, Any]) -> dict[str, Any]:
    root_path = Path(root["path"])
    required_files = [str(name) for name in root["required_files"]]
    rows: list[dict[str, Any]] = []
    for name in required_files:
        path = root_path / name
        entry = {
            "root_id": root["root_id"],
            "root_path": str(root_path),
            "required_file": name,
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else None,
            "sha256": sha256_file(path) if path.exists() and path.is_file() else "",
            "csv_rows": count_csv_rows(path) if path.exists() and path.suffix.lower() == ".csv" else None,
        }
        rows.append(entry)
    return {
        "root_id": root["root_id"],
        "path": str(root_path),
        "root_exists": root_path.exists(),
        "all_required_files_exist": root_path.exists() and all((root_path / name).exists() for name in required_files),
        "files": rows,
    }


def approval_readback() -> dict[str, Any]:
    payload = load_json(APPROVAL_FILE) if APPROVAL_FILE.exists() else None
    assertions = payload.get("assertions", {}) if isinstance(payload, dict) else {}
    return {
        "approval_file": str(APPROVAL_FILE),
        "exists": APPROVAL_FILE.exists(),
        "approval_present": bool(assertions.get("approval_present")),
        "canonical_merge_allowed_now": bool(assertions.get("canonical_merge_allowed_now")),
        "downstream_rerun_allowed_now": bool(assertions.get("downstream_rerun_allowed_now")),
        "flip_controls_accepted_under_current_contract": bool(
            assertions.get("flip_controls_accepted_under_current_contract")
        ),
        "gate_result": payload.get("gate_result", "") if isinstance(payload, dict) else "",
        "next_action": payload.get("next_action", "") if isinstance(payload, dict) else "",
    }


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    board_hash_before = {
        "board_a": sha256_file(BOARD_A) if BOARD_A.exists() else None,
        "board_b": sha256_file(BOARD_B) if BOARD_B.exists() else None,
    }
    roots = [root_readback(root) for root in ROOTS]
    approval = approval_readback()

    flat_file_rows = [file_row for root in roots for file_row in root["files"]]
    r6_owner = next(root for root in roots if root["root_id"] == "r6_owner_export")
    r5 = next(root for root in roots if root["root_id"] == "r5_recency_extension")
    r3 = next(root for root in roots if root["root_id"] == "r3_native_subhour")
    direct = next(root for root in roots if root["root_id"] == "r6_direct_manipulation_intake")

    r3_provenance = load_json(Path("/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_provenance.json"))
    direct_provenance = load_json(Path("/tmp/ict-engine-direct-manipulation-row-intake/provenance_manifest.json"))

    r3_crisis_supported = False
    if isinstance(r3_provenance, dict):
        labels = set(r3_provenance.get("accepted_mapping_confidence_95_labels") or [])
        r3_crisis_supported = "Crisis" in labels

    direct_is_owner_export_root = direct["all_required_files_exist"] and r6_owner["all_required_files_exist"]

    gate_result = "target_root_approval_readback_after_075925_v1=no_target_root_or_approval_unlock"
    summary = {
        "accepted_rows_added": 0,
        "approval": approval,
        "board_hash_before_artifact": board_hash_before,
        "canonical_merge": False,
        "direct_intake_present": direct["all_required_files_exist"],
        "direct_intake_source_run_id": direct_provenance.get("run_id", "") if isinstance(direct_provenance, dict) else "",
        "downstream_promotion_rerun": False,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": gate_result,
        "pid": os.getpid(),
        "r3_crisis_supported": r3_crisis_supported,
        "r3_native_subhour_complete": r3["all_required_files_exist"],
        "r3_native_subhour_unlock": bool(r3["all_required_files_exist"] and r3_crisis_supported),
        "r5_recency_complete": r5["all_required_files_exist"],
        "r5_recency_unlock": False,
        "r6_direct_intake_is_owner_export_root": direct_is_owner_export_root,
        "r6_owner_export_complete": r6_owner["all_required_files_exist"],
        "r6_owner_export_unlock": False,
        "roots": roots,
        "run_id": RUN_ID,
        "selected_data_autoquant_promotion": False,
        "source_control_evidence_acquired": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
        "valid_required_root_unlock": False,
    }

    (ARTIFACT_DIR / "target_root_approval_readback_after_075925_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    with (ARTIFACT_DIR / "target_root_required_files_v1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["root_id", "root_path", "required_file", "exists", "size_bytes", "sha256", "csv_rows"],
        )
        writer.writeheader()
        writer.writerows(flat_file_rows)

    report = f"""# Target Root Approval Readback After 075925 v1

Run id: `{RUN_ID}`

Gate result: `{gate_result}`

## Scope

Read-only exact target-root and approval-package readback after the settled `075925` public dataset-hub probe. This checks only the Board A roots that would allow direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree promotion to proceed. It does not mutate target roots, approve controls, derive labels, run downstream promotion, make a trade claim, or call `update_goal`.

## Readback

- R6 owner/export root complete: `{summary['r6_owner_export_complete']}`.
- R5 recency root complete: `{summary['r5_recency_complete']}`.
- R3 native-subhour root complete: `{summary['r3_native_subhour_complete']}`.
- R3 Crisis supported: `{summary['r3_crisis_supported']}`.
- Direct manipulation intake present: `{summary['direct_intake_present']}`.
- Direct manipulation intake is owner/export root: `{summary['r6_direct_intake_is_owner_export_root']}`.
- Approval package exists: `{summary['approval']['exists']}`.
- Approval present: `{summary['approval']['approval_present']}`.
- Canonical merge allowed now: `{summary['approval']['canonical_merge_allowed_now']}`.
- Downstream rerun allowed now: `{summary['approval']['downstream_rerun_allowed_now']}`.

## Decision

No exact target root or approval state currently unlocks Board A promotion. `/tmp/ict-engine-board-a-r6-owner-export-v1` and `/tmp/ict-engine-source-panel-recency-extension` are absent; `/tmp/ict-engine-native-subhour-source-label-intake` is present but still Crisis-incomplete; `/tmp/ict-engine-direct-manipulation-row-intake` is present but is not the R6 owner/export root and does not override the explicit approval package, where `approval_present=false`, `canonical_merge_allowed_now=false`, and `downstream_rerun_allowed_now=false`.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- JSON: `{ARTIFACT_DIR / 'target_root_approval_readback_after_075925_v1.json'}`
- Required-file CSV: `{ARTIFACT_DIR / 'target_root_required_files_v1.csv'}`
- Assertions: `{CHECKS_DIR / 'target_root_approval_readback_after_075925_v1_assertions.out'}`

## Next

Continue source/control acquisition only. Do not run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion until an exact required root or explicit approval unlock appears.
"""
    (ARTIFACT_DIR / "target_root_approval_readback_after_075925_v1.md").write_text(report, encoding="utf-8")

    assertions = "\n".join(
        [
            "PASS target_root_approval_readback_after_075925_v1",
            f"gate_result={gate_result}",
            f"r6_owner_export_complete={str(summary['r6_owner_export_complete']).lower()}",
            f"r5_recency_complete={str(summary['r5_recency_complete']).lower()}",
            f"r3_native_subhour_complete={str(summary['r3_native_subhour_complete']).lower()}",
            f"r3_crisis_supported={str(summary['r3_crisis_supported']).lower()}",
            f"direct_intake_present={str(summary['direct_intake_present']).lower()}",
            f"approval_present={str(summary['approval']['approval_present']).lower()}",
            f"canonical_merge_allowed_now={str(summary['approval']['canonical_merge_allowed_now']).lower()}",
            f"downstream_rerun_allowed_now={str(summary['approval']['downstream_rerun_allowed_now']).lower()}",
            "accepted_rows_added=0",
            "r6_owner_export_unlock=false",
            "r5_recency_unlock=false",
            "r3_native_subhour_unlock=false",
            "valid_required_root_unlock=false",
            "source_control_evidence_acquired=false",
            "canonical_merge=false",
            "selected_data_autoquant_promotion=false",
            "downstream_promotion_rerun=false",
            "strict_full_objective=false",
            "trade_usable=false",
            "update_goal=false",
        ]
    )
    (CHECKS_DIR / "target_root_approval_readback_after_075925_v1_assertions.out").write_text(
        assertions + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
