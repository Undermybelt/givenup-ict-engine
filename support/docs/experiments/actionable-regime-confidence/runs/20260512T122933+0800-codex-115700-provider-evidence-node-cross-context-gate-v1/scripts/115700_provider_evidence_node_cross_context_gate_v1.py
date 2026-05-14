from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T122933+0800-codex-115700-provider-evidence-node-cross-context-gate-v1"
SOURCE_AQ_RUN_ID = "20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1"
SOURCE_CHAIN_RUN_ID = "20260512T121347+0800-codex-115700-enriched-downstream-chain-v1"
SOURCE_SCAN_RUN_ID = "20260512T122351+0800-codex-115700-provider-evidence-node-scan-v1"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
REPORT_DIR = ROOT / "115700-provider-evidence-node-cross-context-gate-v1"
CHECK_DIR = ROOT / "checks"
PROVIDER_DIR = RUNS / SOURCE_AQ_RUN_ID / "provider-csv"
ENRICHED_ROWS = (
    RUNS
    / SOURCE_CHAIN_RUN_ID
    / "derived"
    / "same_root_six_provider_1h_aq_real_trades.enriched_layer_contract.jsonl"
)
SCAN_JSON = (
    RUNS
    / SOURCE_SCAN_RUN_ID
    / "115700-provider-evidence-node-scan-v1"
    / "115700_provider_evidence_node_scan_v1.json"
)

PROVIDERS = {
    "yfinance": "yfinance_btc_usd_1h.csv",
    "kraken_public": "kraken_xbtusd_1h.csv",
    "binance_public": "binance_btcusdt_1h.csv",
    "bybit_public": "bybit_btcusdt_linear_1h.csv",
    "tvr_default_binance": "tvr_default_binance_btcusdt_1h.csv",
    "ibkr_paxos_long_midpoint": "BTC_1h_midpoint.csv",
}

MIN_ROWS = 30
MIN_CONTEXT_ROWS = 10
BOARD_A_TARGET = 0.95


def pct(value: float | int | None) -> float:
    if value is None or pd.isna(value):
        return 0.0
    return round(float(value), 6)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def wilson_lower(wins: int, total: int, z: float = 1.96) -> float:
    if total <= 0:
        return 0.0
    phat = wins / total
    denom = 1.0 + z * z / total
    center = (phat + z * z / (2.0 * total)) / denom
    margin = z * math.sqrt((phat * (1.0 - phat) / total) + z * z / (4.0 * total * total)) / denom
    return pct(max(0.0, center - margin))


def normalize_provider(provider: str, path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    date_col = "date" if "date" in raw.columns else "timestamp" if "timestamp" in raw.columns else "ts"
    df = pd.DataFrame(
        {
            "ts": pd.to_datetime(raw[date_col], utc=True).dt.floor("h"),
            f"{provider}_open": pd.to_numeric(raw["open"], errors="coerce"),
            f"{provider}_high": pd.to_numeric(raw["high"], errors="coerce"),
            f"{provider}_low": pd.to_numeric(raw["low"], errors="coerce"),
            f"{provider}_close": pd.to_numeric(raw["close"], errors="coerce"),
            f"{provider}_volume": pd.to_numeric(raw.get("volume", 0.0), errors="coerce").fillna(0.0),
        }
    ).dropna()
    close = df[f"{provider}_close"]
    ret_1h = close.pct_change(1)
    ret_4h = close.pct_change(4)
    ret_24h = close.pct_change(24)
    rv_24h = ret_1h.rolling(24).std()
    hi_24 = close.rolling(24).max()
    lo_24 = close.rolling(24).min()
    df[f"{provider}_ret_1h"] = ret_1h
    df[f"{provider}_ret_4h"] = ret_4h
    df[f"{provider}_ret_24h"] = ret_24h
    df[f"{provider}_rv_24h"] = rv_24h
    df[f"{provider}_trend_abs_24h"] = (ret_24h / rv_24h.replace(0, pd.NA)).abs()
    df[f"{provider}_range_pos_24h"] = ((close - lo_24) / (hi_24 - lo_24).replace(0, pd.NA)).clip(0, 1)
    return df


def provider_panel() -> tuple[pd.DataFrame, dict[str, Any]]:
    panel: pd.DataFrame | None = None
    coverage: dict[str, Any] = {}
    for provider, filename in PROVIDERS.items():
        path = PROVIDER_DIR / filename
        df = normalize_provider(provider, path)
        coverage[provider] = {
            "path": str(path),
            "rows": int(len(df)),
            "first_ts": df["ts"].min().isoformat() if len(df) else None,
            "last_ts": df["ts"].max().isoformat() if len(df) else None,
        }
        panel = df if panel is None else panel.merge(df, on="ts", how="outer")
    if panel is None:
        raise RuntimeError("provider panel is empty")
    panel = panel.sort_values("ts").reset_index(drop=True)
    for horizon in ("1h", "4h", "24h"):
        cols = [f"{provider}_ret_{horizon}" for provider in PROVIDERS]
        values = panel[cols]
        pos = (values > 0).sum(axis=1)
        neg = (values < 0).sum(axis=1)
        n = values.notna().sum(axis=1).replace(0, pd.NA)
        panel[f"provider_direction_consensus_{horizon}"] = pd.concat([pos, neg], axis=1).max(axis=1) / n
        panel[f"provider_direction_edge_{horizon}"] = (pos - neg).abs() / n
        panel[f"provider_return_dispersion_{horizon}"] = values.std(axis=1)
        panel[f"provider_return_median_abs_{horizon}"] = values.abs().median(axis=1)
    rv_cols = [f"{provider}_rv_24h" for provider in PROVIDERS]
    trend_cols = [f"{provider}_trend_abs_24h" for provider in PROVIDERS]
    range_cols = [f"{provider}_range_pos_24h" for provider in PROVIDERS]
    panel["provider_count"] = panel[[f"{provider}_close" for provider in PROVIDERS]].notna().sum(axis=1)
    panel["provider_rv_median_24h"] = panel[rv_cols].median(axis=1)
    panel["provider_trend_abs_median_24h"] = panel[trend_cols].median(axis=1)
    panel["provider_range_pos_median_24h"] = panel[range_cols].median(axis=1)
    panel["provider_range_pos_dispersion_24h"] = panel[range_cols].std(axis=1)
    return panel, coverage


def normalize_instrument(symbol: str) -> str:
    upper = symbol.upper().replace("-", "").replace("_", "").replace(":", "")
    if "BTC" in upper or "XBT" in upper:
        return "BTC"
    if "ETH" in upper:
        return "ETH"
    return upper or "unknown"


def load_trades() -> pd.DataFrame:
    rows = [json.loads(line) for line in ENRICHED_ROWS.read_text().splitlines() if line.strip()]
    parsed: list[dict[str, Any]] = []
    for row in rows:
        provenance = row.get("provider_provenance") or {}
        decision = row.get("execution_tree_decision") or {}
        posterior = row.get("bbn_posterior") or {}
        canonical = posterior.get("canonical_probabilities") or {}
        parsed.append(
            {
                "trade_id": row.get("trade_id"),
                "ts": pd.to_datetime(int(row.get("open_ts_ms")), unit="ms", utc=True).floor("h"),
                "source_provider": row.get("source_provider"),
                "provider_symbol": provenance.get("provider_symbol") or row.get("symbol") or "unknown",
                "source_timeframe": row.get("source_timeframe") or row.get("aq_timeframe") or "unknown",
                "branch_path": row.get("branch_path") or row.get("regime_profit_branch_path"),
                "realized_outcome": row.get("realized_outcome"),
                "pnl": float(row.get("pnl") or 0.0),
                "pre_bayes_gate": (row.get("pre_bayes_filter_state") or {}).get("gate"),
                "bbn_range_prob": canonical.get("range"),
                "bbn_stress_prob": canonical.get("stress"),
                "bbn_transition_prob": canonical.get("transition"),
                "bbn_trend_prob": canonical.get("trend"),
                "execution_ready": decision.get("ready"),
                "execution_actionable": decision.get("actionable"),
                "execution_review": decision.get("review"),
            }
        )
    df = pd.DataFrame(parsed)
    df["is_win"] = (df["realized_outcome"] == "win").astype(int)
    df["is_loss"] = (df["realized_outcome"] == "loss").astype(int)
    df["chronological_bucket"] = pd.qcut(
        df["ts"].rank(method="first"),
        q=3,
        labels=["early", "middle", "late"],
    )
    df["instrument_family"] = df["provider_symbol"].map(normalize_instrument)
    return df


def bin_feature(s: pd.Series) -> pd.Series:
    valid = s.dropna()
    if valid.nunique() < 3:
        return pd.Series(["all"] * len(s), index=s.index)
    q1, q2 = valid.quantile([0.33, 0.66])
    if pd.isna(q1) or pd.isna(q2) or q1 >= q2:
        return pd.Series(["all"] * len(s), index=s.index)
    return pd.cut(s, [-float("inf"), q1, q2, float("inf")], labels=["low", "mid", "high"]).astype(str)


def summarize(group: pd.DataFrame) -> dict[str, Any]:
    rows = int(len(group))
    wins = int(group["is_win"].sum()) if rows else 0
    losses = int(group["is_loss"].sum()) if rows else 0
    return {
        "rows": rows,
        "wins": wins,
        "losses": losses,
        "win_rate": pct(wins / rows) if rows else 0.0,
        "loss_rate": pct(losses / rows) if rows else 0.0,
        "avg_pnl": pct(group["pnl"].mean()) if rows else 0.0,
        "wilson_win_lower_95": wilson_lower(wins, rows),
        "meets_min_rows": rows >= MIN_ROWS,
        "meets_95_gate": rows >= MIN_ROWS and wilson_lower(wins, rows) >= BOARD_A_TARGET,
    }


def grouped_summary(df: pd.DataFrame, keys: list[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw_key, group in df.groupby(keys, dropna=False):
        key_values = raw_key if isinstance(raw_key, tuple) else (raw_key,)
        row = {key: str(value) for key, value in zip(keys, key_values)}
        row.update(summarize(group))
        out.append(row)
    return out


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def feature_gate(joined: pd.DataFrame, feature: str) -> dict[str, Any]:
    tmp = joined.dropna(subset=[feature]).copy()
    tmp["feature_bin"] = bin_feature(tmp[feature])
    by_bin = grouped_summary(tmp, ["feature_bin"])
    best_bin = max(by_bin, key=lambda row: (row["win_rate"], row["rows"])) if by_bin else {}
    best_name = str(best_bin.get("feature_bin", "none"))
    best_rows = tmp[tmp["feature_bin"].astype(str) == best_name]
    by_context_rows: list[dict[str, Any]] = []
    for axis in ("source_provider", "chronological_bucket", "branch_path"):
        for row in grouped_summary(best_rows, [axis]):
            row["axis"] = axis
            by_context_rows.append(row)
    passing_contexts = [
        row
        for row in by_context_rows
        if row["rows"] >= MIN_CONTEXT_ROWS and row["wilson_win_lower_95"] >= BOARD_A_TARGET
    ]
    return {
        "feature": feature,
        "rows": int(len(tmp)),
        "by_bin": by_bin,
        "best_bin": best_bin,
        "best_bin_contexts": by_context_rows,
        "accepted_contexts": passing_contexts,
        "feature_gate": "fail_closed_no_95_context",
    }


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")
    (ROOT / "source_aq_run_id.txt").write_text(SOURCE_AQ_RUN_ID + "\n")
    (ROOT / "source_chain_run_id.txt").write_text(SOURCE_CHAIN_RUN_ID + "\n")
    (ROOT / "source_scan_run_id.txt").write_text(SOURCE_SCAN_RUN_ID + "\n")

    panel, coverage = provider_panel()
    trades = load_trades()
    joined = trades.merge(panel, on="ts", how="left")
    scan = json.loads(SCAN_JSON.read_text())
    features = [item["feature"] for item in scan.get("top_candidate_features", [])[:5]]
    gates = [feature_gate(joined, feature) for feature in features]

    all_bin_rows: list[dict[str, Any]] = []
    all_context_rows: list[dict[str, Any]] = []
    for gate in gates:
        for row in gate["by_bin"]:
            all_bin_rows.append({"feature": gate["feature"], **row})
        for row in gate["best_bin_contexts"]:
            all_context_rows.append({"feature": gate["feature"], "best_bin": gate["best_bin"].get("feature_bin"), **row})

    instrument_families = sorted(set(trades["instrument_family"].astype(str)))
    timeframes = sorted(set(trades["source_timeframe"].astype(str)))
    pre_bayes_gates = Counter(str(value) for value in trades["pre_bayes_gate"])
    execution_reviews = Counter(str(value) for value in trades["execution_review"])
    max_prob = pct(
        max(
            pd.to_numeric(
                trades[["bbn_range_prob", "bbn_stress_prob", "bbn_transition_prob", "bbn_trend_prob"]].stack(),
                errors="coerce",
            ).fillna(0.0)
        )
    )
    accepted_features = [
        gate
        for gate in gates
        if gate["best_bin"].get("meets_95_gate") and gate["accepted_contexts"]
    ]
    decision = {
        "gate": "provider_evidence_node_cross_context_gate_fail_closed",
        "accepted_feature_gates": len(accepted_features),
        "production_likelihood_mutation": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "blockers": [
            "no feature bin reaches 95% Wilson lower confidence",
            "instrument family coverage remains BTC-like only",
            "timeframe coverage remains 1h only",
            "Pre-Bayes remains pass_neutralized",
            "execution remains observe/not ready",
        ],
    }
    payload = {
        "run_id": RUN_ID,
        "source_aq_run_id": SOURCE_AQ_RUN_ID,
        "source_chain_run_id": SOURCE_CHAIN_RUN_ID,
        "source_scan_run_id": SOURCE_SCAN_RUN_ID,
        "provider_coverage": coverage,
        "rows": int(len(trades)),
        "features_checked": features,
        "feature_gates": gates,
        "instrument_families": instrument_families,
        "timeframes": timeframes,
        "pre_bayes_gates": dict(pre_bayes_gates),
        "execution_reviews": dict(execution_reviews),
        "max_bbn_probability": max_prob,
        "decision": decision,
    }
    json_path = REPORT_DIR / "115700_provider_evidence_node_cross_context_gate_v1.json"
    write_json(json_path, payload)
    write_rows(REPORT_DIR / "feature_bin_summary_v1.csv", all_bin_rows)
    write_rows(REPORT_DIR / "feature_best_bin_contexts_v1.csv", all_context_rows)

    best = gates[0]["best_bin"] if gates else {}
    md_lines = [
        "# 115700 Provider Evidence Node Cross-Context Gate v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source scan: `{SOURCE_SCAN_RUN_ID}`",
        f"Source enriched chain: `{SOURCE_CHAIN_RUN_ID}`",
        "",
        "## Scope",
        "Validate the top provider evidence-node candidates from `122351` across feature bins, providers, chronology, branches, instrument family, and timeframe.",
        "This is read-only candidate validation. It does not mutate BBN CPDs, CatBoost models, or execution-tree gates.",
        "",
        "## Readback",
        f"- Rows checked: `{len(trades)}`.",
        f"- Features checked: `{features}`.",
        f"- Best candidate remains `{gates[0]['feature'] if gates else 'none'}` best bin `{best.get('feature_bin', 'none')}` with rows `{best.get('rows', 0)}`, win rate `{best.get('win_rate', 0.0)}`, Wilson lower `{best.get('wilson_win_lower_95', 0.0)}`.",
        f"- Instrument families after strict normalization: `{instrument_families}`.",
        f"- Timeframes: `{timeframes}`.",
        f"- Pre-Bayes gates: `{dict(pre_bayes_gates)}`.",
        f"- Execution reviews: `{dict(execution_reviews)}`.",
        f"- Max BBN probability: `{max_prob}`.",
        "",
        "## Decision",
        f"- Gate: `{decision['gate']}`.",
        "- Candidate provider evidence nodes are useful for the next BBN feature design queue, but none is an accepted Board A regime gate.",
        "- `production_likelihood_mutation=false`.",
        "- `promotion_allowed=false`.",
        "- `trade_usable=false`.",
        "- `update_goal=false`.",
        "",
        "## Artifacts",
        f"- JSON: `{json_path}`",
        f"- Feature bins: `{REPORT_DIR / 'feature_bin_summary_v1.csv'}`",
        f"- Best-bin contexts: `{REPORT_DIR / 'feature_best_bin_contexts_v1.csv'}`",
        f"- Assertions: `{CHECK_DIR / '115700_provider_evidence_node_cross_context_gate_v1_assertions.out'}`",
    ]
    (REPORT_DIR / "115700_provider_evidence_node_cross_context_gate_v1.md").write_text(
        "\n".join(md_lines) + "\n"
    )
    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_scan_run_id={SOURCE_SCAN_RUN_ID}",
        f"PASS rows={len(trades)}",
        f"PASS features_checked={len(features)}",
        f"FAIL_CLOSED accepted_feature_gates={len(accepted_features)}",
        f"FAIL_CLOSED instrument_families={len(instrument_families)} required=2 values={'|'.join(instrument_families)}",
        f"FAIL_CLOSED timeframes={len(timeframes)} required=2 values={'|'.join(timeframes)}",
        f"FAIL_CLOSED max_bbn_probability={max_prob} target={BOARD_A_TARGET}",
        f"FAIL_CLOSED pre_bayes_gates={dict(pre_bayes_gates)}",
        f"FAIL_CLOSED execution_reviews={dict(execution_reviews)}",
        "PASS production_likelihood_mutation=false",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "115700_provider_evidence_node_cross_context_gate_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
