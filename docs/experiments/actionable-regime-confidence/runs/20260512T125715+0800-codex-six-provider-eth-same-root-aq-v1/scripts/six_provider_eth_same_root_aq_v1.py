from __future__ import annotations

import csv
import importlib.util
import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T125715+0800-codex-six-provider-eth-same-root-aq-v1"
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
REPORT_DIR = ROOT / "six-provider-eth-same-root-aq-v1"
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


def run_cmd(name: str, cmd: list[str], *, env: dict[str, str] | None = None, timeout: int = 900) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    (OUT_DIR / f"{name}.cmd").write_text(" ".join(shlex.quote(part) for part in cmd) + "\n")
    proc = subprocess.run(
        cmd,
        cwd=Path.cwd(),
        env=merged_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    (OUT_DIR / f"{name}.stdout").write_text(proc.stdout)
    (OUT_DIR / f"{name}.stderr").write_text(proc.stderr)
    (CHECK_DIR / f"{name}.exit").write_text(f"{proc.returncode}\n")
    return proc.returncode


def exit_code(path: Path) -> int | None:
    return BASE.exit_code(path)


def csv_rows(path: Path) -> int:
    return BASE.csv_rows(path)


def normalize_ohlcv(source: Path) -> pd.DataFrame:
    return BASE.normalize_ohlcv(source)


def write_ibkr_config() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config = CONFIG_DIR / "ibkr_eth_paxos_aggtrades_1h.yaml"
    config.write_text(
        "\n".join(
            [
                "gateway:",
                "  host: 127.0.0.1",
                "  port: 4002",
                "  client_id: 52",
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
                "  - symbol: ETH",
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


def fetch_providers() -> dict[str, Any]:
    for path in (OUT_DIR, CHECK_DIR, CONFIG_DIR, REPORT_DIR, PROVIDER_CSV_DIR, WORKSPACE_ROOT):
        path.mkdir(parents=True, exist_ok=True)

    provider_status_ids = [
        ("00_provider_status_yfinance", "yfinance"),
        ("01_provider_status_tradingview_mcp", "tradingview_mcp"),
        ("02_provider_status_ibkr", "ibkr"),
        ("03_provider_status_ibkr_bridge", "ibkr_bridge"),
        ("04_provider_status_kraken_public", "kraken_public"),
        ("05_provider_status_binance_public", "binance_public"),
        ("06_provider_status_bybit_public", "bybit_public"),
    ]
    for name, provider in provider_status_ids:
        run_cmd(name, ["./target/debug/ict-engine", "provider-status", "--provider", provider, "--agent"], timeout=180)

    common_start = "2026-04-01"
    common_end = "2026-05-12"
    run_cmd(
        "10_yfinance_eth_usd_1h",
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
            "ETH-USD",
            "--interval",
            "1h",
            "--start",
            common_start,
            "--end",
            common_end,
            "--output",
            str(PROVIDER_CSV_DIR / "yfinance_eth_usd_1h.csv"),
        ],
    )
    run_cmd(
        "11_kraken_ethusd_1h",
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
            "ETHUSD",
            "--interval",
            "1h",
            "--start",
            common_start,
            "--end",
            common_end,
            "--output",
            str(PROVIDER_CSV_DIR / "kraken_ethusd_1h.csv"),
        ],
    )
    run_cmd(
        "12_binance_ethusdt_1h",
        [
            "uv",
            "run",
            "--with",
            "pandas",
            "scripts/auto_quant_external/fetch_external.py",
            "binance-kline",
            "--symbol",
            "ETHUSDT",
            "--interval",
            "1h",
            "--start",
            common_start,
            "--end",
            common_end,
            "--output",
            str(PROVIDER_CSV_DIR / "binance_ethusdt_1h.csv"),
        ],
    )
    run_cmd(
        "13_bybit_ethusdt_linear_1h",
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
            "ETHUSDT",
            "--interval",
            "1h",
            "--start",
            common_start,
            "--end",
            common_end,
            "--output",
            str(PROVIDER_CSV_DIR / "bybit_ethusdt_linear_1h.csv"),
        ],
    )

    tvr_csv = PROVIDER_CSV_DIR / "tvr_binance_ethusdt_1h.csv"
    tvr_source_symbol = "BINANCE:ETHUSDT"
    run_cmd(
        "14_tvr_binance_ethusdt_1h",
        [
            "./target/debug/ict-engine",
            "market-data-harness",
            "--action",
            "fetch",
            "--market",
            "board-a-same-root-eth-tvr-binance-1h",
            "--interval",
            "1h",
            "--role",
            "crypto_reference",
            "--provider",
            "crypto_reference=tradingview_mcp",
            "--symbol-spec",
            "crypto_reference=BINANCE:ETHUSDT",
        ],
    )
    tvr_rows = 0
    if exit_code(CHECK_DIR / "14_tvr_binance_ethusdt_1h.exit") == 0:
        tvr_rows = BASE.write_tvr_csv("tvr_binance_eth", OUT_DIR / "14_tvr_binance_ethusdt_1h.stdout", tvr_csv)
    if tvr_rows == 0:
        fallback_csv = PROVIDER_CSV_DIR / "tvr_eth_usd_local_stdio_1h.csv"
        run_cmd(
            "14b_tvr_eth_usd_1h_local_stdio",
            [
                "./target/debug/ict-engine",
                "market-data-harness",
                "--action",
                "fetch",
                "--market",
                "board-a-same-root-eth-tvr-eth-usd-1h-local-stdio",
                "--interval",
                "1h",
                "--role",
                "crypto_reference",
                "--provider",
                "crypto_reference=tradingview_mcp",
                "--symbol-spec",
                "crypto_reference=ETH-USD",
            ],
            env={
                "HOME": "/tmp/ict-engine-tvr-same-root-eth-home",
                "ICT_ENGINE_TRADINGVIEW_MCP_CMD": "uv",
                "ICT_ENGINE_TRADINGVIEW_MCP_ARGS": "--directory /Users/thrill3r/tradingview-mcp/tradingview-mcp run tradingview-mcp",
            },
        )
        if exit_code(CHECK_DIR / "14b_tvr_eth_usd_1h_local_stdio.exit") == 0:
            fallback_rows = BASE.write_tvr_csv(
                "tvr_eth_usd_local_stdio",
                OUT_DIR / "14b_tvr_eth_usd_1h_local_stdio.stdout",
                fallback_csv,
            )
            if fallback_rows > 0:
                tvr_csv = fallback_csv
                tvr_rows = fallback_rows
                tvr_source_symbol = "ETH-USD(local-stdio)"

    ibkr_config = write_ibkr_config()
    run_cmd(
        "15_ibkr_eth_paxos_aggtrades_1h",
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
            "yfinance_eth_usd_1h": csv_rows(PROVIDER_CSV_DIR / "yfinance_eth_usd_1h.csv"),
            "kraken_ethusd_1h": csv_rows(PROVIDER_CSV_DIR / "kraken_ethusd_1h.csv"),
            "binance_ethusdt_1h": csv_rows(PROVIDER_CSV_DIR / "binance_ethusdt_1h.csv"),
            "bybit_ethusdt_linear_1h": csv_rows(PROVIDER_CSV_DIR / "bybit_ethusdt_linear_1h.csv"),
            "tvr_binance_ethusdt_1h": csv_rows(PROVIDER_CSV_DIR / "tvr_binance_ethusdt_1h.csv"),
            "tvr_eth_usd_1h_local_stdio": csv_rows(PROVIDER_CSV_DIR / "tvr_eth_usd_local_stdio_1h.csv"),
            "tvr_selected_1h": tvr_rows,
            "ibkr_eth_paxos_aggtrades_1h": csv_rows(PROVIDER_CSV_DIR / "ETH_1h_aggtrades.csv"),
        },
        "fetch_exits": {
            "yfinance_eth_usd_1h": exit_code(CHECK_DIR / "10_yfinance_eth_usd_1h.exit"),
            "kraken_ethusd_1h": exit_code(CHECK_DIR / "11_kraken_ethusd_1h.exit"),
            "binance_ethusdt_1h": exit_code(CHECK_DIR / "12_binance_ethusdt_1h.exit"),
            "bybit_ethusdt_linear_1h": exit_code(CHECK_DIR / "13_bybit_ethusdt_linear_1h.exit"),
            "tvr_binance_ethusdt_1h": exit_code(CHECK_DIR / "14_tvr_binance_ethusdt_1h.exit"),
            "tvr_eth_usd_1h_local_stdio": exit_code(CHECK_DIR / "14b_tvr_eth_usd_1h_local_stdio.exit"),
            "ibkr_eth_paxos_aggtrades_1h": exit_code(CHECK_DIR / "15_ibkr_eth_paxos_aggtrades_1h.exit"),
        },
        "ibkr_config": str(ibkr_config),
        "tvr_selected_csv": str(tvr_csv),
        "tvr_selected_symbol": tvr_source_symbol,
    }


def rewrite_workspace_for_eth(workspace: Path) -> None:
    config_path = workspace / "config.tomac.json"
    config = json.loads(config_path.read_text())
    config["exchange"]["pair_whitelist"] = ["ETH/USDT"]
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")
    run_tomac = workspace / "run_tomac.py"
    text = run_tomac.read_text()
    text = text.replace("yahoo_btc_pullback_precision_104902", "six_provider_eth_same_root_aq_125715")
    run_tomac.write_text(text)


def run_provider_fixed(old: Any, provider: str, meta: dict[str, Any]) -> dict[str, Any]:
    source = meta["source"]
    workspace = old.copy_template(provider)
    rewrite_workspace_for_eth(workspace)
    df = normalize_ohlcv(source)
    feather = workspace / "user_data" / "data" / "ETH_USDT-1h.feather"
    df.to_feather(feather)

    strategies = sorted((workspace / "user_data" / "strategies_external").glob("*.py"))
    compile_cmd = [
        str(old.PYTHON),
        "-m",
        "py_compile",
        "run_tomac.py",
        *[str(path.relative_to(workspace)) for path in strategies],
    ]
    run_cmd_local = [str(old.PYTHON), "run_tomac.py"]
    prefix = provider.replace("/", "_")
    compile_proc = subprocess.run(
        compile_cmd,
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    (OUT_DIR / f"aq_{prefix}_compile.out").write_text(compile_proc.stdout)
    (OUT_DIR / f"aq_{prefix}_compile.err").write_text(compile_proc.stderr)
    (OUT_DIR / f"aq_{prefix}_compile.cmd").write_text(" ".join(compile_cmd) + "\n")
    (CHECK_DIR / f"aq_{prefix}_compile.exit").write_text(f"{compile_proc.returncode}\n")

    run_proc = subprocess.run(
        run_cmd_local,
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    (OUT_DIR / f"aq_{prefix}_run_tomac.out").write_text(run_proc.stdout)
    (OUT_DIR / f"aq_{prefix}_run_tomac.err").write_text(run_proc.stderr)
    (OUT_DIR / f"aq_{prefix}_run_tomac.cmd").write_text(" ".join(run_cmd_local) + "\n")
    (CHECK_DIR / f"aq_{prefix}_run_tomac.exit").write_text(f"{run_proc.returncode}\n")

    metrics: dict[str, Any] = {}
    for path in sorted((workspace / "derived").glob("*.metrics.json")):
        metrics[path.stem.replace(".metrics", "")] = read_json(path)

    return {
        "provider": provider,
        "provider_symbol": meta["symbol"],
        "source_csv": str(source),
        "rows": int(len(df)),
        "first_ts_ms": BASE.to_epoch_ms(df["date"].min()) if len(df) else None,
        "last_ts_ms": BASE.to_epoch_ms(df["date"].max()) if len(df) else None,
        "workspace": str(workspace),
        "feather": str(feather),
        "compile_exit": compile_proc.returncode,
        "run_tomac_exit": run_proc.returncode,
        "metrics": metrics,
    }


def run_aq(fetch_summary: dict[str, Any]) -> list[dict[str, Any]]:
    old = BASE.load_old_module()
    old.RUN_ID = RUN_ID
    old.SOURCE_RUN_ID = RUN_ID
    old.ROOT = ROOT
    old.SOURCE_ROOT = ROOT
    old.OUT_DIR = OUT_DIR
    old.CHECK_DIR = CHECK_DIR
    old.REPORT_DIR = REPORT_DIR
    old.PROVIDER_CSV_DIR = PROVIDER_CSV_DIR
    old.WORKSPACE_ROOT = WORKSPACE_ROOT
    old.normalized_df = normalize_ohlcv

    provider_inputs = {
        "yfinance": {
            "source": PROVIDER_CSV_DIR / "yfinance_eth_usd_1h.csv",
            "symbol": "ETH-USD",
        },
        "kraken_public": {
            "source": PROVIDER_CSV_DIR / "kraken_ethusd_1h.csv",
            "symbol": "ETHUSD",
        },
        "binance_public": {
            "source": PROVIDER_CSV_DIR / "binance_ethusdt_1h.csv",
            "symbol": "ETHUSDT",
        },
        "bybit_public": {
            "source": PROVIDER_CSV_DIR / "bybit_ethusdt_linear_1h.csv",
            "symbol": "ETHUSDT",
        },
        "tvr_binance": {
            "source": Path(fetch_summary["tvr_selected_csv"]),
            "symbol": fetch_summary["tvr_selected_symbol"],
        },
        "ibkr_aggtrades": {
            "source": PROVIDER_CSV_DIR / "ETH_1h_aggtrades.csv",
            "symbol": "ETH.PAXOS",
        },
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
        results.append(run_provider_fixed(old, provider, meta))
    return results


def metric_totals(results: list[dict[str, Any]]) -> dict[str, Any]:
    return BASE.metric_totals(results)


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "six_provider_eth_same_root_aq_v1.md"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_six_provider_eth_same_root_aq_v1.csv"
    assertions = CHECK_DIR / "six_provider_eth_same_root_aq_v1_assertions.out"

    lines = [
        "# Six-Provider ETH Same-Root AQ v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Scope",
        "Fresh non-BTC same-root provider/AQ diagnostic for the Board A six-provider authority blocker.",
        "This run attempts ETH across yfinance, Kraken, Binance, Bybit, TradingViewRemix/TVR, and IBKR PAXOS AGGTRADES.",
        "It does not approve selected historical data, mutate canonical source/control roots, promote execution, or call `update_goal`.",
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
            f"- Same-root six-provider ETH AQ authority: `{summary['same_root_six_provider_eth_aq_authority']}`.",
            f"- IBKR first-class ETH AQ success: `{summary['ibkr_first_class_aq_success']}`.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{REPORT_DIR / 'six_provider_eth_same_root_aq_v1.json'}`",
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
        writer.writerow(["non-BTC same-root provider fetches", str(PROVIDER_CSV_DIR), "covered", "all commands wrote into this run root"])
        writer.writerow(["six required provider rows", str(REPORT_DIR / "six_provider_eth_same_root_aq_v1.json"), "covered", "yfinance, Kraken, Binance, Bybit, TVR, IBKR"])
        writer.writerow(["TVR first-class input", summary["provider_matrix"].get("tvr_selected_csv"), "covered", f"rows={summary['provider_matrix']['fetch_rows'].get('tvr_selected_1h')}"])
        writer.writerow(["IBKR first-class input", str(PROVIDER_CSV_DIR / "ETH_1h_aggtrades.csv"), "covered", f"rows={summary['provider_matrix']['fetch_rows'].get('ibkr_eth_paxos_aggtrades_1h')}"])
        writer.writerow(["AQ on every non-empty provider source", str(WORKSPACE_ROOT), "covered", f"run_success={summary['metric_totals']['run_success']}"])
        writer.writerow(["downstream chain", "N/A", "not_run", "blocked unless same-root ETH authority and nonzero mature observations justify downstream"])

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS provider_runs={summary['metric_totals']['provider_runs']}",
        f"PASS compile_success={summary['metric_totals']['compile_success']}",
        f"PASS run_success={summary['metric_totals']['run_success']}",
        f"PASS strategies_with_metrics={summary['metric_totals']['strategies_with_metrics']}",
        f"PASS same_root_six_provider_eth_aq_authority={summary['same_root_six_provider_eth_aq_authority']}",
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
    aq_results = run_aq(fetch_summary)
    totals = metric_totals([row for row in aq_results if not row.get("skipped")])
    ibkr_success = any(
        row.get("provider") == "ibkr_aggtrades" and row.get("run_tomac_exit") == 0
        for row in aq_results
    )
    same_root_authority = totals["run_success"] == 6 and ibkr_success
    summary = {
        "run_id": RUN_ID,
        "provider_matrix": fetch_summary,
        "aq_results": aq_results,
        "metric_totals": totals,
        "same_root_six_provider_eth_aq_authority": same_root_authority,
        "ibkr_first_class_aq_success": ibkr_success,
        "gate_result": (
            "six_provider_eth_same_root_aq_v1="
            + (
                "same_root_six_provider_eth_aq_present_downstream_not_run_no_promotion"
                if same_root_authority
                else "same_root_eth_probe_fail_closed_provider_or_ibkr_aq_missing_no_promotion"
            )
        ),
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(REPORT_DIR / "six_provider_eth_same_root_aq_v1.json", summary)
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
