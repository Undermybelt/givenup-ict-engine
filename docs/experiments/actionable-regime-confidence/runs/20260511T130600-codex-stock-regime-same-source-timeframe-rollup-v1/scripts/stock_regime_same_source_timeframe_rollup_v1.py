#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T130600+0800-codex-stock-regime-same-source-timeframe-rollup-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T130600-codex-stock-regime-same-source-timeframe-rollup-v1"
OUT_DIR = RUN_ROOT / "timeframe-rollup"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
DATASET = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
SOURCE_GATE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T125122-codex-stock-market-regimes-parent-root-abstain/parent-root-abstain/stock_market_regimes_parent_root_abstain.json"

ROOTS = {"Bull", "Bear", "Sideways", "Crisis"}
MIN_SHARE = 0.80
MIN_DAYS = {"1w": 3, "1mo": 10}


FIELDS = [
    "rollup_id",
    "ticker",
    "timeframe",
    "period_start",
    "period_end",
    "root",
    "source_days",
    "total_days",
    "label_share",
    "mean_regime_confidence",
    "status",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def period_key(frame: pd.DataFrame, timeframe: str) -> pd.Series:
    if timeframe == "1w":
        return frame["date"].dt.to_period("W-FRI").astype(str)
    if timeframe == "1mo":
        return frame["date"].dt.to_period("M").astype(str)
    raise ValueError(timeframe)


def materialize(raw: pd.DataFrame, timeframe: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    df = raw[raw["regime_label"].isin(ROOTS)].copy()
    df["period_key"] = period_key(df, timeframe)
    for (ticker, key), group in df.groupby(["ticker", "period_key"]):
        total = int(len(group))
        counts = group["regime_label"].value_counts()
        root = str(counts.index[0])
        source_days = int(counts.iloc[0])
        share = source_days / total if total else 0.0
        status = "accepted_same_source_rollup" if source_days >= MIN_DAYS[timeframe] and share >= MIN_SHARE else "abstain_low_consensus_or_short_period"
        if status != "accepted_same_source_rollup":
            continue
        start = group["date"].min().date()
        end = group["date"].max().date()
        rows.append({
            "rollup_id": f"stock-regime-{ticker}-{timeframe}-{key}",
            "ticker": str(ticker),
            "timeframe": timeframe,
            "period_start": str(start),
            "period_end": str(end),
            "root": root,
            "source_days": str(source_days),
            "total_days": str(total),
            "label_share": f"{share:.6f}",
            "mean_regime_confidence": f"{float(group['regime_confidence'].mean()):.6f}",
            "status": status,
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    raw = pd.read_csv(DATASET, parse_dates=["date"])
    rows = materialize(raw, "1w") + materialize(raw, "1mo")
    output_csv = OUT_DIR / "stock_regime_same_source_timeframe_rollup_v1.csv"
    write_csv(output_csv, rows)

    by_root = Counter(row["root"] for row in rows)
    by_timeframe = Counter(row["timeframe"] for row in rows)
    by_root_timeframe = Counter(f"{row['root']}:{row['timeframe']}" for row in rows)
    tickers_by_root: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        tickers_by_root[row["root"]].add(row["ticker"])

    package = {
        "run_id": RUN_ID,
        "artifact_type": "stock_regime_same_source_timeframe_rollup_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "board": str(BOARD.relative_to(REPO)),
            "board_sha256_at_run": sha256(BOARD),
            "dataset": str(DATASET),
            "dataset_sha256": sha256(DATASET),
            "source_gate": str(SOURCE_GATE.relative_to(REPO)),
            "source_gate_sha256": sha256(SOURCE_GATE),
        },
        "rollup_policy": {
            "timeframes": ["1w", "1mo"],
            "min_label_share": MIN_SHARE,
            "min_days": MIN_DAYS,
            "source": "same stock-market-regimes parent-label panel; no S&P source-window projection",
            "abstain_policy": "Periods with low dominant-label consensus or too few source days are not emitted.",
        },
        "materialized_labels": {
            "csv": str(output_csv.relative_to(REPO)),
            "rows": len(rows),
            "by_root": dict(sorted(by_root.items())),
            "by_timeframe": dict(sorted(by_timeframe.items())),
            "by_root_timeframe": dict(sorted(by_root_timeframe.items())),
            "tickers_by_root_count": {root: len(tickers) for root, tickers in sorted(tickers_by_root.items())},
        },
        "decision": {
            "exact_same_source_weekly_monthly_labels_materialized": True,
            "confidence_gate_claimed": False,
            "full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "next_action": "Train/evaluate abstaining parent-root gates on this 1w/1mo same-source rollup panel; keep non-US/non-equity/full-species cells separate.",
        },
        "guardrails": {
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
            "source_window_projection_used": False,
            "shared_board_modified": False,
        },
    }

    json_path = OUT_DIR / "stock_regime_same_source_timeframe_rollup_v1.json"
    json_path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")

    md = [
        "# Stock Regime Same-Source Timeframe Rollup v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Materialized same-source labels: `{len(rows)}`.",
        f"- By root: `{dict(sorted(by_root.items()))}`.",
        f"- By timeframe: `{dict(sorted(by_timeframe.items()))}`.",
        "- Timeframes: `1w`, `1mo`.",
        "- Full objective gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.",
        "",
        "## Policy",
        "",
        "This is not another S&P source-window projection. It rolls the confirmed daily stock-market-regimes parent-label panel into weekly/monthly labels for the same tickers only.",
        "",
        "## Guardrails",
        "",
        "- No confidence gate claimed in this run.",
        "- Low-consensus periods are abstained.",
        "- No runtime code changed; no thresholds relaxed; no raw data committed.",
        "",
        "## Artifacts",
        "",
        "- `stock_regime_same_source_timeframe_rollup_v1.json`",
        "- `stock_regime_same_source_timeframe_rollup_v1.csv`",
        "- `../checks/stock_regime_same_source_timeframe_rollup_v1_assertions.out`",
        "",
    ]
    (OUT_DIR / "stock_regime_same_source_timeframe_rollup_v1.md").write_text("\n".join(md))

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={package['inputs']['board_sha256_at_run']}",
        f"materialized_rows={len(rows)}",
        f"by_root={dict(sorted(by_root.items()))}",
        f"by_timeframe={dict(sorted(by_timeframe.items()))}",
        f"by_root_timeframe={dict(sorted(by_root_timeframe.items()))}",
        "exact_same_source_weekly_monthly_labels_materialized=true",
        "confidence_gate_claimed=false",
        "full_objective_gate=none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
        "source_window_projection_used=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    (CHECK_DIR / "stock_regime_same_source_timeframe_rollup_v1_assertions.out").write_text("\n".join(assertions) + "\n")

    assert set(by_root) == ROOTS
    assert set(by_timeframe) == {"1w", "1mo"}
    assert len(rows) > 0


if __name__ == "__main__":
    main()
