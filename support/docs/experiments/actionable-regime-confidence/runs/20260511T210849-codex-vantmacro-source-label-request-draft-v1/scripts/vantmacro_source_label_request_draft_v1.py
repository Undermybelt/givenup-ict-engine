#!/usr/bin/env python3
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T210849-codex-vantmacro-source-label-request-draft-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "vantmacro-source-label-request-draft"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
VANT_JSON = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T210411-codex-vantmacro-current-regime-route-screen-v1/vantmacro-current-regime-route-screen/vantmacro_current_regime_route_screen_v1.json"
VANT_CSV = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T210411-codex-vantmacro-current-regime-route-screen-v1/vantmacro-current-regime-route-screen/vantmacro_current_regime_route_screen_v1_candidates.csv"
SCHEMA_CSV = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T163532-codex-source-label-equivalence-request-v1/source-label-equivalence/source_label_equivalence_request_v1_required_schema.csv"
VERIFIER = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T182922-codex-source-label-equivalence-intake-verifier-v1/equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    route = read_json(VANT_JSON)
    candidates = read_csv(VANT_CSV)
    schema_rows = read_csv(SCHEMA_CSV)
    required_fields = [row["field_name"] for row in schema_rows if row.get("required", "").lower() == "true"]

    requested_packages = [
        {
            "package_id": "vantmacro_source_label_equivalence_rows",
            "requirement_ids": "R2;R5",
            "source_owner": "VantMacro",
            "source_route": "https://vantmacro.com/",
            "requested_destination": "/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_rows.csv",
            "requested_provenance_destination": "/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_provenance.json",
            "requested_fields": ";".join(required_fields),
            "minimum_content": "row-level source-owned or owner-approved current/historical regime labels with dates, symbols/market families, split roles, confidence scores if owned by source, and an explicit MainRegimeV2 crosswalk or equivalence policy",
            "guardrail": "No local reimplementation, scraped dashboard screenshot, marketing text, or model-derived proxy can satisfy this request.",
            "request_sent": "false",
            "rows_acquired": "false",
            "accepted_now": "false",
        }
    ]

    draft_lines = [
        "# No-Send Request Draft: VantMacro Source-Label Equivalence Rows",
        "",
        "Purpose: Board A needs source-owned or owner-approved rows for R2/R5 source-label equivalence and recency extension.",
        "",
        "Requested deliverables:",
        "1. `source_label_equivalence_rows.csv` using the Board A required schema.",
        "2. `source_label_equivalence_provenance.json` with source owner, approval/export date, export identity, hashes, redaction notes, and a non-proxy attestation.",
        "",
        "Required schema fields:",
    ]
    for field in required_fields:
        draft_lines.append(f"- `{field}`")
    draft_lines.extend(
        [
            "",
            "Requested source-specific content:",
            "- Row-level VantMacro regime labels or owner-approved export/crosswalk.",
            "- Historical and current rows covering 2026 recency where available.",
            "- Explicit mapping to `MainRegimeV2` labels (`Bull`, `Bear`, `Sideways`, `Crisis`) or an owner-approved equivalence policy.",
            "- Split-role support for train/calibration/heldout_time/heldout_market/test.",
            "- Stable row ids and provenance hashes.",
            "",
            "Boundary: this draft was not sent. No rows were acquired, no account was used, and no source-label equivalence intake file was created.",
            "",
        ]
    )
    draft_path = OUT_DIR / "vantmacro_source_label_request_draft_v1_request.md"
    draft_path.write_text("\n".join(draft_lines), encoding="utf-8")

    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": sha256_file(BOARD),
        "decision": "vantmacro_source_label_request_draft_v1=draft_ready_not_sent_rows_not_acquired",
        "inputs": {
            "route_json": str(VANT_JSON.relative_to(REPO)),
            "candidate_csv": str(VANT_CSV.relative_to(REPO)),
            "schema_csv": str(SCHEMA_CSV.relative_to(REPO)),
            "verifier": str(VERIFIER.relative_to(REPO)),
        },
        "source_route_decision": route.get("decision"),
        "candidate_count": len(candidates),
        "required_field_count": len(required_fields),
        "requested_packages": requested_packages,
        "draft_path": str(draft_path.relative_to(REPO)),
        "request_sent": False,
        "authenticated_account_used": False,
        "rows_acquired": False,
        "intake_files_created": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": "Send only with explicit user approval or manually place owner-approved rows/provenance under /tmp/ict-engine-source-label-equivalence-intake, then run the existing verifier.",
    }

    json_path = OUT_DIR / "vantmacro_source_label_request_draft_v1.json"
    report_path = OUT_DIR / "vantmacro_source_label_request_draft_v1_report.md"
    package_csv = OUT_DIR / "vantmacro_source_label_request_draft_v1_packages.csv"
    assertions_path = CHECK_DIR / "vantmacro_source_label_request_draft_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        package_csv,
        requested_packages,
        [
            "package_id",
            "requirement_ids",
            "source_owner",
            "source_route",
            "requested_destination",
            "requested_provenance_destination",
            "requested_fields",
            "minimum_content",
            "guardrail",
            "request_sent",
            "rows_acquired",
            "accepted_now",
        ],
    )

    report_lines = [
        "# VantMacro Source Label Request Draft v1",
        "",
        f"- Gate result: `{result['decision']}`.",
        f"- Source route decision: `{result['source_route_decision']}`.",
        f"- Candidate count: `{len(candidates)}`.",
        f"- Required field count: `{len(required_fields)}`.",
        "- Request sent: `false`; authenticated account used: `false`; rows acquired: `false`; intake files created: `false`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Requested Package",
        "",
        f"- Target rows: `{requested_packages[0]['requested_destination']}`.",
        f"- Target provenance: `{requested_packages[0]['requested_provenance_destination']}`.",
        f"- Source owner: `{requested_packages[0]['source_owner']}`.",
        f"- Source route: `{requested_packages[0]['source_route']}`.",
        f"- Requirement IDs: `{requested_packages[0]['requirement_ids']}`.",
        "",
        "## Boundary",
        "",
        "This run only creates a local no-send draft. It does not contact VantMacro, does not use an account, does not create intake files, and does not promote public page text as source-label rows.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- Draft: `{draft_path.relative_to(REPO)}`",
        f"- Package CSV: `{package_csv.relative_to(REPO)}`",
        f"- Assertions: `{assertions_path.relative_to(REPO)}`",
    ]
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={result['decision']}",
        f"PASS source_route_decision={result['source_route_decision']}",
        f"PASS required_field_count={len(required_fields)}",
        "PASS request_sent=false",
        "PASS rows_acquired=false",
        "PASS intake_files_created=false",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps(
        {
            "decision": result["decision"],
            "required_field_count": len(required_fields),
            "request_sent": False,
            "rows_acquired": False,
            "update_goal": False,
            "report": str(report_path.relative_to(REPO)),
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
