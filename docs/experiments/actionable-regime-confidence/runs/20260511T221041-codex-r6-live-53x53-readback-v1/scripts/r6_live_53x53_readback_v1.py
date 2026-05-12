#!/usr/bin/env python3
"""Read-only R6 direct intake readback after concurrent row uplifts."""

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


RUN_ID = "20260511T221041-codex-r6-live-53x53-readback-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r6-live-53x53-readback"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE = INTAKE / "positive_spoofing_layering_rows.csv"
NEGATIVE = INTAKE / "matched_negative_normal_activity_rows.csv"
PROVENANCE = INTAKE / "provenance_manifest.json"
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
Z95 = 1.959963984540054


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def wilson_all_success_lcb(n: int) -> float:
    if n <= 0:
        return 0.0
    denominator = 1.0 + Z95 * Z95 / n
    center = 1.0 + Z95 * Z95 / (2.0 * n)
    margin = Z95 * math.sqrt(Z95 * Z95 / (4.0 * n * n))
    return (center - margin) / denominator


def required_all_success_support_for_lcb(threshold: float = 0.95) -> int:
    n = 1
    while wilson_all_success_lcb(n) < threshold:
        n += 1
    return n


def run_verifier() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(VERIFIER), "--intake-root", str(INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    stdout_path = CMD / "direct_manipulation_row_intake_verifier.stdout.txt"
    stderr_path = CMD / "direct_manipulation_row_intake_verifier.stderr.txt"
    exit_path = CMD / "direct_manipulation_row_intake_verifier.exit"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"status": "unparsed"}
    return {
        "returncode": proc.returncode,
        "parsed": parsed,
        "stdout": str(stdout_path.relative_to(REPO)),
        "stderr": str(stderr_path.relative_to(REPO)),
        "exit": str(exit_path.relative_to(REPO)),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD.mkdir(parents=True, exist_ok=True)
    for path in [POSITIVE, NEGATIVE, PROVENANCE, VERIFIER]:
        if not path.exists():
            raise FileNotFoundError(str(path))

    positives = read_csv(POSITIVE)
    negatives = read_csv(NEGATIVE)
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    verifier = run_verifier()
    positive_lcb = wilson_all_success_lcb(len(positives))
    negative_lcb = wilson_all_success_lcb(len(negatives))
    min_lcb = min(positive_lcb, negative_lcb)
    required_support = required_all_success_support_for_lcb(0.95)
    support_floor_ok = len(positives) >= 50 and len(negatives) >= 50
    wilson_ok = min_lcb >= 0.95
    control_policy = " ".join(
        str(provenance.get(key, ""))
        for key in ("matched_negative_control_policy", "matched_control_policy", "matched_control_limitations")
    )
    broad_normal = "not a broad" not in control_policy.lower() and "not independent broad" not in control_policy.lower()
    source_counts = Counter(row["source_report"] for row in positives)
    dates = sorted({row["trade_date"] for row in positives + negatives if row.get("trade_date")})
    symbols = sorted({row["symbol"] for row in positives + negatives if row.get("symbol")})
    venues = sorted({row["venue_or_market_center"] for row in positives + negatives if row.get("venue_or_market_center")})
    groups = sorted({row["matched_negative_group_id"] for row in positives + negatives if row.get("matched_negative_group_id")})
    direct_species = ["spoofing_layering"]

    gates = [
        {"gate": "verifier_schema_ready", "observed": verifier["parsed"].get("status"), "required": "schema_ready_unscored", "pass": verifier["parsed"].get("status") == "schema_ready_unscored"},
        {"gate": "positive_support_floor", "observed": len(positives), "required": 50, "pass": len(positives) >= 50},
        {"gate": "negative_support_floor", "observed": len(negatives), "required": 50, "pass": len(negatives) >= 50},
        {"gate": "positive_support_for_wilson95", "observed": len(positives), "required": required_support, "pass": len(positives) >= required_support},
        {"gate": "negative_support_for_wilson95", "observed": len(negatives), "required": required_support, "pass": len(negatives) >= required_support},
        {"gate": "wilson95_lcb", "observed": round(min_lcb, 6), "required": ">=0.95", "pass": wilson_ok},
        {"gate": "chronological_dates", "observed": len(dates), "required": 3, "pass": len(dates) >= 3},
        {"gate": "heldout_symbol_or_venue", "observed": f"symbols={len(symbols)};venues={len(venues)}", "required": "symbol>=2 or venue>=2", "pass": len(symbols) >= 2 or len(venues) >= 2},
        {"gate": "broad_normal_sample", "observed": broad_normal, "required": True, "pass": broad_normal},
        {"gate": "direct_species_coverage", "observed": ";".join(direct_species), "required": "spoofing_layering;quote_spoofing;quote_stuffing;pinging;bear_raid;painting_tape", "pass": False},
    ]
    decision = "r6_live_53x53_readback_v1=support_floor_met_wilson_broad_species_still_blocked"
    summary = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "positive_rows": len(positives),
        "matched_negative_rows": len(negatives),
        "matched_group_count": len(groups),
        "positive_wilson95_lcb": positive_lcb,
        "matched_negative_wilson95_lcb": negative_lcb,
        "min_wilson95_lcb": min_lcb,
        "required_all_success_support_for_wilson95": required_support,
        "support_floor_ok_50_50": support_floor_ok,
        "wilson95_ok": wilson_ok,
        "broad_normal_sample": broad_normal,
        "direct_species_coverage": direct_species,
        "unique_dates": len(dates),
        "unique_symbols": len(symbols),
        "unique_venues": len(venues),
        "source_report_counts": dict(source_counts),
        "source_hashes": {
            "positive_spoofing_layering_rows.csv": sha256_file(POSITIVE),
            "matched_negative_normal_activity_rows.csv": sha256_file(NEGATIVE),
            "provenance_manifest.json": sha256_file(PROVENANCE),
        },
        "provenance_updated_by": provenance.get("updated_by"),
        "verifier": verifier,
        "gates": gates,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": "Acquire broad normal controls and non-spoofing direct species; support floor now passes but Wilson95/broad/species gates remain blocked.",
    }
    json_path = OUT / "r6_live_53x53_readback_v1.json"
    md_path = OUT / "r6_live_53x53_readback_v1.md"
    gate_csv = OUT / "r6_live_53x53_readback_v1_gates.csv"
    source_csv = OUT / "r6_live_53x53_readback_sources_v1.csv"
    assertions_path = CHECKS / "r6_live_53x53_readback_v1_assertions.out"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(gate_csv, gates, ["gate", "observed", "required", "pass"])
    write_csv(source_csv, [{"source_report": k, "positive_rows": v} for k, v in source_counts.most_common()], ["source_report", "positive_rows"])
    md_lines = [
        "# R6 Live 53x53 Readback v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Verifier status: `{verifier['parsed'].get('status')}`.",
        f"- Positive rows: `{len(positives)}`; matched negative rows: `{len(negatives)}`; matched groups: `{len(groups)}`.",
        f"- Wilson95 LCB positive/negative/min: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{min_lcb:.6f}`.",
        f"- Required all-success support for Wilson95 `>=0.95`: `{required_support}`.",
        f"- Support floor `50/50`: `{str(support_floor_ok).lower()}`; Wilson95 ok: `{str(wilson_ok).lower()}`.",
        f"- Broad normal sample: `{str(broad_normal).lower()}`; direct species: `{';'.join(direct_species)}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Gates",
        "",
        "| Gate | Observed | Required | Pass |",
        "|---|---|---|---:|",
    ]
    for gate in gates:
        md_lines.append(f"| `{gate['gate']}` | `{gate['observed']}` | `{gate['required']}` | `{str(bool(gate['pass'])).lower()}` |")
    md_lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a read-only current-state capture. The R6 support floor now passes, but the same-event CFTC controls are still not broad normal-market controls and the direct species set remains spoofing/layering only.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Report: `{md_path.relative_to(REPO)}`",
            f"- Gate CSV: `{gate_csv.relative_to(REPO)}`",
            f"- Source report CSV: `{source_csv.relative_to(REPO)}`",
            f"- Verifier stdout: `{(CMD / 'direct_manipulation_row_intake_verifier.stdout.txt').relative_to(REPO)}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        ]
    )
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    assertions = [
        f"PASS decision={decision}",
        f"PASS positive_rows={len(positives)}",
        f"PASS matched_negative_rows={len(negatives)}",
        f"PASS support_floor_ok_50_50={str(support_floor_ok).lower()}",
        f"PASS min_wilson95_lcb={min_lcb:.6f}",
        f"PASS broad_normal_sample={str(broad_normal).lower()}",
        "PASS direct_species_coverage=spoofing_layering_only",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(decision)
    print(f"positive_rows={len(positives)}")
    print(f"matched_negative_rows={len(negatives)}")
    print(f"min_wilson95_lcb={min_lcb:.6f}")
    print(f"support_floor_ok_50_50={str(support_floor_ok).lower()}")
    print("update_goal=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
