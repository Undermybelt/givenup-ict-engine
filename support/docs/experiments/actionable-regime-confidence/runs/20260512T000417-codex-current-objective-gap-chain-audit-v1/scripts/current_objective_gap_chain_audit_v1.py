#!/usr/bin/env python3
"""Audit current Board A objective coverage and the next R6 blockers.

This run is read-only with respect to the shared direct-intake root. It records
fresh command evidence for the provider/Auto-Quant/belief/policy/workflow chain
and turns the current split/species blockers into explicit row deficits.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T000417-codex-current-objective-gap-chain-audit-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "current-objective-gap-chain-audit"
CMD = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
STATE_DIR = Path("/tmp/ict-engine-current-objective-gap-chain-audit-v1")
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
ICT = REPO / "target/debug/ict-engine"

LIVE_INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
CURRENT_R6 = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235815-codex-r6-live-intake-rehydrate-calibration-v1"
    / "r6-live-intake-rehydrate-calibration"
)
CURRENT_R6_JSON = CURRENT_R6 / "r6_live_intake_rehydrate_calibration_v1.json"
CURRENT_R6_SPLITS = CURRENT_R6 / "r6_live_intake_rehydrate_split_metrics_v1.csv"
AUTO_QUANT = Path("/Users/thrill3r/Auto-Quant")

Z_95 = 1.96
MIN_WILSON = 0.95


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def perfect_success_required_total() -> int:
    n = 1
    while wilson_lcb(n, n) < MIN_WILSON:
        n += 1
    return n


def parse_json_maybe(stdout: str) -> Any:
    text = stdout.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def run_command(name: str, args: list[str], cwd: Path = REPO, timeout: int = 120) -> dict[str, Any]:
    CMD.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    stdout = CMD / f"{name}.stdout.txt"
    stderr = CMD / f"{name}.stderr.txt"
    exit_path = CMD / f"{name}.exit"
    stdout.write_text(proc.stdout, encoding="utf-8")
    stderr.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    return {
        "name": name,
        "args": args,
        "returncode": proc.returncode,
        "stdout_path": rel(stdout),
        "stderr_path": rel(stderr),
        "exit_path": rel(exit_path),
        "parsed": parse_json_maybe(proc.stdout),
        "stdout_head": proc.stdout[:500],
    }


def summarize_command(command: dict[str, Any]) -> str:
    parsed = command.get("parsed")
    if isinstance(parsed, dict):
        if parsed.get("status"):
            return str(parsed["status"])
        if parsed.get("healthy") is not None:
            return f"healthy={parsed.get('healthy')} status={parsed.get('status')}"
        if parsed.get("latest_gate_status") is not None:
            return f"latest_gate_status={parsed.get('latest_gate_status')}"
        if parsed.get("entry_models"):
            matched = [model.get("matched_rows", 0) for model in parsed.get("entry_models", [])]
            return f"entry_models={len(parsed['entry_models'])} matched_rows={matched}"
        if parsed.get("execution_gate_status"):
            return f"execution_gate_status={parsed.get('execution_gate_status')} review={parsed.get('review_status')}"
        if parsed.get("rows") is not None:
            return f"rows={parsed.get('rows')} mature_rows={parsed.get('mature_rows')}"
    return f"returncode={command['returncode']}"


def current_cursor_snapshot(board_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    in_cursor = False
    for line in board_text.splitlines():
        if line.strip() == "## Current Cursor":
            in_cursor = True
            continue
        if in_cursor and line.startswith("## "):
            break
        if in_cursor and line.startswith("|") and not line.startswith("|---") and "Field" not in line:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) >= 2:
                fields[cells[0]] = cells[1]
    return fields


def split_gap_rows(split_rows: list[dict[str, str]], required_total: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in split_rows:
        pos = int(row.get("positive_support") or 0)
        neg = int(row.get("negative_support") or 0)
        min_lcb = float(row.get("min_wilson95_lcb") or 0.0)
        passed = row.get("pass") == "True"
        if passed:
            continue
        rows.append(
            {
                "split_family": row.get("split_family"),
                "split_name": row.get("split_name"),
                "positive_support": pos,
                "negative_support": neg,
                "min_wilson95_lcb": round(min_lcb, 12),
                "additional_positive_rows_for_perfect_95": max(0, required_total - pos),
                "additional_negative_rows_for_perfect_95": max(0, required_total - neg),
                "gate_pass": False,
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            0 if row["split_family"] == "chronological_group_split" else 1,
            row["additional_positive_rows_for_perfect_95"] + row["additional_negative_rows_for_perfect_95"],
            str(row["split_name"]),
        ),
    )


def species_audit(positive_rows: list[dict[str, str]], negative_rows: list[dict[str, str]]) -> dict[str, Any]:
    labels = Counter(row.get("label", "") for row in positive_rows + negative_rows)
    text = " ".join(
        " ".join(
            [
                row.get("source_report", ""),
                row.get("source_section", ""),
                row.get("symbol", ""),
                row.get("side", ""),
                row.get("activity_description", ""),
            ]
        ).lower()
        for row in positive_rows
    )
    observed_terms = {
        "spoof_or_layer": ("spoof" in text or "layer" in text),
        "calendar_spread": "spread" in text,
        "cross_market": "cross-market" in text or "lme and comex" in text,
        "large_lot": "large-lot" in text or "large lot" in text,
    }
    missing_required_varieties = [
        "quote_stuffing",
        "pinging",
        "bear_raid_or_painting_tape",
        "social_or_text_pump_dump",
    ]
    return {
        "label_counts": dict(labels),
        "schema_has_direct_species_field": any("species" in key for key in (positive_rows[0].keys() if positive_rows else [])),
        "observed_positive_term_flags": observed_terms,
        "missing_required_varieties_from_board": missing_required_varieties,
        "direct_species_closed": False,
    }


def auto_quant_inventory() -> dict[str, Any]:
    strategies = sorted(str(path.relative_to(AUTO_QUANT)) for path in (AUTO_QUANT / "user_data/strategies").glob("*.py") if not path.name.startswith("_")) if (AUTO_QUANT / "user_data/strategies").exists() else []
    external = sorted(str(path.relative_to(AUTO_QUANT)) for path in (AUTO_QUANT / "user_data/strategies_external").glob("*.py")) if (AUTO_QUANT / "user_data/strategies_external").exists() else []
    data_files = sorted(str(path.relative_to(AUTO_QUANT)) for path in (AUTO_QUANT / "user_data/data").glob("*.feather"))[:80] if (AUTO_QUANT / "user_data/data").exists() else []
    return {
        "repo_exists": AUTO_QUANT.exists(),
        "default_strategy_files": strategies,
        "external_strategy_files": external,
        "feather_data_files_sample": data_files,
    }


def checklist_rows(
    cursor: dict[str, str],
    r6: dict[str, Any],
    direct: dict[str, Any],
    commands: list[dict[str, Any]],
    species: dict[str, Any],
) -> list[dict[str, str]]:
    command_by_name = {command["name"]: command for command in commands}
    provider_summary = summarize_command(command_by_name["provider_status_agent"])
    aq_status = summarize_command(command_by_name["ict_auto_quant_status"])
    pre_bayes = summarize_command(command_by_name["pre_bayes_status"])
    policy = summarize_command(command_by_name["policy_training_status"])
    workflow = summarize_command(command_by_name["workflow_status_execution_candidate"])
    path_ranker = summarize_command(command_by_name["export_structural_path_ranking_target"])
    local_aq = summarize_command(command_by_name["local_auto_quant_run_help"])
    direct_payload = direct.get("parsed") or {}
    return [
        {
            "requirement": "Board file is the active contract and cursor is read before edits",
            "evidence": f"board={rel(BOARD)}; last_loop_id={cursor.get('last_loop_id', '')}; current_run_root={cursor.get('current_run_root', '')}",
            "status": "covered_readback",
            "gap": "None for readback; append-only writeback still must re-read before patching.",
        },
        {
            "requirement": "Every active regime reaches 95 percent calibrated confidence",
            "evidence": f"cursor confidence_lane={cursor.get('confidence_lane', '')}; blocker={cursor.get('blocker', '')}",
            "status": "not_achieved",
            "gap": "Strict full objective still reports blocked; source-label confidence 0/4 and R3/R5 blockers remain in cursor.",
        },
        {
            "requirement": "Cross-market and cross-timeframe validation remains confident",
            "evidence": f"R6 chronological={r6.get('direct_calibration', {}).get('chronological_split_gate')}; symbol={r6.get('direct_calibration', {}).get('heldout_symbol_gate')}; venue={r6.get('direct_calibration', {}).get('heldout_venue_gate')}",
            "status": "not_achieved",
            "gap": "R6 pooled gate passes but chronological/symbol/venue gates are false; R3 native-subhour and R5 recency remain blocked.",
        },
        {
            "requirement": "Direct Manipulation/R6 gate is based on real direct rows, not OHLCV proxy",
            "evidence": f"live verifier status={direct_payload.get('status')}; positives={direct_payload.get('positive_rows')}; controls={direct_payload.get('matched_negative_rows')}; R6 pooled={r6.get('direct_calibration', {}).get('pooled_direct_gate')}",
            "status": "partial",
            "gap": "R6 direct pooled Wilson95 passes on 73/73, but split gates and species coverage remain false.",
        },
        {
            "requirement": "Missing direct Manipulation species are covered",
            "evidence": json.dumps(species, sort_keys=True),
            "status": "not_achieved",
            "gap": "Current schema/labels are spoofing-layering centered; missing quote stuffing, pinging, bear raid/painting tape, and pump-dump social/text varieties.",
        },
        {
            "requirement": "Operate provider paths: IBKR, TradingViewRemix, yfinance, Kraken",
            "evidence": provider_summary,
            "status": "partial",
            "gap": "Provider command ran, but current provider catalog remains degraded for IBKR, TradingView MCP, and Kraken public; yfinance and kraken_cli are usable context only.",
        },
        {
            "requirement": "Operate Auto-Quant rather than infer from docs",
            "evidence": f"ict auto-quant={aq_status}; local Auto-Quant command={local_aq}; inventory={json.dumps(auto_quant_inventory(), sort_keys=True)[:500]}",
            "status": "partial",
            "gap": "ict-managed Auto-Quant remains bootstrap/missing_dependency; local Auto-Quant runs but default strategy dir is empty. Existing external strategy/data are inventoried, not promoted into Board A.",
        },
        {
            "requirement": "Run filter / Pre-Bayes / belief-network path",
            "evidence": f"pre_bayes={pre_bayes}; evidence_quality={summarize_command(command_by_name['evidence_quality_breakdown'])}",
            "status": "partial",
            "gap": "Surface ran, but current isolated state does not produce an accepted Board A 95 percent regime closure.",
        },
        {
            "requirement": "Run CatBoost/path-ranker and execution tree surfaces",
            "evidence": f"policy_training={policy}; path_ranker={path_ranker}; workflow_execution={workflow}",
            "status": "partial",
            "gap": "Policy/CatBoost/path-ranker surface has no mature matched production rows for strict completion; workflow remains observe/no-trade.",
        },
        {
            "requirement": "Do not disturb other agents' construction",
            "evidence": "This run writes only under its own run root and /tmp state; shared live intake is read-only.",
            "status": "covered",
            "gap": "Board patch still requires fresh tail/hash readback immediately before editing.",
        },
    ]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CMD.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    board_text = BOARD.read_text(encoding="utf-8")
    cursor = current_cursor_snapshot(board_text)
    required_total = perfect_success_required_total()

    direct = run_command("direct_manipulation_row_intake_verifier", ["python3", str(DIRECT_VERIFIER), "--intake-root", str(LIVE_INTAKE)])
    r6 = json.loads(CURRENT_R6_JSON.read_text(encoding="utf-8"))
    split_rows = read_csv(CURRENT_R6_SPLITS)
    split_gaps = split_gap_rows(split_rows, required_total)
    positive_rows = read_csv(LIVE_INTAKE / "positive_spoofing_layering_rows.csv") if (LIVE_INTAKE / "positive_spoofing_layering_rows.csv").exists() else []
    negative_rows = read_csv(LIVE_INTAKE / "matched_negative_normal_activity_rows.csv") if (LIVE_INTAKE / "matched_negative_normal_activity_rows.csv").exists() else []
    species = species_audit(positive_rows, negative_rows)

    commands = [
        run_command("provider_status_agent", [str(ICT), "provider-status", "--agent"]),
        run_command("provider_status_compact", [str(ICT), "provider-status", "--compact"]),
        run_command("ict_auto_quant_status", [str(ICT), "auto-quant-status", "--state-dir", str(STATE_DIR / "auto-quant"), "--output-format", "json"]),
        run_command("analyze_demo", [str(ICT), "analyze", "--symbol", "DEMO", "--demo", "--state-dir", str(STATE_DIR), "--output-format", "json"]),
        run_command("pre_bayes_status", [str(ICT), "pre-bayes-status", "--symbol", "DEMO", "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"]),
        run_command("evidence_quality_breakdown", [str(ICT), "evidence-quality-breakdown", "--symbol", "DEMO", "--state-dir", str(STATE_DIR), "--refresh"]),
        run_command("policy_training_status", [str(ICT), "policy-training-status", "--symbol", "DEMO", "--state-dir", str(STATE_DIR), "--output-format", "json"]),
        run_command("workflow_status_execution_candidate", [str(ICT), "workflow-status", "--symbol", "DEMO", "--state-dir", str(STATE_DIR), "--refresh", "--phase", "execution-candidate", "--output-format", "json"]),
        run_command("export_structural_path_ranking_target", [str(ICT), "export-structural-path-ranking-target", "--symbol", "DEMO", "--state-dir", str(STATE_DIR)]),
        run_command("local_auto_quant_run_help", ["uv", "--directory", str(AUTO_QUANT), "run", "python", "run.py", "--help"], cwd=AUTO_QUANT, timeout=180),
    ]

    checklist = checklist_rows(cursor, r6, direct, commands, species)
    direct_payload = direct.get("parsed") or {}
    command_rows = [
        {
            "name": command["name"],
            "returncode": command["returncode"],
            "summary": summarize_command(command),
            "stdout_path": command["stdout_path"],
            "stderr_path": command["stderr_path"],
            "exit_path": command["exit_path"],
        }
        for command in [direct, *commands]
    ]

    split_gap_csv = OUT / "current_objective_r6_split_gap_v1.csv"
    checklist_csv = OUT / "current_objective_prompt_to_artifact_checklist_v1.csv"
    command_csv = OUT / "current_objective_chain_commands_v1.csv"
    species_json = OUT / "current_objective_direct_species_audit_v1.json"
    result_json = OUT / "current_objective_gap_chain_audit_v1.json"
    report_md = OUT / "current_objective_gap_chain_audit_v1.md"
    assertions_path = CHECKS / "current_objective_gap_chain_audit_v1_assertions.out"

    write_csv(
        split_gap_csv,
        split_gaps,
        [
            "split_family",
            "split_name",
            "positive_support",
            "negative_support",
            "min_wilson95_lcb",
            "additional_positive_rows_for_perfect_95",
            "additional_negative_rows_for_perfect_95",
            "gate_pass",
        ],
    )
    write_csv(checklist_csv, checklist, ["requirement", "evidence", "status", "gap"])
    write_csv(command_csv, command_rows, ["name", "returncode", "summary", "stdout_path", "stderr_path", "exit_path"])
    write_json(species_json, species)

    failed_requirements = [row for row in checklist if row["status"] in {"not_achieved", "partial"}]
    all_expected_commands_ran = all(command["returncode"] in {0, 2} for command in [direct, *commands])
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "current_cursor": cursor,
        "objective_restatement": {
            "deliverables": [
                "Every active Board A regime has regime-specific 95 percent calibrated confidence.",
                "Each accepted regime is validated across other markets and periods/timeframes.",
                "Provider, Auto-Quant, Pre-Bayes/BBN, CatBoost/path-ranker, workflow, and execution-tree surfaces are run with artifacts.",
                "The shared Board A markdown remains concurrency-safe.",
            ],
            "strict_completion_achieved": False,
        },
        "direct_verifier": direct,
        "current_r6_source_json": rel(CURRENT_R6_JSON),
        "current_r6_live_positive_rows": direct_payload.get("positive_rows"),
        "current_r6_live_matched_negative_rows": direct_payload.get("matched_negative_rows"),
        "current_r6_pooled_gate": r6.get("direct_calibration", {}).get("pooled_direct_gate"),
        "current_r6_chronological_split_gate": r6.get("direct_calibration", {}).get("chronological_split_gate"),
        "current_r6_heldout_symbol_gate": r6.get("direct_calibration", {}).get("heldout_symbol_gate"),
        "current_r6_heldout_venue_gate": r6.get("direct_calibration", {}).get("heldout_venue_gate"),
        "perfect_success_required_rows_for_wilson95": required_total,
        "split_gap_csv": rel(split_gap_csv),
        "species_audit_json": rel(species_json),
        "prompt_to_artifact_checklist_csv": rel(checklist_csv),
        "provider_downstream_command_csv": rel(command_csv),
        "provider_downstream_commands": commands,
        "auto_quant_inventory": auto_quant_inventory(),
        "failed_or_partial_requirements": failed_requirements,
        "all_expected_commands_ran": all_expected_commands_ran,
        "gate_result": "current_objective_gap_chain_audit_v1=strict_objective_not_achieved_r6_split_species_r3_r5_and_chain_maturity_blocked",
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "shared_intake_mutated": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": (
            "Source direct Manipulation rows that are explicitly non-spoofing species and targeted to the weakest "
            "chronological calibration/test, exact-symbol, and exact-venue buckets; then rerun R6 calibration and "
            "the provider/Auto-Quant/Pre-Bayes/policy/workflow/path-ranker chain while keeping R3/R5 blocked."
        ),
    }
    write_json(result_json, result)

    top_gaps = split_gaps[:8]
    report_lines = [
        "# Current Objective Gap Chain Audit v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Current cursor: `{cursor.get('last_loop_id', '')}`.",
        f"- Live direct verifier: `{direct_payload.get('status')}` with positives `{direct_payload.get('positive_rows')}` and controls `{direct_payload.get('matched_negative_rows')}`.",
        f"- R6 pooled direct gate: `{r6.get('direct_calibration', {}).get('pooled_direct_gate')}`; chronological split: `{r6.get('direct_calibration', {}).get('chronological_split_gate')}`; heldout symbol: `{r6.get('direct_calibration', {}).get('heldout_symbol_gate')}`; heldout venue: `{r6.get('direct_calibration', {}).get('heldout_venue_gate')}`.",
        f"- Perfect all-correct rows needed for Wilson95 >= 0.95: `{required_total}` per class/bucket.",
        f"- Prompt-to-artifact checklist status: failed/partial `{len(failed_requirements)}` of `{len(checklist)}` requirements.",
        f"- Gate result: `{result['gate_result']}`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; shared intake mutated: `false`; trade usable: `false`.",
        "",
        "## Top Split Gaps",
    ]
    for gap in top_gaps:
        report_lines.append(
            "- "
            f"`{gap['split_family']} / {gap['split_name']}`: "
            f"positive `{gap['positive_support']}` needs `+{gap['additional_positive_rows_for_perfect_95']}`, "
            f"negative `{gap['negative_support']}` needs `+{gap['additional_negative_rows_for_perfect_95']}`, "
            f"min LCB `{gap['min_wilson95_lcb']}`."
        )
    report_lines.extend(
        [
            "",
            "## Command Evidence",
        ]
    )
    for row in command_rows:
        report_lines.append(f"- `{row['name']}` returncode `{row['returncode']}` summary `{row['summary']}`.")
    report_lines.extend(
        [
            "",
            "## Artifacts",
            f"- JSON: `{rel(result_json)}`",
            f"- Checklist CSV: `{rel(checklist_csv)}`",
            f"- Split gap CSV: `{rel(split_gap_csv)}`",
            f"- Species audit JSON: `{rel(species_json)}`",
            f"- Command CSV: `{rel(command_csv)}`",
            f"- Assertions: `{rel(assertions_path)}`",
            "",
            "Next: source non-spoofing direct Manipulation rows and target the weakest chronology/symbol/venue buckets before rerunning calibration.",
        ]
    )
    report_md.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    assertions = {
        "direct_verifier_schema_ready": direct_payload.get("status") == "schema_ready_unscored",
        "r6_positive_rows_73": direct_payload.get("positive_rows") == 73,
        "r6_matched_negative_rows_73": direct_payload.get("matched_negative_rows") == 73,
        "r6_pooled_gate_true": r6.get("direct_calibration", {}).get("pooled_direct_gate") is True,
        "r6_chronological_split_false": r6.get("direct_calibration", {}).get("chronological_split_gate") is False,
        "r6_heldout_symbol_false": r6.get("direct_calibration", {}).get("heldout_symbol_gate") is False,
        "r6_heldout_venue_false": r6.get("direct_calibration", {}).get("heldout_venue_gate") is False,
        "direct_species_not_closed": species["direct_species_closed"] is False,
        "provider_autoquant_belief_policy_workflow_commands_captured": all_expected_commands_ran,
        "strict_full_objective_not_complete": result["strict_full_objective_achieved"] is False,
        "update_goal_false": result["update_goal"] is False,
    }
    assertions_path.write_text("\n".join(f"{name}={'ok' if value else 'FAIL'}" for name, value in assertions.items()) + "\n", encoding="utf-8")
    if not all(assertions.values()):
        return 2
    print(json.dumps({"ok": True, "run_id": RUN_ID, "gate_result": result["gate_result"], "update_goal": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
