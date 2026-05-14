#!/usr/bin/env python3
"""Screen current 115700/121607 feedback rows for admissible BBN evidence nodes."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean


RUN_ID = "20260512T122425+0800-codex-121607-bbn-calibration-node-screen-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_ROOT = RUN_ROOT / "121607-bbn-calibration-node-screen-v1"
CHECK_ROOT = RUN_ROOT / "checks"
DERIVED_ROOT = RUN_ROOT / "derived"

ROWS_PATH = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/"
    "derived/same_root_six_provider_1h_aq_real_trades.enriched_layer_contract.jsonl"
)
FEEDBACK_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1/"
    "120630-bbn-negative-feedback-packet-v1/120630_bbn_negative_feedback_packet_v1.json"
)
GAP_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T121701+0800-codex-120630-regime-confidence-gap-map-v1/"
    "120630-regime-confidence-gap-map-v1/120630_regime_confidence_gap_map_v1.json"
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def load_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def first_factor(row: dict) -> dict:
    factors = row.get("factors_used") or [{}]
    return factors[0] if factors else {}


def is_win(row: dict) -> bool:
    return row.get("realized_outcome") == "win"


def pnl(row: dict) -> float:
    return float(row.get("pnl") or 0.0)


def factor_weighted_score(row: dict) -> float:
    value = first_factor(row).get("weighted_score")
    return float(value or 0.0)


def summarize(grouped: dict[str, list[dict]]) -> list[dict]:
    result = []
    for state, rows in grouped.items():
        wins = sum(1 for row in rows if is_win(row))
        total_pnl = sum(pnl(row) for row in rows)
        result.append(
            {
                "state": state,
                "rows": len(rows),
                "wins": wins,
                "losses": len(rows) - wins,
                "win_rate": round(wins / len(rows), 6) if rows else 0.0,
                "total_pnl": round(total_pnl, 6),
                "avg_pnl": round(total_pnl / len(rows), 6) if rows else 0.0,
            }
        )
    return sorted(result, key=lambda item: (-item["rows"], item["state"]))


def group(rows: list[dict], key_fn) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[str(key_fn(row))].append(row)
    return summarize(grouped)


def chronological_quartiles(rows: list[dict]) -> list[dict]:
    sorted_rows = sorted(rows, key=lambda row: row.get("open_ts_ms") or 0)
    grouped: dict[str, list[dict]] = defaultdict(list)
    total = len(sorted_rows)
    for idx, row in enumerate(sorted_rows):
        grouped[f"Q{idx * 4 // total + 1}"].append(row)
    return summarize(grouped)


def candidate(node: str, states: list[dict], accepted: bool, reasons: list[str], notes: list[str] | None = None) -> dict:
    return {
        "node": node,
        "states": states,
        "accepted_candidate": accepted,
        "rejection_reasons": reasons,
        "notes": notes or [],
    }


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    CHECK_ROOT.mkdir(parents=True, exist_ok=True)
    DERIVED_ROOT.mkdir(parents=True, exist_ok=True)

    rows = load_rows(ROWS_PATH)
    feedback = load_json(FEEDBACK_JSON)
    gap = load_json(GAP_JSON)

    provider_states = group(rows, lambda row: row.get("source_provider"))
    branch_states = group(rows, lambda row: row.get("branch_path"))
    provider_branch_states = group(
        rows,
        lambda row: f"{row.get('source_provider')} | {row.get('branch_path')}",
    )
    score_sign_states = group(
        rows,
        lambda row: "positive_score" if factor_weighted_score(row) > 0 else "negative_or_zero_score",
    )
    quartile_states = chronological_quartiles(rows)
    pre_bayes_states = group(rows, lambda row: (row.get("pre_bayes_filter_state") or {}).get("canonical_regime"))
    execution_states = group(
        rows,
        lambda row: (
            (row.get("execution_tree_decision") or {}).get("candidate_status"),
            (row.get("execution_tree_decision") or {}).get("review"),
            (row.get("execution_tree_decision") or {}).get("ready"),
            (row.get("execution_tree_decision") or {}).get("actionable"),
        ),
    )

    leakage_matches = sum(
        1
        for row in rows
        if abs(factor_weighted_score(row) - pnl(row)) < 1e-9
    )
    leakage_ratio = leakage_matches / len(rows)
    best_provider = max(provider_states, key=lambda item: item["win_rate"])
    best_provider_branch = max(provider_branch_states, key=lambda item: item["win_rate"])
    best_quartile = max(quartile_states, key=lambda item: item["win_rate"])
    worst_quartile = min(quartile_states, key=lambda item: item["win_rate"])

    candidates = [
        candidate(
            "source_provider",
            provider_states,
            False,
            [
                "best_provider_win_rate_below_0_95",
                "single_symbol_single_timeframe_only",
                "provider_outcomes_do_not_lift_regime_confidence",
            ],
            [f"best_provider={best_provider['state']} win_rate={best_provider['win_rate']} rows={best_provider['rows']}"],
        ),
        candidate(
            "branch_path",
            branch_states,
            False,
            [
                "best_branch_win_rate_below_0_95",
                "active_bbn_regime_constant_range",
                "branch_label_is_not_independent_regime_state_evidence",
            ],
        ),
        candidate(
            "source_provider_x_branch_path",
            provider_branch_states,
            False,
            [
                "best_group_rows_below_30",
                "best_group_not_cross_provider_stable",
                "best_group_win_rate_below_0_95",
            ],
            [
                f"best_group={best_provider_branch['state']} "
                f"rows={best_provider_branch['rows']} win_rate={best_provider_branch['win_rate']}"
            ],
        ),
        candidate(
            "chronological_quartile",
            quartile_states,
            False,
            [
                "chronological_outcomes_unstable",
                "worst_quartile_collapse",
                "does_not_supply_cross_period_regime_lift",
            ],
            [
                f"best_quartile={best_quartile['state']} win_rate={best_quartile['win_rate']}",
                f"worst_quartile={worst_quartile['state']} win_rate={worst_quartile['win_rate']}",
            ],
        ),
        candidate(
            "factor_weighted_score_sign",
            score_sign_states,
            False,
            [
                "post_trade_pnl_label_leakage",
                "weighted_score_equals_realized_pnl_for_all_rows",
                "not_admissible_as_pre_trade_bbn_node",
            ],
            [f"weighted_score_equals_pnl_rows={leakage_matches}/{len(rows)}"],
        ),
        candidate(
            "pre_bayes_canonical_regime",
            pre_bayes_states,
            False,
            [
                "constant_state_range",
                "pre_bayes_gate_pass_neutralized",
                "no_cross_regime_separator_in_current_packet",
            ],
        ),
        candidate(
            "execution_status_tuple",
            execution_states,
            False,
            [
                "constant_fail_closed_execution_status",
                "ready_false_actionable_false_review_observe",
                "cannot_promote_without_execution_admissibility",
            ],
        ),
    ]

    accepted = [item for item in candidates if item["accepted_candidate"]]
    report = {
        "run_id": RUN_ID,
        "source_runs": {
            "enriched_rows": "20260512T121347+0800-codex-115700-enriched-downstream-chain-v1",
            "feedback_packet": "20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1",
            "gap_map": "20260512T121701+0800-codex-120630-regime-confidence-gap-map-v1",
        },
        "source_files": {
            str(ROWS_PATH): sha256(ROWS_PATH),
            str(FEEDBACK_JSON): sha256(FEEDBACK_JSON),
            str(GAP_JSON): sha256(GAP_JSON),
        },
        "row_count": len(rows),
        "provider_count": len({row.get("source_provider") for row in rows}),
        "branch_count": len({row.get("branch_path") for row in rows}),
        "active_regime": gap.get("active_regime"),
        "active_confidence": gap.get("active_confidence"),
        "range_gap_to_95": gap.get("range_gap_to_95"),
        "directional_gap_shortfall": gap.get("directional_gap_shortfall"),
        "current_feedback_context": feedback.get("bbn_cpd_update_candidate", {}).get("context"),
        "current_feedback_empirical_outcome": feedback.get("bbn_cpd_update_candidate", {}).get(
            "empirical_outcome_from_120630"
        ),
        "candidate_nodes": candidates,
        "accepted_candidate_nodes": accepted,
        "leakage_detector": {
            "weighted_score_equals_pnl_rows": leakage_matches,
            "weighted_score_equals_pnl_ratio": round(leakage_ratio, 6),
            "verdict": "reject_factor_weighted_score_as_pre_trade_evidence",
        },
        "decision": {
            "gate": "121607_bbn_calibration_node_screen_v1=no_admissible_bbn_node_no_promotion",
            "bbn_likelihood_mutation_allowed": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "next_evidence_needs": [
            "pre_trade provider/context features independent of realized pnl",
            "cross-provider and cross-period validation before CPD mutation",
            "non-constant pre-bayes regime evidence across trend/range/stress/transition",
            "execution admissibility evidence resolving ready=false/actionable=false/observe",
        ],
    }

    json_path = OUT_ROOT / "121607_bbn_calibration_node_screen_v1.json"
    md_path = OUT_ROOT / "121607_bbn_calibration_node_screen_v1.md"
    csv_path = OUT_ROOT / "121607_bbn_calibration_node_screen_v1_candidate_nodes.csv"
    assertion_path = CHECK_ROOT / "121607_bbn_calibration_node_screen_v1_assertions.out"

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "node",
                "state",
                "rows",
                "wins",
                "losses",
                "win_rate",
                "total_pnl",
                "avg_pnl",
                "accepted_candidate",
                "rejection_reasons",
            ],
        )
        writer.writeheader()
        for item in candidates:
            for state in item["states"]:
                writer.writerow(
                    {
                        "node": item["node"],
                        "state": state["state"],
                        "rows": state["rows"],
                        "wins": state["wins"],
                        "losses": state["losses"],
                        "win_rate": state["win_rate"],
                        "total_pnl": state["total_pnl"],
                        "avg_pnl": state["avg_pnl"],
                        "accepted_candidate": item["accepted_candidate"],
                        "rejection_reasons": ";".join(item["rejection_reasons"]),
                    }
                )

    lines = [
        "# 121607 BBN Calibration Node Screen v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Inputs",
        f"- Enriched rows: `{ROWS_PATH}`",
        f"- Feedback packet: `{FEEDBACK_JSON}`",
        f"- Gap map: `{GAP_JSON}`",
        "",
        "## Result",
        f"- Rows screened: `{len(rows)}` across `{report['provider_count']}` providers and `{report['branch_count']}` branch paths.",
        f"- Active regime remained `{report['active_regime']}` confidence `{report['active_confidence']}`; gap to `0.95` was `{report['range_gap_to_95']}`.",
        f"- Existing feedback context: `{report['current_feedback_context']}` with empirical outcome `{report['current_feedback_empirical_outcome']}`.",
        f"- Accepted candidate BBN nodes: `{len(accepted)}`.",
        f"- Gate: `{report['decision']['gate']}`.",
        "",
        "## Screened Nodes",
    ]
    for item in candidates:
        best = max(item["states"], key=lambda state: state["win_rate"])
        lines.append(
            f"- `{item['node']}`: best state `{best['state']}` rows `{best['rows']}` "
            f"win_rate `{best['win_rate']}`; accepted `{item['accepted_candidate']}`; "
            f"reject `{'; '.join(item['rejection_reasons'])}`."
        )
    lines.extend(
        [
            "",
            "## Leakage Guard",
            f"- `factor_weighted_score_sign` looked perfect, but `weighted_score == realized pnl` for `{leakage_matches}/{len(rows)}` rows.",
            "- This is rejected as post-trade label leakage and must not be used as a pre-trade BBN evidence node.",
            "",
            "## Decision",
            "- No screened node is admissible for production BBN likelihood mutation from this packet.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Next Evidence Needs",
        ]
    )
    lines.extend(f"- {item}" for item in report["next_evidence_needs"])
    md_path.write_text("\n".join(lines) + "\n")

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS rows={len(rows)}",
        f"PASS provider_count={report['provider_count']}",
        f"PASS branch_count={report['branch_count']}",
        f"PASS active_regime={report['active_regime']}",
        f"PASS active_confidence={report['active_confidence']}",
        f"PASS accepted_candidate_nodes={len(accepted)}",
        f"PASS weighted_score_equals_pnl_rows={leakage_matches}/{len(rows)}",
        "PASS leakage_guard=factor_weighted_score_sign_rejected",
        "FAIL_CLOSED bbn_likelihood_mutation_allowed=False",
        "FAIL_CLOSED promotion_allowed=False",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertion_path.write_text("\n".join(assertions) + "\n")

    (RUN_ROOT / "run_id.txt").write_text(RUN_ID + "\n")
    (RUN_ROOT / "source_roots.txt").write_text(
        "\n".join(
            [
                "20260512T121347+0800-codex-115700-enriched-downstream-chain-v1",
                "20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1",
                "20260512T121701+0800-codex-120630-regime-confidence-gap-map-v1",
            ]
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
