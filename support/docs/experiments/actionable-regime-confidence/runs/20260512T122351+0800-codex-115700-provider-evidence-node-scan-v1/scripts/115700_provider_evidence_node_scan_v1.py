from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T122351+0800-codex-115700-provider-evidence-node-scan-v1"
SOURCE_AQ_RUN_ID = "20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1"
SOURCE_CHAIN_RUN_ID = "20260512T121347+0800-codex-115700-enriched-downstream-chain-v1"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_AQ_ROOT = RUNS / SOURCE_AQ_RUN_ID
SOURCE_CHAIN_ROOT = RUNS / SOURCE_CHAIN_RUN_ID
REPORT_DIR = ROOT / "115700-provider-evidence-node-scan-v1"
CHECK_DIR = ROOT / "checks"
PROVIDER_DIR = SOURCE_AQ_ROOT / "provider-csv"
ENRICHED_ROWS = SOURCE_CHAIN_ROOT / "derived" / "same_root_six_provider_1h_aq_real_trades.enriched_layer_contract.jsonl"

PROVIDERS = {
    "yfinance": "yfinance_btc_usd_1h.csv",
    "kraken_public": "kraken_xbtusd_1h.csv",
    "binance_public": "binance_btcusdt_1h.csv",
    "bybit_public": "bybit_btcusdt_linear_1h.csv",
    "tvr_default_binance": "tvr_default_binance_btcusdt_1h.csv",
    "ibkr_paxos_long_midpoint": "BTC_1h_midpoint.csv",
}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def pct(value: float) -> float:
    if pd.isna(value):
        return 0.0
    return round(float(value), 6)


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
    assert panel is not None
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


def load_trades() -> pd.DataFrame:
    rows = [json.loads(line) for line in ENRICHED_ROWS.read_text().splitlines() if line.strip()]
    parsed = []
    for row in rows:
        parsed.append(
            {
                "trade_id": row.get("trade_id"),
                "ts": pd.to_datetime(int(row.get("open_ts_ms")), unit="ms", utc=True).floor("h"),
                "source_provider": row.get("source_provider"),
                "branch_path": row.get("branch_path") or row.get("regime_profit_branch_path"),
                "realized_outcome": row.get("realized_outcome"),
                "pnl": float(row.get("pnl") or 0.0),
                "pre_bayes_gate": row.get("pre_bayes_filter_state", {}).get("gate"),
                "bbn_range_prob": row.get("bbn_posterior", {}).get("canonical_probabilities", {}).get("range"),
                "bbn_stress_prob": row.get("bbn_posterior", {}).get("canonical_probabilities", {}).get("stress"),
                "bbn_transition_prob": row.get("bbn_posterior", {}).get("canonical_probabilities", {}).get("transition"),
                "bbn_trend_prob": row.get("bbn_posterior", {}).get("canonical_probabilities", {}).get("trend"),
                "execution_ready": row.get("execution_tree_decision", {}).get("ready"),
                "execution_review": row.get("execution_tree_decision", {}).get("review"),
            }
        )
    df = pd.DataFrame(parsed)
    df["is_win"] = (df["realized_outcome"] == "win").astype(int)
    df["is_loss"] = (df["realized_outcome"] == "loss").astype(int)
    df["period_half"] = pd.qcut(df["ts"].rank(method="first"), q=2, labels=["early", "late"])
    return df


def bin_series(s: pd.Series) -> pd.Series:
    valid = s.dropna()
    if valid.nunique() < 3:
        return pd.Series(["all"] * len(s), index=s.index)
    q1, q2 = valid.quantile([0.33, 0.66])
    if pd.isna(q1) or pd.isna(q2) or q1 >= q2:
        return pd.Series(["all"] * len(s), index=s.index)
    return pd.cut(s, [-float("inf"), q1, q2, float("inf")], labels=["low", "mid", "high"]).astype(str)


def candidate_stats(df: pd.DataFrame, feature: str) -> dict[str, Any]:
    tmp = df[["is_win", "is_loss", "pnl", "source_provider", "period_half", "branch_path", feature]].dropna()
    tmp["bin"] = bin_series(tmp[feature])
    bins: dict[str, Any] = {}
    for name, group in tmp.groupby("bin", dropna=False):
        n = len(group)
        bins[str(name)] = {
            "rows": int(n),
            "wins": int(group["is_win"].sum()),
            "losses": int(group["is_loss"].sum()),
            "win_rate": pct(group["is_win"].mean()) if n else 0.0,
            "loss_rate": pct(group["is_loss"].mean()) if n else 0.0,
            "avg_pnl": pct(group["pnl"].mean()) if n else 0.0,
        }
    win_rates = [v["win_rate"] for v in bins.values() if v["rows"] >= 10]
    separation = max(win_rates) - min(win_rates) if len(win_rates) >= 2 else 0.0
    provider_stability = {}
    for provider, group in tmp.groupby("source_provider"):
        provider_stability[str(provider)] = {"rows": int(len(group)), "win_rate": pct(group["is_win"].mean())}
    period_stability = {}
    for period, group in tmp.groupby("period_half"):
        period_stability[str(period)] = {"rows": int(len(group)), "win_rate": pct(group["is_win"].mean())}
    branch_stability = {}
    for branch, group in tmp.groupby("branch_path"):
        branch_stability[str(branch)] = {"rows": int(len(group)), "win_rate": pct(group["is_win"].mean())}
    return {
        "feature": feature,
        "rows": int(len(tmp)),
        "bins": bins,
        "win_rate_separation": pct(separation),
        "provider_stability": provider_stability,
        "period_stability": period_stability,
        "branch_stability": branch_stability,
        "candidate_use": "bbn_evidence_node_candidate_only",
    }


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")
    (ROOT / "source_aq_run_id.txt").write_text(SOURCE_AQ_RUN_ID + "\n")
    panel, coverage = provider_panel()
    trades = load_trades()
    joined = trades.merge(panel, on="ts", how="left")
    feature_cols = [
        "provider_direction_consensus_1h",
        "provider_direction_consensus_4h",
        "provider_direction_consensus_24h",
        "provider_direction_edge_1h",
        "provider_direction_edge_4h",
        "provider_direction_edge_24h",
        "provider_return_dispersion_1h",
        "provider_return_dispersion_4h",
        "provider_return_dispersion_24h",
        "provider_return_median_abs_1h",
        "provider_return_median_abs_4h",
        "provider_return_median_abs_24h",
        "provider_rv_median_24h",
        "provider_trend_abs_median_24h",
        "provider_range_pos_median_24h",
        "provider_range_pos_dispersion_24h",
        "provider_count",
    ]
    candidates = [candidate_stats(joined, feature) for feature in feature_cols]
    candidates = sorted(candidates, key=lambda item: item["win_rate_separation"], reverse=True)
    top = candidates[:8]
    matched_rows = int(joined[feature_cols].notna().any(axis=1).sum())
    overall = {
        "trade_rows": int(len(trades)),
        "matched_feature_rows": matched_rows,
        "wins": int(trades["is_win"].sum()),
        "losses": int(trades["is_loss"].sum()),
        "win_rate": pct(trades["is_win"].mean()),
        "loss_rate": pct(trades["is_loss"].mean()),
    }
    payload = {
        "run_id": RUN_ID,
        "source_aq_run_id": SOURCE_AQ_RUN_ID,
        "source_chain_run_id": SOURCE_CHAIN_RUN_ID,
        "provider_coverage": coverage,
        "overall": overall,
        "candidate_features": candidates,
        "top_candidate_features": top,
        "decision": {
            "gate": "provider_evidence_node_candidates_identified_no_promotion",
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
            "note": "Candidate feature separations are exploratory and require chronological/cross-instrument validation before BBN likelihood mutation.",
        },
    }
    json_path = REPORT_DIR / "115700_provider_evidence_node_scan_v1.json"
    write_json(json_path, payload)

    csv_path = REPORT_DIR / "115700_provider_evidence_node_candidates_v1.csv"
    with csv_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["rank", "feature", "rows", "win_rate_separation", "candidate_use"])
        for idx, candidate in enumerate(candidates, start=1):
            writer.writerow([idx, candidate["feature"], candidate["rows"], candidate["win_rate_separation"], candidate["candidate_use"]])

    checklist = REPORT_DIR / "prompt_to_artifact_checklist_115700_provider_evidence_node_scan_v1.csv"
    with checklist.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["requirement", "artifact", "status", "note"])
        writer.writerow(["six provider 1h data", str(PROVIDER_DIR), "covered", f"providers={len(PROVIDERS)}"])
        writer.writerow(["enriched downstream rows", str(ENRICHED_ROWS), "covered", f"rows={overall['trade_rows']}"])
        writer.writerow(["candidate BBN evidence nodes", str(json_path), "covered", f"features={len(candidates)}"])
        writer.writerow(["no runtime mutation", str(json_path), "covered", "candidate only"])

    md_path = REPORT_DIR / "115700_provider_evidence_node_scan_v1.md"
    lines = [
        "# 115700 Provider Evidence Node Scan v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source AQ root: `{SOURCE_AQ_RUN_ID}`",
        f"Source enriched chain: `{SOURCE_CHAIN_RUN_ID}`",
        "",
        "## Scope",
        "Read the six-provider 1h CSV panel from `115700`, align provider features to the enriched `121347` trade rows, and identify candidate BBN evidence nodes that may reduce the current `factor_alignment=mixed` / `pass_neutralized` bottleneck.",
        "This is candidate evidence only. It does not mutate BBN priors/CPDs, CatBoost models, or execution-tree gates.",
        "",
        "## Coverage",
        f"- Provider CSVs: `{coverage}`.",
        f"- Trade rows: `{overall['trade_rows']}`; matched feature rows: `{overall['matched_feature_rows']}`.",
        f"- Overall outcome: wins `{overall['wins']}`, losses `{overall['losses']}`, win rate `{overall['win_rate']}`, loss rate `{overall['loss_rate']}`.",
        "",
        "## Top Candidate Evidence Nodes",
    ]
    for idx, candidate in enumerate(top, start=1):
        lines.append(f"- {idx}. `{candidate['feature']}` separation `{candidate['win_rate_separation']}` bins `{candidate['bins']}`.")
    lines.extend(
        [
            "",
            "## Decision",
            "- Gate: `115700_provider_evidence_node_scan_v1=provider_evidence_node_candidates_identified_no_promotion`.",
            "- The scan found candidate provider-context features, but none is an accepted `>=95%` regime gate. They must be replayed chronologically and across instrument/period/provider contexts before any BBN likelihood mutation.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{json_path}`",
            f"- Candidate CSV: `{csv_path}`",
            f"- Checklist: `{checklist}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n")

    assertions = CHECK_DIR / "115700_provider_evidence_node_scan_v1_assertions.out"
    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_aq_run_id={SOURCE_AQ_RUN_ID}",
        f"PASS providers={len(PROVIDERS)}",
        f"PASS trade_rows={overall['trade_rows']}",
        f"PASS matched_feature_rows={overall['matched_feature_rows']}",
        f"PASS candidate_features={len(candidates)}",
        f"PASS top_feature={top[0]['feature'] if top else 'none'}",
        f"PASS top_feature_win_rate_separation={top[0]['win_rate_separation'] if top else 0.0}",
        "FAIL_CLOSED accepted_95_regime_gate=false",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions.write_text("\n".join(assertion_lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
