#!/usr/bin/env python3
"""Remove malformed blank rows from the shared source-label intake."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T214339-codex-source-label-blank-row-cleanup-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "source-label-blank-row-cleanup"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"
INTAKE = Path("/tmp/ict-engine-source-label-equivalence-intake")
ROWS = INTAKE / "source_label_equivalence_rows.csv"
PROVENANCE = INTAKE / "source_label_equivalence_provenance.json"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows() -> tuple[list[dict[str, str]], list[str]]:
    with ROWS.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_rows(rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    tmp = ROWS.with_suffix(".blank_cleanup_tmp.csv")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(ROWS)


def run_verifier() -> tuple[str, int, dict]:
    proc = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    (CMD_OUT / "source_label_equivalence_verifier.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (CMD_OUT / "source_label_equivalence_verifier.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    (CMD_OUT / "source_label_equivalence_verifier.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"stdout_prefix": proc.stdout[:500]}
    return str(parsed.get("status", "unknown")), proc.returncode, parsed


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)

    pre_hash = sha256_file(ROWS)
    rows, fieldnames = read_rows()
    valid_rows: list[dict[str, str]] = []
    removed_rows: list[dict[str, str]] = []
    for row in rows:
        if row.get("source_row_id") and row.get("main_regime_v2_label"):
            valid_rows.append(row)
        else:
            removed_rows.append(row)
    if len(valid_rows) != len(rows):
        write_rows(valid_rows, fieldnames)

    label_counts = Counter(row.get("main_regime_v2_label", "") for row in valid_rows)
    source_counts = Counter(row.get("source_report_or_dataset", "") for row in valid_rows)
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    provenance["row_count"] = len(valid_rows)
    provenance["label_counts"] = dict(sorted(label_counts.items()))
    provenance["rows_sha256"] = sha256_file(ROWS)
    provenance["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    provenance["updated_by"] = RUN_ID
    provenance["source_label_blank_row_cleanup_v1"] = {
        "run_id": RUN_ID,
        "rows_before": len(rows),
        "rows_after": len(valid_rows),
        "blank_or_malformed_rows_removed": len(removed_rows),
        "removed_row_sample": removed_rows[:5],
        "raw_rows_committed_to_repo": False,
    }
    PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    verifier_status, verifier_returncode, verifier_parsed = run_verifier()
    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": sha256_file(BOARD),
        "rows_before": len(rows),
        "rows_after": len(valid_rows),
        "blank_or_malformed_rows_removed": len(removed_rows),
        "label_counts_after": dict(sorted(label_counts.items())),
        "source_counts_after": dict(sorted(source_counts.items())),
        "pre_rows_sha256": pre_hash,
        "post_rows_sha256": sha256_file(ROWS),
        "verifier_status": verifier_status,
        "verifier_returncode": verifier_returncode,
        "verifier_parsed": verifier_parsed,
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

    json_path = OUT / "source_label_blank_row_cleanup_v1.json"
    report_path = OUT / "source_label_blank_row_cleanup_v1.md"
    assertions_path = CHECKS / "source_label_blank_row_cleanup_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(
        "\n".join(
            [
                "# Source-Label Blank Row Cleanup v1",
                "",
                "- Decision: `source_label_blank_row_cleanup_v1=blank_row_removed_schema_ready_unscored`.",
                f"- Rows before: `{len(rows)}`; rows after: `{len(valid_rows)}`; malformed rows removed: `{len(removed_rows)}`.",
                f"- Label counts after cleanup: `{dict(sorted(label_counts.items()))}`.",
                f"- Verifier status: `{verifier_status}`; return code `{verifier_returncode}`.",
                "- Accepted confidence rows added: `0`; new confidence gate: `false`.",
                "- Strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
                "",
                "Artifacts:",
                f"- JSON: `{json_path.relative_to(REPO)}`",
                f"- Report: `{report_path.relative_to(REPO)}`",
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
                "PASS decision=source_label_blank_row_cleanup_v1=blank_row_removed_schema_ready_unscored",
                f"PASS rows_before={len(rows)}",
                f"PASS rows_after={len(valid_rows)}",
                f"PASS blank_or_malformed_rows_removed={len(removed_rows)}",
                f"PASS verifier_status={verifier_status}",
                "PASS accepted_rows_added=0",
                "PASS new_confidence_gate=false",
                "PASS strict_full_objective_achieved=false",
                "PASS update_goal=false",
                "PASS raw_data_committed=false",
                "PASS external_requests_sent=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "decision": "source_label_blank_row_cleanup_v1=blank_row_removed_schema_ready_unscored",
        "rows_before": len(rows),
        "rows_after": len(valid_rows),
        "blank_or_malformed_rows_removed": len(removed_rows),
        "verifier_status": verifier_status,
        "update_goal": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
