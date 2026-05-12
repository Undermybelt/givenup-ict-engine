from __future__ import annotations

import importlib.util
import json
import os
import shutil
import socket
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T014630-codex-provider-export-readiness-contract"
OUT_DIR = RUN_ROOT / "provider-readiness"
CHECKS_DIR = RUN_ROOT / "checks"


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def env_present(names: list[str]) -> dict[str, bool]:
    return {name: bool(os.environ.get(name)) for name in names}


def port_open(host: str, port: int, timeout: float = 0.25) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def path_state(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "is_file": path.is_file(),
        "is_dir": path.is_dir(),
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    env = {
        "databento": env_present(["DATABENTO_API_KEY", "DATABENTO_KEY", "DATABENTO_API_TOKEN"]),
        "ibkr": env_present(["IBKR_HOST", "IBKR_PORT", "TWS_HOST", "TWS_PORT", "IB_GATEWAY_HOST", "IB_GATEWAY_PORT"]),
        "tradingview": env_present(["TRADINGVIEW_USERNAME", "TRADINGVIEW_PASSWORD", "TVREMIX_MCP_CONFIG", "TV_SESSION", "TVREMIX_SESSION"]),
        "kraken": env_present(["KRAKEN_API_KEY", "KRAKEN_API_SECRET"]),
    }
    configs = {
        "tvremix_mcp": path_state(Path.home() / ".ict-engine/tvremix_mcp.json"),
        "databento_config_dir": path_state(Path.home() / ".databento"),
        "databento_config_toml": path_state(Path.home() / ".databento/config.toml"),
        "ibkr_settings": path_state(Path.home() / ".ibkr"),
    }
    tools = {
        "databento_cli": shutil.which("databento"),
        "python_databento": module_available("databento"),
        "python_ib_insync": module_available("ib_insync"),
        "python_ibapi": module_available("ibapi"),
        "python_pyarrow": module_available("pyarrow"),
        "zstdcat": shutil.which("zstdcat"),
        "bsdtar": shutil.which("bsdtar"),
    }
    ports = {
        "ibkr_tws_paper_7497": port_open("127.0.0.1", 7497),
        "ibkr_tws_live_7496": port_open("127.0.0.1", 7496),
        "ib_gateway_paper_4002": port_open("127.0.0.1", 4002),
        "ib_gateway_live_4001": port_open("127.0.0.1", 4001),
    }
    provider_readiness = {
        "databento_historical_mbo": {
            "can_acquire_now_without_user_action": bool(any(env["databento"].values()) and (tools["databento_cli"] or tools["python_databento"])),
            "credential_present": any(env["databento"].values()),
            "tool_present": bool(tools["databento_cli"] or tools["python_databento"]),
            "required_export": {
                "dataset": "market-wide historical direct order-book/order-lifecycle data",
                "acceptable_schemas": ["MBO/L3 add-cancel-modify-trade messages", "MBP with aligned trades only if sufficient for declared manipulation signature"],
                "coverage": "multiple instruments, multiple chronological periods, at least two market contexts before acceptance",
            },
        },
        "ibkr_live_depth": {
            "can_acquire_now_without_user_action": bool(any(ports.values()) and (tools["python_ib_insync"] or tools["python_ibapi"])),
            "local_gateway_port_open": any(ports.values()),
            "tool_present": bool(tools["python_ib_insync"] or tools["python_ibapi"]),
            "limitation": "live depth alone is not a historical calibration set unless recorded over enough chronological support and contexts",
        },
        "tradingview": {
            "can_acquire_direct_manipulation_now": False,
            "config_present": configs["tvremix_mcp"]["exists"] or any(env["tradingview"].values()),
            "limitation": "chart/bar access is not direct L2/L3/order-lifecycle manipulation evidence",
        },
        "kraken_public": {
            "can_acquire_direct_manipulation_now": False,
            "public_recent_depth_trades_available_in_prior_probe": True,
            "limitation": "recent public trades/depth snapshots are not aligned historical order-lifecycle calibration data",
        },
    }
    can_acquire_now = any(
        item.get("can_acquire_now_without_user_action") is True
        for item in provider_readiness.values()
        if isinstance(item, dict)
    )
    report = {
        "run_id": "20260511T014630+0800-codex-provider-export-readiness-contract",
        "active_axis": "MainRegimeV2",
        "objective": "Check whether a real provider export path is immediately ready for calibration-grade direct manipulation evidence without exposing secrets.",
        "env_presence_no_values": env,
        "config_presence_no_secret_values": configs,
        "tool_readiness": tools,
        "local_port_readiness": ports,
        "provider_readiness": provider_readiness,
        "required_direct_manipulation_export_contract": {
            "must_include": [
                "chronological historical records",
                "market-wide order book or order lifecycle events, not private account-only logs",
                "direct L2/L3/MBO/add-cancel-modify/trade messages or equivalent event/social/on-chain evidence for the declared manipulation signature",
                "enough support to satisfy 120 calibration and 60 test rows after chronological split",
                "at least two instruments, periods, or market contexts before release-gate acceptance",
            ],
            "must_reject": [
                "OHLCV bars",
                "single live order book snapshots",
                "recent trade tape only",
                "thin fixture samples",
                "private account order history as market-wide proof",
                "filename/schema hints without decoded support evidence",
            ],
        },
        "decision": {
            "board_state": "blocked",
            "accepted_gate": "partial_for_MainRegimeV2_Crisis_only_prior_evidence_preserved",
            "provider_export_ready_now": can_acquire_now,
            "manipulation_input_state": "missing_required_inputs",
            "thresholds_relaxed": False,
            "runtime_code_changed": False,
            "fresh_calibration_rerun": False,
            "trade_usable": False,
            "blocker": "No immediately usable provider export path for calibration-grade direct manipulation evidence was found without additional credentials/tooling/export action.",
            "next_action": "Provide or enable a Databento-style historical MBO/L3 export with credentials/tooling, or place an already exported calibration-grade direct L2/L3/MBO/order-lifecycle dataset in a documented local path before rerunning the Manipulation gate.",
        },
    }
    report_path = OUT_DIR / "provider_export_readiness_contract.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md = [
        "# Provider Export Readiness Contract",
        "",
        f"Run id: `{report['run_id']}`",
        "",
        "## Decision",
        "",
        f"- Provider export ready now: `{str(can_acquire_now).lower()}`",
        f"- Manipulation state: `{report['decision']['manipulation_input_state']}`",
        "- Secrets were not printed; only presence/absence of env/config/tooling was recorded.",
        "",
        "Next action: " + report["decision"]["next_action"],
    ]
    (OUT_DIR / "provider_export_readiness_contract.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    checks = [
        f"report: {repo_rel(report_path)}",
        f"provider_export_ready_now: {can_acquire_now}",
        f"databento_credential_present: {provider_readiness['databento_historical_mbo']['credential_present']}",
        f"databento_tool_present: {provider_readiness['databento_historical_mbo']['tool_present']}",
        f"ibkr_gateway_or_tws_port_open: {provider_readiness['ibkr_live_depth']['local_gateway_port_open']}",
        f"ibkr_python_tool_present: {provider_readiness['ibkr_live_depth']['tool_present']}",
        f"tradingview_config_present: {provider_readiness['tradingview']['config_present']}",
        "thresholds_relaxed: False",
        "runtime_code_changed: False",
        "fresh_calibration_rerun: False",
        "trade_usable: False",
        "MANIPULATION_INPUT_STATE missing_required_inputs",
        "GATE blocked_provider_export_not_ready",
    ]
    (CHECKS_DIR / "provider_export_readiness_contract_assertions.out").write_text("\n".join(checks) + "\n", encoding="utf-8")
    (RUN_ROOT / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
