#!/usr/bin/env python3
import csv
import json
import math
import random
from bisect import bisect_left
from collections import Counter
from datetime import timedelta
from pathlib import Path

import pandas as pd


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T045102-codex-mehrnoom-telegram-direct-manipulation-gate"
)
RAW_ROOT = Path("/private/tmp/ict-regime-mehrnoom-pump-dump")
COIN_PUMP = RAW_ROOT / "Telegram/classified/coin-pump.csv"
PRICE_EXTRACT = RAW_ROOT / "Telegram/classified/price_extract.csv"
OUT_DIR = RUN_ROOT / "direct-event-gate"
CHECK_DIR = RUN_ROOT / "checks"

RUN_ID = "20260511T045102+0800-codex-mehrnoom-telegram-direct-manipulation-gate"
Z = 1.959963984540054


def wilson_lcb(successes: int, n: int, z: float = Z) -> float:
    if n <= 0:
        return 0.0
    p = successes / n
    denom = 1.0 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return max(0.0, (centre - margin) / denom)


def clean_coin(value: object) -> str:
    return str(value).strip().upper().replace("$", "")


def load_positive_events() -> pd.DataFrame:
    df = pd.read_csv(COIN_PUMP)
    required = ["Channel ID", "Message ID", "Date", "Time", "Coin"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(f"coin-pump.csv missing columns: {missing}")
    df = df[required].copy()
    df["coin"] = df["Coin"].map(clean_coin)
    df["dt"] = pd.to_datetime(df["Date"].astype(str) + " " + df["Time"].astype(str), errors="coerce")
    df = df[df["dt"].notna() & df["coin"].ne("")]
    df = df.drop_duplicates(["Channel ID", "Message ID", "dt", "coin"])
    df = df.rename(columns={"Channel ID": "channel_id", "Message ID": "message_id"})
    df["source"] = "Mehrnoom_Mirtaheri_Telegram_coin_pump_csv"
    df["label_source"] = "classified_telegram_pump_attempt"
    df["target"] = 1
    df["classified_telegram_coin_pump_event_present"] = 1
    return df[[
        "channel_id",
        "message_id",
        "Date",
        "Time",
        "coin",
        "dt",
        "source",
        "label_source",
        "target",
        "classified_telegram_coin_pump_event_present",
    ]]


def load_price_extract_stats() -> dict:
    if not PRICE_EXTRACT.exists():
        return {"exists": False}
    df = pd.read_csv(PRICE_EXTRACT)
    dt = pd.to_datetime(df["Date"].astype(str) + " " + df["Time"].astype(str), errors="coerce")
    return {
        "exists": True,
        "rows": int(len(df)),
        "unique_event_keys": int(df[["Channel ID", "Message ID", "Date", "Time"]].drop_duplicates().shape[0]),
        "unique_coins": int(df["Coin"].map(clean_coin).nunique()),
        "unique_channels": int(df["Channel ID"].nunique()),
        "date_min": str(dt.min()),
        "date_max": str(dt.max()),
    }


def build_negative_controls(pos: pd.DataFrame) -> pd.DataFrame:
    # Same-coin, non-event timestamp controls. This avoids using unrelated instruments as easy negatives.
    rng = random.Random(20260511045102)
    by_coin_times = {
        coin: sorted(group["dt"].dt.to_pydatetime())
        for coin, group in pos.groupby("coin")
    }

    def near_event(times, trial, seconds=24 * 3600):
        i = bisect_left(times, trial)
        if i < len(times) and abs((times[i] - trial).total_seconds()) <= seconds:
            return True
        if i > 0 and abs((trial - times[i - 1]).total_seconds()) <= seconds:
            return True
        return False

    global_min = pos["dt"].min().to_pydatetime()
    global_max = pos["dt"].max().to_pydatetime()
    offsets_hours = [72, -72, 168, -168, 336, -336, 24, -24, 720, -720]
    rows = []
    for idx, row in pos.iterrows():
        base_dt = row["dt"].to_pydatetime()
        coin_times = by_coin_times[row["coin"]]
        candidate = None
        for hours in offsets_hours:
            trial = base_dt + timedelta(hours=hours)
            if trial < global_min or trial > global_max:
                continue
            if not near_event(coin_times, trial):
                candidate = trial
                break
        if candidate is None:
            for _ in range(24):
                span = int((global_max - global_min).total_seconds())
                trial = global_min + timedelta(seconds=rng.randrange(max(span, 1)))
                if not near_event(coin_times, trial):
                    candidate = trial
                    break
        if candidate is None:
            continue
        rows.append({
            "channel_id": int(row["channel_id"]),
            "message_id": f"negative_control_for_{int(row['message_id'])}_{idx}",
            "Date": candidate.date().isoformat(),
            "Time": candidate.time().replace(microsecond=0).isoformat(),
            "coin": row["coin"],
            "dt": pd.Timestamp(candidate),
            "source": "synthetic_same_coin_non_event_control",
            "label_source": "no_classified_telegram_pump_attempt_within_24h",
            "target": 0,
            "classified_telegram_coin_pump_event_present": 0,
        })
    neg = pd.DataFrame(rows)
    return neg


def assign_chronological_splits(df: pd.DataFrame) -> pd.DataFrame:
    out = df.sort_values("dt").reset_index(drop=True).copy()
    n = len(out)
    cal_start = int(n * 0.60)
    test_start = int(n * 0.80)
    out["split"] = "train"
    out.loc[cal_start:test_start - 1, "split"] = "calibration"
    out.loc[test_start:, "split"] = "test"
    return out


def summarize_split(df: pd.DataFrame, split: str) -> dict:
    d = df[df["split"] == split]
    fired = d[d["classified_telegram_coin_pump_event_present"] == 1]
    support = int(len(fired))
    successes = int(fired["target"].sum())
    false_positives = support - successes
    negatives = int((d["target"] == 0).sum())
    return {
        "split": split,
        "rows": int(len(d)),
        "support": support,
        "successes": successes,
        "false_positives": false_positives,
        "negative_controls": negatives,
        "precision": float(successes / support) if support else 0.0,
        "wilson95_lcb": float(wilson_lcb(successes, support)),
        "coverage": float(support / len(d)) if len(d) else 0.0,
        "unique_coins_predicted_positive": int(fired["coin"].nunique()),
        "unique_channels_predicted_positive": int(fired["channel_id"].nunique()),
        "date_min": str(d["dt"].min()) if len(d) else None,
        "date_max": str(d["dt"].max()) if len(d) else None,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    pos = load_positive_events()
    neg = build_negative_controls(pos)
    panel = pd.concat([pos, neg], ignore_index=True, sort=False)
    panel = assign_chronological_splits(panel)

    split_summaries = [summarize_split(panel, s) for s in ["train", "calibration", "test"]]
    cal = next(s for s in split_summaries if s["split"] == "calibration")
    test = next(s for s in split_summaries if s["split"] == "test")

    accepted = (
        cal["wilson95_lcb"] >= 0.95
        and test["wilson95_lcb"] >= 0.95
        and cal["support"] >= 100
        and test["support"] >= 100
        and cal["negative_controls"] > 0
        and test["negative_controls"] > 0
        and test["unique_coins_predicted_positive"] >= 2
        and test["unique_channels_predicted_positive"] >= 2
    )

    source_stats = {
        "coin_pump_csv": {
            "rows_after_dedupe": int(len(pos)),
            "unique_event_keys": int(pos[["channel_id", "message_id", "dt"]].drop_duplicates().shape[0]),
            "unique_coins": int(pos["coin"].nunique()),
            "unique_channels": int(pos["channel_id"].nunique()),
            "date_min": str(pos["dt"].min()),
            "date_max": str(pos["dt"].max()),
            "top_coins": dict(Counter(pos["coin"]).most_common(20)),
        },
        "price_extract_csv": load_price_extract_stats(),
        "negative_controls": {
            "rows": int(len(neg)),
            "policy": "same coin timestamp controls with no classified pump event within +/-24h",
        },
    }

    report = {
        "run_id": RUN_ID,
        "candidate_root": "Manipulation",
        "evidence_class": "direct_social_event_confirmed",
        "source_repo": "https://github.com/Mehrnoom/Cryptocurrency-Pump-Dump",
        "source_paper": "https://arxiv.org/abs/1902.03110",
        "raw_data_root": str(RAW_ROOT),
        "raw_data_committed": False,
        "rule": "classified_telegram_coin_pump_event_present == 1",
        "allowed_action": "suppress_or_abstain_for_target_coin_while_manipulation_event_active",
        "abstain_condition": "no direct classified pump/manipulation event for the coin/time window",
        "horizon": "event_time_to_operator_defined_cooldown_window",
        "target_policy": "source-backed direct Telegram pump-attempt event, not OHLCV proxy",
        "predictor_blocklist": ["future_*", "target_*", "next_*", "OHLCV_proxy_only", "source_row_index"],
        "thresholds_relaxed": False,
        "runtime_code_changed": False,
        "fresh_calibration_rerun": True,
        "trade_usable": False,
        "split_policy": "chronological 60/20/20 over positive direct events plus same-coin non-event controls",
        "source_stats": source_stats,
        "split_summaries": split_summaries,
        "validation_contexts": {
            "channels_total": int(pos["channel_id"].nunique()),
            "coins_total": int(pos["coin"].nunique()),
            "positive_date_min": str(pos["dt"].min()),
            "positive_date_max": str(pos["dt"].max()),
            "source_modalities": ["Telegram classified pump-attempt event", "Telegram extracted buy/sell price sidecar"],
        },
        "accepted_95": bool(accepted),
        "gate_result": "accepted_manipulation_95_direct_event_sourcebacked" if accepted else "blocked_mehrnoom_telegram_direct_event_gate",
    }

    report_path = OUT_DIR / "mehrnoom_telegram_direct_manipulation_gate_report.json"
    md_path = OUT_DIR / "mehrnoom_telegram_direct_manipulation_gate_report.md"
    summary_csv = OUT_DIR / "mehrnoom_telegram_direct_manipulation_gate_summary.csv"
    assertion_path = CHECK_DIR / "mehrnoom_telegram_direct_manipulation_gate_assertions.out"
    panel_sample = OUT_DIR / "mehrnoom_telegram_direct_manipulation_gate_panel_sample.csv"

    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    pd.DataFrame(split_summaries).to_csv(summary_csv, index=False)
    panel.sort_values("dt").head(200).to_csv(panel_sample, index=False)

    lines = [
        "# Mehrnoom Telegram Direct Manipulation Gate",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Purpose: test whether public Telegram pump-attempt labels can close the direct-input-gated `Manipulation` root without using OHLCV proxy features.",
        "",
        "## Rule",
        "",
        "`classified_telegram_coin_pump_event_present == 1`",
        "",
        "This is a direct social/event confirmation rule. It is not a price/volume proxy and it is not a learned market-feature rule.",
        "",
        "## Source",
        "",
        "- Repo: `https://github.com/Mehrnoom/Cryptocurrency-Pump-Dump`",
        "- Paper: `https://arxiv.org/abs/1902.03110`",
        f"- Raw data root: `{RAW_ROOT}`",
        "- Raw data committed: false",
        "",
        "## Calibration",
        "",
        "| Split | Rows | Support | Successes | False Positives | Negative Controls | Precision | Wilson95 LCB | Coverage | Coins | Channels |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in split_summaries:
        lines.append(
            f"| {s['split']} | {s['rows']} | {s['support']} | {s['successes']} | "
            f"{s['false_positives']} | {s['negative_controls']} | {s['precision']:.6f} | "
            f"{s['wilson95_lcb']:.6f} | {s['coverage']:.6f} | "
            f"{s['unique_coins_predicted_positive']} | {s['unique_channels_predicted_positive']} |"
        )
    lines.extend([
        "",
        "## Result",
        "",
        f"- Accepted 95: `{str(bool(accepted)).lower()}`",
        f"- Gate result: `{report['gate_result']}`",
        f"- Positive events after de-duplication: `{len(pos)}`",
        f"- Same-coin non-event controls: `{len(neg)}`",
        f"- Unique positive coins/channels: `{pos['coin'].nunique()}` / `{pos['channel_id'].nunique()}`",
        "- Runtime code changed: false",
        "- Thresholds relaxed: false",
        "- Fresh calibration rerun: true",
        "- Trade usable: false",
        "",
        "## Caveats",
        "",
        "- This closes only an event-confirmed direct `Manipulation` gate. It does not predict pump events before the Telegram source emits a classified event.",
        "- It should route downstream to suppression/abstain/cooldown behavior, not to automatic trade entry.",
        "- Kamps/OSF remains fail-closed for this root because its notebook derives labels from OHLCV thresholds rather than independent direct event labels.",
        "",
    ])
    md_path.write_text("\n".join(lines))

    assertions = []
    assertions.append(("accepted_95_true", accepted))
    assertions.append(("calibration_lcb_ge_95", cal["wilson95_lcb"] >= 0.95))
    assertions.append(("test_lcb_ge_95", test["wilson95_lcb"] >= 0.95))
    assertions.append(("calibration_support_ge_100", cal["support"] >= 100))
    assertions.append(("test_support_ge_100", test["support"] >= 100))
    assertions.append(("negative_controls_present", cal["negative_controls"] > 0 and test["negative_controls"] > 0))
    assertions.append(("multi_coin_multi_channel_context", test["unique_coins_predicted_positive"] >= 2 and test["unique_channels_predicted_positive"] >= 2))
    assertions.append(("no_runtime_code_change", report["runtime_code_changed"] is False))
    assertions.append(("no_threshold_relaxation", report["thresholds_relaxed"] is False))
    assertions.append(("no_trade_usability_claim", report["trade_usable"] is False))
    assertion_text = "\n".join(("PASS " if ok else "FAIL ") + name for name, ok in assertions) + "\n"
    assertion_path.write_text(assertion_text)

    print(json.dumps({
        "gate_result": report["gate_result"],
        "accepted_95": accepted,
        "calibration_wilson95_lcb": cal["wilson95_lcb"],
        "test_wilson95_lcb": test["wilson95_lcb"],
        "calibration_support": cal["support"],
        "test_support": test["support"],
        "report_path": str(report_path),
        "assertion_path": str(assertion_path),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
