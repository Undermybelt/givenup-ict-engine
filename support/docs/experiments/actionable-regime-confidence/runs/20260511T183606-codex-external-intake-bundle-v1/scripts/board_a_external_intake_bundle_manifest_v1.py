#!/usr/bin/env python3
"""Build the Board A external intake bundle for remaining strict blockers."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T183606+0800-codex-external-intake-bundle-v1"
RUN_ROOT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T183606-codex-external-intake-bundle-v1"
)
OUT_DIR = RUN_ROOT / "external-intake-bundle"
CHECK_DIR = RUN_ROOT / "checks"
INTAKE_ROOT = Path("/tmp/ict-engine-board-a-external-intake-bundle-v1")

OUT_JSON = OUT_DIR / "board_a_external_intake_bundle_manifest_v1.json"
OUT_MD = OUT_DIR / "board_a_external_intake_bundle_manifest_v1.md"
OUT_REQUIRED = OUT_DIR / "board_a_external_intake_required_files_v1.csv"
OUT_SCHEMA = OUT_DIR / "board_a_external_intake_schema_v1.csv"
OUT_VERIFIER = OUT_DIR / "board_a_external_intake_verifier_v1.py"
OUT_MISSING = OUT_DIR / "board_a_external_intake_missing_result_v1.json"
OUT_ASSERT = CHECK_DIR / "board_a_external_intake_bundle_manifest_v1_assertions.out"

MAIN_REGIME_LABELS = {"Bull", "Bear", "Sideways", "Crisis"}
REQUIRED_PRICE_PACKAGES = {
    "us_index_futures_equivalence",
    "crypto_equivalence",
    "fx_rates_commodities_equivalence",
}
REQUIRED_DIRECT_SPECIES = {
    "spoofing_layering",
    "quote_stuffing",
    "pinging",
    "bear_raid",
    "painting_tape",
    "social_text_pump_dump",
}
ALLOWED_EQUIVALENCE_TYPES = {"source_owned_label", "owner_approved_crosswalk"}
UNSUPPORTED_TOKENS = (
    "provider_ohlcv",
    "ohlcv_proxy",
    "hmm",
    "generated_label",
    "future_return",
    "unapproved_ixic",
)

PRICE_FIELDS = [
    "package_id",
    "market_family",
    "root_symbol",
    "source_symbol",
    "source_timeframe",
    "source_start",
    "source_end",
    "source_label_column",
    "main_regime_v2_label",
    "qualifying_condition_id",
    "validation_instrument",
    "validation_period",
    "validation_market_context",
    "equivalence_type",
    "owner_approval_reference",
    "source_row_id",
    "provenance_hash",
]
RECENCY_FIELDS = [
    "package_id",
    "source_dataset",
    "market_family",
    "symbol",
    "timeframe",
    "timestamp",
    "main_regime_v2_label",
    "qualifying_condition_id",
    "validation_instrument",
    "validation_period",
    "validation_market_context",
    "source_revision_date",
    "source_row_id",
    "provenance_hash",
    "non_proxy_attestation",
]
DIRECT_POSITIVE_FIELDS = [
    "event_id",
    "species",
    "market_family",
    "symbol",
    "timeframe",
    "event_start",
    "event_end",
    "positive_label",
    "source_owner",
    "source_dataset",
    "source_row_id",
    "evidence_type",
    "matched_control_group_id",
    "provenance_hash",
    "source_url_or_record",
]
DIRECT_CONTROL_FIELDS = [
    "matched_control_group_id",
    "control_row_id",
    "control_symbol",
    "control_start",
    "control_end",
    "matching_dimensions",
    "normal_label",
    "source_owner",
    "source_dataset",
    "source_row_id",
    "provenance_hash",
]


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def verifier_source() -> str:
    return f'''#!/usr/bin/env python3
"""Fail-closed verifier for the Board A external intake bundle."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


MAIN_REGIME_LABELS = {sorted(MAIN_REGIME_LABELS)!r}
REQUIRED_PRICE_PACKAGES = {sorted(REQUIRED_PRICE_PACKAGES)!r}
REQUIRED_DIRECT_SPECIES = {sorted(REQUIRED_DIRECT_SPECIES)!r}
ALLOWED_EQUIVALENCE_TYPES = {sorted(ALLOWED_EQUIVALENCE_TYPES)!r}
UNSUPPORTED_TOKENS = {UNSUPPORTED_TOKENS!r}

REQUIRED_FILES = {{
    "price_rows": "price-root/source_label_equivalence_rows.csv",
    "price_provenance": "price-root/source_label_equivalence_provenance.json",
    "recency_rows": "recency/source_panel_recency_extension_rows.csv",
    "recency_provenance": "recency/source_panel_recency_extension_provenance.json",
    "direct_positive_rows": "direct-manipulation/direct_manipulation_positive_rows.csv",
    "direct_controls": "direct-manipulation/direct_manipulation_matched_controls.csv",
    "direct_provenance": "direct-manipulation/direct_manipulation_provenance.json",
}}
FIELDS = {{
    "price_rows": {PRICE_FIELDS!r},
    "recency_rows": {RECENCY_FIELDS!r},
    "direct_positive_rows": {DIRECT_POSITIVE_FIELDS!r},
    "direct_controls": {DIRECT_CONTROL_FIELDS!r},
}}
PROVENANCE_COMMON_KEYS = {{
    "source_owner",
    "pulled_at",
    "export_id",
    "source_urls",
    "input_file_hashes",
    "attestations",
}}


def blocked(reason: str, **extra: object) -> int:
    payload = {{"status": "blocked", "reason": reason}}
    payload.update(extra)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 2


def load_csv(path: Path, required_fields: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        missing = [field for field in required_fields if field not in fields]
        rows = list(reader)
    return rows, missing


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def has_unsupported_token(row: dict[str, str]) -> bool:
    text = " ".join(str(value).lower() for value in row.values())
    return any(token in text for token in UNSUPPORTED_TOKENS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intake-root", required=True)
    args = parser.parse_args()
    root = Path(args.intake_root)
    paths = {{name: root / rel for name, rel in REQUIRED_FILES.items()}}
    missing_files = [str(path) for path in paths.values() if not path.exists()]
    if missing_files:
        return blocked("missing_required_files", missing_files=missing_files)

    try:
        provenances = {{
            "price_provenance": load_json(paths["price_provenance"]),
            "recency_provenance": load_json(paths["recency_provenance"]),
            "direct_provenance": load_json(paths["direct_provenance"]),
        }}
    except Exception as exc:  # noqa: BLE001
        return blocked("provenance_json_unreadable", error=type(exc).__name__)

    missing_provenance_keys = {{
        name: sorted(PROVENANCE_COMMON_KEYS - set(payload.keys()))
        for name, payload in provenances.items()
    }}
    missing_provenance_keys = {{
        name: missing for name, missing in missing_provenance_keys.items() if missing
    }}
    if missing_provenance_keys:
        return blocked("missing_provenance_keys", missing_provenance_keys=missing_provenance_keys)
    attestations = {{
        name: payload.get("attestations", {{}})
        for name, payload in provenances.items()
    }}
    if not attestations["price_provenance"].get("owner_approved_main_regime_v2_equivalence"):
        return blocked("missing_price_equivalence_attestation")
    if not attestations["recency_provenance"].get("post_2026_01_30_source_revision"):
        return blocked("missing_recency_revision_attestation")
    if not attestations["direct_provenance"].get("matched_negative_policy"):
        return blocked("missing_direct_matched_negative_policy")

    tables: dict[str, list[dict[str, str]]] = {{}}
    missing_fields: dict[str, list[str]] = {{}}
    empty_tables: list[str] = []
    for name, fields in FIELDS.items():
        rows, missing = load_csv(paths[name], fields)
        tables[name] = rows
        if missing:
            missing_fields[name] = missing
        if not rows:
            empty_tables.append(name)
    if missing_fields:
        return blocked("missing_required_columns", missing_fields=missing_fields)
    if empty_tables:
        return blocked("empty_required_tables", empty_tables=empty_tables)

    bad_rows = []
    price_packages = set()
    labels_seen = set()
    for idx, row in enumerate(tables["price_rows"], start=2):
        price_packages.add(row.get("package_id", ""))
        labels_seen.add(row.get("main_regime_v2_label", ""))
        if row.get("package_id") not in REQUIRED_PRICE_PACKAGES:
            bad_rows.append({{"table": "price_rows", "line": idx, "reason": "unknown_package_id"}})
        if row.get("main_regime_v2_label") not in MAIN_REGIME_LABELS:
            bad_rows.append({{"table": "price_rows", "line": idx, "reason": "bad_main_regime_v2_label"}})
        if row.get("equivalence_type") not in ALLOWED_EQUIVALENCE_TYPES:
            bad_rows.append({{"table": "price_rows", "line": idx, "reason": "bad_equivalence_type"}})
        if not row.get("owner_approval_reference"):
            bad_rows.append({{"table": "price_rows", "line": idx, "reason": "missing_owner_approval_reference"}})
        if has_unsupported_token(row):
            bad_rows.append({{"table": "price_rows", "line": idx, "reason": "unsupported_proxy_or_generated_token"}})

    recency_labels = set()
    for idx, row in enumerate(tables["recency_rows"], start=2):
        recency_labels.add(row.get("main_regime_v2_label", ""))
        if row.get("package_id") != "source_panel_recency_extension":
            bad_rows.append({{"table": "recency_rows", "line": idx, "reason": "bad_package_id"}})
        if row.get("main_regime_v2_label") not in MAIN_REGIME_LABELS:
            bad_rows.append({{"table": "recency_rows", "line": idx, "reason": "bad_main_regime_v2_label"}})
        if row.get("timestamp", "") <= "2026-01-30":
            bad_rows.append({{"table": "recency_rows", "line": idx, "reason": "not_after_2026_01_30"}})
        if row.get("non_proxy_attestation", "").lower() != "true":
            bad_rows.append({{"table": "recency_rows", "line": idx, "reason": "missing_non_proxy_attestation"}})
        if has_unsupported_token(row):
            bad_rows.append({{"table": "recency_rows", "line": idx, "reason": "unsupported_proxy_or_generated_token"}})

    controls_by_group = {{
        row.get("matched_control_group_id", "")
        for row in tables["direct_controls"]
        if row.get("matched_control_group_id", "")
    }}
    direct_species = set()
    for idx, row in enumerate(tables["direct_positive_rows"], start=2):
        direct_species.add(row.get("species", ""))
        group = row.get("matched_control_group_id", "")
        if row.get("positive_label") != "positive":
            bad_rows.append({{"table": "direct_positive_rows", "line": idx, "reason": "bad_positive_label"}})
        if row.get("species") not in REQUIRED_DIRECT_SPECIES:
            bad_rows.append({{"table": "direct_positive_rows", "line": idx, "reason": "bad_or_untracked_species"}})
        if not group or group not in controls_by_group:
            bad_rows.append({{"table": "direct_positive_rows", "line": idx, "reason": "missing_matched_control_group"}})
        if has_unsupported_token(row):
            bad_rows.append({{"table": "direct_positive_rows", "line": idx, "reason": "unsupported_proxy_or_generated_token"}})
    for idx, row in enumerate(tables["direct_controls"], start=2):
        if row.get("normal_label") != "normal_control":
            bad_rows.append({{"table": "direct_controls", "line": idx, "reason": "bad_normal_label"}})

    missing_price_packages = sorted(set(REQUIRED_PRICE_PACKAGES) - price_packages)
    missing_labels = sorted(set(MAIN_REGIME_LABELS) - (labels_seen | recency_labels))
    missing_species = sorted(set(REQUIRED_DIRECT_SPECIES) - direct_species)
    if bad_rows or missing_price_packages or missing_labels or missing_species:
        return blocked(
            "rows_failed_guardrails",
            bad_rows=bad_rows[:50],
            missing_price_packages=missing_price_packages,
            missing_main_regime_v2_labels=missing_labels,
            missing_direct_species=missing_species,
        )

    print(json.dumps({{
        "status": "schema_ready_unscored",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "price_rows": len(tables["price_rows"]),
        "recency_rows": len(tables["recency_rows"]),
        "direct_positive_rows": len(tables["direct_positive_rows"]),
        "direct_control_rows": len(tables["direct_controls"]),
        "next": "rerun unchanged chronological, heldout-market/timeframe, BBN, CatBoost, and execution-tree gates",
    }}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def build_required_files() -> list[dict[str, Any]]:
    return [
        {
            "package": "price_root_equivalence",
            "file": "source_label_equivalence_rows.csv",
            "destination": str(INTAKE_ROOT / "price-root/source_label_equivalence_rows.csv"),
            "purpose": "source-owned or owner-approved MainRegimeV2 crosswalk rows for QQQ/NQ/NDX/futures, crypto, FX/rates/commodities",
            "required": True,
        },
        {
            "package": "price_root_equivalence",
            "file": "source_label_equivalence_provenance.json",
            "destination": str(INTAKE_ROOT / "price-root/source_label_equivalence_provenance.json"),
            "purpose": "owner, approval, export identity, hashes, source URLs, and non-proxy attestation for price-root equivalence",
            "required": True,
        },
        {
            "package": "source_panel_recency_extension",
            "file": "source_panel_recency_extension_rows.csv",
            "destination": str(INTAKE_ROOT / "recency/source_panel_recency_extension_rows.csv"),
            "purpose": "source-owned MainRegimeV2 rows strictly after 2026-01-30",
            "required": True,
        },
        {
            "package": "source_panel_recency_extension",
            "file": "source_panel_recency_extension_provenance.json",
            "destination": str(INTAKE_ROOT / "recency/source_panel_recency_extension_provenance.json"),
            "purpose": "source revision identity proving labels are not provider-only candles or generated future-return labels",
            "required": True,
        },
        {
            "package": "direct_manipulation_species",
            "file": "direct_manipulation_positive_rows.csv",
            "destination": str(INTAKE_ROOT / "direct-manipulation/direct_manipulation_positive_rows.csv"),
            "purpose": "direct Manipulation positives for missing species: spoofing/layering, quote stuffing, pinging, bear raid, painting tape, social/text pump-dump",
            "required": True,
        },
        {
            "package": "direct_manipulation_species",
            "file": "direct_manipulation_matched_controls.csv",
            "destination": str(INTAKE_ROOT / "direct-manipulation/direct_manipulation_matched_controls.csv"),
            "purpose": "matched normal controls for every positive event group",
            "required": True,
        },
        {
            "package": "direct_manipulation_species",
            "file": "direct_manipulation_provenance.json",
            "destination": str(INTAKE_ROOT / "direct-manipulation/direct_manipulation_provenance.json"),
            "purpose": "source owner, row provenance, event taxonomy, matched-negative policy, and hashes",
            "required": True,
        },
    ]


def build_schema_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for file_name, package, fields in [
        ("source_label_equivalence_rows.csv", "price_root_equivalence", PRICE_FIELDS),
        ("source_panel_recency_extension_rows.csv", "source_panel_recency_extension", RECENCY_FIELDS),
        ("direct_manipulation_positive_rows.csv", "direct_manipulation_species", DIRECT_POSITIVE_FIELDS),
        ("direct_manipulation_matched_controls.csv", "direct_manipulation_species", DIRECT_CONTROL_FIELDS),
    ]:
        for field in fields:
            rows.append(
                {
                    "package": package,
                    "file": file_name,
                    "field": field,
                    "required": True,
                }
            )
    return rows


def write_markdown(manifest: dict[str, Any]) -> None:
    required_files = manifest["required_files"]
    lines = [
        "# Board A External Intake Bundle v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This package converts the remaining strict Board A blockers into an executable external intake contract. It does not accept rows, does not move the Current Cursor, and does not make a trade-usable claim.",
        "",
        "## Decision",
        "",
        "`board_a_external_intake_bundle_v1=ready_for_rows_not_acquired`",
        "",
        "- Accepted rows added: `0`.",
        "- New confidence gate: `false`.",
        "- Full objective achieved: `false`; `update_goal=false`.",
        "- Current Cursor edited: `false`.",
        "- Raw provider rows committed: `false`.",
        "",
        "## Intake Root",
        "",
        f"`{INTAKE_ROOT}`",
        "",
        "## Required Files",
        "",
        "| Package | File | Destination | Purpose |",
        "|---|---|---|---|",
    ]
    for row in required_files:
        lines.append(
            f"| `{row['package']}` | `{row['file']}` | `{row['destination']}` | {row['purpose']} |"
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Price-root equivalence must cover `us_index_futures_equivalence`, `crypto_equivalence`, and `fx_rates_commodities_equivalence`.",
            "- MainRegimeV2 labels are limited to `Bull`, `Bear`, `Sideways`, and `Crisis`; every label needs its own qualifying condition and validation context.",
            "- Recency extension rows must be source-owned labels strictly after `2026-01-30`.",
            "- Direct Manipulation positives must have matched normal controls for every positive group.",
            "- Provider-only OHLCV, HMM/generated labels, future-return labels, and unapproved `^IXIC -> QQQ/NQ=F` mapping fail closed.",
            "- Schema readiness is not confidence acceptance; after a verifier pass, rerun unchanged chronological, heldout market/timeframe, BBN, CatBoost, and execution-tree gates.",
            "",
            "## Verifier",
            "",
            "```bash",
            f"python3 {repo_rel(OUT_VERIFIER)} --intake-root {INTAKE_ROOT}",
            "```",
            "",
            "Current missing-intake result:",
            "",
            "```json",
            json.dumps(manifest["verifier"]["missing_result"], indent=2, sort_keys=True),
            "```",
            "",
            "## Source Evidence Used",
            "",
            "- `20260511T182922-codex-source-label-equivalence-intake-verifier-v1`: existing source-label intake request is executable but missing rows.",
            "- `20260511T183328-codex-external-source-label-candidate-screen-v1`: external candidates remain blocked without owner-approved MainRegimeV2 equivalence.",
            "- `20260511T182601-codex-direct-manipulation-source-scan-v2`: no ready direct species source with positives plus matched negatives.",
            "- `20260511T183018-codex-hf-pumpdump-schema-audit-v1`: pump/dump rows lack explicit labels and matched controls.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    required_files = build_required_files()
    schema_rows = build_schema_rows()

    OUT_VERIFIER.write_text(verifier_source(), encoding="utf-8")
    write_csv(OUT_REQUIRED, required_files, ["package", "file", "destination", "purpose", "required"])
    write_csv(OUT_SCHEMA, schema_rows, ["package", "file", "field", "required"])

    proc = subprocess.run(
        ["python3", str(OUT_VERIFIER), "--intake-root", str(INTAKE_ROOT)],
        cwd=str(REPO),
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        missing_result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        missing_result = {
            "status": "blocked",
            "reason": "invalid_verifier_output",
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    OUT_MISSING.write_text(json.dumps(missing_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest = {
        "run_id": RUN_ID,
        "artifact_type": "board_a_external_intake_bundle_manifest_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "current_cursor_edited": False,
        "intake_root": str(INTAKE_ROOT),
        "required_files": required_files,
        "schema": {
            "path": repo_rel(OUT_SCHEMA),
            "price_fields": PRICE_FIELDS,
            "recency_fields": RECENCY_FIELDS,
            "direct_positive_fields": DIRECT_POSITIVE_FIELDS,
            "direct_control_fields": DIRECT_CONTROL_FIELDS,
        },
        "guardrails": {
            "main_regime_v2_labels": sorted(MAIN_REGIME_LABELS),
            "required_price_packages": sorted(REQUIRED_PRICE_PACKAGES),
            "required_direct_species": sorted(REQUIRED_DIRECT_SPECIES),
            "allowed_equivalence_types": sorted(ALLOWED_EQUIVALENCE_TYPES),
            "fail_closed_unsupported_tokens": list(UNSUPPORTED_TOKENS),
            "source_panel_recency_must_be_after": "2026-01-30",
            "schema_readiness_is_confidence_acceptance": False,
        },
        "acceptance_gates_after_intake": [
            "verifier_passes_without missing files, empty rows, missing columns, proxy/generated labels, or unmatched direct controls",
            "rerun unchanged chronological calibration for every regime label",
            "rerun heldout market, heldout timeframe, and market-context validation",
            "rerun Pre-Bayes/BBN consistency checks",
            "rerun CatBoost/path-ranking checks",
            "rerun execution-tree consumer check without relaxing thresholds",
        ],
        "source_evidence_refs": [
            "20260511T182922-codex-source-label-equivalence-intake-verifier-v1",
            "20260511T183328-codex-external-source-label-candidate-screen-v1",
            "20260511T182601-codex-direct-manipulation-source-scan-v2",
            "20260511T183018-codex-hf-pumpdump-schema-audit-v1",
        ],
        "verifier": {
            "path": repo_rel(OUT_VERIFIER),
            "command": f"python3 {repo_rel(OUT_VERIFIER)} --intake-root {INTAKE_ROOT}",
            "missing_result_path": repo_rel(OUT_MISSING),
            "missing_result": missing_result,
        },
        "decision": {
            "gate_result": "board_a_external_intake_bundle_v1=ready_for_rows_not_acquired",
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
    }
    OUT_JSON.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(manifest)

    assertions = [
        "PASS required_file_count=7" if len(required_files) == 7 else "FAIL required_file_count",
        "PASS missing_intake_blocks" if missing_result.get("status") == "blocked" else "FAIL missing_intake_blocks",
        "PASS missing_required_files" if missing_result.get("reason") == "missing_required_files" else "FAIL missing_required_files",
        "PASS accepted_rows_added=0" if manifest["decision"]["accepted_rows_added"] == 0 else "FAIL accepted_rows_added",
        "PASS full_objective=false" if not manifest["decision"]["full_objective_achieved"] else "FAIL full_objective",
        "PASS current_cursor_edited=false" if not manifest["current_cursor_edited"] else "FAIL current_cursor_edited",
    ]
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    if any(line.startswith("FAIL") for line in assertions):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
