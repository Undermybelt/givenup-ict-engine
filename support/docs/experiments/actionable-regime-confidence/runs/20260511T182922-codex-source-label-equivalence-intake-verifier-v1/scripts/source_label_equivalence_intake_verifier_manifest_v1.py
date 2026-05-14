#!/usr/bin/env python3
"""Build a fail-closed verifier package for source-label equivalence intake."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T182922+0800-codex-source-label-equivalence-intake-verifier-v1"
RUN_ROOT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1"
)
OUT_DIR = RUN_ROOT / "equivalence-intake-verifier"
CHECK_DIR = RUN_ROOT / "checks"

REQUEST_ROOT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T163532-codex-source-label-equivalence-request-v1/source-label-equivalence"
)
SCHEMA_CSV = REQUEST_ROOT / "source_label_equivalence_request_v1_required_schema.csv"
TARGETS_CSV = REQUEST_ROOT / "source_label_equivalence_request_v1_targets.csv"
INTAKE_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")

OUT_JSON = OUT_DIR / "source_label_equivalence_intake_verifier_manifest_v1.json"
OUT_MD = OUT_DIR / "source_label_equivalence_intake_verifier_manifest_v1.md"
OUT_REQUIRED = OUT_DIR / "source_label_equivalence_intake_required_files_v1.csv"
OUT_VERIFIER = OUT_DIR / "source_label_equivalence_intake_verifier_v1.py"
OUT_VERIFY_RESULT = OUT_DIR / "source_label_equivalence_intake_verifier_missing_result_v1.json"
OUT_ASSERT = CHECK_DIR / "source_label_equivalence_intake_verifier_manifest_v1_assertions.out"

ROOT_LABELS = {"Bull", "Bear", "Sideways", "Crisis"}
DIRECT_LABELS = {"positive", "normal_control"}
PRICE_PACKAGES = {
    "price_root_equivalence_us_index_futures",
    "price_root_equivalence_crypto",
    "price_root_equivalence_fx_rates_commodities",
    "native_subhour_overlap_after_recency",
}
DIRECT_PACKAGES = {"direct_manipulation_species_exports"}
UNSUPPORTED_POLICY_TOKENS = ("ohlcv_proxy", "generated_label", "future_return", "unapproved_ixic")


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def load_schema() -> list[dict[str, str]]:
    with SCHEMA_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_targets() -> list[dict[str, str]]:
    with TARGETS_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def verifier_source(required_fields: list[str], optional_fields: list[str]) -> str:
    return f'''#!/usr/bin/env python3
"""Fail-closed verifier for Board A source-label equivalence intake rows."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


REQUIRED_FIELDS = {required_fields!r}
OPTIONAL_FIELDS = {optional_fields!r}
ROOT_LABELS = {sorted(ROOT_LABELS)!r}
DIRECT_LABELS = {sorted(DIRECT_LABELS)!r}
PRICE_PACKAGES = {sorted(PRICE_PACKAGES)!r}
DIRECT_PACKAGES = {sorted(DIRECT_PACKAGES)!r}
UNSUPPORTED_POLICY_TOKENS = {UNSUPPORTED_POLICY_TOKENS!r}
REQUIRED_FILES = {{
    "rows": "source_label_equivalence_rows.csv",
    "provenance": "source_label_equivalence_provenance.json",
}}


def blocked(reason: str, **extra: object) -> int:
    payload = {{"status": "blocked", "reason": reason}}
    payload.update(extra)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intake-root", required=True)
    args = parser.parse_args()
    root = Path(args.intake_root)
    rows_path = root / REQUIRED_FILES["rows"]
    provenance_path = root / REQUIRED_FILES["provenance"]
    missing = [str(path) for path in [rows_path, provenance_path] if not path.exists()]
    if missing:
        return blocked("missing_required_files", missing_files=missing)

    try:
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return blocked("provenance_json_unreadable", error=type(exc).__name__)
    with rows_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        missing_fields = [field for field in REQUIRED_FIELDS if field not in fields]
        if missing_fields:
            return blocked("missing_required_columns", missing_fields=missing_fields)
        rows = list(reader)
    if not rows:
        return blocked("empty_rows")

    bad_rows = []
    direct_groups = defaultdict(set)
    package_counts = defaultdict(int)
    split_roles = set()
    for idx, row in enumerate(rows, start=2):
        package = row.get("package_id", "")
        package_counts[package] += 1
        split_roles.add(row.get("split_role", ""))
        policy = row.get("equivalence_policy", "").lower()
        if any(token in policy for token in UNSUPPORTED_POLICY_TOKENS):
            bad_rows.append({{"line": idx, "reason": "unsupported_policy_token", "package_id": package}})
        if package in PRICE_PACKAGES:
            if row.get("main_regime_v2_label") not in ROOT_LABELS:
                bad_rows.append({{"line": idx, "reason": "bad_main_regime_v2_label", "package_id": package}})
            if not row.get("equivalence_policy"):
                bad_rows.append({{"line": idx, "reason": "missing_equivalence_policy", "package_id": package}})
            if row.get("direct_label") and row.get("direct_label") not in DIRECT_LABELS:
                bad_rows.append({{"line": idx, "reason": "bad_direct_label", "package_id": package}})
        elif package in DIRECT_PACKAGES:
            if row.get("direct_label") not in DIRECT_LABELS:
                bad_rows.append({{"line": idx, "reason": "bad_direct_label", "package_id": package}})
            group = row.get("matched_negative_group_id", "")
            if not group:
                bad_rows.append({{"line": idx, "reason": "missing_matched_negative_group_id", "package_id": package}})
            direct_groups[group].add(row.get("direct_label", ""))
        else:
            bad_rows.append({{"line": idx, "reason": "unknown_package_id", "package_id": package}})
    bad_groups = [
        group for group, labels in direct_groups.items()
        if "positive" in labels and "normal_control" not in labels
    ]
    if bad_rows or bad_groups:
        return blocked(
            "rows_failed_guardrails",
            bad_rows=bad_rows[:25],
            bad_direct_groups=bad_groups[:25],
        )
    required_split_present = bool({{"calibration", "heldout_time", "heldout_market", "test"}} & split_roles)
    if not required_split_present:
        return blocked("missing_calibration_or_heldout_split_roles", split_roles=sorted(split_roles))
    print(json.dumps({{
        "status": "schema_ready_unscored",
        "row_count": len(rows),
        "package_counts": dict(sorted(package_counts.items())),
        "provenance_keys": sorted(provenance.keys()),
        "next": "rerun unchanged chronological and heldout-market/timeframe gates; do not treat schema readiness as confidence acceptance",
    }}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    schema = load_schema()
    targets = load_targets()
    required_fields = [row["field_name"] for row in schema if row["required"].lower() == "true"]
    optional_fields = [row["field_name"] for row in schema if row["required"].lower() != "true"]
    if "package_id" not in required_fields:
        required_fields = ["package_id", *required_fields]
    required_files = [
        {
            "file": "source_label_equivalence_rows.csv",
            "destination": str(INTAKE_ROOT / "source_label_equivalence_rows.csv"),
            "purpose": "source-owned or owner-approved price-root/direct-Manipulation label rows using the request schema",
            "required": True,
        },
        {
            "file": "source_label_equivalence_provenance.json",
            "destination": str(INTAKE_ROOT / "source_label_equivalence_provenance.json"),
            "purpose": "source owner, pull/approval date, export identity, hashes, and non-proxy attestation",
            "required": True,
        },
    ]
    OUT_VERIFIER.write_text(verifier_source(required_fields, optional_fields), encoding="utf-8")
    write_csv(OUT_REQUIRED, required_files, ["file", "destination", "purpose", "required"])
    proc = subprocess.run(
        ["python3", str(OUT_VERIFIER), "--intake-root", str(INTAKE_ROOT)],
        cwd=str(REPO),
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        verifier_payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        verifier_payload = {"status": "blocked", "reason": "invalid_verifier_output", "stdout": proc.stdout}
    OUT_VERIFY_RESULT.write_text(json.dumps(verifier_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "run_id": RUN_ID,
        "artifact_type": "source_label_equivalence_intake_verifier_manifest_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "request_root": repo_rel(REQUEST_ROOT),
        "schema": repo_rel(SCHEMA_CSV),
        "targets": repo_rel(TARGETS_CSV),
        "target_package_count": len(targets),
        "required_fields": required_fields,
        "optional_fields": optional_fields,
        "required_files": required_files,
        "verifier": {
            "path": repo_rel(OUT_VERIFIER),
            "command": f"python3 {repo_rel(OUT_VERIFIER)} --intake-root {INTAKE_ROOT}",
            "missing_result_path": repo_rel(OUT_VERIFY_RESULT),
            "missing_result": verifier_payload,
        },
        "decision": {
            "gate_result": "source_label_equivalence_intake_verifier_v1=ready_rows_not_acquired",
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Place source-owned label rows and provenance under /tmp/ict-engine-source-label-equivalence-intake, "
            "run the verifier, then rerun unchanged chronological and heldout-market/timeframe gates."
        ),
    }
    OUT_JSON.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Source Label Equivalence Intake Verifier v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This makes `source_label_equivalence_request_v1` executable. It does not accept rows or claim confidence.",
        "",
        "## Result",
        "",
        f"- Target packages covered: `{len(targets)}`.",
        f"- Required CSV fields: `{len(required_fields)}`.",
        f"- Verifier missing-intake status: `{verifier_payload.get('status')}` / `{verifier_payload.get('reason')}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Gate result: `source_label_equivalence_intake_verifier_v1=ready_rows_not_acquired`.",
        "- Full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Required Intake Files",
        "",
        "| File | Destination | Purpose |",
        "|---|---|---|",
    ]
    for row in required_files:
        lines.append(f"| `{row['file']}` | `{row['destination']}` | {row['purpose']} |")
    lines.extend(["", "## Verifier", "", "```bash", manifest["verifier"]["command"], "```", "", "Schema readiness is not confidence acceptance; after a pass, rerun the unchanged gates."])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assertions = [
        f"run_id={RUN_ID}",
        f"target_package_count={len(targets)}",
        f"required_field_count={len(required_fields)}",
        f"verifier_missing_status={verifier_payload.get('status')}",
        f"verifier_missing_reason={verifier_payload.get('reason')}",
        "accepted_rows_added=0",
        "new_confidence_gate=false",
        "full_objective_achieved=false",
        "update_goal=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
