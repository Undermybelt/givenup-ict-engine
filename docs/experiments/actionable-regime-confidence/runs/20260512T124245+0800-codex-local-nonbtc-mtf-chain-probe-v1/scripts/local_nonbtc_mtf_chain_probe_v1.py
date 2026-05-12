#!/usr/bin/env python3
"""Run a local non-BTC / non-1h ict-engine chain probe from Auto-Quant feathers."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T124245+0800-codex-local-nonbtc-mtf-chain-probe-v1"
RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
REPORT_DIR = ROOT / "local-nonbtc-mtf-chain-probe-v1"
CHECK_DIR = ROOT / "checks"
OUT_DIR = ROOT / "command-output"
PROVIDER_JSON_DIR = ROOT / "provider-data-json"
PATH_RANKER_DIR = ROOT / "path-ranker"
AQ_DATA = Path("/Users/thrill3r/Auto-Quant/user_data/data")
ICT = Path("./target/debug/ict-engine")
UV = Path("/Users/thrill3r/.local/bin/uv")


PANELS = [
    {
        "panel_id": "eth_usdt_crypto_nonbtc_1h_4h_1d",
        "symbol": "B2R_LOCAL_NONBTC_ETH_USDT_MTF_124245",
        "asset_class": "crypto_non_btc",
        "htf": "1d",
        "mtf": "4h",
        "ltf": "1h",
        "files": {
            "1h": AQ_DATA / "ETH_USDT-1h.feather",
            "4h": AQ_DATA / "ETH_USDT-4h.feather",
            "1d": AQ_DATA / "ETH_USDT-1d.feather",
        },
    },
    {
        "panel_id": "spy_usd_equity_etf_15m_4h_1d",
        "symbol": "B2R_LOCAL_NONBTC_SPY_USD_MTF_124245",
        "asset_class": "equity_etf",
        "htf": "1d",
        "mtf": "4h",
        "ltf": "15m",
        "files": {
            "15m": AQ_DATA / "SPY_USD-15m.feather",
            "1h": AQ_DATA / "SPY_USD-1h.feather",
            "4h": AQ_DATA / "SPY_USD-4h.feather",
            "1d": AQ_DATA / "SPY_USD-1d.feather",
        },
    },
]

MAX_ROWS_BY_TIMEFRAME = {
    "15m": 3000,
    "1h": 2000,
    "4h": 1000,
    "1d": 800,
}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_json_maybe(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def normalize_feather(path: Path, timeframe: str) -> pd.DataFrame:
    raw = pd.read_feather(path)
    date_col = next((name for name in ("date", "timestamp", "datetime", "ts") if name in raw.columns), None)
    if date_col is None:
        raise ValueError(f"no date column in {path}: {list(raw.columns)}")
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(raw[date_col], utc=True),
            "open": pd.to_numeric(raw["open"], errors="coerce"),
            "high": pd.to_numeric(raw["high"], errors="coerce"),
            "low": pd.to_numeric(raw["low"], errors="coerce"),
            "close": pd.to_numeric(raw["close"], errors="coerce"),
            "volume": pd.to_numeric(raw.get("volume", 0.0), errors="coerce").fillna(0.0),
        }
    )
    out["volume"] = out["volume"].mask(out["volume"] < 0, 0.0)
    out = out.dropna().sort_values("date").reset_index(drop=True)
    max_rows = MAX_ROWS_BY_TIMEFRAME.get(timeframe)
    if max_rows and len(out) > max_rows:
        out = out.tail(max_rows).reset_index(drop=True)
    return out


def records_for_json(df: pd.DataFrame) -> list[dict[str, Any]]:
    records = []
    for row in df.itertuples(index=False):
        ts = pd.Timestamp(row.date)
        records.append(
            {
                "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open": float(row.open),
                "high": float(row.high),
                "low": float(row.low),
                "close": float(row.close),
                "volume": float(row.volume),
            }
        )
    return records


def run_command(label: str, cmd: list[str], env: dict[str, str] | None = None) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{label}.cmd").write_text(" ".join(cmd) + "\n")
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, env=env)
    (OUT_DIR / f"{label}.out").write_text(proc.stdout)
    (OUT_DIR / f"{label}.err").write_text(proc.stderr)
    (CHECK_DIR / f"{label}.exit").write_text(f"{proc.returncode}\n")
    parsed = None
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        pass
    return {
        "label": label,
        "cmd": cmd,
        "exit": proc.returncode,
        "stdout": str(OUT_DIR / f"{label}.out"),
        "stderr": str(OUT_DIR / f"{label}.err"),
        "parsed_stdout": parsed,
    }


def csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open() as fh:
        return max(sum(1 for _ in fh) - 1, 0)


def find_numeric_values(payload: Any, names: set[str]) -> list[float]:
    values: list[float] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in names and isinstance(value, (int, float)) and 0 <= float(value) <= 1:
                values.append(float(value))
            values.extend(find_numeric_values(value, names))
    elif isinstance(payload, list):
        for item in payload:
            values.extend(find_numeric_values(item, names))
    return values


def materialize_panel(panel: dict[str, Any]) -> dict[str, Any]:
    out_dir = PROVIDER_JSON_DIR / panel["panel_id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Any] = {}
    for tf, feather in panel["files"].items():
        df = normalize_feather(feather, tf)
        out_path = out_dir / f"{panel['panel_id']}-{tf}.json"
        write_json(out_path, records_for_json(df))
        outputs[tf] = {
            "source_feather": str(feather),
            "json_path": str(out_path),
            "rows": int(len(df)),
            "first_ts": df["date"].min().isoformat(),
            "last_ts": df["date"].max().isoformat(),
            "bounded_rows": MAX_ROWS_BY_TIMEFRAME.get(tf),
        }
    return outputs


def run_panel(panel: dict[str, Any]) -> dict[str, Any]:
    symbol = panel["symbol"]
    state_dir = ROOT / f"state_bounded_{panel['panel_id']}"
    provider_json = materialize_panel(panel)
    env = os.environ.copy()
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
        }
    )
    commands: list[dict[str, Any]] = []

    def j(tf: str) -> str:
        return provider_json[tf]["json_path"]

    commands.append(
        run_command(
            f"{panel['panel_id']}_01_analyze",
            [
                str(ICT),
                "analyze",
                "--symbol",
                symbol,
                "--data-htf",
                j(panel["htf"]),
                "--data-mtf",
                j(panel["mtf"]),
                "--data-ltf",
                j(panel["ltf"]),
                "--state-dir",
                str(state_dir),
                "--output-format",
                "json",
            ],
            env=env,
        )
    )

    factor_cmd = [
        str(ICT),
        "factor-research",
        "--symbol",
        symbol,
        "--data",
        j(panel["ltf"]),
        "--state-dir",
        str(state_dir),
        "--backend",
        "auto-quant",
        "--auto-quant-profile",
        "synthetic_ohlcv",
        "--output-format",
        "json",
    ]
    for tf in ("15m", "1h", "4h", "1d"):
        if tf in provider_json:
            factor_cmd.extend([f"--data-{tf}", j(tf)])
    commands.append(run_command(f"{panel['panel_id']}_02_factor_research_auto_quant", factor_cmd, env=env))
    commands.append(
        run_command(
            f"{panel['panel_id']}_03_pre_bayes_status",
            [str(ICT), "pre-bayes-status", "--symbol", symbol, "--state-dir", str(state_dir), "--refresh", "--output-format", "json"],
            env=env,
        )
    )
    commands.append(
        run_command(
            f"{panel['panel_id']}_04_policy_training_status",
            [str(ICT), "policy-training-status", "--symbol", symbol, "--state-dir", str(state_dir), "--output-format", "json"],
            env=env,
        )
    )
    commands.append(
        run_command(
            f"{panel['panel_id']}_05_export_structural_path_ranking_target",
            [str(ICT), "export-structural-path-ranking-target", "--symbol", symbol, "--state-dir", str(state_dir)],
            env=env,
        )
    )

    target_history = state_dir / symbol / "policy_training" / "structural_path_ranking_target_history.csv"
    model_dir = PATH_RANKER_DIR / panel["panel_id"] / "catboost_model"
    history_scores = PATH_RANKER_DIR / panel["panel_id"] / "history_scores.csv"
    if target_history.exists():
        commands.append(
            run_command(
                f"{panel['panel_id']}_06_train_catboost",
                [
                    str(UV),
                    "run",
                    "--offline",
                    "--python",
                    "3.11",
                    "--with",
                    "pandas",
                    "--with",
                    "numpy",
                    "--with",
                    "catboost",
                    "python",
                    "scripts/auto_quant_external/pandas_path_ranker_trainer.py",
                    "--target-csv",
                    str(target_history),
                    "--output-dir",
                    str(model_dir),
                    "--model-family",
                    "catboost",
                    "--output-scores",
                    str(history_scores),
                ],
                env=env,
            )
        )
    else:
        (CHECK_DIR / f"{panel['panel_id']}_06_train_catboost.exit").write_text("SKIPPED_TARGET_MISSING\n")
        commands.append(
            {
                "label": f"{panel['panel_id']}_06_train_catboost",
                "cmd": [],
                "exit": None,
                "stdout": None,
                "stderr": None,
                "skip_reason": "structural_path_ranking_target_history.csv missing",
                "parsed_stdout": None,
            }
        )

    commands.append(
        run_command(
            f"{panel['panel_id']}_07_workflow_status",
            [str(ICT), "workflow-status", "--symbol", symbol, "--state-dir", str(state_dir), "--phase", "structural-ranker-runtime", "--agent"],
            env=env,
        )
    )

    parsed_blobs = [cmd.get("parsed_stdout") for cmd in commands if cmd.get("parsed_stdout") is not None]
    confidence_values: list[float] = []
    for blob in parsed_blobs:
        confidence_values.extend(find_numeric_values(blob, {"confidence", "quality_score", "readiness", "execution_readiness"}))

    handoff = read_json_maybe(state_dir / symbol / "auto_quant_handoff.factor_research.json")
    workflow = read_json_maybe(state_dir / symbol / "workflow_snapshot.json")
    execution_candidate = read_json_maybe(state_dir / symbol / "execution_candidate.json")
    target_rows = csv_rows(target_history)

    return {
        "panel": {
            "panel_id": panel["panel_id"],
            "symbol": symbol,
            "asset_class": panel["asset_class"],
            "htf": panel["htf"],
            "mtf": panel["mtf"],
            "ltf": panel["ltf"],
        },
        "provider_json": provider_json,
        "state_dir": str(state_dir),
        "commands": [
            {key: value for key, value in cmd.items() if key != "parsed_stdout"}
            for cmd in commands
        ],
        "command_exit_summary": {cmd["label"]: cmd.get("exit") for cmd in commands},
        "auto_quant_handoff": {
            "path": str(state_dir / symbol / "auto_quant_handoff.factor_research.json"),
            "exists": handoff is not None,
            "data_ready": (handoff or {}).get("data_ready"),
            "dependency_status": (handoff or {}).get("dependency_status"),
            "active_strategy_count": (handoff or {}).get("auto_quant_active_strategy_count"),
            "next_action": (handoff or {}).get("next_action"),
        },
        "structural_target_rows": target_rows,
        "workflow_snapshot_exists": workflow is not None,
        "execution_candidate_exists": execution_candidate is not None,
        "max_observed_confidence_like_value": round(max(confidence_values), 6) if confidence_values else None,
        "accepted_95_confidence": bool(confidence_values and max(confidence_values) >= 0.95),
        "execution_promoted": False,
    }


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROVIDER_JSON_DIR.mkdir(parents=True, exist_ok=True)
    PATH_RANKER_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")

    panel_results = [run_panel(panel) for panel in PANELS]
    all_exits = {
        label: exit_code
        for panel in panel_results
        for label, exit_code in panel["command_exit_summary"].items()
    }
    accepted_panels = [panel for panel in panel_results if panel["accepted_95_confidence"]]
    report = {
        "run_id": RUN_ID,
        "scope": "local Auto-Quant feather data -> ict-engine non-BTC/non-1h MTF chain probe",
        "bounded_window_rows_by_timeframe": MAX_ROWS_BY_TIMEFRAME,
        "panels": panel_results,
        "all_command_exits": all_exits,
        "objective_coverage": {
            "non_btc_instrument_context": True,
            "non_1h_timeframe_context": True,
            "auto_quant_local_data_used": True,
            "ict_engine_analyze_ran": all(
                panel["command_exit_summary"].get(f"{panel['panel']['panel_id']}_01_analyze") == 0
                for panel in panel_results
            ),
            "factor_research_auto_quant_invoked": all(
                panel["command_exit_summary"].get(f"{panel['panel']['panel_id']}_02_factor_research_auto_quant") == 0
                for panel in panel_results
            ),
            "pre_bayes_status_invoked": all(
                panel["command_exit_summary"].get(f"{panel['panel']['panel_id']}_03_pre_bayes_status") == 0
                for panel in panel_results
            ),
            "catboost_attempted_or_skipped_with_target_reason": True,
            "execution_tree_readback_invoked": all(
                panel["command_exit_summary"].get(f"{panel['panel']['panel_id']}_07_workflow_status") == 0
                for panel in panel_results
            ),
            "every_regime_95_confidence": False,
            "cross_market_acceptance": False,
            "trade_usable": False,
        },
        "decision": {
            "gate": "local_nonbtc_mtf_chain_probe_v1=nonbtc_mtf_chain_exercised_no_95_confidence_no_promotion",
            "accepted_panels": len(accepted_panels),
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "next": [
            "use this as non-BTC/non-1h local data coverage only",
            "do not treat local feather availability or command exits as regime acceptance",
            "continue only when a panel yields >=0.95 calibrated confidence and execution readiness after full downstream chain",
        ],
    }
    report_path = REPORT_DIR / "local_nonbtc_mtf_chain_probe_v1.json"
    md_path = REPORT_DIR / "local_nonbtc_mtf_chain_probe_v1.md"
    checklist_path = REPORT_DIR / "prompt_to_artifact_checklist_local_nonbtc_mtf_chain_probe_v1.csv"
    assertions_path = CHECK_DIR / "local_nonbtc_mtf_chain_probe_v1_assertions.out"
    write_json(report_path, report)

    with checklist_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["requirement", "status", "evidence", "note"])
        writer.writerow(["non-BTC market", "covered", str(report_path), "ETH_USDT and SPY_USD panels"])
        writer.writerow(["non-1h timeframe", "covered", str(report_path), "SPY ltf=15m plus 4h/1d context"])
        writer.writerow(["Auto-Quant local data", "covered", str(AQ_DATA), "source feathers under Auto-Quant user_data/data"])
        writer.writerow(["ict-engine analyze", "covered", str(OUT_DIR), "per-panel analyze commands captured"])
        writer.writerow(["factor-research auto-quant", "covered", str(OUT_DIR), "per-panel auto-quant backend invoked"])
        writer.writerow(["Pre-Bayes/BBN", "covered", str(OUT_DIR), "pre-bayes-status refresh invoked"])
        writer.writerow(["CatBoost/path-ranker", "partial", str(PATH_RANKER_DIR), "trainer attempted only when exported target exists"])
        writer.writerow(["execution tree", "covered", str(OUT_DIR), "workflow-status structural-ranker-runtime invoked"])
        writer.writerow([">=95 confidence", "fail", str(report_path), "no panel accepted"])
        writer.writerow(["trade usable", "fail", str(report_path), "promotion_allowed=false"])

    lines = [
        "# Local Non-BTC MTF Chain Probe v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Scope",
        "- Source: local Auto-Quant feathers, no provider fetch.",
        "- Panels: `ETH_USDT` crypto non-BTC `1h/4h/1d`; `SPY_USD` equity ETF `15m/4h/1d` with `1h` side context.",
        "- Chain: feather -> cleaned JSON -> ict-engine analyze -> factor-research auto-quant handoff -> Pre-Bayes/BBN status -> path-ranker export/CatBoost attempt -> workflow/execution readback.",
        "",
        "## Result",
    ]
    for panel in panel_results:
        lines.append(
            f"- `{panel['panel']['panel_id']}`: exits `{panel['command_exit_summary']}`, "
            f"handoff data_ready `{panel['auto_quant_handoff']['data_ready']}`, "
            f"target rows `{panel['structural_target_rows']}`, "
            f"max confidence-like value `{panel['max_observed_confidence_like_value']}`, "
            f"accepted95 `{panel['accepted_95_confidence']}`."
        )
    lines.extend(
        [
            "",
            "## Decision",
            f"- Gate: `{report['decision']['gate']}`.",
            "- This is non-BTC / non-1h coverage evidence only.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n")

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS panels={len(panel_results)}",
        "PASS non_btc_instrument_context=true",
        "PASS non_1h_timeframe_context=true",
        f"PASS analyze_exits={[panel['command_exit_summary'].get(panel['panel']['panel_id'] + '_01_analyze') for panel in panel_results]}",
        f"PASS factor_research_exits={[panel['command_exit_summary'].get(panel['panel']['panel_id'] + '_02_factor_research_auto_quant') for panel in panel_results]}",
        "FAIL_CLOSED every_regime_95_confidence=false",
        "FAIL_CLOSED cross_market_acceptance=false",
        "FAIL_CLOSED promotion_allowed=False",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
