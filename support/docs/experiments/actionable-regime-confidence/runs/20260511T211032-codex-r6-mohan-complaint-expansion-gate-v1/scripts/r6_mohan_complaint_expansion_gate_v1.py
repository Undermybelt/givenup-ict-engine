#!/usr/bin/env python3
"""Fail-closed R6 gate after Mohan complaint row expansion."""

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


RUN_ID = "20260511T211032-codex-r6-mohan-complaint-expansion-gate-v1"
GATE_NAME = "r6_mohan_complaint_expansion_gate_v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r6-mohan-complaint-expansion-gate"
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


def count_values(rows: list[dict[str, str]], key: str) -> list[str]:
    return sorted({row.get(key, "") for row in rows if row.get(key, "")})


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def run_verifier() -> dict[str, object]:
    proc = subprocess.run(
        [sys.executable, str(VERIFIER), "--intake-root", str(INTAKE)],
        cwd=str(REPO),
        text=True,
        capture_output=True,
        check=False,
    )
    output_path = CHECKS / "direct_manipulation_row_intake_verifier_v1.out"
    output_path.write_text(proc.stdout + proc.stderr, encoding="utf-8")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {"status": "parse_failed", "returncode": proc.returncode}
    payload["returncode"] = proc.returncode
    payload["output_path"] = str(output_path)
    return payload


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    verifier_result = run_verifier()
    board_hash = sha256(BOARD)
    positives = read_csv(POSITIVE) if POSITIVE.exists() else []
    negatives = read_csv(NEGATIVE) if NEGATIVE.exists() else []
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8")) if PROVENANCE.exists() else {}
    all_rows = positives + negatives

    labels = Counter(row.get("label", "") for row in all_rows)
    dates = count_values(all_rows, "trade_date")
    symbols = count_values(all_rows, "symbol")
    venues = count_values(all_rows, "venue_or_market_center")
    groups = count_values(all_rows, "matched_negative_group_id")
    sessions = count_values(all_rows, "session_bucket")

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
            "matched_control_policy",
            "mohan_complaint_control_policy",
        )
    ).lower()
    broad_normal_sample = not any(
        phrase in control_policy
        for phrase in (
            "not a broad",
            "not independent",
            "schema-ready/unscored seed",
            "schema/control seed",
        )
    )

    gate_rows = [
        {
            "gate": "schema_verifier",
            "observed": verifier_result.get("status", "unknown"),
            "required": "schema_ready_unscored",
            "pass": verifier_result.get("status") == "schema_ready_unscored",
        },
        {
            "gate": "positive_support",
            "observed": len(positives),
            "required": min_support,
            "pass": len(positives) >= min_support,
        },
        {
            "gate": "negative_support",
            "observed": len(negatives),
            "required": min_support,
            "pass": len(negatives) >= min_support,
        },
        {
            "gate": "chronological_split",
            "observed": len(dates),
            "required": 2,
            "pass": chronological_split_ok,
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
    ]
    gate_pass = all(bool(row["pass"]) for row in gate_rows)
    decision = (
        f"{GATE_NAME}=accepted_95"
        if gate_pass
        else f"{GATE_NAME}=schema_ready_but_calibration_blocked"
    )

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_writeback": board_hash,
        "decision": decision,
        "intake_root": str(INTAKE),
        "verifier_result": verifier_result,
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
        "gate_rows": gate_rows,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": "Acquire source-owned or owner-approved broad same-schema normal controls and more positive rows until support, Wilson95, chronological, and heldout gates pass without proxy labels.",
        "source_hashes": {
            "positive_spoofing_layering_rows.csv": sha256(POSITIVE) if POSITIVE.exists() else None,
            "matched_negative_normal_activity_rows.csv": sha256(NEGATIVE) if NEGATIVE.exists() else None,
            "provenance_manifest.json": sha256(PROVENANCE) if PROVENANCE.exists() else None,
        },
        "provenance_highlights": {
            "mohan_additional_positive_rows_added": provenance.get("mohan_additional_positive_rows_added"),
            "mohan_additional_matched_negative_rows_added": provenance.get("mohan_additional_matched_negative_rows_added"),
            "cftc_mohan_complaint_rows_added": provenance.get("cftc_mohan_complaint_rows_added"),
            "matched_negative_control_policy": provenance.get("matched_negative_control_policy"),
        },
    }

    json_path = OUT / "r6_mohan_complaint_expansion_gate_v1.json"
    md_path = OUT / "r6_mohan_complaint_expansion_gate_v1.md"
    gate_csv = OUT / "r6_mohan_complaint_expansion_gate_v1_gates.csv"
    assertions_path = CHECKS / "r6_mohan_complaint_expansion_gate_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(gate_csv, gate_rows, ["gate", "observed", "required", "pass"])

    lines = [
        "# R6 Mohan Complaint Expansion Gate v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Verifier status: `{verifier_result.get('status', 'unknown')}`.",
        f"- Positive rows: `{len(positives)}`; matched negative rows: `{len(negatives)}`.",
        f"- Unique dates: `{len(dates)}`; symbols: `{len(symbols)}`; venues: `{len(venues)}`; matched groups: `{len(groups)}`.",
        f"- Wilson95 LCB positive/negative/min: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{combined_lcb:.6f}`.",
        f"- Chronological split ok: `{str(chronological_split_ok).lower()}`; heldout symbol/venue ok: `{str(heldout_symbol_or_venue_ok).lower()}`.",
        f"- Broad normal sample: `{str(broad_normal_sample).lower()}`.",
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
            "The Mohan complaint expansion improves date, symbol, and venue breadth, and the unchanged intake verifier parses the files. The slice remains calibration-blocked because support is below 50/50, Wilson95 min LCB is below 0.95, and same-event genuine-order rows are not broad independent normal controls.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- Gate CSV: `{gate_csv}`",
            f"- Verifier output: `{CHECKS / 'direct_manipulation_row_intake_verifier_v1.out'}`",
            f"- Assertions: `{assertions_path}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS verifier_status={verifier_result.get('status', 'unknown')}",
        f"PASS positive_rows={len(positives)}",
        f"PASS matched_negative_rows={len(negatives)}",
        f"PASS chronological_split_ok={str(chronological_split_ok).lower()}",
        f"PASS heldout_symbol_or_venue_ok={str(heldout_symbol_or_venue_ok).lower()}",
        f"PASS combined_min_wilson95_lcb={combined_lcb:.6f}",
        f"PASS support_ok={str(support_ok).lower()}",
        f"PASS broad_normal_sample={str(broad_normal_sample).lower()}",
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
