#!/usr/bin/env python3
"""Consolidate remaining provider disposition after IBKR/Polymarket probes."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T081120+0800-codex-provider-residual-disposition-readback"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T081120-codex-provider-residual-disposition-readback"
OUT_DIR = RUN_ROOT / "coverage-disposition"
CHECK_DIR = RUN_ROOT / "checks"

PUBLIC_CRYPTO_DISPOSITION = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T073200-codex-public-crypto-disposition-refresh"
    / "coverage-disposition/public_crypto_disposition_refresh.json"
)
DIRECT_ATTACHABILITY = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T075056-codex-direct-source-label-attachability"
    / "source-label-attachability/direct_source_label_attachability.json"
)
IBKR_PROBE = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T080720-codex-ibkr-ready-lane-operator-probe"
    / "ibkr-ready-lane/ibkr_ready_lane_operator_probe.json"
)
POLYMARKET_PROBE = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T081000-codex-polymarket-public-catalog-probe"
    / "polymarket-catalog/polymarket_public_catalog_probe.json"
)


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": row.get("provider", ""),
        "symbol": row.get("symbol", ""),
        "timeframe": row.get("timeframe", ""),
        "cell_type": row.get("cell_type", ""),
        "root_scope": row.get("root_scope", ""),
        "disposition": row.get("disposition", ""),
        "reason": row.get("reason", ""),
        "data_status": row.get("data_status", ""),
        "label_status": row.get("label_status", ""),
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    previous = load_json(PUBLIC_CRYPTO_DISPOSITION)
    direct_attachability = load_json(DIRECT_ATTACHABILITY)
    ibkr = load_json(IBKR_PROBE)
    polymarket = load_json(POLYMARKET_PROBE)

    rows: list[dict[str, Any]] = []
    for row in previous["rows"]:
        provider = row.get("provider")
        if provider in {"ibkr", "polymarket_public"}:
            continue
        rows.append(normalize_row(row))

    ibkr_blocker = ""
    first_ibkr_failure = next(
        (row for row in ibkr["rows"] if row.get("status") in {"fetch_failed", "fetch_timeout"}),
        None,
    )
    if first_ibkr_failure:
        ibkr_blocker = first_ibkr_failure.get("stderr") or first_ibkr_failure.get("reason", "")
    for row in ibkr["rows"]:
        if row.get("attempted"):
            disposition = "blocked_operator_runtime_fetch"
            reason = f"ibkr_fetch_attempted_{row.get('status')}: {row.get('reason')}; {ibkr_blocker[-300:]}"
            data_status = row.get("status", "")
        else:
            disposition = "blocked_operator_runtime_fetch"
            reason = row.get("reason", "")
            data_status = "not_attempted_after_operator_fetch_blocker"
        rows.append(
            {
                "provider": "ibkr",
                "symbol": row.get("symbol", ""),
                "timeframe": row.get("timeframe", ""),
                "cell_type": "bar_root",
                "root_scope": "Bull/Bear/Sideways/Crisis",
                "disposition": disposition,
                "reason": reason,
                "data_status": data_status,
                "label_status": "missing_independent_root_labels",
                "runtime_code_changed": False,
                "thresholds_relaxed": False,
                "trade_usable": False,
            }
        )

    rows.append(
        {
            "provider": "polymarket_public",
            "symbol": "public_catalog",
            "timeframe": "provider_catalog",
            "cell_type": "alternative_data_sidecar",
            "root_scope": "sidecar_only_not_MainRegimeV2_price_root",
            "disposition": "sidecar_catalog_materialized_root_confidence_pending",
            "reason": f"catalog_rows={polymarket['catalog_rows']}; rows_with_clob_token_ids={polymarket['rows_with_clob_token_ids']}; no MainRegimeV2 root labels attached",
            "data_status": "catalog_materialized",
            "label_status": "not_a_root_label_panel",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "trade_usable": False,
        }
    )

    by_disposition = Counter(row["disposition"] for row in rows)
    by_provider = Counter(row["provider"] for row in rows)
    bar_rows = [row for row in rows if row["cell_type"] == "bar_root"]

    attach = direct_attachability["attachability"]
    report = {
        "run_id": RUN_ID,
        "goal_achieved": False,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective": "Read back remaining provider disposition after direct source-label attachability, IBKR operator fetch, and Polymarket catalog probes.",
        "source_artifacts": {
            "public_crypto_disposition_refresh": rel(PUBLIC_CRYPTO_DISPOSITION),
            "direct_source_label_attachability": rel(DIRECT_ATTACHABILITY),
            "ibkr_ready_lane_operator_probe": rel(IBKR_PROBE),
            "polymarket_public_catalog_probe": rel(POLYMARKET_PROBE),
        },
        "bar_cell_count": len(bar_rows),
        "provider_counts": dict(sorted(by_provider.items())),
        "disposition_counts": dict(sorted(by_disposition.items())),
        "source_label_attachability": {
            "slot_count": direct_attachability["contract"]["slot_count"],
            "direct_source_label_slots": attach["direct_source_label_slots"],
            "missing_slots": attach["missing_slots"],
            "full_four_root_cells": attach["full_four_root_cells"],
            "accepted_full_panel": direct_attachability["completion_accounting"]["accepted_full_panel"],
        },
        "ibkr_operator_probe": {
            "manifest_cells": ibkr["ibkr_manifest_cells"],
            "attempted_count": ibkr["attempted_count"],
            "ok_count": ibkr["ok_count"],
            "failed_count": ibkr["failed_count"],
            "gate_result": ibkr["gate_result"],
        },
        "polymarket_catalog_probe": {
            "catalog_rows": polymarket["catalog_rows"],
            "rows_with_clob_token_ids": polymarket["rows_with_clob_token_ids"],
            "gate_result": polymarket["gate_result"],
        },
        "rows": rows,
        "completion_accounting": {
            "accepted_full_cycle_full_universe": False,
            "accepted_confidence": False,
            "ready_not_yet_attempted_cells": by_disposition.get("ready_not_yet_attempted", 0),
            "why_not_accepted": [
                "Direct public source labels attach to only 16/612 current contract slots and only four yfinance daily/weekly index cells.",
                "IBKR is no longer just ready/not-attempted: the operator fetch path failed because IB Gateway/TWS is not listening on 127.0.0.1:7497.",
                "Polymarket catalog discovery succeeded but is sidecar alternative data, not a MainRegimeV2 root-label panel.",
                "Yfinance/Binance/Bybit/Kraken usable bars remain unsupported for accepted confidence without independent Bull/Bear/Sideways/Crisis labels.",
                "TradingViewRemix remains connectivity-blocked.",
            ],
        },
        "raw_data_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "gate_result": "provider_residuals_dispositioned_full_universe_labels_still_blocked",
        "next_action": "Acquire or provide an independent MainRegimeV2 source-label panel for the non-index, intraday/monthly, crypto, and provider-specific cells; only restart IBKR Gateway/TWS if bar coverage is needed after label coverage exists.",
        "artifacts": {
            "summary_json": rel(OUT_DIR / "provider_residual_disposition_readback.json"),
            "summary_md": rel(OUT_DIR / "provider_residual_disposition_readback.md"),
            "summary_csv": rel(OUT_DIR / "provider_residual_disposition_readback.csv"),
            "assertions": rel(CHECK_DIR / "provider_residual_disposition_readback_assertions.out"),
            "script": rel(Path(__file__)),
        },
    }

    (OUT_DIR / "provider_residual_disposition_readback.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    with (OUT_DIR / "provider_residual_disposition_readback.csv").open("w", newline="") as handle:
        fieldnames = [
            "provider",
            "symbol",
            "timeframe",
            "cell_type",
            "root_scope",
            "disposition",
            "reason",
            "data_status",
            "label_status",
            "runtime_code_changed",
            "thresholds_relaxed",
            "trade_usable",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    md_lines = [
        "# Provider Residual Disposition Readback",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Goal achieved: `false`",
        "",
        f"- Bar cells represented: `{len(bar_rows)}`",
        f"- Ready-not-yet-attempted cells: `{by_disposition.get('ready_not_yet_attempted', 0)}`",
        f"- Direct source-label slots attached: `{attach['direct_source_label_slots']}` / `{direct_attachability['contract']['slot_count']}`",
        f"- Full four-root source-label cells: `{attach['full_four_root_cells']}`",
        f"- IBKR attempted cells: `{ibkr['attempted_count']}`; OK `{ibkr['ok_count']}`; failed `{ibkr['failed_count']}`",
        f"- Polymarket catalog rows: `{polymarket['catalog_rows']}`",
        "",
        "## Disposition Counts",
        "",
        "| Disposition | Count |",
        "|---|---:|",
    ]
    for disposition, count in sorted(by_disposition.items()):
        md_lines.append(f"| `{disposition}` | {count} |")
    md_lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Gate result: `provider_residuals_dispositioned_full_universe_labels_still_blocked`",
            "- No OHLCV/proxy score is counted as accepted confidence.",
            "- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.",
            "",
            "## Next Action",
            "",
            report["next_action"],
        ]
    )
    (OUT_DIR / "provider_residual_disposition_readback.md").write_text("\n".join(md_lines) + "\n")

    assertion_lines = [
        "goal_achieved=false",
        f"bar_cell_count={len(bar_rows)}",
        f"ready_not_yet_attempted_cells={by_disposition.get('ready_not_yet_attempted', 0)}",
        f"direct_source_label_slots={attach['direct_source_label_slots']}",
        f"source_label_slot_count={direct_attachability['contract']['slot_count']}",
        f"full_four_root_source_label_cells={attach['full_four_root_cells']}",
        f"ibkr_attempted_count={ibkr['attempted_count']}",
        f"ibkr_ok_count={ibkr['ok_count']}",
        f"ibkr_failed_count={ibkr['failed_count']}",
        f"polymarket_catalog_rows={polymarket['catalog_rows']}",
        "accepted_full_cycle_full_universe=false",
        "raw_data_committed=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "trade_usable=false",
        "gate_result=provider_residuals_dispositioned_full_universe_labels_still_blocked",
    ]
    for disposition, count in sorted(by_disposition.items()):
        assertion_lines.append(f"disposition.{disposition}={count}")
    (CHECK_DIR / "provider_residual_disposition_readback_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n"
    )
    print(rel(OUT_DIR / "provider_residual_disposition_readback.json"))


if __name__ == "__main__":
    main()
