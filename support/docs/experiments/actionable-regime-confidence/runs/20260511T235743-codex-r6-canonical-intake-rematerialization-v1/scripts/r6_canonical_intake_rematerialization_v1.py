#!/usr/bin/env python3
"""Rematerialize the canonical R6 direct Manipulation intake under a /tmp lock.

The source rows are copied from the latest versioned isolated reconstruction.
This script does not change repo runtime code and does not claim the full Board A
objective, because chronological/symbol/venue split gates remain blocked.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T235743-codex-r6-canonical-intake-rematerialization-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-canonical-intake-rematerialization"
COMMAND_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

SOURCE_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T234414-codex-r6-direct-intake-reconstruction-v55"
    / "r6-direct-intake-reconstruction-v55"
)
SOURCE_POSITIVE = SOURCE_ROOT / "positive_spoofing_layering_rows_v55.csv"
SOURCE_NEGATIVE = SOURCE_ROOT / "matched_negative_normal_activity_rows_v55.csv"
SOURCE_AUDIT = SOURCE_ROOT / "r6_direct_intake_reconstruction_v55.json"
SOURCE_SPLITS = SOURCE_ROOT / "r6_direct_intake_reconstruction_v55_split_metrics.csv"

CANONICAL_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
LOCK_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake.lock")
STAGING_ROOT = Path(f"/tmp/{RUN_ID}-staging")

VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_verifier(root: Path) -> dict[str, object]:
    proc = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(root)],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    stdout_path = COMMAND_OUT / "direct_manipulation_row_intake_verifier.stdout.txt"
    stderr_path = COMMAND_OUT / "direct_manipulation_row_intake_verifier.stderr.txt"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return {
        "returncode": proc.returncode,
        "payload": payload,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
    }


def split_gate_summary() -> dict[str, object]:
    rows = read_csv(SOURCE_SPLITS)
    failed = [row for row in rows if str(row.get("confidence_gate", "")).lower() != "true"]
    return {
        "split_metrics_path": rel(SOURCE_SPLITS),
        "split_rows": len(rows),
        "failed_split_rows": len(failed),
        "chronological_gate": all(
            str(row.get("confidence_gate", "")).lower() == "true"
            for row in rows
            if row.get("split_key") == "chronological"
        ),
        "heldout_symbol_gate": all(
            str(row.get("confidence_gate", "")).lower() == "true"
            for row in rows
            if row.get("split_key") == "symbol"
        ),
        "heldout_venue_gate": all(
            str(row.get("confidence_gate", "")).lower() == "true"
            for row in rows
            if row.get("split_key") == "venue_or_market_center"
        ),
    }


def same_file(path_a: Path, path_b: Path) -> bool:
    return path_a.exists() and path_b.exists() and sha256(path_a) == sha256(path_b)


def main() -> int:
    for path in [OUT, COMMAND_OUT, CHECKS]:
        path.mkdir(parents=True, exist_ok=True)

    board_hash_before = sha256(BOARD)
    source_audit = json.loads(SOURCE_AUDIT.read_text(encoding="utf-8"))
    source_positive_rows = read_csv(SOURCE_POSITIVE)
    source_negative_rows = read_csv(SOURCE_NEGATIVE)

    lock_acquired = False
    rematerialized = False
    preexisting_canonical = CANONICAL_ROOT.exists()
    preexisting_same_as_source = False
    lock_error = ""
    try:
        try:
            os.mkdir(LOCK_ROOT)
            lock_acquired = True
            (LOCK_ROOT / "owner.json").write_text(
                json.dumps(
                    {
                        "run_id": RUN_ID,
                        "created_at_utc": datetime.now(timezone.utc).isoformat(),
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
        except FileExistsError:
            lock_error = f"lock_exists:{LOCK_ROOT}"

        if not lock_acquired:
            raise RuntimeError(lock_error)

        if CANONICAL_ROOT.exists():
            preexisting_same_as_source = (
                same_file(CANONICAL_ROOT / "positive_spoofing_layering_rows.csv", SOURCE_POSITIVE)
                and same_file(CANONICAL_ROOT / "matched_negative_normal_activity_rows.csv", SOURCE_NEGATIVE)
            )
            if not preexisting_same_as_source:
                raise RuntimeError(
                    f"canonical intake already exists with different files: {CANONICAL_ROOT}"
                )
        else:
            if STAGING_ROOT.exists():
                shutil.rmtree(STAGING_ROOT)
            STAGING_ROOT.mkdir(parents=True)
            shutil.copy2(SOURCE_POSITIVE, STAGING_ROOT / "positive_spoofing_layering_rows.csv")
            shutil.copy2(SOURCE_NEGATIVE, STAGING_ROOT / "matched_negative_normal_activity_rows.csv")
            provenance = {
                "artifact_type": "r6_canonical_intake_rematerialization_v1",
                "run_id": RUN_ID,
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "source_reconstruction_json": rel(SOURCE_AUDIT),
                "source_positive_rows": rel(SOURCE_POSITIVE),
                "source_matched_negative_rows": rel(SOURCE_NEGATIVE),
                "source_positive_rows_sha256": sha256(SOURCE_POSITIVE),
                "source_matched_negative_rows_sha256": sha256(SOURCE_NEGATIVE),
                "source_reconstruction_gate_result": source_audit.get("gate_result"),
                "source_reconstruction_update_goal": source_audit.get("update_goal"),
                "policy": "canonical /tmp rematerialization from versioned rows under lock; no repo runtime code changes",
                "raw_data_committed": False,
                "thresholds_relaxed": False,
            }
            (STAGING_ROOT / "provenance_manifest.json").write_text(
                json.dumps(provenance, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            STAGING_ROOT.rename(CANONICAL_ROOT)
            rematerialized = True

        verifier = run_verifier(CANONICAL_ROOT)
    finally:
        if lock_acquired:
            shutil.rmtree(LOCK_ROOT, ignore_errors=True)

    split_summary = split_gate_summary()
    canonical_files = {
        "positive_rows": CANONICAL_ROOT / "positive_spoofing_layering_rows.csv",
        "matched_negative_rows": CANONICAL_ROOT / "matched_negative_normal_activity_rows.csv",
        "provenance_manifest": CANONICAL_ROOT / "provenance_manifest.json",
    }
    manifest_rows = [
        {
            "role": role,
            "path": str(path),
            "exists": path.exists(),
            "sha256": sha256(path) if path.exists() else "",
            "rows": len(read_csv(path)) if path.suffix == ".csv" and path.exists() else "",
        }
        for role, path in canonical_files.items()
    ]
    write_csv(OUT / "r6_canonical_intake_rematerialization_manifest_v1.csv", manifest_rows, ["role", "path", "exists", "sha256", "rows"])
    shutil.copy2(SOURCE_SPLITS, OUT / "r6_canonical_intake_rematerialization_split_metrics_v1.csv")

    payload = verifier["payload"]
    gate_result = (
        "r6_canonical_intake_rematerialization_v1="
        "canonical_schema_ready_pooled_wilson_passed_split_species_still_blocked"
    )
    summary = {
        "accepted_rows_added": 0,
        "board_sha256_at_start": board_hash_before,
        "canonical_root": str(CANONICAL_ROOT),
        "canonical_rematerialized": rematerialized,
        "direct_species_closed": False,
        "gate_result": gate_result,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "lock_acquired": lock_acquired,
        "lock_error": lock_error,
        "new_confidence_gate": payload.get("status") == "schema_ready_unscored",
        "next_action": (
            "Use the restored canonical intake to rerun or extend split calibration; "
            "continue sourcing non-spoofing direct Manipulation species because chronological, "
            "symbol, venue, and direct-species gates remain blocked."
        ),
        "preexisting_canonical": preexisting_canonical,
        "preexisting_same_as_source": preexisting_same_as_source,
        "raw_data_committed": False,
        "run_id": RUN_ID,
        "runtime_code_changed": False,
        "source_reconstruction": rel(SOURCE_AUDIT),
        "split_summary": split_summary,
        "strict_full_objective_achieved": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "update_goal": False,
        "verifier": verifier,
        "verifier_payload": payload,
    }
    json_path = OUT / "r6_canonical_intake_rematerialization_v1.json"
    report_path = OUT / "r6_canonical_intake_rematerialization_v1.md"
    assertions_path = CHECKS / "r6_canonical_intake_rematerialization_v1_assertions.out"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = [
        "# R6 Canonical Intake Rematerialization v1",
        "",
        f"- Run id: `{RUN_ID}`",
        f"- Canonical intake root: `{CANONICAL_ROOT}`",
        f"- Lock acquired: `{str(lock_acquired).lower()}`",
        f"- Rematerialized in this run: `{str(rematerialized).lower()}`",
        f"- Direct verifier status: `{payload.get('status')}`",
        f"- Canonical positives: `{payload.get('positive_rows')}`",
        f"- Canonical matched negatives: `{payload.get('matched_negative_rows')}`",
        f"- Matched groups: `{payload.get('matched_group_count')}`",
        f"- Source reconstruction: `{rel(SOURCE_AUDIT)}`",
        f"- Split gates: chronological `{str(split_summary['chronological_gate']).lower()}`, symbol `{str(split_summary['heldout_symbol_gate']).lower()}`, venue `{str(split_summary['heldout_venue_gate']).lower()}`",
        f"- Gate result: `{gate_result}`",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Artifacts",
        f"- JSON: `{rel(json_path)}`",
        f"- Manifest: `{rel(OUT / 'r6_canonical_intake_rematerialization_manifest_v1.csv')}`",
        f"- Split metrics: `{rel(OUT / 'r6_canonical_intake_rematerialization_split_metrics_v1.csv')}`",
        f"- Verifier stdout/stderr: `{verifier['stdout_path']}`, `{verifier['stderr_path']}`",
        f"- Assertions: `{rel(assertions_path)}`",
        "",
        "## Next",
        str(summary["next_action"]),
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        ("lock_acquired", lock_acquired),
        ("canonical_files_exist", all(path.exists() for path in canonical_files.values())),
        ("verifier_returncode_zero", verifier["returncode"] == 0),
        ("verifier_schema_ready", payload.get("status") == "schema_ready_unscored"),
        ("positive_rows_73", payload.get("positive_rows") == 73),
        ("matched_negative_rows_73", payload.get("matched_negative_rows") == 73),
        ("split_gates_still_blocked", not split_summary["chronological_gate"] and not split_summary["heldout_symbol_gate"] and not split_summary["heldout_venue_gate"]),
        ("strict_objective_still_false", summary["strict_full_objective_achieved"] is False),
    ]
    failed = []
    lines = []
    for name, ok in assertions:
        lines.append(f"{name}={'ok' if ok else 'fail'}")
        if not ok:
            failed.append(name)
    assertions_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if failed:
        raise SystemExit(f"assertions failed: {failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
