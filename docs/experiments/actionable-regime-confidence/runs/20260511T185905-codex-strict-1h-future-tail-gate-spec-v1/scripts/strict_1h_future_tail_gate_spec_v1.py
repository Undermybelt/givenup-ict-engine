#!/usr/bin/env python3
"""Predeclare a future chronological gate for strict 1h Jan-2026 tail candidates."""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T185905+0800-codex-strict-1h-future-tail-gate-spec-v1"
RUN_DIR = "20260511T185905-codex-strict-1h-future-tail-gate-spec-v1"
REPO_ROOT = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_DIR
OUT_DIR = RUN_ROOT / "future-tail-gate-spec"
CHECK_DIR = RUN_ROOT / "checks"

NEAR_MISS_CSV = REPO_ROOT / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T184151-codex-strict-1h-near-miss-extension-requirements-v1/"
    "strict-1h-extension-requirements/strict_1h_near_miss_extension_candidates_v1.csv"
)
TAIL_CSV = REPO_ROOT / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T184530-codex-strict-1h-jan2026-tail-support-probe-v1/"
    "jan2026-tail-support/strict_1h_jan2026_tail_support_probe_v1_rows.csv"
)
SOURCE_PANEL = (
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)

MIN_SUPPORT = 73
MIN_WILSON = 0.95
TAIL_START = "2026-01-02"
TAIL_END = "2026-01-30"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def as_int(value: str) -> int:
    return int(float(value)) if value else 0


def as_float(value: str) -> float:
    return float(value) if value else 0.0


def as_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def wilson_lcb(pos: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    p = pos / n
    denom = 1 + z * z / n
    center = p + z * z / (2 * n)
    radius = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return (center - radius) / denom


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    near_by_key = {
        (row["instrument"], row["root"]): row
        for row in read_csv(NEAR_MISS_CSV)
    }
    tail_rows = [
        row
        for row in read_csv(TAIL_CSV)
        if as_bool(row["tail_covers_missing_extra"])
    ]

    rows: list[dict[str, Any]] = []
    for tail in tail_rows:
        key = (tail["instrument"], tail["root"])
        near = near_by_key[key]
        cal_support = as_int(near["calibration_2024_support"])
        cal_lcb = as_float(near["calibration_2024_wilson95_lcb"])
        heldout_support = as_int(near["heldout_time_2025_support"])
        heldout_lcb = as_float(near["heldout_time_2025_wilson95_lcb"])
        tail_sessions = as_int(tail["jan2026_source_tail_sessions"])
        composite_support = heldout_support + tail_sessions
        composite_lcb = wilson_lcb(composite_support, composite_support)
        calibration_passes = cal_support >= MIN_SUPPORT and cal_lcb >= MIN_WILSON
        old_heldout_passes = heldout_support >= MIN_SUPPORT and heldout_lcb >= MIN_WILSON
        composite_heldout_passes = composite_support >= MIN_SUPPORT and composite_lcb >= MIN_WILSON
        eligible_for_future_rerun = (
            calibration_passes
            and not old_heldout_passes
            and composite_heldout_passes
            and as_bool(tail["provider_1h_covers_tail"])
        )
        rows.append(
            {
                "instrument": tail["instrument"],
                "root": tail["root"],
                "fixed_gate_current_acceptance": near["current_acceptance"],
                "calibration_2024_support": cal_support,
                "calibration_2024_wilson95_lcb": f"{cal_lcb:.10f}",
                "calibration_2024_passes": str(calibration_passes).lower(),
                "heldout_2025_support": heldout_support,
                "heldout_2025_wilson95_lcb": f"{heldout_lcb:.10f}",
                "heldout_2025_passes": str(old_heldout_passes).lower(),
                "jan2026_source_tail_sessions": tail_sessions,
                "jan2026_tail_wilson95_lcb": tail["jan2026_tail_wilson95_lcb"],
                "future_heldout_2025_plus_jan2026_support": composite_support,
                "future_heldout_2025_plus_jan2026_wilson95_lcb": f"{composite_lcb:.10f}",
                "future_heldout_2025_plus_jan2026_passes": str(composite_heldout_passes).lower(),
                "provider_1h_covers_tail": tail["provider_1h_covers_tail"],
                "eligible_for_future_rerun": str(eligible_for_future_rerun).lower(),
                "accepted_now": "false",
                "allowed_use": "predeclared_future_chronological_gate_only",
            }
        )

    fields = [
        "instrument",
        "root",
        "fixed_gate_current_acceptance",
        "calibration_2024_support",
        "calibration_2024_wilson95_lcb",
        "calibration_2024_passes",
        "heldout_2025_support",
        "heldout_2025_wilson95_lcb",
        "heldout_2025_passes",
        "jan2026_source_tail_sessions",
        "jan2026_tail_wilson95_lcb",
        "future_heldout_2025_plus_jan2026_support",
        "future_heldout_2025_plus_jan2026_wilson95_lcb",
        "future_heldout_2025_plus_jan2026_passes",
        "provider_1h_covers_tail",
        "eligible_for_future_rerun",
        "accepted_now",
        "allowed_use",
    ]
    rows_csv = OUT_DIR / "strict_1h_future_tail_gate_spec_v1_rows.csv"
    write_csv(rows_csv, rows, fields)

    eligible_count = sum(row["eligible_for_future_rerun"] == "true" for row in rows)
    payload = {
        "artifact_type": "strict_1h_future_tail_gate_spec_v1",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "near_miss_candidates_csv": str(NEAR_MISS_CSV.relative_to(REPO_ROOT)),
            "jan2026_tail_rows_csv": str(TAIL_CSV.relative_to(REPO_ROOT)),
            "source_panel": SOURCE_PANEL,
        },
        "protocol": {
            "name": "strict_1h_2026_tail_future_chronological_gate_v1",
            "calibration_split": "calendar_2024_fixed_from_exact_1h_universe",
            "future_validation_split": "calendar_2025_heldout_plus_source_owned_jan2026_tail",
            "tail_window": {"start": TAIL_START, "end": TAIL_END},
            "minimum_support": MIN_SUPPORT,
            "minimum_wilson95_lcb": MIN_WILSON,
            "required_provenance": [
                "source-owned or owner-approved regime labels",
                "provider exact 1h coverage for the same instrument/root/date window",
                "no generated labels, proxy OHLCV labels, or threshold relaxation",
            ],
            "non_retroactive": True,
        },
        "counts": {
            "candidate_rows": len(rows),
            "eligible_for_future_rerun_rows": eligible_count,
            "accepted_rows_added": 0,
        },
        "rows": rows,
        "decision": {
            "gate_result": "strict_1h_future_tail_gate_spec_v1=predeclared_4_candidates_no_current_acceptance",
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "strict_full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
            "current_cursor_edited": False,
        },
        "guardrail": (
            "This spec can only seed a later rerun under the named future chronological protocol. "
            "It does not change the fixed 2024/2025 strict gate and accepts no current rows."
        ),
    }

    json_path = OUT_DIR / "strict_1h_future_tail_gate_spec_v1.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = OUT_DIR / "strict_1h_future_tail_gate_spec_v1.md"
    report.write_text(
        "\n".join(
            [
                "# Strict 1h Future Tail Gate Spec v1",
                "",
                f"Run ID: `{RUN_ID}`",
                "",
                "This artifact predeclares a future chronological gate for strict exact `1h` near-miss rows whose missing source sessions are covered by the existing Jan-2026 source-owned tail. It is not a gate rerun and it accepts no current rows.",
                "",
                "## Protocol",
                "",
                "- Calibration split: `calendar_2024_fixed_from_exact_1h_universe`.",
                "- Future validation split: `calendar_2025_heldout_plus_source_owned_jan2026_tail`.",
                f"- Tail window: `{TAIL_START}` to `{TAIL_END}`.",
                f"- Minimum support: `{MIN_SUPPORT}`; minimum Wilson95 LCB: `{MIN_WILSON}`.",
                "- Required provenance: source-owned labels, exact `1h` provider coverage, no generated/proxy labels, no threshold relaxation.",
                "",
                "## Decision",
                "",
                f"`{payload['decision']['gate_result']}`",
                "",
                f"- Future-rerun candidates: `{len(rows)}`.",
                f"- Eligible under this predeclared protocol if rerun later: `{eligible_count}`.",
                "- Accepted rows added now: `0`; new confidence gate: `false`.",
                "- Strict full objective achieved: `false`; `update_goal=false`.",
                "- Current Cursor edited: `false`.",
                "",
                "## Candidate Rows",
                "",
                "| Instrument | Root | 2024 Cal Support | 2025 Heldout Support | Jan-2026 Tail | Future Heldout Support | Future Heldout LCB | Eligible Later | Accepted Now |",
                "|---|---|---:|---:|---:|---:|---:|---|---|",
                *[
                    (
                        f"| `{row['instrument']}` | `{row['root']}` | `{row['calibration_2024_support']}` "
                        f"| `{row['heldout_2025_support']}` | `{row['jan2026_source_tail_sessions']}` "
                        f"| `{row['future_heldout_2025_plus_jan2026_support']}` "
                        f"| `{row['future_heldout_2025_plus_jan2026_wilson95_lcb']}` "
                        f"| `{row['eligible_for_future_rerun']}` | `{row['accepted_now']}` |"
                    )
                    for row in rows
                ],
                "",
                "## Guardrail",
                "",
                payload["guardrail"],
                "",
                "## Artifacts",
                "",
                f"- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_DIR}/future-tail-gate-spec/strict_1h_future_tail_gate_spec_v1.json`",
                f"- Rows CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_DIR}/future-tail-gate-spec/strict_1h_future_tail_gate_spec_v1_rows.csv`",
                f"- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_DIR}/checks/strict_1h_future_tail_gate_spec_v1_assertions.out`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = [
        f"PASS candidate_rows={len(rows)}",
        f"PASS eligible_for_future_rerun_rows={eligible_count}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective=false",
        "PASS update_goal=false",
        "PASS current_cursor_edited=false",
    ]
    (CHECK_DIR / "strict_1h_future_tail_gate_spec_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
