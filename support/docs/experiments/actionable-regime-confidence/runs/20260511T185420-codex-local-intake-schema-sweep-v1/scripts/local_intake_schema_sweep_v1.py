#!/usr/bin/env python3
"""Header/schema-only sweep for local Board A intake candidates."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T185420-codex-local-intake-schema-sweep-v1"
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "local-intake-schema-sweep"
CHECK_DIR = RUN_ROOT / "checks"
TODO_PATH = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
CANDIDATES_CSV = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T185209-codex-board-a-local-acquisition-ledger-v1"
    / "local-acquisition-ledger/board_a_local_acquisition_candidates_v1.csv"
)

SCHEMAS = {
    "external_price_rows": [
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
    ],
    "external_recency_rows": [
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
    ],
    "direct_positive_rows": [
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
    ],
    "direct_controls": [
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
    ],
}


def normalize(values: list[str]) -> set[str]:
    return {value.strip().lower() for value in values if value and value.strip()}


def csv_header(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        sample = handle.read(8192)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(handle, dialect)
        return normalize(next(reader, []))


def json_keys(path: Path) -> set[str]:
    if path.stat().st_size > 2_000_000:
        return set()
    payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    keys: set[str] = set()
    if isinstance(payload, dict):
        keys.update(normalize(list(payload.keys())))
        for value in payload.values():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                keys.update(normalize(list(value[0].keys())))
            elif isinstance(value, dict):
                keys.update(normalize(list(value.keys())))
    elif isinstance(payload, list) and payload and isinstance(payload[0], dict):
        keys.update(normalize(list(payload[0].keys())))
    return keys


def parquet_or_feather_schema(path: Path) -> set[str]:
    try:
        import pyarrow.feather as feather  # type: ignore
        import pyarrow.parquet as pq  # type: ignore
    except Exception:
        return set()
    if path.suffix.lower() == ".parquet":
        return normalize(pq.read_schema(path).names)
    if path.suffix.lower() == ".feather":
        return normalize(feather.read_table(path, memory_map=True).schema.names)
    return set()


def file_keys(path: Path) -> tuple[set[str], str]:
    suffix = path.suffix.lower()
    try:
        if suffix == ".csv":
            return csv_header(path), "csv_header"
        if suffix == ".json":
            return json_keys(path), "json_keys"
        if suffix in {".parquet", ".feather"}:
            return parquet_or_feather_schema(path), "arrow_schema"
        return set(), "unsupported_suffix"
    except Exception as exc:  # noqa: BLE001
        return set(), f"parse_error:{type(exc).__name__}"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    candidates = list(csv.DictReader(CANDIDATES_CSV.open(encoding="utf-8")))

    rows = []
    exact_matches = []
    partial_matches = []
    parsed_count = 0
    for candidate in candidates:
        path = Path(candidate["path"])
        keys, parser = file_keys(path)
        if keys:
            parsed_count += 1
        best = {
            "schema": "",
            "present": 0,
            "missing": 0,
            "missing_fields": "",
            "present_fields": "",
            "exact": False,
            "strong_partial": False,
        }
        for schema_name, fields in SCHEMAS.items():
            required = normalize(fields)
            present_fields = sorted(required & keys)
            missing_fields = sorted(required - keys)
            score = len(present_fields)
            strong_partial = score >= max(4, len(required) // 2)
            exact = not missing_fields and bool(required)
            if score > int(best["present"]):
                best = {
                    "schema": schema_name,
                    "present": score,
                    "missing": len(missing_fields),
                    "missing_fields": ";".join(missing_fields[:20]),
                    "present_fields": ";".join(present_fields[:20]),
                    "exact": exact,
                    "strong_partial": strong_partial,
                }
        row = {
            "path": str(path),
            "classification": candidate.get("classification", ""),
            "suffix": path.suffix.lower(),
            "parser": parser,
            "key_count": len(keys),
            "best_schema": best["schema"],
            "present_required_fields": best["present"],
            "missing_required_fields": best["missing"],
            "present_fields": best["present_fields"],
            "missing_fields": best["missing_fields"],
            "exact_schema_match": best["exact"],
            "strong_partial_schema_match": best["strong_partial"],
        }
        rows.append(row)
        if best["exact"]:
            exact_matches.append(row)
        if best["strong_partial"]:
            partial_matches.append(row)

    out_csv = OUT_DIR / "local_intake_schema_sweep_v1_rows.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    partial_csv = OUT_DIR / "local_intake_schema_sweep_v1_partial_matches.csv"
    with partial_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(partial_matches)

    decision = {
        "gate_result": "local_intake_schema_sweep_v1=no_exact_required_schema_match",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }
    payload = {
        "artifact_type": "local_intake_schema_sweep_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": RUN_ID,
        "todo_hash_before_append": __import__("hashlib").sha256(TODO_PATH.read_bytes()).hexdigest(),
        "candidate_files": len(candidates),
        "parsed_files": parsed_count,
        "exact_schema_matches": len(exact_matches),
        "strong_partial_schema_matches": len(partial_matches),
        "schemas_checked": sorted(SCHEMAS),
        "decision": decision,
    }
    (OUT_DIR / "local_intake_schema_sweep_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Local Intake Schema Sweep v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "Header/schema-only sweep over local candidate files from the Board A local acquisition ledger. Raw rows were not promoted and Current Cursor was not edited.",
        "",
        "## Decision",
        "",
        f"`{decision['gate_result']}`",
        "",
        f"- Candidate files checked: `{len(candidates)}`.",
        f"- Files with readable headers/keys/schema: `{parsed_count}`.",
        f"- Exact required schema matches: `{len(exact_matches)}`.",
        f"- Strong partial schema matches: `{len(partial_matches)}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Schemas Checked",
        "",
    ]
    for name, fields in SCHEMAS.items():
        report.append(f"- `{name}`: `{len(fields)}` required fields.")
    report.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/local-intake-schema-sweep/local_intake_schema_sweep_v1.json`",
            f"- Rows CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/local-intake-schema-sweep/local_intake_schema_sweep_v1_rows.csv`",
            f"- Partial matches CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/local-intake-schema-sweep/local_intake_schema_sweep_v1_partial_matches.csv`",
            f"- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/local_intake_schema_sweep_v1_assertions.out`",
            "",
        ]
    )
    (OUT_DIR / "local_intake_schema_sweep_v1.md").write_text("\n".join(report), encoding="utf-8")

    assertions = [
        f"PASS candidate_files={len(candidates)}",
        f"PASS parsed_files={parsed_count}",
        f"PASS exact_schema_matches={len(exact_matches)}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective=false",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "local_intake_schema_sweep_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
