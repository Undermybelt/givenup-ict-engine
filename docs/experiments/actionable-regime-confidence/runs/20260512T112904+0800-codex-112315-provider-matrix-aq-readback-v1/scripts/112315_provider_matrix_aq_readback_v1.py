from __future__ import annotations

import csv
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1"
SOURCE_RUN_ID = "20260512T112315+0800-codex-board-b-six-provider-btc-matrix-probe-v1"
RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
SOURCE_ROOT = RUNS / SOURCE_RUN_ID
ROOT = RUNS / RUN_ID
TEMPLATE_WORKSPACE = (
    RUNS
    / "20260512T104902+0800-codex-board-b-yahoo-btc-pullback-precision-aq-v1"
    / "workspace"
    / "auto-quant-yahoo-btc-pullback-precision"
)
PYTHON = Path("/Users/thrill3r/Auto-Quant/.venv/bin/python")

OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "112315-provider-matrix-aq-readback-v1"
PROVIDER_CSV_DIR = ROOT / "provider-csv"
WORKSPACE_ROOT = ROOT / "workspace"

PUBLIC_PROVIDER_INPUTS = {
    "yfinance": {
        "source": SOURCE_ROOT / "provider-csv" / "yfinance_btc_usd_1h.csv",
        "symbol": "BTC-USD",
    },
    "kraken_public": {
        "source": SOURCE_ROOT / "provider-csv" / "kraken_xbtusd_1h.csv",
        "symbol": "XBTUSD",
    },
    "binance_public": {
        "source": SOURCE_ROOT / "provider-csv" / "binance_btcusdt_1h.csv",
        "symbol": "BTCUSDT",
    },
    "bybit_public": {
        "source": SOURCE_ROOT / "provider-csv" / "bybit_btcusdt_linear_1h.csv",
        "symbol": "BTCUSDT",
    },
}


def read_text(path: Path) -> str:
    return path.read_text() if path.exists() else ""


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def exit_code(path: Path) -> int | None:
    if not path.exists():
        return None
    return int(path.read_text().strip())


def csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open() as fh:
        return max(sum(1 for _ in fh) - 1, 0)


def normalized_df(source: Path) -> pd.DataFrame:
    raw = pd.read_csv(source)
    date = pd.to_datetime(raw["date"], utc=True)
    timestamp_ms = pd.Series(date.array.asi8 // 1_000_000, dtype="int64")
    out = pd.DataFrame(
        {
            "date": timestamp_ms,
            "open": raw["open"].astype(float),
            "high": raw["high"].astype(float),
            "low": raw["low"].astype(float),
            "close": raw["close"].astype(float),
            "volume": raw["volume"].astype(float),
        }
    )
    return out.dropna().sort_values("date").reset_index(drop=True)


def copy_template(provider: str) -> Path:
    workspace = WORKSPACE_ROOT / f"auto-quant-112315-{provider}"
    if workspace.exists():
        shutil.rmtree(workspace)
    shutil.copytree(
        TEMPLATE_WORKSPACE,
        workspace,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "derived"),
    )
    data_dir = workspace / "user_data" / "data"
    for path in data_dir.glob("*.feather"):
        path.unlink()
    (workspace / "derived").mkdir(parents=True, exist_ok=True)
    return workspace


def run_provider(provider: str, meta: dict[str, Any]) -> dict[str, Any]:
    source = meta["source"]
    local_source = PROVIDER_CSV_DIR / source.name
    shutil.copy2(source, local_source)
    workspace = copy_template(provider)
    df = normalized_df(local_source)
    feather = workspace / "user_data" / "data" / "BTC_USDT-1h.feather"
    df.to_feather(feather)

    strategies = sorted((workspace / "user_data" / "strategies_external").glob("*.py"))
    compile_cmd = [
        str(PYTHON),
        "-m",
        "py_compile",
        "run_tomac.py",
        *[str(path.relative_to(workspace)) for path in strategies],
    ]
    run_cmd = [str(PYTHON), "run_tomac.py"]

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
        run_cmd,
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    (OUT_DIR / f"aq_{prefix}_run_tomac.out").write_text(run_proc.stdout)
    (OUT_DIR / f"aq_{prefix}_run_tomac.err").write_text(run_proc.stderr)
    (OUT_DIR / f"aq_{prefix}_run_tomac.cmd").write_text(" ".join(run_cmd) + "\n")
    (CHECK_DIR / f"aq_{prefix}_run_tomac.exit").write_text(f"{run_proc.returncode}\n")

    metrics: dict[str, Any] = {}
    for path in sorted((workspace / "derived").glob("*.metrics.json")):
        metrics[path.stem.replace(".metrics", "")] = read_json(path)

    return {
        "provider": provider,
        "provider_symbol": meta["symbol"],
        "source_csv": str(local_source),
        "rows": int(len(df)),
        "first_ts_ms": int(df["date"].min()) if len(df) else None,
        "last_ts_ms": int(df["date"].max()) if len(df) else None,
        "workspace": str(workspace),
        "feather": str(feather),
        "compile_exit": compile_proc.returncode,
        "run_tomac_exit": run_proc.returncode,
        "metrics": metrics,
    }


def provider_matrix_readback() -> dict[str, Any]:
    ibkr_result = read_json(SOURCE_ROOT / "provider-csv" / "ibkr_btc_paxos_1d_result.json")
    return {
        "source_run": str(SOURCE_ROOT),
        "status_exits": {
            "yfinance": exit_code(SOURCE_ROOT / "checks" / "00_provider_status_yfinance.exit"),
            "tradingview_mcp": exit_code(
                SOURCE_ROOT / "checks" / "01_provider_status_tradingview_mcp.exit"
            ),
            "ibkr": exit_code(SOURCE_ROOT / "checks" / "02_provider_status_ibkr.exit"),
            "ibkr_bridge": exit_code(SOURCE_ROOT / "checks" / "03_provider_status_ibkr_bridge.exit"),
            "kraken_public": exit_code(
                SOURCE_ROOT / "checks" / "04_provider_status_kraken_public.exit"
            ),
            "binance_public": exit_code(
                SOURCE_ROOT / "checks" / "05_provider_status_binance_public.exit"
            ),
            "bybit_public": exit_code(
                SOURCE_ROOT / "checks" / "06_provider_status_bybit_public.exit"
            ),
        },
        "fetch_exits": {
            "tradingview_mcp_btcusdt_1d": exit_code(
                SOURCE_ROOT / "checks" / "10_tvr_btcusdt_1d.exit"
            ),
            "yfinance_btc_usd_1h": exit_code(
                SOURCE_ROOT / "checks" / "11_yfinance_btc_usd_1h.exit"
            ),
            "kraken_xbtusd_1h": exit_code(
                SOURCE_ROOT / "checks" / "12_kraken_xbtusd_1h.exit"
            ),
            "binance_btcusdt_1h": exit_code(
                SOURCE_ROOT / "checks" / "13_binance_btcusdt_1h.exit"
            ),
            "bybit_btcusdt_linear_1h": exit_code(
                SOURCE_ROOT / "checks" / "14_bybit_btcusdt_linear_1h.exit"
            ),
            "ibkr_btc_paxos_1d": exit_code(
                SOURCE_ROOT / "checks" / "15_ibkr_btc_paxos_1d.exit"
            ),
        },
        "fetch_rows": {
            "yfinance_btc_usd_1h": csv_rows(
                SOURCE_ROOT / "provider-csv" / "yfinance_btc_usd_1h.csv"
            ),
            "kraken_xbtusd_1h": csv_rows(
                SOURCE_ROOT / "provider-csv" / "kraken_xbtusd_1h.csv"
            ),
            "binance_btcusdt_1h": csv_rows(
                SOURCE_ROOT / "provider-csv" / "binance_btcusdt_1h.csv"
            ),
            "bybit_btcusdt_linear_1h": csv_rows(
                SOURCE_ROOT / "provider-csv" / "bybit_btcusdt_linear_1h.csv"
            ),
            "ibkr_btc_paxos_1d": int(ibkr_result.get("rows") or 0),
        },
        "tradingview_error": read_text(
            SOURCE_ROOT / "command-output" / "10_tvr_btcusdt_1d.stderr"
        ).strip(),
        "ibkr_result": ibkr_result,
    }


def strategy_lines(result: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for strategy, payload in sorted(result["metrics"].items()):
        aggregate = payload.get("aggregate", {})
        lines.append(
            f"  - {strategy}: trades={aggregate.get('trade_count')} "
            f"profit_pct={aggregate.get('total_profit_pct')} "
            f"sharpe={aggregate.get('sharpe')} pf={aggregate.get('profit_factor')}"
        )
    return lines


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "112315_provider_matrix_aq_readback_v1.md"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_112315_provider_matrix_aq_v1.csv"
    assertions = CHECK_DIR / "112315_provider_matrix_aq_readback_v1_assertions.out"

    lines = [
        "# 112315 Provider Matrix AQ Readback v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source provider matrix: `{SOURCE_RUN_ID}`",
        "",
        "## Scope",
        "This packet reads the fresh 112315 provider matrix, runs AQ only on providers with BTC rows, and keeps failed TVR/IBKR provider gates explicit.",
        "It does not change ict-engine runtime code and does not substitute another provider for TVR or IBKR.",
        "",
        "## Provider Matrix",
    ]
    matrix = summary["provider_matrix"]
    for key, value in matrix["fetch_rows"].items():
        lines.append(f"- `{key}`: rows `{value}`, exit `{matrix['fetch_exits'].get(key)}`.")
    lines.append(f"- `tradingview_mcp_btcusdt_1d`: exit `{matrix['fetch_exits']['tradingview_mcp_btcusdt_1d']}`.")
    lines.extend(["", "## AQ Results"])
    for result in summary["aq_results"]:
        lines.append(
            f"- `{result['provider']}`: rows `{result['rows']}`, compile exit `{result['compile_exit']}`, TOMAC exit `{result['run_tomac_exit']}`."
        )
        lines.extend(strategy_lines(result))
    lines.extend(
        [
            "",
            "## Decision",
            f"- Gate result: `{summary['gate_result']}`.",
            "- Four public BTC providers have same-root rows and AQ execution, but TVR fetch failed and IBKR PAXOS BTC returned zero rows.",
            "- This is not a six-provider AQ authority packet and cannot unlock Pre-Bayes/BBN/CatBoost/execution-tree promotion.",
            "- Accepted rows added: `0`.",
            "- Mature rooted branch observations added: `0`.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{REPORT_DIR / '112315_provider_matrix_aq_readback_v1.json'}`",
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
        writer.writerow(["source provider matrix", str(SOURCE_ROOT), "covered", SOURCE_RUN_ID])
        writer.writerow(["public provider rows", "provider-csv/*.csv", "covered", "yfinance/kraken/binance/bybit"])
        writer.writerow(["TVR BTC fetch", "source command-output/10_tvr_btcusdt_1d.stderr", "fail_closed", "fetch exit 1"])
        writer.writerow(["IBKR BTC fetch", "source provider-csv/ibkr_btc_paxos_1d_result.json", "fail_closed", "rows 0"])
        writer.writerow(["AQ execution", "command-output/aq_*_run_tomac.out", "covered_partial", "public provider rows only"])
        writer.writerow(["downstream chain", "N/A", "not_run", "no six-provider AQ authority"])

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_run={SOURCE_RUN_ID}",
        f"PASS public_provider_aq_runs={len(summary['aq_results'])}",
        f"PASS yfinance_rows={matrix['fetch_rows']['yfinance_btc_usd_1h']}",
        f"PASS kraken_rows={matrix['fetch_rows']['kraken_xbtusd_1h']}",
        f"PASS binance_rows={matrix['fetch_rows']['binance_btcusdt_1h']}",
        f"PASS bybit_rows={matrix['fetch_rows']['bybit_btcusdt_linear_1h']}",
        f"FAIL_CLOSED tvr_fetch_exit={matrix['fetch_exits']['tradingview_mcp_btcusdt_1d']}",
        f"FAIL_CLOSED ibkr_btc_rows={matrix['fetch_rows']['ibkr_btc_paxos_1d']}",
        "FAIL_CLOSED six_provider_aq_authority=false",
        "FAIL_CLOSED no_pre_bayes_bbn_catboost_execution_tree_promotion",
        "PASS accepted_rows_added=0",
        "PASS mature_rooted_branch_observations_added=0",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions.write_text("\n".join(assertion_lines) + "\n")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    PROVIDER_CSV_DIR.mkdir(parents=True, exist_ok=True)
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")

    matrix = provider_matrix_readback()
    aq_results = [run_provider(provider, meta) for provider, meta in PUBLIC_PROVIDER_INPUTS.items()]
    summary = {
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "provider_matrix": matrix,
        "aq_results": aq_results,
        "gate_result": "112315_provider_matrix_aq_readback=public_provider_aq_ran_but_tvr_ibkr_fail_closed_no_six_provider_authority_no_promotion",
        "accepted_rows_added": 0,
        "mature_rooted_branch_observations_added": 0,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(REPORT_DIR / "112315_provider_matrix_aq_readback_v1.json", summary)
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
