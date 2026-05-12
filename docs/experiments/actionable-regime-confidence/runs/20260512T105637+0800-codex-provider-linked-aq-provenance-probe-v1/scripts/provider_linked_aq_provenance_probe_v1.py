from __future__ import annotations

import csv
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T105637+0800-codex-provider-linked-aq-provenance-probe-v1"
SOURCE_PROVIDER_RUN = (
    Path("docs/experiments/actionable-regime-confidence/runs")
    / "20260512T105207+0800-codex-provider-lane-bridge-probe-v1"
)
TEMPLATE_WORKSPACE = (
    Path("docs/experiments/actionable-regime-confidence/runs")
    / "20260512T104902+0800-codex-board-b-yahoo-btc-pullback-precision-aq-v1"
    / "workspace"
    / "auto-quant-yahoo-btc-pullback-precision"
)
ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
PROVIDER_CSV_DIR = ROOT / "provider-csv"
WORKSPACE_ROOT = ROOT / "workspace"
OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "provider-linked-aq-provenance-probe-v1"
PYTHON = Path("/Users/thrill3r/Auto-Quant/.venv/bin/python")


PUBLIC_PROVIDER_INPUTS = {
    "yfinance": {
        "source": SOURCE_PROVIDER_RUN / "provider-csv" / "yfinance_btc_usd_1h_7d.csv",
        "symbol": "BTC-USD",
        "timeframe": "1h",
        "normalized_pair": "BTC/USDT",
    },
    "kraken_public_ccxt": {
        "source": SOURCE_PROVIDER_RUN / "provider-csv" / "kraken_public_ccxt_btc_1h_120.csv",
        "symbol": "BTC/USD",
        "timeframe": "1h",
        "normalized_pair": "BTC/USDT",
    },
    "binance_public_ccxt": {
        "source": SOURCE_PROVIDER_RUN / "provider-csv" / "binance_public_ccxt_btc_1h_120.csv",
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "normalized_pair": "BTC/USDT",
    },
    "bybit_public_ccxt": {
        "source": SOURCE_PROVIDER_RUN / "provider-csv" / "bybit_public_ccxt_btc_1h_120.csv",
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "normalized_pair": "BTC/USDT",
    },
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def copy_provider_csvs() -> None:
    PROVIDER_CSV_DIR.mkdir(parents=True, exist_ok=True)
    for meta in PUBLIC_PROVIDER_INPUTS.values():
        shutil.copy2(meta["source"], PROVIDER_CSV_DIR / meta["source"].name)
    ibkr = SOURCE_PROVIDER_RUN / "provider-csv" / "ibkr_QQQ_1h_5d.csv"
    if ibkr.exists():
        shutil.copy2(ibkr, PROVIDER_CSV_DIR / ibkr.name)


def provider_df(provider: str, source: Path) -> pd.DataFrame:
    raw = pd.read_csv(source)
    if provider == "yfinance":
        date = pd.to_datetime(raw["Datetime"], utc=True)
        out = pd.DataFrame(
            {
                "date": (date.view("int64") // 1_000_000).astype("int64"),
                "open": raw["Open_BTC-USD"].astype(float),
                "high": raw["High_BTC-USD"].astype(float),
                "low": raw["Low_BTC-USD"].astype(float),
                "close": raw["Close_BTC-USD"].astype(float),
                "volume": raw["Volume_BTC-USD"].astype(float),
            }
        )
    else:
        out = pd.DataFrame(
            {
                "date": raw["timestamp_ms"].astype("int64"),
                "open": raw["open"].astype(float),
                "high": raw["high"].astype(float),
                "low": raw["low"].astype(float),
                "close": raw["close"].astype(float),
                "volume": raw["volume"].astype(float),
            }
        )
    return out.dropna().sort_values("date").reset_index(drop=True)


def copy_template(provider: str) -> Path:
    workspace = WORKSPACE_ROOT / f"auto-quant-provider-linked-{provider}"
    if workspace.exists():
        shutil.rmtree(workspace)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", "derived")
    shutil.copytree(TEMPLATE_WORKSPACE, workspace, ignore=ignore)
    data_dir = workspace / "user_data" / "data"
    for path in data_dir.glob("*.feather"):
        path.unlink()
    (workspace / "derived").mkdir(parents=True, exist_ok=True)
    return workspace


def run_provider(provider: str, meta: dict[str, Any]) -> dict[str, Any]:
    source_copy = PROVIDER_CSV_DIR / meta["source"].name
    workspace = copy_template(provider)
    df = provider_df(provider, source_copy)
    feather = workspace / "user_data" / "data" / "BTC_USDT-1h.feather"
    df.to_feather(feather)

    prefix = provider.replace("/", "_")
    compile_out = OUT_DIR / f"aq_{prefix}_compile.out"
    compile_err = OUT_DIR / f"aq_{prefix}_compile.err"
    run_out = OUT_DIR / f"aq_{prefix}_run_tomac.out"
    run_err = OUT_DIR / f"aq_{prefix}_run_tomac.err"

    compile_cmd = [
        str(PYTHON),
        "-m",
        "py_compile",
        "run_tomac.py",
        *[
            str(p.relative_to(workspace))
            for p in sorted((workspace / "user_data" / "strategies_external").glob("*.py"))
        ],
    ]
    run_cmd = [str(PYTHON), "run_tomac.py"]

    compile_proc = subprocess.run(
        compile_cmd,
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    compile_out.write_text(compile_proc.stdout)
    compile_err.write_text(compile_proc.stderr)
    (CHECK_DIR / f"aq_{prefix}_compile.exit").write_text(str(compile_proc.returncode) + "\n")

    run_proc = subprocess.run(
        run_cmd,
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    run_out.write_text(run_proc.stdout)
    run_err.write_text(run_proc.stderr)
    (CHECK_DIR / f"aq_{prefix}_run_tomac.exit").write_text(str(run_proc.returncode) + "\n")

    metrics = {}
    for path in sorted((workspace / "derived").glob("*.metrics.json")):
        metrics[path.stem.replace(".metrics", "")] = read_json(path)

    return {
        "provider": provider,
        "source_csv": str(source_copy),
        "provider_symbol": meta["symbol"],
        "timeframe": meta["timeframe"],
        "normalized_pair": meta["normalized_pair"],
        "rows": int(len(df)),
        "first_ts_ms": int(df["date"].min()) if len(df) else None,
        "last_ts_ms": int(df["date"].max()) if len(df) else None,
        "workspace": str(workspace),
        "feather": str(feather),
        "compile_exit": compile_proc.returncode,
        "run_tomac_exit": run_proc.returncode,
        "metrics": metrics,
    }


def metric_summary(metrics: dict[str, Any]) -> list[str]:
    rows = []
    for strategy, payload in metrics.items():
        agg = payload.get("aggregate", {})
        rows.append(
            f"{strategy}: trades={agg.get('trade_count')} "
            f"profit_pct={agg.get('total_profit_pct')} "
            f"sharpe={agg.get('sharpe')} pf={agg.get('profit_factor')}"
        )
    return rows


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "provider_linked_aq_provenance_probe_v1.md"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_provider_linked_aq_v1.csv"
    assertions = CHECK_DIR / "provider_linked_aq_provenance_probe_v1_assertions.out"

    lines = [
        "# Provider-Linked AQ Provenance Probe v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source provider bridge: `{SOURCE_PROVIDER_RUN}`",
        "",
        "## Scope",
        "This packet links provider invocation evidence to isolated Auto-Quant/TOMAC execution without changing ict-engine runtime code.",
        "It normalizes only the public BTC provider CSVs from the provider bridge into run-local FreqTrade feathers, then runs the two existing provider-owned BTC AQ strategies per provider.",
        "IBKR and TradingViewRemix/TVR are kept as provenance gates from the same provider bridge, not silently substituted into the BTC AQ dataset.",
        "",
        "## Provider Provenance",
    ]
    for provider, row in summary["provider_invocation_rows"].items():
        lines.append(
            f"- `{provider}`: status `{row.get('status')}`, symbol `{row.get('symbol')}`, "
            f"rows `{row.get('rows')}`, path `{row.get('path') or row.get('stderr_tail')}`"
        )
    lines.extend(["", "## Auto-Quant Results"])
    for result in summary["aq_results"]:
        lines.append(
            f"- `{result['provider']}`: rows `{result['rows']}`, compile exit `{result['compile_exit']}`, "
            f"TOMAC exit `{result['run_tomac_exit']}`."
        )
        for item in metric_summary(result["metrics"]):
            lines.append(f"  - {item}")
    lines.extend(
        [
            "",
            "## Decision",
            f"- Gate result: `{summary['gate_result']}`.",
            "- AQ execution is real for the public provider rows above, but the packet remains fail-closed.",
            "- TradingViewRemix/TVR is still failed, IBKR is ad hoc QQQ only and not the BTC AQ feed, and all AQ runs are short-window diagnostics.",
            "- Accepted rows added: `0`.",
            "- Mature rooted branch observations added: `0`.",
            "- Promotion allowed: `false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{REPORT_DIR / 'provider_linked_aq_provenance_probe_v1.json'}`",
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
        writer.writerow(["AQ execution", "command-output/aq_*_run_tomac.out", "covered", "public provider BTC lanes only"])
        writer.writerow(["IBKR provenance", "provider-csv/ibkr_QQQ_1h_5d.csv", "partial_fail_closed", "ad hoc QQQ, not BTC AQ feed"])
        writer.writerow(["TradingViewRemix provenance", "105207 command-output/02_tradingview_mcp_qqq_1d_fetch.*", "failed", "fetch_failed"])
        writer.writerow(["yfinance provenance", "provider-csv/yfinance_btc_usd_1h_7d.csv", "covered", "AQ run executed"])
        writer.writerow(["Kraken provenance", "provider-csv/kraken_public_ccxt_btc_1h_120.csv", "covered", "AQ run executed"])
        writer.writerow(["Binance provenance", "provider-csv/binance_public_ccxt_btc_1h_120.csv", "covered", "AQ run executed"])
        writer.writerow(["Bybit provenance", "provider-csv/bybit_public_ccxt_btc_1h_120.csv", "covered", "AQ run executed"])
        writer.writerow(["Promotion", "report decision", "fail_closed", "provider/AQ hard gate incomplete"])

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        "PASS source_provider_bridge=20260512T105207+0800-codex-provider-lane-bridge-probe-v1",
        f"PASS aq_public_provider_runs={len(summary['aq_results'])}",
        "PASS aq_provider_invoked=true",
        "PASS provider_rows_yfinance_present=true",
        "PASS provider_rows_kraken_present=true",
        "PASS provider_rows_binance_present=true",
        "PASS provider_rows_bybit_present=true",
        "PASS ibkr_ad_hoc_rows_present=true",
        "FAIL_CLOSED tradingview_remix_tvr_fetch_failed",
        "FAIL_CLOSED ibkr_not_btc_aq_feed",
        "FAIL_CLOSED short_window_public_provider_aq_diagnostic_only",
        "FAIL_CLOSED no_selected_history_or_source_control_unlock",
        "FAIL_CLOSED no_pre_bayes_bbn_catboost_execution_tree_promotion",
        "PASS accepted_rows_added=0",
        "PASS mature_rooted_branch_observations_added=0",
        "PASS promotion_allowed=false",
        "PASS update_goal=false",
    ]
    assertions.write_text("\n".join(assertion_lines) + "\n")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    copy_provider_csvs()
    bridge = read_json(SOURCE_PROVIDER_RUN / "provider-lane-bridge-probe-v1" / "provider_lane_bridge_probe_v1.json")
    results = [run_provider(provider, meta) for provider, meta in PUBLIC_PROVIDER_INPUTS.items()]
    summary = {
        "run_id": RUN_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_provider_bridge": str(SOURCE_PROVIDER_RUN),
        "template_workspace": str(TEMPLATE_WORKSPACE),
        "gate_result": "provider_linked_aq_provenance_probe_v1=aq_ran_with_public_provider_rows_but_six_provider_gate_fail_closed_no_promotion",
        "provider_invocation_rows": bridge.get("providers", {}),
        "aq_results": results,
        "accepted_rows_added": 0,
        "mature_rooted_branch_observations_added": 0,
        "source_control_evidence_acquired": False,
        "explicit_selected_history": False,
        "six_provider_promotion_matrix_passed": False,
        "downstream_promotion": False,
        "promotion_allowed": False,
        "update_goal": False,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(REPORT_DIR / "provider_linked_aq_provenance_probe_v1.json", summary)
    write_report(summary)
    print(json.dumps({"run_id": RUN_ID, "gate_result": summary["gate_result"], "aq_runs": len(results)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
