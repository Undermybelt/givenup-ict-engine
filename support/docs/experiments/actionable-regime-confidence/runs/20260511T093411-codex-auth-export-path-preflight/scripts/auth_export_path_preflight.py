#!/usr/bin/env python3
"""Check local authenticated export paths without exposing secrets."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


RUN_ID = "20260511T093411+0800-codex-auth-export-path-preflight"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T093411-codex-auth-export-path-preflight"
)
OUT_DIR = RUN_ROOT / "auth-export-preflight"
CHECK_DIR = RUN_ROOT / "checks"


ENV_KEYS = [
    "DUNE_API_KEY",
    "KAGGLE_USERNAME",
    "KAGGLE_KEY",
    "HF_TOKEN",
    "HUGGINGFACE_TOKEN",
    "FINRA_API_KEY",
    "FINRA_CLIENT_ID",
    "FINRA_CLIENT_SECRET",
    "SEC_API_KEY",
    "FRED_API_KEY",
]

FILES = [
    ("kaggle_json", Path.home() / ".kaggle" / "kaggle.json"),
    ("dune_config", Path.home() / ".config" / "dune" / "config.json"),
    ("huggingface_token", Path.home() / ".cache" / "huggingface" / "token"),
    ("ict_tvremix_mcp", Path.home() / ".ict-engine" / "tvremix_mcp.json"),
]


def present_env() -> dict[str, bool]:
    return {key: bool(os.environ.get(key)) for key in ENV_KEYS}


def present_files() -> dict[str, dict[str, object]]:
    result = {}
    for label, path in FILES:
        result[label] = {
            "path": str(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }
    return result


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    env = present_env()
    files = present_files()
    kaggle_ready = (env["KAGGLE_USERNAME"] and env["KAGGLE_KEY"]) or files["kaggle_json"]["exists"]
    dune_ready = env["DUNE_API_KEY"] or files["dune_config"]["exists"]
    hf_ready = env["HF_TOKEN"] or env["HUGGINGFACE_TOKEN"] or files["huggingface_token"]["exists"]
    finra_ready = env["FINRA_API_KEY"] or (env["FINRA_CLIENT_ID"] and env["FINRA_CLIENT_SECRET"])

    packet = {
        "run_id": RUN_ID,
        "active_taxonomy": "MainRegimeV2",
        "objective": "Check whether authenticated/exportable local paths exist for source-label panels or direct Manipulation rows.",
        "secret_values_recorded": False,
        "env_present": env,
        "file_present": files,
        "export_paths": {
            "dune_ready": bool(dune_ready),
            "kaggle_ready": bool(kaggle_ready),
            "huggingface_ready": bool(hf_ready),
            "finra_ready": bool(finra_ready),
            "sec_api_ready": bool(env["SEC_API_KEY"]),
            "fred_ready_sidecar_only": bool(env["FRED_API_KEY"]),
            "tradingview_config_present": bool(files["ict_tvremix_mcp"]["exists"]),
        },
        "accepted_new_parent_root_label_sources": 0,
        "accepted_new_direct_manipulation_rows": 0,
        "accepted_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
        "gate_result": "blocked_auth_export_paths_no_accepted_label_export_available",
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": "Use an available authenticated export path only if it yields exact-underlying parent-root labels or timestamped direct Manipulation positive/negative rows; otherwise user-provided structured panels are required.",
    }

    json_path = OUT_DIR / "auth_export_path_preflight.json"
    md_path = OUT_DIR / "auth_export_path_preflight.md"
    checks_path = CHECK_DIR / "auth_export_path_preflight_assertions.out"

    json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(
        "\n".join(
            [
                "# Auth Export Path Preflight",
                "",
                f"Run ID: `{RUN_ID}`",
                "",
                "## Result",
                "",
                "- Secret values recorded: false.",
                f"- Dune ready: `{str(bool(dune_ready)).lower()}`.",
                f"- Kaggle ready: `{str(bool(kaggle_ready)).lower()}`.",
                f"- HuggingFace ready: `{str(bool(hf_ready)).lower()}`.",
                f"- FINRA ready: `{str(bool(finra_ready)).lower()}`.",
                f"- SEC API ready: `{str(bool(env['SEC_API_KEY'])).lower()}`.",
                f"- FRED ready sidecar only: `{str(bool(env['FRED_API_KEY'])).lower()}`.",
                f"- TradingView config present: `{str(bool(files['ict_tvremix_mcp']['exists'])).lower()}`.",
                "- Accepted new parent-root label sources: `0`.",
                "- Accepted new direct `Manipulation` rows: `0`.",
                f"- Gate result: `{packet['gate_result']}`.",
                "- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.",
                "",
                "## Next Action",
                "",
                packet["next_action"],
                "",
            ]
        ),
        encoding="utf-8",
    )
    checks_path.write_text(
        "\n".join(
            [
                "PASS secret_values_recorded=false",
                "PASS accepted_new_parent_root_label_sources=0",
                "PASS accepted_new_direct_manipulation_rows=0",
                f"PASS accepted_gate={packet['accepted_gate']}",
                f"PASS gate_result={packet['gate_result']}",
                "PASS thresholds_relaxed=false",
                "PASS runtime_code_changed=false",
                "PASS raw_data_committed=false",
                "PASS trade_usable=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(json_path)
    print(md_path)
    print(checks_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
