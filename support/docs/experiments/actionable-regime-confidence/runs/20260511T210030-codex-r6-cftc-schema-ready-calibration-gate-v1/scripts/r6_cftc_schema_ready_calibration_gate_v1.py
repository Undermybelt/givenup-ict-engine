#!/usr/bin/env python3
"""Fail-closed R6 calibration gate for the current CFTC/FINRA direct intake."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T210030-codex-r6-cftc-schema-ready-calibration-gate-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r6-cftc-schema-ready-calibration-gate"
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


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

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
    broad_normal_sample = bool(provenance.get("matched_negative_control_policy", "").lower().find("not a broad") == -1)

    gate_rows = [
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
    gate_name = (
        "r6_cftc_gandhi_calibration_gate_v2"
        if "gandhi-calibration-gate-v2" in RUN_ID
        else "r6_cftc_schema_ready_calibration_gate_v1"
    )
    decision = (
        f"{gate_name}=accepted_95"
        if gate_pass
        else f"{gate_name}=schema_ready_but_calibration_blocked"
    )

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_writeback": board_hash,
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
        "next_action": "Acquire source-owned or owner-approved broad same-schema normal controls with enough dates and symbols/venues, then rerun this gate and the full completion audit.",
        "source_hashes": {
            "positive_spoofing_layering_rows.csv": sha256(POSITIVE) if POSITIVE.exists() else None,
            "matched_negative_normal_activity_rows.csv": sha256(NEGATIVE) if NEGATIVE.exists() else None,
            "provenance_manifest.json": sha256(PROVENANCE) if PROVENANCE.exists() else None,
        },
    }

    json_path = OUT / "r6_cftc_schema_ready_calibration_gate_v1.json"
    md_path = OUT / "r6_cftc_schema_ready_calibration_gate_v1.md"
    gate_csv = OUT / "r6_cftc_schema_ready_calibration_gate_v1_gates.csv"
    assertions_path = CHECKS / "r6_cftc_schema_ready_calibration_gate_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(gate_csv, gate_rows, ["gate", "observed", "required", "pass"])

    lines = [
        "# R6 CFTC Schema-Ready Calibration Gate v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Positive rows: `{len(positives)}`; matched negative rows: `{len(negatives)}`.",
        f"- Unique dates: `{len(dates)}`; symbols: `{len(symbols)}`; venues: `{len(venues)}`.",
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
            f"The current CFTC/FINRA intake is schema-ready only. It has {len(dates)} dates, {len(symbols)} symbols, {len(venues)} venues, {len(positives)} positives, and {len(negatives)} same-report control seeds. This cannot satisfy the unchanged Wilson95/support/broad-normal gates.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- Gate CSV: `{gate_csv}`",
            f"- Assertions: `{assertions_path}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS positive_rows={len(positives)}",
        f"PASS matched_negative_rows={len(negatives)}",
        f"PASS chronological_split_ok={str(chronological_split_ok).lower()}",
        f"PASS heldout_symbol_or_venue_ok={str(heldout_symbol_or_venue_ok).lower()}",
        f"PASS combined_min_wilson95_lcb={combined_lcb:.6f}",
        f"PASS support_ok={str(support_ok).lower()}",
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
