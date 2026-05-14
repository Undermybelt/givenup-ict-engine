#!/usr/bin/env python3
"""Materialize the 020037 read-only runtime-chain refresh report."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "readonly-runtime-chain-refresh-after-015533-v1"
CMD = ROOT / "command-output"


def read_json(name: str) -> dict:
    return json.loads((CMD / f"{name}.stdout.txt").read_text())


def read_exit(name: str) -> int:
    return int((CMD / f"{name}.exit").read_text().strip())


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (ROOT / "checks").mkdir(parents=True, exist_ok=True)

    names = [
        "provider_status_agent",
        "provider_status_tradingview_mcp",
        "provider_status_yfinance",
        "auto_quant_status_json",
        "analyze_demo_agent",
        "pre_bayes_status_json",
        "policy_training_status_json",
        "workflow_status_execution_candidate_agent",
        "workflow_status_structural_path_bundle_agent",
        "workflow_status_full_json",
        "export_structural_path_ranking_target",
    ]
    exits = {name: read_exit(name) for name in names}

    provider = read_json("provider_status_agent")
    tv = read_json("provider_status_tradingview_mcp")
    yf = read_json("provider_status_yfinance")
    aq = read_json("auto_quant_status_json")
    analyze = read_json("analyze_demo_agent")
    pre_bayes = read_json("pre_bayes_status_json")
    policy = read_json("policy_training_status_json")
    exec_candidate = read_json("workflow_status_execution_candidate_agent")
    structural_bundle = read_json("workflow_status_structural_path_bundle_agent")
    workflow_full = read_json("workflow_status_full_json")
    export_target = read_json("export_structural_path_ranking_target")

    entry_models = policy.get("entry_models", [])
    matched_rows = sum(int(m.get("matched_rows") or 0) for m in entry_models)
    ranker_runtime = policy.get("structural_path_ranking_runtime", {})
    artifact_summary = workflow_full.get("artifact_decision_summary", {})

    root_status_rows = []
    for path in [
        "/tmp/ict-engine-board-a-r6-owner-export-v1",
        "/tmp/ict-engine-native-subhour-source-label-intake",
        "/tmp/ict-engine-source-panel-recency-extension",
        "/tmp/ict-engine-source-label-equivalence-intake",
    ]:
        p = Path(path)
        root_status_rows.append(
            {
                "path": path,
                "exists": str(p.exists()).lower(),
                "top_level_files": sum(1 for child in p.iterdir() if child.is_file()) if p.exists() else 0,
            }
        )

    command_rows = []
    for name in names:
        command_rows.append(
            {
                "command_id": name,
                "exit_code": exits[name],
                "stdout_file": f"command-output/{name}.stdout.txt",
                "stderr_file": f"command-output/{name}.stderr.txt",
            }
        )

    provider_rows = [
        {
            "surface": "provider_status_agent",
            "summary": provider.get("summary_line", ""),
            "ready": "partial",
            "promotion_note": "overall provider catalog callable but market_data only 1/7 ready",
        },
        {
            "surface": "provider_status_tradingview_mcp",
            "summary": tv.get("summary_line", ""),
            "ready": "false",
            "promotion_note": "TradingViewRemix/MCP remains connectivity-blocked",
        },
        {
            "surface": "provider_status_yfinance",
            "summary": yf.get("summary_line", ""),
            "ready": "true",
            "promotion_note": "yfinance is ready but does not supply missing source/control roots by itself",
        },
    ]

    summary = {
        "run_id": "20260512T020037-codex-readonly-runtime-chain-refresh-after-015533-v1",
        "gate_result": "readonly_runtime_chain_refresh_after_015533_v1=runtime_surfaces_callable_non_promoting_source_control_blocked",
        "all_command_exit_zero": all(code == 0 for code in exits.values()),
        "provider_status_agent": provider.get("summary_line"),
        "tradingview_mcp_status": tv.get("summary_line"),
        "yfinance_status": yf.get("summary_line"),
        "auto_quant_status": aq.get("status"),
        "auto_quant_healthy": aq.get("healthy"),
        "auto_quant_bootstrap_needed": aq.get("bootstrap_needed"),
        "analyze_decision": analyze.get("decision_summary"),
        "analyze_direction": analyze.get("direction"),
        "analyze_pre_bayes_gate": analyze.get("pre_bayes_gate"),
        "execution_gate_status": analyze.get("execution_triage", {}).get("gate_status"),
        "execution_branch": analyze.get("execution_triage", {}).get("branch"),
        "pre_bayes_latest_gate_status": pre_bayes.get("latest_gate_status"),
        "pre_bayes_structural_confidence": pre_bayes.get("latest_canonical_structural_confidence"),
        "pre_bayes_structural_regime": pre_bayes.get("latest_canonical_structural_active_regime"),
        "policy_training_matched_rows": matched_rows,
        "policy_training_entry_models_ready": [m.get("ready") for m in entry_models],
        "structural_path_ranker_runtime_status": ranker_runtime.get("status"),
        "structural_path_ranker_active_match_count": ranker_runtime.get("active_match_count"),
        "execution_candidate_actionable": exec_candidate.get("actionable"),
        "execution_candidate_status": exec_candidate.get("candidate_status"),
        "execution_candidate_gate_status": exec_candidate.get("execution_gate_status"),
        "structural_bundle_direction": structural_bundle.get("direction"),
        "structural_bundle_composite_score": structural_bundle.get("composite_score"),
        "workflow_full_actionable_artifacts": artifact_summary.get("actionable_artifact_count"),
        "workflow_full_consumed_targets": artifact_summary.get("consumed_target_kinds"),
        "workflow_full_consumed_trend_status": artifact_summary.get("consumed_trend_status"),
        "export_rows": export_target.get("rows"),
        "export_mature_rows": export_target.get("mature_rows"),
        "export_rows_with_training_weight": export_target.get("rows_with_training_weight"),
        "export_rows_with_execution_gate_status": export_target.get("rows_with_execution_gate_status"),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_promotion_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "root_status": root_status_rows,
    }

    (OUT / "readonly_runtime_chain_refresh_after_015533_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    write_csv(OUT / "readonly_runtime_command_summary_v1.csv", command_rows)
    write_csv(OUT / "readonly_runtime_selected_provider_status_v1.csv", provider_rows)
    write_csv(OUT / "readonly_runtime_root_status_v1.csv", root_status_rows)

    report = f"""# Read-only Runtime Chain Refresh After 015533 v1

Gate result: `{summary["gate_result"]}`.

This packet materializes the completed command-output root only. It does not mutate runtime code, shared intake roots, R3/R5/R6 roots, provider credentials, Auto-Quant strategies, canonical merge state, or board cursor state.

## Command Coverage

- All captured commands exited zero: `{str(summary["all_command_exit_zero"]).lower()}`.
- Provider catalog: `{summary["provider_status_agent"]}`.
- TradingViewRemix/MCP: `{summary["tradingview_mcp_status"]}`.
- yfinance: `{summary["yfinance_status"]}`.
- Auto-Quant: status `{summary["auto_quant_status"]}`, healthy `{summary["auto_quant_healthy"]}`, bootstrap needed `{summary["auto_quant_bootstrap_needed"]}`.
- Analyze demo: `{summary["analyze_decision"]}`, direction `{summary["analyze_direction"]}`, pre-Bayes gate `{summary["analyze_pre_bayes_gate"]}`, execution gate `{summary["execution_gate_status"]}`, branch `{summary["execution_branch"]}`.
- Pre-Bayes: latest gate `{summary["pre_bayes_latest_gate_status"]}`, structural regime `{summary["pre_bayes_structural_regime"]}`, confidence `{summary["pre_bayes_structural_confidence"]}`.
- Policy/CatBoost readiness: matched rows `{summary["policy_training_matched_rows"]}`; entry models ready `{summary["policy_training_entry_models_ready"]}`.
- Structural path ranker runtime: status `{summary["structural_path_ranker_runtime_status"]}`, active matches `{summary["structural_path_ranker_active_match_count"]}`.
- Execution candidate: actionable `{summary["execution_candidate_actionable"]}`, status `{summary["execution_candidate_status"]}`, gate `{summary["execution_candidate_gate_status"]}`.
- Structural bundle: direction `{summary["structural_bundle_direction"]}`, composite score `{summary["structural_bundle_composite_score"]}`.
- Path-ranking export: rows `{summary["export_rows"]}`, mature rows `{summary["export_mature_rows"]}`, rows with training weight `{summary["export_rows_with_training_weight"]}`, rows with execution gate status `{summary["export_rows_with_execution_gate_status"]}`.

## Acceptance

This is not Board A acceptance evidence. It proves callable runtime surfaces over a demo/read-only state, but it still has no source-owned R6 controls, no explicit `FLIP` approval, no canonical merge, no accepted new confidence gate, no mature path-ranking rows, no policy/CatBoost matched rows, and no trade-usable downstream promotion.
"""
    (OUT / "readonly_runtime_chain_refresh_after_015533_v1.md").write_text(report)

    assertions = [
        ("all_commands_exit_zero", summary["all_command_exit_zero"]),
        ("auto_quant_non_promoting", summary["auto_quant_status"] == "missing_dependency"),
        ("analyze_observe_only", summary["analyze_decision"] == "Observe only"),
        ("pre_bayes_pass_neutralized", summary["pre_bayes_latest_gate_status"] == "pass_neutralized"),
        ("policy_training_no_matched_rows", summary["policy_training_matched_rows"] == 0),
        ("execution_candidate_not_actionable", summary["execution_candidate_actionable"] is False),
        ("path_export_no_mature_rows", summary["export_mature_rows"] == 0),
        ("no_canonical_merge", summary["canonical_merge_allowed"] is False),
        ("no_goal_update", summary["update_goal"] is False),
    ]
    assertion_lines = []
    ok = True
    for name, passed in assertions:
        assertion_lines.append(f"{name}: {'PASS' if passed else 'FAIL'}")
        ok = ok and bool(passed)
    assertion_lines.append(f"overall: {'PASS' if ok else 'FAIL'}")
    (ROOT / "checks" / "readonly_runtime_chain_refresh_after_015533_v1_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
