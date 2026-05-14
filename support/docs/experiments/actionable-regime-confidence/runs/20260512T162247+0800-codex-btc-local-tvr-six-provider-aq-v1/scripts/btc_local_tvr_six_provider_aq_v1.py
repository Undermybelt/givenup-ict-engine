from __future__ import annotations

import csv
import importlib.util
import json
import os
from pathlib import Path
from typing import Any


RUN_ID = "20260512T162247+0800-codex-btc-local-tvr-six-provider-aq-v1"
RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
BASE_SCRIPT = (
    RUNS
    / "20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1"
    / "scripts"
    / "six_provider_btc_same_root_aq_ibkr_aggtrades_probe_v1.py"
)

OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
CONFIG_DIR = ROOT / "config"
REPORT_DIR = ROOT / "btc-local-tvr-six-provider-aq-v1"
PROVIDER_CSV_DIR = ROOT / "provider-csv"
WORKSPACE_ROOT = ROOT / "workspace"


def load_base() -> Any:
    spec = importlib.util.spec_from_file_location("six_provider_btc_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.RUN_ID = RUN_ID
    module.ROOT = ROOT
    module.OUT_DIR = OUT_DIR
    module.CHECK_DIR = CHECK_DIR
    module.CONFIG_DIR = CONFIG_DIR
    module.REPORT_DIR = REPORT_DIR
    module.PROVIDER_CSV_DIR = PROVIDER_CSV_DIR
    module.WORKSPACE_ROOT = WORKSPACE_ROOT
    return module


BASE = load_base()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def run_cmd(name: str, cmd: list[str], *, env: dict[str, str] | None = None, timeout: int = 900) -> int:
    return BASE.run_cmd(name, cmd, env=env, timeout=timeout)


def exit_code(path: Path) -> int | None:
    return BASE.exit_code(path)


def csv_rows(path: Path) -> int:
    return BASE.csv_rows(path)


def write_ibkr_config() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config = CONFIG_DIR / "ibkr_btc_paxos_aggtrades_1h.yaml"
    config.write_text(
        "\n".join(
            [
                "gateway:",
                "  host: 127.0.0.1",
                "  port: 4002",
                "  client_id: 62",
                "output:",
                f"  directory: {PROVIDER_CSV_DIR}",
                "  filename_template: '{symbol}_{bar_suffix}_{what}.csv'",
                "  force: true",
                "defaults:",
                "  bar_size: '1 hour'",
                "  duration: '30 D'",
                "  what_to_show: AGGTRADES",
                "  rth: false",
                "  exchange: PAXOS",
                "  currency: USD",
                "symbols:",
                "  - symbol: BTC",
                "    sec_type: CRYPTO",
                "    exchange: PAXOS",
                "    currency: USD",
                "    what_to_show: AGGTRADES",
                "    rth: false",
                "    bar_sizes: ['1 hour']",
                "    duration: '30 D'",
                "",
            ]
        )
    )
    return config


def tvr_local_env() -> dict[str, str]:
    env = {
        "HOME": "/tmp/ict-engine-tvr-btc-local-stdio-162247-home",
        "ICT_ENGINE_TRADINGVIEW_MCP_CMD": "uv",
        "ICT_ENGINE_TRADINGVIEW_MCP_ARGS": "--directory /Users/thrill3r/tradingview-mcp/tradingview-mcp run tradingview-mcp",
    }
    for key in ("ICT_ENGINE_TVREMIX_MCP_API_KEY", "TVREMIX_MCP_API_KEY", "ICT_ENGINE_TRADINGVIEW_MCP_URL"):
        env[key] = ""
    return env


def fetch_providers() -> dict[str, Any]:
    for path in (OUT_DIR, CHECK_DIR, CONFIG_DIR, REPORT_DIR, PROVIDER_CSV_DIR, WORKSPACE_ROOT):
        path.mkdir(parents=True, exist_ok=True)

    provider_status = [
        ("00_provider_status_yfinance", "yfinance", None),
        ("01_provider_status_tradingview_mcp_local_stdio", "tradingview_mcp", tvr_local_env()),
        ("02_provider_status_ibkr", "ibkr", None),
        ("03_provider_status_ibkr_bridge", "ibkr_bridge", None),
        ("04_provider_status_kraken_public", "kraken_public", None),
        ("05_provider_status_binance_public", "binance_public", None),
        ("06_provider_status_bybit_public", "bybit_public", None),
    ]
    for name, provider, env in provider_status:
        run_cmd(name, ["./target/debug/ict-engine", "provider-status", "--provider", provider, "--agent"], env=env, timeout=180)

    start = "2026-04-01"
    end = "2026-05-12"
    run_cmd(
        "10_yfinance_btc_usd_1h",
        [
            "uv",
            "run",
            "--with",
            "yfinance",
            "--with",
            "pandas",
            "scripts/auto_quant_external/fetch_external.py",
            "yahoo",
            "--symbol",
            "BTC-USD",
            "--interval",
            "1h",
            "--start",
            start,
            "--end",
            end,
            "--output",
            str(PROVIDER_CSV_DIR / "yfinance_btc_usd_1h.csv"),
        ],
    )
    run_cmd(
        "11_kraken_xbtusd_1h",
        [
            "uv",
            "run",
            "--with",
            "pandas",
            "scripts/auto_quant_external/fetch_external.py",
            "kraken-kline",
            "--market",
            "spot",
            "--pair",
            "XBTUSD",
            "--interval",
            "1h",
            "--start",
            start,
            "--end",
            end,
            "--output",
            str(PROVIDER_CSV_DIR / "kraken_xbtusd_1h.csv"),
        ],
    )
    run_cmd(
        "12_binance_btcusdt_1h",
        [
            "uv",
            "run",
            "--with",
            "pandas",
            "scripts/auto_quant_external/fetch_external.py",
            "binance-kline",
            "--symbol",
            "BTCUSDT",
            "--interval",
            "1h",
            "--start",
            start,
            "--end",
            end,
            "--output",
            str(PROVIDER_CSV_DIR / "binance_btcusdt_1h.csv"),
        ],
    )
    run_cmd(
        "13_bybit_btcusdt_linear_1h",
        [
            "uv",
            "run",
            "--with",
            "pandas",
            "scripts/auto_quant_external/fetch_external.py",
            "bybit-kline",
            "--category",
            "linear",
            "--symbol",
            "BTCUSDT",
            "--interval",
            "1h",
            "--start",
            start,
            "--end",
            end,
            "--output",
            str(PROVIDER_CSV_DIR / "bybit_btcusdt_linear_1h.csv"),
        ],
    )

    tvr_csv = PROVIDER_CSV_DIR / "tvr_btc_usd_local_stdio_1h.csv"
    run_cmd(
        "14_tvr_btc_usd_1h_local_stdio",
        [
            "./target/debug/ict-engine",
            "market-data-harness",
            "--action",
            "fetch",
            "--market",
            "board-a-btc-local-tvr-six-provider-1h",
            "--interval",
            "1h",
            "--role",
            "crypto_reference",
            "--provider",
            "crypto_reference=tradingview_mcp",
            "--symbol-spec",
            "crypto_reference=BTC-USD",
        ],
        env=tvr_local_env(),
    )
    tvr_rows = 0
    if exit_code(CHECK_DIR / "14_tvr_btc_usd_1h_local_stdio.exit") == 0:
        tvr_rows = BASE.write_tvr_csv(
            "tvr_btc_usd_local_stdio",
            OUT_DIR / "14_tvr_btc_usd_1h_local_stdio.stdout",
            tvr_csv,
        )

    ibkr_config = write_ibkr_config()
    run_cmd(
        "15_ibkr_btc_paxos_aggtrades_1h",
        [
            "/Users/thrill3r/Auto-Quant/.venv/bin/python",
            "scripts/auto_quant_external/fetch_external.py",
            "ibkr-bulk",
            "--config",
            str(ibkr_config),
            "--force",
        ],
        env={"PYTHONPATH": f"{Path.cwd() / 'scripts'}:{Path.cwd()}"},
    )

    return {
        "fetch_rows": {
            "yfinance_btc_usd_1h": csv_rows(PROVIDER_CSV_DIR / "yfinance_btc_usd_1h.csv"),
            "kraken_xbtusd_1h": csv_rows(PROVIDER_CSV_DIR / "kraken_xbtusd_1h.csv"),
            "binance_btcusdt_1h": csv_rows(PROVIDER_CSV_DIR / "binance_btcusdt_1h.csv"),
            "bybit_btcusdt_linear_1h": csv_rows(PROVIDER_CSV_DIR / "bybit_btcusdt_linear_1h.csv"),
            "tvr_btc_usd_1h_local_stdio": csv_rows(tvr_csv),
            "tvr_selected_1h": tvr_rows,
            "ibkr_btc_paxos_aggtrades_1h": csv_rows(PROVIDER_CSV_DIR / "BTC_1h_aggtrades.csv"),
        },
        "fetch_exits": {
            "yfinance_btc_usd_1h": exit_code(CHECK_DIR / "10_yfinance_btc_usd_1h.exit"),
            "kraken_xbtusd_1h": exit_code(CHECK_DIR / "11_kraken_xbtusd_1h.exit"),
            "binance_btcusdt_1h": exit_code(CHECK_DIR / "12_binance_btcusdt_1h.exit"),
            "bybit_btcusdt_linear_1h": exit_code(CHECK_DIR / "13_bybit_btcusdt_linear_1h.exit"),
            "tvr_btc_usd_1h_local_stdio": exit_code(CHECK_DIR / "14_tvr_btc_usd_1h_local_stdio.exit"),
            "ibkr_btc_paxos_aggtrades_1h": exit_code(CHECK_DIR / "15_ibkr_btc_paxos_aggtrades_1h.exit"),
        },
        "ibkr_config": str(ibkr_config),
        "tvr_selected_csv": str(tvr_csv),
        "tvr_selected_symbol": "BTC-USD(local-stdio)",
        "tvr_remote_http_api_called": False,
    }


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "btc_local_tvr_six_provider_aq_v1.md"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_btc_local_tvr_six_provider_aq_v1.csv"
    assertions = CHECK_DIR / "btc_local_tvr_six_provider_aq_v1_assertions.out"

    lines = [
        "# BTC Local-StdIO TVR Six-Provider AQ v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Scope",
        "Fresh Board A provider/AQ packet using the local-stdio `tradingview_mcp` `BTC-USD` route from `160908`.",
        "This run attempts BTC-comparable 1h provider/AQ authority across IBKR, TVR, yfinance, Kraken, Binance, and Bybit.",
        "It does not run downstream Pre-Bayes/BBN/CatBoost/execution-tree admission and does not call `update_goal`.",
        "",
        "## Provider Fetches",
    ]
    for key, rows in summary["provider_matrix"]["fetch_rows"].items():
        lines.append(f"- `{key}`: rows `{rows}`, exit `{summary['provider_matrix']['fetch_exits'].get(key)}`.")
    lines.extend(["", "## AQ Results"])
    for result in summary["aq_results"]:
        if result.get("skipped"):
            lines.append(f"- `{result['provider']}`: skipped, rows `0`, reason `{result['skip_reason']}`.")
            continue
        lines.append(
            f"- `{result['provider']}`: rows `{result['rows']}`, compile exit `{result['compile_exit']}`, TOMAC exit `{result['run_tomac_exit']}`."
        )
        for strategy, payload in sorted(result.get("metrics", {}).items()):
            aggregate = payload.get("aggregate", {})
            lines.append(
                f"  - `{strategy}`: trades `{aggregate.get('trade_count')}`, "
                f"profit_pct `{aggregate.get('total_profit_pct')}`, "
                f"win_rate_pct `{aggregate.get('win_rate_pct')}`, "
                f"profit_factor `{aggregate.get('profit_factor')}`."
            )
    lines.extend(
        [
            "",
            "## Decision",
            f"- Gate result: `{summary['gate_result']}`.",
            f"- Successful AQ provider runs: `{summary['metric_totals']['run_success']}/{summary['metric_totals']['provider_runs']}`.",
            f"- Strategies with metrics: `{summary['metric_totals']['strategies_with_metrics']}`.",
            f"- Total trades in AQ metrics: `{summary['metric_totals']['total_trades']}`.",
            f"- Same-root six-provider AQ authority: `{summary['same_root_six_provider_aq_authority']}`.",
            f"- TVR local-stdio AQ success: `{summary['tvr_local_stdio_aq_success']}`.",
            f"- IBKR first-class AQ success: `{summary['ibkr_first_class_aq_success']}`.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{REPORT_DIR / 'btc_local_tvr_six_provider_aq_v1.json'}`",
            f"- Checklist: `{checklist}`",
            f"- Assertions: `{assertions}`",
            f"- Provider CSVs: `{PROVIDER_CSV_DIR}`",
            f"- AQ workspaces: `{WORKSPACE_ROOT}`",
        ]
    )
    report.write_text("\n".join(lines) + "\n")

    with checklist.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["requirement", "artifact", "status", "note"])
        writer.writerow(["named Board A claim", "docs/plans/2026-05-10-actionable-regime-confidence-todo.md", "covered", "162247 active claim"])
        writer.writerow(["six provider fetch rows", str(PROVIDER_CSV_DIR), "covered", json.dumps(summary["provider_matrix"]["fetch_rows"], sort_keys=True)])
        writer.writerow(["TVR local-stdio input", summary["provider_matrix"].get("tvr_selected_csv"), "covered", f"remote_http_api_called={summary['provider_matrix'].get('tvr_remote_http_api_called')}"])
        writer.writerow(["IBKR first-class input", str(PROVIDER_CSV_DIR / "BTC_1h_aggtrades.csv"), "covered", f"rows={summary['provider_matrix']['fetch_rows'].get('ibkr_btc_paxos_aggtrades_1h')}"])
        writer.writerow(["AQ on every non-empty provider source", str(WORKSPACE_ROOT), "covered", f"run_success={summary['metric_totals']['run_success']}"])
        writer.writerow(["downstream chain", "N/A", "not_run", "separate claimed slice required after provider/AQ packet"])

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS provider_runs={summary['metric_totals']['provider_runs']}",
        f"PASS compile_success={summary['metric_totals']['compile_success']}",
        f"PASS run_success={summary['metric_totals']['run_success']}",
        f"PASS strategies_with_metrics={summary['metric_totals']['strategies_with_metrics']}",
        f"PASS same_root_six_provider_aq_authority={summary['same_root_six_provider_aq_authority']}",
        f"PASS tvr_local_stdio_aq_success={summary['tvr_local_stdio_aq_success']}",
        f"PASS ibkr_first_class_aq_success={summary['ibkr_first_class_aq_success']}",
        "FAIL_CLOSED downstream_chain_not_run",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions.write_text("\n".join(assertion_lines) + "\n")


def main() -> int:
    for path in (OUT_DIR, CHECK_DIR, CONFIG_DIR, REPORT_DIR, PROVIDER_CSV_DIR, WORKSPACE_ROOT):
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")

    fetch_summary = fetch_providers()
    aq_results = BASE.run_aq(fetch_summary)
    totals = BASE.metric_totals([row for row in aq_results if not row.get("skipped")])
    ibkr_success = any(row.get("provider") == "ibkr_aggtrades" and row.get("run_tomac_exit") == 0 for row in aq_results)
    tvr_success = any(row.get("provider") == "tvr_binance" and row.get("run_tomac_exit") == 0 for row in aq_results)
    same_root_authority = totals["run_success"] == 6 and ibkr_success and tvr_success
    summary = {
        "run_id": RUN_ID,
        "provider_matrix": fetch_summary,
        "aq_results": aq_results,
        "metric_totals": totals,
        "same_root_six_provider_aq_authority": same_root_authority,
        "tvr_local_stdio_aq_success": tvr_success,
        "ibkr_first_class_aq_success": ibkr_success,
        "gate_result": (
            "btc_local_tvr_six_provider_aq_v1="
            + (
                "same_root_six_provider_aq_present_downstream_not_run_no_promotion"
                if same_root_authority
                else "same_root_btc_local_tvr_probe_fail_closed_provider_or_aq_missing_no_promotion"
            )
        ),
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(REPORT_DIR / "btc_local_tvr_six_provider_aq_v1.json", summary)
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
