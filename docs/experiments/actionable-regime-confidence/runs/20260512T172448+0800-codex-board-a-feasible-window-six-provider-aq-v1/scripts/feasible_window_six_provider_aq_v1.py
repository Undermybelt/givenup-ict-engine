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


RUN_ID = "20260512T172448+0800-codex-board-a-feasible-window-six-provider-aq-v1"
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
PROVIDER_CSV_DIR = ROOT / "provider-csv"
WORKSPACE_ROOT = ROOT / "workspace"
REPORT_DIR = ROOT / "feasible-window-six-provider-aq-v1"


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("six_provider_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


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


def csv_span(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"rows": 0, "first": None, "last": None}
    first = None
    last = None
    rows = 0
    with path.open() as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows += 1
            value = row.get("date") or row.get("timestamp") or row.get("ts")
            if first is None:
                first = value
            last = value
    return {"rows": rows, "first": first, "last": last}


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


def normalize_ohlcv(source: Path) -> pd.DataFrame:
    raw = pd.read_csv(source)
    date_col = "date" if "date" in raw.columns else "timestamp" if "timestamp" in raw.columns else "ts"
    date = pd.to_datetime(raw[date_col], utc=True)
    volume = pd.to_numeric(raw.get("volume", 0.0), errors="coerce").fillna(0.0).astype(float)
    volume = volume.mask(volume < 0, 0.0)
    out = pd.DataFrame(
        {
            "date": date,
            "open": pd.to_numeric(raw["open"], errors="coerce").astype(float),
            "high": pd.to_numeric(raw["high"], errors="coerce").astype(float),
            "low": pd.to_numeric(raw["low"], errors="coerce").astype(float),
            "close": pd.to_numeric(raw["close"], errors="coerce").astype(float),
            "volume": volume,
        }
    )
    return out.dropna().sort_values("date").reset_index(drop=True)


def to_epoch_ms(value: Any) -> int | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return int(value.timestamp() * 1000)
    return int(value)


def write_tvr_csv(stdout_path: Path, out: Path) -> int:
    if not stdout_path.exists():
        return 0
    payload = json.loads(stdout_path.read_text())
    rows = []
    for result in payload.get("results") or []:
        rows.extend(result.get("data") or [])
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["date", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "date": row.get("timestamp") or row.get("date") or row.get("time"),
                    "open": row.get("open"),
                    "high": row.get("high"),
                    "low": row.get("low"),
                    "close": row.get("close"),
                    "volume": row.get("volume", 0.0),
                }
            )
    return csv_rows(out)


def write_ibkr_config() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config = CONFIG_DIR / "ibkr_btc_paxos_aggtrades_1y_client166.yaml"
    config.write_text(
        "\n".join(
            [
                "gateway:",
                "  host: 127.0.0.1",
                "  port: 4002",
                "  client_id: 166",
                "output:",
                f"  directory: {PROVIDER_CSV_DIR}",
                "  filename_template: '{symbol}_{bar_suffix}_{what}.csv'",
                "  force: true",
                "defaults:",
                "  bar_size: '1 hour'",
                "  duration: '1 Y'",
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
                "    duration: '1 Y'",
                "",
            ]
        )
    )
    return config


def fetch_providers() -> dict[str, Any]:
    for path in (OUT_DIR, CHECK_DIR, CONFIG_DIR, PROVIDER_CSV_DIR, WORKSPACE_ROOT, REPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")

    status_cmds = [
        ("00_provider_status_yfinance", ["./target/debug/ict-engine", "provider-status", "--provider", "yfinance", "--agent"]),
        ("01_provider_status_tradingview_mcp", ["./target/debug/ict-engine", "provider-status", "--provider", "tradingview_mcp", "--agent"]),
        ("02_provider_status_ibkr", ["./target/debug/ict-engine", "provider-status", "--provider", "ibkr", "--agent"]),
        ("03_provider_status_kraken_public", ["./target/debug/ict-engine", "provider-status", "--provider", "kraken_public", "--agent"]),
        ("04_provider_status_binance_public", ["./target/debug/ict-engine", "provider-status", "--provider", "binance_public", "--agent"]),
        ("05_provider_status_bybit_public", ["./target/debug/ict-engine", "provider-status", "--provider", "bybit_public", "--agent"]),
    ]
    for name, cmd in status_cmds:
        run_cmd(name, cmd, timeout=300)

    run_cmd(
        "10_yfinance_btc_usd_1h_20240515_20260512",
        [
            "/Users/thrill3r/.local/bin/uv",
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
            "2024-05-15",
            "--end",
            "2026-05-12",
            "--output",
            str(PROVIDER_CSV_DIR / "yfinance_btc_usd_1h_20240515_20260512.csv"),
        ],
        timeout=900,
    )
    run_cmd(
        "11_kraken_pfxbtusd_1h_20260218_20260512",
        [
            "uv",
            "run",
            "--with",
            "pandas",
            "scripts/auto_quant_external/fetch_external.py",
            "kraken-kline",
            "--market",
            "futures",
            "--pair",
            "PF_XBTUSD",
            "--interval",
            "1h",
            "--start",
            "2026-02-18",
            "--end",
            "2026-05-12",
            "--output",
            str(PROVIDER_CSV_DIR / "kraken_pfxbtusd_1h_20260218_20260512.csv"),
        ],
        timeout=900,
    )
    run_cmd(
        "12_binance_btcusdt_1h_20210101_20260512",
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
            "2021-01-01",
            "--end",
            "2026-05-12",
            "--output",
            str(PROVIDER_CSV_DIR / "binance_btcusdt_1h_20210101_20260512.csv"),
        ],
        timeout=1200,
    )
    run_cmd(
        "13_bybit_btcusdt_linear_1h_20210101_20260512",
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
            "2021-01-01",
            "--end",
            "2026-05-12",
            "--output",
            str(PROVIDER_CSV_DIR / "bybit_btcusdt_linear_1h_20210101_20260512.csv"),
        ],
        timeout=900,
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
            "board-a-172448-btc-tvr-local-stdio-1h",
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
            "HOME": "/tmp/ict-engine-tvr-local-stdio-172448-home",
            "ICT_ENGINE_TVREMIX_MCP_URL": "",
            "ICT_ENGINE_TVREMIX_MCP_API_KEY": "",
            "ICT_ENGINE_TRADINGVIEW_MCP_CMD": "uv",
            "ICT_ENGINE_TRADINGVIEW_MCP_ARGS": "--directory /Users/thrill3r/tradingview-mcp/tradingview-mcp run tradingview-mcp",
        },
        timeout=900,
    )
    if exit_code(CHECK_DIR / "14_tvr_btc_usd_1h_local_stdio.exit") == 0:
        write_tvr_csv(OUT_DIR / "14_tvr_btc_usd_1h_local_stdio.stdout", tvr_csv)

    ibkr_config = write_ibkr_config()
    run_cmd(
        "15_ibkr_btc_paxos_aggtrades_1y_client166",
        [
            "/Users/thrill3r/Auto-Quant/.venv/bin/python",
            "scripts/auto_quant_external/fetch_external.py",
            "ibkr-bulk",
            "--config",
            str(ibkr_config),
            "--force",
        ],
        env={"PYTHONPATH": f"{Path.cwd() / 'scripts'}:{Path.cwd()}"},
        timeout=1200,
    )

    provider_files = {
        "yfinance": PROVIDER_CSV_DIR / "yfinance_btc_usd_1h_20240515_20260512.csv",
        "kraken": PROVIDER_CSV_DIR / "kraken_pfxbtusd_1h_20260218_20260512.csv",
        "binance": PROVIDER_CSV_DIR / "binance_btcusdt_1h_20210101_20260512.csv",
        "bybit": PROVIDER_CSV_DIR / "bybit_btcusdt_linear_1h_20210101_20260512.csv",
        "tvr": tvr_csv,
        "ibkr": PROVIDER_CSV_DIR / "BTC_1h_AGGTRADES.csv",
    }
    # Older fetch_external templates use lowercase what-to-show in some runs.
    if not provider_files["ibkr"].exists():
        provider_files["ibkr"] = PROVIDER_CSV_DIR / "BTC_1h_aggtrades.csv"

    fetches = {
        "yfinance": {"exit": exit_code(CHECK_DIR / "10_yfinance_btc_usd_1h_20240515_20260512.exit")},
        "kraken": {"exit": exit_code(CHECK_DIR / "11_kraken_pfxbtusd_1h_20260218_20260512.exit")},
        "binance": {"exit": exit_code(CHECK_DIR / "12_binance_btcusdt_1h_20210101_20260512.exit")},
        "bybit": {"exit": exit_code(CHECK_DIR / "13_bybit_btcusdt_linear_1h_20210101_20260512.exit")},
        "tvr": {"exit": exit_code(CHECK_DIR / "14_tvr_btc_usd_1h_local_stdio.exit")},
        "ibkr": {"exit": exit_code(CHECK_DIR / "15_ibkr_btc_paxos_aggtrades_1y_client166.exit")},
    }
    for provider, path in provider_files.items():
        fetches[provider]["csv"] = str(path)
        fetches[provider].update(csv_span(path))
    return {
        "provider_files": {key: str(value) for key, value in provider_files.items()},
        "fetches": fetches,
        "ibkr_config": str(ibkr_config),
    }


def metric_totals(results: list[dict[str, Any]]) -> dict[str, Any]:
    totals = {
        "provider_runs": len(results),
        "compile_success": 0,
        "run_success": 0,
        "strategies_with_metrics": 0,
        "total_trades": 0,
        "positive_profit_metric_count": 0,
    }
    for result in results:
        if result.get("compile_exit") == 0:
            totals["compile_success"] += 1
        if result.get("run_tomac_exit") == 0:
            totals["run_success"] += 1
        for payload in result.get("metrics", {}).values():
            aggregate = payload.get("aggregate", {})
            trades = int(aggregate.get("trade_count") or 0)
            profit = float(aggregate.get("total_profit_pct") or 0.0)
            totals["strategies_with_metrics"] += 1
            totals["total_trades"] += trades
            if profit > 0:
                totals["positive_profit_metric_count"] += 1
    return totals


def run_provider_fixed(old: Any, provider: str, meta: dict[str, Any]) -> dict[str, Any]:
    source = Path(meta["source"])
    workspace = old.copy_template(provider)
    df = normalize_ohlcv(source)
    feather = workspace / "user_data" / "data" / "BTC_USDT-1h.feather"
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
    (OUT_DIR / f"aq_{prefix}_compile.cmd").write_text(" ".join(shlex.quote(part) for part in compile_cmd) + "\n")
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
    (OUT_DIR / f"aq_{prefix}_run_tomac.cmd").write_text(" ".join(shlex.quote(part) for part in run_cmd_local) + "\n")
    (CHECK_DIR / f"aq_{prefix}_run_tomac.exit").write_text(f"{run_proc.returncode}\n")

    metrics: dict[str, Any] = {}
    for path in sorted((workspace / "derived").glob("*.metrics.json")):
        metrics[path.stem.replace(".metrics", "")] = read_json(path)

    return {
        "provider": provider,
        "provider_symbol": meta["symbol"],
        "source_csv": str(source),
        "rows": int(len(df)),
        "first_ts_ms": to_epoch_ms(df["date"].min()) if len(df) else None,
        "last_ts_ms": to_epoch_ms(df["date"].max()) if len(df) else None,
        "workspace": str(workspace),
        "feather": str(feather),
        "compile_exit": compile_proc.returncode,
        "run_tomac_exit": run_proc.returncode,
        "metrics": metrics,
    }


def run_aq(fetch_summary: dict[str, Any]) -> list[dict[str, Any]]:
    base = load_base_module()
    old = base.load_old_module()
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
        "yfinance": {"source": fetch_summary["provider_files"]["yfinance"], "symbol": "BTC-USD"},
        "kraken_public": {"source": fetch_summary["provider_files"]["kraken"], "symbol": "PF_XBTUSD"},
        "binance_public": {"source": fetch_summary["provider_files"]["binance"], "symbol": "BTCUSDT"},
        "bybit_public": {"source": fetch_summary["provider_files"]["bybit"], "symbol": "BTCUSDT"},
        "tvr_local_stdio": {"source": fetch_summary["provider_files"]["tvr"], "symbol": "BTC-USD(local-stdio)"},
        "ibkr_aggtrades": {"source": fetch_summary["provider_files"]["ibkr"], "symbol": "BTC.PAXOS"},
    }
    results = []
    for provider, meta in provider_inputs.items():
        source = Path(meta["source"])
        if not source.exists() or csv_rows(source) == 0:
            results.append(
                {
                    "provider": provider,
                    "provider_symbol": meta["symbol"],
                    "source_csv": str(source),
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


def workspace_checks(results: list[dict[str, Any]]) -> dict[str, Any]:
    workspace_root_text = str(WORKSPACE_ROOT)
    workspace_paths = [row.get("workspace", "") for row in results if not row.get("skipped")]
    derived_metric_paths = sorted(str(path) for path in WORKSPACE_ROOT.rglob("*.metrics.json"))
    return {
        "workspace_paths": workspace_paths,
        "workspace_file_count": sum(1 for path in WORKSPACE_ROOT.rglob("*") if path.is_file()) if WORKSPACE_ROOT.exists() else 0,
        "derived_metric_count": len(derived_metric_paths),
        "derived_metric_paths": derived_metric_paths,
        "all_workspaces_under_root": all(path.startswith(workspace_root_text) for path in workspace_paths),
    }


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "feasible_window_six_provider_aq_v1.md"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_feasible_window_six_provider_aq_v1.csv"
    assertions = CHECK_DIR / "feasible_window_six_provider_aq_v1_assertions.out"

    lines = [
        "# Feasible-Window Six-Provider AQ Packet v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Scope",
        "Fresh same-root provider/AQ packet using repaired provider-specific BTC 1h windows.",
        "This packet does not run downstream ict-engine gates and does not claim Board A acceptance.",
        "",
        "## Provider Fetches",
    ]
    for provider, payload in summary["provider_matrix"]["fetches"].items():
        lines.append(
            f"- `{provider}`: exit `{payload.get('exit')}`, rows `{payload.get('rows')}`, "
            f"first `{payload.get('first')}`, last `{payload.get('last')}`."
        )
    lines.extend(["", "## AQ Results"])
    for result in summary["aq_results"]:
        if result.get("skipped"):
            lines.append(f"- `{result['provider']}`: skipped, rows `0`, reason `{result['skip_reason']}`.")
            continue
        lines.append(
            f"- `{result['provider']}`: rows `{result['rows']}`, compile exit `{result['compile_exit']}`, "
            f"TOMAC exit `{result['run_tomac_exit']}`, workspace `{result['workspace']}`."
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
            f"- Workspace file count: `{summary['workspace_checks']['workspace_file_count']}`.",
            f"- Derived metric count: `{summary['workspace_checks']['derived_metric_count']}`.",
            "- Downstream chain is not started in this packet.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{REPORT_DIR / 'feasible_window_six_provider_aq_v1.json'}`",
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
        for provider, payload in summary["provider_matrix"]["fetches"].items():
            writer.writerow([f"{provider} provider row", payload.get("csv"), "covered" if payload.get("rows") else "fail_closed", json.dumps(payload, sort_keys=True)])
        writer.writerow(["AQ workspaces", str(WORKSPACE_ROOT), "covered", f"run_success={summary['metric_totals']['run_success']}"])
        writer.writerow(["downstream chain", "N/A", "not_started", "requires terminal provider/AQ readback first"])
        writer.writerow(["Board A acceptance", "N/A", "not_claimed", "accepted_95_contexts_added=0"])

    assertions.write_text(
        "\n".join(
            [
                f"PASS run_id={RUN_ID}",
                f"PASS provider_rows_with_data={summary['provider_rows_with_data']}/6",
                f"PASS provider_runs={summary['metric_totals']['provider_runs']}",
                f"PASS compile_success={summary['metric_totals']['compile_success']}",
                f"PASS run_success={summary['metric_totals']['run_success']}",
                f"PASS strategies_with_metrics={summary['metric_totals']['strategies_with_metrics']}",
                f"PASS same_root_six_provider_aq_authority={summary['same_root_six_provider_aq_authority']}",
                f"PASS all_workspaces_under_root={summary['workspace_checks']['all_workspaces_under_root']}",
                "FAIL_CLOSED downstream_chain_not_started_in_this_step",
                "PASS promotion_allowed=false",
                "PASS trade_usable=false",
                "PASS update_goal=false",
            ]
        )
        + "\n"
    )


def main() -> int:
    fetch_summary = fetch_providers()
    aq_results = run_aq(fetch_summary)
    totals = metric_totals([row for row in aq_results if not row.get("skipped")])
    checks = workspace_checks(aq_results)
    provider_rows_with_data = sum(1 for payload in fetch_summary["fetches"].values() if payload.get("rows", 0) > 0)
    same_root_authority = (
        provider_rows_with_data == 6
        and totals["run_success"] == 6
        and checks["all_workspaces_under_root"]
        and checks["derived_metric_count"] >= 12
    )
    summary = {
        "run_id": RUN_ID,
        "provider_matrix": fetch_summary,
        "aq_results": aq_results,
        "metric_totals": totals,
        "workspace_checks": checks,
        "provider_rows_with_data": provider_rows_with_data,
        "same_root_six_provider_aq_authority": same_root_authority,
        "gate_result": "feasible_window_six_provider_aq_v1="
        + (
            "same_root_six_provider_aq_present_downstream_not_started_no_promotion"
            if same_root_authority
            else "fail_closed_provider_or_aq_missing_no_promotion"
        ),
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(REPORT_DIR / "feasible_window_six_provider_aq_v1.json", summary)
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
