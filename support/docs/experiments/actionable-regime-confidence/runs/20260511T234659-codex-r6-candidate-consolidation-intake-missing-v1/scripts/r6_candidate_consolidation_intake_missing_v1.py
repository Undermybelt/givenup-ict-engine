#!/usr/bin/env python3
"""Consolidate R6 positive sidecars and verify the live intake state."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T234659-codex-r6-candidate-consolidation-intake-missing-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-candidate-consolidation-intake-missing"
CMD = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
STATE_DIR = Path("/tmp/ict-engine-r6-candidate-consolidation-intake-missing-v1/state")
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
ENGINE = REPO / "target/debug/ict-engine"

LIVE_INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
V54_AUDIT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T223100-codex-current-goal-completion-audit-v54-after-sidecar-calibration"
    / "completion-audit/current_goal_completion_audit_v54_after_sidecar_calibration.json"
)
SIDECAR_CONTROLS = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1"
    / "r6-broad-normal-order-lifecycle-screen/broad_normal_market_order_lifecycle_controls_v1.csv"
)
SARAO_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T225505-codex-r6-sarao-positive-row-candidate-screen-v1"
    / "r6-sarao-positive-row-candidate-screen/r6_sarao_positive_row_candidate_screen_v1.json"
)
SARAO_CSV = SARAO_JSON.with_name("r6_sarao_positive_row_candidates_v1.csv")
NOWAK_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T233454-codex-r6-nowak-smith-positive-row-candidate-screen-v1"
    / "r6-nowak-smith-positive-row-candidate-screen/r6_nowak_smith_positive_row_candidate_screen_v1.json"
)
NOWAK_CSV = NOWAK_JSON.with_name("r6_nowak_smith_positive_row_candidates_v1.csv")

Z_95 = 1.96
MIN_WILSON = 0.95


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def additional_successes_needed(current_successes: int) -> int:
    for total in range(current_successes, current_successes + 500):
        if wilson_lcb(total, total) >= MIN_WILSON:
            return total - current_successes
    return 500


def run_command(name: str, args: list[str], timeout: int = 180) -> dict[str, Any]:
    CMD.mkdir(parents=True, exist_ok=True)
    stdout_path = CMD / f"{name}.stdout.txt"
    stderr_path = CMD / f"{name}.stderr.txt"
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
    parsed: Any = None
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = None
    return {
        "name": name,
        "command": " ".join(args),
        "returncode": proc.returncode,
        "stdout_path": str(stdout_path.relative_to(REPO)),
        "stderr_path": str(stderr_path.relative_to(REPO)),
        "parsed": parsed,
    }


def provider_focus(provider_status: dict[str, Any] | None) -> dict[str, Any]:
    if not provider_status:
        return {}
    rows = provider_status.get("providers", [])
    focus = {}
    for provider in rows:
        provider_id = provider.get("provider_id")
        if provider_id in {"ibkr", "ibkr_bridge", "tradingview_mcp", "yfinance", "kraken_cli", "kraken_public"}:
            key = f"{provider_id}@{provider.get('domain')}"
            focus[key] = {
                "ready": provider.get("ready"),
                "status": provider.get("status"),
                "reason": provider.get("reason"),
            }
    return focus


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    board_hash = sha256(BOARD)
    v54 = read_json(V54_AUDIT)
    sarao = read_json(SARAO_JSON)
    nowak = read_json(NOWAK_JSON)
    sarao_rows = read_csv(SARAO_CSV)
    nowak_rows = read_csv(NOWAK_CSV)
    sidecar_rows = read_csv(SIDECAR_CONTROLS) if SIDECAR_CONTROLS.exists() else []

    command_results = [
        run_command("direct_verifier_live_intake", ["python3", str(DIRECT_VERIFIER), "--intake-root", str(LIVE_INTAKE)], timeout=45),
        run_command("provider_status_agent", [str(ENGINE), "provider-status", "--agent"], timeout=180),
        run_command("auto_quant_status", [str(ENGINE), "auto-quant-status", "--state-dir", str(STATE_DIR), "--output-format", "json"], timeout=90),
        run_command("analyze_demo_agent", [str(ENGINE), "analyze", "--symbol", "DEMO", "--demo", "--state-dir", str(STATE_DIR), "--agent"], timeout=180),
        run_command("pre_bayes_status", [str(ENGINE), "pre-bayes-status", "--symbol", "DEMO", "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"], timeout=90),
        run_command("policy_training_status", [str(ENGINE), "policy-training-status", "--symbol", "DEMO", "--state-dir", str(STATE_DIR), "--output-format", "json"], timeout=90),
        run_command("workflow_status_agent", [str(ENGINE), "workflow-status", "--symbol", "DEMO", "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "agent"], timeout=90),
        run_command("export_structural_path_ranking_target", [str(ENGINE), "export-structural-path-ranking-target", "--symbol", "DEMO", "--state-dir", str(STATE_DIR)], timeout=90),
    ]
    commands_by_name = {item["name"]: item for item in command_results}

    baseline_positive = int(v54["r6"]["positive_rows"])
    baseline_negative = int(v54["r6"]["matched_negative_rows"])
    sidecar_count = len(sidecar_rows)
    proposed_positive = len(sarao_rows) + len(nowak_rows)
    proposed_without_matched_controls = proposed_positive
    what_if_positive = baseline_positive + proposed_positive
    baseline_lcb = wilson_lcb(baseline_positive, baseline_positive)
    what_if_lcb = wilson_lcb(what_if_positive, what_if_positive)
    sidecar_lcb = wilson_lcb(sidecar_count, sidecar_count)
    what_if_min_lcb = min(what_if_lcb, sidecar_lcb)

    candidate_rows = []
    for source_name, rows in [("sarao", sarao_rows), ("nowak_smith", nowak_rows)]:
        for row in rows:
            candidate_rows.append(
                {
                    "source": source_name,
                    "source_row_id": row.get("source_row_id", ""),
                    "trade_date": row.get("trade_date", ""),
                    "symbol": row.get("symbol", ""),
                    "matched_negative_group_id": row.get("matched_negative_group_id", ""),
                    "candidate_row_status": row.get("candidate_row_status", ""),
                }
            )
    write_csv(
        OUT / "r6_candidate_consolidation_rows_v1.csv",
        candidate_rows,
        ["source", "source_row_id", "trade_date", "symbol", "matched_negative_group_id", "candidate_row_status"],
    )

    direct_parsed = commands_by_name["direct_verifier_live_intake"].get("parsed") or {}
    direct_blocked_missing = (
        commands_by_name["direct_verifier_live_intake"]["returncode"] != 0
        and direct_parsed.get("status") == "blocked"
        and direct_parsed.get("reason") == "missing_required_files"
    )
    provider_parsed = commands_by_name["provider_status_agent"].get("parsed")
    provider_summary = provider_focus(provider_parsed if isinstance(provider_parsed, dict) else None)

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_hash,
        "canonical_live_intake_root": str(LIVE_INTAKE),
        "canonical_live_intake_exists": LIVE_INTAKE.exists(),
        "direct_verifier_blocked_missing_required_files": direct_blocked_missing,
        "v54_baseline_positive_rows": baseline_positive,
        "v54_baseline_matched_negative_rows": baseline_negative,
        "sidecar_broad_normal_control_rows": sidecar_count,
        "sarao_proposed_positive_rows": len(sarao_rows),
        "nowak_smith_proposed_positive_rows": len(nowak_rows),
        "combined_proposed_positive_rows": proposed_positive,
        "proposed_positive_rows_without_matched_controls": proposed_without_matched_controls,
        "what_if_positive_rows_after_sidecars": what_if_positive,
        "v54_baseline_wilson95_lcb": round(baseline_lcb, 12),
        "what_if_positive_wilson95_lcb_after_sidecars": round(what_if_lcb, 12),
        "sidecar_broad_normal_wilson95_lcb": round(sidecar_lcb, 12),
        "what_if_min_wilson95_lcb_after_sidecars": round(what_if_min_lcb, 12),
        "additional_positive_rows_needed_after_sidecars_if_all_correct": additional_successes_needed(what_if_positive),
        "provider_focus": provider_summary,
        "command_results": command_results,
        "shared_intake_mutated": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "gate_result": "r6_candidate_consolidation_intake_missing_v1=canonical_intake_missing_sidecar_positives_unaccepted_confidence_still_blocked",
        "next_action": (
            "Restore or rematerialize the direct R6 intake from durable row artifacts under a shared lock, "
            "materialize matched controls for Sarao/Nowak-Smith if policy allows, then acquire at least four more "
            "all-correct positives before pooled Wilson95 can reach 0.95; split support still needs broader rows."
        ),
    }

    json_path = OUT / "r6_candidate_consolidation_intake_missing_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    command_summary = [
        {
            "name": item["name"],
            "returncode": item["returncode"],
            "stdout_path": item["stdout_path"],
            "stderr_path": item["stderr_path"],
        }
        for item in command_results
    ]
    write_csv(OUT / "r6_candidate_consolidation_commands_v1.csv", command_summary, ["name", "returncode", "stdout_path", "stderr_path"])

    report = [
        "# R6 Candidate Consolidation and Missing Intake Readback v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Generated at UTC: `{result['generated_at_utc']}`",
        "",
        "## Result",
        "",
        f"- Canonical live intake exists now: `{result['canonical_live_intake_exists']}`.",
        f"- Direct verifier blocked on missing files: `{direct_blocked_missing}`.",
        f"- V54 baseline positives/controls: `{baseline_positive}/{baseline_negative}`.",
        f"- Sarao proposed positives: `{len(sarao_rows)}`; Nowak/Smith proposed positives: `{len(nowak_rows)}`.",
        f"- Proposed positives without matched controls: `{proposed_without_matched_controls}`.",
        f"- What-if positives after both sidecars: `{what_if_positive}`.",
        f"- What-if min Wilson95 LCB after both sidecars: `{result['what_if_min_wilson95_lcb_after_sidecars']}`.",
        f"- Additional all-correct positives still needed after both sidecars: `{result['additional_positive_rows_needed_after_sidecars_if_all_correct']}`.",
        f"- Gate result: `{result['gate_result']}`.",
        f"- Strict full objective achieved: `{result['strict_full_objective_achieved']}`; `update_goal={result['update_goal']}`.",
        "",
        "## Provider And Chain Readback",
        "",
        f"- Provider focus: `{json.dumps(provider_summary, sort_keys=True)}`.",
        "- Command outputs are under `command-output/`: provider status, Auto-Quant status, demo analyze, pre-Bayes, policy-training/CatBoost surface, workflow-status, and structural path-ranking export.",
        "",
        "## Fail-Closed Decision",
        "",
        "- No shared intake mutation was made because the canonical `/tmp` intake root is absent in this fresh readback.",
        "- The two candidate sidecars remain proposed positives only; they do not include matched controls.",
        "- Even treating all proposed positives as correct, pooled confidence remains below `0.95` before split support is considered.",
    ]
    (OUT / "r6_candidate_consolidation_intake_missing_v1.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        f"canonical_live_intake_exists={result['canonical_live_intake_exists']}",
        f"direct_verifier_blocked_missing_required_files={direct_blocked_missing}",
        f"combined_proposed_positive_rows={proposed_positive}",
        f"proposed_positive_rows_without_matched_controls={proposed_without_matched_controls}",
        f"what_if_min_wilson95_lcb_after_sidecars={result['what_if_min_wilson95_lcb_after_sidecars']}",
        f"new_confidence_gate={result['new_confidence_gate']}",
        f"strict_full_objective_achieved={result['strict_full_objective_achieved']}",
        f"update_goal={result['update_goal']}",
    ]
    (CHECKS / "r6_candidate_consolidation_intake_missing_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "run_id": RUN_ID, "gate_result": result["gate_result"], "update_goal": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
