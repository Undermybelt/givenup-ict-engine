#!/usr/bin/env python3
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs/20260512T122144+0800-codex-121607-bbn-feedback-cross-context-calibration-audit-v1")
OUT_DIR = RUN_ROOT / "121607-bbn-feedback-cross-context-calibration-audit-v1"
CHECK_DIR = RUN_ROOT / "checks"

SOURCE_FEEDBACK_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1/"
    "120630-bbn-negative-feedback-packet-v1/120630_bbn_negative_feedback_packet_v1.json"
)
SOURCE_PROVIDER_BRANCH_CSV = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1/"
    "120630-bbn-negative-feedback-packet-v1/120630_bbn_negative_feedback_by_provider_branch_v1.csv"
)
SOURCE_ENRICHED_JSONL = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/"
    "derived/same_root_six_provider_1h_aq_real_trades.enriched_layer_contract.jsonl"
)

THRESHOLD = 0.95
REQUIRED_PROVIDERS = {
    "yfinance",
    "kraken_public",
    "binance_public",
    "bybit_public",
    "tvr_default_binance",
    "ibkr_paxos_long_midpoint",
}


def load_json(path):
    with path.open() as handle:
        return json.load(handle)


def load_jsonl(path):
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_csv(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def iso_from_ms(value):
    if value is None:
        return None
    return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).isoformat()


def normalize_instrument(row):
    provenance = row.get("provider_provenance") or {}
    symbol = (provenance.get("provider_symbol") or row.get("symbol") or "").upper()
    if "BTC" in symbol or "XBT" in symbol:
        return "BTC"
    if "NQ" in symbol:
        return "NQ"
    if "ES" in symbol:
        return "ES"
    if symbol:
        return symbol
    return "unknown"


def win_loss_counts(rows):
    counts = Counter(row.get("realized_outcome") for row in rows)
    wins = counts.get("win", 0)
    losses = counts.get("loss", 0)
    breakeven = counts.get("breakeven", 0)
    total = len(rows)
    return {
        "rows": total,
        "wins": wins,
        "losses": losses,
        "breakeven": breakeven,
        "win_rate": round(wins / total, 6) if total else 0.0,
        "loss_rate": round(losses / total, 6) if total else 0.0,
    }


def max_bbn_prob(row):
    posterior = (row.get("bbn_posterior") or {}).get("canonical_probabilities") or {}
    if not posterior:
        posterior = (row.get("bbn_posterior") or {}).get("posterior") or {}
    if not posterior:
        return {"state": None, "probability": 0.0}
    state, probability = max(posterior.items(), key=lambda item: item[1])
    return {"state": state, "probability": float(probability)}


def aggregate_named(rows, key_fn):
    groups = defaultdict(list)
    for row in rows:
        groups[key_fn(row)].append(row)
    out = {}
    for key in sorted(groups):
        subset = groups[key]
        metrics = win_loss_counts(subset)
        max_prob = max(max_bbn_prob(row)["probability"] for row in subset)
        metrics.update(
            {
                "max_bbn_probability": round(max_prob, 6),
                "providers": sorted({row.get("source_provider") for row in subset if row.get("source_provider")}),
                "timeframes": sorted({row.get("source_timeframe") for row in subset if row.get("source_timeframe")}),
                "instruments": sorted({normalize_instrument(row) for row in subset}),
                "execution_ready_rows": sum(1 for row in subset if (row.get("execution_tree_decision") or {}).get("ready") is True),
                "execution_actionable_rows": sum(1 for row in subset if (row.get("execution_tree_decision") or {}).get("actionable") is True),
            }
        )
        out[key] = metrics
    return out


def chronological_buckets(rows, bucket_count=3):
    sorted_rows = sorted(rows, key=lambda row: row.get("open_ts_ms") or 0)
    buckets = []
    for index in range(bucket_count):
        start = index * len(sorted_rows) // bucket_count
        end = (index + 1) * len(sorted_rows) // bucket_count
        subset = sorted_rows[start:end]
        if not subset:
            continue
        metrics = win_loss_counts(subset)
        metrics.update(
            {
                "bucket": index + 1,
                "start_open_ts": iso_from_ms(subset[0].get("open_ts_ms")),
                "end_open_ts": iso_from_ms(subset[-1].get("open_ts_ms")),
                "providers": sorted({row.get("source_provider") for row in subset if row.get("source_provider")}),
                "branches": sorted({row.get("branch_path") for row in subset if row.get("branch_path")}),
                "main_regimes": sorted({row.get("main_regime") for row in subset if row.get("main_regime")}),
                "max_bbn_probability": round(max(max_bbn_prob(row)["probability"] for row in subset), 6),
                "max_pre_bayes_confidence": round(max(float((row.get("pre_bayes_filter_state") or {}).get("confidence") or 0.0) for row in subset), 6),
                "execution_ready_rows": sum(1 for row in subset if (row.get("execution_tree_decision") or {}).get("ready") is True),
                "execution_actionable_rows": sum(1 for row in subset if (row.get("execution_tree_decision") or {}).get("actionable") is True),
            }
        )
        buckets.append(metrics)
    return buckets


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    feedback = load_json(SOURCE_FEEDBACK_JSON)
    provider_branch_rows = load_csv(SOURCE_PROVIDER_BRANCH_CSV)
    rows = load_jsonl(SOURCE_ENRICHED_JSONL)

    providers = sorted({row.get("source_provider") for row in rows if row.get("source_provider")})
    missing_providers = sorted(REQUIRED_PROVIDERS - set(providers))
    timeframes = sorted({row.get("source_timeframe") for row in rows if row.get("source_timeframe")})
    instruments = sorted({normalize_instrument(row) for row in rows})
    main_regimes = sorted({row.get("main_regime") for row in rows if row.get("main_regime")})
    branches = sorted({row.get("branch_path") for row in rows if row.get("branch_path")})

    max_row_prob = max(max_bbn_prob(row)["probability"] for row in rows) if rows else 0.0
    max_pre_bayes_conf = max(float((row.get("pre_bayes_filter_state") or {}).get("confidence") or 0.0) for row in rows) if rows else 0.0
    execution_ready_rows = sum(1 for row in rows if (row.get("execution_tree_decision") or {}).get("ready") is True)
    execution_actionable_rows = sum(1 for row in rows if (row.get("execution_tree_decision") or {}).get("actionable") is True)
    promotional_reviews = sum(1 for row in rows if (row.get("execution_tree_decision") or {}).get("review") not in (None, "observe"))

    by_provider = aggregate_named(rows, lambda row: row.get("source_provider") or "unknown")
    by_branch = aggregate_named(rows, lambda row: row.get("branch_path") or "unknown")
    by_provider_branch = aggregate_named(rows, lambda row: f"{row.get('source_provider') or 'unknown'} | {row.get('branch_path') or 'unknown'}")
    buckets = chronological_buckets(rows)

    provider_context_pass = not missing_providers and len(providers) >= 6
    instrument_context_pass = len(instruments) > 1
    timeframe_context_pass = len(timeframes) > 1
    chronological_context_pass = all(bucket["max_bbn_probability"] >= THRESHOLD for bucket in buckets)
    confidence_95_pass = max_row_prob >= THRESHOLD and max_pre_bayes_conf >= THRESHOLD
    execution_admissible = execution_ready_rows > 0 and execution_actionable_rows > 0 and promotional_reviews > 0
    every_visible_regime_95 = all(metrics["max_bbn_probability"] >= THRESHOLD for metrics in by_branch.values())
    accepted_regime_count_95 = sum(1 for metrics in by_branch.values() if metrics["max_bbn_probability"] >= THRESHOLD)

    gate_failures = []
    if not confidence_95_pass:
        gate_failures.append("confidence_below_95")
    if not instrument_context_pass:
        gate_failures.append("single_instrument_only")
    if not timeframe_context_pass:
        gate_failures.append("single_timeframe_only")
    if not chronological_context_pass:
        gate_failures.append("chronological_buckets_below_95")
    if not execution_admissible:
        gate_failures.append("execution_not_admissible")
    if not every_visible_regime_95:
        gate_failures.append("not_every_visible_regime_at_95")

    checklist = [
        {
            "requirement": "Use exact Board A run artifacts, not chat-only inference",
            "evidence": str(SOURCE_ENRICHED_JSONL),
            "status": "pass" if rows else "fail",
            "notes": f"read {len(rows)} enriched exact-root rows",
        },
        {
            "requirement": "Provider coverage includes YF, Kraken, Binance, Bybit, TVR, IBKR",
            "evidence": ",".join(providers),
            "status": "pass" if provider_context_pass else "fail",
            "notes": f"missing={missing_providers}",
        },
        {
            "requirement": "Every visible regime/branch reaches >=95% confidence",
            "evidence": f"max_bbn_probability={max_row_prob:.6f}; max_pre_bayes_confidence={max_pre_bayes_conf:.6f}",
            "status": "fail",
            "notes": f"accepted_regime_count_95={accepted_regime_count_95}/{len(by_branch)}",
        },
        {
            "requirement": "Validate on other markets/instruments",
            "evidence": ",".join(instruments),
            "status": "fail" if not instrument_context_pass else "pass",
            "notes": "all observed rows normalize to BTC" if not instrument_context_pass else "multiple instruments present",
        },
        {
            "requirement": "Validate on other periods/timeframes",
            "evidence": ",".join(timeframes),
            "status": "fail" if not timeframe_context_pass else "pass",
            "notes": "all observed rows are 1h" if not timeframe_context_pass else "multiple timeframes present",
        },
        {
            "requirement": "Chronological calibration remains >=95%",
            "evidence": "chronological_buckets.csv",
            "status": "fail" if not chronological_context_pass else "pass",
            "notes": "at least one chronological bucket is below 95%",
        },
        {
            "requirement": "Pass through Pre-Bayes/BBN/CatBoost/execution tree",
            "evidence": str(SOURCE_FEEDBACK_JSON),
            "status": "partial",
            "notes": "chain exists, but Pre-Bayes is pass_neutralized and execution is observe/blocked",
        },
        {
            "requirement": "Do not promote or update goal unless all gates pass",
            "evidence": "assertions",
            "status": "pass",
            "notes": "promotion_allowed=false; trade_usable=false; update_goal=false",
        },
    ]

    report = {
        "run_id": "20260512T122144+0800-codex-121607-bbn-feedback-cross-context-calibration-audit-v1",
        "source_feedback_packet": str(SOURCE_FEEDBACK_JSON),
        "source_enriched_rows": str(SOURCE_ENRICHED_JSONL),
        "source_provider_branch_csv": str(SOURCE_PROVIDER_BRANCH_CSV),
        "threshold": THRESHOLD,
        "summary": {
            "rows": len(rows),
            "providers": providers,
            "missing_providers": missing_providers,
            "timeframes": timeframes,
            "instruments": instruments,
            "main_regimes": main_regimes,
            "branches": branches,
            "max_bbn_probability": round(max_row_prob, 6),
            "max_pre_bayes_confidence": round(max_pre_bayes_conf, 6),
            "execution_ready_rows": execution_ready_rows,
            "execution_actionable_rows": execution_actionable_rows,
            "promotional_review_rows": promotional_reviews,
            "accepted_regime_count_95": accepted_regime_count_95,
            "visible_regime_or_branch_count": len(by_branch),
        },
        "gate_results": {
            "provider_context_pass": provider_context_pass,
            "instrument_context_pass": instrument_context_pass,
            "timeframe_context_pass": timeframe_context_pass,
            "chronological_context_pass": chronological_context_pass,
            "confidence_95_pass": confidence_95_pass,
            "execution_admissible": execution_admissible,
            "every_visible_regime_95": every_visible_regime_95,
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
            "gate": "fail_closed:" + ",".join(gate_failures),
        },
        "by_provider": by_provider,
        "by_branch": by_branch,
        "by_provider_branch": by_provider_branch,
        "chronological_buckets": buckets,
        "source_feedback_packet_summary": {
            "rows": feedback.get("rows"),
            "wins": feedback.get("wins"),
            "losses": feedback.get("losses"),
            "win_rate": feedback.get("win_rate"),
            "pre_bayes_gate": feedback.get("pre_bayes_gate"),
            "active_structural_regime": feedback.get("active_structural_regime"),
            "active_structural_regime_confidence": feedback.get("active_structural_regime_confidence"),
            "execution": feedback.get("execution"),
        },
        "checklist": checklist,
        "provider_branch_source_rows": provider_branch_rows,
    }

    json_path = OUT_DIR / "121607_bbn_feedback_cross_context_calibration_audit_v1.json"
    md_path = OUT_DIR / "121607_bbn_feedback_cross_context_calibration_audit_v1.md"
    checklist_path = OUT_DIR / "prompt_to_artifact_checklist_121607_bbn_feedback_cross_context_calibration_audit_v1.csv"
    bucket_path = OUT_DIR / "chronological_buckets_121607_bbn_feedback_cross_context_calibration_audit_v1.csv"
    assertions_path = CHECK_DIR / "121607_bbn_feedback_cross_context_calibration_audit_v1_assertions.out"

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_csv(checklist_path, checklist, ["requirement", "evidence", "status", "notes"])
    write_csv(
        bucket_path,
        buckets,
        [
            "bucket",
            "start_open_ts",
            "end_open_ts",
            "rows",
            "wins",
            "losses",
            "breakeven",
            "win_rate",
            "loss_rate",
            "providers",
            "branches",
            "main_regimes",
            "max_bbn_probability",
            "max_pre_bayes_confidence",
            "execution_ready_rows",
            "execution_actionable_rows",
        ],
    )

    md_lines = [
        "# 121607 BBN Feedback Cross-Context Calibration Audit v1",
        "",
        f"Run id: `{report['run_id']}`",
        f"Source feedback packet: `{SOURCE_FEEDBACK_JSON}`",
        f"Source enriched rows: `{SOURCE_ENRICHED_JSONL}`",
        "",
        "## Result",
        f"- Rows audited: `{len(rows)}`.",
        f"- Providers present: `{len(providers)}/6` ({', '.join(providers)}).",
        f"- Instruments present: `{', '.join(instruments)}`.",
        f"- Timeframes present: `{', '.join(timeframes)}`.",
        f"- Visible branch/regime paths: `{len(by_branch)}`.",
        f"- Max BBN probability: `{max_row_prob:.6f}`; max Pre-Bayes confidence: `{max_pre_bayes_conf:.6f}`.",
        f"- Accepted branch/regime paths at 95%: `{accepted_regime_count_95}/{len(by_branch)}`.",
        f"- Execution ready/actionable/promotional rows: `{execution_ready_rows}/{execution_actionable_rows}/{promotional_reviews}`.",
        f"- Gate: `{report['gate_results']['gate']}`.",
        "",
        "## Decision",
        "- The exact `115700 -> 120630 -> 121607` packet is valid hard-negative candidate evidence, but it does not satisfy Board A acceptance.",
        "- Provider coverage is present across the six required lanes, but market/instrument coverage is still BTC-only and timeframe coverage is still 1h-only.",
        "- No visible branch/regime path reaches 95% confidence, chronological buckets remain below 95%, and execution remains observe/blocked.",
        "- `promotion_allowed=false`.",
        "- `trade_usable=false`.",
        "- `update_goal=false`.",
        "",
        "## Artifacts",
        f"- JSON: `{json_path}`",
        f"- Checklist: `{checklist_path}`",
        f"- Chronological buckets: `{bucket_path}`",
        f"- Assertions: `{assertions_path}`",
    ]
    md_path.write_text("\n".join(md_lines) + "\n")

    assertions = [
        f"PASS run_id={report['run_id']}",
        f"PASS rows={len(rows)}",
        f"PASS required_provider_coverage={provider_context_pass}",
        f"FAIL_CLOSED max_bbn_probability={max_row_prob:.6f}_below_0.95",
        f"FAIL_CLOSED max_pre_bayes_confidence={max_pre_bayes_conf:.6f}_below_0.95",
        f"FAIL_CLOSED accepted_regime_count_95={accepted_regime_count_95}",
        f"FAIL_CLOSED instrument_context_pass={instrument_context_pass}",
        f"FAIL_CLOSED timeframe_context_pass={timeframe_context_pass}",
        f"FAIL_CLOSED chronological_context_pass={chronological_context_pass}",
        f"FAIL_CLOSED execution_admissible={execution_admissible}",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n")

    print(json_path)
    print(md_path)
    print(checklist_path)
    print(bucket_path)
    print(assertions_path)


if __name__ == "__main__":
    main()
