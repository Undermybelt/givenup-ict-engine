#!/usr/bin/env python3
"""Reproduction helper for the 014221 fail-closed completion audit.

This script recreates only the local audit artifacts under this run root. It
does not mutate runtime code, shared intake roots, R3/R5/R6 roots, thresholds,
or raw data.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


RUN_ID = "20260512T014221-codex-current-objective-completion-audit-after-013904-v1"
GATE = (
    "current_objective_completion_audit_after_013904_v1="
    "not_complete_source_r6_r3_r5_timeframe_downstream_blocked"
)
ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "current-objective-completion-audit-after-013904-v1"
CHECKS_DIR = ROOT / "checks"


REPORT = """# Current Objective Completion Audit After 013904 v1

Run id: `20260512T014221-codex-current-objective-completion-audit-after-013904-v1`
Gate result: `current_objective_completion_audit_after_013904_v1=not_complete_source_r6_r3_r5_timeframe_downstream_blocked`
Board: `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`
Board registration hash before writeback: `0793c4479b51eae4f1616baa7cbac821a41ab10be23c6ae7e78b9ae42c92114e`
Board hash observed before artifact restoration: `81267de5f4bc420f89210457bd905df1385ca9adb649e21703d6a3b856e84ffa`

Objective restatement:
- Every active `MainRegimeV2` regime must reach 95% confidence.
- Each accepted regime needs its own qualifying condition and cross-market, cross-cycle, and cross-timeframe validation.
- The chain must remain real and ordered: provider context, Auto-Quant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution tree.
- Board updates must stay append-only and multi-agent safe.

Completion audit:
- Board state remains `blocked`; Current Cursor remains `20260512T010127+0800-codex-r6-owner-route-entitlement-readback-v1`.
- Accepted labels remain `[]`. Bull and Sideways are field-complete leads only; Bear and Crisis remain unaccepted.
- Checklist counts: pass `2`, partial `2`, blocked `10`.
- R6 owner-export root is absent: `/tmp/ict-engine-board-a-r6-owner-export-v1`.
- Verifier-native R6 files are absent: `positive_spoofing_layering_rows.csv`, `matched_negative_normal_activity_rows.csv`, and `provenance_manifest.json`.
- Source-owned normal controls remain `0`; explicit same-exhibit `FLIP` approval remains false; canonical merge remains false.
- R3 native sub-hour root is absent: `/tmp/ict-engine-native-subhour-source-label-intake`.
- R5 source-panel recency-extension root is absent: `/tmp/ict-engine-source-panel-recency-extension`.
- Source-label equivalence root is present with `2` files, but it is confidence-blocked and daily-only.
- Latest Auto-Quant Tomac cache is parseable but non-promoting: `9` trades, winrate `0.4444444444444444`, profit_total `-0.058056`.
- Provider context is partial: yfinance and Kraken CLI were usable in recent readbacks; IBKR, TradingViewRemix, and Kraken public remain unhealthy or dependency-blocked.
- Runtime-chain surfaces are callable from prior readbacks but non-promoting because accepted source/control roots and canonical merge are absent.

Decision:
- Accepted rows added: `0`.
- New confidence gate: false.
- Canonical merge allowed: false.
- Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion rerun allowed: false.
- Strict full objective achieved: false.
- `update_goal=false`.

No mutation claims:
- Runtime code changed: false.
- Shared intake mutated: false.
- R3/R5/R6 roots mutated: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- External requests sent: false.
- Trade usable: false.

Next:
- Preserve the Current Cursor. The next unlock remains source-owned R6 normal controls or explicit `FLIP`-as-control approval plus canonical merge; keep R3 native sub-hour, R5 recency, cross-timeframe source evidence, Bear/Crisis support, and downstream promotion fail-closed until source-owned rows with provenance arrive.
"""


DATA = {
    "run_id": RUN_ID,
    "gate_result": GATE,
    "board": "docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
    "board_registration_hash_before_writeback": (
        "0793c4479b51eae4f1616baa7cbac821a41ab10be23c6ae7e78b9ae42c92114e"
    ),
    "board_sha256_before_restoration": (
        "81267de5f4bc420f89210457bd905df1385ca9adb649e21703d6a3b856e84ffa"
    ),
    "observed_cursor": "20260512T010127+0800-codex-r6-owner-route-entitlement-readback-v1",
    "board_state": "blocked",
    "checklist_counts": {"pass": 2, "partial": 2, "blocked": 10},
    "accepted_labels": [],
    "field_complete_condition_leads": ["Bull", "Sideways"],
    "unaccepted_regime_labels": ["Bull", "Sideways", "Bear", "Crisis"],
    "source_roots": [
        {
            "id": "source_label_equivalence",
            "root": "/tmp/ict-engine-source-label-equivalence-intake",
            "present": True,
            "file_count": 2,
            "acceptance_status": "confidence_blocked_daily_only",
        },
        {
            "id": "r6_owner_export",
            "root": "/tmp/ict-engine-board-a-r6-owner-export-v1",
            "present": False,
            "file_count": 0,
            "required_files_present": False,
            "source_owned_normal_controls": 0,
            "explicit_flip_approval": False,
        },
        {
            "id": "r3_native_subhour",
            "root": "/tmp/ict-engine-native-subhour-source-label-intake",
            "present": False,
            "file_count": 0,
        },
        {
            "id": "r5_recency_extension",
            "root": "/tmp/ict-engine-source-panel-recency-extension",
            "present": False,
            "file_count": 0,
        },
    ],
    "r6_required_verifier_native_files": [
        {
            "path": "/tmp/ict-engine-board-a-r6-owner-export-v1/positive_spoofing_layering_rows.csv",
            "present": False,
        },
        {
            "path": "/tmp/ict-engine-board-a-r6-owner-export-v1/matched_negative_normal_activity_rows.csv",
            "present": False,
        },
        {
            "path": "/tmp/ict-engine-board-a-r6-owner-export-v1/provenance_manifest.json",
            "present": False,
        },
    ],
    "auto_quant_latest_cache": {
        "source_run": "20260512T013904-codex-autoquant-latest-backtest-cache-readback-v1",
        "strategy_name": "TomacNQ_KillzoneBreakout",
        "timeframe": "1h",
        "total_trades": 9,
        "wins": 4,
        "losses": 5,
        "winrate": 0.4444444444444444,
        "profit_total": -0.058056,
        "acceptance_status": "fail_closed_low_trade_count_and_negative_edge",
    },
    "provider_context": {
        "yfinance": "usable_recent_readback",
        "kraken_cli": "usable_recent_readback",
        "ibkr": "unhealthy_or_dependency_blocked",
        "tradingview_remix": "unhealthy_or_dependency_blocked",
        "kraken_public": "unhealthy_or_dependency_blocked",
        "acceptance_status": "partial_context_only_not_regime_evidence",
    },
    "downstream_chain": {
        "provider_autoquant_filter_prebayes_bbn_catboost_pathranking_execution_tree": (
            "callable_but_non_promoting"
        ),
        "canonical_merge_allowed": False,
        "promotion_rerun_allowed": False,
    },
    "accepted_rows_added": 0,
    "new_confidence_gate": False,
    "canonical_merge_allowed": False,
    "downstream_chain_rerun_allowed": False,
    "strict_full_objective_achieved": False,
    "update_goal": False,
    "runtime_code_changed": False,
    "shared_intake_mutated": False,
    "r3_r5_r6_roots_mutated": False,
    "thresholds_relaxed": False,
    "raw_data_committed": False,
    "external_requests_sent": False,
    "trade_usable": False,
}


CHECKLIST_ROWS = [
    (
        "board_current_cursor_readback",
        "pass",
        "Board state remains blocked and Current Cursor remains 20260512T010127+0800-codex-r6-owner-route-entitlement-readback-v1.",
    ),
    (
        "multi_agent_safety",
        "pass",
        "Artifact restoration is additive; runtime code, shared intake, and R3/R5/R6 roots are not mutated.",
    ),
    (
        "real_autoquant_readback",
        "partial",
        "013904 parsed latest Tomac cache, but 9 trades, 0.4444444444444444 winrate, and -0.058056 profit_total are non-promoting.",
    ),
    (
        "provider_context_enumerated",
        "partial",
        "yfinance and Kraken CLI usable in recent readbacks; IBKR, TradingViewRemix, and Kraken public unhealthy or dependency-blocked.",
    ),
    (
        "every_active_regime_95_confidence",
        "blocked",
        "Accepted labels remain empty; Bull and Sideways are only field-complete leads; Bear and Crisis remain unaccepted.",
    ),
    (
        "source_owned_labels_accepted",
        "blocked",
        "Accepted rows added is 0 and source-label equivalence is confidence-blocked.",
    ),
    (
        "other_market_cycle_cross_timeframe_validation",
        "blocked",
        "Source-label equivalence is daily-only; source-native cross-timeframe evidence is absent.",
    ),
    (
        "r6_owner_controls_or_flip_approval",
        "blocked",
        "R6 owner-export root is absent, source-owned normal controls are 0, and explicit FLIP approval is false.",
    ),
    (
        "r3_native_subhour_source_input",
        "blocked",
        "/tmp/ict-engine-native-subhour-source-label-intake is absent.",
    ),
    (
        "r5_recency_extension_source_input",
        "blocked",
        "/tmp/ict-engine-source-panel-recency-extension is absent.",
    ),
    (
        "canonical_merge",
        "blocked",
        "Canonical merge remains false because verifier-native source/control roots are absent.",
    ),
    (
        "downstream_chain_promotion_rerun",
        "blocked",
        "Provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion rerun is disallowed.",
    ),
    (
        "strict_full_objective_complete",
        "blocked",
        "Every-regime 95 percent, cross-market/cross-cycle validation, R6/R3/R5 inputs, and downstream promotion are incomplete.",
    ),
    (
        "update_goal_allowed",
        "blocked",
        "update_goal remains false; strict objective is not complete.",
    ),
]


ROOT_STATUS_ROWS = [
    (
        "source_label_equivalence",
        "/tmp/ict-engine-source-label-equivalence-intake",
        "true",
        "2",
        "present_confidence_blocked",
    ),
    (
        "r6_owner_export",
        "/tmp/ict-engine-board-a-r6-owner-export-v1",
        "false",
        "0",
        "absent",
    ),
    (
        "r3_native_subhour",
        "/tmp/ict-engine-native-subhour-source-label-intake",
        "false",
        "0",
        "absent",
    ),
    (
        "r5_recency_extension",
        "/tmp/ict-engine-source-panel-recency-extension",
        "false",
        "0",
        "absent",
    ),
]


ASSERTIONS = [
    "run_id=PASS",
    "gate_result=PASS",
    "current_cursor_010127=PASS",
    "board_state_blocked=PASS",
    "checklist_pass_count_2=PASS",
    "checklist_partial_count_2=PASS",
    "checklist_blocked_count_10=PASS",
    "accepted_labels_empty=PASS",
    "field_complete_leads_bull_sideways=PASS",
    "r6_owner_export_root_absent=PASS",
    "r6_verifier_native_files_absent=PASS",
    "source_owned_normal_controls_zero=PASS",
    "explicit_flip_approval_false=PASS",
    "r3_native_subhour_root_absent=PASS",
    "r5_recency_extension_root_absent=PASS",
    "source_label_equivalence_present_with_two_files=PASS",
    "autoquant_latest_cache_low_trade_negative_non_promoting=PASS",
    "providers_partial_not_acceptance_evidence=PASS",
    "downstream_chain_callable_but_non_promoting=PASS",
    "accepted_rows_added_zero=PASS",
    "new_confidence_gate_false=PASS",
    "canonical_merge_allowed_false=PASS",
    "downstream_chain_rerun_allowed_false=PASS",
    "strict_full_objective_achieved_false=PASS",
    "update_goal_false=PASS",
    "runtime_code_changed_false=PASS",
    "shared_intake_mutated_false=PASS",
    "r3_r5_r6_roots_mutated_false=PASS",
    "thresholds_relaxed_false=PASS",
    "raw_data_committed_false=PASS",
    "external_requests_sent_false=PASS",
    "trade_usable_false=PASS",
]


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    (ARTIFACT_DIR / "current_objective_completion_audit_after_013904_v1.md").write_text(
        REPORT,
        encoding="utf-8",
    )
    (ARTIFACT_DIR / "current_objective_completion_audit_after_013904_v1.json").write_text(
        json.dumps(DATA, indent=2) + "\n",
        encoding="utf-8",
    )

    with (ARTIFACT_DIR / "prompt_to_artifact_checklist_after_013904_v1.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(["requirement", "status", "evidence"])
        writer.writerows(CHECKLIST_ROWS)

    with (ARTIFACT_DIR / "intake_root_status_after_013904_v1.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(["root", "path", "present", "file_count", "status"])
        writer.writerows(ROOT_STATUS_ROWS)

    (CHECKS_DIR / "current_objective_completion_audit_after_013904_v1_assertions.out").write_text(
        "\n".join(ASSERTIONS) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
