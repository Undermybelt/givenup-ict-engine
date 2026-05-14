#!/usr/bin/env python3
"""Build the source-label panel contract for ready Board A cells.

The contract expands provider/symbol/timeframe/root slots so the remaining
source-label gap is concrete. It does not derive labels from proxy OHLCV scores
and does not relax acceptance thresholds.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T073700+0800-codex-root-label-panel-contract"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T073700-codex-root-label-panel-contract"
OUT_DIR = RUN_ROOT / "label-panel-contract"
CHECK_DIR = RUN_ROOT / "checks"

ATTACHABILITY = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T073430-codex-source-label-attachability-audit/source-label-attachability/source_label_attachability_audit.json"
KRAKEN_LANE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T072500-codex-kraken-public-lowpollution-lane/kraken-lane/kraken_public_lowpollution_lane.json"
SOURCE_SCAN = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T073600-codex-source-label-web-acquisition-scan/source-scan/source_label_web_acquisition_scan.json"

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
YFINANCE_ROOT_FIELDS = {
    "Bull": "bull_source_status",
    "Bear": "bear_source_status",
    "Sideways": "sideways_source_status",
    "Crisis": "crisis_source_status",
}


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


def yfinance_slots(attachability: dict[str, Any]) -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []
    for row in attachability["rows"]:
        for root in ROOTS:
            source_status = row[YFINANCE_ROOT_FIELDS[root]]
            if source_status == "existing_packet_overlap":
                slot_status = "attached_existing_packet_sparse"
                required_action = "preserve_as_provenance_but_do_not_count_full_panel_complete"
            else:
                slot_status = "missing_independent_source_label"
                required_action = "acquire_or_materialize_independent_source_label_for_this_root_cell"
            slots.append(
                {
                    "provider": "yfinance",
                    "instrument": row["symbol"],
                    "timeframe": row["timeframe"],
                    "root": root,
                    "data_status": row["data_status"],
                    "slot_status": slot_status,
                    "source_status": source_status,
                    "proxy_scores_allowed_for_acceptance": False,
                    "required_action": required_action,
                }
            )
    return slots


def kraken_slots(kraken: dict[str, Any]) -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []
    for cell in kraken["cells"]:
        for root in ROOTS:
            if cell["data_status"] == "usable":
                slot_status = "missing_independent_source_label"
                required_action = "acquire_or_materialize_independent_source_label_for_this_root_cell"
            else:
                slot_status = "provider_interval_unsupported"
                required_action = "keep_unsupported_or_replace_with_source_label_supported_interval"
            slots.append(
                {
                    "provider": "kraken_public_lowpollution_http",
                    "instrument": cell["pair"],
                    "timeframe": cell["timeframe"],
                    "root": root,
                    "data_status": cell["data_status"],
                    "slot_status": slot_status,
                    "source_status": cell["label_status"],
                    "proxy_scores_allowed_for_acceptance": False,
                    "required_action": required_action,
                }
            )
    return slots


def summarize_slots(slots: list[dict[str, Any]]) -> dict[str, Any]:
    by_status = Counter(slot["slot_status"] for slot in slots)
    by_provider_status = Counter((slot["provider"], slot["slot_status"]) for slot in slots)
    by_root_status = Counter((slot["root"], slot["slot_status"]) for slot in slots)
    attached = by_status.get("attached_existing_packet_sparse", 0)
    complete_ready = by_status.get("accepted_full_panel_label", 0)
    missing = by_status.get("missing_independent_source_label", 0)
    unsupported = by_status.get("provider_interval_unsupported", 0)
    return {
        "total_slots": len(slots),
        "attached_existing_packet_sparse_slots": attached,
        "accepted_full_panel_label_slots": complete_ready,
        "missing_independent_source_label_slots": missing,
        "provider_interval_unsupported_slots": unsupported,
        "slot_status_counts": dict(sorted(by_status.items())),
        "provider_status_counts": {
            f"{provider}:{status}": count
            for (provider, status), count in sorted(by_provider_status.items())
        },
        "root_status_counts": {
            f"{root}:{status}": count
            for (root, status), count in sorted(by_root_status.items())
        },
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    attachability = load_json(ATTACHABILITY)
    kraken = load_json(KRAKEN_LANE)
    source_scan = load_json(SOURCE_SCAN)

    slots = [*yfinance_slots(attachability), *kraken_slots(kraken)]
    summary = summarize_slots(slots)

    report = {
        "run_id": RUN_ID,
        "goal_achieved": False,
        "objective": "Expand the current yfinance/Kraken Board A cells into explicit source-label slots by MainRegimeV2 root.",
        "source_artifacts": {
            "source_label_attachability": rel(ATTACHABILITY),
            "kraken_public_lane": rel(KRAKEN_LANE),
            "source_label_web_acquisition_scan": rel(SOURCE_SCAN),
        },
        "main_price_roots": ROOTS,
        "summary": summary,
        "completion_accounting": {
            "accepted_full_cycle_full_universe": False,
            "gate_result": "blocked_root_label_panel_contract_requires_external_labels",
            "why_not_accepted": [
                "No slot has accepted_full_panel_label status.",
                "Existing accepted packets remain sparse provenance only, not a full provider/cycle label panel.",
                "Missing independent labels cannot be replaced by close/OHLC proxy scores.",
                "The source web acquisition scan found no public full-matrix label panel.",
            ],
        },
        "source_scan_gate_result": source_scan["gate_result"],
        "raw_ohlcv_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "gate_result": "blocked_root_label_panel_contract_requires_external_labels",
        "next_action": "Provide or acquire an explicitly labeled multi-asset multi-timeframe MainRegimeV2 panel, then attach it to this slot contract and rerun calibration; otherwise keep full-universe completion blocked.",
        "artifacts": {
            "contract_json": rel(OUT_DIR / "root_label_panel_contract.json"),
            "contract_md": rel(OUT_DIR / "root_label_panel_contract.md"),
            "contract_csv": rel(OUT_DIR / "root_label_panel_contract.csv"),
            "assertions": rel(CHECK_DIR / "root_label_panel_contract_assertions.out"),
            "script": rel(Path(__file__)),
        },
    }

    (OUT_DIR / "root_label_panel_contract.json").write_text(
        json.dumps({**report, "slots": slots}, indent=2, sort_keys=True) + "\n"
    )

    with (OUT_DIR / "root_label_panel_contract.csv").open("w", newline="") as handle:
        fieldnames = list(slots[0].keys())
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(slots)

    lines = [
        "# Root Label Panel Contract",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Goal achieved: `false`",
        "",
        "## Summary",
        "",
        f"- Total root-label slots: `{summary['total_slots']}`",
        f"- Attached sparse existing-packet slots: `{summary['attached_existing_packet_sparse_slots']}`",
        f"- Accepted full-panel label slots: `{summary['accepted_full_panel_label_slots']}`",
        f"- Missing independent source-label slots: `{summary['missing_independent_source_label_slots']}`",
        f"- Provider-interval unsupported slots: `{summary['provider_interval_unsupported_slots']}`",
        "",
        "## Status Counts",
        "",
        "| Status | Slots |",
        "|---|---:|",
    ]
    for status, count in summary["slot_status_counts"].items():
        lines.append(f"| `{status}` | {count} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Gate result: `blocked_root_label_panel_contract_requires_external_labels`",
            "- Proxy OHLCV scores are explicitly not accepted as label slots.",
            "- No thresholds were relaxed.",
            "- No runtime code changed.",
            "- No raw OHLCV was committed.",
            "",
            "## Next Action",
            "",
            report["next_action"],
        ]
    )
    (OUT_DIR / "root_label_panel_contract.md").write_text("\n".join(lines) + "\n")

    assertion_lines = [
        "goal_achieved=false",
        f"total_slots={summary['total_slots']}",
        f"accepted_full_panel_label_slots={summary['accepted_full_panel_label_slots']}",
        f"missing_independent_source_label_slots={summary['missing_independent_source_label_slots']}",
        f"provider_interval_unsupported_slots={summary['provider_interval_unsupported_slots']}",
        "thresholds_relaxed=false",
        "runtime_code_changed=false",
        "gate_result=blocked_root_label_panel_contract_requires_external_labels",
    ]
    (CHECK_DIR / "root_label_panel_contract_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n"
    )

    print(rel(OUT_DIR / "root_label_panel_contract.json"))
    print("\n".join(assertion_lines))


if __name__ == "__main__":
    main()
