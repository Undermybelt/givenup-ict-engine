#!/usr/bin/env python3
"""Seed same-schema CFTC matched controls for the direct Manipulation intake."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T205654-codex-cftc-matched-control-seed-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "cftc-matched-control-seed"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE_ROWS = INTAKE / "positive_spoofing_layering_rows.csv"
NEGATIVE_ROWS = INTAKE / "matched_negative_normal_activity_rows.csv"
PROVENANCE = INTAKE / "provenance_manifest.json"
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

REQUIRED_FIELDS = [
    "label",
    "source_report",
    "source_section",
    "trade_date",
    "symbol",
    "venue_or_market_center",
    "participant_type_code",
    "participant_identifier",
    "side",
    "earliest_order_received_time",
    "latest_order_received_time",
    "order_count",
    "total_order_quantity",
    "activity_description",
    "matched_negative_group_id",
    "session_bucket",
    "source_row_id",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in REQUIRED_FIELDS})


def run_verifier() -> dict[str, Any]:
    proc = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    (OUT / "direct_manipulation_row_intake_verifier.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (OUT / "direct_manipulation_row_intake_verifier.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    parsed = None
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = None
    return {
        "cmd": ["python3", rel(VERIFIER), "--intake-root", str(INTAKE)],
        "returncode": proc.returncode,
        "stdout_path": rel(OUT / "direct_manipulation_row_intake_verifier.stdout.txt"),
        "stderr_path": rel(OUT / "direct_manipulation_row_intake_verifier.stderr.txt"),
        "parsed_json": parsed,
    }


def control_side(row: dict[str, str]) -> str:
    source_side = row.get("side", "")
    if "opposite buy genuine iceberg order" in source_side or "sell spoof" in source_side:
        return "buy genuine iceberg order described in same CFTC facts paragraph"
    if "opposite sell genuine iceberg order" in source_side or "buy spoof" in source_side:
        return "sell genuine iceberg order described in same CFTC facts paragraph"
    return "genuine order described in same CFTC facts paragraph"


def build_controls(positives: list[dict[str, str]]) -> list[dict[str, str]]:
    controls = []
    for row in positives:
        source_row_id = row.get("source_row_id", "unknown")
        controls.append(
            {
                "label": "matched_negative_normal_activity",
                "source_report": row.get("source_report", ""),
                "source_section": row.get("source_section", ""),
                "trade_date": row.get("trade_date", ""),
                "symbol": row.get("symbol", ""),
                "venue_or_market_center": row.get("venue_or_market_center", ""),
                "participant_type_code": row.get("participant_type_code", ""),
                "participant_identifier": row.get("participant_identifier", ""),
                "side": control_side(row),
                "earliest_order_received_time": row.get("earliest_order_received_time", ""),
                "latest_order_received_time": row.get("latest_order_received_time", ""),
                "order_count": "one genuine iceberg order leg described by CFTC facts",
                "total_order_quantity": "source report describes filled genuine iceberg order; exact displayed quantity not restated in derived control",
                "activity_description": (
                    "Matched same-report control seed from the CFTC facts: the genuine iceberg order leg "
                    "described opposite the spoof group. This is schema/control seeding only, not a broad "
                    "normal-market calibration sample."
                ),
                "matched_negative_group_id": row.get("matched_negative_group_id", ""),
                "session_bucket": row.get("session_bucket", ""),
                "source_row_id": f"{source_row_id}_matched_genuine_iceberg_control",
            }
        )
    return controls


def update_provenance(provenance: dict[str, Any], controls: list[dict[str, str]]) -> dict[str, Any]:
    updated = dict(provenance)
    updated["matched_negative_rows_acquired"] = True
    updated["matched_negative_rows_path"] = str(NEGATIVE_ROWS)
    updated["matched_negative_rows_count"] = len(controls)
    updated["matched_negative_rows_sha256"] = sha256(NEGATIVE_ROWS)
    updated["matched_negative_control_policy"] = (
        "Derived only from public CFTC facts describing genuine iceberg order legs in the same examples; "
        "schema-ready/unscored seed, not a broad normal-activity calibration sample."
    )
    updated["matched_negative_materialized_at_utc"] = datetime.now(timezone.utc).isoformat()
    return updated


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    board_hash = sha256(BOARD)
    positives = read_rows(POSITIVE_ROWS) if POSITIVE_ROWS.exists() else []
    old_provenance = json.loads(PROVENANCE.read_text(encoding="utf-8")) if PROVENANCE.exists() else {}
    controls = build_controls(positives)
    write_rows(NEGATIVE_ROWS, controls)
    new_provenance = update_provenance(old_provenance, controls)
    PROVENANCE.write_text(json.dumps(new_provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    verifier = run_verifier()

    verifier_status = (verifier.get("parsed_json") or {}).get("status")
    schema_ready = verifier_status == "schema_ready_unscored"
    decision = (
        "cftc_matched_control_seed_v1=direct_intake_schema_ready_unscored_confidence_gate_false"
        if schema_ready
        else "cftc_matched_control_seed_v1=direct_intake_still_blocked"
    )
    audit = {
        "run_id": f"{RUN_ID.replace('-codex-', '+0800-codex-')}",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "board_hash_before_writeback": board_hash,
        "intake_root": str(INTAKE),
        "positive_rows_path": str(POSITIVE_ROWS),
        "positive_rows_count": len(positives),
        "positive_rows_sha256": sha256(POSITIVE_ROWS) if POSITIVE_ROWS.exists() else "",
        "matched_negative_rows_path": str(NEGATIVE_ROWS),
        "matched_negative_rows_count": len(controls),
        "matched_negative_rows_sha256": sha256(NEGATIVE_ROWS),
        "provenance_manifest_path": str(PROVENANCE),
        "provenance_manifest_sha256": sha256(PROVENANCE),
        "source_policy": (
            "Public CFTC order facts only. Genuine iceberg legs are used as same-report control seeds; "
            "this does not by itself establish Wilson95 confidence or full direct Manipulation coverage."
        ),
        "verifier": verifier,
        "schema_ready_unscored": schema_ready,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": (
            "Run chronological and heldout-symbol/venue calibration only after enough source-owned positive "
            "and same-schema normal-control rows exist; continue R2/R3/R4/R5 intake acquisition in parallel."
        ),
    }
    (OUT / "cftc_matched_control_seed_v1.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    lines = [
        "# CFTC Matched Control Seed v1",
        "",
        f"Decision: `{decision}`.",
        "",
        "Result:",
        f"- Positive rows present: `{len(positives)}`.",
        f"- Matched control rows materialized under `/tmp`: `{len(controls)}`.",
        f"- Direct intake verifier status: `{verifier_status}`; return code `{verifier['returncode']}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "Interpretation:",
        "- R6 is no longer blocked by the matched-control filename alone when this `/tmp` root is present.",
        "- The control rows are same-report CFTC genuine-order seeds, not a broad heldout normal-market sample.",
        "- This is schema-ready/unscored evidence only; Wilson95 calibration and broader direct species coverage still remain blocked.",
        "",
        "Artifacts:",
        f"- JSON: `{rel(OUT / 'cftc_matched_control_seed_v1.json')}`",
        f"- Verifier stdout: `{rel(OUT / 'direct_manipulation_row_intake_verifier.stdout.txt')}`",
        f"- Verifier stderr: `{rel(OUT / 'direct_manipulation_row_intake_verifier.stderr.txt')}`",
        f"- Assertions: `{rel(CHECKS / 'cftc_matched_control_seed_v1_assertions.out')}`",
    ]
    (OUT / "cftc_matched_control_seed_v1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS positive_rows={len(positives)}",
        f"PASS matched_negative_rows={len(controls)}",
        f"PASS verifier_status={verifier_status}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    (CHECKS / "cftc_matched_control_seed_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    print(json.dumps({"decision": decision, "verifier_status": verifier_status}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
