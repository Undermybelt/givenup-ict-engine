#!/usr/bin/env python3
"""Refresh Board A coverage disposition after the uv provider wrapper probe."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T072800+0800-codex-uv-coverage-disposition-refresh"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T072800-codex-uv-coverage-disposition-refresh"
OUT_DIR = RUN_ROOT / "coverage-disposition"
CHECK_DIR = RUN_ROOT / "checks"

MANIFEST = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T070103-codex-full-universe-scope-reset/provider-universe-manifest/provider_universe_manifest.json"
YFINANCE_READINESS = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T072200-codex-yfinance-label-calibration-readiness/label-calibration/yfinance_label_calibration_readiness.json"
KRAKEN_SMOKE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T072600-codex-uv-provider-readiness-kraken-smoke/kraken-matrix/uv_provider_readiness_kraken_smoke.json"
UV_PROVIDER_STATUS = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T072600-codex-uv-provider-readiness-kraken-smoke/provider-readiness/provider_status_uv_market_data_stdout.json"

TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mo"]


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


def add_row(
    rows: list[dict[str, Any]],
    provider: str,
    symbol: str,
    timeframe: str,
    cell_type: str,
    disposition: str,
    reason: str,
    data_status: str,
    label_status: str,
    root_scope: str = "Bull/Bear/Sideways/Crisis",
) -> None:
    rows.append(
        {
            "provider": provider,
            "symbol": symbol,
            "timeframe": timeframe,
            "cell_type": cell_type,
            "root_scope": root_scope,
            "disposition": disposition,
            "reason": reason,
            "data_status": data_status,
            "label_status": label_status,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "trade_usable": False,
        }
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    manifest = load_json(MANIFEST)
    yf = load_json(YFINANCE_READINESS)
    kraken = load_json(KRAKEN_SMOKE)
    uv_status = load_json(UV_PROVIDER_STATUS)
    catalog = manifest["repo_market_catalog_universe"]
    relationships = manifest["relationship_universe"]

    rows: list[dict[str, Any]] = []

    for cell in yf["rows"]:
        add_row(
            rows,
            "yfinance",
            cell["symbol"],
            cell["timeframe"],
            "bar_root",
            "unsupported_for_accepted_confidence",
            "usable_close_and_close_score_but_missing_independent_source_backed_root_labels",
            "usable",
            cell["label_source_status"],
        )

    for cell in kraken["rows"]:
        if cell["status"] == "ok":
            add_row(
                rows,
                "kraken_public",
                cell["symbol"],
                cell["timeframe"],
                "bar_root",
                "unsupported_for_accepted_confidence",
                "kraken_public_data_available_but_missing_independent_source_backed_root_labels",
                f"ok_rows={cell['rows']}",
                "missing_independent_root_labels",
            )
        else:
            add_row(
                rows,
                "kraken_public",
                cell["symbol"],
                cell["timeframe"],
                "bar_root",
                "unsupported_timeframe",
                cell["reason"],
                cell["status"],
                "not_labeled_timeframe_unsupported",
            )

    ready_not_attempted = {
        "binance_public": relationships["crypto_symbols"],
        "bybit_public": relationships["crypto_symbols"],
    }
    for provider, symbols in ready_not_attempted.items():
        for symbol in symbols:
            for timeframe in TIMEFRAMES:
                add_row(
                    rows,
                    provider,
                    symbol,
                    timeframe,
                    "bar_root",
                    "ready_not_yet_attempted",
                    "uv_wrapper_provider_ready_but_data_matrix_not_attempted_in_this_slice",
                    "provider_ready_no_fetch_yet",
                    "not_labeled_no_fetch_yet",
                )

    for symbol in catalog["ibkr_symbols"]:
        for timeframe in TIMEFRAMES:
            add_row(
                rows,
                "ibkr",
                symbol,
                timeframe,
                "bar_root",
                "ready_not_yet_attempted",
                "uv_wrapper_reports_ibkr_ready_but_operator_runtime_fetch_not_attempted_in_this_slice",
                "provider_ready_no_fetch_yet",
                "not_labeled_no_fetch_yet",
            )

    add_row(
        rows,
        "polymarket_public",
        "prediction_market_catalog_unmaterialized",
        "provider_catalog",
        "bar_root",
        "ready_not_yet_attempted",
        "uv_wrapper_reports_polymarket_ready_but_market_catalog_not_materialized_in_this_slice",
        "provider_ready_no_fetch_yet",
        "not_labeled_no_fetch_yet",
    )

    for symbol in catalog["tradingview_symbols"]:
        for timeframe in TIMEFRAMES:
            add_row(
                rows,
                "tradingview_mcp",
                symbol,
                timeframe,
                "bar_root",
                "blocked_provider_unavailable",
                "tradingview_mcp_connectivity_probe_failed",
                "not_attempted_provider_blocked",
                "not_labeled_provider_blocked",
            )

    add_row(
        rows,
        "direct_event_source",
        "direct_event_variety",
        "event_window",
        "manipulation_overlay",
        "accepted_overlay",
        "direct_event_label_source_backed; suppress_abstain_cooldown_only",
        "20260511T045102+0800-codex-mehrnoom-telegram-direct-manipulation-gate",
        "direct_event_label",
        "classified_telegram_coin_pump_event_present",
    )
    for variety, reason in [
        ("raw_telegram_message_text_gate", "below_95_in_strict_raw_message_audit"),
        ("twitter_social_aggregate_gate", "below_95_in_sparse_social_aggregate_diagnostic"),
        ("systemslab_hgb_event_rank_gate", "below_95_or_rank_only_event_path"),
        ("mendeley_gox_hgb_wash_gate", "below_95_or_not_current_direct_event_overlay"),
        ("bayi_sequence_gate", "below_95_sequence_path"),
        ("kaggle_nft_wash_gate", "below_95_nft_wash_path"),
        ("l2_l3_mbo_order_lifecycle", "missing_required_inputs"),
        ("onchain_direct_event", "missing_required_inputs"),
    ]:
        add_row(
            rows,
            "direct_event_source",
            "direct_event_variety",
            "event_window",
            "manipulation_overlay",
            "blocked_or_diagnostic",
            reason,
            "not_available",
            "blocked_or_diagnostic",
            variety,
        )

    by_disposition = Counter(row["disposition"] for row in rows)
    by_provider = Counter(row["provider"] for row in rows)
    bar_rows = [row for row in rows if row["cell_type"] == "bar_root"]
    ready_not_attempted_count = by_disposition["ready_not_yet_attempted"]

    report = {
        "run_id": RUN_ID,
        "goal_achieved": False,
        "objective": "Refresh full coverage disposition after a low-pollution uv wrapper makes six market-data providers ready and Kraken public data is smoke-fetched.",
        "source_artifacts": {
            "provider_universe_manifest": rel(MANIFEST),
            "yfinance_label_calibration_readiness": rel(YFINANCE_READINESS),
            "kraken_smoke": rel(KRAKEN_SMOKE),
            "uv_provider_status": rel(UV_PROVIDER_STATUS),
        },
        "uv_provider_status_summary": uv_status.get("summary_line"),
        "uv_ready_providers": uv_status.get("ready_providers", []),
        "uv_pending_providers": uv_status.get("pending_providers", []),
        "bar_cell_count": len(bar_rows),
        "disposition_counts": dict(sorted(by_disposition.items())),
        "provider_counts": dict(sorted(by_provider.items())),
        "rows": rows,
        "completion_accounting": {
            "all_current_cells_represented": True,
            "accepted_full_cycle_full_universe": False,
            "why_not_accepted": [
                "Yfinance and fetched Kraken cells still lack independent source-backed MainRegimeV2 root labels.",
                "Binance, Bybit, IBKR, and Polymarket are ready under uv wrapper but not data-attempted in this slice.",
                "TradingViewRemix remains connectivity-blocked.",
                "Only one direct Manipulation variety is accepted; other direct varieties remain blocked or diagnostic.",
            ],
        },
        "raw_ohlcv_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "gate_result": "uv_coverage_disposition_refreshed_remaining_cells_pending",
        "next_action": "Attempt Binance and Bybit public crypto matrices under the same uv wrapper, then refresh disposition again before any completion audit.",
        "artifacts": {
            "disposition_json": rel(OUT_DIR / "uv_coverage_disposition_refresh.json"),
            "disposition_md": rel(OUT_DIR / "uv_coverage_disposition_refresh.md"),
            "disposition_csv": rel(OUT_DIR / "uv_coverage_disposition_refresh.csv"),
            "assertions": rel(CHECK_DIR / "uv_coverage_disposition_refresh_assertions.out"),
            "script": rel(Path(__file__)),
        },
    }

    (OUT_DIR / "uv_coverage_disposition_refresh.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    with (OUT_DIR / "uv_coverage_disposition_refresh.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# UV Coverage Disposition Refresh",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Goal achieved: `false`",
        "",
        f"- UV provider status: `{uv_status.get('summary_line')}`",
        f"- Bar cells represented: `{len(bar_rows)}`",
        f"- Ready-not-yet-attempted cells: `{ready_not_attempted_count}`",
        "",
        "## Disposition Counts",
        "",
        "| Disposition | Count |",
        "|---|---:|",
    ]
    for key, count in sorted(by_disposition.items()):
        lines.append(f"| `{key}` | {count} |")
    lines.extend(["", "## Provider Counts", "", "| Provider | Cells |", "|---|---:|"])
    for key, count in sorted(by_provider.items()):
        lines.append(f"| `{key}` | {count} |")
    lines.extend(
        [
            "",
            "Gate result: `uv_coverage_disposition_refreshed_remaining_cells_pending`",
            "",
            "Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.",
        ]
    )
    (OUT_DIR / "uv_coverage_disposition_refresh.md").write_text("\n".join(lines) + "\n")

    assertion_lines = [
        "goal_achieved=false",
        f"uv_provider_status_summary={uv_status.get('summary_line')}",
        f"bar_cell_count={len(bar_rows)}",
        f"ready_not_yet_attempted={ready_not_attempted_count}",
        "accepted_full_cycle_full_universe=false",
    ]
    for key, count in sorted(by_disposition.items()):
        assertion_lines.append(f"disposition.{key}={count}")
    for key, count in sorted(by_provider.items()):
        assertion_lines.append(f"provider.{key}={count}")
    assertion_lines.extend(
        [
            "raw_ohlcv_committed=false",
            "runtime_code_changed=false",
            "thresholds_relaxed=false",
            "trade_usable=false",
            "gate_result=uv_coverage_disposition_refreshed_remaining_cells_pending",
        ]
    )
    (CHECK_DIR / "uv_coverage_disposition_refresh_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n"
    )
    print(rel(OUT_DIR / "uv_coverage_disposition_refresh.json"))


if __name__ == "__main__":
    main()
