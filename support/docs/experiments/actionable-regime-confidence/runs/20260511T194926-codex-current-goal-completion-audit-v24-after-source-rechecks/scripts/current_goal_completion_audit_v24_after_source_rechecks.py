#!/usr/bin/env python3
"""Prompt-to-artifact completion audit after latest Board A source rechecks."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T194926-codex-current-goal-completion-audit-v24-after-source-rechecks"
)
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"


ARTIFACTS = {
    "v23_latest": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T193453-codex-current-goal-completion-audit-v23-after-latest-readbacks/"
        "completion-audit/current_goal_completion_audit_v23_after_latest_readbacks.json"
    ),
    "strict_1h_source_intake": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T192432-codex-strict-1h-source-intake-verifier-readback-v1/"
        "source-intake-verifier-readback/strict_1h_source_intake_verifier_readback_v1.json"
    ),
    "strict_1h_panel_exhaustion": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T192900-codex-strict-1h-contract-panel-exhaustion-v1/"
        "strict-1h-contract-panel-exhaustion/strict_1h_contract_panel_exhaustion_v1.json"
    ),
    "direct_intake": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T193301-codex-direct-manipulation-intake-verifier-readback-v1/"
        "direct-manipulation-intake-verifier-readback/direct_manipulation_intake_verifier_readback_v1.json"
    ),
    "intake_file_rescan": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T193804-codex-board-a-intake-file-presence-rescan-v1/"
        "intake-file-presence-rescan/board_a_intake_file_presence_rescan_v1.json"
    ),
    "web_source_label_recheck": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T193908-codex-web-source-label-broad-recheck-v1/"
        "web-source-label-broad-recheck/web_source_label_broad_recheck_v1.json"
    ),
    "external_metadata_readback": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T194230-codex-external-metadata-search-readback-v1/"
        "external-metadata-search-readback/external_metadata_search_readback_v1.json"
    ),
    "github_source_label_screen": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T193958-codex-github-source-label-candidate-screen-v1/"
        "github-source-label-screen/github_source_label_candidate_screen_v1.json"
    ),
    "native_subhour_recheck": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T194400-codex-native-subhour-source-recheck-v2/"
        "native-subhour-source-recheck/native_subhour_source_recheck_v2.json"
    ),
}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {"missing_artifact": True, "path": str(path)}
    return json.loads(path.read_text())


def bool_field(data: dict, key: str, default: bool = False) -> bool:
    value = data.get(key, default)
    return bool(value)


def nested(data: dict, *keys: str, default=None):
    cur = data
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    loaded = {name: load_json(path) for name, path in ARTIFACTS.items()}

    v23 = loaded["v23_latest"]
    strict_intake = loaded["strict_1h_source_intake"]
    panel_exhaustion = loaded["strict_1h_panel_exhaustion"]
    direct_intake = loaded["direct_intake"]
    intake_rescan = loaded["intake_file_rescan"]
    web_recheck = loaded["web_source_label_recheck"]
    metadata_readback = loaded["external_metadata_readback"]
    github_screen = loaded["github_source_label_screen"]
    native_subhour = loaded["native_subhour_recheck"]

    checklist = [
        {
            "id": "R1",
            "requirement": "Every active regime has calibrated >=95% confidence.",
            "status": "pass_scoped_only",
            "artifact": str(ARTIFACTS["v23_latest"]),
            "evidence": "v23 records scoped active-lane >=95% evidence, but not strict transfer completion.",
            "gap": "This passes only the scoped active-lane check; it does not by itself satisfy other-market and other-cycle validation.",
        },
        {
            "id": "R2",
            "requirement": "Other-market/species validation has suitable confidence and source-label equivalence.",
            "status": "fail_blocked",
            "artifact": ";".join(
                str(ARTIFACTS[k])
                for k in [
                    "web_source_label_recheck",
                    "external_metadata_readback",
                    "github_source_label_screen",
                ]
            ),
            "evidence": (
                f"web={web_recheck.get('decision')}; "
                f"metadata={metadata_readback.get('decision')}; "
                f"github={nested(github_screen, 'decision', 'gate_result', default=github_screen.get('decision'))}"
            ),
            "gap": "Latest web/GitHub/metadata screens still found zero promotable source-owned or owner-approved equivalence rows.",
        },
        {
            "id": "R3",
            "requirement": "Other-cycle/timeframe validation has suitable confidence, including native sub-hour labels.",
            "status": "fail_blocked",
            "artifact": str(ARTIFACTS["native_subhour_recheck"]),
            "evidence": (
                f"native_subhour_decision={native_subhour.get('decision')}; "
                f"ready_sources={native_subhour.get('ready_native_subhour_source_owned_label_sources')}; "
                f"candidate_records={native_subhour.get('candidate_records')}"
            ),
            "gap": "Native sub-hour source-owned label sources remain zero; generated/model, raw-panel, synthetic, bot, and research-code surfaces remain fail-closed.",
        },
        {
            "id": "R4",
            "requirement": "Strict exact 1h remaining slots have new source-owned rows and provenance.",
            "status": "fail_blocked",
            "artifact": ";".join(
                str(ARTIFACTS[k])
                for k in ["strict_1h_source_intake", "strict_1h_panel_exhaustion", "intake_file_rescan"]
            ),
            "evidence": (
                f"source_intake={strict_intake.get('decision')}; "
                f"panel_exhaustion={panel_exhaustion.get('decision')}; "
                f"required_present={intake_rescan.get('required_present_count')}/"
                f"{intake_rescan.get('required_file_count')}"
            ),
            "gap": "No strict 1h intake files or extra source rows are available; existing panel rows are already counted.",
        },
        {
            "id": "R5",
            "requirement": "XOM/Sideways and remaining strict 1h targets have recency-tail repair where required.",
            "status": "fail_blocked",
            "artifact": str(ARTIFACTS["v23_latest"]),
            "evidence": "v23 carries fixed_gate=41/156 and future_protocol=45/156; prior stock-regime live recency check found no XOM/Sideways post-tail repair.",
            "gap": "No new source-owned recency-tail rows were added after the latest rechecks.",
        },
        {
            "id": "R6",
            "requirement": "Direct Manipulation has row-level positives, matched normal controls, and provenance.",
            "status": "fail_blocked",
            "artifact": str(ARTIFACTS["direct_intake"]),
            "evidence": (
                f"decision={direct_intake.get('decision')}; "
                f"missing_files={len(direct_intake.get('missing_files', []))}"
            ),
            "gap": "Direct row-intake files remain missing for positives, matched negatives, and provenance.",
        },
        {
            "id": "R7",
            "requirement": "No proxy/generated/OHLCV-only/HMM/future-return labels are promoted.",
            "status": "pass_guardrail",
            "artifact": ";".join(str(path) for path in ARTIFACTS.values()),
            "evidence": "Latest source screens and native sub-hour recheck explicitly fail-closed generated/model-derived, raw-panel, synthetic, bot, and method-code surfaces.",
            "gap": "",
        },
        {
            "id": "R8",
            "requirement": "Goal can be marked complete only if every strict requirement is covered by real artifacts.",
            "status": "fail_blocked",
            "artifact": str(RUN_ROOT),
            "evidence": "Checklist contains fail_blocked items R2, R3, R4, R5, and R6.",
            "gap": "Strict full objective is not achieved; update_goal must remain false.",
        },
    ]

    failed = [row for row in checklist if row["status"].startswith("fail")]
    summary = {
        "audit_started_at": datetime.now(timezone.utc).isoformat(),
        "objective": "Every regime reaches calibrated >=95% confidence and also validates with suitable confidence on other markets/species and other cycles/timeframes.",
        "artifacts_checked": {name: str(path) for name, path in ARTIFACTS.items()},
        "checklist_rows": len(checklist),
        "failed_rows": len(failed),
        "failed_ids": [row["id"] for row in failed],
        "decision": "current_goal_completion_audit_v24=latest_source_rechecks_confirm_full_objective_blocked",
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    checklist_csv = OUT_DIR / "current_goal_completion_audit_v24_checklist.csv"
    with checklist_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["id", "requirement", "status", "artifact", "evidence", "gap"],
        )
        writer.writeheader()
        writer.writerows(checklist)

    unmet_csv = OUT_DIR / "current_goal_completion_audit_v24_unmet_requirements.csv"
    with unmet_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["id", "requirement", "status", "artifact", "evidence", "gap"],
        )
        writer.writeheader()
        writer.writerows(failed)

    json_path = OUT_DIR / "current_goal_completion_audit_v24_after_source_rechecks.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    report = [
        "# Current Goal Completion Audit v24 After Source Rechecks",
        "",
        f"- Decision: `{summary['decision']}`",
        f"- Checklist rows: `{len(checklist)}`",
        f"- Failed rows: `{len(failed)}`",
        f"- Failed ids: `{', '.join(summary['failed_ids'])}`",
        "- Accepted rows added: `0`",
        "- New confidence gate: `false`",
        "- Strict full objective achieved: `false`; `update_goal=false`",
        "",
        "Strict blockers still open:",
    ]
    for row in failed:
        report.append(f"- `{row['id']}` {row['requirement']} {row['gap']}")
    (OUT_DIR / "current_goal_completion_audit_v24_after_source_rechecks.md").write_text(
        "\n".join(report) + "\n"
    )

    assertions = [
        f"decision={summary['decision']}",
        f"checklist_rows={len(checklist)}",
        f"failed_rows={len(failed)}",
        f"failed_ids={','.join(summary['failed_ids'])}",
        "strict_full_objective_achieved=false",
        "update_goal=false",
    ]
    (CHECK_DIR / "current_goal_completion_audit_v24_after_source_rechecks_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
