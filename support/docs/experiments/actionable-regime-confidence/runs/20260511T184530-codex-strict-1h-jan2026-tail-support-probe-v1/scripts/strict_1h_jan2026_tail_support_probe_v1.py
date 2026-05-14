#!/usr/bin/env python3
"""Probe existing Jan-2026 source-label tail support for strict 1h near misses.

This does not retroactively change the fixed 2024/2025 strict gate. It only
checks whether already-local source-owned Jan-2026 labels cover the extension
targets identified by strict_1h_near_miss_extension_requirements_v1.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T184530+0800-codex-strict-1h-jan2026-tail-support-probe-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T184530-codex-strict-1h-jan2026-tail-support-probe-v1"
)
OUT_DIR = RUN_ROOT / "jan2026-tail-support"
CHECK_DIR = RUN_ROOT / "checks"

SOURCE_PANEL = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
TICKERS_CSV = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T141910-codex-exact-1h-source-universe-expansion-v1/"
    "exact-1h-universe/exact_1h_source_universe_expansion_v1_tickers.csv"
)
CANDIDATES_CSV = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T184151-codex-strict-1h-near-miss-extension-requirements-v1/"
    "strict-1h-extension-requirements/strict_1h_near_miss_extension_candidates_v1.csv"
)

TAIL_START = "2026-01-01"
TAIL_END = "2026-01-30"
MIN_SUPPORT = 73


def wilson_lcb(pos: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    p = pos / n
    denom = 1 + z * z / n
    center = p + z * z / (2 * n)
    radius = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return (center - radius) / denom


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


def load_tail_counts() -> tuple[dict[tuple[str, str], int], dict[str, Any]]:
    counts: Counter[tuple[str, str]] = Counter()
    tickers: set[str] = set()
    roots: set[str] = set()
    row_count = 0
    date_min = None
    date_max = None
    with SOURCE_PANEL.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            date = row["date"]
            if date < TAIL_START or date > TAIL_END:
                continue
            ticker = row["ticker"]
            root = row["regime_label"]
            if root not in {"Bull", "Bear", "Sideways", "Crisis"}:
                continue
            counts[(ticker, root)] += 1
            tickers.add(ticker)
            roots.add(root)
            row_count += 1
            date_min = date if date_min is None or date < date_min else date_min
            date_max = date if date_max is None or date > date_max else date_max
    return dict(counts), {
        "row_count": row_count,
        "ticker_count": len(tickers),
        "roots": sorted(roots),
        "date_min": date_min,
        "date_max": date_max,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    candidates = read_csv(CANDIDATES_CSV)
    ticker_rows = {row["ticker"]: row for row in read_csv(TICKERS_CSV)}
    tail_counts, tail_summary = load_tail_counts()

    rows: list[dict[str, Any]] = []
    enough_for_missing_extra = 0
    standalone_tail_passes = 0
    provider_ready = 0
    for candidate in candidates:
        ticker = candidate["instrument"]
        root = candidate["root"]
        missing_total = int(candidate["total_extra_sessions_to_make_fixed_splits_pass"])
        tail_support = int(tail_counts.get((ticker, root), 0))
        tail_lcb = round(wilson_lcb(tail_support, tail_support), 10)
        ticker_state = ticker_rows.get(ticker, {})
        ready = ticker_state.get("download_state") == "ready" and ticker_state.get("date_max", "") >= TAIL_END
        provider_ready += 1 if ready else 0
        covers_missing = tail_support >= missing_total
        standalone_pass = tail_support >= MIN_SUPPORT and tail_lcb >= 0.95
        enough_for_missing_extra += 1 if covers_missing else 0
        standalone_tail_passes += 1 if standalone_pass else 0
        rows.append({
            "instrument": ticker,
            "root": root,
            "missing_extra_sessions_from_184151": missing_total,
            "jan2026_source_tail_sessions": tail_support,
            "jan2026_tail_wilson95_lcb": f"{tail_lcb:.10f}",
            "provider_1h_covers_tail": str(ready).lower(),
            "tail_covers_missing_extra": str(covers_missing).lower(),
            "standalone_tail_gate_passes": str(standalone_pass).lower(),
            "allowed_use": "future_chronological_gate_preflight_only",
        })

    rows.sort(
        key=lambda item: (
            item["tail_covers_missing_extra"] != "true",
            -int(item["jan2026_source_tail_sessions"]),
            int(item["missing_extra_sessions_from_184151"]),
            item["root"],
            item["instrument"],
        )
    )

    payload = {
        "run_id": RUN_ID,
        "artifact_type": "strict_1h_jan2026_tail_support_probe_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_panel": str(SOURCE_PANEL),
        "candidate_source": str(CANDIDATES_CSV.relative_to(REPO)),
        "tail_window": {"start": TAIL_START, "end": TAIL_END},
        "tail_summary": tail_summary,
        "counts": {
            "candidate_rows": len(candidates),
            "provider_ready_for_tail": provider_ready,
            "tail_covers_missing_extra_rows": enough_for_missing_extra,
            "standalone_tail_gate_passes": standalone_tail_passes,
            "accepted_rows_added": 0,
        },
        "rows": rows,
        "decision": {
            "gate_result": "strict_1h_jan2026_tail_support_probe_v1=tail_support_found_future_gate_only_no_current_acceptance",
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "guardrail": (
            "Jan-2026 source labels are source-owned tail evidence, but they are not a retroactive repair "
            "for the fixed 2024/2025 strict gate. They can only seed a predeclared future chronological gate."
        ),
        "next_action": (
            "For strict 1h, use the rows with tail_covers_missing_extra=true as the first future-gate targets "
            "if a predeclared 2026-tail validation protocol is opened; otherwise keep strict support at 41/156."
        ),
    }

    json_path = OUT_DIR / "strict_1h_jan2026_tail_support_probe_v1.json"
    md_path = OUT_DIR / "strict_1h_jan2026_tail_support_probe_v1.md"
    rows_path = OUT_DIR / "strict_1h_jan2026_tail_support_probe_v1_rows.csv"
    assertions_path = CHECK_DIR / "strict_1h_jan2026_tail_support_probe_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    fields = [
        "instrument",
        "root",
        "missing_extra_sessions_from_184151",
        "jan2026_source_tail_sessions",
        "jan2026_tail_wilson95_lcb",
        "provider_1h_covers_tail",
        "tail_covers_missing_extra",
        "standalone_tail_gate_passes",
        "allowed_use",
    ]
    write_csv(rows_path, rows, fields)

    lines = [
        "# Strict 1h Jan-2026 Tail Support Probe v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        "- Current strict exact `1h` accepted rows remain `41/156`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        f"- Candidate rows checked: `{len(candidates)}`.",
        f"- Provider-ready for Jan-2026 tail: `{provider_ready}/{len(candidates)}`.",
        f"- Existing Jan-2026 source tail covers the missing-extra count for `{enough_for_missing_extra}` candidates.",
        f"- Standalone Jan-2026 tail gates passing `support>=73` and Wilson95>=0.95: `{standalone_tail_passes}`.",
        "- Gate result: `strict_1h_jan2026_tail_support_probe_v1=tail_support_found_future_gate_only_no_current_acceptance`.",
        "- Full objective achieved: false. `update_goal=false`.",
        "",
        "## Tail-Covered Candidates",
        "",
        "| Instrument | Root | Missing extra | Jan-2026 tail sessions | Tail LCB |",
        "|---|---|---:|---:|---:|",
    ]
    for row in [r for r in rows if r["tail_covers_missing_extra"] == "true"]:
        lines.append(
            f"| {row['instrument']} | {row['root']} | {row['missing_extra_sessions_from_184151']} | "
            f"{row['jan2026_source_tail_sessions']} | {row['jan2026_tail_wilson95_lcb']} |"
        )
    lines.extend(["", "## Guardrail", "", payload["guardrail"], "", "## Next", "", payload["next_action"]])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"run_id={RUN_ID}",
        f"candidate_rows={len(candidates)}",
        f"provider_ready_for_tail={provider_ready}",
        f"tail_covers_missing_extra_rows={enough_for_missing_extra}",
        f"standalone_tail_gate_passes={standalone_tail_passes}",
        "accepted_rows_added=0",
        "new_confidence_gate=false",
        "full_objective_achieved=false",
        "update_goal=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
    ]
    assertion_status = "PASS" if len(candidates) == 13 and provider_ready == 13 and standalone_tail_passes == 0 else "FAIL"
    assertion_lines.append(f"assertion_status={assertion_status}")
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    return 0 if assertion_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
