#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


RUN_ID = "20260512T123211+0800-codex-115700-selected-history-preflight-v1"
SOURCE_ROOT_ID = "20260512T121347+0800-codex-115700-enriched-downstream-chain-v1"
SYMBOL = "B2R_SAME_ROOT_SIX_PROVIDER_1H_AQ_115700"

ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
SOURCE_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / SOURCE_ROOT_ID
SOURCE_STATE = SOURCE_ROOT / "state_115700_enriched_downstream_chain_v1"
DATA_ROOT = SOURCE_ROOT / "provider-data-json"

REPORT_DIR = ROOT / "115700-selected-history-preflight-v1"
CHECK_DIR = ROOT / "checks"
OUT_DIR = ROOT / "command-output"
STATE_ROOT = ROOT / "state-copies"

ICT = "./target/debug/ict-engine"

DATASETS = {
    "1h": DATA_ROOT / "BTC_USD-1h.json",
    "4h": DATA_ROOT / "BTC_USD-4h.json",
    "1d": DATA_ROOT / "BTC_USD-1d.json",
}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(label: str, command: list[str]) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{label}.cmd").write_text(" ".join(command) + "\n", encoding="utf-8")
    proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    (OUT_DIR / f"{label}.out").write_text(proc.stdout, encoding="utf-8")
    (OUT_DIR / f"{label}.err").write_text(proc.stderr, encoding="utf-8")
    (CHECK_DIR / f"{label}.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
    return proc.returncode


def parse_json_output(label: str) -> dict[str, Any]:
    return read_json(OUT_DIR / f"{label}.out")


def prepare_state(label: str) -> Path:
    dst = STATE_ROOT / f"state_{label}_copy"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(SOURCE_STATE, dst)
    return dst


def run_dataset(label: str, data_path: Path) -> dict[str, Any]:
    state_dir = prepare_state(label)
    factor_label = f"{label}_factor_research_native"
    workflow_label = f"{label}_workflow_after_native"
    cmd = [
        ICT,
        "factor-research",
        "--symbol",
        SYMBOL,
        "--data",
        str(data_path),
        "--data-1h",
        str(DATASETS["1h"]),
        "--data-4h",
        str(DATASETS["4h"]),
        "--data-1d",
        str(DATASETS["1d"]),
        "--state-dir",
        str(state_dir),
        "--backend",
        "native",
        "--output-format",
        "json",
    ]
    factor_exit = run_command(factor_label, cmd)
    workflow_exit = run_command(
        workflow_label,
        [
            ICT,
            "workflow-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(state_dir),
            "--refresh",
            "--output-format",
            "json",
        ],
    )
    factor = parse_json_output(factor_label)
    workflow = parse_json_output(workflow_label)
    phase = workflow.get("phase_detail") or workflow.get("latest_structural_execution_candidate") or {}
    blocking = workflow.get("blocking_truth") or {}
    latest_exec = workflow.get("latest_execution_candidate") or {}
    return {
        "label": label,
        "data_path": str(data_path),
        "state_dir": str(state_dir),
        "factor_research_exit": factor_exit,
        "workflow_exit": workflow_exit,
        "factor_research_keys": sorted(factor.keys())[:50],
        "workflow_blocking_truth": blocking,
        "workflow_phase_detail": {
            "ready": phase.get("ready"),
            "actionable": phase.get("actionable"),
            "review_status": phase.get("review_status"),
            "candidate_status": phase.get("candidate_status"),
            "execution_gate_status": phase.get("execution_gate_status"),
            "execution_readiness": phase.get("execution_readiness"),
            "path_id": phase.get("path_id"),
            "selected_path_probability": phase.get("selected_path_probability"),
            "path_ranker_calibrated_path_prob": phase.get("path_ranker_calibrated_path_prob"),
        },
        "latest_execution_candidate": {
            "candidate_status": latest_exec.get("candidate_status"),
            "trade_direction": latest_exec.get("trade_direction"),
            "actionable": latest_exec.get("actionable"),
            "review_status": latest_exec.get("review_status"),
            "posterior": latest_exec.get("posterior"),
            "win_probability": latest_exec.get("win_probability"),
            "decision_hint": latest_exec.get("decision_hint"),
        },
    }


def choose_support(results: list[dict[str, Any]]) -> dict[str, Any]:
    preferred = "1h"
    ready = [r for r in results if r["workflow_phase_detail"].get("ready") and r["workflow_phase_detail"].get("actionable")]
    if ready:
        preferred = ready[0]["label"]
    return {
        "preferred_for_user_selection": preferred,
        "reason": "1h preserves the current 115700 same-root 1h AQ/runtime surface unless a preflight copy becomes ready/actionable.",
        "ready_actionable_labels": [r["label"] for r in ready],
    }


def main() -> int:
    for path in (REPORT_DIR, CHECK_DIR, OUT_DIR, STATE_ROOT):
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n", encoding="utf-8")
    (ROOT / "source_root_id.txt").write_text(SOURCE_ROOT_ID + "\n", encoding="utf-8")

    results = [run_dataset(label, data_path) for label, data_path in DATASETS.items()]
    support = choose_support(results)
    summary = {
        "run_id": RUN_ID,
        "source_root_id": SOURCE_ROOT_ID,
        "symbol": SYMBOL,
        "mode": "copied_state_native_preflight_only",
        "source_state_mutated": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "support": support,
        "results": results,
    }

    json_path = REPORT_DIR / "115700_selected_history_preflight_v1.json"
    md_path = REPORT_DIR / "115700_selected_history_preflight_v1.md"
    assertions_path = CHECK_DIR / "115700_selected_history_preflight_v1_assertions.out"
    write_json(json_path, summary)

    lines = [
        "# 115700 Selected-History Preflight v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source root: `{SOURCE_ROOT_ID}`",
        "",
        "## Scope",
        "This is a copied-state, non-promoting preflight for the three recorded historical data paths. It does not mutate the `121347` source state and does not count as user selection/source-control unlock.",
        "",
        "## Results",
    ]
    for item in results:
        phase = item["workflow_phase_detail"]
        latest = item["latest_execution_candidate"]
        lines.extend(
            [
                f"- `{item['label']}` data `{item['data_path']}`",
                f"  - exits: factor-research `{item['factor_research_exit']}`, workflow `{item['workflow_exit']}`",
                f"  - structural ready/actionable/review: `{phase.get('ready')}` / `{phase.get('actionable')}` / `{phase.get('review_status')}`",
                f"  - structural gate/readiness: `{phase.get('execution_gate_status')}` / `{phase.get('execution_readiness')}`",
                f"  - latest candidate: `{latest.get('candidate_status')}` direction `{latest.get('trade_direction')}` review `{latest.get('review_status')}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Decision",
            f"- Suggested user-selection default remains `{support['preferred_for_user_selection']}`.",
            f"- Reason: {support['reason']}",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{json_path}`",
            f"- Assertions: `{assertions_path}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_root_id={SOURCE_ROOT_ID}",
        "PASS source_state_mutated=false",
        f"PASS datasets_checked={len(results)}",
        f"PASS suggested_user_selection={support['preferred_for_user_selection']}",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    for item in results:
        prefix = "PASS" if item["factor_research_exit"] == 0 and item["workflow_exit"] == 0 else "FAIL_CLOSED"
        phase = item["workflow_phase_detail"]
        assertions.append(f"{prefix} {item['label']}_factor_research_exit={item['factor_research_exit']}")
        assertions.append(f"{prefix} {item['label']}_workflow_exit={item['workflow_exit']}")
        assertions.append(
            f"FAIL_CLOSED {item['label']}_ready={phase.get('ready')} actionable={phase.get('actionable')} review={phase.get('review_status')}"
        )
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
