#!/usr/bin/env python3
"""Quantify the remaining R6 split/species gaps from the live canonical intake.

This run is read-only with respect to the shared /tmp intake. It exists to turn
the current "split/species still blocked" state into concrete acquisition
targets instead of another pooled-confidence readback.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T000657-codex-r6-split-species-gap-audit-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-split-species-gap-audit"
CMD_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

LIVE_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
LIVE_POSITIVE = LIVE_ROOT / "positive_spoofing_layering_rows.csv"
LIVE_NEGATIVE = LIVE_ROOT / "matched_negative_normal_activity_rows.csv"
LIVE_PROVENANCE = LIVE_ROOT / "provenance_manifest.json"

DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
CURRENT_SPLIT_METRICS = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235815-codex-r6-live-intake-rehydrate-calibration-v1"
    / "r6-live-intake-rehydrate-calibration/r6_live_intake_rehydrate_split_metrics_v1.csv"
)
CURRENT_SIDECAR_METRICS = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235815-codex-r6-live-intake-rehydrate-calibration-v1"
    / "r6-live-intake-rehydrate-calibration/r6_live_intake_rehydrate_sidecar_metrics_v1.csv"
)
SPECIES_SUMMARY = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T203523-codex-direct-manipulation-species-request-matrix-v1"
    / "direct-manipulation-species-request-matrix/direct_manipulation_species_summary_v1.csv"
)
LATEST_CHAIN_READBACK = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T000048-codex-r6-isolated-reconstruction-verification-v57"
    / "r6-isolated-reconstruction-verification/r6_isolated_reconstruction_verification_v57.json"
)

MIN_SUPPORT = 50
MIN_WILSON = 0.95
Z_95 = 1.96


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


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def required_all_successes() -> int:
    n = max(1, MIN_SUPPORT)
    while wilson_lcb(n, n) < MIN_WILSON:
        n += 1
    return n


def run_verifier() -> dict[str, Any]:
    proc = subprocess.run(
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(LIVE_ROOT)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    stdout_path = CMD_OUT / "direct_manipulation_row_intake_verifier.stdout.txt"
    stderr_path = CMD_OUT / "direct_manipulation_row_intake_verifier.stderr.txt"
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"status": "parse_failed", "stdout_sample": proc.stdout[:500]}
    return {
        "returncode": proc.returncode,
        "payload": parsed,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
    }


def split_gap_rows(required_n: int) -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(CURRENT_SPLIT_METRICS):
        pos = int(row["positive_support"])
        neg = int(row["negative_support"])
        pos_add = max(0, required_n - pos)
        neg_add = max(0, required_n - neg)
        rows.append(
            {
                "split_family": row["split_family"],
                "split_name": row["split_name"],
                "positive_support": pos,
                "negative_support": neg,
                "current_min_wilson95_lcb": row["min_wilson95_lcb"],
                "current_pass": row["pass"],
                "required_positive_support_for_95_if_all_correct": required_n,
                "required_negative_support_for_95_if_all_correct": required_n,
                "additional_positive_rows_needed_min": pos_add,
                "additional_negative_rows_needed_min": neg_add,
                "additional_pair_rows_needed_min": max(pos_add, neg_add),
            }
        )
    return rows


def summarize_split_gaps(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for family in sorted({row["split_family"] for row in rows}):
        family_rows = [row for row in rows if row["split_family"] == family]
        failing = [row for row in family_rows if str(row["current_pass"]).lower() != "true"]
        summary[family] = {
            "cells": len(family_rows),
            "failing_cells": len(failing),
            "max_pair_rows_needed_min": max((int(row["additional_pair_rows_needed_min"]) for row in failing), default=0),
            "sum_pair_rows_needed_min_if_exact_cells_must_all_pass": sum(
                int(row["additional_pair_rows_needed_min"]) for row in failing
            ),
            "worst_cells": sorted(
                failing,
                key=lambda item: int(item["additional_pair_rows_needed_min"]),
                reverse=True,
            )[:10],
        }
    return summary


def species_gap_rows() -> list[dict[str, Any]]:
    species_rows = read_csv(SPECIES_SUMMARY)
    observed = {
        "spoofing_layering": {
            "positive_rows": len(read_csv(LIVE_POSITIVE)) if LIVE_POSITIVE.exists() else 0,
            "matched_negative_rows": len(read_csv(LIVE_NEGATIVE)) if LIVE_NEGATIVE.exists() else 0,
            "status": "pooled95_ready_split_blocked",
        }
    }
    rows = []
    for row in species_rows:
        species = row["species"]
        obs = observed.get(species, {"positive_rows": 0, "matched_negative_rows": 0, "status": "absent"})
        rows.append(
            {
                "species": species,
                "observed_positive_rows": obs["positive_rows"],
                "observed_matched_negative_rows": obs["matched_negative_rows"],
                "observed_status": obs["status"],
                "candidate_surfaces": row.get("candidate_surfaces", ""),
                "ready_positive_control_sources": row.get("ready_positive_control_sources", ""),
                "prior_gate_state": row.get("gate_state", ""),
                "required_next_artifact": (
                    "source_owned_positive_rows_plus_matched_controls_plus_provenance"
                    if obs["status"] == "absent"
                    else "split_balanced_rows_and_non_spoofing_species_still_needed"
                ),
            }
        )
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    missing = [
        rel(path)
        for path in [
            BOARD,
            DIRECT_VERIFIER,
            LIVE_POSITIVE,
            LIVE_NEGATIVE,
            LIVE_PROVENANCE,
            CURRENT_SPLIT_METRICS,
            CURRENT_SIDECAR_METRICS,
            SPECIES_SUMMARY,
            LATEST_CHAIN_READBACK,
        ]
        if not path.exists()
    ]
    if missing:
        payload = {
            "run_id": RUN_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "blocked",
            "reason": "missing_required_inputs",
            "missing_inputs": missing,
            "update_goal": False,
        }
        write_json(OUT / "r6_split_species_gap_audit_v1.json", payload)
        return 2

    required_n = required_all_successes()
    verifier = run_verifier()
    split_rows = split_gap_rows(required_n)
    split_summary = summarize_split_gaps(split_rows)
    species_rows = species_gap_rows()
    chain_readback = json.loads(LATEST_CHAIN_READBACK.read_text(encoding="utf-8"))
    sidecar_metrics = read_csv(CURRENT_SIDECAR_METRICS)

    chronological_gate = split_summary["chronological_group_split"]["failing_cells"] == 0
    symbol_gate = split_summary["heldout_symbol_exact"]["failing_cells"] == 0
    venue_gate = split_summary["heldout_venue_exact"]["failing_cells"] == 0
    direct_species_closed = all(row["observed_status"] != "absent" for row in species_rows)
    verifier_ok = verifier["returncode"] == 0 and verifier["payload"].get("status") == "schema_ready_unscored"

    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "live_root": str(LIVE_ROOT),
        "live_hashes": {
            "positive_rows": sha256(LIVE_POSITIVE),
            "matched_negative_rows": sha256(LIVE_NEGATIVE),
            "provenance": sha256(LIVE_PROVENANCE),
        },
        "verifier": verifier,
        "minimum_all_success_support_for_wilson95_ge_095": required_n,
        "split_gap_csv": rel(OUT / "r6_split_species_gap_audit_v1_split_gaps.csv"),
        "species_gap_csv": rel(OUT / "r6_split_species_gap_audit_v1_species_gaps.csv"),
        "split_summary": split_summary,
        "species_summary": {
            "required_species": [row["species"] for row in species_rows],
            "observed_species": [row["species"] for row in species_rows if row["observed_status"] != "absent"],
            "missing_species": [row["species"] for row in species_rows if row["observed_status"] == "absent"],
        },
        "sidecar_metrics": sidecar_metrics,
        "latest_chain_readback": {
            "path": rel(LATEST_CHAIN_READBACK),
            "gate_result": chain_readback.get("gate_result"),
            "providers": chain_readback.get("providers"),
            "auto_quant_status_returncode": chain_readback.get("chain_readback", {}).get("auto_quant_status", {}).get("returncode"),
            "pre_bayes_returncode": chain_readback.get("chain_readback", {}).get("pre_bayes_status", {}).get("returncode"),
            "policy_training_returncode": chain_readback.get("chain_readback", {}).get("policy_training_status", {}).get("returncode"),
            "workflow_status_returncode": chain_readback.get("chain_readback", {}).get("workflow_status_execution_candidate", {}).get("returncode"),
            "path_ranking_export_returncode": chain_readback.get("chain_readback", {}).get("export_structural_path_ranking_target", {}).get("returncode"),
        },
        "decision": {
            "gate_result": "r6_split_species_gap_audit_v1=pooled95_live_ready_split_species_targets_quantified_still_blocked",
            "pooled_live_schema_ready": verifier_ok,
            "chronological_split_gate": chronological_gate,
            "heldout_symbol_gate": symbol_gate,
            "heldout_venue_gate": venue_gate,
            "direct_species_closed": direct_species_closed,
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "strict_full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "shared_intake_mutated": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Acquire source-owned direct rows that specifically fill chronological calibration/test, "
            "exact-symbol, exact-venue, and missing quote_spoofing/quote_stuffing/pinging/"
            "bear_raid/painting_tape species cells; then rerun the unchanged direct verifier, "
            "split calibration, and provider/Auto-Quant/pre-Bayes/CatBoost/workflow readback."
        ),
    }

    write_csv(
        OUT / "r6_split_species_gap_audit_v1_split_gaps.csv",
        split_rows,
        [
            "split_family",
            "split_name",
            "positive_support",
            "negative_support",
            "current_min_wilson95_lcb",
            "current_pass",
            "required_positive_support_for_95_if_all_correct",
            "required_negative_support_for_95_if_all_correct",
            "additional_positive_rows_needed_min",
            "additional_negative_rows_needed_min",
            "additional_pair_rows_needed_min",
        ],
    )
    write_csv(
        OUT / "r6_split_species_gap_audit_v1_species_gaps.csv",
        species_rows,
        [
            "species",
            "observed_positive_rows",
            "observed_matched_negative_rows",
            "observed_status",
            "candidate_surfaces",
            "ready_positive_control_sources",
            "prior_gate_state",
            "required_next_artifact",
        ],
    )
    write_json(OUT / "r6_split_species_gap_audit_v1.json", payload)

    chronological_deficits = {
        row["split_name"].replace("chronological_", ""): row["additional_pair_rows_needed_min"]
        for row in split_rows
        if row["split_family"] == "chronological_group_split"
    }

    report = f"""# R6 Split Species Gap Audit v1

- Run id: `{RUN_ID}`.
- Live canonical verifier status: `{verifier["payload"].get("status")}`.
- Live rows: positives `{verifier["payload"].get("positive_rows")}`, matched controls `{verifier["payload"].get("matched_negative_rows")}`, matched groups `{verifier["payload"].get("matched_group_count")}`.
- Minimum all-success support needed for Wilson95 LCB >= 0.95: `{required_n}` rows per positive/control side.
- Chronological split gate: `{str(chronological_gate).lower()}`; minimum pair deficits: train `{chronological_deficits.get("train")}`, calibration `{chronological_deficits.get("calibration")}`, test `{chronological_deficits.get("test")}`.
- Heldout symbol gate: `{str(symbol_gate).lower()}`; failing exact-symbol cells `{split_summary["heldout_symbol_exact"]["failing_cells"]}`.
- Heldout venue gate: `{str(venue_gate).lower()}`; failing exact-venue cells `{split_summary["heldout_venue_exact"]["failing_cells"]}`.
- Direct species closed: `{str(direct_species_closed).lower()}`; missing species `{", ".join(payload["species_summary"]["missing_species"])}`.
- Latest full-chain readback reused: `{rel(LATEST_CHAIN_READBACK)}`.
- Gate result: `{payload["decision"]["gate_result"]}`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Artifacts

- JSON: `{rel(OUT / "r6_split_species_gap_audit_v1.json")}`
- Split gaps CSV: `{rel(OUT / "r6_split_species_gap_audit_v1_split_gaps.csv")}`
- Species gaps CSV: `{rel(OUT / "r6_split_species_gap_audit_v1_species_gaps.csv")}`
- Direct verifier stdout: `{verifier["stdout_path"]}`

## Next

Acquire source-owned direct rows that specifically fill chronological calibration/test, exact-symbol, exact-venue, and missing non-spoofing species cells; then rerun the unchanged direct verifier, split calibration, and provider/Auto-Quant/pre-Bayes/CatBoost/workflow readback.
"""
    (OUT / "r6_split_species_gap_audit_v1.md").write_text(report, encoding="utf-8")

    checks = [
        ("live_verifier_schema_ready", verifier_ok),
        ("live_positive_rows_73", verifier["payload"].get("positive_rows") == 73),
        ("live_matched_negative_rows_73", verifier["payload"].get("matched_negative_rows") == 73),
        ("required_support_is_73", required_n == 73),
        ("chronological_split_still_blocked", not chronological_gate),
        ("heldout_symbol_still_blocked", not symbol_gate),
        ("heldout_venue_still_blocked", not venue_gate),
        ("direct_species_not_closed", not direct_species_closed),
        ("strict_full_objective_not_complete", payload["decision"]["strict_full_objective_achieved"] is False),
        ("update_goal_false", payload["decision"]["update_goal"] is False),
    ]
    checks_path = CHECKS / "r6_split_species_gap_audit_v1_assertions.out"
    checks_path.parent.mkdir(parents=True, exist_ok=True)
    checks_path.write_text(
        "".join(f"{name}={'PASS' if passed else 'FAIL'}\n" for name, passed in checks),
        encoding="utf-8",
    )
    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
