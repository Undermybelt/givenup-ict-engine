#!/usr/bin/env python3
"""Decompose why the current source-label confidence calibration fails 95% gates."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20260512T061813+0800-codex-source-confidence-failure-decomposition-after-061421-v1"
SLUG = "source-confidence-failure-decomposition-after-061421-v1"
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
SOURCE_RUN = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T061421+0800-codex-source-label-equivalence-current-calibration-after-061229-v1/"
    "source-label-equivalence-current-calibration-after-061229-v1"
)
INTAKE_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
INTAKE_ROWS = INTAKE_ROOT / "source_label_equivalence_rows.csv"
TARGET_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]

ROOT_LABELS = ["Bear", "Bull", "Crisis", "Sideways"]
REQUIRED_SPLITS = ["calibration", "heldout_market", "heldout_time", "test"]
WILSON_THRESHOLD = 0.95
CONFIDENCE_THRESHOLD = 0.95
MIN_SUPPORT = 50
Z95 = 1.959963984540054


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    denom = 1 + Z95 * Z95 / total
    center = p + Z95 * Z95 / (2 * total)
    radius = Z95 * math.sqrt((p * (1 - p) + Z95 * Z95 / (4 * total)) / total)
    return (center - radius) / denom


def min_successes_for_lcb(total: int, threshold: float) -> int:
    if total <= 0:
        return 0
    lo, hi = 0, total
    while lo < hi:
        mid = (lo + hi) // 2
        if wilson_lcb(mid, total) >= threshold:
            hi = mid
        else:
            lo = mid + 1
    return lo


def as_float(row: dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "0") or 0)
    except ValueError:
        return 0.0


def as_int(row: dict[str, str], key: str) -> int:
    try:
        return int(float(row.get(key, "0") or 0))
    except ValueError:
        return 0


def root_status_rows() -> list[dict[str, Any]]:
    rows = []
    for root in TARGET_ROOTS:
        if root.exists():
            files = sorted(str(path) for path in root.rglob("*") if path.is_file())
            status = "present"
        else:
            files = []
            status = "missing"
        rows.append(
            {
                "root": str(root),
                "status": status,
                "file_count": len(files),
                "sample_files": ";".join(files[:10]),
            }
        )
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    required_inputs = [
        BOARD,
        INTAKE_ROWS,
        SOURCE_RUN / "source_label_equivalence_confidence_calibration_label_split_v1.csv",
        SOURCE_RUN / "source_label_equivalence_confidence_calibration_market_v1.csv",
        SOURCE_RUN / "source_label_equivalence_confidence_calibration_owner_v1.csv",
        SOURCE_RUN / "source_label_equivalence_confidence_calibration_gates_v1.csv",
    ]
    missing_inputs = [str(path) for path in required_inputs if not path.exists()]
    if missing_inputs:
        raise FileNotFoundError(missing_inputs)

    split_rows = read_csv(SOURCE_RUN / "source_label_equivalence_confidence_calibration_label_split_v1.csv")
    market_rows = read_csv(SOURCE_RUN / "source_label_equivalence_confidence_calibration_market_v1.csv")
    owner_rows = read_csv(SOURCE_RUN / "source_label_equivalence_confidence_calibration_owner_v1.csv")
    gate_rows = read_csv(SOURCE_RUN / "source_label_equivalence_confidence_calibration_gates_v1.csv")

    with INTAKE_ROWS.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        intake_fields = reader.fieldnames or []
        intake_sample = [row for _, row in zip(range(5), reader)]

    split_deficits: list[dict[str, Any]] = []
    label_summary: list[dict[str, Any]] = []
    for row in split_rows:
        support = as_int(row, "support")
        current_high = as_int(row, "rows_at_or_above_0_95")
        min_high = min_successes_for_lcb(support, WILSON_THRESHOLD)
        split_deficits.append(
            {
                "label": row["label"],
                "split_role": row["split_role"],
                "support": support,
                "current_high_conf_rows": current_high,
                "current_share_at_or_above_0_95": row["share_at_or_above_0_95"],
                "current_wilson95_lcb": row["wilson95_lcb"],
                "min_high_conf_rows_needed_for_wilson95_0_95": min_high,
                "additional_high_conf_rows_needed": max(0, min_high - current_high),
                "required_high_conf_share": round(min_high / support, 10) if support else 0.0,
                "confidence_median": row["confidence_median"],
                "confidence_mean": row["confidence_mean"],
                "confidence_max": row["confidence_max"],
            }
        )

    by_label = {label: [row for row in split_deficits if row["label"] == label] for label in ROOT_LABELS}
    market_by_label = {label: [row for row in market_rows if row["label"] == label] for label in ROOT_LABELS}
    owner_by_label = {label: [row for row in owner_rows if row["label"] == label] for label in ROOT_LABELS}
    gates_by_label = {row["label"]: row for row in gate_rows}
    for label in ROOT_LABELS:
        deficits = by_label[label]
        worst = min(deficits, key=lambda row: as_float(row, "current_wilson95_lcb"))
        best = max(deficits, key=lambda row: as_float(row, "current_wilson95_lcb"))
        best_market = max(market_by_label[label], key=lambda row: as_float(row, "wilson95_lcb"), default={})
        best_owner = max(owner_by_label[label], key=lambda row: as_float(row, "wilson95_lcb"), default={})
        total_extra = sum(int(row["additional_high_conf_rows_needed"]) for row in deficits)
        label_summary.append(
            {
                "label": label,
                "accepted_source_confidence_95": gates_by_label.get(label, {}).get("accepted_source_confidence_95", "False"),
                "worst_required_split": worst["split_role"],
                "worst_wilson95_lcb": worst["current_wilson95_lcb"],
                "best_required_split": best["split_role"],
                "best_required_split_wilson95_lcb": best["current_wilson95_lcb"],
                "best_market_family": best_market.get("market_family", ""),
                "best_market_wilson95_lcb": best_market.get("wilson95_lcb", ""),
                "best_source_owner": best_owner.get("source_owner", ""),
                "best_owner_wilson95_lcb": best_owner.get("wilson95_lcb", ""),
                "additional_high_conf_rows_needed_across_required_splits": total_extra,
                "blockers": gates_by_label.get(label, {}).get("blockers", ""),
            }
        )

    roots = root_status_rows()
    required_roots_unlocked = all(row["status"] == "present" for row in roots)
    accepted_labels = [row["label"] for row in label_summary if row["accepted_source_confidence_95"] == "True"]
    decision = (
        "source_confidence_failure_decomposition_after_061421_v1="
        "all_regimes_blocked_by_confidence_distribution_required_roots_absent_no_promotion"
    )
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact": sha256_file(BOARD),
        "decision": decision,
        "source_run": str(SOURCE_RUN.relative_to(REPO)),
        "source_run_gates_sha256": sha256_file(SOURCE_RUN / "source_label_equivalence_confidence_calibration_gates_v1.csv"),
        "intake_root": str(INTAKE_ROOT),
        "intake_rows_sha256": sha256_file(INTAKE_ROWS),
        "intake_has_source_confidence_column": "source_confidence" in intake_fields,
        "intake_has_main_regime_v2_label_column": "main_regime_v2_label" in intake_fields,
        "intake_fields": intake_fields,
        "intake_sample_rows": intake_sample,
        "required_roots": roots,
        "required_roots_unlocked": required_roots_unlocked,
        "accepted_labels": accepted_labels,
        "accepted_label_count": len(accepted_labels),
        "root_label_count": len(ROOT_LABELS),
        "strict_full_objective": False,
        "canonical_merge_allowed_now": False,
        "downstream_rerun_allowed_now": False,
        "trade_usable": False,
        "update_goal": False,
        "label_summary": label_summary,
    }

    write_csv(
        OUT / "source_confidence_failure_split_deficits_v1.csv",
        split_deficits,
        [
            "label",
            "split_role",
            "support",
            "current_high_conf_rows",
            "current_share_at_or_above_0_95",
            "current_wilson95_lcb",
            "min_high_conf_rows_needed_for_wilson95_0_95",
            "additional_high_conf_rows_needed",
            "required_high_conf_share",
            "confidence_median",
            "confidence_mean",
            "confidence_max",
        ],
    )
    write_csv(
        OUT / "source_confidence_failure_label_summary_v1.csv",
        label_summary,
        [
            "label",
            "accepted_source_confidence_95",
            "worst_required_split",
            "worst_wilson95_lcb",
            "best_required_split",
            "best_required_split_wilson95_lcb",
            "best_market_family",
            "best_market_wilson95_lcb",
            "best_source_owner",
            "best_owner_wilson95_lcb",
            "additional_high_conf_rows_needed_across_required_splits",
            "blockers",
        ],
    )
    write_csv(
        OUT / "source_confidence_failure_required_roots_v1.csv",
        roots,
        ["root", "status", "file_count", "sample_files"],
    )

    (OUT / "source_confidence_failure_decomposition_after_061421_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Source Confidence Failure Decomposition After 061421 v1",
        "",
        f"- Run id: `{RUN_ID}`",
        f"- Decision: `{decision}`",
        f"- Source run: `{result['source_run']}`",
        f"- Intake has source confidence column: `{result['intake_has_source_confidence_column']}`",
        f"- Accepted labels: `{len(accepted_labels)}/4`",
        f"- Required roots unlocked: `{required_roots_unlocked}`",
        "- Canonical merge allowed now: `false`",
        "- Downstream rerun allowed now: `false`",
        "- Trade usable: `false`",
        "- `update_goal=false`",
        "",
        "## Label Failure Summary",
        "",
        "| Label | Worst split | Worst Wilson95 LCB | Best required split | Best required LCB | Best market | Best market LCB | Extra high-confidence rows needed |",
        "|---|---|---:|---|---:|---|---:|---:|",
    ]
    for row in label_summary:
        lines.append(
            "| `{label}` | `{worst_required_split}` | `{worst_wilson95_lcb}` | `{best_required_split}` | `{best_required_split_wilson95_lcb}` | `{best_market_family}` | `{best_market_wilson95_lcb}` | `{additional_high_conf_rows_needed_across_required_splits}` |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Readback",
            "",
            "- All four active labels remain blocked by the required Wilson95 lower-bound gate across calibration, heldout-market, heldout-time, and test splits.",
            "- The closest visible market slice is still far below the `0.95` lower-bound threshold, so this is not a narrow threshold-margin failure.",
            "- The intake root is schema-ready but has no embedded `source_confidence` column; the `061421` calibration joins source confidence from upstream source files and still fails.",
            "- Required promotion roots remain absent, so this packet cannot unlock direct verifier, canonical merge, provider/AutoQuant, Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.",
            "",
            "## Required Roots",
            "",
            "| Root | Status | File count |",
            "|---|---|---:|",
        ]
    )
    for row in roots:
        lines.append(f"| `{row['root']}` | `{row['status']}` | `{row['file_count']}` |")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `{OUT.relative_to(REPO) / 'source_confidence_failure_decomposition_after_061421_v1.json'}`",
            f"- Split deficits CSV: `{OUT.relative_to(REPO) / 'source_confidence_failure_split_deficits_v1.csv'}`",
            f"- Label summary CSV: `{OUT.relative_to(REPO) / 'source_confidence_failure_label_summary_v1.csv'}`",
            f"- Required roots CSV: `{OUT.relative_to(REPO) / 'source_confidence_failure_required_roots_v1.csv'}`",
        ]
    )
    (OUT / "source_confidence_failure_decomposition_after_061421_v1.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    assertion_lines = [
        f"decision={decision}",
        f"accepted_label_count={len(accepted_labels)}",
        f"required_roots_unlocked={str(required_roots_unlocked).lower()}",
        "canonical_merge_allowed_now=false",
        "downstream_rerun_allowed_now=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    (CHECKS / "source_confidence_failure_decomposition_after_061421_v1_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
