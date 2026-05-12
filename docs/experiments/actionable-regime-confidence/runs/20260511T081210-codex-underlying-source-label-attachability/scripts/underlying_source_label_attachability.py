#!/usr/bin/env python3
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


RUN_ID = "20260511T081210+0800-codex-underlying-source-label-attachability"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T081210-codex-underlying-source-label-attachability"
)
CONTRACT_PATH = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T073700-codex-root-label-panel-contract/"
    "label-panel-contract/root_label_panel_contract.json"
)
SOURCE_FEATURE_TABLE = Path(
    "/private/tmp/ict-regime-kaggle-regime-label-root/"
    "kaggle_regime_label_feature_table.csv"
)

MAIN_ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
EXACT_UNDERLYING = {
    "SPY": "^GSPC",
    "ES=F": "^GSPC",
    "DIA": "^DJI",
    "YM=F": "^DJI",
}
NEAR_PROXY_REJECTED = {
    "QQQ": "^IXIC",
    "^NDX": "^IXIC",
    "NQ=F": "^IXIC",
}


def read_source_index(path: Path) -> dict[tuple[str, str], set[str]]:
    source_roots: dict[tuple[str, str], set[str]] = defaultdict(set)
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            root = row["regime_label"]
            if root not in MAIN_ROOTS:
                continue
            source_roots[(row["ticker"], row["timeframe"])].add(root)
    return source_roots


def slot_status(slot: dict, source_roots: dict[tuple[str, str], set[str]]) -> dict:
    provider = slot["provider"]
    instrument = slot["instrument"]
    timeframe = slot["timeframe"]
    root = slot["root"]
    source_ticker = ""
    source_relation = "none"

    if root in source_roots.get((instrument, timeframe), set()):
        status = "direct_source_label_attached_candidate"
        source_ticker = instrument
        source_relation = "exact_source_instrument"
    elif instrument in EXACT_UNDERLYING and root in source_roots.get((EXACT_UNDERLYING[instrument], timeframe), set()):
        status = "exact_underlying_source_label_attached_candidate"
        source_ticker = EXACT_UNDERLYING[instrument]
        source_relation = "exact_underlying_index"
    elif instrument in NEAR_PROXY_REJECTED and root in source_roots.get((NEAR_PROXY_REJECTED[instrument], timeframe), set()):
        status = "rejected_near_underlying_proxy_not_accepted"
        source_ticker = NEAR_PROXY_REJECTED[instrument]
        source_relation = "near_underlying_proxy_rejected"
    elif provider != "yfinance":
        status = "missing_non_yfinance_source_label"
    elif timeframe not in {"1d", "1w"}:
        status = "missing_intraday_or_monthly_source_label"
    else:
        status = "missing_instrument_source_label"

    accepted_candidate = status in {
        "direct_source_label_attached_candidate",
        "exact_underlying_source_label_attached_candidate",
    }
    return {
        "provider": provider,
        "instrument": instrument,
        "timeframe": timeframe,
        "root": root,
        "status": status,
        "source_ticker": source_ticker,
        "source_relation": source_relation,
        "accepted_candidate": accepted_candidate,
    }


def main() -> int:
    contract = json.loads(CONTRACT_PATH.read_text())
    source_roots = read_source_index(SOURCE_FEATURE_TABLE)
    rows = [slot_status(slot, source_roots) for slot in contract["slots"]]

    status_counts = Counter(row["status"] for row in rows)
    attached = [row for row in rows if row["accepted_candidate"]]
    attached_by_root = Counter(row["root"] for row in attached)
    attached_by_relation = Counter(row["source_relation"] for row in attached)
    attached_by_provider = Counter(row["provider"] for row in attached)

    cell_roots: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for row in attached:
        cell_roots[(row["provider"], row["instrument"], row["timeframe"])].add(row["root"])
    full_cells = [
        {
            "provider": provider,
            "instrument": instrument,
            "timeframe": timeframe,
            "attached_roots": sorted(roots),
        }
        for (provider, instrument, timeframe), roots in sorted(cell_roots.items())
        if set(MAIN_ROOTS).issubset(roots)
    ]

    missing_slots = len(rows) - len(attached)
    blocker = (
        f"Only {len(attached)} of {len(rows)} current MainRegimeV2 root-label slots "
        f"have direct or exact-underlying source-label candidates; {missing_slots} slots "
        "remain missing or rejected. Intraday/monthly, Kraken/non-yfinance, non-index "
        "commodities/crypto, near-proxy Nasdaq mappings, and full direct Manipulation "
        "coverage remain outside accepted source-label coverage."
    )

    result = {
        "run_id": RUN_ID,
        "objective": "Attach exact-underlying source labels without accepting near proxies.",
        "active_taxonomy": "MainRegimeV2",
        "main_price_roots": MAIN_ROOTS,
        "source": {
            "name": "Kaggle stock-market-regimes-2000-2026",
            "local_feature_table": str(SOURCE_FEATURE_TABLE),
            "raw_data_committed": False,
        },
        "contract": {
            "path": str(CONTRACT_PATH),
            "slot_count": len(rows),
        },
        "attachability": {
            "attached_candidate_slots": len(attached),
            "missing_or_rejected_slots": missing_slots,
            "full_four_root_cells": len(full_cells),
            "full_four_root_cell_details": full_cells,
            "attached_slots_by_root": dict(sorted(attached_by_root.items())),
            "attached_slots_by_relation": dict(sorted(attached_by_relation.items())),
            "attached_slots_by_provider": dict(sorted(attached_by_provider.items())),
            "status_counts": dict(sorted(status_counts.items())),
            "rejected_near_proxy_map": NEAR_PROXY_REJECTED,
            "accepted_exact_underlying_map": EXACT_UNDERLYING,
        },
        "completion_accounting": {
            "accepted_confidence": False,
            "accepted_full_panel": False,
            "goal_achieved": False,
            "blocker": blocker,
        },
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
    }

    out_dir = RUN_ROOT / "source-label-attachability"
    checks_dir = RUN_ROOT / "checks"
    out_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "underlying_source_label_attachability.json"
    csv_path = out_dir / "underlying_source_label_attachability.csv"
    md_path = out_dir / "underlying_source_label_attachability.md"
    assertions_path = checks_dir / "underlying_source_label_attachability_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "provider",
                "instrument",
                "timeframe",
                "root",
                "status",
                "source_ticker",
                "source_relation",
                "accepted_candidate",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    md_lines = [
        "# Underlying Source Label Attachability",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Root-label slots audited: `{len(rows)}`",
        f"- Direct or exact-underlying source-label candidate slots: `{len(attached)}`",
        f"- Missing or rejected source-label slots: `{missing_slots}`",
        f"- Full four-root cells: `{len(full_cells)}`",
        f"- Attached slots by root: `{dict(sorted(attached_by_root.items()))}`",
        f"- Attached slots by relation: `{dict(sorted(attached_by_relation.items()))}`",
        "",
        "Exact-underlying source labels are accepted only for same-underlying market exposures:",
        "",
    ]
    for target, source in sorted(EXACT_UNDERLYING.items()):
        md_lines.append(f"- `{source}` source labels can attach to `{target}` daily/weekly slots.")
    md_lines.extend(
        [
            "",
            "Near-proxy mappings are rejected rather than promoted:",
            "",
        ]
    )
    for target, source in sorted(NEAR_PROXY_REJECTED.items()):
        md_lines.append(f"- `{source}` is not accepted as an exact source label for `{target}`.")
    md_lines.extend(
        [
            "",
            "This is source-label availability only; it is not accepted full-universe/full-cycle confidence.",
            "",
            "## Blocker",
            "",
            blocker,
            "",
            "Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.",
        ]
    )
    md_path.write_text("\n".join(md_lines) + "\n")

    checks = [
        "PASS active_taxonomy=MainRegimeV2",
        f"PASS slot_count={len(rows)}",
        f"PASS attached_candidate_slots={len(attached)}",
        f"PASS full_four_root_cells={len(full_cells)}",
        f"PASS missing_or_rejected_slots={missing_slots}",
        f"PASS rejected_near_proxy_slots={status_counts.get('rejected_near_underlying_proxy_not_accepted', 0)}",
        "PASS accepted_full_panel=false",
        "PASS goal_achieved=false",
        "PASS raw_data_committed=false",
        "PASS thresholds_relaxed=false",
        "PASS trade_usable=false",
    ]
    assertions_path.write_text("\n".join(checks) + "\n")

    print(json.dumps(result["attachability"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
