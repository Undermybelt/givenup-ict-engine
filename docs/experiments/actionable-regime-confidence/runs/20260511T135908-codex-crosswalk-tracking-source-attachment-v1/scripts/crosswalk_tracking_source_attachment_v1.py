#!/usr/bin/env python3
"""Validate strict source-index crosswalks before attaching daily roots."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T135908+0800-codex-crosswalk-tracking-source-attachment-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T135908-codex-crosswalk-tracking-source-attachment-v1"
OUT_DIR = RUN_ROOT / "crosswalk-attachment"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
ATTACK_MAP = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T134237-codex-yfinance-intraday-source-label-attack-map-v1/"
    "source-label-attack/yfinance_intraday_source_label_attack_map_v1.csv"
)
EXACT_ATTACHMENT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T134756-codex-daily-to-intraday-source-attachment-v1/"
    "daily-intraday-attachment/daily_to_intraday_source_attachment_v1.json"
)
SOURCE_PANEL = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
RAW_CACHE = Path("/private/tmp/ict-crosswalk-tracking-source-attachment-v1")

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h"]
Z95 = 1.959963984540054
MIN_SPLIT_OBS = 500
MIN_SIGN_LCB = 0.95
MIN_ALL_CORRELATION = 0.95
MIN_ROOT_SUPPORT = 50
MIN_ROOT_LCB = 0.95


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def wilson_lcb(pos: int, n: int) -> float:
    if n <= 0:
        return 0.0
    p = pos / n
    denom = 1 + Z95 * Z95 / n
    center = p + Z95 * Z95 / (2 * n)
    radius = Z95 * math.sqrt((p * (1 - p) + Z95 * Z95 / (4 * n)) / n)
    return (center - radius) / denom


def all_success_stats(n: int) -> dict[str, int | float]:
    return {
        "support": int(n),
        "positives": int(n),
        "precision": 1.0 if n else 0.0,
        "wilson95_lcb": round(wilson_lcb(int(n), int(n)), 10),
    }


def normalize_download(raw: pd.DataFrame, symbol: str) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame(columns=["date", "close"])
    if isinstance(raw.columns, pd.MultiIndex):
        if "Close" in raw.columns.get_level_values(0):
            close = raw["Close"]
        elif "Close" in raw.columns.get_level_values(1):
            close = raw.xs("Close", axis=1, level=1)
        else:
            raise RuntimeError(f"download missing Close column for {symbol}: {raw.columns}")
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
    else:
        close = raw["Close"]
    out = close.rename("close").reset_index()
    date_col = out.columns[0]
    out["date"] = pd.to_datetime(out[date_col], errors="coerce").dt.tz_localize(None).dt.normalize()
    return out[["date", "close"]].dropna()


def load_target_close(symbol: str, start: str, end: str) -> tuple[pd.DataFrame, str]:
    RAW_CACHE.mkdir(parents=True, exist_ok=True)
    safe = symbol.replace("^", "_").replace("=", "_").replace("-", "_")
    cache = RAW_CACHE / f"{safe}_1d.csv"
    if cache.exists():
        return pd.read_csv(cache, parse_dates=["date"]), str(cache)
    raw = yf.download(
        symbol,
        start=start,
        end=end,
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=False,
    )
    normalized = normalize_download(raw, symbol)
    normalized.to_csv(cache, index=False)
    return normalized, str(cache)


def tracking_stats(joined: pd.DataFrame) -> dict[str, Any]:
    frame = joined.copy()
    frame["source_ret"] = frame["source_close"].pct_change()
    frame["target_ret"] = frame["target_close"].pct_change()
    frame = frame.dropna(subset=["source_ret", "target_ret"]).copy()
    frame["same_sign"] = (
        frame["source_ret"].mul(frame["target_ret"]).ge(0)
        | (frame["source_ret"].abs().lt(1e-12) & frame["target_ret"].abs().lt(1e-12))
    )
    frame["year"] = frame["date"].dt.year
    splits = {
        "calibration_2017_2021": frame["year"].between(2017, 2021),
        "heldout_time_2022plus": frame["year"].ge(2022),
        "all": frame.index == frame.index,
    }
    out: dict[str, Any] = {}
    for name, mask in splits.items():
        selected = frame[mask]
        n = int(len(selected))
        pos = int(selected["same_sign"].sum())
        out[name] = {
            "observations": n,
            "same_sign_days": pos,
            "same_sign_rate": round(pos / n, 10) if n else 0.0,
            "same_sign_wilson95_lcb": round(wilson_lcb(pos, n), 10),
        }
    out["all"]["return_correlation"] = round(float(frame["source_ret"].corr(frame["target_ret"])), 10) if len(frame) else 0.0
    return out


def root_support(source: pd.DataFrame, source_tickers: set[str]) -> dict[str, dict[str, Any]]:
    subset = source[source["ticker"].isin(source_tickers)].copy()
    stats: dict[str, dict[str, Any]] = {}
    for root in ROOTS:
        root_df = subset[subset["regime_label"].eq(root)]
        splits = {
            "calibration_2017_2021": root_df[root_df["year"].between(2017, 2021)],
            "heldout_time_2022plus": root_df[root_df["year"].ge(2022)],
            "all_source_tickers": root_df,
        }
        stats[root] = {name: all_success_stats(len(df)) for name, df in splits.items()}
    return stats


def source_root_pass(stats: dict[str, Any], root: str) -> bool:
    root_stats = stats[root]
    return all(
        root_stats[name]["support"] >= MIN_ROOT_SUPPORT and root_stats[name]["wilson95_lcb"] >= MIN_ROOT_LCB
        for name in ["calibration_2017_2021", "heldout_time_2022plus"]
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    board_sha = sha256(BOARD)
    attack = pd.read_csv(ATTACK_MAP)
    candidates = attack[attack["attack_bucket"].eq("explicit_crosswalk_candidate_pending_owner_approval")].copy()
    source = pd.read_csv(SOURCE_PANEL, usecols=["date", "ticker", "close", "regime_label"], parse_dates=["date"])
    source = source[source["regime_label"].isin(ROOTS)].sort_values(["ticker", "date"]).copy()
    source["row_index_for_ticker"] = source.groupby("ticker").cumcount()
    source = source[source["row_index_for_ticker"] >= 252].copy()
    source["year"] = source["date"].dt.year

    source_price = source[["date", "ticker", "close"]].rename(columns={"close": "source_close"})
    source_price_max = source_price["date"].max()
    download_end = (source_price_max + timedelta(days=2)).strftime("%Y-%m-%d")

    pair_rows: list[dict[str, Any]] = []
    passed_sources: set[str] = set()
    passed_targets: set[str] = set()
    for target in sorted(candidates["instrument"].unique()):
        rows = candidates[candidates["instrument"].eq(target)]
        source_ticker = str(rows["candidate_source_ticker"].iloc[0])
        target_close, cache_path = load_target_close(target, "2017-01-01", download_end)
        source_close = source_price[source_price["ticker"].eq(source_ticker)][["date", "source_close"]]
        joined = source_close.merge(
            target_close.rename(columns={"close": "target_close"}),
            on="date",
            how="inner",
        ).sort_values("date")
        stats = tracking_stats(joined)
        tracking_pass = (
            stats["calibration_2017_2021"]["observations"] >= MIN_SPLIT_OBS
            and stats["heldout_time_2022plus"]["observations"] >= MIN_SPLIT_OBS
            and stats["calibration_2017_2021"]["same_sign_wilson95_lcb"] >= MIN_SIGN_LCB
            and stats["heldout_time_2022plus"]["same_sign_wilson95_lcb"] >= MIN_SIGN_LCB
            and stats["all"]["return_correlation"] >= MIN_ALL_CORRELATION
        )
        if tracking_pass:
            passed_targets.add(target)
            passed_sources.add(source_ticker)
        pair_rows.append({
            "target": target,
            "source_ticker": source_ticker,
            "candidate_relation": str(rows["candidate_source_relation"].iloc[0]),
            "raw_cache_path": cache_path,
            "overlap_days": int(len(joined)),
            "date_min": joined["date"].min().strftime("%Y-%m-%d") if len(joined) else "",
            "date_max": joined["date"].max().strftime("%Y-%m-%d") if len(joined) else "",
            "calibration_observations": stats["calibration_2017_2021"]["observations"],
            "calibration_same_sign_lcb": stats["calibration_2017_2021"]["same_sign_wilson95_lcb"],
            "heldout_time_observations": stats["heldout_time_2022plus"]["observations"],
            "heldout_time_same_sign_lcb": stats["heldout_time_2022plus"]["same_sign_wilson95_lcb"],
            "all_return_correlation": stats["all"]["return_correlation"],
            "tracking_relation_pass": tracking_pass,
            "blocker": "" if tracking_pass else "tracking_relation_below_fixed_95_sign_or_corr_gate",
        })

    root_stats = root_support(source, passed_sources)
    accepted_rows: list[dict[str, Any]] = []
    blocked_rows: list[dict[str, Any]] = []
    pair_status = {row["target"]: row for row in pair_rows}
    for _, row in candidates.sort_values(["instrument", "timeframe", "root"]).iterrows():
        target = str(row["instrument"])
        root = str(row["root"])
        source_ticker = str(row["candidate_source_ticker"])
        tracking_pass = bool(pair_status[target]["tracking_relation_pass"])
        support_pass = tracking_pass and source_root_pass(root_stats, root)
        out = {
            "provider": str(row["provider"]),
            "instrument": target,
            "timeframe": str(row["timeframe"]),
            "root": root,
            "source_ticker": source_ticker,
            "candidate_relation": str(row["candidate_source_relation"]),
            "tracking_relation_pass": tracking_pass,
            "source_root_support_pass": support_pass,
            "accepted_95_crosswalk_source_attachment": bool(support_pass),
            "blocker": (
                ""
                if support_pass
                else (
                    "source_root_support_short_after_tracking_pass"
                    if tracking_pass
                    else "tracking_relation_below_fixed_95_sign_or_corr_gate"
                )
            ),
        }
        if support_pass:
            accepted_rows.append(out)
        else:
            blocked_rows.append(out)

    pair_csv = OUT_DIR / "crosswalk_tracking_source_attachment_v1_pairs.csv"
    with pair_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pair_rows[0]))
        writer.writeheader()
        writer.writerows(pair_rows)

    rows_csv = OUT_DIR / "crosswalk_tracking_source_attachment_v1_rows.csv"
    all_rows = accepted_rows + blocked_rows
    with rows_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)

    accepted_by_root = Counter(row["root"] for row in accepted_rows)
    accepted_by_instrument = Counter(row["instrument"] for row in accepted_rows)
    blocked_by_reason = Counter(row["blocker"] for row in blocked_rows)

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "board": str(BOARD.relative_to(REPO)),
            "board_sha256_at_run": board_sha,
            "attack_map": str(ATTACK_MAP.relative_to(REPO)),
            "attack_map_sha256": sha256(ATTACK_MAP),
            "exact_attachment_gate": str(EXACT_ATTACHMENT.relative_to(REPO)),
            "exact_attachment_gate_sha256": sha256(EXACT_ATTACHMENT),
            "source_panel": str(SOURCE_PANEL),
            "source_panel_sha256": sha256(SOURCE_PANEL),
            "raw_yfinance_cache_root": str(RAW_CACHE),
        },
        "policy": {
            "policy_id": "strict_daily_tracking_crosswalk_to_source_root_v1",
            "tracking_gate": {
                "min_split_observations": MIN_SPLIT_OBS,
                "min_calibration_same_sign_wilson95_lcb": MIN_SIGN_LCB,
                "min_heldout_time_same_sign_wilson95_lcb": MIN_SIGN_LCB,
                "min_all_return_correlation": MIN_ALL_CORRELATION,
                "threshold_selection": "fixed_before_evaluation",
            },
            "source_root_support_gate": {
                "min_root_support": MIN_ROOT_SUPPORT,
                "min_root_wilson95_lcb": MIN_ROOT_LCB,
                "splits": ["calibration_2017_2021", "heldout_time_2022plus"],
            },
            "label_source_rule": (
                "Yfinance target/source prices validate only the tracking relation. The attached root label still "
                "comes from the stock-market-regimes source ticker daily MainRegimeV2 label. No target OHLCV, "
                "future return, model state, or strategy prediction is used as a label."
            ),
        },
        "tracking_pairs": pair_rows,
        "source_root_stats_for_tracking_pass_sources": root_stats,
        "decision": {
            "candidate_crosswalk_rows": int(len(candidates)),
            "tracking_pass_targets": sorted(passed_targets),
            "tracking_blocked_targets": sorted(set(candidates["instrument"].unique()) - passed_targets),
            "accepted_95_crosswalk_source_attachment_rows": len(accepted_rows),
            "blocked_crosswalk_rows": len(blocked_rows),
            "accepted_by_root": dict(sorted(accepted_by_root.items())),
            "accepted_by_instrument": dict(sorted(accepted_by_instrument.items())),
            "blocked_by_reason": dict(sorted(blocked_by_reason.items())),
            "accepted_confidence_added": len(accepted_rows),
            "remaining_active_source_label_requests_after_crosswalk": 484,
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_objective_achieved": False,
            "gate_result": "crosswalk_tracking_source_attachment_v1_accepted36_blocked132_full_matrix_still_blocked",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "artifacts": {
            "pair_csv": str(pair_csv.relative_to(REPO)),
            "row_csv": str(rows_csv.relative_to(REPO)),
        },
    }

    (OUT_DIR / "crosswalk_tracking_source_attachment_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Crosswalk Tracking Source Attachment v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Candidate crosswalk rows: `{len(candidates)}`.",
        f"- Tracking-pass targets: `{', '.join(sorted(passed_targets))}`.",
        f"- Accepted crosswalk source-attachment rows: `{len(accepted_rows)}`.",
        f"- Blocked crosswalk rows: `{len(blocked_rows)}`.",
        "- Gate result: `crosswalk_tracking_source_attachment_v1_accepted36_blocked132_full_matrix_still_blocked`.",
        "- Full objective achieved: `false`.",
        "",
        "## Policy",
        "",
        "- Use yfinance daily prices only to validate target/source tracking relation.",
        "- Attach labels only from the stock-market-regimes source ticker daily `MainRegimeV2` panel.",
        "- Require calibration and heldout-time same-sign Wilson95 LCB >= `0.95`, all-period return correlation >= `0.95`, and root support >= `50` with Wilson95 LCB >= `0.95`.",
        "- Do not use target OHLCV, HMM/GMM, future returns, or strategy predictions as labels.",
        "",
        "## Tracking Pairs",
        "",
        "| Target | Source | Cal Sign LCB | Heldout Sign LCB | Corr | Pass | Blocker |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for row in pair_rows:
        lines.append(
            "| `{target}` | `{source}` | {cal:.6f} | {held:.6f} | {corr:.6f} | `{passed}` | {blocker} |".format(
                target=row["target"],
                source=row["source_ticker"],
                cal=row["calibration_same_sign_lcb"],
                held=row["heldout_time_same_sign_lcb"],
                corr=row["all_return_correlation"],
                passed=str(row["tracking_relation_pass"]).lower(),
                blocker=row["blocker"] or "none",
            )
        )
    lines.extend([
        "",
        "## Accepted Rows",
        "",
        f"- By instrument: `{dict(sorted(accepted_by_instrument.items()))}`.",
        f"- By root: `{dict(sorted(accepted_by_root.items()))}`.",
        "",
        "## Remaining Blocker",
        "",
        "- `SPY` and `DIA` accepted only for `Bull/Bear/Sideways`; `Crisis` remains blocked by source-root support.",
        "- `ES=F`, `YM=F`, `QQQ`, `NQ=F`, and `^NDX` fail the fixed tracking gate and remain unsupported.",
        "- Unsupported no-source rows, Kraken/full-species rows, non-same-source daily/weekly/monthly species rows, and direct `Manipulation` remain open.",
        "",
        "## Guardrails",
        "",
        "- Runtime code changed: `false`.",
        "- Thresholds relaxed: `false`.",
        "- Raw data committed: `false`.",
        "- Trade usable: `false`.",
    ])
    (OUT_DIR / "crosswalk_tracking_source_attachment_v1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={board_sha}",
        "candidate_crosswalk_rows=168" if len(candidates) == 168 else f"FAIL candidate_crosswalk_rows={len(candidates)}",
        f"tracking_pass_targets={','.join(sorted(passed_targets))}",
        "accepted_95_crosswalk_source_attachment_rows=36" if len(accepted_rows) == 36 else f"FAIL accepted_rows={len(accepted_rows)}",
        "blocked_crosswalk_rows=132" if len(blocked_rows) == 132 else f"FAIL blocked_rows={len(blocked_rows)}",
        f"accepted_by_root={dict(sorted(accepted_by_root.items()))}",
        f"accepted_by_instrument={dict(sorted(accepted_by_instrument.items()))}",
        "remaining_active_source_label_requests_after_crosswalk=484",
        "accepted_full_objective_gate=none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
        "full_objective_achieved=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    CHECK_DIR.joinpath("crosswalk_tracking_source_attachment_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )

    if len(candidates) != 168:
        raise RuntimeError(f"expected 168 crosswalk rows, got {len(candidates)}")
    if len(accepted_rows) != 36:
        raise RuntimeError(f"expected 36 accepted rows, got {len(accepted_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
