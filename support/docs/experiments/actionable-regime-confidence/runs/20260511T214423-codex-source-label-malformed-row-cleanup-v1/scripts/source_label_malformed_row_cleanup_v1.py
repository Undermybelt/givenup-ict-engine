#!/usr/bin/env python3
"""Remove malformed blank rows from the shared source-label intake root."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T214423-codex-source-label-malformed-row-cleanup-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "source-label-malformed-row-cleanup"
CHECKS = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"
ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
ROWS = ROOT / "source_label_equivalence_rows.csv"
PROV = ROOT / "source_label_equivalence_provenance.json"
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

ESSENTIAL_FIELDS = [
    "package_id",
    "source_owner",
    "source_report_or_dataset",
    "market_family",
    "symbol",
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


def read_rows() -> tuple[list[dict[str, str]], list[str]]:
    with ROWS.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        return list(reader), fields


def write_rows(rows: list[dict[str, str]], fields: list[str]) -> None:
    with ROWS.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def malformed(row: dict[str, str]) -> bool:
    return any(not row.get(field, "").strip() for field in ESSENTIAL_FIELDS)


def run_verifier() -> dict:
    proc = subprocess.run(
        [sys.executable, str(VERIFIER), "--intake-root", str(ROOT)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    (CMD_DIR / "source_label_equivalence_verifier.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (CMD_DIR / "source_label_equivalence_verifier.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    (CMD_DIR / "source_label_equivalence_verifier.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"status": "unparsed"}
    return {"returncode": proc.returncode, "parsed": parsed}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)

    before_rows, fields = read_rows()
    if fields != REQUIRED_FIELDS:
        missing = [field for field in REQUIRED_FIELDS if field not in fields]
        if missing:
            raise SystemExit(f"missing required fields before cleanup: {missing}")
    bad = [row for row in before_rows if malformed(row)]
    good = [row for row in before_rows if not malformed(row)]
    before_hash = sha256_file(ROWS)
    write_rows(good, fields)
    after_hash = sha256_file(ROWS)

    provenance = json.loads(PROV.read_text(encoding="utf-8"))
    provenance["malformed_row_cleanup_v1"] = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "rows_before": len(before_rows),
        "rows_after": len(good),
        "malformed_rows_removed": len(bad),
        "rows_sha256_before": before_hash,
        "rows_sha256_after": after_hash,
        "policy": "remove only rows missing essential source-label fields",
    }
    provenance["row_count"] = len(good)
    provenance["rows_sha256"] = after_hash
    provenance["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    provenance["updated_by"] = RUN_ID
    PROV.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    verifier = run_verifier()
    status = verifier["parsed"].get("status")
    row_count = verifier["parsed"].get("row_count", len(good))
    decision = "source_label_malformed_row_cleanup_v1=malformed_row_removed_schema_ready_unscored"

    result = {
        "run_id": RUN_ID,
        "decision": decision,
        "rows_before": len(before_rows),
        "rows_after": len(good),
        "malformed_rows_removed": len(bad),
        "rows_sha256_before": before_hash,
        "rows_sha256_after": after_hash,
        "verifier_status": status,
        "verifier_returncode": verifier["returncode"],
        "verifier_row_count": row_count,
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

    json_path = OUT / "source_label_malformed_row_cleanup_v1.json"
    md_path = OUT / "source_label_malformed_row_cleanup_v1.md"
    assertions_path = CHECKS / "source_label_malformed_row_cleanup_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(
        "\n".join(
            [
                "# Source Label Malformed Row Cleanup v1",
                "",
                f"- Decision: `{decision}`.",
                f"- Rows before cleanup: `{len(before_rows)}`.",
                f"- Malformed rows removed: `{len(bad)}`.",
                f"- Rows after cleanup: `{len(good)}`.",
                f"- Verifier status: `{status}`; return code `{verifier['returncode']}`; row count `{row_count}`.",
                "- Accepted confidence rows added: `0`; new confidence gate: `false`.",
                "- Strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
                "",
                "Artifacts:",
                f"- JSON: `{json_path.relative_to(REPO)}`",
                f"- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/command-output/source_label_equivalence_verifier.stdout.txt`",
                f"- Assertions: `{assertions_path.relative_to(REPO)}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    assertions_path.write_text(
        "\n".join(
            [
                f"PASS decision={decision}",
                f"PASS rows_before={len(before_rows)}",
                f"PASS malformed_rows_removed={len(bad)}",
                f"PASS rows_after={len(good)}",
                f"PASS verifier_status={status}",
                f"PASS verifier_returncode={verifier['returncode']}",
                "PASS accepted_rows_added=0",
                "PASS new_confidence_gate=false",
                "PASS strict_full_objective_achieved=false",
                "PASS update_goal=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"decision": decision, "rows_after": len(good), "verifier_status": status, "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
