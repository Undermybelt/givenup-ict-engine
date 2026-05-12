#!/usr/bin/env python3
"""Build sendable R3 native sub-hour source-label request drafts."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


RUN_ID = "20260512T010401-codex-r3-native-subhour-sendable-requests-v2"
BASE = Path("docs/experiments/actionable-regime-confidence/runs")
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")

REQUEST_RUN = BASE / "20260511T203100-codex-native-subhour-intake-request-package-v1"
REQUEST_DIR = REQUEST_RUN / "native-subhour-intake-request-package"
REQUEST_JSON = REQUEST_DIR / "native_subhour_intake_request_package_v1.json"
FOCUS_CSV = REQUEST_DIR / "native_subhour_intake_focus_cells_v1.csv"
REQUIRED_FIELDS_CSV = REQUEST_DIR / "native_subhour_intake_required_fields_v1.csv"
REQUEST_TEMPLATE = REQUEST_DIR / "native_subhour_intake_request_template_v1.md"

CONTACT_RUN = BASE / "20260511T203505-codex-native-subhour-contact-leads-v1"
CONTACT_DIR = CONTACT_RUN / "native-subhour-contact-leads"
CONTACT_CSV = CONTACT_DIR / "native_subhour_contact_leads_v1.csv"

OUT_ROOT = BASE / RUN_ID
OUT_DIR = OUT_ROOT / "r3-native-subhour-sendable-requests-v2"
CHECK_DIR = OUT_ROOT / "checks"

INTAKE_ROOT = "/tmp/ict-engine-native-subhour-source-label-intake"
REQUIRED_ROW_FILE = f"{INTAKE_ROOT}/native_subhour_source_label_rows.csv"
REQUIRED_PROVENANCE_FILE = f"{INTAKE_ROOT}/native_subhour_source_label_provenance.json"
ROOT_LABELS = ["Bull", "Bear", "Sideways", "Crisis"]
EXPECTED_FOCUS = {
    ("AAPL", "15m"),
    ("AAPL", "30m"),
    ("^IXIC", "15m"),
    ("^IXIC", "30m"),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def board_cursor_and_hash() -> tuple[str, str]:
    raw = BOARD.read_bytes()
    text = raw.decode("utf-8")
    match = re.search(r"\| last_loop_id \| ([^|]+) \|", text)
    cursor = match.group(1).strip() if match else "missing"
    return cursor, hashlib.sha256(raw).hexdigest()


def md_table(rows: list[dict[str, str]], fields: list[str]) -> str:
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "/") for field in fields) + " |")
    return "\n".join(out)


def focus_table(focus_rows: list[dict[str, str]]) -> str:
    fields = [
        "symbol",
        "timeframe",
        "provider_date_min",
        "provider_date_max",
        "source_date_max",
        "source_overlap_sessions",
        "blocker",
    ]
    return md_table(focus_rows, fields)


def required_field_list(required_fields: list[dict[str, str]]) -> str:
    return "\n".join(f"- `{row['field']}`: {row['description']}" for row in required_fields)


def common_boundary() -> str:
    return f"""Required delivery root after approval/export: `{INTAKE_ROOT}`

Required files:
- `{REQUIRED_ROW_FILE}`
- `{REQUIRED_PROVENANCE_FILE}`

Accepted root labels: `{', '.join(ROOT_LABELS)}`.

Fail-closed boundary:
- Do not provide HMM/KMeans/classifier/future-return/generated/OHLCV-only labels.
- Do not provide daily or monthly labels projected into sub-hour windows.
- Include owner/licensor permission, source version/hash, row ids, per-row provenance, and per-root qualifying conditions.
- This request is not an external send record and does not authorize a downstream rerun by itself.
"""


def message_kaggle(focus_rows: list[dict[str, str]], required_fields: list[dict[str, str]]) -> str:
    return f"""# Kaggle Source-Label Owner Native Sub-hour Extension Request v2

Subject: Request for owner-approved native 15m/30m regime-label extension for AAPL and IXIC

We are auditing whether existing source-owned market-regime labels can support native sub-hour confidence validation. The current source panel for the stock-regime dataset ends at `2026-01-30`; the current provider-visible sub-hour cells begin at `2026-02-12`, so the four focus cells have zero source overlap.

Focus cells:

{focus_table(focus_rows)}

Request:
- Please confirm whether source-native 15m and 30m regime labels exist, or can be exported/approved, for `AAPL` and `^IXIC` after `2026-01-30`.
- Please cover all four root labels where available: `{', '.join(ROOT_LABELS)}`.
- Please include enough rows to support chronological validation across the `2026-02-12` to `2026-05-08` provider-visible window, or explicitly identify the source-native covered dates if different.
- Please provide row-level provenance and permission terms sufficient to populate the two intake files below.

{common_boundary()}

Required row fields:

{required_field_list(required_fields)}
"""


def message_nasdaq(focus_rows: list[dict[str, str]], required_fields: list[dict[str, str]]) -> str:
    ixic_rows = [row for row in focus_rows if row["symbol"] == "^IXIC"]
    return f"""# Nasdaq Indexes Native Sub-hour Source-Label Request v2

Subject: Request for IXIC native 15m/30m source-label availability or approval path

We need source-owned or owner-approved native sub-hour regime labels for the Nasdaq Composite focus cells. The current blocker is not bar availability; it is absence of source-native labels after the existing source panel tail.

IXIC focus cells:

{focus_table(ixic_rows)}

Request:
- Please confirm whether Nasdaq Indexes can provide or approve native 15m/30m source labels for `^IXIC` market-regime intervals.
- If the available product is index context rather than root-regime labels, please state that explicitly; context-only or OHLCV-only data will not close this intake.
- If a licensed/custom export route exists, please identify the route, date coverage, version/export id, and permission language needed for the provenance manifest.

{common_boundary()}

Required row fields:

{required_field_list(required_fields)}
"""


def message_yahoo(focus_rows: list[dict[str, str]], required_fields: list[dict[str, str]]) -> str:
    return f"""# Yahoo Finance Intraday Provenance and Label Availability Request v2

Subject: Request for intraday provenance and source-native regime-label availability for AAPL and IXIC

This request asks whether Yahoo Finance can provide or authorize source-native sub-hour regime labels for the listed focus cells. Intraday OHLCV bars alone are useful for provider context but are not accepted as source labels for this Board A R3 gate.

Focus cells:

{focus_table(focus_rows)}

Request:
- Please confirm whether source-native 15m/30m regime-label rows exist for `AAPL` and `^IXIC`.
- If only OHLCV/intraday quote bars are available, please confirm that limitation so the R3 source-label gate remains blocked.
- If labels or owner-approved provenance are available, please provide the permission/export reference and row-level fields required below.

{common_boundary()}

Required row fields:

{required_field_list(required_fields)}
"""


def message_vendor(focus_rows: list[dict[str, str]], required_fields: list[dict[str, str]]) -> str:
    return f"""# Market Data Vendor Native Sub-hour Label Availability Request v2

Subject: Availability request for source-native 15m/30m regime-label rows for AAPL and IXIC

We are looking for source-native or owner-approved sub-hour market-regime labels, not a derived label set produced from bars. The immediate cells are `AAPL` and `^IXIC` at 15m and 30m.

Focus cells:

{focus_table(focus_rows)}

Request:
- Please confirm whether a licensed dataset or custom export can provide native 15m/30m regime-label intervals for these cells.
- If the available product is raw trades/quotes/bars only, please state that explicitly; raw market data by itself does not satisfy the source-label intake.
- If a source-native label export is available, please include date coverage, root-label vocabulary, version/export id, license/permission terms, and row-level provenance.

{common_boundary()}

Required row fields:

{required_field_list(required_fields)}
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    request = json.loads(REQUEST_JSON.read_text())
    focus_rows = read_csv(FOCUS_CSV)
    required_fields = read_csv(REQUIRED_FIELDS_CSV)
    contacts = read_csv(CONTACT_CSV)
    template_text = REQUEST_TEMPLATE.read_text()
    current_cursor, board_sha256 = board_cursor_and_hash()

    focus_set = {(row["symbol"], row["timeframe"]) for row in focus_rows}
    contact_counts = Counter(row["lead_type"] for row in contacts)

    messages = [
        {
            "request_id": "kaggle_source_label_owner_native_subhour_extension",
            "message_file": "kaggle_source_label_owner_native_subhour_request_v2.md",
            "primary_contact_leads": "kaggle_stock_regime_owner_discussion_intraday_extension;kaggle_stock_regime_owner_profile_intraday_extension",
            "purpose": "Ask existing source-label owner for post-2026-01-30 native 15m/30m AAPL and IXIC regime-label export or approval.",
            "sendable": "true",
            "content": message_kaggle(focus_rows, required_fields),
        },
        {
            "request_id": "nasdaq_indexes_ixic_native_subhour_label_route",
            "message_file": "nasdaq_indexes_ixic_native_subhour_request_v2.md",
            "primary_contact_leads": "nasdaq_indexes_contact",
            "purpose": "Ask index owner for IXIC native source-label availability or explicit context-only limitation.",
            "sendable": "true",
            "content": message_nasdaq(focus_rows, required_fields),
        },
        {
            "request_id": "yahoo_finance_intraday_provenance_label_availability",
            "message_file": "yahoo_finance_intraday_provenance_request_v2.md",
            "primary_contact_leads": "yahoo_finance_help_surface;yahoo_terms_surface",
            "purpose": "Clarify whether Yahoo can provide source-native labels; OHLCV-only provenance does not close R3.",
            "sendable": "true",
            "content": message_yahoo(focus_rows, required_fields),
        },
        {
            "request_id": "vendor_native_subhour_label_availability",
            "message_file": "market_data_vendor_native_subhour_label_availability_request_v2.md",
            "primary_contact_leads": "nasdaq_data_link_contact;polygon_contact",
            "purpose": "Ask vendors for true source-native or owner-approved sub-hour regime-label products, not derived labels.",
            "sendable": "true",
            "content": message_vendor(focus_rows, required_fields),
        },
    ]

    for msg in messages:
        (OUT_DIR / msg["message_file"]).write_text(msg["content"])

    index_rows = []
    lead_to_request = {
        "kaggle_stock_regime_owner_discussion_intraday_extension": messages[0],
        "kaggle_stock_regime_owner_profile_intraday_extension": messages[0],
        "nasdaq_indexes_contact": messages[1],
        "yahoo_finance_help_surface": messages[2],
        "yahoo_terms_surface": messages[2],
        "nasdaq_data_link_contact": messages[3],
        "polygon_contact": messages[3],
    }
    for contact in contacts:
        msg = lead_to_request.get(contact["lead_id"])
        if msg:
            focus_use = "sendable_focus_or_provenance_route"
            message_file = msg["message_file"]
            sendable = "true"
        else:
            focus_use = "deferred_non_focus_exchange_route"
            message_file = ""
            sendable = "false"
        index_rows.append(
            {
                "lead_id": contact["lead_id"],
                "lead_type": contact["lead_type"],
                "contact_surface": contact["contact_surface"],
                "url": contact["url"],
                "focus_use": focus_use,
                "message_file": message_file,
                "sendable": sendable,
                "rows_acquired": "false",
                "request_sent": "false",
            }
        )
    write_csv(
        OUT_DIR / "r3_native_subhour_request_index_v2.csv",
        index_rows,
        [
            "lead_id",
            "lead_type",
            "contact_surface",
            "url",
            "focus_use",
            "message_file",
            "sendable",
            "rows_acquired",
            "request_sent",
        ],
    )

    focus_fields = [
        "symbol",
        "timeframe",
        "provider_date_min",
        "provider_date_max",
        "source_date_min",
        "source_date_max",
        "source_overlap_sessions",
        "native_subhour_source_overlap_ready",
        "blocker",
        "intake_row_file",
        "intake_provenance_file",
    ]
    write_csv(OUT_DIR / "r3_native_subhour_focus_cells_v2.csv", focus_rows, focus_fields)

    row_file_exists = Path(REQUIRED_ROW_FILE).exists()
    provenance_file_exists = Path(REQUIRED_PROVENANCE_FILE).exists()
    rows_acquired = row_file_exists and provenance_file_exists
    gate_result = "r3_native_subhour_sendable_requests_v2=sendable_requests_created_rows_not_acquired_no_downstream"

    summary = {
        "run_id": RUN_ID,
        "board": str(BOARD),
        "board_sha256_at_run": board_sha256,
        "current_cursor_observed": current_cursor,
        "request_package": str(REQUEST_RUN),
        "contact_leads": str(CONTACT_RUN),
        "gate_result": gate_result,
        "active_native_intraday_request_rows": request["native_intraday_target_count"],
        "focus_cell_count": len(focus_rows),
        "focus_cells": focus_rows,
        "expected_focus_cells_present": focus_set == EXPECTED_FOCUS,
        "required_intake_root": INTAKE_ROOT,
        "required_row_file": REQUIRED_ROW_FILE,
        "required_provenance_file": REQUIRED_PROVENANCE_FILE,
        "row_file_exists": row_file_exists,
        "provenance_file_exists": provenance_file_exists,
        "rows_acquired": rows_acquired,
        "request_sent": False,
        "sendable_request_count": len(messages),
        "contact_lead_count": len(contacts),
        "contact_lead_type_counts": dict(contact_counts),
        "deferred_non_focus_leads": [
            row["lead_id"] for row in index_rows if row["sendable"] == "false"
        ],
        "required_field_count": len(required_fields),
        "request_template_used": template_text.startswith("# Native Sub-hour Source Label Intake Request Template"),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "r3_native_subhour_closed": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "raw_data_committed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "external_requests_sent": False,
    }
    (OUT_DIR / "r3_native_subhour_sendable_requests_v2.json").write_text(json.dumps(summary, indent=2) + "\n")

    message_lines = "\n".join(
        f"- `{msg['message_file']}`: {msg['purpose']}" for msg in messages
    )
    (OUT_DIR / "r3_native_subhour_sendable_requests_v2.md").write_text(
        f"""# R3 Native Sub-hour Sendable Requests v2

- Run id: `{RUN_ID}`.
- Gate result: `{gate_result}`.
- Board cursor observed: `{current_cursor}`.
- Request package: `{REQUEST_RUN}`.
- Contact leads: `{CONTACT_RUN}`.
- Active native intraday request rows: `{request['native_intraday_target_count']}`.
- Focus blocker cells: `{len(focus_rows)}`.
- Sendable request drafts created: `{len(messages)}`.
- Required intake root: `{INTAKE_ROOT}`.
- Required files: `{REQUIRED_ROW_FILE}` and `{REQUIRED_PROVENANCE_FILE}`.
- Rows acquired: `false`; requests sent: `false`; accepted rows added: `0`.
- Canonical merge allowed: `false`; downstream chain rerun allowed: `false`; strict full objective achieved: false. `update_goal=false`.
- Runtime code changed: false. Shared intake mutated: false. Raw data committed: false. External requests sent: false.

## Focus Cells

{focus_table(focus_rows)}

## Request Drafts

{message_lines}

## Boundary

This packet only turns the existing R3 request/contact artifacts into sendable request drafts. It does not create source labels, does not download rows, does not create `{INTAKE_ROOT}`, and does not run provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree promotion.
"""
    )

    checks = [
        ("board_present", BOARD.exists()),
        ("current_cursor_010127", "20260512T010127" in current_cursor),
        ("request_json_present", REQUEST_JSON.exists()),
        ("contact_csv_present", CONTACT_CSV.exists()),
        ("focus_cell_count_4", len(focus_rows) == 4),
        ("focus_cells_expected", focus_set == EXPECTED_FOCUS),
        ("active_native_intraday_target_count_336", request["native_intraday_target_count"] == 336),
        ("required_field_count_ge_18", len(required_fields) >= 18),
        ("contact_lead_count_9", len(contacts) == 9),
        ("sendable_request_count_4", len(messages) == 4),
        ("row_file_absent", not row_file_exists),
        ("provenance_file_absent", not provenance_file_exists),
        ("rows_acquired_false", not rows_acquired),
        ("requests_sent_false", not summary["request_sent"]),
        ("accepted_rows_added_zero", summary["accepted_rows_added"] == 0),
        ("r3_closed_false", not summary["r3_native_subhour_closed"]),
        ("downstream_chain_rerun_allowed_false", not summary["downstream_chain_rerun_allowed"]),
        ("strict_full_objective_achieved_false", not summary["strict_full_objective_achieved"]),
        ("update_goal_false", not summary["update_goal"]),
        ("runtime_code_changed_false", not summary["runtime_code_changed"]),
        ("shared_intake_mutated_false", not summary["shared_intake_mutated"]),
        ("raw_data_committed_false", not summary["raw_data_committed"]),
        ("external_requests_sent_false", not summary["external_requests_sent"]),
    ]
    assertion_text = "\n".join(f"{name}={'PASS' if ok else 'FAIL'}" for name, ok in checks) + "\n"
    (CHECK_DIR / "r3_native_subhour_sendable_requests_v2_assertions.out").write_text(assertion_text)

    failed = [name for name, ok in checks if not ok]
    if failed:
        raise SystemExit("failed checks: " + ", ".join(failed))


if __name__ == "__main__":
    main()
