#!/usr/bin/env python3
"""Read-only calibration over live R6 positives and sidecar broad-normal controls."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T222600-codex-r6-sidecar-broad-normal-calibration-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-sidecar-broad-normal-calibration"
COMMAND_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

LIVE_INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE_NAME = "positive_spoofing_layering_rows.csv"
NEGATIVE_NAME = "matched_negative_normal_activity_rows.csv"
SIDECAR = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1"
    / "r6-broad-normal-order-lifecycle-screen/broad_normal_market_order_lifecycle_controls_v1.csv"
)
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

MIN_SUPPORT = 50
MIN_WILSON = 0.95
Z_95 = 1.96
MISSING_DIRECT_SPECIES = [
    "quote_stuffing",
    "pinging",
    "bear_raid_or_painting_tape",
    "pump_dump_social_text_or_twitter",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def additional_successes_needed(current_successes: int, threshold: float = MIN_WILSON) -> int:
    for total in range(current_successes, current_successes + 500):
        if wilson_lcb(total, total) >= threshold:
            return total - current_successes
    return 500


def run_command(name: str, cmd: list[str], timeout: int = 45) -> dict[str, object]:
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)
    stdout_path = COMMAND_OUT / f"{name}.stdout.txt"
    stderr_path = COMMAND_OUT / f"{name}.stderr.txt"
    completed = subprocess.run(
        cmd,
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    return {
        "name": name,
        "cmd": cmd,
        "returncode": completed.returncode,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
    }


def parse_command_json(command: dict[str, object]) -> dict[str, object] | None:
    path = Path(str(command.get("stdout_path", "")))
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def group_counts(rows: list[dict[str, str]], field: str) -> list[dict[str, object]]:
    counts = Counter(" ".join((row.get(field, "") or "UNKNOWN").split()) for row in rows)
    return [{"name": name, "count": count} for name, count in sorted(counts.items())]


def chronological_split_support(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get("matched_negative_group_id", "")].append(row)
    ordered = sorted(
        groups,
        key=lambda gid: (min(row.get("trade_date", "9999-12-31") for row in groups[gid]), gid),
    )
    train_end = max(1, int(len(ordered) * 0.50))
    calibration_end = max(train_end + 1, int(len(ordered) * 0.75))
    split_rows = {"chronological_train": [], "chronological_calibration": [], "chronological_test": []}
    for index, gid in enumerate(ordered):
        if index < train_end:
            split = "chronological_train"
        elif index < calibration_end:
            split = "chronological_calibration"
        else:
            split = "chronological_test"
        split_rows[split].extend(groups[gid])
    return [
        {
            "split": split,
            "positive_support": len(rows_for_split),
            "positive_wilson95_lcb": round(wilson_lcb(len(rows_for_split), len(rows_for_split)), 12),
            "support_ok": len(rows_for_split) >= MIN_SUPPORT,
            "wilson_ok": wilson_lcb(len(rows_for_split), len(rows_for_split)) >= MIN_WILSON,
        }
        for split, rows_for_split in split_rows.items()
    ]


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intake-root", default=str(LIVE_INTAKE))
    parser.add_argument("--sidecar", default=str(SIDECAR))
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)

    intake = Path(args.intake_root)
    positive_path = intake / POSITIVE_NAME
    same_event_negative_path = intake / NEGATIVE_NAME
    sidecar_path = Path(args.sidecar)
    missing = [str(path) for path in [positive_path, same_event_negative_path, sidecar_path] if not path.exists()]
    if missing:
        raise SystemExit(f"missing required files: {missing}")

    direct_verifier_command = run_command(
        "direct_manipulation_row_intake_verifier",
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(intake)],
    )
    direct_verifier = parse_command_json(direct_verifier_command)

    positives = read_csv(positive_path)
    same_event_negatives = read_csv(same_event_negative_path)
    broad_controls = read_csv(sidecar_path)

    broad_labels = sorted({row.get("label", "") for row in broad_controls})
    broad_source_gate = (
        len(broad_controls) >= MIN_SUPPORT
        and broad_labels == ["independent_broad_normal_order_lifecycle_control"]
        and all("ITCH" in row.get("source_report", "") for row in broad_controls)
    )
    positive_lcb = wilson_lcb(len(positives), len(positives))
    broad_lcb = wilson_lcb(len(broad_controls), len(broad_controls))
    pooled_sidecar_min_lcb = min(positive_lcb, broad_lcb)
    pooled_gate = (
        len(positives) >= MIN_SUPPORT
        and len(broad_controls) >= MIN_SUPPORT
        and pooled_sidecar_min_lcb >= MIN_WILSON
    )
    positive_split_metrics = chronological_split_support(positives)
    positive_split_gate = all(metric["support_ok"] and metric["wilson_ok"] for metric in positive_split_metrics)
    direct_species_closed = False
    accepted_gate = pooled_gate and broad_source_gate and positive_split_gate and direct_species_closed

    additional_positive_rows_for_pooled_95 = additional_successes_needed(len(positives))
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": (
            "r6_sidecar_broad_normal_calibration_v1="
            "broad_normal_sidecar_available_positive_split_species_still_blocked"
        ),
        "board_hash_before_start": sha256(BOARD) if BOARD.exists() else None,
        "intake_root": str(intake),
        "sidecar_path": str(sidecar_path),
        "input_hashes": {
            POSITIVE_NAME: sha256(positive_path),
            NEGATIVE_NAME: sha256(same_event_negative_path),
            "broad_normal_market_order_lifecycle_controls_v1.csv": sha256(sidecar_path),
        },
        "direct_verifier_command": direct_verifier_command,
        "direct_verifier": direct_verifier,
        "positive_rows": len(positives),
        "same_event_negative_rows": len(same_event_negatives),
        "broad_normal_sidecar_rows": len(broad_controls),
        "broad_normal_sidecar_gate": broad_source_gate,
        "positive_wilson95_lcb": round(positive_lcb, 12),
        "broad_normal_wilson95_lcb": round(broad_lcb, 12),
        "pooled_sidecar_min_wilson95_lcb": round(pooled_sidecar_min_lcb, 12),
        "pooled_sidecar_gate": pooled_gate,
        "positive_chronological_split_gate": positive_split_gate,
        "positive_chronological_split_metrics": positive_split_metrics,
        "direct_species_closed": direct_species_closed,
        "missing_direct_species": MISSING_DIRECT_SPECIES,
        "accepted_gate": accepted_gate,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "shared_intake_mutated": False,
        "additional_positive_rows_for_pooled_95": additional_positive_rows_for_pooled_95,
        "next_action": (
            "Acquire source-owned positive direct rows: at least "
            f"{additional_positive_rows_for_pooled_95} more for pooled Wilson95, and more for chronological/symbol/venue split support; "
            "then rerun calibration with sidecar broad-normal controls."
        ),
        "symbol_counts": group_counts(positives, "symbol"),
        "venue_counts": group_counts(positives, "venue_or_market_center"),
        "broad_control_symbol_counts": group_counts(broad_controls, "symbol"),
    }

    json_path = OUT / "r6_sidecar_broad_normal_calibration_v1.json"
    report_path = OUT / "r6_sidecar_broad_normal_calibration_v1.md"
    split_path = OUT / "r6_sidecar_broad_normal_positive_split_metrics_v1.csv"
    assertions_path = CHECKS / "r6_sidecar_broad_normal_calibration_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        split_path,
        positive_split_metrics,
        ["split", "positive_support", "positive_wilson95_lcb", "support_ok", "wilson_ok"],
    )

    lines = [
        "# R6 Sidecar Broad Normal Calibration v1",
        "",
        f"- Decision: `{result['decision']}`.",
        f"- Live R6 positives: `{len(positives)}`; same-event controls: `{len(same_event_negatives)}`; sidecar broad-normal controls: `{len(broad_controls)}`.",
        f"- Broad-normal sidecar gate: `{str(broad_source_gate).lower()}`; broad-normal Wilson95 LCB: `{broad_lcb:.6f}`.",
        f"- Positive Wilson95 LCB: `{positive_lcb:.6f}`; pooled sidecar min LCB: `{pooled_sidecar_min_lcb:.6f}`; pooled sidecar gate: `{str(pooled_gate).lower()}`.",
        f"- Positive chronological split gate: `{str(positive_split_gate).lower()}`; direct species closed: `false`.",
        f"- Additional source-owned positive rows needed for pooled Wilson95 only: `{additional_positive_rows_for_pooled_95}`; split/heldout gates require materially more.",
        "- Shared intake mutated: `false`; strict full objective achieved: `false`; new confidence gate: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "## Positive Chronological Split Metrics",
        "",
        "| Split | Pos | Wilson95 LCB | Support OK | Wilson OK |",
        "|---|---:|---:|---:|---:|",
    ]
    for metric in positive_split_metrics:
        lines.append(
            f"| `{metric['split']}` | `{metric['positive_support']}` | `{float(metric['positive_wilson95_lcb']):.6f}` | `{str(metric['support_ok']).lower()}` | `{str(metric['wilson_ok']).lower()}` |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a read-only calibration over the live R6 positive rows and the V52 sidecar Nasdaq ITCH broad-normal controls. It does not append sidecar rows into the shared intake and does not convert OHLCV/provider surfaces into direct evidence.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/r6-sidecar-broad-normal-calibration/r6_sidecar_broad_normal_calibration_v1.json`",
            f"- Split metrics CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/r6-sidecar-broad-normal-calibration/r6_sidecar_broad_normal_positive_split_metrics_v1.csv`",
            f"- Reproduction script: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/scripts/r6_sidecar_broad_normal_calibration_v1.py`",
            f"- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/r6_sidecar_broad_normal_calibration_v1_assertions.out`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"PASS broad_normal_sidecar_rows={len(broad_controls)}",
        f"PASS broad_normal_sidecar_gate={str(broad_source_gate).lower()}",
        f"PASS positive_rows={len(positives)}",
        f"PASS pooled_sidecar_gate={str(pooled_gate).lower()}",
        f"PASS accepted_gate={str(accepted_gate).lower()}",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "decision": result["decision"],
                "broad_normal_sidecar_gate": broad_source_gate,
                "pooled_sidecar_gate": pooled_gate,
                "accepted_gate": accepted_gate,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
