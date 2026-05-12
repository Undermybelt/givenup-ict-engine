#!/usr/bin/env python3
"""Audit label-calibration readiness for the ready yfinance matrix.

This run intentionally does not derive new root labels from the same close-only
features. Board A requires independent/source-backed labels for 95% calibration;
close-only rule hits are applicability evidence, not label evidence.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T072200+0800-codex-yfinance-label-calibration-readiness"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T072200-codex-yfinance-label-calibration-readiness"
OUT_DIR = RUN_ROOT / "label-calibration"
CHECK_DIR = RUN_ROOT / "checks"

FETCH_MATRIX = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T070440-codex-provider-universe-manifest-readback/yfinance-full-matrix/yfinance_full_universe_fetch_matrix.json"
SCORE_MATRIX = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T072000-codex-yfinance-root-gate-score-matrix/score-matrix/yfinance_root_gate_score_matrix.json"
PROVIDER_READBACK = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T070440-codex-provider-universe-manifest-readback/provider-universe-manifest/provider_universe_manifest_readback.json"

MAIN_ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
DIRECT_OVERLAYS = ["Manipulation"]
USABLE_DATA_STATUSES = {"ok", "derived_ok"}


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


def score_lookup(score_matrix: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for row in score_matrix["score_rows"]:
        out[(row["symbol"], row["timeframe"])] = row
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    fetch_matrix = load_json(FETCH_MATRIX)
    score_matrix = load_json(SCORE_MATRIX)
    provider_readback = load_json(PROVIDER_READBACK)
    scores = score_lookup(score_matrix)

    rows: list[dict[str, Any]] = []
    for fetch_row in fetch_matrix["rows"]:
        symbol = fetch_row["symbol"]
        timeframe = fetch_row["timeframe"]
        score_row = scores.get((symbol, timeframe), {})
        root_hit_counts = {
            root: int(score_row.get("root_hits", {}).get(root, {}).get("candidate_rows", 0))
            for root in MAIN_ROOTS
        }
        rows.append(
            {
                "provider": "yfinance",
                "symbol": symbol,
                "timeframe": timeframe,
                "data_status": fetch_row["status"],
                "data_usable": fetch_row["status"] in USABLE_DATA_STATUSES,
                "bars": int(fetch_row.get("bars", 0)),
                "score_status": score_row.get("status", "missing_score_row"),
                "label_source_status": "unsupported_missing_independent_root_labels",
                "label_calibration_status": "blocked",
                "unsupported_reason": "yfinance_close_matrix_has_prices_but_no_source_backed_root_labels_per_cell",
                "bull_candidate_rows": root_hit_counts["Bull"],
                "bear_candidate_rows": root_hit_counts["Bear"],
                "sideways_candidate_rows": root_hit_counts["Sideways"],
                "crisis_candidate_rows": root_hit_counts["Crisis"],
                "manipulation_overlay_status": "not_applicable_to_bar_ohlcv_cell",
                "manipulation_reason": "direct_event_overlay_requires_order_lifecycle_l2_l3_mbo_social_or_onchain_event_evidence",
            }
        )

    total_cells = len(rows)
    ok_data_cells = sum(1 for row in rows if row["data_usable"])
    scored_cells = sum(1 for row in rows if row["score_status"] == "scored")
    label_ready_cells = sum(1 for row in rows if row["label_calibration_status"] == "ready")
    unsupported_label_cells = sum(
        1 for row in rows if row["label_source_status"] == "unsupported_missing_independent_root_labels"
    )

    root_summary: dict[str, dict[str, Any]] = {}
    for root in MAIN_ROOTS:
        field = f"{root.lower()}_candidate_rows"
        root_summary[root] = {
            "cells_audited": total_cells,
            "data_ok_cells": ok_data_cells,
            "scored_cells": scored_cells,
            "label_ready_cells": 0,
            "unsupported_label_cells": unsupported_label_cells,
            "candidate_rows_seen_in_close_only_score": int(sum(row[field] for row in rows)),
            "candidate_hit_cells_in_close_only_score": int(sum(1 for row in rows if row[field] > 0)),
            "calibration_gate": "blocked_missing_independent_source_labels",
        }

    manipulation_summary = {
        "overlay": "Manipulation",
        "bar_ohlcv_cells_audited": total_cells,
        "bar_ohlcv_cells_accepted_for_overlay": 0,
        "bar_ohlcv_status": "not_applicable",
        "accepted_direct_varieties": [
            {
                "variety": "classified_telegram_coin_pump_event_present",
                "packet": "20260511T045102+0800-codex-mehrnoom-telegram-direct-manipulation-gate",
                "role": "suppress_abstain_cooldown_overlay",
            }
        ],
        "blocked_or_diagnostic_varieties": [
            "raw_telegram_message_text_gate_below_95",
            "twitter_social_aggregate_below_95",
            "systemslab_hgb_event_rank_gate_below_95",
            "mendeley_gox_hgb_wash_gate_below_95",
            "bayi_sequence_gate_below_95",
            "kaggle_nft_wash_gate_below_95",
            "l2_l3_mbo_order_lifecycle_inputs_missing",
            "onchain_direct_event_inputs_missing",
        ],
        "calibration_gate": "bar_cells_fail_closed_for_manipulation_overlay",
    }

    pending_provider_cells = provider_readback["provider_status_readback"]["pending_cells_must_be_recorded"]

    report = {
        "run_id": RUN_ID,
        "goal_achieved": False,
        "objective": "Audit whether the ready yfinance full species/cycle matrix has independent labels for accepted MainRegimeV2 root calibration.",
        "source_artifacts": {
            "fetch_matrix": rel(FETCH_MATRIX),
            "score_matrix": rel(SCORE_MATRIX),
            "provider_readback": rel(PROVIDER_READBACK),
        },
        "main_price_roots": MAIN_ROOTS,
        "direct_overlay_gates": DIRECT_OVERLAYS,
        "cell_count": total_cells,
        "ok_data_cells": ok_data_cells,
        "scored_cells": scored_cells,
        "label_ready_cells": label_ready_cells,
        "unsupported_label_cells": unsupported_label_cells,
        "root_summary": root_summary,
        "manipulation_summary": manipulation_summary,
        "pending_provider_cells": pending_provider_cells,
        "rows": rows,
        "completion_accounting": {
            "accepted_full_cycle_full_universe": False,
            "why_not_accepted": [
                "All 126 yfinance cells have usable close data and close-only root scores, but none carry independent source-backed root labels.",
                "Deriving labels from the same close-only rule features would be circular and is not accepted as calibrated 95% evidence.",
                "Manipulation is a direct-event overlay and cannot be accepted from yfinance OHLCV/bar cells.",
                "IBKR, TradingViewRemix, and public crypto provider cells remain pending with explicit blocker reasons.",
            ],
        },
        "raw_ohlcv_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "gate_result": "blocked_yfinance_full_matrix_missing_independent_root_labels",
        "next_action": "Attach an independent labeled root source to the ready yfinance cells, or mark each provider/symbol/timeframe cell unsupported by source-label reason; separately expand direct Manipulation varieties only from direct event/order-lifecycle sources.",
        "artifacts": {
            "readiness_json": rel(OUT_DIR / "yfinance_label_calibration_readiness.json"),
            "readiness_md": rel(OUT_DIR / "yfinance_label_calibration_readiness.md"),
            "readiness_csv": rel(OUT_DIR / "yfinance_label_calibration_readiness.csv"),
            "assertions": rel(CHECK_DIR / "yfinance_label_calibration_readiness_assertions.out"),
            "script": rel(Path(__file__)),
        },
    }

    (OUT_DIR / "yfinance_label_calibration_readiness.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )

    with (OUT_DIR / "yfinance_label_calibration_readiness.csv").open("w", newline="") as handle:
        fieldnames = list(rows[0].keys()) if rows else []
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# YFinance Label Calibration Readiness",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Goal achieved: `false`",
        "",
        "## Summary",
        "",
        f"- Cells audited: `{total_cells}`",
        f"- Data OK cells: `{ok_data_cells}`",
        f"- Close-only scored cells: `{scored_cells}`",
        f"- Independent-label-ready cells: `{label_ready_cells}`",
        f"- Unsupported label cells: `{unsupported_label_cells}`",
        "",
        "## Main Price Root Readiness",
        "",
        "| Root | Data OK Cells | Scored Cells | Label Ready Cells | Unsupported Label Cells | Close-Only Candidate Rows | Gate |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for root, item in root_summary.items():
        lines.append(
            f"| `{root}` | {item['data_ok_cells']} | {item['scored_cells']} | "
            f"{item['label_ready_cells']} | {item['unsupported_label_cells']} | "
            f"{item['candidate_rows_seen_in_close_only_score']} | `{item['calibration_gate']}` |"
        )
    lines.extend(
        [
            "",
            "## Manipulation Overlay",
            "",
            "- Yfinance OHLCV/bar cells accepted for direct `Manipulation`: `0`.",
            "- Reason: the overlay requires direct event, order-lifecycle, L2/L3/MBO, social, or on-chain evidence; bar proxies fail closed.",
            "- Accepted direct variety preserved: `classified_telegram_coin_pump_event_present` from the Mehrnoom/Mirtaheri Telegram event packet.",
            "",
            "## Pending Provider Cells",
            "",
        ]
    )
    for pending_cell in pending_provider_cells:
        lines.append(f"- `{pending_cell}`")
    lines.extend(
        [
            "",
            "## Accounting",
            "",
            "- This run converts the yfinance label blocker into an explicit 126-cell readiness matrix.",
            "- It does not derive labels from the same close-only features.",
            "- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.",
            "",
            "Gate result: `blocked_yfinance_full_matrix_missing_independent_root_labels`",
        ]
    )
    (OUT_DIR / "yfinance_label_calibration_readiness.md").write_text("\n".join(lines) + "\n")

    assertion_lines = [
        "goal_achieved=false",
        f"cell_count={total_cells}",
        f"ok_data_cells={ok_data_cells}",
        f"scored_cells={scored_cells}",
        f"label_ready_cells={label_ready_cells}",
        f"unsupported_label_cells={unsupported_label_cells}",
    ]
    for root, item in root_summary.items():
        assertion_lines.append(f"{root}.label_ready_cells={item['label_ready_cells']}")
        assertion_lines.append(f"{root}.unsupported_label_cells={item['unsupported_label_cells']}")
        assertion_lines.append(f"{root}.calibration_gate={item['calibration_gate']}")
    assertion_lines.extend(
        [
            f"Manipulation.bar_ohlcv_cells_accepted_for_overlay={manipulation_summary['bar_ohlcv_cells_accepted_for_overlay']}",
            "accepted_full_cycle_full_universe=false",
            "raw_ohlcv_committed=false",
            "runtime_code_changed=false",
            "thresholds_relaxed=false",
            "trade_usable=false",
            "gate_result=blocked_yfinance_full_matrix_missing_independent_root_labels",
        ]
    )
    (CHECK_DIR / "yfinance_label_calibration_readiness_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n"
    )

    print(rel(OUT_DIR / "yfinance_label_calibration_readiness.json"))


if __name__ == "__main__":
    main()
