#!/usr/bin/env python3
"""Board A current objective audit after the 071457/071316 source-control readbacks."""

from __future__ import annotations

import csv
import json
import subprocess
import time
from pathlib import Path
from typing import Any


RUN_ID = "20260512T071625+0800-codex-current-objective-audit-after-071457-v1"
GATE = (
    "current_objective_audit_after_071457_v1="
    "not_complete_required_roots_absent_no_downstream_promotion"
)
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
PACKET = RUN_ROOT / "current-objective-audit-after-071457-v1"
OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
STATE_DIR = Path("/tmp/ict-engine-board-a-064259-runtime-v1")

ROOTS = {
    "r6_owner_export": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r5_recency_extension": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "r3_native_subhour": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "source_label_equivalence": Path("/tmp/ict-engine-source-label-equivalence-intake"),
}

REFERENCED_RUNS = [
    "20260512T070842+0800-codex-current-goal-completion-audit-after-070531-v1",
    "20260512T071032+0800-codex-r3-label-count-readback-after-070434-v1",
    "20260512T071107+0800-codex-r6-order-lifecycle-local-scan-readback-after-070820-v1",
    "20260512T071316+0800-codex-local-order-lifecycle-depth-source-scan-after-070840-v1",
    "20260512T071346+0800-codex-r3-label-count-settled-readback-after-071032-v1",
]


def run_cmd(key: str, args: list[str], timeout: int = 120) -> dict[str, Any]:
    cmd_path = OUT / f"{key}.cmd"
    stdout_path = OUT / f"{key}.stdout"
    stderr_path = OUT / f"{key}.stderr"
    exit_path = OUT / f"{key}.exit"
    cmd_path.write_text(" ".join(args) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(
            args,
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        stdout_path.write_text(proc.stdout, encoding="utf-8")
        stderr_path.write_text(proc.stderr, encoding="utf-8")
        exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
        return {
            "key": key,
            "args": args,
            "returncode": proc.returncode,
            "timeout": False,
            "stdout_path": str(stdout_path.relative_to(REPO)),
            "stderr_path": str(stderr_path.relative_to(REPO)),
        }
    except subprocess.TimeoutExpired as exc:
        stdout_path.write_text(exc.stdout or "", encoding="utf-8")
        stderr_path.write_text(exc.stderr or "", encoding="utf-8")
        exit_path.write_text("timeout\n", encoding="utf-8")
        return {
            "key": key,
            "args": args,
            "returncode": None,
            "timeout": True,
            "stdout_path": str(stdout_path.relative_to(REPO)),
            "stderr_path": str(stderr_path.relative_to(REPO)),
        }


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def command_json(key: str) -> dict[str, Any]:
    return load_json(OUT / f"{key}.stdout")


def command_text(key: str) -> str:
    return load_text(OUT / f"{key}.stdout")


def root_status() -> list[dict[str, Any]]:
    required = {
        "r6_owner_export": [
            "direct_manipulation_positive_rows.csv",
            "direct_manipulation_matched_controls.csv",
            "direct_manipulation_provenance.json",
        ],
        "r5_recency_extension": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
        "r3_native_subhour": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
        "source_label_equivalence": [
            "source_label_equivalence_rows.csv",
            "source_label_equivalence_provenance.json",
        ],
    }
    rows = []
    for key, root in ROOTS.items():
        files = sorted(p.name for p in root.iterdir() if p.is_file()) if root.exists() else []
        present = {name: (root / name).exists() for name in required[key]}
        rows.append(
            {
                "id": key,
                "root": str(root),
                "exists": root.exists(),
                "file_count": len(files),
                "required_present": present,
                "physical_complete": all(present.values()),
                "accepted_for_promotion": False,
                "notes": root_notes(key, root.exists()),
                "files": ";".join(files[:20]),
            }
        )
    return rows


def root_notes(key: str, exists: bool) -> str:
    if key == "r6_owner_export":
        return "target root absent; no verifier-native owner/export positive/control/provenance files" if not exists else "requires owner/export controls and provenance"
    if key == "r5_recency_extension":
        return "target root absent; no source-owned post-2026-01-30 MainRegimeV2 rows" if not exists else "requires source-owned recency provenance"
    if key == "r3_native_subhour":
        return "present but TSIE-derived/quarantined and Crisis-absent per 071032/071346"
    return "present but non-target equivalence context; non-promoting"


def referenced_run_status() -> list[dict[str, Any]]:
    base = REPO / "docs/experiments/actionable-regime-confidence/runs"
    rows = []
    for run_id in REFERENCED_RUNS:
        root = base / run_id
        rows.append(
            {
                "run_id": run_id,
                "exists": root.exists(),
                "report_count": len(list(root.glob("**/*.md"))) if root.exists() else 0,
                "json_count": len(list(root.glob("**/*.json"))) if root.exists() else 0,
                "assertion_count": len(list(root.glob("**/*assertions.out"))) if root.exists() else 0,
                "status": "materialized" if root.exists() else "missing",
            }
        )
    return rows


def provider_summary() -> dict[str, Any]:
    data = command_json("provider_status_agent")
    return {
        "summary_line": data.get("summary_line", ""),
        "ready_by_domain": data.get("ready_by_domain", {}),
        "ready_providers": data.get("ready_providers", []),
        "pending_providers": data.get("pending_providers", []),
    }


def auto_quant_summary() -> dict[str, Any]:
    data = command_json("auto_quant_status")
    dep = data.get("dependency_status") or {}
    return {
        "status": data.get("status"),
        "healthy": data.get("healthy"),
        "dependency_healthy": data.get("dependency_healthy"),
        "data_ready": data.get("data_ready"),
        "bootstrap_needed": data.get("bootstrap_needed"),
        "current_commit": dep.get("current_commit"),
    }


def workflow_summary() -> dict[str, Any]:
    text = command_text("workflow_status_nq_agent")
    return {
        "contains_user_selected_historical_data_missing": "user_selected_historical_data_missing" in text,
        "contains_blocked": "blocked" in text.lower(),
        "first_lines": "\n".join(text.splitlines()[:24]),
    }


def path_ranking_summary() -> dict[str, Any]:
    text = command_text("export_structural_path_ranking_target_nq")
    summary_line = ""
    for line in text.splitlines():
        if "structural_path_ranking_target rows=" in line:
            summary_line = line
            break
    return {
        "summary_line": summary_line,
        "contains_mature_rows0": "mature_rows=0" in text,
        "contains_calibrated_rows0": "calibrated_rows=0" in text,
    }


def checklist(
    provider: dict[str, Any],
    auto_quant: dict[str, Any],
    workflow: dict[str, Any],
    path_ranking: dict[str, Any],
    roots: list[dict[str, Any]],
) -> list[dict[str, str]]:
    root_map = {row["id"]: row for row in roots}
    return [
        {
            "requirement": "Every regime reaches accepted 95%-99% confidence",
            "evidence": "No accepted verifier-native R3/R5/R6 source-control unlock exists; no new calibration packet can be promoted.",
            "status": "blocked",
        },
        {
            "requirement": "Each regime has cross-market, cross-period, and cross-timeframe validation",
            "evidence": "Latest accepted source-control roots are absent or non-promoting; cross-axis validation cannot be completed from proxy rows.",
            "status": "blocked",
        },
        {
            "requirement": "R3 native-subhour Crisis-capable MainRegimeV2 labels",
            "evidence": f"exists={root_map['r3_native_subhour']['exists']} notes={root_map['r3_native_subhour']['notes']}; 071032/071346 report Crisis=0.",
            "status": "blocked",
        },
        {
            "requirement": "R5 source-owned post-2026-01-30 MainRegimeV2 recency rows",
            "evidence": f"exists={root_map['r5_recency_extension']['exists']} file_count={root_map['r5_recency_extension']['file_count']}",
            "status": "blocked",
        },
        {
            "requirement": "R6 owner/export rows with valid normal controls and provenance",
            "evidence": f"exists={root_map['r6_owner_export']['exists']} file_count={root_map['r6_owner_export']['file_count']}; 071107/071316 found local code/OHLCV false positives only.",
            "status": "blocked",
        },
        {
            "requirement": "Real provider coverage for IBKR, TradingViewRemix, yfinance, and Kraken",
            "evidence": f"provider_summary={provider.get('summary_line')}; pending={len(provider.get('pending_providers', []))}",
            "status": "partial_non_promoting",
        },
        {
            "requirement": "Real Auto-Quant operation",
            "evidence": f"status={auto_quant.get('status')} data_ready={auto_quant.get('data_ready')}; selected-data promotion is blocked until source-control unlock.",
            "status": "partial_non_promoting",
        },
        {
            "requirement": "Filter / Pre-Bayes / BBN / CatBoost / path-ranking / execution-tree chain",
            "evidence": f"workflow_missing_selected_history={workflow.get('contains_user_selected_historical_data_missing')} path_ranking={path_ranking.get('summary_line')}",
            "status": "partial_non_promoting",
        },
        {
            "requirement": "Do not disturb concurrent Board A work",
            "evidence": "This audit writes a new run root only and requires append-only board registration.",
            "status": "pass",
        },
        {
            "requirement": "No proxy signals accepted as completion",
            "evidence": "OHLCV archives, source-code hits, public CFTC route context, TSIE rows, and binary NIFTY labels remain non-promoting.",
            "status": "pass",
        },
        {
            "requirement": "Completion / update_goal",
            "evidence": "Required roots and downstream promotion are absent; objective not achieved.",
            "status": "not_complete",
        },
    ]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> str:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return str(path.relative_to(REPO))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    PACKET.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    commands = [
        run_cmd("board_sha256_before", ["shasum", "-a", "256", str(BOARD.relative_to(REPO))]),
        run_cmd("git_status_short", ["git", "status", "--short"]),
        run_cmd("provider_status_agent", ["target/debug/ict-engine", "provider-status", "--agent"]),
        run_cmd(
            "auto_quant_status",
            [
                "target/debug/ict-engine",
                "auto-quant-status",
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
        ),
        run_cmd(
            "pre_bayes_status_nq",
            [
                "target/debug/ict-engine",
                "pre-bayes-status",
                "--symbol",
                "NQ",
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--output-format",
                "json",
            ],
        ),
        run_cmd(
            "workflow_status_nq_agent",
            [
                "target/debug/ict-engine",
                "workflow-status",
                "--symbol",
                "NQ",
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--agent",
            ],
        ),
        run_cmd(
            "export_structural_path_ranking_target_nq",
            [
                "target/debug/ict-engine",
                "export-structural-path-ranking-target",
                "--symbol",
                "NQ",
                "--state-dir",
                str(STATE_DIR),
            ],
        ),
    ]

    roots = root_status()
    referenced = referenced_run_status()
    provider = provider_summary()
    auto_quant = auto_quant_summary()
    workflow = workflow_summary()
    path_ranking = path_ranking_summary()
    checks = checklist(provider, auto_quant, workflow, path_ranking, roots)
    blocked = [row for row in checks if row["status"] in {"blocked", "not_complete"}]
    partial = [row for row in checks if row["status"] == "partial_non_promoting"]

    checklist_csv = write_csv(
        PACKET / "prompt_to_artifact_checklist_after_071457_v1.csv",
        checks,
        ["requirement", "evidence", "status"],
    )
    roots_csv = write_csv(
        PACKET / "required_root_status_after_071457_v1.csv",
        roots,
        ["id", "root", "exists", "file_count", "required_present", "physical_complete", "accepted_for_promotion", "notes", "files"],
    )
    referenced_csv = write_csv(
        PACKET / "referenced_run_status_after_071457_v1.csv",
        referenced,
        ["run_id", "exists", "report_count", "json_count", "assertion_count", "status"],
    )

    artifact = {
        "run_id": RUN_ID,
        "gate_result": GATE,
        "generated_at_epoch": int(time.time()),
        "objective_restatement": (
            "Every target regime needs 95%-99% accepted confidence with cross-market, "
            "cross-period, and cross-timeframe validation, followed by real provider, "
            "Auto-Quant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree "
            "readbacks without disturbing concurrent board work."
        ),
        "commands": commands,
        "provider": provider,
        "auto_quant": auto_quant,
        "workflow": workflow,
        "path_ranking": path_ranking,
        "roots": roots,
        "referenced_runs": referenced,
        "prompt_to_artifact_checklist": checks,
        "checklist_counts": {
            "blocked_or_not_complete": len(blocked),
            "partial_non_promoting": len(partial),
            "pass": sum(1 for row in checks if row["status"] == "pass"),
        },
        "decision": {
            "accepted_rows_added": 0,
            "valid_required_root_unlock": False,
            "source_control_evidence_acquired": False,
            "direct_verifier_run": False,
            "split_calibration_run": False,
            "canonical_merge": False,
            "provider_autoquant_promotion": False,
            "pre_bayes_bbn_catboost_execution_tree_promotion": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "artifacts": {
            "report": str((PACKET / "current_objective_audit_after_071457_v1.md").relative_to(REPO)),
            "json": str((PACKET / "current_objective_audit_after_071457_v1.json").relative_to(REPO)),
            "checklist_csv": checklist_csv,
            "roots_csv": roots_csv,
            "referenced_runs_csv": referenced_csv,
            "assertions": str((CHECKS / "current_objective_audit_after_071457_v1_assertions.out").relative_to(REPO)),
        },
        "next": (
            "Continue source/control acquisition only until explicit approval, verifier-native "
            "R6 owner/export controls, source-owned post-2026-01-30 R5 rows, verifier-native "
            "Crisis-capable R3 labels, or a genuinely new accepted cross-timeframe MainRegimeV2 "
            "source export exists."
        ),
    }

    (PACKET / "current_objective_audit_after_071457_v1.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (PACKET / "current_objective_audit_after_071457_v1.md").write_text(
        render_report(artifact),
        encoding="utf-8",
    )
    (CHECKS / "current_objective_audit_after_071457_v1_assertions.out").write_text(
        render_assertions(artifact),
        encoding="utf-8",
    )
    return 0


def render_report(artifact: dict[str, Any]) -> str:
    checklist_lines = [
        f"- {row['status']}: {row['requirement']} -- {row['evidence']}"
        for row in artifact["prompt_to_artifact_checklist"]
    ]
    roots_lines = [
        f"- {row['id']}: exists={row['exists']} file_count={row['file_count']} accepted={row['accepted_for_promotion']} notes={row['notes']}"
        for row in artifact["roots"]
    ]
    return "\n".join(
        [
            "# Current Objective Audit After 071457 v1",
            "",
            f"Run id: `{artifact['run_id']}`",
            "",
            f"Gate result: `{artifact['gate_result']}`",
            "",
            "## Objective",
            "",
            artifact["objective_restatement"],
            "",
            "## Prompt-To-Artifact Checklist",
            "",
            *checklist_lines,
            "",
            "## Required Roots",
            "",
            *roots_lines,
            "",
            "## Runtime Readback",
            "",
            f"- Provider summary: `{artifact['provider'].get('summary_line')}`",
            f"- Auto-Quant: status `{artifact['auto_quant'].get('status')}`, data_ready `{artifact['auto_quant'].get('data_ready')}`",
            f"- Workflow missing selected history: `{artifact['workflow'].get('contains_user_selected_historical_data_missing')}`",
            f"- Path-ranking: `{artifact['path_ranking'].get('summary_line')}`",
            "",
            "## Decision",
            "",
            "- Accepted rows added: `0`",
            "- Valid required-root unlock: `false`",
            "- Source/control evidence acquired: `false`",
            "- Direct verifier run: `false`",
            "- Split calibration run: `false`",
            "- Canonical merge: `false`",
            "- Provider/AutoQuant promotion: `false`",
            "- Filter / Pre-Bayes / BBN / CatBoost / execution-tree promotion: `false`",
            "- Strict full objective: `false`",
            "- Trade usable: `false`",
            "- `update_goal=false`",
            "",
            "## Next",
            "",
            artifact["next"],
            "",
        ]
    )


def render_assertions(artifact: dict[str, Any]) -> str:
    decision = artifact["decision"]
    return "\n".join(
        [
            f"gate_result={artifact['gate_result']}",
            "provider_status_called=true",
            "auto_quant_status_called=true",
            "pre_bayes_status_called=true",
            "workflow_status_called=true",
            "path_ranking_export_called=true",
            f"auto_quant_data_ready={str(artifact['auto_quant'].get('data_ready')).lower()}",
            f"workflow_user_selected_historical_data_missing={str(artifact['workflow'].get('contains_user_selected_historical_data_missing')).lower()}",
            f"path_ranking_mature_rows0={str(artifact['path_ranking'].get('contains_mature_rows0')).lower()}",
            f"path_ranking_calibrated_rows0={str(artifact['path_ranking'].get('contains_calibrated_rows0')).lower()}",
            f"blocked_or_not_complete={artifact['checklist_counts']['blocked_or_not_complete']}",
            f"partial_non_promoting={artifact['checklist_counts']['partial_non_promoting']}",
            f"accepted_rows_added={decision['accepted_rows_added']}",
            f"valid_required_root_unlock={str(decision['valid_required_root_unlock']).lower()}",
            f"source_control_evidence_acquired={str(decision['source_control_evidence_acquired']).lower()}",
            f"direct_verifier_run={str(decision['direct_verifier_run']).lower()}",
            f"split_calibration_run={str(decision['split_calibration_run']).lower()}",
            f"canonical_merge={str(decision['canonical_merge']).lower()}",
            f"provider_autoquant_promotion={str(decision['provider_autoquant_promotion']).lower()}",
            f"pre_bayes_bbn_catboost_execution_tree_promotion={str(decision['pre_bayes_bbn_catboost_execution_tree_promotion']).lower()}",
            f"strict_full_objective={str(decision['strict_full_objective']).lower()}",
            f"trade_usable={str(decision['trade_usable']).lower()}",
            f"update_goal={str(decision['update_goal']).lower()}",
            "",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
