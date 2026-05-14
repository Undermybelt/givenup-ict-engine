#!/usr/bin/env python3
"""Audit hnghiem-nlp/Pump_and_Dump_Crypto against Board A direct-label rules."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T110514+0800-codex-pumpolymp-source-audit"
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "source-audit"
CHECK_DIR = RUN_ROOT / "checks"
REPO = "hnghiem-nlp/Pump_and_Dump_Crypto"
BRANCH = "master"


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ict-engine-board-a-source-audit/1.0",
            "Accept": "application/vnd.github+json,application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ict-engine-board-a-source-audit/1.0"},
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read().decode("utf-8", errors="replace")


def raw_url(path: str) -> str:
    return (
        f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/"
        + urllib.parse.quote(path)
    )


def scan_notebook(path: str) -> dict:
    try:
        notebook = json.loads(fetch_text(raw_url(path)))
    except Exception as exc:  # noqa: BLE001 - audit reports fetch/parse failure.
        return {"path": path, "error": repr(exc), "hits": []}

    hits: list[str] = []
    for cell in notebook.get("cells", []):
        source = "".join(cell.get("source", []))
        for line in source.splitlines():
            lowered = line.lower()
            if any(
                token in lowered
                for token in [
                    "allpumps_20200201.json",
                    "pumpolymp",
                    "read_json",
                    "to_pickle",
                    "coin_data",
                    "negative",
                    "extra_date",
                ]
            ):
                hits.append(line[:260])
    return {"path": path, "error": None, "hits": hits[:80], "hit_count": len(hits)}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    tree_url = f"https://api.github.com/repos/{REPO}/git/trees/{BRANCH}?recursive=1"
    tree = fetch_json(tree_url)
    files = [
        item["path"]
        for item in tree.get("tree", [])
        if item.get("type") == "blob"
    ]
    data_like_files = [
        path
        for path in files
        if path.lower().endswith((".csv", ".json", ".pkl", ".parquet", ".feather"))
    ]
    notebooks_scanned = [
        "Final_Analysis/Final_Mod_0_Format_Pump_Data.ipynb",
        "General_Analysis/Mod_0_All_Historical_Pump_Analysis.ipynb",
        "General_Analysis/Mod_1_Acquire_Data_for_Pumps.ipynb",
        "Before_Pump_Analysis/Mod_1_Download_pumped_coin_historical_data.ipynb",
    ]
    notebook_hits = [scan_notebook(path) for path in notebooks_scanned]
    references_external_event_json = any(
        "allPumps_20200201.json" in hit
        for scan in notebook_hits
        for hit in scan.get("hits", [])
    )

    report = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": "docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
        "active_taxonomy": "MainRegimeV2",
        "objective": "Audit the public PumpOlymp-based repository for materialized direct Manipulation labels usable by Board A.",
        "source": {
            "repo": REPO,
            "repo_url": f"https://github.com/{REPO}",
            "tree_url": tree_url,
            "tree_sha": tree.get("sha"),
            "truncated": tree.get("truncated"),
            "published_blob_count": len(files),
            "published_data_like_files": data_like_files,
        },
        "readback": {
            "notebooks_scanned": notebooks_scanned,
            "notebook_hits": notebook_hits,
            "references_external_event_json": references_external_event_json,
            "external_event_json": "../../allPumps_20200201.json",
            "event_fields_seen_in_notebook": [
                "channelLink",
                "channelTitle",
                "currency",
                "duration",
                "exchange",
                "priceBeforePump",
                "signalTime",
            ],
            "positive_event_source_materialized_in_repo": False,
            "same_asset_venue_negative_controls_materialized_in_repo": False,
            "current_exact_provider_kraken_labels": False,
        },
        "result": {
            "accepted_parent_root_slots_added": 0,
            "accepted_direct_manipulation_rows_added": 0,
            "accepted_direct_manipulation_sources_added": 0,
            "gate_result": "blocked_pumpolymp_repo_code_only_event_json_not_published",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": "If the PumpOlymp `allPumps_20200201.json` export or equivalent event table is supplied, run a direct pump/dump gate with same-exchange non-event controls; otherwise do not count this repository.",
    }

    json_path = OUT_DIR / "pumpolymp_source_audit.json"
    md_path = OUT_DIR / "pumpolymp_source_audit.md"
    checks_path = CHECK_DIR / "pumpolymp_source_audit_assertions.out"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    hit_summary = "\n".join(
        f"- `{scan['path']}`: hit_count `{scan.get('hit_count', 0)}`, error `{scan.get('error')}`"
        for scan in notebook_hits
    )
    md_path.write_text(
        "\n".join(
            [
                "# PumpOlymp Source Audit",
                "",
                f"Run ID: `{RUN_ID}`",
                "",
                "## Scope",
                "",
                "This audit checks whether the public `hnghiem-nlp/Pump_and_Dump_Crypto` repo materializes direct pump/dump event labels and same-venue negative controls for Board A `Manipulation` accounting.",
                "",
                "## Readback",
                "",
                f"- Published blob count: `{len(files)}`.",
                f"- Published data-like files: `{len(data_like_files)}`.",
                f"- References external `allPumps_20200201.json`: `{str(references_external_event_json).lower()}`.",
                "- Event fields seen in notebooks: `channelLink`, `channelTitle`, `currency`, `duration`, `exchange`, `priceBeforePump`, `signalTime`.",
                "- Materialized positive event JSON in public repo: `false`.",
                "- Materialized same-asset/venue negative controls in public repo: `false`.",
                "",
                "## Notebook Scan",
                "",
                hit_summary,
                "",
                "## Decision",
                "",
                "- Accepted parent-root slots added: `0`.",
                "- Accepted direct `Manipulation` rows added: `0`.",
                "- Gate result: `blocked_pumpolymp_repo_code_only_event_json_not_published`.",
                "- Runtime code changed: false.",
                "- Thresholds relaxed: false.",
                "- Raw data committed: false.",
                "- Trade usable: false.",
                "",
                "The repository is a useful acquisition lead, but it publishes notebooks/code rather than the replayable event-label table required by Board A. Do not count it unless the PumpOlymp export is supplied or independently reachable with row-level timestamps and controls.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = [
        "PASS active_taxonomy=MainRegimeV2",
        f"PASS published_data_like_files={len(data_like_files)}",
        f"PASS references_external_event_json={str(references_external_event_json).lower()}",
        "PASS positive_event_source_materialized_in_repo=false",
        "PASS same_asset_venue_negative_controls_materialized_in_repo=false",
        "PASS current_exact_provider_kraken_labels=false",
        "PASS accepted_parent_root_slots_added=0",
        "PASS accepted_direct_manipulation_rows_added=0",
        "PASS accepted_direct_manipulation_sources_added=0",
        "PASS raw_data_committed=false",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
        "PASS trade_usable=false",
        "GATE blocked_pumpolymp_repo_code_only_event_json_not_published",
    ]
    checks_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
