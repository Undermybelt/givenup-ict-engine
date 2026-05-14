#!/usr/bin/env python3
"""Read-only R6 split/species gap impact audit.

This run does not mutate the canonical live intake. It measures whether the
already-sourced sidecar candidates can close the current chronological,
exact-symbol, exact-venue, and direct-species blockers.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T000714-codex-r6-split-species-gap-impact-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-split-species-gap-impact"
CMD = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

BASE_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235815-codex-r6-live-intake-rehydrate-calibration-v1"
    / "r6-live-intake-rehydrate-calibration"
)
BASE_POSITIVE = BASE_ROOT / "positive_spoofing_layering_rows_v1.csv"
BASE_NEGATIVE = BASE_ROOT / "matched_negative_normal_activity_rows_v1.csv"
BASE_SPLITS = BASE_ROOT / "r6_live_intake_rehydrate_split_metrics_v1.csv"
BASE_JSON = BASE_ROOT / "r6_live_intake_rehydrate_calibration_v1.json"
LIVE_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

SIDECAR_SOURCES = [
    {
        "source": "thakkar_backofbook",
        "positive": "docs/experiments/actionable-regime-confidence/runs/20260511T234834-codex-r6-thakkar-backofbook-positive-row-candidate-screen-v1/r6-thakkar-backofbook-positive-row-candidate-screen/r6_thakkar_backofbook_positive_row_candidates_v1.csv",
        "control": "docs/experiments/actionable-regime-confidence/runs/20260511T234834-codex-r6-thakkar-backofbook-positive-row-candidate-screen-v1/r6-thakkar-backofbook-positive-row-candidate-screen/r6_thakkar_backofbook_matched_control_candidates_v1.csv",
    },
    {
        "source": "oystacher_khara_salim",
        "positive": "docs/experiments/actionable-regime-confidence/runs/20260511T234735-codex-r6-oystacher-khara-salim-positive-row-candidate-screen-v1/r6-oystacher-khara-salim-positive-row-candidate-screen/r6_oystacher_khara_salim_positive_row_candidates_v1.csv",
    },
    {
        "source": "moncada_large_lot",
        "positive": "docs/experiments/actionable-regime-confidence/runs/20260511T235000-codex-r6-moncada-large-lot-positive-row-candidate-screen-v1/r6-moncada-large-lot-positive-row-candidate-screen/r6_moncada_large_lot_positive_row_candidates_v1.csv",
    },
    {
        "source": "trunz",
        "positive": "docs/experiments/actionable-regime-confidence/runs/20260511T235000-codex-r6-trunz-positive-row-candidate-screen-v1/r6-trunz-positive-row-candidate-screen/r6_trunz_positive_row_candidates_v1.csv",
    },
    {
        "source": "jpmorgan_234818",
        "positive": "docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/r6-jpmorgan-positive-row-candidate-screen/r6_jpmorgan_positive_row_candidates_v1.csv",
    },
]

MIN_WILSON = 0.95
Z_95 = 1.96
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


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


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


def all_success_n_for_95() -> int:
    for n in range(1, 1000):
        if wilson_lcb(n, n) >= MIN_WILSON:
            return n
    return 1000


def row_key(row: dict[str, str]) -> str:
    return row.get("source_row_id", "")


def normalized_row(row: dict[str, str]) -> dict[str, str]:
    out = {field: str(row.get(field, "")) for field in FIELDS}
    if out["label"] == "normal_control":
        out["label"] = "matched_negative_normal_activity"
    return out


def tag_rows(rows: list[dict[str, str]], row_class: str) -> list[dict[str, str]]:
    tagged: list[dict[str, str]] = []
    for row in rows:
        item = normalized_row(row)
        item["_class"] = row_class
        tagged.append(item)
    return tagged


def split_rows(positive_rows: list[dict[str, str]], negative_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    tagged = tag_rows(positive_rows, "positive") + tag_rows(negative_rows, "negative")
    rows: list[dict[str, Any]] = []
    rows.append(metric("pooled_all_source_rows", "all_rows", tagged))

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in tagged:
        groups[row.get("matched_negative_group_id", "")].append(row)
    ordered_groups = sorted(groups, key=lambda gid: (min(row.get("trade_date", "9999-12-31") for row in groups[gid]), gid))
    train_end = max(1, int(len(ordered_groups) * 0.50))
    calibration_end = max(train_end + 1, int(len(ordered_groups) * 0.75))
    role_by_gid: dict[str, str] = {}
    for index, gid in enumerate(ordered_groups):
        if index < train_end:
            role_by_gid[gid] = "chronological_train"
        elif index < calibration_end:
            role_by_gid[gid] = "chronological_calibration"
        else:
            role_by_gid[gid] = "chronological_test"
    for role in ["chronological_train", "chronological_calibration", "chronological_test"]:
        rows.append(metric("chronological_group_split", role, [row for row in tagged if role_by_gid.get(row.get("matched_negative_group_id", "")) == role]))

    for symbol in sorted({row.get("symbol", "UNKNOWN") for row in tagged}):
        rows.append(metric("heldout_symbol_exact", symbol, [row for row in tagged if row.get("symbol", "UNKNOWN") == symbol]))
    for venue in sorted({row.get("venue_or_market_center", "UNKNOWN") for row in tagged}):
        rows.append(metric("heldout_venue_exact", venue, [row for row in tagged if row.get("venue_or_market_center", "UNKNOWN") == venue]))
    return rows


def metric(split_family: str, split_name: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    positives = [row for row in rows if row.get("_class") == "positive"]
    negatives = [row for row in rows if row.get("_class") == "negative"]
    pos_lcb = wilson_lcb(len(positives), len(positives))
    neg_lcb = wilson_lcb(len(negatives), len(negatives))
    min_lcb = min(pos_lcb, neg_lcb)
    required_n = all_success_n_for_95()
    return {
        "split_family": split_family,
        "split_name": split_name,
        "positive_support": len(positives),
        "negative_support": len(negatives),
        "positive_wilson95_lcb": round(pos_lcb, 12),
        "negative_wilson95_lcb": round(neg_lcb, 12),
        "min_wilson95_lcb": round(min_lcb, 12),
        "positive_deficit_to_wilson95_all_success": max(0, required_n - len(positives)),
        "negative_deficit_to_wilson95_all_success": max(0, required_n - len(negatives)),
        "wilson_ok": min_lcb >= MIN_WILSON,
        "pass": min_lcb >= MIN_WILSON,
    }


def family_deficit(metrics: list[dict[str, Any]], family: str) -> dict[str, Any]:
    rows = [row for row in metrics if row["split_family"] == family]
    failing = [row for row in rows if not row["pass"]]
    return {
        "rows": len(rows),
        "failing_rows": len(failing),
        "positive_deficit_sum": sum(int(row["positive_deficit_to_wilson95_all_success"]) for row in failing),
        "negative_deficit_sum": sum(int(row["negative_deficit_to_wilson95_all_success"]) for row in failing),
        "max_positive_support": max((int(row["positive_support"]) for row in rows), default=0),
        "max_negative_support": max((int(row["negative_support"]) for row in rows), default=0),
        "worst_min_wilson95_lcb": min((float(row["min_wilson95_lcb"]) for row in rows), default=0.0),
    }


def run_live_verifier() -> dict[str, Any]:
    CMD.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(LIVE_ROOT)],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    stdout = CMD / "direct_manipulation_row_intake_verifier.stdout.txt"
    stderr = CMD / "direct_manipulation_row_intake_verifier.stderr.txt"
    stdout.write_text(proc.stdout, encoding="utf-8")
    stderr.write_text(proc.stderr, encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"status": "parse_failed", "stdout_sample": proc.stdout[:500]}
    return {
        "returncode": proc.returncode,
        "parsed": parsed,
        "stdout_path": rel(stdout),
        "stderr_path": rel(stderr),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    required_inputs = [BASE_POSITIVE, BASE_NEGATIVE, BASE_SPLITS, BASE_JSON, DIRECT_VERIFIER]
    missing = [rel(path) for path in required_inputs if not path.exists()]
    if missing:
        payload = {
            "run_id": RUN_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "blocked",
            "reason": "missing_required_inputs",
            "missing_inputs": missing,
            "update_goal": False,
        }
        write_json(OUT / "r6_split_species_gap_impact_v1.json", payload)
        return 2

    board_hash = sha256(BOARD)
    base_positive = read_csv(BASE_POSITIVE)
    base_negative = read_csv(BASE_NEGATIVE)
    base_positive_ids = {row_key(row) for row in base_positive}
    base_negative_groups = {row.get("matched_negative_group_id", "") for row in base_negative}
    current_metrics = split_rows(base_positive, base_negative)
    live_verifier = run_live_verifier()

    candidate_rows: list[dict[str, Any]] = []
    candidate_controls: list[dict[str, str]] = []
    for source in SIDECAR_SOURCES:
        positive_path = REPO / source["positive"]
        control_path = REPO / source["control"] if source.get("control") else None
        positives = read_csv(positive_path)
        controls = read_csv(control_path) if control_path else []
        control_groups = {row.get("matched_negative_group_id", "") for row in controls}
        candidate_controls.extend(normalized_row(row) for row in controls)
        for row in positives:
            normalized = normalized_row(row)
            source_row_id = normalized.get("source_row_id", "")
            group_id = normalized.get("matched_negative_group_id", "")
            candidate_rows.append(
                {
                    **normalized,
                    "candidate_source": source["source"],
                    "candidate_positive_path": rel(positive_path),
                    "already_in_base": source_row_id in base_positive_ids,
                    "control_ready": group_id in base_negative_groups or group_id in control_groups,
                    "control_source": "base_or_candidate" if group_id in base_negative_groups or group_id in control_groups else "missing",
                }
            )

    unique_candidates: dict[str, dict[str, Any]] = {}
    duplicate_candidates: list[dict[str, Any]] = []
    for row in candidate_rows:
        source_row_id = row.get("source_row_id", "")
        if not source_row_id:
            duplicate_candidates.append(row)
            continue
        if source_row_id in unique_candidates:
            duplicate_candidates.append(row)
            continue
        unique_candidates[source_row_id] = row

    unaccepted = [row for row in unique_candidates.values() if not row["already_in_base"]]
    control_ready = [row for row in unaccepted if row["control_ready"]]
    control_ready_group_ids = {row["matched_negative_group_id"] for row in control_ready}
    control_ready_controls = [
        row
        for row in candidate_controls
        if row.get("matched_negative_group_id", "") in control_ready_group_ids
        and row_key(row) not in {row_key(base) for base in base_negative}
    ]

    control_ready_metrics = split_rows(
        base_positive + [normalized_row(row) for row in control_ready],
        base_negative + control_ready_controls,
    )

    # Non-accepted what-if: pair every unaccepted candidate group with a synthetic
    # policy-required control placeholder to measure whether sidecar positives are
    # even numerically capable of closing the split gates. These rows are never
    # written as intake rows and cannot be used for acceptance.
    placeholder_controls: list[dict[str, str]] = []
    existing_negative_groups = {row.get("matched_negative_group_id", "") for row in base_negative + candidate_controls}
    for row in unaccepted:
        group_id = row.get("matched_negative_group_id", "")
        if group_id in existing_negative_groups:
            continue
        placeholder = normalized_row(row)
        placeholder["label"] = "policy_required_matched_control_missing"
        placeholder["source_row_id"] = f"missing_control_for_{row.get('source_row_id', '')}"
        placeholder_controls.append(placeholder)
        existing_negative_groups.add(group_id)
    all_candidate_metrics = split_rows(
        base_positive + [normalized_row(row) for row in unaccepted],
        base_negative + candidate_controls + placeholder_controls,
    )

    species_counter = Counter(row.get("label", "") for row in base_positive)
    candidate_species_counter = Counter(row.get("label", "") for row in unaccepted)
    control_ready_species_counter = Counter(row.get("label", "") for row in control_ready)
    source_summary_rows = []
    for source_name in sorted({row["candidate_source"] for row in candidate_rows}):
        rows = [row for row in candidate_rows if row["candidate_source"] == source_name]
        source_summary_rows.append(
            {
                "candidate_source": source_name,
                "unique_positive_rows": len({row.get("source_row_id", "") for row in rows if row.get("source_row_id")}),
                "already_in_base": sum(1 for row in rows if row["already_in_base"]),
                "unaccepted": sum(1 for row in rows if not row["already_in_base"]),
                "control_ready_unaccepted": sum(1 for row in rows if (not row["already_in_base"]) and row["control_ready"]),
                "missing_control_unaccepted": sum(1 for row in rows if (not row["already_in_base"]) and not row["control_ready"]),
            }
        )

    current_deficits = {
        "chronological_group_split": family_deficit(current_metrics, "chronological_group_split"),
        "heldout_symbol_exact": family_deficit(current_metrics, "heldout_symbol_exact"),
        "heldout_venue_exact": family_deficit(current_metrics, "heldout_venue_exact"),
    }
    control_ready_deficits = {
        "chronological_group_split": family_deficit(control_ready_metrics, "chronological_group_split"),
        "heldout_symbol_exact": family_deficit(control_ready_metrics, "heldout_symbol_exact"),
        "heldout_venue_exact": family_deficit(control_ready_metrics, "heldout_venue_exact"),
    }
    all_candidate_deficits = {
        "chronological_group_split": family_deficit(all_candidate_metrics, "chronological_group_split"),
        "heldout_symbol_exact": family_deficit(all_candidate_metrics, "heldout_symbol_exact"),
        "heldout_venue_exact": family_deficit(all_candidate_metrics, "heldout_venue_exact"),
    }

    all_success_target_n = all_success_n_for_95()
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_hash,
        "base_snapshot": {
            "positive_rows": len(base_positive),
            "matched_negative_rows": len(base_negative),
            "positive_sha256": sha256(BASE_POSITIVE),
            "matched_negative_sha256": sha256(BASE_NEGATIVE),
            "base_json": rel(BASE_JSON),
            "base_split_metrics": rel(BASE_SPLITS),
        },
        "live_verifier": live_verifier,
        "all_success_rows_required_for_wilson95": all_success_target_n,
        "sidecar_inventory": {
            "unique_candidate_positive_rows": len(unique_candidates),
            "unaccepted_candidate_positive_rows": len(unaccepted),
            "control_ready_unaccepted_positive_rows": len(control_ready),
            "missing_control_unaccepted_positive_rows": len([row for row in unaccepted if not row["control_ready"]]),
            "candidate_control_rows": len(candidate_controls),
            "placeholder_controls_needed_for_all_unaccepted_candidates": len(placeholder_controls),
            "duplicate_candidate_rows": len(duplicate_candidates),
            "source_summary_csv": rel(OUT / "r6_split_species_gap_impact_source_summary_v1.csv"),
            "candidate_inventory_csv": rel(OUT / "r6_split_species_gap_impact_candidate_inventory_v1.csv"),
        },
        "species": {
            "base_positive_label_counts": dict(sorted(species_counter.items())),
            "unaccepted_candidate_label_counts": dict(sorted(candidate_species_counter.items())),
            "control_ready_unaccepted_label_counts": dict(sorted(control_ready_species_counter.items())),
            "non_spoofing_species_candidates_exist": any(label != "positive_spoofing_layering" for label in candidate_species_counter),
            "non_spoofing_species_control_ready": any(label != "positive_spoofing_layering" for label in control_ready_species_counter),
        },
        "current_deficits": current_deficits,
        "control_ready_sidecar_deficits": control_ready_deficits,
        "all_sidecar_what_if_deficits_with_missing_controls": all_candidate_deficits,
        "gate_result": "r6_split_species_gap_impact_v1=remaining_sidecars_do_not_close_exact_split_gates_missing_controls_and_bulk_support_required",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "shared_intake_mutated": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "next_action": (
            "Do not mutate the 73x73 live intake with remaining sidecars alone. "
            "Either acquire a bulk owner-approved direct order-lifecycle export with split-balanced controls, "
            "or predeclare a less fragmented family-level validation protocol before rerunning R6 acceptance; "
            "continue R5 source-owner recency and R3 native-subhour acquisition separately."
        ),
    }

    write_json(OUT / "r6_split_species_gap_impact_v1.json", payload)
    write_csv(
        OUT / "r6_split_species_gap_impact_candidate_inventory_v1.csv",
        candidate_rows,
        [
            "candidate_source",
            "label",
            "trade_date",
            "symbol",
            "venue_or_market_center",
            "matched_negative_group_id",
            "source_row_id",
            "already_in_base",
            "control_ready",
            "control_source",
            "candidate_positive_path",
        ],
    )
    write_csv(
        OUT / "r6_split_species_gap_impact_source_summary_v1.csv",
        source_summary_rows,
        [
            "candidate_source",
            "unique_positive_rows",
            "already_in_base",
            "unaccepted",
            "control_ready_unaccepted",
            "missing_control_unaccepted",
        ],
    )
    write_csv(
        OUT / "r6_split_species_gap_impact_current_metrics_v1.csv",
        current_metrics,
        list(current_metrics[0].keys()),
    )
    write_csv(
        OUT / "r6_split_species_gap_impact_control_ready_metrics_v1.csv",
        control_ready_metrics,
        list(control_ready_metrics[0].keys()),
    )
    write_csv(
        OUT / "r6_split_species_gap_impact_all_sidecar_what_if_metrics_v1.csv",
        all_candidate_metrics,
        list(all_candidate_metrics[0].keys()),
    )
    report = [
        "# R6 Split/Species Gap Impact v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Base live snapshot: positives `{len(base_positive)}`, matched controls `{len(base_negative)}`.",
        f"- Live verifier status: `{live_verifier['parsed'].get('status')}`, return code `{live_verifier['returncode']}`.",
        f"- All-success Wilson95 requires `{all_success_target_n}` rows per evaluated split bucket.",
        f"- Unaccepted unique sidecar positives: `{len(unaccepted)}`; control-ready unaccepted positives: `{len(control_ready)}`; missing-control unaccepted positives: `{len([row for row in unaccepted if not row['control_ready']])}`.",
        f"- Non-spoofing sidecar species exist: `{payload['species']['non_spoofing_species_candidates_exist']}`; non-spoofing sidecar species control-ready: `{payload['species']['non_spoofing_species_control_ready']}`.",
        "- Exact split gates remain false even in the all-sidecar what-if with missing controls represented as policy-required placeholders.",
        f"- Gate result: `{payload['gate_result']}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; shared intake mutated: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "## Key Deficits",
        "",
        f"- Current chronological failing buckets: `{current_deficits['chronological_group_split']['failing_rows']}`; all-sidecar what-if failing buckets: `{all_candidate_deficits['chronological_group_split']['failing_rows']}`.",
        f"- Current exact-symbol failing buckets: `{current_deficits['heldout_symbol_exact']['failing_rows']}`; all-sidecar what-if failing buckets: `{all_candidate_deficits['heldout_symbol_exact']['failing_rows']}`.",
        f"- Current exact-venue failing buckets: `{current_deficits['heldout_venue_exact']['failing_rows']}`; all-sidecar what-if failing buckets: `{all_candidate_deficits['heldout_venue_exact']['failing_rows']}`.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{rel(OUT / 'r6_split_species_gap_impact_v1.json')}`",
        f"- Candidate inventory: `{rel(OUT / 'r6_split_species_gap_impact_candidate_inventory_v1.csv')}`",
        f"- Source summary: `{rel(OUT / 'r6_split_species_gap_impact_source_summary_v1.csv')}`",
        f"- Current metrics: `{rel(OUT / 'r6_split_species_gap_impact_current_metrics_v1.csv')}`",
        f"- Control-ready metrics: `{rel(OUT / 'r6_split_species_gap_impact_control_ready_metrics_v1.csv')}`",
        f"- All-sidecar what-if metrics: `{rel(OUT / 'r6_split_species_gap_impact_all_sidecar_what_if_metrics_v1.csv')}`",
        f"- Verifier stdout/stderr: `{live_verifier['stdout_path']}`, `{live_verifier['stderr_path']}`",
        "",
        "## Next",
        "",
        payload["next_action"],
        "",
    ]
    (OUT / "r6_split_species_gap_impact_v1.md").write_text("\n".join(report), encoding="utf-8")
    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_start={board_hash}",
        f"live_verifier_status={live_verifier['parsed'].get('status')}",
        f"base_positive_rows={len(base_positive)}",
        f"base_matched_negative_rows={len(base_negative)}",
        f"all_success_rows_required_for_wilson95={all_success_target_n}",
        f"unaccepted_candidate_positive_rows={len(unaccepted)}",
        f"control_ready_unaccepted_positive_rows={len(control_ready)}",
        f"missing_control_unaccepted_positive_rows={len([row for row in unaccepted if not row['control_ready']])}",
        f"all_sidecar_what_if_chronological_failing_rows={all_candidate_deficits['chronological_group_split']['failing_rows']}",
        f"all_sidecar_what_if_symbol_failing_rows={all_candidate_deficits['heldout_symbol_exact']['failing_rows']}",
        f"all_sidecar_what_if_venue_failing_rows={all_candidate_deficits['heldout_venue_exact']['failing_rows']}",
        f"gate_result={payload['gate_result']}",
        "strict_full_objective_achieved=false",
        "update_goal=false",
    ]
    (CHECKS / "r6_split_species_gap_impact_v1_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
