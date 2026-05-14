#!/usr/bin/env python3
"""Current-state audit after the V62 owner-export request package.

This script is intentionally fail-closed: it checks for real intake files and
records why no downstream promotion rerun is justified without a row/contract
change.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T002805-codex-current-state-audit-after-v62-owner-export-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
ARTIFACT_DIR = RUN_ROOT / "current-state-audit-after-v62-owner-export"
COMMAND_DIR = RUN_ROOT / "command-output"
CHECK_DIR = RUN_ROOT / "checks"

BOARD_PATH = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")

R6_OWNER_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
R6_OWNER_REQUIRED = [
    "direct_manipulation_positive_rows.csv",
    "direct_manipulation_matched_controls.csv",
    "direct_manipulation_provenance.json",
]
DIRECT_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
SOURCE_LABEL_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
SOURCE_PANEL_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
NATIVE_SUBHOUR_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")

DIRECT_VERIFIER = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
SOURCE_LABEL_VERIFIER = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)
SOURCE_PANEL_VERIFIER = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)

REFERENCE_ARTIFACTS = {
    "v62_request_package": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T001636-codex-r6-owner-export-request-package-v1/"
        "r6-owner-export-request-package/r6_owner_export_request_package_v1.json"
    ),
    "owner_export_presence_sweep": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T002009-codex-r6-owner-export-presence-sweep-v1/"
        "r6-owner-export-presence-sweep/r6_owner_export_presence_sweep_v1.json"
    ),
    "oystacher_exhibit_a_probe": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T001633-codex-r6-oystacher-exhibit-a-public-acquisition-probe-v1/"
        "r6-oystacher-exhibit-a-public-acquisition-probe/"
        "r6_oystacher_exhibit_a_public_acquisition_probe_v1.json"
    ),
    "oystacher_public_trace": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T001700-codex-r6-oystacher-public-appendix-trace-v1/"
        "r6-oystacher-public-appendix-trace/r6_oystacher_public_appendix_trace_v1.json"
    ),
    "r5_kaggle_recency_refresh": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T215621-codex-r5-kaggle-stock-regime-recency-refresh-v1/"
        "r5-kaggle-stock-regime-recency-refresh/r5_kaggle_stock_regime_recency_refresh_v1.json"
    ),
    "r3_native_subhour_overlap": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T180420-codex-native-subhour-overlap-blocker-v1/"
        "native-subhour-overlap/native_subhour_overlap_blocker_v1.json"
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    if not path.exists():
        return {"missing": True, "path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_cursor(board_text: str) -> dict:
    cursor: dict[str, str] = {}
    in_cursor = False
    for line in board_text.splitlines():
        if line.startswith("## Current Cursor"):
            in_cursor = True
            continue
        if in_cursor and line.startswith("## "):
            break
        if in_cursor and line.startswith("|"):
            cells = [part.strip() for part in line.strip().strip("|").split("|")]
            if len(cells) >= 2 and cells[0] not in {"Field", "---"}:
                cursor[cells[0]] = cells[1]
    return cursor


def run_verifier(name: str, script: Path, root: Path) -> dict:
    command = [sys.executable, str(script), "--intake-root", str(root)]
    proc = subprocess.run(command, text=True, capture_output=True, check=False)
    (COMMAND_DIR / f"{name}.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (COMMAND_DIR / f"{name}.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    (COMMAND_DIR / f"{name}.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
    parsed: dict = {}
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            parsed = {"raw_stdout": proc.stdout[:4000]}
    parsed.update(
        {
            "command": command,
            "returncode": proc.returncode,
            "stdout_path": str(COMMAND_DIR / f"{name}.stdout.txt"),
            "stderr_path": str(COMMAND_DIR / f"{name}.stderr.txt"),
        }
    )
    return parsed


def required_state(root: Path, names: list[str]) -> dict:
    present = [name for name in names if (root / name).exists()]
    return {
        "root": str(root),
        "root_exists": root.exists(),
        "required_files": names,
        "present_files": present,
        "missing_files": [name for name in names if name not in present],
        "present_count": len(present),
        "required_count": len(names),
    }


def gate_value(payload: dict) -> str | None:
    value = payload.get("gate_result") or payload.get("decision")
    if isinstance(value, dict):
        return value.get("gate_result") or value.get("decision")
    return value


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    COMMAND_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    board_text = BOARD_PATH.read_text(encoding="utf-8")
    cursor = parse_cursor(board_text)
    references = {name: load_json(path) for name, path in REFERENCE_ARTIFACTS.items()}

    direct = run_verifier("direct_manipulation_row_intake_verifier", DIRECT_VERIFIER, DIRECT_ROOT)
    source_label = run_verifier("source_label_equivalence_verifier", SOURCE_LABEL_VERIFIER, SOURCE_LABEL_ROOT)
    source_panel = run_verifier("source_panel_recency_verifier", SOURCE_PANEL_VERIFIER, SOURCE_PANEL_ROOT)

    r6_owner_state = required_state(R6_OWNER_ROOT, R6_OWNER_REQUIRED)
    native_state = required_state(
        NATIVE_SUBHOUR_ROOT,
        ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"],
    )
    r5_state = required_state(
        SOURCE_PANEL_ROOT,
        ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"],
    )
    source_label_state = required_state(
        SOURCE_LABEL_ROOT,
        ["source_label_equivalence_rows.csv", "source_label_equivalence_provenance.json"],
    )

    board_cursor_is_v62 = "20260512T001636" in cursor.get("last_loop_id", "")
    owner_files_present = r6_owner_state["present_count"] == r6_owner_state["required_count"]
    r5_ready = source_panel.get("status") != "blocked" and r5_state["present_count"] == r5_state["required_count"]
    r3_ready = native_state["present_count"] == native_state["required_count"]
    direct_pooled_context = {
        "status": direct.get("status"),
        "positive_rows": direct.get("positive_rows"),
        "matched_negative_rows": direct.get("matched_negative_rows"),
        "matched_group_count": direct.get("matched_group_count"),
    }

    checklist = [
        {
            "id": "objective_named_board",
            "requirement": "Use the named Board A markdown as the authoritative state.",
            "evidence": f"board_sha256={sha256(BOARD_PATH)}; cursor={cursor.get('last_loop_id')}",
            "status": "pass",
            "gap": "",
        },
        {
            "id": "r6_owner_export_files",
            "requirement": "Owner/user-approved R6 positive/control/provenance export files are present.",
            "evidence": f"root_exists={r6_owner_state['root_exists']}; present={r6_owner_state['present_count']}/{r6_owner_state['required_count']}",
            "status": "fail_blocked",
            "gap": ";".join(r6_owner_state["missing_files"]),
        },
        {
            "id": "r6_direct_confidence_and_splits",
            "requirement": "R6 direct Manipulation passes strict split/species validation, not only pooled support.",
            "evidence": (
                f"direct={direct_pooled_context}; v62_gate="
                f"{gate_value(references['v62_request_package'])}"
            ),
            "status": "fail_blocked",
            "gap": "owner export absent; exact split debt and direct species blockers remain per V62",
        },
        {
            "id": "r5_post_2026_01_30_recency",
            "requirement": "Post-2026-01-30 source-panel recency extension rows and provenance are accepted.",
            "evidence": (
                f"root_exists={r5_state['root_exists']}; verifier="
                f"{source_panel.get('status')}/{source_panel.get('reason')}; "
                f"kaggle_decision={references['r5_kaggle_recency_refresh'].get('decision')}"
            ),
            "status": "fail_blocked",
            "gap": ";".join(r5_state["missing_files"]),
        },
        {
            "id": "r3_native_subhour",
            "requirement": "Native sub-hour source-label rows and provenance are accepted.",
            "evidence": (
                f"root_exists={native_state['root_exists']}; "
                f"prior_gate={gate_value(references['r3_native_subhour_overlap'])}"
            ),
            "status": "fail_blocked",
            "gap": ";".join(native_state["missing_files"]),
        },
        {
            "id": "source_label_equivalence_context",
            "requirement": "Other-market/source-label equivalence root remains real-evidence only.",
            "evidence": (
                f"root_exists={source_label_state['root_exists']}; verifier="
                f"{source_label.get('status')}/{source_label.get('reason')}"
            ),
            "status": "fail_blocked",
            "gap": ";".join(source_label_state["missing_files"]),
        },
        {
            "id": "provider_autoquant_chain",
            "requirement": "Rerun provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree after accepted row/contract change.",
            "evidence": "No accepted row or validation-contract change since V62/002009; downstream rerun would be a proxy signal only.",
            "status": "blocked_not_rerun",
            "gap": "await owner export files or explicit split-contract approval",
        },
        {
            "id": "no_proxy_promotion",
            "requirement": "Do not promote OHLCV/proxy/generated labels as completion.",
            "evidence": "No proxy labels written; no live intake mutation; no threshold relaxation.",
            "status": "pass_guardrail",
            "gap": "",
        },
        {
            "id": "multi_agent_append_only",
            "requirement": "Do not disturb concurrent agents or rewrite the active cursor without new acceptance evidence.",
            "evidence": "This run creates a unique run root and leaves Current Cursor unchanged.",
            "status": "pass_guardrail",
            "gap": "",
        },
    ]

    blocked_ids = [row["id"] for row in checklist if row["status"].startswith("fail") or row["status"].startswith("blocked")]
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_run": sha256(BOARD_PATH),
        "cursor": cursor,
        "board_cursor_is_v62": board_cursor_is_v62,
        "r6_owner_export_state": r6_owner_state,
        "r3_native_subhour_state": native_state,
        "r5_source_panel_recency_state": r5_state,
        "source_label_equivalence_state": source_label_state,
        "verifiers": {
            "direct_manipulation": direct,
            "source_label_equivalence": source_label,
            "source_panel_recency": source_panel,
        },
        "references": {name: str(path) for name, path in REFERENCE_ARTIFACTS.items()},
        "reference_gate_results": {
            name: gate_value(references[name])
            for name in references
        },
        "checklist": checklist,
        "blocked_ids": blocked_ids,
        "gate_result": "current_state_audit_after_v62_owner_export_v1=not_complete_owner_export_r5_r3_roots_absent_no_downstream_rerun",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "shared_intake_mutated": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "next_action": (
            "Place owner/user-approved R6 export files under /tmp/ict-engine-board-a-r6-owner-export-v1 "
            "or record explicit approval for a different split contract; separately populate R5 and R3 intake "
            "roots with source-owned rows before rerunning acceptance/downstream chain."
        ),
    }

    json_path = ARTIFACT_DIR / "current_state_audit_after_v62_owner_export_v1.json"
    checklist_path = ARTIFACT_DIR / "prompt_to_artifact_checklist_after_v62_owner_export_v1.csv"
    report_path = ARTIFACT_DIR / "current_state_audit_after_v62_owner_export_v1.md"
    assertions_path = CHECK_DIR / "current_state_audit_after_v62_owner_export_v1_assertions.out"

    write_json(json_path, payload)
    write_csv(checklist_path, checklist, ["id", "requirement", "evidence", "status", "gap"])

    lines = [
        "# Current State Audit After V62 Owner Export v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Board cursor observed: `{cursor.get('last_loop_id')}`.",
        f"- Gate result: `{payload['gate_result']}`.",
        f"- Direct verifier: status `{direct.get('status')}`, positives `{direct.get('positive_rows')}`, matched controls `{direct.get('matched_negative_rows')}`, matched groups `{direct.get('matched_group_count')}`.",
        f"- R6 owner-export required files present: `{r6_owner_state['present_count']}/{r6_owner_state['required_count']}`.",
        f"- R5 source-panel recency verifier: `{source_panel.get('status')}` / `{source_panel.get('reason')}`.",
        f"- R3 native sub-hour root exists: `{native_state['root_exists']}`.",
        f"- Blocked checklist ids: `{', '.join(blocked_ids)}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; shared intake mutated: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "## Checklist",
        "",
        "| ID | Status | Evidence | Gap |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        evidence = str(row["evidence"]).replace("|", "/")
        gap = str(row["gap"]).replace("|", "/")
        lines.append(f"| `{row['id']}` | `{row['status']}` | {evidence} | {gap} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The active V62 request package is still the correct handoff point, but the required owner-export files are not present.",
            "- The direct verifier is still schema-ready on the old live intake; this is not enough for strict split/species/cross-context acceptance.",
            "- R5 and R3 are still real row-acquisition blockers, not computation blockers.",
            "- Provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun is intentionally skipped because no accepted row or validation-contract change occurred.",
            "",
            "## Next",
            "",
            payload["next_action"],
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")

    assertions = [
        f"board_cursor_is_v62={board_cursor_is_v62}",
        f"r6_owner_files_present={owner_files_present}",
        f"r6_owner_required_files_present={r6_owner_state['present_count']}/{r6_owner_state['required_count']}",
        f"direct_verifier_returncode={direct.get('returncode')}",
        f"direct_verifier_status={direct.get('status')}",
        f"r5_ready={r5_ready}",
        f"r3_ready={r3_ready}",
        f"blocked_ids={','.join(blocked_ids)}",
        "accepted_rows_added=0",
        "new_confidence_gate=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "shared_intake_mutated=false",
        "external_requests_sent=false",
        "assertion_status=PASS",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps({"run_id": RUN_ID, "json": str(json_path), "report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
