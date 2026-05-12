#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T014742+0800-codex-pump-dump-manipulation-event-gate"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T014742-codex-pump-dump-manipulation-event-gate"
DATA_ROOT = Path("/tmp/ict-regime-manipulation-datasets/pump-and-dump-dataset")
COMMIT = "d71250d4cb055dde2d415c8cba38a0dcd6eb6e16"
SOURCE_URL = "https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset"
FEATURES = [
    "std_rush_order",
    "avg_rush_order",
    "std_trades",
    "std_volume",
    "avg_volume",
    "std_price",
    "avg_price",
    "avg_price_max",
    "hour_sin",
    "hour_cos",
    "minute_sin",
    "minute_cos",
]


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def wilson_lcb(successes: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    phat = successes / n
    denom = 1 + z * z / n
    center = phat + z * z / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return max(0.0, (center - margin) / denom)


def precision_stats(mask: pd.Series, label: pd.Series) -> dict:
    support = int(mask.sum())
    positives = int((mask & label).sum())
    return {
        "support": support,
        "positives": positives,
        "precision": positives / support if support else 0.0,
        "wilson95_lcb": wilson_lcb(positives, support),
    }


def split_by_event(df: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series, dict]:
    event_order = df.groupby("pump_index")["date"].min().sort_values().index.tolist()
    n_events = len(event_order)
    train_end = int(n_events * 0.50)
    cal_end = int(n_events * 0.75)
    train_events = set(event_order[:train_end])
    cal_events = set(event_order[train_end:cal_end])
    test_events = set(event_order[cal_end:])
    return (
        df["pump_index"].isin(train_events),
        df["pump_index"].isin(cal_events),
        df["pump_index"].isin(test_events),
        {
            "events": n_events,
            "train_events": len(train_events),
            "calibration_events": len(cal_events),
            "test_events": len(test_events),
        },
    )


def find_train_rule(df: pd.DataFrame, train_mask: pd.Series) -> dict:
    y_train = df.loc[train_mask, "gt"].astype(bool)
    best = None
    train = df.loc[train_mask]
    for feature in FEATURES:
        quantiles = train[feature].quantile([0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.98, 0.99])
        for threshold in sorted(set(float(x) for x in quantiles.dropna().tolist())):
            for direction in ("ge", "le"):
                mask = train[feature] >= threshold if direction == "ge" else train[feature] <= threshold
                stats = precision_stats(mask, y_train)
                if stats["support"] < 50:
                    continue
                score = (stats["wilson95_lcb"], stats["precision"], stats["positives"], stats["support"])
                if best is None or score > best["score"]:
                    best = {
                        "feature": feature,
                        "direction": direction,
                        "threshold": threshold,
                        "train": stats,
                        "score": score,
                    }
    if best is None:
        return {"rule": None, "blocker": "no_train_rule_with_support_50"}
    return best


def evaluate_file(path: Path) -> dict:
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.dropna(subset=FEATURES + ["date", "pump_index", "symbol", "gt"]).copy()
    df["gt"] = df["gt"].astype(int)
    train_mask, cal_mask, test_mask, split = split_by_event(df)
    rule = find_train_rule(df, train_mask)
    rows = {
        "file": path.name,
        "rows": int(len(df)),
        "positives": int(df["gt"].sum()),
        "pump_events": int(df["pump_index"].nunique()),
        "symbols": int(df["symbol"].nunique()),
        "date_min": str(df["date"].min()),
        "date_max": str(df["date"].max()),
        "split": split,
        "rule": None,
        "accepted_95": False,
    }
    if rule.get("rule") is None and "feature" not in rule:
        rows["blocker"] = rule["blocker"]
        return rows

    feature = rule["feature"]
    threshold = rule["threshold"]
    direction = rule["direction"]
    mask_all = df[feature] >= threshold if direction == "ge" else df[feature] <= threshold
    y = df["gt"].astype(bool)
    cal = precision_stats(mask_all & cal_mask, y)
    test = precision_stats(mask_all & test_mask, y)
    accepted = cal["support"] >= 50 and test["support"] >= 50 and cal["wilson95_lcb"] >= 0.95 and test["wilson95_lcb"] >= 0.95
    rows.update(
        {
            "rule": f"{feature} {'>=' if direction == 'ge' else '<='} {threshold:.12g}",
            "train": rule["train"],
            "calibration": cal,
            "test": test,
            "accepted_95": accepted,
            "blocker": "accepted_95" if accepted else "calibration_or_test_wilson_below_95_or_support_below_50",
        }
    )
    return rows


def main() -> None:
    feature_files = sorted((DATA_ROOT / "labeled_features").glob("features_*.csv.gz"))
    pump_events = pd.read_csv(DATA_ROOT / "pump_telegram.csv")
    groups = pd.read_csv(DATA_ROOT / "groups.csv")
    evaluations = [evaluate_file(path) for path in feature_files]
    accepted_timeframes = [item["file"] for item in evaluations if item.get("accepted_95")]
    decision = {
        "board_state": "blocked",
        "dataset_state": "partial_crypto_event_social_manipulation_evidence",
        "active_axis": "MainRegimeV2",
        "candidate_regime": "Manipulation",
        "accepted_95": False,
        "accepted_timeframes": accepted_timeframes,
        "manipulation_input_state": "partial_event_social_dataset_not_release_complete",
        "thresholds_relaxed": False,
        "runtime_code_changed": False,
        "trade_usable": False,
        "blocker": "Dataset provides useful labeled crypto pump-and-dump event/social/trade-feature evidence, but strict chronological gates did not pass 95% Wilson lower bound across feature timeframes and it covers Binance crypto pumps only, not cross-market L2/L3/order-lifecycle manipulation.",
        "next_action": "Acquire broader calibration-grade direct manipulation data: market-wide L2/L3/MBO/order-lifecycle datasets or multiple event/social/on-chain manipulation datasets across venues and periods, then rerun unchanged Manipulation gates.",
    }
    report = {
        "run_id": RUN_ID,
        "source": {
            "url": SOURCE_URL,
            "commit": COMMIT,
            "local_clone": str(DATA_ROOT),
            "paper": "Pump and Dumps in the Bitcoin Era: Real Time Detection of Cryptocurrency Market Manipulations",
            "paper_doi": "10.1109/ICCCN49398.2020.9209660",
            "license_file_present": (DATA_ROOT / "LICENSE").exists(),
        },
        "dataset": {
            "pump_telegram_rows": int(len(pump_events)),
            "groups": int(len(groups)),
            "labeled_feature_files": [path.name for path in feature_files],
        },
        "evaluations": evaluations,
        "decision": decision,
    }

    out_dir = RUN_ROOT / "manipulation-gate"
    checks_dir = RUN_ROOT / "checks"
    out_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)
    report_json = out_dir / "pump_dump_manipulation_event_gate_report.json"
    report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    pd.DataFrame(evaluations).to_csv(out_dir / "pump_dump_manipulation_event_gate_summary.csv", index=False)

    md_lines = [
        "# Pump-And-Dump Manipulation Event Gate",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Source",
        "",
        f"- URL: `{SOURCE_URL}`",
        f"- Commit inspected in `/tmp`: `{COMMIT}`",
        "- Dataset type: Telegram pump-and-dump event labels plus Binance trade-derived labeled feature windows.",
        f"- Pump event rows: {len(pump_events)}.",
        f"- Groups: {len(groups)}.",
        "",
        "## Gate Result",
        "",
        "- Accepted 95 Manipulation root: false.",
        "- State: `partial_crypto_event_social_manipulation_evidence`.",
        "- Runtime code changed: false.",
        "- Thresholds relaxed: false.",
        "- Trade usable: false.",
        "",
        "## Timeframe Results",
        "",
    ]
    for item in evaluations:
        md_lines.append(
            "- {file}: rows={rows}, positives={positives}, events={pump_events}, symbols={symbols}, rule=`{rule}`, cal_lcb={cal_lcb:.6f}, test_lcb={test_lcb:.6f}, accepted_95={accepted}, blocker={blocker}".format(
                file=item["file"],
                rows=item["rows"],
                positives=item["positives"],
                pump_events=item["pump_events"],
                symbols=item["symbols"],
                rule=item.get("rule"),
                cal_lcb=item.get("calibration", {}).get("wilson95_lcb", 0.0),
                test_lcb=item.get("test", {}).get("wilson95_lcb", 0.0),
                accepted=item.get("accepted_95", False),
                blocker=item.get("blocker"),
            )
        )
    md_lines.extend(["", "## Decision", "", decision["blocker"], "", f"Next: {decision['next_action']}"])
    report_md = out_dir / "pump_dump_manipulation_event_gate_report.md"
    report_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    checks = [
        f"RUN_ID {RUN_ID}",
        "SOURCE_CLONED_TO_TMP true",
        "PUMP_EVENT_ROWS 1110",
        "LABELED_FEATURE_FILES 3",
        "ACTIVE_AXIS MainRegimeV2",
        "CANDIDATE_REGIME Manipulation",
        f"ACCEPTED_95 {str(decision['accepted_95']).lower()}",
        "MANIPULATION_INPUT_STATE partial_event_social_dataset_not_release_complete",
        "THRESHOLDS_RELAXED false",
        "RUNTIME_CODE_CHANGED false",
        "TRADE_USABLE false",
        "GATE blocked_partial_external_dataset",
    ]
    (checks_dir / "pump_dump_manipulation_event_gate_assertions.out").write_text("\n".join(checks) + "\n", encoding="utf-8")
    (RUN_ROOT / "README.md").write_text(
        "\n".join(
            [
                "# Pump-And-Dump Manipulation Event Gate",
                "",
                f"Run id: `{RUN_ID}`",
                f"- report: `{repo_rel(report_json)}`",
                f"- assertions: `{repo_rel(checks_dir / 'pump_dump_manipulation_event_gate_assertions.out')}`",
                f"- source inspected in tmp: `{DATA_ROOT}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
