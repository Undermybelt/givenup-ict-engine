#!/usr/bin/env python3
"""Board B sibling Crisis leaf with explicit crowded-context suppression."""

from __future__ import annotations

import csv
import json
import math
import random
import statistics
import subprocess
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any


RUN_ID = "20260511T235616+0800-codex-board-b-crisis-crowded-suppression-sibling-v1"
SCHEMA_VERSION = "board-b-crisis-crowded-suppression-sibling/v1"
SYMBOL = "SRC_ROOT_CARRY_LONG_220646"
SOURCE_RECIPE = "SourceRootStopCarryLongHorizonV1"
SIBLING_RECIPE = "SourceRootStopCarryLongHorizonV1_CrisisCrowdedSuppressionV1"
SOURCE_BRANCH = (
    "Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> "
    "SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12"
)
SIBLING_BRANCH = (
    "Crisis -> CrisisReliefCarry -> CrowdedRangeSuppression -> "
    "SourceRootStopCarryLongHorizonV1_CrisisCrowdedSuppressionV1:"
    "crisis_carry_h8_sl048_tp12_vixgt24"
)
VIX_THRESHOLD = 24.0


SCRIPT = Path(__file__).resolve()
RUN_ROOT = SCRIPT.parents[1]
REPO = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
ICT = REPO / "target" / "debug" / "ict-engine"
OUT = RUN_ROOT / "crisis-crowded-suppression-sibling-v1"
LOGS = OUT / "command-output"
CHECKS = RUN_ROOT / "checks"
STATE_DIR = OUT / "state_crisis_crowded_suppression_v1"

SOURCE_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1"
)
SELECTED_ROWS = (
    SOURCE_ROOT
    / "branch-rc-spa/source_root_stop_carry_longhorizon_selected_rows_v1.csv"
)
SOURCE_WIRE = SOURCE_ROOT / "b5-branch-feedback-calibration-v1/selected_real_trades_wire.jsonl"

ROWS_OUT = OUT / "crisis_crowded_suppression_selected_rows_v1.csv"
WIRE_OUT = OUT / "crisis_crowded_suppression_real_trades_wire_v1.jsonl"
GRID_OUT = OUT / "crisis_crowded_suppression_threshold_grid_v1.csv"
SUMMARY_JSON = OUT / "crisis_crowded_suppression_sibling_v1.json"
SUMMARY_MD = OUT / "crisis_crowded_suppression_sibling_v1.md"
ASSERTIONS = CHECKS / "crisis_crowded_suppression_sibling_v1_assertions.out"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def normal_lcb(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    return mean(values) - 1.645 * (statistics.pstdev(values) / math.sqrt(len(values)))


def bootstrap_lcb(values: list[float], rounds: int = 2000) -> float:
    if not values:
        return 0.0
    rng = random.Random(220646)
    n = len(values)
    means = []
    for _ in range(rounds):
        means.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    return means[max(0, int(0.05 * len(means)) - 1)]


def threshold_grid(crisis_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grid = []
    for threshold in [18.0, 20.0, 22.0, 24.0, 25.0, 28.0, 30.0, 35.0, 40.0, 45.0]:
        kept = [row for row in crisis_rows if float(row["source_ticker_vix"]) > threshold]
        returns = [float(row["profit_ratio_net"]) for row in kept]
        stressed = [
            float(row["profit_ratio_net"]) - float(row["roundtrip_cost"])
            for row in kept
        ]
        by_fold: dict[str, list[float]] = defaultdict(list)
        for row in kept:
            by_fold[row["year_fold"]].append(float(row["profit_ratio_net"]))
        positive_folds = sum(1 for values in by_fold.values() if sum(values) > 0.0)
        folds = len(by_fold)
        fold_positive_rate = positive_folds / folds if folds else 0.0
        min_fold_trades = min((len(values) for values in by_fold.values()), default=0)
        grid.append(
            {
                "threshold_rule": f"source_ticker_vix>{threshold:g}",
                "threshold": threshold,
                "kept_trades": len(kept),
                "suppressed_trades": len(crisis_rows) - len(kept),
                "folds": folds,
                "min_fold_trades": min_fold_trades,
                "fold_positive_rate": round(fold_positive_rate, 6),
                "mean_net": round(mean(returns), 8),
                "normal_lcb_5pct": round(normal_lcb(returns), 8),
                "bootstrap_lcb_5pct": round(bootstrap_lcb(returns), 8),
                "cost_stress_lcb_5pct": round(normal_lcb(stressed), 8),
                "nursery_gate": (
                    len(kept) >= 50
                    and folds >= 4
                    and min_fold_trades >= 10
                    and fold_positive_rate >= 0.75
                    and normal_lcb(stressed) > 0
                ),
            }
        )
    return grid


def apply_sibling_to_selected_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output = []
    for row in rows:
        if row["parent_regime_root"] != "Crisis":
            output.append(row)
            continue
        if float(row["source_ticker_vix"]) <= VIX_THRESHOLD:
            continue
        edited = dict(row)
        edited["schema_version"] = SCHEMA_VERSION
        edited["run_id"] = RUN_ID
        edited["recipe_id"] = SIBLING_RECIPE
        edited["variant_id"] = "crisis_carry_h8_sl048_tp12_vixgt24"
        edited["sub_sub_regime_or_profit_factor"] = "CrowdedRangeSuppression"
        edited["profit_factor_family"] = "source_root_stop_carry_longhorizon_crowded_suppression"
        edited["profit_factor_leaf"] = (
            f"{SIBLING_RECIPE}:crisis_carry_h8_sl048_tp12_vixgt24"
        )
        edited["regime_profit_branch_path"] = SIBLING_BRANCH
        edited["regime_profit_branch_path_version"] = SCHEMA_VERSION
        edited["allowed_action"] = (
            "long_relief_only_when_crisis_vix_gt_24_and_execution_not_crowded"
        )
        edited["suppression_rule"] = (
            "suppress_if_source_ticker_vix_lte_24_or_runtime_market_state_"
            "RangeConsolidation_WideRange_crowded"
        )
        edited["trade_id"] = f"{edited['trade_id']}:crowded_suppressed_v1"
        output.append(edited)
    return output


def build_wire(selected_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    keep_ids = {row["trade_id"].replace(":crowded_suppressed_v1", ""): row for row in selected_rows}
    output = []
    total = len(selected_rows)
    for record in read_jsonl(SOURCE_WIRE):
        source_id = str(record.get("trade_id", ""))
        if source_id not in keep_ids:
            continue
        row = keep_ids[source_id]
        edited = deepcopy(record)
        edited["auto_quant_run_id"] = RUN_ID
        edited["strategy_name"] = SIBLING_RECIPE if row["parent_regime_root"] == "Crisis" else record.get("strategy_name")
        edited["trade_id"] = row["trade_id"]
        if row["parent_regime_root"] == "Crisis":
            edited["entry_signal"] = row["variant_id"]
            edited["strategy_mutation_id"] = "board-b-crisis-crowded-suppression-v1"
            for factor in edited.get("factors_used", []):
                if factor.get("category") == "source_root_stop_carry_longhorizon":
                    factor["category"] = "source_root_stop_carry_longhorizon_crowded_suppression"
                    factor["factor_name"] = row["profit_factor_leaf"]
                if factor.get("category") == "branch_path":
                    factor["factor_name"] = "regime_profit_branch_path"
            feedback = edited.get("structural_feedback", {})
            feedback["protocol_version"] = SCHEMA_VERSION
            feedback["branch_id"] = SIBLING_BRANCH
            feedback["path_id"] = SIBLING_BRANCH
            feedback["entry_style"] = row["variant_id"]
            feedback["scenario_id"] = "CrisisReliefCarry"
            feedback["candidate_set_id"] = RUN_ID
            feedback["candidate_set_size"] = total
            feedback["notes"] = (
                "board_b_crisis_crowded_suppression_sibling_v1;"
                "suppressed low-VIX/crowded-range proxy Crisis entries;"
                "incubation_only_not_production"
            )
        else:
            edited.get("structural_feedback", {})["candidate_set_id"] = RUN_ID
            edited.get("structural_feedback", {})["candidate_set_size"] = total
        output.append(edited)
    return output


def run_command(name: str, cmd: list[str], timeout: int = 120) -> dict[str, Any]:
    LOGS.mkdir(parents=True, exist_ok=True)
    out_path = LOGS / f"{name}.out"
    err_path = LOGS / f"{name}.err"
    exit_path = LOGS / f"{name}.exit"
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(REPO),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        stderr = f"{stderr}\nTIMEOUT after {timeout}s\n"
        code = 124
        timed_out = True
    out_path.write_text(stdout, encoding="utf-8")
    err_path.write_text(stderr, encoding="utf-8")
    exit_path.write_text(f"{code}\n", encoding="utf-8")
    return {
        "name": name,
        "cmd": " ".join(cmd),
        "returncode": code,
        "timed_out": timed_out,
        "stdout": rel(out_path),
        "stderr": rel(err_path),
        "exit": rel(exit_path),
    }


def load_json_from_log(name: str) -> dict[str, Any]:
    path = LOGS / f"{name}.out"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    source_rows = read_csv(SELECTED_ROWS)
    crisis_rows = [row for row in source_rows if row["parent_regime_root"] == "Crisis"]
    grid = threshold_grid(crisis_rows)
    write_csv(GRID_OUT, grid)

    selected_rows = apply_sibling_to_selected_rows(source_rows)
    write_csv(ROWS_OUT, selected_rows)
    wire = build_wire(selected_rows)
    WIRE_OUT.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in wire),
        encoding="utf-8",
    )

    commands = [
        run_command("01_provider_status_agent", [str(ICT), "provider-status", "--agent"]),
        run_command(
            "02_auto_quant_status_local",
            [
                str(ICT),
                "auto-quant-status",
                "--state-dir",
                str(STATE_DIR / "auto-quant"),
                "--output-format",
                "json",
            ],
        ),
        run_command(
            "03_ingest_real_trades_dry_run",
            [
                str(ICT),
                "auto-quant-ingest-real-trades",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--trades",
                str(WIRE_OUT),
                "--source",
                "board_b_crisis_crowded_suppression_sibling_v1",
                "--dry-run",
            ],
            timeout=180,
        ),
        run_command(
            "04_ingest_real_trades_apply",
            [
                str(ICT),
                "auto-quant-ingest-real-trades",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--trades",
                str(WIRE_OUT),
                "--source",
                "board_b_crisis_crowded_suppression_sibling_v1",
            ],
            timeout=180,
        ),
        run_command(
            "05_pre_bayes_status",
            [
                str(ICT),
                "pre-bayes-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
        ),
        run_command(
            "06_policy_training_status",
            [
                str(ICT),
                "policy-training-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
        ),
        run_command(
            "07_workflow_status",
            [
                str(ICT),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
        ),
    ]

    selected_grid = next(row for row in grid if float(row["threshold"]) == VIX_THRESHOLD)
    root_counts = Counter(row["parent_regime_root"] for row in selected_rows)
    suppressed_crisis = len(crisis_rows) - root_counts["Crisis"]
    command_failures = [cmd for cmd in commands if cmd["returncode"] != 0]
    ingest_dry = load_json_from_log("03_ingest_real_trades_dry_run")
    ingest_apply = load_json_from_log("04_ingest_real_trades_apply")
    pre_bayes = load_json_from_log("05_pre_bayes_status")
    policy = load_json_from_log("06_policy_training_status")
    workflow = load_json_from_log("07_workflow_status")

    packet = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "source_recipe": SOURCE_RECIPE,
        "sibling_recipe": SIBLING_RECIPE,
        "nursery_status": "incubation_only",
        "parent_regime_root": "Crisis",
        "source_branch_path": SOURCE_BRANCH,
        "sibling_branch_path": SIBLING_BRANCH,
        "suppression_rule": (
            "suppress Crisis carry when source_ticker_vix <= 24.0 as a historical "
            "proxy for crowded/non-panic wide-range contexts; live runtime still "
            "must enforce RangeConsolidation/WideRange execution suppression directly."
        ),
        "threshold_grid": rel(GRID_OUT),
        "selected_threshold": selected_grid,
        "root_counts_after_suppression": dict(root_counts),
        "suppressed_crisis_trades": suppressed_crisis,
        "selected_rows": rel(ROWS_OUT),
        "wire_jsonl": rel(WIRE_OUT),
        "commands": commands,
        "downstream_probe": {
            "ingest_dry_run_status": ingest_dry.get("status"),
            "ingest_apply_status": ingest_apply.get("status"),
            "pre_bayes_gate_status": pre_bayes.get("latest_gate_status"),
            "policy_training_status_keys": sorted(policy.keys())[:12],
            "workflow_blocking_stage": (
                workflow.get("blocking_truth", {}).get("stage")
                if isinstance(workflow.get("blocking_truth"), dict)
                else None
            ),
            "workflow_blocking_reason": (
                workflow.get("blocking_truth", {}).get("reason")
                if isinstance(workflow.get("blocking_truth"), dict)
                else None
            ),
        },
        "promotion_allowed": False,
        "promotion_blocker": (
            "nursery_only: sibling Crisis leaf has a positive replay proxy and parses/applies "
            "in isolated ict-engine state, but it has not produced execution-tree admission "
            "or closed-loop confidence."
        ),
        "next_action": (
            "If this sibling remains useful, add historical market-state/execution-readiness "
            "labels or rerun the full Auto-Quant branch with runtime RangeConsolidation/"
            "WideRange suppression as a first-class branch field."
        ),
    }
    write_json(SUMMARY_JSON, packet)

    assertions = [
        f"run_id={RUN_ID}",
        "nursery_status=incubation_only",
        f"sibling_branch_path={SIBLING_BRANCH}",
        f"source_crisis_trades={len(crisis_rows)}",
        f"sibling_crisis_trades={root_counts['Crisis']}",
        f"suppressed_crisis_trades={suppressed_crisis}",
        f"selected_threshold={VIX_THRESHOLD}",
        f"threshold_nursery_gate={selected_grid['nursery_gate']}",
        f"threshold_fold_positive_rate={selected_grid['fold_positive_rate']}",
        f"threshold_cost_stress_lcb={selected_grid['cost_stress_lcb_5pct']}",
        f"wire_records={len(wire)}",
        f"command_failures={len(command_failures)}",
        f"ingest_dry_run_exit={commands[2]['returncode']}",
        f"ingest_apply_exit={commands[3]['returncode']}",
        f"promotion_allowed={packet['promotion_allowed']}",
        "update_goal=false",
    ]
    ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    SUMMARY_MD.write_text(
        "\n".join(
            [
                "# Crisis Crowded Suppression Sibling v1",
                "",
                "## Decision",
                "",
                "This is an `incubation_only` sibling Crisis leaf. It suppresses low-VIX Crisis carry rows as a historical proxy for crowded/non-panic wide-range contexts, then proves the modified branch artifact can be parsed and applied in isolated ict-engine state. It is not promoted.",
                "",
                "## Branch",
                "",
                f"- Source branch: `{SOURCE_BRANCH}`",
                f"- Sibling branch: `{SIBLING_BRANCH}`",
                f"- Suppression: `source_ticker_vix <= {VIX_THRESHOLD:g}` is no-trade for this nursery replay.",
                f"- Crisis rows: source `{len(crisis_rows)}`, sibling `{root_counts['Crisis']}`, suppressed `{suppressed_crisis}`.",
                "",
                "## Nursery Backtest Proxy",
                "",
                f"- Selected threshold: `{selected_grid['threshold_rule']}`",
                f"- Kept trades: `{selected_grid['kept_trades']}`",
                f"- Folds: `{selected_grid['folds']}`; min fold trades `{selected_grid['min_fold_trades']}`",
                f"- Fold positive rate: `{selected_grid['fold_positive_rate']}`",
                f"- Bootstrap LCB 5pct: `{selected_grid['bootstrap_lcb_5pct']}`",
                f"- 2x-cost stress LCB 5pct: `{selected_grid['cost_stress_lcb_5pct']}`",
                f"- Nursery gate: `{selected_grid['nursery_gate']}`",
                "",
                "## Downstream Probe",
                "",
                f"- Modified wire records: `{len(wire)}`",
                f"- Command failures: `{len(command_failures)}`",
                f"- Dry-run ingest exit: `{commands[2]['returncode']}`",
                f"- Apply ingest exit: `{commands[3]['returncode']}`",
                f"- Pre-Bayes latest gate after apply: `{packet['downstream_probe']['pre_bayes_gate_status']}`",
                f"- Workflow blocker after apply: `{packet['downstream_probe']['workflow_blocking_reason']}`",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{rel(SUMMARY_JSON)}`",
                f"- Selected rows: `{rel(ROWS_OUT)}`",
                f"- Wire JSONL: `{rel(WIRE_OUT)}`",
                f"- Threshold grid: `{rel(GRID_OUT)}`",
                f"- Assertions: `{rel(ASSERTIONS)}`",
                f"- Logs: `{rel(LOGS)}`",
                "",
                "## Next",
                "",
                "Do not promote this sibling. The next useful step is adding historical market-state / execution-readiness labels, or rerunning the Auto-Quant branch with runtime `RangeConsolidation/WideRange` suppression emitted as a first-class field before the same Pre-Bayes / BBN / CatBoost / execution-tree chain.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(rel(SUMMARY_MD))
    return 0 if not command_failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
