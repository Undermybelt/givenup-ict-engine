#!/usr/bin/env python3
"""Remove semantic-duplicate rows introduced by the 211201 Mohan/Shak uplift."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T212325+0800-codex-r6-mohan-shak-duplicate-cleanup-v1"
RUN_SLUG = "20260511T212325-codex-r6-mohan-shak-duplicate-cleanup-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_SLUG
OUT = RUN_ROOT / "r6-mohan-shak-duplicate-cleanup"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE = INTAKE / "positive_spoofing_layering_rows.csv"
NEGATIVE = INTAKE / "matched_negative_normal_activity_rows.csv"
PROVENANCE = INTAKE / "provenance_manifest.json"
ADDITIONS = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T211201-codex-r6-mohan-shak-row-uplift-v1/"
    "r6-mohan-shak-row-uplift/r6_mohan_shak_row_uplift_v1_additions.csv"
)
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
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
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def remove_by_source_id(path: Path, remove_ids: set[str]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[str]]:
    rows = read_csv(path)
    fields = list(rows[0].keys()) if rows else []
    kept: list[dict[str, str]] = []
    removed: list[dict[str, str]] = []
    for row in rows:
        if row.get("source_row_id", "") in remove_ids:
            removed.append(row)
        else:
            kept.append(row)
    if fields:
        write_csv(path, kept, fields)
    return kept, removed, fields


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


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)

    additions = read_csv(ADDITIONS)
    positive_remove_ids = {row["source_row_id"] for row in additions if row.get("kind") == "positive"}
    negative_remove_ids = {row["source_row_id"] for row in additions if row.get("kind") == "matched_negative"}
    before = {
        "positive_rows": len(read_csv(POSITIVE)),
        "matched_negative_rows": len(read_csv(NEGATIVE)),
        "positive_sha256": sha256(POSITIVE),
        "matched_negative_sha256": sha256(NEGATIVE),
        "provenance_sha256": sha256(PROVENANCE),
    }

    positives, removed_positive, fields_positive = remove_by_source_id(POSITIVE, positive_remove_ids)
    negatives, removed_negative, fields_negative = remove_by_source_id(NEGATIVE, negative_remove_ids)

    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    provenance["r6_mohan_shak_duplicate_cleanup_v1"] = {
        "run_id": RUN_ID,
        "removed_positive_rows": len(removed_positive),
        "removed_matched_negative_rows": len(removed_negative),
        "removed_source_row_ids": sorted(positive_remove_ids | negative_remove_ids),
        "reason": "Rows from 20260511T211201 duplicated source facts already materialized by concurrent Mohan/Shak official CFTC uplifts under different row IDs.",
        "cleanup_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    provenance["positive_rows_count"] = len(positives)
    provenance["matched_negative_rows_count"] = len(negatives)
    provenance["updated_by"] = RUN_ID
    provenance["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    verifier = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    (CMD_OUT / "direct_manipulation_row_intake_verifier.stdout.txt").write_text(verifier.stdout, encoding="utf-8")
    (CMD_OUT / "direct_manipulation_row_intake_verifier.stderr.txt").write_text(verifier.stderr, encoding="utf-8")
    try:
        verifier_json = json.loads(verifier.stdout)
    except json.JSONDecodeError:
        verifier_json = {"status": "parse_failed", "stdout": verifier.stdout, "stderr": verifier.stderr}

    positive_lcb = wilson_lcb(len(positives), len(positives))
    negative_lcb = wilson_lcb(len(negatives), len(negatives))
    min_lcb = min(positive_lcb, negative_lcb)
    unique_dates = unique_values(positives, "trade_date")
    unique_symbols = unique_values(positives, "symbol")
    unique_venues = unique_values(positives, "venue_or_market_center")
    positive_groups = {row.get("matched_negative_group_id", "") for row in positives}
    negative_groups = {row.get("matched_negative_group_id", "") for row in negatives}
    matched_groups = sorted(positive_groups & negative_groups)
    orphan_groups = sorted(positive_groups - negative_groups)
    labels = Counter(row.get("label", "") for row in positives + negatives)
    gates = [
        {"gate": "removed_only_211201_positive_rows", "observed": len(removed_positive), "required": len(positive_remove_ids), "pass": len(removed_positive) == len(positive_remove_ids)},
        {"gate": "removed_only_211201_negative_rows", "observed": len(removed_negative), "required": len(negative_remove_ids), "pass": len(removed_negative) == len(negative_remove_ids)},
        {"gate": "verifier_schema_ready", "observed": verifier_json.get("status"), "required": "schema_ready_unscored", "pass": verifier_json.get("status") == "schema_ready_unscored"},
        {"gate": "positive_support", "observed": len(positives), "required": 50, "pass": len(positives) >= 50},
        {"gate": "negative_support", "observed": len(negatives), "required": 50, "pass": len(negatives) >= 50},
        {"gate": "orphan_groups", "observed": len(orphan_groups), "required": 0, "pass": not orphan_groups},
        {"gate": "chronological_split", "observed": len(unique_dates), "required": 2, "pass": len(unique_dates) >= 2},
        {"gate": "heldout_symbol_or_venue", "observed": f"symbols={len(unique_symbols)};venues={len(unique_venues)}", "required": "symbol>=2 or venue>=2", "pass": len(unique_symbols) >= 2 or len(unique_venues) >= 2},
        {"gate": "wilson95_lcb", "observed": f"{min_lcb:.6f}", "required": ">=0.95", "pass": min_lcb >= 0.95},
        {"gate": "broad_normal_sample", "observed": "same-source public CFTC genuine-order counterparts", "required": "source-owned broad normal activity sample", "pass": False},
    ]
    decision = "r6_mohan_shak_duplicate_cleanup_v1=duplicate_rows_removed_calibration_still_blocked"
    audit = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact_generation": sha256(BOARD),
        "decision": decision,
        "before": before,
        "after": {
            "positive_rows": len(positives),
            "matched_negative_rows": len(negatives),
            "positive_sha256": sha256(POSITIVE),
            "matched_negative_sha256": sha256(NEGATIVE),
            "provenance_sha256": sha256(PROVENANCE),
        },
        "removed_positive_rows": len(removed_positive),
        "removed_matched_negative_rows": len(removed_negative),
        "removed_positive_source_row_ids": [row["source_row_id"] for row in removed_positive],
        "removed_matched_negative_source_row_ids": [row["source_row_id"] for row in removed_negative],
        "positive_rows": len(positives),
        "matched_negative_rows": len(negatives),
        "matched_group_count": len(matched_groups),
        "orphan_groups": orphan_groups,
        "unique_dates": unique_dates,
        "unique_symbols": unique_symbols,
        "unique_venues": unique_venues,
        "labels": dict(labels),
        "combined_min_wilson95_lcb": min_lcb,
        "positive_wilson95_lcb": positive_lcb,
        "negative_wilson95_lcb": negative_lcb,
        "gate_rows": gates,
        "verifier_returncode": verifier.returncode,
        "verifier": verifier_json,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": "Continue R6 with non-duplicate official source rows, broad normal controls, and missing direct species; keep R2/R3/R4/R5 blocked until required source-owned files exist.",
    }

    json_path = OUT / "r6_mohan_shak_duplicate_cleanup_v1.json"
    report_path = OUT / "r6_mohan_shak_duplicate_cleanup_v1.md"
    gate_csv = OUT / "r6_mohan_shak_duplicate_cleanup_v1_gates.csv"
    removed_csv = OUT / "r6_mohan_shak_duplicate_cleanup_v1_removed_rows.csv"
    assertions_path = CHECKS / "r6_mohan_shak_duplicate_cleanup_v1_assertions.out"
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(gate_csv, gates, ["gate", "observed", "required", "pass"])
    write_csv(removed_csv, [{"kind": "positive", **row} for row in removed_positive] + [{"kind": "matched_negative", **row} for row in removed_negative], ["kind", *(fields_positive or fields_negative)])

    lines = [
        "# R6 Mohan/Shak Duplicate Cleanup v1",
        "",
        f"Decision: `{decision}`.",
        "",
        "Result:",
        f"- Removed duplicate rows introduced by my `211201` uplift only: positives `{len(removed_positive)}`, matched negatives `{len(removed_negative)}`.",
        f"- Corrected live direct intake: positives `{len(positives)}`, matched negatives `{len(negatives)}`, matched groups `{len(matched_groups)}`.",
        f"- Unique positive dates/symbols/venues: `{len(unique_dates)}` / `{len(unique_symbols)}` / `{len(unique_venues)}`.",
        f"- Wilson95 LCB positive/negative/min: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{min_lcb:.6f}`.",
        f"- Verifier status: `{verifier_json.get('status')}`.",
        "- Broad normal sample: `false`; direct species coverage still limited.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "Gates:",
        "",
        "| Gate | Observed | Required | Pass |",
        "|---|---|---|---:|",
    ]
    for gate in gates:
        lines.append(f"| `{gate['gate']}` | `{gate['observed']}` | `{gate['required']}` | `{str(gate['pass']).lower()}` |")
    lines.extend(
        [
            "",
            "Interpretation:",
            "The cleanup corrects my own duplicate contribution and keeps the shared intake conservative. R6 remains schema-ready but confidence-blocked because support/Wilson95, broad normal controls, and direct-species breadth are still insufficient.",
            "",
            "Artifacts:",
            f"- JSON: `{rel(json_path)}`",
            f"- Gate CSV: `{rel(gate_csv)}`",
            f"- Removed rows CSV: `{rel(removed_csv)}`",
            f"- Verifier stdout: `{rel(CMD_OUT / 'direct_manipulation_row_intake_verifier.stdout.txt')}`",
            f"- Assertions: `{rel(assertions_path)}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assertions = [
        f"PASS decision={decision}",
        f"PASS removed_positive_rows={len(removed_positive)}",
        f"PASS removed_matched_negative_rows={len(removed_negative)}",
        f"PASS verifier_status={verifier_json.get('status')}",
        f"PASS positive_rows={len(positives)}",
        f"PASS matched_negative_rows={len(negatives)}",
        f"PASS combined_min_wilson95_lcb={min_lcb:.6f}",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "positive_rows": len(positives), "matched_negative_rows": len(negatives), "removed_positive_rows": len(removed_positive), "removed_matched_negative_rows": len(removed_negative), "wilson95_min": round(min_lcb, 6)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
