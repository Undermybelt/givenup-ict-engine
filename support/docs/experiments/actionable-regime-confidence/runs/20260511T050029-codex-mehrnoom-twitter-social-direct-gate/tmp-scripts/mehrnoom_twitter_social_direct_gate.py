#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import statistics
from bisect import bisect_left, bisect_right
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T050029+0800-codex-mehrnoom-twitter-social-direct-gate"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T050029-codex-mehrnoom-twitter-social-direct-gate"
OUT_DIR = RUN_ROOT / "mehrnoom-social-gate"
CHECK_DIR = RUN_ROOT / "checks"
SOURCE_ROOT = Path("/private/tmp/ict-regime-mehrnoom-pumpdump-sparse")
CLASSIFIED = SOURCE_ROOT / "Telegram/classified/coin-pump.csv"
COINS = ("BTC", "ADA")

MIN_CAL_SUPPORT = 120
MIN_TEST_SUPPORT = 120
MIN_COVERAGE = 0.03
MIN_WILSON = 0.95
NEGATIVE_MULTIPLE = 3
EXCLUSION_MS = 6 * 60 * 60 * 1000
WINDOWS_MS = {
    "1h": 60 * 60 * 1000,
    "6h": 6 * 60 * 60 * 1000,
    "24h": 24 * 60 * 60 * 1000,
}


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


def stats(rows: list[dict], predicate) -> dict:
    selected = [row for row in rows if predicate(row)]
    successes = sum(1 for row in selected if row["label"] == 1)
    return {
        "support": len(selected),
        "successes": successes,
        "precision": successes / len(selected) if selected else 0.0,
        "wilson95_lcb": wilson_lcb(successes, len(selected)),
        "coverage": len(selected) / len(rows) if rows else 0.0,
    }


def load_series(path: Path) -> tuple[list[int], list[float], list[float]]:
    data = json.loads(path.read_text())
    pairs = []
    for item in data.get("data", []):
        if not isinstance(item, list) or len(item) != 2:
            continue
        ts_obj, value = item
        try:
            ts = int(ts_obj["$date"])
            val = float(value)
        except (KeyError, TypeError, ValueError):
            continue
        pairs.append((ts, val))
    pairs.sort()
    times = [ts for ts, _ in pairs]
    values = [val for _, val in pairs]
    prefix = [0.0]
    for value in values:
        prefix.append(prefix[-1] + value)
    return times, values, prefix


def value_at(series: tuple[list[int], list[float], list[float]], ts: int) -> float:
    times, values, _ = series
    idx = bisect_right(times, ts) - 1
    return values[idx] if idx >= 0 else 0.0


def mean_between(series: tuple[list[int], list[float], list[float]], lo: int, hi: int) -> float:
    times, _, prefix = series
    left = bisect_left(times, lo)
    right = bisect_right(times, hi)
    count = right - left
    if count <= 0:
        return 0.0
    return (prefix[right] - prefix[left]) / count


def parse_event_time(date_s: str, time_s: str) -> int:
    dt = datetime.strptime(f"{date_s} {time_s}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def load_positive_events() -> dict[str, list[int]]:
    events: dict[str, list[int]] = {coin: [] for coin in COINS}
    with CLASSIFIED.open(newline="", encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            coin = (row.get("Coin") or "").strip().upper()
            if coin not in events:
                continue
            try:
                events[coin].append(parse_event_time(row["Date"], row["Time"]))
            except (KeyError, ValueError):
                continue
    return {coin: sorted(set(times)) for coin, times in events.items()}


def load_coin_series(coin: str) -> dict[str, tuple[list[int], list[float], list[float]]]:
    return {
        "sentiment": load_series(SOURCE_ROOT / f"Twitter/sentiment-ts/{coin}.json"),
        "tweets": load_series(SOURCE_ROOT / f"Twitter/tweets-ts/${coin}.json"),
        "users": load_series(SOURCE_ROOT / f"Twitter/users-ts/${coin}.json"),
    }


def features_for(coin: str, ts: int, series_map: dict[str, tuple[list[int], list[float], list[float]]]) -> dict:
    row = {"coin": coin, "timestamp": ts}
    for name, series in series_map.items():
        current = value_at(series, ts)
        row[f"{name}_current"] = current
        for label, width in WINDOWS_MS.items():
            avg = mean_between(series, ts - width, ts)
            prev = mean_between(series, ts - 2 * width, ts - width)
            row[f"{name}_mean_{label}"] = avg
            row[f"{name}_delta_{label}"] = avg - prev
            row[f"{name}_ratio_{label}"] = (avg + 1.0) / (prev + 1.0)
        row[f"{name}_current_vs_24h"] = (current + 1.0) / (row[f"{name}_mean_24h"] + 1.0)
    return row


def build_panel() -> tuple[list[dict], dict]:
    positive_events = load_positive_events()
    rows: list[dict] = []
    meta = {"positive_events": {coin: len(times) for coin, times in positive_events.items()}, "negative_controls": {}}
    for coin, event_times in positive_events.items():
        series = load_coin_series(coin)
        timeline = sorted(set(series["tweets"][0]) & set(series["users"][0]) & set(series["sentiment"][0]))
        event_set = set(event_times)
        for ts in event_times:
            row = features_for(coin, ts, series)
            row["label"] = 1
            rows.append(row)

        candidates = []
        for ts in timeline:
            pos = bisect_left(event_times, ts)
            nearest = []
            if pos < len(event_times):
                nearest.append(abs(event_times[pos] - ts))
            if pos > 0:
                nearest.append(abs(event_times[pos - 1] - ts))
            if nearest and min(nearest) <= EXCLUSION_MS:
                continue
            candidates.append(ts)
        stride = max(1, len(candidates) // max(1, len(event_times) * NEGATIVE_MULTIPLE))
        sampled = candidates[::stride][: len(event_times) * NEGATIVE_MULTIPLE]
        meta["negative_controls"][coin] = len(sampled)
        for ts in sampled:
            row = features_for(coin, ts, series)
            row["label"] = 0
            rows.append(row)
    rows.sort(key=lambda row: (row["timestamp"], row["coin"], row["label"]))
    return rows, meta


def split_rows(rows: list[dict]) -> dict[str, list[dict]]:
    n = len(rows)
    return {
        "train": rows[: int(n * 0.60)],
        "calibration": rows[int(n * 0.60) : int(n * 0.80)],
        "test": rows[int(n * 0.80) :],
    }


def candidate_rules(train: list[dict]) -> list[dict]:
    numeric_keys = [key for key, value in train[0].items() if isinstance(value, (int, float)) and key not in {"timestamp", "label"}]
    rules = []
    positives = [row for row in train if row["label"] == 1]
    negatives = [row for row in train if row["label"] == 0]
    for key in numeric_keys:
        pos_values = [row[key] for row in positives]
        neg_values = [row[key] for row in negatives]
        if not pos_values or not neg_values:
            continue
        direction = "ge" if statistics.mean(pos_values) >= statistics.mean(neg_values) else "le"
        sorted_vals = sorted(row[key] for row in train)
        for q in (0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.92, 0.95, 0.97):
            threshold = sorted_vals[min(len(sorted_vals) - 1, int(q * (len(sorted_vals) - 1)))]
            if direction == "le":
                threshold = sorted_vals[min(len(sorted_vals) - 1, int((1 - q) * (len(sorted_vals) - 1)))]
            def pred(row, k=key, t=threshold, d=direction):
                return row[k] >= t if d == "ge" else row[k] <= t
            train_stats = stats(train, pred)
            if train_stats["support"] >= MIN_CAL_SUPPORT:
                rules.append({"feature": key, "direction": direction, "threshold": threshold, "train": train_stats})
    rules.sort(key=lambda r: (r["train"]["wilson95_lcb"], r["train"]["precision"], r["train"]["support"]), reverse=True)
    return rules[:100]


def evaluate_rule(rule: dict, split: list[dict]) -> dict:
    key, threshold, direction = rule["feature"], rule["threshold"], rule["direction"]
    return stats(split, lambda row: row[key] >= threshold if direction == "ge" else row[key] <= threshold)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    rows, meta = build_panel()
    splits = split_rows(rows)
    rules = candidate_rules(splits["train"])
    evaluated = []
    for rule in rules:
        cal = evaluate_rule(rule, splits["calibration"])
        test = evaluate_rule(rule, splits["test"])
        accepted = (
            cal["support"] >= MIN_CAL_SUPPORT
            and test["support"] >= MIN_TEST_SUPPORT
            and cal["coverage"] >= MIN_COVERAGE
            and test["coverage"] >= MIN_COVERAGE
            and cal["wilson95_lcb"] >= MIN_WILSON
            and test["wilson95_lcb"] >= MIN_WILSON
        )
        evaluated.append({**rule, "calibration": cal, "test": test, "accepted_95": accepted})
    evaluated.sort(
        key=lambda r: (
            r["accepted_95"],
            min(r["calibration"]["wilson95_lcb"], r["test"]["wilson95_lcb"]),
            min(r["calibration"]["coverage"], r["test"]["coverage"]),
            r["test"]["support"],
        ),
        reverse=True,
    )
    best = evaluated[0] if evaluated else None
    accepted = bool(best and best["accepted_95"])
    gate_result = "accepted_mehrnoom_twitter_social_manipulation_95" if accepted else "blocked_mehrnoom_twitter_social_below_95"
    report = {
        "run_id": RUN_ID,
        "candidate_regime": "Manipulation",
        "evidence_class": "direct_event_social_positive_attempts_with_same_coin_twitter_non_event_controls",
        "source": {
            "repo": "https://github.com/Mehrnoom/Cryptocurrency-Pump-Dump",
            "paper": "https://arxiv.org/abs/1902.03110",
            "sparse_checkout": str(SOURCE_ROOT),
            "raw_committed_to_repo": False,
            "full_checkout_attempt": "failed_no_space_left_on_device_then_cleaned",
        },
        "panel": {
            "coins": list(COINS),
            "rows": len(rows),
            "positives": sum(row["label"] for row in rows),
            "negatives": sum(1 for row in rows if row["label"] == 0),
            "positive_events": meta["positive_events"],
            "negative_controls": meta["negative_controls"],
            "split_rows": {name: len(split) for name, split in splits.items()},
            "split_positives": {name: sum(row["label"] for row in split) for name, split in splits.items()},
            "negative_control_policy": "same coin Twitter timestamps outside +/-6h of classified pump attempts, deterministic 3x sampling",
        },
        "gate_contract": {
            "min_calibration_support": MIN_CAL_SUPPORT,
            "min_test_support": MIN_TEST_SUPPORT,
            "min_coverage": MIN_COVERAGE,
            "min_wilson95_lcb": MIN_WILSON,
            "thresholds_relaxed": False,
            "future_or_target_leakage_allowed": False,
        },
        "best_rule": best,
        "leaderboard_top20": evaluated[:20],
        "decision": {
            "gate_result": gate_result,
            "accepted_95": accepted,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "fresh_calibration_rerun": True,
            "trade_usable": False,
            "blocker": None if accepted else "classified pump attempts plus Twitter social aggregates did not reach unchanged held-out Wilson95 and coverage gates",
            "next_action": "Acquire stronger direct order-lifecycle/L2/L3/MBO/social/on-chain positives and negatives; do not treat positive-only social event lists as sufficient without robust controls.",
        },
    }
    report_json = OUT_DIR / "mehrnoom_twitter_social_direct_gate_report.json"
    report_md = OUT_DIR / "mehrnoom_twitter_social_direct_gate_report.md"
    summary_csv = OUT_DIR / "mehrnoom_twitter_social_direct_gate_summary.csv"
    assertions = CHECK_DIR / "mehrnoom_twitter_social_direct_gate_assertions.out"
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    with summary_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["rank", "feature", "direction", "threshold", "cal_lcb", "test_lcb", "cal_support", "test_support", "cal_coverage", "test_coverage", "accepted_95"])
        writer.writeheader()
        for idx, rule in enumerate(evaluated[:50], 1):
            writer.writerow({
                "rank": idx,
                "feature": rule["feature"],
                "direction": rule["direction"],
                "threshold": rule["threshold"],
                "cal_lcb": rule["calibration"]["wilson95_lcb"],
                "test_lcb": rule["test"]["wilson95_lcb"],
                "cal_support": rule["calibration"]["support"],
                "test_support": rule["test"]["support"],
                "cal_coverage": rule["calibration"]["coverage"],
                "test_coverage": rule["test"]["coverage"],
                "accepted_95": rule["accepted_95"],
            })
    best_lines = []
    if best:
        best_lines = [
            f"- Rule: `{best['feature']} {best['direction']} {best['threshold']}`.",
            f"- Calibration Wilson95 / support / coverage: `{best['calibration']['wilson95_lcb']:.6f}` / `{best['calibration']['support']}` / `{best['calibration']['coverage']:.6f}`.",
            f"- Test Wilson95 / support / coverage: `{best['test']['wilson95_lcb']:.6f}` / `{best['test']['support']}` / `{best['test']['coverage']:.6f}`.",
        ]
    report_md.write_text("\n".join([
        "# Mehrnoom Twitter Social Direct Manipulation Gate",
        "",
        f"Run: `{RUN_ID}`",
        "",
        "Source: sparse checkout of `Mehrnoom/Cryptocurrency-Pump-Dump`; raw sparse data stayed under `/private/tmp/ict-regime-mehrnoom-pumpdump-sparse` and was not committed.",
        "",
        "Target: direct-input-gated `Manipulation` from classified Telegram pump attempts for `BTC` and `ADA`, with same-coin Twitter non-event timestamp controls outside +/-6h of classified attempts.",
        "",
        f"Panel rows: `{len(rows)}`; positives `{report['panel']['positives']}`; negatives `{report['panel']['negatives']}`.",
        "",
        "Best rule:",
        *best_lines,
        "",
        f"Gate result: `{gate_result}`. Accepted 95: `{str(accepted).lower()}`. Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.",
        "",
    ]) + "\n")
    assertions.write_text("\n".join([
        f"gate_result={gate_result}",
        f"accepted_95={str(accepted).lower()}",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_committed_to_repo=false",
        f"rows={len(rows)}",
        f"positives={report['panel']['positives']}",
        f"negatives={report['panel']['negatives']}",
        f"best_cal_lcb={best['calibration']['wilson95_lcb']:.6f}" if best else "best_cal_lcb=0.000000",
        f"best_test_lcb={best['test']['wilson95_lcb']:.6f}" if best else "best_test_lcb=0.000000",
    ]) + "\n")
    print(json.dumps({"gate_result": gate_result, "accepted_95": accepted, "report": repo_rel(report_json)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
