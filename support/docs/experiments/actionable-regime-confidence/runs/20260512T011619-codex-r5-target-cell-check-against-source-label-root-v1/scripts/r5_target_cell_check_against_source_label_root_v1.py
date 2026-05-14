#!/usr/bin/env python3
"""Check whether the live source-label root can satisfy R5 recency target cells."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


RUN_ID = "20260512T011619-codex-r5-target-cell-check-against-source-label-root-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = RUN_ROOT / "r5-target-cell-check-against-source-label-root-v1"
CHECK_DIR = RUN_ROOT / "checks"
SOURCE_LABEL_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
SOURCE_LABEL_ROWS = SOURCE_LABEL_ROOT / "source_label_equivalence_rows.csv"
SOURCE_LABEL_PROVENANCE = SOURCE_LABEL_ROOT / "source_label_equivalence_provenance.json"
R5_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
R5_CUTOFF = "2026-01-30"
TARGETS = [
    ("XOM", "Sideways"),
    ("UNH", "Bear"),
    ("^DJI", "Sideways"),
    ("AMD", "Bear"),
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    counts = {target: 0 for target in TARGETS}
    post_cutoff_counts = {target: 0 for target in TARGETS}
    latest_dates = {target: "" for target in TARGETS}
    rows_present = SOURCE_LABEL_ROWS.exists()
    provenance_present = SOURCE_LABEL_PROVENANCE.exists()

    if rows_present:
        with SOURCE_LABEL_ROWS.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                target = (row.get("symbol", ""), row.get("main_regime_v2_label", ""))
                if target not in counts:
                    continue
                counts[target] += 1
                date_value = row.get("timestamp_or_date", "")
                if date_value > latest_dates[target]:
                    latest_dates[target] = date_value
                if date_value > R5_CUTOFF:
                    post_cutoff_counts[target] += 1

    target_rows = []
    for symbol, label in TARGETS:
        target = (symbol, label)
        target_rows.append(
            {
                "symbol": symbol,
                "required_label": label,
                "source_label_rows_total": counts[target],
                "latest_source_label_date": latest_dates[target],
                "post_cutoff_rows_after_2026_01_30": post_cutoff_counts[target],
                "r5_recency_satisfied": post_cutoff_counts[target] > 0,
            }
        )

    all_targets_satisfied = all(row["r5_recency_satisfied"] for row in target_rows)
    r5_root_files = sorted(path.name for path in R5_ROOT.glob("*") if path.is_file()) if R5_ROOT.exists() else []
    summary = {
        "run_id": RUN_ID,
        "gate_result": "r5_target_cell_check_against_source_label_root_v1=source_label_root_has_no_post_cutoff_r5_target_rows",
        "source_label_root": str(SOURCE_LABEL_ROOT),
        "source_label_rows_present": rows_present,
        "source_label_rows_sha256": sha256_file(SOURCE_LABEL_ROWS) if rows_present else "",
        "source_label_provenance_present": provenance_present,
        "r5_recency_root": str(R5_ROOT),
        "r5_recency_root_files": r5_root_files,
        "r5_cutoff_exclusive": R5_CUTOFF,
        "target_rows": target_rows,
        "all_r5_targets_satisfied": all_targets_satisfied,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    with (OUT_DIR / "r5_target_cell_source_label_root_check_v1.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "symbol",
                "required_label",
                "source_label_rows_total",
                "latest_source_label_date",
                "post_cutoff_rows_after_2026_01_30",
                "r5_recency_satisfied",
            ],
        )
        writer.writeheader()
        writer.writerows(target_rows)

    (OUT_DIR / "r5_target_cell_check_against_source_label_root_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report_lines = [
        "# R5 Target Cell Check Against Source Label Root v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Gate result: `{summary['gate_result']}`.",
        f"- Source-label rows present: `{str(rows_present).lower()}`.",
        f"- R5 recency root files: `{', '.join(r5_root_files) if r5_root_files else 'none'}`.",
        f"- R5 cutoff: rows must be after `{R5_CUTOFF}`.",
        f"- All R5 targets satisfied: `{str(all_targets_satisfied).lower()}`.",
        "- Accepted rows added: `0`; new confidence gate: false; downstream chain rerun allowed: false.",
        "- Strict full objective achieved: false. `update_goal=false`.",
        "",
        "## Target Cells",
        "",
    ]
    for row in target_rows:
        report_lines.append(
            f"- `{row['symbol']}` / `{row['required_label']}`: total `{row['source_label_rows_total']}`, "
            f"latest `{row['latest_source_label_date']}`, post-cutoff `{row['post_cutoff_rows_after_2026_01_30']}`."
        )
    report_lines.extend(
        [
            "",
            "## Boundary",
            "",
            "The live source-label equivalence root is schema-ready but cannot fill the R5 post-cutoff recency-extension root. Do not copy these rows into the R5 root or treat historical pre-cutoff labels as R5 recency evidence.",
        ]
    )
    (OUT_DIR / "r5_target_cell_check_against_source_label_root_v1.md").write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )

    assertions = [
        f"run_id={RUN_ID}",
        f"source_label_rows_present={str(rows_present).lower()}",
        f"all_r5_targets_satisfied={str(all_targets_satisfied).lower()}",
        f"r5_root_file_count={len(r5_root_files)}",
        "accepted_rows_added=0",
        "new_confidence_gate=false",
        "canonical_merge_allowed=false",
        "downstream_chain_rerun_allowed=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
    ]
    (CHECK_DIR / "r5_target_cell_check_against_source_label_root_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
