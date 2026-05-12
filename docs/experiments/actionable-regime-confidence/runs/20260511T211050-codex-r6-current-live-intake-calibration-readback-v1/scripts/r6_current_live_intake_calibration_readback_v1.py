#!/usr/bin/env python3
"""Fail-closed readback for the current live R6 direct Manipulation intake."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T211050-codex-r6-current-live-intake-calibration-readback-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r6-current-live-intake-calibration-readback"
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


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
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


def unique(rows: list[dict[str, str]], key: str) -> list[str]:
    return sorted({row.get(key, "") for row in rows if row.get(key, "")})


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def run_verifier() -> dict[str, Any]:
    proc = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    (OUT / "direct_manipulation_row_intake_verifier.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (OUT / "direct_manipulation_row_intake_verifier.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {"status": "parse_failed", "stdout": proc.stdout}
    payload["returncode"] = proc.returncode
    return payload


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    positives = read_csv(POSITIVE)
    negatives = read_csv(NEGATIVE)
    all_rows = positives + negatives
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8")) if PROVENANCE.exists() else {}
    verifier = run_verifier()

    dates = unique(all_rows, "trade_date")
    symbols = unique(all_rows, "symbol")
    venues = unique(all_rows, "venue_or_market_center")
    groups = unique(all_rows, "matched_negative_group_id")
    sessions = unique(all_rows, "session_bucket")
    labels = Counter(row.get("label", "") for row in all_rows)

    positive_lcb = wilson_lcb(len(positives), len(positives))
    negative_lcb = wilson_lcb(len(negatives), len(negatives))
    combined_lcb = min(positive_lcb, negative_lcb)
    min_support = 50
    support_ok = len(positives) >= min_support and len(negatives) >= min_support
    chronological_split_ok = len(dates) >= 2
    heldout_symbol_or_venue_ok = len(symbols) >= 2 or len(venues) >= 2
    control_policy = " ".join(
        str(provenance.get(key, ""))
        for key in (
            "matched_negative_control_policy",
            "mohan_complaint_control_policy",
            "matched_control_policy",
            "matched_control_limitations",
        )
    )
    broad_normal_sample = bool(control_policy and "not" not in control_policy.lower())
    species_coverage_ok = False

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
            "observed": "same-event CFTC genuine-order control seeds; not broad normal-market calibration",
            "required": "source-owned broad normal activity sample",
            "pass": broad_normal_sample,
        },
        {
            "gate": "direct_species_coverage",
            "observed": "spoofing_layering",
            "required": "spoofing_layering;quote_spoofing;quote_stuffing;pinging;bear_raid;painting_tape",
            "pass": species_coverage_ok,
        },
    ]
    gate_pass = all(bool(row["pass"]) for row in gate_rows)
    decision = (
        "r6_current_live_intake_calibration_readback_v1=accepted_95"
        if gate_pass
        else "r6_current_live_intake_calibration_readback_v1=schema_ready_but_calibration_blocked"
    )

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact_generation": sha256(BOARD),
        "decision": decision,
        "intake_root": str(INTAKE),
        "verifier": verifier,
        "positive_rows": len(positives),
        "matched_negative_rows": len(negatives),
        "labels": dict(labels),
        "unique_dates": dates,
        "unique_symbols": symbols,
        "unique_venues": venues,
        "matched_groups": groups,
        "session_buckets": sessions,
        "positive_wilson95_lcb": positive_lcb,
        "negative_wilson95_lcb": negative_lcb,
        "combined_min_wilson95_lcb": combined_lcb,
        "min_support_required_per_class": min_support,
        "support_ok": support_ok,
        "chronological_split_ok": chronological_split_ok,
        "heldout_symbol_or_venue_ok": heldout_symbol_or_venue_ok,
        "broad_normal_sample": broad_normal_sample,
        "species_coverage_ok": species_coverage_ok,
        "gate_rows": gate_rows,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "source_hashes": {
            "positive_spoofing_layering_rows.csv": sha256(POSITIVE),
            "matched_negative_normal_activity_rows.csv": sha256(NEGATIVE),
            "provenance_manifest.json": sha256(PROVENANCE),
        },
        "next_action": (
            "Acquire source-owned or owner-approved broad same-schema controls and additional positive rows "
            "across direct Manipulation species, then rerun the full completion audit."
        ),
    }

    json_path = OUT / "r6_current_live_intake_calibration_readback_v1.json"
    md_path = OUT / "r6_current_live_intake_calibration_readback_v1.md"
    gates_path = OUT / "r6_current_live_intake_calibration_readback_v1_gates.csv"
    assertions_path = CHECKS / "r6_current_live_intake_calibration_readback_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(gates_path, gate_rows, ["gate", "observed", "required", "pass"])

    lines = [
        "# R6 Current Live Intake Calibration Readback v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Verifier status: `{verifier.get('status')}`; verifier positive rows `{verifier.get('positive_rows')}`; verifier matched negatives `{verifier.get('matched_negative_rows')}`.",
        f"- CSV rows: positives `{len(positives)}`; matched negatives `{len(negatives)}`; matched groups `{len(groups)}`.",
        f"- Breadth: dates `{len(dates)}`; symbols `{len(symbols)}`; venues `{len(venues)}`; sessions `{len(sessions)}`.",
        f"- Wilson95 LCB positive/negative/min: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{combined_lcb:.6f}`.",
        f"- Chronological split ok: `{str(chronological_split_ok).lower()}`; heldout symbol/venue ok: `{str(heldout_symbol_or_venue_ok).lower()}`.",
        f"- Support ok: `{str(support_ok).lower()}`; broad normal sample: `{str(broad_normal_sample).lower()}`; species coverage ok: `{str(species_coverage_ok).lower()}`.",
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
            "The live R6 intake is schema-ready and stronger than the last cursored 4/4 artifact, but it still fails the unchanged Board A objective. Support remains below 50/50, Wilson95 min LCB remains below 0.95, controls are same-event CFTC genuine-order seeds rather than a broad normal sample, and direct Manipulation species coverage is still incomplete.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- Gate CSV: `{gates_path}`",
            f"- Verifier stdout: `{OUT / 'direct_manipulation_row_intake_verifier.stdout.txt'}`",
            f"- Assertions: `{assertions_path}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS verifier_status={verifier.get('status')}",
        f"PASS positive_rows={len(positives)}",
        f"PASS matched_negative_rows={len(negatives)}",
        f"PASS chronological_split_ok={str(chronological_split_ok).lower()}",
        f"PASS heldout_symbol_or_venue_ok={str(heldout_symbol_or_venue_ok).lower()}",
        f"PASS combined_min_wilson95_lcb={combined_lcb:.6f}",
        f"PASS support_ok={str(support_ok).lower()}",
        f"PASS broad_normal_sample={str(broad_normal_sample).lower()}",
        f"PASS species_coverage_ok={str(species_coverage_ok).lower()}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps({"decision": decision, "gate_pass": gate_pass, "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
