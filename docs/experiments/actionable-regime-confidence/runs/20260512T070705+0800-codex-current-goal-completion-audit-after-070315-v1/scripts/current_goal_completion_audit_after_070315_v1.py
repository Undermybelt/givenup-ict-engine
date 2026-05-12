#!/usr/bin/env python3
"""Current Board A completion audit after the 070315 source-route probe."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


RUN_ID = "20260512T070705+0800-codex-current-goal-completion-audit-after-070315-v1"
GATE = (
    "current_goal_completion_audit_after_070315_v1="
    "not_complete_source_control_blocked_no_downstream_promotion"
)
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
PACKET = RUN_ROOT / "current-goal-completion-audit-after-070315-v1"
OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
STATE_DIR = Path("/tmp/ict-engine-board-a-064259-runtime-v1")

ROOTS = {
    "r6_owner_export": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r3_native_subhour": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "r5_recency_extension": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "source_label_equivalence": Path("/tmp/ict-engine-source-label-equivalence-intake"),
}

KEY_RUNS = [
    "20260512T065820+0800-codex-r5-r3-target-contract-readback-after-065449-v1",
    "20260512T065822+0800-codex-source-control-provider-refresh-after-065506-v1",
    "20260512T070031+0800-codex-autoquant-run-readback-after-data-ready-v1",
    "20260512T070115+0800-codex-autoquant-final-readback-after-065824-v1",
    "20260512T070312+0800-codex-autoquant-readback-reconciliation-after-070031-v1",
    "20260512T070315+0800-codex-public-exact-source-route-probe-after-065820-v1",
    "20260512T070434+0800-codex-r6-owner-export-arrival-poll-after-070315-v1",
    "20260512T070443+0800-codex-local-tomac-futures-ohlcv-r6-applicability-v1",
]


def run_cmd(key: str, args: list[str], timeout: int = 90) -> dict[str, Any]:
    cmd = OUT / f"{key}.cmd"
    stdout = OUT / f"{key}.stdout"
    stderr = OUT / f"{key}.stderr"
    exit_file = OUT / f"{key}.exit"
    cmd.write_text(" ".join(args) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(
            args,
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        stdout.write_text(proc.stdout, encoding="utf-8")
        stderr.write_text(proc.stderr, encoding="utf-8")
        exit_file.write_text(f"{proc.returncode}\n", encoding="utf-8")
        return {
            "key": key,
            "args": args,
            "returncode": proc.returncode,
            "timeout": False,
            "stdout_path": str(stdout.relative_to(REPO)),
            "stderr_path": str(stderr.relative_to(REPO)),
        }
    except subprocess.TimeoutExpired as exc:
        stdout.write_text(exc.stdout or "", encoding="utf-8")
        stderr.write_text(exc.stderr or "", encoding="utf-8")
        exit_file.write_text("timeout\n", encoding="utf-8")
        return {
            "key": key,
            "args": args,
            "returncode": None,
            "timeout": True,
            "stdout_path": str(stdout.relative_to(REPO)),
            "stderr_path": str(stderr.relative_to(REPO)),
        }


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def command_json(key: str) -> dict[str, Any]:
    return load_json(OUT / f"{key}.stdout")


def root_status() -> list[dict[str, Any]]:
    rows = []
    for key, root in ROOTS.items():
        files = sorted(p.name for p in root.iterdir() if p.is_file()) if root.exists() else []
        rows.append(
            {
                "id": key,
                "root": str(root),
                "exists": root.exists(),
                "file_count": len(files),
                "files": ";".join(files[:20]),
            }
        )
    return rows


def run_status() -> list[dict[str, Any]]:
    rows = []
    base = REPO / "docs/experiments/actionable-regime-confidence/runs"
    for run_id in KEY_RUNS:
        root = base / run_id
        jsons = list(root.glob("**/*.json")) if root.exists() else []
        mds = list(root.glob("**/*.md")) if root.exists() else []
        checks = list(root.glob("**/*assertions.out")) if root.exists() else []
        rows.append(
            {
                "run_id": run_id,
                "exists": root.exists(),
                "json_count": len(jsons),
                "report_count": len(mds),
                "assertion_count": len(checks),
                "decision": "materialized" if jsons and mds and checks else "placeholder_or_incomplete",
            }
        )
    return rows


def provider_summary() -> dict[str, Any]:
    data = command_json("provider_status_agent")
    return {
        "summary_line": data.get("summary_line"),
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


def checklist(provider: dict[str, Any], auto_quant: dict[str, Any], roots: list[dict[str, Any]]) -> list[dict[str, str]]:
    root_map = {row["id"]: row for row in roots}
    return [
        {
            "requirement": "Every MainRegimeV2 root has 95%-99% calibrated evidence",
            "evidence": "Latest required-root readbacks still show no valid R3/R5/R6 unlock; source-label confidence remains non-promoting.",
            "status": "blocked",
        },
        {
            "requirement": "Cross-market, cross-period, cross-timeframe/context validation",
            "evidence": "No accepted post-unlock packet spans all required axes for Bull/Bear/Sideways/Crisis; latest R5/R3 candidates rejected by target contract.",
            "status": "blocked",
        },
        {
            "requirement": "R6 owner/export controls or explicit source/control approval",
            "evidence": f"R6 root exists={root_map['r6_owner_export']['exists']} file_count={root_map['r6_owner_export']['file_count']}; approval package remains non-approving.",
            "status": "blocked",
        },
        {
            "requirement": "R5 source-owned post-2026-01-30 recency rows",
            "evidence": f"R5 root exists={root_map['r5_recency_extension']['exists']} file_count={root_map['r5_recency_extension']['file_count']}; 065820 rejects NIFTY/macro candidates and stock-regime rows still end at 2026-01-30.",
            "status": "blocked",
        },
        {
            "requirement": "R3 verifier-native Crisis-capable native-subhour MainRegimeV2 labels",
            "evidence": f"R3 root exists={root_map['r3_native_subhour']['exists']} file_count={root_map['r3_native_subhour']['file_count']}; provenance is TSIE-derived and lacks Crisis.",
            "status": "blocked",
        },
        {
            "requirement": "Operate Auto-Quant on real local artifacts",
            "evidence": f"Auto-Quant status={auto_quant.get('status')} data_ready={auto_quant.get('data_ready')}; 070115 records one Tomac-specific runtime success but default managed runs failed market loading.",
            "status": "partial_non_promoting",
        },
        {
            "requirement": "Operate ict-engine filter / Pre-Bayes / BBN / CatBoost / execution tree",
            "evidence": "065822 ran analyze-live, pre-bayes-status, policy-training-status, workflow-status, and path-ranking export; workflow remained blocked and path-ranking had 0 mature/calibrated rows.",
            "status": "partial_non_promoting",
        },
        {
            "requirement": "Check IBKR, TradingViewRemix, yfinance, Kraken",
            "evidence": f"Provider summary={provider.get('summary_line')}; yfinance and kraken_cli ready, IBKR/TradingViewRemix/Kraken public remain dependency/runtime blocked.",
            "status": "partial_non_promoting",
        },
        {
            "requirement": "Do not disturb concurrent board work",
            "evidence": "Current slice is append-only and does not rewrite Current Cursor or modify other agents' run roots.",
            "status": "pass",
        },
        {
            "requirement": "Completion / update_goal",
            "evidence": "At least R6, R5, R3, per-regime 95%, cross-axis validation, and post-unlock downstream promotion are missing.",
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
        run_cmd("git_status_short", ["git", "status", "--short"]),
    ]

    roots = root_status()
    runs = run_status()
    provider = provider_summary()
    auto_quant = auto_quant_summary()
    checks = checklist(provider, auto_quant, roots)
    blocked = [row for row in checks if row["status"] in {"blocked", "not_complete"}]
    incomplete_runs = [row for row in runs if row["decision"] == "placeholder_or_incomplete"]

    checklist_csv = write_csv(
        PACKET / "prompt_to_artifact_checklist_after_070315_v1.csv",
        checks,
        ["requirement", "evidence", "status"],
    )
    roots_csv = write_csv(
        PACKET / "required_root_status_after_070315_v1.csv",
        roots,
        ["id", "root", "exists", "file_count", "files"],
    )
    runs_csv = write_csv(
        PACKET / "referenced_run_status_after_070315_v1.csv",
        runs,
        ["run_id", "exists", "json_count", "report_count", "assertion_count", "decision"],
    )

    summary = {
        "run_id": RUN_ID,
        "generated_at_epoch": int(time.time()),
        "gate_result": GATE,
        "board_sha256_before_artifact": (
            (OUT / "board_sha256_before.stdout").read_text(encoding="utf-8").split()[0]
            if (OUT / "board_sha256_before.stdout").exists()
            else ""
        ),
        "objective_restatement": (
            "Each active MainRegimeV2 regime must have accepted 95%-99% calibrated "
            "evidence that survives cross-market, cross-period, and cross-timeframe/"
            "context validation, then a real provider/Auto-Quant/filter/Pre-Bayes/"
            "BBN/CatBoost/path-ranking/execution-tree chain must be rerun without "
            "disturbing concurrent board work."
        ),
        "commands": commands,
        "provider": provider,
        "auto_quant": auto_quant,
        "required_roots": roots,
        "referenced_runs": runs,
        "checklist": checks,
        "checklist_counts": {
            "blocked_or_not_complete": len(blocked),
            "partial_non_promoting": sum(1 for row in checks if row["status"] == "partial_non_promoting"),
            "pass": sum(1 for row in checks if row["status"] == "pass"),
            "placeholder_or_incomplete_runs": len(incomplete_runs),
        },
        "accounting": {
            "accepted_rows_added": 0,
            "valid_required_root_unlock": False,
            "source_control_evidence_acquired": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "decision": (
            "The objective is not achieved. Current evidence is useful runtime and "
            "source-route disposition only; it does not satisfy the source/control "
            "roots or the per-regime cross-axis acceptance contract."
        ),
        "next_action": (
            "Continue only from explicit source/control approval, verifier-native "
            "R6 owner-export controls, source-owned R5 post-cutoff rows matching "
            "the source-panel schema, verifier-native Crisis-capable R3 labels, "
            "or a genuinely new accepted cross-timeframe MainRegimeV2 source export."
        ),
        "artifacts": {
            "json": str((PACKET / "current_goal_completion_audit_after_070315_v1.json").relative_to(REPO)),
            "report": str((PACKET / "current_goal_completion_audit_after_070315_v1.md").relative_to(REPO)),
            "checklist_csv": checklist_csv,
            "roots_csv": roots_csv,
            "referenced_runs_csv": runs_csv,
            "assertions": str((CHECKS / "current_goal_completion_audit_after_070315_v1_assertions.out").relative_to(REPO)),
        },
    }

    (PACKET / "current_goal_completion_audit_after_070315_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    lines = [
        "# Current Goal Completion Audit After 070315 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE}`",
        "",
        "## Objective Restatement",
        "",
        summary["objective_restatement"],
        "",
        "## Completion Checklist",
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
            "- Command output: `docs/experiments/actionable-regime-confidence/runs/20260512T070705+0800-codex-current-goal-completion-audit-after-070315-v1/command-output/`",
            "",
        ]
    )
    (PACKET / "current_goal_completion_audit_after_070315_v1.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )

    assertions = [
        f"gate_result={GATE}",
        f"provider_status_called={str(commands[1]['returncode'] == 0).lower()}",
        f"auto_quant_status_called={str(commands[2]['returncode'] == 0).lower()}",
        f"auto_quant_data_ready={str(bool(auto_quant.get('data_ready'))).lower()}",
        f"blocked_or_not_complete={len(blocked)}",
        f"placeholder_or_incomplete_runs={len(incomplete_runs)}",
        "accepted_rows_added=0",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
        "",
    ]
    (CHECKS / "current_goal_completion_audit_after_070315_v1_assertions.out").write_text(
        "\n".join(assertions), encoding="utf-8"
    )

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
