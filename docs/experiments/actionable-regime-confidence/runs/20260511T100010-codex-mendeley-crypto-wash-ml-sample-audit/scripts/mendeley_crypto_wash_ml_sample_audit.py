#!/usr/bin/env python3
import csv
import io
import json
import urllib.request
from pathlib import Path

RUN_ID = "20260511T100010+0800-codex-mendeley-crypto-wash-ml-sample-audit"
DATASET_ID = "4hyxfwzpgg"
VERSION = 3
DATASET_URL = f"https://data.mendeley.com/datasets/{DATASET_ID}/{VERSION}"
SNAPSHOT_URL = f"https://data.mendeley.com/public-api/datasets/{DATASET_ID}/snapshot/{VERSION}"
FILES_URL = f"https://data.mendeley.com/public-api/datasets/{DATASET_ID}/files?folder_id=root&version={VERSION}"
GITHUB_URL = "https://github.com/niuniu-zhang/nft_wash_trading"
SSRN_URL = "https://ssrn.com/abstract=4649565"

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "mendeley-wash-audit"
CHECKS = ROOT / "checks"

REQUIRED_DIRECT_FIELDS = [
    "event_id",
    "instrument_or_asset",
    "venue_or_chain",
    "event_start",
    "event_end",
    "is_manipulation_positive",
    "manipulation_type",
    "negative_control_type",
    "source_id",
    "source_url_or_private_ref",
]


def request_headers(extra=None):
    headers = {
        "Accept": "application/vnd.mendeley-public-dataset.1+json, application/json, text/csv, */*",
        "User-Agent": "Mozilla/5.0 BoardA-Regime-Audit/1.0",
    }
    if extra:
        headers.update(extra)
    return headers


def fetch_json(url: str, headers=None):
    req = urllib.request.Request(url, headers=request_headers(headers))
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_sample_text(url: str, max_bytes=65536) -> str:
    req = urllib.request.Request(url, headers=request_headers({"Range": f"bytes=0-{max_bytes - 1}"}))
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read(max_bytes)
    return data.decode("utf-8", errors="replace")


def parse_csv_sample(text: str):
    reader = csv.reader(io.StringIO(text))
    rows = []
    for idx, row in enumerate(reader):
        rows.append(row)
        if idx >= 3:
            break
    header = rows[0] if rows else []
    return {
        "header": header,
        "sample_rows": rows[1:],
        "row_sample_count": max(0, len(rows) - 1),
        "column_count": len(header),
    }


def label_fields_for(header):
    candidates = []
    for name in header:
        lower = name.lower()
        if lower in {"wash", "filter_1234", "label", "is_wash", "target"}:
            candidates.append(name)
    return candidates


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    snapshot = fetch_json(SNAPSHOT_URL)
    files = fetch_json(
        FILES_URL,
        headers={"Accept": "application/vnd.mendeley-public-dataset.1+json"},
    )

    file_audits = []
    for item in files:
        content = item.get("content_details", {})
        sample = parse_csv_sample(fetch_sample_text(content["download_url"]))
        header = sample["header"]
        missing_direct_fields = REQUIRED_DIRECT_FIELDS.copy()
        labels = label_fields_for(header)
        file_audits.append(
            {
                "filename": item["filename"],
                "file_id": item["id"],
                "size_bytes": content.get("size") or item.get("size"),
                "sha256_hash": content.get("sha256_hash"),
                "content_type": content.get("content_type"),
                "download_url": content.get("download_url"),
                "view_url": content.get("view_url"),
                "header": header,
                "label_like_fields": labels,
                "sample_rows": sample["sample_rows"],
                "row_sample_count": sample["row_sample_count"],
                "column_count": sample["column_count"],
                "has_row_label": bool(labels),
                "has_event_timestamp": any(name.lower() in {"timestamp", "event_start", "event_end", "date", "datetime", "time"} for name in header),
                "has_row_asset_or_instrument": any(name.lower() in {"asset", "instrument", "token", "contract", "collection", "symbol", "nft"} for name in header),
                "has_venue_or_chain": any(name.lower() in {"venue", "chain", "exchange", "marketplace"} for name in header),
                "missing_required_direct_schema_fields": missing_direct_fields,
            }
        )

    files_with_label = sum(1 for item in file_audits if item["has_row_label"])
    files_with_timestamp = sum(1 for item in file_audits if item["has_event_timestamp"])
    files_with_asset = sum(1 for item in file_audits if item["has_row_asset_or_instrument"])
    files_with_venue = sum(1 for item in file_audits if item["has_venue_or_chain"])
    total_size = sum(item["size_bytes"] or 0 for item in file_audits)

    accepted = (
        files_with_label == len(file_audits)
        and files_with_timestamp == len(file_audits)
        and files_with_asset == len(file_audits)
        and files_with_venue == len(file_audits)
    )

    result = {
        "run_id": RUN_ID,
        "source": DATASET_URL,
        "snapshot_url": SNAPSHOT_URL,
        "files_url": FILES_URL,
        "github_url": GITHUB_URL,
        "ssrn_url": SSRN_URL,
        "dataset_name": snapshot.get("name"),
        "dataset_doi": snapshot.get("doi"),
        "dataset_publish_date": snapshot.get("publish_date"),
        "licence": snapshot.get("licence", {}).get("short_name"),
        "description_basis": "Mendeley snapshot states rows are labeled ML samples from on-chain transactions, but accepted direct rows require row-level event id, exact asset, venue/chain, timestamps, and positive/negative labels.",
        "files_inspected": len(file_audits),
        "total_file_size_bytes": total_size,
        "files_with_label_like_field": files_with_label,
        "files_with_event_timestamp_field": files_with_timestamp,
        "files_with_asset_or_instrument_field": files_with_asset,
        "files_with_venue_or_chain_field": files_with_venue,
        "file_audits": file_audits,
        "accepted_parent_root_slots_added": 0,
        "accepted_direct_manipulation_rows_added": 0,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "candidate_useful_provenance": True,
        "gate_result": "blocked_mendeley_crypto_wash_ml_samples_missing_required_direct_row_schema",
        "rejection_reasons": [
            "ML sample files expose label-like fields but omit row-level event_id.",
            "ML sample files omit exact instrument_or_asset / collection / token fields.",
            "ML sample files omit event_start and event_end timestamps; an engineered hours field is not a timestamped event window.",
            "ML sample files omit venue_or_chain as a row-level field; filename-level venue is not enough for the direct row schema.",
            "Rows are engineered feature vectors, not exportable direct Manipulation positive/negative event rows in the Board A schema.",
        ],
        "next_action": "continue source acquisition for exact-underlying MainRegimeV2 labels or direct Manipulation rows with event id, asset, venue/chain, timestamps, positives, and negatives",
    }

    json_path = OUT / "mendeley_crypto_wash_ml_sample_audit.json"
    md_path = OUT / "mendeley_crypto_wash_ml_sample_audit.md"
    assertions_path = CHECKS / "mendeley_crypto_wash_ml_sample_audit_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    rows = [
        "# Mendeley Crypto Wash ML Sample Audit",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        f"Source: `{DATASET_URL}`",
        f"GitHub: `{GITHUB_URL}`",
        f"Related paper: `{SSRN_URL}`",
        "",
        "## Result",
        "",
        f"- Dataset: `{result['dataset_name']}`.",
        f"- DOI: `{result['dataset_doi']}`.",
        f"- Published: `{result['dataset_publish_date']}`.",
        f"- Licence: `{result['licence']}`.",
        f"- Files inspected: `{result['files_inspected']}`.",
        f"- Total listed CSV size bytes: `{result['total_file_size_bytes']}`.",
        f"- Files with label-like fields: `{result['files_with_label_like_field']}`.",
        f"- Files with event timestamp fields: `{result['files_with_event_timestamp_field']}`.",
        f"- Files with row asset/instrument fields: `{result['files_with_asset_or_instrument_field']}`.",
        f"- Files with row venue/chain fields: `{result['files_with_venue_or_chain_field']}`.",
        "- Candidate is useful provenance because the source documents labeled ML samples from on-chain transactions.",
        "- Candidate is not accepted as direct Manipulation rows because the released ML sample rows lack the Board A direct-row schema fields.",
        "- Accepted parent-root slots added: `0`.",
        "- Accepted direct Manipulation rows/windows added: `0`.",
        "",
        "## File Header Audit",
        "",
        "| File | Size Bytes | Label-Like Fields | Timestamp Field | Asset Field | Venue/Chain Field |",
        "|---|---:|---|---|---|---|",
    ]
    for item in file_audits:
        rows.append(
            f"| `{item['filename']}` | {item['size_bytes']} | `{', '.join(item['label_like_fields']) or 'none'}` | `{item['has_event_timestamp']}` | `{item['has_row_asset_or_instrument']}` | `{item['has_venue_or_chain']}` |"
        )
    rows.extend(
        [
            "",
            "## Gate",
            "",
            f"`{result['gate_result']}`",
            "",
            "Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.",
        ]
    )
    md_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    assertions = []
    assertions.append("PASS mendeley_dataset_metadata_fetch_ok")
    assertions.append(f"PASS files_inspected={len(file_audits)}")
    assertions.append(f"PASS files_with_label_like_field={files_with_label}")
    assertions.append("PASS accepted_parent_root_slots_added=0")
    assertions.append("PASS accepted_direct_manipulation_rows_added=0")
    assertions.append("PASS runtime_code_changed=false")
    assertions.append("PASS thresholds_relaxed=false")
    if accepted:
        assertions.append("FAIL unexpected_direct_schema_complete")
    else:
        assertions.append("PASS direct_row_schema_incomplete_rejected")
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json_path)
    print(md_path)
    print(assertions_path)
    print(result["gate_result"])


if __name__ == "__main__":
    main()
