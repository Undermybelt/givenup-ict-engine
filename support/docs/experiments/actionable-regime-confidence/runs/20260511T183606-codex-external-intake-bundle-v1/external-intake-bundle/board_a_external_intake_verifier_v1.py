#!/usr/bin/env python3
"""Fail-closed verifier for the Board A external intake bundle."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


MAIN_REGIME_LABELS = ['Bear', 'Bull', 'Crisis', 'Sideways']
REQUIRED_PRICE_PACKAGES = ['crypto_equivalence', 'fx_rates_commodities_equivalence', 'us_index_futures_equivalence']
REQUIRED_DIRECT_SPECIES = ['bear_raid', 'painting_tape', 'pinging', 'quote_stuffing', 'social_text_pump_dump', 'spoofing_layering']
ALLOWED_EQUIVALENCE_TYPES = ['owner_approved_crosswalk', 'source_owned_label']
UNSUPPORTED_TOKENS = ('provider_ohlcv', 'ohlcv_proxy', 'hmm', 'generated_label', 'future_return', 'unapproved_ixic')

REQUIRED_FILES = {
    "price_rows": "price-root/source_label_equivalence_rows.csv",
    "price_provenance": "price-root/source_label_equivalence_provenance.json",
    "recency_rows": "recency/source_panel_recency_extension_rows.csv",
    "recency_provenance": "recency/source_panel_recency_extension_provenance.json",
    "direct_positive_rows": "direct-manipulation/direct_manipulation_positive_rows.csv",
    "direct_controls": "direct-manipulation/direct_manipulation_matched_controls.csv",
    "direct_provenance": "direct-manipulation/direct_manipulation_provenance.json",
}
FIELDS = {
    "price_rows": ['package_id', 'market_family', 'root_symbol', 'source_symbol', 'source_timeframe', 'source_start', 'source_end', 'source_label_column', 'main_regime_v2_label', 'qualifying_condition_id', 'validation_instrument', 'validation_period', 'validation_market_context', 'equivalence_type', 'owner_approval_reference', 'source_row_id', 'provenance_hash'],
    "recency_rows": ['package_id', 'source_dataset', 'market_family', 'symbol', 'timeframe', 'timestamp', 'main_regime_v2_label', 'qualifying_condition_id', 'validation_instrument', 'validation_period', 'validation_market_context', 'source_revision_date', 'source_row_id', 'provenance_hash', 'non_proxy_attestation'],
    "direct_positive_rows": ['event_id', 'species', 'market_family', 'symbol', 'timeframe', 'event_start', 'event_end', 'positive_label', 'source_owner', 'source_dataset', 'source_row_id', 'evidence_type', 'matched_control_group_id', 'provenance_hash', 'source_url_or_record'],
    "direct_controls": ['matched_control_group_id', 'control_row_id', 'control_symbol', 'control_start', 'control_end', 'matching_dimensions', 'normal_label', 'source_owner', 'source_dataset', 'source_row_id', 'provenance_hash'],
}
PROVENANCE_COMMON_KEYS = {
    "source_owner",
    "pulled_at",
    "export_id",
    "source_urls",
    "input_file_hashes",
    "attestations",
}


def blocked(reason: str, **extra: object) -> int:
    payload = {"status": "blocked", "reason": reason}
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
    paths = {name: root / rel for name, rel in REQUIRED_FILES.items()}
    missing_files = [str(path) for path in paths.values() if not path.exists()]
    if missing_files:
        return blocked("missing_required_files", missing_files=missing_files)

    try:
        provenances = {
            "price_provenance": load_json(paths["price_provenance"]),
            "recency_provenance": load_json(paths["recency_provenance"]),
            "direct_provenance": load_json(paths["direct_provenance"]),
        }
    except Exception as exc:  # noqa: BLE001
        return blocked("provenance_json_unreadable", error=type(exc).__name__)

    missing_provenance_keys = {
        name: sorted(PROVENANCE_COMMON_KEYS - set(payload.keys()))
        for name, payload in provenances.items()
    }
    missing_provenance_keys = {
        name: missing for name, missing in missing_provenance_keys.items() if missing
    }
    if missing_provenance_keys:
        return blocked("missing_provenance_keys", missing_provenance_keys=missing_provenance_keys)
    attestations = {
        name: payload.get("attestations", {})
        for name, payload in provenances.items()
    }
    if not attestations["price_provenance"].get("owner_approved_main_regime_v2_equivalence"):
        return blocked("missing_price_equivalence_attestation")
    if not attestations["recency_provenance"].get("post_2026_01_30_source_revision"):
        return blocked("missing_recency_revision_attestation")
    if not attestations["direct_provenance"].get("matched_negative_policy"):
        return blocked("missing_direct_matched_negative_policy")

    tables: dict[str, list[dict[str, str]]] = {}
    missing_fields: dict[str, list[str]] = {}
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
            bad_rows.append({"table": "price_rows", "line": idx, "reason": "unknown_package_id"})
        if row.get("main_regime_v2_label") not in MAIN_REGIME_LABELS:
            bad_rows.append({"table": "price_rows", "line": idx, "reason": "bad_main_regime_v2_label"})
        if row.get("equivalence_type") not in ALLOWED_EQUIVALENCE_TYPES:
            bad_rows.append({"table": "price_rows", "line": idx, "reason": "bad_equivalence_type"})
        if not row.get("owner_approval_reference"):
            bad_rows.append({"table": "price_rows", "line": idx, "reason": "missing_owner_approval_reference"})
        if has_unsupported_token(row):
            bad_rows.append({"table": "price_rows", "line": idx, "reason": "unsupported_proxy_or_generated_token"})

    recency_labels = set()
    for idx, row in enumerate(tables["recency_rows"], start=2):
        recency_labels.add(row.get("main_regime_v2_label", ""))
        if row.get("package_id") != "source_panel_recency_extension":
            bad_rows.append({"table": "recency_rows", "line": idx, "reason": "bad_package_id"})
        if row.get("main_regime_v2_label") not in MAIN_REGIME_LABELS:
            bad_rows.append({"table": "recency_rows", "line": idx, "reason": "bad_main_regime_v2_label"})
        if row.get("timestamp", "") <= "2026-01-30":
            bad_rows.append({"table": "recency_rows", "line": idx, "reason": "not_after_2026_01_30"})
        if row.get("non_proxy_attestation", "").lower() != "true":
            bad_rows.append({"table": "recency_rows", "line": idx, "reason": "missing_non_proxy_attestation"})
        if has_unsupported_token(row):
            bad_rows.append({"table": "recency_rows", "line": idx, "reason": "unsupported_proxy_or_generated_token"})

    controls_by_group = {
        row.get("matched_control_group_id", "")
        for row in tables["direct_controls"]
        if row.get("matched_control_group_id", "")
    }
    direct_species = set()
    for idx, row in enumerate(tables["direct_positive_rows"], start=2):
        direct_species.add(row.get("species", ""))
        group = row.get("matched_control_group_id", "")
        if row.get("positive_label") != "positive":
            bad_rows.append({"table": "direct_positive_rows", "line": idx, "reason": "bad_positive_label"})
        if row.get("species") not in REQUIRED_DIRECT_SPECIES:
            bad_rows.append({"table": "direct_positive_rows", "line": idx, "reason": "bad_or_untracked_species"})
        if not group or group not in controls_by_group:
            bad_rows.append({"table": "direct_positive_rows", "line": idx, "reason": "missing_matched_control_group"})
        if has_unsupported_token(row):
            bad_rows.append({"table": "direct_positive_rows", "line": idx, "reason": "unsupported_proxy_or_generated_token"})
    for idx, row in enumerate(tables["direct_controls"], start=2):
        if row.get("normal_label") != "normal_control":
            bad_rows.append({"table": "direct_controls", "line": idx, "reason": "bad_normal_label"})

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

    print(json.dumps({
        "status": "schema_ready_unscored",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "price_rows": len(tables["price_rows"]),
        "recency_rows": len(tables["recency_rows"]),
        "direct_positive_rows": len(tables["direct_positive_rows"]),
        "direct_control_rows": len(tables["direct_controls"]),
        "next": "rerun unchanged chronological, heldout-market/timeframe, BBN, CatBoost, and execution-tree gates",
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
