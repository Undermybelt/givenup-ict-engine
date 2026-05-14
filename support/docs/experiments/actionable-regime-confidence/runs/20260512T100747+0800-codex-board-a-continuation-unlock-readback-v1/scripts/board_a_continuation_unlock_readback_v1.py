#!/usr/bin/env python3
"""Board A continuation readback after the latest `continue` request."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260512T100747+0800-codex-board-a-continuation-unlock-readback-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
ARTIFACT_DIR = RUN_ROOT / "board-a-continuation-unlock-readback-v1"
CMD_DIR = RUN_ROOT / "command-output"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
ICT = REPO / "target/debug/ict-engine"
READY_AUTOQ_STATE = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T092832+0800-codex-board-b-aq-first-nursery-ltf-v1/"
    "state_b2r_nq_ltf_nursery_v1"
)
SELECTED_HISTORY_CSV = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T092249+0800-codex-selected-history-decision-request-after-091346-v1/"
    "selected-history-decision-request-after-091346-v1/"
    "selected_history_options_after_091346_v1.csv"
)

ROOTS = [
    {
        "id": "R6_owner_export",
        "path": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        "required_any_sets": [
            [
                "direct_manipulation_positive_rows.csv",
                "direct_manipulation_matched_controls.csv",
                "direct_manipulation_provenance.json",
            ],
            [
                "positive_spoofing_layering_rows.csv",
                "matched_negative_normal_activity_rows.csv",
                "provenance_manifest.json",
            ],
        ],
        "non_unlock_reason": "absent_or_missing_owner_export_positive_control_provenance_triplet",
    },
    {
        "id": "R5_source_panel_recency",
        "path": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required_any_sets": [
            ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"],
        ],
        "non_unlock_reason": "absent_or_missing_post_2026_01_30_source_panel_recency_package",
    },
    {
        "id": "R3_native_subhour",
        "path": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required_any_sets": [
            ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"],
        ],
        "non_unlock_reason": "present_but_tsie_quarantined_crisis_absent",
    },
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_command(name: str, cmd: list[str]) -> dict[str, object]:
    result = subprocess.run(
        cmd,
        cwd=str(REPO),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    (CMD_DIR / f"{name}.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (CMD_DIR / f"{name}.stderr.txt").write_text(result.stderr, encoding="utf-8")
    (CMD_DIR / f"{name}.exit").write_text(f"{result.returncode}\n", encoding="utf-8")
    parsed = {}
    try:
        parsed = json.loads(result.stdout)
    except Exception:
        parsed = {}
    return {
        "name": name,
        "cmd": " ".join(cmd),
        "exit_code": result.returncode,
        "stdout_path": str((CMD_DIR / f"{name}.stdout.txt").relative_to(REPO)),
        "stderr_path": str((CMD_DIR / f"{name}.stderr.txt").relative_to(REPO)),
        "parsed": parsed,
    }


def selected_history_status() -> dict[str, object]:
    rows = []
    if SELECTED_HISTORY_CSV.exists():
        with SELECTED_HISTORY_CSV.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    selected = [row["option"] for row in rows if row.get("selected", "").lower() == "true"]
    return {
        "options_file": str(SELECTED_HISTORY_CSV.relative_to(REPO)) if SELECTED_HISTORY_CSV.exists() else "",
        "options": rows,
        "selected": selected,
        "explicit_user_selected_history": len(selected) == 1,
    }


def root_status(root: dict[str, object]) -> dict[str, object]:
    path = root["path"]
    assert isinstance(path, Path)
    files = sorted([p.name for p in path.iterdir()]) if path.exists() else []
    required_sets = root["required_any_sets"]
    required_set_complete = False
    missing_by_set = []
    for required in required_sets:
        missing = [name for name in required if not (path / name).exists()]
        missing_by_set.append(";".join(missing))
        if not missing:
            required_set_complete = True

    provenance = {}
    for prov_name in [
        "native_subhour_source_label_provenance.json",
        "source_panel_recency_provenance.json",
        "direct_manipulation_provenance.json",
        "provenance_manifest.json",
    ]:
        candidate = path / prov_name
        if candidate.exists():
            provenance = read_json(candidate)
            break

    labels = provenance.get("accepted_mapping_confidence_95_labels") or []
    limitations = " ".join(provenance.get("limitations") or [])
    crisis_present = "Crisis" in labels
    tsie_quarantined = root["id"] == "R3_native_subhour" and (
        not crisis_present or "Crisis has no direct TSIE source taxonomy class" in limitations
    )
    valid_unlock = bool(required_set_complete and not tsie_quarantined and root["id"] != "R5_source_panel_recency")
    if root["id"] == "R5_source_panel_recency":
        valid_unlock = bool(required_set_complete)

    return {
        "id": root["id"],
        "path": str(path),
        "exists": path.exists(),
        "file_count": len(files),
        "files": ";".join(files),
        "required_set_complete": required_set_complete,
        "missing_by_set": "|".join(missing_by_set),
        "labels_from_provenance": ";".join(labels),
        "crisis_present": crisis_present,
        "tsie_quarantined": tsie_quarantined,
        "valid_required_unlock": valid_unlock,
        "reason": "valid_required_unlock" if valid_unlock else root["non_unlock_reason"],
    }


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    provider = run_command("provider_status_agent", [str(ICT), "provider-status", "--agent"])
    auto_quant_fresh = run_command(
        "auto_quant_status_fresh_isolated",
        [
            str(ICT),
            "auto-quant-status",
            "--state-dir",
            "/tmp/ict-engine-board-a-continuation-unlock-readback-v1",
            "--output-format",
            "agent",
        ],
    )
    auto_quant_ready = run_command(
        "auto_quant_status_existing_ready_state",
        [
            str(ICT),
            "auto-quant-status",
            "--state-dir",
            str(READY_AUTOQ_STATE.relative_to(REPO)),
            "--output-format",
            "agent",
        ],
    )
    roots = [root_status(root) for root in ROOTS]
    selection = selected_history_status()

    provider_parsed = provider.get("parsed") or {}
    auto_quant_fresh_parsed = auto_quant_fresh.get("parsed") or {}
    auto_quant_ready_parsed = auto_quant_ready.get("parsed") or {}
    r6 = next(row for row in roots if row["id"] == "R6_owner_export")
    r5 = next(row for row in roots if row["id"] == "R5_source_panel_recency")
    r3 = next(row for row in roots if row["id"] == "R3_native_subhour")
    valid_required_unlock = any(bool(row["valid_required_unlock"]) for row in roots)
    downstream_allowed = bool(valid_required_unlock and selection["explicit_user_selected_history"])

    checklist = [
        {
            "requirement": "R6 direct Manipulation source/control owner-export rows",
            "evidence": r6["path"],
            "status": "blocked",
            "gap": r6["reason"],
        },
        {
            "requirement": "R5 post-2026-01-30 source-panel recency package",
            "evidence": r5["path"],
            "status": "blocked",
            "gap": r5["reason"],
        },
        {
            "requirement": "R3 native sub-hour MainRegimeV2 labels including Crisis",
            "evidence": r3["path"],
            "status": "blocked",
            "gap": r3["reason"],
        },
        {
            "requirement": "Explicit selected-history choice",
            "evidence": selection["options_file"],
            "status": "blocked" if not selection["explicit_user_selected_history"] else "ready",
            "gap": "awaiting exactly one of HTF/MTF/LTF" if not selection["explicit_user_selected_history"] else "",
        },
        {
            "requirement": "Provider readback: IBKR, TradingViewRemix, yfinance, Kraken",
            "evidence": provider["stdout_path"],
            "status": "read_only_non_promoting",
            "gap": provider_parsed.get("summary_line", "provider output unparsed"),
        },
        {
            "requirement": "Auto-Quant readiness before selected-data promotion",
            "evidence": auto_quant_ready["stdout_path"],
            "status": "read_only_non_promoting",
            "gap": (
                f"existing_ready_state={auto_quant_ready_parsed.get('status', 'unparsed')}; "
                f"fresh_isolated={auto_quant_fresh_parsed.get('status', 'unparsed')}"
            ),
        },
        {
            "requirement": "Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost -> execution tree promotion rerun",
            "evidence": str(ARTIFACT_DIR.relative_to(REPO) / "board_a_continuation_unlock_readback_v1.json"),
            "status": "not_run",
            "gap": "blocked until required source/control unlock plus explicit selected-history choice",
        },
    ]

    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_at_run": sha256(BOARD),
        "provider_status": {
            "exit_code": provider["exit_code"],
            "summary_line": provider_parsed.get("summary_line"),
            "ready_by_domain": provider_parsed.get("ready_by_domain"),
            "ready_providers": provider_parsed.get("ready_providers"),
            "pending_providers": provider_parsed.get("pending_providers"),
        },
        "auto_quant_status": {
            "fresh_isolated": {
                "exit_code": auto_quant_fresh["exit_code"],
                "status": auto_quant_fresh_parsed.get("status"),
                "healthy": auto_quant_fresh_parsed.get("healthy"),
                "dependency_healthy": auto_quant_fresh_parsed.get("dependency_healthy"),
                "data_ready": auto_quant_fresh_parsed.get("data_ready"),
                "recommended_next_command": auto_quant_fresh_parsed.get("recommended_next_command"),
            },
            "existing_ready_state": {
                "exit_code": auto_quant_ready["exit_code"],
                "status": auto_quant_ready_parsed.get("status"),
                "healthy": auto_quant_ready_parsed.get("healthy"),
                "dependency_healthy": auto_quant_ready_parsed.get("dependency_healthy"),
                "data_ready": auto_quant_ready_parsed.get("data_ready"),
                "recommended_next_command": auto_quant_ready_parsed.get("recommended_next_command"),
            },
        },
        "source_control_roots": roots,
        "selected_history": selection,
        "decision": {
            "valid_required_root_unlock": valid_required_unlock,
            "explicit_user_selected_history": selection["explicit_user_selected_history"],
            "canonical_merge_allowed": False,
            "selected_data_autoquant_promotion_allowed": False,
            "downstream_promotion_rerun_allowed": downstream_allowed,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
            "gate_result": (
                "board_a_continuation_unlock_readback_v1="
                "no_required_root_unlock_no_selected_history_no_promotion"
            ),
        },
        "prompt_to_artifact_checklist": checklist,
        "next_action": (
            "Obtain a real R6/R5/R3 source-control unlock or explicit source/control approval, "
            "and provide exactly one selected-history choice (HTF, MTF, or LTF) before any canonical "
            "merge, selected-data Auto-Quant promotion, Pre-Bayes/BBN/CatBoost/path-ranking, "
            "execution-tree promotion, trade claim, or update_goal."
        ),
    }

    json_path = ARTIFACT_DIR / "board_a_continuation_unlock_readback_v1.json"
    md_path = ARTIFACT_DIR / "board_a_continuation_unlock_readback_v1.md"
    roots_csv = ARTIFACT_DIR / "source_control_root_status_v1.csv"
    checklist_csv = ARTIFACT_DIR / "prompt_to_artifact_checklist_v1.csv"
    assertions_path = CHECK_DIR / "board_a_continuation_unlock_readback_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(
        roots_csv,
        roots,
        [
            "id",
            "path",
            "exists",
            "file_count",
            "files",
            "required_set_complete",
            "missing_by_set",
            "labels_from_provenance",
            "crisis_present",
            "tsie_quarantined",
            "valid_required_unlock",
            "reason",
        ],
    )
    write_csv(checklist_csv, checklist, ["requirement", "evidence", "status", "gap"])

    md_lines = [
        "# Board A Continuation Unlock Readback v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Gate result: `board_a_continuation_unlock_readback_v1=no_required_root_unlock_no_selected_history_no_promotion`",
        "",
        "## Readback",
        "",
        f"- Provider status: `{provider_parsed.get('summary_line', 'unparsed')}`.",
        f"- Auto-Quant existing ready-state status: `{auto_quant_ready_parsed.get('status', 'unparsed')}`.",
        f"- Auto-Quant fresh isolated status: `{auto_quant_fresh_parsed.get('status', 'unparsed')}`.",
        f"- R6 owner-export root valid unlock: `{str(r6['valid_required_unlock']).lower()}`.",
        f"- R5 recency root valid unlock: `{str(r5['valid_required_unlock']).lower()}`.",
        f"- R3 native sub-hour valid unlock: `{str(r3['valid_required_unlock']).lower()}`; labels `{r3['labels_from_provenance']}`; Crisis present `{str(r3['crisis_present']).lower()}`.",
        f"- Explicit selected-history choice: `{str(selection['explicit_user_selected_history']).lower()}`.",
        "",
        "## Decision",
        "",
        "- Canonical merge allowed: `false`.",
        "- Selected-data Auto-Quant promotion allowed: `false`.",
        "- Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree promotion rerun allowed: `false`.",
        "- Strict full objective achieved: `false`.",
        "- Trade usable: `false`.",
        "- `update_goal=false`.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- Root status CSV: `{roots_csv.relative_to(REPO)}`",
        f"- Prompt-to-artifact checklist: `{checklist_csv.relative_to(REPO)}`",
        f"- Provider stdout: `{provider['stdout_path']}`",
        f"- Auto-Quant existing ready-state stdout: `{auto_quant_ready['stdout_path']}`",
        f"- Auto-Quant fresh isolated stdout: `{auto_quant_fresh['stdout_path']}`",
        f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        "",
        "## Next",
        "",
        payload["next_action"],
        "",
    ]
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    assertions = [
        f"gate_result={payload['decision']['gate_result']}",
        f"provider_exit={provider['exit_code']}",
        f"provider_summary={provider_parsed.get('summary_line')}",
        f"auto_quant_ready_exit={auto_quant_ready['exit_code']}",
        f"auto_quant_ready_status={auto_quant_ready_parsed.get('status')}",
        f"auto_quant_fresh_exit={auto_quant_fresh['exit_code']}",
        f"auto_quant_fresh_status={auto_quant_fresh_parsed.get('status')}",
        f"r6_valid_unlock={str(r6['valid_required_unlock']).lower()}",
        f"r5_valid_unlock={str(r5['valid_required_unlock']).lower()}",
        f"r3_valid_unlock={str(r3['valid_required_unlock']).lower()}",
        f"r3_crisis_present={str(r3['crisis_present']).lower()}",
        f"explicit_user_selected_history={str(selection['explicit_user_selected_history']).lower()}",
        "canonical_merge_allowed=false",
        "downstream_promotion_rerun_allowed=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
