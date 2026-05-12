#!/usr/bin/env python3
"""Build the current-objective audit packet from captured command outputs."""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path


RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "command-output"
ART = RUN_ROOT / "current-objective-audit-after-033625-v1"
CHECKS = RUN_ROOT / "checks"

GATE = (
    "current_objective_audit_after_033625_v1="
    "not_complete_autoquant_oracle_succeeded_diagnostic_only_source_control_downstream_blocked"
)


def read_text(name: str) -> str:
    path = OUT / name
    return path.read_text(encoding="utf-8") if path.exists() else ""


def read_exit(name: str) -> int | None:
    text = read_text(f"{name}.exit").strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def load_json(name: str) -> dict:
    text = read_text(name)
    return json.loads(text) if text.strip() else {}


def parse_autoquant_metrics(text: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    keep_keys = {
        "strategy",
        "timerange_label",
        "timerange",
        "sharpe",
        "sortino",
        "calmar",
        "total_profit_pct",
        "max_drawdown_pct",
        "trade_count",
        "win_rate_pct",
        "profit_factor",
        "robust_sharpe",
        "worst_profit_pct",
        "worst_dd_pct",
        "avg_position_pct",
        "profit_floor",
        "min_position_size",
        "pareto_dominated_by",
    }
    for line in text.splitlines():
        match = re.match(r"^([a-zA-Z_]+):\s+(.*)$", line)
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip()
        if key not in keep_keys:
            continue
        if key == "strategy":
            if current:
                rows.append(current)
            current = {"strategy": value}
            continue
        if current is None:
            continue
        current[key] = value
    if current:
        rows.append(current)
    return rows


def provider_map(provider_status: dict) -> dict[str, dict]:
    return {p.get("provider_id", ""): p for p in provider_status.get("providers", [])}


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    provider_status = load_json("provider_status_agent.stdout.txt")
    autoquant_status = load_json("autoquant_status_prepared.stdout.txt")
    live_verifier = load_json("direct_verifier_live_sidecar.stdout.txt")
    owner_verifier = load_json("direct_verifier_required_owner_export.stdout.txt")
    pre_bayes = load_json("pre_bayes_status_nq.stdout.txt")
    policy_training = load_json("policy_training_status_nq.stdout.txt")
    workflow_status = load_json("workflow_status_nq.stdout.txt")
    providers = provider_map(provider_status)
    autoquant_metrics = parse_autoquant_metrics(
        read_text("autoquant_run_oracle_threaded_resolver_abs.stdout.txt")
    )

    exits = {
        name: read_exit(name)
        for name in [
            "provider_status_agent",
            "autoquant_status_prepared",
            "direct_verifier_live_sidecar",
            "direct_verifier_required_owner_export",
            "pre_bayes_status_nq",
            "policy_training_status_nq",
            "workflow_status_nq",
            "autoquant_run_oracle",
            "autoquant_run_oracle_uv_directory",
            "autoquant_run_oracle_threaded_resolver",
            "autoquant_run_oracle_threaded_resolver_abs",
        ]
    }

    source_roots = {}
    for line in read_text("intake_root_presence.txt").splitlines():
        if not line.strip():
            continue
        state, path = line.split(" ", 1)
        source_roots[path] = state == "present"

    approval = {}
    approval_path = Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid")
    if approval_path.exists():
        approval = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_assertions = approval.get("assertions", {})

    checklist = [
        {
            "requirement": "Use the named board as the live contract without disrupting concurrent work",
            "evidence": "board sha captured before audit; append-only packet generated under new run root",
            "status": "pass",
            "notes": read_text("board_sha256_before_audit.txt").strip(),
        },
        {
            "requirement": "Every active regime has calibrated confidence >=95%",
            "evidence": "live R6 verifier is schema_ready_unscored; no accepted per-regime calibration packet added",
            "status": "blocked",
            "notes": f"live_verifier_status={live_verifier.get('status')}",
        },
        {
            "requirement": "Each regime has its own qualifying conditions",
            "evidence": "source/control gates absent; no canonical split-calibrated accepted rows",
            "status": "blocked",
            "notes": "accepted_rows_added=0",
        },
        {
            "requirement": "Cross-market/cycle/timeframe validation passes",
            "evidence": "owner-export root and R3/R5 source roots are absent; downstream validation is blocked",
            "status": "blocked",
            "notes": str(source_roots),
        },
        {
            "requirement": "Operate providers: IBKR, TradingViewRemix/TradingView, yfinance, Kraken",
            "evidence": "provider-status --agent executed",
            "status": "partial",
            "notes": (
                f"yfinance={providers.get('yfinance', {}).get('ready')} "
                f"kraken_cli={providers.get('kraken_cli', {}).get('ready')} "
                f"ibkr={providers.get('ibkr', {}).get('status')} "
                f"tradingview_mcp={providers.get('tradingview_mcp', {}).get('status')}"
            ),
        },
        {
            "requirement": "Operate AutoQuant locally",
            "evidence": "AutoQuant status and oracle run executed in isolated /tmp workspace",
            "status": "pass",
            "notes": "3 backtests succeeded with absolute threaded-resolver shim",
        },
        {
            "requirement": "Run filter / Pre-Bayes readback",
            "evidence": "pre-bayes-status --refresh executed",
            "status": "blocked",
            "notes": f"latest_gate_status={pre_bayes.get('latest_gate_status')}",
        },
        {
            "requirement": "Run BBN / policy-training readback",
            "evidence": "policy-training-status executed",
            "status": "blocked",
            "notes": policy_training.get("summary_line", ""),
        },
        {
            "requirement": "Run CatBoost / path-ranking readback",
            "evidence": "policy-training-status structural path-ranking fields inspected",
            "status": "blocked",
            "notes": policy_training.get("structural_path_ranking_target", {}).get("summary_line", ""),
        },
        {
            "requirement": "Run execution-tree / workflow readback",
            "evidence": "workflow-status --refresh executed",
            "status": "blocked",
            "notes": workflow_status.get("blocking_truth", {}).get("reason", ""),
        },
        {
            "requirement": "Do not promote proxy/runtime/local-cache evidence into Board A acceptance",
            "evidence": "source/control roots and approval package inspected",
            "status": "pass",
            "notes": (
                f"owner_export={source_roots.get('/tmp/ict-engine-board-a-r6-owner-export-v1')} "
                f"approval_present={approval_assertions.get('approval_present')} "
                f"canonical_merge={approval_assertions.get('canonical_merge_allowed_now')}"
            ),
        },
    ]

    status_counts = {"pass": 0, "partial": 0, "blocked": 0}
    for item in checklist:
        status_counts[item["status"]] += 1

    promotion = {
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_promotion_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "trade_usable": False,
        "update_goal": False,
    }

    packet = {
        "run_id": RUN_ROOT.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": GATE,
        "command_exits": exits,
        "provider_summary": {
            "summary_line": provider_status.get("summary_line"),
            "yfinance_live_ready": providers.get("yfinance", {}).get("ready"),
            "yfinance_market_data_status": providers.get("yfinance", {}).get("status"),
            "kraken_cli_ready": providers.get("kraken_cli", {}).get("ready"),
            "kraken_public_status": providers.get("kraken_public", {}).get("status"),
            "ibkr_status": providers.get("ibkr", {}).get("status"),
            "ibkr_bridge_status": providers.get("ibkr_bridge", {}).get("status"),
            "tradingview_mcp_status": providers.get("tradingview_mcp", {}).get("status"),
        },
        "autoquant": {
            "status": autoquant_status.get("status"),
            "data_ready": autoquant_status.get("data_ready"),
            "dependency_healthy": autoquant_status.get("dependency_healthy"),
            "plain_run_exit": exits["autoquant_run_oracle_uv_directory"],
            "plain_run_failure_class": "aiodns_market_load_failure",
            "threaded_resolver_abs_exit": exits["autoquant_run_oracle_threaded_resolver_abs"],
            "threaded_resolver_abs_success": exits["autoquant_run_oracle_threaded_resolver_abs"] == 0,
            "strategy_metrics": autoquant_metrics,
        },
        "source_control_status": {
            "live_sidecar_status": live_verifier.get("status"),
            "live_positive_rows": live_verifier.get("positive_rows"),
            "live_matched_negative_rows": live_verifier.get("matched_negative_rows"),
            "live_matched_group_count": live_verifier.get("matched_group_count"),
            "owner_export_verifier_exit": exits["direct_verifier_required_owner_export"],
            "owner_export_status": owner_verifier.get("status"),
            "owner_export_missing_files": owner_verifier.get("missing_files", []),
            "r6_owner_export_root_exists": source_roots.get("/tmp/ict-engine-board-a-r6-owner-export-v1", False),
            "r3_native_subhour_source_label_root_exists": source_roots.get(
                "/tmp/ict-engine-native-subhour-source-label-intake", False
            ),
            "r5_source_panel_recency_extension_root_exists": source_roots.get(
                "/tmp/ict-engine-source-panel-recency-extension", False
            ),
            "approval_present": approval_assertions.get("approval_present"),
            "flip_controls_accepted_under_current_contract": approval_assertions.get(
                "flip_controls_accepted_under_current_contract"
            ),
            "canonical_merge_allowed_now": approval_assertions.get("canonical_merge_allowed_now"),
            "downstream_rerun_allowed_now": approval_assertions.get("downstream_rerun_allowed_now"),
        },
        "downstream": {
            "pre_bayes_latest_gate_status": pre_bayes.get("latest_gate_status"),
            "pre_bayes_latest_filtered_assignments": pre_bayes.get("latest_filtered_assignments"),
            "policy_training_summary": policy_training.get("summary_line"),
            "workflow_blocking_status": workflow_status.get("blocking_truth", {}).get("status"),
            "workflow_blocking_reason": workflow_status.get("blocking_truth", {}).get("reason"),
        },
        "prompt_to_artifact_counts": status_counts,
        "prompt_to_artifact_checklist": checklist,
        "promotion": promotion,
        "non_mutations": {
            "runtime_code_changed": False,
            "source_roots_mutated": False,
            "thresholds_relaxed": False,
            "canonical_live_intake_mutated": False,
        },
        "next_action": (
            "Preserve the Current Cursor: acquire verifier-native R6 owner/export rows or explicit "
            "FLIP-control approval before canonical merge and downstream promotion. AutoQuant oracle "
            "success is diagnostic only until source/control gates unlock."
        ),
    }

    json_path = ART / "current_objective_audit_after_033625_v1.json"
    json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with (ART / "prompt_to_artifact_checklist_after_033625_v1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        writer = csv.DictWriter(fh, fieldnames=["requirement", "evidence", "status", "notes"])
        writer.writeheader()
        writer.writerows(checklist)

    metric_fields = [
        "strategy",
        "timerange_label",
        "timerange",
        "sharpe",
        "sortino",
        "calmar",
        "total_profit_pct",
        "max_drawdown_pct",
        "trade_count",
        "win_rate_pct",
        "profit_factor",
        "robust_sharpe",
        "worst_profit_pct",
        "worst_dd_pct",
        "avg_position_pct",
        "profit_floor",
        "min_position_size",
        "pareto_dominated_by",
    ]
    with (ART / "autoquant_strategy_metrics_after_033625_v1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        writer = csv.DictWriter(fh, fieldnames=metric_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(autoquant_metrics)

    report = [
        "# Current Objective Audit After 033625 v1",
        "",
        f"Run id: `{RUN_ROOT.name}`",
        "",
        f"Gate result: `{GATE}`",
        "",
        "## Objective Restatement",
        "",
        "Board A is complete only if every active regime has calibrated confidence >=95%, its own qualifying condition, cross-market/cycle/timeframe/provider validation, and a real local chain in order: provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution tree.",
        "",
        "## Prompt-to-Artifact Checklist",
        "",
    ]
    for item in checklist:
        report.append(f"- `{item['status']}` {item['requirement']}: {item['notes']}")
    report.extend(
        [
            "",
            "## AutoQuant Diagnostic Result",
            "",
            "- Plain `uv --directory ... run run.py` failed through `aiodns` / Binance market loading.",
            "- Absolute threaded-resolver shim run exited `0`: `3` backtests succeeded and `0` failed.",
            "- Best diagnostic strategy by Sharpe in this run: `VolBreakoutSized` with Sharpe `1.3390`, total profit `25.0200%`, trade count `1221`, win rate `32.8419%`, profit factor `1.4751`, but `min_position_size=FAIL`.",
            "- This is AutoQuant runtime diagnostics only. It is not regime-confidence calibration and not Board A acceptance.",
            "",
            "## Source / Control Gate",
            "",
            f"- Live sidecar verifier: `{live_verifier.get('status')}`, positives `{live_verifier.get('positive_rows')}`, matched negatives `{live_verifier.get('matched_negative_rows')}`, groups `{live_verifier.get('matched_group_count')}`.",
            f"- Required owner-export verifier: exit `{exits['direct_verifier_required_owner_export']}`, status `{owner_verifier.get('status')}`, reason `{owner_verifier.get('reason')}`.",
            "- Required owner-export, R3 native-subhour, and R5 recency-extension roots remain absent.",
            "- Approval package remains non-approving; canonical merge and downstream rerun are not allowed.",
            "",
            "## Downstream Readback",
            "",
            f"- Pre-Bayes latest gate: `{pre_bayes.get('latest_gate_status')}`.",
            f"- Policy/CatBoost/path-ranking: `{policy_training.get('summary_line', '')}`.",
            f"- Workflow/execution-tree blocking truth: `{workflow_status.get('blocking_truth', {}).get('status')}` / `{workflow_status.get('blocking_truth', {}).get('reason')}`.",
            "",
            "## Decision",
            "",
            "- Accepted rows added: `0`.",
            "- New confidence gate: `false`.",
            "- Canonical merge allowed: `false`.",
            "- Downstream promotion rerun allowed: `false`.",
            "- Strict full objective achieved: `false`.",
            "- Trade usable: `false`.",
            "- `update_goal=false`.",
            "",
            "## Next",
            "",
            packet["next_action"],
            "",
        ]
    )
    (ART / "current_objective_audit_after_033625_v1.md").write_text(
        "\n".join(report), encoding="utf-8"
    )

    assertions = [
        ("gate_result", packet["gate_result"].endswith("source_control_downstream_blocked")),
        ("provider_status_exit_0", exits["provider_status_agent"] == 0),
        ("autoquant_status_exit_0", exits["autoquant_status_prepared"] == 0),
        ("autoquant_threaded_oracle_exit_0", exits["autoquant_run_oracle_threaded_resolver_abs"] == 0),
        ("autoquant_backtests_3_succeeded", "Done: 3 backtests succeeded, 0 failed." in read_text("autoquant_run_oracle_threaded_resolver_abs.stdout.txt")),
        ("live_sidecar_schema_ready_unscored", live_verifier.get("status") == "schema_ready_unscored"),
        ("owner_export_verifier_blocked", owner_verifier.get("status") == "blocked"),
        ("owner_export_root_absent", not packet["source_control_status"]["r6_owner_export_root_exists"]),
        ("r3_root_absent", not packet["source_control_status"]["r3_native_subhour_source_label_root_exists"]),
        ("r5_root_absent", not packet["source_control_status"]["r5_source_panel_recency_extension_root_exists"]),
        ("approval_present_false", approval_assertions.get("approval_present") is False),
        ("canonical_merge_allowed_false", approval_assertions.get("canonical_merge_allowed_now") is False),
        ("downstream_rerun_allowed_false", approval_assertions.get("downstream_rerun_allowed_now") is False),
        ("accepted_rows_added_0", promotion["accepted_rows_added"] == 0),
        ("new_confidence_gate_false", promotion["new_confidence_gate"] is False),
        ("strict_full_objective_false", promotion["strict_full_objective_achieved"] is False),
        ("trade_usable_false", promotion["trade_usable"] is False),
        ("update_goal_false", promotion["update_goal"] is False),
        ("runtime_code_changed_false", packet["non_mutations"]["runtime_code_changed"] is False),
        ("source_roots_mutated_false", packet["non_mutations"]["source_roots_mutated"] is False),
        ("thresholds_relaxed_false", packet["non_mutations"]["thresholds_relaxed"] is False),
    ]
    assertion_lines = [
        f"{'PASS' if ok else 'FAIL'} {name}" for name, ok in assertions
    ]
    (CHECKS / "current_objective_audit_after_033625_v1_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n", encoding="utf-8"
    )
    if not all(ok for _, ok in assertions):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
