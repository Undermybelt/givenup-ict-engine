from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T155014+0800-codex-board-b-ote-branch-continuation-contract-v1"
)
OTE_SOURCE_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T150855+0800-codex-145809-aq-material-seed-dispatch-v1"
)
TVR_BLOCKER_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T154536+0800-codex-board-b-tvr-mcp-redacted-health-probe-v1"
)


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_ote_summary() -> dict:
    return json.loads((OTE_SOURCE_ROOT / "summaries/ibkr_spy_ote_real_trades_summary.json").read_text())


def build_contract(summary: dict) -> dict:
    levels = [
        {"tag": "ote_050", "ratio": 0.500, "branch_leaf": "OTERetracement050"},
        {"tag": "ote_0618", "ratio": 0.618, "branch_leaf": "OTERetracement0618"},
        {"tag": "ote_0705", "ratio": 0.705, "branch_leaf": "OTERetracement0705"},
        {"tag": "ote_0786", "ratio": 0.786, "branch_leaf": "OTERetracement0786"},
    ]
    for row in levels:
        tag = row["tag"]
        row["branch_path"] = (
            f"TrendExpansion -> NormalVolatility -> {row['branch_leaf']} -> "
            "OTEContinuationLong"
        )
        row["ibkr_spy_trade_count"] = int(summary["counts_by_ote_tag"].get(tag, 0))
        row["ibkr_spy_pnl_ratio_sum"] = float(summary["pnl_ratio_sum_by_ote_tag"].get(tag, 0.0))

    provider_rows = [
        {
            "provider": "IBKR",
            "symbol_context": "SPY 1h",
            "aq_provider_invoked": True,
            "provider_requested": True,
            "provider_data_acquired": True,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "source_root": str(OTE_SOURCE_ROOT),
            "status": "completed_positive_seed",
            "trade_count": 162,
            "profit_factor": 1.2609,
            "failure_reason": "",
        },
        {
            "provider": "TradingViewRemix/TVR",
            "symbol_context": "BTC 1h route",
            "aq_provider_invoked": False,
            "provider_requested": True,
            "provider_data_acquired": False,
            "provider_unreachable": True,
            "local_cache_replay": False,
            "source_root": str(TVR_BLOCKER_ROOT),
            "status": "provider_unreachable_current_rate_limited",
            "trade_count": 0,
            "profit_factor": "",
            "failure_reason": "tvr_tools_list_http_429_rate_limited",
        },
        {
            "provider": "yfinance/YF",
            "symbol_context": "ES 1h",
            "aq_provider_invoked": True,
            "provider_requested": True,
            "provider_data_acquired": True,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "source_root": str(OTE_SOURCE_ROOT),
            "status": "completed_negative",
            "trade_count": 103,
            "profit_factor": 0.9270,
            "failure_reason": "negative_total_profit",
        },
        {
            "provider": "Kraken",
            "symbol_context": "XBTUSD 1h",
            "aq_provider_invoked": True,
            "provider_requested": True,
            "provider_data_acquired": True,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "source_root": str(OTE_SOURCE_ROOT),
            "status": "aq_job_failed",
            "trade_count": 0,
            "profit_factor": "",
            "failure_reason": "OperationalException_no_data_found",
        },
        {
            "provider": "Binance",
            "symbol_context": "BTCUSDT 1h",
            "aq_provider_invoked": True,
            "provider_requested": True,
            "provider_data_acquired": True,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "source_root": str(OTE_SOURCE_ROOT),
            "status": "completed_zero_trades",
            "trade_count": 0,
            "profit_factor": 0.0,
            "failure_reason": "zero_trades",
        },
        {
            "provider": "Bybit",
            "symbol_context": "BTCUSDT linear 1h",
            "aq_provider_invoked": True,
            "provider_requested": True,
            "provider_data_acquired": True,
            "provider_unreachable": False,
            "local_cache_replay": False,
            "source_root": str(OTE_SOURCE_ROOT),
            "status": "aq_job_failed",
            "trade_count": 0,
            "profit_factor": "",
            "failure_reason": "OperationalException_no_data_found",
        },
    ]

    return {
        "schema_version": "board-b-ote-branch-continuation-contract/v1",
        "owned_run_root": str(RUN_ROOT),
        "source_seed_root": str(OTE_SOURCE_ROOT),
        "current_tvr_blocker_root": str(TVR_BLOCKER_ROOT),
        "board_scope": "Board B profitability factor branch only",
        "not_board_a_market_state_analysis": True,
        "factor_family": "OTE trend retracement continuation",
        "assumed_ote_ratios": [0.500, 0.618, 0.705, 0.786],
        "ratio_correction_note": "If the user's remembered two 0.7x levels differ, replace 0.705/0.786 in the next packet.",
        "branch_levels": levels,
        "provider_rows": provider_rows,
        "decision": {
            "nursery_status": "incubation_only",
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
            "evidence_class": "ote_profitability_branch_contract_with_current_provider_blocker",
            "failure_reason": "not_six_provider_aq_authority_tvr_rate_limited_and_mixed_provider_results",
            "allowed_feedback_target": "profitability_factor_branch_queue_and_provider_repair_queue_only",
        },
    }


def write_provider_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = [
        "provider",
        "symbol_context",
        "aq_provider_invoked",
        "provider_requested",
        "provider_data_acquired",
        "provider_unreachable",
        "local_cache_replay",
        "source_root",
        "status",
        "trade_count",
        "profit_factor",
        "failure_reason",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_branch_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = [
        "tag",
        "ratio",
        "branch_leaf",
        "branch_path",
        "ibkr_spy_trade_count",
        "ibkr_spy_pnl_ratio_sum",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, contract: dict) -> None:
    levels = contract["branch_levels"]
    provider_rows = contract["provider_rows"]
    level_lines = "\n".join(
        f"- `{row['tag']}` / `{row['ratio']:.3f}`: `{row['branch_path']}`, "
        f"IBKR seed trades `{row['ibkr_spy_trade_count']}`, "
        f"pnl_ratio_sum `{row['ibkr_spy_pnl_ratio_sum']:.8f}`"
        for row in levels
    )
    provider_lines = "\n".join(
        f"- `{row['provider']}`: requested=`{row['provider_requested']}`, "
        f"aq_invoked=`{row['aq_provider_invoked']}`, acquired=`{row['provider_data_acquired']}`, "
        f"unreachable=`{row['provider_unreachable']}`, status=`{row['status']}`"
        for row in provider_rows
    )
    report = f"""# OTE Branch Continuation Contract v1

Run root:
`{RUN_ROOT}`

Source seed:
`{OTE_SOURCE_ROOT}`

Purpose: preserve the user's OTE continuation-pullback idea as a Board B profitability-factor branch packet without mixing it into Board A market-state or regime-confidence work.

## Branch Leaves

{level_lines}

## Provider Authority Readback

{provider_lines}

## Gate

- `support_once:155014_ote_branch_continuation_contract_v1`.
- `evidence_class:ote_profitability_branch_contract_with_current_provider_blocker`.
- `pass:ote_levels_050_0618_0705_0786_encoded`.
- `pass:branch_paths_explicit`.
- `pass:ibkr_spy_positive_seed_162_trades`.
- `partial:yfinance_es_completed_negative`.
- `partial:binance_completed_zero_trades`.
- `fail_closed:kraken_xbtusd_no_data_found_in_seed`.
- `fail_closed:bybit_btcusdt_no_data_found_in_seed`.
- `fail_closed:tvr_current_rate_limited`.
- `fail_closed:not_six_provider_aq_authority`.
- `fail_closed:no_new_aq_dispatch_due_active_heavy_process_and_tvr_blocker`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Keep OTE as a Board B branch nursery factor, with four leaves under `TrendExpansion -> NormalVolatility`. The next valid continuation should wait for TVR recovery or another explicitly healthy TVR route, then rerun a new same-root six-provider OTE packet before any downstream handoff probes.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report)


def write_assertions(path: Path, contract: dict) -> None:
    levels = contract["branch_levels"]
    assertions = []
    assertions.append(("ote_level_count_4", len(levels) == 4))
    assertions.append(("ote_ratios_expected", contract["assumed_ote_ratios"] == [0.5, 0.618, 0.705, 0.786]))
    assertions.append(
        (
            "all_branch_paths_profitability_only",
            all(
                row["branch_path"].startswith("TrendExpansion -> NormalVolatility")
                and row["branch_path"].endswith("OTEContinuationLong")
                for row in levels
            ),
        )
    )
    assertions.append(("ibkr_seed_records_162", sum(row["ibkr_spy_trade_count"] for row in levels) == 162))
    assertions.append(
        (
            "six_provider_rows_present",
            {row["provider"] for row in contract["provider_rows"]}
            == {"IBKR", "TradingViewRemix/TVR", "yfinance/YF", "Kraken", "Binance", "Bybit"},
        )
    )
    assertions.append(("promotion_false", contract["decision"]["promotion_allowed"] is False))
    assertions.append(("not_board_a_market_state_analysis", contract["not_board_a_market_state_analysis"] is True))

    lines = []
    ok = True
    for name, passed in assertions:
        lines.append(f"{'PASS' if passed else 'FAIL'} {name}")
        ok = ok and passed
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    if not ok:
        raise SystemExit(1)


def main() -> int:
    summary = load_ote_summary()
    contract = build_contract(summary)
    out_dir = RUN_ROOT / "ote-branch"
    write_json(out_dir / "ote_branch_continuation_contract_v1.json", contract)
    write_provider_csv(out_dir / "provider_provenance_matrix.csv", contract["provider_rows"])
    write_branch_csv(out_dir / "ote_branch_levels.csv", contract["branch_levels"])
    write_report(RUN_ROOT / "ote_branch_continuation_contract_v1.md", contract)
    write_assertions(RUN_ROOT / "checks/ote_branch_continuation_contract_v1_assertions.out", contract)
    (RUN_ROOT / "run_root.txt").write_text(str(RUN_ROOT) + "\n")

    manifest_paths = [
        RUN_ROOT / "ote_branch_continuation_contract_v1.md",
        out_dir / "ote_branch_continuation_contract_v1.json",
        out_dir / "provider_provenance_matrix.csv",
        out_dir / "ote_branch_levels.csv",
        RUN_ROOT / "checks/ote_branch_continuation_contract_v1_assertions.out",
    ]
    manifest = "\n".join(f"{sha256(path)}  {path}" for path in manifest_paths) + "\n"
    (RUN_ROOT / "checks/sha256_manifest.out").write_text(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
