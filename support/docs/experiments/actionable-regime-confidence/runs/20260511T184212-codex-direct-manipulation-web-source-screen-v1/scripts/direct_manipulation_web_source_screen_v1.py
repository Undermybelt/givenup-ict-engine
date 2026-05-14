#!/usr/bin/env python3
"""Build a web/GitHub/arXiv direct-manipulation source screen artifact."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T184212+0800-codex-direct-manipulation-web-source-screen-v1"
RUN_ROOT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T184212-codex-direct-manipulation-web-source-screen-v1"
)
OUT_DIR = RUN_ROOT / "direct-web-source-screen"
CHECK_DIR = RUN_ROOT / "checks"
OUT_JSON = OUT_DIR / "direct_manipulation_web_source_screen_v1.json"
OUT_MD = OUT_DIR / "direct_manipulation_web_source_screen_v1.md"
OUT_CSV = OUT_DIR / "direct_manipulation_web_source_screen_v1_candidates.csv"
OUT_ASSERT = CHECK_DIR / "direct_manipulation_web_source_screen_v1_assertions.out"


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def candidates() -> list[dict[str, Any]]:
    return [
        {
            "source_family": "github",
            "ref": "kpetridis24/lobsim",
            "url": "https://github.com/kpetridis24/lobsim",
            "candidate_type": "limit_order_book_simulator",
            "positive_labels": False,
            "matched_negative_controls": False,
            "provenance_rows": False,
            "synthetic_or_simulated": True,
            "disposition": "blocked_simulator_no_source_rows",
            "reason": "Repository provides simulated LOB machinery/sample data, not real direct manipulation positives with matched normal controls.",
        },
        {
            "source_family": "paper",
            "ref": "Spoofing the Limit Order Book: A Strategic Agent-Based Analysis",
            "url": "https://www.mdpi.com/2073-4336/12/2/46",
            "candidate_type": "agent_based_spoofing_model",
            "positive_labels": False,
            "matched_negative_controls": False,
            "provenance_rows": False,
            "synthetic_or_simulated": True,
            "disposition": "blocked_paper_simulation_no_row_export",
            "reason": "Useful model/background source; it describes an agent-based spoofing simulation, not a real row dataset with positives and matched normal controls.",
        },
        {
            "source_family": "paper",
            "ref": "arXiv 2504.15908 spoofability",
            "url": "https://ideas.repec.org/p/arx/papers/2504.15908.html",
            "candidate_type": "level3_spoofability_method",
            "positive_labels": False,
            "matched_negative_controls": False,
            "provenance_rows": False,
            "synthetic_or_simulated": False,
            "disposition": "blocked_method_only_no_public_matched_rows",
            "reason": "Uses Level-3 data and computes spoofability probabilities, but the public record is a method/paper, not an export with accepted positives plus matched normal controls.",
        },
        {
            "source_family": "kaggle",
            "ref": "marvingozo/polymarket-tick-level-orderbook-dataset",
            "url": "https://www.kaggle.com/datasets/marvingozo/polymarket-tick-level-orderbook-dataset",
            "candidate_type": "raw_tick_orderbook",
            "positive_labels": False,
            "matched_negative_controls": False,
            "provenance_rows": True,
            "synthetic_or_simulated": False,
            "disposition": "blocked_raw_lob_no_direct_labels",
            "reason": "Tick/orderbook rows may support future feature work, but no source-owned direct Manipulation labels or matched control groups were exposed in the public dataset page.",
        },
        {
            "source_family": "huggingface",
            "ref": "solsticestudioai/dark-pool-pack",
            "url": "https://huggingface.co/datasets/solsticestudioai/dark-pool-pack",
            "candidate_type": "synthetic_financial_fraud_sequences",
            "positive_labels": True,
            "matched_negative_controls": True,
            "provenance_rows": True,
            "synthetic_or_simulated": True,
            "disposition": "blocked_synthetic_not_source_owned_market_rows",
            "reason": "Dataset has fraudulent/benign spoofing-like sequences, but the card states it is 100% synthetic and contains no real transactions or order books.",
        },
    ]


def write_csv(rows: list[dict[str, Any]]) -> None:
    fields = [
        "source_family",
        "ref",
        "url",
        "candidate_type",
        "positive_labels",
        "matched_negative_controls",
        "provenance_rows",
        "synthetic_or_simulated",
        "disposition",
        "reason",
    ]
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# Direct Manipulation Web Source Screen v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This is a supplemental public web/GitHub/arXiv screen for direct Manipulation row sources. It does not download raw rows and does not alter the Current Cursor.",
        "",
        "## Decision",
        "",
        f"`{payload['decision']['gate_result']}`",
        "",
        f"- Candidates screened: `{payload['candidate_count']}`.",
        f"- Ready source candidates: `{payload['ready_source_candidate_count']}`.",
        "- Accepted rows added: `0`.",
        "- New confidence gate: `false`.",
        "- Full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Candidate Disposition",
        "",
    ]
    for row in payload["candidates"]:
        lines.extend(
            [
                f"- `{row['ref']}`: `{row['disposition']}`.",
                f"  Source: {row['url']}",
                f"  Reason: {row['reason']}",
            ]
        )
    lines.extend(
        [
            "",
            "## Why It Still Blocks",
            "",
            "Board A strict direct `Manipulation` still needs real row-level positives, matched normal controls, and provenance. Simulators, papers, raw LOB feeds without direct labels, model-computed probabilities, and synthetic fraud packs can be useful for design or tests, but they cannot satisfy the strict confidence gate.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{repo_rel(OUT_JSON)}`",
            f"- Candidate CSV: `{repo_rel(OUT_CSV)}`",
            f"- Assertions: `{repo_rel(OUT_ASSERT)}`",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    rows = candidates()
    ready = [
        row for row in rows
        if row["positive_labels"]
        and row["matched_negative_controls"]
        and row["provenance_rows"]
        and not row["synthetic_or_simulated"]
    ]
    payload = {
        "run_id": RUN_ID,
        "artifact_type": "direct_manipulation_web_source_screen_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "current_cursor_edited": False,
        "candidate_count": len(rows),
        "ready_source_candidate_count": len(ready),
        "candidates": rows,
        "decision": {
            "gate_result": "direct_manipulation_web_source_screen_v1=no_ready_real_matched_negative_source",
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next": "Acquire real direct Manipulation positive rows plus matched normal controls, then run the external intake verifier before any confidence claim.",
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(rows)
    write_markdown(payload)
    assertions = [
        "PASS candidate_count=5" if len(rows) == 5 else "FAIL candidate_count",
        "PASS ready_source_candidate_count=0" if len(ready) == 0 else "FAIL ready_source_candidate_count",
        "PASS accepted_rows_added=0" if payload["decision"]["accepted_rows_added"] == 0 else "FAIL accepted_rows_added",
        "PASS full_objective=false" if not payload["decision"]["full_objective_achieved"] else "FAIL full_objective",
        "PASS current_cursor_edited=false" if not payload["current_cursor_edited"] else "FAIL current_cursor_edited",
    ]
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    if any(line.startswith("FAIL") for line in assertions):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
