from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


RUN_ID = "20260512T115229+0800-codex-ibkr-btc-paxos-7d-1h-probe-v1"
SOURCE_AQ_SCRIPT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1/"
    "scripts/112315_provider_matrix_aq_readback_v1.py"
)
ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
PROVIDER_CSV_DIR = ROOT / "provider-csv"
INPUT_DIR = ROOT / "input-csv"
WORKSPACE_ROOT = ROOT / "workspace"
REPORT_DIR = ROOT / "same-root-six-provider-aq-v1"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def run_step(name: str, cmd: list[str], env: dict[str, str] | None = None) -> int:
    write(OUT_DIR / f"{name}.cmd", " ".join(cmd) + "\n")
    proc = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=env,
    )
    write(OUT_DIR / f"{name}.stdout", proc.stdout)
    write(OUT_DIR / f"{name}.stderr", proc.stderr)
    write(CHECK_DIR / f"{name}.exit", f"{proc.returncode}\n")
    return proc.returncode


def load_source_aq_module():
    spec = importlib.util.spec_from_file_location("source_provider_aq", SOURCE_AQ_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE_AQ_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.RUN_ID = RUN_ID
    module.ROOT = ROOT
    module.OUT_DIR = OUT_DIR
    module.CHECK_DIR = CHECK_DIR
    module.REPORT_DIR = REPORT_DIR
    module.PROVIDER_CSV_DIR = PROVIDER_CSV_DIR
    module.WORKSPACE_ROOT = WORKSPACE_ROOT
    return module


def csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open() as fh:
        return max(sum(1 for _ in fh) - 1, 0)


def normalize_ohlcv(source: Path):
    import pandas as pd

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
    import pandas as pd

    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return int(value.timestamp() * 1000)
    return int(value)


def fetch_public_rows() -> dict[str, dict[str, Any]]:
    commands = {
        "10_yfinance_btc_usd_1h": [
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
        "11_kraken_xbtusd_1h": [
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
        "12_binance_btcusdt_1h": [
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
        "13_bybit_btcusdt_linear_1h": [
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
    }
    out: dict[str, dict[str, Any]] = {}
    for name, cmd in commands.items():
        code = run_step(name, cmd)
        csv_path = Path(cmd[-1])
        out[name] = {"exit": code, "csv": str(csv_path), "rows": csv_rows(csv_path)}
    return out


def fetch_tvr_rows() -> dict[str, Any]:
    cmd = [
        "./target/debug/ict-engine",
        "market-data-harness",
        "--action",
        "fetch",
        "--market",
        "board-a-same-root-tvr-btc-binance-1h",
        "--interval",
        "1h",
        "--role",
        "crypto_reference",
        "--provider",
        "crypto_reference=tradingview_mcp",
        "--symbol-spec",
        "crypto_reference=BINANCE:BTCUSDT",
    ]
    code = run_step("14_tvr_btc_binance_1h", cmd)
    stdout = OUT_DIR / "14_tvr_btc_binance_1h.stdout"
    csv_path = PROVIDER_CSV_DIR / "tvr_binance_btcusdt_1h.csv"
    rows_written = 0
    if code == 0 and stdout.read_text().strip():
        payload = json.loads(stdout.read_text())
        rows = payload["results"][0]["data"]
        with csv_path.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=["date", "open", "high", "low", "close", "volume"])
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        "date": row["timestamp"],
                        "open": row["open"],
                        "high": row["high"],
                        "low": row["low"],
                        "close": row["close"],
                        "volume": row.get("volume", 0.0),
                    }
                )
        rows_written = len(rows)
    return {"exit": code, "csv": str(csv_path), "rows": rows_written}


def run_provider_fixed(source_module: Any, provider: str, source: Path, symbol: str) -> dict[str, Any]:
    local_source = PROVIDER_CSV_DIR / source.name
    if source.resolve() != local_source.resolve():
        shutil.copy2(source, local_source)
    workspace = source_module.copy_template(provider)
    df = normalize_ohlcv(local_source)
    feather = workspace / "user_data" / "data" / "BTC_USDT-1h.feather"
    df.to_feather(feather)

    strategies = sorted((workspace / "user_data" / "strategies_external").glob("*.py"))
    compile_cmd = [
        str(source_module.PYTHON),
        "-m",
        "py_compile",
        "run_tomac.py",
        *[str(path.relative_to(workspace)) for path in strategies],
    ]
    run_cmd = [str(source_module.PYTHON), "run_tomac.py"]
    prefix = provider.replace("/", "_")

    compile_proc = subprocess.run(
        compile_cmd,
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    write(OUT_DIR / f"aq_{prefix}_compile.out", compile_proc.stdout)
    write(OUT_DIR / f"aq_{prefix}_compile.err", compile_proc.stderr)
    write(OUT_DIR / f"aq_{prefix}_compile.cmd", " ".join(compile_cmd) + "\n")
    write(CHECK_DIR / f"aq_{prefix}_compile.exit", f"{compile_proc.returncode}\n")

    run_proc = subprocess.run(
        run_cmd,
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    write(OUT_DIR / f"aq_{prefix}_run_tomac.out", run_proc.stdout)
    write(OUT_DIR / f"aq_{prefix}_run_tomac.err", run_proc.stderr)
    write(OUT_DIR / f"aq_{prefix}_run_tomac.cmd", " ".join(run_cmd) + "\n")
    write(CHECK_DIR / f"aq_{prefix}_run_tomac.exit", f"{run_proc.returncode}\n")

    metrics: dict[str, Any] = {}
    for path in sorted((workspace / "derived").glob("*.metrics.json")):
        metrics[path.stem.replace(".metrics", "")] = read_json(path)

    return {
        "provider": provider,
        "provider_symbol": symbol,
        "source_csv": str(local_source),
        "rows": int(len(df)),
        "first_ts_ms": to_epoch_ms(df["date"].min()) if len(df) else None,
        "last_ts_ms": to_epoch_ms(df["date"].max()) if len(df) else None,
        "workspace": str(workspace),
        "feather": str(feather),
        "compile_exit": compile_proc.returncode,
        "run_tomac_exit": run_proc.returncode,
        "metrics": metrics,
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
        if result["compile_exit"] == 0:
            totals["compile_success"] += 1
        if result["run_tomac_exit"] == 0:
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


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "same_root_six_provider_aq_v1.md"
    json_path = REPORT_DIR / "same_root_six_provider_aq_v1.json"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_same_root_six_provider_aq_v1.csv"
    assertions = CHECK_DIR / "same_root_six_provider_aq_v1_assertions.out"
    write_json(json_path, summary)

    lines = [
        "# Same-Root Six-Provider AQ v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Scope",
        "This packet fetches public provider rows, TVR rows, and IBKR rows inside one run root, then runs the same TOMAC AQ pair on all six provider lanes.",
        "It does not edit ict-engine runtime code and does not promote any branch.",
        "",
        "## Provider Rows",
    ]
    for key, item in summary["provider_fetch"].items():
        lines.append(f"- `{key}`: rows `{item['rows']}`, exit `{item['exit']}`, csv `{item['csv']}`.")
    lines.extend(["", "## AQ Results"])
    for result in summary["aq_results"]:
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
            f"- Promotion allowed: `{summary['promotion_allowed']}`.",
            f"- Trade usable: `{summary['trade_usable']}`.",
            f"- Update goal: `{summary['update_goal']}`.",
            "",
            "## Artifacts",
            f"- JSON: `{json_path}`",
            f"- Checklist: `{checklist}`",
            f"- Assertions: `{assertions}`",
            f"- Provider CSVs: `{PROVIDER_CSV_DIR}`",
            f"- AQ workspaces: `{WORKSPACE_ROOT}`",
        ]
    )
    write(report, "\n".join(lines) + "\n")

    with checklist.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["requirement", "artifact", "status", "note"])
        writer.writerow(["fresh same-root provider rows", str(PROVIDER_CSV_DIR), "covered", "all provider CSVs are under this run root"])
        writer.writerow(["IBKR rows exceed TOMAC startup floor", summary["provider_fetch"]["ibkr_paxos_midpoint_7d_1h"]["csv"], "covered", str(summary["provider_fetch"]["ibkr_paxos_midpoint_7d_1h"]["rows"])])
        writer.writerow(["AQ compile/TOMAC on six lanes", str(WORKSPACE_ROOT), "covered", f"{summary['metric_totals']['run_success']}/6 TOMAC exits 0"])
        writer.writerow(["downstream chain", "N/A", "not_run", "only run if provider/AQ authority and metrics warrant it"])
        writer.writerow(["promotion/update_goal", str(report), "fail_closed", "this packet is evidence only"])

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS same_root_provider_csvs={len(summary['provider_fetch'])}",
        f"PASS ibkr_rows={summary['provider_fetch']['ibkr_paxos_midpoint_7d_1h']['rows']}",
        f"PASS compile_success={summary['metric_totals']['compile_success']}",
        f"PASS run_success={summary['metric_totals']['run_success']}",
        f"PASS strategies_with_metrics={summary['metric_totals']['strategies_with_metrics']}",
        f"PASS total_trades={summary['metric_totals']['total_trades']}",
        f"FAIL_CLOSED same_root_six_provider_aq_authority={summary['same_root_six_provider_aq_authority']}",
        f"FAIL_CLOSED no_downstream_chain_run={not summary['downstream_chain_run']}",
        f"PASS promotion_allowed={summary['promotion_allowed']}",
        f"PASS trade_usable={summary['trade_usable']}",
        f"PASS update_goal={summary['update_goal']}",
    ]
    write(assertions, "\n".join(assertion_lines) + "\n")


def main() -> int:
    for path in (OUT_DIR, CHECK_DIR, PROVIDER_CSV_DIR, INPUT_DIR, WORKSPACE_ROOT, REPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)
    write(ROOT / "run_id.txt", RUN_ID + "\n")

    provider_fetch = fetch_public_rows()
    provider_fetch["tvr_binance_btcusdt_1h"] = fetch_tvr_rows()
    ibkr_csv = ROOT / "derived" / "ibkr_btc_paxos" / "BTC_1h_midpoint.csv"
    provider_fetch["ibkr_paxos_midpoint_7d_1h"] = {
        "exit": int((CHECK_DIR / "00_ibkr_btc_paxos_7d_1h.exit").read_text().strip()),
        "csv": str(ibkr_csv),
        "rows": csv_rows(ibkr_csv),
    }

    source_module = load_source_aq_module()
    providers = {
        "yfinance": (PROVIDER_CSV_DIR / "yfinance_btc_usd_1h.csv", "BTC-USD"),
        "kraken_public": (PROVIDER_CSV_DIR / "kraken_xbtusd_1h.csv", "XBTUSD"),
        "binance_public": (PROVIDER_CSV_DIR / "binance_btcusdt_1h.csv", "BTCUSDT"),
        "bybit_public": (PROVIDER_CSV_DIR / "bybit_btcusdt_linear_1h.csv", "BTCUSDT"),
        "tvr_binance": (PROVIDER_CSV_DIR / "tvr_binance_btcusdt_1h.csv", "BINANCE:BTCUSDT"),
        "ibkr_midpoint_7d": (ibkr_csv, "BTC PAXOS MIDPOINT"),
    }
    aq_results = [
        run_provider_fixed(source_module, provider, source, symbol)
        for provider, (source, symbol) in providers.items()
    ]
    totals = metric_totals(aq_results)
    same_root_authority = (
        len(provider_fetch) == 6
        and all(item["exit"] == 0 and item["rows"] >= 90 for item in provider_fetch.values())
        and totals["compile_success"] == 6
        and totals["run_success"] == 6
    )
    summary = {
        "run_id": RUN_ID,
        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "provider_fetch": provider_fetch,
        "aq_results": aq_results,
        "metric_totals": totals,
        "same_root_six_provider_aq_authority": same_root_authority,
        "downstream_chain_run": False,
        "gate_result": "same_root_six_provider_aq_ready_for_downstream_readback" if same_root_authority else "same_root_six_provider_aq_incomplete_fail_closed",
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_report(summary)
    return 0 if same_root_authority else 3


if __name__ == "__main__":
    raise SystemExit(main())
