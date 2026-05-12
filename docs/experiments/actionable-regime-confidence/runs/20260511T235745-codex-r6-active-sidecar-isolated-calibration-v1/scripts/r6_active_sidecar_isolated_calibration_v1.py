#!/usr/bin/env python3
"""Isolated R6 reconstruction using the current active sidecar set.

This script does not mutate the canonical shared /tmp intake. It materializes
canonical verifier filenames under this run root, then runs the existing direct
Manipulation verifier and split/support diagnostics.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


RUN_ID = "20260511T235745-codex-r6-active-sidecar-isolated-calibration-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-active-sidecar-isolated-calibration"
INTAKE = OUT / "isolated-direct-intake"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

BASE_POSITIVE = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T234414-codex-r6-direct-intake-reconstruction-v55/"
    "r6-direct-intake-reconstruction-v55/positive_spoofing_layering_rows_v55.csv"
)
BASE_NEGATIVE = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T234414-codex-r6-direct-intake-reconstruction-v55/"
    "r6-direct-intake-reconstruction-v55/matched_negative_normal_activity_rows_v55.csv"
)
SARAO_POSITIVE = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T225505-codex-r6-sarao-positive-row-candidate-screen-v1/"
    "r6-sarao-positive-row-candidate-screen/r6_sarao_positive_row_candidates_v1.csv"
)
NOWAK_POSITIVE = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T233454-codex-r6-nowak-smith-positive-row-candidate-screen-v1/"
    "r6-nowak-smith-positive-row-candidate-screen/r6_nowak_smith_positive_row_candidates_v1.csv"
)
THAKKAR_POSITIVE = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T234834-codex-r6-thakkar-backofbook-positive-row-candidate-screen-v1/"
    "r6-thakkar-backofbook-positive-row-candidate-screen/"
    "r6_thakkar_backofbook_positive_row_candidates_v1.csv"
)
THAKKAR_CONTROL = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T234834-codex-r6-thakkar-backofbook-positive-row-candidate-screen-v1/"
    "r6-thakkar-backofbook-positive-row-candidate-screen/"
    "r6_thakkar_backofbook_matched_control_candidates_v1.csv"
)
BROAD_NORMAL_CONTROLS = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1/"
    "r6-broad-normal-order-lifecycle-screen/broad_normal_market_order_lifecycle_controls_v1.csv"
)

SUPPLEMENTAL_SIDECARS = {
    "oystacher_khara_salim": REPO / (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T234735-codex-r6-oystacher-khara-salim-positive-row-candidate-screen-v1/"
        "r6-oystacher-khara-salim-positive-row-candidate-screen/"
        "r6_oystacher_khara_salim_positive_row_candidates_v1.csv"
    ),
    "jpmorgan": REPO / (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/"
        "r6-jpmorgan-positive-row-candidate-screen/r6_jpmorgan_positive_row_candidates_v1.csv"
    ),
    "moncada": REPO / (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T235000-codex-r6-moncada-large-lot-positive-row-candidate-screen-v1/"
        "r6-moncada-large-lot-positive-row-candidate-screen/"
        "r6_moncada_large_lot_positive_row_candidates_v1.csv"
    ),
    "trunz": REPO / (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T235000-codex-r6-trunz-positive-row-candidate-screen-v1/"
        "r6-trunz-positive-row-candidate-screen/r6_trunz_positive_row_candidates_v1.csv"
    ),
}

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

SIDECAR_PREFIXES = (
    "cftc_sarao_",
    "cftc_nowak_smith_",
    "cftc_jpm_",
)


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


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: Iterable[dict[str, str]], fields: list[str] = FIELDS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_generic_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def is_prior_sidecar(row: dict[str, str]) -> bool:
    sid = row.get("source_row_id", "")
    return sid.startswith(SIDECAR_PREFIXES)


def unique_by_source_row(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for row in rows:
        sid = row.get("source_row_id", "")
        if not sid or sid in seen:
            continue
        seen.add(sid)
        out.append({field: row.get(field, "") for field in FIELDS})
    return out


def normalize_positive(row: dict[str, str], note: str) -> dict[str, str]:
    normalized = {field: row.get(field, "") for field in FIELDS}
    normalized["label"] = "positive_spoofing_layering"
    if note and note not in normalized["activity_description"]:
        normalized["activity_description"] = (
            normalized["activity_description"].rstrip(".") + f". {note}"
        )
    return normalized


def generated_control(row: dict[str, str], source: str) -> dict[str, str]:
    return {
        "label": "matched_negative_normal_activity",
        "source_report": row.get("source_report", ""),
        "source_section": row.get("source_section", ""),
        "trade_date": row.get("trade_date", ""),
        "symbol": row.get("symbol", ""),
        "venue_or_market_center": row.get("venue_or_market_center", ""),
        "participant_type_code": row.get("participant_type_code", ""),
        "participant_identifier": row.get("participant_identifier", ""),
        "side": f"same-source matched context for isolated {source} preflight",
        "earliest_order_received_time": row.get("earliest_order_received_time", ""),
        "latest_order_received_time": row.get("latest_order_received_time", ""),
        "order_count": "one generated same-report control row for schema verification",
        "total_order_quantity": "source-described matched or opposite-side activity; not broad-normal background",
        "activity_description": (
            f"Generated matched-control placeholder for isolated {source} calibration "
            "preflight. This is not an accepted canonical control and not an "
            "independent broad-normal market sample."
        ),
        "matched_negative_group_id": row.get("matched_negative_group_id", ""),
        "session_bucket": row.get("session_bucket", ""),
        "source_row_id": f"{row.get('source_row_id', 'unknown')}_isolated_{source}_control",
    }


def thakkar_control_rows(positive_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    source_controls = read_rows(THAKKAR_CONTROL)
    by_group = {row.get("matched_negative_group_id", ""): row for row in source_controls}
    controls = []
    for row in positive_rows:
        group = row.get("matched_negative_group_id", "")
        source = by_group.get(group)
        if source:
            control = {field: source.get(field, "") for field in FIELDS}
            control["label"] = "matched_negative_normal_activity"
            control["source_row_id"] = f"{row.get('source_row_id')}_isolated_thakkar_control"
            control["activity_description"] = (
                source.get("activity_description", "").rstrip(".")
                + ". Duplicated per positive row only for isolated verifier count parity; "
                "not accepted into the canonical intake."
            )
        else:
            control = generated_control(row, "thakkar")
        controls.append(control)
    return controls


def wilson_all_success_lcb(n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    phat = 1.0
    denom = 1.0 + z * z / n
    centre = phat + z * z / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat) / n) + (z * z / (4 * n * n)))
    return (centre - margin) / denom


def date_key(row: dict[str, str]) -> str:
    return row.get("trade_date", "")


def split_metrics(positive_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    rows = sorted(positive_rows, key=lambda row: (date_key(row), row.get("source_row_id", "")))
    n = len(rows)
    train_end = math.ceil(n * 0.50)
    calibration_end = train_end + math.ceil((n - train_end) / 2)
    splits = [
        ("chronological", "train", rows[:train_end]),
        ("chronological", "calibration", rows[train_end:calibration_end]),
        ("chronological", "test", rows[calibration_end:]),
    ]
    metrics: list[dict[str, object]] = []
    for key, value, part in splits:
        metrics.append(
            {
                "split_key": key,
                "split_value": value,
                "rows": len(part),
                "start_trade_date": part[0].get("trade_date", "") if part else "",
                "end_trade_date": part[-1].get("trade_date", "") if part else "",
                "wilson95_lcb": f"{wilson_all_success_lcb(len(part)):.12f}",
                "support_gate": len(part) >= 50,
                "confidence_gate": len(part) >= 50 and wilson_all_success_lcb(len(part)) >= 0.95,
            }
        )
    for field in ("symbol", "venue_or_market_center"):
        counts = Counter(row.get(field, "") for row in rows)
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
            metrics.append(
                {
                    "split_key": field,
                    "split_value": value,
                    "rows": count,
                    "start_trade_date": "",
                    "end_trade_date": "",
                    "wilson95_lcb": f"{wilson_all_success_lcb(count):.12f}",
                    "support_gate": count >= 50,
                    "confidence_gate": count >= 50 and wilson_all_success_lcb(count) >= 0.95,
                }
            )
    return metrics


def count_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def run_verifier() -> tuple[int, dict[str, object]]:
    proc = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    (CMD_OUT / "direct_manipulation_row_intake_verifier.stdout.txt").write_text(
        proc.stdout, encoding="utf-8"
    )
    (CMD_OUT / "direct_manipulation_row_intake_verifier.stderr.txt").write_text(
        proc.stderr, encoding="utf-8"
    )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {"stdout": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, payload


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    INTAKE.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)

    board_hash = sha256(BOARD)
    base_positive_all = read_rows(BASE_POSITIVE)
    base_negative_all = read_rows(BASE_NEGATIVE)
    base_positive = [row for row in base_positive_all if not is_prior_sidecar(row)]
    base_negative = [row for row in base_negative_all if not is_prior_sidecar(row)]

    sarao = [
        normalize_positive(row, "Isolated active-sidecar preflight row; canonical intake not mutated.")
        for row in read_rows(SARAO_POSITIVE)
    ]
    nowak = [
        normalize_positive(row, "Isolated active-sidecar preflight row; canonical intake not mutated.")
        for row in read_rows(NOWAK_POSITIVE)
    ]
    thakkar = [
        normalize_positive(row, "Isolated active-sidecar preflight row; canonical intake not mutated.")
        for row in read_rows(THAKKAR_POSITIVE)
    ]

    active_sidecars = sarao + nowak + thakkar
    positives = unique_by_source_row(base_positive + active_sidecars)
    controls = unique_by_source_row(
        base_negative
        + [generated_control(row, "sarao") for row in sarao]
        + [generated_control(row, "nowak_smith") for row in nowak]
        + thakkar_control_rows(thakkar)
    )

    write_rows(INTAKE / "positive_spoofing_layering_rows.csv", positives)
    write_rows(INTAKE / "matched_negative_normal_activity_rows.csv", controls)

    supplemental_counts = {
        name: count_rows(path) for name, path in SUPPLEMENTAL_SIDECARS.items()
    }
    provenance = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_hash,
        "artifact_type": "isolated_active_sidecar_preflight",
        "canonical_shared_intake_mutated": False,
        "baseline_source": rel(BASE_POSITIVE),
        "baseline_positive_rows": len(base_positive),
        "baseline_matched_negative_rows": len(base_negative),
        "active_sidecars": {
            "sarao_positive_rows": len(sarao),
            "nowak_smith_positive_rows": len(nowak),
            "thakkar_positive_rows": len(thakkar),
            "thakkar_source_control_rows": count_rows(THAKKAR_CONTROL),
        },
        "supplemental_sidecar_positive_rows_not_used": supplemental_counts,
        "matched_control_policy": (
            "Sarao and Nowak/Smith controls are generated same-report placeholders "
            "for isolated schema parity. Thakkar uses source control context rows, "
            "duplicated per positive only for isolated count parity. None are "
            "accepted into the canonical shared intake by this run."
        ),
        "sidecar_broad_normal_controls_path": rel(BROAD_NORMAL_CONTROLS),
        "raw_data_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
    }
    (INTAKE / "provenance_manifest.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    verifier_returncode, verifier_payload = run_verifier()
    split_rows = split_metrics(positives)
    write_generic_csv(OUT / "r6_active_sidecar_isolated_calibration_v1_split_metrics.csv", split_rows)

    positive_lcb = wilson_all_success_lcb(len(positives))
    negative_lcb = wilson_all_success_lcb(len(controls))
    broad_normal_count = count_rows(BROAD_NORMAL_CONTROLS)
    broad_normal_lcb = wilson_all_success_lcb(broad_normal_count)
    chronological_gate = all(
        row["confidence_gate"]
        for row in split_rows
        if row["split_key"] == "chronological"
    )
    symbol_gate = any(
        row["confidence_gate"] for row in split_rows if row["split_key"] == "symbol"
    )
    venue_gate = any(
        row["confidence_gate"]
        for row in split_rows
        if row["split_key"] == "venue_or_market_center"
    )
    pooled_gate = min(positive_lcb, negative_lcb, broad_normal_lcb) >= 0.95
    gate_result = (
        "r6_active_sidecar_isolated_calibration_v1="
        "pooled_wilson95_passed_split_species_canonical_intake_still_blocked"
        if pooled_gate
        else "r6_active_sidecar_isolated_calibration_v1=confidence_still_blocked"
    )

    source_steps = [
        {
            "source": "v55_versioned_csv_after_excluding_prior_sidecars",
            "positive_rows": len(base_positive),
            "matched_negative_rows": len(base_negative),
            "accepted_into_canonical_intake": False,
        },
        {
            "source": "sarao_sidecar",
            "positive_rows": len(sarao),
            "matched_negative_rows": len(sarao),
            "accepted_into_canonical_intake": False,
        },
        {
            "source": "nowak_smith_sidecar",
            "positive_rows": len(nowak),
            "matched_negative_rows": len(nowak),
            "accepted_into_canonical_intake": False,
        },
        {
            "source": "thakkar_active_sidecar",
            "positive_rows": len(thakkar),
            "matched_negative_rows": len(thakkar),
            "accepted_into_canonical_intake": False,
        },
    ]
    write_generic_csv(OUT / "r6_active_sidecar_isolated_calibration_v1_source_steps.csv", source_steps)

    gates = [
        {"gate": "verifier_schema_ready", "observed": verifier_payload.get("status"), "pass": verifier_returncode == 0},
        {"gate": "baseline_recovered_57x57", "observed": f"{len(base_positive)}/{len(base_negative)}", "pass": len(base_positive) == 57 and len(base_negative) == 57},
        {"gate": "active_sidecar_positive_rows", "observed": len(active_sidecars), "pass": len(active_sidecars) == 16},
        {"gate": "positive_wilson95_lcb", "observed": f"{positive_lcb:.12f}", "pass": positive_lcb >= 0.95},
        {"gate": "matched_negative_wilson95_lcb", "observed": f"{negative_lcb:.12f}", "pass": negative_lcb >= 0.95},
        {"gate": "sidecar_broad_normal_wilson95_lcb", "observed": f"{broad_normal_lcb:.12f}", "pass": broad_normal_lcb >= 0.95},
        {"gate": "pooled_wilson95", "observed": f"{min(positive_lcb, negative_lcb, broad_normal_lcb):.12f}", "pass": pooled_gate},
        {"gate": "chronological_split", "observed": chronological_gate, "pass": chronological_gate},
        {"gate": "heldout_symbol", "observed": symbol_gate, "pass": symbol_gate},
        {"gate": "heldout_venue", "observed": venue_gate, "pass": venue_gate},
        {"gate": "direct_species_closed", "observed": False, "pass": False},
        {"gate": "canonical_shared_intake_mutated", "observed": False, "pass": True},
    ]
    write_generic_csv(OUT / "r6_active_sidecar_isolated_calibration_v1_gates.csv", gates)

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_hash,
        "gate_result": gate_result,
        "verifier_returncode": verifier_returncode,
        "verifier_payload": verifier_payload,
        "baseline_positive_rows": len(base_positive),
        "baseline_matched_negative_rows": len(base_negative),
        "active_sidecar_positive_rows": len(active_sidecars),
        "positive_rows": len(positives),
        "matched_negative_rows": len(controls),
        "sidecar_broad_normal_control_rows": broad_normal_count,
        "positive_wilson95_lcb": positive_lcb,
        "matched_negative_wilson95_lcb": negative_lcb,
        "sidecar_broad_normal_wilson95_lcb": broad_normal_lcb,
        "pooled_min_wilson95_lcb": min(positive_lcb, negative_lcb, broad_normal_lcb),
        "pooled_wilson95_gate": pooled_gate,
        "chronological_split_gate": chronological_gate,
        "heldout_symbol_gate": symbol_gate,
        "heldout_venue_gate": venue_gate,
        "direct_species_closed": False,
        "canonical_shared_intake_mutated": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": (
            "Promote nothing from this isolated preflight. Restore or lock the "
            "canonical shared intake, materialize accepted matched controls under "
            "policy, then rerun direct plus sidecar calibration and split/species gates."
        ),
        "artifacts": {
            "positive_rows": rel(INTAKE / "positive_spoofing_layering_rows.csv"),
            "matched_negative_rows": rel(INTAKE / "matched_negative_normal_activity_rows.csv"),
            "provenance_manifest": rel(INTAKE / "provenance_manifest.json"),
            "split_metrics": rel(OUT / "r6_active_sidecar_isolated_calibration_v1_split_metrics.csv"),
            "source_steps": rel(OUT / "r6_active_sidecar_isolated_calibration_v1_source_steps.csv"),
            "gates": rel(OUT / "r6_active_sidecar_isolated_calibration_v1_gates.csv"),
            "verifier_stdout": rel(CMD_OUT / "direct_manipulation_row_intake_verifier.stdout.txt"),
        },
    }
    (OUT / "r6_active_sidecar_isolated_calibration_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    report = f"""# R6 Active Sidecar Isolated Calibration v1

- Run id: `{RUN_ID}`
- Verifier status: `{verifier_payload.get('status')}`; return code `{verifier_returncode}`.
- Baseline reconstructed from durable V55 rows after excluding prior sidecars: `{len(base_positive)}/{len(base_negative)}`.
- Active sidecar positives materialized only in this isolated preflight: Sarao `{len(sarao)}`, Nowak/Smith `{len(nowak)}`, Thakkar `{len(thakkar)}`.
- Final isolated direct rows: positives `{len(positives)}`, matched controls `{len(controls)}`, broad-normal sidecar controls `{broad_normal_count}`.
- Pooled Wilson95 min LCB: `{min(positive_lcb, negative_lcb, broad_normal_lcb):.12f}`; pooled gate `{str(pooled_gate).lower()}`.
- Chronological split gate: `{str(chronological_gate).lower()}`; heldout symbol gate: `{str(symbol_gate).lower()}`; heldout venue gate: `{str(venue_gate).lower()}`.
- Direct species closed: `false`.
- Canonical shared intake mutated: `false`.
- Gate result: `{gate_result}`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Interpretation

This run converts the active Thakkar what-if into a durable isolated verifier packet with canonical filenames. It still does not accept a Board A confidence gate because the shared canonical intake is absent, matched controls are policy-preflight only, and chronological/symbol/venue plus species gates fail.

## Artifacts

- JSON: `{rel(OUT / 'r6_active_sidecar_isolated_calibration_v1.json')}`
- Isolated intake root: `{rel(INTAKE)}`
- Split metrics: `{rel(OUT / 'r6_active_sidecar_isolated_calibration_v1_split_metrics.csv')}`
- Gates: `{rel(OUT / 'r6_active_sidecar_isolated_calibration_v1_gates.csv')}`
- Source steps: `{rel(OUT / 'r6_active_sidecar_isolated_calibration_v1_source_steps.csv')}`
- Verifier stdout: `{rel(CMD_OUT / 'direct_manipulation_row_intake_verifier.stdout.txt')}`
- Assertions: `{rel(CHECKS / 'r6_active_sidecar_isolated_calibration_v1_assertions.out')}`
"""
    (OUT / "r6_active_sidecar_isolated_calibration_v1.md").write_text(report, encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        f"verifier_status={verifier_payload.get('status')}",
        f"baseline_positive_rows={len(base_positive)}",
        f"baseline_matched_negative_rows={len(base_negative)}",
        f"active_sidecar_positive_rows={len(active_sidecars)}",
        f"positive_rows={len(positives)}",
        f"matched_negative_rows={len(controls)}",
        f"pooled_min_wilson95_lcb={min(positive_lcb, negative_lcb, broad_normal_lcb):.12f}",
        f"pooled_wilson95_gate={str(pooled_gate).lower()}",
        f"chronological_split_gate={str(chronological_gate).lower()}",
        f"heldout_symbol_gate={str(symbol_gate).lower()}",
        f"heldout_venue_gate={str(venue_gate).lower()}",
        "canonical_shared_intake_mutated=false",
        f"gate_result={gate_result}",
        "strict_full_objective_achieved=false",
        "update_goal=false",
    ]
    (CHECKS / "r6_active_sidecar_isolated_calibration_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if verifier_returncode == 0 else verifier_returncode


if __name__ == "__main__":
    raise SystemExit(main())
