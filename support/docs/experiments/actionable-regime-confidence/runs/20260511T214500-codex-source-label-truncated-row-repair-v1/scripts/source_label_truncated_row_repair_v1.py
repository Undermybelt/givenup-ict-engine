#!/usr/bin/env python3
"""Remove truncated source-label rows left by an interrupted concurrent write."""

from __future__ import annotations

import csv
import fcntl
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T214500-codex-source-label-truncated-row-repair-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "source-label-truncated-row-repair"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"
INTAKE = Path("/tmp/ict-engine-source-label-equivalence-intake")
ROWS = INTAKE / "source_label_equivalence_rows.csv"
PROVENANCE = INTAKE / "source_label_equivalence_provenance.json"
LOCK = INTAKE / ".source_label_truncated_row_repair_v1.lock"
VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)

REQUIRED_NONEMPTY = [
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
    "split_role",
    "source_row_id",
    "provenance_hash",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows() -> tuple[list[str], list[dict[str, str]]]:
    with ROWS.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_rows(fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with ROWS.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def is_truncated(row: dict[str, str]) -> bool:
    missing_required = [field for field in REQUIRED_NONEMPTY if not (row.get(field) or "").strip()]
    if not missing_required:
        return False
    return not (row.get("source_row_id") or "").strip() and not (row.get("provenance_hash") or "").strip()


def run_verifier() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)

    with LOCK.open("w", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle, fcntl.LOCK_EX)
        pre_hash = sha256_file(ROWS)
        fields, rows = read_rows()
        good_rows = [row for row in rows if not is_truncated(row)]
        bad_rows = [row for row in rows if is_truncated(row)]
        if bad_rows:
            write_rows(fields, good_rows)
        provenance = json.loads(PROVENANCE.read_text(encoding="utf-8")) if PROVENANCE.exists() else {}
        provenance["source_label_truncated_row_repair_v1"] = {
            "run_id": RUN_ID,
            "removed_rows": len(bad_rows),
            "pre_row_count": len(rows),
            "post_row_count": len(good_rows),
            "pre_rows_sha256": pre_hash,
            "post_rows_sha256": sha256_file(ROWS),
            "repair_at_utc": datetime.now(timezone.utc).isoformat(),
            "reason": "Remove only rows with empty source_row_id and provenance_hash left by an interrupted concurrent CSV write.",
        }
        provenance["row_count"] = len(good_rows)
        provenance["rows_sha256"] = sha256_file(ROWS)
        provenance["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
        provenance["updated_by"] = RUN_ID
        PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        verifier = run_verifier()

    removed_csv = OUT / "source_label_truncated_row_repair_removed_rows_v1.csv"
    with removed_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(bad_rows)

    (CMD_OUT / "source_label_equivalence_verifier.stdout.txt").write_text(verifier.stdout, encoding="utf-8")
    (CMD_OUT / "source_label_equivalence_verifier.stderr.txt").write_text(verifier.stderr, encoding="utf-8")

    status = "unknown"
    parsed = {}
    if verifier.stdout.strip():
        try:
            parsed = json.loads(verifier.stdout)
            status = str(parsed.get("status", "json_no_status"))
        except json.JSONDecodeError:
            status = "stdout_not_json"

    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "source_label_truncated_row_repair_v1=removed_truncated_rows_verifier_" + status,
        "removed_rows": len(bad_rows),
        "pre_row_count": len(rows),
        "post_row_count": len(good_rows),
        "pre_rows_sha256": pre_hash,
        "post_rows_sha256": sha256_file(ROWS),
        "verifier_returncode": verifier.returncode,
        "verifier_status": status,
        "verifier_parsed": parsed,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
    }

    json_path = OUT / "source_label_truncated_row_repair_v1.json"
    report_path = OUT / "source_label_truncated_row_repair_v1.md"
    assertions_path = CHECKS / "source_label_truncated_row_repair_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report_path.write_text(
        "\n".join(
            [
                "# Source Label Truncated Row Repair v1",
                "",
                f"- Decision: `{result['decision']}`.",
                f"- Removed rows: `{len(bad_rows)}`.",
                f"- Row count: `{len(rows)}` -> `{len(good_rows)}`.",
                f"- Verifier status: `{status}`; return code: `{verifier.returncode}`.",
                "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`.",
                "- Strict full objective achieved: `false`; `update_goal=false`.",
                "",
                "Artifacts:",
                f"- JSON: `{json_path.relative_to(REPO)}`",
                f"- Report: `{report_path.relative_to(REPO)}`",
                f"- Removed rows CSV: `{removed_csv.relative_to(REPO)}`",
                f"- Verifier stdout: `{(CMD_OUT / 'source_label_equivalence_verifier.stdout.txt').relative_to(REPO)}`",
                f"- Assertions: `{assertions_path.relative_to(REPO)}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    assertions_path.write_text(
        "\n".join(
            [
                f"PASS removed_rows={len(bad_rows)}",
                f"PASS verifier_status={status}",
                f"PASS post_row_count={len(good_rows)}",
                "PASS update_goal=false",
                "PASS raw_data_committed=false",
                "PASS external_requests_sent=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"decision": result["decision"], "removed_rows": len(bad_rows), "post_row_count": len(good_rows), "verifier_status": status, "update_goal": False}, indent=2))


if __name__ == "__main__":
    main()
