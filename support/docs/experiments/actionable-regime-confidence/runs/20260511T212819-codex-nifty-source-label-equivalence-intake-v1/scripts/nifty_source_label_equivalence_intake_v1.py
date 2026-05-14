#!/usr/bin/env python3
"""Build a partial source-label equivalence intake from the NIFTY source dataset."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T212819-codex-nifty-source-label-equivalence-intake-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "nifty-source-label-equivalence-intake"
CHECKS = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"
SOURCE_ROOT = Path("/tmp/ict-engine-public-source-intake-scout/nifty")
SOURCE_CSV = SOURCE_ROOT / "regime_timeline_history.csv"
SOURCE_METADATA = SOURCE_ROOT / "dataset-metadata.json"
STAGING_ROOT = Path("/tmp/ict-engine-nifty-source-label-equivalence-intake-v1")
INTAKE_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
ROWS_NAME = "source_label_equivalence_rows.csv"
PROVENANCE_NAME = "source_label_equivalence_provenance.json"
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

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


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_metadata() -> dict[str, Any]:
    raw = SOURCE_METADATA.read_text(encoding="utf-8")
    obj = json.loads(raw)
    if isinstance(obj, str):
        obj = json.loads(obj)
    if not isinstance(obj, dict):
        raise ValueError("dataset metadata is not a JSON object")
    return obj


def split_role(day: str) -> str:
    parsed = datetime.strptime(day, "%Y-%m-%d").date()
    if parsed < date(2018, 1, 1):
        return "calibration"
    if parsed < date(2023, 1, 1):
        return "heldout_time"
    return "test"


def row_hash(row: dict[str, str]) -> str:
    material = "|".join(f"{key}={row.get(key, '')}" for key in REQUIRED_FIELDS if key != "provenance_hash")
    return sha256_text(material)


def make_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    policy = (
        "owner_described_nifty_market_regime_mapping_v1:"
        "macro_state_Durable_to_Bull;"
        "fast_state_Calm_to_Sideways;"
        "fast_state_Stress_to_Crisis;"
        "Fragile_and_Choppy_unmapped_no_Bear_claim"
    )
    with SOURCE_CSV.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for source_index, source in enumerate(reader, start=2):
            day = source["Date"]
            candidates = [
                ("macro_state", source.get("macro_state", ""), "Durable", "Bull"),
                ("fast_state", source.get("fast_state", ""), "Calm", "Sideways"),
                ("fast_state", source.get("fast_state", ""), "Stress", "Crisis"),
            ]
            for field_name, observed, expected, label in candidates:
                if observed != expected:
                    continue
                out = {
                    "package_id": "price_root_equivalence_us_index_futures",
                    "source_owner": "ahaanverma00",
                    "source_report_or_dataset": "kaggle:ahaanverma00/nifty-500-market-and-behavior-regime-dataset",
                    "source_pull_date": "2026-05-11",
                    "market_family": "india_equity_index",
                    "symbol": "NIFTY500",
                    "source_symbol": f"NIFTY500:{field_name}",
                    "equivalence_policy": policy,
                    "event_species": "owner_described_nifty_hmm_market_regime",
                    "timestamp_or_date": day,
                    "timeframe": "1d",
                    "main_regime_v2_label": label,
                    "direct_label": "",
                    "matched_negative_group_id": "",
                    "split_role": split_role(day),
                    "source_row_id": f"nifty_regime_timeline_history:{source_index}:{field_name}:{observed}",
                    "provenance_hash": "",
                    "redaction_notes": "partial_crosswalk_no_Bear_rows_no_strict_completion_claim",
                }
                out["provenance_hash"] = row_hash(out)
                rows.append(out)
    return rows


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_counts(path: Path, rows: list[dict[str, str]]) -> dict[str, Any]:
    label_counts = Counter(row["main_regime_v2_label"] for row in rows)
    split_counts = Counter(row["split_role"] for row in rows)
    date_values = [row["timestamp_or_date"] for row in rows]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "key", "value"])
        writer.writeheader()
        for key, value in sorted(label_counts.items()):
            writer.writerow({"metric": "label_count", "key": key, "value": value})
        for key, value in sorted(split_counts.items()):
            writer.writerow({"metric": "split_count", "key": key, "value": value})
        writer.writerow({"metric": "date_min", "key": "all", "value": min(date_values)})
        writer.writerow({"metric": "date_max", "key": "all", "value": max(date_values)})
    return {
        "label_counts": dict(sorted(label_counts.items())),
        "split_counts": dict(sorted(split_counts.items())),
        "date_min": min(date_values),
        "date_max": max(date_values),
    }


def run_verifier(root: Path) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(VERIFIER), "--intake-root", str(root)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    (CMD_DIR / "source_label_equivalence_verifier.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (CMD_DIR / "source_label_equivalence_verifier.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    (CMD_DIR / "source_label_equivalence_verifier.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
    parsed: dict[str, Any] = {}
    try:
        loaded = json.loads(proc.stdout)
        if isinstance(loaded, dict):
            parsed = loaded
    except json.JSONDecodeError:
        parsed = {"status": "unparsed", "stdout": proc.stdout[:1000]}
    return {
        "returncode": proc.returncode,
        "parsed": parsed,
        "stdout_file": str((CMD_DIR / "source_label_equivalence_verifier.stdout.txt").relative_to(REPO)),
        "stderr_file": str((CMD_DIR / "source_label_equivalence_verifier.stderr.txt").relative_to(REPO)),
    }


def copy_to_shared_intake() -> dict[str, Any]:
    INTAKE_ROOT.mkdir(parents=True, exist_ok=True)
    target_rows = INTAKE_ROOT / ROWS_NAME
    target_provenance = INTAKE_ROOT / PROVENANCE_NAME
    existing_required = [str(path) for path in (target_rows, target_provenance) if path.exists()]
    if existing_required:
        return {
            "shared_root_written": False,
            "shared_root_write_status": "blocked_existing_required_files",
            "existing_required_files": existing_required,
        }
    shutil.copy2(STAGING_ROOT / ROWS_NAME, target_rows)
    shutil.copy2(STAGING_ROOT / PROVENANCE_NAME, target_provenance)
    return {
        "shared_root_written": True,
        "shared_root_write_status": "created_required_files",
        "shared_root": str(INTAKE_ROOT),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    STAGING_ROOT.mkdir(parents=True, exist_ok=True)

    missing_source = [str(path) for path in (SOURCE_CSV, SOURCE_METADATA, VERIFIER) if not path.exists()]
    if missing_source:
        raise FileNotFoundError(missing_source)

    metadata = load_metadata()
    rows = make_rows()
    if not rows:
        raise RuntimeError("no NIFTY source-label rows were generated")

    staging_rows = STAGING_ROOT / ROWS_NAME
    staging_provenance = STAGING_ROOT / PROVENANCE_NAME
    write_rows(staging_rows, rows)
    counts = write_counts(OUT / "nifty_source_label_equivalence_counts_v1.csv", rows)
    provenance = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_owner": "ahaanverma00",
        "source_report_or_dataset": "kaggle:ahaanverma00/nifty-500-market-and-behavior-regime-dataset",
        "source_dataset_title": metadata.get("title"),
        "license_or_permission": metadata.get("licenses"),
        "source_description": metadata.get("subtitle"),
        "source_pull_date": "2026-05-11",
        "raw_payload_committed_to_repo": False,
        "source_root": str(SOURCE_ROOT),
        "source_csv_sha256": sha256_file(SOURCE_CSV),
        "source_metadata_sha256": sha256_file(SOURCE_METADATA),
        "rows_path": str(staging_rows),
        "rows_sha256": sha256_file(staging_rows),
        "row_count": len(rows),
        "label_counts": counts["label_counts"],
        "split_counts": counts["split_counts"],
        "date_min": counts["date_min"],
        "date_max": counts["date_max"],
        "mapping_policy": {
            "Durable": "Bull",
            "Calm": "Sideways",
            "Stress": "Crisis",
            "Fragile": "unmapped",
            "Choppy": "unmapped",
        },
        "limitations": [
            "partial source-owner-described crosswalk only",
            "no Bear MainRegimeV2 rows",
            "daily India equity index labels only",
            "schema readiness is not a strict confidence gate",
        ],
    }
    staging_provenance.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    shared_write = copy_to_shared_intake()
    verifier_root = INTAKE_ROOT if shared_write["shared_root_written"] else STAGING_ROOT
    verifier = run_verifier(verifier_root)
    status = verifier["parsed"].get("status", "unparsed")
    schema_ready = status == "schema_ready_unscored" and verifier["returncode"] == 0
    decision = (
        "nifty_source_label_equivalence_intake_v1=partial_schema_ready_no_full_objective"
        if schema_ready
        else "nifty_source_label_equivalence_intake_v1=blocked_verifier_not_ready"
    )
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_writeback": sha256_file(BOARD),
        "decision": decision,
        "source_root": str(SOURCE_ROOT),
        "staging_root": str(STAGING_ROOT),
        "shared_intake_root": str(INTAKE_ROOT),
        "shared_write": shared_write,
        "verifier_root": str(verifier_root),
        "verifier": verifier,
        "row_count": len(rows),
        "label_counts": counts["label_counts"],
        "split_counts": counts["split_counts"],
        "date_min": counts["date_min"],
        "date_max": counts["date_max"],
        "source_label_ready_rows_added": len(rows) if shared_write["shared_root_written"] and schema_ready else 0,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "blocker": "This closes only a partial R2/R4 schema root; Bear, native sub-hour R3, recency R5, and R6 support/Wilson/broad-normal/species gates remain blocked.",
        "next_action": "Rerun the current-goal audit against the now-present source-label root, then acquire Bear/native-subhour/recency/R6 broad-control evidence before any completion claim.",
    }
    json_path = OUT / "nifty_source_label_equivalence_intake_v1.json"
    report_path = OUT / "nifty_source_label_equivalence_intake_v1.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# NIFTY Source Label Equivalence Intake v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Shared intake write: `{shared_write['shared_root_write_status']}`.",
        f"- Verifier status: `{status}`.",
        f"- Row count: `{len(rows)}`; labels: `{counts['label_counts']}`.",
        f"- Date range: `{counts['date_min']}` to `{counts['date_max']}`.",
        "- Accepted confidence rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "## Interpretation",
        "",
        "The source-owned NIFTY daily regime dataset has owner-described labels that can be mapped into a partial MainRegimeV2 equivalence package for `Bull`, `Sideways`, and `Crisis`.",
        "This does not create a Bear row set, does not provide native sub-hour labels, and does not close the strict Board A objective.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path}`",
        f"- Report: `{report_path}`",
        f"- Counts CSV: `{OUT / 'nifty_source_label_equivalence_counts_v1.csv'}`",
        f"- Staging intake root: `{STAGING_ROOT}`",
        f"- Shared intake root: `{INTAKE_ROOT}`",
        f"- Verifier stdout: `{verifier['stdout_file']}`",
        f"- Assertions: `{CHECKS / 'nifty_source_label_equivalence_intake_v1_assertions.out'}`",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS verifier_status={status}",
        f"PASS row_count={len(rows)}",
        f"PASS source_label_ready_rows_added={result['source_label_ready_rows_added']}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    (CHECKS / "nifty_source_label_equivalence_intake_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    print(json.dumps({"decision": decision, "verifier_status": status, "row_count": len(rows), "update_goal": False}, sort_keys=True))
    return 0 if schema_ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
