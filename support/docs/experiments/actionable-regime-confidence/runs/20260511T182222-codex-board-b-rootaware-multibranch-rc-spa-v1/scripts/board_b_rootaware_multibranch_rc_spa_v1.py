#!/usr/bin/env python3
"""Run RootAwareMultiBranchV1 through Board B branch-path RC-SPA scoring."""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[6]
HELPER_SCRIPT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T181445-codex-board-b-volbreakoutsized-branch-rc-spa-v1/"
    "scripts/board_b_volbreakoutsized_branch_rc_spa_v1.py"
)

spec = importlib.util.spec_from_file_location("vol_helper", HELPER_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot import helper script: {HELPER_SCRIPT}")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
base = helper.base


RUN_ID = "20260511T182222+0800-codex-board-b-rootaware-multibranch-rc-spa-v1"
STRATEGY_NAME = "RootAwareMultiBranchV1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182222-codex-board-b-rootaware-multibranch-rc-spa-v1"
)
OUT_DIR = RUN_ROOT / "branch-rc-spa"
CHECK_DIR = RUN_ROOT / "checks"
LOG_DIR = RUN_ROOT / "logs"
STRATEGY_DIR = RUN_ROOT / "strategies"
TRADES_CSV = OUT_DIR / "rootaware_multibranch_trades_v1.csv"
TRADES_JSONL = OUT_DIR / "rootaware_multibranch_trades_v1.jsonl"
LABELS_JSONL = OUT_DIR / "rootaware_multibranch_purged_cv_labels_v1.jsonl"
SUMMARY_JSON = OUT_DIR / "rootaware_multibranch_summary_v1.json"
RC_SPA_JSON = OUT_DIR / "rootaware_multibranch_rc_spa_report_v1.json"
PAYOFF_JSON = OUT_DIR / "rootaware_multibranch_payoff_shape_v1.json"
PURGED_JSON = OUT_DIR / "rootaware_multibranch_purged_cv_guard_v1.json"
PACKET_JSON = OUT_DIR / "rootaware_multibranch_profitability_packet_v1.json"
IMPORT_MANIFEST = OUT_DIR / "rootaware_multibranch_strategy_library_for_import_v1.json"
REPORT_MD = OUT_DIR / "rootaware_multibranch_rc_spa_v1.md"
ASSERTIONS = CHECK_DIR / "board_b_rootaware_multibranch_rc_spa_v1_assertions.out"

AUTO_QUANT_ROOT = Path("/Users/thrill3r/Auto-Quant")
STRATEGY_FILE = STRATEGY_DIR / f"{STRATEGY_NAME}.py"
PAIR_BASKET = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "AVAX/USDT"]
ROOT_TO_SUB_REGIME = {
    "Bull": "TrendExpansion",
    "Bear": "SuppressBearRootNoTrade",
    "Sideways": "SuppressSidewaysRootNoTrade",
    "Crisis": "SuppressCrisisRootNoTrade",
}
SUPPRESS_PATHS = {
    "Bear": "Bear -> SuppressBearRootNoTrade -> NoPositiveEdge -> no_trade",
    "Sideways": "Sideways -> SuppressSidewaysRootNoTrade -> NoPositiveEdge -> no_trade",
    "Crisis": "Crisis -> SuppressCrisisRootNoTrade -> TailRiskSuppression -> no_trade",
}
SUB_SUB_FACTOR = "Donchian24Ema4hTrendVolumeVolTarget"
PROFIT_FAMILY = "RootAwareTrendBreakoutSuppressNonBull"
PROFIT_LEAF = STRATEGY_NAME


def install_constants() -> None:
    values = {
        "RUN_ID": RUN_ID,
        "RUN_ROOT": RUN_ROOT,
        "OUT_DIR": OUT_DIR,
        "CHECK_DIR": CHECK_DIR,
        "LOG_DIR": LOG_DIR,
        "TRADES_CSV": TRADES_CSV,
        "TRADES_JSONL": TRADES_JSONL,
        "LABELS_JSONL": LABELS_JSONL,
        "SUMMARY_JSON": SUMMARY_JSON,
        "RC_SPA_JSON": RC_SPA_JSON,
        "PAYOFF_JSON": PAYOFF_JSON,
        "PURGED_JSON": PURGED_JSON,
        "PACKET_JSON": PACKET_JSON,
        "IMPORT_MANIFEST": IMPORT_MANIFEST,
        "REPORT_MD": REPORT_MD,
        "ASSERTIONS": ASSERTIONS,
        "AUTO_QUANT_ROOT": AUTO_QUANT_ROOT,
        "AUTO_QUANT_STRATEGY_PATH": STRATEGY_DIR,
        "STRATEGY_FILE": STRATEGY_FILE,
        "PAIR_BASKET": PAIR_BASKET,
        "ROOT_TO_SUB_REGIME": ROOT_TO_SUB_REGIME,
        "SUB_SUB_FACTOR": SUB_SUB_FACTOR,
        "PROFIT_FAMILY": PROFIT_FAMILY,
        "PROFIT_LEAF": PROFIT_LEAF,
    }
    for name, value in values.items():
        setattr(helper, name, value)
        setattr(base, name, value)
    helper.STRATEGY_NAME = STRATEGY_NAME


def patch_suppression_paths(rc_spa: dict) -> None:
    for root, path in SUPPRESS_PATHS.items():
        if root in rc_spa["branch_summary"] and not rc_spa["branch_summary"][root]["branch_path"]:
            rc_spa["branch_summary"][root]["branch_path"] = path


def build_import_manifest(full_result: dict) -> dict:
    commit = base.subprocess.check_output(
        ["git", "-C", str(AUTO_QUANT_ROOT), "rev-parse", "--short", "HEAD"],
        text=True,
    ).strip()
    return {
        "manifest_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "auto_quant_repo_url": str(AUTO_QUANT_ROOT),
        "auto_quant_pinned_ref": commit,
        "config_path": str(AUTO_QUANT_ROOT / "config.json"),
        "timeframe": "1h",
        "log_path": full_result["log_path"],
        "strategies": [
            {
                "name": STRATEGY_NAME,
                "file_path": str(STRATEGY_FILE),
                "metadata": {
                    "strategy": STRATEGY_NAME,
                    "mutation_id": "board-b-rootaware-multibranch-rc-spa-v1",
                    "base_factor": "volbreakoutsized_bull_branch_with_source_root_gate",
                    "hypothesis": "Use Board A/source root as first branch key: trade Bull trend-expansion breakouts and suppress Bear/Sideways/Crisis roots.",
                    "paradigm": "root-aware trend breakout with explicit non-bull suppression",
                    "expected_regime": "Bull",
                    "factors_used": [
                        "market_regime_context.root",
                        "source_root_is_bull",
                        "donchian_high_24",
                        "ema50_4h_gt_ema200_4h",
                        "volume_sma20",
                        "atr_pct_4h_vol_target",
                        "regime_profit_branch_path",
                    ],
                    "parent": "VolBreakoutSized",
                    "asset_class": "crypto_spot",
                    "status": "active",
                    "created": commit,
                },
                "status": "ok",
                "validation_metrics": full_result["aggregate_metrics"],
                "per_pair_metrics": full_result["per_pair_metrics"],
                "pairs": list(PAIR_BASKET),
                "timerange": "20210101-20251231",
                "commit": commit,
                "error": None,
            }
        ],
        "validation_errors": [],
    }


def write_report(summary: dict, rc_spa: dict, timerange_results: list[dict]) -> None:
    lines = [
        "# RootAwareMultiBranchV1 Branch RC-SPA v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Inputs",
        "",
        f"- Board B: `{base.BOARD_B}`",
        f"- Board A consumer map: `{base.BOARD_A_MAP}`",
        f"- Board A market context: `{base.BOARD_A_CONTEXT}`",
        f"- Source regime CSV: `{base.SOURCE_REGIME_CSV}`",
        f"- Strategy file: `{STRATEGY_FILE}`",
        "",
        "## Auto-Quant Backtest Readback",
        "",
        "| Segment | Timerange | Trades | Win rate % | Profit % | Sharpe | Log |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for result in timerange_results:
        metrics = result["aggregate_metrics"]
        lines.append(
            f"| `{result['label']}` | `{result['timerange']}` | {metrics['trade_count']} | "
            f"{metrics['win_rate_pct']:.3f} | {metrics['total_profit_pct']:.3f} | "
            f"{metrics['sharpe']:.4f} | `{result['log_path']}` |"
        )
    lines.extend([
        "",
        "## Branch Summary",
        "",
        "| Root | Trades | Win rate % | Net R | Mean R | Edge LCB 5% | 2x cost net R | Branch path |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ])
    for root, payload in rc_spa["branch_summary"].items():
        lines.append(
            f"| `{root}` | {payload['trade_count']} | {base._pct(payload['win_rate']):.3f} | "
            f"{payload['net_return_R']:.6f} | {payload['mean_R']:.6f} | "
            f"{payload['bootstrap_edge_lcb_5pct']:.6f} | {payload['stressed_2x_cost_net_R']:.6f} | "
            f"`{payload['branch_path']}` |"
        )
    lines.extend([
        "",
        "## RC-SPA Decision",
        "",
        f"- RC-SPA: `{rc_spa['rc_spa']:.3f}`",
        f"- Promotion level: `{rc_spa['promotion_level']}`",
        f"- Failure reasons: `{', '.join(rc_spa['failure_reasons']) if rc_spa['failure_reasons'] else 'none'}`",
        f"- Total trades: `{rc_spa['total_trades']}`",
        f"- Fold positive rate: `{rc_spa['fold_positive_rate']:.3f}`",
        f"- PBO: `{rc_spa['pbo']:.3f}`",
        f"- DSR: `{rc_spa['dsr']:.3f}`",
        f"- Tail loss abs p95: `{rc_spa['tail_loss_p95_abs']:.6f}` vs budget `{rc_spa['tail_loss_budget_abs']}`",
        "",
        "## Artifacts",
        "",
        f"- Trades CSV: `{TRADES_CSV}`",
        f"- Summary JSON: `{SUMMARY_JSON}`",
        f"- RC-SPA JSON: `{RC_SPA_JSON}`",
        f"- Profitability packet: `{PACKET_JSON}`",
        f"- Import manifest: `{IMPORT_MANIFEST}`",
    ])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    install_constants()
    for path in [OUT_DIR, CHECK_DIR, LOG_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    if not STRATEGY_FILE.exists():
        raise FileNotFoundError(STRATEGY_FILE)

    timerange_results = [helper.run_backtest(label, timerange) for label, timerange in base.TIMERANGES]
    full_result = next(result for result in timerange_results if result["label"] == "full_5y")
    lookup = base.SourceRegimeLookup(base.SOURCE_REGIME_CSV)
    root_confidence = base.load_root_confidence()
    rows = [base.trade_to_row(trade, lookup, root_confidence) for trade in full_result["trades"]]
    base.write_rows(rows)
    payoff, purged = base.call_research_reports()
    rc_spa = base.build_rc_spa(rows, payoff, purged)
    patch_suppression_paths(rc_spa)

    summary = {
        "schema_version": "board-b-rootaware-multibranch-summary/v1",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "board_b": str(base.BOARD_B),
            "board_a_map": str(base.BOARD_A_MAP),
            "board_a_context": str(base.BOARD_A_CONTEXT),
            "source_regime_csv": str(base.SOURCE_REGIME_CSV),
            "auto_quant_root": str(AUTO_QUANT_ROOT),
            "strategy_file": str(STRATEGY_FILE),
        },
        "timerange_results": [{k: v for k, v in result.items() if k != "trades"} for result in timerange_results],
        "full_5y_trade_count": len(rows),
        "root_coverage": {root: sum(1 for row in rows if row["parent_regime_root"] == root) for root in base.ROOTS},
        "root_lookup_status_counts": pd.Series([row["root_lookup_status"] for row in rows]).value_counts().to_dict() if rows else {},
        "manipulation_overlay_state": "not_present_no_direct_source_match",
        "suppressed_roots": sorted(SUPPRESS_PATHS),
    }
    packet = {
        "schema_version": "regime-profitability-packet/v1",
        "run_id": RUN_ID,
        "accepted_regime_id": rc_spa["accepted_regime_id"],
        "recipe_id": STRATEGY_NAME,
        "recipe_artifact_path": str(STRATEGY_FILE),
        "backtest_artifact_path": str(TRADES_CSV),
        "total_trades": rc_spa["total_trades"],
        "test_folds": rc_spa["test_folds"],
        "fold_positive_rate": rc_spa["fold_positive_rate"],
        "bootstrap_edge_lcb_5pct": rc_spa["bootstrap_edge_lcb_5pct"],
        "pbo": rc_spa["pbo"],
        "dsr": rc_spa["dsr"],
        "cost_stress_result": "pass" if rc_spa["cost_stress_survival"] else "fail",
        "tail_loss_p95": rc_spa["tail_loss_p95_abs"],
        "regime_specificity_ratio": rc_spa["regime_specificity_ratio"],
        "rc_spa": rc_spa["rc_spa"],
        "promotion_level": rc_spa["promotion_level"],
        "downstream_consumption_status": "not_started_rc_spa_rejected" if rc_spa["promotion_level"] == "reject" else "not_started_rc_spa_candidate",
        "branch_summary": rc_spa["branch_summary"],
        "hard_gates": rc_spa["hard_gates"],
        "failure_reasons": rc_spa["failure_reasons"],
    }

    base._write_json(SUMMARY_JSON, summary)
    base._write_json(RC_SPA_JSON, rc_spa)
    base._write_json(PACKET_JSON, packet)
    base._write_json(IMPORT_MANIFEST, build_import_manifest(full_result))
    write_report(summary, rc_spa, timerange_results)
    ASSERTIONS.write_text(
        "\n".join([
            f"run_id={RUN_ID}",
            f"strategy={STRATEGY_NAME}",
            f"auto_quant_backtest_full_5y_trades={len(rows)}",
            f"branch_path_present={rc_spa['hard_gates']['branch_path_present']}",
            f"root_lookup_coverage_full={rc_spa['hard_gates']['root_lookup_coverage_full']}",
            f"rc_spa={rc_spa['rc_spa']:.6f}",
            f"promotion_level={rc_spa['promotion_level']}",
            f"failure_reasons={','.join(rc_spa['failure_reasons'])}",
            f"trades_csv={TRADES_CSV}",
            f"packet_json={PACKET_JSON}",
            f"import_manifest={IMPORT_MANIFEST}",
        ])
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "ok": True,
        "run_id": RUN_ID,
        "strategy": STRATEGY_NAME,
        "trades": len(rows),
        "rc_spa": rc_spa["rc_spa"],
        "promotion_level": rc_spa["promotion_level"],
        "failure_reasons": rc_spa["failure_reasons"],
        "report": str(REPORT_MD),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
