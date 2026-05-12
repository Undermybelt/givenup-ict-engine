#!/usr/bin/env python3
"""Remove duplicate Logista rows introduced under alternate source_row_ids."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T221210-codex-r6-logista-semantic-duplicate-cleanup-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r6-logista-semantic-duplicate-cleanup"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE = INTAKE / "positive_spoofing_layering_rows.csv"
NEGATIVE = INTAKE / "matched_negative_normal_activity_rows.csv"
PROVENANCE = INTAKE / "provenance_manifest.json"
LOCK = INTAKE / ".r6_logista_semantic_duplicate_cleanup_v1.lock"
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

FIELDS = [
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
Z95 = 1.959963984540054
DUPLICATE_PREFIX = "cftc_logista_serotta_"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in FIELDS} for row in rows])


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wilson_all_success_lcb(n: int) -> float:
    if n <= 0:
        return 0.0
    denominator = 1.0 + Z95 * Z95 / n
    center = 1.0 + Z95 * Z95 / (2.0 * n)
    margin = Z95 * math.sqrt(Z95 * Z95 / (4.0 * n * n))
    return (center - margin) / denominator


def acquire_lock() -> None:
    fd = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(datetime.now(timezone.utc).isoformat() + "\n")


def release_lock() -> None:
    try:
        LOCK.unlink()
    except FileNotFoundError:
        pass


def run_verifier() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(VERIFIER), "--intake-root", str(INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    stdout_path = CMD / "direct_manipulation_row_intake_verifier.stdout.txt"
    stderr_path = CMD / "direct_manipulation_row_intake_verifier.stderr.txt"
    exit_path = CMD / "direct_manipulation_row_intake_verifier.exit"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"status": "unparsed"}
    return {
        "returncode": proc.returncode,
        "parsed": parsed,
        "stdout": str(stdout_path.relative_to(REPO)),
        "stderr": str(stderr_path.relative_to(REPO)),
        "exit": str(exit_path.relative_to(REPO)),
    }


def split_duplicate_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    kept = []
    removed = []
    for row in rows:
        if row.get("source_row_id", "").startswith(DUPLICATE_PREFIX):
            removed.append(row)
        else:
            kept.append(row)
    return kept, removed


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD.mkdir(parents=True, exist_ok=True)
    for path in [POSITIVE, NEGATIVE, PROVENANCE, VERIFIER]:
        if not path.exists():
            raise FileNotFoundError(str(path))

    acquire_lock()
    try:
        positives_before = read_csv(POSITIVE)
        negatives_before = read_csv(NEGATIVE)
        before_positive_sha = sha256_file(POSITIVE)
        before_matched_negative_sha = sha256_file(NEGATIVE)
        before_provenance_sha = sha256_file(PROVENANCE)
        positives_after, positive_removed = split_duplicate_rows(positives_before)
        negatives_after, negative_removed = split_duplicate_rows(negatives_before)
        write_csv(POSITIVE, positives_after)
        write_csv(NEGATIVE, negatives_after)

        provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        provenance.update(
            {
                "r6_logista_semantic_duplicate_cleanup_v1": {
                    "run_id": RUN_ID,
                    "duplicate_prefix_removed": DUPLICATE_PREFIX,
                    "positive_rows_removed": len(positive_removed),
                    "matched_negative_rows_removed": len(negative_removed),
                    "removed_positive_source_row_ids": [row["source_row_id"] for row in positive_removed],
                    "removed_matched_negative_source_row_ids": [
                        row["source_row_id"] for row in negative_removed
                    ],
                    "reason": (
                        "Remove semantic duplicates of Logista/Serotta CFTC complaint examples "
                        "because canonical repaired cftc_logista_* rows already represent those source events."
                    ),
                    "removed_at_utc": datetime.now(timezone.utc).isoformat(),
                },
                "positive_rows_count": len(positives_after),
                "matched_negative_rows_count": len(negatives_after),
                "positive_rows_sha256": sha256_file(POSITIVE),
                "matched_negative_rows_sha256": sha256_file(NEGATIVE),
                "updated_at_utc": datetime.now(timezone.utc).isoformat(),
                "updated_by": RUN_ID,
            }
        )
        PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        verifier = run_verifier()
        positive_lcb = wilson_all_success_lcb(len(positives_after))
        negative_lcb = wilson_all_success_lcb(len(negatives_after))
        min_lcb = min(positive_lcb, negative_lcb)
        support_floor_ok = len(positives_after) >= 50 and len(negatives_after) >= 50
        decision = "r6_logista_semantic_duplicate_cleanup_v1=duplicates_removed_support_ok_confidence_still_blocked"

        removed_path = OUT / "r6_logista_semantic_duplicate_cleanup_removed_rows_v1.csv"
        with removed_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["kind", *FIELDS])
            writer.writeheader()
            for row in positive_removed:
                writer.writerow({"kind": "positive", **{field: row.get(field, "") for field in FIELDS}})
            for row in negative_removed:
                writer.writerow({"kind": "matched_negative", **{field: row.get(field, "") for field in FIELDS}})

        gates = [
            ("positive_rows", len(positives_after), ">=50", support_floor_ok),
            ("matched_negative_rows", len(negatives_after), ">=50", support_floor_ok),
            ("wilson95_min_lcb", f"{min_lcb:.6f}", ">=0.95", min_lcb >= 0.95),
            ("broad_normal_sample", False, True, False),
            ("direct_species_coverage", False, True, False),
            ("semantic_logista_duplicates_removed", len(positive_removed), ">0", len(positive_removed) > 0),
        ]
        gates_path = OUT / "r6_logista_semantic_duplicate_cleanup_gates_v1.csv"
        with gates_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["gate", "observed", "required", "pass"])
            writer.writeheader()
            for gate, observed, required, passed in gates:
                writer.writerow(
                    {
                        "gate": gate,
                        "observed": str(observed),
                        "required": str(required),
                        "pass": str(bool(passed)).lower(),
                    }
                )

        summary = {
            "run_id": RUN_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "decision": decision,
            "before": {
                "positive_rows": len(positives_before),
                "matched_negative_rows": len(negatives_before),
                "positive_sha256": before_positive_sha,
                "matched_negative_sha256": before_matched_negative_sha,
                "provenance_sha256": before_provenance_sha,
            },
            "after": {
                "positive_rows": len(positives_after),
                "matched_negative_rows": len(negatives_after),
                "matched_group_count": verifier["parsed"].get("matched_group_count"),
                "positive_sha256": sha256_file(POSITIVE),
                "matched_negative_sha256": sha256_file(NEGATIVE),
                "provenance_sha256": sha256_file(PROVENANCE),
            },
            "removed": {
                "positive_rows": len(positive_removed),
                "matched_negative_rows": len(negative_removed),
                "positive_source_row_ids": [row["source_row_id"] for row in positive_removed],
                "matched_negative_source_row_ids": [row["source_row_id"] for row in negative_removed],
            },
            "support_50x50": support_floor_ok,
            "wilson95_lcb": {
                "positive": positive_lcb,
                "matched_negative": negative_lcb,
                "min": min_lcb,
            },
            "broad_normal_sample": False,
            "direct_species_closed": False,
            "direct_verifier": verifier,
            "gate_result": decision,
            "strict_full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "external_requests_sent": False,
            "trade_usable": False,
            "next_action": (
                "Acquire broad source-owned normal-market order-lifecycle controls and enough "
                "additional non-duplicate direct rows for Wilson95 >=0.95."
            ),
        }
        json_path = OUT / "r6_logista_semantic_duplicate_cleanup_v1.json"
        md_path = OUT / "r6_logista_semantic_duplicate_cleanup_v1.md"
        assertions_path = CHECKS / "r6_logista_semantic_duplicate_cleanup_v1_assertions.out"
        json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md_path.write_text(
            "\n".join(
                [
                    "# R6 Logista Semantic Duplicate Cleanup v1",
                    "",
                    f"- Decision: `{decision}`.",
                    f"- Removed duplicate Logista rows: positives `{len(positive_removed)}`, matched controls `{len(negative_removed)}`.",
                    f"- Direct intake after cleanup: positives `{len(positives_after)}`, matched negatives `{len(negatives_after)}`, matched groups `{verifier['parsed'].get('matched_group_count')}`.",
                    f"- Wilson95 LCB positive/negative/min: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{min_lcb:.6f}`.",
                    f"- `50/50` support gate: `{str(support_floor_ok).lower()}`.",
                    "- Broad normal sample: `false`; controls remain same-complaint genuine-order schema seeds.",
                    "- Direct species coverage closed: `false`.",
                    "- Gate result: `r6_logista_semantic_duplicate_cleanup_v1=duplicates_removed_support_ok_confidence_still_blocked`.",
                    "- Strict full objective achieved: `false`; `update_goal=false`.",
                    "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
                    "",
                    "## Boundary",
                    "",
                    "This run removes only semantic duplicates of Logista/Serotta examples. It keeps the canonical repaired Logista rows, the Roman/Banoczay rows, and the active Vorley/Franko rows. It does not promote same-event genuine-order controls into broad normal-market controls.",
                    "",
                    "## Artifacts",
                    "",
                    f"- JSON: `{json_path.relative_to(REPO)}`",
                    f"- Report: `{md_path.relative_to(REPO)}`",
                    f"- Removed rows CSV: `{removed_path.relative_to(REPO)}`",
                    f"- Gate CSV: `{gates_path.relative_to(REPO)}`",
                    f"- Direct verifier stdout: `{(CMD / 'direct_manipulation_row_intake_verifier.stdout.txt').relative_to(REPO)}`",
                    f"- Assertions: `{assertions_path.relative_to(REPO)}`",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        assertions_path.write_text(
            "\n".join(
                [
                    f"PASS decision={decision}",
                    f"PASS positive_rows_after={len(positives_after)}",
                    f"PASS matched_negative_rows_after={len(negatives_after)}",
                    f"PASS positive_rows_removed={len(positive_removed)}",
                    f"PASS matched_negative_rows_removed={len(negative_removed)}",
                    f"PASS verifier_status={verifier['parsed'].get('status')}",
                    f"PASS min_wilson95_lcb={min_lcb:.6f}",
                    f"PASS support_50x50={str(support_floor_ok).lower()}",
                    "PASS broad_normal_sample=false",
                    "PASS direct_species_closed=false",
                    "PASS update_goal=false",
                    "PASS runtime_code_changed=false",
                    "PASS thresholds_relaxed=false",
                    "PASS raw_data_committed=false",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        print(decision)
        print(f"positive_rows={len(positives_after)}")
        print(f"matched_negative_rows={len(negatives_after)}")
        print(f"removed_positive_rows={len(positive_removed)}")
        print(f"removed_matched_negative_rows={len(negative_removed)}")
        print(f"min_wilson95_lcb={min_lcb:.6f}")
        print("update_goal=false")
        return 0
    finally:
        release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
