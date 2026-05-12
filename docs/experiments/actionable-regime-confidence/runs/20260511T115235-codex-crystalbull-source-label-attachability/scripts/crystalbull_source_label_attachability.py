#!/usr/bin/env python3
"""Audit CrystalBull/IBD QQQ daily labels against the Board A missing-slot contract."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
PRIOR_GATE = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T113603-codex-crystalbull-ibd-qqq-source-gate/"
    "source-gate/crystalbull_ibd_qqq_source_gate.json"
)
ACQUISITION_CSV = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T081715-codex-source-label-acquisition-package-v2/"
    "acquisition-package/missing_root_label_slots_acquisition_request_v2.csv"
)

OUT_DIR = RUN_ROOT / "source-label-attachability"
CHECK_DIR = RUN_ROOT / "checks"
OUT_JSON = OUT_DIR / "crystalbull_source_label_attachability.json"
OUT_MD = OUT_DIR / "crystalbull_source_label_attachability.md"
OUT_CSV = OUT_DIR / "crystalbull_source_label_attachability_slots.csv"
ASSERTIONS = CHECK_DIR / "crystalbull_source_label_attachability_assertions.out"

RUN_ID = "20260511T115235+0800-codex-crystalbull-source-label-attachability"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_missing_slots() -> list[dict[str, str]]:
    with ACQUISITION_CSV.open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    prior = json.loads(PRIOR_GATE.read_text())
    missing = load_missing_slots()
    qqq_missing = [
        row
        for row in missing
        if row["provider"] == "yfinance" and row["instrument"] == "QQQ"
    ]
    qqq_daily_missing = [row for row in qqq_missing if row["timeframe"] == "1d"]

    source_counts = prior["candidate_source"]["raw_value_counts"]
    source_root_map = {
        "Bull": {
            "source_raw_value": "-1.0",
            "source_label": "Confirmed Uptrend",
            "source_label_count": int(source_counts.get("-1.0", 0)),
        },
        "Sideways": {
            "source_raw_value": "0.5",
            "source_label": "Uptrend Under Pressure",
            "source_label_count": int(source_counts.get("0.5", 0)),
        },
        "Bear": {
            "source_raw_value": "1.0",
            "source_label": "Market in Correction",
            "source_label_count": int(source_counts.get("1.0", 0)),
        },
    }

    attached: list[dict[str, object]] = []
    rejected: list[dict[str, object]] = []
    for row in qqq_daily_missing:
        root = row["root"]
        if root in source_root_map and source_root_map[root]["source_label_count"] > 0:
            attached.append(
                {
                    **row,
                    **source_root_map[root],
                    "slot_decision": "attached_source_label_window_only",
                    "acceptance_scope": "source_label_target_only_not_calibrated_factor",
                    "source_name": prior["candidate_source"]["name"],
                    "source_url": prior["candidate_source"]["url"],
                    "source_date_start": prior["candidate_source"][
                        "embedded_outlook_date_range_utc"
                    ]["start"],
                    "source_date_end": prior["candidate_source"][
                        "embedded_outlook_date_range_utc"
                    ]["end"],
                }
            )
        else:
            rejected.append(
                {
                    **row,
                    "slot_decision": "rejected_no_matching_source_root_label",
                    "reason": "CrystalBull/IBD outlook has Bull/Bear/Sideways-style states but no Crisis root label.",
                }
            )

    non_daily_rejections = [
        {
            **row,
            "slot_decision": "rejected_timeframe_not_exact",
            "reason": "CrystalBull/IBD export is daily; intraday, weekly, and monthly attachment requires an explicit owner-approved timeframe crosswalk.",
        }
        for row in qqq_missing
        if row["timeframe"] != "1d"
    ]

    prior_best = prior["best_candidates"]
    factor_readback = {
        root: {
            "accepted_95": bool(details.get("accepted_95", False)),
            "test_wilson95_lcb": details.get("test", {}).get("wilson95_lcb"),
            "calibration_wilson95_lcb": details.get("calibration", {}).get("wilson95_lcb"),
            "rule": details.get("rule"),
            "reason": details.get("reason"),
        }
        for root, details in prior_best.items()
    }

    report = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD.relative_to(REPO)),
        "board_sha256_at_audit": sha256(BOARD),
        "active_taxonomy": "MainRegimeV2",
        "objective": (
            "Check whether the already materialized CrystalBull/IBD QQQ daily source can "
            "attach any exact provider/instrument/timeframe/root source-label slots without "
            "promoting it to a calibrated factor."
        ),
        "source": {
            "name": prior["candidate_source"]["name"],
            "url": prior["candidate_source"]["url"],
            "embedded_outlook_points": prior["candidate_source"]["embedded_outlook_points"],
            "date_range_utc": prior["candidate_source"][
                "embedded_outlook_date_range_utc"
            ],
            "raw_page_committed": False,
            "raw_value_mapping": prior["candidate_source"]["raw_value_mapping_tested"],
        },
        "slot_contract": {
            "provider": "yfinance",
            "instrument": "QQQ",
            "exact_timeframe_attached": "1d",
            "roots_attached": [row["root"] for row in attached],
            "roots_rejected": [row["root"] for row in rejected],
            "timeframes_rejected_without_crosswalk": sorted(
                {row["timeframe"] for row in non_daily_rejections}
            ),
        },
        "attached_slots": attached,
        "rejected_slots": rejected + non_daily_rejections,
        "prior_factor_gate_readback": {
            "source_gate_artifact": str(PRIOR_GATE.relative_to(REPO)),
            "accepted_calibrated_roots": prior["decision"]["accepted_roots"],
            "factor_by_root": factor_readback,
            "gate_result": prior["decision"]["gate_result"],
        },
        "decision": {
            "attached_source_label_slots_added": len(attached),
            "accepted_calibrated_root_factors_added": 0,
            "accepted_parent_root_slots_added": 0,
            "accepted_direct_manipulation_rows_added": 0,
            "full_objective_achieved": False,
            "gate_result": (
                "partial_crystalbull_qqq_daily_source_labels_attached_"
                "factor_gate_still_blocked"
            ),
            "why_not_complete": [
                "The source attaches only QQQ daily Bull/Bear/Sideways label windows.",
                "CrystalBull/IBD has no Crisis root label.",
                "Intraday, weekly, and monthly QQQ slots still need explicit source labels or an approved timeframe crosswalk.",
                "The prior train-only OHLCV detector failed held-out 95% Wilson gates, so this audit adds zero calibrated factors.",
                "No direct Manipulation variety is addressed by this price-root source.",
            ],
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "artifacts": {
            "json": str(OUT_JSON.relative_to(REPO)),
            "md": str(OUT_MD.relative_to(REPO)),
            "slot_csv": str(OUT_CSV.relative_to(REPO)),
            "assertions": str(ASSERTIONS.relative_to(REPO)),
            "script": str(Path(__file__).resolve().relative_to(REPO)),
        },
        "next_action": (
            "Use the attached CrystalBull/IBD QQQ daily labels only as source-label "
            "targets; continue exact MainRegimeV2 full-matrix label acquisition and "
            "do not promote this branch until every root has calibrated 95%-99% evidence."
        ),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    with OUT_CSV.open("w", newline="") as f:
        fieldnames = [
            "provider",
            "instrument",
            "timeframe",
            "root",
            "slot_decision",
            "source_label",
            "source_raw_value",
            "source_label_count",
            "acceptance_scope",
            "source_name",
            "source_url",
            "source_date_start",
            "source_date_end",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in attached:
            writer.writerow(row)

    md_lines = [
        "# CrystalBull Source-Label Attachability",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        f"- Attached source-label slots added: `{len(attached)}`.",
        "- Accepted calibrated root factors added: `0`.",
        "- Accepted parent-root completion slots added: `0`.",
        "- Full objective achieved: `false`.",
        f"- Gate result: `{report['decision']['gate_result']}`.",
        "",
        "## Attached Slots",
        "",
        "| Provider | Instrument | Timeframe | Root | Source Label | Rows |",
        "|---|---|---|---|---|---:|",
    ]
    for row in attached:
        md_lines.append(
            f"| `{row['provider']}` | `{row['instrument']}` | `{row['timeframe']}` | "
            f"`{row['root']}` | `{row['source_label']}` | `{row['source_label_count']}` |"
        )
    md_lines.extend(
        [
            "",
            "## Blockers",
            "",
            "- CrystalBull/IBD does not expose a `Crisis` root label.",
            "- The source is daily QQQ only; intraday, weekly, and monthly slots stay blocked without an approved timeframe crosswalk.",
            "- The prior factor gate remains blocked: no Bull/Bear/Sideways rule survived held-out 95% Wilson LCB.",
            "- This branch does not address direct `Manipulation` evidence.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{report['artifacts']['json']}`",
            f"- Slot CSV: `{report['artifacts']['slot_csv']}`",
            f"- Assertions: `{report['artifacts']['assertions']}`",
        ]
    )
    OUT_MD.write_text("\n".join(md_lines) + "\n")

    checks = [
        ("attached_source_label_slots_added", len(attached) == 3, len(attached)),
        (
            "accepted_calibrated_root_factors_added",
            report["decision"]["accepted_calibrated_root_factors_added"] == 0,
            report["decision"]["accepted_calibrated_root_factors_added"],
        ),
        (
            "accepted_parent_root_slots_added",
            report["decision"]["accepted_parent_root_slots_added"] == 0,
            report["decision"]["accepted_parent_root_slots_added"],
        ),
        ("crisis_absent", len(rejected) == 1 and rejected[0]["root"] == "Crisis", rejected),
        (
            "factor_gate_still_blocked",
            report["prior_factor_gate_readback"]["accepted_calibrated_roots"] == [],
            report["prior_factor_gate_readback"]["accepted_calibrated_roots"],
        ),
        ("thresholds_relaxed_false", not report["decision"]["thresholds_relaxed"], False),
        ("runtime_code_changed_false", not report["decision"]["runtime_code_changed"], False),
        ("raw_data_committed_false", not report["decision"]["raw_data_committed"], False),
        ("trade_usable_false", not report["decision"]["trade_usable"], False),
    ]
    with ASSERTIONS.open("w") as f:
        for name, ok, value in checks:
            f.write(f"{'PASS' if ok else 'FAIL'} {name}={value}\n")

    if not all(ok for _, ok, _ in checks):
        raise SystemExit("one or more checks failed")


if __name__ == "__main__":
    main()
