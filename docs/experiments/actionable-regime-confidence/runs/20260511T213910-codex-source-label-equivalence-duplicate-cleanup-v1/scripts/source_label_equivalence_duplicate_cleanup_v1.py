#!/usr/bin/env python3
"""Remove duplicate source-label equivalence rows from the shared /tmp intake."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T213910-codex-source-label-equivalence-duplicate-cleanup-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "source-label-equivalence-duplicate-cleanup"
CHECKS = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"
INTAKE_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
ROWS_PATH = INTAKE_ROOT / "source_label_equivalence_rows.csv"
PROVENANCE_PATH = INTAKE_ROOT / "source_label_equivalence_provenance.json"
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)
REQUIRED_FIELDS = [
    "package_id",
    "source_owner",
    "source_report_or_dataset",
    "source_pull_date",
    "market_family",
    "symbol",
    "source_symbol",
    "equivalence_policy",
    "event_species",
    "timestamp_or_date",
    "timeframe",
    "main_regime_v2_label",
    "direct_label",
    "matched_negative_group_id",
    "split_role",
    "source_row_id",
    "provenance_hash",
    "redaction_notes",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_rows() -> tuple[list[dict[str, str]], str, list[str]]:
    start_hash = sha256_file(ROWS_PATH)
    with ROWS_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        missing = [field for field in REQUIRED_FIELDS if field not in fields]
        if missing:
            raise ValueError(f"missing required columns: {missing}")
        return list(reader), start_hash, fields


def valid_row(row: dict[str, str]) -> bool:
    return all(row.get(field, "") for field in [
        "package_id",
        "source_owner",
        "source_report_or_dataset",
        "market_family",
        "symbol",
        "source_symbol",
        "equivalence_policy",
        "event_species",
        "timestamp_or_date",
        "timeframe",
        "main_regime_v2_label",
        "split_role",
        "source_row_id",
        "provenance_hash",
    ])


def dedupe(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    seen: set[tuple[str, str, str, str]] = set()
    kept: list[dict[str, str]] = []
    removed: list[dict[str, str]] = []
    for row in rows:
        if not valid_row(row):
            removed.append(row)
            continue
        key = (
            row.get("package_id", ""),
            row.get("source_owner", ""),
            row.get("source_row_id", ""),
            row.get("main_regime_v2_label", ""),
        )
        if key in seen:
            removed.append(row)
            continue
        seen.add(key)
        kept.append(row)
    return kept, removed


def write_rows(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def count_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    labels = Counter(row.get("main_regime_v2_label") or "" for row in rows)
    owners = Counter(row.get("source_owner") or "" for row in rows)
    packages = Counter(row.get("package_id") or "" for row in rows)
    return {
        "row_count": len(rows),
        "label_counts": dict(sorted(labels.items())),
        "source_owner_counts": dict(sorted(owners.items())),
        "package_counts": dict(sorted(packages.items())),
    }


def run_verifier() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(VERIFIER), "--intake-root", str(INTAKE_ROOT)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    stdout_path = CMD_DIR / "source_label_equivalence_verifier.stdout.txt"
    stderr_path = CMD_DIR / "source_label_equivalence_verifier.stderr.txt"
    exit_path = CMD_DIR / "source_label_equivalence_verifier.exit"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    parsed: dict[str, Any] = {}
    try:
        loaded = json.loads(proc.stdout)
        if isinstance(loaded, dict):
            parsed = loaded
    except json.JSONDecodeError:
        parsed = {"status": "unparsed", "stdout": proc.stdout[:1000]}
    return {"returncode": proc.returncode, "parsed": parsed}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)

    rows, start_hash, fields = load_rows()
    kept, removed = dedupe(rows)
    before_counts = count_rows(rows)
    after_counts = count_rows(kept)
    removed_counts = count_rows(removed)

    staged_rows = OUT / "source_label_equivalence_rows_deduped.csv"
    removed_csv = OUT / "source_label_equivalence_duplicate_rows_removed_v1.csv"
    write_rows(staged_rows, kept, fields)
    write_rows(removed_csv, removed, fields)

    provenance = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
    cleanup_entry = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dedupe_key": ["package_id", "source_owner", "source_row_id", "main_regime_v2_label"],
        "rows_before": len(rows),
        "rows_after": len(kept),
        "rows_removed": len(removed),
        "removed_counts": removed_counts,
        "raw_payload_committed_to_repo": False,
    }
    cleanups = list(provenance.get("cleanups", []))
    cleanups.append(cleanup_entry)
    provenance["cleanups"] = cleanups
    provenance["updated_by"] = RUN_ID
    provenance["updated_at_utc"] = cleanup_entry["created_at_utc"]
    provenance["row_count"] = len(kept)
    provenance["label_counts"] = after_counts["label_counts"]
    staged_prov = OUT / "source_label_equivalence_provenance_deduped.json"
    staged_prov.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if sha256_file(ROWS_PATH) != start_hash:
        raise RuntimeError("shared source-label rows changed during cleanup; aborting")
    tmp_rows = INTAKE_ROOT / f".source_label_equivalence_rows.csv.{RUN_ID}.tmp"
    tmp_prov = INTAKE_ROOT / f".source_label_equivalence_provenance.json.{RUN_ID}.tmp"
    shutil.copy2(staged_rows, tmp_rows)
    shutil.copy2(staged_prov, tmp_prov)
    tmp_rows.replace(ROWS_PATH)
    tmp_prov.replace(PROVENANCE_PATH)

    verifier = run_verifier()
    decision = "source_label_equivalence_duplicate_cleanup_v1=duplicates_or_malformed_rows_removed_schema_ready_unscored"
    result = {
        "run_id": RUN_ID,
        "created_at_utc": cleanup_entry["created_at_utc"],
        "decision": decision,
        "rows_before": len(rows),
        "rows_after": len(kept),
        "rows_removed": len(removed),
        "before_counts": before_counts,
        "after_counts": after_counts,
        "removed_counts": removed_counts,
        "start_rows_sha256": start_hash,
        "final_rows_sha256": sha256_file(ROWS_PATH),
        "verifier": verifier,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }

    json_path = OUT / "source_label_equivalence_duplicate_cleanup_v1.json"
    report_path = OUT / "source_label_equivalence_duplicate_cleanup_v1.md"
    assertions_path = CHECKS / "source_label_equivalence_duplicate_cleanup_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(
        "\n".join([
            "# Source Label Equivalence Duplicate Cleanup v1",
            "",
            f"- Decision: `{decision}`.",
            f"- Rows before: `{len(rows)}`.",
            f"- Duplicate rows removed: `{len(removed)}`.",
            f"- Rows after: `{len(kept)}`.",
            f"- After label counts: `{after_counts['label_counts']}`.",
            f"- Verifier status: `{verifier['parsed'].get('status')}`; return code `{verifier['returncode']}`.",
            "- Accepted confidence rows added: `0`; new confidence gate: `false`.",
            "- Strict full objective achieved: `false`; `update_goal=false`.",
            "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
            "",
            "Artifacts:",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Report: `{report_path.relative_to(REPO)}`",
            f"- Removed rows CSV: `{removed_csv.relative_to(REPO)}`",
            f"- Verifier stdout: `{(CMD_DIR / 'source_label_equivalence_verifier.stdout.txt').relative_to(REPO)}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        ]) + "\n",
        encoding="utf-8",
    )
    assertions_path.write_text(
        "\n".join([
            f"PASS decision={decision}",
            f"PASS rows_before={len(rows)}",
            f"PASS rows_removed={len(removed)}",
            f"PASS rows_after={len(kept)}",
            f"PASS verifier_status={verifier['parsed'].get('status')}",
            "PASS accepted_rows_added=0",
            "PASS new_confidence_gate=false",
            "PASS strict_full_objective_achieved=false",
            "PASS update_goal=false",
            "PASS raw_data_committed=false",
            "PASS external_requests_sent=false",
        ]) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "decision": decision,
        "rows_before": len(rows),
        "rows_removed": len(removed),
        "rows_after": len(kept),
        "verifier_status": verifier["parsed"].get("status"),
        "report": str(report_path.relative_to(REPO)),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
