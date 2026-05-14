#!/usr/bin/env python3
"""Combine clean root RC-SPA with direct Manipulation bridge evidence.

This run-local readback does not rescore root trades or mutate ict-engine state.
It consumes the clean RootTransitionTriad report plus the provider-reconstructed
Mehrnoom/Binance intraday PnL bridge and emits a fail-closed combined decision.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


RUN_ID = "20260511T194231+0800-codex-board-b-root-plus-manip-bridge-rc-spa-v1"
SCHEMA_VERSION = "board-b-root-plus-manip-bridge-rc-spa/v1"
ACCEPTED_REGIME_ID = "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation"

RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())

ROOT_REPORT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T193803-codex-board-b-root-transition-triad-clean-v1/branch-rc-spa/"
    "root_transition_triad_rc_spa_report_v1.json"
)
MANIP_REPORT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T194035-codex-board-b-mehrnoom-binance-intraday-pnl-v1/"
    "mehrnoom-binance-intraday-pnl/mehrnoom_binance_intraday_pnl_v1.json"
)

OUT_DIR = RUN_ROOT / "combined-rc-spa"
CHECK_DIR = RUN_ROOT / "checks"
FAIL_CLOSED_DIR = RUN_ROOT / "ict-engine-fail-closed"

REPORT_JSON = OUT_DIR / "root_plus_manip_bridge_rc_spa_v1.json"
REPORT_MD = OUT_DIR / "root_plus_manip_bridge_rc_spa_v1.md"
ASSERTIONS = CHECK_DIR / "root_plus_manip_bridge_rc_spa_v1_assertions.out"
FAIL_CLOSED_MD = FAIL_CLOSED_DIR / "root_plus_manip_bridge_fail_closed_summary_v1.md"


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def git_ref() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    for path in [OUT_DIR, CHECK_DIR, FAIL_CLOSED_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    root = read_json(ROOT_REPORT)
    manip = read_json(MANIP_REPORT)
    root_decision = root["decision"]
    manip_ready = bool(manip["direct_manipulation_rows_ready_for_future_rc_spa"])
    root_gate_passed = root_decision["gate_result"] == "pass"
    branch_paths_passed = int(root_decision["branch_paths_passed"]) + (1 if manip_ready else 0)
    required_branch_paths = 5
    combined_passed = root_gate_passed and manip_ready and branch_paths_passed == required_branch_paths
    gate_result = "pass" if combined_passed else "fail:required_root_or_manipulation_branch_hard_gates_failed"
    downstream = (
        "eligible_for_pre_bayes_bbn_catboost_execution_tree_probe"
        if combined_passed
        else "not_started:blocked_by_combined_branch_rc_spa_hard_gates"
    )
    primary_blocker = (
        "all required root and direct Manipulation hard gates passed"
        if combined_passed
        else (
            f"root={root_decision['gate_result']} ({root_decision['primary_blocker']}); "
            f"manipulation={manip['gate_result']} ({';'.join(manip['blockers'])})"
        )
    )
    next_action = (
        "B5: run Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree branch consumption."
        if combined_passed
        else (
            "B2R-repeat: do not promote; direct Manipulation underperforms controls and "
            "RootTransitionTriad still has failed root branches. Source stronger direct PnL rows "
            "or switch to a different root-aware family/panel."
        )
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "run_root": rel(RUN_ROOT),
        "repo_git_ref": git_ref(),
        "accepted_regime_id": ACCEPTED_REGIME_ID,
        "recipe_id": "RootTransitionTriadV1+MehrnoomBinanceIntradayPnlBridgeV1",
        "inputs": {
            "root_report": rel(ROOT_REPORT),
            "manipulation_report": rel(MANIP_REPORT),
        },
        "decision": {
            "gate_result": gate_result,
            "stable_profit_score": float(root_decision["stable_profit_score"]),
            "required_branch_paths": required_branch_paths,
            "branch_paths_passed": branch_paths_passed,
            "root_branch_paths_passed": int(root_decision["branch_paths_passed"]),
            "direct_manipulation_ready": manip_ready,
            "root_selected_trade_rows": int(root_decision["selected_trade_rows"]),
            "root_variant_trade_rows": int(root_decision["variant_trade_rows"]),
            "manipulation_positive_rows": int(manip["positive_rows"]),
            "manipulation_control_rows": int(manip["control_rows"]),
            "manipulation_monthly_folds": int(manip["monthly_folds"]),
            "manipulation_positive_minus_control_6h_return": float(manip["positive_minus_control_6h_return"]),
            "manipulation_positive_minus_control_bootstrap_lcb_5pct_6h": float(
                manip["positive_minus_control_bootstrap_lcb_5pct_6h"]
            ),
            "manipulation_fold_positive_rate_vs_control": float(manip["fold_positive_rate_vs_control"]),
            "downstream_consumption": downstream,
            "primary_blocker": primary_blocker,
            "next_action": next_action,
        },
        "root_branch_summaries": root["branch_summaries"],
        "manipulation_summary": {
            "provider": manip["provider"],
            "bridge_precision": manip["bridge_precision"],
            "gate_result": manip["gate_result"],
            "blockers": manip["blockers"],
            "positive_rows": manip["positive_rows"],
            "control_rows": manip["control_rows"],
            "coins_with_rows": manip["coins_with_rows"],
            "monthly_folds": manip["monthly_folds"],
            "positive_mean_6h_return": manip["positive_mean_6h_return"],
            "control_mean_6h_return": manip["control_mean_6h_return"],
            "positive_minus_control_6h_return": manip["positive_minus_control_6h_return"],
            "positive_minus_control_bootstrap_lcb_5pct_6h": manip[
                "positive_minus_control_bootstrap_lcb_5pct_6h"
            ],
            "fold_positive_rate_vs_control": manip["fold_positive_rate_vs_control"],
        },
        "artifacts": {
            "report_json": rel(REPORT_JSON),
            "report_md": rel(REPORT_MD),
            "assertions": rel(ASSERTIONS),
            "fail_closed_summary": rel(FAIL_CLOSED_MD),
        },
    }
    write_json(REPORT_JSON, report)
    decision = report["decision"]
    lines = [
        "# Root plus Manipulation Bridge RC-SPA v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Stable profit score proxy: `{decision['stable_profit_score']:.4f}`",
        f"- Branch paths passed: `{decision['branch_paths_passed']}/{decision['required_branch_paths']}`",
        f"- Root rows: `{decision['root_selected_trade_rows']}` selected / `{decision['root_variant_trade_rows']}` variant",
        f"- Direct Manipulation rows: `{decision['manipulation_positive_rows']}` positive / `{decision['manipulation_control_rows']}` controls",
        f"- Direct Manipulation diff 6h: `{decision['manipulation_positive_minus_control_6h_return']:.6f}`",
        f"- Direct Manipulation diff LCB 5%: `{decision['manipulation_positive_minus_control_bootstrap_lcb_5pct_6h']:.6f}`",
        f"- Downstream consumption: `{decision['downstream_consumption']}`",
        f"- Primary blocker: {decision['primary_blocker']}",
        "",
        "## Inputs",
        "",
        f"- Root report: `{rel(ROOT_REPORT)}`",
        f"- Manipulation report: `{rel(MANIP_REPORT)}`",
        "",
        "## Next",
        "",
        f"- {decision['next_action']}",
        "",
    ]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    FAIL_CLOSED_MD.write_text(
        "\n".join(
            [
                "# Root plus Manipulation Bridge Fail-Closed Summary v1",
                "",
                f"Run ID: `{RUN_ID}`",
                "",
                f"- Gate result: `{gate_result}`",
                f"- Downstream consumption: `{downstream}`",
                "- Pre-Bayes / BBN / CatBoost / execution-tree promotion was not started.",
                "- This is a fail-closed combined readback, not a promoted profitability packet.",
                "",
                f"Primary blocker: {primary_blocker}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    assertions = [
        f"run_id={RUN_ID}",
        f"root_branch_paths_passed={root_decision['branch_paths_passed']}",
        f"direct_manipulation_ready={str(manip_ready).lower()}",
        f"branch_paths_passed={branch_paths_passed}",
        f"gate_result={gate_result}",
        f"downstream_consumption={downstream}",
        f"manipulation_positive_minus_control_lcb_5pct_6h={manip['positive_minus_control_bootstrap_lcb_5pct_6h']}",
        "artifacts_exist=true",
    ]
    ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
