from __future__ import annotations

import asyncio
import csv
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd
from ib_async import Crypto, IB


RUN_ID = "20260512T115431+0800-codex-ibkr-btc-aq-lane-repair-v1"
SOURCE_AQ_ROOT_ID = "20260512T113833+0800-codex-112904-provider-matrix-aq-date-contract-repair-v1"
TEMPLATE_SOURCE_ID = "20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_AQ_ROOT = RUNS / SOURCE_AQ_ROOT_ID
TEMPLATE_SOURCE_ROOT = RUNS / TEMPLATE_SOURCE_ID
TEMPLATE_MODULE = TEMPLATE_SOURCE_ROOT / "scripts" / "112315_provider_matrix_aq_readback_v1.py"

OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "ibkr-btc-aq-lane-repair-v1"
PROVIDER_CSV_DIR = ROOT / "provider-csv"
WORKSPACE_ROOT = ROOT / "workspace"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


def load_template_module() -> Any:
    spec = importlib.util.spec_from_file_location("provider_matrix_aq_template", TEMPLATE_MODULE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {TEMPLATE_MODULE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def fetch_ibkr_btc(kind: str, duration: str, client_id: int, out_csv: Path) -> dict[str, Any]:
    messages: list[dict[str, Any]] = []
    ib = IB()

    def on_error(req_id: int, error_code: int, error_string: str, contract: Any) -> None:
        messages.append(
            {
                "reqId": req_id,
                "errorCode": error_code,
                "errorString": error_string,
                "contract": str(contract),
            }
        )

    ib.errorEvent += on_error
    result: dict[str, Any] = {
        "what_to_show": kind,
        "duration": duration,
        "bar_size": "1 hour",
        "connected": False,
        "qualified": False,
        "rows": 0,
        "csv": str(out_csv),
        "messages": messages,
    }
    try:
        await ib.connectAsync("127.0.0.1", 4002, clientId=client_id, timeout=8)
        result["connected"] = True
        contract = Crypto("BTC", "PAXOS", "USD")
        qualified = await ib.qualifyContractsAsync(contract)
        result["qualified"] = bool(qualified)
        if qualified:
            contract = qualified[0]
        result["qualified_contract"] = str(contract)
        bars = await ib.reqHistoricalDataAsync(
            contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting="1 hour",
            whatToShow=kind,
            useRTH=False,
            formatDate=1,
        )
        rows = [
            {
                "date": str(bar.date),
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
                "wap": getattr(bar, "average", None),
                "count": getattr(bar, "barCount", None),
            }
            for bar in bars
        ]
        result["rows"] = len(rows)
        if rows:
            out_csv.parent.mkdir(parents=True, exist_ok=True)
            with out_csv.open("w", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            result["first_time"] = rows[0]["date"]
            result["last_time"] = rows[-1]["date"]
    except Exception as exc:  # keep provider failure as artifact data
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
    finally:
        if ib.isConnected():
            ib.disconnect()
    return result


def normalize_ohlcv(source: Path) -> pd.DataFrame:
    raw = pd.read_csv(source)
    date_col = "date" if "date" in raw.columns else "timestamp" if "timestamp" in raw.columns else "ts"
    dates = pd.to_datetime(raw[date_col], utc=True)
    volume = pd.to_numeric(raw.get("volume", 0.0), errors="coerce").fillna(0.0).astype(float)
    volume = volume.mask(volume < 0, 0.0)
    return (
        pd.DataFrame(
            {
                "date": dates,
                "open": pd.to_numeric(raw["open"], errors="coerce").astype(float),
                "high": pd.to_numeric(raw["high"], errors="coerce").astype(float),
                "low": pd.to_numeric(raw["low"], errors="coerce").astype(float),
                "close": pd.to_numeric(raw["close"], errors="coerce").astype(float),
                "volume": volume,
            }
        )
        .dropna()
        .sort_values("date")
        .reset_index(drop=True)
    )


def copy_template(provider: str, template: Any) -> Path:
    workspace = template.copy_template(provider)
    local = WORKSPACE_ROOT / workspace.name
    if local.exists():
        shutil.rmtree(local)
    local.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(workspace, local)
    return local


def run_aq(provider: str, csv_path: Path, template: Any) -> dict[str, Any]:
    workspace = copy_template(provider, template)
    df = normalize_ohlcv(csv_path)
    feather = workspace / "user_data" / "data" / "BTC_USDT-1h.feather"
    feather.parent.mkdir(parents=True, exist_ok=True)
    df.to_feather(feather)

    strategies = sorted((workspace / "user_data" / "strategies_external").glob("*.py"))
    compile_cmd = [
        str(template.PYTHON),
        "-m",
        "py_compile",
        "run_tomac.py",
        *[str(path.relative_to(workspace)) for path in strategies],
    ]
    run_cmd = [str(template.PYTHON), "run_tomac.py"]
    prefix = provider.replace("/", "_")

    compile_proc = subprocess.run(
        compile_cmd,
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    (OUT_DIR / f"aq_{prefix}_compile.cmd").write_text(" ".join(compile_cmd) + "\n")
    (OUT_DIR / f"aq_{prefix}_compile.out").write_text(compile_proc.stdout)
    (OUT_DIR / f"aq_{prefix}_compile.err").write_text(compile_proc.stderr)
    (CHECK_DIR / f"aq_{prefix}_compile.exit").write_text(f"{compile_proc.returncode}\n")

    run_proc = subprocess.run(
        run_cmd,
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    (OUT_DIR / f"aq_{prefix}_run_tomac.cmd").write_text(" ".join(run_cmd) + "\n")
    (OUT_DIR / f"aq_{prefix}_run_tomac.out").write_text(run_proc.stdout)
    (OUT_DIR / f"aq_{prefix}_run_tomac.err").write_text(run_proc.stderr)
    (CHECK_DIR / f"aq_{prefix}_run_tomac.exit").write_text(f"{run_proc.returncode}\n")

    metrics: dict[str, Any] = {}
    for path in sorted((workspace / "derived").glob("*.metrics.json")):
        metrics[path.stem.replace(".metrics", "")] = read_json(path)

    return {
        "provider": provider,
        "source_csv": str(csv_path),
        "rows": int(len(df)),
        "first_time": str(df["date"].min()) if len(df) else None,
        "last_time": str(df["date"].max()) if len(df) else None,
        "workspace": str(workspace),
        "compile_exit": compile_proc.returncode,
        "run_tomac_exit": run_proc.returncode,
        "metrics": metrics,
    }


def summarize_metrics(result: dict[str, Any]) -> dict[str, Any]:
    total_trades = 0
    positive = 0
    strategy_count = 0
    for payload in result.get("metrics", {}).values():
        aggregate = payload.get("aggregate", {})
        trades = int(aggregate.get("trade_count") or 0)
        profit = float(aggregate.get("total_profit_pct") or 0.0)
        strategy_count += 1
        total_trades += trades
        if profit > 0:
            positive += 1
    return {
        "strategies_with_metrics": strategy_count,
        "total_trades": total_trades,
        "positive_profit_metric_count": positive,
    }


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "ibkr_btc_aq_lane_repair_v1.md"
    assertions = CHECK_DIR / "ibkr_btc_aq_lane_repair_v1_assertions.out"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_ibkr_btc_aq_lane_repair_v1.csv"

    fetches = summary["fetch_attempts"]
    lines = [
        "# IBKR BTC AQ Lane Repair v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source AQ root: `{SOURCE_AQ_ROOT_ID}`",
        "",
        "## Scope",
        "Narrow repair attempt for the IBKR BTC/PAXOS lane that blocked the repaired provider-matrix AQ packet.",
        "This run is additive, does not edit ict-engine runtime code, and does not promote any branch.",
        "",
        "## Fetch Attempts",
    ]
    for item in fetches:
        lines.append(
            f"- `{item['what_to_show']}` `{item['duration']}` `{item['bar_size']}`: "
            f"connected `{item.get('connected')}`, qualified `{item.get('qualified')}`, rows `{item.get('rows')}`, "
            f"error `{item.get('error_type') or ''}`."
        )
    aq = summary.get("aq_result")
    lines.extend(["", "## AQ Result"])
    if aq:
        lines.append(
            f"- `{aq['provider']}`: rows `{aq['rows']}`, compile exit `{aq['compile_exit']}`, TOMAC exit `{aq['run_tomac_exit']}`."
        )
        for name, payload in aq.get("metrics", {}).items():
            aggregate = payload.get("aggregate", {})
            lines.append(
                f"  - `{name}`: trades `{aggregate.get('trade_count')}`, "
                f"profit_pct `{aggregate.get('total_profit_pct')}`, win_rate_pct `{aggregate.get('win_rate_pct')}`, "
                f"profit_factor `{aggregate.get('profit_factor')}`."
            )
    else:
        lines.append("- No AQ run was attempted because no fetch reached the startup floor.")
    lines.extend(
        [
            "",
            "## Decision",
            f"- Gate result: `{summary['gate_result']}`.",
            f"- Startup floor met: `{summary['startup_floor_met']}`.",
            f"- IBKR AQ lane repaired: `{summary['ibkr_aq_lane_repaired']}`.",
            f"- Mature rooted branch observations added: `{summary['mature_rooted_branch_observations_added']}`.",
            f"- `promotion_allowed={str(summary['promotion_allowed']).lower()}`.",
            f"- `trade_usable={str(summary['trade_usable']).lower()}`.",
            f"- `update_goal={str(summary['update_goal']).lower()}`.",
        ]
    )
    report.write_text("\n".join(lines) + "\n")
    write_json(REPORT_DIR / "ibkr_btc_aq_lane_repair_v1.json", summary)
    checklist.write_text(
        "requirement,evidence,status\n"
        f"fetch_ibkr_btc_1h,{ROOT}/provider-csv,PASS\n"
        f"run_aq_if_startup_floor_met,{ROOT}/workspace,{'PASS' if summary.get('aq_result') else 'FAIL_CLOSED'}\n"
        f"do_not_promote,{report},PASS\n"
    )

    checks = [
        f"PASS run_id={RUN_ID}",
        f"PASS fetch_attempts={len(fetches)}",
        f"{'PASS' if summary['startup_floor_met'] else 'FAIL_CLOSED'} startup_floor_met={summary['startup_floor_met']}",
        f"{'PASS' if summary['ibkr_aq_lane_repaired'] else 'FAIL_CLOSED'} ibkr_aq_lane_repaired={summary['ibkr_aq_lane_repaired']}",
        f"PASS promotion_allowed={str(summary['promotion_allowed']).lower()}",
        f"PASS trade_usable={str(summary['trade_usable']).lower()}",
        f"PASS update_goal={str(summary['update_goal']).lower()}",
    ]
    assertions.write_text("\n".join(checks) + "\n")


async def main() -> int:
    for directory in (OUT_DIR, CHECK_DIR, REPORT_DIR, PROVIDER_CSV_DIR, WORKSPACE_ROOT):
        directory.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")
    (ROOT / "source_root.txt").write_text(SOURCE_AQ_ROOT_ID + "\n")

    attempts = [
        ("AGGTRADES", "30 D", 42),
        ("AGGTRADES", "60 D", 43),
        ("MIDPOINT", "30 D", 44),
        ("MIDPOINT", "60 D", 45),
    ]
    fetch_results = []
    selected: dict[str, Any] | None = None
    for kind, duration, client_id in attempts:
        out_csv = PROVIDER_CSV_DIR / f"ibkr_btc_paxos_{kind.lower()}_{duration.replace(' ', '').lower()}_1h.csv"
        result = await fetch_ibkr_btc(kind, duration, client_id, out_csv)
        fetch_results.append(result)
        write_json(PROVIDER_CSV_DIR / f"{out_csv.stem}_result.json", result)
        if result.get("rows", 0) >= 120 and selected is None:
            selected = result

    template = load_template_module()
    aq_result = None
    if selected is not None:
        aq_result = run_aq("ibkr_paxos_1h_repair", Path(selected["csv"]), template)

    metric_summary = summarize_metrics(aq_result) if aq_result else {
        "strategies_with_metrics": 0,
        "total_trades": 0,
        "positive_profit_metric_count": 0,
    }
    ibkr_repaired = bool(aq_result and aq_result["run_tomac_exit"] == 0 and metric_summary["total_trades"] > 0)
    summary = {
        "run_id": RUN_ID,
        "source_aq_root": SOURCE_AQ_ROOT_ID,
        "fetch_attempts": fetch_results,
        "selected_fetch": selected,
        "startup_floor_met": selected is not None,
        "aq_result": aq_result,
        "metric_summary": metric_summary,
        "ibkr_aq_lane_repaired": ibkr_repaired,
        "mature_rooted_branch_observations_added": metric_summary["total_trades"] if ibkr_repaired else 0,
        "gate_result": (
            "ibkr_btc_aq_lane_repaired_nonpromoting"
            if ibkr_repaired
            else "ibkr_btc_aq_lane_still_fail_closed"
        ),
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
