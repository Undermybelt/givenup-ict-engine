#!/usr/bin/env python3
"""Repair the shared source-label intake after concurrent extension/cleanup drift."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T214406-codex-source-label-intake-race-repair-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "source-label-intake-race-repair"
CHECKS = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"

SOURCE_LABEL_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
SOURCE_LABEL_ROWS = SOURCE_LABEL_ROOT / "source_label_equivalence_rows.csv"
SOURCE_LABEL_PROVENANCE = SOURCE_LABEL_ROOT / "source_label_equivalence_provenance.json"
SOURCE_PANEL_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
DIRECT_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
NATIVE_SUBHOUR_ROOT = Path("/tmp/ict-engine-native-subhour-source-labels")

SOURCE_LABEL_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)
SOURCE_PANEL_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)
DIRECT_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
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
ROOT_LABELS = {"Bear", "Bull", "Crisis", "Sideways"}
DIRECT_LABELS = {"", "normal_control", "positive"}
PRICE_PACKAGES = {
    "native_subhour_overlap_after_recency",
    "price_root_equivalence_crypto",
    "price_root_equivalence_fx_rates_commodities",
    "price_root_equivalence_us_index_futures",
}
DIRECT_PACKAGES = {"direct_manipulation_species_exports"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows() -> tuple[list[dict[str, str]], list[str], str]:
    start_hash = sha256_file(SOURCE_LABEL_ROWS)
    with SOURCE_LABEL_ROWS.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        missing = [field for field in REQUIRED_FIELDS if field not in fields]
        if missing:
            raise RuntimeError(f"missing required source-label columns: {missing}")
        return list(reader), fields, start_hash


def invalid_reasons(row: dict[str, str]) -> list[str]:
    if not any((row.get(field) or "").strip() for field in REQUIRED_FIELDS):
        return ["empty_or_truncated_row"]
    reasons: list[str] = []
    package = row.get("package_id", "")
    if package in PRICE_PACKAGES:
        if row.get("main_regime_v2_label") not in ROOT_LABELS:
            reasons.append("bad_main_regime_v2_label")
        if not row.get("equivalence_policy"):
            reasons.append("missing_equivalence_policy")
        if row.get("direct_label", "") not in DIRECT_LABELS:
            reasons.append("bad_direct_label")
    elif package in DIRECT_PACKAGES:
        if row.get("direct_label") not in {"normal_control", "positive"}:
            reasons.append("bad_direct_label")
        if not row.get("matched_negative_group_id"):
            reasons.append("missing_matched_negative_group_id")
    else:
        reasons.append("unknown_package_id")
    if not row.get("source_row_id"):
        reasons.append("missing_source_row_id")
    if not row.get("provenance_hash"):
        reasons.append("missing_provenance_hash")
    return reasons


def split_valid_invalid(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    valid: list[dict[str, str]] = []
    invalid: list[dict[str, str]] = []
    for line_number, row in enumerate(rows, start=2):
        reasons = invalid_reasons(row)
        if reasons:
            out_row = dict(row)
            out_row["line_number"] = str(line_number)
            out_row["repair_reason"] = ";".join(reasons)
            invalid.append(out_row)
        else:
            valid.append(row)
    return valid, invalid


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def row_counts(rows: list[dict[str, str]]) -> dict[str, Any]:
    labels = Counter(row.get("main_regime_v2_label") or "" for row in rows)
    packages = Counter(row.get("package_id") or "" for row in rows)
    owners = Counter(row.get("source_owner") or "" for row in rows)
    markets = Counter(row.get("market_family") or "" for row in rows)
    splits = Counter(row.get("split_role") or "" for row in rows)
    symbols = {row.get("symbol") for row in rows if row.get("symbol")}
    dates = [row.get("timestamp_or_date") for row in rows if row.get("timestamp_or_date")]
    return {
        "row_count": len(rows),
        "label_counts": dict(sorted(labels.items())),
        "package_counts": dict(sorted(packages.items())),
        "source_owner_counts": dict(sorted(owners.items())),
        "market_family_counts": dict(sorted(markets.items())),
        "split_counts": dict(sorted(splits.items())),
        "symbol_count": len(symbols),
        "date_min": min(dates) if dates else None,
        "date_max": max(dates) if dates else None,
    }


def run_verifier(name: str, verifier: Path, root: Path) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(verifier), "--intake-root", str(root)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    stdout_path = CMD_DIR / f"{name}.stdout.txt"
    stderr_path = CMD_DIR / f"{name}.stderr.txt"
    exit_path = CMD_DIR / f"{name}.exit"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    parsed: dict[str, Any]
    try:
        loaded = json.loads(proc.stdout)
        parsed = loaded if isinstance(loaded, dict) else {"status": "unparsed"}
    except json.JSONDecodeError:
        parsed = {"status": "unparsed", "stdout": proc.stdout[:1000]}
    return {
        "name": name,
        "returncode": proc.returncode,
        "parsed": parsed,
        "stdout": str(stdout_path.relative_to(REPO)),
        "stderr": str(stderr_path.relative_to(REPO)),
        "exit": str(exit_path.relative_to(REPO)),
    }


def wilson_lower_all_success(n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    denominator = 1.0 + z * z / n
    center = 1.0 + z * z / (2.0 * n)
    margin = z * math.sqrt(z * z / (4.0 * n * n))
    return (center - margin) / denominator


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)

    rows, fields, start_hash = read_rows()
    valid_rows, invalid_rows = split_valid_invalid(rows)
    before = row_counts(rows)
    after = row_counts(valid_rows)
    invalid_counts = row_counts(invalid_rows)

    staged_rows = OUT / "source_label_equivalence_rows_repaired.csv"
    invalid_csv = OUT / "source_label_equivalence_invalid_rows_removed_v1.csv"
    write_csv(staged_rows, valid_rows, fields)
    write_csv(invalid_csv, invalid_rows, ["line_number", "repair_reason", *fields])

    previous_provenance: dict[str, Any] = {}
    if SOURCE_LABEL_PROVENANCE.exists():
        previous_provenance = json.loads(SOURCE_LABEL_PROVENANCE.read_text(encoding="utf-8"))
    previous_provenance_path = OUT / "source_label_equivalence_previous_provenance_v1.json"
    previous_provenance_path.write_text(
        json.dumps(previous_provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    repaired_hash = sha256_file(staged_rows)
    now = datetime.now(timezone.utc).isoformat()
    repaired_provenance = {
        "run_id": RUN_ID,
        "created_at_utc": now,
        "updated_at_utc": now,
        "updated_by": RUN_ID,
        "repair_reason": "concurrent_us_panel_extension_and_duplicate_cleanup_left_provenance_out_of_sync_and_one_truncated_csv_row",
        "previous_provenance_path": str(previous_provenance_path.relative_to(REPO)),
        "raw_payload_committed_to_repo": False,
        "rows_path": str(SOURCE_LABEL_ROWS),
        "rows_sha256": repaired_hash,
        "row_count": after["row_count"],
        "label_counts": after["label_counts"],
        "package_counts": after["package_counts"],
        "source_owner_counts": after["source_owner_counts"],
        "market_family_counts": after["market_family_counts"],
        "split_counts": after["split_counts"],
        "symbol_count": after["symbol_count"],
        "date_min": after["date_min"],
        "date_max": after["date_max"],
        "invalid_rows_removed": len(invalid_rows),
        "limitations": [
            "schema readiness is not Board A confidence acceptance",
            "daily source-label equivalence rows do not satisfy native sub-hour validation",
            "R5 source-panel recency extension remains a separate missing intake root",
            "R6 direct Manipulation remains a separate direct-event root",
        ],
    }
    staged_provenance = OUT / "source_label_equivalence_provenance_repaired.json"
    staged_provenance.write_text(
        json.dumps(repaired_provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if sha256_file(SOURCE_LABEL_ROWS) != start_hash:
        raise RuntimeError("source-label rows changed during race repair; aborting before replace")
    tmp_rows = SOURCE_LABEL_ROOT / f".source_label_equivalence_rows.csv.{RUN_ID}.tmp"
    tmp_provenance = SOURCE_LABEL_ROOT / f".source_label_equivalence_provenance.json.{RUN_ID}.tmp"
    shutil.copy2(staged_rows, tmp_rows)
    shutil.copy2(staged_provenance, tmp_provenance)
    tmp_rows.replace(SOURCE_LABEL_ROWS)
    tmp_provenance.replace(SOURCE_LABEL_PROVENANCE)

    source_label_verifier = run_verifier("source_label_equivalence_verifier", SOURCE_LABEL_VERIFIER, SOURCE_LABEL_ROOT)
    source_panel_verifier = run_verifier("source_panel_recency_verifier", SOURCE_PANEL_VERIFIER, SOURCE_PANEL_ROOT)
    direct_verifier = run_verifier("direct_manipulation_verifier", DIRECT_VERIFIER, DIRECT_ROOT)
    direct = direct_verifier["parsed"]
    positive_rows = int(direct.get("positive_rows") or 0)
    negative_rows = int(direct.get("matched_negative_rows") or 0)
    wilson_min_lcb = min(wilson_lower_all_success(positive_rows), wilson_lower_all_success(negative_rows))

    decision = "source_label_intake_race_repair_v1=malformed_row_removed_schema_ready_unscored_strict_blocked"
    result = {
        "run_id": RUN_ID,
        "created_at_utc": now,
        "decision": decision,
        "rows_before": before,
        "rows_after": after,
        "invalid_rows_removed": len(invalid_rows),
        "invalid_counts": invalid_counts,
        "start_rows_sha256": start_hash,
        "final_rows_sha256": sha256_file(SOURCE_LABEL_ROWS),
        "source_label_verifier": source_label_verifier,
        "source_panel_recency_verifier": source_panel_verifier,
        "direct_manipulation_verifier": direct_verifier,
        "native_subhour_root_exists": NATIVE_SUBHOUR_ROOT.exists(),
        "r6_wilson95_min_lcb": round(wilson_min_lcb, 6),
        "r6_support_gate": positive_rows >= 50 and negative_rows >= 50,
        "r6_wilson95_gate": wilson_min_lcb >= 0.95,
        "r6_broad_normal_sample": False,
        "r6_direct_species_closed": False,
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

    json_path = OUT / "source_label_intake_race_repair_v1.json"
    report_path = OUT / "source_label_intake_race_repair_v1.md"
    assertions_path = CHECKS / "source_label_intake_race_repair_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(
        "\n".join([
            "# Source Label Intake Race Repair v1",
            "",
            f"- Decision: `{decision}`.",
            f"- Rows before repair: `{before['row_count']}`.",
            f"- Invalid/truncated rows removed: `{len(invalid_rows)}`.",
            f"- Rows after repair: `{after['row_count']}`.",
            f"- Repaired label counts: `{after['label_counts']}`.",
            f"- Repaired split counts: `{after['split_counts']}`.",
            f"- Source-label verifier: `{source_label_verifier['parsed'].get('status')}`; return code `{source_label_verifier['returncode']}`.",
            f"- Source-panel recency verifier: `{source_panel_verifier['parsed'].get('status')}` / `{source_panel_verifier['parsed'].get('reason')}`.",
            f"- Native sub-hour root exists: `{NATIVE_SUBHOUR_ROOT.exists()}`.",
            f"- Direct R6 verifier: `{direct.get('status')}` with positives `{positive_rows}`, matched negatives `{negative_rows}`, matched groups `{direct.get('matched_group_count')}`, Wilson95 min LCB `{wilson_min_lcb:.6f}`.",
            "- R6 support/Wilson/broad-normal/direct-species gates remain blocked.",
            "- Accepted confidence rows added: `0`; new confidence gate: `false`.",
            "- Strict full objective achieved: `false`; `update_goal=false`.",
            "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
            "",
            "Artifacts:",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Report: `{report_path.relative_to(REPO)}`",
            f"- Invalid rows CSV: `{invalid_csv.relative_to(REPO)}`",
            f"- Repaired provenance copy: `{staged_provenance.relative_to(REPO)}`",
            f"- Previous provenance copy: `{previous_provenance_path.relative_to(REPO)}`",
            f"- Source-label verifier stdout: `{Path(source_label_verifier['stdout'])}`",
            f"- Source-panel verifier stdout: `{Path(source_panel_verifier['stdout'])}`",
            f"- Direct verifier stdout: `{Path(direct_verifier['stdout'])}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        ]) + "\n",
        encoding="utf-8",
    )
    assertions_path.write_text(
        "\n".join([
            f"PASS decision={decision}",
            f"PASS rows_before={before['row_count']}",
            f"PASS invalid_rows_removed={len(invalid_rows)}",
            f"PASS rows_after={after['row_count']}",
            f"PASS source_label_verifier_status={source_label_verifier['parsed'].get('status')}",
            f"PASS source_label_verifier_returncode={source_label_verifier['returncode']}",
            f"PASS source_panel_recency_status={source_panel_verifier['parsed'].get('status')}",
            f"PASS direct_verifier_status={direct.get('status')}",
            f"PASS r6_positive_rows={positive_rows}",
            f"PASS r6_matched_negative_rows={negative_rows}",
            f"PASS r6_wilson95_min_lcb={wilson_min_lcb:.6f}",
            "PASS strict_full_objective_achieved=false",
            "PASS update_goal=false",
            "PASS raw_data_committed=false",
            "PASS external_requests_sent=false",
        ]) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "decision": decision,
        "rows_before": before["row_count"],
        "invalid_rows_removed": len(invalid_rows),
        "rows_after": after["row_count"],
        "source_label_verifier_status": source_label_verifier["parsed"].get("status"),
        "source_panel_recency_status": source_panel_verifier["parsed"].get("status"),
        "direct_positive_rows": positive_rows,
        "direct_matched_negative_rows": negative_rows,
        "r6_wilson95_min_lcb": round(wilson_min_lcb, 6),
        "strict_full_objective_achieved": False,
        "report": str(report_path.relative_to(REPO)),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
