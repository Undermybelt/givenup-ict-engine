#!/usr/bin/env python3
"""Consolidate R6 proposed direct Manipulation rows after the Thakkar cursor."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T235253-codex-r6-post-thakkar-candidate-consolidation-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-post-thakkar-candidate-consolidation"
CMD = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

LIVE_INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
V54_AUDIT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T223100-codex-current-goal-completion-audit-v54-after-sidecar-calibration"
    / "completion-audit/current_goal_completion_audit_v54_after_sidecar_calibration.json"
)
SIDECAR_CONTROLS = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1"
    / "r6-broad-normal-order-lifecycle-screen/broad_normal_market_order_lifecycle_controls_v1.csv"
)

SOURCE_ROOTS = [
    {
        "source": "sarao",
        "run_id": "20260511T225505-codex-r6-sarao-positive-row-candidate-screen-v1",
        "positive_csv": "r6-sarao-positive-row-candidate-screen/r6_sarao_positive_row_candidates_v1.csv",
    },
    {
        "source": "nowak_smith",
        "run_id": "20260511T233454-codex-r6-nowak-smith-positive-row-candidate-screen-v1",
        "positive_csv": "r6-nowak-smith-positive-row-candidate-screen/r6_nowak_smith_positive_row_candidates_v1.csv",
    },
    {
        "source": "oystacher_khara_salim",
        "run_id": "20260511T234735-codex-r6-oystacher-khara-salim-positive-row-candidate-screen-v1",
        "positive_csv": "r6-oystacher-khara-salim-positive-row-candidate-screen/r6_oystacher_khara_salim_positive_row_candidates_v1.csv",
    },
    {
        "source": "jpmorgan_latest",
        "run_id": "20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1",
        "positive_csv": "r6-jpmorgan-positive-row-candidate-screen/r6_jpmorgan_positive_row_candidates_v1.csv",
        "control_csv": "r6-jpmorgan-positive-row-candidate-screen/r6_jpmorgan_matched_control_candidates_v1.csv",
    },
    {
        "source": "thakkar_backofbook",
        "run_id": "20260511T234834-codex-r6-thakkar-backofbook-positive-row-candidate-screen-v1",
        "positive_csv": "r6-thakkar-backofbook-positive-row-candidate-screen/r6_thakkar_backofbook_positive_row_candidates_v1.csv",
        "control_csv": "r6-thakkar-backofbook-positive-row-candidate-screen/r6_thakkar_backofbook_matched_control_candidates_v1.csv",
    },
    {
        "source": "moncada_large_lot",
        "run_id": "20260511T235000-codex-r6-moncada-large-lot-positive-row-candidate-screen-v1",
        "positive_csv": "r6-moncada-large-lot-positive-row-candidate-screen/r6_moncada_large_lot_positive_row_candidates_v1.csv",
    },
    {
        "source": "trunz_empty_screen",
        "run_id": "20260511T235000-codex-r6-trunz-positive-row-candidate-screen-v1",
        "positive_csv": "r6-trunz-positive-row-candidate-screen/r6_trunz_positive_row_candidates_v1.csv",
    },
]

Z_95 = 1.96
MIN_WILSON = 0.95


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def run_direct_verifier() -> dict[str, Any]:
    CMD.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(LIVE_INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=45,
        check=False,
    )
    stdout = CMD / "direct_manipulation_row_intake_verifier.stdout.txt"
    stderr = CMD / "direct_manipulation_row_intake_verifier.stderr.txt"
    stdout.write_text(proc.stdout, encoding="utf-8")
    stderr.write_text(proc.stderr, encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"parse_error": True, "raw_stdout": proc.stdout[:500]}
    return {
        "returncode": proc.returncode,
        "stdout_path": str(stdout.relative_to(REPO)),
        "stderr_path": str(stderr.relative_to(REPO)),
        "parsed": parsed,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    board_hash = sha256(BOARD)
    v54 = read_json(V54_AUDIT)
    baseline_positive = int(v54["r6"]["positive_rows"])
    baseline_negative = int(v54["r6"]["matched_negative_rows"])
    sidecar_controls = read_csv(SIDECAR_CONTROLS)
    direct_verifier = run_direct_verifier()

    source_summaries: list[dict[str, Any]] = []
    unique_rows: dict[str, dict[str, Any]] = {}
    duplicate_rows: list[dict[str, Any]] = []
    control_rows: list[dict[str, Any]] = []

    for source in SOURCE_ROOTS:
        run_root = REPO / "docs/experiments/actionable-regime-confidence/runs" / source["run_id"]
        positive_path = run_root / source["positive_csv"]
        positives = read_csv(positive_path)
        controls = read_csv(run_root / source["control_csv"]) if source.get("control_csv") else []
        for row in positives:
            row_id = row.get("source_row_id", "")
            item = {
                "candidate_source": source["source"],
                "run_id": source["run_id"],
                "source_row_id": row_id,
                "trade_date": row.get("trade_date", ""),
                "symbol": row.get("symbol", ""),
                "venue_or_market_center": row.get("venue_or_market_center", ""),
                "matched_negative_group_id": row.get("matched_negative_group_id", ""),
                "candidate_row_status": row.get("candidate_row_status", ""),
            }
            if row_id and row_id not in unique_rows:
                unique_rows[row_id] = item
            else:
                duplicate_rows.append(item)
        for row in controls:
            control_rows.append(
                {
                    "candidate_source": source["source"],
                    "run_id": source["run_id"],
                    "source_row_id": row.get("source_row_id", ""),
                    "matched_negative_group_id": row.get("matched_negative_group_id", ""),
                    "label": row.get("label", ""),
                }
            )
        source_summaries.append(
            {
                "source": source["source"],
                "run_id": source["run_id"],
                "positive_rows": len(positives),
                "control_rows": len(controls),
                "positive_csv_exists": positive_path.exists(),
            }
        )

    unique_candidates = list(unique_rows.values())
    proposed_unique_count = len(unique_candidates)
    what_if_positive = baseline_positive + proposed_unique_count
    baseline_lcb = wilson_lcb(baseline_positive, baseline_positive)
    what_if_lcb = wilson_lcb(what_if_positive, what_if_positive)
    sidecar_lcb = wilson_lcb(len(sidecar_controls), len(sidecar_controls))
    what_if_min_lcb = min(what_if_lcb, sidecar_lcb)

    write_csv(
        OUT / "r6_post_thakkar_unique_candidate_rows_v1.csv",
        unique_candidates,
        [
            "candidate_source",
            "run_id",
            "source_row_id",
            "trade_date",
            "symbol",
            "venue_or_market_center",
            "matched_negative_group_id",
            "candidate_row_status",
        ],
    )
    write_csv(
        OUT / "r6_post_thakkar_duplicate_candidate_rows_v1.csv",
        duplicate_rows,
        [
            "candidate_source",
            "run_id",
            "source_row_id",
            "trade_date",
            "symbol",
            "venue_or_market_center",
            "matched_negative_group_id",
            "candidate_row_status",
        ],
    )
    write_csv(
        OUT / "r6_post_thakkar_control_candidate_rows_v1.csv",
        control_rows,
        ["candidate_source", "run_id", "source_row_id", "matched_negative_group_id", "label"],
    )
    write_csv(
        OUT / "r6_post_thakkar_source_summary_v1.csv",
        source_summaries,
        ["source", "run_id", "positive_rows", "control_rows", "positive_csv_exists"],
    )

    verifier_parsed = direct_verifier.get("parsed") or {}
    live_missing = (
        direct_verifier["returncode"] != 0
        and verifier_parsed.get("status") == "blocked"
        and verifier_parsed.get("reason") == "missing_required_files"
    )
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_hash,
        "canonical_live_intake_root": str(LIVE_INTAKE),
        "canonical_live_intake_exists": LIVE_INTAKE.exists(),
        "direct_verifier": direct_verifier,
        "direct_verifier_blocked_missing_required_files": live_missing,
        "v54_baseline_positive_rows": baseline_positive,
        "v54_baseline_matched_negative_rows": baseline_negative,
        "sidecar_broad_normal_control_rows": len(sidecar_controls),
        "sidecar_broad_normal_wilson95_lcb": round(sidecar_lcb, 12),
        "source_summaries": source_summaries,
        "unique_proposed_positive_rows": proposed_unique_count,
        "duplicate_candidate_rows": len(duplicate_rows),
        "proposed_matched_control_rows": len(control_rows),
        "what_if_positive_rows_after_unique_sidecars": what_if_positive,
        "v54_baseline_wilson95_lcb": round(baseline_lcb, 12),
        "what_if_positive_wilson95_lcb_after_unique_sidecars": round(what_if_lcb, 12),
        "what_if_min_wilson95_lcb_after_unique_sidecars": round(what_if_min_lcb, 12),
        "pooled_what_if_wilson95_pass": what_if_min_lcb >= MIN_WILSON,
        "matched_controls_materialized_for_all_candidates": len(control_rows) >= proposed_unique_count,
        "shared_intake_mutated": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "gate_result": "r6_post_thakkar_candidate_consolidation_v1=pooled_whatif_passes_but_live_intake_missing_and_split_gates_not_rerun",
        "next_action": (
            "Restore or rematerialize the direct R6 intake from durable row artifacts under a shared lock, "
            "materialize matched controls for every accepted candidate, then rerun direct plus sidecar calibration "
            "and chronological/symbol/venue split gates before any acceptance claim."
        ),
    }

    json_path = OUT / "r6_post_thakkar_candidate_consolidation_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    report = [
        "# R6 Post-Thakkar Candidate Consolidation v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Generated at UTC: `{result['generated_at_utc']}`",
        "",
        "## Result",
        "",
        f"- Canonical live intake exists now: `{result['canonical_live_intake_exists']}`.",
        f"- Direct verifier blocked on missing files: `{live_missing}`.",
        f"- V54 durable baseline positives/controls: `{baseline_positive}/{baseline_negative}`.",
        f"- Unique proposed positives after de-duplication: `{proposed_unique_count}`.",
        f"- Duplicate proposed candidate rows ignored: `{len(duplicate_rows)}`.",
        f"- Proposed matched-control rows currently materialized in sidecar packets: `{len(control_rows)}`.",
        f"- What-if positives after all unique sidecars: `{what_if_positive}`.",
        f"- What-if min Wilson95 LCB after all unique sidecars: `{result['what_if_min_wilson95_lcb_after_unique_sidecars']}`.",
        f"- Pooled what-if Wilson95 pass: `{result['pooled_what_if_wilson95_pass']}`.",
        f"- Gate result: `{result['gate_result']}`.",
        f"- Strict full objective achieved: `{result['strict_full_objective_achieved']}`; `update_goal={result['update_goal']}`.",
        "",
        "## Fail-Closed Decision",
        "",
        "- This run did not mutate the shared intake and did not accept any sidecar rows.",
        "- The pooled what-if is above `0.95`, but the live intake is missing, candidate matched controls are incomplete, and chronological/symbol/venue split gates have not rerun.",
        "- R5 source-panel recency and R3 native-subhour blockers remain outside this direct R6 sidecar consolidation.",
    ]
    (OUT / "r6_post_thakkar_candidate_consolidation_v1.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        f"canonical_live_intake_exists={result['canonical_live_intake_exists']}",
        f"direct_verifier_blocked_missing_required_files={live_missing}",
        f"unique_proposed_positive_rows={proposed_unique_count}",
        f"duplicate_candidate_rows={len(duplicate_rows)}",
        f"proposed_matched_control_rows={len(control_rows)}",
        f"what_if_min_wilson95_lcb_after_unique_sidecars={result['what_if_min_wilson95_lcb_after_unique_sidecars']}",
        f"pooled_what_if_wilson95_pass={result['pooled_what_if_wilson95_pass']}",
        f"shared_intake_mutated={result['shared_intake_mutated']}",
        f"new_confidence_gate={result['new_confidence_gate']}",
        f"strict_full_objective_achieved={result['strict_full_objective_achieved']}",
        f"update_goal={result['update_goal']}",
    ]
    (CHECKS / "r6_post_thakkar_candidate_consolidation_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "run_id": RUN_ID, "gate_result": result["gate_result"], "update_goal": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
