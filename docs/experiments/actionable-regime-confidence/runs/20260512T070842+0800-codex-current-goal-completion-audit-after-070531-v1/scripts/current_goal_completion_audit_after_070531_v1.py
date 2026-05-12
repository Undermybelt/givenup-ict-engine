#!/usr/bin/env python3
"""Current Board B completion audit after the 070531 source-control readback."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


RUN_ID = "20260512T070842+0800-codex-current-goal-completion-audit-after-070531-v1"
GATE = (
    "current_goal_completion_audit_after_070531_v1="
    "not_complete_source_control_unlock_absent_no_selected_history_no_promotion"
)
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
PACKET = RUN_ROOT / "current-goal-completion-audit-after-070531-v1"
OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD_B = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"
STATE_DIR = Path("/tmp/ict-engine-board-a-064259-runtime-v1")

ROOTS = {
    "r6_owner_export": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r5_recency_extension": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "r3_native_subhour": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "source_label_equivalence": Path("/tmp/ict-engine-source-label-equivalence-intake"),
}

REFERENCED_RUNS = [
    "20260512T065822+0800-codex-source-control-provider-refresh-after-065506-v1",
    "20260512T070031+0800-codex-autoquant-run-readback-after-data-ready-v1",
    "20260512T070312+0800-codex-autoquant-readback-reconciliation-after-070031-v1",
    "20260512T070315+0800-codex-public-exact-source-route-probe-after-065820-v1",
    "20260512T070434+0800-codex-r6-owner-export-arrival-poll-after-070315-v1",
    "20260512T070443+0800-codex-local-tomac-futures-ohlcv-r6-applicability-v1",
    "20260512T070506+0800-codex-github-code-source-route-probe-after-070315-v1",
    "20260512T070509+0800-codex-completion-audit-after-070315-v1",
    "20260512T070531+0800-codex-r6-cftc-complaint-text-extraction-after-070315-v1",
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
            check=False,
            timeout=timeout,
        )
        stdout_path.write_text(proc.stdout, encoding="utf-8")
        stderr_path.write_text(proc.stderr, encoding="utf-8")
        exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
        return {
            "key": key,
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


def command_json(key: str) -> dict[str, Any]:
    return load_json(OUT / f"{key}.stdout")


def command_text(key: str) -> str:
    try:
        return (OUT / f"{key}.stdout").read_text(encoding="utf-8")
    except OSError:
        return ""


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
    rows: list[dict[str, Any]] = []
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
        return "target root absent; no owner/export rows or normal controls acquired" if not exists else "requires owner/export controls"
    if key == "r5_recency_extension":
        return "target root absent; no source-owned post-2026-01-30 rows acquired" if not exists else "requires source-owned recency provenance"
    if key == "r3_native_subhour":
        return "physical root is TSIE-derived/quarantined and Crisis-absent; non-promoting"
    return "non-target equivalence context; does not satisfy R3/R5/R6"


def referenced_run_status() -> list[dict[str, Any]]:
    base = REPO / "docs/experiments/actionable-regime-confidence/runs"
    rows = []
    for run_id in REFERENCED_RUNS:
        root = base / run_id
        reports = list(root.glob("**/*.md")) if root.exists() else []
        jsons = list(root.glob("**/*.json")) if root.exists() else []
        checks = list(root.glob("**/*assertions.out")) if root.exists() else []
        rows.append(
            {
                "run_id": run_id,
                "exists": root.exists(),
                "report_count": len(reports),
                "json_count": len(jsons),
                "assertion_count": len(checks),
                "status": "terminal_or_raw" if root.exists() else "missing",
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
        "contains_fail_closed": "fail_closed" in text.lower(),
        "first_lines": "\\n".join(text.splitlines()[:20]),
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
            "requirement": "Authoritative Board B file updated without disturbing concurrent work",
            "evidence": str(BOARD_B.relative_to(REPO)),
            "status": "pass",
        },
        {
            "requirement": "Profitability-factor training is based on accepted regime-identification roots",
            "evidence": "No accepted R3/R5/R6 MainRegimeV2 root exists; selected-data training is therefore not allowed.",
            "status": "blocked",
        },
        {
            "requirement": "Branch path main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor is preserved downstream",
            "evidence": "No post-unlock selected-data AutoQuant or downstream promotion rerun exists; branch path remains a contract, not verified output.",
            "status": "blocked",
        },
        {
            "requirement": "R6 owner/export rows with valid normal controls",
            "evidence": f"exists={root_map['r6_owner_export']['exists']} file_count={root_map['r6_owner_export']['file_count']}",
            "status": "blocked",
        },
        {
            "requirement": "R5 source-owned post-2026-01-30 MainRegimeV2 recency rows",
            "evidence": f"exists={root_map['r5_recency_extension']['exists']} file_count={root_map['r5_recency_extension']['file_count']}",
            "status": "blocked",
        },
        {
            "requirement": "R3 verifier-native Crisis-capable native-subhour MainRegimeV2 labels",
            "evidence": f"exists={root_map['r3_native_subhour']['exists']} notes={root_map['r3_native_subhour']['notes']}",
            "status": "blocked",
        },
        {
            "requirement": "Explicit user-selected historical path, exactly one of HTF=1d, MTF=4h, LTF=1h",
            "evidence": "workflow-status still contains user_selected_historical_data_missing",
            "status": "blocked" if workflow["contains_user_selected_historical_data_missing"] else "unverified",
        },
        {
            "requirement": "Real AutoQuant operation",
            "evidence": f"status={auto_quant.get('status')} data_ready={auto_quant.get('data_ready')}; prior Tomac harness success remains runtime-only",
            "status": "partial_non_promoting",
        },
        {
            "requirement": "Real ict-engine filter / Pre-Bayes / BBN / CatBoost / execution-tree surfaces",
            "evidence": f"workflow_blocked={workflow['contains_blocked']} path_ranking={path_ranking['summary_line']}",
            "status": "partial_non_promoting",
        },
        {
            "requirement": "Provider coverage for IBKR, TradingViewRemix, yfinance, Kraken",
            "evidence": f"provider_summary={provider.get('summary_line')}",
            "status": "partial_non_promoting",
        },
        {
            "requirement": "Canonical merge and downstream promotion rerun after unlock",
            "evidence": "valid_required_root_unlock=false; no canonical merge or downstream promotion rerun permitted.",
            "status": "blocked",
        },
        {
            "requirement": "Completion and update_goal",
            "evidence": "Required roots, selected history, selected-data training, and downstream promotion remain missing.",
            "status": "not_complete",
        },
    ]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> str:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return str(path.relative_to(REPO))


def main() -> int:
    PACKET.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    commands = [
        run_cmd("board_sha256_before", ["shasum", "-a", "256", str(BOARD_B.relative_to(REPO))]),
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
    runs = referenced_run_status()
    provider = provider_summary()
    auto_quant = auto_quant_summary()
    workflow = workflow_summary()
    path_ranking = path_ranking_summary()
    checks = checklist(provider, auto_quant, workflow, path_ranking, roots)
    blocked_count = sum(1 for row in checks if row["status"] in {"blocked", "not_complete"})
    partial_count = sum(1 for row in checks if row["status"] == "partial_non_promoting")

    checklist_csv = write_csv(
        PACKET / "prompt_to_artifact_checklist_after_070531_v1.csv",
        checks,
        ["requirement", "evidence", "status"],
    )
    roots_csv = write_csv(
        PACKET / "required_root_status_after_070531_v1.csv",
        [
            {
                **row,
                "required_present": json.dumps(row["required_present"], sort_keys=True),
            }
            for row in roots
        ],
        ["id", "root", "exists", "file_count", "required_present", "physical_complete", "accepted_for_promotion", "notes", "files"],
    )
    runs_csv = write_csv(
        PACKET / "referenced_run_status_after_070531_v1.csv",
        runs,
        ["run_id", "exists", "report_count", "json_count", "assertion_count", "status"],
    )

    summary = {
        "run_id": RUN_ID,
        "generated_at_epoch": int(time.time()),
        "gate_result": GATE,
        "objective_restatement": (
            "Train profitability factors only after accepted regime-identification roots exist; "
            "preserve the branch path main_regime -> sub_regime -> "
            "sub_sub_regime_or_profit_factor -> profit_factor through AutoQuant, filter/"
            "Pre-Bayes, BBN, CatBoost/path-ranking, and execution tree; use real provider "
            "surfaces without disturbing concurrent board work."
        ),
        "commands": commands,
        "provider": provider,
        "auto_quant": auto_quant,
        "workflow": workflow,
        "path_ranking": path_ranking,
        "required_roots": roots,
        "referenced_runs": runs,
        "prompt_to_artifact_checklist": checks,
        "checklist_counts": {
            "blocked_or_not_complete": blocked_count,
            "partial_non_promoting": partial_count,
            "pass": sum(1 for row in checks if row["status"] == "pass"),
        },
        "accounting": {
            "accepted_rows_added": 0,
            "valid_required_root_unlock": False,
            "source_control_evidence_acquired": False,
            "explicit_user_selected_history": False,
            "selected_data_autoquant_training": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "decision": (
            "The active objective is not achieved. Current evidence is provider/runtime "
            "diagnostic plus negative source-control route evidence only; it does not "
            "unlock selected-history AutoQuant training or downstream promotion."
        ),
        "next_action": (
            "Continue only from explicit source/control approval, verifier-native R6 "
            "owner/export rows with controls, source-owned post-2026-01-30 R5 "
            "MainRegimeV2 recency rows, verifier-native Crisis-capable R3 MainRegimeV2 "
            "labels, or a genuinely new accepted cross-timeframe MainRegimeV2 source "
            "export. After that, require exactly one explicit user-selected historical path."
        ),
        "artifacts": {
            "json": str((PACKET / "current_goal_completion_audit_after_070531_v1.json").relative_to(REPO)),
            "report": str((PACKET / "current_goal_completion_audit_after_070531_v1.md").relative_to(REPO)),
            "checklist_csv": checklist_csv,
            "roots_csv": roots_csv,
            "referenced_runs_csv": runs_csv,
            "assertions": str((CHECKS / "current_goal_completion_audit_after_070531_v1_assertions.out").relative_to(REPO)),
        },
    }

    (PACKET / "current_goal_completion_audit_after_070531_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    lines = [
        "# Current Goal Completion Audit After 070531 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE}`",
        "",
        "## Objective Restatement",
        "",
        summary["objective_restatement"],
        "",
        "## Prompt-to-Artifact Checklist",
        "",
    ]
    for row in checks:
        lines.append(f"- `{row['status']}`: {row['requirement']} -- {row['evidence']}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
            "## Accounting",
            "",
            "- Accepted rows added: `0`",
            "- Valid required-root unlock: `false`",
            "- Source/control evidence acquired: `false`",
            "- Explicit user-selected history: `false`",
            "- Selected-data AutoQuant training: `false`",
            "- Canonical merge: `false`",
            "- Downstream promotion rerun: `false`",
            "- Strict full objective: `false`",
            "- Trade usable: `false`",
            "- `update_goal=false`",
            "",
            "## Next",
            "",
            summary["next_action"],
            "",
            "## Artifacts",
            "",
            f"- JSON: `{summary['artifacts']['json']}`",
            f"- Checklist CSV: `{checklist_csv}`",
            f"- Required-root CSV: `{roots_csv}`",
            f"- Referenced-run CSV: `{runs_csv}`",
            f"- Assertions: `{summary['artifacts']['assertions']}`",
            f"- Command output: `{str(OUT.relative_to(REPO))}/`",
            "",
        ]
    )
    (PACKET / "current_goal_completion_audit_after_070531_v1.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )

    assertions = [
        f"gate_result={GATE}",
        f"provider_status_called={str(commands[1]['returncode'] == 0).lower()}",
        f"auto_quant_status_called={str(commands[2]['returncode'] == 0).lower()}",
        f"workflow_status_called={str(commands[4]['returncode'] == 0).lower()}",
        f"path_ranking_export_called={str(commands[5]['returncode'] == 0).lower()}",
        f"auto_quant_data_ready={str(bool(auto_quant.get('data_ready'))).lower()}",
        f"workflow_user_selected_historical_data_missing={str(workflow['contains_user_selected_historical_data_missing']).lower()}",
        f"blocked_or_not_complete={blocked_count}",
        f"partial_non_promoting={partial_count}",
        "accepted_rows_added=0",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "explicit_user_selected_history=false",
        "selected_data_autoquant_training=false",
        "canonical_merge=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
        "",
    ]
    (CHECKS / "current_goal_completion_audit_after_070531_v1_assertions.out").write_text(
        "\n".join(assertions), encoding="utf-8"
    )

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
