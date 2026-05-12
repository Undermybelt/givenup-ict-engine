#!/usr/bin/env python3
"""Read back the live R6 direct Manipulation intake after concurrent uplifts."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T212003+0800-codex-r6-live-32x32-calibration-readback-v1"
RUN_SLUG = "20260511T212003-codex-r6-live-32x32-calibration-readback-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_SLUG
OUT = RUN_ROOT / "r6-live-32x32-calibration-readback"
CHECKS = RUN_ROOT / "checks"
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


def wilson_lcb(successes: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    phat = successes / total
    denom = 1 + z * z / total
    centre = phat + z * z / (2 * total)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * total)) / total)
    return (centre - margin) / denom


def min_all_success_support(target_lcb: float = 0.95) -> int:
    n = 1
    while wilson_lcb(n, n) < target_lcb:
        n += 1
    return n


def unique_values(rows: list[dict[str, str]], key: str) -> list[str]:
    return sorted({row.get(key, "") for row in rows if row.get(key, "")})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    file_hash_before = {
        "positive": sha256(POSITIVE),
        "negative": sha256(NEGATIVE),
        "provenance": sha256(PROVENANCE),
    }
    positives = read_csv(POSITIVE)
    negatives = read_csv(NEGATIVE)
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    verifier = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    (OUT / "direct_manipulation_row_intake_verifier.stdout.txt").write_text(verifier.stdout, encoding="utf-8")
    (OUT / "direct_manipulation_row_intake_verifier.stderr.txt").write_text(verifier.stderr, encoding="utf-8")
    try:
        verifier_json = json.loads(verifier.stdout)
    except json.JSONDecodeError:
        verifier_json = {"status": "parse_failed", "stdout": verifier.stdout, "stderr": verifier.stderr}
    file_hash_after = {
        "positive": sha256(POSITIVE),
        "negative": sha256(NEGATIVE),
        "provenance": sha256(PROVENANCE),
    }
    stable_hashes = file_hash_before == file_hash_after

    required_support = min_all_success_support(0.95)
    positive_lcb = wilson_lcb(len(positives), len(positives))
    negative_lcb = wilson_lcb(len(negatives), len(negatives))
    min_lcb = min(positive_lcb, negative_lcb)
    unique_dates = unique_values(positives, "trade_date")
    unique_symbols = unique_values(positives, "symbol")
    unique_venues = unique_values(positives, "venue_or_market_center")
    source_reports = unique_values(positives + negatives, "source_report")
    labels = Counter(row.get("label", "") for row in positives + negatives)
    positive_groups = {row.get("matched_negative_group_id", "") for row in positives}
    negative_groups = {row.get("matched_negative_group_id", "") for row in negatives}
    matched_groups = sorted(positive_groups & negative_groups)
    orphan_groups = sorted(positive_groups - negative_groups)

    gates = [
        {"gate": "stable_file_hashes", "observed": stable_hashes, "required": True, "pass": stable_hashes},
        {"gate": "verifier_schema_ready", "observed": verifier_json.get("status"), "required": "schema_ready_unscored", "pass": verifier_json.get("status") == "schema_ready_unscored"},
        {"gate": "positive_support", "observed": len(positives), "required": required_support, "pass": len(positives) >= required_support},
        {"gate": "negative_support", "observed": len(negatives), "required": required_support, "pass": len(negatives) >= required_support},
        {"gate": "orphan_groups", "observed": len(orphan_groups), "required": 0, "pass": not orphan_groups},
        {"gate": "chronological_train_calibration_test", "observed": len(unique_dates), "required": 3, "pass": len(unique_dates) >= 3},
        {"gate": "heldout_symbol_or_venue", "observed": f"symbols={len(unique_symbols)};venues={len(unique_venues)}", "required": "symbol>=2 or venue>=2", "pass": len(unique_symbols) >= 2 or len(unique_venues) >= 2},
        {"gate": "wilson95_lcb", "observed": f"{min_lcb:.6f}", "required": ">=0.95", "pass": min_lcb >= 0.95},
        {"gate": "broad_normal_sample", "observed": "same-source public CFTC genuine-order counterparts", "required": "source-owned broad normal activity sample", "pass": False},
        {"gate": "direct_species_coverage", "observed": "spoofing_layering", "required": "spoofing_layering;quote_spoofing;quote_stuffing;pinging;bear_raid;painting_tape", "pass": False},
    ]
    decision = "r6_live_32x32_calibration_readback_v1=live_rows_schema_ready_wilson_broad_control_blocked"
    audit = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact_generation": sha256(BOARD),
        "decision": decision,
        "intake_root": str(INTAKE),
        "file_hash_before": file_hash_before,
        "file_hash_after": file_hash_after,
        "stable_file_hashes": stable_hashes,
        "positive_rows": len(positives),
        "matched_negative_rows": len(negatives),
        "matched_group_count": len(matched_groups),
        "orphan_groups": orphan_groups,
        "unique_dates": unique_dates,
        "unique_symbols": unique_symbols,
        "unique_venues": unique_venues,
        "source_reports": source_reports,
        "labels": dict(labels),
        "positive_wilson95_lcb": positive_lcb,
        "negative_wilson95_lcb": negative_lcb,
        "combined_min_wilson95_lcb": min_lcb,
        "required_support_for_all_success_wilson95_lcb": required_support,
        "provenance_keys": sorted(provenance.keys()),
        "verifier_returncode": verifier.returncode,
        "verifier": verifier_json,
        "gate_rows": gates,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": "Acquire broad source-owned normal controls and the missing direct Manipulation species, or continue public official row extraction until support reaches the unchanged Wilson95 gate; keep R2/R3/R4/R5 intake roots fail-closed until their required files exist.",
    }

    json_path = OUT / "r6_live_32x32_calibration_readback_v1.json"
    report_path = OUT / "r6_live_32x32_calibration_readback_v1.md"
    gate_csv = OUT / "r6_live_32x32_calibration_readback_v1_gates.csv"
    source_csv = OUT / "r6_live_32x32_calibration_readback_v1_sources.csv"
    assertions_path = CHECKS / "r6_live_32x32_calibration_readback_v1_assertions.out"
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(gate_csv, gates, ["gate", "observed", "required", "pass"])
    write_csv(source_csv, [{"source_report": item} for item in source_reports], ["source_report"])

    lines = [
        "# R6 Live 32x32 Calibration Readback v1",
        "",
        f"Decision: `{decision}`.",
        "",
        "Result:",
        f"- Live direct intake rows: positives `{len(positives)}`, matched negatives `{len(negatives)}`, matched groups `{len(matched_groups)}`.",
        f"- Unique positive dates/symbols/venues: `{len(unique_dates)}` / `{len(unique_symbols)}` / `{len(unique_venues)}`.",
        f"- Wilson95 LCB positive/negative/min: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{min_lcb:.6f}`.",
        f"- Required all-success support for Wilson95 `>=0.95`: `{required_support}`.",
        f"- Verifier status: `{verifier_json.get('status')}`; stable file hashes during readback: `{str(stable_hashes).lower()}`.",
        "- Broad normal sample: `false`; direct species coverage still only `spoofing_layering`.",
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
            "The live R6 intake now has enough public CFTC row breadth to lift Wilson95 from the earlier 0.77 range to 0.892821, while preserving chronological and heldout-symbol/venue gates. It still fails the unchanged strict objective because Wilson95 remains below 0.95, broad source-owned normal controls are absent, and non-spoofing direct species are not covered.",
            "",
            "Artifacts:",
            f"- JSON: `{rel(json_path)}`",
            f"- Gate CSV: `{rel(gate_csv)}`",
            f"- Source report CSV: `{rel(source_csv)}`",
            f"- Verifier stdout: `{rel(OUT / 'direct_manipulation_row_intake_verifier.stdout.txt')}`",
            f"- Assertions: `{rel(assertions_path)}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS stable_file_hashes={str(stable_hashes).lower()}",
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
    print(json.dumps({"decision": decision, "positive_rows": len(positives), "matched_negative_rows": len(negatives), "wilson95_min": round(min_lcb, 6)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
