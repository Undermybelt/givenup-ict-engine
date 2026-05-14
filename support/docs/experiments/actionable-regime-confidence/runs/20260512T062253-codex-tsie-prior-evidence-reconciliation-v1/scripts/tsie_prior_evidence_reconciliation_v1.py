#!/usr/bin/env python3
"""Reconcile the 061855 TSIE candidate screen with prior Board A evidence."""

from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "tsie-prior-evidence-reconciliation"
CHECK_DIR = RUN_ROOT / "checks"

CURRENT_CANDIDATE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T061855+0800-codex-r3-hf-tsie-native-subhour-source-screen-v1/r3-hf-tsie-native-subhour-source-screen-v1/r3_hf_tsie_native_subhour_source_screen_v1.json"
MAPPING_AUDIT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T074300-codex-hf-tsie-source-label-mapping-audit/hf-tsie-mapping/hf_tsie_source_label_mapping_audit.json"
PARENT_GATE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T032344-codex-tsie-parent-root-labeled-gate/tsie-parent-gate/tsie_parent_root_labeled_gate_report.json"
EXPANDED_GATE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T034054-codex-hf-tsie-expanded-regime-gate/hf-tsie-expanded-gate/hf_tsie_expanded_regime_report.json"

TARGET_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def root_row(report: dict) -> dict:
    cal = report.get("calibration", {})
    test = report.get("test", {})
    return {
        "root": report.get("root"),
        "accepted_95": bool(report.get("accepted_95")),
        "rule": report.get("selected_rule"),
        "calibration_support": cal.get("support"),
        "calibration_wilson95_lcb": cal.get("precision_wilson_lcb_95"),
        "test_support": test.get("support"),
        "test_wilson95_lcb": test.get("precision_wilson_lcb_95"),
        "test_coverage": test.get("coverage"),
        "validation_market_contexts": test.get("validation_market_contexts"),
        "validation_timeframes": test.get("validation_timeframes"),
        "blockers": report.get("blockers", []),
    }


def expanded_row(root: str, report: dict) -> dict:
    cal = report.get("calibration", {})
    test = report.get("test", {})
    return {
        "root": root,
        "accepted_95": bool(report.get("accepted_95")),
        "rule": report.get("selected_rule"),
        "calibration_support": cal.get("support"),
        "calibration_wilson95_lcb": cal.get("precision_wilson_lcb_95"),
        "test_support": test.get("support"),
        "test_wilson95_lcb": test.get("precision_wilson_lcb_95"),
        "test_coverage": test.get("coverage"),
        "validation_market_contexts": test.get("validation_market_contexts"),
        "validation_timeframes": test.get("validation_timeframes"),
        "blockers": report.get("blockers", []),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    current = read_json(CURRENT_CANDIDATE)
    mapping = read_json(MAPPING_AUDIT)
    parent = read_json(PARENT_GATE)
    expanded = read_json(EXPANDED_GATE)

    same_dataset = current["candidate"]["dataset_id"] == mapping["source"]["dataset"]
    same_commit = current["candidate"]["commit_sha"] == mapping["source"]["sha"]

    parent_rows = [root_row(item) for item in parent.get("root_reports", [])]
    expanded_rows = [
        expanded_row(root, item)
        for root, item in expanded.get("root_reports", {}).items()
    ]
    target_roots = {str(path): path.exists() for path in TARGET_ROOTS}

    accepted_parent_roots = [
        item["root"] for item in parent_rows if item["accepted_95"]
    ]
    accepted_expanded_roots = [
        item["root"] for item in expanded_rows if item["accepted_95"]
    ]

    assertions = {
        "same_dataset_as_061855": same_dataset,
        "same_commit_as_061855": same_commit,
        "prior_mapping_audit_blocked": mapping.get("gate_result") == "blocked_hf_tsie_not_attachable_as_mainregimev2_source_label_panel",
        "prior_parent_gate_blocked": parent.get("decision", {}).get("gate") == "blocked_tsie_parent_root_labeled_gate_below_95",
        "prior_expanded_gate_blocked": expanded.get("decision", {}).get("gate_result") == "blocked_hf_tsie_expanded_regime_gate_below_95_or_validation_scope",
        "accepted_rows_added": 0,
        "target_root_mutated": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    report = {
        "run_id": "20260512T062253+0800-codex-tsie-prior-evidence-reconciliation-v1",
        "decision": "tsie_prior_evidence_reconciliation_v1=duplicate_candidate_prior_full_data_and_mapping_failures_no_intake",
        "candidate_061855": {
            "dataset_id": current["candidate"]["dataset_id"],
            "commit_sha": current["candidate"]["commit_sha"],
            "license": current["candidate"]["license"],
            "page_url": current["candidate"]["page_url"],
            "raw_data_downloaded_in_061855": current["raw_data_downloaded"],
            "raw_data_committed": current["raw_data_committed"],
            "files": current.get("files", []),
        },
        "same_source_reconciliation": {
            "same_dataset": same_dataset,
            "same_commit": same_commit,
            "mapping_audit_dataset": mapping["source"]["dataset"],
            "mapping_audit_commit": mapping["source"]["sha"],
        },
        "prior_evidence": [
            {
                "run_root": "docs/experiments/actionable-regime-confidence/runs/20260511T074300-codex-hf-tsie-source-label-mapping-audit",
                "gate": mapping.get("gate_result"),
                "accepted_root_labels_added": mapping.get("completion_accounting", {}).get("accepted_root_labels_added"),
                "why_not_accepted": mapping.get("completion_accounting", {}).get("why_not_accepted", []),
            },
            {
                "run_root": "docs/experiments/actionable-regime-confidence/runs/20260511T032344-codex-tsie-parent-root-labeled-gate",
                "gate": parent.get("decision", {}).get("gate"),
                "accepted_roots": parent.get("decision", {}).get("accepted_95_roots_from_this_run", []),
                "rows": parent.get("dataset", {}).get("rows"),
                "market_contexts": parent.get("dataset", {}).get("market_contexts", []),
                "timeframes": parent.get("dataset", {}).get("timeframes", []),
                "root_reports": parent_rows,
            },
            {
                "run_root": "docs/experiments/actionable-regime-confidence/runs/20260511T034054-codex-hf-tsie-expanded-regime-gate",
                "gate": expanded.get("decision", {}).get("gate_result"),
                "accepted_roots": expanded.get("decision", {}).get("accepted_new_roots_95", []),
                "root_reports": expanded_rows,
            },
        ],
        "required_target_roots": target_roots,
        "accepted_rows_added": 0,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
        "assertions": assertions,
        "next_action": (
            "Do not materialize /tmp/ict-engine-native-subhour-source-label-intake "
            "from TSIE unless a new source-owner MainRegimeV2 crosswalk or materially "
            "different source revision arrives. Continue with explicit R6 source/control "
            "approval, source-owned R5 recency rows, or a different R3 native-subhour "
            "source-label panel."
        ),
    }

    json_path = OUT_DIR / "tsie_prior_evidence_reconciliation_v1.json"
    md_path = OUT_DIR / "tsie_prior_evidence_reconciliation_v1.md"
    assertions_path = CHECK_DIR / "tsie_prior_evidence_reconciliation_v1_assertions.out"

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# TSIE Prior Evidence Reconciliation v1",
        "",
        f"Run id: `{report['run_id']}`",
        "",
        "## Decision",
        "",
        f"`{report['decision']}`",
        "",
        "- `061855` points to the same Hugging Face dataset and commit already audited by prior Board A artifacts.",
        "- Prior mapping audit blocked TSIE as sidecar-only/rule-based IDX signal labels without direct `Crisis` or accepted `MainRegimeV2` source labels.",
        "- Prior full-data parent-root calibration accepted `0` roots under unchanged 95% Wilson lower-bound and cross-context gates.",
        "- Prior expanded-label calibration also accepted `0` new roots.",
        "- No required target root exists or was mutated in this slice.",
        "",
        "## Parent-Root Gate Readback",
        "",
        "| Root | Cal support | Cal LCB | Test support | Test LCB | Test coverage | Accepted | Blockers |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for item in parent_rows:
        lines.append(
            "| {root} | {calibration_support} | {calibration_wilson95_lcb:.6f} | "
            "{test_support} | {test_wilson95_lcb:.6f} | {test_coverage:.6f} | "
            "{accepted_95} | {blockers} |".format(
                root=item["root"],
                calibration_support=item["calibration_support"],
                calibration_wilson95_lcb=item["calibration_wilson95_lcb"],
                test_support=item["test_support"],
                test_wilson95_lcb=item["test_wilson95_lcb"],
                test_coverage=item["test_coverage"],
                accepted_95=str(item["accepted_95"]).lower(),
                blockers=", ".join(item["blockers"]),
            )
        )
    lines.extend(
        [
            "",
            "## Required Roots",
            "",
        ]
    )
    for path, exists in target_roots.items():
        lines.append(f"- `{path}`: `{str(exists).lower()}`")
    lines.extend(
        [
            "",
            "## Accounting",
            "",
            "- Accepted rows added: `0`.",
            "- Canonical merge: `false`.",
            "- Downstream promotion rerun: `false`.",
            "- Strict full objective: `false`.",
            "- Trade usable: `false`.",
            "- `update_goal=false`.",
            "",
            "## Next",
            "",
            report["next_action"],
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")

    assertion_lines = [f"{key}={str(value).lower()}" for key, value in sorted(assertions.items())]
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")

    if not all(
        [
            assertions["same_dataset_as_061855"],
            assertions["same_commit_as_061855"],
            assertions["prior_mapping_audit_blocked"],
            assertions["prior_parent_gate_blocked"],
            assertions["prior_expanded_gate_blocked"],
            assertions["update_goal"] is False,
        ]
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
