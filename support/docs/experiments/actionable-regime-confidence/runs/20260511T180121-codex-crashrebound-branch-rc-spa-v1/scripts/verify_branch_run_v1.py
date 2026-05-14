#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


SCRIPT = Path(__file__).resolve()
RUN_ROOT = SCRIPT.parents[1]
CHECKS = RUN_ROOT / "checks"
BRANCH = RUN_ROOT / "branch-rc-spa"
PROVIDER = RUN_ROOT / "provider"
ICT = RUN_ROOT / "ict-engine"

BRANCH_PATH = "Bull -> BullPullback -> CapitulationMeanReversionSetup -> CrashRebound"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def csv_data_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        return max(0, sum(1 for _ in csv.reader(handle)) - 1)


def harness_rows(path: Path) -> int:
    payload = load_json(path)
    results = payload.get("results") or []
    if not results:
        return 0
    return len(results[0].get("data") or [])


def contains(path: Path, needle: str) -> bool:
    return needle in path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    summary = load_json(BRANCH / "crashrebound_branch_rc_spa_v1.json")
    imported = load_json(ICT / "01_auto_quant_results_import_crashrebound.json")
    prior = load_json(ICT / "02_auto_quant_prior_init_crashrebound_dry_run.json")
    analyze = load_json(ICT / "03_analyze_demo_branch_bundle_agent.json")
    pre_bayes = load_json(ICT / "04_pre_bayes_status_after_branch_bundle.json")
    policy = load_json(ICT / "05_policy_training_status_after_branch_bundle.agent.json")
    exported = load_json(ICT / "07_export_structural_path_ranking_target.json")

    downstream_files = [
        ICT / "02_auto_quant_prior_init_crashrebound_dry_run.json",
        ICT / "03_analyze_demo_branch_bundle_agent.json",
        ICT / "04_pre_bayes_status_after_branch_bundle.json",
        ICT / "05_policy_training_status_after_branch_bundle.agent.json",
        ICT / "06_workflow_status_after_branch_bundle.agent.json",
        ICT / "07_export_structural_path_ranking_target.json",
    ]
    branch_path_visible_downstream = any(contains(path, BRANCH_PATH) for path in downstream_files)

    checks = {
        "auto_quant_trades_207": summary["total_trades"] == 207,
        "rc_spa_reject": summary["promotion_level"] == "reject",
        "gate_mentions_missing_branch_path": "reject_missing_branch_path" in summary["gate_result"],
        "yfinance_rows_positive": harness_rows(PROVIDER / "03_yfinance_harness_fetch.json") > 0,
        "tradingview_rows_positive": harness_rows(PROVIDER / "04_tradingview_mcp_harness_fetch.json") > 0,
        "kraken_rows_positive": csv_data_rows(PROVIDER / "05_kraken_spot_xbtusd_1h.csv") > 0,
        "ibkr_rows_positive": csv_data_rows(PROVIDER / "06_ibkr_qqq_1h.csv") > 0,
        "ict_engine_import_ok": imported["n_ok"] == 1 and imported["n_error"] == 0,
        "bbn_dry_run_applied": prior["dry_run"] is True and prior["evidence_value_gate_passed"] is True,
        "pre_bayes_pass_neutralized": pre_bayes["latest_gate_status"] == "pass_neutralized",
        "execution_tree_guardrail": analyze["execution_triage"]["branch"] == "transition_guardrail",
        "catboost_path_target_unmatured": exported["rows"] == 3 and exported["mature_rows"] == 0,
        "policy_training_not_ready": (
            "pending=[" in policy["summary_line"]
            and "runtime_matches=0" in policy["summary_line"]
        ),
        "branch_path_present_in_input_bundle": contains(ICT / "branch_consumer_bundle_crashrebound_bull_v1.json", BRANCH_PATH),
        "branch_path_not_preserved_by_current_downstream": branch_path_visible_downstream is False,
    }

    lines = []
    failed = []
    for name, passed in checks.items():
        lines.append(f"{'PASS' if passed else 'FAIL'} {name}")
        if not passed:
            failed.append(name)
    detail = {
        "provider_rows": {
            "yfinance": harness_rows(PROVIDER / "03_yfinance_harness_fetch.json"),
            "tradingview_mcp": harness_rows(PROVIDER / "04_tradingview_mcp_harness_fetch.json"),
            "kraken_spot_xbtusd": csv_data_rows(PROVIDER / "05_kraken_spot_xbtusd_1h.csv"),
            "ibkr_qqq": csv_data_rows(PROVIDER / "06_ibkr_qqq_1h.csv"),
        },
        "rc_spa": summary["rc_spa"],
        "promotion_level": summary["promotion_level"],
        "gate_result": summary["gate_result"],
        "execution_tree_branch": analyze["execution_triage"]["branch"],
        "branch_path_visible_downstream": branch_path_visible_downstream,
        "failed_checks": failed,
    }
    CHECKS.mkdir(parents=True, exist_ok=True)
    (CHECKS / "branch_run_downstream_assertions.out").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (CHECKS / "branch_run_downstream_assertions.json").write_text(json.dumps(detail, indent=2), encoding="utf-8")
    print(json.dumps(detail, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
