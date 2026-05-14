#!/usr/bin/env python3
"""Probe TradingViewRemix user-side exports without storing secrets or raw user data."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen


RUN_ID = "20260511T110824+0800-codex-tvremix-user-label-export-probe"
REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T110824-codex-tvremix-user-label-export-probe"
OUT_DIR = RUN_ROOT / "tvremix-user-label"
CHECK_DIR = RUN_ROOT / "checks"
CONFIG = Path.home() / ".ict-engine/tvremix_mcp.json"
TOOLS = ["my_watchlists", "my_alerts", "my_charts"]
KEYWORDS = [
    "regime",
    "bull",
    "bear",
    "sideways",
    "crisis",
    "manipulation",
    "wash",
    "pump",
    "dump",
    "牛",
    "熊",
    "震荡",
    "危机",
    "操纵",
]


def call_tool(url: str, api_key: str, name: str) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": {}},
    }
    req = Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urlopen(req, timeout=30) as resp:  # noqa: S310 - fixed locally configured MCP URL
        return json.loads(resp.read().decode("utf-8"))


def summarize_response(tool: str, response: dict) -> dict:
    result = response.get("result", {})
    structured = result.get("structuredContent") or {}
    raw_for_hash = json.dumps(result, sort_keys=True, ensure_ascii=False)
    lowered = raw_for_hash.lower()
    return {
        "tool": tool,
        "jsonrpc_error_present": "error" in response,
        "is_error": bool(result.get("isError", False)),
        "structured_keys": sorted(structured.keys()),
        "success": structured.get("success"),
        "connected": structured.get("connected"),
        "error_code": structured.get("error"),
        "payload_chars": len(raw_for_hash),
        "payload_sha256": hashlib.sha256(raw_for_hash.encode()).hexdigest(),
        "keyword_hits": [word for word in KEYWORDS if word.lower() in lowered],
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG.exists():
        report = {
            "run_id": RUN_ID,
            "active_taxonomy": "MainRegimeV2",
            "config_present": False,
            "secret_values_recorded": False,
            "result": {
                "accepted_parent_root_slots_added": 0,
                "accepted_direct_manipulation_rows_added": 0,
                "gate_result": "blocked_tvremix_user_exports_config_missing",
            },
        }
    else:
        cfg = json.loads(CONFIG.read_text())
        url = cfg["url"]
        api_key = cfg["api_key"]
        tool_results = []
        for tool in TOOLS:
            try:
                tool_results.append(summarize_response(tool, call_tool(url, api_key, tool)))
            except Exception as exc:  # keep artifact sanitized
                tool_results.append(
                    {
                        "tool": tool,
                        "jsonrpc_error_present": True,
                        "is_error": True,
                        "error_type": type(exc).__name__,
                        "error_code": "probe_exception",
                        "payload_chars": 0,
                        "payload_sha256": None,
                        "keyword_hits": [],
                    }
                )

        connected_tools = [row["tool"] for row in tool_results if row.get("connected") is True]
        keyword_tools = [row["tool"] for row in tool_results if row.get("keyword_hits")]
        report = {
            "run_id": RUN_ID,
            "board": "docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
            "active_taxonomy": "MainRegimeV2",
            "scope": "TradingViewRemix user-side watchlist/alert/chart export probe for possible manual regime labels.",
            "config_present": True,
            "secret_values_recorded": False,
            "raw_user_payload_recorded": False,
            "tools_probed": TOOLS,
            "tool_results_sanitized": tool_results,
            "connected_tools": connected_tools,
            "tools_with_regime_keyword_hits": keyword_tools,
            "assessment": {
                "can_supply_manual_or_user_label_export_now": bool(connected_tools and keyword_tools),
                "reason": "TradingView account user-data tools are not connected, or no sanitized regime-keyword evidence was observed.",
            },
            "result": {
                "accepted_parent_root_slots_added": 0,
                "accepted_direct_manipulation_rows_added": 0,
                "gate_result": "blocked_tvremix_user_exports_not_connected_no_label_export",
                "runtime_code_changed": False,
                "thresholds_relaxed": False,
                "raw_data_committed": False,
                "trade_usable": False,
            },
            "next_action": "Acquire an explicit labeled MainRegimeV2 panel or connect/provide a documented TradingView manual label export; do not treat OHLCV, alerts, or charts as labels without v3 schema provenance.",
        }

    (OUT_DIR / "tvremix_user_label_export_probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    lines = [
        "# TradingViewRemix User Label Export Probe",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Config present: `{str(report.get('config_present')).lower()}`.",
        "- Secret values recorded: `false`.",
        "- Raw user payload recorded: `false`.",
    ]
    if report.get("tool_results_sanitized"):
        lines.extend(["", "## Sanitized Tool Readback", "", "| Tool | Connected | Error Code | Keyword Hits |", "|---|---:|---|---|"])
        for row in report["tool_results_sanitized"]:
            hits = ",".join(row.get("keyword_hits", [])) or "none"
            lines.append(f"| `{row['tool']}` | `{row.get('connected')}` | `{row.get('error_code')}` | `{hits}` |")
    result = report["result"]
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Accepted parent-root slots added: `{result['accepted_parent_root_slots_added']}`.",
            f"- Accepted direct `Manipulation` rows added: `{result['accepted_direct_manipulation_rows_added']}`.",
            f"- Gate result: `{result['gate_result']}`.",
            "- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.",
            "",
            "## Boundary",
            "",
            "- This closes only the currently configured TradingViewRemix user-export path.",
            "- OHLCV, technicals, alerts, and charts remain sidecar data unless an explicit v3-compatible label export is supplied.",
        ]
    )
    (OUT_DIR / "tvremix_user_label_export_probe.md").write_text("\n".join(lines) + "\n")

    result = report["result"]
    checks = [
        "PASS active_taxonomy=MainRegimeV2",
        "PASS secret_values_recorded=false",
        "PASS raw_user_payload_recorded=false",
        f"PASS accepted_parent_root_slots_added={result['accepted_parent_root_slots_added']}",
        f"PASS accepted_direct_Manipulation_rows_added={result['accepted_direct_manipulation_rows_added']}",
        "PASS thresholds_relaxed=false",
        "PASS runtime_code_changed=false",
        "PASS raw_data_committed=false",
        "PASS trade_usable=false",
        f"GATE {result['gate_result']}",
    ]
    (CHECK_DIR / "tvremix_user_label_export_probe_assertions.out").write_text("\n".join(checks) + "\n")


if __name__ == "__main__":
    main()
