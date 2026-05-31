#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


REPO = Path(__file__).resolve().parents[5]
BASE_REL = Path("support/docs/experiments/actionable-regime-confidence")
BASE = REPO / BASE_REL
CLAIMS_DIR = Path("/tmp/ict-engine-agent-claims/board-b-factor-refinement")
AQ_PY = "${AUTO_QUANT_PY:-$HOME/Auto-Quant/.venv/bin/python}"
RUN_TOMAC_ONE = Path("support/scripts/auto_quant_external/run_tomac_one.py")

AGENT_PREFIX = "codex-rachev-tail-reward-risk-admission-training-prep"
FACTOR_FAMILY = "rachev_tail_reward_risk_admission_filter"
BRANCH_PATH = (
    "ValidationMaturity -> TailRewardRiskAsymmetry -> RachevExpectedTailGainLoss -> "
    "ParentSignalAdmissionFilter"
)
SESSION_SCOPE = "ETH/full_retained_session"
TARGET_TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]
SOURCE_PACKET = BASE_REL / "20260531T073131+0800-codex-rachev-tail-reward-risk-admission-source-prep.md"


@dataclass(frozen=True)
class StrategySpec:
    timeframe: str
    class_name: str
    factor_id: str
    branch_path: str
    pair: str
    material_path: str
    trade_export_path: str
    run_command: str


@dataclass(frozen=True)
class PrepPlan:
    factor_family: str
    branch_path: str
    session_scope: str
    rth_filter_applied: bool
    target_timeframes: list[str]
    source_packet: str
    strategy_specs: list[StrategySpec]
    status: str
    decision: str
    coordination_only: bool
    no_provider_fetch: bool
    no_ibkr_historical: bool
    no_autoquant_or_freqtrade_launch: bool
    no_local_backtest_launch: bool
    no_paper_sim_live: bool
    no_downstream_lifecycle: bool
    provider_attempted: bool
    ibkr_attempted: bool
    autoquant_attempted: bool
    local_backtest_attempted: bool
    paper_or_live_attempted: bool
    downstream_lifecycle_attempted: bool
    promotion_allowed: bool
    trade_usable: bool
    update_goal: bool
    same_tree_practical_closure: None
    root: str
    compact_root: str


def factor_id(timeframe: str) -> str:
    return f"tomac_idxfut_clean_{FACTOR_FAMILY}_{timeframe}_v1"


def class_name(timeframe: str) -> str:
    safe_tf = timeframe.replace("m", "m").replace("h", "h").replace("d", "d")
    return f"TomacNq{safe_tf}RachevTailRewardRiskAdmissionV1"


def build_strategy_specs(root: Path | None = None) -> list[StrategySpec]:
    root = root or Path("/tmp/ict-engine-rachev-tail-reward-risk-admission-training-prep")
    specs: list[StrategySpec] = []
    for timeframe in TARGET_TIMEFRAMES:
        klass = class_name(timeframe)
        material = root / "materials" / f"{klass}.py"
        export = root / "checks" / f"aq_trades_{klass}.json"
        command = " ".join(
            [
                AQ_PY,
                str(RUN_TOMAC_ONE),
                klass,
                timeframe,
                str(export),
                "NQ/USD",
                "20210103-20251231",
            ]
        )
        specs.append(
            StrategySpec(
                timeframe=timeframe,
                class_name=klass,
                factor_id=factor_id(timeframe),
                branch_path=f"{BRANCH_PATH} -> {factor_id(timeframe)}",
                pair="NQ/USD",
                material_path=str(material),
                trade_export_path=str(export),
                run_command=command,
            )
        )
    return specs


def build_plan(root: Path, compact_root: Path) -> PrepPlan:
    return PrepPlan(
        factor_family=FACTOR_FAMILY,
        branch_path=BRANCH_PATH,
        session_scope=SESSION_SCOPE,
        rth_filter_applied=False,
        target_timeframes=TARGET_TIMEFRAMES,
        source_packet=str(SOURCE_PACKET),
        strategy_specs=build_strategy_specs(root),
        status="terminalized_training_prep_no_launch",
        decision="prep_packet_complete_no_launch_runtime_blocked",
        coordination_only=True,
        no_provider_fetch=True,
        no_ibkr_historical=True,
        no_autoquant_or_freqtrade_launch=True,
        no_local_backtest_launch=True,
        no_paper_sim_live=True,
        no_downstream_lifecycle=True,
        provider_attempted=False,
        ibkr_attempted=False,
        autoquant_attempted=False,
        local_backtest_attempted=False,
        paper_or_live_attempted=False,
        downstream_lifecycle_attempted=False,
        promotion_allowed=False,
        trade_usable=False,
        update_goal=False,
        same_tree_practical_closure=None,
        root=str(root),
        compact_root=str(compact_root),
    )


def strategy_source(spec: StrategySpec) -> str:
    return f'''# factor_id: {spec.factor_id}
# branch_path: {spec.branch_path}
# session_scope: {SESSION_SCOPE}
# rth_filter_applied: false
from freqtrade.strategy import IStrategy
import numpy as np
import pandas as pd


class {spec.class_name}(IStrategy):
    timeframe = "{spec.timeframe}"
    can_short = True
    startup_candle_count = 180
    minimal_roi = {{"0": 0.012}}
    stoploss = -0.0075
    trailing_stop = True
    trailing_stop_positive = 0.0022
    trailing_stop_positive_offset = 0.0065

    @staticmethod
    def _upper_tail_gain(window):
        sample = pd.Series(window).dropna()
        if len(sample) < 48:
            return np.nan
        cutoff = sample.quantile(0.90)
        gains = sample[sample >= cutoff]
        if len(gains) == 0:
            return np.nan
        return float(gains.mean())

    @staticmethod
    def _lower_tail_loss(window):
        sample = pd.Series(window).dropna()
        if len(sample) < 48:
            return np.nan
        cutoff = sample.quantile(0.10)
        losses = -sample[sample <= cutoff]
        if len(losses) == 0:
            return np.nan
        return float(losses.mean())

    def populate_indicators(self, dataframe, metadata):
        returns = dataframe["close"].pct_change()
        completed_returns = returns.shift(1)
        upper_tail_gain = completed_returns.rolling(96, min_periods=48).apply(
            self._upper_tail_gain, raw=False
        )
        lower_tail_loss = completed_returns.rolling(96, min_periods=48).apply(
            self._lower_tail_loss, raw=False
        )
        rachev_ratio_raw = upper_tail_gain / lower_tail_loss.replace(0, np.nan)
        dataframe["upper_tail_gain"] = upper_tail_gain
        dataframe["lower_tail_loss"] = lower_tail_loss
        dataframe["rachev_ratio_raw"] = rachev_ratio_raw
        dataframe["rolling_rachev_ratio"] = rachev_ratio_raw.shift(1)
        dataframe["parent_trend_slope"] = (
            dataframe["close"].rolling(55).mean() - dataframe["close"].rolling(144).mean()
        ).shift(1)
        dataframe["parent_pullback"] = (
            dataframe["close"] < dataframe["close"].rolling(21).mean()
        ).shift(1).fillna(False)
        dataframe["rachev_admission_long"] = (
            (dataframe["rolling_rachev_ratio"] > 1.18)
            & (dataframe["upper_tail_gain"].shift(1) > dataframe["lower_tail_loss"].shift(1))
            & (dataframe["parent_trend_slope"] > 0)
        )
        dataframe["rachev_admission_short"] = (
            (dataframe["rolling_rachev_ratio"] > 1.18)
            & (dataframe["upper_tail_gain"].shift(1) > dataframe["lower_tail_loss"].shift(1))
            & (dataframe["parent_trend_slope"] < 0)
        )
        return dataframe

    def populate_entry_trend(self, dataframe, metadata):
        entry_raw = dataframe["rachev_admission_long"] & dataframe["parent_pullback"]
        short_entry_raw = dataframe["rachev_admission_short"] & dataframe["parent_pullback"]
        entry = entry_raw.shift(1).fillna(False)
        short_entry = short_entry_raw.shift(1).fillna(False)
        dataframe.loc[entry, "enter_long"] = 1
        dataframe.loc[short_entry, "enter_short"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe, metadata):
        exit_long = (
            (dataframe["rolling_rachev_ratio"] < 0.92) | (dataframe["parent_trend_slope"] < 0)
        ).shift(1).fillna(False)
        exit_short = (
            (dataframe["rolling_rachev_ratio"] < 0.92) | (dataframe["parent_trend_slope"] > 0)
        ).shift(1).fillna(False)
        dataframe.loc[exit_long, "exit_long"] = 1
        dataframe.loc[exit_short, "exit_short"] = 1
        return dataframe
'''


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_workdoc(plan: PrepPlan, claim: Path, repo_doc: Path, stamp: str) -> str:
    commands = "\n".join(f"- `{spec.run_command}`" for spec in plan.strategy_specs)
    factors = "\n".join(f"- `{spec.factor_id}` -> `{spec.material_path}`" for spec in plan.strategy_specs)
    return "\n".join(
        [
            "# Rachev Tail Reward-Risk Admission Training Prep",
            "",
            f"- created_at: `{stamp}`",
            "- owner: `codex`",
            f"- agent_name: `{AGENT_PREFIX}-{stamp}`",
            f"- run_root: `{plan.root}`",
            f"- compact_root: `{plan.compact_root}`",
            f"- repo_doc: `{repo_doc}`",
            f"- claim: `{claim}`",
            f"- source_packet: `{plan.source_packet}`",
            f"- factor_family: `{plan.factor_family}`",
            f"- branch_path: `{plan.branch_path}`",
            f"- session_scope: `{plan.session_scope}`",
            f"- rth_filter_applied: `{str(plan.rth_filter_applied).lower()}`",
            f"- status: `{plan.status}`",
            "- coordination_only: `true`",
            "- promotion_allowed: `false`",
            "- trade_usable: `false`",
            "- update_goal: `false`",
            "",
            "## Objective",
            "",
            "Turn the Rachev source packet into a launch-ready training prep packet while a fresh active Board B claim blocks shared runtime. This writes exact strategy materials and commands only; it does not fetch, backtest, launch AutoQuant, or downstream lifecycle.",
            "",
            "## Independent Factors",
            "",
            factors,
            "",
            "## Runtime Boundary",
            "",
            "- No provider fetch.",
            "- No IBKR historical.",
            "- No AutoQuant, Freqtrade, or TOMAC runtime launch.",
            "- No retained-cache local screen or local backtest launch.",
            "- No paper, simulated, or live execution.",
            "- No downstream lifecycle launch.",
            "- No same_tree_practical_closure packet.",
            "- No promotion_allowed=true, trade_usable=true, or update_goal=true.",
            "",
            "## Feature Contract",
            "",
            "Use only completed, shifted return windows. Rachev admission compares rolling upper-tail gain with lower-tail loss before entry, then gates an existing parent trend/pullback signal. The first runnable slice must compare parent-only versus parent-plus-Rachev under ETH/full-retained coverage, verified instrument cost, sample, density, year split, accepted execution feedback, and lifecycle gates.",
            "",
            "## Commands When Claim Audit Clears",
            "",
            commands,
            "",
            "## Status",
            "",
            "- decision: `prep_packet_complete_no_launch_runtime_blocked`",
            "- next_gate: `run_one_timeframe_after_claim_audit_clears`",
            "- promotion_allowed: `false`",
            "- trade_usable: `false`",
            "- update_goal: `false`",
        ]
    ) + "\n"


def build_summary(plan: PrepPlan, claim: Path, repo_doc: Path, workdoc: Path) -> dict[str, object]:
    payload = asdict(plan)
    payload.update(
        {
            "schema_version": "rachev-tail-reward-risk-admission-training-prep/v1",
            "claim": str(claim),
            "repo_doc": str(repo_doc),
            "workdoc": str(workdoc),
            "commands_when_clear": [spec.run_command for spec in plan.strategy_specs],
        }
    )
    return payload


def build_claim(plan: PrepPlan, claim: Path, repo_doc: Path, workdoc: Path, stamp: str) -> dict[str, object]:
    return {
        "schema_version": "board-b-factor-claim/v1",
        "claimed_at": stamp,
        "last_progress_at": stamp,
        "owner": "codex",
        "agent_name": f"{AGENT_PREFIX}-{stamp}",
        "scope": "Board B no-launch training prep for Rachev tail reward-risk admission while a fresh VHF/CHOP claim blocks AQ launch.",
        "active_task": "Create launch-ready strategy materials, workdoc, claim, summaries, and commands only; do not launch provider/AQ/IBKR/paper/lifecycle/local backtest.",
        "non_goals": [
            "No provider fetch",
            "No IBKR historical",
            "No AutoQuant, Freqtrade, or TOMAC runtime launch",
            "No retained-cache local screen or local backtest launch",
            "No paper, simulated, or live execution",
            "No downstream lifecycle launch",
            "No same_tree_practical_closure packet",
            "No promotion_allowed=true, trade_usable=true, or update_goal=true",
        ],
        "write_surface": str(workdoc),
        "repo_workdoc": str(repo_doc),
        "source_packet": plan.source_packet,
        "run_root": plan.root,
        "tmp_root": plan.root,
        "repo_run_root": plan.compact_root,
        "factor_family": plan.factor_family,
        "factor_id_shape": f"tomac_idxfut_clean_{FACTOR_FAMILY}_<timeframe>_v1",
        "target_timeframes": plan.target_timeframes,
        "branch_path": f"{plan.branch_path} -> tomac_idxfut_clean_{FACTOR_FAMILY}_<timeframe>_v1",
        "session_scope": plan.session_scope,
        "rth_filter_applied": plan.rth_filter_applied,
        "coordination_only": True,
        "status": plan.status,
        "decision": plan.decision,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "same_tree_practical_closure": None,
        "progress_report": "Rachev no-launch training prep packet created; runtime commands intentionally not launched while compact audit is blocked by a fresh active claim.",
        "latest_report": str(workdoc),
        "terminal_summary": str(Path(plan.root) / "summaries" / "prep_summary.json"),
        "next_commands_when_clear": [spec.run_command for spec in plan.strategy_specs],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Rachev tail reward-risk admission materials without launching runtime.")
    now = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
    parser.add_argument("--root", default=None)
    parser.add_argument("--compact-root", default=None)
    parser.add_argument("--claim", default=None)
    parser.add_argument("--repo-doc", default=None)
    parser.add_argument("--stamp", default=now)
    args = parser.parse_args(argv)
    stamp = args.stamp
    if args.root is None:
        args.root = str(Path("/tmp") / f"ict-engine-rachev-tail-reward-risk-admission-training-prep-{stamp}")
    if args.compact_root is None:
        args.compact_root = str(BASE / "runs" / f"{stamp}-codex-rachev-tail-reward-risk-admission-training-prep-v1")
    if args.claim is None:
        args.claim = str(CLAIMS_DIR / f"{stamp}-codex-rachev-tail-reward-risk-admission-training-prep.claim")
    if args.repo_doc is None:
        args.repo_doc = str(BASE / f"{stamp}-codex-rachev-tail-reward-risk-admission-training-prep.md")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root)
    compact_root = Path(args.compact_root)
    claim = Path(args.claim)
    repo_doc = Path(args.repo_doc)
    workdoc = root / "workdoc.md"
    plan = build_plan(root, compact_root)

    for spec in plan.strategy_specs:
        material = Path(spec.material_path)
        material.parent.mkdir(parents=True, exist_ok=True)
        material.write_text(strategy_source(spec), encoding="utf-8")

    workdoc_text = render_workdoc(plan, claim, repo_doc, args.stamp)
    workdoc.parent.mkdir(parents=True, exist_ok=True)
    repo_doc.parent.mkdir(parents=True, exist_ok=True)
    workdoc.write_text(workdoc_text, encoding="utf-8")
    repo_doc.write_text(workdoc_text, encoding="utf-8")

    launch_plan = {
        "schema_version": "rachev-tail-reward-risk-admission-launch-plan/v1",
        "commands_when_clear": [spec.run_command for spec in plan.strategy_specs],
        "strategy_materials": [spec.material_path for spec in plan.strategy_specs],
        "status": plan.status,
        "promotion_allowed": False,
        "trade_usable": False,
    }
    write_json(root / "summaries" / "launch_plan.json", launch_plan)
    write_json(compact_root / "summaries" / "launch_plan.json", launch_plan)
    summary = build_summary(plan, claim, repo_doc, workdoc)
    write_json(root / "summaries" / "prep_summary.json", summary)
    write_json(compact_root / "summaries" / "prep_summary.json", summary)
    write_json(claim, build_claim(plan, claim, repo_doc, workdoc, args.stamp))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
