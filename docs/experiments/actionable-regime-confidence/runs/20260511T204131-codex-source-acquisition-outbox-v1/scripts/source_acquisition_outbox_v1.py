#!/usr/bin/env python3
"""Consolidated source-acquisition outbox for Board A strict blockers."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T204131-codex-source-acquisition-outbox-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "source-acquisition-outbox"
CHECK_DIR = RUN_ROOT / "checks"

R2_CONTACT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T202712-codex-source-label-equivalence-contact-leads-v1/source-label-equivalence-contact-leads/source_label_equivalence_contact_leads_v1.json"
R3_REQUEST = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T203100-codex-native-subhour-intake-request-package-v1/native-subhour-intake-request-package/native_subhour_intake_request_package_v1.json"
R3_CONTACT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T203505-codex-native-subhour-contact-leads-v1/native-subhour-contact-leads/native_subhour_contact_leads_v1.json"
R4R5_STOCK_CONTACT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T202304-codex-stock-regime-owner-contact-leads-v1/stock-regime-owner-contact-leads/stock_regime_owner_contact_leads_v1.json"
R5_KAGGLE_REFRESH = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T202501-codex-kaggle-stock-regime-live-refresh-v1/kaggle-stock-regime-live-refresh/kaggle_stock_regime_live_refresh_v1.json"
R6_DO_CONTACT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T201759-codex-do-putnins-contact-leads-v1/do-putnins-contact-leads/do_putnins_contact_leads_v1.json"
R6_DIRECT_MATRIX = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T203523-codex-direct-manipulation-species-request-matrix-v1/direct-manipulation-species-request-matrix/direct_manipulation_species_request_matrix_v1.json"
V34_AUDIT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T203817-codex-current-goal-completion-audit-v34-after-request-matrices/completion-audit/current_goal_completion_audit_v34_after_request_matrices.json"


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def count_leads(payload: dict[str, object]) -> int:
    value = payload.get("contact_lead_count")
    if isinstance(value, int):
        return value
    leads = payload.get("contact_leads")
    return len(leads) if isinstance(leads, list) else 0


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    r2 = load_json(R2_CONTACT)
    r3_request = load_json(R3_REQUEST)
    r3_contact = load_json(R3_CONTACT)
    stock_contact = load_json(R4R5_STOCK_CONTACT)
    kaggle_refresh = load_json(R5_KAGGLE_REFRESH)
    do_contact = load_json(R6_DO_CONTACT)
    direct_matrix = load_json(R6_DIRECT_MATRIX)
    v34 = load_json(V34_AUDIT)

    outbox_rows = [
        {
            "outbox_id": "R2-source-label-equivalence-crossmarket",
            "requirements": "R2",
            "source_artifacts": str(R2_CONTACT.relative_to(REPO)),
            "primary_contact_surface": "Kaggle owner, Nasdaq indexes/licensing, CME, Kraken public data/contact surfaces",
            "required_intake_root": "/tmp/ict-engine-source-label-equivalence-intake",
            "required_files": "source_label_equivalence_rows.csv;source_label_equivalence_provenance.json",
            "request_payload": "owner-approved or source-owned cross-market/species equivalence rows and provenance",
            "lead_count": count_leads(r2),
            "request_sent": False,
            "rows_acquired": False,
            "gate_after_request": "rerun source_label_equivalence_intake_verifier_v1.py",
        },
        {
            "outbox_id": "R3-native-subhour-source-labels",
            "requirements": "R3",
            "source_artifacts": f"{R3_REQUEST.relative_to(REPO)};{R3_CONTACT.relative_to(REPO)}",
            "primary_contact_surface": "Kaggle stock-regime owner, Yahoo/Yahoo terms, Nasdaq, CME, Cboe, Polygon",
            "required_intake_root": "/tmp/ict-engine-native-subhour-source-label-intake",
            "required_files": "native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json",
            "request_payload": "source-native 1m/5m/15m/30m/1h/4h Bull/Bear/Sideways/Crisis labels with per-row provenance",
            "lead_count": count_leads(r3_contact),
            "request_sent": False,
            "rows_acquired": False,
            "gate_after_request": "rerun native-subhour intake package check and source-label verifier if crosswalk rows are also supplied",
        },
        {
            "outbox_id": "R4-R5-stock-regime-owner-recency-and-1h",
            "requirements": "R4;R5",
            "source_artifacts": f"{R4R5_STOCK_CONTACT.relative_to(REPO)};{R5_KAGGLE_REFRESH.relative_to(REPO)}",
            "primary_contact_surface": "Kaggle stock-regime owner discussion/profile and collaborator profile",
            "required_intake_root": "/tmp/ict-engine-source-panel-recency-extension",
            "required_files": "stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json",
            "request_payload": "post-2026-01-30 source-owned extension rows for XOM/Sideways, UNH/Bear, ^DJI/Sideways, AMD/Bear and strict 1h source/provenance if available",
            "lead_count": count_leads(stock_contact),
            "request_sent": False,
            "rows_acquired": False,
            "gate_after_request": "rerun source_panel_recency_extension_verifier_v1.py and strict 1h source gates",
        },
        {
            "outbox_id": "R6-do-putnins-spoofing-layering",
            "requirements": "R6",
            "source_artifacts": str(R6_DO_CONTACT.relative_to(REPO)),
            "primary_contact_surface": "SSRN author email links, SSRN contact-author, UTS profile, RePEc fallback",
            "required_intake_root": "/tmp/ict-engine-direct-manipulation-row-intake",
            "required_files": "positive_spoofing_layering_rows.csv;matched_negative_normal_activity_rows.csv;provenance_manifest.json",
            "request_payload": "owner-approved prosecuted-case spoofing/layering positives, matched same-schema controls, and provenance manifest",
            "lead_count": count_leads(do_contact),
            "request_sent": False,
            "rows_acquired": False,
            "gate_after_request": "rerun direct_manipulation_row_intake_verifier_v1.py then chronological/heldout calibration",
        },
        {
            "outbox_id": "R6-direct-manipulation-remaining-species",
            "requirements": "R6",
            "source_artifacts": str(R6_DIRECT_MATRIX.relative_to(REPO)),
            "primary_contact_surface": "direct species matrix candidates plus no-candidate placeholders for bear_raid and painting_tape",
            "required_intake_root": "/tmp/ict-engine-direct-manipulation-row-intake",
            "required_files": "positive_spoofing_layering_rows.csv;matched_negative_normal_activity_rows.csv;provenance_manifest.json",
            "request_payload": "source-owned positives, matched controls, and provenance for spoofing_layering, quote_spoofing, quote_stuffing, pinging, bear_raid, painting_tape",
            "lead_count": int(direct_matrix.get("matrix_row_count", 0) or 0),
            "request_sent": False,
            "rows_acquired": False,
            "gate_after_request": "extend direct verifier package and rerun strict R6 calibration",
        },
    ]

    required_roots = sorted({row["required_intake_root"] for row in outbox_rows})
    payload: dict[str, object] = {
        "run_id": RUN_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decision": "source_acquisition_outbox_v1=outbox_ready_rows_not_acquired",
        "prior_v34_decision": v34.get("decision"),
        "outbox_rows": outbox_rows,
        "outbox_row_count": len(outbox_rows),
        "required_intake_roots": required_roots,
        "request_sent": False,
        "rows_acquired": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "operator_boundary": "Do not send external requests or post authenticated messages without explicit user approval.",
    }

    json_path = OUT_DIR / "source_acquisition_outbox_v1.json"
    report_path = OUT_DIR / "source_acquisition_outbox_v1.md"
    outbox_csv = OUT_DIR / "source_acquisition_outbox_v1.csv"
    assertion_path = CHECK_DIR / "source_acquisition_outbox_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        outbox_csv,
        outbox_rows,
        [
            "outbox_id",
            "requirements",
            "source_artifacts",
            "primary_contact_surface",
            "required_intake_root",
            "required_files",
            "request_payload",
            "lead_count",
            "request_sent",
            "rows_acquired",
            "gate_after_request",
        ],
    )

    lines = [
        "# Source Acquisition Outbox v1",
        "",
        f"- Decision: `{payload['decision']}`",
        f"- Prior v34 decision: `{payload['prior_v34_decision']}`",
        f"- Outbox rows: `{payload['outbox_row_count']}`",
        f"- Required intake roots: `{len(required_roots)}`",
        "- Request sent: `false`; rows acquired: `false`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Outbox",
        "",
        "| ID | Requirements | Required Files | Gate After Request |",
        "|---|---|---|---|",
    ]
    for row in outbox_rows:
        lines.append(
            f"| `{row['outbox_id']}` | `{row['requirements']}` | `{row['required_files']}` | {row['gate_after_request']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This artifact is a send-ready queue only. It does not contact owners, use authenticated accounts, download private rows, create intake files, or promote proxy labels. The next real closure step is external acquisition of the required source-owned or owner-approved files, followed by the existing fail-closed verifiers.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- Outbox CSV: `{outbox_csv}`",
            f"- Assertions: `{assertion_path}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        ("outbox_row_count_5", len(outbox_rows) == 5),
        ("has_R2", any(row["requirements"] == "R2" for row in outbox_rows)),
        ("has_R3", any(row["requirements"] == "R3" for row in outbox_rows)),
        ("has_R4_R5", any(row["requirements"] == "R4;R5" for row in outbox_rows)),
        ("has_R6", sum(1 for row in outbox_rows if row["requirements"] == "R6") >= 2),
        ("request_sent_false", payload["request_sent"] is False),
        ("rows_acquired_false", payload["rows_acquired"] is False),
        ("accepted_rows_added_zero", payload["accepted_rows_added"] == 0),
        ("strict_full_objective_achieved_false", payload["strict_full_objective_achieved"] is False),
        ("update_goal_false", payload["update_goal"] is False),
        ("raw_data_committed_false", payload["raw_data_committed"] is False),
    ]
    assertion_path.write_text(
        "\n".join(f"{name}={'PASS' if passed else 'FAIL'}" for name, passed in assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if all(passed for _, passed in assertions) else 1


if __name__ == "__main__":
    raise SystemExit(main())
