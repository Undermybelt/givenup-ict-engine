#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260512T083001+0800-codex-current-objective-audit-after-082430-082629-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "current-objective-audit-after-082430-082629-v1"
CHECKS_DIR = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

ASSERTION_INPUTS = [
    (
        "082240_current_objective_after_081705",
        "docs/experiments/actionable-regime-confidence/runs/20260512T082240+0800-codex-current-objective-audit-after-081705-v1/checks/current_objective_audit_after_081705_v1_assertions.out",
        "objective_audit",
    ),
    (
        "082302_r6_dispatch_arrival",
        "docs/experiments/actionable-regime-confidence/runs/20260512T082302+0800-codex-r6-owner-export-current-dispatch-and-arrival-readback-after-081705-v1/checks/r6_owner_export_current_dispatch_and_arrival_readback_after_081705_v1_assertions.out",
        "source_control",
    ),
    (
        "082314_arrival_after_081705",
        "docs/experiments/actionable-regime-confidence/runs/20260512T082314+0800-codex-source-control-arrival-poll-after-081705-v1/checks/source_control_arrival_poll_after_081705_v1_assertions.out",
        "source_control",
    ),
    (
        "082337_terminal_correction",
        "docs/experiments/actionable-regime-confidence/runs/20260512T082337+0800-codex-post-081705-required-root-dispatch-gate-v1/checks/post_081705_required_root_dispatch_gate_v1_assertions.out",
        "source_control",
    ),
    (
        "082430_runtime_readiness",
        "docs/experiments/actionable-regime-confidence/runs/20260512T082430+0800-codex-runtime-readiness-after-082215-v1/checks/runtime_readiness_after_082215_v1_assertions.out",
        "runtime_chain",
    ),
    (
        "082458_arrival_after_082240",
        "docs/experiments/actionable-regime-confidence/runs/20260512T082458+0800-codex-source-control-arrival-poll-after-082240-v1/checks/source_control_arrival_poll_after_082240_v1_assertions.out",
        "source_control",
    ),
    (
        "082629_local_databento",
        "docs/experiments/actionable-regime-confidence/runs/20260512T082629+0800-codex-local-databento-archive-readback-after-082240-v1/checks/local_databento_archive_readback_after_082240_v1_assertions.out",
        "source_control",
    ),
    (
        "082720_current_objective_after_082458",
        "docs/experiments/actionable-regime-confidence/runs/20260512T082720+0800-codex-current-objective-audit-after-082458-v1/checks/current_objective_audit_after_082458_v1_assertions.out",
        "objective_audit",
    ),
]


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_assertions(path: Path) -> dict[str, str]:
    parsed: dict[str, str] = {}
    if not path.is_file():
        return parsed
    for raw in path.read_text(errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("PASS ") and "=" in line[5:]:
            key, value = line[5:].split("=", 1)
            parsed[key.strip()] = value.strip()
        elif line.startswith("PASS "):
            parsed["pass_marker"] = line[5:].strip()
        elif "=" in line:
            key, value = line.split("=", 1)
            parsed[key.strip()] = value.strip()
    return parsed


def is_false(value: str | None) -> bool:
    return str(value).strip().lower() in {"false", "0", "no"}


def is_true(value: str | None) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    assertion_rows = []
    merged: dict[str, str] = {}
    missing_assertion_roots = 0
    for evidence_id, rel_path, category in ASSERTION_INPUTS:
        path = REPO / rel_path
        parsed = parse_assertions(path)
        if not parsed:
            missing_assertion_roots += 1
        for key, value in parsed.items():
            merged[f"{evidence_id}.{key}"] = value
        assertion_rows.append(
            {
                "evidence_id": evidence_id,
                "category": category,
                "path": rel_path,
                "exists": path.is_file(),
                "gate_result": parsed.get("gate_result", parsed.get("gate", "")),
                "accepted_rows_added": parsed.get("accepted_rows_added", ""),
                "valid_required_root_unlock": parsed.get("valid_required_root_unlock", ""),
                "source_control_evidence_acquired": parsed.get("source_control_evidence_acquired", ""),
                "canonical_merge": parsed.get("canonical_merge", ""),
                "downstream_promotion_rerun": parsed.get("downstream_promotion_rerun", ""),
                "update_goal": parsed.get("update_goal", ""),
            }
        )

    runtime = parse_assertions(
        REPO
        / "docs/experiments/actionable-regime-confidence/runs/20260512T082430+0800-codex-runtime-readiness-after-082215-v1/checks/runtime_readiness_after_082215_v1_assertions.out"
    )
    databento = parse_assertions(
        REPO
        / "docs/experiments/actionable-regime-confidence/runs/20260512T082629+0800-codex-local-databento-archive-readback-after-082240-v1/checks/local_databento_archive_readback_after_082240_v1_assertions.out"
    )
    latest_objective = parse_assertions(
        REPO
        / "docs/experiments/actionable-regime-confidence/runs/20260512T082720+0800-codex-current-objective-audit-after-082458-v1/checks/current_objective_audit_after_082458_v1_assertions.out"
    )

    source_control_unlock = False
    if any(is_true(row["valid_required_root_unlock"]) for row in assertion_rows):
        source_control_unlock = True
    source_control_acquired = any(is_true(row["source_control_evidence_acquired"]) for row in assertion_rows)
    canonical_merge = any(is_true(row["canonical_merge"]) for row in assertion_rows)
    downstream = any(is_true(row["downstream_promotion_rerun"]) for row in assertion_rows)
    update_goal = any(is_true(row["update_goal"]) for row in assertion_rows)

    checklist = [
        {
            "requirement_id": "R1_named_board_and_artifacts",
            "requirement": "Use the named Board A markdown and repo-local docs/experiments artifacts.",
            "evidence": f"board_exists={BOARD.is_file()}; board_sha256={sha256(BOARD)}; assertion_roots_checked={len(ASSERTION_INPUTS)}; missing_assertion_roots={missing_assertion_roots}",
            "status": "pass" if BOARD.is_file() and missing_assertion_roots == 0 else "fail_blocked",
        },
        {
            "requirement_id": "R2_every_regime_95_cross_context",
            "requirement": "Every regime/root reaches 95%+ calibrated confidence and survives other market/period/timeframe validation.",
            "evidence": f"latest_blocked_requirements={latest_objective.get('blocked_requirements')}; latest_partial_requirements={latest_objective.get('partial_requirements')}; strict_full_objective={latest_objective.get('strict_full_objective')}",
            "status": "fail_blocked",
        },
        {
            "requirement_id": "R3_real_runtime_chain_operated",
            "requirement": "Operate ict-engine/AutoQuant/provider/pre-Bayes/BBN/CatBoost/path-ranking/execution-tree surfaces, not prose only.",
            "evidence": f"commands_run={runtime.get('commands_run')}; commands_exit0={runtime.get('commands_exit0')}; provider_surface_mentions_all={runtime.get('provider_surface_mentions_all')}; promotion_allowed={runtime.get('promotion_allowed')}",
            "status": "partial_blocked" if is_true(runtime.get("all_commands_exit0")) else "fail_blocked",
        },
        {
            "requirement_id": "R4_provider_surfaces_checked",
            "requirement": "IBKR, TradingViewRemix, yfinance, and Kraken provider surfaces are checked.",
            "evidence": f"ibkr={runtime.get('provider_ibkr_visible')}; tradingviewremix={runtime.get('provider_tradingviewremix_visible')}; yfinance={runtime.get('provider_yfinance_visible')}; kraken={runtime.get('provider_kraken_visible')}",
            "status": "pass" if is_true(runtime.get("provider_surface_mentions_all")) else "fail_blocked",
        },
        {
            "requirement_id": "R5_source_control_unlock",
            "requirement": "Acquire valid R6 owner-export controls or R5 recency or accepted R3 native-subhour source/control root before promotion.",
            "evidence": f"valid_required_root_unlock={source_control_unlock}; source_control_evidence_acquired={source_control_acquired}; databento_gate={databento.get('gate_result')}; databento_no_order_lifecycle_columns={databento.get('no_order_lifecycle_columns')}",
            "status": "fail_blocked",
        },
        {
            "requirement_id": "R6_no_proxy_completion",
            "requirement": "Do not accept OHLCV-only/proxy artifacts or runtime readiness as completion.",
            "evidence": f"local_databento_dataset={databento.get('dataset')}; schema={databento.get('schema')}; gate={databento.get('gate_result')}; downstream_promotion_rerun={downstream}",
            "status": "pass" if is_false(databento.get("source_control_evidence_acquired")) and not downstream else "fail_blocked",
        },
        {
            "requirement_id": "R7_no_downstream_without_unlock",
            "requirement": "Do not run or promote canonical/downstream chain as accepted while source/control gates are false.",
            "evidence": f"canonical_merge={canonical_merge}; downstream_promotion_rerun={downstream}; selected_data_autoquant_promotion={runtime.get('selected_data_autoquant_promotion')}",
            "status": "pass" if not canonical_merge and not downstream else "fail_blocked",
        },
        {
            "requirement_id": "R8_update_goal_allowed",
            "requirement": "Only call update_goal when the full objective is actually achieved.",
            "evidence": f"update_goal_any={update_goal}; latest_update_goal={latest_objective.get('update_goal')}",
            "status": "fail_blocked",
        },
    ]

    blocked_requirements = sum(1 for row in checklist if row["status"] == "fail_blocked")
    partial_requirements = sum(1 for row in checklist if row["status"] == "partial_blocked")
    strict_full_objective = blocked_requirements == 0 and partial_requirements == 0

    payload = {
        "run_id": RUN_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "board_sha256_before_artifact": sha256(BOARD),
        "objective_restatement": (
            "Each Board A regime/root must have >=95% calibrated confidence with cross-market, cross-period, "
            "and cross-timeframe validation; real provider/AutoQuant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree "
            "surfaces must be operated; no completion claim is allowed until source/control gates and downstream promotion evidence are satisfied."
        ),
        "assertions_checked": assertion_rows,
        "checklist": checklist,
        "missing_assertion_roots": missing_assertion_roots,
        "blocked_requirements": blocked_requirements,
        "partial_requirements": partial_requirements,
        "accepted_rows_added": 0,
        "valid_required_root_unlock": source_control_unlock,
        "source_control_evidence_acquired": source_control_acquired,
        "canonical_merge": canonical_merge,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": downstream,
        "strict_full_objective": strict_full_objective,
        "trade_usable": False,
        "update_goal": False,
        "gate_result": "current_objective_audit_after_082430_082629_v1=not_complete_runtime_observed_source_control_absent",
        "next_action": (
            "Continue source/control acquisition only: owner-approved CME/Cboe/CFE/FINRA/CAT-like export with matched normal controls, "
            "explicit FLIP-as-control approval, or verifier-native R5/R3 source roots before canonical merge or downstream promotion."
        ),
    }

    json_path = OUT_DIR / "current_objective_audit_after_082430_082629_v1.json"
    checklist_path = OUT_DIR / "prompt_to_artifact_checklist_after_082430_082629_v1.csv"
    assertions_csv_path = OUT_DIR / "assertion_roots_after_082430_082629_v1.csv"
    md_path = OUT_DIR / "current_objective_audit_after_082430_082629_v1.md"
    assertions_path = CHECKS_DIR / "current_objective_audit_after_082430_082629_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    with checklist_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["requirement_id", "requirement", "evidence", "status"])
        writer.writeheader()
        writer.writerows(checklist)

    with assertions_csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(assertion_rows[0].keys()))
        writer.writeheader()
        writer.writerows(assertion_rows)

    md_lines = [
        "# Current Objective Audit After 082430 / 082629 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Gate result: `current_objective_audit_after_082430_082629_v1=not_complete_runtime_observed_source_control_absent`",
        "",
        f"Board sha256 before artifact: `{payload['board_sha256_before_artifact']}`",
        "",
        "## Objective Restatement",
        "",
        payload["objective_restatement"],
        "",
        "## Checklist",
        "",
        "| requirement | status | evidence |",
        "|---|---|---|",
    ]
    for row in checklist:
        md_lines.append(f"| `{row['requirement_id']}` | `{row['status']}` | {row['evidence']} |")
    md_lines += [
        "",
        "## Decision",
        "",
        f"- Missing assertion roots: `{missing_assertion_roots}`.",
        f"- Blocked requirements: `{blocked_requirements}`.",
        f"- Partial requirements: `{partial_requirements}`.",
        f"- Valid required-root unlock: `{source_control_unlock}`.",
        f"- Source/control evidence acquired: `{source_control_acquired}`.",
        f"- Canonical merge: `{canonical_merge}`.",
        f"- Downstream promotion rerun: `{downstream}`.",
        f"- Strict full objective: `{strict_full_objective}`.",
        f"- `update_goal`: `False`.",
        "",
        "## Next",
        "",
        payload["next_action"],
        "",
    ]
    md_path.write_text("\n".join(md_lines))

    assertions = [
        f"gate_result={payload['gate_result']}",
        f"assertion_roots_checked={len(assertion_rows)}",
        f"missing_assertion_roots={missing_assertion_roots}",
        f"blocked_requirements={blocked_requirements}",
        f"partial_requirements={partial_requirements}",
        "accepted_rows_added=0",
        f"valid_required_root_unlock={str(source_control_unlock).lower()}",
        f"source_control_evidence_acquired={str(source_control_acquired).lower()}",
        f"canonical_merge={str(canonical_merge).lower()}",
        "selected_data_autoquant_promotion=false",
        f"downstream_promotion_rerun={str(downstream).lower()}",
        f"strict_full_objective={str(strict_full_objective).lower()}",
        "trade_usable=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n")

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
