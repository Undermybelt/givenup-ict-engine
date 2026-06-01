#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


SCRIPT = Path(__file__).resolve()
BASE = SCRIPT.parents[1]
REPO = BASE.parents[3]
RESEARCH_SCRIPTS = REPO / "support/scripts/research"
if str(RESEARCH_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(RESEARCH_SCRIPTS))

from same_tree_practical_closure import (  # noqa: E402
    DEPLOY_READY_READINESS_CONTRACT,
    REQUIRED_COMMAND_RESULT_STAGES,
    write_same_tree_practical_closure_packet,
)


STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
DEFAULT_MATERIALIZATION_ROOT = Path(
    "/tmp/ict-engine-nq-compound-rv-stress-feedback-materialization-20260530T043351+0800"
)
ROOT = Path(f"/tmp/ict-engine-nq-compound-rv-stress-practical-lifecycle-{STAMP}")

SYMBOL = "TOMAC_NQ_COMPOUND_RV_STRESS_GATE_PRACTICAL_LIFECYCLE_V1"
FACTOR_ID = "nq_compound_trend_rrr_chopfilter_rv_stress_gate_rescore_v1"
PARENT_FACTOR_ID = "nq_compound_trend_rrr_chopfilter_v1"
TRADE_FEEDBACK_SOURCE = "auto_quant_real_trades:simulated_backtest:tomac_nq_compound_rv_stress_gate_v1"
ACCEPTED_FEEDBACK_MARKERS = (
    "paper_execution_feedback",
    "live_execution_feedback",
    "paper_trade_feedback",
    "live_trade_feedback",
    "broker_execution_feedback",
)
SIMULATED_FEEDBACK_MARKERS = (
    "simulated_backtest",
    "retained_real_event_label_simulation",
    "ibkr_paper_trade_simulation",
    "paper_trade_simulation",
    "simulation_child_gate",
    "child_gate_filtered",
    "simulated_feedback",
)
BRANCH_PATH = (
    "US index futures -> NQ -> ETH/full_retained_session -> 1m parent execution + shifted 5m/15m/30m/1h/4h/1d context "
    "-> HtfTrendRegime -> ChopFilter(ER>=0.35,n40) -> MomentumResonance -> CompoundTrendRrrBreadth "
    "-> FixedRrrBracket -> RealizedVolatilityStressGate(30m_abs_ret16_max <= 0.04174409724) "
    "-> PracticalLifecycleContinuation"
)
ROW_CAPS = {
    "1m": 5000,
    "5m": 2500,
    "15m": 1200,
    "30m": 800,
    "1h": 500,
    "4h": 240,
    "1d": 160,
}
SOURCE_DATA_ROOT = Path(
    os.environ.get("NQ_COMPOUND_SOURCE_DATA_ROOT", "/tmp/ict-engine-auto-quant/user_data/data")
)

STATE = ROOT / "state"
CMD = ROOT / "command-output"
CHECKS = ROOT / "checks"
SUMMARIES = ROOT / "summaries"
MATERIALS = ROOT / "materials"
MODEL_DIR = ROOT / "path_ranker_model"
DATA_DIR = ROOT / "data/provider/normalized"
SCORES = ROOT / "path_ranker_scores.csv"

ICT = REPO / ".local-artifacts/cargo-target/debug/ict-engine"
if not ICT.exists():
    ICT = REPO / "target/debug/ict-engine"
TRAINER = REPO / "support/scripts/auto_quant_external/pandas_path_ranker_trainer.py"
PY_RUNNER = Path("python3")


def configure_paths(root: Path) -> None:
    global ROOT, STATE, CMD, CHECKS, SUMMARIES, MATERIALS, MODEL_DIR, DATA_DIR, SCORES
    ROOT = Path(root)
    STATE = ROOT / "state"
    CMD = ROOT / "command-output"
    CHECKS = ROOT / "checks"
    SUMMARIES = ROOT / "summaries"
    MATERIALS = ROOT / "materials"
    MODEL_DIR = ROOT / "path_ranker_model"
    DATA_DIR = ROOT / "data/provider/normalized"
    SCORES = ROOT / "path_ranker_scores.csv"


def read_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def read_policy_training_summary() -> dict:
    summary = read_json(STATE / SYMBOL / "policy_training/structural_path_ranking_target_summary.json")
    for name in ("19_policy_after_ranker.out", "10_policy_after_feedback.out"):
        payload = read_json(CMD / name)
        if not payload:
            continue
        merged = dict(summary)
        merged.update(payload)
        summary = merged
    return summary


def read_json_or_list(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_safe(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def source_feather_path(timeframe: str) -> Path:
    candidates = [
        SOURCE_DATA_ROOT / f"NQ_USD-{timeframe}.feather",
        SOURCE_DATA_ROOT / "binance" / f"NQ_USD-{timeframe}.feather",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def feather_to_csv(source_feather: Path, target_csv: Path) -> int:
    target_csv.parent.mkdir(parents=True, exist_ok=True)
    script = r"""
import json
import sys
from pathlib import Path

import pandas as pd

source = Path(sys.argv[1])
target = Path(sys.argv[2])
frame = pd.read_feather(source)
frame["date"] = pd.to_datetime(frame["date"], utc=True)
frame = frame.sort_values("date").drop_duplicates(subset=["date"], keep="last")
frame["timestamp"] = frame["date"].dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
out = frame[["timestamp", "open", "high", "low", "close", "volume"]].copy()
out.to_csv(target, index=False)
print(json.dumps({"rows": int(len(out))}))
"""
    proc = subprocess.run(
        [str(PY_RUNNER), "-c", script, str(source_feather), str(target_csv)],
        text=True,
        capture_output=True,
        timeout=900,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or f"feather_to_csv failed for {source_feather}")
    summary = json.loads(proc.stdout)
    return int(summary.get("rows") or 0)


def trim_csv_rows(source: Path, target: Path, keep_rows: int) -> int:
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = deque(reader, maxlen=keep_rows)
        fieldnames = reader.fieldnames or ["timestamp", "open", "high", "low", "close", "volume"]
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def trimmed_csv_to_cleaned_json(source_csv: Path, target_json: Path) -> int:
    with source_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        candles = [
            {
                "timestamp": row["timestamp"],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }
            for row in reader
        ]
    target_json.parent.mkdir(parents=True, exist_ok=True)
    target_json.write_text(
        json.dumps({"symbol": SYMBOL, "candles": candles}, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(candles)


def prepare_local_data(data_root: Path) -> dict[str, dict[str, object]]:
    full_dir = ROOT / "data/provider/full"
    full_dir.mkdir(parents=True, exist_ok=True)
    summaries: dict[str, dict[str, object]] = {}
    market = SYMBOL.lower()
    for timeframe, keep_rows in ROW_CAPS.items():
        source = source_feather_path(timeframe)
        if not source.exists():
            raise RuntimeError(f"missing NQ source feather for {timeframe}: {source}")
        full_csv = full_dir / f"nq_usd_{timeframe}_full.csv"
        trimmed_csv = data_root / f"nq_usd_{timeframe}_trimmed.csv"
        cleaned_json = data_root / f"cleaned-{timeframe}" / f"{market}.continuous-{timeframe}.json"
        full_rows = feather_to_csv(source, full_csv)
        kept_rows = trim_csv_rows(full_csv, trimmed_csv, keep_rows)
        cleaned_rows = trimmed_csv_to_cleaned_json(trimmed_csv, cleaned_json)
        summaries[timeframe] = {
            "source": str(source),
            "full_csv": str(full_csv),
            "trimmed_csv": str(trimmed_csv),
            "cleaned_json": str(cleaned_json),
            "full_rows": full_rows,
            "kept_rows": kept_rows,
            "cleaned_rows": cleaned_rows,
        }
    write_json(
        CHECKS / "source_data_summary.json",
        {
            "source_data_root": str(SOURCE_DATA_ROOT),
            "row_caps": ROW_CAPS,
            "timeframes": summaries,
        },
    )
    return summaries


def reset_prior_init_state() -> dict[str, list[str]]:
    removed: list[str] = []
    rolled_back: list[str] = []
    symbol_dirs = [STATE / SYMBOL, STATE / "auto-quant" / SYMBOL]
    for symbol_dir in dict.fromkeys(symbol_dirs):
        for path in (
            symbol_dir / "bbn_network.json",
            symbol_dir / "auto_quant_prior_init_history.json",
        ):
            if path.exists():
                path.unlink()
                removed.append(str(path))
        if symbol_dir.exists():
            for path in symbol_dir.glob("auto_quant_prior_init*.json"):
                if path.exists():
                    path.unlink()
                    removed.append(str(path))
        ledger_path = symbol_dir / "artifact_ledger.json"
        ledger = read_json(ledger_path)
        if not isinstance(ledger, list):
            try:
                ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else []
            except Exception:
                ledger = []
        if isinstance(ledger, list):
            changed = False
            for entry in ledger:
                if not isinstance(entry, dict):
                    continue
                if entry.get("artifact_kind") == "auto_quant_prior_init_applied" and entry.get("status") == "applied":
                    entry["status"] = "rolled_back_before_lifecycle_rerun"
                    entry["decision_hint"] = "rolled_back_before_lifecycle_rerun"
                    rolled_back.append(str(entry.get("artifact_id") or entry.get("entry_id") or "unknown"))
                    changed = True
            if changed:
                write_json(ledger_path, ledger)
    summary = {"removed": removed, "rolled_back": rolled_back}
    if removed or rolled_back:
        write_json(CHECKS / "prior_init_reset.json", summary)
    return summary


def json_safe(value: object) -> object:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    return value


def run_cmd(name: str, argv: list[object], timeout: int = 300) -> dict:
    CMD.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    argv_s = [str(item) for item in argv]
    (CMD / f"{name}.cmd").write_text(" ".join(argv_s) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(argv_s, cwd=REPO, text=True, capture_output=True, timeout=timeout)
        stdout = proc.stdout
        stderr = proc.stderr
        rc = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n"
        rc = 124
        timed_out = True
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    (CMD / f"{name}.out").write_text(stdout, encoding="utf-8")
    (CMD / f"{name}.err").write_text(stderr, encoding="utf-8")
    (CHECKS / f"{name}.exit").write_text(f"{rc}\n", encoding="utf-8")
    return {"name": name, "exit": rc, "timed_out": timed_out}


def run_stage(stage: str, name: str, argv: list[object], timeout: int = 300) -> dict:
    result = run_cmd(name, argv, timeout)
    result["stage"] = stage
    return result


def replace_cli_arg(argv: list[object], flag: str, value: object) -> list[object]:
    updated = list(argv)
    try:
        index = [str(item) for item in updated].index(flag)
    except ValueError:
        updated.extend([flag, value])
        return updated
    if index + 1 < len(updated):
        updated[index + 1] = value
    else:
        updated.append(value)
    return updated


def register_trainer_argv_from_artifact(argv: list[object]) -> list[object]:
    artifact = read_json(MODEL_DIR / "trainer_artifact.json")
    model_family = str(artifact.get("model_family") or "").strip()
    if not model_family:
        return list(argv)
    updated = replace_cli_arg(argv, "--model-family", model_family)
    trained_rows = positive_int(artifact.get("trained_rows"))
    if trained_rows > 0:
        updated = replace_cli_arg(updated, "--trained-rows", trained_rows)
    calibration_rows = positive_int(artifact.get("calibration_rows"))
    if calibration_rows > 0:
        updated = replace_cli_arg(updated, "--calibration-rows", calibration_rows)
    return updated


def command_results_cover_practical_stages(value: object) -> bool:
    if not isinstance(value, list):
        return False
    stages = {
        str(row.get("stage") or "").strip().lower().replace("-", "_").replace(" ", "_")
        for row in value
        if isinstance(row, dict)
    }
    return all(stage in stages for stage in REQUIRED_COMMAND_RESULT_STAGES)


def staged_command_results(materialization_root: Path) -> list[dict]:
    for path in (
        materialization_root / "checks" / "terminal_metrics.json",
        materialization_root / "summaries" / "terminal_summary.json",
    ):
        payload = read_json(path)
        rows = payload.get("command_results")
        if command_results_cover_practical_stages(rows):
            return rows
    return []


def terminal_metrics(root: Path) -> dict:
    return read_json(root / "checks" / "terminal_metrics.json")


def child_rescore_metrics(materialization_root: Path) -> tuple[dict, str | None]:
    material = terminal_metrics(materialization_root)
    child_root = material.get("child_rescore_root")
    if not isinstance(child_root, str) or not child_root.strip():
        return ({}, None)
    child_path = Path(child_root) / "checks" / "terminal_metrics.json"
    return (read_json(child_path), str(child_path))


def market_data_provenance(materialization_root: Path) -> dict:
    payload = terminal_metrics(materialization_root)
    provenance = payload.get("market_data_provenance")
    if isinstance(provenance, dict) and provenance:
        out = dict(provenance)
        source_payload = str(materialization_root / "checks" / "terminal_metrics.json")
    else:
        child_payload, child_payload_path = child_rescore_metrics(materialization_root)
        child_provenance = child_payload.get("market_data_provenance")
        if isinstance(child_provenance, dict) and child_provenance:
            out = dict(child_provenance)
            source_payload = child_payload_path
        else:
            out = {
                "status": "missing_explicit_market_data_provenance",
                "source_class": None,
                "return_sanity": {"status": "missing_explicit_return_sanity"},
            }
            source_payload = None
    out.setdefault("materialization_root", str(materialization_root))
    if source_payload:
        out.setdefault("source_payload", source_payload)
    out.setdefault("status", "missing_explicit_market_data_provenance")
    out.setdefault("source_class", None)
    out.setdefault("return_sanity", {"status": "missing_explicit_return_sanity"})
    return out


def first_present(*values: object) -> object:
    for value in values:
        if value is not None:
            return value
    return None


def first_non_missing_status(default: dict, *values: object) -> object:
    for value in values:
        if not isinstance(value, dict):
            if value is not None:
                return value
            continue
        status = normalized_text(value.get("status"))
        if status and not status.startswith("missing_"):
            return value
    return default


def practical_evidence_fields(materialization_root: Path | None, source_packet: dict | None = None) -> dict:
    packet = source_packet if isinstance(source_packet, dict) else {}
    if materialization_root is None:
        return {
            "session_scope": packet.get("session_scope"),
            "rth_filter_applied": packet.get("rth_filter_applied"),
            "retained_session_coverage": first_non_missing_status(
                {"status": "missing_explicit_retained_session_coverage"},
                packet.get("retained_session_coverage"),
            ),
            "promotion_cost_verified": packet.get("promotion_cost_verified") is True,
            "cost_model": first_non_missing_status(
                {"status": "missing_explicit_verified_cost_model"},
                packet.get("cost_model"),
            ),
        }
    material = terminal_metrics(materialization_root)
    child, _child_path = child_rescore_metrics(materialization_root)
    return {
        "session_scope": first_present(material.get("session_scope"), child.get("session_scope"), packet.get("session_scope")),
        "rth_filter_applied": first_present(
            material.get("rth_filter_applied"),
            child.get("rth_filter_applied"),
            packet.get("rth_filter_applied"),
        ),
        "retained_session_coverage": first_non_missing_status(
            {"status": "missing_explicit_retained_session_coverage"},
            material.get("retained_session_coverage"),
            child.get("retained_session_coverage"),
            packet.get("retained_session_coverage"),
        ),
        "promotion_cost_verified": any(
            value is True
            for value in (
                material.get("promotion_cost_verified"),
                child.get("promotion_cost_verified"),
                packet.get("promotion_cost_verified"),
            )
        ),
        "cost_model": first_non_missing_status(
            {"status": "missing_explicit_verified_cost_model"},
            material.get("cost_model"),
            child.get("cost_model"),
            packet.get("cost_model"),
        ),
    }


def validated_extension_complete(source_packet: dict | None) -> bool:
    if not isinstance(source_packet, dict):
        return False
    if source_packet.get("validated_extension_complete") is not True:
        return False
    evidence = source_packet.get("validated_extension_evidence") or source_packet.get(
        "validated_extension_evidence_packet"
    )
    return isinstance(evidence, (str, dict, list)) and bool(evidence)


def normalized_text(value: object) -> str:
    return str(value or "").strip().lower()


def positive_int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return 0


def lifecycle_surface(policy: dict) -> dict:
    lifecycle = policy.get("factor_profitability_lifecycle")
    return lifecycle if isinstance(lifecycle, dict) else {}


def deploy_ready_from_policy(policy: dict) -> bool:
    lifecycle = lifecycle_surface(policy)
    return bool(
        policy.get("deploy_ready") is True
        or lifecycle.get("deploy_ready") is True
        or positive_int(policy.get("deploy_ready_count")) > 0
        or positive_int(lifecycle.get("deploy_ready_count")) > 0
    )


def funded_live_fill_required_from_policy(policy: dict) -> object:
    lifecycle = lifecycle_surface(policy)
    if "funded_live_fill_required" in lifecycle:
        return lifecycle.get("funded_live_fill_required")
    return policy.get("funded_live_fill_required")


def readiness_contract_from_policy(policy: dict) -> object:
    lifecycle = lifecycle_surface(policy)
    return lifecycle.get("readiness_contract") or policy.get("readiness_contract")


def trainer_cmd(*extra: object) -> list[object]:
    return [PY_RUNNER, TRAINER, *extra]


def command_step(stage: str, name: str, argv: list[object], timeout: int) -> dict[str, object]:
    return {"stage": stage, "name": name, "argv": [str(item) for item in argv], "timeout": timeout}


def resolve_data_root(value: str) -> Path:
    return Path(value) if value else DATA_DIR


def cleaned_interval_file_count(data_root: Path) -> int:
    market = SYMBOL.lower()
    return sum(
        1
        for timeframe in ROW_CAPS
        if (data_root / f"cleaned-{timeframe}" / f"{market}.continuous-{timeframe}.json").exists()
    )


def path_is_under_run_root(path: Path) -> bool:
    try:
        return path.resolve().is_relative_to(ROOT.resolve())
    except OSError:
        return False


def should_prepare_local_data(data_root: Path, *, data_root_explicit: bool) -> bool:
    if not data_root_explicit:
        return True
    if cleaned_interval_file_count(data_root) >= 3:
        return False
    return path_is_under_run_root(data_root)


def _float_value(value: object, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return default
    return default


def prepare_runtime_strategy_library(source_library: Path) -> Path:
    payload = read_json(source_library)
    source_strategies = payload.get("strategies") if isinstance(payload.get("strategies"), list) else []
    strategies: list[dict[str, object]] = []
    for raw in source_strategies:
        if not isinstance(raw, dict):
            continue
        metadata = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
        trade_count = positive_int(
            first_present(
                metadata.get("child_full_trade_count"),
                metadata.get("trade_count"),
                metadata.get("trades"),
            )
        )
        total_profit_pct = _float_value(
            first_present(
                metadata.get("child_full_instrument_cost_total_ret_pct"),
                metadata.get("child_full_net5bps_total_ret_pct"),
                metadata.get("instrument_cost_total_profit_pct"),
                metadata.get("total_profit_pct"),
            )
        )
        strategy_name = str(raw.get("name") or metadata.get("factor_id") or FACTOR_ID)
        runtime_metadata = dict(metadata)
        runtime_metadata.update(
            {
                "strategy": strategy_name,
                "mutation_id": FACTOR_ID,
                "base_factor": PARENT_FACTOR_ID,
                "hypothesis": "rv-stress child gate continuation of NQ compound trend RRR chop filter",
                "paradigm": "regime_rooted_tomac_nq_practical_lifecycle",
                "expected_regime": "HtfTrendRegime -> ChopFilter -> MomentumResonance",
                "main_regime": "HtfTrendRegime",
                "sub_regime": "ChopFilterMomentumResonance",
                "sub_sub_regime_or_profit_factor": "realized_volatility_stress_gate",
                "profit_factor": FACTOR_ID,
                "regime_profit_branch_path": BRANCH_PATH,
                "parent": PARENT_FACTOR_ID,
                "asset_class": "futures",
                "status": "active",
                "promotion_allowed": False,
                "trade_usable": False,
            }
        )
        strategies.append(
            {
                "name": strategy_name,
                "status": "ok",
                "error": None,
                "file_path": str(source_library),
                "pairs": ["NQ"],
                "timerange": "20210103-20251231",
                "validation_metrics": {
                    "trade_count": trade_count,
                    "win_rate_pct": _float_value(metadata.get("child_full_win_rate_pct"), 50.0),
                    "total_profit_pct": total_profit_pct,
                    "profit_factor": _float_value(metadata.get("child_full_profit_factor"), 1.0),
                    "sharpe": _float_value(metadata.get("child_full_sharpe"), 0.0),
                    "sortino": _float_value(metadata.get("child_full_sortino"), 0.0),
                    "calmar": _float_value(metadata.get("child_full_calmar"), 0.0),
                    "max_drawdown_pct": _float_value(metadata.get("child_full_max_drawdown_pct"), 0.0),
                },
                "per_pair_metrics": {
                    "NQ_USD_1m_ETH_FULL_RETAINED": {
                        "trade_count": trade_count,
                        "win_rate_pct": _float_value(metadata.get("child_full_win_rate_pct"), 50.0),
                        "total_profit_pct": total_profit_pct,
                        "profit_factor": _float_value(metadata.get("child_full_profit_factor"), 1.0),
                        "sharpe": _float_value(metadata.get("child_full_sharpe"), 0.0),
                        "sortino": _float_value(metadata.get("child_full_sortino"), 0.0),
                        "calmar": _float_value(metadata.get("child_full_calmar"), 0.0),
                        "max_drawdown_pct": _float_value(metadata.get("child_full_max_drawdown_pct"), 0.0),
                    }
                },
                "metadata": runtime_metadata,
            }
        )
    runtime_library = {
        "manifest_version": "1.0",
        "auto_quant_repo_url": "tomac_nq_compound_rv_stress_gate_practical_lifecycle_v1",
        "auto_quant_pinned_ref": "local_materialization_runtime_adapter",
        "timeframe": str(payload.get("timeframe") or "1m"),
        "strategies": strategies,
        "validation_errors": [],
    }
    MATERIALS.mkdir(parents=True, exist_ok=True)
    out = MATERIALS / "tomac_nq_compound_rv_stress_runtime_strategy_library.json"
    write_json(out, runtime_library)
    return out


def parse_utc_datetime(value: object) -> datetime:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        seconds = float(value) / 1000.0 if abs(float(value)) > 10_000_000_000 else float(value)
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    text = str(value or "").strip()
    if not text:
        return datetime.now(timezone.utc)
    text = text.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def timestamp_ms(value: object) -> int:
    return int(parse_utc_datetime(value).timestamp() * 1000)


def direction_label(value: object) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value > 0:
            return "Bull"
        if value < 0:
            return "Bear"
        return "Neutral"
    text = str(value or "").strip().lower()
    if text in {"1", "+1", "bull", "bullish", "long", "buy"}:
        return "Bull"
    if text in {"-1", "bear", "bearish", "short", "sell"}:
        return "Bear"
    return "Neutral"


def realized_outcome_from_pnl(pnl: float) -> str:
    if pnl > 0.0:
        return "win"
    if pnl < 0.0:
        return "loss"
    return "breakeven"


def selected_probability_from_pnl(pnl: float) -> float:
    return min(0.95, max(0.05, 0.5 + pnl * 8.0))


def runtime_trade_record(row: dict[str, object], index: int) -> dict[str, object]:
    open_value = row.get("open_ts") or row.get("event_ts")
    open_dt = parse_utc_datetime(open_value)
    bars_held = positive_int(row.get("bars_held")) or 1
    close_dt = parse_utc_datetime(row.get("close_ts")) if row.get("close_ts") else open_dt + timedelta(minutes=bars_held)
    pnl = _float_value(
        first_present(
            row.get("instrument_cost_return"),
            row.get("realized_pnl"),
            row.get("net5bps_return"),
            row.get("gross_return"),
        )
    )
    direction = direction_label(row.get("direction"))
    selected_probability = selected_probability_from_pnl(pnl)
    if direction == "Bear":
        long_score = 1.0 - selected_probability
        short_score = selected_probability
    elif direction == "Bull":
        long_score = selected_probability
        short_score = 1.0 - selected_probability
    else:
        long_score = short_score = 0.5
    stream_label = str(row.get("stream_label") or FACTOR_ID)
    child_gate = str(row.get("child_gate") or "30m_abs_ret16_max")
    open_ms = int(open_dt.timestamp() * 1000)
    close_ms = int(close_dt.timestamp() * 1000)
    trade_id = f"rv-stress-{index:04d}-{open_ms}"
    original_branch = str(row.get("regime_profit_branch_path") or row.get("branch_path") or "")
    return {
        "schema_version": "1.0",
        "symbol": SYMBOL,
        "trade_id": trade_id,
        "strategy_name": stream_label,
        "strategy_mutation_id": FACTOR_ID,
        "auto_quant_run_id": "simulated_backtest_from_rv_stress_materialization",
        "open_ts_ms": open_ms,
        "close_ts_ms": close_ms,
        "direction": direction,
        "pnl": pnl,
        "realized_outcome": realized_outcome_from_pnl(pnl),
        "regime_at_entry": "trend",
        "entry_signal": "medium",
        "factors_used": [
            {
                "factor_name": stream_label,
                "category": "strategy_stream",
                "direction": direction,
                "value": 1.0,
                "confidence": 0.65,
                "weighted_score": 0.65,
                "uncertainty_contribution": 0.20,
            },
            {
                "factor_name": child_gate,
                "category": "realized_volatility_stress_gate",
                "direction": direction,
                "value": _float_value(row.get("child_threshold")),
                "confidence": 0.72,
                "weighted_score": 0.72,
                "uncertainty_contribution": 0.15,
            },
        ],
        "model_probabilities_before_trade": {
            "selected_direction": direction,
            "selected_probability": selected_probability,
            "long_score": long_score,
            "short_score": short_score,
            "win_prob_long": long_score,
            "win_prob_short": short_score,
            "uncertainty": max(0.0, 1.0 - abs(selected_probability - 0.5) * 2.0),
        },
        "structural_feedback": {
            "protocol_version": "structural-feedback-v1",
            "recommendation_id": f"structural-feedback:{SYMBOL}:rv-stress:{index:04d}:{open_ms}",
            "recommended_at": open_dt.isoformat().replace("+00:00", "Z"),
            "node_id": "US index futures",
            "branch_id": "US index futures -> NQ",
            "scenario_id": "US index futures -> NQ -> ETH/full_retained_session",
            "path_id": BRANCH_PATH,
            "followed_path": True,
            "exit_reason": str(row.get("exit_reason") or realized_outcome_from_pnl(pnl)),
            "notes": f"simulated backtest feedback from retained ETH materialization; not broker fill evidence; original_branch={original_branch}",
        },
        "regime_profit_branch_path": BRANCH_PATH,
        "main_regime": "US index futures",
        "sub_regime": "NQ",
        "sub_sub_regime_or_profit_factor": "ETH/full_retained_session",
        "profit_factor": FACTOR_ID,
    }


def prepare_runtime_trade_feedback(source_feedback: Path) -> tuple[Path, dict[str, object]]:
    if not source_feedback.exists():
        raise RuntimeError(f"missing materialized feedback JSONL: {source_feedback}")
    out_dir = ROOT / "feedback"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "tomac_nq_compound_rv_stress_runtime_real_trades.jsonl"
    rows = wins = losses = breakevens = 0
    with source_feedback.open(encoding="utf-8") as source, out.open("w", encoding="utf-8") as handle:
        for raw_line in source:
            line = raw_line.strip()
            if not line:
                continue
            raw_payload = json.loads(line)
            if not isinstance(raw_payload, dict):
                continue
            record = runtime_trade_record(raw_payload, rows)
            handle.write(json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n")
            rows += 1
            outcome = record["realized_outcome"]
            wins += int(outcome == "win")
            losses += int(outcome == "loss")
            breakevens += int(outcome == "breakeven")
    summary = {
        "source_feedback": str(source_feedback),
        "runtime_feedback": str(out),
        "target_schema": "auto_quant_real_trades_jsonl/v1",
        "source": TRADE_FEEDBACK_SOURCE,
        "rows": rows,
        "wins": wins,
        "losses": losses,
        "breakevens": breakevens,
        "broker_realized": False,
        "broker_fill_evidence": False,
        "session_scope": "ETH/full_retained_session",
        "rth_filter_applied": False,
    }
    write_json(CHECKS / "runtime_trade_feedback_summary.json", summary)
    return out, summary


def accepted_execution_feedback_source(value: object) -> str | None:
    text = str(value or "").strip()
    normalized = text.lower()
    if not normalized or any(marker in normalized for marker in SIMULATED_FEEDBACK_MARKERS):
        return None
    if any(marker in normalized for marker in ACCEPTED_FEEDBACK_MARKERS):
        return text
    return None


def inspect_runtime_trade_feedback(source_feedback: Path) -> dict[str, object]:
    if not source_feedback.exists():
        raise RuntimeError(f"missing feedback JSONL: {source_feedback}")
    rows = wins = losses = breakevens = 0
    broker_realized = False
    broker_fill_evidence = False
    accepted_source: str | None = None
    with source_feedback.open(encoding="utf-8") as source:
        for raw_line in source:
            line = raw_line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                continue
            rows += 1
            accepted_source = accepted_source or accepted_execution_feedback_source(payload.get("source"))
            accepted_source = accepted_source or accepted_execution_feedback_source(payload.get("feedback_source"))
            broker_realized = broker_realized or payload.get("broker_realized") is True
            broker_fill_evidence = broker_fill_evidence or payload.get("broker_fill_evidence") is True
            outcome = str(payload.get("realized_outcome") or "").strip().lower()
            if not outcome:
                outcome = realized_outcome_from_pnl(_float_value(payload.get("pnl")))
            wins += int(outcome == "win")
            losses += int(outcome == "loss")
            breakevens += int(outcome == "breakeven")
    return {
        "source_feedback": str(source_feedback),
        "runtime_feedback": str(source_feedback),
        "target_schema": "auto_quant_real_trades_jsonl/v1",
        "source": accepted_source,
        "rows": rows,
        "wins": wins,
        "losses": losses,
        "breakevens": breakevens,
        "broker_realized": broker_realized,
        "broker_fill_evidence": broker_fill_evidence,
        "session_scope": "ETH/full_retained_session",
        "rth_filter_applied": False,
    }


def prepare_real_trade_feedback(source_feedback: Path) -> Path:
    summary = inspect_runtime_trade_feedback(source_feedback)
    if summary.get("source") and summary.get("broker_realized") is True and summary.get("broker_fill_evidence") is True:
        write_json(CHECKS / "runtime_trade_feedback_summary.json", summary)
        return source_feedback
    runtime_feedback, _summary = prepare_runtime_trade_feedback(source_feedback)
    return runtime_feedback


def runtime_trade_feedback_source() -> str:
    summary = read_json(CHECKS / "runtime_trade_feedback_summary.json")
    source = accepted_execution_feedback_source(summary.get("source"))
    if source:
        return source
    return TRADE_FEEDBACK_SOURCE


def build_lifecycle_command_plan(
    *,
    strategy_library: Path,
    data_root: Path,
    feedback_file: Path,
) -> list[dict[str, object]]:
    target_csv = STATE / SYMBOL / "policy_training/structural_path_ranking_target.csv"
    trainer_artifact = MODEL_DIR / "trainer_artifact.json"
    return [
        command_step(
            "provider_data",
            "01_auto_quant_results_import",
            [
                ICT,
                "auto-quant-results-import",
                "--symbol",
                SYMBOL,
                "--state-dir",
                STATE,
                "--library",
                strategy_library,
            ],
            180,
        ),
        command_step(
            "pre_bayes",
            "02_auto_quant_prior_init",
            [
                ICT,
                "auto-quant-prior-init",
                "--symbol",
                SYMBOL,
                "--state-dir",
                STATE,
                "--library",
                strategy_library,
                "--temper",
                "0.5",
                "--prior-strength",
                "4.0",
            ],
            180,
        ),
        command_step(
            "execution_tree",
            "03_analyze_seed",
            [ICT, "analyze", "--symbol", SYMBOL, "--data-root", data_root, "--state-dir", STATE, "--output-format", "json"],
            300,
        ),
        command_step(
            "bbn_workflow",
            "04_workflow_seed",
            [ICT, "workflow-status", "--symbol", SYMBOL, "--state-dir", STATE, "--refresh", "--output-format", "json"],
            120,
        ),
        command_step(
            "pre_bayes",
            "05_pre_bayes_seed",
            [ICT, "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", STATE, "--refresh", "--output-format", "json"],
            120,
        ),
        command_step(
            "path_ranker",
            "06_export_target_seed",
            [ICT, "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", STATE],
            120,
        ),
        command_step(
            "feedback_update",
            "08_feedback_update",
            [
                ICT,
                "auto-quant-ingest-real-trades",
                "--symbol",
                SYMBOL,
                "--state-dir",
                STATE,
                "--trades",
                feedback_file,
                "--source",
                runtime_trade_feedback_source(),
            ],
            300,
        ),
        command_step(
            "path_ranker",
            "09_export_target_after_feedback",
            [ICT, "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", STATE],
            120,
        ),
        command_step(
            "policy_training",
            "10_policy_after_feedback",
            [ICT, "policy-training-status", "--symbol", SYMBOL, "--state-dir", STATE, "--output-format", "json"],
            120,
        ),
        command_step(
            "path_ranker",
            "11_train_ranker",
            trainer_cmd("--target-csv", target_csv, "--output-dir", MODEL_DIR, "--output-scores", SCORES, "--allow-direct-fallback"),
            300,
        ),
        command_step(
            "path_ranker",
            "12_apply_ranker",
            trainer_cmd("--apply", "--model-dir", MODEL_DIR, "--target-csv", target_csv, "--output-scores", SCORES, "--allow-direct-fallback"),
            180,
        ),
        command_step(
            "path_ranker",
            "13_apply_scores_to_ict",
            [ICT, "apply-structural-path-ranking-external-scores", "--symbol", SYMBOL, "--state-dir", STATE, "--scores-file", SCORES],
            120,
        ),
        command_step(
            "path_ranker",
            "14_register_trainer",
            [
                ICT,
                "register-structural-path-ranking-trainer-artifact",
                "--symbol",
                SYMBOL,
                "--state-dir",
                STATE,
                "--artifact-uri",
                trainer_artifact,
                "--model-family",
                "catboost",
                "--trained-rows",
                "1",
                "--calibration-rows",
                "0",
            ],
            120,
        ),
        command_step(
            "path_ranker",
            "15_enable_runtime",
            [ICT, "enable-structural-path-ranking-runtime", "--symbol", SYMBOL, "--state-dir", STATE, "--reuse-mode", "prefer_history"],
            120,
        ),
        command_step(
            "execution_tree",
            "16_analyze_after_ranker",
            [ICT, "analyze", "--symbol", SYMBOL, "--data-root", data_root, "--state-dir", STATE, "--output-format", "json"],
            300,
        ),
        command_step(
            "bbn_workflow",
            "17_workflow_after_ranker",
            [ICT, "workflow-status", "--symbol", SYMBOL, "--state-dir", STATE, "--refresh", "--output-format", "json"],
            120,
        ),
        command_step(
            "pre_bayes",
            "18_pre_bayes_after_ranker",
            [ICT, "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", STATE, "--refresh", "--output-format", "json"],
            120,
        ),
        command_step(
            "policy_training",
            "19_policy_after_ranker",
            [ICT, "policy-training-status", "--symbol", SYMBOL, "--state-dir", STATE, "--output-format", "json"],
            120,
        ),
    ]


def run_lifecycle_driver(plan: list[dict[str, object]]) -> list[dict]:
    results: list[dict] = []
    for step in plan:
        argv = list(step["argv"])
        if str(step["name"]) == "14_register_trainer":
            argv = register_trainer_argv_from_artifact(argv)
        result = run_stage(
            str(step["stage"]),
            str(step["name"]),
            argv,
            int(step.get("timeout") or 300),
        )
        results.append(result)
        if result.get("exit") != 0 or result.get("timed_out") is True:
            break
    return results


def validation_counters(trace_output: dict) -> dict[str, str]:
    counters: dict[str, str] = {}
    for line in trace_output.get("split_reason_lineage") or []:
        for key in ("raw_scored_mature", "production_validation", "observation_validation"):
            marker = f"{key}="
            if marker in line:
                counters[key] = line.split(marker, 1)[1].split()[0].strip()
    return counters


def ratio_covers(value: str | None) -> bool:
    if not value or "/" not in value:
        return False
    left, right = value.split("/", 1)
    try:
        actual = int(left)
        required = int(right)
    except ValueError:
        return False
    return required > 0 and actual >= required


def exact_branch_survived(candidate: dict, trace_output: dict, closed_loop: dict) -> bool:
    values = [
        candidate.get("path_id"),
        candidate.get("path_label"),
        candidate.get("branch_path"),
        trace_output.get("path_id"),
        trace_output.get("path_label"),
        trace_output.get("branch_path"),
        closed_loop.get("path_id"),
        closed_loop.get("path_label"),
        closed_loop.get("branch_path"),
    ]
    return BRANCH_PATH in values


def branch_local_admitted(closed_loop: dict) -> bool:
    status = normalized_text(closed_loop.get("status") or closed_loop.get("admission_status"))
    return bool(closed_loop.get("ready") is True and closed_loop.get("actionable") is True) or status in {
        "admitted",
        "ready",
        "execution_ready",
    }


def materialization_summary(materialization_root: Path) -> dict:
    return read_json(materialization_root / "checks" / "terminal_metrics.json")


def write_summary(
    command_results: list[dict],
    data_summary: dict,
    materialization_root: Path | None = None,
    source_packet: dict | None = None,
    source_packet_path: Path | None = None,
) -> dict:
    workflow = read_json(STATE / SYMBOL / "workflow_snapshot.json")
    candidate = read_json(STATE / SYMBOL / "execution_candidate.json")
    trace = read_json(STATE / SYMBOL / "execution_tree_trace.json")
    trace_output = trace.get("output") if isinstance(trace.get("output"), dict) else trace
    policy = read_policy_training_summary()
    closed_loop = workflow.get("closed_loop_branch_admission") or trace.get("closed_loop_branch_admission") or {}
    counters = validation_counters(trace_output)
    actionable = bool(candidate.get("actionable") or trace_output.get("actionable") or closed_loop.get("actionable"))
    candidate_status = str(closed_loop.get("candidate_status") or trace_output.get("candidate_status") or candidate.get("candidate_status") or "")
    exact_survived = exact_branch_survived(candidate, trace_output, closed_loop)
    pass_exec = branch_local_admitted(closed_loop) and exact_survived
    all_ok = bool(command_results) and all(
        row.get("exit") == 0 and row.get("timed_out") is False for row in command_results
    )
    material = materialization_summary(materialization_root) if materialization_root else {}
    evidence_fields = practical_evidence_fields(materialization_root, source_packet)
    source_extension_complete = validated_extension_complete(source_packet)
    runtime_feedback_summary = read_json(CHECKS / "runtime_trade_feedback_summary.json")
    feedback_source = first_present(runtime_feedback_summary.get("source"), runtime_feedback_summary.get("feedback_source"))
    metrics = {
        "schema_version": "tomac-nq-compound-rv-stress-practical-lifecycle-terminal/v1",
        "status": "practical_lifecycle_evaluating",
        "run_root": str(ROOT),
        "symbol": SYMBOL,
        "factor_id": FACTOR_ID,
        "parent_factor_id": PARENT_FACTOR_ID,
        "branch_path": BRANCH_PATH,
        "materialization_root": str(materialization_root) if materialization_root else None,
        "source_cost_coverage_packet": str(source_packet_path) if source_packet_path else None,
        "materialization_status": material.get("status"),
        "feedback_rows": material.get("feedback_rows"),
        "feedback_source": feedback_source,
        "runtime_trade_feedback_summary": runtime_feedback_summary,
        "best_gate": material.get("best_gate"),
        "best_threshold": material.get("best_threshold"),
        "command_results": command_results,
        "all_command_exits_zero": all_ok,
        "exact_branch_survived": exact_survived,
        "execution_candidate_actionable": actionable,
        "execution_candidate_status": candidate_status,
        "branch_local_admitted": pass_exec,
        "validation_ready": all(ratio_covers(counters.get(key)) for key in ("raw_scored_mature", "production_validation", "observation_validation")),
        "validation_counters": counters,
        "path_ranker_score_visible_to_execution_tree": trace_output.get("path_ranker_score_visible_to_execution_tree"),
        "path_ranker_score_used_by_execution_tree": trace_output.get("path_ranker_score_used_by_execution_tree"),
        "path_ranker_used": trace_output.get("path_ranker_score_used_by_execution_tree") is True,
        "policy_training_summary": policy,
        "learning_admission_status": policy.get("learning_admission_status"),
        "paper_admission_status": policy.get("paper_admission_status"),
        "deploy_ready": deploy_ready_from_policy(policy),
        "live_trade_status": policy.get("live_trade_status"),
        "funded_live_fill_required": funded_live_fill_required_from_policy(policy),
        "readiness_contract": readiness_contract_from_policy(policy),
        "market_data_provenance": data_summary,
        "session_scope": evidence_fields["session_scope"],
        "rth_filter_applied": evidence_fields["rth_filter_applied"],
        "retained_session_coverage": evidence_fields["retained_session_coverage"],
        "promotion_cost_verified": evidence_fields["promotion_cost_verified"],
        "cost_model": evidence_fields["cost_model"],
        "validated_extension_complete": source_extension_complete,
        "extension_complete": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    packet = write_same_tree_practical_closure_packet(
        metrics,
        SUMMARIES / "same_tree_practical_closure.json",
        evidence_packet="checks/terminal_metrics.json",
    )
    # Practical authority lives in the canonical same-tree packet. Wrapper
    # terminal metrics stay fail-closed to avoid self-promotion through local
    # lifecycle readbacks.
    closure_pass = packet is not None
    metrics["status"] = "practical_closure_pass" if closure_pass else "practical_lifecycle_fail_closed"
    metrics["same_tree_practical_closure"] = str(SUMMARIES / "same_tree_practical_closure.json") if closure_pass else None
    write_json(CHECKS / "terminal_metrics.json", metrics)
    summary = {
        "status": metrics["status"],
        "factor_id": FACTOR_ID,
        "branch_path": BRANCH_PATH,
        "all_command_exits_zero": all_ok,
        "exact_branch_survived": exact_survived,
        "execution_candidate_actionable": actionable,
        "execution_candidate_status": candidate_status,
        "branch_local_admitted": metrics["branch_local_admitted"],
        "validation_ready": metrics["validation_ready"],
        "path_ranker_score_used_by_execution_tree": metrics["path_ranker_score_used_by_execution_tree"],
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "same_tree_practical_closure": str(SUMMARIES / "same_tree_practical_closure.json") if packet else None,
    }
    write_json(SUMMARIES / "terminal_summary.json", summary)
    return metrics


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize same-tree practical lifecycle evidence for the NQ compound RV-stress child gate."
    )
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--materialization-root", default=str(DEFAULT_MATERIALIZATION_ROOT))
    parser.add_argument("--execute-driver", action="store_true")
    parser.add_argument(
        "--strategy-library",
        default=str(DEFAULT_MATERIALIZATION_ROOT / "materials/tomac_nq_compound_rv_stress_gate_strategy_library.json"),
    )
    parser.add_argument("--data-root", default="")
    parser.add_argument(
        "--feedback-file",
        default=str(DEFAULT_MATERIALIZATION_ROOT / "feedback/tomac_nq_compound_rv_stress_gate_simulated_feedback.jsonl"),
    )
    parser.add_argument(
        "--source-packet",
        default="",
        help="Optional JSON packet with retained-session coverage and verified NQ futures cost-model readbacks.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root)
    materialization_root = Path(args.materialization_root)
    source_packet_path = Path(args.source_packet) if args.source_packet else None
    source_packet = read_json(source_packet_path) if source_packet_path else None
    configure_paths(root)
    for directory in (STATE, CMD, CHECKS, SUMMARIES, MATERIALS, MODEL_DIR, DATA_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    if args.execute_driver:
        data_root = resolve_data_root(args.data_root)
        if should_prepare_local_data(data_root, data_root_explicit=bool(args.data_root)):
            prepare_local_data(data_root)
        reset_prior_init_state()
        runtime_strategy_library = prepare_runtime_strategy_library(Path(args.strategy_library))
        runtime_feedback_file = prepare_real_trade_feedback(Path(args.feedback_file))
        plan = build_lifecycle_command_plan(
            strategy_library=runtime_strategy_library,
            data_root=data_root,
            feedback_file=runtime_feedback_file,
        )
        write_json(CHECKS / "lifecycle_command_plan.json", {"steps": plan})
        command_results = run_lifecycle_driver(plan)
    else:
        command_results = staged_command_results(materialization_root)
    metrics = write_summary(
        command_results,
        market_data_provenance(materialization_root),
        materialization_root,
        source_packet,
        source_packet_path,
    )
    print(json.dumps({"status": metrics["status"], "feedback_rows": metrics.get("feedback_rows")}, sort_keys=True))
    return 0 if (SUMMARIES / "same_tree_practical_closure.json").exists() else 2


if __name__ == "__main__":
    raise SystemExit(main())
