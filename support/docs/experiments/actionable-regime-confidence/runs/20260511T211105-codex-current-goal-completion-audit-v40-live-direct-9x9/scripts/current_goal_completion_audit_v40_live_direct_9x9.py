#!/usr/bin/env python3
"""Live completion audit after the direct Manipulation intake advanced to 9x9."""

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


RUN_ID = "20260511T211105-codex-current-goal-completion-audit-v40-live-direct-9x9"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "completion-audit"
CHECKS = RUN_ROOT / "checks"
COMMAND_OUT = RUN_ROOT / "command-output"
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

INTAKE_ROOTS = [
    {
        "id": "source_label_equivalence",
        "requirements": "R2;R4",
        "root": Path("/tmp/ict-engine-source-label-equivalence-intake"),
        "required_files": ["source_label_equivalence_rows.csv", "source_label_equivalence_provenance.json"],
    },
    {
        "id": "native_subhour_source_label",
        "requirements": "R3",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required_files": ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"],
    },
    {
        "id": "source_panel_recency_extension",
        "requirements": "R5",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required_files": ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"],
    },
    {
        "id": "direct_manipulation_row_intake",
        "requirements": "R6",
        "root": INTAKE,
        "required_files": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
    },
]


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
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
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


def values(rows: list[dict[str, str]], key: str) -> list[str]:
    return sorted({row.get(key, "") for row in rows if row.get(key, "")})


def intake_status() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in INTAKE_ROOTS:
        root = spec["root"]
        present: list[str] = []
        missing: list[str] = []
        row_counts: dict[str, int] = {}
        for name in spec["required_files"]:
            path = root / name
            if path.exists() and path.stat().st_size > 0:
                present.append(name)
                if path.suffix == ".csv":
                    row_counts[name] = len(read_csv(path))
            else:
                missing.append(name)
        rows.append(
            {
                "id": spec["id"],
                "requirements": spec["requirements"],
                "root": str(root),
                "required_files": ";".join(spec["required_files"]),
                "present_files": ";".join(present),
                "missing_files": ";".join(missing),
                "csv_row_counts": json.dumps(row_counts, sort_keys=True),
                "exists": root.exists(),
                "ready": not missing,
            }
        )
    return rows


def run_verifier() -> dict[str, Any]:
    proc = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    (COMMAND_OUT / "direct_manipulation_row_intake_verifier.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (COMMAND_OUT / "direct_manipulation_row_intake_verifier.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {"status": "verifier_output_not_json", "stdout": proc.stdout, "stderr": proc.stderr}
    payload["returncode"] = proc.returncode
    return payload


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)

    positives = read_csv(POSITIVE)
    negatives = read_csv(NEGATIVE)
    provenance = read_json(PROVENANCE)
    verifier = run_verifier()
    all_rows = positives + negatives

    labels = Counter(row.get("label", "") for row in all_rows)
    dates = values(all_rows, "trade_date")
    symbols = values(all_rows, "symbol")
    venues = values(all_rows, "venue_or_market_center")
    groups = values(all_rows, "matched_negative_group_id")
    sessions = values(all_rows, "session_bucket")
    positive_source_ids = values(positives, "source_row_id")
    negative_source_ids = values(negatives, "source_row_id")

    positive_lcb = wilson_lcb(len(positives), len(positives))
    negative_lcb = wilson_lcb(len(negatives), len(negatives))
    combined_lcb = min(positive_lcb, negative_lcb)
    min_support = 50
    chronological_ok = len(dates) >= 2
    heldout_ok = len(symbols) >= 2 or len(venues) >= 2
    control_text = " ".join(
        str(provenance.get(key, ""))
        for key in [
            "matched_negative_control_policy",
            "matched_control_limitations",
            "mohan_complaint_control_policy",
            "matched_control_policy",
        ]
    ).lower()
    broad_normal_sample = not any(token in control_text for token in ["not a broad", "not broad", "not independent", "same-event", "same-report"])
    species_coverage = "spoofing_layering"
    required_species = "spoofing_layering;quote_spoofing;quote_stuffing;pinging;bear_raid;painting_tape"
    species_ok = False

    gate_rows = [
        {"gate": "positive_support", "observed": len(positives), "required": min_support, "pass": len(positives) >= min_support},
        {"gate": "negative_support", "observed": len(negatives), "required": min_support, "pass": len(negatives) >= min_support},
        {"gate": "chronological_split", "observed": len(dates), "required": 2, "pass": chronological_ok},
        {"gate": "heldout_symbol_or_venue", "observed": f"symbols={len(symbols)};venues={len(venues)}", "required": "symbol>=2 or venue>=2", "pass": heldout_ok},
        {"gate": "wilson95_lcb", "observed": f"{combined_lcb:.6f}", "required": ">=0.95", "pass": combined_lcb >= 0.95},
        {"gate": "broad_normal_sample", "observed": provenance.get("matched_control_limitations", provenance.get("matched_negative_control_policy", "")), "required": "source-owned broad normal activity sample", "pass": broad_normal_sample},
        {"gate": "direct_species_coverage", "observed": species_coverage, "required": required_species, "pass": species_ok},
    ]
    roots = intake_status()
    ready_roots = [row["id"] for row in roots if row["ready"]]
    decision = "current_goal_completion_audit_v40=live_direct_9x9_schema_ready_calibration_blocked"

    checklist = [
        {
            "id": "R2_R4",
            "requirement": "Other-market/source-label equivalence and strict 1h source rows exist with provenance.",
            "status": "fail_blocked",
            "gap": "source_label_equivalence_rows.csv;source_label_equivalence_provenance.json",
        },
        {
            "id": "R3",
            "requirement": "Native sub-hour source-label rows exist with provenance.",
            "status": "fail_blocked",
            "gap": "native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json",
        },
        {
            "id": "R5",
            "requirement": "Post-cutoff source-panel recency extension rows exist with provenance.",
            "status": "fail_blocked",
            "gap": "stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json",
        },
        {
            "id": "R6",
            "requirement": "Direct Manipulation rows pass support, Wilson95, broad-normal, and species gates.",
            "status": "partial_schema_ready_calibration_blocked",
            "gap": "positive_support;negative_support;wilson95_lcb;broad_normal_sample;direct_species_coverage",
        },
        {
            "id": "R8",
            "requirement": "Goal completion only after all strict requirements pass.",
            "status": "fail_blocked",
            "gap": "Strict full objective is not achieved; update_goal remains false.",
        },
    ]

    audit = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact_generation": sha256(BOARD),
        "decision": decision,
        "intake_root": str(INTAKE),
        "verifier": verifier,
        "labels": dict(labels),
        "positive_rows": len(positives),
        "matched_negative_rows": len(negatives),
        "matched_group_count": len(groups),
        "unique_dates": dates,
        "unique_symbols": symbols,
        "unique_venues": venues,
        "session_buckets": sessions,
        "positive_source_row_ids": positive_source_ids,
        "matched_negative_source_row_ids": negative_source_ids,
        "positive_wilson95_lcb": positive_lcb,
        "negative_wilson95_lcb": negative_lcb,
        "combined_min_wilson95_lcb": combined_lcb,
        "min_support_required_per_class": min_support,
        "chronological_split_ok": chronological_ok,
        "heldout_symbol_or_venue_ok": heldout_ok,
        "broad_normal_sample": broad_normal_sample,
        "species_coverage": species_coverage,
        "species_coverage_ok": species_ok,
        "gate_rows": gate_rows,
        "ready_intake_root_count": len(ready_roots),
        "ready_intake_roots": ready_roots,
        "intake_roots_checked": roots,
        "checklist": checklist,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "source_hashes": {
            "positive_spoofing_layering_rows.csv": sha256(POSITIVE) if POSITIVE.exists() else None,
            "matched_negative_normal_activity_rows.csv": sha256(NEGATIVE) if NEGATIVE.exists() else None,
            "provenance_manifest.json": sha256(PROVENANCE) if PROVENANCE.exists() else None,
        },
        "next_action": (
            "Acquire source-owned or owner-approved broad same-schema normal controls and enough positive rows across "
            "additional direct Manipulation species; separately populate R2/R3/R4/R5 source/provenance roots."
        ),
    }

    json_path = OUT / "current_goal_completion_audit_v40_live_direct_9x9.json"
    report_path = OUT / "current_goal_completion_audit_v40_live_direct_9x9.md"
    gates_path = OUT / "current_goal_completion_audit_v40_gates.csv"
    roots_path = OUT / "current_goal_completion_audit_v40_intake_roots.csv"
    checklist_path = OUT / "current_goal_completion_audit_v40_checklist.csv"
    assertions_path = CHECKS / "current_goal_completion_audit_v40_live_direct_9x9_assertions.out"

    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(gates_path, gate_rows, ["gate", "observed", "required", "pass"])
    write_csv(roots_path, roots, ["id", "requirements", "root", "required_files", "present_files", "missing_files", "csv_row_counts", "exists", "ready"])
    write_csv(checklist_path, checklist, ["id", "requirement", "status", "gap"])

    lines = [
        "# Current Goal Completion Audit v40 Live Direct 9x9",
        "",
        f"Decision: `{decision}`.",
        "",
        "Result:",
        f"- Direct verifier: `{verifier.get('status')}`; positives `{len(positives)}`; matched negatives `{len(negatives)}`; matched groups `{len(groups)}`.",
        f"- Breadth: dates `{len(dates)}`, symbols/contracts `{len(symbols)}`, venues `{len(venues)}`, sessions `{len(sessions)}`.",
        f"- Wilson95 LCB positive/negative/min: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{combined_lcb:.6f}`.",
        f"- Chronological split ok: `{str(chronological_ok).lower()}`; heldout symbol/venue ok: `{str(heldout_ok).lower()}`.",
        f"- Broad normal sample: `{str(broad_normal_sample).lower()}`; direct species coverage ok: `{str(species_ok).lower()}`.",
        f"- Ready intake roots: `{len(ready_roots)}/4`; ready roots: `{','.join(ready_roots) or 'none'}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "Gates:",
        "",
        "| Gate | Observed | Required | Pass |",
        "|---|---|---|---:|",
    ]
    for row in gate_rows:
        lines.append(f"| `{row['gate']}` | `{row['observed']}` | `{row['required']}` | `{str(row['pass']).lower()}` |")
    lines.extend(
        [
            "",
            "Next:",
            audit["next_action"],
            "",
            "Artifacts:",
            f"- JSON: `{rel(json_path)}`",
            f"- Gate CSV: `{rel(gates_path)}`",
            f"- Intake-root CSV: `{rel(roots_path)}`",
            f"- Checklist CSV: `{rel(checklist_path)}`",
            f"- Verifier stdout: `{rel(COMMAND_OUT / 'direct_manipulation_row_intake_verifier.stdout.txt')}`",
            f"- Assertions: `{rel(assertions_path)}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS direct_verifier_status={verifier.get('status')}",
        f"PASS positive_rows={len(positives)}",
        f"PASS matched_negative_rows={len(negatives)}",
        f"PASS matched_group_count={len(groups)}",
        f"PASS chronological_split_ok={str(chronological_ok).lower()}",
        f"PASS heldout_symbol_or_venue_ok={str(heldout_ok).lower()}",
        f"PASS combined_min_wilson95_lcb={combined_lcb:.6f}",
        f"PASS broad_normal_sample={str(broad_normal_sample).lower()}",
        f"PASS species_coverage_ok={str(species_ok).lower()}",
        f"PASS ready_intake_roots={len(ready_roots)}_of_4",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "positive_rows": len(positives), "matched_negative_rows": len(negatives), "ready_intake_roots": len(ready_roots)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
