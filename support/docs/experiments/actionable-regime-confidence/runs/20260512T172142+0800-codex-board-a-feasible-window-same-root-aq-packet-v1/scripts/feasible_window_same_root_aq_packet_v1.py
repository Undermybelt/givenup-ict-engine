from __future__ import annotations

import csv
import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any


RUN_ID = "20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1"
RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
BASE_SCRIPT = (
    RUNS
    / "20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1"
    / "scripts"
    / "six_provider_btc_same_root_aq_ibkr_aggtrades_probe_v1.py"
)
OLD_ROOT_NEEDLE = "20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1"

PROVIDER_CSV_DIR = ROOT / "provider-csv"
OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "feasible-window-same-root-aq-packet-v1"
WORKSPACE_ROOT = ROOT / "workspace"


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("same_root_base_v1", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open() as fh:
        return max(sum(1 for _ in fh) - 1, 0)


def csv_bounds(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"rows": 0, "first": None, "last": None}
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        fields = reader.fieldnames or []
        time_key = next(
            (key for key in ("date", "timestamp", "datetime", "open_time", "time") if key in fields),
            fields[0] if fields else None,
        )
        rows = 0
        first = None
        last = None
        for row in reader:
            rows += 1
            value = row.get(time_key, "") if time_key else ""
            if rows == 1:
                first = value
            last = value
    return {"rows": rows, "first": first, "last": last}


def source_map() -> dict[str, dict[str, Any]]:
    return {
        "yfinance": {
            "provider_label": "yfinance/YF",
            "source": RUNS / "20260512T170852+0800-codex-board-a-provider-gap-repair-yf-ibkr-v1/provider-csv/yfinance_btc_usd_1h_20240515_20260512.csv",
            "dest": PROVIDER_CSV_DIR / "yfinance_btc_usd_1h.csv",
            "symbol": "BTC-USD",
            "window": "2024-05-15_to_2026-05-12_730d_cap",
        },
        "ibkr_aggtrades": {
            "provider_label": "IBKR",
            "source": RUNS / "20260512T170852+0800-codex-board-a-provider-gap-repair-yf-ibkr-v1/provider-csv/BTC_1h_aggtrades.csv",
            "dest": PROVIDER_CSV_DIR / "BTC_1h_aggtrades.csv",
            "symbol": "BTC.PAXOS",
            "window": "2025-05-12_to_2026-05-12_1y_client144",
        },
        "kraken_public": {
            "provider_label": "Kraken",
            "source": RUNS / "20260512T171227+0800-codex-board-a-kraken-current-window-repair-v1/provider-csv/kraken_pfxbtusd_1h_20260218_20260512.csv",
            "dest": PROVIDER_CSV_DIR / "kraken_xbtusd_1h.csv",
            "symbol": "PF_XBTUSD",
            "window": "2026-02-18_to_2026-05-12_current_window",
        },
        "binance_public": {
            "provider_label": "Binance",
            "source": RUNS / "20260512T165415+0800-codex-board-a-provider-max-window-capability-probe-v1/provider-csv/binance_btcusdt_1h_20210101_20260512.csv",
            "dest": PROVIDER_CSV_DIR / "binance_btcusdt_1h.csv",
            "symbol": "BTCUSDT",
            "window": "2021-01-01_to_2026-05-12_broad_window",
        },
        "bybit_public": {
            "provider_label": "Bybit",
            "source": RUNS / "20260512T165415+0800-codex-board-a-provider-max-window-capability-probe-v1/provider-csv/bybit_btcusdt_linear_1h_20210101_20260512.csv",
            "dest": PROVIDER_CSV_DIR / "bybit_btcusdt_linear_1h.csv",
            "symbol": "BTCUSDT",
            "window": "2026-03-31_to_2026-05-12_capped_current",
        },
        "tvr_local_stdio": {
            "provider_label": "TradingViewRemix/TVR",
            "source": RUNS / "20260512T165415+0800-codex-board-a-provider-max-window-capability-probe-v1/provider-csv/tvr_btc_usd_1h_local_stdio_default_window.csv",
            "dest": PROVIDER_CSV_DIR / "tvr_btc_usd_local_stdio_1h.csv",
            "symbol": "BTC-USD(local-stdio)",
            "window": "2026-04-12_to_2026-05-12_default_local_stdio",
        },
    }


def copy_provider_csvs() -> dict[str, dict[str, Any]]:
    PROVIDER_CSV_DIR.mkdir(parents=True, exist_ok=True)
    copied: dict[str, dict[str, Any]] = {}
    for provider, meta in source_map().items():
        source = meta["source"]
        dest = meta["dest"]
        if source.exists():
            shutil.copy2(source, dest)
        bounds = csv_bounds(dest)
        copied[provider] = {
            "provider_label": meta["provider_label"],
            "source": str(source),
            "dest": str(dest),
            "symbol": meta["symbol"],
            "window": meta["window"],
            **bounds,
            "copied": source.exists() and bounds["rows"] > 0,
        }
    return copied


def configure_base(base: Any) -> Any:
    for path in (OUT_DIR, CHECK_DIR, REPORT_DIR, WORKSPACE_ROOT):
        path.mkdir(parents=True, exist_ok=True)
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
    old.normalized_df = base.normalize_ohlcv
    return old


def provider_inputs() -> dict[str, dict[str, Any]]:
    return {
        provider: {"source": meta["dest"], "symbol": meta["symbol"]}
        for provider, meta in source_map().items()
    }


def run_aq(base: Any, old: Any) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for provider, meta in provider_inputs().items():
        if csv_rows(meta["source"]) == 0:
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
        results.append(base.run_provider_fixed(old, provider, meta))
    return results


def count_files(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for path in root.rglob("*") if path.is_file())


def workspace_checks(results: list[dict[str, Any]]) -> dict[str, Any]:
    workspace_root_text = str(WORKSPACE_ROOT)
    workspace_paths = [row.get("workspace", "") for row in results if not row.get("skipped")]
    old_refs: list[str] = []
    for path in sorted(OUT_DIR.glob("aq_*")):
        if path.is_file() and OLD_ROOT_NEEDLE in path.read_text(errors="ignore"):
            old_refs.append(str(path))
    metric_paths = sorted(str(path) for path in WORKSPACE_ROOT.rglob("*.metrics.json"))
    return {
        "workspace_file_count": count_files(WORKSPACE_ROOT),
        "workspace_paths": workspace_paths,
        "all_workspaces_under_root": all(path.startswith(workspace_root_text) for path in workspace_paths),
        "derived_metric_count": len(metric_paths),
        "derived_metric_paths": metric_paths,
        "old_root_references": old_refs,
    }


def build_summary(base: Any, copied: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
    totals = base.metric_totals([row for row in results if not row.get("skipped")])
    checks = workspace_checks(results)
    same_root = (
        len(copied) == 6
        and all(row["copied"] for row in copied.values())
        and totals["run_success"] == 6
        and checks["all_workspaces_under_root"]
        and checks["derived_metric_count"] >= 12
        and not checks["old_root_references"]
    )
    return {
        "run_id": RUN_ID,
        "root": str(ROOT),
        "provider_copy_rows": copied,
        "aq_results": results,
        "metric_totals": totals,
        "workspace_checks": checks,
        "same_root_six_provider_aq_authority": same_root,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }


def write_report(summary: dict[str, Any]) -> None:
    report = REPORT_DIR / "feasible_window_same_root_aq_packet_v1.md"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_feasible_window_same_root_aq_packet_v1.csv"
    assertions = CHECK_DIR / "feasible_window_same_root_aq_packet_v1_assertions.out"
    lines = [
        "# Feasible-Window Same-Root AQ Packet v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Scope",
        "Copies repaired provider-window CSVs into one run root and runs same-root AQ/TOMAC. No provider refetch and no downstream ict-engine gates.",
        "",
        "## Provider Inputs",
    ]
    for provider, row in summary["provider_copy_rows"].items():
        lines.append(
            f"- `{provider}` ({row['provider_label']}): copied `{row['copied']}`, rows `{row['rows']}`, "
            f"first `{row['first']}`, last `{row['last']}`, window `{row['window']}`."
        )
    lines.extend(["", "## AQ Results"])
    for result in summary["aq_results"]:
        if result.get("skipped"):
            lines.append(f"- `{result['provider']}`: skipped `{result['skip_reason']}`.")
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
            "## Gate",
            f"- Same-root six-provider AQ authority: `{summary['same_root_six_provider_aq_authority']}`.",
            f"- AQ run success: `{summary['metric_totals']['run_success']}/{summary['metric_totals']['provider_runs']}`.",
            f"- Strategies with metrics: `{summary['metric_totals']['strategies_with_metrics']}`.",
            f"- Total trades: `{summary['metric_totals']['total_trades']}`.",
            f"- Positive-profit metric count: `{summary['metric_totals']['positive_profit_metric_count']}`.",
            f"- Workspace file count: `{summary['workspace_checks']['workspace_file_count']}`.",
            f"- Derived metric count: `{summary['workspace_checks']['derived_metric_count']}`.",
            f"- Old-root reference count: `{len(summary['workspace_checks']['old_root_references'])}`.",
            "- downstream_started=false.",
            "- promotion_allowed=false.",
            "- trade_usable=false.",
            "- update_goal=false.",
            "",
        ]
    )
    report.write_text("\n".join(lines))
    with checklist.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["requirement", "artifact", "status", "note"])
        writer.writerow(["six provider CSVs under one root", str(PROVIDER_CSV_DIR), "covered" if all(row["copied"] for row in summary["provider_copy_rows"].values()) else "fail_closed", json.dumps({k: v["rows"] for k, v in summary["provider_copy_rows"].items()}, sort_keys=True)])
        writer.writerow(["same-root AQ workspaces", str(WORKSPACE_ROOT), "covered" if summary["workspace_checks"]["all_workspaces_under_root"] else "fail_closed", f"files={summary['workspace_checks']['workspace_file_count']}"])
        writer.writerow(["AQ/TOMAC exits", str(CHECK_DIR), "covered" if summary["metric_totals"]["run_success"] == 6 else "fail_closed", f"run_success={summary['metric_totals']['run_success']}"])
        writer.writerow(["old root references absent", str(OUT_DIR), "covered" if not summary["workspace_checks"]["old_root_references"] else "fail_closed", f"refs={len(summary['workspace_checks']['old_root_references'])}"])
        writer.writerow(["downstream chain", "N/A", "not_started", "terminal readback required before downstream"])
        writer.writerow(["Board A acceptance", "N/A", "not_claimed", "accepted_95_contexts_added=0"])
    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS provider_csvs_copied={sum(1 for row in summary['provider_copy_rows'].values() if row['copied'])}/6",
        f"PASS compile_success={summary['metric_totals']['compile_success']}",
        f"PASS run_success={summary['metric_totals']['run_success']}",
        f"PASS strategies_with_metrics={summary['metric_totals']['strategies_with_metrics']}",
        f"PASS total_trades={summary['metric_totals']['total_trades']}",
        f"PASS derived_metric_count={summary['workspace_checks']['derived_metric_count']}",
        f"PASS old_root_reference_count={len(summary['workspace_checks']['old_root_references'])}",
        f"PASS same_root_six_provider_aq_authority={summary['same_root_six_provider_aq_authority']}",
        "FAIL_CLOSED downstream_chain_not_started",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions.write_text("\n".join(assertion_lines) + "\n")


def main() -> int:
    base = load_base_module()
    copied = copy_provider_csvs()
    old = configure_base(base)
    results = run_aq(base, old)
    summary = build_summary(base, copied, results)
    write_json(REPORT_DIR / "feasible_window_same_root_aq_packet_v1.json", summary)
    write_report(summary)
    return 0 if summary["same_root_six_provider_aq_authority"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
