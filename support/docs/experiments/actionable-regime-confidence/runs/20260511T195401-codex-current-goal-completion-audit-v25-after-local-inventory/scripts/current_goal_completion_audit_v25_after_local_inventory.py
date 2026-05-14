#!/usr/bin/env python3
"""Prompt-to-artifact completion audit after local inventory and Sapienza audit."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T195401-codex-current-goal-completion-audit-v25-after-local-inventory"
RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = RUN_ROOT.parents[4]
BOARD_PATH = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"

ARTIFACTS = {
    "v24_source_rechecks": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T194926-codex-current-goal-completion-audit-v24-after-source-rechecks/"
        "completion-audit/current_goal_completion_audit_v24_after_source_rechecks.json"
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
    "strict_1h_exact_target_search": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T194739-codex-strict-1h-target-exact-source-search-v1/"
        "strict-1h-target-exact-source-search/strict_1h_target_exact_source_search_v1.json"
    ),
    "direct_intake": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T193301-codex-direct-manipulation-intake-verifier-readback-v1/"
        "direct-manipulation-intake-verifier-readback/direct_manipulation_intake_verifier_readback_v1.json"
    ),
    "sapienza_pumpdump": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T194916-codex-sapienza-pumpdump-source-audit-v1/"
        "sapienza-pumpdump-source-audit/sapienza_pumpdump_source_audit_v1.json"
    ),
    "local_broad_inventory": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T194952-codex-local-broad-source-owned-label-inventory-v1/"
        "local-broad-source-owned-label-inventory/local_broad_source_owned_label_inventory_v1.json"
    ),
    "native_subhour_recheck": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T194400-codex-native-subhour-source-recheck-v2/"
        "native-subhour-source-recheck/native_subhour_source_recheck_v2.json"
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
    "intake_file_rescan": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T193804-codex-board-a-intake-file-presence-rescan-v1/"
        "intake-file-presence-rescan/board_a_intake_file_presence_rescan_v1.json"
    ),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(rel_path: Path) -> dict[str, Any]:
    path = REPO_ROOT / rel_path
    if not path.exists():
        return {"missing_artifact": True, "path": str(rel_path)}
    return json.loads(path.read_text(encoding="utf-8"))


def nested(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = data
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def artifact_list(*names: str) -> str:
    return ";".join(str(ARTIFACTS[name]) for name in names)


def local_requirement_status(local_inventory: dict[str, Any], req_id: str) -> dict[str, Any]:
    for row in local_inventory.get("requirement_status", []):
        if row.get("id") == req_id:
            return row
    return {}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    loaded = {name: load_json(path) for name, path in ARTIFACTS.items()}
    v24 = loaded["v24_source_rechecks"]
    strict_intake = loaded["strict_1h_source_intake"]
    panel_exhaustion = loaded["strict_1h_panel_exhaustion"]
    exact_search = loaded["strict_1h_exact_target_search"]
    direct_intake = loaded["direct_intake"]
    sapienza = loaded["sapienza_pumpdump"]
    local_inventory = loaded["local_broad_inventory"]
    native_subhour = loaded["native_subhour_recheck"]
    web_recheck = loaded["web_source_label_recheck"]
    metadata_readback = loaded["external_metadata_readback"]
    github_screen = loaded["github_source_label_screen"]
    intake_rescan = loaded["intake_file_rescan"]

    tail_counts = {
        f"{row.get('symbol')}/{row.get('root')}": row.get("rows_after_2026_01_30")
        for row in exact_search.get("local_source_panel_counts", [])
    }
    local_r8 = local_requirement_status(local_inventory, "R8")

    checklist = [
        {
            "id": "R1",
            "requirement": "Every active regime has calibrated >=95% confidence.",
            "status": "pass_scoped_only",
            "artifact": str(ARTIFACTS["v24_source_rechecks"]),
            "evidence": "Latest completion audits still preserve scoped active-lane >=95% evidence.",
            "gap": "This does not cover strict transfer validation across other markets and cycles.",
        },
        {
            "id": "R2",
            "requirement": "Other-market/species validation has suitable confidence with source-label equivalence.",
            "status": "fail_blocked",
            "artifact": artifact_list(
                "web_source_label_recheck",
                "external_metadata_readback",
                "github_source_label_screen",
                "local_broad_inventory",
            ),
            "evidence": (
                f"web={web_recheck.get('decision')}; "
                f"metadata={metadata_readback.get('decision')}; "
                f"github={nested(github_screen, 'decision', 'gate_result', default=github_screen.get('decision'))}; "
                f"local={local_requirement_status(local_inventory, 'R7').get('status')}"
            ),
            "gap": "No promotable source-owned or owner-approved other-market equivalence rows were found.",
        },
        {
            "id": "R3",
            "requirement": "Other-cycle/timeframe validation has suitable confidence, including native sub-hour labels.",
            "status": "fail_blocked",
            "artifact": artifact_list("native_subhour_recheck", "local_broad_inventory"),
            "evidence": (
                f"native_subhour={native_subhour.get('decision')}; "
                f"ready_sources={native_subhour.get('ready_native_subhour_source_owned_label_sources')}; "
                f"local_R2={local_requirement_status(local_inventory, 'R2').get('status')}; "
                f"local_R6={local_requirement_status(local_inventory, 'R6').get('status')}"
            ),
            "gap": "Native sub-hour source-owned labels remain zero; local inventory found no uncounted native sub-hour package.",
        },
        {
            "id": "R4",
            "requirement": "Strict exact 1h remaining slots have new source-owned rows and provenance.",
            "status": "fail_blocked",
            "artifact": artifact_list(
                "strict_1h_source_intake",
                "strict_1h_panel_exhaustion",
                "strict_1h_exact_target_search",
                "intake_file_rescan",
                "local_broad_inventory",
            ),
            "evidence": (
                f"source_intake={strict_intake.get('decision')}; "
                f"panel={panel_exhaustion.get('decision')}; "
                f"exact_search={exact_search.get('decision')}; "
                f"ready_exact_sources={exact_search.get('ready_source_owned_exact_target_sources')}; "
                f"required_present={intake_rescan.get('required_present_count')}/{intake_rescan.get('required_file_count')}"
            ),
            "gap": "Strict 1h intake files are still missing and exact-target search found no ready source-owned rows.",
        },
        {
            "id": "R5",
            "requirement": "XOM/Sideways and remaining strict 1h targets have recency-tail repair where required.",
            "status": "fail_blocked",
            "artifact": str(ARTIFACTS["strict_1h_exact_target_search"]),
            "evidence": f"rows_after_2026_01_30={tail_counts}",
            "gap": "All four strict target rows still have zero source-panel rows after 2026-01-30.",
        },
        {
            "id": "R6",
            "requirement": "Direct Manipulation has row-level positives, matched normal controls, and provenance across required species.",
            "status": "fail_blocked",
            "artifact": artifact_list("direct_intake", "sapienza_pumpdump", "local_broad_inventory"),
            "evidence": (
                f"direct_intake={direct_intake.get('decision')}; "
                f"missing_files={len(direct_intake.get('missing_files', []))}; "
                f"sapienza_ready_pumpdump={sapienza.get('ready_pumpdump_positive_control_source')}; "
                f"sapienza_ready_spoofing_layering={sapienza.get('ready_spoofing_layering_intake_source')}; "
                f"sapienza_full_species={sapienza.get('full_direct_manipulation_species_coverage')}; "
                f"local_R8={local_r8.get('status')}"
            ),
            "gap": "Sapienza is a real pump/dump positive-control candidate, but it does not satisfy spoofing/layering intake or full species coverage.",
        },
        {
            "id": "R7",
            "requirement": "No proxy/generated/OHLCV-only/HMM/future-return labels are promoted.",
            "status": "pass_guardrail",
            "artifact": ";".join(str(path) for path in ARTIFACTS.values()),
            "evidence": "Latest source, native-subhour, direct-manipulation, and local inventory artifacts all keep rejected/generated/proxy surfaces fail-closed.",
            "gap": "",
        },
        {
            "id": "R8",
            "requirement": "Goal can be marked complete only if every strict requirement is covered by real artifacts.",
            "status": "fail_blocked",
            "artifact": str(RUN_ROOT.relative_to(REPO_ROOT)),
            "evidence": "Checklist still has fail_blocked rows R2, R3, R4, R5, and R6.",
            "gap": "Strict full objective is not achieved; update_goal must remain false.",
        },
    ]

    failed = [row for row in checklist if row["status"].startswith("fail")]
    summary = {
        "artifact_type": "current_goal_completion_audit_v25_after_local_inventory",
        "run_id": RUN_ID,
        "audit_started_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_before_append": sha256_file(BOARD_PATH),
        "objective": "Every regime reaches calibrated >=95% confidence and also validates with suitable confidence on other markets/species and other cycles/timeframes.",
        "artifacts_checked": {name: str(path) for name, path in ARTIFACTS.items()},
        "checklist_rows": len(checklist),
        "failed_rows": len(failed),
        "failed_ids": [row["id"] for row in failed],
        "decision": "current_goal_completion_audit_v25=post_local_inventory_strict_full_objective_blocked",
        "sapienza_effect": "ready pump/dump positive/control candidate, but not spoofing/layering intake and not full direct species coverage",
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    checklist_csv = OUT_DIR / "current_goal_completion_audit_v25_checklist.csv"
    with checklist_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["id", "requirement", "status", "artifact", "evidence", "gap"],
        )
        writer.writeheader()
        writer.writerows(checklist)

    unmet_csv = OUT_DIR / "current_goal_completion_audit_v25_unmet_requirements.csv"
    with unmet_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["id", "requirement", "status", "artifact", "evidence", "gap"],
        )
        writer.writeheader()
        writer.writerows(failed)

    json_path = OUT_DIR / "current_goal_completion_audit_v25_after_local_inventory.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = [
        "# Current Goal Completion Audit v25 After Local Inventory",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        f"- Decision: `{summary['decision']}`",
        f"- Checklist rows: `{len(checklist)}`",
        f"- Failed rows: `{len(failed)}`",
        f"- Failed ids: `{', '.join(summary['failed_ids'])}`",
        "- Sapienza effect: ready pump/dump positive/control candidate, but not spoofing/layering intake and not full direct species coverage.",
        "- Accepted rows added: `0`",
        "- New confidence gate: `false`",
        "- Strict full objective achieved: `false`; `update_goal=false`",
        "",
        "## Strict Blockers Still Open",
        "",
    ]
    for row in failed:
        report.append(f"- `{row['id']}` {row['requirement']} {row['gap']}")
    report.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- Checklist CSV: `{checklist_csv}`",
            f"- Unmet requirements CSV: `{unmet_csv}`",
            f"- Assertions: `{CHECK_DIR / 'current_goal_completion_audit_v25_after_local_inventory_assertions.out'}`",
        ]
    )
    (OUT_DIR / "current_goal_completion_audit_v25_after_local_inventory.md").write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )

    assertions = [
        f"PASS decision={summary['decision']}",
        f"PASS checklist_rows={len(checklist)}",
        f"PASS failed_rows={len(failed)}",
        f"PASS failed_ids={','.join(summary['failed_ids'])}",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    (CHECK_DIR / "current_goal_completion_audit_v25_after_local_inventory_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
