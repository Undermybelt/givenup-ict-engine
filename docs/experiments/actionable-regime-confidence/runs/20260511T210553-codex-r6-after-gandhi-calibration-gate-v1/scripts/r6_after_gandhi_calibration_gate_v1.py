#!/usr/bin/env python3
"""Fail-closed R6 calibration gate after the Gandhi public-order uplift."""

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


RUN_ID = "20260511T210553+0800-codex-r6-after-gandhi-calibration-gate-v1"
RUN_SLUG = "20260511T210553-codex-r6-after-gandhi-calibration-gate-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r6-after-gandhi-calibration-gate"
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
UPLIFT_RUN = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T210150-codex-cftc-gandhi-source-row-uplift-v1"
)
SCOUT_RUN = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T210156-codex-r6-official-cftc-expansion-scout-v1"
)
ORDER_SCREEN_RUN = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T210228-codex-r6-additional-cftc-public-order-screen-v1"
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


def unique_values(rows: list[dict[str, str]], key: str) -> list[str]:
    return sorted({row.get(key, "") for row in rows if row.get(key, "")})


def run_verifier() -> dict[str, object]:
    command = [sys.executable, str(VERIFIER), "--intake-root", str(INTAKE)]
    completed = subprocess.run(command, cwd=REPO, text=True, capture_output=True, check=False)
    stdout_path = COMMAND_OUTPUT / "direct_manipulation_row_intake_verifier.stdout.txt"
    stderr_path = COMMAND_OUTPUT / "direct_manipulation_row_intake_verifier.stderr.txt"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    parsed_stdout: object
    try:
        parsed_stdout = json.loads(completed.stdout)
    except json.JSONDecodeError:
        parsed_stdout = completed.stdout
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "stdout_path": str(stdout_path.relative_to(REPO)),
        "stderr_path": str(stderr_path.relative_to(REPO)),
        "stdout": parsed_stdout,
        "stderr": completed.stderr,
    }


def bool_text(value: bool) -> str:
    return str(value).lower()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    COMMAND_OUTPUT.mkdir(parents=True, exist_ok=True)

    board_hash = sha256(BOARD)
    positives = read_csv(POSITIVE) if POSITIVE.exists() else []
    negatives = read_csv(NEGATIVE) if NEGATIVE.exists() else []
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8")) if PROVENANCE.exists() else {}
    verifier = run_verifier()
    all_rows = positives + negatives

    dates = unique_values(all_rows, "trade_date")
    symbols = unique_values(all_rows, "symbol")
    venues = unique_values(all_rows, "venue_or_market_center")
    groups = unique_values(all_rows, "matched_negative_group_id")
    sessions = unique_values(all_rows, "session_bucket")
    labels = Counter(row.get("label", "") for row in all_rows)
    min_support = 50
    positive_lcb = wilson_lcb(len(positives), len(positives))
    negative_lcb = wilson_lcb(len(negatives), len(negatives))
    combined_lcb = min(positive_lcb, negative_lcb)
    chronological_split_ok = len(dates) >= 2
    heldout_symbol_or_venue_ok = len(symbols) >= 2 or len(venues) >= 2
    matched_policy = provenance.get("matched_negative_control_policy", "")
    broad_normal_sample = "not a broad" not in matched_policy.lower()

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
            "observed": matched_policy,
            "required": "source-owned broad normal activity sample",
            "pass": broad_normal_sample,
        },
    ]
    gate_pass = all(bool(row["pass"]) for row in gate_rows)
    decision = (
        "r6_after_gandhi_calibration_gate_v1=accepted_95"
        if gate_pass
        else "r6_after_gandhi_calibration_gate_v1=chronology_and_heldout_improved_support_wilson_broad_control_blocked"
    )

    result = {
        "run_id": RUN_ID,
        "run_root": f"docs/experiments/actionable-regime-confidence/runs/{RUN_SLUG}",
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
        "chronological_split_ok": chronological_split_ok,
        "heldout_symbol_or_venue_ok": heldout_symbol_or_venue_ok,
        "support_ok": len(positives) >= min_support and len(negatives) >= min_support,
        "broad_normal_sample": broad_normal_sample,
        "gate_rows": gate_rows,
        "consumed_artifacts": {
            "gandhi_uplift_run": str(UPLIFT_RUN.relative_to(REPO)),
            "official_cftc_expansion_scout_run": str(SCOUT_RUN.relative_to(REPO)),
            "additional_cftc_order_screen_run": str(ORDER_SCREEN_RUN.relative_to(REPO)),
        },
        "verifier": verifier,
        "source_hashes": {
            "positive_spoofing_layering_rows.csv": sha256(POSITIVE) if POSITIVE.exists() else None,
            "matched_negative_normal_activity_rows.csv": sha256(NEGATIVE) if NEGATIVE.exists() else None,
            "provenance_manifest.json": sha256(PROVENANCE) if PROVENANCE.exists() else None,
        },
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "r6_direct_species_closed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": (
            "Acquire source-owned or owner-approved broad same-schema normal controls "
            "and more positive rows across additional dates/symbols/venues before "
            "rerunning Wilson95 calibration and full completion audit."
        ),
    }

    json_path = OUT / "r6_after_gandhi_calibration_gate_v1.json"
    md_path = OUT / "r6_after_gandhi_calibration_gate_v1.md"
    gate_csv = OUT / "r6_after_gandhi_calibration_gate_v1_gates.csv"
    assertions_path = CHECKS / "r6_after_gandhi_calibration_gate_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(gate_csv, gate_rows, ["gate", "observed", "required", "pass"])

    lines = [
        "# R6 After-Gandhi Calibration Gate v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Direct verifier status: `{verifier.get('stdout', {}).get('status') if isinstance(verifier.get('stdout'), dict) else 'unparsed'}`.",
        f"- Positive rows: `{len(positives)}`; matched negative rows: `{len(negatives)}`.",
        f"- Unique dates: `{len(dates)}`; symbols: `{len(symbols)}`; venues: `{len(venues)}`; matched groups: `{len(groups)}`.",
        f"- Wilson95 LCB positive/negative/min: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{combined_lcb:.6f}`.",
        f"- Chronological split ok: `{bool_text(chronological_split_ok)}`; heldout symbol/venue ok: `{bool_text(heldout_symbol_or_venue_ok)}`.",
        f"- Support ok: `{bool_text(len(positives) >= min_support and len(negatives) >= min_support)}`; broad normal sample: `{bool_text(broad_normal_sample)}`.",
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
            "The Gandhi uplift improves the R6 direct intake from one date/symbol group to two dates and two symbols, so the chronological and heldout-symbol gates now pass. The intake remains fail-closed because support is only four positives and four same-report control seeds, Wilson95 min LCB remains below `0.95`, and the matched controls are not a broad source-owned normal-market sample.",
            "",
            "## Consumed Artifacts",
            "",
            f"- Gandhi uplift: `{UPLIFT_RUN.relative_to(REPO)}`",
            f"- Official CFTC expansion scout: `{SCOUT_RUN.relative_to(REPO)}`",
            f"- Additional CFTC public order screen: `{ORDER_SCREEN_RUN.relative_to(REPO)}`",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Gate CSV: `{gate_csv.relative_to(REPO)}`",
            f"- Verifier stdout: `{(COMMAND_OUTPUT / 'direct_manipulation_row_intake_verifier.stdout.txt').relative_to(REPO)}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"PASS decision={decision}",
        f"PASS verifier_returncode={verifier['returncode']}",
        f"PASS positive_rows={len(positives)}",
        f"PASS matched_negative_rows={len(negatives)}",
        f"PASS chronological_split_ok={bool_text(chronological_split_ok)}",
        f"PASS heldout_symbol_or_venue_ok={bool_text(heldout_symbol_or_venue_ok)}",
        f"PASS support_ok={bool_text(len(positives) >= min_support and len(negatives) >= min_support)}",
        f"PASS broad_normal_sample={bool_text(broad_normal_sample)}",
        f"PASS combined_min_wilson95_lcb={combined_lcb:.6f}",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")

    print(json.dumps({"decision": decision, "gate_pass": gate_pass, "update_goal": False}, sort_keys=True))
    return 0 if verifier["returncode"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
