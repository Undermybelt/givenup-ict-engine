#!/usr/bin/env python3
"""Reconstruct an isolated R6 direct Manipulation intake from versioned artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import runpy
import subprocess
import sys
import types
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T234414+0800-codex-r6-direct-intake-reconstruction-v55"
RUN_SLUG = "20260511T234414-codex-r6-direct-intake-reconstruction-v55"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_SLUG
OUT = RUN_ROOT / "r6-direct-intake-reconstruction"
CHECKS = RUN_ROOT / "checks"
ISOLATED_ROOT = OUT / "isolated-direct-intake"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
V54_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T223100-codex-current-goal-completion-audit-v54-after-sidecar-calibration"
    / "completion-audit/current_goal_completion_audit_v54_after_sidecar_calibration.json"
)
SARAO_CSV = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T225505-codex-r6-sarao-positive-row-candidate-screen-v1"
    / "r6-sarao-positive-row-candidate-screen/r6_sarao_positive_row_candidates_v1.csv"
)
NOWAK_CSV = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T233454-codex-r6-nowak-smith-positive-row-candidate-screen-v1"
    / "r6-nowak-smith-positive-row-candidate-screen/r6_nowak_smith_positive_row_candidates_v1.csv"
)

FIELDS = [
    "label",
    "source_report",
    "source_section",
    "trade_date",
    "symbol",
    "venue_or_market_center",
    "participant_type_code",
    "participant_identifier",
    "side",
    "earliest_order_received_time",
    "latest_order_received_time",
    "order_count",
    "total_order_quantity",
    "activity_description",
    "matched_negative_group_id",
    "session_bucket",
    "source_row_id",
]
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


def normalize(row: dict[str, Any]) -> dict[str, str]:
    normalized = {field: str(row.get(field, "")) for field in FIELDS}
    if normalized["label"] == "normal_control":
        normalized["label"] = "matched_negative_normal_activity"
    return normalized


def add_unique(rows: list[dict[str, str]], additions: list[dict[str, Any]]) -> int:
    seen = {row["source_row_id"] for row in rows}
    added = 0
    for row in additions:
        if not isinstance(row, dict) or not row.get("source_row_id"):
            continue
        normalized = normalize(row)
        if normalized["source_row_id"] in seen:
            continue
        rows.append(normalized)
        seen.add(normalized["source_row_id"])
        added += 1
    return added


def load_script(path: Path) -> dict[str, Any]:
    # Some historical scripts import pypdf only to define helper functions. Avoid
    # adding a dependency just to read their literal row lists.
    sys.modules.setdefault("pypdf", types.SimpleNamespace(PdfReader=object))
    return runpy.run_path(str(path), run_name="__not_main__")


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def additional_successes_needed(current_successes: int) -> int:
    for total in range(current_successes, current_successes + 500):
        if wilson_lcb(total, total) >= 0.95:
            return total - current_successes
    return 500


def run_verifier(root: Path) -> dict[str, Any]:
    proc = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(root)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    stdout_path = OUT / "direct_manipulation_row_intake_verifier.stdout.txt"
    stderr_path = OUT / "direct_manipulation_row_intake_verifier.stderr.txt"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {"status": "parse_failed", "raw_stdout": proc.stdout[:500]}
    return {
        "returncode": proc.returncode,
        "payload": payload,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
    }


def cleanup_ids() -> set[str]:
    ids: set[str] = set()
    cleanup_script = (
        REPO
        / "docs/experiments/actionable-regime-confidence/runs"
        / "20260511T212004-codex-r6-shak-duplicate-row-cleanup-v1"
        / "scripts/r6_shak_duplicate_row_cleanup_v1.py"
    )
    ns = load_script(cleanup_script)
    ids.update(ns.get("POSITIVE_DUPLICATE_IDS", set()))
    ids.update(ns.get("NEGATIVE_DUPLICATE_IDS", set()))
    for rel_path in [
        "docs/experiments/actionable-regime-confidence/runs/20260511T212325-codex-r6-mohan-shak-duplicate-cleanup-v1/r6-mohan-shak-duplicate-cleanup/r6_mohan_shak_duplicate_cleanup_v1_removed_rows.csv",
        "docs/experiments/actionable-regime-confidence/runs/20260511T221210-codex-r6-logista-semantic-duplicate-cleanup-v1/r6-logista-semantic-duplicate-cleanup/r6_logista_semantic_duplicate_cleanup_removed_rows_v1.csv",
    ]:
        for row in read_csv(REPO / rel_path):
            if row.get("source_row_id"):
                ids.add(row["source_row_id"])
    return ids


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    ISOLATED_ROOT.mkdir(parents=True, exist_ok=True)

    board_hash_before = sha256(BOARD)
    positives: list[dict[str, str]] = []
    negatives: list[dict[str, str]] = []
    source_steps: list[dict[str, Any]] = []

    initial_script = (
        REPO
        / "docs/experiments/actionable-regime-confidence/runs"
        / "20260511T205239-codex-cftc-finra-direct-public-positive-probe-v1"
        / "scripts/cftc_finra_direct_public_positive_probe_v1.py"
    )
    ns = load_script(initial_script)
    added_pos = add_unique(positives, ns["cftc_positive_rows"]())
    source_steps.append({"source": rel(initial_script), "positive_added": added_pos, "negative_added": 0})

    control_script = (
        REPO
        / "docs/experiments/actionable-regime-confidence/runs"
        / "20260511T205654-codex-cftc-matched-control-seed-v1"
        / "scripts/cftc_matched_control_seed_v1.py"
    )
    ns = load_script(control_script)
    added_neg = add_unique(negatives, ns["build_controls"](positives))
    source_steps.append({"source": rel(control_script), "positive_added": 0, "negative_added": added_neg})

    addition_scripts = [
        "20260511T210150-codex-cftc-gandhi-source-row-uplift-v1/scripts/cftc_gandhi_source_row_uplift_v1.py",
        "20260511T210744-codex-r6-mohan-additional-row-uplift-v1/scripts/r6_mohan_additional_row_uplift_v1.py",
        "20260511T211201-codex-r6-mohan-shak-row-uplift-v1/scripts/r6_mohan_shak_row_uplift_v1.py",
        "20260511T211208-codex-cftc-vorley-chanu-row-uplift-calibration-v1/scripts/cftc_vorley_chanu_row_uplift_calibration_v1.py",
        "20260511T211606-codex-r6-shak-complaint-row-uplift-gate-v1/scripts/r6_shak_complaint_row_uplift_gate_v1.py",
        "20260511T211628-codex-r6-shak-cftc-row-uplift-v1/scripts/r6_shak_cftc_row_uplift_v1.py",
        "20260511T212137-codex-r6-geneva-cftc-row-uplift-v1/scripts/r6_geneva_cftc_row_uplift_v1.py",
        "20260511T213113-codex-r6-zhao-skudder-cftc-row-uplift-v1/scripts/r6_zhao_skudder_cftc_row_uplift_v1.py",
        "20260511T213312-codex-r6-flotron-cftc-row-uplift-v1/scripts/r6_flotron_cftc_row_uplift_v1.py",
        "20260511T220410-codex-r6-vorley-franko-row-uplift-v1/scripts/r6_vorley_franko_row_uplift_v1.py",
        "20260511T220755-codex-r6-official-rowlevel-support-extension-v1/scripts/r6_official_rowlevel_support_extension_v1.py",
    ]
    for rel_script in addition_scripts:
        path = REPO / "docs/experiments/actionable-regime-confidence/runs" / rel_script
        ns = load_script(path)
        positive_additions = ns.get("POSITIVE_ADDITIONS", [])
        negative_additions = ns.get("NEGATIVE_ADDITIONS", [])
        added_pos = add_unique(positives, positive_additions)
        added_neg = add_unique(negatives, negative_additions)
        source_steps.append({"source": rel(path), "positive_added": added_pos, "negative_added": added_neg})

    remove = cleanup_ids()
    before_cleanup = {"positive_rows": len(positives), "matched_negative_rows": len(negatives)}
    positives = [row for row in positives if row["source_row_id"] not in remove]
    negatives = [row for row in negatives if row["source_row_id"] not in remove]
    after_cleanup = {"positive_rows": len(positives), "matched_negative_rows": len(negatives)}

    provenance = {
        "artifact_type": "r6_direct_intake_reconstruction_v55",
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": board_hash_before,
        "source_steps": source_steps,
        "cleanup_removed_source_row_ids": sorted(remove),
        "before_cleanup": before_cleanup,
        "after_cleanup": after_cleanup,
        "policy": "isolated reconstruction only; does not mutate canonical /tmp shared intake",
    }

    positive_path = ISOLATED_ROOT / "positive_spoofing_layering_rows.csv"
    negative_path = ISOLATED_ROOT / "matched_negative_normal_activity_rows.csv"
    provenance_path = ISOLATED_ROOT / "provenance_manifest.json"
    write_csv(positive_path, positives, FIELDS)
    write_csv(negative_path, negatives, FIELDS)
    provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    verifier = run_verifier(ISOLATED_ROOT)
    v54 = json.loads(V54_JSON.read_text(encoding="utf-8"))
    v54_positive = int(v54["r6"]["positive_rows"])
    v54_negative = int(v54["r6"]["matched_negative_rows"])
    sarao_count = len(read_csv(SARAO_CSV))
    nowak_count = len(read_csv(NOWAK_CSV))
    reconstructed_positive = len(positives)
    reconstructed_negative = len(negatives)
    reconstructed_lcb = min(
        wilson_lcb(reconstructed_positive, reconstructed_positive),
        wilson_lcb(reconstructed_negative, reconstructed_negative),
    )
    v54_with_sidecars = v54_positive + sarao_count + nowak_count
    v54_sidecar_lcb = wilson_lcb(v54_with_sidecars, v54_with_sidecars)

    groups_pos = {row["matched_negative_group_id"] for row in positives}
    groups_neg = {row["matched_negative_group_id"] for row in negatives}
    gate_rows = [
        {
            "gate": "isolated_verifier_schema",
            "observed": verifier["payload"].get("status"),
            "required": "schema_ready_unscored",
            "pass": verifier["payload"].get("status") == "schema_ready_unscored",
        },
        {
            "gate": "reconstructs_v54_positive_count",
            "observed": reconstructed_positive,
            "required": v54_positive,
            "pass": reconstructed_positive == v54_positive,
        },
        {
            "gate": "reconstructs_v54_negative_count",
            "observed": reconstructed_negative,
            "required": v54_negative,
            "pass": reconstructed_negative == v54_negative,
        },
        {
            "gate": "positive_groups_have_matched_controls",
            "observed": len(groups_pos - groups_neg),
            "required": 0,
            "pass": not (groups_pos - groups_neg),
        },
        {
            "gate": "reconstructed_wilson95",
            "observed": f"{reconstructed_lcb:.12f}",
            "required": ">=0.95",
            "pass": reconstructed_lcb >= 0.95,
        },
        {
            "gate": "v54_plus_sarao_nowak_wilson95",
            "observed": f"{v54_sidecar_lcb:.12f}",
            "required": ">=0.95",
            "pass": v54_sidecar_lcb >= 0.95,
        },
    ]
    gate_result = "r6_direct_intake_reconstruction_v55=isolated_schema_ready_reconstruction_incomplete_confidence_still_blocked"
    audit = {
        "artifact_type": "r6_direct_intake_reconstruction_v55",
        "run_id": RUN_ID,
        "board_hash_before": board_hash_before,
        "isolated_root": rel(ISOLATED_ROOT),
        "isolated_files": {
            "positive_rows": rel(positive_path),
            "matched_negative_rows": rel(negative_path),
            "provenance_manifest": rel(provenance_path),
        },
        "verifier": verifier,
        "v54_baseline": {
            "positive_rows": v54_positive,
            "matched_negative_rows": v54_negative,
            "wilson95_min_lcb": v54["r6"]["wilson95_min_lcb"],
            "path": rel(V54_JSON),
        },
        "reconstruction": {
            "positive_rows": reconstructed_positive,
            "matched_negative_rows": reconstructed_negative,
            "matched_group_count": len(groups_pos & groups_neg),
            "missing_vs_v54_positive_rows": max(0, v54_positive - reconstructed_positive),
            "missing_vs_v54_negative_rows": max(0, v54_negative - reconstructed_negative),
            "wilson95_min_lcb": reconstructed_lcb,
        },
        "sidecar_candidates": {
            "sarao_positive_rows": sarao_count,
            "nowak_smith_positive_rows": nowak_count,
            "v54_what_if_positive_rows_after_both": v54_with_sidecars,
            "v54_what_if_wilson95_lcb_after_both": v54_sidecar_lcb,
            "additional_positive_rows_needed_after_both_on_v54_baseline": additional_successes_needed(v54_with_sidecars),
        },
        "gates": gate_rows,
        "gate_result": gate_result,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "shared_intake_mutated": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "next_action": (
            "Recover the missing durable source rows or rerun the row-uplift scripts under a shared lock until the isolated reconstruction "
            "matches V54 57/57 exactly, then materialize matched controls for Sarao and Nowak/Smith before calibration."
        ),
    }

    json_path = OUT / "r6_direct_intake_reconstruction_v55.json"
    gates_path = OUT / "r6_direct_intake_reconstruction_v55_gates.csv"
    source_steps_path = OUT / "r6_direct_intake_reconstruction_v55_source_steps.csv"
    report_path = OUT / "r6_direct_intake_reconstruction_v55.md"
    assertions_path = CHECKS / "r6_direct_intake_reconstruction_v55_assertions.out"
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(gates_path, gate_rows, ["gate", "observed", "required", "pass"])
    write_csv(source_steps_path, source_steps, ["source", "positive_added", "negative_added"])

    report = [
        "# R6 Direct Intake Reconstruction v55",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Isolated verifier status: `{verifier['payload'].get('status')}`.",
        f"- Isolated reconstructed rows: positives `{reconstructed_positive}`, matched negatives `{reconstructed_negative}`, matched groups `{len(groups_pos & groups_neg)}`.",
        f"- V54 durable baseline rows: positives `{v54_positive}`, matched negatives `{v54_negative}`.",
        f"- Reconstruction gap vs V54: positives `{max(0, v54_positive - reconstructed_positive)}`, matched negatives `{max(0, v54_negative - reconstructed_negative)}`.",
        f"- Reconstructed Wilson95 min LCB: `{reconstructed_lcb:.12f}`.",
        f"- Sarao plus Nowak/Smith proposed positives: `{sarao_count + nowak_count}`; V54 what-if rows `{v54_with_sidecars}`; V54 what-if Wilson95 LCB `{v54_sidecar_lcb:.12f}`.",
        f"- Additional all-correct positives still needed after both sidecars on the V54 baseline: `{additional_successes_needed(v54_with_sidecars)}`.",
        f"- Gate result: `{gate_result}`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; shared intake mutated: `false`; trade usable: `false`.",
        "",
        "## Interpretation",
        "",
        "The isolated CSVs are schema-ready, but the durable reconstruction does not reproduce the saved V54 `57/57` state. "
        "This confirms the live `/tmp` root was carrying mutable state that was not fully snapshotted as versioned row CSVs. "
        "Sarao and Nowak/Smith remain proposed positives only until matched controls are materialized and the base intake is rehydrated.",
        "",
        "## Artifacts",
        "",
        f"- Reconstruction JSON: `{rel(json_path)}`",
        f"- Isolated positive rows: `{rel(positive_path)}`",
        f"- Isolated matched controls: `{rel(negative_path)}`",
        f"- Isolated provenance: `{rel(provenance_path)}`",
        f"- Gates CSV: `{rel(gates_path)}`",
        f"- Source steps CSV: `{rel(source_steps_path)}`",
        f"- Verifier stdout/stderr: `{verifier['stdout_path']}`, `{verifier['stderr_path']}`",
        f"- Assertions: `{rel(assertions_path)}`",
        "",
    ]
    report_path.write_text("\n".join(report), encoding="utf-8")
    assertions_path.write_text(
        "\n".join(
            [
                f"run_id={RUN_ID}",
                f"board_hash_before={board_hash_before}",
                f"isolated_verifier_status={verifier['payload'].get('status')}",
                f"reconstructed_positive_rows={reconstructed_positive}",
                f"reconstructed_matched_negative_rows={reconstructed_negative}",
                f"v54_positive_rows={v54_positive}",
                f"v54_matched_negative_rows={v54_negative}",
                f"missing_vs_v54_positive_rows={max(0, v54_positive - reconstructed_positive)}",
                f"missing_vs_v54_negative_rows={max(0, v54_negative - reconstructed_negative)}",
                f"v54_sidecar_wilson95_lcb={v54_sidecar_lcb:.12f}",
                f"gate_result={gate_result}",
                "strict_full_objective_achieved=false",
                "update_goal=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
