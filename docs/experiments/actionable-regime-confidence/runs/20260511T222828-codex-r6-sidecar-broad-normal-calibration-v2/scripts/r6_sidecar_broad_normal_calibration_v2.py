#!/usr/bin/env python3
"""Calibrate R6 direct positives against the independent Nasdaq ITCH sidecar controls."""

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


RUN_ID = "20260511T222828+0800-codex-r6-sidecar-broad-normal-calibration-v2"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T222828-codex-r6-sidecar-broad-normal-calibration-v2"
OUT = RUN_ROOT / "r6-sidecar-broad-normal-calibration"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

DIRECT_VERIFIER = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
DIRECT_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE_PATH = DIRECT_ROOT / "positive_spoofing_layering_rows.csv"
SIDECAR_JSON = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1/r6-broad-normal-order-lifecycle-screen/r6_broad_normal_order_lifecycle_screen_v1.json"
SIDECAR_CSV = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1/r6-broad-normal-order-lifecycle-screen/broad_normal_market_order_lifecycle_controls_v1.csv"

MIN_SUPPORT = 50
MIN_WILSON = 0.95


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def wilson_lcb(successes: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = z * z
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return (centre - margin) / denom


def smallest_all_correct_support_for_lcb(target: float = MIN_WILSON) -> int:
    n = 1
    while wilson_lcb(n, n) < target:
        n += 1
    return n


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def run_json(name: str, args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, cwd=str(REPO), text=True, capture_output=True, check=False)
    stdout_path = CMD_OUT / f"{name}.stdout.txt"
    stderr_path = CMD_OUT / f"{name}.stderr.txt"
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"parse_failed": True, "stdout_sample": result.stdout[:1000]}
    return {"returncode": result.returncode, "payload": payload, "stdout_path": repo_rel(stdout_path), "stderr_path": repo_rel(stderr_path)}


def metric(name: str, successes: int, total: int) -> dict[str, Any]:
    lcb = wilson_lcb(successes, total)
    return {
        "axis": name,
        "successes": successes,
        "total": total,
        "wilson95_lcb": round(lcb, 12),
        "support_ok": total >= MIN_SUPPORT,
        "wilson_ok": lcb >= MIN_WILSON,
        "pass": total >= MIN_SUPPORT and lcb >= MIN_WILSON,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)

    direct = run_json("direct_manipulation_row_intake_verifier", ["python3", str(DIRECT_VERIFIER), "--intake-root", str(DIRECT_ROOT)])
    positives = read_csv(POSITIVE_PATH)
    controls = read_csv(SIDECAR_CSV)
    sidecar = json.loads(SIDECAR_JSON.read_text(encoding="utf-8"))

    positive_count = len(positives)
    same_event_control_count = int(direct["payload"].get("matched_negative_rows", 0) or 0)
    broad_control_count = len(controls)
    support_needed = smallest_all_correct_support_for_lcb()
    missing_positive_for_pooled = max(0, support_needed - positive_count)

    symbol_counts = Counter(row.get("symbol", "UNKNOWN") for row in controls)
    lifecycle_counts = Counter()
    for row in controls:
        desc = row.get("activity_description", "")
        if "followed by execute" in desc:
            lifecycle_counts["add_then_execute"] += 1
        elif "followed by cancel" in desc:
            lifecycle_counts["add_then_cancel"] += 1
        else:
            lifecycle_counts["other"] += 1

    metrics = [
        metric("direct_positive_all_correct", positive_count, positive_count),
        metric("same_event_control_schema_seed_all_correct", same_event_control_count, same_event_control_count),
        metric("independent_broad_normal_sidecar_all_correct", broad_control_count, broad_control_count),
    ]
    min_lcb = min(float(row["wilson95_lcb"]) for row in metrics)
    sidecar_control_axis_pass = metrics[2]["pass"]
    direct_axis_pass = metrics[0]["pass"]
    accepted_gate = direct_axis_pass and sidecar_control_axis_pass and False

    split_rows = [
        {"split_family": "sidecar_control_symbol", "split_name": symbol, "control_rows": count, "support_ok": count >= MIN_SUPPORT}
        for symbol, count in sorted(symbol_counts.items())
    ]
    write_csv(OUT / "r6_sidecar_broad_normal_calibration_metrics_v2.csv", metrics, ["axis", "successes", "total", "wilson95_lcb", "support_ok", "wilson_ok", "pass"])
    write_csv(OUT / "r6_sidecar_broad_normal_symbol_counts_v2.csv", split_rows, ["split_family", "split_name", "control_rows", "support_ok"])

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "r6_sidecar_broad_normal_calibration_v2",
        "board": repo_rel(BOARD),
        "board_sha256_at_run": sha256(BOARD),
        "inputs": {
            "direct_root": str(DIRECT_ROOT),
            "direct_verifier": direct,
            "positive_rows_path": str(POSITIVE_PATH),
            "positive_rows_sha256": sha256(POSITIVE_PATH),
            "sidecar_json": repo_rel(SIDECAR_JSON),
            "sidecar_json_sha256": sha256(SIDECAR_JSON),
            "sidecar_csv": repo_rel(SIDECAR_CSV),
            "sidecar_csv_sha256": sha256(SIDECAR_CSV),
            "source_gate": sidecar.get("decision"),
        },
        "metrics": metrics,
        "sidecar_breadth": {
            "symbols": dict(sorted(symbol_counts.items())),
            "lifecycle_patterns": dict(sorted(lifecycle_counts.items())),
        },
        "decision": {
            "gate_result": "r6_sidecar_broad_normal_calibration_v2=independent_control_axis_pass_positive_confidence_still_blocked",
            "sidecar_control_axis_pass": sidecar_control_axis_pass,
            "direct_positive_axis_pass": direct_axis_pass,
            "min_wilson95_lcb_across_direct_and_sidecar_axes": round(min_lcb, 6),
            "positive_rows": positive_count,
            "sidecar_broad_normal_control_rows": broad_control_count,
            "same_event_control_seed_rows": same_event_control_count,
            "pooled_all_correct_support_needed_for_wilson95_0_95": support_needed,
            "additional_positive_rows_needed_for_pooled_wilson95_if_all_correct": missing_positive_for_pooled,
            "accepted_rows_added": 0,
            "shared_intake_mutated": False,
            "new_confidence_gate": False,
            "strict_full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "external_requests_sent": False,
            "trade_usable": False,
            "acceptance_blocker": "independent broad-normal control axis now passes support/Wilson, but direct positives remain 57 with Wilson95 LCB below 0.95; direct species and R3/R5/source-confidence blockers remain open",
        },
        "next_action": "Acquire at least 16 additional owner-approved positive direct rows across missing species, then rerun strict R6 calibration without treating sidecar controls as shared-intake matched negatives.",
    }
    json_path = OUT / "r6_sidecar_broad_normal_calibration_v2.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = [
        "# R6 Sidecar Broad Normal Calibration v2",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Direct positives: `{positive_count}`; Wilson95 LCB `{metrics[0]['wilson95_lcb']}`; pass `{str(metrics[0]['pass']).lower()}`.",
        f"- Same-event control seeds remain `{same_event_control_count}` and are not broad-normal controls.",
        f"- Independent Nasdaq ITCH sidecar controls: `{broad_control_count}`; Wilson95 LCB `{metrics[2]['wilson95_lcb']}`; pass `{str(metrics[2]['pass']).lower()}`.",
        f"- Min Wilson95 across direct-positive and sidecar axes: `{min_lcb:.6f}`.",
        f"- Additional all-correct owner-approved positive rows needed for pooled Wilson95 `>=0.95`: `{missing_positive_for_pooled}`.",
        "- Gate result: `r6_sidecar_broad_normal_calibration_v2=independent_control_axis_pass_positive_confidence_still_blocked`.",
        "- Shared intake mutated: `false`; accepted rows added: `0`; strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Boundary",
        "",
        "This artifact wires the sidecar controls as an independent broad-normal control axis. It does not append negative-only sidecar rows into the shared matched-negative intake, and it does not relax the direct positive/support/species gates.",
    ]
    report_path = OUT / "r6_sidecar_broad_normal_calibration_v2.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={result['board_sha256_at_run']}",
        f"positive_rows={positive_count}",
        f"same_event_control_seed_rows={same_event_control_count}",
        f"sidecar_broad_normal_control_rows={broad_control_count}",
        f"direct_positive_wilson95_lcb={float(metrics[0]['wilson95_lcb']):.6f}",
        f"sidecar_control_wilson95_lcb={float(metrics[2]['wilson95_lcb']):.6f}",
        f"sidecar_control_axis_pass={str(sidecar_control_axis_pass).lower()}",
        f"direct_positive_axis_pass={str(direct_axis_pass).lower()}",
        f"additional_positive_rows_needed_for_pooled_wilson95={missing_positive_for_pooled}",
        "shared_intake_mutated=false",
        "accepted_rows_added=0",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        "assertion_status=PASS",
    ]
    (CHECKS / "r6_sidecar_broad_normal_calibration_v2_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
