#!/usr/bin/env python3
"""Build an owner request package for strict 1h recency/source-label rows."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T201655-codex-stock-regime-owner-recency-request-package-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "stock-regime-owner-recency-request-package"
CHECK_DIR = RUN_ROOT / "checks"

DATASET_ID = "mafaqbhatti/stock-market-regimes-20002026"
DATASET_URL = "https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026"
LOCAL_PANEL = "/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv"
INTAKE_ROOT = "/tmp/ict-engine-source-label-equivalence-intake"
VERIFIER = (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)
REQUIRED_FILES = [
    "source_label_equivalence_rows.csv",
    "source_label_equivalence_provenance.json",
]
REQUIRED_FIELDS = [
    "package_id",
    "source_owner",
    "source_report_or_dataset",
    "source_pull_date",
    "market_family",
    "symbol",
    "source_symbol",
    "equivalence_policy",
    "event_species",
    "timestamp_or_date",
    "timeframe",
    "main_regime_v2_label",
    "direct_label",
    "matched_negative_group_id",
    "split_role",
    "source_row_id",
    "provenance_hash",
]
TARGET_ROWS = [
    {
        "priority": 1,
        "symbol": "XOM",
        "main_regime_v2_label": "Sideways",
        "split_role": "heldout_time",
        "min_new_source_sessions": 5,
        "package_id": "native_subhour_overlap_after_recency",
    },
    {
        "priority": 2,
        "symbol": "UNH",
        "main_regime_v2_label": "Bear",
        "split_role": "calibration",
        "min_new_source_sessions": 7,
        "package_id": "native_subhour_overlap_after_recency",
    },
    {
        "priority": 3,
        "symbol": "^DJI",
        "main_regime_v2_label": "Sideways",
        "split_role": "calibration",
        "min_new_source_sessions": 7,
        "package_id": "native_subhour_overlap_after_recency",
    },
    {
        "priority": 4,
        "symbol": "AMD",
        "main_regime_v2_label": "Bear",
        "split_role": "calibration",
        "min_new_source_sessions": 10,
        "package_id": "native_subhour_overlap_after_recency",
    },
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    command = f"python3 {VERIFIER} --intake-root {INTAKE_ROOT}"
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Convert R4/R5 strict 1h recency/source-label gaps into an owner request package for the existing stock-regime source panel.",
        "source_owner_or_dataset": DATASET_ID,
        "dataset_url": DATASET_URL,
        "local_panel": LOCAL_PANEL,
        "known_current_gap": {
            "local_panel_max_date": "2026-01-30",
            "kaggle_dataset_version_seen": "1",
            "kaggle_dataset_updated_at_seen": "2026-02-01T02:25:29.437Z",
            "post_2026_01_30_rows_for_targets": 0,
        },
        "intake_root": INTAKE_ROOT,
        "required_files": REQUIRED_FILES,
        "required_fields": REQUIRED_FIELDS,
        "target_rows": TARGET_ROWS,
        "verification_command": command,
        "acceptance_conditions": [
            "Place both required files under /tmp/ict-engine-source-label-equivalence-intake.",
            "Rows include source-owned or owner-approved labels for the target symbol/root cells.",
            "Rows include post-2026-01-30 source-owned sessions where R5 recency-tail repair is claimed.",
            "Rows use package_id native_subhour_overlap_after_recency unless the verifier is changed first.",
            "No equivalence_policy contains ohlcv_proxy, generated_label, future_return, or unapproved_ixic.",
            "The unchanged source-label equivalence verifier returns schema_ready_unscored before any confidence audit.",
        ],
        "explicit_non_acceptance": [
            "Do not use provider candles or OHLCV-only rows without source-owned regime labels.",
            "Do not forward-fill the current panel past 2026-01-30.",
            "Do not reuse already-counted source-panel rows as new strict 1h support.",
            "Do not use HMM/model-generated labels or future-return labels.",
        ],
        "decision": "stock_regime_owner_recency_request_package_v1=owner_request_ready_rows_not_acquired",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "r4_strict_1h_source_rows_acquired": False,
        "r5_recency_tail_repair_closed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    json_path = OUT_DIR / "stock_regime_owner_recency_request_package_v1.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    target_csv = OUT_DIR / "stock_regime_owner_recency_request_targets_v1.csv"
    with target_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(TARGET_ROWS[0].keys()))
        writer.writeheader()
        writer.writerows(TARGET_ROWS)

    fields_csv = OUT_DIR / "stock_regime_owner_recency_request_required_fields_v1.csv"
    with fields_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["file", "required_field"])
        writer.writeheader()
        for field in REQUIRED_FIELDS:
            writer.writerow({"file": "source_label_equivalence_rows.csv", "required_field": field})
        writer.writerow({"file": "source_label_equivalence_provenance.json", "required_field": "source_owner"})
        writer.writerow({"file": "source_label_equivalence_provenance.json", "required_field": "source_pull_date"})
        writer.writerow({"file": "source_label_equivalence_provenance.json", "required_field": "input_file_hashes"})
        writer.writerow({"file": "source_label_equivalence_provenance.json", "required_field": "owner_approval_or_source_label_policy"})

    request_md = OUT_DIR / "stock_regime_owner_recency_request_template_v1.md"
    request_md.write_text(
        "\n".join(
            [
                "# Stock Regime Source-Panel Owner Request Template v1",
                "",
                f"Dataset target: `{DATASET_ID}`.",
                f"Dataset URL: `{DATASET_URL}`.",
                "",
                "Request:",
                "",
                "Please provide a source-owned or owner-approved row package for the strict Board A target cells below:",
                "",
                "| Symbol | MainRegimeV2 label | Split role | Minimum new source sessions |",
                "|---|---|---|---:|",
                *[
                    f"| `{row['symbol']}` | `{row['main_regime_v2_label']}` | `{row['split_role']}` | `{row['min_new_source_sessions']}` |"
                    for row in TARGET_ROWS
                ],
                "",
                "Required files:",
                "",
                "- `source_label_equivalence_rows.csv`",
                "- `source_label_equivalence_provenance.json`",
                "",
                "Required row fields:",
                "",
                ", ".join(REQUIRED_FIELDS),
                "",
                "The package will be checked locally with:",
                "",
                f"`{command}`",
                "",
                "Rows cannot be accepted if they are generated/model labels, future-return labels, provider OHLCV-only rows, forward-filled source labels, or duplicates of already-counted source-panel rows.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report_md = OUT_DIR / "stock_regime_owner_recency_request_package_v1.md"
    report_md.write_text(
        "\n".join(
            [
                "# Stock Regime Owner Recency Request Package v1",
                "",
                f"Run ID: `{RUN_ID}`",
                "",
                "- Gate result: `stock_regime_owner_recency_request_package_v1=owner_request_ready_rows_not_acquired`.",
                "- Source target: `mafaqbhatti/stock-market-regimes-20002026`.",
                "- Current blocker converted: R4 strict exact `1h` source rows and R5 post-`2026-01-30` recency-tail repair.",
                "- Target cells: `XOM/Sideways`, `UNH/Bear`, `^DJI/Sideways`, and `AMD/Bear`.",
                "- Required intake root: `/tmp/ict-engine-source-label-equivalence-intake`.",
                "- Accepted rows added: `0`; new confidence gate: `false`.",
                "- Strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path}`",
                f"- Target CSV: `{target_csv}`",
                f"- Required fields CSV: `{fields_csv}`",
                f"- Request template: `{request_md}`",
                f"- Assertions: `{CHECK_DIR / 'stock_regime_owner_recency_request_package_v1_assertions.out'}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assertions = [
        "PASS decision=stock_regime_owner_recency_request_package_v1=owner_request_ready_rows_not_acquired",
        "PASS source_dataset=mafaqbhatti/stock-market-regimes-20002026",
        f"PASS target_rows={len(TARGET_ROWS)}",
        f"PASS required_fields={len(REQUIRED_FIELDS)}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS r4_strict_1h_source_rows_acquired=false",
        "PASS r5_recency_tail_repair_closed=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    (CHECK_DIR / "stock_regime_owner_recency_request_package_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
