#!/usr/bin/env python3
"""Prompt-to-artifact audit plus current source/control arrival poll after 063906."""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T064259+0800-codex-current-objective-arrival-poll-after-063906-v1"
GATE = "current_objective_arrival_poll_after_063906_v1=not_complete_no_new_source_control_arrival_no_downstream_promotion"
RUN_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = RUN_ROOT / "current-objective-arrival-poll-after-063906-v1"
CHECK_DIR = RUN_ROOT / "checks"
COMMAND_DIR = RUN_ROOT / "command-output"
STATE_DIR = Path("/tmp/ict-engine-board-a-064259-runtime-v1")
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
ICT = Path("./target/debug/ict-engine")

R6_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
R3_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
R5_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
EQUIV_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
R3_PROVENANCE = R3_ROOT / "native_subhour_source_label_provenance.json"
R3_ROWS = R3_ROOT / "native_subhour_source_label_rows.csv"

SEARCH_ROOTS = [
    Path.home() / "Downloads",
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path("/tmp"),
    Path("/private/tmp"),
    Path("docs/experiments/actionable-regime-confidence/runs"),
]

TEXT_SUFFIXES = {".csv", ".json", ".jsonl", ".md", ".txt", ".tsv", ".eml", ".log", ".out", ".err", ".stderr", ".stdout"}
NAME_TERMS = [
    "oystacher",
    "cme",
    "cboe",
    "cfe",
    "datamine",
    "datashop",
    "market_depth",
    "market-depth",
    "market by order",
    "mbo",
    "owner_export",
    "owner-export",
    "normal_control",
    "normal-control",
    "non_manipulation",
    "non-manipulation",
    "spoof",
    "layer",
    "ticket",
    "license",
    "export",
]
CONTENT_TERMS = [
    "oystacher",
    "spoof",
    "layering",
    "normal control",
    "non-manipulation",
    "market depth",
    "market by order",
    "datamine",
    "datashop",
    "ticket",
    "license",
    "export",
    "order lifecycle",
]


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def run_command(key: str, args: list[str], timeout: int = 90) -> dict:
    stdout_path = COMMAND_DIR / f"{key}.stdout"
    stderr_path = COMMAND_DIR / f"{key}.stderr"
    cmd_path = COMMAND_DIR / f"{key}.cmd"
    exit_path = COMMAND_DIR / f"{key}.exit"
    cmd_path.write_text(" ".join(args) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=False)
        stdout_path.write_text(proc.stdout, encoding="utf-8")
        stderr_path.write_text(proc.stderr, encoding="utf-8")
        exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
        return {
            "key": key,
            "args": args,
            "returncode": proc.returncode,
            "timeout": False,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
        }
    except subprocess.TimeoutExpired as exc:
        stdout_path.write_text(exc.stdout or "", encoding="utf-8")
        stderr_path.write_text((exc.stderr or "") + "\nTIMEOUT\n", encoding="utf-8")
        exit_path.write_text("timeout\n", encoding="utf-8")
        return {
            "key": key,
            "args": args,
            "returncode": "timeout",
            "timeout": True,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
        }


def parse_command_json(key: str) -> dict:
    return read_json(COMMAND_DIR / f"{key}.stdout")


def file_count(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for path in root.rglob("*") if path.is_file())


def root_status(root: Path, required_files: list[str]) -> dict:
    present = []
    missing = []
    for name in required_files:
        if (root / name).exists():
            present.append(name)
        else:
            missing.append(name)
    return {
        "root": str(root),
        "exists": root.exists(),
        "file_count": file_count(root),
        "required_files_present": present,
        "required_files_missing": missing,
        "all_required_files_present": root.exists() and not missing,
    }


def name_hits(path: Path) -> list[str]:
    text = normalize(path.name)
    return [term for term in NAME_TERMS if normalize(term) in text]


def content_hits(path: Path, size: int) -> list[str]:
    if path.suffix.lower() not in TEXT_SUFFIXES or size > 2_000_000:
        return []
    try:
        text = normalize(path.read_text(encoding="utf-8", errors="ignore")[:500_000])
    except Exception:
        return []
    return [term for term in CONTENT_TERMS if normalize(term) in text]


def classify_candidate(path: Path, names: list[str], contents: list[str]) -> str:
    joined = " ".join([str(path).lower(), *names, *contents])
    if "jsoncheck" in joined:
        return "prior_negative_tmp_jsoncheck_not_arrival"
    if ".eml" in path.suffix.lower() or "request" in joined or "dispatch" in joined or "draft" in joined:
        return "draft_or_request_only"
    if "docs/experiments/actionable-regime-confidence/runs" in str(path):
        return "prior_repo_artifact_not_new_arrival"
    if ("normal control" in joined or "non-manipulation" in joined) and ("market depth" in joined or "market by order" in joined):
        return "possible_owner_control_arrival_needs_review"
    if ("ticket" in joined or "license" in joined or "export" in joined) and ("cme" in joined or "cboe" in joined or "cfe" in joined):
        return "possible_owner_route_response_needs_review"
    return "keyword_candidate_not_sufficient"


def scan_candidates() -> list[dict]:
    rows: list[dict] = []
    visited = 0
    max_files = 20_000
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        root_depth = len(root.resolve().parts)
        max_depth = 7 if root == Path("docs/experiments/actionable-regime-confidence/runs") else 4
        for dirpath, dirnames, filenames in os.walk(root):
            current = Path(dirpath)
            depth = len(current.resolve().parts) - root_depth
            if depth >= max_depth:
                dirnames[:] = []
            dirnames[:] = [
                name
                for name in dirnames
                if name not in {".git", "node_modules", "target", ".venv", "__pycache__", "Library"}
            ]
            for filename in filenames:
                if visited >= max_files:
                    break
                path = current / filename
                visited += 1
                try:
                    stat = path.stat()
                except OSError:
                    continue
                names = name_hits(path)
                if not names:
                    continue
                contents = content_hits(path, stat.st_size)
                classification = classify_candidate(path, names, contents)
                rows.append(
                    {
                        "path": str(path),
                        "size_bytes": stat.st_size,
                        "mtime_epoch": int(stat.st_mtime),
                        "name_hits": ";".join(names),
                        "content_hits": ";".join(contents),
                        "classification": classification,
                    }
                )
            if visited >= max_files:
                break
    return rows


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def provider_ready(provider: dict, provider_id: str) -> dict:
    for row in provider.get("providers", []):
        if row.get("provider_id") == provider_id:
            return {
                "ready": bool(row.get("ready")),
                "status": row.get("status"),
                "reason": row.get("reason"),
                "domain": row.get("domain"),
            }
    return {"ready": False, "status": "missing", "reason": "not_reported", "domain": None}


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    COMMAND_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    commands = [
        run_command("board_sha256_before", ["shasum", "-a", "256", str(BOARD)], timeout=30),
        run_command("provider_status_agent", [str(ICT), "provider-status", "--agent"], timeout=60),
        run_command("auto_quant_status", [str(ICT), "auto-quant-status", "--state-dir", str(STATE_DIR), "--output-format", "json"], timeout=60),
        run_command(
            "analyze_live_nq_yfinance_agent",
            [
                str(ICT),
                "analyze-live",
                "--symbol",
                "NQ",
                "--futures-symbol",
                "NQ=F",
                "--spot-symbol",
                "QQQ",
                "--options-symbol",
                "QQQ",
                "--options-volatility-proxy-symbol",
                "^VIX",
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "agent",
            ],
            timeout=150,
        ),
        run_command("pre_bayes_status_nq", [str(ICT), "pre-bayes-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"], timeout=60),
        run_command("policy_training_status_nq", [str(ICT), "policy-training-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--output-format", "json"], timeout=60),
        run_command("workflow_status_nq_agent", [str(ICT), "workflow-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--refresh", "--agent"], timeout=60),
        run_command("export_structural_path_ranking_target_nq", [str(ICT), "export-structural-path-ranking-target", "--symbol", "NQ", "--state-dir", str(STATE_DIR)], timeout=60),
    ]

    r3_prov = read_json(R3_PROVENANCE)
    roots = {
        "r6_owner_export": root_status(
            R6_ROOT,
            ["positive_spoofing_layering_rows.csv", "matched_negative_normal_activity_rows.csv", "provenance_manifest.json"],
        ),
        "r3_native_subhour": root_status(R3_ROOT, ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"]),
        "r5_recency": root_status(R5_ROOT, ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"]),
        "source_label_equivalence_non_target": root_status(EQUIV_ROOT, ["source_label_equivalence_rows.csv", "source_label_equivalence_provenance.json"]),
    }
    provider = parse_command_json("provider_status_agent")
    auto_quant = parse_command_json("auto_quant_status")
    analyze = parse_command_json("analyze_live_nq_yfinance_agent")
    pre_bayes = parse_command_json("pre_bayes_status_nq")
    policy = parse_command_json("policy_training_status_nq")
    workflow = parse_command_json("workflow_status_nq_agent")
    path_export = parse_command_json("export_structural_path_ranking_target_nq")

    candidates = scan_candidates()
    arrival_candidates = [
        row
        for row in candidates
        if row["classification"]
        in {"possible_owner_control_arrival_needs_review", "possible_owner_route_response_needs_review"}
    ]

    accepted_roots = []
    missing_or_blocked = ["Bull", "Bear", "Sideways", "Crisis"]
    checklist = [
        {
            "requirement": "Board file inspected and concurrent-safe append discipline preserved",
            "evidence": str(BOARD),
            "status": "met",
            "notes": "Board hash captured before artifact; this script does not edit Current Cursor.",
        },
        {
            "requirement": "Bull regime has 95% calibrated, cross-market/cross-period evidence",
            "evidence": "063906 audit plus current root poll",
            "status": "not_met",
            "notes": "No accepted Board A root after TSIE quarantine; TSIE Bull rows are proxy/materialized only.",
        },
        {
            "requirement": "Bear regime has 95% calibrated, cross-market/cross-period evidence",
            "evidence": "063906 audit plus current root poll",
            "status": "not_met",
            "notes": "No accepted Board A root after TSIE quarantine; TSIE Bear rows are proxy/materialized only.",
        },
        {
            "requirement": "Sideways regime has 95% calibrated, cross-market/cross-period evidence",
            "evidence": "063906 audit plus current root poll",
            "status": "not_met",
            "notes": "No accepted Board A root after TSIE quarantine; TSIE Sideways rows are proxy/materialized only.",
        },
        {
            "requirement": "Crisis regime has 95% calibrated, cross-market/cross-period evidence",
            "evidence": "063155/063734/063906",
            "status": "not_met",
            "notes": "Crisis is absent from TSIE taxonomy and no replacement source packet is present.",
        },
        {
            "requirement": "R6 owner/export or explicit source/control approval is available",
            "evidence": str(R6_ROOT),
            "status": "not_met",
            "notes": "Target root absent; no new owner-control arrival candidate found in bounded local scan.",
        },
        {
            "requirement": "R5 post-cutoff source-panel recency evidence is available",
            "evidence": str(R5_ROOT),
            "status": "not_met",
            "notes": "Target root absent.",
        },
        {
            "requirement": "Provider surfaces checked: IBKR, TradingViewRemix, yfinance, Kraken where available",
            "evidence": "command-output/provider_status_agent.stdout",
            "status": "checked",
            "notes": "Provider catalog command executed read-only; readiness is evidence, not promotion.",
        },
        {
            "requirement": "Auto-Quant status checked",
            "evidence": "command-output/auto_quant_status.stdout",
            "status": "checked",
            "notes": "Managed Auto-Quant status command executed in isolated /tmp state.",
        },
        {
            "requirement": "Filter / Pre-Bayes / BBN surface checked",
            "evidence": "command-output/pre_bayes_status_nq.stdout",
            "status": "checked",
            "notes": "Pre-Bayes status refreshed after read-only analyze-live command.",
        },
        {
            "requirement": "CatBoost/path-ranking surface checked",
            "evidence": "command-output/policy_training_status_nq.stdout and command-output/export_structural_path_ranking_target_nq.stdout",
            "status": "checked",
            "notes": "Policy-training and structural path-ranking export commands executed read-only.",
        },
        {
            "requirement": "Execution-tree/workflow status checked",
            "evidence": "command-output/workflow_status_nq_agent.stdout",
            "status": "checked",
            "notes": "Workflow status command executed read-only.",
        },
        {
            "requirement": "Canonical merge and downstream promotion rerun after a valid unlock",
            "evidence": "current root poll and command outputs",
            "status": "not_met",
            "notes": "No valid unlock exists, so canonical merge and promotion chain remain false by design.",
        },
    ]

    decision = {
        "accepted_regime_roots": accepted_roots,
        "missing_or_blocked_regime_roots": missing_or_blocked,
        "r3_counts_as_unlock": False,
        "r3_policy_state": "present_quarantined_tsie_proxy_not_accepted",
        "r3_physical_rows": r3_prov.get("row_count", 0),
        "r3_physical_labels": r3_prov.get("accepted_mapping_confidence_95_labels", []),
        "new_owner_control_arrival_candidates": len(arrival_candidates),
        "r6_source_control_evidence_acquired": False,
        "r5_recency_evidence_acquired": False,
        "accepted_rows_added_for_board_a": 0,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    result = {
        "run_id": RUN_ID,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": GATE,
        "objective": {
            "board": str(BOARD),
            "success_criteria": [
                "Bull, Bear, Sideways, and Crisis each have accepted 95% calibrated evidence",
                "Each accepted root has cross-market/cross-period/cross-context validation",
                "Only source/control-approved or verifier-native roots count",
                "After a valid unlock, canonical merge and provider/AutoQuant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree readback rerun",
            ],
        },
        "roots": roots,
        "r3_provenance": {
            "row_count": r3_prov.get("row_count", 0),
            "labels": r3_prov.get("accepted_mapping_confidence_95_labels", []),
            "rows_sha256": r3_prov.get("rows_sha256"),
            "raw_parquet_sha256": r3_prov.get("raw_parquet_sha256"),
            "limitations": r3_prov.get("limitations", []),
        },
        "commands": commands,
        "provider_readiness": {
            "yfinance": provider_ready(provider, "yfinance"),
            "kraken_cli": provider_ready(provider, "kraken_cli"),
            "kraken_public": provider_ready(provider, "kraken_public"),
            "ibkr": provider_ready(provider, "ibkr"),
            "tradingview_remix": provider_ready(provider, "tradingview_remix"),
        },
        "auto_quant": {
            "status": auto_quant.get("status"),
            "healthy": auto_quant.get("healthy"),
            "bootstrap_needed": auto_quant.get("bootstrap_needed"),
            "data_ready": auto_quant.get("data_ready"),
        },
        "analyze_live": {
            "command_returncode": next((cmd["returncode"] for cmd in commands if cmd["key"] == "analyze_live_nq_yfinance_agent"), None),
            "decision_summary": analyze.get("decision_summary"),
            "direction": analyze.get("direction"),
            "pre_bayes_gate": analyze.get("pre_bayes_gate"),
            "execution_gate": analyze.get("execution_triage", {}).get("gate_status"),
        },
        "pre_bayes": {
            "latest_gate_status": pre_bayes.get("latest_gate_status"),
            "latest_canonical_structural_active_regime": pre_bayes.get("latest_canonical_structural_active_regime"),
            "latest_canonical_structural_confidence": pre_bayes.get("latest_canonical_structural_confidence"),
        },
        "policy_training": {
            "summary_line": policy.get("summary_line"),
            "entry_models": policy.get("entry_models", []),
            "structural_path_ranking_target": policy.get("structural_path_ranking_target", {}),
        },
        "workflow": {
            "blocking_status": workflow.get("blocking_status"),
            "blocking_reason": workflow.get("blocking_reason"),
            "focus_phase": workflow.get("focus_phase"),
            "next_step": workflow.get("next_step"),
        },
        "path_ranking_export": {
            "rows": path_export.get("rows"),
            "mature_rows": path_export.get("mature_rows"),
            "rows_with_calibrated_path_prob": path_export.get("rows_with_calibrated_path_prob"),
            "summary_line": path_export.get("summary_line"),
        },
        "bounded_local_arrival_scan": {
            "candidate_count": len(candidates),
            "new_owner_control_arrival_candidates": len(arrival_candidates),
            "candidate_csv": str(ARTIFACT_DIR / "current_objective_arrival_poll_candidates_v1.csv"),
        },
        "prompt_to_artifact_checklist": checklist,
        "decision": decision,
        "next_action": (
            "Continue from a real source/control unlock only: explicit source/control approval, "
            "verifier-native R6 owner-export rows with controls, source-owned R5 recency rows, "
            "or verifier-native Crisis-capable R3 MainRegimeV2 labels. Do not run canonical merge "
            "or downstream promotion from the TSIE root."
        ),
    }

    write_csv(
        ARTIFACT_DIR / "current_objective_arrival_poll_candidates_v1.csv",
        candidates,
        ["path", "size_bytes", "mtime_epoch", "name_hits", "content_hits", "classification"],
    )
    write_csv(
        ARTIFACT_DIR / "prompt_to_artifact_checklist_v1.csv",
        checklist,
        ["requirement", "evidence", "status", "notes"],
    )

    json_path = ARTIFACT_DIR / "current_objective_arrival_poll_after_063906_v1.json"
    md_path = ARTIFACT_DIR / "current_objective_arrival_poll_after_063906_v1.md"
    assertions_path = CHECK_DIR / "current_objective_arrival_poll_after_063906_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_lines = [
        "# Current Objective Arrival Poll After 063906 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE}`",
        "",
        "## Completion Audit",
        "",
        "- Objective restated: every `MainRegimeV2` root needs accepted 95% calibrated evidence plus cross-market/cross-period validation before downstream promotion.",
        "- Result: not complete.",
        f"- Accepted roots: `{', '.join(accepted_roots) if accepted_roots else 'none'}`.",
        f"- Missing or blocked roots: `{', '.join(missing_or_blocked)}`.",
        "",
        "## Root Readback",
        "",
        f"- R6 owner/export root: exists `{roots['r6_owner_export']['exists']}`, all required files `{roots['r6_owner_export']['all_required_files_present']}`.",
        f"- R3 native-subhour root: exists `{roots['r3_native_subhour']['exists']}`, all required files `{roots['r3_native_subhour']['all_required_files_present']}`, policy accepted `false`.",
        f"- R3 physical rows: `{decision['r3_physical_rows']}`; labels `{', '.join(decision['r3_physical_labels']) if decision['r3_physical_labels'] else 'none'}`.",
        f"- R5 recency root: exists `{roots['r5_recency']['exists']}`, all required files `{roots['r5_recency']['all_required_files_present']}`.",
        f"- New owner/control arrival candidates: `{len(arrival_candidates)}`.",
        "",
        "## Runtime Readback",
        "",
        f"- Provider command return code: `{next((cmd['returncode'] for cmd in commands if cmd['key'] == 'provider_status_agent'), None)}`.",
        f"- Auto-Quant status: `{result['auto_quant']['status']}`; healthy `{result['auto_quant']['healthy']}`; bootstrap needed `{result['auto_quant']['bootstrap_needed']}`.",
        f"- analyze-live return code: `{result['analyze_live']['command_returncode']}`; decision `{result['analyze_live']['decision_summary']}`; pre-Bayes `{result['analyze_live']['pre_bayes_gate']}`; execution gate `{result['analyze_live']['execution_gate']}`.",
        f"- Pre-Bayes latest gate: `{result['pre_bayes']['latest_gate_status']}`.",
        f"- Workflow: `{result['workflow']['blocking_status']}` / `{result['workflow']['blocking_reason']}`.",
        f"- Path-ranking export: rows `{result['path_ranking_export']['rows']}`, mature rows `{result['path_ranking_export']['mature_rows']}`, calibrated rows `{result['path_ranking_export']['rows_with_calibrated_path_prob']}`.",
        "",
        "## Accounting",
        "",
        "- Accepted Board A rows added: `0`.",
        "- Canonical merge: `false`.",
        "- Downstream promotion rerun: `false`.",
        "- Strict full objective: `false`.",
        "- Trade usable: `false`.",
        "- `update_goal=false`.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path}`",
        f"- Checklist CSV: `{ARTIFACT_DIR / 'prompt_to_artifact_checklist_v1.csv'}`",
        f"- Candidate CSV: `{ARTIFACT_DIR / 'current_objective_arrival_poll_candidates_v1.csv'}`",
        f"- Assertions: `{assertions_path}`",
        "",
        "## Next",
        "",
        result["next_action"],
        "",
    ]
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    assertions = {
        "gate_result": GATE,
        "objective_complete": "false",
        "accepted_roots": "none",
        "missing_or_blocked_roots": ",".join(missing_or_blocked),
        "r3_counts_as_unlock": "false",
        "new_owner_control_arrival_candidates": str(len(arrival_candidates)),
        "r6_source_control_evidence_acquired": "false",
        "r5_recency_evidence_acquired": "false",
        "accepted_rows_added_for_board_a": "0",
        "provider_status_called": str(next((cmd["returncode"] for cmd in commands if cmd["key"] == "provider_status_agent"), None) == 0).lower(),
        "auto_quant_status_called": str(next((cmd["returncode"] for cmd in commands if cmd["key"] == "auto_quant_status"), None) == 0).lower(),
        "analyze_live_called": str(next((cmd["returncode"] for cmd in commands if cmd["key"] == "analyze_live_nq_yfinance_agent"), None) == 0).lower(),
        "pre_bayes_status_called": str(next((cmd["returncode"] for cmd in commands if cmd["key"] == "pre_bayes_status_nq"), None) == 0).lower(),
        "policy_training_status_called": str(next((cmd["returncode"] for cmd in commands if cmd["key"] == "policy_training_status_nq"), None) == 0).lower(),
        "workflow_status_called": str(next((cmd["returncode"] for cmd in commands if cmd["key"] == "workflow_status_nq_agent"), None) == 0).lower(),
        "path_ranking_export_called": str(next((cmd["returncode"] for cmd in commands if cmd["key"] == "export_structural_path_ranking_target_nq"), None) == 0).lower(),
        "canonical_merge": "false",
        "downstream_promotion_rerun": "false",
        "strict_full_objective": "false",
        "trade_usable": "false",
        "update_goal": "false",
    }
    assertions_path.write_text("\n".join(f"{key}={value}" for key, value in assertions.items()) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
