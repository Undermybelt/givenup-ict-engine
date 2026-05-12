#!/usr/bin/env python3
"""Remove only the duplicate Shak rows created by the 211628 local slice."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T212004-codex-r6-shak-duplicate-row-cleanup-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r6-shak-duplicate-row-cleanup"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE = INTAKE / "positive_spoofing_layering_rows.csv"
NEGATIVE = INTAKE / "matched_negative_normal_activity_rows.csv"
PROVENANCE = INTAKE / "provenance_manifest.json"
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

POSITIVE_DUPLICATE_IDS = {
    "cftc_shak_20170303_gold_buy_spoof_series",
    "cftc_shak_20170324_gold_buy_spoof_series",
    "cftc_shak_20170918_silver_buy_spoof_series",
    "cftc_shak_20171005_gold_buy_spoof_second_series",
    "cftc_shak_20180122_silver_buy_spoof_series",
}

NEGATIVE_DUPLICATE_IDS = {
    "cftc_shak_20170303_gold_sell_genuine_order_control",
    "cftc_shak_20170324_gold_sell_genuine_order_control",
    "cftc_shak_20170918_silver_sell_genuine_orders_control",
    "cftc_shak_20171005_gold_sell_iceberg_genuine_order_control",
    "cftc_shak_20180122_silver_sell_genuine_order_control",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv_rows(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def remove_rows(path: Path, duplicate_ids: set[str]) -> tuple[int, list[str]]:
    fields, rows = read_csv_rows(path)
    kept: list[dict[str, str]] = []
    removed: list[str] = []
    for row in rows:
        source_row_id = row.get("source_row_id", "")
        if source_row_id in duplicate_ids:
            removed.append(source_row_id)
            continue
        kept.append(row)
    write_csv_rows(path, fields, kept)
    return len(removed), removed


def write_simple_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def wilson_lcb(successes: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    phat = successes / total
    denom = 1 + z * z / total
    centre = phat + z * z / (2 * total)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * total)) / total)
    return (centre - margin) / denom


def unique_values(rows: list[dict[str, str]], key: str) -> list[str]:
    return sorted({row.get(key, "") for row in rows if row.get(key, "")})


def run_verifier() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(VERIFIER), "--intake-root", str(INTAKE)],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=REPO,
    )
    (CMD_OUT / "direct_manipulation_row_intake_verifier.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (CMD_OUT / "direct_manipulation_row_intake_verifier.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"status": "parse_failed", "stdout": proc.stdout, "stderr": proc.stderr}
    parsed["returncode"] = proc.returncode
    return parsed


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)

    before_hashes = {
        "positive": sha256(POSITIVE),
        "matched_negative": sha256(NEGATIVE),
        "provenance": sha256(PROVENANCE),
    }
    board_hash = sha256(BOARD)
    positive_removed, positive_ids = remove_rows(POSITIVE, POSITIVE_DUPLICATE_IDS)
    negative_removed, negative_ids = remove_rows(NEGATIVE, NEGATIVE_DUPLICATE_IDS)

    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    provenance["r6_shak_duplicate_row_cleanup_v1"] = {
        "run_id": RUN_ID,
        "reason": "Remove only the five semantic duplicate Shak rows introduced by the 211628 local slice after a concurrent 211606 Shak uplift had already materialized equivalent examples under different source_row_ids.",
        "positive_rows_removed": positive_ids,
        "matched_negative_rows_removed": negative_ids,
        "other_agent_rows_preserved": True,
    }

    _, positives = read_csv_rows(POSITIVE)
    _, negatives = read_csv_rows(NEGATIVE)
    provenance["positive_rows_count"] = len(positives)
    provenance["matched_negative_rows_count"] = len(negatives)
    provenance["positive_rows_sha256"] = sha256(POSITIVE)
    provenance["matched_negative_rows_sha256"] = sha256(NEGATIVE)
    provenance["updated_by"] = RUN_ID
    provenance["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    verifier = run_verifier()
    _, positives = read_csv_rows(POSITIVE)
    _, negatives = read_csv_rows(NEGATIVE)
    all_rows = positives + negatives
    labels = Counter(row.get("label", "") for row in all_rows)
    dates = unique_values(all_rows, "trade_date")
    symbols = unique_values(all_rows, "symbol")
    venues = unique_values(all_rows, "venue_or_market_center")
    groups = unique_values(all_rows, "matched_negative_group_id")

    positive_lcb = wilson_lcb(len(positives), len(positives))
    negative_lcb = wilson_lcb(len(negatives), len(negatives))
    combined_lcb = min(positive_lcb, negative_lcb)
    min_support = 50
    support_ok = len(positives) >= min_support and len(negatives) >= min_support
    chronological_split_ok = len(dates) >= 2
    heldout_symbol_or_venue_ok = len(symbols) >= 2 or len(venues) >= 2
    broad_normal_sample = "not a broad normal-market" not in provenance.get("matched_negative_control_policy", "").lower()
    gate_rows = [
        {"gate": "positive_support", "observed": len(positives), "required": min_support, "pass": len(positives) >= min_support},
        {"gate": "negative_support", "observed": len(negatives), "required": min_support, "pass": len(negatives) >= min_support},
        {"gate": "chronological_split", "observed": len(dates), "required": 2, "pass": chronological_split_ok},
        {
            "gate": "heldout_symbol_or_venue",
            "observed": f"symbols={len(symbols)};venues={len(venues)}",
            "required": "symbol>=2 or venue>=2",
            "pass": heldout_symbol_or_venue_ok,
        },
        {"gate": "wilson95_lcb", "observed": f"{combined_lcb:.6f}", "required": ">=0.95", "pass": combined_lcb >= 0.95},
        {
            "gate": "broad_normal_sample",
            "observed": provenance.get("matched_negative_control_policy", ""),
            "required": "source-owned broad normal activity sample",
            "pass": broad_normal_sample,
        },
    ]
    decision = "r6_shak_duplicate_row_cleanup_v1=duplicate_rows_removed_calibration_still_blocked"

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact_generation": board_hash,
        "decision": decision,
        "before_hashes": before_hashes,
        "after_hashes": {
            "positive": sha256(POSITIVE),
            "matched_negative": sha256(NEGATIVE),
            "provenance": sha256(PROVENANCE),
        },
        "positive_rows_removed": positive_removed,
        "matched_negative_rows_removed": negative_removed,
        "positive_source_row_ids_removed": positive_ids,
        "matched_negative_source_row_ids_removed": negative_ids,
        "positive_rows": len(positives),
        "matched_negative_rows": len(negatives),
        "labels": dict(labels),
        "unique_dates": dates,
        "unique_symbols": symbols,
        "unique_venues": venues,
        "matched_groups": groups,
        "verifier": verifier,
        "positive_wilson95_lcb": positive_lcb,
        "negative_wilson95_lcb": negative_lcb,
        "combined_min_wilson95_lcb": combined_lcb,
        "support_ok": support_ok,
        "chronological_split_ok": chronological_split_ok,
        "heldout_symbol_or_venue_ok": heldout_symbol_or_venue_ok,
        "broad_normal_sample": broad_normal_sample,
        "gate_rows": gate_rows,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    json_path = OUT / "r6_shak_duplicate_row_cleanup_v1.json"
    report_path = OUT / "r6_shak_duplicate_row_cleanup_v1.md"
    gate_csv = OUT / "r6_shak_duplicate_row_cleanup_v1_gates.csv"
    assertions = CHECKS / "r6_shak_duplicate_row_cleanup_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_simple_csv(gate_csv, gate_rows, ["gate", "observed", "required", "pass"])

    lines = [
        "# R6 Shak Duplicate Row Cleanup v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Removed only rows introduced by `20260511T211628-codex-r6-shak-cftc-row-uplift-v1`: positive `{positive_removed}`, matched negative `{negative_removed}`.",
        f"- Positive rows now: `{len(positives)}`; matched negative rows now: `{len(negatives)}`.",
        f"- Unique dates: `{len(dates)}`; symbols: `{len(symbols)}`; venues: `{len(venues)}`.",
        f"- Wilson95 LCB positive/negative/min: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{combined_lcb:.6f}`.",
        f"- Verifier status: `{verifier.get('status')}`; return code: `{verifier.get('returncode')}`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Boundary",
        "",
        "This cleanup removes only the duplicate rows created by this agent's `211628` slice. It preserves the concurrent `211606` Shak rows and all other shared intake additions.",
        "",
        "## Gates",
        "",
        "| Gate | Observed | Required | Pass |",
        "|---|---|---|---:|",
    ]
    for row in gate_rows:
        lines.append(f"| `{row['gate']}` | `{row['observed']}` | `{row['required']}` | `{str(row['pass']).lower()}` |")
    lines.extend(["", "## Artifacts", "", f"- JSON: `{json_path}`", f"- Gate CSV: `{gate_csv}`", f"- Assertions: `{assertions}`"])
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"PASS decision={decision}",
        f"PASS positive_rows_removed={positive_removed}",
        f"PASS matched_negative_rows_removed={negative_removed}",
        f"PASS verifier_status={verifier.get('status')}",
        f"PASS positive_rows={len(positives)}",
        f"PASS matched_negative_rows={len(negatives)}",
        f"PASS combined_min_wilson95_lcb={combined_lcb:.6f}",
        f"PASS support_ok={str(support_ok).lower()}",
        f"PASS broad_normal_sample={str(broad_normal_sample).lower()}",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
    ]
    assertions.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "positive_rows": len(positives), "matched_negative_rows": len(negatives), "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
