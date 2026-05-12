#!/usr/bin/env python3
"""Board A latest completion audit after 075426.

Read-only prompt-to-artifact audit over the latest settled source/control
artifacts. This script does not derive labels, mutate target roots, or promote
downstream runtime evidence.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


RUN_ID = "20260512T075814+0800-codex-board-a-latest-completion-audit-after-075426-v1"
GATE = "board_a_latest_completion_audit_after_075426_v1=not_complete_latest_inventory_no_required_unlock"

SCRIPT = Path(__file__).resolve()
RUN_ROOT = SCRIPT.parents[1]
REPO = RUN_ROOT.parents[4]
OUT = RUN_ROOT / "board-a-latest-completion-audit-after-075426-v1"
CHECKS = RUN_ROOT / "checks"
RUNS = REPO / "docs/experiments/actionable-regime-confidence/runs"
BOARD_A = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
BOARD_B = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"

EVIDENCE = {
    "audit_075413": RUNS / "20260512T075413+0800-codex-board-a-latest-completion-audit-after-075009-v1/checks/board_a_latest_completion_audit_after_075009_v1_assertions.out",
    "tomac_075411": RUNS / "20260512T075411+0800-codex-tomac-local-source-label-sidecar-scan-after-074844-v1/checks/tomac_local_source_label_sidecar_scan_after_074844_v1_assertions.out",
    "provider_cache_075420": RUNS / "20260512T075420+0800-codex-provider-cache-source-control-sweep-after-075206-v1/checks/provider_cache_source_control_sweep_after_075206_v1_assertions.out",
    "local_download_075426": RUNS / "20260512T075426+0800-codex-local-download-arrival-sweep-after-075009-v1/checks/local_download_arrival_sweep_after_075009_v1_assertions.out",
}

REPORTS = {
    "audit_075413": RUNS / "20260512T075413+0800-codex-board-a-latest-completion-audit-after-075009-v1/board-a-latest-completion-audit-after-075009-v1/board_a_latest_completion_audit_after_075009_v1.md",
    "tomac_075411": RUNS / "20260512T075411+0800-codex-tomac-local-source-label-sidecar-scan-after-074844-v1/tomac-local-source-label-sidecar-scan-after-074844-v1/tomac_local_source_label_sidecar_scan_after_074844_v1.md",
    "provider_cache_075420": RUNS / "20260512T075420+0800-codex-provider-cache-source-control-sweep-after-075206-v1/provider-cache-source-control-sweep-after-075206-v1/provider_cache_source_control_sweep_after_075206_v1.md",
    "local_download_075426": RUNS / "20260512T075426+0800-codex-local-download-arrival-sweep-after-075009-v1/local-download-arrival-sweep-after-075009-v1/local_download_arrival_sweep_after_075009_v1.md",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def parse_assertions(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith("PASS "):
            out["pass_marker"] = line.removeprefix("PASS ").strip()
        elif "=" in line:
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def is_true(value: str | None) -> bool:
    return str(value).strip().lower() == "true"


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def checklist_row(requirement: str, status: str, evidence: str, blocker: str) -> dict[str, str]:
    return {
        "requirement": requirement,
        "status": status,
        "evidence": evidence,
        "blocker": blocker,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    parsed = {name: parse_assertions(path) for name, path in EVIDENCE.items()}
    missing = [rel(path) for path in [*EVIDENCE.values(), *REPORTS.values()] if not path.exists()]
    if missing:
        raise FileNotFoundError("\n".join(missing))

    board_a_hash = sha256(BOARD_A)
    board_b_hash = sha256(BOARD_B)
    any_unlock = any(
        is_true(values.get(key))
        for values in parsed.values()
        for key in (
            "valid_required_root_unlock",
            "source_control_evidence_acquired",
            "r6_owner_export_unlock",
            "r5_recency_unlock",
            "r3_native_subhour_unlock",
            "r6_owner_export_complete",
            "r5_recency_root_present",
        )
    )
    any_promotion = any(
        is_true(values.get(key))
        for values in parsed.values()
        for key in (
            "canonical_merge",
            "selected_data_autoquant_promotion",
            "downstream_promotion_rerun",
            "strict_full_objective",
            "trade_usable",
            "update_goal",
        )
    )

    checklist = [
        checklist_row(
            "Read latest Board A contract",
            "pass",
            f"{rel(BOARD_A)} sha256={board_a_hash}",
            "",
        ),
        checklist_row(
            "Count 075413 latest audit once",
            "pass_fail_closed",
            parsed["audit_075413"].get("gate_result", ""),
            "075413 remains not complete with blocked requirements and no required-root unlock.",
        ),
        checklist_row(
            "Count 075411 Tomac sidecar scan once",
            "pass_fail_closed",
            parsed["tomac_075411"].get("gate_result", ""),
            "No source-label or control sidecar; no accepted rows.",
        ),
        checklist_row(
            "Count 075420 provider/cache sweep once",
            "pass_fail_closed",
            parsed["provider_cache_075420"].get("gate_result", ""),
            "Provider/cache inventory yielded no valid required root.",
        ),
        checklist_row(
            "Count 075426 local/download arrival sweep once",
            "pass_fail_closed",
            parsed["local_download_075426"].get("gate_result", ""),
            "Local/download candidates were not source labels or order-lifecycle controls.",
        ),
        checklist_row(
            "Do not promote proxy evidence",
            "pass_fail_closed",
            "TSIE-derived R3, raw OHLCV, provider/cache inventory, local downloads, and runtime readiness remain non-promoting.",
            "R6 owner/export, R5 source-panel recency, and verifier-native Crisis-capable R3 roots are still absent or quarantined.",
        ),
        checklist_row(
            "Do not run blocked downstream chain",
            "pass",
            "No direct verifier, split calibration, canonical merge, selected-data AutoQuant, Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion was run by this audit.",
            "",
        ),
        checklist_row(
            "Completion objective",
            "blocked",
            "accepted_rows_added=0; valid_required_root_unlock=false; source_control_evidence_acquired=false; strict_full_objective=false; update_goal=false",
            "Continue source/control acquisition only.",
        ),
    ]

    result = {
        "run_id": RUN_ID,
        "gate_result": GATE,
        "board_a_sha256": board_a_hash,
        "board_b_sha256": board_b_hash,
        "evidence_assertions": {name: rel(path) for name, path in EVIDENCE.items()},
        "evidence_reports": {name: rel(path) for name, path in REPORTS.items()},
        "parsed_assertions": parsed,
        "checklist": checklist,
        "accepted_rows_added": 0,
        "r6_owner_export_unlock": False,
        "r5_recency_unlock": False,
        "r3_native_subhour_unlock": False,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
    }

    json_path = OUT / "board_a_latest_completion_audit_after_075426_v1.json"
    csv_path = OUT / "prompt_to_artifact_checklist_after_075426_v1.csv"
    md_path = OUT / "board_a_latest_completion_audit_after_075426_v1.md"
    assertions_path = CHECKS / "board_a_latest_completion_audit_after_075426_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(checklist[0].keys()))
        writer.writeheader()
        writer.writerows(checklist)

    lines = [
        "# Board A Latest Completion Audit After 075426 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE}`",
        "",
        "## Scope",
        "",
        "Read-only prompt-to-artifact audit after the latest settled `075411`, `075420`, and `075426` source/control inventory artifacts. This audit does not mutate target roots, derive labels, approve controls, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.",
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence | Blocker |",
        "|---|---|---|---|",
    ]
    for item in checklist:
        lines.append(f"| {item['requirement']} | `{item['status']}` | {item['evidence']} | {item['blocker']} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- `075413` remains not complete after `075009`.",
            "- `075411` found no Tomac local source-label or control sidecar unlock.",
            "- `075420` scanned provider/cache roots with candidate hits but no valid required root.",
            "- `075426` scanned local/download arrivals and found only non-promoting Databento-check output candidates.",
            "- Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.",
            "",
            "## Next",
            "",
            "Continue source/control acquisition only before any direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines))

    checks = [
        f"gate_result={GATE}",
        "count_once_075411=true",
        "count_once_075420=true",
        "count_once_075426=true",
        "accepted_rows_added=0",
        "r6_owner_export_unlock=false",
        "r5_recency_unlock=false",
        "r3_native_subhour_unlock=false",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "promotion_allowed=false",
        "update_goal=false",
    ]
    if any_unlock or any_promotion:
        assertions_path.write_text("FAIL unexpected unlock_or_promotion_token=true\n")
        return 1
    assertions_path.write_text("\n".join(checks) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
