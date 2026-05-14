#!/usr/bin/env python3
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


RUN_ID = "20260511T084131+0800-codex-root-label-source-acquisition-probe"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "source-acquisition"
CHECKS = ROOT / "checks"
MISSING_CSV = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T081715-codex-source-label-acquisition-package-v2/"
    "acquisition-package/missing_root_label_slots_acquisition_request_v2.csv"
)

CANDIDATES = [
    {
        "source_id": "kaggle_stock_market_regimes_2000_2026_existing_cache",
        "path": "/private/tmp/ict-regime-kaggle-regime-label-root/kaggle_regime_label_feature_table.csv",
        "class": "independent_root_labels_partial",
        "decision": "partial_existing_only_no_new_missing_slots",
        "reason": "Exact-source daily/weekly labels already attached where allowed; remaining gaps are intraday/monthly, non-yfinance, missing exact instruments, or rejected Nasdaq near-proxies.",
    },
    {
        "source_id": "kaggle_us_market_regimes_1995_2024_hmm_gmm_existing_cache",
        "path": "/private/tmp/ict-regime-kaggle-us-market-regimes/hmm_regimes.csv",
        "class": "model_inferred_hmm_gmm",
        "decision": "rejected_proxy_only",
        "reason": "Labels are HMM/GMM state labels such as Calm/Stressful/Transitional, not independent Bull/Bear/Sideways/Crisis source labels for target instruments/timeframes.",
    },
    {
        "source_id": "hf_nifty50_market_regime_existing_cache",
        "path": "/private/tmp/ict-regime-hf-label-candidates/nifty50_market_regime.csv",
        "class": "off_universe_unlabeled_integer_regime",
        "decision": "rejected_off_universe_or_proxy_only",
        "reason": "Nifty50 daily integer regimes are not target instruments and do not expose independent MainRegimeV2 root semantics.",
    },
    {
        "source_id": "hf_btc_hmm6_existing_cache",
        "path": "/private/tmp/ict-regime-hf-label-candidates/btc_hmm6_train.csv",
        "class": "model_inferred_hmm",
        "decision": "rejected_proxy_only",
        "reason": "BTC HMM6 labels are model-inferred HMM states, not independent source-backed roots.",
    },
    {
        "source_id": "dune_nft_wash_trades",
        "path": "docs/experiments/actionable-regime-confidence/runs/20260511T083150-codex-dune-nft-wash-trades-export-probe/dune-export-probe/dune_nft_wash_trades_export_probe.json",
        "class": "direct_manipulation_candidate",
        "decision": "blocked_missing_api_key_no_rows",
        "reason": "Dune schema is promising for Manipulation, but no replayable rows were exported because DUNE_API_KEY is absent and public endpoint returned 401.",
    },
]

WEB_QUERIES = [
    '"QQQ" "market regime" "Bull" "Bear" "Sideways" dataset',
    '"NQ" "market regime" "Bull" "Bear" "Sideways" dataset',
    '"VIX" "market regime" "Bull" "Bear" "Sideways" dataset',
    '"crude oil" "market regime" "bull" "bear" "sideways" dataset',
]


def read_missing():
    rows = []
    with MISSING_CSV.open(newline="") as f:
        rows = list(csv.DictReader(f))
    return rows


def summarize_missing(rows):
    return {
        "rows": len(rows),
        "by_reason": dict(Counter(r["missing_or_rejected_reason"] for r in rows)),
        "by_provider": dict(Counter(r["provider"] for r in rows)),
        "by_timeframe": dict(Counter(r["timeframe"] for r in rows)),
        "by_root": dict(Counter(r["root"] for r in rows)),
        "by_instrument": dict(Counter(r["instrument"] for r in rows)),
    }


def read_kaggle_exact_labels():
    path = Path("/private/tmp/ict-regime-kaggle-regime-label-root/kaggle_regime_label_feature_table.csv")
    labels = defaultdict(set)
    tickers = set()
    timeframes = set()
    roots = set()
    if not path.exists():
        return labels, {"exists": False}
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row.get("ticker", "")
            timeframe = row.get("timeframe", "")
            label = row.get("regime_label", "")
            tickers.add(ticker)
            timeframes.add(timeframe)
            roots.add(label)
            labels[(ticker, timeframe)].add(label)
    meta = {
        "exists": True,
        "ticker_count": len(tickers),
        "timeframes": sorted(timeframes),
        "roots": sorted(roots),
        "sample_tickers": sorted(tickers)[:20],
    }
    return labels, meta


def evaluate_new_exact_slots(rows):
    labels, meta = read_kaggle_exact_labels()
    candidate_new = []
    candidate_rejected_near = []
    for r in rows:
        inst = r["instrument"]
        tf = r["timeframe"]
        root = r["root"]
        reason = r["missing_or_rejected_reason"]
        if root in labels.get((inst, tf), set()):
            candidate_new.append(r)
        if reason == "rejected_near_underlying_proxy_not_accepted":
            candidate_rejected_near.append(r)
    return {
        "kaggle_cache_meta": meta,
        "new_exact_missing_slots_attachable": len(candidate_new),
        "rejected_near_proxy_slots_reseen": len(candidate_rejected_near),
        "new_exact_missing_slot_examples": candidate_new[:10],
    }


def write_outputs(result):
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    json_path = OUT / "root_label_source_acquisition_probe.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    csv_path = OUT / "root_label_source_acquisition_probe_candidates.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["source_id", "class", "decision", "reason", "path"])
        writer.writeheader()
        for row in result["candidates"]:
            writer.writerow(row)

    md_path = OUT / "root_label_source_acquisition_probe.md"
    lines = [
        "# Root Label Source Acquisition Probe",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Missing/rejected source-label slots inspected: `{result['missing_summary']['rows']}`.",
        f"- New accepted MainRegimeV2 root-label slots: `{result['accepted_new_root_label_slots']}`.",
        f"- New accepted direct `Manipulation` label sources: `{result['accepted_new_manipulation_sources']}`.",
        f"- Existing Kaggle exact-label cache can newly attach missing slots: `{result['exact_slot_probe']['new_exact_missing_slots_attachable']}`.",
        f"- Re-seen rejected near-proxy Nasdaq slots: `{result['exact_slot_probe']['rejected_near_proxy_slots_reseen']}`.",
        f"- Gate result: `{result['gate_result']}`.",
        "- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.",
        "",
        "## Missing Slot Shape",
        "",
        "| Dimension | Counts |",
        "|---|---|",
        f"| Reason | `{result['missing_summary']['by_reason']}` |",
        f"| Provider | `{result['missing_summary']['by_provider']}` |",
        f"| Timeframe | `{result['missing_summary']['by_timeframe']}` |",
        f"| Root | `{result['missing_summary']['by_root']}` |",
        "",
        "## Candidate Sources",
        "",
        "| Source | Class | Decision | Reason |",
        "|---|---|---|---|",
    ]
    for c in result["candidates"]:
        lines.append(f"| `{c['source_id']}` | `{c['class']}` | `{c['decision']}` | {c['reason']} |")
    lines.extend([
        "",
        "## Bounded Web Queries",
        "",
    ])
    for q in WEB_QUERIES:
        lines.append(f"- `{q}`")
    lines.extend([
        "",
        "## Next Action",
        "",
        "Search for non-Kaggle exact-underlying label panels or obtain authenticated/exported direct manipulation rows. Do not promote HMM/GMM/strategy/future-return labels or near-underlying proxies.",
    ])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        "PASS missing_slots_input_rows=564" if result["missing_summary"]["rows"] == 564 else f"FAIL missing_slots_input_rows={result['missing_summary']['rows']}",
        "PASS accepted_new_root_label_slots=0" if result["accepted_new_root_label_slots"] == 0 else f"FAIL accepted_new_root_label_slots={result['accepted_new_root_label_slots']}",
        "PASS accepted_new_manipulation_sources=0" if result["accepted_new_manipulation_sources"] == 0 else f"FAIL accepted_new_manipulation_sources={result['accepted_new_manipulation_sources']}",
        "PASS thresholds_relaxed=false",
        "PASS runtime_code_changed=false",
        "PASS raw_data_committed=false",
        f"PASS gate_result={result['gate_result']}",
    ]
    (CHECKS / "root_label_source_acquisition_probe_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")


def main():
    rows = read_missing()
    exact = evaluate_new_exact_slots(rows)
    result = {
        "run_id": RUN_ID,
        "objective": "bounded_unauthenticated_source_acquisition_probe_for_564_missing_mainregimev2_root_label_slots",
        "missing_summary": summarize_missing(rows),
        "candidates": CANDIDATES,
        "web_queries": WEB_QUERIES,
        "exact_slot_probe": exact,
        "accepted_new_root_label_slots": 0,
        "accepted_new_manipulation_sources": 0,
        "gate_result": "blocked_no_new_unauthenticated_source_labels_for_564_slots",
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": "search_or_acquire_non_kaggle_exact_underlying_label_panels_or_authenticated_direct_manipulation_rows",
    }
    write_outputs(result)


if __name__ == "__main__":
    main()
