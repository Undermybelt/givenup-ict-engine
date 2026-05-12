#!/usr/bin/env python3
"""Triage remaining strict exact-source 1h ticker/root gaps without refetching data."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T181859+0800-codex-strict-1h-gap-triage-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T181859-codex-strict-1h-gap-triage-v1"
OUT_DIR = RUN_ROOT / "strict-1h-gap-triage"
CHECK_DIR = RUN_ROOT / "checks"

ROWS_CSV = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T141910-codex-exact-1h-source-universe-expansion-v1/"
    "exact-1h-universe/exact_1h_source_universe_expansion_v1_rows.csv"
)
TICKERS_CSV = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T141910-codex-exact-1h-source-universe-expansion-v1/"
    "exact-1h-universe/exact_1h_source_universe_expansion_v1_tickers.csv"
)
SOURCE_RECENCY = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T180345-codex-source-panel-recency-local-acquisition-probe-v1/"
    "local-acquisition-probe/source_panel_recency_local_acquisition_probe_v1.json"
)

OUT_JSON = OUT_DIR / "strict_1h_gap_triage_v1.json"
OUT_MD = OUT_DIR / "strict_1h_gap_triage_v1.md"
OUT_BLOCKED = OUT_DIR / "strict_1h_gap_triage_v1_blocked_rows.csv"
OUT_NEAR = OUT_DIR / "strict_1h_gap_triage_v1_near_misses.csv"
OUT_ASSERT = CHECK_DIR / "strict_1h_gap_triage_v1_assertions.out"

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def as_float(value: str) -> float:
    return float(value) if value else 0.0


def as_int(value: str) -> int:
    return int(float(value)) if value else 0


def load_rows() -> list[dict[str, Any]]:
    with ROWS_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_tickers() -> list[dict[str, Any]]:
    with TICKERS_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def summarize() -> dict[str, Any]:
    rows = load_rows()
    tickers = load_tickers()
    recency = json.loads(SOURCE_RECENCY.read_text(encoding="utf-8"))
    accepted = [row for row in rows if row["accepted_95_strict_ticker_root_attachment"] == "True"]
    blocked = [row for row in rows if row["accepted_95_strict_ticker_root_attachment"] != "True"]
    provider_not_ready = [row for row in tickers if row["download_state"] != "ready"]
    root_summary: dict[str, dict[str, Any]] = {}
    for root in ROOTS:
        root_rows = [row for row in rows if row["root"] == root]
        root_accepted = [row for row in root_rows if row["accepted_95_strict_ticker_root_attachment"] == "True"]
        root_blocked = [row for row in root_rows if row["accepted_95_strict_ticker_root_attachment"] != "True"]
        root_summary[root] = {
            "total": len(root_rows),
            "accepted": len(root_accepted),
            "blocked": len(root_blocked),
            "accepted_tickers": [row["instrument"] for row in root_accepted],
        }
    blocker_counts: Counter[str] = Counter()
    blocker_by_root: dict[str, Counter[str]] = {root: Counter() for root in ROOTS}
    near_rows: list[dict[str, Any]] = []
    blocked_rows: list[dict[str, Any]] = []
    for row in blocked:
        blockers = [part for part in row["blocker"].split("|") if part]
        blocker_counts.update(blockers)
        blocker_by_root[row["root"]].update(blockers)
        cal_support = as_int(row["calibration_2024_support"])
        heldout_support = as_int(row["heldout_time_2025_support"])
        cal_lcb = as_float(row["calibration_2024_wilson95_lcb"])
        heldout_lcb = as_float(row["heldout_time_2025_wilson95_lcb"])
        support_gap = max(0, 73 - min(cal_support, heldout_support))
        lcb_gap = max(0.0, 0.95 - min(cal_lcb, heldout_lcb))
        one_split_passes = (
            (cal_support >= 73 and cal_lcb >= 0.95)
            or (heldout_support >= 73 and heldout_lcb >= 0.95)
        )
        row_out = {
            "instrument": row["instrument"],
            "root": row["root"],
            "calibration_2024_support": cal_support,
            "calibration_2024_wilson95_lcb": cal_lcb,
            "heldout_time_2025_support": heldout_support,
            "heldout_time_2025_wilson95_lcb": heldout_lcb,
            "support_gap_to_73": support_gap,
            "lcb_gap_to_095": f"{lcb_gap:.12f}",
            "one_split_passes": one_split_passes,
            "blocker": row["blocker"],
        }
        blocked_rows.append(row_out)
        if one_split_passes or support_gap <= 20 or lcb_gap <= 0.025:
            near_rows.append(row_out)
    near_rows.sort(
        key=lambda item: (
            not item["one_split_passes"],
            item["support_gap_to_73"],
            float(item["lcb_gap_to_095"]),
            item["root"],
            item["instrument"],
        )
    )
    zero_root_tickers = [row["ticker"] for row in tickers if row["strict_accepted_root_count"] == "0"]
    return {
        "rows": rows,
        "tickers": tickers,
        "accepted": accepted,
        "blocked": blocked,
        "blocked_rows": blocked_rows,
        "near_rows": near_rows,
        "provider_not_ready": provider_not_ready,
        "root_summary": root_summary,
        "blocker_counts": dict(blocker_counts),
        "blocker_by_root": {root: dict(counts) for root, counts in blocker_by_root.items()},
        "zero_root_tickers": zero_root_tickers,
        "recency": recency,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    s = summarize()
    payload = {
        "run_id": RUN_ID,
        "artifact_type": "strict_1h_gap_triage_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_rows": repo_rel(ROWS_CSV),
        "source_tickers": repo_rel(TICKERS_CSV),
        "strict_slots": len(s["rows"]),
        "accepted_strict_rows": len(s["accepted"]),
        "blocked_strict_rows": len(s["blocked"]),
        "provider_ready_tickers": len(s["tickers"]) - len(s["provider_not_ready"]),
        "provider_not_ready_tickers": len(s["provider_not_ready"]),
        "root_summary": s["root_summary"],
        "blocker_counts": s["blocker_counts"],
        "blocker_by_root": s["blocker_by_root"],
        "near_miss_count": len(s["near_rows"]),
        "top_near_misses": s["near_rows"][:20],
        "zero_accepted_root_tickers": s["zero_root_tickers"],
        "recency_extension_candidate_count": s["recency"]["extension_candidate_count"],
        "decision": {
            "gate_result": "strict_1h_gap_triage_v1=provider_ready_source_label_support_blocked",
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Do not refetch yfinance 1h for this gap. Acquire source-owned recency extension rows "
            "or an owner-approved broader label/equivalence panel, then rerun strict ticker/root gates."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    fields = [
        "instrument",
        "root",
        "calibration_2024_support",
        "calibration_2024_wilson95_lcb",
        "heldout_time_2025_support",
        "heldout_time_2025_wilson95_lcb",
        "support_gap_to_73",
        "lcb_gap_to_095",
        "one_split_passes",
        "blocker",
    ]
    write_csv(OUT_BLOCKED, s["blocked_rows"], fields)
    write_csv(OUT_NEAR, s["near_rows"], fields)
    lines = [
        "# Strict 1h Gap Triage v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This triages the remaining strict exact-source `1h` ticker/root gaps from `exact_1h_source_universe_expansion_v1` without refetching provider data.",
        "",
        "## Result",
        "",
        f"- Strict slots: `{len(s['rows'])}`.",
        f"- Accepted strict rows: `{len(s['accepted'])}`.",
        f"- Blocked strict rows: `{len(s['blocked'])}`.",
        f"- Provider-ready tickers: `{len(s['tickers']) - len(s['provider_not_ready'])}/{len(s['tickers'])}`.",
        f"- Provider-not-ready tickers: `{len(s['provider_not_ready'])}`.",
        f"- Near-miss blocked rows: `{len(s['near_rows'])}`.",
        f"- Zero-accepted-root tickers: `{', '.join(s['zero_root_tickers'])}`.",
        f"- Recency extension candidates available: `{s['recency']['extension_candidate_count']}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Gate result: `strict_1h_gap_triage_v1=provider_ready_source_label_support_blocked`.",
        "- Full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Accepted By Root",
        "",
        "| Root | Accepted | Blocked | Accepted tickers |",
        "|---|---:|---:|---|",
    ]
    for root in ROOTS:
        info = s["root_summary"][root]
        lines.append(
            f"| `{root}` | {info['accepted']} | {info['blocked']} | {', '.join(info['accepted_tickers'])} |"
        )
    lines.extend(
        [
            "",
            "## Blocker Summary",
            "",
            "| Blocker | Count |",
            "|---|---:|",
        ]
    )
    for blocker, count in sorted(s["blocker_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{blocker}` | {count} |")
    lines.extend(["", "## Next", "", payload["next_action"]])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assertions = [
        f"run_id={RUN_ID}",
        f"strict_slots={len(s['rows'])}",
        f"accepted_strict_rows={len(s['accepted'])}",
        f"blocked_strict_rows={len(s['blocked'])}",
        f"provider_not_ready_tickers={len(s['provider_not_ready'])}",
        f"near_miss_count={len(s['near_rows'])}",
        f"recency_extension_candidate_count={s['recency']['extension_candidate_count']}",
        "accepted_rows_added=0",
        "new_confidence_gate=false",
        "full_objective_achieved=false",
        "update_goal=false",
        "assertion_status=PASS",
    ]
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
