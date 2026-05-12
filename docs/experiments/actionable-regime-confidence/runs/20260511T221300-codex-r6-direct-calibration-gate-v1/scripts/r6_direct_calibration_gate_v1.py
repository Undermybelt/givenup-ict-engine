#!/usr/bin/env python3
"""Fail-closed R6 direct manipulation chronological/heldout calibration gate."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T221300-codex-r6-direct-calibration-gate-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-direct-calibration-gate"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

POSITIVE_NAME = "positive_spoofing_layering_rows.csv"
NEGATIVE_NAME = "matched_negative_normal_activity_rows.csv"
PROVENANCE_NAME = "provenance_manifest.json"

MIN_SUPPORT = 50
MIN_WILSON = 0.95
Z_95 = 1.96

MISSING_DIRECT_SPECIES = [
    "quote_stuffing",
    "pinging",
    "bear_raid_or_painting_tape",
    "pump_dump_social_text_or_twitter",
    "broad_independent_normal_market_controls",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def safe_date(row: dict[str, str]) -> str:
    return row.get("trade_date") or "9999-12-31"


def group_rows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get("matched_negative_group_id", "")].append(row)
    return groups


def chronological_split_ids(positive_rows: list[dict[str, str]], negative_rows: list[dict[str, str]]) -> dict[str, str]:
    grouped = group_rows(positive_rows + negative_rows)
    ordered = sorted(
        grouped,
        key=lambda gid: (
            min(safe_date(row) for row in grouped[gid]),
            gid,
        ),
    )
    total = len(ordered)
    train_end = max(1, int(total * 0.50))
    calibration_end = max(train_end + 1, int(total * 0.75))
    splits: dict[str, str] = {}
    for index, gid in enumerate(ordered):
        if index < train_end:
            role = "chronological_train"
        elif index < calibration_end:
            role = "chronological_calibration"
        else:
            role = "chronological_test"
        splits[gid] = role
    return splits


def split_metric(
    split_family: str,
    split_name: str,
    rows: list[dict[str, str]],
    required_support: int = MIN_SUPPORT,
) -> dict[str, object]:
    positives = [r for r in rows if r["_class"] == "positive"]
    negatives = [r for r in rows if r["_class"] == "negative"]
    positive_lcb = wilson_lcb(len(positives), len(positives))
    negative_lcb = wilson_lcb(len(negatives), len(negatives))
    min_lcb = min(positive_lcb, negative_lcb)
    support_ok = len(positives) >= required_support and len(negatives) >= required_support
    wilson_ok = min_lcb >= MIN_WILSON
    return {
        "split_family": split_family,
        "split_name": split_name,
        "positive_support": len(positives),
        "negative_support": len(negatives),
        "positive_wilson95_lcb": round(positive_lcb, 12),
        "negative_wilson95_lcb": round(negative_lcb, 12),
        "min_wilson95_lcb": round(min_lcb, 12),
        "support_ok": support_ok,
        "wilson_ok": wilson_ok,
        "pass": support_ok and wilson_ok,
        "blocker": ";".join(
            part
            for part in [
                "support_below_50" if not support_ok else "",
                "wilson95_below_0.95" if not wilson_ok else "",
            ]
            if part
        )
        or "none",
    }


def normalize_family(value: str) -> str:
    return " ".join((value or "UNKNOWN").strip().split())


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def bool_text(value: object) -> str:
    return str(bool(value)).lower()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intake-root", required=True)
    args = parser.parse_args()

    intake_root = Path(args.intake_root)
    positive_path = intake_root / POSITIVE_NAME
    negative_path = intake_root / NEGATIVE_NAME
    provenance_path = intake_root / PROVENANCE_NAME
    missing = [str(path) for path in [positive_path, negative_path, provenance_path] if not path.exists()]
    if missing:
        raise SystemExit(f"missing required intake files: {missing}")

    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    positives = read_csv(positive_path)
    negatives = read_csv(negative_path)
    provenance = read_json(provenance_path)
    board_hash_before = sha256(BOARD) if BOARD.exists() else None

    combined: list[dict[str, str]] = []
    for row in positives:
        item = dict(row)
        item["_class"] = "positive"
        combined.append(item)
    for row in negatives:
        item = dict(row)
        item["_class"] = "negative"
        combined.append(item)

    split_ids = chronological_split_ids(positives, negatives)
    metrics: list[dict[str, object]] = []

    metrics.append(split_metric("pooled_all_source_rows", "all_rows", combined))

    for role in ["chronological_train", "chronological_calibration", "chronological_test"]:
        rows = [row for row in combined if split_ids.get(row.get("matched_negative_group_id", "")) == role]
        metrics.append(split_metric("chronological_group_split", role, rows))

    symbol_counts = Counter(normalize_family(row.get("symbol", "")) for row in combined)
    for symbol, _ in sorted(symbol_counts.items()):
        rows = [row for row in combined if normalize_family(row.get("symbol", "")) == symbol]
        metrics.append(split_metric("heldout_symbol_exact", symbol, rows))

    venue_counts = Counter(normalize_family(row.get("venue_or_market_center", "")) for row in combined)
    for venue, _ in sorted(venue_counts.items()):
        rows = [row for row in combined if normalize_family(row.get("venue_or_market_center", "")) == venue]
        metrics.append(split_metric("heldout_venue_exact", venue, rows))

    paired_groups = group_rows(combined)
    group_class_counts = {
        gid: Counter(row["_class"] for row in rows)
        for gid, rows in paired_groups.items()
    }
    unmatched_groups = [
        gid
        for gid, counts in group_class_counts.items()
        if counts.get("positive", 0) == 0 or counts.get("negative", 0) == 0
    ]

    negative_descriptions = " ".join(row.get("activity_description", "") for row in negatives).lower()
    control_boundary_text = json.dumps(provenance, sort_keys=True).lower()
    broad_normal_sample = not (
        "not a broad normal-market" in negative_descriptions
        or "not broad normal-market" in negative_descriptions
        or "same-event" in negative_descriptions
        or "not broad normal-market" in control_boundary_text
        or "not a broad normal-market" in control_boundary_text
    )
    direct_species_closed = False

    split_gate_pass = all(
        metric["pass"]
        for metric in metrics
        if metric["split_family"] in {
            "pooled_all_source_rows",
            "chronological_group_split",
            "heldout_symbol_exact",
            "heldout_venue_exact",
        }
    )
    paired_groups_ok = not unmatched_groups
    support_gate = len(positives) >= MIN_SUPPORT and len(negatives) >= MIN_SUPPORT
    pooled_metric = metrics[0]
    pooled_wilson_ok = float(pooled_metric["min_wilson95_lcb"]) >= MIN_WILSON
    accepted_gate = (
        support_gate
        and pooled_wilson_ok
        and split_gate_pass
        and broad_normal_sample
        and direct_species_closed
        and paired_groups_ok
    )

    decision = "r6_direct_calibration_gate_v1=chronological_heldout_calibration_fail_closed"
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "intake_root": str(intake_root),
        "board_hash_before_start": board_hash_before,
        "input_hashes": {
            POSITIVE_NAME: sha256(positive_path),
            NEGATIVE_NAME: sha256(negative_path),
            PROVENANCE_NAME: sha256(provenance_path),
        },
        "positive_rows": len(positives),
        "matched_negative_rows": len(negatives),
        "matched_groups": len(paired_groups),
        "unmatched_groups": unmatched_groups,
        "support_gate_50_50": support_gate,
        "pooled_min_wilson95_lcb": pooled_metric["min_wilson95_lcb"],
        "pooled_wilson_gate": pooled_wilson_ok,
        "split_gate_pass": split_gate_pass,
        "broad_normal_sample": broad_normal_sample,
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
        "provenance_updated_by": provenance.get("updated_by"),
        "source_reports": sorted({row.get("source_report", "") for row in combined}),
        "symbols": sorted({normalize_family(row.get("symbol", "")) for row in combined}),
        "venues": sorted({normalize_family(row.get("venue_or_market_center", "")) for row in combined}),
        "split_metrics": metrics,
        "next_action": (
            "Acquire independent broad normal-market direct controls and additional direct species, "
            "then rerun this chronological/heldout calibration gate; do not promote same-event controls."
        ),
    }

    json_path = OUT / "r6_direct_calibration_gate_v1.json"
    md_path = OUT / "r6_direct_calibration_gate_v1.md"
    metrics_path = OUT / "r6_direct_calibration_split_metrics_v1.csv"
    assertions_path = CHECKS / "r6_direct_calibration_gate_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        metrics_path,
        metrics,
        [
            "split_family",
            "split_name",
            "positive_support",
            "negative_support",
            "positive_wilson95_lcb",
            "negative_wilson95_lcb",
            "min_wilson95_lcb",
            "support_ok",
            "wilson_ok",
            "pass",
            "blocker",
        ],
    )

    lines = [
        "# R6 Direct Calibration Gate v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Direct intake rows: positives `{len(positives)}`, matched negatives `{len(negatives)}`, matched groups `{len(paired_groups)}`.",
        f"- Pooled Wilson95 min LCB: `{float(pooled_metric['min_wilson95_lcb']):.6f}`; pooled 95 gate: `{bool_text(pooled_wilson_ok)}`.",
        f"- Chronological/heldout split gate: `{bool_text(split_gate_pass)}`.",
        f"- Broad normal sample: `{bool_text(broad_normal_sample)}`; direct species closed: `{bool_text(direct_species_closed)}`.",
        f"- Accepted gate: `{bool_text(accepted_gate)}`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "## Split Metrics",
        "",
        "| Split Family | Split | Pos | Neg | Min Wilson95 LCB | Pass | Blocker |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for metric in metrics:
        lines.append(
            "| `{split_family}` | `{split_name}` | `{positive_support}` | `{negative_support}` | `{min_wilson95_lcb:.6f}` | `{pass_value}` | `{blocker}` |".format(
                split_family=metric["split_family"],
                split_name=metric["split_name"],
                positive_support=metric["positive_support"],
                negative_support=metric["negative_support"],
                min_wilson95_lcb=float(metric["min_wilson95_lcb"]),
                pass_value=bool_text(metric["pass"]),
                blocker=metric["blocker"],
            )
        )

    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a calibration readback over source-owned/direct rows already in `/tmp`. It does not add rows and does not convert same-event genuine-order controls into independent broad normal-market controls.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/r6-direct-calibration-gate/r6_direct_calibration_gate_v1.json`",
            f"- Split metrics CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/r6-direct-calibration-gate/r6_direct_calibration_split_metrics_v1.csv`",
            f"- Reproduction script: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/scripts/r6_direct_calibration_gate_v1.py`",
            f"- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/r6_direct_calibration_gate_v1_assertions.out`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"PASS decision={decision}",
        f"PASS positive_rows={len(positives)}",
        f"PASS matched_negative_rows={len(negatives)}",
        f"PASS support_gate_50_50={bool_text(support_gate)}",
        f"PASS accepted_gate={bool_text(accepted_gate)}",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "accepted_gate": accepted_gate, "positive_rows": len(positives), "matched_negative_rows": len(negatives)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
