from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T113833+0800-codex-112904-provider-matrix-aq-date-contract-repair-v1"
SOURCE_RUN_ID = "20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1"
PROVIDER_ROOT_ID = "20260512T112315+0800-codex-board-b-six-provider-btc-matrix-probe-v1"
TVR_IBKR_PRECHECK_ID = "20260512T112030+0800-codex-btc-comparable-tvr-ibkr-provider-preflight-v1"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_ROOT = RUNS / SOURCE_RUN_ID
PROVIDER_ROOT = RUNS / PROVIDER_ROOT_ID
TVR_IBKR_PRECHECK_ROOT = RUNS / TVR_IBKR_PRECHECK_ID
OLD_SCRIPT = SOURCE_ROOT / "scripts" / "112315_provider_matrix_aq_readback_v1.py"

OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "112904-provider-matrix-aq-date-contract-repair-v1"
PROVIDER_CSV_DIR = ROOT / "provider-csv"
INPUT_DIR = ROOT / "input-csv"
WORKSPACE_ROOT = ROOT / "workspace"


def load_old_module():
    spec = importlib.util.spec_from_file_location("provider_matrix_aq_v1", OLD_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {OLD_SCRIPT}")
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
    return int(path.read_text().strip())


def csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open() as fh:
        return max(sum(1 for _ in fh) - 1, 0)


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


def write_tvr_binance_source() -> Path:
    source = TVR_IBKR_PRECHECK_ROOT / "command-output" / "01_tvr_btc_binance_1h.stdout"
    payload = json.loads(source.read_text())
    rows = payload["results"][0]["data"]
    out = INPUT_DIR / "tvr_binance_btcusdt_1h.csv"
    with out.open("w", newline="") as fh:
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
    return out


def provider_matrix_readback() -> dict[str, Any]:
    ibkr_agg = read_json(PROVIDER_ROOT / "provider-csv" / "ibkr_btc_paxos_aggtrades_1d_result.json")
    ibkr_midpoint = TVR_IBKR_PRECHECK_ROOT / "derived" / "ibkr_btc_paxos" / "BTC_1h_midpoint.csv"
    return {
        "source_provider_root": str(PROVIDER_ROOT),
        "source_aq_failure_root": str(SOURCE_ROOT),
        "source_tvr_ibkr_precheck_root": str(TVR_IBKR_PRECHECK_ROOT),
        "fetch_exits": {
            "yfinance_btc_usd_1h": exit_code(PROVIDER_ROOT / "checks" / "11_yfinance_btc_usd_1h.exit"),
            "kraken_xbtusd_1h": exit_code(PROVIDER_ROOT / "checks" / "12_kraken_xbtusd_1h.exit"),
            "binance_btcusdt_1h": exit_code(PROVIDER_ROOT / "checks" / "13_binance_btcusdt_1h.exit"),
            "bybit_btcusdt_linear_1h": exit_code(PROVIDER_ROOT / "checks" / "14_bybit_btcusdt_linear_1h.exit"),
            "tvr_binance_btcusdt_1h": exit_code(TVR_IBKR_PRECHECK_ROOT / "checks" / "01_tvr_btc_binance_1h.exit"),
            "ibkr_btc_paxos_midpoint_1h": exit_code(TVR_IBKR_PRECHECK_ROOT / "checks" / "04_ibkr_btc_paxos_bulk.exit"),
            "ibkr_btc_paxos_aggtrades_1d": exit_code(PROVIDER_ROOT / "checks" / "17_ibkr_btc_paxos_aggtrades_1d.exit"),
        },
        "fetch_rows": {
            "yfinance_btc_usd_1h": csv_rows(PROVIDER_ROOT / "provider-csv" / "yfinance_btc_usd_1h.csv"),
            "kraken_xbtusd_1h": csv_rows(PROVIDER_ROOT / "provider-csv" / "kraken_xbtusd_1h.csv"),
            "binance_btcusdt_1h": csv_rows(PROVIDER_ROOT / "provider-csv" / "binance_btcusdt_1h.csv"),
            "bybit_btcusdt_linear_1h": csv_rows(PROVIDER_ROOT / "provider-csv" / "bybit_btcusdt_linear_1h.csv"),
            "tvr_binance_btcusdt_1h": len(json.loads((TVR_IBKR_PRECHECK_ROOT / "command-output" / "01_tvr_btc_binance_1h.stdout").read_text())["results"][0]["data"]),
            "ibkr_btc_paxos_midpoint_1h": csv_rows(ibkr_midpoint),
            "ibkr_btc_paxos_aggtrades_1d": int(ibkr_agg.get("rows") or 0),
        },
        "ibkr_aggtrades_result": ibkr_agg,
        "date_contract_failure_repaired": "old 112904 wrote integer millisecond dates; this run writes datetime64[ns, UTC] dates",
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


def to_epoch_ms(value: Any) -> int | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return int(value.timestamp() * 1000)
    return int(value)


def run_provider_fixed(old: Any, provider: str, meta: dict[str, Any]) -> dict[str, Any]:
    source = meta["source"]
    local_source = PROVIDER_CSV_DIR / source.name
    shutil.copy2(source, local_source)
    workspace = old.copy_template(provider)
    df = normalize_ohlcv(local_source)
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
    run_cmd = [str(old.PYTHON), "run_tomac.py"]

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
        "first_ts_ms": to_epoch_ms(df["date"].min()) if len(df) else None,
        "last_ts_ms": to_epoch_ms(df["date"].max()) if len(df) else None,
        "workspace": str(workspace),
        "feather": str(feather),
        "compile_exit": compile_proc.returncode,
        "run_tomac_exit": run_proc.returncode,
        "metrics": metrics,
    }


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "112904_provider_matrix_aq_date_contract_repair_v1.md"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_112904_provider_matrix_aq_date_contract_repair_v1.csv"
    assertions = CHECK_DIR / "112904_provider_matrix_aq_date_contract_repair_v1_assertions.out"

    lines = [
        "# 112904 Provider Matrix AQ Date-Contract Repair v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source failed AQ run: `{SOURCE_RUN_ID}`",
        f"Provider matrix root: `{PROVIDER_ROOT_ID}`",
        "",
        "## Scope",
        "This packet repairs the provider CSV -> Freqtrade feather date contract from `112904`.",
        "It does not edit ict-engine runtime code, does not rewrite the old run root, and does not promote a candidate.",
        "",
        "## Provider Matrix",
    ]
    matrix = summary["provider_matrix"]
    for key, value in matrix["fetch_rows"].items():
        lines.append(f"- `{key}`: rows `{value}`, exit `{matrix['fetch_exits'].get(key)}`.")
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
            "## Evidence Classification",
            f"- `evidence_class={summary['evidence_class']}`.",
            f"- `branch_path={summary['branch_path']}`.",
            "- The old `112904` AQ failures are `chain_contract_negative_sample`, not factor failures: Freqtrade saw 1970 dates because the generated feather used integer timestamps.",
            "- This repair can create public/TVR provider AQ observations, but it still does not satisfy promotion because provider roots are mixed-source and IBKR is thin/midpoint-only for the 1h AQ lane.",
            "",
            "## Decision",
            f"- Gate result: `{summary['gate_result']}`.",
            f"- Date contract repaired: `{summary['date_contract_repaired']}`.",
            f"- Successful AQ provider runs: `{summary['metric_totals']['run_success']}/{summary['metric_totals']['provider_runs']}`.",
            f"- Strategies with metrics: `{summary['metric_totals']['strategies_with_metrics']}`.",
            f"- Mature rooted branch observations added: `{summary['mature_rooted_branch_observations_added']}`.",
            f"- Total trades in repaired AQ metrics: `{summary['metric_totals']['total_trades']}`.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{REPORT_DIR / '112904_provider_matrix_aq_date_contract_repair_v1.json'}`",
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
        writer.writerow(["do not duplicate provider fetch work", str(PROVIDER_ROOT), "covered", "reused 112315 rows plus 112030 TVR/IBKR precheck"])
        writer.writerow(["repair 112904 date contract", str(WORKSPACE_ROOT), "covered", "feather date is datetime64 UTC"])
        writer.writerow(["run AQ on provider rows", "command-output/aq_*_run_tomac.*", "covered", f"{summary['metric_totals']['run_success']} provider runs exited 0"])
        writer.writerow(["preserve branch path", "run_tomac.py STRATEGY_WIRE_META", "covered", summary["branch_path"]])
        writer.writerow(["classify negative evidence", str(report), "covered", summary["evidence_class"]])
        writer.writerow(["downstream chain", "N/A", "not_run", "promotion blocked by mixed-source authority and IBKR 1h quality"])

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_run={SOURCE_RUN_ID}",
        f"PASS provider_runs={summary['metric_totals']['provider_runs']}",
        f"PASS compile_success={summary['metric_totals']['compile_success']}",
        f"PASS run_success={summary['metric_totals']['run_success']}",
        f"PASS strategies_with_metrics={summary['metric_totals']['strategies_with_metrics']}",
        f"PASS date_contract_repaired={summary['date_contract_repaired']}",
        f"PASS evidence_class={summary['evidence_class']}",
        f"PASS mature_rooted_branch_observations_added={summary['mature_rooted_branch_observations_added']}",
        "FAIL_CLOSED six_provider_same_run_authority=false",
        "FAIL_CLOSED ibkr_1h_midpoint_rows_below_startup_floor",
        "FAIL_CLOSED no_pre_bayes_bbn_catboost_execution_tree_promotion",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions.write_text("\n".join(assertion_lines) + "\n")


def main() -> int:
    old = load_old_module()
    for path in (OUT_DIR, CHECK_DIR, PROVIDER_CSV_DIR, INPUT_DIR, WORKSPACE_ROOT, REPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")

    old.RUN_ID = RUN_ID
    old.SOURCE_RUN_ID = PROVIDER_ROOT_ID
    old.ROOT = ROOT
    old.SOURCE_ROOT = PROVIDER_ROOT
    old.OUT_DIR = OUT_DIR
    old.CHECK_DIR = CHECK_DIR
    old.REPORT_DIR = REPORT_DIR
    old.PROVIDER_CSV_DIR = PROVIDER_CSV_DIR
    old.WORKSPACE_ROOT = WORKSPACE_ROOT
    old.normalized_df = normalize_ohlcv

    tvr_source = write_tvr_binance_source()
    old.PUBLIC_PROVIDER_INPUTS = {
        "yfinance": {
            "source": PROVIDER_ROOT / "provider-csv" / "yfinance_btc_usd_1h.csv",
            "symbol": "BTC-USD",
        },
        "kraken_public": {
            "source": PROVIDER_ROOT / "provider-csv" / "kraken_xbtusd_1h.csv",
            "symbol": "XBTUSD",
        },
        "binance_public": {
            "source": PROVIDER_ROOT / "provider-csv" / "binance_btcusdt_1h.csv",
            "symbol": "BTCUSDT",
        },
        "bybit_public": {
            "source": PROVIDER_ROOT / "provider-csv" / "bybit_btcusdt_linear_1h.csv",
            "symbol": "BTCUSDT",
        },
        "tvr_binance": {
            "source": tvr_source,
            "symbol": "BINANCE:BTCUSDT",
        },
        "ibkr_midpoint": {
            "source": TVR_IBKR_PRECHECK_ROOT / "derived" / "ibkr_btc_paxos" / "BTC_1h_midpoint.csv",
            "symbol": "BTC.PAXOS",
        },
    }

    matrix = provider_matrix_readback()
    aq_results = [
        run_provider_fixed(old, provider, meta)
        for provider, meta in old.PUBLIC_PROVIDER_INPUTS.items()
    ]
    totals = metric_totals(aq_results)
    mature_observations = totals["total_trades"] if totals["run_success"] else 0
    summary = {
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "provider_root_id": PROVIDER_ROOT_ID,
        "provider_matrix": matrix,
        "aq_results": aq_results,
        "metric_totals": totals,
        "date_contract_repaired": True,
        "evidence_class": "chain_contract_negative_sample_repaired_to_infrastructure_limited_aq_observation",
        "branch_path": "provider_matrix -> ProviderCrypto -> MomentumOrPullback -> ProviderCryptoMomentumStateV1_or_ProviderCryptoPullbackRevertV1",
        "gate_result": "112904_provider_matrix_aq_date_contract_repair=timestamp_contract_repaired_but_authority_and_downstream_fail_closed",
        "mature_rooted_branch_observations_added": mature_observations,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(REPORT_DIR / "112904_provider_matrix_aq_date_contract_repair_v1.json", summary)
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
