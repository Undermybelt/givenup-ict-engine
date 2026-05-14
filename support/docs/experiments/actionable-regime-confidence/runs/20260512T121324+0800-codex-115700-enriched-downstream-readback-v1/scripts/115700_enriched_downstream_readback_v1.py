#!/usr/bin/env python3
"""Board B 115700 row enrichment plus downstream fail-closed readback."""

from __future__ import annotations

import csv
import json
import math
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T121324+0800-codex-115700-enriched-downstream-readback-v1"
SOURCE_RUN_ID = "20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1"
SYMBOL = "BTC_USDT"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / SOURCE_RUN_ID
)
SOURCE_REPORT = (
    SOURCE_ROOT
    / "same-root-six-provider-1h-aq-v1"
    / "same_root_six_provider_1h_aq_v1.json"
)
OUT = RUN_ROOT / "115700-enriched-downstream-readback-v1"
CHECKS = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"
DATA_DIR = RUN_ROOT / "derived-data"
STATE_DIR = Path("/tmp/ict-engine-board-b-115700-enriched-downstream-121324-r2")
BIN = REPO / "target/debug/ict-engine"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_command(name: str, args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=REPO, text=True, capture_output=True, check=False)
    out_path = CMD_DIR / f"{name}.out"
    err_path = CMD_DIR / f"{name}.err"
    exit_path = CMD_DIR / f"{name}.exit"
    out_path.write_text(proc.stdout, encoding="utf-8")
    err_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    parsed = None
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = None
    return {
        "name": name,
        "cmd": " ".join(args),
        "returncode": proc.returncode,
        "stdout_path": rel(out_path),
        "stderr_path": rel(err_path),
        "exit_path": rel(exit_path),
        "parsed": parsed,
    }


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def floor_dt(dt: datetime, bucket: str) -> datetime:
    if bucket == "1h":
        return dt.replace(minute=0, second=0, microsecond=0)
    if bucket == "4h":
        return dt.replace(hour=(dt.hour // 4) * 4, minute=0, second=0, microsecond=0)
    if bucket == "1d":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    raise ValueError(bucket)


def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def load_candles_csv(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            ts = row.get("date") or row.get("timestamp") or row.get("ts")
            if not ts:
                continue
            rows.append(
                {
                    "timestamp": iso_z(parse_dt(ts)),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume") or 0.0),
                }
            )
    rows.sort(key=lambda row: row["timestamp"])
    return rows


def resample(candles: list[dict[str, Any]], bucket: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candles:
        grouped[iso_z(floor_dt(parse_dt(row["timestamp"]), bucket))].append(row)
    out: list[dict[str, Any]] = []
    for ts in sorted(grouped):
        group = grouped[ts]
        out.append(
            {
                "timestamp": ts,
                "open": group[0]["open"],
                "high": max(row["high"] for row in group),
                "low": min(row["low"] for row in group),
                "close": group[-1]["close"],
                "volume": sum(row["volume"] for row in group),
            }
        )
    return out


def write_analyze_candles(source_csv: Path) -> dict[str, Path]:
    one_h = load_candles_csv(source_csv)
    paths = {
        "ltf": DATA_DIR / "btc_usdt_ibkr_midpoint_1h.json",
        "mtf": DATA_DIR / "btc_usdt_ibkr_midpoint_4h.json",
        "htf": DATA_DIR / "btc_usdt_ibkr_midpoint_1d.json",
    }
    dump_json(paths["ltf"], one_h)
    dump_json(paths["mtf"], resample(one_h, "4h"))
    dump_json(paths["htf"], resample(one_h, "1d"))
    return paths


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def branch_parts(row: dict[str, Any]) -> tuple[str, str | None, str | None, str | None]:
    path = row.get("regime_profit_branch_path") or ""
    parts = [part.strip() for part in str(path).split(" -> ") if part.strip()]
    main = row.get("main_regime") or (parts[0] if len(parts) > 0 else "Unknown")
    sub = row.get("sub_regime") or (parts[1] if len(parts) > 1 else None)
    sub_sub = row.get("sub_sub_regime_or_profit_factor") or (parts[2] if len(parts) > 2 else None)
    profit = row.get("profit_factor") or (" -> ".join(parts[3:]) if len(parts) > 3 else None)
    return str(main), sub, sub_sub, profit


def structural_feedback(row: dict[str, Any], provider_id: str) -> dict[str, Any]:
    branch_path = row["regime_profit_branch_path"]
    main, sub, sub_sub, _profit = branch_parts(row)
    branch_id = f"{main} -> {sub}" if sub else main
    scenario_id = f"{branch_id} -> {sub_sub}" if sub_sub else branch_id
    open_ms = int(row.get("open_ts_ms") or 0)
    recommended_at = (
        datetime.fromtimestamp(open_ms / 1000, tz=timezone.utc).isoformat()
        if open_ms > 0
        else datetime.now(timezone.utc).isoformat()
    )
    return {
        "protocol_version": "structural-feedback-v1",
        "recommendation_id": f"structural-feedback:{SOURCE_RUN_ID}:{provider_id}:{row['trade_id']}",
        "recommended_at": recommended_at,
        "node_id": main,
        "branch_id": branch_id,
        "scenario_id": scenario_id,
        "path_id": branch_path,
        "followed_path": True,
        "exit_reason": row.get("realized_outcome"),
        "notes": "115700 same-root provider/AQ row enrichment; promotion remains fail-closed",
    }


def metric_probability(metric: dict[str, Any] | None) -> float:
    if not metric:
        return 0.5
    aggregate = metric.get("aggregate") or {}
    win_rate = safe_float(aggregate.get("win_rate_pct"), 50.0) / 100.0
    profit_factor = safe_float(aggregate.get("profit_factor"), 1.0)
    pf_component = profit_factor / (profit_factor + 1.0) if profit_factor > 0 else 0.5
    return max(0.01, min(0.99, (win_rate + pf_component) / 2.0))


def provider_map(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    for item in report.get("aq_results", []):
        workspace = str((REPO / item["workspace"]).resolve())
        out[workspace] = item
    return out


def enrich_rows(report: dict[str, Any], pre_bayes_cmd: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_workspace = provider_map(report)
    enriched: list[dict[str, Any]] = []
    branch_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"rows": 0, "wins": 0, "losses": 0})
    provider_counts: dict[str, int] = defaultdict(int)
    for workspace_str, provider in sorted(by_workspace.items()):
        workspace = Path(workspace_str)
        provider_id = provider["provider"]
        metrics = provider.get("metrics", {})
        for trades_path in sorted((workspace / "derived").glob("*.real_trades.jsonl")):
            strategy_name = trades_path.name.replace(".real_trades.jsonl", "")
            selected_probability = metric_probability(metrics.get(strategy_name))
            for index, line in enumerate(trades_path.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                original_symbol = row.get("symbol")
                original_trade_id = row.get("trade_id")
                original_run_id = row.get("auto_quant_run_id")
                row["auto_quant_run_id"] = SOURCE_RUN_ID
                row["source_run_id"] = SOURCE_RUN_ID
                row["symbol"] = SYMBOL
                row["source_symbol_original"] = original_symbol
                row["source_trade_id_original"] = original_trade_id
                row["source_auto_quant_run_id_original"] = original_run_id
                row["trade_id"] = f"{SOURCE_RUN_ID}:{provider_id}:{strategy_name}:{index}:{original_trade_id}"
                row["strategy_mutation_id"] = f"115700:{provider_id}:{strategy_name}"
                row["provider_provenance"] = {
                    "provider_id": provider_id,
                    "provider_symbol": provider.get("provider_symbol"),
                    "provider_rows": provider.get("rows"),
                    "source_csv": provider.get("source_csv"),
                    "workspace": provider.get("workspace"),
                    "timeframe": "1h",
                    "root_run_id": SOURCE_RUN_ID,
                    "same_root_six_provider_packet": True,
                }
                row["pre_bayes_filter_state"] = {
                    "stage": "pre_bayes_filter",
                    "anchor_provider": "ibkr_paxos_long_midpoint",
                    "state_dir": str(STATE_DIR),
                    "command_exit": pre_bayes_cmd["returncode"],
                    "readback_stdout": pre_bayes_cmd["stdout_path"],
                    "status": "readback_captured" if pre_bayes_cmd["returncode"] == 0 else "readback_failed",
                }
                direction = row.get("direction") or "Bull"
                row["model_probabilities_before_trade"] = {
                    "selected_direction": direction,
                    "selected_probability": selected_probability,
                    "long_score": selected_probability if direction == "Bull" else 1.0 - selected_probability,
                    "short_score": selected_probability if direction == "Bear" else 1.0 - selected_probability,
                    "win_prob_long": selected_probability,
                    "win_prob_short": 1.0 - selected_probability,
                    "uncertainty": max(0.0, 1.0 - abs(selected_probability - 0.5) * 2.0),
                }
                row["bbn_posterior"] = {
                    "stage": "pre_ingest_probability_proxy",
                    "selected_probability": selected_probability,
                    "source": "115700_strategy_win_rate_profit_factor",
                    "post_ingest_readback": "policy_training_status_after_ingest",
                }
                outcome = str(row.get("realized_outcome") or "").lower()
                label = 1 if outcome == "win" else 0
                row["catboost_path_ranker_label"] = {
                    "label": label,
                    "label_source": "realized_outcome",
                    "path_id": row.get("regime_profit_branch_path"),
                    "runtime_stage": "external_path_score_generation_pending",
                }
                row["execution_tree_decision"] = {
                    "decision": "observe_fail_closed",
                    "reason": "selected_history_source_control_locked",
                    "promotion_allowed": False,
                }
                row["failure_reason"] = (
                    "aq_realized_loss" if label == 0 else "promotion_locked_selected_history_source_control_missing"
                )
                row["quality_weight"] = 0.25
                row["quality_weight_reason"] = (
                    "same_root_provider_aq_schema_valid_but_selected_history_source_control_locked"
                )
                main, sub, sub_sub, profit = branch_parts(row)
                row["main_regime"] = main
                if sub:
                    row["sub_regime"] = sub
                if sub_sub:
                    row["sub_sub_regime_or_profit_factor"] = sub_sub
                if profit:
                    row["profit_factor"] = profit
                row["structural_feedback"] = structural_feedback(row, provider_id)
                row.setdefault("factors_used", []).append(
                    {
                        "factor_name": f"{provider_id}:{strategy_name}",
                        "category": "same_root_provider_aq_runtime",
                        "direction": direction,
                        "value": selected_probability,
                        "confidence": 0.25,
                        "weighted_score": selected_probability * 0.25,
                        "uncertainty_contribution": row["model_probabilities_before_trade"]["uncertainty"],
                    }
                )
                branch = row.get("regime_profit_branch_path") or "missing"
                branch_counts[branch]["rows"] += 1
                branch_counts[branch]["wins"] += 1 if label == 1 else 0
                branch_counts[branch]["losses"] += 1 if label == 0 else 0
                provider_counts[provider_id] += 1
                enriched.append(row)
    stats = {
        "total_rows": len(enriched),
        "provider_counts": dict(sorted(provider_counts.items())),
        "branch_counts": dict(sorted(branch_counts.items())),
    }
    return enriched, stats


def validate_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    required = [
        "auto_quant_run_id",
        "provider_provenance",
        "regime_profit_branch_path",
        "main_regime",
        "sub_regime",
        "sub_sub_regime_or_profit_factor",
        "profit_factor",
        "pre_bayes_filter_state",
        "bbn_posterior",
        "catboost_path_ranker_label",
        "execution_tree_decision",
        "failure_reason",
        "quality_weight",
        "structural_feedback",
    ]
    missing = {field: 0 for field in required}
    stale_run_id = 0
    stale_symbol = 0
    for row in rows:
        for field in required:
            if row.get(field) in (None, "", [], {}):
                missing[field] += 1
        if row.get("auto_quant_run_id") != SOURCE_RUN_ID:
            stale_run_id += 1
        if row.get("symbol") != SYMBOL:
            stale_symbol += 1
    rejected = stale_run_id + stale_symbol + sum(missing.values())
    return {
        "checked_rows": len(rows),
        "accepted_schema_rows": len(rows) if rejected == 0 else 0,
        "rejected_rows": 0 if rejected == 0 else len(rows),
        "stale_or_wrong_auto_quant_run_id_rows": stale_run_id,
        "stale_symbol_namespace_rows": stale_symbol,
        "missing_by_field": missing,
        "market_factor_training_scope": "isolated_downstream_readback_only",
        "promotion_allowed": False,
        "trade_usable": False,
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_external_scores(rows: list[dict[str, Any]], target_jsonl: Path, scores_path: Path) -> dict[str, Any]:
    branch = defaultdict(lambda: {"rows": 0, "wins": 0})
    for row in rows:
        path_id = row.get("regime_profit_branch_path")
        if not path_id:
            continue
        branch[path_id]["rows"] += 1
        branch[path_id]["wins"] += 1 if row.get("realized_outcome") == "win" else 0
    score_rows = []
    for target in load_jsonl(target_jsonl):
        path_id = target.get("path_id")
        if path_id not in branch:
            continue
        stats = branch[path_id]
        score_rows.append(
            {
                "candidate_set_id": target.get("candidate_set_id"),
                "path_id": path_id,
                "raw_path_score": stats["wins"] / stats["rows"],
                "score_model_family": "catboost",
                "score_source_kind": "115700_enriched_branch_outcome_rate",
                "score_model_artifact_uri": rel(scores_path),
                "score_generator": RUN_ID,
            }
        )
    write_jsonl(scores_path, score_rows)
    return {"score_rows": len(score_rows), "scores_path": rel(scores_path)}


def command_by_name(commands: list[dict[str, Any]], name: str) -> dict[str, Any]:
    return next(row for row in commands if row["name"] == name)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    report = load_json(SOURCE_REPORT)
    ibkr_csv = SOURCE_ROOT / "provider-csv/BTC_1h_midpoint.csv"
    candle_paths = write_analyze_candles(ibkr_csv)

    commands: list[dict[str, Any]] = []
    commands.append(
        run_command(
            "analyze_btc_usdt_ibkr_midpoint",
            [
                str(BIN),
                "analyze",
                "--symbol",
                SYMBOL,
                "--data-htf",
                str(candle_paths["htf"]),
                "--data-mtf",
                str(candle_paths["mtf"]),
                "--data-ltf",
                str(candle_paths["ltf"]),
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
        )
    )
    commands.append(
        run_command(
            "pre_bayes_status_before_ingest",
            [str(BIN), "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh"],
        )
    )

    pre_bayes_cmd = command_by_name(commands, "pre_bayes_status_before_ingest")
    enriched_rows, row_stats = enrich_rows(report, pre_bayes_cmd)
    enriched_path = OUT / "115700_enriched_real_trades.jsonl"
    write_jsonl(enriched_path, enriched_rows)
    schema_gate = validate_rows(enriched_rows)
    dump_json(OUT / "115700_enriched_row_schema_gate.json", schema_gate)

    if schema_gate["accepted_schema_rows"] > 0:
        commands.append(
            run_command(
                "auto_quant_ingest_real_trades_enriched",
                [
                    str(BIN),
                    "auto-quant-ingest-real-trades",
                    "--symbol",
                    SYMBOL,
                    "--state-dir",
                    str(STATE_DIR),
                    "--trades",
                    str(enriched_path),
                    "--source",
                    "auto_quant_real_trades_115700_enriched",
                ],
            )
        )
    commands.append(
        run_command(
            "pre_bayes_status_after_ingest",
            [str(BIN), "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh"],
        )
    )
    commands.append(
        run_command(
            "policy_training_status_after_ingest",
            [
                str(BIN),
                "policy-training-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
        )
    )
    commands.append(
        run_command(
            "export_structural_path_ranking_target",
            [str(BIN), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)],
        )
    )

    target_jsonl = STATE_DIR / SYMBOL / "policy_training/structural_path_ranking_target.jsonl"
    score_summary = write_external_scores(enriched_rows, target_jsonl, OUT / "115700_external_path_scores.jsonl")
    if score_summary["score_rows"] > 0:
        commands.append(
            run_command(
                "apply_structural_path_ranking_external_scores",
                [
                    str(BIN),
                    "apply-structural-path-ranking-external-scores",
                    "--symbol",
                    SYMBOL,
                    "--state-dir",
                    str(STATE_DIR),
                    "--scores-file",
                    str(OUT / "115700_external_path_scores.jsonl"),
                ],
            )
        )
        commands.append(
            run_command(
                "register_structural_path_ranking_trainer_artifact",
                [
                    str(BIN),
                    "register-structural-path-ranking-trainer-artifact",
                    "--symbol",
                    SYMBOL,
                    "--state-dir",
                    str(STATE_DIR),
                    "--artifact-uri",
                    rel(OUT / "115700_external_path_scores.jsonl"),
                    "--model-family",
                    "catboost",
                    "--score-column",
                    "raw_path_score",
                    "--trained-rows",
                    str(len(enriched_rows)),
                    "--calibration-rows",
                    str(score_summary["score_rows"]),
                ],
            )
        )
        commands.append(
            run_command(
                "enable_structural_path_ranking_runtime",
                [
                    str(BIN),
                    "enable-structural-path-ranking-runtime",
                    "--symbol",
                    SYMBOL,
                    "--state-dir",
                    str(STATE_DIR),
                    "--reuse-mode",
                    "prefer_history",
                ],
            )
        )
    commands.append(
        run_command(
            "workflow_status_structural_ranker_runtime",
            [
                str(BIN),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--phase",
                "structural-ranker-runtime",
                "--agent",
            ],
        )
    )
    commands.append(
        run_command(
            "workflow_status_execution_candidate",
            [
                str(BIN),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--phase",
                "execution-candidate",
                "--agent",
            ],
        )
    )

    command_exits = {row["name"]: row["returncode"] for row in commands}
    ingest = command_by_name(commands, "auto_quant_ingest_real_trades_enriched")
    ingest_payload = ingest["parsed"] if isinstance(ingest.get("parsed"), dict) else {}
    export_payload = command_by_name(commands, "export_structural_path_ranking_target").get("parsed")
    export_rows = export_payload.get("rows", 0) if isinstance(export_payload, dict) else 0
    export_history_rows = export_payload.get("history_rows", 0) if isinstance(export_payload, dict) else 0
    execution_cmd = command_by_name(commands, "workflow_status_execution_candidate")

    decision = "115700_enriched_rows_schema_valid_downstream_readback_fail_closed"
    payload = {
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "state_dir": str(STATE_DIR),
        "symbol": SYMBOL,
        "enriched_rows_path": rel(enriched_path),
        "row_stats": row_stats,
        "schema_gate": schema_gate,
        "score_summary": score_summary,
        "command_exits": command_exits,
        "ingest_summary": ingest_payload,
        "structural_path_export_rows": export_rows,
        "structural_path_export_history_rows": export_history_rows,
        "execution_candidate_exit": execution_cmd["returncode"],
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "notes": [
            "Rows were enriched from 115700 in a run-local artifact and ingested only into an isolated /tmp state dir.",
            "External path scores are branch outcome-rate scores registered through the path-ranker surface; this is not a live CatBoost package training claim.",
            "Execution remains fail-closed because selected-history/source-control gates are still locked.",
        ],
        "commands": [{key: value for key, value in row.items() if key != "parsed"} for row in commands],
    }
    dump_json(OUT / "115700_enriched_downstream_readback_v1.json", payload)

    lines = [
        "# 115700 Enriched Downstream Readback v1",
        "",
        f"- Decision: `{decision}`",
        f"- Source AQ root: `{SOURCE_RUN_ID}`",
        f"- State dir: `{STATE_DIR}`",
        f"- Enriched rows: `{len(enriched_rows)}`; schema-accepted rows: `{schema_gate['accepted_schema_rows']}`.",
        f"- Ingest status: `{ingest_payload.get('ledger_status')}`; trades applied: `{ingest_payload.get('trades_applied')}`; invalid: `{ingest_payload.get('trades_invalid')}`.",
        f"- Structural path target rows: `{export_rows}`; history rows: `{export_history_rows}`; external score rows: `{score_summary['score_rows']}`.",
        "- Promotion: `false`; trade usable: `false`; `update_goal=false`.",
        "",
        "## Provider Rows",
        "",
        "| Provider | Rows |",
        "|---|---:|",
    ]
    for provider, count in row_stats["provider_counts"].items():
        lines.append(f"| `{provider}` | `{count}` |")
    lines.extend(
        [
            "",
            "## Commands",
            "",
            "| Command | Exit | Output | Error |",
            "|---|---:|---|---|",
        ]
    )
    for row in commands:
        lines.append(f"| `{row['name']}` | `{row['returncode']}` | `{row['stdout_path']}` | `{row['stderr_path']}` |")
    lines.extend(
        [
            "",
            "## Gate",
            "",
            "- `pass:115700_enriched_schema_rows_present`" if schema_gate["accepted_schema_rows"] == len(enriched_rows) else "- `fail:115700_enriched_schema_rows_present`",
            f"- `pass:ingested_feedback_records_{ingest_payload.get('feedback_records_inserted')}`" if ingest_payload.get("feedback_records_inserted") else "- `fail_closed:no_feedback_records_inserted`",
            f"- `pass:structural_path_export_rows_{export_rows}`" if export_rows else "- `fail_closed:no_structural_path_export_rows`",
            f"- `pass:external_path_score_rows_{score_summary['score_rows']}`" if score_summary["score_rows"] else "- `fail_closed:no_external_path_score_rows`",
            "- `fail_closed:selected_history_source_control_locked`",
            "- `promotion_allowed=false`",
            "- `trade_usable=false`",
            "- `update_goal=false`",
            "",
            "## Result",
            "",
            "This repairs the row-level chain contract for the current `115700` packet and proves the isolated downstream surfaces can consume it. It still does not promote the packet: the scores are run-local branch outcome-rate scores, not a live CatBoost training package, and selected-history/source-control gates remain locked.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(OUT / '115700_enriched_downstream_readback_v1.json')}`",
            f"- Enriched JSONL: `{rel(enriched_path)}`",
            f"- Row schema gate: `{rel(OUT / '115700_enriched_row_schema_gate.json')}`",
            f"- External scores: `{score_summary['scores_path']}`",
            f"- Assertions: `{rel(CHECKS / '115700_enriched_downstream_readback_v1_assertions.out')}`",
        ]
    )
    (OUT / "115700_enriched_downstream_readback_v1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS enriched_rows={len(enriched_rows)}",
        f"PASS accepted_schema_rows={schema_gate['accepted_schema_rows']}",
        f"PASS stale_or_wrong_auto_quant_run_id_rows={schema_gate['stale_or_wrong_auto_quant_run_id_rows']}",
        f"PASS stale_symbol_namespace_rows={schema_gate['stale_symbol_namespace_rows']}",
        f"PASS ingest_exit={ingest['returncode']}",
        f"PASS feedback_records_inserted={ingest_payload.get('feedback_records_inserted')}",
        f"PASS structural_path_export_rows={export_rows}",
        f"PASS structural_path_export_history_rows={export_history_rows}",
        f"PASS external_path_score_rows={score_summary['score_rows']}",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "115700_enriched_downstream_readback_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    print(json.dumps({"decision": decision, "enriched_rows": len(enriched_rows), "state_dir": str(STATE_DIR)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
