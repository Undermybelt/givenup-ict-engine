#!/usr/bin/env python3
"""Clean readback for the V55 73x73 R6 direct-intake artifact.

V55 was touched concurrently: its generated 73x73 CSV artifact is intact under
`r6-direct-intake-reconstruction-v55/`, while the shared `scripts/` and `checks/`
paths were later overwritten by a different reconstruction attempt. This V56
run copies only the intact CSV/provenance evidence into a fresh isolated intake
root, reruns the fail-closed verifier, and recomputes gates.
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


RUN_ID = "20260511T235900-codex-r6-direct-intake-v56-clean-readback"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-direct-intake-v56-clean-readback"
COMMAND_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
INTAKE_ROOT = Path("/tmp/ict-engine-r6-direct-intake-v56-clean-readback/intake")

V55_OUT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T234414-codex-r6-direct-intake-reconstruction-v55"
    / "r6-direct-intake-reconstruction-v55"
)
V55_POSITIVE = V55_OUT / "positive_spoofing_layering_rows_v55.csv"
V55_NEGATIVE = V55_OUT / "matched_negative_normal_activity_rows_v55.csv"
V55_JSON = V55_OUT / "r6_direct_intake_reconstruction_v55.json"
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


def split_rows(rows: list[dict[str, str]], key: str) -> list[dict[str, object]]:
    counts = Counter(row[key] for row in rows)
    return [
        {
            "split_key": key,
            "split_value": value,
            "rows": count,
            "wilson95_lcb": wilson_lcb(count, count),
            "support_gate": count >= MIN_SUPPORT,
            "confidence_gate": wilson_lcb(count, count) >= MIN_WILSON,
        }
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def chronological(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    ordered = sorted(rows, key=lambda row: (row["trade_date"], row["source_row_id"]))
    a = math.ceil(len(ordered) * 0.5)
    b = math.ceil(len(ordered) * 0.75)
    buckets = [("train", ordered[:a]), ("calibration", ordered[a:b]), ("test", ordered[b:])]
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
    for path in (OUT, COMMAND_OUT, CHECKS, INTAKE_ROOT):
        path.mkdir(parents=True, exist_ok=True)
    positive_dst = INTAKE_ROOT / "positive_spoofing_layering_rows.csv"
    negative_dst = INTAKE_ROOT / "matched_negative_normal_activity_rows.csv"
    provenance_dst = INTAKE_ROOT / "provenance_manifest.json"
    shutil.copy2(V55_POSITIVE, positive_dst)
    shutil.copy2(V55_NEGATIVE, negative_dst)
    shutil.copy2(V55_POSITIVE, OUT / "positive_spoofing_layering_rows_v56.csv")
    shutil.copy2(V55_NEGATIVE, OUT / "matched_negative_normal_activity_rows_v56.csv")

    v55 = json.loads(V55_JSON.read_text(encoding="utf-8"))
    provenance = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_v55_json": rel(V55_JSON),
        "source_v55_positive_csv": rel(V55_POSITIVE),
        "source_v55_negative_csv": rel(V55_NEGATIVE),
        "v55_positive_sha256": sha256(V55_POSITIVE),
        "v55_negative_sha256": sha256(V55_NEGATIVE),
        "v55_generation_note": "V55 CSV subdirectory preserved 73x73 output; V55 scripts/checks paths were concurrently overwritten, so V56 re-verifies the CSV artifact in a fresh root.",
        "accepted_sarao_positive_rows": v55.get("accepted_sarao_positive_rows"),
        "accepted_nowak_smith_positive_rows": v55.get("accepted_nowak_smith_positive_rows"),
        "accepted_jpm_cftc_positive_rows": v55.get("accepted_jpm_cftc_positive_rows"),
        "jpm_source_url": "https://www.cftc.gov/media/4826/enfjpmorganchaseorder092920/download",
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
    }
    provenance_dst.write_text(json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8")

    verifier = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE_ROOT)],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    (COMMAND_OUT / "direct_manipulation_row_intake_verifier.stdout.txt").write_text(verifier.stdout, encoding="utf-8")
    (COMMAND_OUT / "direct_manipulation_row_intake_verifier.stderr.txt").write_text(verifier.stderr, encoding="utf-8")
    payload = json.loads(verifier.stdout)

    positives = read_csv(positive_dst)
    negatives = read_csv(negative_dst)
    sidecar = read_csv(SIDECAR_CONTROLS)
    pos_lcb = wilson_lcb(len(positives), len(positives))
    neg_lcb = wilson_lcb(len(negatives), len(negatives))
    sidecar_lcb = wilson_lcb(len(sidecar), len(sidecar))
    pooled_lcb = min(pos_lcb, neg_lcb, sidecar_lcb)
    split_metrics = chronological(positives) + split_rows(positives, "symbol") + split_rows(positives, "venue_or_market_center")
    split_gate = all(row["support_gate"] and row["confidence_gate"] for row in split_metrics if row["split_key"] == "chronological")
    symbol_gate = all(row["support_gate"] and row["confidence_gate"] for row in split_metrics if row["split_key"] == "symbol")
    venue_gate = all(row["support_gate"] and row["confidence_gate"] for row in split_metrics if row["split_key"] == "venue_or_market_center")
    direct_species_closed = False
    pooled_gate = pooled_lcb >= MIN_WILSON
    gate_result = "r6_direct_intake_v56_clean_readback=pooled_wilson95_passed_split_species_full_objective_still_blocked"

    write_csv(
        OUT / "r6_direct_intake_v56_split_metrics.csv",
        [{key: str(value) for key, value in row.items()} for row in split_metrics],
        ["split_key", "split_value", "rows", "start_trade_date", "end_trade_date", "wilson95_lcb", "support_gate", "confidence_gate"],
    )
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "isolated_intake_root": str(INTAKE_ROOT),
        "source_v55_json": rel(V55_JSON),
        "positive_rows": len(positives),
        "matched_negative_rows": len(negatives),
        "matched_group_count": payload.get("matched_group_count"),
        "sidecar_broad_normal_control_rows": len(sidecar),
        "positive_wilson95_lcb": pos_lcb,
        "matched_negative_wilson95_lcb": neg_lcb,
        "sidecar_broad_normal_wilson95_lcb": sidecar_lcb,
        "pooled_min_wilson95_lcb": pooled_lcb,
        "pooled_wilson95_gate": pooled_gate,
        "chronological_split_gate": split_gate,
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
        "next_action": "Keep R6 fail-closed for strict completion: pooled direct Wilson95 now passes, but chronological/symbol/venue split support and non-spoofing direct species are still open; R5 source-owner recency also remains blocked.",
    }
    json_path = OUT / "r6_direct_intake_v56_clean_readback.json"
    report_path = OUT / "r6_direct_intake_v56_clean_readback.md"
    assertions_path = CHECKS / "r6_direct_intake_v56_clean_readback_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    report_path.write_text(
        "\n".join(
            [
                "# R6 Direct Intake V56 Clean Readback",
                "",
                f"- Run id: `{RUN_ID}`",
                f"- Source V55 CSV artifact: `{rel(V55_OUT)}`",
                f"- Isolated verifier status: `{payload.get('status')}`.",
                f"- Direct rows: positives `{len(positives)}`, same-event controls `{len(negatives)}`, matched groups `{payload.get('matched_group_count')}`.",
                f"- Sidecar broad-normal controls: `{len(sidecar)}`.",
                f"- Pooled Wilson95 min LCB: `{pooled_lcb:.12f}`; pooled gate `{str(pooled_gate).lower()}`.",
                f"- Chronological split gate: `{str(split_gate).lower()}`; heldout symbol gate `{str(symbol_gate).lower()}`; heldout venue gate `{str(venue_gate).lower()}`.",
                f"- Direct species closed: `{str(direct_species_closed).lower()}`.",
                f"- Gate result: `{gate_result}`.",
                "- Strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
                "",
                "## Artifacts",
                f"- JSON: `{rel(json_path)}`",
                f"- Report: `{rel(report_path)}`",
                f"- Positive rows CSV: `{rel(OUT / 'positive_spoofing_layering_rows_v56.csv')}`",
                f"- Matched control CSV: `{rel(OUT / 'matched_negative_normal_activity_rows_v56.csv')}`",
                f"- Split metrics CSV: `{rel(OUT / 'r6_direct_intake_v56_split_metrics.csv')}`",
                f"- Verifier stdout: `{rel(COMMAND_OUT / 'direct_manipulation_row_intake_verifier.stdout.txt')}`",
                f"- Assertions: `{rel(assertions_path)}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    assertions = [
        ("verifier_ok", verifier.returncode == 0 and payload.get("status") == "schema_ready_unscored"),
        ("positive_rows_73", len(positives) == 73),
        ("matched_negative_rows_73", len(negatives) == 73),
        ("pooled_wilson95_passed", pooled_gate),
        ("chronological_split_still_blocked", not split_gate),
        ("heldout_symbol_still_blocked", not symbol_gate),
        ("heldout_venue_still_blocked", not venue_gate),
        ("direct_species_not_closed", not direct_species_closed),
        ("strict_full_objective_not_complete", not result["strict_full_objective_achieved"]),
        ("no_runtime_code_changed", not result["runtime_code_changed"]),
    ]
    assertions_path.write_text("\n".join(f"{name}={'ok' if passed else 'FAIL'}" for name, passed in assertions) + "\n", encoding="utf-8")
    if not all(passed for _, passed in assertions):
        return 2
    print(json.dumps({"ok": True, "gate_result": gate_result, "positive_rows": len(positives), "pooled_lcb": pooled_lcb, "update_goal": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
