#!/usr/bin/env python3
"""Build a fail-closed R3 native sub-hour source-label acquisition package."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T203100-codex-native-subhour-intake-request-package-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = RUN_ROOT / "native-subhour-intake-request-package"
CHECK_DIR = RUN_ROOT / "checks"

POST_AXISWISE_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T133453-codex-post-axiswise-acquisition-request-v12/acquisition-request"
)
POST_AXISWISE_JSON = POST_AXISWISE_ROOT / "post_axiswise_acquisition_request_v12.json"
POST_AXISWISE_ACTIVE_CSV = POST_AXISWISE_ROOT / "post_axiswise_active_source_label_requests_v12.csv"

NATIVE_BLOCKER_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T180420-codex-native-subhour-overlap-blocker-v1/native-subhour-overlap"
)
NATIVE_BLOCKER_JSON = NATIVE_BLOCKER_ROOT / "native_subhour_overlap_blocker_v1.json"
NATIVE_BLOCKER_CELLS_CSV = NATIVE_BLOCKER_ROOT / "native_subhour_overlap_blocker_v1_cells.csv"

INTAKE_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
REQUIRED_ROW_FILE = INTAKE_ROOT / "native_subhour_source_label_rows.csv"
REQUIRED_PROVENANCE_FILE = INTAKE_ROOT / "native_subhour_source_label_provenance.json"
NATIVE_TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "4h"}

REQUIRED_ROW_FIELDS = [
    {
        "field": "source_row_id",
        "required": True,
        "description": "Stable row identifier from the owner/source package.",
    },
    {
        "field": "source_name",
        "required": True,
        "description": "Dataset, licensor, venue, or owner-approved source name.",
    },
    {
        "field": "owner_or_licensor",
        "required": True,
        "description": "Entity approving the label export or source-native label policy.",
    },
    {
        "field": "license_or_permission",
        "required": True,
        "description": "License, written permission, or export approval reference.",
    },
    {
        "field": "instrument",
        "required": True,
        "description": "Board A target instrument, for example QQQ, NQ=F, SPY, ES=F.",
    },
    {
        "field": "timeframe",
        "required": True,
        "description": "Native sub-hour timeframe: 1m, 5m, 15m, 30m, or exact 1h/4h if source-native.",
    },
    {
        "field": "timestamp_start_utc",
        "required": True,
        "description": "Start timestamp for the source-labeled interval in UTC.",
    },
    {
        "field": "timestamp_end_utc",
        "required": True,
        "description": "End timestamp for the source-labeled interval in UTC.",
    },
    {
        "field": "root_label",
        "required": True,
        "description": "One of Bull, Bear, Sideways, Crisis using the accepted MainRegimeV2 root vocabulary.",
    },
    {
        "field": "source_label",
        "required": True,
        "description": "Original owner/source label before normalization.",
    },
    {
        "field": "qualifying_condition",
        "required": True,
        "description": "Per-root condition that makes this row eligible for Board A, not borrowed from another regime.",
    },
    {
        "field": "confidence_or_quality_flag",
        "required": True,
        "description": "Source confidence, adjudication flag, or source quality marker; may be categorical.",
    },
    {
        "field": "validation_instrument_group",
        "required": True,
        "description": "Instrument/species group used for cross-market validation.",
    },
    {
        "field": "validation_period",
        "required": True,
        "description": "Chronological period bucket used for train/calibration/test separation.",
    },
    {
        "field": "validation_market_context",
        "required": True,
        "description": "Market context or provider/source context for the row.",
    },
    {
        "field": "provenance_url_or_path",
        "required": True,
        "description": "Owner-approved URL, local intake path, or manifest reference.",
    },
    {
        "field": "source_version_hash",
        "required": True,
        "description": "Dataset hash, source package version, or signed export id.",
    },
    {
        "field": "forbidden_proxy_flag",
        "required": True,
        "description": "Must be false. True means HMM/KMeans/classifier/future-return/generated/OHLCV-only proxy.",
    },
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def build_targets(active_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    targets: list[dict[str, object]] = []
    for row in active_rows:
        if row.get("provider") != "yfinance":
            continue
        if row.get("timeframe") not in NATIVE_TIMEFRAMES:
            continue
        if row.get("post_axiswise_disposition") != "active_request_after_axiswise":
            continue
        targets.append(
            {
                "provider": row.get("provider", ""),
                "instrument": row.get("instrument", ""),
                "timeframe": row.get("timeframe", ""),
                "root": row.get("root", ""),
                "required_label_source": row.get("required_label_source", ""),
                "forbidden_proxy_sources": row.get("forbidden_proxy_sources", ""),
                "required_next_artifact": row.get("required_next_artifact", ""),
                "request_package_id": "native_intraday_yfinance_index_etf_futures",
                "intake_row_file": str(REQUIRED_ROW_FILE),
                "intake_provenance_file": str(REQUIRED_PROVENANCE_FILE),
            }
        )
    targets.sort(key=lambda item: (str(item["instrument"]), str(item["timeframe"]), str(item["root"])))
    return targets


def build_focus_cells(blocker_cells: list[dict[str, str]]) -> list[dict[str, object]]:
    focus: list[dict[str, object]] = []
    for cell in blocker_cells:
        focus.append(
            {
                "symbol": cell.get("symbol", ""),
                "timeframe": cell.get("timeframe", ""),
                "download_state": cell.get("download_state", ""),
                "provider_date_min": cell.get("provider_date_min", ""),
                "provider_date_max": cell.get("provider_date_max", ""),
                "source_date_min": cell.get("source_date_min", ""),
                "source_date_max": cell.get("source_date_max", ""),
                "source_overlap_sessions": cell.get("source_overlap_sessions", ""),
                "native_subhour_source_overlap_ready": cell.get("native_subhour_source_overlap_ready", ""),
                "blocker": cell.get("blocker", ""),
                "focus_reason": "native_subhour_overlap_blocker_cell",
                "intake_row_file": str(REQUIRED_ROW_FILE),
                "intake_provenance_file": str(REQUIRED_PROVENANCE_FILE),
            }
        )
    return focus


def write_report(payload: dict[str, object], focus_cells: list[dict[str, object]]) -> None:
    report_path = OUT_DIR / "native_subhour_intake_request_package_v1.md"
    lines = [
        "# Native Sub-hour Intake Request Package v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        f"- Gate result: `{payload['decision']}`.",
        "- Purpose: convert the R3 native sub-hour blocker into exact source-owned intake requirements without accepting proxy labels.",
        f"- Active native intraday source-label request rows: `{payload['native_intraday_target_count']}`.",
        f"- Focus blocker cells carried forward: `{payload['focus_blocker_cell_count']}`.",
        f"- Required intake root: `{INTAKE_ROOT}`.",
        f"- Required files: `{REQUIRED_ROW_FILE.name}` and `{REQUIRED_PROVENANCE_FILE.name}`.",
        f"- Accepted rows added: `{payload['accepted_rows_added']}`; new confidence gate: `{str(payload['new_confidence_gate']).lower()}`.",
        f"- Strict full objective achieved: `{str(payload['strict_full_objective_achieved']).lower()}`; `update_goal={str(payload['update_goal']).lower()}`.",
        "",
        "## Focus Cells",
        "",
        "| Instrument | Timeframe | Root | Intake row file |",
        "|---|---|---|---|",
    ]
    for cell in focus_cells:
        lines.append(
            f"| `{cell['symbol']}` | `{cell['timeframe']}` | `all four roots required` | `{REQUIRED_ROW_FILE}` |"
        )
    lines.extend(
        [
            "",
            "## Request Boundary",
            "",
            "- This package does not create source labels, does not download raw rows, and does not run calibration.",
            "- OHLCV/provider candles, HMM states, KMeans labels, future-return labels, classifier outputs, generated labels, and daily/monthly labels projected into sub-hour windows remain fail-closed.",
            "- After files appear under the intake root, rerun the fail-closed native sub-hour verifier before any completion audit.",
            "",
            "## Artifacts",
            "",
            "- JSON: `native_subhour_intake_request_package_v1.json`",
            "- Target rows: `native_subhour_intake_request_targets_v1.csv`",
            "- Focus cells: `native_subhour_intake_focus_cells_v1.csv`",
            "- Required fields: `native_subhour_intake_required_fields_v1.csv`",
            "- Request template: `native_subhour_intake_request_template_v1.md`",
            "- Assertions: `../checks/native_subhour_intake_request_package_v1_assertions.out`",
            "",
        ]
    )
    report_path.write_text("\n".join(lines))


def write_template(target_count: int, focus_count: int) -> None:
    template_path = OUT_DIR / "native_subhour_intake_request_template_v1.md"
    template_path.write_text(
        "\n".join(
            [
                "# Native Sub-hour Source Label Intake Request Template v1",
                "",
                "We need owner-approved or source-native sub-hour market-regime labels for an audit of regime-confidence transfer across markets and cycles.",
                "",
                "Required scope:",
                f"- Active native intraday request rows: {target_count}",
                f"- Immediate focus cells from the live blocker: {focus_count}",
                "- Timeframes: 1m, 5m, 15m, 30m, 1h, and 4h only when the labels are source-native at that horizon.",
                "- Root labels: Bull, Bear, Sideways, Crisis.",
                "",
                "Required files:",
                f"- `{REQUIRED_ROW_FILE}`",
                f"- `{REQUIRED_PROVENANCE_FILE}`",
                "",
                "Required boundary:",
                "- Do not provide HMM/KMeans/classifier/future-return/generated/OHLCV-only labels.",
                "- Do not provide daily or monthly labels projected into sub-hour windows.",
                "- Include source version, license or permission, row ids, and per-row provenance.",
                "",
            ]
        )
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    post_axiswise = load_json(POST_AXISWISE_JSON)
    native_blocker = load_json(NATIVE_BLOCKER_JSON)
    active_rows = read_csv(POST_AXISWISE_ACTIVE_CSV)
    blocker_cells = read_csv(NATIVE_BLOCKER_CELLS_CSV)

    targets = build_targets(active_rows)
    focus_cells = build_focus_cells(blocker_cells)

    fields = [
        "provider",
        "instrument",
        "timeframe",
        "root",
        "required_label_source",
        "forbidden_proxy_sources",
        "required_next_artifact",
        "request_package_id",
        "intake_row_file",
        "intake_provenance_file",
    ]
    write_csv(OUT_DIR / "native_subhour_intake_request_targets_v1.csv", targets, fields)
    write_csv(
        OUT_DIR / "native_subhour_intake_focus_cells_v1.csv",
        focus_cells,
        [
            "symbol",
            "timeframe",
            "download_state",
            "provider_date_min",
            "provider_date_max",
            "source_date_min",
            "source_date_max",
            "source_overlap_sessions",
            "native_subhour_source_overlap_ready",
            "blocker",
            "focus_reason",
            "intake_row_file",
            "intake_provenance_file",
        ],
    )
    write_csv(
        OUT_DIR / "native_subhour_intake_required_fields_v1.csv",
        REQUIRED_ROW_FIELDS,
        ["field", "required", "description"],
    )
    write_template(len(targets), len(focus_cells))

    payload: dict[str, object] = {
        "run_id": RUN_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decision": "native_subhour_intake_request_package_v1=request_ready_rows_not_acquired",
        "input_post_axiswise_json": str(POST_AXISWISE_JSON),
        "input_active_request_csv": str(POST_AXISWISE_ACTIVE_CSV),
        "input_native_blocker_json": str(NATIVE_BLOCKER_JSON),
        "input_native_blocker_cells_csv": str(NATIVE_BLOCKER_CELLS_CSV),
        "post_axiswise_decision": post_axiswise.get("decision", {}),
        "native_blocker_decision": native_blocker.get("decision", {}),
        "native_intraday_target_count": len(targets),
        "focus_blocker_cell_count": len(focus_cells),
        "required_intake_root": str(INTAKE_ROOT),
        "required_row_file": str(REQUIRED_ROW_FILE),
        "required_provenance_file": str(REQUIRED_PROVENANCE_FILE),
        "required_field_count": len(REQUIRED_ROW_FIELDS),
        "request_sent": False,
        "rows_acquired": False,
        "native_subhour_source_label_intake_files_created": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "r3_native_subhour_closed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "fail_closed_rules": [
            "no_hmm_kmeans_classifier_future_return_generated_or_synthetic_labels",
            "no_ohlcv_only_proxy_labels",
            "no_daily_or_monthly_projection_into_subhour_windows",
        ],
    }
    (OUT_DIR / "native_subhour_intake_request_package_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    write_report(payload, focus_cells)

    assertions = [
        ("post_axiswise_json_present", POST_AXISWISE_JSON.exists()),
        ("active_request_csv_present", POST_AXISWISE_ACTIVE_CSV.exists()),
        ("native_blocker_json_present", NATIVE_BLOCKER_JSON.exists()),
        ("native_blocker_cells_csv_present", NATIVE_BLOCKER_CELLS_CSV.exists()),
        ("native_intraday_target_count_336", len(targets) == 336),
        ("focus_blocker_cell_count_4", len(focus_cells) == 4),
        ("required_field_count_ge_15", len(REQUIRED_ROW_FIELDS) >= 15),
        ("rows_acquired_false", payload["rows_acquired"] is False),
        ("accepted_rows_added_zero", payload["accepted_rows_added"] == 0),
        ("r3_closed_false", payload["r3_native_subhour_closed"] is False),
        ("strict_full_objective_achieved_false", payload["strict_full_objective_achieved"] is False),
        ("update_goal_false", payload["update_goal"] is False),
        ("raw_data_committed_false", payload["raw_data_committed"] is False),
    ]
    failed = [name for name, ok in assertions if not ok]
    (CHECK_DIR / "native_subhour_intake_request_package_v1_assertions.out").write_text(
        "\n".join(f"{name}=PASS" if ok else f"{name}=FAIL" for name, ok in assertions)
        + "\n"
    )
    if failed:
        raise SystemExit(f"failed assertions: {', '.join(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
