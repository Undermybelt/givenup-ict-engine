#!/usr/bin/env python3
"""Run non-BTC local Auto-Quant MTF data through ict-engine readback chain.

This is an experiment artifact, not runtime code. It keeps all generated state
inside this run root and records fail-closed gate evidence.
"""

from __future__ import annotations

import csv
import json
import math
import os
import subprocess
from datetime import timezone
from pathlib import Path
from typing import Any

import pandas as pd


SCRIPT = Path(__file__).resolve()
RUN_ROOT = SCRIPT.parents[1]
REPO = RUN_ROOT.parents[4]
BIN = REPO / "target/debug/ict-engine"
AQ_DATA = Path("/Users/thrill3r/Auto-Quant/user_data/data")
PACKET = RUN_ROOT / "non-btc-local-aq-mtf-chain-probe-v1"
PROVIDER_JSON = RUN_ROOT / "provider-data-json"
OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"

MARKETS = [
    {
        "symbol": "ETH_USDT",
        "state_symbol": "ETH_LOCAL_AQ_MTF_123820",
        "family": "crypto_non_btc",
        "files": {
            "1h": AQ_DATA / "ETH_USDT-1h.feather",
            "4h": AQ_DATA / "ETH_USDT-4h.feather",
            "1d": AQ_DATA / "ETH_USDT-1d.feather",
        },
    },
    {
        "symbol": "NQ_USD",
        "state_symbol": "NQ_LOCAL_AQ_MTF_123820",
        "family": "tradfi_futures",
        "files": {
            "1h": AQ_DATA / "NQ_USD-1h.feather",
            "4h": AQ_DATA / "NQ_USD-4h.feather",
            "1d": AQ_DATA / "NQ_USD-1d.feather",
        },
    },
]


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def safe_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(result) or math.isinf(result):
        return None
    return result


def normalize_timestamp(value: Any) -> str:
    ts = pd.to_datetime(value, utc=True)
    return ts.tz_convert(timezone.utc).isoformat().replace("+00:00", "Z")


def convert_feather(source: Path, dest: Path, max_rows: int = 1500) -> dict[str, Any]:
    df = pd.read_feather(source)
    if "date" in df.columns and "timestamp" not in df.columns:
        df = df.rename(columns={"date": "timestamp"})
    required = ["timestamp", "open", "high", "low", "close", "volume"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise RuntimeError(f"{source} missing columns {missing}")
    df = df[required].dropna(subset=["timestamp", "open", "high", "low", "close"])
    df = df.tail(max_rows).copy()
    rows: list[dict[str, Any]] = []
    for record in df.to_dict("records"):
        rows.append(
            {
                "timestamp": normalize_timestamp(record["timestamp"]),
                "open": safe_float(record["open"]),
                "high": safe_float(record["high"]),
                "low": safe_float(record["low"]),
                "close": safe_float(record["close"]),
                "volume": safe_float(record.get("volume")) or 0.0,
            }
        )
    dest.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    return {
        "source": str(source),
        "dest": rel(dest),
        "rows": len(rows),
        "first_ts": rows[0]["timestamp"] if rows else None,
        "last_ts": rows[-1]["timestamp"] if rows else None,
    }


def run_command(name: str, args: list[str], timeout: int = 180) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    cmd_path = OUT / f"{name}.cmd"
    out_path = OUT / f"{name}.out"
    err_path = OUT / f"{name}.err"
    exit_path = OUT / f"{name}.exit"
    cmd_path.write_text(" ".join(args) + "\n", encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
        }
    )
    try:
        proc = subprocess.run(
            args,
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            env=env,
        )
        code = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        code = 124
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n"
    out_path.write_text(stdout, encoding="utf-8")
    err_path.write_text(stderr, encoding="utf-8")
    exit_path.write_text(f"{code}\n", encoding="utf-8")
    return {
        "name": name,
        "exit": code,
        "cmd_path": rel(cmd_path),
        "stdout_path": rel(out_path),
        "stderr_path": rel(err_path),
        "exit_path": rel(exit_path),
    }


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def parse_stdout_json(command: dict[str, Any]) -> Any:
    return load_json(REPO / command["stdout_path"])


def walk(obj: Any, keys: set[str], found: dict[str, Any]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in keys and key not in found:
                found[key] = value
            walk(value, keys, found)
    elif isinstance(obj, list):
        for item in obj:
            walk(item, keys, found)


def summarize_symbol(state_dir: Path, state_symbol: str, commands: list[dict[str, Any]]) -> dict[str, Any]:
    symbol_dir = state_dir / state_symbol
    snapshot = load_json(symbol_dir / "workflow_snapshot.json")
    execution = load_json(symbol_dir / "execution_candidate.json")
    latest = snapshot.get("latest_analyze", {}) if isinstance(snapshot, dict) else {}
    latest_exec = snapshot.get("latest_execution_candidate", {}) if isinstance(snapshot, dict) else {}
    soft = latest.get("pre_bayes_soft_evidence") if isinstance(latest, dict) else None
    market_probs = soft.get("market_regime", {}) if isinstance(soft, dict) else {}
    max_regime_probability = max(
        [safe_float(v) or 0.0 for v in market_probs.values()],
        default=0.0,
    )
    command_exits = {cmd["name"]: cmd["exit"] for cmd in commands}
    found: dict[str, Any] = {}
    walk(
        snapshot,
        {
            "path_ranker_runtime_source",
            "raw_scored_mature",
            "production_validation",
            "candidate_status",
            "promotion_status",
            "pre_bayes_gate_status",
            "canonical_structural_active_regime",
            "canonical_structural_confidence",
            "execution_readiness",
            "execution_gate_status",
            "selected_direction",
        },
        found,
    )
    return {
        "state_symbol": state_symbol,
        "state_dir": rel(state_dir),
        "state_files": {
            "workflow_snapshot": (symbol_dir / "workflow_snapshot.json").exists(),
            "bbn_network": (symbol_dir / "bbn_network.json").exists(),
            "execution_candidate": (symbol_dir / "execution_candidate.json").exists(),
            "execution_tree_trace": (symbol_dir / "execution_tree_trace.json").exists(),
            "pre_bayes_policy_history": (symbol_dir / "pre_bayes_policy_history.json").exists(),
        },
        "command_exits": command_exits,
        "active_regime": latest.get("canonical_structural_active_regime") if isinstance(latest, dict) else None,
        "canonical_structural_confidence": latest.get("canonical_structural_confidence") if isinstance(latest, dict) else None,
        "market_regime_probabilities": market_probs,
        "max_regime_probability": max_regime_probability,
        "pre_bayes_gate_status": latest.get("pre_bayes_gate_status") if isinstance(latest, dict) else None,
        "selected_direction": latest.get("selected_direction") if isinstance(latest, dict) else None,
        "execution_gate_status": latest.get("execution_gate_status") if isinstance(latest, dict) else None,
        "execution_readiness": latest.get("execution_readiness") if isinstance(latest, dict) else None,
        "execution_candidate_status": (
            execution.get("candidate_status")
            if isinstance(execution, dict)
            else latest_exec.get("candidate_status")
            if isinstance(latest_exec, dict)
            else None
        ),
        "actionable": (
            execution.get("actionable")
            if isinstance(execution, dict)
            else latest_exec.get("actionable")
            if isinstance(latest_exec, dict)
            else None
        ),
        "found_fields": found,
    }


def main() -> int:
    PACKET.mkdir(parents=True, exist_ok=True)
    PROVIDER_JSON.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    conversions: list[dict[str, Any]] = []
    for market in MARKETS:
        for timeframe, source in market["files"].items():
            dest = PROVIDER_JSON / f"{market['symbol']}-{timeframe}.json"
            conversions.append(convert_feather(source, dest))

    provider_commands = [
        run_command("00_provider_status_compact", [str(BIN), "provider-status", "--compact"], 90),
        run_command("01_provider_yfinance_compact", [str(BIN), "provider-status", "--provider", "yfinance", "--compact"], 90),
        run_command("02_provider_kraken_cli_compact", [str(BIN), "provider-status", "--provider", "kraken_cli", "--compact"], 90),
        run_command("03_provider_ibkr_compact", [str(BIN), "provider-status", "--provider", "ibkr", "--compact"], 90),
        run_command("04_provider_tradingview_mcp_compact", [str(BIN), "provider-status", "--provider", "tradingview_mcp", "--compact"], 90),
    ]

    market_summaries: list[dict[str, Any]] = []
    market_command_records: dict[str, list[dict[str, Any]]] = {}
    for market in MARKETS:
        state_symbol = market["state_symbol"]
        state_dir = RUN_ROOT / f"state_{market['symbol'].lower()}_local_aq_mtf_v1"
        files = {
            tf: PROVIDER_JSON / f"{market['symbol']}-{tf}.json"
            for tf in ["1h", "4h", "1d"]
        }
        commands = [
            run_command(
                f"10_{market['symbol']}_factor_research_native",
                [
                    str(BIN),
                    "factor-research",
                    "--symbol",
                    state_symbol,
                    "--data",
                    rel(files["1h"]),
                    "--data-1h",
                    rel(files["1h"]),
                    "--data-4h",
                    rel(files["4h"]),
                    "--data-1d",
                    rel(files["1d"]),
                    "--state-dir",
                    rel(state_dir),
                    "--backend",
                    "native",
                    "--output-format",
                    "json",
                ],
                240,
            ),
            run_command(
                f"11_{market['symbol']}_analyze_mtf",
                [
                    str(BIN),
                    "analyze",
                    "--symbol",
                    state_symbol,
                    "--data-ltf",
                    rel(files["1h"]),
                    "--data-mtf",
                    rel(files["4h"]),
                    "--data-htf",
                    rel(files["1d"]),
                    "--state-dir",
                    rel(state_dir),
                    "--output-format",
                    "json",
                ],
                240,
            ),
            run_command(
                f"12_{market['symbol']}_pre_bayes_status",
                [
                    str(BIN),
                    "pre-bayes-status",
                    "--symbol",
                    state_symbol,
                    "--state-dir",
                    rel(state_dir),
                    "--refresh",
                    "--output-format",
                    "json",
                ],
                120,
            ),
            run_command(
                f"13_{market['symbol']}_policy_training_status",
                [
                    str(BIN),
                    "policy-training-status",
                    "--symbol",
                    state_symbol,
                    "--state-dir",
                    rel(state_dir),
                    "--output-format",
                    "json",
                ],
                120,
            ),
            run_command(
                f"14_{market['symbol']}_workflow_status",
                [
                    str(BIN),
                    "workflow-status",
                    "--symbol",
                    state_symbol,
                    "--state-dir",
                    rel(state_dir),
                    "--refresh",
                    "--output-format",
                    "json",
                ],
                120,
            ),
            run_command(
                f"15_{market['symbol']}_export_path_ranking_target",
                [
                    str(BIN),
                    "export-structural-path-ranking-target",
                    "--symbol",
                    state_symbol,
                    "--state-dir",
                    rel(state_dir),
                ],
                120,
            ),
            run_command(
                f"16_{market['symbol']}_validate_market_state_1h",
                [
                    str(BIN),
                    "validate-market-state",
                    "--data",
                    rel(files["1h"]),
                    "--window-size",
                    "100",
                    "--step-size",
                    "50",
                    "--profile",
                    "high_confidence",
                    "--compact",
                ],
                120,
            ),
            run_command(
                f"17_{market['symbol']}_validate_market_state_4h",
                [
                    str(BIN),
                    "validate-market-state",
                    "--data",
                    rel(files["4h"]),
                    "--window-size",
                    "100",
                    "--step-size",
                    "50",
                    "--profile",
                    "high_confidence",
                    "--compact",
                ],
                120,
            ),
        ]
        market_command_records[market["symbol"]] = commands
        summary = summarize_symbol(state_dir, state_symbol, commands)
        summary["source_symbol"] = market["symbol"]
        summary["family"] = market["family"]
        market_summaries.append(summary)

    max_prob = max((item["max_regime_probability"] for item in market_summaries), default=0.0)
    accepted_95 = [item for item in market_summaries if item["max_regime_probability"] >= 0.95]
    execution_ready = [
        item
        for item in market_summaries
        if item.get("actionable") is True
        or item.get("execution_candidate_status") in {"ready", "actionable"}
    ]
    gate = (
        "non_btc_local_aq_mtf_chain_probe_fail_closed"
        if not accepted_95 or not execution_ready
        else "non_btc_local_aq_mtf_chain_probe_candidate"
    )

    provider_statuses = {cmd["name"]: parse_stdout_json(cmd) for cmd in provider_commands}
    packet = {
        "run_id": RUN_ROOT.name,
        "scope": "non_btc_local_auto_quant_mtf_data_through_ict_engine_readback_chain",
        "data_source": "local_auto_quant_feather_files_under_/Users/thrill3r/Auto-Quant/user_data/data",
        "provider_status_commands": provider_commands,
        "provider_statuses": provider_statuses,
        "conversions": conversions,
        "markets": market_summaries,
        "market_commands": market_command_records,
        "gate": gate,
        "accepted_95_count": len(accepted_95),
        "max_regime_probability": max_prob,
        "production_likelihood_mutation": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    (PACKET / "non_btc_local_aq_mtf_chain_probe_v1.json").write_text(
        json.dumps(packet, indent=2) + "\n",
        encoding="utf-8",
    )

    with (PACKET / "market_summary_v1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "source_symbol",
                "family",
                "state_symbol",
                "pre_bayes_gate_status",
                "active_regime",
                "canonical_structural_confidence",
                "max_regime_probability",
                "execution_gate_status",
                "execution_readiness",
                "execution_candidate_status",
                "actionable",
            ],
        )
        writer.writeheader()
        for item in market_summaries:
            writer.writerow({key: item.get(key) for key in writer.fieldnames})

    report = [
        "# Non-BTC Local Auto-Quant MTF Chain Probe v1",
        "",
        f"Run id: `{RUN_ROOT.name}`",
        "",
        "## Scope",
        "Use existing local Auto-Quant feather data for non-BTC / non-1h context checks, convert it to ict-engine candle JSON, then run ict-engine factor-research, analyze, Pre-Bayes/BBN workflow readback, policy training status, path-ranking export, and market-state validation.",
        "",
        "This does not mutate production BBN CPDs, CatBoost models, execution-tree gates, or repo runtime code.",
        "",
        "## Readback",
        f"- Markets: `{', '.join(item['source_symbol'] for item in market_summaries)}`.",
        f"- Converted candle files: `{len(conversions)}`.",
        f"- Max regime probability observed: `{max_prob:.6f}`.",
        f"- Accepted >=95% regime contexts: `{len(accepted_95)}`.",
        f"- Execution-ready/actionable contexts: `{len(execution_ready)}`.",
        f"- Gate: `{gate}`.",
        "",
        "## Market Summary",
    ]
    for item in market_summaries:
        report.append(
            "- `{source_symbol}` family `{family}` active_regime `{active_regime}` "
            "confidence `{canonical_structural_confidence}` max_prob `{max_regime_probability}` "
            "pre_bayes `{pre_bayes_gate_status}` execution_gate `{execution_gate_status}` "
            "candidate `{execution_candidate_status}` actionable `{actionable}`.".format(**item)
        )
    report.extend(
        [
            "",
            "## Decision",
            "- Candidate non-BTC / non-1h local Auto-Quant contexts were exercised through ict-engine, but they do not satisfy Board A acceptance.",
            "- `production_likelihood_mutation=false`.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{rel(PACKET / 'non_btc_local_aq_mtf_chain_probe_v1.json')}`",
            f"- Market summary CSV: `{rel(PACKET / 'market_summary_v1.csv')}`",
            f"- Converted candle JSON root: `{rel(PROVIDER_JSON)}`",
            f"- Command output root: `{rel(OUT)}`",
            f"- Assertions: `{rel(CHECKS / 'non_btc_local_aq_mtf_chain_probe_v1_assertions.out')}`",
        ]
    )
    (PACKET / "non_btc_local_aq_mtf_chain_probe_v1.md").write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )

    assertions = [
        f"PASS run_id={RUN_ROOT.name}",
        f"PASS converted_candle_files={len(conversions)}",
        f"PASS markets_checked={len(market_summaries)}",
        f"FAIL_CLOSED accepted_95_count={len(accepted_95)} target=2",
        f"FAIL_CLOSED max_regime_probability={max_prob:.6f} target=0.95",
        f"FAIL_CLOSED execution_ready_contexts={len(execution_ready)} target=2",
        "PASS production_likelihood_mutation=false",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "non_btc_local_aq_mtf_chain_probe_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
