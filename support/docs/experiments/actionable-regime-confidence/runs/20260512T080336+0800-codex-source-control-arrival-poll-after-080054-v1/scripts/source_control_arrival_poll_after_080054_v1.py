#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T080336+0800-codex-source-control-arrival-poll-after-080054-v1"
SLUG = "source-control-arrival-poll-after-080054-v1"
GATE_RESULT = "source_control_arrival_poll_after_080054_v1=no_new_required_root_no_unlock"

REPO = Path(__file__).resolve().parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_ROOT = RUN_ROOT / SLUG
CHECK_ROOT = RUN_ROOT / "checks"

R6_OWNER_EXPORT_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"),
]
R5_RECENCY_ROOTS = [
    Path("/tmp/ict-engine-source-panel-recency-extension"),
    Path("/private/tmp/ict-engine-source-panel-recency-extension"),
]
R3_NATIVE_ROOTS = [
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/private/tmp/ict-engine-native-subhour-source-label-intake"),
]
SOURCE_EQUIV_ROOTS = [
    Path("/tmp/ict-engine-source-label-equivalence-v1"),
    Path("/private/tmp/ict-engine-source-label-equivalence-v1"),
]
APPROVAL_PACKAGE = Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid")
KNOWN_R5_REDOWNLOAD = Path(
    "/tmp/ict-engine-board-a-r5-kaggle-stock-regimes-recency-redownload-v1/"
    "stock_market_regimes_2000_2026.csv"
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def list_files(root: Path | None, limit: int = 80) -> list[str]:
    if root is None or not root.exists():
        return []
    if root.is_file():
        return [str(root)]
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            files.append(str(path))
            if len(files) >= limit:
                break
    return files


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open() as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {"_non_object": data}
    except Exception as exc:  # keep poll fail-closed and auditable
        return {"_read_error": str(exc)}


def inspect_approval(path: Path) -> dict[str, Any]:
    present = path.exists()
    data = load_json(path) if present else {}
    return {
        "path": str(path),
        "present": present,
        "approval_present": bool(data.get("approval_present")) if present else False,
        "canonical_merge_allowed_now": bool(data.get("canonical_merge_allowed_now")) if present else False,
        "downstream_rerun_allowed_now": bool(data.get("downstream_rerun_allowed_now")) if present else False,
        "flip_controls_accepted_under_current_contract": bool(
            data.get("flip_controls_accepted_under_current_contract")
        )
        if present
        else False,
        "keys": sorted(data.keys()) if present else [],
    }


def inspect_r3_native(root: Path | None) -> dict[str, Any]:
    rows_path = root / "native_subhour_source_label_rows.csv" if root else None
    provenance_path = root / "native_subhour_source_label_provenance.json" if root else None
    provenance = load_json(provenance_path) if provenance_path and provenance_path.exists() else {}
    labels = set(provenance.get("accepted_mapping_confidence_95_labels") or [])
    rows = int(provenance.get("row_count") or 0)
    if not labels and rows_path and rows_path.exists():
        with rows_path.open(newline="") as f:
            reader = csv.DictReader(f)
            label_fields = [
                field
                for field in (reader.fieldnames or [])
                if field and field.lower() in {"label", "regime", "mainregimev2", "market_regime"}
            ]
            for idx, row in enumerate(reader):
                if idx >= 10000:
                    break
                rows += 1
                for field in label_fields:
                    value = (row.get(field) or "").strip()
                    if value:
                        labels.add(value)
    crisis_present = "Crisis" in labels
    return {
        "path": str(root) if root else "",
        "present": bool(root and root.exists()),
        "rows_path": str(rows_path) if rows_path else "",
        "rows": rows,
        "labels": sorted(labels),
        "crisis_present": crisis_present,
        "provenance": provenance.get("source") or provenance.get("dataset") or provenance.get("provenance") or "",
        "promotion_allowed": bool(root and root.exists() and crisis_present and not provenance.get("quarantined", False)),
    }


def inspect_known_r5_redownload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "present": False}
    rows = 0
    rows_after_cutoff = 0
    min_date = ""
    max_date = ""
    labels: dict[str, int] = {}
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        date_field = next((x for x in fields if x.lower() in {"date", "timestamp", "time"}), "")
        label_field = next((x for x in fields if x.lower() in {"mainregimev2", "regime", "label"}), "")
        for row in reader:
            rows += 1
            date_value = (row.get(date_field) or "")[:10] if date_field else ""
            if date_value:
                min_date = date_value if not min_date or date_value < min_date else min_date
                max_date = date_value if not max_date or date_value > max_date else max_date
                if date_value > "2026-01-30":
                    rows_after_cutoff += 1
            label = (row.get(label_field) or "").strip() if label_field else ""
            if label:
                labels[label] = labels.get(label, 0) + 1
    return {
        "path": str(path),
        "present": True,
        "rows": rows,
        "min_date": min_date,
        "max_date": max_date,
        "rows_after_2026_01_30": rows_after_cutoff,
        "labels": labels,
    }


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    CHECK_ROOT.mkdir(parents=True, exist_ok=True)

    board_hash = sha256_file(BOARD)
    r6_root = first_existing(R6_OWNER_EXPORT_ROOTS)
    r5_root = first_existing(R5_RECENCY_ROOTS)
    r3_root = first_existing(R3_NATIVE_ROOTS)
    source_equiv_root = first_existing(SOURCE_EQUIV_ROOTS)

    approval = inspect_approval(APPROVAL_PACKAGE)
    r3 = inspect_r3_native(r3_root)
    known_r5 = inspect_known_r5_redownload(KNOWN_R5_REDOWNLOAD)

    r6_unlock = bool(
        r6_root
        and r6_root.exists()
        and approval["approval_present"]
        and approval["canonical_merge_allowed_now"]
    )
    r5_unlock = bool(r5_root and r5_root.exists())
    r3_unlock = bool(r3["present"] and r3["crisis_present"] and r3["promotion_allowed"])
    source_control_unlock = r6_unlock or r5_unlock or r3_unlock

    decision = {
        "accepted_rows_added": 0,
        "r6_owner_export_unlock": r6_unlock,
        "r5_recency_unlock": r5_unlock,
        "r3_native_subhour_unlock": r3_unlock,
        "valid_required_root_unlock": source_control_unlock,
        "source_control_evidence_acquired": source_control_unlock,
        "direct_verifier_promoting": False,
        "split_calibration_run": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }
    if source_control_unlock:
        decision["strict_full_objective"] = False
        decision["update_goal"] = False

    payload = {
        "run_id": RUN_ID,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact": board_hash,
        "gate_result": GATE_RESULT if not source_control_unlock else "source_control_arrival_poll_after_080054_v1=unlock_detected_requires_manual_gate_review",
        "r6_owner_export": {
            "roots": [str(p) for p in R6_OWNER_EXPORT_ROOTS],
            "present": bool(r6_root),
            "path": str(r6_root) if r6_root else "",
            "files": list_files(r6_root),
            "unlock": r6_unlock,
        },
        "r6_approval_package": approval,
        "r5_recency": {
            "roots": [str(p) for p in R5_RECENCY_ROOTS],
            "present": bool(r5_root),
            "path": str(r5_root) if r5_root else "",
            "files": list_files(r5_root),
            "unlock": r5_unlock,
        },
        "known_r5_redownload": known_r5,
        "r3_native_subhour": r3,
        "source_label_equivalence": {
            "roots": [str(p) for p in SOURCE_EQUIV_ROOTS],
            "present": bool(source_equiv_root),
            "path": str(source_equiv_root) if source_equiv_root else "",
            "files": list_files(source_equiv_root),
            "promotion_allowed": False,
        },
        "decision": decision,
    }

    json_path = OUT_ROOT / "source_control_arrival_poll_after_080054_v1.json"
    csv_path = OUT_ROOT / "source_control_arrival_poll_after_080054_v1.csv"
    md_path = OUT_ROOT / "source_control_arrival_poll_after_080054_v1.md"
    assertions_path = CHECK_ROOT / "source_control_arrival_poll_after_080054_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    rows = [
        ("board_hash_before_artifact", board_hash, "observed"),
        ("r6_owner_export_root_present", str(bool(r6_root)).lower(), "no_unlock" if not r6_unlock else "unlock_candidate"),
        ("r6_approval_package_present", str(approval["present"]).lower(), "read"),
        ("r6_approval_present", str(approval["approval_present"]).lower(), "no_merge" if not approval["approval_present"] else "approval_candidate"),
        (
            "r6_canonical_merge_allowed_now",
            str(approval["canonical_merge_allowed_now"]).lower(),
            "no_merge" if not approval["canonical_merge_allowed_now"] else "merge_candidate",
        ),
        ("r5_recency_root_present", str(bool(r5_root)).lower(), "no_unlock" if not r5_unlock else "unlock_candidate"),
        (
            "known_r5_rows_after_cutoff",
            str(known_r5.get("rows_after_2026_01_30", "")),
            "no_unlock" if known_r5.get("rows_after_2026_01_30", 0) == 0 else "review",
        ),
        ("r3_native_subhour_root_present", str(r3["present"]).lower(), "present_non_promoting" if r3["present"] else "absent"),
        ("r3_crisis_present", str(r3["crisis_present"]).lower(), "no_unlock" if not r3["crisis_present"] else "review"),
        ("source_label_equivalence_target_present", str(bool(source_equiv_root)).lower(), "no_unlock"),
        ("accepted_rows_added", "0", "blocked"),
        ("valid_required_root_unlock", str(source_control_unlock).lower(), "blocked" if not source_control_unlock else "review"),
        ("source_control_evidence_acquired", str(source_control_unlock).lower(), "blocked" if not source_control_unlock else "review"),
        ("update_goal", "false", "blocked"),
    ]
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["check", "value", "decision"])
        writer.writerows(rows)

    md_path.write_text(
        "\n".join(
            [
                "# Source/Control Arrival Poll After 080054 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{payload['gate_result']}`",
                "",
                "## Scope",
                "",
                "Read-only poll after the `080054` current-objective audit. This checks only whether a valid R6 owner/export root, R5 post-cutoff source-panel root, R3 Crisis-capable native-subhour source-label root, or explicit R6 approval package has arrived. It does not mutate target roots, derive labels, run verifier/calibration, canonical merge, AutoQuant, Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Readback",
                "",
                f"- Board hash before artifact: `{board_hash}`.",
                f"- R6 owner/export root present: `{str(bool(r6_root)).lower()}`.",
                f"- R6 approval package present: `{str(approval['present']).lower()}`; approval present `{str(approval['approval_present']).lower()}`; canonical merge allowed `{str(approval['canonical_merge_allowed_now']).lower()}`; downstream rerun allowed `{str(approval['downstream_rerun_allowed_now']).lower()}`.",
                f"- R5 recency root present: `{str(bool(r5_root)).lower()}`.",
                f"- Known R5 redownload rows after `2026-01-30`: `{known_r5.get('rows_after_2026_01_30', 'n/a')}`.",
                f"- R3 native-subhour root present: `{str(r3['present']).lower()}`; labels `{', '.join(r3['labels']) if r3['labels'] else 'none'}`; Crisis present `{str(r3['crisis_present']).lower()}`.",
                f"- Source-label equivalence target present: `{str(bool(source_equiv_root)).lower()}`.",
                "",
                "## Decision",
                "",
                "- No valid required source/control root was unlocked in this poll.",
                "- Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path.relative_to(REPO)}`",
                f"- CSV: `{csv_path.relative_to(REPO)}`",
                f"- Assertions: `{assertions_path.relative_to(REPO)}`",
                "",
                "## Next",
                "",
                "Continue source/control acquisition only before any direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.",
                "",
            ]
        )
    )

    assertion_lines = [
        "PASS source_control_arrival_poll_after_080054_v1" if not source_control_unlock else "REVIEW source_control_arrival_poll_after_080054_v1",
        f"gate_result={payload['gate_result']}",
        f"r6_owner_export_root_present={str(bool(r6_root)).lower()}",
        f"r6_approval_present={str(approval['approval_present']).lower()}",
        f"r6_canonical_merge_allowed_now={str(approval['canonical_merge_allowed_now']).lower()}",
        f"r5_recency_root_present={str(bool(r5_root)).lower()}",
        f"known_r5_rows_after_cutoff={known_r5.get('rows_after_2026_01_30', '')}",
        f"r3_native_subhour_root_present={str(r3['present']).lower()}",
        f"r3_crisis_present={str(r3['crisis_present']).lower()}",
        f"valid_required_root_unlock={str(source_control_unlock).lower()}",
        f"source_control_evidence_acquired={str(source_control_unlock).lower()}",
        "accepted_rows_added=0",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertion_lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
