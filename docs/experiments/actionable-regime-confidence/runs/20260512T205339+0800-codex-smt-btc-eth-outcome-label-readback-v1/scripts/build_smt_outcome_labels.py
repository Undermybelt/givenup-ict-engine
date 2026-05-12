#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[4]
SOURCE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T204643+0800-codex-smt-btc-eth-provider-backed-observation-v1"
EVENTS = SOURCE / "summaries/smt_btc_eth_provider_observation_events.csv"
MANIFEST = SOURCE / "inputs/provider_file_manifest.csv"


def parse_ts(raw: str) -> datetime:
    dt = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def read_candles(path: Path) -> dict[datetime, dict[str, float]]:
    out: dict[datetime, dict[str, float]] = {}
    for row in read_rows(path):
        raw_ts = row.get("date") or row.get("ts")
        if not raw_ts:
            continue
        try:
            ts = parse_ts(raw_ts)
            out[ts] = {k: float(row[k]) for k in ["open", "high", "low", "close"]}
        except Exception:
            continue
    return out


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="") as f:
        if not rows:
            return
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def favorable(signal: str, ret: float) -> bool:
    if signal == "bullish_smt":
        return ret > 0
    if signal == "bearish_smt":
        return ret < 0
    return False


def summarize(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row[key])].append(row)
    out = []
    for name, vals in sorted(groups.items()):
        with_6h = [v for v in vals if v["forward_6h_return"] != ""]
        with_12h = [v for v in vals if v["forward_12h_return"] != ""]
        out.append(
            {
                key: name,
                "event_count": len(vals),
                "outcome_6h_count": len(with_6h),
                "hit_rate_6h": round(mean(1.0 if v["favorable_6h"] else 0.0 for v in with_6h), 6) if with_6h else None,
                "mean_forward_6h_return": round(mean(float(v["forward_6h_return"]) for v in with_6h), 8) if with_6h else None,
                "outcome_12h_count": len(with_12h),
                "hit_rate_12h": round(mean(1.0 if v["favorable_12h"] else 0.0 for v in with_12h), 6) if with_12h else None,
                "mean_forward_12h_return": round(mean(float(v["forward_12h_return"]) for v in with_12h), 8) if with_12h else None,
            }
        )
    return out


def main() -> int:
    manifest = {row["provider_id"]: row for row in read_rows(MANIFEST)}
    candles_by_provider = {provider: read_candles(REPO / row["btc_path"]) for provider, row in manifest.items()}
    labelled = []
    for event in read_rows(EVENTS):
        provider = event["provider_id"]
        candles = candles_by_provider[provider]
        ts = parse_ts(event["event_time"])
        cur = candles.get(ts)
        row = dict(event)
        row["forward_6h_return"] = ""
        row["forward_12h_return"] = ""
        row["favorable_6h"] = ""
        row["favorable_12h"] = ""
        row["outcome_fail_closed_reason"] = "missing_event_or_forward_candle"
        if cur:
            for horizon in (6, 12):
                future_ts = ts.replace(hour=ts.hour)  # keep explicit before timedelta import avoidance below
                from datetime import timedelta

                future = candles.get(future_ts + timedelta(hours=horizon))
                if future and cur["close"]:
                    ret = (future["close"] - cur["close"]) / cur["close"]
                    row[f"forward_{horizon}h_return"] = round(ret, 8)
                    row[f"favorable_{horizon}h"] = favorable(event["smt_signal"], ret)
                    row["outcome_fail_closed_reason"] = "confirmation_only_missing_mss_cisd_displacement_pda_context"
        labelled.append(row)

    provider_summary = summarize(labelled, "provider_id")
    regime_summary = summarize(labelled, "regime_label")
    outcome_6h_count = sum(1 for row in labelled if row["forward_6h_return"] != "")
    outcome_12h_count = sum(1 for row in labelled if row["forward_12h_return"] != "")
    with_6h = [row for row in labelled if row["forward_6h_return"] != ""]
    with_12h = [row for row in labelled if row["forward_12h_return"] != ""]
    summary = {
        "factor_name": "smt_relationship_resolver",
        "factor_version": "2026-05-12.outcome-label-readback.v1",
        "source_observation_root": str(SOURCE.relative_to(REPO)),
        "branch_path": "Transition -> LiquiditySweepConfirmationFailure -> smt_divergence_confirmation_only -> smt_relationship_resolver:btc_eth_1h_v1",
        "aggregate": {
            "event_count": len(labelled),
            "outcome_6h_count": outcome_6h_count,
            "outcome_12h_count": outcome_12h_count,
            "hit_rate_6h": round(mean(1.0 if row["favorable_6h"] else 0.0 for row in with_6h), 6) if with_6h else None,
            "hit_rate_12h": round(mean(1.0 if row["favorable_12h"] else 0.0 for row in with_12h), 6) if with_12h else None,
            "mean_forward_6h_return": round(mean(float(row["forward_6h_return"]) for row in with_6h), 8) if with_6h else None,
            "mean_forward_12h_return": round(mean(float(row["forward_12h_return"]) for row in with_12h), 8) if with_12h else None,
        },
        "provider_summary": provider_summary,
        "regime_summary": regime_summary,
        "quality_gate": {
            "outcome_labels_present": outcome_6h_count > 0,
            "mss_cisd_displacement_pda_present": False,
            "observation_quality_weight": 0.25 if outcome_6h_count > 0 else 0.0,
            "learning_quality_weight": 0.0,
            "auto_quant_dispatch_allowed": False,
            "pre_bayes_filter_allowed": False,
            "bbn_learning_allowed": False,
            "catboost_learning_allowed": False,
            "execution_tree_branch_weight_update_allowed": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "fail_closed_reason": "outcome_labels_exist_but_entry_context_missing_mss_cisd_displacement_pda",
        },
    }
    write_csv(ROOT / "summaries/smt_btc_eth_outcome_labels.csv", labelled)
    write_csv(ROOT / "summaries/smt_btc_eth_outcome_provider_summary.csv", provider_summary)
    write_csv(ROOT / "summaries/smt_btc_eth_outcome_regime_summary.csv", regime_summary)
    (ROOT / "summaries/smt_btc_eth_outcome_label_readback_v1.json").write_text(json.dumps(summary, indent=2) + "\n")
    assert len(labelled) == 127
    assert outcome_6h_count > 100
    assert summary["quality_gate"]["learning_quality_weight"] == 0.0
    assert summary["quality_gate"]["pre_bayes_filter_allowed"] is False
    print(json.dumps(summary["aggregate"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
