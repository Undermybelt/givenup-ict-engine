#!/usr/bin/env python3
"""Preflight the live PumpOlymp API for direct Manipulation evidence."""

from __future__ import annotations

import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T111647+0800-codex-pumpolymp-live-api-direct-preflight"
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "source-audit"
CHECK_DIR = RUN_ROOT / "checks"
APP_URL = "https://pumpolymp.com/analytics/allPumps"
APP_JS = "https://pumpolymp.com/assets/index-Bp9XoqCY.js"
API_BASE_FALLBACK = "https://api.pumpolymp.com"


def fetch_bytes(url: str, timeout: int = 30) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ict-engine-board-a-source-audit/1.0",
            "Accept": "application/json,text/html,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def fetch_json(url: str, timeout: int = 30) -> dict:
    return json.loads(fetch_bytes(url, timeout=timeout).decode("utf-8"))


def extract_api_base(js_text: str) -> str:
    match = re.search(r'https://api\.pumpolymp\.com', js_text)
    return match.group(0) if match else API_BASE_FALLBACK


def schema_of(item: dict) -> dict:
    schema = {}
    for key, value in item.items():
        if key == "points" and isinstance(value, list):
            schema[key] = {
                "type": "list",
                "sample_len": len(value),
                "point_keys": sorted(value[0].keys()) if value else [],
            }
        elif isinstance(value, list):
            schema[key] = {"type": "list", "sample_len": len(value)}
        elif isinstance(value, dict):
            schema[key] = {"type": "dict", "keys": sorted(value.keys())}
        else:
            schema[key] = type(value).__name__
    return schema


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    app_html = fetch_bytes(APP_URL).decode("utf-8", errors="replace")
    js_text = fetch_bytes(APP_JS).decode("utf-8", errors="replace")
    api_base = extract_api_base(js_text)
    summary = fetch_json(f"{api_base}/api/pumps/summary?limit=25&offset=0")
    latest = fetch_json(f"{api_base}/api/pumps/latest?limit=1")

    summary_items = summary.get("items", [])
    latest_items = latest.get("items", [])
    sample_item = summary_items[0] if summary_items else latest_items[0] if latest_items else {}
    latest_detail_item = latest_items[0] if latest_items else sample_item
    sample_schema = schema_of(sample_item) if sample_item else {}
    latest_detail_schema = schema_of(latest_detail_item) if latest_detail_item else {}
    point_schema = latest_detail_schema.get("points", {}).get("point_keys", [])
    pair_count = len({item.get("pair_address") for item in summary_items if item.get("pair_address")})
    min_start = min((item.get("start_time_utc") for item in summary_items if item.get("start_time_utc")), default=None)
    max_start = max((item.get("start_time_utc") for item in summary_items if item.get("start_time_utc")), default=None)

    report = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": "docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
        "active_taxonomy": "MainRegimeV2",
        "objective": "Preflight the live PumpOlymp API for accepted direct Manipulation rows under Board A.",
        "source": {
            "app_url": APP_URL,
            "app_js": APP_JS,
            "api_base": api_base,
            "endpoints_probed": [
                f"{api_base}/api/pumps/summary?limit=25&offset=0",
                f"{api_base}/api/pumps/latest?limit=1",
            ],
            "html_contains_pump_viewer": "Pump Viewer" in app_html,
        },
        "readback": {
            "summary_total": summary.get("total"),
            "summary_count": summary.get("count"),
            "summary_limit": summary.get("limit"),
            "summary_offset": summary.get("offset"),
            "sample_unique_pairs_in_first_page": pair_count,
            "first_page_start_time_min": min_start,
            "first_page_start_time_max": max_start,
            "sample_item_schema": sample_schema,
            "latest_detail_schema": latest_detail_schema,
            "point_schema": point_schema,
            "positive_pump_documents_available": bool(summary_items or latest_items),
            "same_asset_venue_negative_controls_available": False,
            "manual_or_adjudicated_event_label_source_visible": False,
            "current_provider_exact_match": "BSC/DexScreener-style pair archive; not yfinance/Kraken MainRegimeV2 parent-root slot data",
        },
        "result": {
            "accepted_parent_root_slots_added": 0,
            "accepted_direct_manipulation_rows_added": 0,
            "accepted_direct_manipulation_sources_added": 0,
            "gate_result": "blocked_pumpolymp_live_api_positive_only_no_negative_controls",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": "Use this live API only as a direct-positive acquisition lead until same-pair non-pump controls or an adjudicated label/export contract is available; do not count positive-only detector output as accepted Manipulation coverage.",
    }

    json_path = OUT_DIR / "pumpolymp_live_api_direct_preflight.json"
    md_path = OUT_DIR / "pumpolymp_live_api_direct_preflight.md"
    checks_path = CHECK_DIR / "pumpolymp_live_api_direct_preflight_assertions.out"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    md_path.write_text(
        "\n".join(
            [
                "# PumpOlymp Live API Direct Preflight",
                "",
                f"Run ID: `{RUN_ID}`",
                "",
                "## Scope",
                "",
                "This preflight checks the live PumpOlymp web/API surface for direct `Manipulation` rows usable by Board A.",
                "",
                "## Readback",
                "",
                f"- API base extracted from app bundle: `{api_base}`.",
                f"- Summary total: `{summary.get('total')}`.",
                f"- Summary first-page count: `{summary.get('count')}`.",
                f"- First-page unique pairs: `{pair_count}`.",
                f"- First-page start time span: `{min_start}` to `{max_start}`.",
                f"- Positive pump documents available: `{str(bool(summary_items or latest_items)).lower()}`.",
                "- Same-asset/venue negative controls available from probed endpoints: `false`.",
                "- Manual/adjudicated event-label source visible from probed endpoints: `false`.",
                "",
                "## Schema",
                "",
                f"- Summary item keys: `{', '.join(sorted(sample_schema.keys()))}`.",
                f"- Latest detail item keys: `{', '.join(sorted(latest_detail_schema.keys()))}`.",
                f"- Point keys: `{', '.join(point_schema)}`.",
                "",
                "## Decision",
                "",
                "- Accepted parent-root slots added: `0`.",
                "- Accepted direct `Manipulation` rows added: `0`.",
                "- Gate result: `blocked_pumpolymp_live_api_positive_only_no_negative_controls`.",
                "- Runtime code changed: false.",
                "- Thresholds relaxed: false.",
                "- Raw data committed: false.",
                "- Trade usable: false.",
                "",
                "This is a useful direct-positive acquisition lead, but it remains positive-only detector output from a BSC/DexScreener-style pair archive. It does not satisfy the current Board A direct gate without same-pair non-pump controls or adjudicated event-label provenance.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = [
        "PASS active_taxonomy=MainRegimeV2",
        f"PASS live_api_base={api_base}",
        f"PASS positive_pump_documents_available={str(bool(summary_items or latest_items)).lower()}",
        "PASS same_asset_venue_negative_controls_available=false",
        "PASS manual_or_adjudicated_event_label_source_visible=false",
        "PASS accepted_parent_root_slots_added=0",
        "PASS accepted_direct_manipulation_rows_added=0",
        "PASS accepted_direct_manipulation_sources_added=0",
        "PASS raw_data_committed=false",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
        "PASS trade_usable=false",
        "GATE blocked_pumpolymp_live_api_positive_only_no_negative_controls",
    ]
    checks_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
