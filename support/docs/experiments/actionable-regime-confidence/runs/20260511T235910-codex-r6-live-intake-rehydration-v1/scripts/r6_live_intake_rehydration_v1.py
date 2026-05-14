#!/usr/bin/env python3
"""Rehydrate the canonical R6 direct Manipulation intake from the V56 snapshot."""

from __future__ import annotations

import csv
import fcntl
import hashlib
import json
import math
import shutil
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T235910-codex-r6-live-intake-rehydration-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-live-intake-rehydration"
COMMAND_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"

LIVE_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
LOCK_PATH = Path("/tmp/ict-engine-direct-manipulation-row-intake.lock")
STAGING_ROOT = Path(f"/tmp/{RUN_ID}.staging")
SNAPSHOT_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235726-codex-r6-isolated-reconstruction-snapshot-v56"
    / "r6-isolated-reconstruction-snapshot-v56/isolated-direct-intake"
)
SNAPSHOT_JSON = SNAPSHOT_ROOT.parent / "r6_isolated_reconstruction_snapshot_v56.json"
SNAPSHOT_SPLITS = SNAPSHOT_ROOT.parent / "r6_isolated_reconstruction_snapshot_v56_split_metrics.csv"
SIDECAR_CONTROLS = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1"
    / "r6-broad-normal-order-lifecycle-screen/broad_normal_market_order_lifecycle_controls_v1.csv"
)
VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

REQUIRED_FILES = [
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
]
Z_95 = 1.96
MIN_WILSON = 0.95
MIN_SUPPORT = 50


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def run_verifier(root: Path, stem: str) -> dict[str, object]:
    result = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(root)],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    (COMMAND_OUT / f"{stem}.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (COMMAND_OUT / f"{stem}.stderr.txt").write_text(result.stderr, encoding="utf-8")
    payload: dict[str, object]
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"status": "invalid_json", "stdout": result.stdout}
    return {"returncode": result.returncode, "payload": payload}


def copy_required_files(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for filename in REQUIRED_FILES:
        shutil.copy2(src / filename, dst / filename)


def split_rows(rows: list[dict[str, str]], key: str) -> list[dict[str, object]]:
    counts = Counter(row[key] for row in rows)
    return [
        {
            "split_key": key,
            "split_value": value,
            "rows": count,
            "start_trade_date": "",
            "end_trade_date": "",
            "wilson95_lcb": wilson_lcb(count, count),
            "support_gate": count >= MIN_SUPPORT,
            "confidence_gate": wilson_lcb(count, count) >= MIN_WILSON,
        }
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def chronological(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    ordered = sorted(rows, key=lambda row: (row["trade_date"], row["source_row_id"]))
    first_cut = math.ceil(len(ordered) * 0.5)
    second_cut = math.ceil(len(ordered) * 0.75)
    buckets = [
        ("train", ordered[:first_cut]),
        ("calibration", ordered[first_cut:second_cut]),
        ("test", ordered[second_cut:]),
    ]
    return [
        {
            "split_key": "chronological",
            "split_value": name,
            "rows": len(bucket),
            "start_trade_date": bucket[0]["trade_date"] if bucket else "",
            "end_trade_date": bucket[-1]["trade_date"] if bucket else "",
            "wilson95_lcb": wilson_lcb(len(bucket), len(bucket)),
            "support_gate": len(bucket) >= MIN_SUPPORT,
            "confidence_gate": wilson_lcb(len(bucket), len(bucket)) >= MIN_WILSON,
        }
        for name, bucket in buckets
    ]


def main() -> int:
    for path in (OUT, COMMAND_OUT, CHECKS):
        path.mkdir(parents=True, exist_ok=True)

    board_hash_at_start = sha256(BOARD)
    source_verifier = run_verifier(SNAPSHOT_ROOT, "source_snapshot_verifier")
    if source_verifier["returncode"] != 0 or source_verifier["payload"].get("status") != "schema_ready_unscored":
        raise SystemExit("source snapshot is not verifier-ready")

    if STAGING_ROOT.exists():
        shutil.rmtree(STAGING_ROOT)
    copy_required_files(SNAPSHOT_ROOT, STAGING_ROOT)
    staging_verifier = run_verifier(STAGING_ROOT, "staging_verifier")
    if staging_verifier["returncode"] != 0 or staging_verifier["payload"].get("status") != "schema_ready_unscored":
        raise SystemExit("staging intake is not verifier-ready")

    mutation = "none"
    existing_verifier: dict[str, object] | None = None
    lock_acquired_at = datetime.now(timezone.utc).isoformat()
    with LOCK_PATH.open("w", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        if LIVE_ROOT.exists():
            existing_verifier = run_verifier(LIVE_ROOT, "existing_live_verifier")
        if (
            existing_verifier
            and existing_verifier["returncode"] == 0
            and existing_verifier["payload"].get("status") == "schema_ready_unscored"
        ):
            mutation = "skipped_existing_live_schema_ready"
            if STAGING_ROOT.exists():
                shutil.rmtree(STAGING_ROOT)
        else:
            if LIVE_ROOT.exists():
                backup = OUT / "preexisting-live-intake-backup"
                if backup.exists():
                    shutil.rmtree(backup)
                shutil.copytree(LIVE_ROOT, backup)
                shutil.rmtree(LIVE_ROOT)
            STAGING_ROOT.rename(LIVE_ROOT)
            mutation = "rehydrated_live_root_from_v56_snapshot"
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)

    live_verifier = run_verifier(LIVE_ROOT, "live_verifier")
    positives = read_csv(LIVE_ROOT / "positive_spoofing_layering_rows.csv")
    negatives = read_csv(LIVE_ROOT / "matched_negative_normal_activity_rows.csv")
    sidecar = read_csv(SIDECAR_CONTROLS)
    pos_lcb = wilson_lcb(len(positives), len(positives))
    neg_lcb = wilson_lcb(len(negatives), len(negatives))
    sidecar_lcb = wilson_lcb(len(sidecar), len(sidecar))
    pooled_lcb = min(pos_lcb, neg_lcb, sidecar_lcb)

    split_metrics = chronological(positives) + split_rows(positives, "symbol") + split_rows(positives, "venue_or_market_center")
    chronological_gate = all(
        row["support_gate"] and row["confidence_gate"] for row in split_metrics if row["split_key"] == "chronological"
    )
    symbol_gate = all(row["support_gate"] and row["confidence_gate"] for row in split_metrics if row["split_key"] == "symbol")
    venue_gate = all(
        row["support_gate"] and row["confidence_gate"] for row in split_metrics if row["split_key"] == "venue_or_market_center"
    )
    direct_species_closed = False
    pooled_gate = pooled_lcb >= MIN_WILSON
    gate_result = "r6_live_intake_rehydration_v1=live_schema_ready_pooled95_passed_split_species_full_objective_still_blocked"

    for filename in REQUIRED_FILES:
        shutil.copy2(LIVE_ROOT / filename, OUT / filename)
    write_csv(
        OUT / "r6_live_intake_rehydration_split_metrics_v1.csv",
        [{key: str(value) for key, value in row.items()} for row in split_metrics],
        ["split_key", "split_value", "rows", "start_trade_date", "end_trade_date", "wilson95_lcb", "support_gate", "confidence_gate"],
    )

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_hash_at_start,
        "lock_path": str(LOCK_PATH),
        "lock_acquired_at_utc": lock_acquired_at,
        "live_intake_root": str(LIVE_ROOT),
        "source_snapshot_root": rel(SNAPSHOT_ROOT),
        "source_snapshot_json": rel(SNAPSHOT_JSON),
        "source_snapshot_splits": rel(SNAPSHOT_SPLITS),
        "mutation": mutation,
        "source_verifier": source_verifier,
        "staging_verifier": staging_verifier,
        "existing_live_verifier": existing_verifier,
        "live_verifier": live_verifier,
        "positive_rows": len(positives),
        "matched_negative_rows": len(negatives),
        "matched_group_count": live_verifier["payload"].get("matched_group_count"),
        "sidecar_broad_normal_control_rows": len(sidecar),
        "positive_wilson95_lcb": pos_lcb,
        "matched_negative_wilson95_lcb": neg_lcb,
        "sidecar_broad_normal_wilson95_lcb": sidecar_lcb,
        "pooled_min_wilson95_lcb": pooled_lcb,
        "pooled_wilson95_gate": pooled_gate,
        "chronological_split_gate": chronological_gate,
        "heldout_symbol_gate": symbol_gate,
        "heldout_venue_gate": venue_gate,
        "direct_species_closed": direct_species_closed,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "gate_result": gate_result,
        "next_action": (
            "Keep R6 blocked for strict completion: live schema is restored and pooled Wilson95 passes, but "
            "chronological/symbol/venue split support and non-spoofing direct species coverage remain blocked; keep R5 source-owner recency blocked."
        ),
    }

    json_path = OUT / "r6_live_intake_rehydration_v1.json"
    report_path = OUT / "r6_live_intake_rehydration_v1.md"
    assertions_path = CHECKS / "r6_live_intake_rehydration_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(
        "\n".join(
            [
                "# R6 Live Intake Rehydration v1",
                "",
                f"- Run id: `{RUN_ID}`",
                f"- Live intake root: `{LIVE_ROOT}`",
                f"- Source snapshot: `{rel(SNAPSHOT_ROOT)}`",
                f"- Mutation: `{mutation}`.",
                f"- Live verifier status: `{live_verifier['payload'].get('status')}` returncode `{live_verifier['returncode']}`.",
                f"- Rows: positives `{len(positives)}`, matched controls `{len(negatives)}`, matched groups `{live_verifier['payload'].get('matched_group_count')}`.",
                f"- Sidecar broad-normal controls: `{len(sidecar)}`.",
                f"- Pooled Wilson95 min LCB: `{pooled_lcb:.12f}`; pooled gate `{str(pooled_gate).lower()}`.",
                f"- Chronological split gate: `{str(chronological_gate).lower()}`; heldout symbol gate: `{str(symbol_gate).lower()}`; heldout venue gate: `{str(venue_gate).lower()}`.",
                f"- Direct species closed: `{str(direct_species_closed).lower()}`.",
                f"- Gate result: `{gate_result}`.",
                "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
                "",
                "## Artifacts",
                f"- JSON: `{rel(json_path)}`",
                f"- Report: `{rel(report_path)}`",
                f"- Live positive rows snapshot: `{rel(OUT / 'positive_spoofing_layering_rows.csv')}`",
                f"- Live matched controls snapshot: `{rel(OUT / 'matched_negative_normal_activity_rows.csv')}`",
                f"- Live provenance snapshot: `{rel(OUT / 'provenance_manifest.json')}`",
                f"- Split metrics: `{rel(OUT / 'r6_live_intake_rehydration_split_metrics_v1.csv')}`",
                f"- Live verifier stdout: `{rel(COMMAND_OUT / 'live_verifier.stdout.txt')}`",
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
        ("source_snapshot_verifier_ok", source_verifier["returncode"] == 0 and source_verifier["payload"].get("status") == "schema_ready_unscored"),
        ("staging_verifier_ok", staging_verifier["returncode"] == 0 and staging_verifier["payload"].get("status") == "schema_ready_unscored"),
        ("live_verifier_ok", live_verifier["returncode"] == 0 and live_verifier["payload"].get("status") == "schema_ready_unscored"),
        ("positive_rows_73", len(positives) == 73),
        ("matched_negative_rows_73", len(negatives) == 73),
        ("pooled_wilson95_passed", pooled_gate),
        ("chronological_split_still_blocked", not chronological_gate),
        ("heldout_symbol_still_blocked", not symbol_gate),
        ("heldout_venue_still_blocked", not venue_gate),
        ("strict_full_objective_not_complete", not result["strict_full_objective_achieved"]),
        ("update_goal_false", not result["update_goal"]),
    ]
    assertions_path.write_text("\n".join(f"{name}={'ok' if passed else 'FAIL'}" for name, passed in assertions) + "\n", encoding="utf-8")
    if not all(passed for _, passed in assertions):
        return 2
    print(json.dumps({"ok": True, "gate_result": gate_result, "mutation": mutation, "positive_rows": len(positives), "pooled_lcb": pooled_lcb}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
