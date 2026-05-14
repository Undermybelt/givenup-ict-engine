#!/usr/bin/env python3
"""Isolated R6 direct Manipulation species-extension calibration.

This run starts from the durable V57 canonical intake snapshot, adds the
already-screened Moncada large-lot quote-pressure rows in an isolated verifier
root, reruns fail-closed direct-intake checks, and calls the ict-engine runtime
surfaces required by Board A. It does not mutate the shared canonical /tmp
intake and does not fetch or commit raw provider data.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T000345-codex-r6-moncada-species-extension-calibration-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-moncada-species-extension-calibration"
INTAKE = OUT / "isolated-direct-intake"
CMD_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
STATE_DIR = Path("/tmp/ict-engine-r6-moncada-species-extension-calibration-v1-state")
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
ICT = REPO / "target/debug/ict-engine"

V57_OUT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235910-codex-r6-canonical-intake-v57-materialization-v1"
    / "r6-canonical-intake-v57-materialization"
)
V57_POSITIVE = V57_OUT / "positive_spoofing_layering_rows_v57.csv"
V57_NEGATIVE = V57_OUT / "matched_negative_normal_activity_rows_v57.csv"
V57_JSON = V57_OUT / "r6_canonical_intake_v57_materialization.json"
MONCADA_POSITIVE = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235000-codex-r6-moncada-large-lot-positive-row-candidate-screen-v1"
    / "r6-moncada-large-lot-positive-row-candidate-screen"
    / "r6_moncada_large_lot_positive_row_candidates_v1.csv"
)
SIDECAR_CONTROLS = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1"
    / "r6-broad-normal-order-lifecycle-screen"
    / "broad_normal_market_order_lifecycle_controls_v1.csv"
)
VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
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
MIN_SUPPORT = 50
MIN_WILSON = 0.95
Z_95 = 1.96
REQUIRED_DIRECT_SPECIES = [
    "spoofing_layering",
    "large_lot_quote_pressure",
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


def normalize_row(row: dict[str, str], label: str | None = None) -> dict[str, str]:
    normalized = {field: row.get(field, "") for field in FIELDS}
    if label is not None:
        normalized["label"] = label
    return normalized


def unique_by_source_row(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for row in rows:
        source_row_id = row.get("source_row_id", "")
        if not source_row_id or source_row_id in seen:
            continue
        seen.add(source_row_id)
        out.append(row)
    return out


def moncada_control(row: dict[str, str]) -> dict[str, str]:
    return {
        "label": "matched_negative_normal_activity",
        "source_report": row.get("source_report", ""),
        "source_section": row.get("source_section", ""),
        "trade_date": row.get("trade_date", ""),
        "symbol": row.get("symbol", ""),
        "venue_or_market_center": row.get("venue_or_market_center", ""),
        "participant_type_code": row.get("participant_type_code", ""),
        "participant_identifier": row.get("participant_identifier", ""),
        "side": "same-source context control for isolated Moncada species preflight",
        "earliest_order_received_time": row.get("earliest_order_received_time", ""),
        "latest_order_received_time": row.get("latest_order_received_time", ""),
        "order_count": "one generated same-source control row for schema verification",
        "total_order_quantity": "source-described same-table order-lifecycle context; not broad normal background",
        "activity_description": (
            "Generated matched-control placeholder for isolated Moncada large-lot "
            "quote-pressure species calibration. This is not accepted into the "
            "canonical shared intake and is not an independent broad-normal market sample."
        ),
        "matched_negative_group_id": row.get("matched_negative_group_id", ""),
        "session_bucket": row.get("session_bucket", ""),
        "source_row_id": f"{row.get('source_row_id', 'unknown')}_isolated_moncada_control",
    }


def chronological(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: (row.get("trade_date", ""), row.get("source_row_id", "")))
    first_cut = math.ceil(len(ordered) * 0.50)
    second_cut = math.ceil(len(ordered) * 0.75)
    buckets = [
        ("train", ordered[:first_cut]),
        ("calibration", ordered[first_cut:second_cut]),
        ("test", ordered[second_cut:]),
    ]
    out = []
    for name, bucket in buckets:
        lcb = wilson_lcb(len(bucket), len(bucket))
        out.append(
            {
                "split_key": "chronological",
                "split_value": name,
                "rows": len(bucket),
                "start_trade_date": bucket[0]["trade_date"] if bucket else "",
                "end_trade_date": bucket[-1]["trade_date"] if bucket else "",
                "wilson95_lcb": round(lcb, 12),
                "support_gate": len(bucket) >= MIN_SUPPORT,
                "confidence_gate": lcb >= MIN_WILSON,
                "pass": len(bucket) >= MIN_SUPPORT and lcb >= MIN_WILSON,
            }
        )
    return out


def split_rows(rows: list[dict[str, str]], key: str) -> list[dict[str, Any]]:
    counts = Counter(row.get(key, "") for row in rows)
    out = []
    for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        lcb = wilson_lcb(count, count)
        out.append(
            {
                "split_key": key,
                "split_value": value,
                "rows": count,
                "start_trade_date": "",
                "end_trade_date": "",
                "wilson95_lcb": round(lcb, 12),
                "support_gate": count >= MIN_SUPPORT,
                "confidence_gate": lcb >= MIN_WILSON,
                "pass": count >= MIN_SUPPORT and lcb >= MIN_WILSON,
            }
        )
    return out


def species_for_label(label: str) -> str:
    if label == "positive_order_lifecycle_large_lot_quote_pressure":
        return "large_lot_quote_pressure"
    if "large_lot" in label or "quote_pressure" in label:
        return "large_lot_quote_pressure"
    return "spoofing_layering"


def species_metrics(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    counts = Counter(species_for_label(row.get("label", "")) for row in rows)
    metrics = []
    for species in REQUIRED_DIRECT_SPECIES:
        count = counts.get(species, 0)
        lcb = wilson_lcb(count, count)
        metrics.append(
            {
                "species": species,
                "rows": count,
                "present": count > 0,
                "support_gate": count >= MIN_SUPPORT,
                "wilson95_lcb": round(lcb, 12),
                "confidence_gate": lcb >= MIN_WILSON,
                "pass": count >= MIN_SUPPORT and lcb >= MIN_WILSON,
            }
        )
    return metrics


def run_command(name: str, argv: list[str], timeout: int = 120) -> dict[str, Any]:
    proc = subprocess.run(
        argv,
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    stdout_name = f"{name}.stdout.json" if proc.stdout.lstrip().startswith(("{", "[")) else f"{name}.stdout.txt"
    stdout_path = CMD_OUT / stdout_name
    stderr_path = CMD_OUT / f"{name}.stderr.txt"
    exit_path = CMD_OUT / f"{name}.exit"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(str(proc.returncode) + "\n", encoding="utf-8")
    parsed: Any = None
    if proc.stdout.lstrip().startswith(("{", "[")):
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            parsed = None
    return {
        "argv": argv,
        "returncode": proc.returncode,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
        "exit_path": rel(exit_path),
        "stdout_first_line": proc.stdout.splitlines()[0] if proc.stdout.splitlines() else "",
        "parsed_json": parsed,
    }


def main() -> int:
    for path in (OUT, INTAKE, CMD_OUT, CHECKS, STATE_DIR):
        path.mkdir(parents=True, exist_ok=True)

    baseline_positive = [normalize_row(row) for row in read_csv(V57_POSITIVE)]
    baseline_negative = [normalize_row(row) for row in read_csv(V57_NEGATIVE)]
    moncada_positive = [
        normalize_row(row, row.get("label") or "positive_order_lifecycle_large_lot_quote_pressure")
        for row in read_csv(MONCADA_POSITIVE)
    ]
    moncada_positive = unique_by_source_row(moncada_positive)
    moncada_negative = [moncada_control(row) for row in moncada_positive]

    positive_rows = unique_by_source_row(baseline_positive + moncada_positive)
    negative_rows = unique_by_source_row(baseline_negative + moncada_negative)
    sidecar_controls = read_csv(SIDECAR_CONTROLS)

    positive_path = INTAKE / "positive_spoofing_layering_rows.csv"
    negative_path = INTAKE / "matched_negative_normal_activity_rows.csv"
    provenance_path = INTAKE / "provenance_manifest.json"
    write_csv(positive_path, positive_rows, FIELDS)
    write_csv(negative_path, negative_rows, FIELDS)
    shutil.copy2(positive_path, OUT / "positive_spoofing_layering_rows_moncada_species_v1.csv")
    shutil.copy2(negative_path, OUT / "matched_negative_normal_activity_rows_moncada_species_v1.csv")

    provenance = {
        "run_id": RUN_ID,
        "artifact_type": "isolated_moncada_species_extension_calibration",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_source_v57_json": rel(V57_JSON),
        "baseline_positive_rows": len(baseline_positive),
        "baseline_matched_negative_rows": len(baseline_negative),
        "moncada_positive_rows_added_isolated_only": len(moncada_positive),
        "moncada_matched_controls_generated_isolated_only": len(moncada_negative),
        "canonical_shared_intake_mutated": False,
        "matched_control_policy": (
            "Moncada controls are generated same-source schema controls for isolated "
            "species preflight only; they are not accepted canonical controls and not "
            "independent broad-normal samples."
        ),
        "source_v57_positive_csv": rel(V57_POSITIVE),
        "source_v57_negative_csv": rel(V57_NEGATIVE),
        "source_v57_positive_sha256": sha256(V57_POSITIVE),
        "source_v57_negative_sha256": sha256(V57_NEGATIVE),
        "moncada_candidate_csv": rel(MONCADA_POSITIVE),
        "sidecar_broad_normal_controls_path": rel(SIDECAR_CONTROLS),
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }
    write_json(provenance_path, provenance)

    verifier = run_command(
        "direct_manipulation_row_intake_verifier",
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE)],
    )
    verifier_payload = verifier.get("parsed_json") or {}

    pos_lcb = wilson_lcb(len(positive_rows), len(positive_rows))
    neg_lcb = wilson_lcb(len(negative_rows), len(negative_rows))
    sidecar_lcb = wilson_lcb(len(sidecar_controls), len(sidecar_controls))
    pooled_lcb = min(pos_lcb, neg_lcb, sidecar_lcb)
    pooled_gate = pooled_lcb >= MIN_WILSON

    split_metrics = (
        chronological(positive_rows)
        + split_rows(positive_rows, "symbol")
        + split_rows(positive_rows, "venue_or_market_center")
    )
    chronological_gate = all(row["pass"] for row in split_metrics if row["split_key"] == "chronological")
    symbol_gate = all(row["pass"] for row in split_metrics if row["split_key"] == "symbol")
    venue_gate = all(row["pass"] for row in split_metrics if row["split_key"] == "venue_or_market_center")
    species_rows = species_metrics(positive_rows)
    direct_species_closed = all(row["pass"] for row in species_rows)
    moncada_species_present = any(
        row["species"] == "large_lot_quote_pressure" and row["present"] for row in species_rows
    )

    write_csv(
        OUT / "r6_moncada_species_extension_split_metrics_v1.csv",
        split_metrics,
        [
            "split_key",
            "split_value",
            "rows",
            "start_trade_date",
            "end_trade_date",
            "wilson95_lcb",
            "support_gate",
            "confidence_gate",
            "pass",
        ],
    )
    write_csv(
        OUT / "r6_moncada_species_extension_species_metrics_v1.csv",
        species_rows,
        ["species", "rows", "present", "support_gate", "wilson95_lcb", "confidence_gate", "pass"],
    )

    chain_commands = {
        "provider_status_compact": [str(ICT), "provider-status", "--compact"],
        "auto_quant_status_agent": [
            str(ICT),
            "auto-quant-status",
            "--state-dir",
            str(STATE_DIR / "auto-quant"),
            "--output-format",
            "agent",
        ],
        "pre_bayes_status_nq": [
            str(ICT),
            "pre-bayes-status",
            "--symbol",
            "NQ",
            "--state-dir",
            str(STATE_DIR),
            "--refresh",
            "--output-format",
            "json",
        ],
        "policy_training_status_nq": [
            str(ICT),
            "policy-training-status",
            "--symbol",
            "NQ",
            "--state-dir",
            str(STATE_DIR),
            "--output-format",
            "json",
        ],
        "workflow_status_execution_candidate": [
            str(ICT),
            "workflow-status",
            "--symbol",
            "NQ",
            "--state-dir",
            str(STATE_DIR),
            "--phase",
            "execution-candidate",
            "--output-format",
            "json",
        ],
        "workflow_status_structural_feedback": [
            str(ICT),
            "workflow-status",
            "--symbol",
            "NQ",
            "--state-dir",
            str(STATE_DIR),
            "--phase",
            "structural-feedback",
            "--output-format",
            "json",
        ],
        "export_structural_path_ranking_target": [
            str(ICT),
            "export-structural-path-ranking-target",
            "--symbol",
            "NQ",
            "--state-dir",
            str(STATE_DIR),
        ],
    }
    chain_results = {name: run_command(name, argv) for name, argv in chain_commands.items()}
    chain_exit_codes = {name: result["returncode"] for name, result in chain_results.items()}

    workflow_execution = chain_results["workflow_status_execution_candidate"].get("parsed_json") or {}
    policy_training = chain_results["policy_training_status_nq"].get("parsed_json") or {}
    pre_bayes = chain_results["pre_bayes_status_nq"].get("parsed_json") or {}
    export_target = chain_results["export_structural_path_ranking_target"].get("parsed_json") or {}

    gate_result = (
        "r6_moncada_species_extension_calibration_v1="
        "pooled_wilson95_passed_nonspoofing_species_added_split_species_full_objective_still_blocked"
    )
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "isolated_intake_root": rel(INTAKE),
        "baseline_positive_rows": len(baseline_positive),
        "baseline_matched_negative_rows": len(baseline_negative),
        "moncada_positive_rows_added_isolated_only": len(moncada_positive),
        "moncada_matched_controls_generated_isolated_only": len(moncada_negative),
        "positive_rows": len(positive_rows),
        "matched_negative_rows": len(negative_rows),
        "matched_group_count": verifier_payload.get("matched_group_count"),
        "sidecar_broad_normal_control_rows": len(sidecar_controls),
        "positive_wilson95_lcb": round(pos_lcb, 12),
        "matched_negative_wilson95_lcb": round(neg_lcb, 12),
        "sidecar_broad_normal_wilson95_lcb": round(sidecar_lcb, 12),
        "pooled_min_wilson95_lcb": round(pooled_lcb, 12),
        "pooled_wilson95_gate": pooled_gate,
        "chronological_split_gate": chronological_gate,
        "heldout_symbol_gate": symbol_gate,
        "heldout_venue_gate": venue_gate,
        "moncada_species_present": moncada_species_present,
        "direct_species_closed": direct_species_closed,
        "verifier_payload": verifier_payload,
        "chain_exit_codes": chain_exit_codes,
        "chain_summary": {
            "provider_first_line": chain_results["provider_status_compact"]["stdout_first_line"],
            "auto_quant_first_line": chain_results["auto_quant_status_agent"]["stdout_first_line"],
            "pre_bayes_latest_policy": pre_bayes.get("latest_policy"),
            "policy_training_matched_rows": [
                model.get("matched_rows")
                for model in policy_training.get("entry_models", [])
            ],
            "workflow_ready": workflow_execution.get("ready"),
            "workflow_review_status": workflow_execution.get("review_status"),
            "workflow_trade_direction": workflow_execution.get("trade_direction"),
            "export_rows": export_target.get("rows"),
            "export_mature_rows": export_target.get("mature_rows"),
        },
        "gate_result": gate_result,
        "new_confidence_gate": False,
        "accepted_confidence_gate": False,
        "accepted_rows_added": 0,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "canonical_shared_intake_mutated": False,
        "trade_usable": False,
        "next_action": (
            "Do not accept R6 yet: source and materialize enough direct rows for "
            "chronological, heldout-symbol, heldout-venue, and missing direct species "
            "coverage; separately keep R5 recency and R3 native-subhour acquisition open."
        ),
        "artifacts": {
            "json": rel(OUT / "r6_moncada_species_extension_calibration_v1.json"),
            "report": rel(OUT / "r6_moncada_species_extension_calibration_v1.md"),
            "positive_rows": rel(OUT / "positive_spoofing_layering_rows_moncada_species_v1.csv"),
            "matched_negative_rows": rel(OUT / "matched_negative_normal_activity_rows_moncada_species_v1.csv"),
            "provenance_manifest": rel(provenance_path),
            "split_metrics": rel(OUT / "r6_moncada_species_extension_split_metrics_v1.csv"),
            "species_metrics": rel(OUT / "r6_moncada_species_extension_species_metrics_v1.csv"),
            "verifier_stdout": verifier["stdout_path"],
        },
    }

    json_path = OUT / "r6_moncada_species_extension_calibration_v1.json"
    report_path = OUT / "r6_moncada_species_extension_calibration_v1.md"
    assertions_path = CHECKS / "r6_moncada_species_extension_calibration_v1_assertions.out"
    write_json(json_path, result)
    report_path.write_text(
        "\n".join(
            [
                "# R6 Moncada Species Extension Calibration v1",
                "",
                f"- Run id: `{RUN_ID}`",
                f"- Baseline source: `{rel(V57_JSON)}`",
                f"- Moncada candidate source: `{rel(MONCADA_POSITIVE)}`",
                f"- Isolated verifier status: `{verifier_payload.get('status')}`; return code `{verifier['returncode']}`.",
                f"- Rows after isolated extension: positives `{len(positive_rows)}`, matched controls `{len(negative_rows)}`, matched groups `{verifier_payload.get('matched_group_count')}`.",
                f"- Added isolated Moncada large-lot quote-pressure rows: `{len(moncada_positive)}` positives and `{len(moncada_negative)}` generated same-source controls.",
                f"- Pooled Wilson95 min LCB: `{pooled_lcb:.12f}`; pooled gate `{str(pooled_gate).lower()}`.",
                f"- Chronological split gate: `{str(chronological_gate).lower()}`; heldout symbol gate `{str(symbol_gate).lower()}`; heldout venue gate `{str(venue_gate).lower()}`.",
                f"- Moncada non-spoofing species present: `{str(moncada_species_present).lower()}`; direct species closed: `{str(direct_species_closed).lower()}`.",
                f"- Provider/Auto-Quant/Pre-Bayes/CatBoost/execution-tree command exit codes: `{chain_exit_codes}`.",
                f"- Runtime readback: provider `{result['chain_summary']['provider_first_line']}`; workflow `{result['chain_summary']['workflow_review_status']}/{result['chain_summary']['workflow_trade_direction']}`; policy matched rows `{result['chain_summary']['policy_training_matched_rows']}`.",
                f"- Gate result: `{gate_result}`.",
                "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; shared intake mutated: `false`; trade usable: `false`.",
                "",
                "## Artifacts",
                f"- JSON: `{rel(json_path)}`",
                f"- Report: `{rel(report_path)}`",
                f"- Positive rows CSV: `{rel(OUT / 'positive_spoofing_layering_rows_moncada_species_v1.csv')}`",
                f"- Matched controls CSV: `{rel(OUT / 'matched_negative_normal_activity_rows_moncada_species_v1.csv')}`",
                f"- Provenance: `{rel(provenance_path)}`",
                f"- Split metrics: `{rel(OUT / 'r6_moncada_species_extension_split_metrics_v1.csv')}`",
                f"- Species metrics: `{rel(OUT / 'r6_moncada_species_extension_species_metrics_v1.csv')}`",
                f"- Command outputs: `{rel(CMD_OUT)}`",
                f"- Assertions: `{rel(assertions_path)}`",
                "",
                "## Next",
                result["next_action"],
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = [
        ("verifier_ok", verifier["returncode"] == 0 and verifier_payload.get("status") == "schema_ready_unscored"),
        ("baseline_positive_rows_73", len(baseline_positive) == 73),
        ("baseline_matched_negative_rows_73", len(baseline_negative) == 73),
        ("moncada_positive_rows_6", len(moncada_positive) == 6),
        ("positive_rows_79", len(positive_rows) == 79),
        ("matched_negative_rows_79", len(negative_rows) == 79),
        ("pooled_wilson95_passed", pooled_gate),
        ("moncada_species_present", moncada_species_present),
        ("chronological_split_still_blocked", not chronological_gate),
        ("heldout_symbol_still_blocked", not symbol_gate),
        ("heldout_venue_still_blocked", not venue_gate),
        ("direct_species_not_closed", not direct_species_closed),
        ("chain_commands_called", all(code == 0 for code in chain_exit_codes.values())),
        ("strict_full_objective_not_complete", not result["strict_full_objective_achieved"]),
        ("shared_intake_not_mutated", not result["canonical_shared_intake_mutated"]),
        ("no_runtime_code_changed", not result["runtime_code_changed"]),
    ]
    assertions_path.write_text(
        "\n".join(f"{name}={'ok' if passed else 'FAIL'}" for name, passed in assertions) + "\n",
        encoding="utf-8",
    )
    if not all(passed for _, passed in assertions):
        print(json.dumps({"ok": False, "gate_result": gate_result, "assertions": assertions}, indent=2))
        return 2

    print(
        json.dumps(
            {
                "ok": True,
                "gate_result": gate_result,
                "positive_rows": len(positive_rows),
                "pooled_lcb": round(pooled_lcb, 12),
                "strict_full_objective_achieved": False,
                "update_goal": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
