from __future__ import annotations

import csv
import json
import urllib.request
from datetime import datetime
from io import TextIOWrapper
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T021058-codex-wash-trading-public-api-raw-access"
)
OUT_DIR = RUN_ROOT / "raw-access"
CHECKS_DIR = RUN_ROOT / "checks"
LOOP_ID = "20260511T021058+0800-codex-wash-trading-public-api-raw-access"
DATASET_URL = "https://data.mendeley.com/public-api/datasets/4hyxfwzpgg"


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "curl/8.7.1",
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def sample_csv(download_url: str, max_rows: int = 5) -> dict[str, Any]:
    request = urllib.request.Request(
        download_url,
        headers={
            "Accept": "text/csv",
            "User-Agent": "curl/8.7.1",
        },
    )
    rows: list[dict[str, str]] = []
    with urllib.request.urlopen(request, timeout=45) as response:
        reader = csv.DictReader(TextIOWrapper(response, encoding="utf-8", newline=""))
        for row in reader:
            rows.append(dict(row))
            if len(rows) >= max_rows:
                break
        header = reader.fieldnames or []
    return {
        "header": header,
        "sample_rows": rows,
        "label_like_columns": [
            column
            for column in header
            if "label" in column.lower()
            or column.lower().startswith("is_")
            or column.lower() in {"target", "wash", "filter_1234"}
        ],
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    dataset = fetch_json(DATASET_URL)
    files: list[dict[str, Any]] = []
    for file in dataset.get("files", []):
        details = file["content_details"]
        sample = sample_csv(details["download_url"])
        files.append(
            {
                "filename": file["filename"],
                "file_id": file["id"],
                "size": file["size"],
                "content_type": details.get("content_type"),
                "sha256_hash": details.get("sha256_hash"),
                "download_url_verified": bool(details.get("download_url")),
                "view_url_verified": bool(details.get("view_url")),
                "header": sample["header"],
                "label_like_columns": sample["label_like_columns"],
                "sample_rows": sample["sample_rows"],
            }
        )

    row_level_files = [
        file
        for file in files
        if file["download_url_verified"]
        and file["content_type"] == "text/csv"
        and set(file["label_like_columns"]).intersection({"filter_1234", "wash"})
    ]
    decision = {
        "board_state": "blocked",
        "active_axis": "MainRegimeV2",
        "candidate_regime": "Manipulation",
        "raw_row_level_public_downloads_verified": len(row_level_files),
        "qualifying_direct_manipulation_input_sets": 1 if row_level_files else 0,
        "accepted_95": False,
        "manipulation_input_state": "raw_event_onchain_wash_labels_accessible_not_calibrated",
        "thresholds_relaxed": False,
        "runtime_code_changed": False,
        "fresh_calibration_rerun": False,
        "trade_usable": False,
        "blocker": (
            "Mendeley public API exposes row-level labeled wash-trading CSV downloads, but this slice only "
            "verified metadata and bounded samples. A chronological calibration/test gate has not been run."
        ),
        "next_action": (
            "Stream the Mendeley wash-trading CSVs into a run-local calibration job, confirm label polarity for "
            "`filter_1234`, and evaluate the unchanged 95% Manipulation gate without committing raw data."
        ),
    }
    result = {
        "schema_version": "wash-trading-public-api-raw-access/v1",
        "loop_id": LOOP_ID,
        "run_root": repo_rel(RUN_ROOT),
        "dataset": {
            "url": DATASET_URL,
            "id": dataset.get("id"),
            "doi": dataset.get("doi", {}).get("id"),
            "version": dataset.get("version"),
            "name": dataset.get("name"),
            "size": dataset.get("size"),
            "license": dataset.get("data_licence", {}).get("short_name"),
            "fetched_at_local": datetime.now().isoformat(timespec="seconds"),
        },
        "files": files,
        "raw_data_policy": "no_raw_csv_committed; metadata_and_first_rows_only",
        "decision": decision,
    }

    report_json = OUT_DIR / "wash_trading_public_api_raw_access.json"
    report_md = OUT_DIR / "wash_trading_public_api_raw_access.md"
    report_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    report_md.write_text(
        "# Wash Trading Public API Raw Access\n\n"
        f"Run id: `{LOOP_ID}`\n\n"
        "This probe found the Mendeley public API path that exposes raw row-level CSV download URLs. "
        "It retained only metadata and first-row samples in the repo; no full raw CSVs were committed.\n\n"
        "Files verified:\n\n"
        + "\n".join(
            [
                f"- `{file['filename']}`: {file['size']} bytes, label-like columns {file['label_like_columns']}"
                for file in files
            ]
        )
        + "\n\n"
        f"Decision: `{decision['manipulation_input_state']}`. "
        f"Qualifying direct/event input sets: `{decision['qualifying_direct_manipulation_input_sets']}`. "
        f"Accepted 95: `{decision['accepted_95']}`. "
        f"Blocker: {decision['blocker']}\n\n"
        f"Next action: {decision['next_action']}\n",
        encoding="utf-8",
    )
    (CHECKS_DIR / "wash_trading_public_api_raw_access_assertions.out").write_text(
        "\n".join(
            [
                f"RUN_ID {LOOP_ID}",
                f"REPORT {repo_rel(report_json)}",
                f"RAW_ROW_LEVEL_PUBLIC_DOWNLOADS_VERIFIED {len(row_level_files)}",
                f"QUALIFYING_DIRECT_MANIPULATION_INPUT_SETS {decision['qualifying_direct_manipulation_input_sets']}",
                f"MANIPULATION_INPUT_STATE {decision['manipulation_input_state']}",
                "ACCEPTED_95 false",
                "THRESHOLDS_RELAXED false",
                "RUNTIME_CODE_CHANGED false",
                "FRESH_CALIBRATION_RERUN false",
                "TRADE_USABLE false",
                "RAW_DATA_COMMITTED false",
                "GATE blocked_raw_access_verified_calibration_not_run",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (RUN_ROOT / "README.md").write_text(
        "# Wash Trading Public API Raw Access\n\n"
        "- report: `raw-access/wash_trading_public_api_raw_access.md`\n"
        "- json: `raw-access/wash_trading_public_api_raw_access.json`\n"
        "- assertions: `checks/wash_trading_public_api_raw_access_assertions.out`\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
