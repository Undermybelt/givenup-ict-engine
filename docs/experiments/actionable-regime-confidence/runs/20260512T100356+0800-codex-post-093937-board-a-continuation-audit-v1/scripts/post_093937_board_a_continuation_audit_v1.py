#!/usr/bin/env python3
"""Post-093937 Board A continuation audit.

This is a read-only evidence intake. It counts the unregistered 093435 Board B
discovery root, duplicate-guards later roots already registered by concurrent
agents, checks the current direct Manipulation sidecar, and refreshes provider /
Auto-Quant status without promoting any candidate or mutating runtime code.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T100356+0800-codex-post-093937-board-a-continuation-audit-v1"
REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "post-093937-board-a-continuation-audit-v1"
CMD_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

LOCAL_AQ_STATE = Path("/private/tmp/ict-engine-board-a-autoquant-local-cache-data-ready-065613-v1")
DIRECT_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
OWNER_EXPORT_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

ROOTS = {
    "093435_tomac_smoke": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T093435+0800-codex-board-b-aq-first-tomac-smoke-downstream-v1",
    "093820_pair_repair": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T093820+0800-codex-board-b-aq-first-nursery-provider-ltf-pair-repair-v1",
    "093854_htf_nursery": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T093854+0800-codex-board-b-htf-nursery-v1",
    "093937_branch_preservation": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T093937+0800-codex-board-b-execution-candidate-branch-preservation-v1",
}


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


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def run_command(name: str, args: list[str], timeout: int = 120) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=REPO, text=True, capture_output=True, timeout=timeout, check=False)
    stdout_path = CMD_OUT / f"{name}.stdout.txt"
    stderr_path = CMD_OUT / f"{name}.stderr.txt"
    exit_path = CMD_OUT / f"{name}.exit"
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    parsed: Any = None
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = None
    return {
        "command": " ".join(args),
        "returncode": proc.returncode,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
        "exit_path": rel(exit_path),
        "json": parsed,
    }


def parse_metric(text: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def provider_summary(provider_payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not provider_payload:
        return []
    keep = {"ibkr", "ibkr_bridge", "tradingview_mcp", "yfinance", "kraken_cli", "kraken_public"}
    out = []
    for provider in provider_payload.get("providers", []):
        if provider.get("provider_id") in keep:
            out.append(
                {
                    "provider_id": provider.get("provider_id"),
                    "domain": provider.get("domain"),
                    "ready": provider.get("ready"),
                    "status": provider.get("status"),
                    "reason": provider.get("reason"),
                }
            )
    return out


def audit_roots() -> list[dict[str, Any]]:
    tomac_out = read_text(ROOTS["093435_tomac_smoke"] / "raw/auto_quant_run_tomac_one.out")
    pair_repair_out = read_text(ROOTS["093820_pair_repair"] / "command-output/00_run_tomac_pair_repair.out")
    htf_factor_out = read_text(ROOTS["093854_htf_nursery"] / "logs/01_factor_research_htf.out")
    htf_prepare_err = read_text(ROOTS["093854_htf_nursery"] / "logs/02_auto_quant_prepare_htf.err")
    branch_report = read_text(
        ROOTS["093937_branch_preservation"]
        / "execution-candidate-branch-preservation-v1/execution_candidate_branch_preservation_v1.md"
    )
    return [
        {
            "run": "093435_tomac_smoke",
            "path": rel(ROOTS["093435_tomac_smoke"]),
            "exists": ROOTS["093435_tomac_smoke"].exists(),
            "gate": "non_promoting_tomac_smoke_negative_profit",
            "auto_quant_ran": "Result for strategy" in tomac_out,
            "trade_count": parse_metric(tomac_out, "trade_count"),
            "win_rate_pct": parse_metric(tomac_out, "win_rate_pct"),
            "total_profit_pct": parse_metric(tomac_out, "total_profit_pct"),
            "profit_factor": parse_metric(tomac_out, "profit_factor"),
            "sharpe": parse_metric(tomac_out, "sharpe"),
            "promotion": False,
            "reason": "Measured 5 trades but total profit and Sharpe were negative; Board B feedback only.",
        },
        {
            "run": "093820_pair_repair",
            "path": rel(ROOTS["093820_pair_repair"]),
            "exists": ROOTS["093820_pair_repair"].exists(),
            "gate": "non_promoting_pair_repair_no_data_found",
            "exit": read_text(ROOTS["093820_pair_repair"] / "command-output/00_run_tomac_pair_repair.exit").strip(),
            "error_seen": "No data found" in pair_repair_out,
            "promotion": False,
            "reason": "Pair whitelist repair moved past the underscore issue but the measured run had no data.",
        },
        {
            "run": "093854_htf_nursery",
            "path": rel(ROOTS["093854_htf_nursery"]),
            "exists": ROOTS["093854_htf_nursery"].exists(),
            "gate": "non_promoting_htf_prepare_dns_blocked",
            "factor_exit": read_text(ROOTS["093854_htf_nursery"] / "logs/01_factor_research_htf.exit").strip(),
            "prepare_exit": read_text(ROOTS["093854_htf_nursery"] / "logs/02_auto_quant_prepare_htf.exit").strip(),
            "data_ready": '"data_ready": false' not in htf_factor_out and "data_ready=true" in htf_factor_out,
            "dns_error_seen": "Could not contact DNS servers" in htf_prepare_err,
            "promotion": False,
            "reason": "HTF handoff exists, but Auto-Quant prepare failed before data readiness.",
        },
        {
            "run": "093937_branch_preservation",
            "path": rel(ROOTS["093937_branch_preservation"]),
            "exists": ROOTS["093937_branch_preservation"].exists(),
            "gate": "incubation_only_execution_candidate_branch_path_preserved_observe_only",
            "branch_path_preserved": "path now survives to execution-candidate" in branch_report,
            "pre_bayes_gate_status": "pass_neutralized" if "pre_bayes_gate_status=pass_neutralized" in branch_report else None,
            "execution_readiness": "0.4504361163104953"
            if "execution_readiness=0.4504361163104953" in branch_report
            else None,
            "ready": False,
            "promotion": False,
            "reason": "Branch path survives to execution-candidate, but execution remains observe-only.",
        },
    ]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)

    provider_cmd = run_command("provider_status_agent_fresh", ["./target/debug/ict-engine", "provider-status", "--agent"])
    auto_quant_cmd = run_command(
        "auto_quant_status_local_data_ready_fresh",
        ["./target/debug/ict-engine", "auto-quant-status", "--state-dir", str(LOCAL_AQ_STATE)],
    )
    verifier_cmd = run_command(
        "direct_manipulation_row_intake_verifier_fresh",
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(DIRECT_ROOT)],
    )

    owner_required = [
        OWNER_EXPORT_ROOT / "direct_manipulation_positive_rows.csv",
        OWNER_EXPORT_ROOT / "direct_manipulation_matched_controls.csv",
        OWNER_EXPORT_ROOT / "direct_manipulation_provenance.json",
    ]
    sidecar_required = [
        DIRECT_ROOT / "positive_spoofing_layering_rows.csv",
        DIRECT_ROOT / "matched_negative_normal_activity_rows.csv",
        DIRECT_ROOT / "provenance_manifest.json",
    ]

    direct_status = verifier_cmd["json"] if isinstance(verifier_cmd["json"], dict) else {}
    aq_status = auto_quant_cmd["json"] if isinstance(auto_quant_cmd["json"], dict) else {}
    providers = provider_summary(provider_cmd["json"] if isinstance(provider_cmd["json"], dict) else None)

    reviewed_roots = audit_roots()
    checklist = [
        {
            "requirement": "every active root has >=95 confidence and cross-context validation",
            "evidence": "prior Board A scoped map exists, but strict current objective remains blocked by source/control and selected-history gates",
            "status": "not_complete",
        },
        {
            "requirement": "do not disturb multi-agent construction",
            "evidence": "append-only artifact; no existing root edited; 093435 counted and later roots duplicate-guarded as non-promoting feedback",
            "status": "pass",
        },
        {
            "requirement": "use provider/readiness surfaces including IBKR, TradingView, yfinance, Kraken",
            "evidence": rel(Path(provider_cmd["stdout_path"])),
            "status": "pass_readonly",
        },
        {
            "requirement": "use Auto-Quant without inventing status",
            "evidence": rel(Path(auto_quant_cmd["stdout_path"])),
            "status": "pass_readonly",
        },
        {
            "requirement": "use filter / Pre-Bayes / BBN / CatBoost / execution-tree chain",
            "evidence": "093937 confirms execution-candidate branch preservation but observe-only; no new promotion rerun because selected-history/source-control gates are absent",
            "status": "blocked_no_promotion",
        },
        {
            "requirement": "R6 direct manipulation verifier",
            "evidence": rel(Path(verifier_cmd["stdout_path"])),
            "status": "schema_ready_unscored_non_promoting",
        },
        {
            "requirement": "owner-approved source/control export",
            "evidence": "direct_manipulation_* owner-export triplet absent under /tmp/ict-engine-board-a-r6-owner-export-v1",
            "status": "blocked",
        },
        {
            "requirement": "explicit selected history HTF/MTF/LTF",
            "evidence": "latest board text requires explicit selection and no new user selection is encoded in repo artifacts",
            "status": "blocked",
        },
    ]

    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_file": rel(BOARD),
        "board_sha256_before": sha256(BOARD),
        "reviewed_roots": reviewed_roots,
        "provider_status": {
            "command": provider_cmd["command"],
            "returncode": provider_cmd["returncode"],
            "providers": providers,
        },
        "auto_quant_status": {
            "command": auto_quant_cmd["command"],
            "returncode": auto_quant_cmd["returncode"],
            "status": aq_status.get("status"),
            "healthy": aq_status.get("healthy"),
            "dependency_healthy": aq_status.get("dependency_healthy"),
            "data_ready": aq_status.get("data_ready"),
            "managed_dir": aq_status.get("managed_dir"),
        },
        "direct_intake": {
            "root": str(DIRECT_ROOT),
            "sidecar_triplet_present": all(path.exists() for path in sidecar_required),
            "sidecar_files": [str(path) for path in sidecar_required],
            "verifier_returncode": verifier_cmd["returncode"],
            "verifier_status": direct_status.get("status"),
            "positive_rows": direct_status.get("positive_rows"),
            "matched_negative_rows": direct_status.get("matched_negative_rows"),
            "matched_group_count": direct_status.get("matched_group_count"),
            "verifier_next": direct_status.get("next"),
        },
        "owner_export": {
            "root": str(OWNER_EXPORT_ROOT),
            "required_files_present": all(path.exists() for path in owner_required),
            "missing_files": [str(path) for path in owner_required if not path.exists()],
        },
        "gates": {
            "accepted_rows_added": 0,
            "source_control_evidence_acquired": False,
            "explicit_user_selected_history": False,
            "canonical_merge": False,
            "selected_data_autoquant_promotion": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "promotion_allowed": False,
            "update_goal": False,
        },
        "gate_result": "post_093937_board_a_continuation_audit_v1=093435_counted_later_roots_duplicate_guard_non_promoting_goal_not_complete",
        "checklist": checklist,
        "next": "Ask for exactly one explicit selected-history lane: HTF, MTF, or LTF; keep R6/R5/R3 source-control gates fail-closed.",
    }
    write_json(OUT / "post_093937_board_a_continuation_audit_v1.json", payload)
    write_csv(
        OUT / "prompt_to_artifact_checklist_post_093937_v1.csv",
        checklist,
        ["requirement", "evidence", "status"],
    )

    report = f"""# Post-093937 Board A Continuation Audit v1

Run id: `{RUN_ID}`

Mode: `append_only_readonly_non_promoting`

## Scope

This audit counts late Board B discovery root `093435` against Board A without promotion. It rechecks `093820`, `093854`, and `093937` only as duplicate-guard context because concurrent EOF registrations already count those roots. It also refreshes provider status, checks a known local Auto-Quant data-ready state, and reruns the direct Manipulation intake verifier. It does not select `HTF`, `MTF`, or `LTF`, does not approve source/control evidence, does not mutate canonical intake, and does not call `update_goal`.

## Readback

- `093435`: Auto-Quant TOMAC smoke ran and produced `5` trades, win rate `{reviewed_roots[0]['win_rate_pct']}`, total profit `{reviewed_roots[0]['total_profit_pct']}`, Sharpe `{reviewed_roots[0]['sharpe']}`, profit factor `{reviewed_roots[0]['profit_factor']}`. Non-promoting.
- `093820`: pair repair exits `{reviewed_roots[1]['exit']}` with `No data found`. Non-promoting.
- `093854`: HTF factor handoff exits `{reviewed_roots[2]['factor_exit']}`, but prepare exits `{reviewed_roots[2]['prepare_exit']}` with DNS / Binance market-load failure. Non-promoting.
- `093937`: execution-candidate branch path is preserved, but readiness remains `{reviewed_roots[3]['execution_readiness']}` and observe-only. Non-promoting.
- Direct Manipulation sidecar verifier exits `{verifier_cmd['returncode']}` with status `{direct_status.get('status')}`, positives `{direct_status.get('positive_rows')}`, controls `{direct_status.get('matched_negative_rows')}`, matched groups `{direct_status.get('matched_group_count')}`.
- Owner-export `direct_manipulation_*` triplet under `/tmp/ict-engine-board-a-r6-owner-export-v1` is present: `{all(path.exists() for path in owner_required)}`.
- Local Auto-Quant status is `{aq_status.get('status')}`, healthy `{aq_status.get('healthy')}`, data_ready `{aq_status.get('data_ready')}`.

Provider status refresh:
"""
    for provider in providers:
        report += (
            f"- `{provider['provider_id']}` / `{provider['domain']}`: ready={provider['ready']}, "
            f"status=`{provider['status']}`, reason=`{provider['reason']}`.\n"
        )
    report += f"""
## Decision

Gate: `{payload['gate_result']}`.

Accepted rows added `0`; source/control evidence acquired false; explicit user-selected history false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed false; `update_goal=false`.

## Next

Ask for exactly one explicit selected-history lane: `HTF`, `MTF`, or `LTF`; keep R6/R5/R3 source-control gates fail-closed and do not infer the selection from agent artifacts.
"""
    (OUT / "post_093937_board_a_continuation_audit_v1.md").write_text(report, encoding="utf-8")

    assertions = {
        "provider_status_exit_0": provider_cmd["returncode"] == 0,
        "auto_quant_status_exit_0": auto_quant_cmd["returncode"] == 0,
        "direct_verifier_exit_0": verifier_cmd["returncode"] == 0,
        "direct_verifier_schema_ready_unscored": direct_status.get("status") == "schema_ready_unscored",
        "owner_export_triplet_absent": not all(path.exists() for path in owner_required),
        "all_late_roots_present": all(item["exists"] for item in reviewed_roots),
        "promotion_allowed_false": payload["gates"]["promotion_allowed"] is False,
        "update_goal_false": payload["gates"]["update_goal"] is False,
        "strict_full_objective_false": payload["gates"]["strict_full_objective"] is False,
    }
    write_json(CHECKS / "post_093937_board_a_continuation_audit_v1_assertions.json", assertions)
    (CHECKS / "post_093937_board_a_continuation_audit_v1_assertions.out").write_text(
        "\n".join(f"{key}={value}" for key, value in sorted(assertions.items())) + "\n",
        encoding="utf-8",
    )
    return 0 if all(assertions.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
