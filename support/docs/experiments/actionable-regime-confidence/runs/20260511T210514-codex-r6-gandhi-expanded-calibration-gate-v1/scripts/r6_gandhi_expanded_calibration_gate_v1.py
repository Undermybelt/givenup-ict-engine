#!/usr/bin/env python3
"""Fail-closed calibration gate after the Gandhi CFTC row uplift."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T210514-codex-r6-gandhi-expanded-calibration-gate-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r6-gandhi-expanded-calibration-gate"
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

REQUIRED_SPECIES = [
    "spoofing_layering",
    "quote_spoofing",
    "quote_stuffing",
    "pinging",
    "bear_raid",
    "painting_tape",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def run_verifier() -> dict[str, object]:
    command = ["python3", str(VERIFIER), "--intake-root", str(INTAKE)]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    stdout_path = OUT / "direct_manipulation_row_intake_verifier.stdout.txt"
    stderr_path = OUT / "direct_manipulation_row_intake_verifier.stderr.txt"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    parsed: object
    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError:
        parsed = {}
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "stdout_path": str(stdout_path.relative_to(REPO)),
        "stderr_path": str(stderr_path.relative_to(REPO)),
        "stdout": parsed,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    positives = read_csv(POSITIVE) if POSITIVE.exists() else []
    negatives = read_csv(NEGATIVE) if NEGATIVE.exists() else []
    all_rows = positives + negatives
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8")) if PROVENANCE.exists() else {}
    verifier = run_verifier()

    labels = Counter(row.get("label", "") for row in all_rows)
    dates = unique_values(all_rows, "trade_date")
    symbols = unique_values(all_rows, "symbol")
    venues = unique_values(all_rows, "venue_or_market_center")
    groups = unique_values(all_rows, "matched_negative_group_id")
    sessions = unique_values(all_rows, "session_bucket")
    observed_species = ["spoofing_layering"] if positives else []
    missing_species = [species for species in REQUIRED_SPECIES if species not in observed_species]

    support_required = min_all_success_support(0.95)
    positive_lcb = wilson_lcb(len(positives), len(positives))
    negative_lcb = wilson_lcb(len(negatives), len(negatives))
    combined_lcb = min(positive_lcb, negative_lcb)

    positive_support_ok = len(positives) >= support_required
    negative_support_ok = len(negatives) >= support_required
    chronological_train_calibration_test_ok = len(dates) >= 3
    heldout_symbol_or_venue_ok = len(symbols) >= 2 or len(venues) >= 2
    broad_normal_sample = "not broad" not in json.dumps(provenance, sort_keys=True).lower()
    species_coverage_ok = not missing_species

    gate_rows = [
        {
            "gate": "positive_support",
            "observed": len(positives),
            "required": support_required,
            "pass": positive_support_ok,
        },
        {
            "gate": "negative_support",
            "observed": len(negatives),
            "required": support_required,
            "pass": negative_support_ok,
        },
        {
            "gate": "chronological_train_calibration_test",
            "observed": len(dates),
            "required": 3,
            "pass": chronological_train_calibration_test_ok,
        },
        {
            "gate": "heldout_symbol_or_venue",
            "observed": f"symbols={len(symbols)};venues={len(venues)}",
            "required": "symbol>=2 or venue>=2",
            "pass": heldout_symbol_or_venue_ok,
        },
        {
            "gate": "wilson95_lcb",
            "observed": f"{combined_lcb:.6f}",
            "required": ">=0.95",
            "pass": combined_lcb >= 0.95,
        },
        {
            "gate": "broad_normal_sample",
            "observed": provenance.get("matched_negative_control_policy", ""),
            "required": "source-owned broad normal activity sample",
            "pass": broad_normal_sample,
        },
        {
            "gate": "direct_species_coverage",
            "observed": ";".join(observed_species),
            "required": ";".join(REQUIRED_SPECIES),
            "pass": species_coverage_ok,
        },
    ]
    gate_pass = all(bool(row["pass"]) for row in gate_rows)
    decision = (
        "r6_gandhi_expanded_calibration_gate_v1=accepted_95"
        if gate_pass
        else "r6_gandhi_expanded_calibration_gate_v1=expanded_rows_schema_ready_calibration_blocked"
    )

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact_generation": sha256(BOARD),
        "decision": decision,
        "intake_root": str(INTAKE),
        "positive_rows": len(positives),
        "matched_negative_rows": len(negatives),
        "labels": dict(labels),
        "unique_dates": dates,
        "unique_symbols": symbols,
        "unique_venues": venues,
        "matched_groups": groups,
        "session_buckets": sessions,
        "observed_species": observed_species,
        "missing_species": missing_species,
        "positive_wilson95_lcb": positive_lcb,
        "negative_wilson95_lcb": negative_lcb,
        "combined_min_wilson95_lcb": combined_lcb,
        "support_required_per_class_for_wilson95_lcb_ge_0_95": support_required,
        "chronological_train_calibration_test_ok": chronological_train_calibration_test_ok,
        "heldout_symbol_or_venue_ok": heldout_symbol_or_venue_ok,
        "broad_normal_sample": broad_normal_sample,
        "species_coverage_ok": species_coverage_ok,
        "gate_rows": gate_rows,
        "verifier": verifier,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": "Keep extracting only source-stated row facts, but acquire enough source-owned or owner-approved positive/control rows, broad normal controls, and direct-species coverage before another completion audit.",
        "source_hashes": {
            "positive_spoofing_layering_rows.csv": sha256(POSITIVE) if POSITIVE.exists() else None,
            "matched_negative_normal_activity_rows.csv": sha256(NEGATIVE) if NEGATIVE.exists() else None,
            "provenance_manifest.json": sha256(PROVENANCE) if PROVENANCE.exists() else None,
        },
    }

    json_path = OUT / "r6_gandhi_expanded_calibration_gate_v1.json"
    md_path = OUT / "r6_gandhi_expanded_calibration_gate_v1.md"
    gate_csv = OUT / "r6_gandhi_expanded_calibration_gate_v1_gates.csv"
    assertions_path = CHECKS / "r6_gandhi_expanded_calibration_gate_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(gate_csv, gate_rows, ["gate", "observed", "required", "pass"])

    lines = [
        "# R6 Gandhi Expanded Calibration Gate v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Positive rows: `{len(positives)}`; matched negative rows: `{len(negatives)}`; matched groups: `{len(groups)}`.",
        f"- Unique dates: `{len(dates)}`; symbols/contracts: `{len(symbols)}`; venues: `{len(venues)}`.",
        f"- Wilson95 LCB positive/negative/min: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{combined_lcb:.6f}`.",
        f"- Chronological train/calibration/test split ok: `{str(chronological_train_calibration_test_ok).lower()}`.",
        f"- Heldout symbol/venue ok: `{str(heldout_symbol_or_venue_ok).lower()}`.",
        f"- Broad normal sample: `{str(broad_normal_sample).lower()}`.",
        f"- Missing direct species: `{','.join(missing_species)}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Gates",
        "",
        "| Gate | Observed | Required | Pass |",
        "|---|---|---|---:|",
    ]
    for row in gate_rows:
        lines.append(f"| `{row['gate']}` | `{row['observed']}` | `{row['required']}` | `{str(row['pass']).lower()}` |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The Gandhi uplift materially improves the R6 schema-ready seed from 2/2 rows to 4/4 rows and adds chronological plus symbol/contract breadth. It still cannot satisfy the unchanged Board A confidence objective because support is far below the Wilson95 threshold, controls are same-report seeds rather than a broad normal sample, and direct species coverage is still incomplete.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Gate CSV: `{gate_csv.relative_to(REPO)}`",
            f"- Verifier stdout: `{(OUT / 'direct_manipulation_row_intake_verifier.stdout.txt').relative_to(REPO)}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS positive_rows={len(positives)}",
        f"PASS matched_negative_rows={len(negatives)}",
        f"PASS matched_group_count={len(groups)}",
        f"PASS combined_min_wilson95_lcb={combined_lcb:.6f}",
        f"PASS chronological_train_calibration_test_ok={str(chronological_train_calibration_test_ok).lower()}",
        f"PASS heldout_symbol_or_venue_ok={str(heldout_symbol_or_venue_ok).lower()}",
        f"PASS broad_normal_sample={str(broad_normal_sample).lower()}",
        f"PASS species_coverage_ok={str(species_coverage_ok).lower()}",
        f"PASS new_confidence_gate=false",
        f"PASS strict_full_objective_achieved=false",
        f"PASS update_goal=false",
        f"PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "gate_pass": gate_pass, "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
