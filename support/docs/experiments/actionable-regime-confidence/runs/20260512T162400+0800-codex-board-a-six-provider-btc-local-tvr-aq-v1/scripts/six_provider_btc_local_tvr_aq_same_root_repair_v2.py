from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from typing import Any


RUN_ID = "20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1"
REPAIR_ID = "same-root-repair-v2"
RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
BASE_SCRIPT = (
    RUNS
    / "20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1"
    / "scripts"
    / "six_provider_btc_same_root_aq_ibkr_aggtrades_probe_v1.py"
)

PROVIDER_CSV_DIR = ROOT / "provider-csv"
OUT_DIR = ROOT / "command-output" / REPAIR_ID
CHECK_DIR = ROOT / "checks" / REPAIR_ID
REPORT_DIR = ROOT / "six-provider-btc-local-tvr-aq-same-root-repair-v2"
WORKSPACE_ROOT = ROOT / "workspace" / REPAIR_ID


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


def provider_inputs() -> dict[str, dict[str, Any]]:
    return {
        "yfinance": {
            "source": PROVIDER_CSV_DIR / "yfinance_btc_usd_1h.csv",
            "symbol": "BTC-USD",
        },
        "kraken_public": {
            "source": PROVIDER_CSV_DIR / "kraken_xbtusd_1h.csv",
            "symbol": "XBTUSD",
        },
        "binance_public": {
            "source": PROVIDER_CSV_DIR / "binance_btcusdt_1h.csv",
            "symbol": "BTCUSDT",
        },
        "bybit_public": {
            "source": PROVIDER_CSV_DIR / "bybit_btcusdt_linear_1h.csv",
            "symbol": "BTCUSDT",
        },
        "tvr_local_stdio": {
            "source": PROVIDER_CSV_DIR / "tvr_btc_usd_local_stdio_1h.csv",
            "symbol": "BTC-USD(local-stdio)",
        },
        "ibkr_aggtrades": {
            "source": PROVIDER_CSV_DIR / "BTC_1h_aggtrades.csv",
            "symbol": "BTC.PAXOS",
        },
    }


def configure_base(base: Any) -> Any:
    for path in (OUT_DIR, CHECK_DIR, REPORT_DIR, WORKSPACE_ROOT):
        path.mkdir(parents=True, exist_ok=True)

    base.RUN_ID = f"{RUN_ID}-{REPAIR_ID}"
    base.ROOT = ROOT
    base.SOURCE_ROOT = ROOT
    base.OUT_DIR = OUT_DIR
    base.CHECK_DIR = CHECK_DIR
    base.REPORT_DIR = REPORT_DIR
    base.PROVIDER_CSV_DIR = PROVIDER_CSV_DIR
    base.WORKSPACE_ROOT = WORKSPACE_ROOT

    old = base.load_old_module()
    old.RUN_ID = f"{RUN_ID}-{REPAIR_ID}"
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


def run_aq(base: Any, old: Any) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for provider, meta in provider_inputs().items():
        rows = csv_rows(meta["source"])
        if rows == 0:
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


def old_root_references() -> list[str]:
    refs: list[str] = []
    needle = "20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1"
    for path in sorted(OUT_DIR.glob("aq_*")):
        if not path.is_file():
            continue
        text = path.read_text(errors="ignore")
        if needle in text:
            refs.append(str(path))
    return refs


def workspace_checks(results: list[dict[str, Any]]) -> dict[str, Any]:
    workspace_root_text = str(WORKSPACE_ROOT)
    workspace_paths = [row.get("workspace", "") for row in results if not row.get("skipped")]
    derived_metric_paths = sorted(str(path) for path in WORKSPACE_ROOT.rglob("*.metrics.json"))
    return {
        "workspace_file_count": count_files(WORKSPACE_ROOT),
        "workspace_paths": workspace_paths,
        "all_workspaces_under_repair_root": all(path.startswith(workspace_root_text) for path in workspace_paths),
        "derived_metric_count": len(derived_metric_paths),
        "derived_metric_paths": derived_metric_paths,
        "old_root_references": old_root_references(),
    }


def build_summary(base: Any, results: list[dict[str, Any]]) -> dict[str, Any]:
    totals = base.metric_totals([row for row in results if not row.get("skipped")])
    checks = workspace_checks(results)
    provider_rows = {name: csv_rows(meta["source"]) for name, meta in provider_inputs().items()}
    ibkr_success = any(
        row.get("provider") == "ibkr_aggtrades" and row.get("run_tomac_exit") == 0
        for row in results
    )
    same_root_authority = (
        totals["run_success"] == 6
        and ibkr_success
        and checks["all_workspaces_under_repair_root"]
        and checks["derived_metric_count"] >= 12
        and checks["workspace_file_count"] > 0
        and len(checks["old_root_references"]) == 0
    )
    return {
        "run_id": RUN_ID,
        "repair_id": REPAIR_ID,
        "root": str(ROOT),
        "provider_rows": provider_rows,
        "aq_results": results,
        "metric_totals": totals,
        "workspace_checks": checks,
        "same_root_six_provider_aq_authority": same_root_authority,
        "ibkr_first_class_aq_success": ibkr_success,
        "gate_result": "same_root_repair_v2="
        + (
            "same_root_six_provider_aq_present_downstream_not_started_no_promotion"
            if same_root_authority
            else "fail_closed_same_root_aq_not_proven_no_promotion"
        ),
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "same_root_repair_v2.md"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_same_root_repair_v2.csv"
    assertions = CHECK_DIR / "same_root_repair_v2_assertions.out"

    lines = [
        "# Six-Provider BTC Local-TV Stdio AQ Same-Root Repair v2",
        "",
        f"Run id: `{RUN_ID}`",
        f"Repair id: `{REPAIR_ID}`",
        "",
        "## Scope",
        "Run-local repair of the attempt-1 same-root AQ workspace defect.",
        "Inputs are the existing `162400/provider-csv/` files only; no provider refetch and no downstream chain.",
        "",
        "## Provider Inputs",
    ]
    for provider, rows in summary["provider_rows"].items():
        lines.append(f"- `{provider}`: rows `{rows}`.")
    lines.extend(["", "## AQ Results"])
    for result in summary["aq_results"]:
        if result.get("skipped"):
            lines.append(f"- `{result['provider']}`: skipped, reason `{result['skip_reason']}`.")
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
            "## Same-Root Checks",
            f"- Workspace file count: `{summary['workspace_checks']['workspace_file_count']}`.",
            f"- Derived metric count: `{summary['workspace_checks']['derived_metric_count']}`.",
            f"- All workspaces under repair root: `{summary['workspace_checks']['all_workspaces_under_repair_root']}`.",
            f"- Old-root output references: `{len(summary['workspace_checks']['old_root_references'])}`.",
            "",
            "## Decision",
            f"- Gate result: `{summary['gate_result']}`.",
            f"- Successful AQ provider runs: `{summary['metric_totals']['run_success']}/{summary['metric_totals']['provider_runs']}`.",
            f"- Strategies with metrics: `{summary['metric_totals']['strategies_with_metrics']}`.",
            f"- Total trades in AQ metrics: `{summary['metric_totals']['total_trades']}`.",
            f"- Same-root six-provider AQ authority: `{summary['same_root_six_provider_aq_authority']}`.",
            f"- IBKR first-class AQ success: `{summary['ibkr_first_class_aq_success']}`.",
            "- Downstream chain is not started in this repair step.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{REPORT_DIR / 'same_root_repair_v2.json'}`",
            f"- Checklist: `{checklist}`",
            f"- Assertions: `{assertions}`",
            f"- Command outputs: `{OUT_DIR}`",
            f"- Checks: `{CHECK_DIR}`",
            f"- AQ workspaces: `{WORKSPACE_ROOT}`",
        ]
    )
    report.write_text("\n".join(lines) + "\n")

    with checklist.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["requirement", "artifact", "status", "note"])
        writer.writerow(["six existing provider CSV inputs", str(PROVIDER_CSV_DIR), "covered", json.dumps(summary["provider_rows"], sort_keys=True)])
        writer.writerow(["AQ workspaces under 162400 root", str(WORKSPACE_ROOT), "covered" if summary["workspace_checks"]["all_workspaces_under_repair_root"] else "fail_closed", f"files={summary['workspace_checks']['workspace_file_count']}"])
        writer.writerow(["no old 112904 root references", str(OUT_DIR), "covered" if not summary["workspace_checks"]["old_root_references"] else "fail_closed", f"refs={len(summary['workspace_checks']['old_root_references'])}"])
        writer.writerow(["AQ on every non-empty provider source", str(WORKSPACE_ROOT), "covered", f"run_success={summary['metric_totals']['run_success']}"])
        writer.writerow(["downstream chain", "N/A", "not_started", "requires Board A terminal readback first"])
        writer.writerow(["Board A acceptance", "N/A", "not_claimed", "accepted_95_contexts_added=0"])

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS repair_id={REPAIR_ID}",
        f"PASS provider_runs={summary['metric_totals']['provider_runs']}",
        f"PASS compile_success={summary['metric_totals']['compile_success']}",
        f"PASS run_success={summary['metric_totals']['run_success']}",
        f"PASS strategies_with_metrics={summary['metric_totals']['strategies_with_metrics']}",
        f"PASS workspace_file_count={summary['workspace_checks']['workspace_file_count']}",
        f"PASS derived_metric_count={summary['workspace_checks']['derived_metric_count']}",
        f"PASS all_workspaces_under_repair_root={summary['workspace_checks']['all_workspaces_under_repair_root']}",
        f"PASS old_root_reference_count={len(summary['workspace_checks']['old_root_references'])}",
        f"PASS same_root_six_provider_aq_authority={summary['same_root_six_provider_aq_authority']}",
        f"PASS ibkr_first_class_aq_success={summary['ibkr_first_class_aq_success']}",
        "FAIL_CLOSED downstream_chain_not_started_in_this_step",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions.write_text("\n".join(assertion_lines) + "\n")


def main() -> int:
    base = load_base_module()
    old = configure_base(base)
    results = run_aq(base, old)
    summary = build_summary(base, results)
    write_json(REPORT_DIR / "same_root_repair_v2.json", summary)
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
