#!/usr/bin/env python3
"""Fail-closed readback of Board A source/control intake roots."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


RUN_ID = "20260512T010855-codex-source-root-presence-readback-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs"
) / RUN_ID
OUT_DIR = RUN_ROOT / "source-root-presence-readback-v1"
CHECK_DIR = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"
VERIFIER = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)

ROOTS = [
    {
        "branch": "r6_owner_export",
        "root": "/tmp/ict-engine-board-a-r6-owner-export-v1",
        "required_files": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
        "promotion_use": "R6 direct verifier source-owned normal controls",
    },
    {
        "branch": "source_label_equivalence",
        "root": "/tmp/ict-engine-source-label-equivalence-intake",
        "required_files": [
            "source_label_equivalence_rows.csv",
            "source_label_equivalence_provenance.json",
        ],
        "promotion_use": "source-label confidence equivalence",
    },
    {
        "branch": "r3_native_subhour",
        "root": "/tmp/ict-engine-native-subhour-source-label-intake",
        "required_files": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
        "promotion_use": "R3 native sub-hour source labels",
    },
    {
        "branch": "r5_panel_recency_extension",
        "root": "/tmp/ict-engine-source-panel-recency-extension",
        "required_files": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
        "promotion_use": "R5 post-2026-01-30 source-panel recency extension",
    },
]


def list_files(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file()
    )


def run_source_label_verifier(root: str) -> dict[str, object]:
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, str(VERIFIER), "--intake-root", root],
        text=True,
        capture_output=True,
        check=False,
        timeout=240,
    )
    stdout_path = CMD_DIR / "source_label_equivalence_verifier.stdout.txt"
    stderr_path = CMD_DIR / "source_label_equivalence_verifier.stderr.txt"
    exit_path = CMD_DIR / "source_label_equivalence_verifier.exit"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"status": "unparsed", "stdout_prefix": proc.stdout[:500]}
    return {
        "returncode": proc.returncode,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "exit": str(exit_path),
        "parsed": parsed,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    for item in ROOTS:
        root = Path(item["root"])
        files = list_files(root)
        present = set(files)
        required = item["required_files"]
        missing = [name for name in required if name not in present]
        rows.append(
            {
                "branch": item["branch"],
                "root": str(root),
                "root_exists": root.exists(),
                "file_count": len(files),
                "required_files": required,
                "present_files": files,
                "missing_required_files": missing,
                "required_files_complete": not missing,
                "promotion_use": item["promotion_use"],
            }
        )

    r6_complete = next(
        row["required_files_complete"]
        for row in rows
        if row["branch"] == "r6_owner_export"
    )
    source_label_row = next(
        row for row in rows if row["branch"] == "source_label_equivalence"
    )
    source_label_verifier = (
        run_source_label_verifier(source_label_row["root"])
        if source_label_row["required_files_complete"]
        else None
    )
    source_label_schema_ready = bool(
        source_label_verifier
        and source_label_verifier["returncode"] == 0
        and source_label_verifier["parsed"].get("status") == "schema_ready_unscored"
    )
    r3_complete = next(
        row["required_files_complete"]
        for row in rows
        if row["branch"] == "r3_native_subhour"
    )
    r5_complete = next(
        row["required_files_complete"]
        for row in rows
        if row["branch"] == "r5_panel_recency_extension"
    )
    any_files_present = any(row["file_count"] > 0 for row in rows)

    summary = {
        "run_id": RUN_ID,
        "input_cursor": "20260512T010127+0800-codex-r6-owner-route-entitlement-readback-v1",
        "latest_observed_append": "20260512T010506-codex-r6-owner-export-official-contact-route-check-v1",
        "root_readback": rows,
        "source_label_verifier": source_label_verifier,
        "source_label_schema_ready_unscored": source_label_schema_ready,
        "source_label_confidence_gate_now": False,
        "valid_source_owned_normal_controls_acquired_now": r6_complete,
        "non_r6_source_label_equivalence_rows_acquired_now": source_label_row["required_files_complete"],
        "r3_native_subhour_rows_acquired_now": r3_complete,
        "r5_panel_recency_extension_rows_acquired_now": r5_complete,
        "same_exhibit_flip_approval_acquired_now": False,
        "canonical_merge_allowed_now": False,
        "downstream_rerun_allowed_now": False,
        "strict_full_objective_achieved": False,
        "decision": (
            "blocked_no_source_files_present"
            if not any_files_present
            else "blocked_source_label_schema_ready_unscored_no_r6_r3_r5"
            if source_label_schema_ready
            else "blocked_required_source_contract_incomplete"
        ),
    }

    (OUT_DIR / "source_root_presence_readback_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with (OUT_DIR / "source_root_presence_readback_v1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "branch",
                "root",
                "root_exists",
                "file_count",
                "required_files_complete",
                "missing_required_files",
                "promotion_use",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "branch": row["branch"],
                    "root": row["root"],
                    "root_exists": row["root_exists"],
                    "file_count": row["file_count"],
                    "required_files_complete": row["required_files_complete"],
                    "missing_required_files": "|".join(row["missing_required_files"]),
                    "promotion_use": row["promotion_use"],
                }
            )

    report_lines = [
        "# Source Root Presence Readback v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Decision: `{summary['decision']}`",
        f"- R6 source-owned controls acquired now: `{str(r6_complete).lower()}`",
        f"- Source-label equivalence schema ready: `{str(source_label_schema_ready).lower()}`",
        "- Source-label confidence gate now: `false`",
        f"- R3 native sub-hour rows acquired now: `{str(r3_complete).lower()}`",
        f"- R5 panel-recency extension rows acquired now: `{str(r5_complete).lower()}`",
        "- Same-exhibit FLIP approval acquired now: `false`",
        "- Canonical merge allowed now: `false`",
        "- Downstream rerun allowed now: `false`",
        "- Strict full objective achieved: `false`",
        "",
        "## Roots",
        "",
    ]
    for row in rows:
        report_lines.extend(
            [
                f"### {row['branch']}",
                "",
                f"- Root: `{row['root']}`",
                f"- Root exists: `{str(row['root_exists']).lower()}`",
                f"- File count: `{row['file_count']}`",
                f"- Required files complete: `{str(row['required_files_complete']).lower()}`",
                f"- Missing required files: `{', '.join(row['missing_required_files'])}`",
                "",
            ]
        )
    (OUT_DIR / "source_root_presence_readback_v1.md").write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS checked_roots={len(rows)}",
        f"PASS any_files_present={str(any_files_present).lower()}",
        f"PASS r6_required_files_complete={str(r6_complete).lower()}",
        f"PASS source_label_required_files_complete={str(source_label_row['required_files_complete']).lower()}",
        f"PASS source_label_schema_ready_unscored={str(source_label_schema_ready).lower()}",
        "PASS source_label_confidence_gate_now=false",
        f"PASS r3_required_files_complete={str(r3_complete).lower()}",
        f"PASS r5_required_files_complete={str(r5_complete).lower()}",
        "PASS same_exhibit_flip_approval_acquired_now=false",
        "PASS canonical_merge_allowed_now=false",
        "PASS downstream_rerun_allowed_now=false",
        "PASS strict_full_objective_achieved=false",
    ]
    (CHECK_DIR / "source_root_presence_readback_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
