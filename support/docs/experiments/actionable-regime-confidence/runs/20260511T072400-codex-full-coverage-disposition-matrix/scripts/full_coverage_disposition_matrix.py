#!/usr/bin/env python3
"""Build a full provider/symbol/timeframe disposition matrix for Board A.

The matrix records each manifest cell as accepted, blocked, or unsupported by
reason. It is coverage accounting only; it does not promote a regime gate.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T072400+0800-codex-full-coverage-disposition-matrix"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T072400-codex-full-coverage-disposition-matrix"
OUT_DIR = RUN_ROOT / "coverage-disposition"
CHECK_DIR = RUN_ROOT / "checks"

MANIFEST = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T070103-codex-full-universe-scope-reset/provider-universe-manifest/provider_universe_manifest.json"
YFINANCE_READINESS = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T072200-codex-yfinance-label-calibration-readiness/label-calibration/yfinance_label_calibration_readiness.json"

MAIN_ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mo"]


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


def add_bar_cell(
    rows: list[dict[str, Any]],
    provider: str,
    symbol: str,
    timeframe: str,
    disposition: str,
    reason: str,
    data_status: str,
    score_status: str,
    label_status: str,
    root_scope: str = "Bull/Bear/Sideways/Crisis",
) -> None:
    rows.append(
        {
            "provider": provider,
            "symbol": symbol,
            "timeframe": timeframe,
            "cell_type": "bar_root",
            "root_scope": root_scope,
            "disposition": disposition,
            "reason": reason,
            "data_status": data_status,
            "score_status": score_status,
            "label_status": label_status,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "trade_usable": False,
        }
    )


def add_manipulation_cell(
    rows: list[dict[str, Any]],
    variety: str,
    disposition: str,
    reason: str,
    evidence_packet: str = "",
) -> None:
    rows.append(
        {
            "provider": "direct_event_source",
            "symbol": "direct_event_variety",
            "timeframe": "event_window",
            "cell_type": "manipulation_overlay",
            "root_scope": variety,
            "disposition": disposition,
            "reason": reason,
            "data_status": evidence_packet or "not_available",
            "score_status": "not_bar_score",
            "label_status": "direct_event_label" if disposition == "accepted_overlay" else "blocked_or_diagnostic",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "trade_usable": False,
        }
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    manifest = load_json(MANIFEST)
    yfinance_readiness = load_json(YFINANCE_READINESS)

    rows: list[dict[str, Any]] = []

    for cell in yfinance_readiness["rows"]:
        add_bar_cell(
            rows,
            provider="yfinance",
            symbol=cell["symbol"],
            timeframe=cell["timeframe"],
            disposition="unsupported_for_accepted_confidence",
            reason="usable_close_and_close_score_but_missing_independent_source_backed_root_labels",
            data_status="usable" if cell["data_usable"] else cell["data_status"],
            score_status=cell["score_status"],
            label_status=cell["label_source_status"],
        )

    catalog = manifest["repo_market_catalog_universe"]
    pending = manifest["provider_status_readback"]["market_data_pending"]
    relationships = manifest["relationship_universe"]

    pending_provider_symbols = {
        "ibkr": catalog["ibkr_symbols"],
        "tradingview_mcp": catalog["tradingview_symbols"],
        "binance_public": relationships["crypto_symbols"],
        "bybit_public": relationships["crypto_symbols"],
        "kraken_public": relationships["crypto_symbols"],
    }
    for provider, symbols in pending_provider_symbols.items():
        for symbol in symbols:
            for timeframe in TIMEFRAMES:
                add_bar_cell(
                    rows,
                    provider=provider,
                    symbol=symbol,
                    timeframe=timeframe,
                    disposition="blocked_provider_unavailable",
                    reason=pending[provider],
                    data_status="not_attempted_provider_blocked",
                    score_status="not_scored_provider_blocked",
                    label_status="not_labeled_provider_blocked",
                )

    # The manifest has no concrete Polymarket symbol universe yet; keep a
    # provider-level unsupported cell instead of inventing instruments.
    add_bar_cell(
        rows,
        provider="polymarket_public",
        symbol="prediction_market_catalog_unmaterialized",
        timeframe="provider_catalog",
        disposition="blocked_provider_unavailable",
        reason=pending["polymarket_public"],
        data_status="not_attempted_provider_blocked",
        score_status="not_scored_provider_blocked",
        label_status="not_labeled_provider_blocked",
    )

    add_manipulation_cell(
        rows,
        "classified_telegram_coin_pump_event_present",
        "accepted_overlay",
        "direct_event_label_source_backed; suppress_abstain_cooldown_only",
        "20260511T045102+0800-codex-mehrnoom-telegram-direct-manipulation-gate",
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
        add_manipulation_cell(rows, variety, "blocked_or_diagnostic", reason)

    by_disposition = Counter(row["disposition"] for row in rows)
    by_provider = Counter(row["provider"] for row in rows)
    bar_rows = [row for row in rows if row["cell_type"] == "bar_root"]
    manipulation_rows = [row for row in rows if row["cell_type"] == "manipulation_overlay"]

    report = {
        "run_id": RUN_ID,
        "goal_achieved": False,
        "objective": "Materialize explicit provider/symbol/timeframe disposition reasons for the expanded full-species/full-cycle Board A requirement.",
        "source_artifacts": {
            "provider_universe_manifest": rel(MANIFEST),
            "yfinance_label_calibration_readiness": rel(YFINANCE_READINESS),
        },
        "main_price_roots": MAIN_ROOTS,
        "bar_cell_count": len(bar_rows),
        "manipulation_variety_count": len(manipulation_rows),
        "disposition_counts": dict(sorted(by_disposition.items())),
        "provider_counts": dict(sorted(by_provider.items())),
        "bar_provider_counts": dict(sorted(Counter(row["provider"] for row in bar_rows).items())),
        "manipulation_disposition_counts": dict(sorted(Counter(row["disposition"] for row in manipulation_rows).items())),
        "rows": rows,
        "completion_accounting": {
            "all_manifest_cells_dispositioned": True,
            "accepted_full_cycle_full_universe": False,
            "why_not_accepted": [
                "Yfinance cells are usable/scored but unsupported for accepted confidence because independent source-backed root labels are missing.",
                "IBKR, TradingViewRemix, and public crypto provider cells are blocked by provider-status reasons.",
                "Polymarket has no concrete symbol catalog materialized in the current manifest and its provider path is dependency-blocked.",
                "Only one direct Manipulation variety is accepted; other direct varieties remain blocked or diagnostic.",
            ],
        },
        "raw_ohlcv_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "gate_result": "full_coverage_dispositioned_but_acceptance_blocked",
        "next_action": "Open one blocked provider lane with a low-pollution dependency wrapper, then rerun the provider/symbol/timeframe disposition matrix with the same label-source rules.",
        "artifacts": {
            "disposition_json": rel(OUT_DIR / "full_coverage_disposition_matrix.json"),
            "disposition_md": rel(OUT_DIR / "full_coverage_disposition_matrix.md"),
            "disposition_csv": rel(OUT_DIR / "full_coverage_disposition_matrix.csv"),
            "assertions": rel(CHECK_DIR / "full_coverage_disposition_matrix_assertions.out"),
            "script": rel(Path(__file__)),
        },
    }

    (OUT_DIR / "full_coverage_disposition_matrix.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    with (OUT_DIR / "full_coverage_disposition_matrix.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Full Coverage Disposition Matrix",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Goal achieved: `false`",
        "",
        "## Summary",
        "",
        f"- Bar provider/symbol/timeframe cells dispositioned: `{len(bar_rows)}`",
        f"- Direct `Manipulation` varieties dispositioned: `{len(manipulation_rows)}`",
        f"- Accepted full-cycle/full-universe gate: `false`",
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
            "## Accounting",
            "",
            "- All current manifest cells are now represented with an explicit disposition.",
            "- Yfinance remains blocked for acceptance by missing independent root labels, despite usable/scored close cells.",
            "- Pending provider cells are blocked by their provider-status reasons, not silently skipped.",
            "- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.",
            "",
            "Gate result: `full_coverage_dispositioned_but_acceptance_blocked`",
        ]
    )
    (OUT_DIR / "full_coverage_disposition_matrix.md").write_text("\n".join(lines) + "\n")

    assertion_lines = [
        "goal_achieved=false",
        f"bar_cell_count={len(bar_rows)}",
        f"manipulation_variety_count={len(manipulation_rows)}",
        "all_manifest_cells_dispositioned=true",
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
            "gate_result=full_coverage_dispositioned_but_acceptance_blocked",
        ]
    )
    (CHECK_DIR / "full_coverage_disposition_matrix_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n"
    )

    print(rel(OUT_DIR / "full_coverage_disposition_matrix.json"))


if __name__ == "__main__":
    main()
