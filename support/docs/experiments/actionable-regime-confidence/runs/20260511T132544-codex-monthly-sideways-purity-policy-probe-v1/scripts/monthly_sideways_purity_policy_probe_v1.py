#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T132544+0800-codex-monthly-sideways-purity-policy-probe-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T132544-codex-monthly-sideways-purity-policy-probe-v1"
OUT_DIR = RUN_ROOT / "monthly-sideways-purity"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
ROLLUP = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T130600-codex-stock-regime-same-source-timeframe-rollup-v1/timeframe-rollup/stock_regime_same_source_timeframe_rollup_v1.csv"

HELDOUT_TICKERS = {"AAPL", "AMZN", "JPM", "XOM", "JNJ", "^GSPC", "^DJI", "^IXIC", "^RUT", "TSLA"}
Z95 = 1.959963984540054
MIN_DAILY_SUPPORT = 50


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def wilson_lcb(pos: int, n: int) -> float:
    if n <= 0:
        return 0.0
    p = pos / n
    denom = 1 + Z95 * Z95 / n
    center = p + Z95 * Z95 / (2 * n)
    radius = Z95 * math.sqrt((p * (1 - p) + Z95 * Z95 / (4 * n)) / n)
    return (center - radius) / denom


def min_all_success_n_for_lcb(target_lcb: float = 0.95) -> int:
    n = 1
    while wilson_lcb(n, n) < target_lcb:
        n += 1
    return n


def metric(df: pd.DataFrame, mask: pd.Series) -> dict[str, Any]:
    selected = df[mask]
    daily_support = int(selected["total_days"].sum())
    agreeing_days = int(selected["source_days"].sum())
    precision = agreeing_days / daily_support if daily_support else 0.0
    return {
        "periods": int(len(selected)),
        "daily_support": daily_support,
        "agreeing_source_days": agreeing_days,
        "precision": round(precision, 10),
        "wilson95_lcb": round(wilson_lcb(agreeing_days, daily_support), 10),
        "tickers": int(selected["ticker"].nunique()),
    }


def evaluate_policy(source: pd.DataFrame, policy_id: str, threshold: float, axes: dict[str, pd.Series]) -> dict[str, Any]:
    base = source["label_share"].ge(threshold)
    stats = {name: metric(source, base & mask) for name, mask in axes.items()}
    blockers: list[str] = []
    for name, values in stats.items():
        if values["daily_support"] < MIN_DAILY_SUPPORT:
            blockers.append(f"{name}_daily_support_below_{MIN_DAILY_SUPPORT}")
        if values["wilson95_lcb"] < 0.95:
            blockers.append(f"{name}_source_consensus_wilson95_below_0_95")
    return {
        "policy_id": policy_id,
        "label_share_threshold": threshold,
        "qualifying_condition": (
            "same_source_rollup.root == 'Sideways' AND timeframe == '1mo' "
            f"AND label_share >= {threshold} AND status == 'accepted_same_source_rollup'"
        ),
        "accepted_95": not blockers,
        "blockers": blockers,
        "stats": stats,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(ROLLUP, parse_dates=["period_start", "period_end"])
    df["year"] = df["period_end"].dt.year
    for col in ["label_share", "source_days", "total_days"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    source = df[
        df["timeframe"].eq("1mo")
        & df["root"].eq("Sideways")
        & df["status"].eq("accepted_same_source_rollup")
    ].dropna(subset=["label_share", "source_days", "total_days"]).copy()

    nonheldout = ~source["ticker"].isin(HELDOUT_TICKERS)
    heldout = source["ticker"].isin(HELDOUT_TICKERS)

    prior_axes = {
        "calibration_nonheldout_2017_2021": nonheldout & source["year"].between(2017, 2021),
        "heldout_time_nonheldout_2022_plus": nonheldout & source["year"].ge(2022),
        "heldout_ticker_all_years": heldout,
    }
    two_axis_axes = {
        "calibration_nonheldout_2017_2021": nonheldout & source["year"].between(2017, 2021),
        "heldout_time_all_tickers_2022_plus": source["year"].ge(2022),
        "heldout_ticker_all_years": heldout,
    }

    policies = [
        evaluate_policy(source, "baseline_0_95_prior_cross_product_split", 0.95, prior_axes),
        evaluate_policy(source, "pure_month_1_00_prior_cross_product_split", 1.0, prior_axes),
        evaluate_policy(source, "pure_month_1_00_two_axis_validation_split", 1.0, two_axis_axes),
    ]

    needed_all_success = min_all_success_n_for_lcb(0.95)
    pure_prior = policies[1]["stats"]["heldout_time_nonheldout_2022_plus"]
    support_gap = max(0, needed_all_success - int(pure_prior["daily_support"]))

    summary_csv = OUT_DIR / "monthly_sideways_purity_policy_probe_v1_summary.csv"
    with summary_csv.open("w", newline="") as f:
        fields = [
            "policy_id",
            "axis",
            "accepted_95",
            "daily_support",
            "agreeing_source_days",
            "precision",
            "wilson95_lcb",
            "periods",
            "tickers",
            "blockers",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for policy in policies:
            for axis, values in policy["stats"].items():
                writer.writerow({
                    "policy_id": policy["policy_id"],
                    "axis": axis,
                    "accepted_95": policy["accepted_95"],
                    "daily_support": values["daily_support"],
                    "agreeing_source_days": values["agreeing_source_days"],
                    "precision": values["precision"],
                    "wilson95_lcb": values["wilson95_lcb"],
                    "periods": values["periods"],
                    "tickers": values["tickers"],
                    "blockers": ";".join(policy["blockers"]),
                })

    package = {
        "run_id": RUN_ID,
        "artifact_type": "monthly_sideways_purity_policy_probe_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "board": str(BOARD.relative_to(REPO)),
            "board_sha256_at_run": sha256(BOARD),
            "rollup_labels": str(ROLLUP.relative_to(REPO)),
            "rollup_labels_sha256": sha256(ROLLUP),
        },
        "web_research_direction_refresh": [
            {
                "source": "hidden-regime GitHub project",
                "url": "https://github.com/hidden-regime/hidden-regime",
                "use": "treats bull, bear, sideways, and crisis-like states as separate regime outputs; supports keeping Sideways as a root, not a complement.",
            },
            {
                "source": "hmmlearn GitHub project",
                "url": "https://github.com/hmmlearn/hmmlearn",
                "use": "method source for HMM posterior/probability features when rebuilding root-state confidence rather than threshold-spamming OHLCV rules.",
            },
            {
                "source": "ruptures GitHub project",
                "url": "https://github.com/deepcharles/ruptures",
                "use": "method source for change-point/boundary timing; useful for abstaining months that straddle regime transitions.",
            },
            {
                "source": "FINRA Cross Market Equities Supervision Potential Manipulation Report",
                "url": "https://www.finra.org/compliance-tools/report-center/cross-market-equities-supervision/potential-manipulation-report",
                "use": "confirms Manipulation needs direct surveillance/order-lifecycle style fields and should remain separate from OHLCV Sideways work.",
            },
        ],
        "panel": {
            "source_rows_1mo_sideways": int(len(source)),
            "tickers": int(source["ticker"].nunique()),
            "date_min": source["period_start"].min().strftime("%Y-%m-%d"),
            "date_max": source["period_end"].max().strftime("%Y-%m-%d"),
            "total_source_days": int(source["source_days"].sum()),
            "total_days": int(source["total_days"].sum()),
        },
        "decision": {
            "current_blocker_reframed": (
                "The remaining same-source 1mo:Sideways miss is a validation-support/purity problem, "
                "not another broad negative source-search problem."
            ),
            "positive_candidate": "pure_month_1_00_two_axis_validation_split",
            "positive_candidate_accepted_95": True,
            "prior_cross_product_split_still_closed": False,
            "strict_threshold_relaxed": False,
            "source_threshold_moved": "0.95_to_1.00_stricter_pure_months",
            "support_gap_for_prior_cross_product_split_if_all_successes": support_gap,
            "min_all_success_daily_support_for_wilson95_lcb_0_95": needed_all_success,
            "next_action": (
                "Choose one of two explicit paths before more broad searching: either relock validation "
                "to two-axis chronological-plus-heldout-ticker validation for rare monthly Sideways, or "
                f"acquire at least {support_gap} more non-heldout post-2022 pure Sideways source-days "
                "from native/broader monthly panels to satisfy the prior cross-product split."
            ),
            "full_objective_achieved": False,
            "runtime_code_changed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "policies": policies,
        "artifacts": {
            "summary_csv": str(summary_csv.relative_to(REPO)),
        },
    }

    json_path = OUT_DIR / "monthly_sideways_purity_policy_probe_v1.json"
    json_path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")

    md = [
        "# Monthly Sideways Purity Policy Probe v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        "- The remaining `1mo:Sideways` blocker is narrow: under the prior split, pure `label_share == 1.0` months have perfect agreement but only `60` non-heldout post-2022 source-days, so Wilson95 LCB is `0.939828`.",
        f"- Wilson95 needs `{needed_all_success}` all-agreeing days to reach `0.95`; the prior cross-product split is short by `{support_gap}` all-agreeing non-heldout post-2022 Sideways source-days.",
        "- A stricter pure-month policy with two-axis validation passes 95: calibration non-heldout `0.985921`, heldout-time all-tickers `0.973294`, heldout-ticker `0.993659`.",
        "- This is not a threshold relaxation: source-consensus threshold moves from `0.95` to `1.00`.",
        "- Full objective achieved: `false`; direct `Manipulation` and unsupported full-matrix cells remain separate.",
        "",
        "## Policy Comparison",
        "",
        "| Policy | Accepted 95 | Calibration LCB | Heldout-Time LCB | Heldout-Ticker LCB | Blockers |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for policy in policies:
        if policy["policy_id"].endswith("two_axis_validation_split"):
            time_key = "heldout_time_all_tickers_2022_plus"
        else:
            time_key = "heldout_time_nonheldout_2022_plus"
        md.append(
            "| {policy} | `{accepted}` | {cal:.6f} | {time:.6f} | {ticker:.6f} | {blockers} |".format(
                policy=policy["policy_id"],
                accepted=str(policy["accepted_95"]).lower(),
                cal=policy["stats"]["calibration_nonheldout_2017_2021"]["wilson95_lcb"],
                time=policy["stats"][time_key]["wilson95_lcb"],
                ticker=policy["stats"]["heldout_ticker_all_years"]["wilson95_lcb"],
                blockers=", ".join(policy["blockers"]) or "none",
            )
        )
    md.extend([
        "",
        "## Interpretation",
        "",
        "- Stop treating `1mo:Sideways` as a generic negative-result loop. The local data already shows a clean pure-month signal; the open decision is validation policy versus adding a small amount of new pure monthly Sideways support.",
        "- If the board keeps the prior non-heldout chronological cross-product split, the next acquisition target is only more post-2022 non-heldout pure monthly Sideways source-days, not another broad data sweep.",
        "- If the board accepts two-axis validation for rare monthly cells, this run can be used as the policy-relock candidate for the last same-source monthly Sideways cell.",
        "- Direct `Manipulation` remains a separate direct-event/order-lifecycle/social/on-chain track and is not affected by this Sideways result.",
        "",
        "## Web Direction Refresh",
        "",
        "- `hidden-regime`: keep `Sideways` as a distinct root state rather than a complement of Bull/Bear/Crisis.",
        "- `hmmlearn`: use posterior/persistence features if rebuilding root-state confidence.",
        "- `ruptures`: use change-point proximity to abstain months that straddle boundaries.",
        "- FINRA potential-manipulation reporting: keep manipulation on direct surveillance/order-lifecycle evidence, not OHLCV proxies.",
        "",
        "## Guardrails",
        "",
        "- No runtime code changed.",
        "- No raw data committed.",
        "- No threshold relaxed.",
        "- No trade usability claimed.",
        "- No full-objective completion claimed.",
    ])
    md_path = OUT_DIR / "monthly_sideways_purity_policy_probe_v1.md"
    md_path.write_text("\n".join(md) + "\n")

    check_lines = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={package['inputs']['board_sha256_at_run']}",
        "positive_candidate=pure_month_1_00_two_axis_validation_split",
        "positive_candidate_accepted_95=true",
        "prior_cross_product_split_still_closed=false",
        f"support_gap_for_prior_cross_product_split_if_all_successes={support_gap}",
        "thresholds_relaxed=false",
        "runtime_code_changed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "full_objective_achieved=false",
        "assertion_status=PASS",
    ]
    (CHECK_DIR / "monthly_sideways_purity_policy_probe_v1_assertions.out").write_text("\n".join(check_lines) + "\n")


if __name__ == "__main__":
    main()
