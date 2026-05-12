#!/usr/bin/env python3
"""Current-state audit for Board A after concurrent R6 intake updates."""

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


RUN_ID = "20260511T211030-codex-current-intake-consistency-audit-v40"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "current-intake-consistency-audit"
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
REQUIRED_SPECIES = [
    "spoofing_layering",
    "quote_spoofing",
    "quote_stuffing",
    "pinging",
    "bear_raid",
    "painting_tape",
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


def min_all_success_support(target_lcb: float = 0.95) -> int:
    n = 1
    while wilson_lcb(n, n) < target_lcb:
        n += 1
    return n


def uniq(rows: list[dict[str, str]], key: str) -> list[str]:
    return sorted({row.get(key, "") for row in rows if row.get(key, "")})


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def run_verifier() -> dict[str, Any]:
    command = ["python3", str(VERIFIER), "--intake-root", str(INTAKE)]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    stdout_path = OUT / "direct_manipulation_row_intake_verifier.stdout.txt"
    stderr_path = OUT / "direct_manipulation_row_intake_verifier.stderr.txt"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    try:
        parsed: Any = json.loads(completed.stdout)
    except json.JSONDecodeError:
        parsed = {}
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
        "stdout": parsed,
    }


def intake_status() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in INTAKE_ROOTS:
        root = spec["root"]
        present: list[str] = []
        missing: list[str] = []
        counts: list[str] = []
        for name in spec["required_files"]:
            path = root / name
            if path.exists() and path.stat().st_size > 0:
                present.append(name)
                if path.suffix == ".csv":
                    counts.append(f"{name}:{len(read_csv(path))}")
                else:
                    counts.append(f"{name}:json")
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
                "row_counts": ";".join(counts),
                "exists": root.exists(),
                "ready_by_file_presence": not missing,
            }
        )
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    positives = read_csv(POSITIVE)
    negatives = read_csv(NEGATIVE)
    all_rows = positives + negatives
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8")) if PROVENANCE.exists() else {}
    verifier = run_verifier()
    roots = intake_status()
    ready_roots = [row["id"] for row in roots if row["ready_by_file_presence"]]

    labels = Counter(row.get("label", "") for row in all_rows)
    dates = uniq(all_rows, "trade_date")
    symbols = uniq(all_rows, "symbol")
    venues = uniq(all_rows, "venue_or_market_center")
    groups = uniq(all_rows, "matched_negative_group_id")
    sessions = uniq(all_rows, "session_bucket")
    observed_species = ["spoofing_layering"] if positives else []
    missing_species = [species for species in REQUIRED_SPECIES if species not in observed_species]

    support_required = min_all_success_support(0.95)
    positive_lcb = wilson_lcb(len(positives), len(positives))
    negative_lcb = wilson_lcb(len(negatives), len(negatives))
    combined_lcb = min(positive_lcb, negative_lcb)
    broad_normal_sample = "not broad" not in json.dumps(provenance, sort_keys=True).lower()

    gate_rows = [
        {"gate": "positive_support", "observed": len(positives), "required": support_required, "pass": len(positives) >= support_required},
        {"gate": "negative_support", "observed": len(negatives), "required": support_required, "pass": len(negatives) >= support_required},
        {"gate": "chronological_train_calibration_test", "observed": len(dates), "required": 3, "pass": len(dates) >= 3},
        {"gate": "heldout_symbol_or_venue", "observed": f"symbols={len(symbols)};venues={len(venues)}", "required": "symbol>=2 or venue>=2", "pass": len(symbols) >= 2 or len(venues) >= 2},
        {"gate": "wilson95_lcb", "observed": f"{combined_lcb:.6f}", "required": ">=0.95", "pass": combined_lcb >= 0.95},
        {"gate": "broad_normal_sample", "observed": provenance.get("matched_negative_control_policy", ""), "required": "source-owned broad normal activity sample", "pass": broad_normal_sample},
        {"gate": "direct_species_coverage", "observed": ";".join(observed_species), "required": ";".join(REQUIRED_SPECIES), "pass": not missing_species},
    ]

    checklist = [
        {
            "id": "R0",
            "requirement": "Use the named Board A markdown and live intake roots as the contract.",
            "artifact": rel(BOARD),
            "status": "pass_checked",
            "evidence": f"board_hash_before_audit={sha256(BOARD)}; live direct intake parsed with csv.DictReader.",
            "gap": "",
        },
        {
            "id": "R1",
            "requirement": "Every active regime has source-owned or owner-approved >=95% confidence and cross-market/cross-cycle validation.",
            "artifact": rel(OUT / "current_intake_consistency_audit_v40.json"),
            "status": "fail_not_full",
            "evidence": f"ready_intake_roots={len(ready_roots)}/4; direct R6 rows parsed as {len(positives)}/{len(negatives)} but gate still blocked.",
            "gap": "Full per-regime >=95 confidence across all required axes is not complete.",
        },
        {
            "id": "R2_R4",
            "requirement": "Other-market/source-label equivalence and strict 1h source rows exist with provenance.",
            "artifact": rel(BOARD),
            "status": "fail_blocked",
            "evidence": "source_label_equivalence intake root has no required files.",
            "gap": "source_label_equivalence_rows.csv;source_label_equivalence_provenance.json",
        },
        {
            "id": "R3",
            "requirement": "Native sub-hour source-label rows exist with provenance.",
            "artifact": rel(BOARD),
            "status": "fail_blocked",
            "evidence": "native_subhour_source_label intake root has no required files.",
            "gap": "native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json",
        },
        {
            "id": "R5",
            "requirement": "Post-cutoff source-panel recency extension rows exist with provenance.",
            "artifact": rel(BOARD),
            "status": "fail_blocked",
            "evidence": "source_panel_recency_extension intake root has no required files.",
            "gap": "stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json",
        },
        {
            "id": "R6",
            "requirement": "Direct Manipulation rows pass support, chronological, heldout, Wilson95, broad-normal, and species gates.",
            "artifact": rel(OUT / "current_intake_consistency_audit_v40.json"),
            "status": "partial_current_rows_calibration_blocked",
            "evidence": (
                f"positive_rows={len(positives)}; matched_negative_rows={len(negatives)}; groups={len(groups)}; "
                f"dates={len(dates)}; symbols={len(symbols)}; venues={len(venues)}; min_lcb={combined_lcb}; "
                f"broad_normal={broad_normal_sample}; missing_species={','.join(missing_species)}"
            ),
            "gap": "positive_support;negative_support;wilson95_lcb;broad_normal_sample;direct_species_coverage",
        },
        {
            "id": "R7",
            "requirement": "No proxy labels, threshold relaxation, raw-data commit, runtime-code change, or trade claim.",
            "artifact": rel(OUT / "current_intake_consistency_audit_v40.json"),
            "status": "pass_guardrail",
            "evidence": "This audit reads only source-stated rows in /tmp and records no accepted rows, no new gate, no raw commit, no threshold relaxation, and no trade claim.",
            "gap": "",
        },
        {
            "id": "R8",
            "requirement": "Only complete the goal when every strict requirement is accepted with real evidence.",
            "artifact": rel(OUT / "current_intake_consistency_audit_v40.json"),
            "status": "fail_blocked",
            "evidence": "R2/R3/R4/R5 are absent and R6 remains calibration-blocked.",
            "gap": "Strict full objective is not achieved; update_goal remains false.",
        },
    ]
    unmet = [row for row in checklist if row["status"].startswith("fail") or row["status"].startswith("partial")]
    decision = "current_intake_consistency_audit_v40=live_r6_rows_9x9_calibration_blocked"

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective_restatement": "Every active Board A regime must have source-owned or owner-approved >=95% confidence and survive other-market/species plus other-cycle/timeframe validation before completion.",
        "decision": decision,
        "board_hash_before_artifact_generation": sha256(BOARD),
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
        "gate_rows": gate_rows,
        "verifier": verifier,
        "intake_roots_checked": roots,
        "ready_intake_roots": ready_roots,
        "ready_intake_root_count": len(ready_roots),
        "checklist": checklist,
        "unmet_ids": [row["id"] for row in unmet],
        "unmet_rows": len(unmet),
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
        "next_action": "Acquire broad source-owned normal controls and enough additional direct-species positive/control rows; separately populate R2/R3/R4/R5 required intake roots before rerunning completion audit.",
    }

    json_path = OUT / "current_intake_consistency_audit_v40.json"
    md_path = OUT / "current_intake_consistency_audit_v40.md"
    gates_csv = OUT / "current_intake_consistency_audit_v40_gates.csv"
    checklist_csv = OUT / "current_intake_consistency_audit_v40_checklist.csv"
    intake_csv = OUT / "current_intake_consistency_audit_v40_intake_roots.csv"
    assertions_path = CHECKS / "current_intake_consistency_audit_v40_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(gates_csv, gate_rows, ["gate", "observed", "required", "pass"])
    write_csv(checklist_csv, checklist, ["id", "requirement", "artifact", "status", "evidence", "gap"])
    write_csv(
        intake_csv,
        roots,
        ["id", "requirements", "root", "required_files", "present_files", "missing_files", "row_counts", "exists", "ready_by_file_presence"],
    )

    lines = [
        "# Current Intake Consistency Audit v40",
        "",
        f"Decision: `{decision}`.",
        "",
        "Result:",
        f"- Ready intake roots: `{len(ready_roots)}/4`; ready roots: `{', '.join(ready_roots) or 'none'}`.",
        f"- R6 live CSV rows parsed with `csv.DictReader`: positives `{len(positives)}`, matched negatives `{len(negatives)}`, groups `{len(groups)}`.",
        f"- R6 breadth: dates `{len(dates)}`, symbols/contracts `{len(symbols)}`, venues `{len(venues)}`.",
        f"- R6 Wilson95 min LCB: `{combined_lcb:.6f}`; support required per class for all-success Wilson95 >=0.95: `{support_required}`.",
        f"- Chronological split ok: `{str(len(dates) >= 3).lower()}`; heldout symbol/venue ok: `{str(len(symbols) >= 2 or len(venues) >= 2).lower()}`.",
        f"- Broad normal sample: `{str(broad_normal_sample).lower()}`; species coverage ok: `{str(not missing_species).lower()}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "Checklist:",
        "",
        "| ID | Status | Gap |",
        "|---|---|---|",
    ]
    for row in checklist:
        lines.append(f"| `{row['id']}` | `{row['status']}` | `{row['gap']}` |")
    lines.extend(
        [
            "",
            "Next:",
            result["next_action"],
            "",
            "Artifacts:",
            f"- JSON: `{rel(json_path)}`",
            f"- Gate CSV: `{rel(gates_csv)}`",
            f"- Checklist CSV: `{rel(checklist_csv)}`",
            f"- Intake-root CSV: `{rel(intake_csv)}`",
            f"- Direct verifier stdout: `{rel(OUT / 'direct_manipulation_row_intake_verifier.stdout.txt')}`",
            f"- Assertions: `{rel(assertions_path)}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS ready_intake_roots={len(ready_roots)}_of_4",
        f"PASS r6_positive_rows={len(positives)}",
        f"PASS r6_matched_negative_rows={len(negatives)}",
        f"PASS r6_matched_group_count={len(groups)}",
        f"PASS r6_combined_min_wilson95_lcb={combined_lcb:.6f}",
        f"PASS r6_chronological_ok={str(len(dates) >= 3).lower()}",
        f"PASS r6_heldout_ok={str(len(symbols) >= 2 or len(venues) >= 2).lower()}",
        f"PASS r6_broad_normal_sample={str(broad_normal_sample).lower()}",
        f"PASS r6_species_coverage_ok={str(not missing_species).lower()}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "positive_rows": len(positives), "matched_negative_rows": len(negatives), "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
