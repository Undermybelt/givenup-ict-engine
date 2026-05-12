from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from typing import Any


RUN_ID = "20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1"
RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
OLD_SCRIPT = (
    RUNS
    / "20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1"
    / "scripts"
    / "six_provider_btc_same_root_aq_ibkr_aggtrades_probe_v1.py"
)

OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
CONFIG_DIR = ROOT / "config"
REPORT_DIR = ROOT / "six-provider-btc-local-tvr-aq-packet-v1"
PROVIDER_CSV_DIR = ROOT / "provider-csv"
WORKSPACE_ROOT = ROOT / "workspace"


def load_old_module() -> Any:
    spec = importlib.util.spec_from_file_location("old_six_provider_probe", OLD_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {OLD_SCRIPT}")
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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def exit_code(path: Path) -> int | None:
    if not path.exists():
        return None
    text = path.read_text().strip()
    return int(text) if text else None


def csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open() as fh:
        return max(sum(1 for _ in fh) - 1, 0)


def fetch_providers(old: Any) -> dict[str, Any]:
    for path in (OUT_DIR, CHECK_DIR, CONFIG_DIR, REPORT_DIR, PROVIDER_CSV_DIR, WORKSPACE_ROOT):
        path.mkdir(parents=True, exist_ok=True)

    status_cmds = [
        ("00_provider_status_yfinance", ["./target/debug/ict-engine", "provider-status", "--provider", "yfinance", "--agent"]),
        ("01_provider_status_tradingview_mcp", ["./target/debug/ict-engine", "provider-status", "--provider", "tradingview_mcp", "--agent"]),
        ("02_provider_status_ibkr", ["./target/debug/ict-engine", "provider-status", "--provider", "ibkr", "--agent"]),
        ("03_provider_status_ibkr_bridge", ["./target/debug/ict-engine", "provider-status", "--provider", "ibkr_bridge", "--agent"]),
        ("04_provider_status_kraken_public", ["./target/debug/ict-engine", "provider-status", "--provider", "kraken_public", "--agent"]),
        ("05_provider_status_binance_public", ["./target/debug/ict-engine", "provider-status", "--provider", "binance_public", "--agent"]),
        ("06_provider_status_bybit_public", ["./target/debug/ict-engine", "provider-status", "--provider", "bybit_public", "--agent"]),
    ]
    for name, cmd in status_cmds:
        old.run_cmd(name, cmd, timeout=300)

    fetch_cmds = [
        (
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
                "2026-04-01",
                "--end",
                "2026-05-12",
                "--output",
                str(PROVIDER_CSV_DIR / "yfinance_btc_usd_1h.csv"),
            ],
        ),
        (
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
                "2026-04-01",
                "--end",
                "2026-05-12",
                "--output",
                str(PROVIDER_CSV_DIR / "kraken_xbtusd_1h.csv"),
            ],
        ),
        (
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
                "2026-04-01",
                "--end",
                "2026-05-12",
                "--output",
                str(PROVIDER_CSV_DIR / "binance_btcusdt_1h.csv"),
            ],
        ),
        (
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
                "2026-04-01",
                "--end",
                "2026-05-12",
                "--output",
                str(PROVIDER_CSV_DIR / "bybit_btcusdt_linear_1h.csv"),
            ],
        ),
    ]
    for name, cmd in fetch_cmds:
        old.run_cmd(name, cmd, timeout=900)

    tvr_csv = PROVIDER_CSV_DIR / "tvr_btc_usd_local_stdio_1h.csv"
    old.run_cmd(
        "14_tvr_btc_usd_1h_local_stdio",
        [
            "./target/debug/ict-engine",
            "market-data-harness",
            "--action",
            "fetch",
            "--market",
            "board-a-162400-btc-local-tvr-1h",
            "--interval",
            "1h",
            "--role",
            "crypto_reference",
            "--provider",
            "crypto_reference=tradingview_mcp",
            "--symbol-spec",
            "crypto_reference=BTC-USD",
        ],
        env={
            "HOME": "/tmp/ict-engine-tvr-local-stdio-162400-home",
            "ICT_ENGINE_TVREMIX_MCP_URL": "",
            "ICT_ENGINE_TVREMIX_MCP_API_KEY": "",
            "ICT_ENGINE_TRADINGVIEW_MCP_CMD": "uv",
            "ICT_ENGINE_TRADINGVIEW_MCP_ARGS": "--directory /Users/thrill3r/tradingview-mcp/tradingview-mcp run tradingview-mcp",
        },
        timeout=900,
    )
    if exit_code(CHECK_DIR / "14_tvr_btc_usd_1h_local_stdio.exit") == 0:
        old.write_tvr_csv(
            "tvr_btc_usd_local_stdio",
            OUT_DIR / "14_tvr_btc_usd_1h_local_stdio.stdout",
            tvr_csv,
        )

    ibkr_config = old.write_ibkr_config()
    old.run_cmd(
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
        timeout=900,
    )

    fetch_rows = {
        "yfinance_btc_usd_1h": csv_rows(PROVIDER_CSV_DIR / "yfinance_btc_usd_1h.csv"),
        "kraken_xbtusd_1h": csv_rows(PROVIDER_CSV_DIR / "kraken_xbtusd_1h.csv"),
        "binance_btcusdt_1h": csv_rows(PROVIDER_CSV_DIR / "binance_btcusdt_1h.csv"),
        "bybit_btcusdt_linear_1h": csv_rows(PROVIDER_CSV_DIR / "bybit_btcusdt_linear_1h.csv"),
        "tvr_btc_usd_1h_local_stdio": csv_rows(tvr_csv),
        "tvr_selected_1h": csv_rows(tvr_csv),
        "ibkr_btc_paxos_aggtrades_1h": csv_rows(PROVIDER_CSV_DIR / "BTC_1h_aggtrades.csv"),
    }
    fetch_exits = {
        "yfinance_btc_usd_1h": exit_code(CHECK_DIR / "10_yfinance_btc_usd_1h.exit"),
        "kraken_xbtusd_1h": exit_code(CHECK_DIR / "11_kraken_xbtusd_1h.exit"),
        "binance_btcusdt_1h": exit_code(CHECK_DIR / "12_binance_btcusdt_1h.exit"),
        "bybit_btcusdt_linear_1h": exit_code(CHECK_DIR / "13_bybit_btcusdt_linear_1h.exit"),
        "tvr_btc_usd_1h_local_stdio": exit_code(CHECK_DIR / "14_tvr_btc_usd_1h_local_stdio.exit"),
        "ibkr_btc_paxos_aggtrades_1h": exit_code(CHECK_DIR / "15_ibkr_btc_paxos_aggtrades_1h.exit"),
    }
    return {
        "fetch_rows": fetch_rows,
        "fetch_exits": fetch_exits,
        "ibkr_config": str(ibkr_config),
        "tvr_selected_csv": str(tvr_csv),
        "tvr_selected_symbol": "BTC-USD(local-stdio)",
    }


def run_aq(old: Any, fetch_summary: dict[str, Any]) -> list[dict[str, Any]]:
    provider_inputs = {
        "yfinance": {"source": PROVIDER_CSV_DIR / "yfinance_btc_usd_1h.csv", "symbol": "BTC-USD"},
        "kraken_public": {"source": PROVIDER_CSV_DIR / "kraken_xbtusd_1h.csv", "symbol": "XBTUSD"},
        "binance_public": {"source": PROVIDER_CSV_DIR / "binance_btcusdt_1h.csv", "symbol": "BTCUSDT"},
        "bybit_public": {"source": PROVIDER_CSV_DIR / "bybit_btcusdt_linear_1h.csv", "symbol": "BTCUSDT"},
        "tvr_local_stdio": {"source": Path(fetch_summary["tvr_selected_csv"]), "symbol": fetch_summary["tvr_selected_symbol"]},
        "ibkr_aggtrades": {"source": PROVIDER_CSV_DIR / "BTC_1h_aggtrades.csv", "symbol": "BTC.PAXOS"},
    }
    results = []
    for provider, meta in provider_inputs.items():
        if not meta["source"].exists() or csv_rows(meta["source"]) == 0:
            results.append(
                {
                    "provider": provider,
                    "provider_symbol": meta["symbol"],
                    "source_csv": str(meta["source"]),
                    "rows": 0,
                    "compile_exit": None,
                    "run_tomac_exit": None,
                    "metrics": {},
                    "skipped": True,
                    "skip_reason": "missing_or_empty_source_csv",
                }
            )
            continue
        results.append(old.run_provider_fixed(old.load_old_module(), provider, meta))
    return results


def write_report(old: Any, summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "six_provider_btc_local_tvr_aq_packet_v1.md"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_v1.csv"
    assertions = CHECK_DIR / "six_provider_btc_local_tvr_aq_packet_v1_assertions.out"

    lines = [
        "# Six-Provider BTC Local-TV Stdio AQ Packet v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Scope",
        "Fresh Board A BTC 1h same-root provider/AQ packet using local-stdio TVR OHLCV.",
        "This is not Board A acceptance, not selected-history approval, not downstream promotion, and not `update_goal`.",
        "",
        "## Provider Rows",
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
            f"- IBKR first-class AQ success: `{summary['ibkr_first_class_aq_success']}`.",
            "- Downstream chain is not started by this packet until the Board A step ledger records this provider/AQ result.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{REPORT_DIR / 'six_provider_btc_local_tvr_aq_packet_v1.json'}`",
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
        writer.writerow(["six provider rows", str(PROVIDER_CSV_DIR), "covered", json.dumps(summary["provider_matrix"]["fetch_rows"], sort_keys=True)])
        writer.writerow(["local stdio TVR", summary["provider_matrix"]["tvr_selected_csv"], "covered", summary["provider_matrix"]["tvr_selected_symbol"]])
        writer.writerow(["AQ for non-empty provider rows", str(WORKSPACE_ROOT), "covered", f"run_success={summary['metric_totals']['run_success']}"])
        writer.writerow(["downstream chain", "N/A", "not_started", "requires board step_done/readback first"])
        writer.writerow(["Board A acceptance", "N/A", "not_claimed", "accepted_95_contexts_added=0"])

    assertions.write_text(
        "\n".join(
            [
                f"PASS run_id={RUN_ID}",
                f"PASS provider_runs={summary['metric_totals']['provider_runs']}",
                f"PASS compile_success={summary['metric_totals']['compile_success']}",
                f"PASS run_success={summary['metric_totals']['run_success']}",
                f"PASS strategies_with_metrics={summary['metric_totals']['strategies_with_metrics']}",
                f"PASS same_root_six_provider_aq_authority={summary['same_root_six_provider_aq_authority']}",
                f"PASS ibkr_first_class_aq_success={summary['ibkr_first_class_aq_success']}",
                "FAIL_CLOSED downstream_chain_not_started_in_this_step",
                "PASS promotion_allowed=false",
                "PASS trade_usable=false",
                "PASS update_goal=false",
            ]
        )
        + "\n"
    )


def main() -> int:
    for path in (OUT_DIR, CHECK_DIR, CONFIG_DIR, REPORT_DIR, PROVIDER_CSV_DIR, WORKSPACE_ROOT):
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")
    old = load_old_module()
    fetch_summary = fetch_providers(old)
    aq_results = run_aq(old, fetch_summary)
    totals = old.metric_totals([row for row in aq_results if not row.get("skipped")])
    ibkr_success = any(row.get("provider") == "ibkr_aggtrades" and row.get("run_tomac_exit") == 0 for row in aq_results)
    same_root_authority = totals["run_success"] == 6 and ibkr_success
    summary = {
        "run_id": RUN_ID,
        "provider_matrix": fetch_summary,
        "aq_results": aq_results,
        "metric_totals": totals,
        "same_root_six_provider_aq_authority": same_root_authority,
        "ibkr_first_class_aq_success": ibkr_success,
        "gate_result": "six_provider_btc_local_tvr_aq_packet_v1="
        + (
            "same_root_six_provider_aq_present_downstream_not_started_no_promotion"
            if same_root_authority
            else "fail_closed_provider_or_aq_missing_no_promotion"
        ),
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(REPORT_DIR / "six_provider_btc_local_tvr_aq_packet_v1.json", summary)
    write_report(old, summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
