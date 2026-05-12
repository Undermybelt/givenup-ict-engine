#!/usr/bin/env python3
"""Build a fail-closed intake manifest for direct Manipulation row exports."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T151950+0800-codex-direct-manipulation-row-intake-manifest-v1"
RUN_ROOT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
)
OUT_DIR = RUN_ROOT / "direct-manipulation-intake"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
FINRA_SCHEMA_CSV = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T133337-codex-finra-manipulation-acquisition-schema-v1/"
    "acquisition-schema/finra_manipulation_acquisition_schema_v1.csv"
)
FINRA_SCHEMA_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T133337-codex-finra-manipulation-acquisition-schema-v1/"
    "acquisition-schema/finra_manipulation_acquisition_schema_v1.json"
)
LOCAL_CHECK = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T134038-codex-local-row-export-acquisition-check-v1/"
    "acquisition-check/local_row_export_acquisition_check_v1.json"
)
LOCAL_INVENTORY = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T134054-codex-local-row-export-inventory-v1/"
    "local-inventory/local_row_export_inventory_v1.json"
)
DIRECT_MATRIX = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T131311-codex-direct-manipulation-variety-matrix-v1/"
    "direct-manipulation/direct_manipulation_variety_matrix_v1.json"
)

OUT_JSON = OUT_DIR / "direct_manipulation_row_intake_manifest_v1.json"
OUT_MD = OUT_DIR / "direct_manipulation_row_intake_manifest_v1.md"
OUT_CSV = OUT_DIR / "direct_manipulation_row_intake_required_files_v1.csv"
OUT_VERIFIER = OUT_DIR / "direct_manipulation_row_intake_verifier_v1.py"
OUT_ASSERT = CHECK_DIR / "direct_manipulation_row_intake_manifest_v1_assertions.out"


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_schema() -> list[dict[str, str]]:
    with FINRA_SCHEMA_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def verifier_source(required_fields: list[str]) -> str:
    fields_literal = repr(required_fields)
    return f'''#!/usr/bin/env python3
"""Fail-closed verifier for direct Manipulation row intake exports."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


REQUIRED_FIELDS = {fields_literal}
REQUIRED_FILES = {{
    "positive_rows": "positive_spoofing_layering_rows.csv",
    "matched_negative_rows": "matched_negative_normal_activity_rows.csv",
    "provenance_manifest": "provenance_manifest.json",
}}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [field for field in REQUIRED_FIELDS if field not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(f"missing_required_fields in {{path}}: {{missing}}")
        return list(reader)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intake-root", required=True)
    args = parser.parse_args()
    root = Path(args.intake_root)
    paths = {{name: root / filename for name, filename in REQUIRED_FILES.items()}}
    missing_files = [str(path) for path in paths.values() if not path.exists()]
    if missing_files:
        print(json.dumps({{"status": "blocked", "reason": "missing_required_files", "missing_files": missing_files}}, indent=2))
        return 2

    positives = read_csv_rows(paths["positive_rows"])
    negatives = read_csv_rows(paths["matched_negative_rows"])
    provenance = json.loads(paths["provenance_manifest"].read_text(encoding="utf-8"))
    if not positives or not negatives:
        print(json.dumps({{"status": "blocked", "reason": "empty_positive_or_negative_rows"}}, indent=2))
        return 2
    positive_groups = {{row["matched_negative_group_id"] for row in positives if row.get("matched_negative_group_id")}}
    negative_groups = {{row["matched_negative_group_id"] for row in negatives if row.get("matched_negative_group_id")}}
    orphan_groups = sorted(positive_groups - negative_groups)
    if orphan_groups:
        print(json.dumps({{"status": "blocked", "reason": "positive_groups_without_matched_negatives", "groups": orphan_groups[:20]}}, indent=2))
        return 2
    print(json.dumps({{
        "status": "schema_ready_unscored",
        "positive_rows": len(positives),
        "matched_negative_rows": len(negatives),
        "matched_group_count": len(positive_groups & negative_groups),
        "provenance_keys": sorted(provenance.keys()),
        "next": "run chronological and heldout-symbol/venue Wilson95 calibration gate"
    }}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    schema_rows = read_schema()
    required_fields = [row["field"] for row in schema_rows if row["required"].strip().lower() == "true"]
    all_fields = [row["field"] for row in schema_rows]
    finra_schema = load_json(FINRA_SCHEMA_JSON)
    local_check = load_json(LOCAL_CHECK)
    local_inventory = load_json(LOCAL_INVENTORY)
    direct_matrix = load_json(DIRECT_MATRIX)

    required_files = [
        {
            "file": "positive_spoofing_layering_rows.csv",
            "destination": "/tmp/ict-engine-direct-manipulation-row-intake/positive_spoofing_layering_rows.csv",
            "purpose": "direct positive spoofing/layering rows",
            "required": True,
        },
        {
            "file": "matched_negative_normal_activity_rows.csv",
            "destination": "/tmp/ict-engine-direct-manipulation-row-intake/matched_negative_normal_activity_rows.csv",
            "purpose": "same-schema normal controls matched by venue/symbol/date/session/liquidity bucket",
            "required": True,
        },
        {
            "file": "provenance_manifest.json",
            "destination": "/tmp/ict-engine-direct-manipulation-row-intake/provenance_manifest.json",
            "purpose": "source export identity, pull date, source owner, redaction notes",
            "required": True,
        },
    ]

    manifest = {
        "run_id": RUN_ID,
        "artifact_type": "direct_manipulation_row_intake_manifest_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": repo_rel(BOARD),
        "board_sha256_at_run": sha256(BOARD),
        "purpose": "Make the direct Manipulation blocker executable without accepting proxy rows.",
        "target": {
            "taxonomy": "direct Manipulation",
            "variety": "spoofing_layering",
            "consumer_gate": "direct_manipulation_gate",
            "not_main_regime_price_root": True,
        },
        "accepted_source_classes": [
            {
                "name": "FINRA Potential Manipulation Report detail export",
                "url": "https://www.finra.org/compliance-tools/report-center/cross-market-equities-supervision/potential-manipulation-report",
                "condition": "authenticated/user-provided row export with positives and matched negatives",
            },
            {
                "name": "equivalent venue or surveillance order-lifecycle export",
                "url": "local_or_authenticated_source",
                "condition": "must match schema and include direct positives plus matched normal controls",
            },
        ],
        "rejected_source_classes": [
            {
                "name": "public FINRA documentation page alone",
                "reason": "schema/report description only; no exportable positive and matched-negative rows",
            },
            {
                "name": "OHLCV, session, liquidity, sweep, or HMM/model labels",
                "reason": "proxy labels are explicitly forbidden for direct Manipulation completion",
            },
            {
                "name": "synthetic or teaching microstructure datasets",
                "reason": "not accepted unless source provenance proves direct real order-lifecycle positives and controls",
            },
            {
                "name": "public enforcement case inventory without controls",
                "reason": "positive case metadata only; lacks matched negative row groups",
            },
        ],
        "required_files": required_files,
        "schema": {
            "schema_csv": repo_rel(FINRA_SCHEMA_CSV),
            "field_count": len(all_fields),
            "required_field_count": len(required_fields),
            "required_fields": required_fields,
            "all_fields": all_fields,
        },
        "existing_evidence": {
            "finra_schema_gate": finra_schema["decision"]["gate_result"],
            "local_row_check_gate": local_check["decision"]["gate_result"],
            "local_inventory_gate": local_inventory["gate_result"],
            "accepted_scoped_direct_varieties": direct_matrix["rollup"]["accepted_scoped_varieties"],
            "usable_local_finra_positive_rows": local_check["accepted_finra_like_positive_rows_found"],
            "usable_local_finra_matched_negative_rows": local_check["accepted_matched_negative_rows_found"],
        },
        "verifier": {
            "path": repo_rel(OUT_VERIFIER),
            "status": "ready_fail_closed",
            "command": (
                "python3 "
                + repo_rel(OUT_VERIFIER)
                + " --intake-root /tmp/ict-engine-direct-manipulation-row-intake"
            ),
            "pass_means": "required files and matched groups are present; scoring gate still must run next",
        },
        "decision": {
            "gate_result": "direct_manipulation_row_intake_manifest_v1_ready_rows_not_acquired",
            "accepted_direct_manipulation_rows_added": 0,
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Place authenticated/user-provided spoofing/layering positive rows, matched negative rows, "
            "and provenance manifest under /tmp/ict-engine-direct-manipulation-row-intake, then run the "
            "fail-closed verifier before any Wilson95 scoring."
        ),
    }

    write_csv(OUT_CSV, required_files, ["file", "destination", "purpose", "required"])
    OUT_VERIFIER.write_text(verifier_source(required_fields), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Direct Manipulation Row Intake Manifest v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This turns the remaining direct `Manipulation` blocker into an executable intake package. It does not accept proxy rows or claim new confidence.",
        "",
        "## Result",
        "",
        "- Target variety: `spoofing_layering`.",
        f"- Schema fields: `{len(all_fields)}`; required fields: `{len(required_fields)}`.",
        "- Accepted direct rows added: `0`.",
        "- Gate result: `direct_manipulation_row_intake_manifest_v1=ready_rows_not_acquired`.",
        "- Full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Required Intake Files",
        "",
        "| File | Destination | Purpose |",
        "|---|---|---|",
    ]
    for row in required_files:
        lines.append(f"| `{row['file']}` | `{row['destination']}` | {row['purpose']} |")
    lines.extend(
        [
            "",
            "## Verifier",
            "",
            "```bash",
            "python3 docs/experiments/actionable-regime-confidence/runs/20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py --intake-root /tmp/ict-engine-direct-manipulation-row-intake",
            "```",
            "",
            "The verifier is fail-closed: missing files, missing fields, empty positives/negatives, or positives without matched negative groups block the gate.",
            "",
            "## Guardrails",
            "",
            "- Public docs without row exports remain schema evidence only.",
            "- OHLCV/session/liquidity/sweep/HMM/model labels remain rejected proxies.",
            "- Synthetic or teaching datasets are not accepted unless they prove real direct order-lifecycle provenance.",
            "- Enforcement case metadata without matched negatives remains positive inventory only.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    failures = []
    if local_check["accepted_finra_like_positive_rows_found"] != 0:
        failures.append("unexpected_existing_positive_rows")
    if local_check["accepted_matched_negative_rows_found"] != 0:
        failures.append("unexpected_existing_matched_negative_rows")
    if "matched_negative_group_id" not in required_fields:
        failures.append("matched_negative_group_id_not_required")
    if manifest["decision"]["full_objective_achieved"]:
        failures.append("must_not_mark_full_objective_complete")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={manifest['board_sha256_at_run']}",
        f"field_count={len(all_fields)}",
        f"required_field_count={len(required_fields)}",
        f"verifier_path={repo_rel(OUT_VERIFIER)}",
        "accepted_direct_manipulation_rows_added=0",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "full_objective_achieved=false",
        "update_goal=false",
        f"assertion_status={'FAIL' if failures else 'PASS'}",
    ]
    if failures:
        assertions.append("failures=" + ",".join(failures))
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
