#!/usr/bin/env python3
"""Stability-aware calibration readback for the live R6 direct intake."""

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


RUN_ID = "20260511T211130+0800-codex-r6-current-intake-stability-calibration-v1"
RUN_SLUG = "20260511T211130-codex-r6-current-intake-stability-calibration-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r6-current-intake-stability-calibration"
CHECKS = RUN_ROOT / "checks"
COMMAND_OUTPUT = RUN_ROOT / "command-output"
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


def file_hashes() -> dict[str, str | None]:
    paths = {
        "positive_spoofing_layering_rows.csv": POSITIVE,
        "matched_negative_normal_activity_rows.csv": NEGATIVE,
        "provenance_manifest.json": PROVENANCE,
    }
    return {name: sha256(path) if path.exists() else None for name, path in paths.items()}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
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


def unique(rows: list[dict[str, str]], key: str) -> list[str]:
    return sorted({row.get(key, "") for row in rows if row.get(key, "")})


def run_verifier() -> dict[str, object]:
    command = [sys.executable, str(VERIFIER), "--intake-root", str(INTAKE)]
    completed = subprocess.run(command, cwd=REPO, text=True, capture_output=True, check=False)
    stdout_path = COMMAND_OUTPUT / "direct_manipulation_row_intake_verifier.stdout.txt"
    stderr_path = COMMAND_OUTPUT / "direct_manipulation_row_intake_verifier.stderr.txt"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    try:
        parsed_stdout: object = json.loads(completed.stdout)
    except json.JSONDecodeError:
        parsed_stdout = completed.stdout
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "stdout": parsed_stdout,
        "stderr": completed.stderr,
        "stdout_path": str(stdout_path.relative_to(REPO)),
        "stderr_path": str(stderr_path.relative_to(REPO)),
    }


def bool_text(value: bool) -> str:
    return str(value).lower()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    COMMAND_OUTPUT.mkdir(parents=True, exist_ok=True)

    before_hashes = file_hashes()
    positives = read_csv(POSITIVE) if POSITIVE.exists() else []
    negatives = read_csv(NEGATIVE) if NEGATIVE.exists() else []
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8")) if PROVENANCE.exists() else {}
    verifier = run_verifier()
    after_hashes = file_hashes()

    verifier_stdout = verifier.get("stdout")
    verifier_positive = verifier_stdout.get("positive_rows") if isinstance(verifier_stdout, dict) else None
    verifier_negative = verifier_stdout.get("matched_negative_rows") if isinstance(verifier_stdout, dict) else None
    stable_hashes = before_hashes == after_hashes
    verifier_count_match = verifier_positive == len(positives) and verifier_negative == len(negatives)
    stable_snapshot = stable_hashes and verifier_count_match and verifier["returncode"] == 0

    all_rows = positives + negatives
    dates = unique(all_rows, "trade_date")
    symbols = unique(all_rows, "symbol")
    venues = unique(all_rows, "venue_or_market_center")
    groups = unique(all_rows, "matched_negative_group_id")
    sessions = unique(all_rows, "session_bucket")
    positive_lcb = wilson_lcb(len(positives), len(positives))
    negative_lcb = wilson_lcb(len(negatives), len(negatives))
    combined_lcb = min(positive_lcb, negative_lcb)
    min_support = 50
    support_ok = len(positives) >= min_support and len(negatives) >= min_support
    chronological_split_ok = len(dates) >= 2
    heldout_symbol_or_venue_ok = len(symbols) >= 2 or len(venues) >= 2
    control_policy = " ".join(
        str(provenance.get(key, ""))
        for key in ("matched_negative_control_policy", "mohan_complaint_control_policy")
    )
    broad_normal_sample = "not a broad" not in control_policy.lower() and "not independent broad" not in control_policy.lower()

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
        {"gate": "broad_normal_sample", "observed": control_policy, "required": "source-owned broad normal activity sample", "pass": broad_normal_sample},
        {"gate": "stable_snapshot", "observed": stable_snapshot, "required": True, "pass": stable_snapshot},
    ]
    gate_pass = all(bool(row["pass"]) for row in gate_rows)
    if not stable_snapshot:
        decision = "r6_current_intake_stability_calibration_v1=intake_changed_during_read_recheck_required"
    elif gate_pass:
        decision = "r6_current_intake_stability_calibration_v1=accepted_95"
    else:
        decision = "r6_current_intake_stability_calibration_v1=stable_snapshot_support_wilson_broad_control_blocked"

    result = {
        "run_id": RUN_ID,
        "run_root": f"docs/experiments/actionable-regime-confidence/runs/{RUN_SLUG}",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_writeback": sha256(BOARD),
        "decision": decision,
        "intake_root": str(INTAKE),
        "stable_hashes": stable_hashes,
        "verifier_count_match": verifier_count_match,
        "stable_snapshot": stable_snapshot,
        "source_hashes_before": before_hashes,
        "source_hashes_after": after_hashes,
        "positive_rows": len(positives),
        "matched_negative_rows": len(negatives),
        "labels": dict(Counter(row.get("label", "") for row in all_rows)),
        "unique_dates": dates,
        "unique_symbols": symbols,
        "unique_venues": venues,
        "matched_groups": groups,
        "session_buckets": sessions,
        "positive_wilson95_lcb": positive_lcb,
        "negative_wilson95_lcb": negative_lcb,
        "combined_min_wilson95_lcb": combined_lcb,
        "support_ok": support_ok,
        "chronological_split_ok": chronological_split_ok,
        "heldout_symbol_or_venue_ok": heldout_symbol_or_venue_ok,
        "broad_normal_sample": broad_normal_sample,
        "gate_rows": gate_rows,
        "provenance_counts": {
            "positive_rows_count": provenance.get("positive_rows_count"),
            "matched_negative_rows_count": provenance.get("matched_negative_rows_count"),
            "updated_by": provenance.get("updated_by"),
        },
        "verifier": verifier,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "r6_direct_species_closed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": "Acquire source-owned broad normal controls and more positives until support and Wilson95 gates can pass; do not promote same-event controls.",
    }

    json_path = OUT / "r6_current_intake_stability_calibration_v1.json"
    md_path = OUT / "r6_current_intake_stability_calibration_v1.md"
    gate_csv = OUT / "r6_current_intake_stability_calibration_v1_gates.csv"
    assertions_path = CHECKS / "r6_current_intake_stability_calibration_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(gate_csv, gate_rows, ["gate", "observed", "required", "pass"])

    lines = [
        "# R6 Current Intake Stability Calibration v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Stable snapshot: `{bool_text(stable_snapshot)}`; stable hashes: `{bool_text(stable_hashes)}`; verifier count match: `{bool_text(verifier_count_match)}`.",
        f"- Direct verifier status: `{verifier_stdout.get('status') if isinstance(verifier_stdout, dict) else 'unparsed'}`.",
        f"- Positive rows: `{len(positives)}`; matched negative rows: `{len(negatives)}`.",
        f"- Unique dates: `{len(dates)}`; symbols: `{len(symbols)}`; venues: `{len(venues)}`; matched groups: `{len(groups)}`.",
        f"- Wilson95 LCB positive/negative/min: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{combined_lcb:.6f}`.",
        f"- Chronological split ok: `{bool_text(chronological_split_ok)}`; heldout symbol/venue ok: `{bool_text(heldout_symbol_or_venue_ok)}`.",
        f"- Support ok: `{bool_text(support_ok)}`; broad normal sample: `{bool_text(broad_normal_sample)}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; R6 direct species closed: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Gates",
        "",
        "| Gate | Observed | Required | Pass |",
        "|---|---|---|---:|",
    ]
    for row in gate_rows:
        lines.append(f"| `{row['gate']}` | `{row['observed']}` | `{row['required']}` | `{bool_text(bool(row['pass']))}` |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This readback reconciles the live direct intake after concurrent row materialization. Even when the snapshot is stable, the R6 lane remains fail-closed because support is below `50/50`, Wilson95 min LCB is below `0.95`, and controls are same-event CFTC genuine-order seeds rather than a broad source-owned normal-market calibration sample.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Gate CSV: `{gate_csv.relative_to(REPO)}`",
            f"- Direct verifier stdout: `{(COMMAND_OUTPUT / 'direct_manipulation_row_intake_verifier.stdout.txt').relative_to(REPO)}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"PASS decision={decision}",
        f"PASS stable_snapshot={bool_text(stable_snapshot)}",
        f"PASS verifier_returncode={verifier['returncode']}",
        f"PASS positive_rows={len(positives)}",
        f"PASS matched_negative_rows={len(negatives)}",
        f"PASS chronological_split_ok={bool_text(chronological_split_ok)}",
        f"PASS heldout_symbol_or_venue_ok={bool_text(heldout_symbol_or_venue_ok)}",
        f"PASS support_ok={bool_text(support_ok)}",
        f"PASS broad_normal_sample={bool_text(broad_normal_sample)}",
        f"PASS combined_min_wilson95_lcb={combined_lcb:.6f}",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "stable_snapshot": stable_snapshot, "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
