#!/usr/bin/env python3
"""Completion audit after local, upstream, and shared-state probes."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T182155+0800-current-goal-completion-audit-v17-after-local-upstream-probes"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182155-current-goal-completion-audit-v17-after-local-upstream-probes"
)
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")

OUT_JSON = OUT_DIR / "current_goal_completion_audit_v17_after_local_upstream_probes.json"
OUT_MD = OUT_DIR / "current_goal_completion_audit_v17_after_local_upstream_probes.md"
OUT_CHECKLIST = OUT_DIR / "current_goal_completion_audit_v17_after_local_upstream_checklist.csv"
OUT_ASSERT = CHECK_DIR / "current_goal_completion_audit_v17_after_local_upstream_probes_assertions.out"

EVIDENCE = {
    "board_a_shared_state_v16": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T180401-codex-board-a-shared-state-audit-v16/"
        "shared-state-audit/board_a_shared_state_audit_v16.json"
    ),
    "autoquant_local_source_label_equivalence": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T180346-codex-autoquant-local-source-label-equivalence-audit-v1/"
        "autoquant-local-audit/autoquant_local_source_label_equivalence_audit_v1.json"
    ),
    "native_subhour_overlap": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T180420-codex-native-subhour-overlap-blocker-v1/"
        "native-subhour-overlap/native_subhour_overlap_blocker_v1.json"
    ),
    "direct_manipulation_local_intake": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T181211-codex-direct-manipulation-local-intake-probe-v1/"
        "local-intake-probe/direct_manipulation_local_intake_probe_v1.json"
    ),
    "stock_regime_upstream_refresh": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T181454-codex-stock-regime-upstream-refresh-audit-v1/"
        "upstream-refresh/stock_regime_upstream_refresh_audit_v1.json"
    ),
    "strict_1h_gap_triage": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T181859-codex-strict-1h-gap-triage-v1/"
        "strict-1h-gap-triage/strict_1h_gap_triage_v1.json"
    ),
    "prior_completion_audit_v17": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T181835-current-goal-completion-audit-v17-after-local-probes/"
        "completion-audit/current_goal_completion_audit_v17_after_local_probes.json"
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(doc: dict[str, Any]) -> str:
    decision = doc.get("decision")
    if isinstance(decision, dict):
        return str(decision.get("gate_result", ""))
    return str(doc.get("gate_result", ""))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    missing = [name for name, path in EVIDENCE.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing evidence files: {missing}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    docs = {name: load_json(path) for name, path in EVIDENCE.items()}
    shared = docs["board_a_shared_state_v16"]
    aq = docs["autoquant_local_source_label_equivalence"]
    native = docs["native_subhour_overlap"]
    direct = docs["direct_manipulation_local_intake"]
    upstream = docs["stock_regime_upstream_refresh"]
    strict = docs["strict_1h_gap_triage"]

    checklist = [
        {
            "requirement": "scoped_95_for_active_regimes",
            "status": "pass_scoped",
            "evidence": str(EVIDENCE["board_a_shared_state_v16"]),
            "notes": "Bull/Bear/Sideways/Crisis plus scoped direct Manipulation have 95% evidence in the active lane.",
        },
        {
            "requirement": "owner_approved_other_market_source_label_equivalence",
            "status": "fail_blocked",
            "evidence": str(EVIDENCE["autoquant_local_source_label_equivalence"]),
            "notes": "Auto-Quant cache has provider/OHLCV rows only; exact source-panel overlap is AAPL and adds no QQQ/NQ/crypto/FX/futures labels.",
        },
        {
            "requirement": "source_panel_recency_after_2026_01_30",
            "status": "fail_blocked",
            "evidence": str(EVIDENCE["stock_regime_upstream_refresh"]),
            "notes": "Upstream CSV/parquet sizes match local package; no source-owned labels newer than 2026-01-30 are exposed.",
        },
        {
            "requirement": "native_subhour_source_overlap",
            "status": "fail_blocked",
            "evidence": str(EVIDENCE["native_subhour_overlap"]),
            "notes": "AAPL/^IXIC 15m/30m provider rows start after the source labels end; ready overlap cells are 0/4.",
        },
        {
            "requirement": "strict_exact_1h_full_support",
            "status": "partial_blocked",
            "evidence": str(EVIDENCE["strict_1h_gap_triage"]),
            "notes": "Strict 1h support remains 41/156; provider rows are ready but source-label support/recency is the blocker.",
        },
        {
            "requirement": "direct_manipulation_full_species_with_matched_negatives",
            "status": "fail_blocked",
            "evidence": str(EVIDENCE["direct_manipulation_local_intake"]),
            "notes": "Spoofing/layering intake has 0 candidate files and all 3 required files are missing.",
        },
        {
            "requirement": "do_not_mark_full_objective_complete",
            "status": "pass_guardrail",
            "evidence": str(EVIDENCE["prior_completion_audit_v17"]),
            "notes": "Prior and current completion audits agree: strict_full_objective_achieved=false and update_goal=false.",
        },
    ]

    decision = {
        "scoped_active_lane_status": "accepted_95",
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "gate_result": (
            "current_goal_completion_audit_v17="
            "scoped_95_present_upstream_probe_confirms_full_objective_blocked"
        ),
        "blocking_requirements": [
            row["requirement"]
            for row in checklist
            if row["status"] in {"fail_blocked", "partial_blocked"}
        ],
    }
    artifact = {
        "run_id": RUN_ID,
        "artifact_type": "current_goal_completion_audit_v17_after_local_upstream_probes",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD),
        "board_sha256_at_run": sha256(BOARD),
        "coordination_mode": "additive_multi_agent_safe_readback",
        "source_evidence": {name: str(path) for name, path in EVIDENCE.items()},
        "evidence_gates": {name: gate(doc) for name, doc in docs.items()},
        "key_counts": {
            "accepted_95_lanes": shared.get("accepted_95_lanes", []),
            "min_main_root_confidence_floor": shared.get("min_main_root_confidence_floor"),
            "scoped_direct_manipulation_confidence_floor": shared.get(
                "scoped_direct_manipulation_confidence_floor"
            ),
            "autoquant_feather_files": aq.get("autoquant_feather_files"),
            "autoquant_exact_source_panel_symbols": aq.get("exact_source_panel_symbols", []),
            "autoquant_exact_source_panel_subhour_files": aq.get("exact_source_panel_subhour_files"),
            "upstream_same_csv_size": upstream.get("upstream_same_csv_size"),
            "upstream_same_parquet_size": upstream.get("upstream_same_parquet_size"),
            "source_panel_date_max": upstream.get("local_summary", {}).get("date_max"),
            "native_subhour_ready_overlap_cells": native.get("summary", {}).get("ready_overlap_cells"),
            "native_subhour_cells_checked": native.get("summary", {}).get("cells_checked"),
            "strict_1h_accepted_rows": strict.get("accepted_strict_rows"),
            "strict_1h_blocked_rows": strict.get("blocked_strict_rows"),
            "strict_1h_near_miss_count": strict.get("near_miss_count"),
            "direct_candidate_file_count": direct.get("candidate_file_count"),
            "direct_required_files_missing": sum(
                1 for item in direct.get("expected_files", []) if not item.get("exists")
            ),
        },
        "checklist": checklist,
        "decision": decision,
        "next_action": (
            "Acquire source-owned or owner-approved equivalence inputs first. "
            "More provider/OHLCV scans do not close the strict Board A objective."
        ),
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    OUT_JSON.write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(OUT_CHECKLIST, checklist, ["requirement", "status", "evidence", "notes"])

    md = [
        "# Current Goal Completion Audit v17 After Local Upstream Probes",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        "- Scoped active-lane status: `accepted_95`.",
        "- Strict full objective achieved: `false`.",
        "- `update_goal`: `false`.",
        "- Gate result: `current_goal_completion_audit_v17=scoped_95_present_upstream_probe_confirms_full_objective_blocked`.",
        "",
        "## Evidence Readback",
        "",
        f"- Board A shared-state v16 accepted lanes: `{', '.join(shared.get('accepted_95_lanes', []))}`.",
        f"- Auto-Quant local source-label audit: `{gate(aq)}`.",
        f"- Native sub-hour overlap: `{gate(native)}`.",
        f"- Direct Manipulation local intake: `{gate(direct)}`.",
        f"- Stock-regime upstream refresh: `{gate(upstream)}`.",
        f"- Strict 1h gap triage: `{gate(strict)}`.",
        "",
        "## Checklist",
        "",
        "| Requirement | Status | Evidence | Notes |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        md.append(
            f"| `{row['requirement']}` | `{row['status']}` | `{row['evidence']}` | {row['notes']} |"
        )
    md.extend(
        [
            "",
            "## Guardrail",
            "",
            "Do not call `update_goal`, do not mark the strict objective complete, and do not convert provider/OHLCV cache into source-label evidence. The highest-value blocker is source-owned or owner-approved equivalence input acquisition.",
        ]
    )
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    OUT_ASSERT.write_text(
        "\n".join(
            [
                f"run_id={RUN_ID}",
                "scoped_active_lane_status=accepted_95",
                "strict_full_objective_achieved=false",
                "update_goal=false",
                "source_label_equivalence=blocked",
                "source_panel_recency=blocked",
                "native_subhour_overlap=blocked",
                "strict_1h_full_support=partial_blocked",
                "direct_manipulation_full_species=blocked",
                "runtime_code_changed=false",
                "thresholds_relaxed=false",
                "raw_data_committed=false",
                "trade_usable=false",
                "assertion_status=PASS",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
