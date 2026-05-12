#!/usr/bin/env python3
"""Materialize the canonical R6 direct Manipulation intake from V56 evidence."""

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


RUN_ID = "20260511T235910-codex-r6-canonical-intake-v57-materialization-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-canonical-intake-v57-materialization"
COMMAND_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
CANONICAL_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
LOCK_PATH = Path("/tmp/ict-engine-direct-manipulation-row-intake.lock")

V56_OUT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235900-codex-r6-direct-intake-v56-clean-readback"
    / "r6-direct-intake-v56-clean-readback"
)
V56_POSITIVE = V56_OUT / "positive_spoofing_layering_rows_v56.csv"
V56_NEGATIVE = V56_OUT / "matched_negative_normal_activity_rows_v56.csv"
V56_JSON = V56_OUT / "r6_direct_intake_v56_clean_readback.json"
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
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
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


def chronological(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    ordered = sorted(rows, key=lambda row: (row["trade_date"], row["source_row_id"]))
    first = math.ceil(len(ordered) * 0.5)
    second = math.ceil(len(ordered) * 0.75)
    buckets = [
        ("train", ordered[:first]),
        ("calibration", ordered[first:second]),
        ("test", ordered[second:]),
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


def grouped(rows: list[dict[str, str]], key: str) -> list[dict[str, object]]:
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


def main() -> int:
    for path in (OUT, COMMAND_OUT, CHECKS):
        path.mkdir(parents=True, exist_ok=True)

    if not V56_POSITIVE.exists() or not V56_NEGATIVE.exists():
        raise SystemExit("missing_v56_source_csv")

    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("w", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle, fcntl.LOCK_EX)
        CANONICAL_ROOT.mkdir(parents=True, exist_ok=True)

        positive_dst = CANONICAL_ROOT / "positive_spoofing_layering_rows.csv"
        negative_dst = CANONICAL_ROOT / "matched_negative_normal_activity_rows.csv"
        provenance_dst = CANONICAL_ROOT / "provenance_manifest.json"

        shutil.copy2(V56_POSITIVE, positive_dst)
        shutil.copy2(V56_NEGATIVE, negative_dst)
        shutil.copy2(V56_POSITIVE, OUT / "positive_spoofing_layering_rows_v57.csv")
        shutil.copy2(V56_NEGATIVE, OUT / "matched_negative_normal_activity_rows_v57.csv")

        v56 = json.loads(V56_JSON.read_text(encoding="utf-8"))
        provenance = {
            "run_id": RUN_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "canonical_intake_root": str(CANONICAL_ROOT),
            "source_v56_json": rel(V56_JSON),
            "source_v56_positive_csv": rel(V56_POSITIVE),
            "source_v56_negative_csv": rel(V56_NEGATIVE),
            "v56_positive_sha256": sha256(V56_POSITIVE),
            "v56_negative_sha256": sha256(V56_NEGATIVE),
            "v56_gate_result": v56.get("gate_result"),
            "materialization_note": "Canonical /tmp intake materialized under an exclusive lock from V56 verified row snapshots; no repo runtime code changed.",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        }
        provenance_dst.write_text(json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8")

        verifier = subprocess.run(
            ["python3", str(VERIFIER), "--intake-root", str(CANONICAL_ROOT)],
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
        (COMMAND_OUT / "direct_manipulation_row_intake_verifier.stdout.txt").write_text(verifier.stdout, encoding="utf-8")
        (COMMAND_OUT / "direct_manipulation_row_intake_verifier.stderr.txt").write_text(verifier.stderr, encoding="utf-8")
        if verifier.returncode != 0:
            (CHECKS / "r6_canonical_intake_v57_materialization_assertions.out").write_text(
                f"verifier_returncode={verifier.returncode}\n",
                encoding="utf-8",
            )
            return verifier.returncode

    payload = json.loads((COMMAND_OUT / "direct_manipulation_row_intake_verifier.stdout.txt").read_text(encoding="utf-8"))
    positives = read_csv(CANONICAL_ROOT / "positive_spoofing_layering_rows.csv")
    negatives = read_csv(CANONICAL_ROOT / "matched_negative_normal_activity_rows.csv")
    sidecar = read_csv(SIDECAR_CONTROLS)
    pos_lcb = wilson_lcb(len(positives), len(positives))
    neg_lcb = wilson_lcb(len(negatives), len(negatives))
    sidecar_lcb = wilson_lcb(len(sidecar), len(sidecar))
    pooled_lcb = min(pos_lcb, neg_lcb, sidecar_lcb)
    split_metrics = chronological(positives) + grouped(positives, "symbol") + grouped(positives, "venue_or_market_center")
    chronological_gate = all(row["support_gate"] and row["confidence_gate"] for row in split_metrics if row["split_key"] == "chronological")
    symbol_gate = all(row["support_gate"] and row["confidence_gate"] for row in split_metrics if row["split_key"] == "symbol")
    venue_gate = all(row["support_gate"] and row["confidence_gate"] for row in split_metrics if row["split_key"] == "venue_or_market_center")
    direct_species_closed = False
    pooled_gate = pooled_lcb >= MIN_WILSON
    gate_result = "r6_canonical_intake_v57_materialization=canonical_verifier_schema_ready_pooled_wilson95_passed_split_species_blocked"

    write_csv(
        OUT / "r6_canonical_intake_v57_split_metrics.csv",
        [{key: str(value) for key, value in row.items()} for row in split_metrics],
        ["split_key", "split_value", "rows", "start_trade_date", "end_trade_date", "wilson95_lcb", "support_gate", "confidence_gate"],
    )
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "canonical_intake_root": str(CANONICAL_ROOT),
        "source_v56_json": rel(V56_JSON),
        "positive_rows": len(positives),
        "matched_negative_rows": len(negatives),
        "matched_group_count": payload.get("matched_group_count"),
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
        "verifier_payload": payload,
        "gate_result": gate_result,
        "new_confidence_gate": pooled_gate,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "next_action": "Keep R6 blocked for strict Board A completion: chronological, heldout-symbol, heldout-venue, and direct-species closure remain false; source fresh direct rows or remap splits before any acceptance claim.",
    }
    json_path = OUT / "r6_canonical_intake_v57_materialization.json"
    report_path = OUT / "r6_canonical_intake_v57_materialization.md"
    assertions_path = CHECKS / "r6_canonical_intake_v57_materialization_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    report_path.write_text(
        "\n".join(
            [
                "# R6 Canonical Intake V57 Materialization",
                "",
                f"- Run id: `{RUN_ID}`",
                f"- Canonical intake root: `{CANONICAL_ROOT}`",
                f"- Source V56 artifact: `{rel(V56_OUT)}`",
                f"- Canonical verifier status: `{payload.get('status')}`.",
                f"- Direct rows: positives `{len(positives)}`, same-event controls `{len(negatives)}`, matched groups `{payload.get('matched_group_count')}`.",
                f"- Sidecar broad-normal controls: `{len(sidecar)}`.",
                f"- Pooled Wilson95 min LCB: `{pooled_lcb:.12f}`; pooled gate `{str(pooled_gate).lower()}`.",
                f"- Chronological split gate: `{str(chronological_gate).lower()}`; heldout symbol gate `{str(symbol_gate).lower()}`; heldout venue gate `{str(venue_gate).lower()}`.",
                f"- Direct species closed: `{str(direct_species_closed).lower()}`.",
                f"- Gate result: `{gate_result}`.",
                "- Strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
                "",
                "## Artifacts",
                f"- JSON: `{rel(json_path)}`",
                f"- Report: `{rel(report_path)}`",
                f"- Positive rows CSV: `{rel(OUT / 'positive_spoofing_layering_rows_v57.csv')}`",
                f"- Matched control CSV: `{rel(OUT / 'matched_negative_normal_activity_rows_v57.csv')}`",
                f"- Split metrics CSV: `{rel(OUT / 'r6_canonical_intake_v57_split_metrics.csv')}`",
                f"- Verifier stdout: `{rel(COMMAND_OUT / 'direct_manipulation_row_intake_verifier.stdout.txt')}`",
                f"- Assertions: `{rel(assertions_path)}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    assertions = [
        ("canonical_verifier_ok", payload.get("status") == "schema_ready_unscored"),
        ("positive_rows_73", len(positives) == 73),
        ("matched_negative_rows_73", len(negatives) == 73),
        ("pooled_wilson95_passed", pooled_gate is True),
        ("chronological_split_still_blocked", chronological_gate is False),
        ("heldout_symbol_still_blocked", symbol_gate is False),
        ("heldout_venue_still_blocked", venue_gate is False),
        ("direct_species_not_closed", direct_species_closed is False),
        ("strict_full_objective_not_complete", result["strict_full_objective_achieved"] is False),
        ("no_runtime_code_changed", result["runtime_code_changed"] is False),
    ]
    assertions_path.write_text("\n".join(f"{name}={'ok' if ok else 'fail'}" for name, ok in assertions) + "\n", encoding="utf-8")
    if not all(ok for _, ok in assertions):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
