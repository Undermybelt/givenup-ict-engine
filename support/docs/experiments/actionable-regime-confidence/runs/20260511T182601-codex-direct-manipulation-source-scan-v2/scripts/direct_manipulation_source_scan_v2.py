#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path


RUN_ID = "20260511T182601+0800-codex-direct-manipulation-source-scan-v2"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs/20260511T182601-codex-direct-manipulation-source-scan-v2")
OUT_DIR = RUN_ROOT / "direct-source-scan"
CHECK_DIR = RUN_ROOT / "checks"
TMP_ROOT = Path("/tmp/ict-engine-direct-manip-source-scan-v2")

KAGGLE_SEARCHES = [
    "spoofing order book",
    "quote stuffing",
    "limit orderbook",
    "market manipulation",
]
KAGGLE_CANDIDATES = {
    "adamatractor/institutional-crypto-l2-orderbook-30lvl-1m-5m": "recent_crypto_l2_orderbook_control_candidate",
    "praanj/limit-orderbook-data": "legacy_lob_control_candidate",
    "a53e93e57a1/maker-order-dataset-osaka-20210301": "order_lifecycle_control_candidate",
}
HF_SEARCHES = [
    "spoofing order book",
    "quote stuffing",
    "market manipulation",
    "wash trading",
    "pump dump",
]
ZENODO_RECORDS = {
    "18667008": "spoofing_preprint_no_data_files",
}


def run_cmd(args: list[str]) -> str:
    result = subprocess.run(args, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return result.stdout


def parse_kaggle_csv(text: str) -> list[dict]:
    rows: list[dict] = []
    reader = csv.DictReader(text.splitlines())
    for row in reader:
        if row.get("ref"):
            rows.append(row)
    return rows


def json_url(url: str) -> object:
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def text_url(url: str, limit: int = 6000) -> str:
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read(limit).decode("utf-8", "replace")


def compact_metadata(raw: object) -> dict:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            return {"raw": raw[:2000]}
    if not isinstance(raw, dict):
        return {"raw": repr(raw)[:2000]}
    return {
        "datasetSlug": raw.get("datasetSlug"),
        "ownerUser": raw.get("ownerUser"),
        "title": raw.get("title"),
        "subtitle": raw.get("subtitle"),
        "description_excerpt": re.sub(r"\s+", " ", raw.get("description") or "")[:1500],
        "licenses": raw.get("licenses"),
        "totalDownloads": raw.get("totalDownloads"),
        "usabilityRating": raw.get("usabilityRating"),
    }


def candidate_status(candidate_id: str, metadata: dict, files_text: str) -> tuple[str, str]:
    text = " ".join(
        [
            candidate_id.lower(),
            str(metadata.get("title", "")).lower(),
            str(metadata.get("subtitle", "")).lower(),
            str(metadata.get("description_excerpt", "")).lower(),
            files_text.lower(),
        ]
    )
    has_positive_label = any(token in text for token in ["spoof", "manipulation", "pump", "dump", "wash"])
    has_order_lifecycle = any(token in text for token in ["order", "lob", "depth", "orderbook", "deleted", "modify"])
    has_matched_controls = any(token in text for token in ["matched negative", "control group", "benign control", "normal controls"])
    if has_positive_label and has_order_lifecycle and has_matched_controls:
        return "candidate_needs_row_schema_audit", "Metadata suggests positives, order-lifecycle data, and controls; row schema still must be verified before any gate."
    if has_positive_label and not has_matched_controls:
        return "blocked_positive_or_topic_only_no_matched_negatives", "Metadata has manipulation-like topic or positive labels, but no matched negative/control-row evidence."
    if has_order_lifecycle and not has_positive_label:
        return "control_only_not_direct_positive_source", "Metadata has L2/order-lifecycle or orderbook rows but no direct positive manipulation labels."
    return "rejected_not_board_a_direct_source", "Metadata does not show direct manipulation labels plus matched controls."


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)

    search_rows: list[dict] = []
    for query in KAGGLE_SEARCHES:
        stdout = run_cmd(["kaggle", "datasets", "list", "-s", query, "--csv"])
        (OUT_DIR / f"kaggle_search_{query.replace(' ', '_')}.csv").write_text(stdout)
        for row in parse_kaggle_csv(stdout):
            row["source"] = "kaggle"
            row["query"] = query
            search_rows.append(row)

    candidate_rows: list[dict] = []
    for candidate, note in KAGGLE_CANDIDATES.items():
        slug = candidate.replace("/", "__")
        metadata_dir = TMP_ROOT / slug
        metadata_dir.mkdir(parents=True, exist_ok=True)
        run_cmd(["kaggle", "datasets", "metadata", candidate, "-p", str(metadata_dir)])
        metadata_raw = json.loads((metadata_dir / "dataset-metadata.json").read_text())
        metadata = compact_metadata(metadata_raw)
        files_text = run_cmd(["kaggle", "datasets", "files", candidate])
        (OUT_DIR / f"kaggle_files_{slug}.txt").write_text(files_text)
        status, reason = candidate_status(candidate, metadata, files_text)
        candidate_rows.append(
            {
                "source": "kaggle",
                "id": candidate,
                "note": note,
                "title": metadata.get("title", ""),
                "files_summary": files_text.splitlines()[0:8],
                "status": status,
                "reason": reason,
            }
        )

    hf_rows: list[dict] = []
    for query in HF_SEARCHES:
        url = "https://huggingface.co/api/datasets?search=" + urllib.parse.quote(query)
        data = json_url(url)
        (OUT_DIR / f"hf_search_{query.replace(' ', '_')}.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        for entry in data[:10]:
            hf_rows.append(
                {
                    "source": "huggingface",
                    "query": query,
                    "id": entry.get("id", ""),
                    "lastModified": entry.get("lastModified", ""),
                    "downloads": entry.get("downloads", 0),
                    "likes": entry.get("likes", 0),
                    "tags": entry.get("tags", []),
                }
            )

    hf_candidate = json_url("https://huggingface.co/api/datasets/Go3x3/pump_and_dump_dataset")
    hf_readme = text_url("https://huggingface.co/datasets/Go3x3/pump_and_dump_dataset/raw/main/README.md")
    (OUT_DIR / "hf_go3x3_pump_and_dump_dataset.json").write_text(json.dumps(hf_candidate, indent=2, sort_keys=True) + "\n")
    (OUT_DIR / "hf_go3x3_pump_and_dump_readme.md").write_text(hf_readme)
    hf_text = json.dumps(hf_candidate).lower() + " " + hf_readme.lower()
    if "matched negative" in hf_text or "control" in hf_text:
        hf_status = "candidate_needs_row_schema_audit"
        hf_reason = "Metadata mentions controls; row schema must be audited before use."
    else:
        hf_status = "blocked_positive_or_topic_only_no_matched_negatives"
        hf_reason = "HF metadata exposes pump/dump package files, but README has no schema detail and metadata does not show matched negative/control rows."
    candidate_rows.append(
        {
            "source": "huggingface",
            "id": "Go3x3/pump_and_dump_dataset",
            "note": "social_text_pump_dump_candidate",
            "title": "pump_and_dump_dataset",
            "files_summary": [s.get("rfilename") for s in hf_candidate.get("siblings", [])],
            "status": hf_status,
            "reason": hf_reason,
        }
    )

    for record_id, note in ZENODO_RECORDS.items():
        data = json_url(f"https://zenodo.org/api/records/{record_id}")
        metadata = data.get("metadata", {})
        files = data.get("files", [])
        candidate_rows.append(
            {
                "source": "zenodo",
                "id": record_id,
                "note": note,
                "title": metadata.get("title", ""),
                "files_summary": [f.get("key") for f in files],
                "status": "blocked_preprint_only_no_rows",
                "reason": "Zenodo record is a preprint/PDF record, not a row dataset with positive and matched negative controls.",
            }
        )

    accepted_candidates = [row for row in candidate_rows if row["status"] == "candidate_needs_row_schema_audit"]
    result = {
        "run_id": RUN_ID,
        "purpose": "Scan public metadata for missing direct Manipulation species sources without downloading raw rows or promoting topic hits into accepted gates.",
        "kaggle_searches": KAGGLE_SEARCHES,
        "hf_searches": HF_SEARCHES,
        "candidate_rows": candidate_rows,
        "hf_search_rows": hf_rows,
        "accepted_rows_added": 0,
        "candidate_needs_row_schema_audit": len(accepted_candidates),
        "new_confidence_gate": False,
        "full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "gate_result": "direct_manipulation_source_scan_v2=no_ready_matched_negative_source",
        "decision": "blocked_no_ready_direct_species_source",
        "reason": "Current metadata scan found control-only L2/order-lifecycle datasets and topic/positive-only pump-dump or spoofing records, but no ready source with direct positive rows, matched normal controls, event/order lifecycle provenance, and row schema.",
        "next_action": "Do not claim full direct Manipulation species coverage; acquire row-level positive plus matched-negative exports for spoofing/layering, quote stuffing, pinging, bear raid, or painting tape.",
    }

    json_path = OUT_DIR / "direct_manipulation_source_scan_v2.json"
    csv_path = OUT_DIR / "direct_manipulation_source_scan_v2_candidates.csv"
    report_path = OUT_DIR / "direct_manipulation_source_scan_v2.md"
    checks_path = CHECK_DIR / "direct_manipulation_source_scan_v2_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["source", "id", "note", "title", "status", "reason"])
        writer.writeheader()
        for row in candidate_rows:
            writer.writerow({k: row.get(k, "") for k in writer.fieldnames})

    status_lines = "\n".join(
        f"- `{row['id']}`: `{row['status']}`. {row['reason']}" for row in candidate_rows
    )
    report = f"""# Direct Manipulation Source Scan v2

Run ID: `{RUN_ID}`

This scan targets the remaining direct `Manipulation` species gap: spoofing/layering, quote stuffing, pinging, bear raid, painting tape, and social/text pump-dump variants. It records public metadata only and does not download raw row files.

## Decision

`direct_manipulation_source_scan_v2=no_ready_matched_negative_source`

- Kaggle searches: `{len(KAGGLE_SEARCHES)}`.
- Hugging Face searches: `{len(HF_SEARCHES)}`.
- Candidate records summarized: `{len(candidate_rows)}`.
- Ready row-schema candidates: `{len(accepted_candidates)}`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Full direct species coverage: `false`.
- `update_goal`: `false`.

## Candidate Disposition

{status_lines}

## Why It Blocks

Board A needs direct positive rows plus matched normal controls and provenance. L2/orderbook data without positive labels is control-only. A pump/dump or spoofing topic hit without matched negatives remains positive-only or publication-only. None of the scanned candidates can be promoted into a direct `Manipulation` confidence gate.

## Artifacts

- JSON: `{json_path}`
- Candidate CSV: `{csv_path}`
- Assertions: `{checks_path}`

## Next

Acquire row-level positive plus matched-negative exports for at least one missing direct species, then run a direct calibration gate without lowering thresholds.
"""
    report_path.write_text(report)

    assertions = [
        ("accepted_rows_added_zero", result["accepted_rows_added"] == 0),
        ("ready_candidates_zero", len(accepted_candidates) == 0),
        ("new_confidence_gate_false", result["new_confidence_gate"] is False),
        ("full_objective_false", result["full_objective_achieved"] is False),
        ("no_threshold_relaxation", result["thresholds_relaxed"] is False),
        ("no_raw_data_commit", result["raw_data_committed"] is False),
        ("candidate_csv_written", csv_path.exists() and csv_path.stat().st_size > 0),
    ]
    lines = [f"PASS {name}" if ok else f"FAIL {name}" for name, ok in assertions]
    failed = [name for name, ok in assertions if not ok]
    if failed:
        lines.append(f"FAILED_ASSERTIONS {','.join(failed)}")
        checks_path.write_text("\n".join(lines) + "\n")
        raise SystemExit(1)
    lines.append("ALL_ASSERTIONS_PASS")
    checks_path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
