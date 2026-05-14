#!/usr/bin/env python3
"""Audit whether existing accepted packets can label the yfinance matrix.

This is an attachability audit, not a new calibration. It keeps accepted
sampled packets as provenance and checks whether they form a complete
source-backed label panel for every yfinance symbol/timeframe cell.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T073430+0800-codex-source-label-attachability-audit"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T073430-codex-source-label-attachability-audit"
OUT_DIR = RUN_ROOT / "source-label-attachability"
CHECK_DIR = RUN_ROOT / "checks"

YFINANCE_MATRIX = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T070440-codex-provider-universe-manifest-readback/yfinance-full-matrix/yfinance_full_universe_fetch_matrix.json"
READINESS = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T072200-codex-yfinance-label-calibration-readiness/label-calibration/yfinance_label_calibration_readiness.json"
PROVIDER_READBACK = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T070440-codex-provider-universe-manifest-readback/provider-universe-manifest/provider_universe_manifest_readback.json"

BULL_PACKET = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T035045-codex-kaggle-bull-coverage-buffer-gate/kaggle-bull-gate/kaggle_bull_coverage_buffer_gate_report.json"
YAHOO_PACKET = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T041923-codex-yahoo-sourcebacked-parent-root-gate/yahoo-parent-root-gate/yahoo_sourcebacked_parent_root_gate_report.json"
CRISIS_PACKET = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T235220-codex-broader-root-v2-probe/root-v2-broader/main_regime_v2_broader_root_calibration_report.json"
MANIPULATION_PACKET = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T045102-codex-mehrnoom-telegram-direct-manipulation-gate/direct-event-gate/mehrnoom_telegram_direct_manipulation_gate_report.json"

MAIN_ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]


@dataclass(frozen=True)
class SourcePacket:
    root: str
    packet_id: str
    artifact: Path
    source_kind: str
    rule: str
    calibration_wilson95: float
    test_wilson95: float
    validation_pairs: frozenset[tuple[str, str]]
    granularity: str


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


def pairs_from_contexts(contexts: list[str]) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for context in contexts:
        parts = context.split(":")
        if len(parts) >= 2:
            pairs.add((parts[0], parts[-1]))
    return pairs


def pairs_from_split_payloads(payloads: list[dict[str, Any]]) -> tuple[set[tuple[str, str]], str]:
    pairs: set[tuple[str, str]] = set()
    exact_seen = False
    for payload in payloads:
        contexts = payload.get("validation_contexts") or []
        if contexts:
            pairs.update(pairs_from_contexts(contexts))
            exact_seen = True
            continue
        instruments = payload.get("validation_instruments") or []
        timeframes = payload.get("validation_timeframes") or []
        for symbol in instruments:
            for timeframe in timeframes:
                pairs.add((symbol, timeframe))
    if exact_seen:
        return pairs, "reported_symbol_timeframe_contexts"
    return pairs, "instrument_timeframe_cross_product_from_report_summary"


def bull_packet() -> SourcePacket:
    data = load_json(BULL_PACKET)
    pairs, granularity = pairs_from_split_payloads([data["calibration"], data["test"]])
    return SourcePacket(
        root="Bull",
        packet_id=data["loop_id"],
        artifact=BULL_PACKET,
        source_kind="kaggle_regime_label_source",
        rule=data["rule"],
        calibration_wilson95=float(data["calibration"]["precision_wilson_lcb_95"]),
        test_wilson95=float(data["test"]["precision_wilson_lcb_95"]),
        validation_pairs=frozenset(pairs),
        granularity=granularity,
    )


def yahoo_packets() -> list[SourcePacket]:
    data = load_json(YAHOO_PACKET)
    packets: list[SourcePacket] = []
    for root in ["Bear", "Sideways"]:
        report = data["root_reports"][root]
        pairs, granularity = pairs_from_split_payloads([report["calibration"], report["test"]])
        packets.append(
            SourcePacket(
                root=root,
                packet_id=data["loop_id"],
                artifact=YAHOO_PACKET,
                source_kind="yahoo_public_source_backed_definition",
                rule=report["rule"],
                calibration_wilson95=float(report["calibration"]["precision_wilson_lcb_95"]),
                test_wilson95=float(report["test"]["precision_wilson_lcb_95"]),
                validation_pairs=frozenset(pairs),
                granularity=granularity,
            )
        )
    return packets


def crisis_packet() -> SourcePacket:
    data = load_json(CRISIS_PACKET)
    report = next(item for item in data["root_reports"] if item["root_class"] == "Crisis")
    selected = report["selected_candidate"]
    pairs, granularity = pairs_from_split_payloads([selected["calibration"], selected["test"]])
    return SourcePacket(
        root="Crisis",
        packet_id=data["loop_id"],
        artifact=CRISIS_PACKET,
        source_kind="broader_root_v2_source_backed_stress_panel",
        rule=selected["rule"],
        calibration_wilson95=float(selected["calibration"]["precision_wilson_lcb_95"]),
        test_wilson95=float(selected["test"]["precision_wilson_lcb_95"]),
        validation_pairs=frozenset(pairs),
        granularity=granularity,
    )


def manipulation_summary() -> dict[str, Any]:
    data = load_json(MANIPULATION_PACKET)
    return {
        "overlay": "Manipulation",
        "packet_id": data["run_id"],
        "artifact": rel(MANIPULATION_PACKET),
        "source_kind": data["evidence_class"],
        "accepted_95": bool(data["accepted_95"]),
        "rule": data["rule"],
        "allowed_action": data["allowed_action"],
        "bar_matrix_attachable_cells": 0,
        "attachability_gate": "not_applicable_to_yfinance_ohlcv_bar_cells",
        "why": "direct event overlay requires event/order-lifecycle/L2/L3/MBO/social/on-chain evidence, not OHLCV bar cells",
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    matrix = load_json(YFINANCE_MATRIX)
    readiness = load_json(READINESS)
    provider_readback = load_json(PROVIDER_READBACK)

    packets = [bull_packet(), *yahoo_packets(), crisis_packet()]
    packet_by_root = {packet.root: packet for packet in packets}

    rows: list[dict[str, Any]] = []
    root_match_counts = {root: 0 for root in MAIN_ROOTS}
    cells_with_any_root = 0
    full_root_ready_cells = 0

    for item in matrix["rows"]:
        symbol = item["symbol"]
        timeframe = item["timeframe"]
        per_root: dict[str, str] = {}
        matched_roots: list[str] = []
        for root in MAIN_ROOTS:
            packet = packet_by_root[root]
            if (symbol, timeframe) in packet.validation_pairs:
                per_root[root] = "existing_packet_overlap"
                matched_roots.append(root)
                root_match_counts[root] += 1
            else:
                per_root[root] = "unsupported_no_existing_accepted_packet_for_symbol_timeframe"

        if matched_roots:
            cells_with_any_root += 1
        if len(matched_roots) == len(MAIN_ROOTS):
            full_root_ready_cells += 1

        rows.append(
            {
                "provider": "yfinance",
                "symbol": symbol,
                "timeframe": timeframe,
                "data_status": item["status"],
                "any_existing_packet_overlap": bool(matched_roots),
                "matched_roots": ";".join(matched_roots),
                "full_main_roots_attached": len(matched_roots) == len(MAIN_ROOTS),
                "bull_source_status": per_root["Bull"],
                "bear_source_status": per_root["Bear"],
                "sideways_source_status": per_root["Sideways"],
                "crisis_source_status": per_root["Crisis"],
                "manipulation_overlay_status": "not_applicable_to_bar_ohlcv_cell",
                "unsupported_reason": (
                    "no cell has all four MainRegimeV2 root labels attached from existing accepted packets"
                    if matched_roots
                    else "no accepted source packet overlaps this symbol/timeframe"
                ),
            }
        )

    unsupported_cells = len(rows) - full_root_ready_cells
    source_packets = []
    for packet in packets:
        source_packets.append(
            {
                "root": packet.root,
                "packet_id": packet.packet_id,
                "artifact": rel(packet.artifact),
                "source_kind": packet.source_kind,
                "rule": packet.rule,
                "calibration_wilson95": packet.calibration_wilson95,
                "test_wilson95": packet.test_wilson95,
                "validation_pair_count": len(packet.validation_pairs),
                "yfinance_matrix_overlap_cells": root_match_counts[packet.root],
                "granularity": packet.granularity,
            }
        )

    timeframes_without_full_labels = sorted(
        {row["timeframe"] for row in rows if not row["full_main_roots_attached"]}
    )
    symbols_without_full_labels = sorted(
        {row["symbol"] for row in rows if not row["full_main_roots_attached"]}
    )

    pending_provider_cells = provider_readback["provider_status_readback"]["pending_cells_must_be_recorded"]
    report = {
        "run_id": RUN_ID,
        "goal_achieved": False,
        "objective": "Check whether existing accepted 95% packets can attach independent/source-backed labels to the expanded yfinance symbol/timeframe matrix.",
        "source_artifacts": {
            "yfinance_matrix": rel(YFINANCE_MATRIX),
            "previous_label_readiness": rel(READINESS),
            "provider_readback": rel(PROVIDER_READBACK),
            "accepted_packets": [entry["artifact"] for entry in source_packets] + [rel(MANIPULATION_PACKET)],
        },
        "cell_count": len(rows),
        "cells_with_any_existing_root_packet_overlap": cells_with_any_root,
        "full_main_roots_attached_cells": full_root_ready_cells,
        "unsupported_full_root_label_cells": unsupported_cells,
        "previous_readiness_label_ready_cells": readiness["label_ready_cells"],
        "root_overlap_counts": root_match_counts,
        "source_packets": source_packets,
        "manipulation_overlay": manipulation_summary(),
        "timeframes_without_full_labels": timeframes_without_full_labels,
        "symbols_without_full_labels": symbols_without_full_labels,
        "pending_provider_cells": pending_provider_cells,
        "rows": rows,
        "completion_accounting": {
            "accepted_full_cycle_full_universe": False,
            "accepted_gate": "none_for_expanded_full_universe_full_cycle_goal",
            "why_not_accepted": [
                "Existing accepted root packets overlap only a sparse subset of the 126 yfinance cells.",
                "No yfinance symbol/timeframe cell has all four MainRegimeV2 root labels attached from existing accepted packets.",
                "Most full-cycle ladder cells remain unsupported by source-label reason, especially 1m, 5m, 30m, 4h, and 1mo.",
                "Manipulation remains a direct-event overlay and cannot be attached to OHLCV/bar cells.",
                "Pending IBKR, TradingViewRemix, and public crypto provider cells still require provider-specific readback or explicit source-label blockers.",
            ],
        },
        "raw_ohlcv_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "gate_result": "blocked_existing_packets_do_not_form_full_yfinance_label_panel",
        "next_action": "Acquire or materialize an independent/source-backed root label panel for the unsupported yfinance/provider cells; keep Manipulation expansion limited to direct event/order-lifecycle sources.",
        "artifacts": {
            "audit_json": rel(OUT_DIR / "source_label_attachability_audit.json"),
            "audit_md": rel(OUT_DIR / "source_label_attachability_audit.md"),
            "audit_csv": rel(OUT_DIR / "source_label_attachability_audit.csv"),
            "assertions": rel(CHECK_DIR / "source_label_attachability_audit_assertions.out"),
            "script": rel(Path(__file__)),
        },
    }

    (OUT_DIR / "source_label_attachability_audit.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    with (OUT_DIR / "source_label_attachability_audit.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Source Label Attachability Audit",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Goal achieved: `false`",
        "",
        "## Summary",
        "",
        f"- Yfinance matrix cells audited: `{len(rows)}`",
        f"- Cells with any existing accepted root-packet overlap: `{cells_with_any_root}`",
        f"- Cells with all four MainRegimeV2 roots attached: `{full_root_ready_cells}`",
        f"- Unsupported full-root label cells: `{unsupported_cells}`",
        f"- Previous readiness label-ready cells: `{readiness['label_ready_cells']}`",
        "",
        "## Root Overlap",
        "",
        "| Root | Existing Packet Overlap Cells | Source Packet | Test Wilson95 | Granularity |",
        "|---|---:|---|---:|---|",
    ]
    for packet in source_packets:
        lines.append(
            f"| `{packet['root']}` | {packet['yfinance_matrix_overlap_cells']} | "
            f"`{packet['packet_id']}` | {packet['test_wilson95']:.6f} | `{packet['granularity']}` |"
        )
    lines.extend(
        [
            "",
            "## Manipulation Overlay",
            "",
            "- Existing accepted `Manipulation` packet is direct social/event-confirmed.",
            "- Yfinance OHLCV/bar attachable cells: `0`.",
            "- It remains suppress/abstain/cooldown evidence, not a main price-root label and not a bar proxy.",
            "",
            "## Unsupported Coverage",
            "",
            f"- Timeframes without complete four-root labels: `{', '.join(timeframes_without_full_labels)}`",
            f"- Symbols without complete four-root labels: `{', '.join(symbols_without_full_labels)}`",
            "",
            "## Pending Provider Cells",
            "",
        ]
    )
    for pending in pending_provider_cells:
        lines.append(f"- `{pending}`")
    lines.extend(
        [
            "",
            "## Accounting",
            "",
            "- This run does not create new labels, fetch raw data, or relax thresholds.",
            "- Sparse overlap from accepted packets is provenance only; it is not enough for the expanded all-species/all-cycle gate.",
            "- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.",
            "",
            "Gate result: `blocked_existing_packets_do_not_form_full_yfinance_label_panel`",
        ]
    )
    (OUT_DIR / "source_label_attachability_audit.md").write_text("\n".join(lines) + "\n")

    assertion_lines = [
        "goal_achieved=false",
        f"cell_count={len(rows)}",
        f"cells_with_any_existing_root_packet_overlap={cells_with_any_root}",
        f"full_main_roots_attached_cells={full_root_ready_cells}",
        f"unsupported_full_root_label_cells={unsupported_cells}",
        f"previous_readiness_label_ready_cells={readiness['label_ready_cells']}",
    ]
    for root in MAIN_ROOTS:
        assertion_lines.append(f"{root}.existing_packet_overlap_cells={root_match_counts[root]}")
    assertion_lines.extend(
        [
            "Manipulation.bar_matrix_attachable_cells=0",
            "accepted_full_cycle_full_universe=false",
            "raw_ohlcv_committed=false",
            "runtime_code_changed=false",
            "thresholds_relaxed=false",
            "trade_usable=false",
            "gate_result=blocked_existing_packets_do_not_form_full_yfinance_label_panel",
        ]
    )
    (CHECK_DIR / "source_label_attachability_audit_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n"
    )

    print(rel(OUT_DIR / "source_label_attachability_audit.json"))


if __name__ == "__main__":
    main()
