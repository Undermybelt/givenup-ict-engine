#!/usr/bin/env python3
"""Current-goal strict gap audit for Board A after the V58/V57 R6 readbacks.

This run is deliberately read-only with respect to repo runtime code and the
shared direct-manipulation intake. It checks the prompt requirements against
current artifacts, reruns lightweight provider/downstream surfaces, and
quantifies the exact R6 split deficits that still block the strict objective.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T000724-codex-current-goal-strict-gap-audit-v59"
AUDIT_ID = "current_goal_strict_gap_audit_v59"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "current-goal-strict-gap-audit"
CMD = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
STATE_DIR = Path("/tmp/ict-engine-board-a-v59-demo-chain")
LIVE_STATE_DIR = Path("/tmp/ict-engine-board-a-v59-yfinance-live")
KRAKEN_STATE_DIR = Path("/tmp/ict-engine-board-a-v59-kraken-live")
AQ_STATE_DIR = Path("/tmp/ict-engine-board-a-v59-autoquant")
LOCAL_AUTO_QUANT = Path("/Users/thrill3r/Auto-Quant")

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
BIN = REPO / "target/debug/ict-engine"
DIRECT_INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
CONSUMER_MAP_CSV = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T153637-codex-regime-factor-consumer-map-v1"
    / "regime-factor-map/regime_factor_consumer_map_v1.csv"
)
CONSUMER_MAP_JSON = CONSUMER_MAP_CSV.with_suffix(".json")
R6_CURRENT_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235815-codex-r6-live-intake-rehydrate-calibration-v1"
    / "r6-live-intake-rehydrate-calibration/r6_live_intake_rehydrate_calibration_v1.json"
)
R6_SPLIT_METRICS = R6_CURRENT_JSON.with_name("r6_live_intake_rehydrate_split_metrics_v1.csv")
R6_POSITIVE_ROWS = R6_CURRENT_JSON.with_name("positive_spoofing_layering_rows_v1.csv")
R6_NEGATIVE_ROWS = R6_CURRENT_JSON.with_name("matched_negative_normal_activity_rows_v1.csv")

Z_95 = 1.96
TARGET_LCB = 0.95


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
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


def required_all_correct_n(target_lcb: float = TARGET_LCB) -> int:
    n = 1
    while wilson_lcb(n, n) < target_lcb:
        n += 1
    return n


def parse_json_maybe(text: str) -> Any | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def run_command(
    name: str,
    args: list[str],
    timeout_seconds: int = 120,
    env_extra: dict[str, str] | None = None,
) -> dict[str, Any]:
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    try:
        proc = subprocess.run(
            args,
            cwd=REPO,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        returncode = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout_seconds}s\n"
        returncode = 124
        timed_out = True
    out_path = CMD / f"{AUDIT_ID}_{name}.out"
    err_path = CMD / f"{AUDIT_ID}_{name}.err"
    exit_path = CMD / f"{AUDIT_ID}_{name}.exit"
    out_path.write_text(stdout, encoding="utf-8")
    err_path.write_text(stderr, encoding="utf-8")
    exit_path.write_text(f"{returncode}\n", encoding="utf-8")
    return {
        "name": name,
        "cmd": " ".join(args),
        "returncode": returncode,
        "timed_out": timed_out,
        "stdout_path": rel(out_path),
        "stderr_path": rel(err_path),
        "exit_path": rel(exit_path),
        "parsed": parse_json_maybe(stdout),
    }


def provider_summary(payload: dict[str, Any] | None, provider_id: str) -> dict[str, Any]:
    if not payload:
        return {
            "provider_id": provider_id,
            "observed": False,
            "ready": False,
            "status": "unparsed",
            "reason": "",
        }
    matches = [row for row in payload.get("providers", []) if row.get("provider_id") == provider_id]
    if not matches:
        return {
            "provider_id": provider_id,
            "observed": False,
            "ready": False,
            "status": "not_listed",
            "reason": "",
        }
    return {
        "provider_id": provider_id,
        "observed": True,
        "ready": any(bool(row.get("ready")) for row in matches),
        "domains": sorted({str(row.get("domain")) for row in matches}),
        "status": ";".join(sorted({str(row.get("status")) for row in matches})),
        "reason": ";".join(sorted({str(row.get("reason")) for row in matches})),
    }


def count_strategy_files() -> dict[str, Any]:
    strategies_dir = LOCAL_AUTO_QUANT / "user_data/strategies"
    files = sorted(path for path in strategies_dir.glob("*.py") if path.is_file())
    active = [path for path in files if not path.name.startswith("_")]
    return {
        "strategies_dir": str(strategies_dir),
        "python_files": [path.name for path in files],
        "active_non_underscore_strategy_files": [path.name for path in active],
        "active_count": len(active),
    }


def consumer_map_summary() -> dict[str, Any]:
    rows = read_csv(CONSUMER_MAP_CSV)
    active = [row for row in rows if row["regime"] in ["Bull", "Bear", "Sideways", "Crisis", "Manipulation"]]
    return {
        "artifact": rel(CONSUMER_MAP_CSV),
        "json": rel(CONSUMER_MAP_JSON),
        "active_lane_count": len(active),
        "accepted_95_count": sum(row["accepted_95"] == "True" for row in active),
        "lanes": [
            {
                "regime": row["regime"],
                "taxonomy_role": row["taxonomy_role"],
                "consumer_factor": row["consumer_factor"],
                "accepted_95": row["accepted_95"] == "True",
                "confidence_floor": float(row["confidence_floor"]),
                "abstain_or_limit": row["abstain_or_limit"],
                "source_artifact": row["source_artifact"],
            }
            for row in active
        ],
    }


def split_deficit_summary(required_n: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = read_csv(R6_SPLIT_METRICS)
    deficits: list[dict[str, Any]] = []
    for row in rows:
        pos = int(row["positive_support"])
        neg = int(row["negative_support"])
        deficits.append(
            {
                "split_family": row["split_family"],
                "split_name": row["split_name"],
                "positive_support": pos,
                "negative_support": neg,
                "positive_deficit_to_wilson95": max(0, required_n - pos),
                "negative_deficit_to_wilson95": max(0, required_n - neg),
                "min_wilson95_lcb": float(row["min_wilson95_lcb"]),
                "pass": row["pass"] == "True",
            }
        )
    by_family: dict[str, dict[str, Any]] = {}
    for row in deficits:
        family = row["split_family"]
        bucket = by_family.setdefault(
            family,
            {
                "bucket_count": 0,
                "failing_bucket_count": 0,
                "total_positive_deficit_to_wilson95": 0,
                "total_negative_deficit_to_wilson95": 0,
                "worst_min_wilson95_lcb": 1.0,
                "passes": True,
            },
        )
        bucket["bucket_count"] += 1
        bucket["failing_bucket_count"] += 0 if row["pass"] else 1
        bucket["total_positive_deficit_to_wilson95"] += row["positive_deficit_to_wilson95"]
        bucket["total_negative_deficit_to_wilson95"] += row["negative_deficit_to_wilson95"]
        bucket["worst_min_wilson95_lcb"] = min(bucket["worst_min_wilson95_lcb"], row["min_wilson95_lcb"])
        bucket["passes"] = bool(bucket["passes"] and row["pass"])
    return deficits, by_family


def checklist(
    consumer: dict[str, Any],
    r6: dict[str, Any],
    providers: list[dict[str, Any]],
    auto_quant: dict[str, Any],
    command_by_name: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    provider_ready = {row["provider_id"]: row["ready"] for row in providers}
    auto_quant_ready = auto_quant.get("healthy") is True and auto_quant.get("data_ready") is True
    return [
        {
            "requirement": "Authoritative board file used and multi-agent safety preserved",
            "evidence": rel(BOARD),
            "status": "pass",
            "notes": "This audit reads the board and writes only under its own run root; board writeback is append-only if performed.",
        },
        {
            "requirement": "Each active regime has a 95% scoped consumer factor",
            "evidence": consumer["artifact"],
            "status": "pass" if consumer["accepted_95_count"] == 5 else "fail",
            "notes": f"accepted_95_count={consumer['accepted_95_count']}/5 for Bull/Bear/Sideways/Crisis/scoped Manipulation.",
        },
        {
            "requirement": "Strict objective: every regime validated across other markets and other periods/timeframes",
            "evidence": f"{rel(R6_CURRENT_JSON)} plus board Current Cursor",
            "status": "fail",
            "notes": "Board still marks strict objective blocked; R6 chronological/symbol/venue/species gates remain false.",
        },
        {
            "requirement": "Direct Manipulation is direct-source evidence, not OHLCV proxy promotion",
            "evidence": rel(R6_POSITIVE_ROWS),
            "status": "pass",
            "notes": "Current R6 rows are timestamped CFTC event/order-lifecycle spoofing/layering rows with matched controls.",
        },
        {
            "requirement": "R6 direct Manipulation pooled Wilson95 >= 0.95",
            "evidence": rel(R6_CURRENT_JSON),
            "status": "pass" if r6["direct_calibration"]["pooled_direct_gate"] else "fail",
            "notes": f"pooled_min_wilson95_lcb={r6['direct_calibration']['pooled_min_wilson95_lcb']}",
        },
        {
            "requirement": "R6 direct Manipulation chronological, symbol, venue, and species gates close",
            "evidence": rel(R6_SPLIT_METRICS),
            "status": "fail",
            "notes": "chronological_split_gate=false, heldout_symbol_gate=false, heldout_venue_gate=false, direct_species_closed=false.",
        },
        {
            "requirement": "IBKR, TradingViewRemix, yfinance, Kraken provider paths checked",
            "evidence": rel(CMD),
            "status": "partial" if any(provider_ready.values()) else "fail",
            "notes": f"ready={provider_ready}; provider paths checked but only ready providers can promote evidence.",
        },
        {
            "requirement": "Auto-Quant personally checked against local runtime",
            "evidence": str(LOCAL_AUTO_QUANT),
            "status": "partial" if auto_quant_ready else "fail",
            "notes": f"healthy={auto_quant.get('healthy')} data_ready={auto_quant.get('data_ready')} next={auto_quant.get('status')}",
        },
        {
            "requirement": "ict-engine chain exercised through filter/BBN/CatBoost/execution tree surfaces",
            "evidence": rel(CMD),
            "status": "partial",
            "notes": (
                "analyze/pre-bayes/policy-training/workflow/path-ranking commands were run. "
                f"policy_training_exit={command_by_name['policy_training_status_demo']['returncode']} "
                f"workflow_execution_exit={command_by_name['workflow_status_execution_candidate_demo']['returncode']}."
            ),
        },
    ]


def main() -> int:
    for path in [OUT, CMD, CHECKS, STATE_DIR, LIVE_STATE_DIR, KRAKEN_STATE_DIR, AQ_STATE_DIR]:
        path.mkdir(parents=True, exist_ok=True)

    commands: list[dict[str, Any]] = [
        run_command("direct_manipulation_verifier", [sys.executable, str(DIRECT_VERIFIER), "--intake-root", str(DIRECT_INTAKE)]),
        run_command("provider_status_agent", [str(BIN), "provider-status", "--agent"]),
    ]
    for provider in ["ibkr", "tradingview_mcp", "yfinance", "kraken_public", "kraken_cli"]:
        commands.append(run_command(f"provider_status_{provider}_agent", [str(BIN), "provider-status", "--provider", provider, "--agent"]))
    commands.extend(
        [
            run_command(
                "auto_quant_status_local",
                [str(BIN), "auto-quant-status", "--state-dir", str(AQ_STATE_DIR), "--output-format", "json"],
                env_extra={"ICT_ENGINE_AUTO_QUANT_DIR": str(LOCAL_AUTO_QUANT)},
            ),
            run_command("analyze_demo_agent", [str(BIN), "analyze", "--symbol", "DEMO", "--demo", "--state-dir", str(STATE_DIR), "--agent"]),
            run_command("pre_bayes_status_demo", [str(BIN), "pre-bayes-status", "--symbol", "DEMO", "--state-dir", str(STATE_DIR), "--refresh"]),
            run_command("policy_training_status_demo", [str(BIN), "policy-training-status", "--symbol", "DEMO", "--state-dir", str(STATE_DIR), "--output-format", "json"]),
            run_command("workflow_status_demo_agent", [str(BIN), "workflow-status", "--symbol", "DEMO", "--state-dir", str(STATE_DIR), "--refresh", "--agent"]),
            run_command(
                "workflow_status_execution_candidate_demo",
                [str(BIN), "workflow-status", "--symbol", "DEMO", "--state-dir", str(STATE_DIR), "--phase", "execution-candidate", "--agent"],
            ),
            run_command("export_structural_path_ranking_target_demo", [str(BIN), "export-structural-path-ranking-target", "--symbol", "DEMO", "--state-dir", str(STATE_DIR)]),
            run_command(
                "analyze_live_nq_yfinance_compact",
                [
                    str(BIN),
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
                    "--futures-backend",
                    "yfinance",
                    "--aux-backend",
                    "yfinance",
                    "--state-dir",
                    str(LIVE_STATE_DIR),
                    "--compact",
                ],
                timeout_seconds=180,
            ),
            run_command(
                "analyze_live_btc_kraken_public_compact",
                [
                    str(BIN),
                    "analyze-live",
                    "--symbol",
                    "BTCUSD",
                    "--futures-symbol",
                    "BTC/USD",
                    "--spot-symbol",
                    "BTC/USD",
                    "--futures-backend",
                    "kraken_public",
                    "--aux-backend",
                    "kraken_public",
                    "--state-dir",
                    str(KRAKEN_STATE_DIR),
                    "--compact",
                ],
                timeout_seconds=90,
            ),
        ]
    )
    by_name = {row["name"]: row for row in commands}

    consumer = consumer_map_summary()
    r6 = json.loads(R6_CURRENT_JSON.read_text(encoding="utf-8"))
    required_n = required_all_correct_n()
    split_deficits, split_summary = split_deficit_summary(required_n)
    positive_rows = read_csv(R6_POSITIVE_ROWS)
    negative_rows = read_csv(R6_NEGATIVE_ROWS)
    positive_labels = Counter(row.get("label", "") for row in positive_rows)
    negative_labels = Counter(row.get("label", "") for row in negative_rows)
    provider_payload = by_name["provider_status_agent"]["parsed"]
    providers = [
        provider_summary(provider_payload if isinstance(provider_payload, dict) else None, provider)
        for provider in ["ibkr", "tradingview_mcp", "yfinance", "kraken_public", "kraken_cli"]
    ]
    auto_quant_payload = by_name["auto_quant_status_local"]["parsed"]
    if not isinstance(auto_quant_payload, dict):
        auto_quant_payload = {"status": "unparsed", "healthy": False, "data_ready": False}
    strategy_files = count_strategy_files()
    direct_payload = by_name["direct_manipulation_verifier"]["parsed"]
    if not isinstance(direct_payload, dict):
        direct_payload = {"status": "unparsed"}

    checklist_rows = checklist(consumer, r6, providers, auto_quant_payload, by_name)
    checklist_status = "blocked" if any(row["status"] == "fail" for row in checklist_rows) else "partial"

    deficit_csv = OUT / "r6_split_deficits_v59.csv"
    checklist_csv = OUT / "prompt_to_artifact_checklist_v59.csv"
    write_csv(
        deficit_csv,
        split_deficits,
        [
            "split_family",
            "split_name",
            "positive_support",
            "negative_support",
            "positive_deficit_to_wilson95",
            "negative_deficit_to_wilson95",
            "min_wilson95_lcb",
            "pass",
        ],
    )
    write_csv(checklist_csv, checklist_rows, ["requirement", "evidence", "status", "notes"])

    gate_result = "current_goal_strict_gap_audit_v59=scoped_consumer_95_passes_strict_full_goal_still_blocked"
    result = {
        "run_id": RUN_ID,
        "audit_id": AUDIT_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "objective_restatement": {
            "board_file": rel(BOARD),
            "success_criteria": [
                "Every active regime lane has >=95% calibrated confidence.",
                "The same confidence is validated across other markets and other periods/timeframes.",
                "Provider paths IBKR, TradingViewRemix, yfinance, Kraken, local cache, and Auto-Quant cache are checked.",
                "ict-engine downstream chain is exercised through filter/pre-Bayes, BBN, CatBoost/policy-training, and execution tree/workflow surfaces.",
                "Do not overwrite concurrent board edits or mutate unrelated runtime code.",
            ],
        },
        "checklist_status": checklist_status,
        "checklist_csv": rel(checklist_csv),
        "consumer_map": consumer,
        "r6_current": {
            "artifact": rel(R6_CURRENT_JSON),
            "positive_rows": len(positive_rows),
            "matched_negative_rows": len(negative_rows),
            "positive_labels": dict(positive_labels),
            "negative_labels": dict(negative_labels),
            "direct_verifier": direct_payload,
            "pooled_direct_gate": r6["direct_calibration"]["pooled_direct_gate"],
            "pooled_min_wilson95_lcb": r6["direct_calibration"]["pooled_min_wilson95_lcb"],
            "sidecar_axis_gate": r6["sidecar_calibration"]["sidecar_axis_gate"],
            "chronological_split_gate": r6["direct_calibration"]["chronological_split_gate"],
            "heldout_symbol_gate": r6["direct_calibration"]["heldout_symbol_gate"],
            "heldout_venue_gate": r6["direct_calibration"]["heldout_venue_gate"],
            "direct_species_closed": False,
            "split_deficit_csv": rel(deficit_csv),
            "required_all_correct_rows_for_wilson95": required_n,
            "split_summary": split_summary,
        },
        "providers": providers,
        "auto_quant": {
            "status": auto_quant_payload.get("status"),
            "healthy": auto_quant_payload.get("healthy"),
            "data_ready": auto_quant_payload.get("data_ready"),
            "managed_dir": auto_quant_payload.get("managed_dir"),
            "next_step": auto_quant_payload.get("next_step"),
            "strategy_files": strategy_files,
        },
        "commands": [{key: value for key, value in row.items() if key != "parsed"} for row in commands],
        "gate_result": gate_result,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "shared_intake_mutated": False,
        "external_requests_sent": True,
        "trade_usable": False,
        "blocker": (
            "Scoped consumer 95 is preserved, but strict completion is blocked by R6 chronological/symbol/venue/species "
            "deficits plus provider/runtime readiness gaps: IBKR and TradingView MCP are not ready, kraken_public is not ready, "
            "and local Auto-Quant has no active non-underscore strategy files."
        ),
        "next_action": (
            "Do not chase more pooled R6 rows. Either redesign the validation axis away from impossible exact-symbol/exact-venue all-bucket closure, "
            "or acquire bulk direct rows and matched controls that raise each chosen validation bucket to at least 73 all-correct rows; then rerun the direct verifier and downstream chain."
        ),
    }

    json_path = OUT / f"{AUDIT_ID}.json"
    md_path = OUT / f"{AUDIT_ID}.md"
    assertions_path = CHECKS / f"{AUDIT_ID}_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Current Goal Strict Gap Audit v59",
        "",
        f"- Gate result: `{gate_result}`.",
        f"- Checklist status: `{checklist_status}`.",
        f"- Scoped consumer 95 lanes: `{consumer['accepted_95_count']}/5` accepted.",
        f"- R6 live rows: positives `{len(positive_rows)}`, matched controls `{len(negative_rows)}`; verifier status `{direct_payload.get('status')}`.",
        f"- R6 pooled direct Wilson95 LCB: `{r6['direct_calibration']['pooled_min_wilson95_lcb']}`; pooled gate `{str(r6['direct_calibration']['pooled_direct_gate']).lower()}`.",
        f"- R6 split/species gates: chronological `{str(r6['direct_calibration']['chronological_split_gate']).lower()}`, symbol `{str(r6['direct_calibration']['heldout_symbol_gate']).lower()}`, venue `{str(r6['direct_calibration']['heldout_venue_gate']).lower()}`, species `false`.",
        f"- All-correct Wilson95 row requirement per bucket: `{required_n}`.",
        f"- Local Auto-Quant: status `{auto_quant_payload.get('status')}`, healthy `{auto_quant_payload.get('healthy')}`, data_ready `{auto_quant_payload.get('data_ready')}`, active strategy files `{strategy_files['active_count']}`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; shared intake mutated: `false`; trade usable: `false`.",
        "",
        "## Prompt To Artifact Checklist",
        "",
        "| Requirement | Status | Evidence | Notes |",
        "|---|---|---|---|",
    ]
    for row in checklist_rows:
        lines.append(f"| {row['requirement']} | `{row['status']}` | `{row['evidence']}` | {row['notes']} |")
    lines.extend(["", "## R6 Split Summary", "", "| Split Family | Buckets | Failing | Pos Deficit | Neg Deficit | Worst LCB | Passes |", "|---|---:|---:|---:|---:|---:|---:|"])
    for family, row in split_summary.items():
        lines.append(
            f"| `{family}` | `{row['bucket_count']}` | `{row['failing_bucket_count']}` | "
            f"`{row['total_positive_deficit_to_wilson95']}` | `{row['total_negative_deficit_to_wilson95']}` | "
            f"`{row['worst_min_wilson95_lcb']}` | `{str(row['passes']).lower()}` |"
        )
    lines.extend(["", "## Providers", "", "| Provider | Ready | Status | Reason |", "|---|---:|---|---|"])
    for provider in providers:
        lines.append(f"| `{provider['provider_id']}` | `{str(provider['ready']).lower()}` | `{provider['status']}` | `{provider['reason']}` |")
    lines.extend(["", "## Commands", "", "| Command | Exit | Output | Error |", "|---|---:|---|---|"])
    for row in commands:
        lines.append(f"| `{row['name']}` | `{row['returncode']}` | `{row['stdout_path']}` | `{row['stderr_path']}` |")
    lines.extend(
        [
            "",
            "## Next",
            "",
            result["next_action"],
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(json_path)}`",
            f"- Report: `{rel(md_path)}`",
            f"- Checklist CSV: `{rel(checklist_csv)}`",
            f"- R6 split deficit CSV: `{rel(deficit_csv)}`",
            f"- Assertions: `{rel(assertions_path)}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = {
        "consumer_map_all_scoped_lanes_95": consumer["accepted_95_count"] == 5,
        "r6_pooled_gate_passes": r6["direct_calibration"]["pooled_direct_gate"] is True,
        "r6_chronological_gate_still_false": r6["direct_calibration"]["chronological_split_gate"] is False,
        "r6_symbol_gate_still_false": r6["direct_calibration"]["heldout_symbol_gate"] is False,
        "r6_venue_gate_still_false": r6["direct_calibration"]["heldout_venue_gate"] is False,
        "direct_verifier_schema_ready": direct_payload.get("status") == "schema_ready_unscored",
        "local_auto_quant_checked": auto_quant_payload.get("managed_dir") == str(LOCAL_AUTO_QUANT),
        "provider_status_checked": all(provider["observed"] for provider in providers),
        "strict_full_objective_not_achieved": result["strict_full_objective_achieved"] is False,
    }
    assertions_path.write_text(
        "\n".join(f"{name}={'ok' if passed else 'FAIL'}" for name, passed in assertions.items()) + "\n",
        encoding="utf-8",
    )
    if not all(assertions.values()):
        raise SystemExit(2)
    print(json.dumps({"gate_result": gate_result, "checklist_status": checklist_status, "commands": len(commands)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
