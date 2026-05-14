#!/usr/bin/env python3
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T183644-codex-board-b-crisis-coverage-provider-probe-v1"
)
OUT_DIR = RUN_ROOT / "crisis-coverage"
SOURCE_CSV = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
ROOT_SCHEDULE = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T183030-codex-board-b-rootaware-dense-readback-v1/"
    "strategy/board_a_root_schedule_v1.json"
)
CURRENT_BOARD_REFERENCED_REPORT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182222-codex-board-b-rootaware-multibranch-rc-spa-v1/"
    "branch-rc-spa/rootaware_multibranch_branch_rc_spa_report_v1.md"
)
ACTUAL_DENSE_REPORT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T183030-codex-board-b-rootaware-dense-readback-v1/"
    "branch-rc-spa/rootaware_multibranch_branch_rc_spa_report_v1.md"
)


def load_source_coverage():
    rows = 0
    tickers = set()
    label_rows = Counter()
    crisis_rows_by_year = Counter()
    crisis_dates_by_year = defaultdict(set)
    label_by_date = defaultdict(Counter)

    with SOURCE_CSV.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows += 1
            date = row["date"]
            year = date[:4]
            label = row["regime_label"]
            tickers.add(row["ticker"])
            label_rows[label] += 1
            label_by_date[date][label] += 1
            if label == "Crisis":
                crisis_rows_by_year[year] += 1
                crisis_dates_by_year[year].add(date)

    dominant_by_label = Counter()
    dominant_crisis = []
    for date, counts in sorted(label_by_date.items()):
        label, count = max(counts.items(), key=lambda item: item[1])
        dominant_by_label[label] += 1
        if label == "Crisis":
            dominant_crisis.append(
                {
                    "date": date,
                    "dominant_count": count,
                    "row_count": sum(counts.values()),
                    "label_counts": dict(sorted(counts.items())),
                }
            )

    return {
        "source_csv": str(SOURCE_CSV),
        "total_rows": rows,
        "ticker_count": len(tickers),
        "label_rows": dict(sorted(label_rows.items())),
        "crisis_rows_by_year": dict(sorted(crisis_rows_by_year.items())),
        "crisis_dates_by_year": {
            year: len(dates) for year, dates in sorted(crisis_dates_by_year.items())
        },
        "dominant_days_by_label": dict(sorted(dominant_by_label.items())),
        "dominant_crisis_days_by_year": dict(
            sorted(Counter(item["date"][:4] for item in dominant_crisis).items())
        ),
        "dominant_crisis_2021_2025": [
            item
            for item in dominant_crisis
            if "2021" <= item["date"][:4] <= "2025"
        ],
        "dominant_crisis_first_20": dominant_crisis[:20],
        "dominant_crisis_last_20": dominant_crisis[-20:],
    }


def load_schedule_coverage():
    rows = json.loads(ROOT_SCHEDULE.read_text())
    by_root = Counter(row["parent_regime_root"] for row in rows)
    by_root_2021_2025 = Counter(
        row["parent_regime_root"]
        for row in rows
        if "2021" <= row["date"][:4] <= "2025"
    )
    crisis_2021_2025 = [
        row
        for row in rows
        if row["parent_regime_root"] == "Crisis"
        and "2021" <= row["date"][:4] <= "2025"
    ]
    return {
        "root_schedule": str(ROOT_SCHEDULE),
        "total_days": len(rows),
        "root_days": dict(sorted(by_root.items())),
        "root_days_2021_2025": dict(sorted(by_root_2021_2025.items())),
        "crisis_days_2021_2025": crisis_2021_2025,
    }


def load_provider_statuses():
    rows = []
    for path in sorted((RUN_ROOT / "checks").glob("provider-status-*.json")):
        data = json.loads(path.read_text())
        provider_rows = data.get("providers", [])
        rows.append(
            {
                "artifact": str(path),
                "summary_line": data.get("summary_line", ""),
                "ready_providers": sorted(set(data.get("ready_providers", []))),
                "pending_providers": data.get("pending_providers", []),
                "providers": [
                    {
                        "provider_id": item.get("provider_id"),
                        "domain": item.get("domain"),
                        "ready": item.get("ready"),
                        "status": item.get("status"),
                        "reason": item.get("reason"),
                    }
                    for item in provider_rows
                ],
            }
        )
    return rows


def load_fetch_summaries():
    rows = []
    for path in sorted(OUT_DIR.glob("yfinance_*_fetch.json")):
        data = json.loads(path.read_text())
        for result in data.get("results", []):
            candles = result.get("data") or []
            rows.append(
                {
                    "artifact": str(path),
                    "role": result.get("role"),
                    "provider": result.get("provider"),
                    "symbol": result.get("symbol"),
                    "ok": result.get("ok"),
                    "rows": len(candles),
                    "first_timestamp": candles[0]["timestamp"] if candles else "",
                    "last_timestamp": candles[-1]["timestamp"] if candles else "",
                }
            )
    return rows


def write_csv(path, rows, fields):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source = load_source_coverage()
    schedule = load_schedule_coverage()
    providers = load_provider_statuses()
    fetches = load_fetch_summaries()

    dominant_rows = [
        {
            "year": year,
            "dominant_crisis_days": count,
            "crisis_source_rows": source["crisis_rows_by_year"].get(year, 0),
            "crisis_distinct_dates": source["crisis_dates_by_year"].get(year, 0),
        }
        for year, count in source["dominant_crisis_days_by_year"].items()
    ]
    write_csv(
        OUT_DIR / "source_regime_crisis_dominant_by_year_v1.csv",
        dominant_rows,
        [
            "year",
            "dominant_crisis_days",
            "crisis_source_rows",
            "crisis_distinct_dates",
        ],
    )
    write_csv(
        OUT_DIR / "provider_fetch_summary_v1.csv",
        fetches,
        [
            "artifact",
            "role",
            "provider",
            "symbol",
            "ok",
            "rows",
            "first_timestamp",
            "last_timestamp",
        ],
    )

    summary = {
        "run_id": "20260511T183644+0800-codex-board-b-crisis-coverage-provider-probe-v1",
        "decision": {
            "board_state": "rejected",
            "gate_result": "fail:no_new_auto_quant_recipe_scored",
            "downstream_consumption": "not_started:blocked_by_missing_rc_spa_candidate",
            "primary_blocker": (
                "Current Auto-Quant/Freqtrade crypto window is crisis-thin; "
                "local source labels and yfinance can support older tradfi "
                "crisis windows, but no new Auto-Quant recipe has been scored."
            ),
            "next_action": (
                "B2R-repeat: convert the broader 2000-2020 tradfi crisis "
                "panel into an Auto-Quant-compatible backtest input or select "
                "a recipe that can trade older crisis windows before any "
                "downstream branch promotion."
            ),
        },
        "current_board_artifact_path_check": {
            "referenced_report_exists": CURRENT_BOARD_REFERENCED_REPORT.exists(),
            "referenced_report": str(CURRENT_BOARD_REFERENCED_REPORT),
            "actual_dense_report_exists": ACTUAL_DENSE_REPORT.exists(),
            "actual_dense_report": str(ACTUAL_DENSE_REPORT),
        },
        "source_coverage": source,
        "root_schedule_coverage": schedule,
        "provider_statuses": providers,
        "provider_fetches": fetches,
        "completion": {
            "auto_quant_recipe_scored": False,
            "downstream_runtime_consumed_branch_path": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
        },
    }

    summary_path = OUT_DIR / "board_b_crisis_coverage_probe_v1.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    dominant_2021_2025 = len(source["dominant_crisis_2021_2025"])
    schedule_crisis_2021_2025 = len(schedule["crisis_days_2021_2025"])
    fetch_lines = "\n".join(
        [
            f"- `{row['symbol']}` via `{row['provider']}`: "
            f"`{row['rows']}` rows, `{row['first_timestamp']}` -> "
            f"`{row['last_timestamp']}`"
            for row in fetches
        ]
    )
    md = f"""# Board B Crisis Coverage Provider Probe v1

Run id: `20260511T183644+0800-codex-board-b-crisis-coverage-provider-probe-v1`.

## Decision

- Board state: `rejected`
- Gate result: `fail:no_new_auto_quant_recipe_scored`
- Downstream consumption: `not_started:blocked_by_missing_rc_spa_candidate`
- Stable profit score: `0`
- Primary blocker: current Auto-Quant/Freqtrade crypto evidence uses the `2021-2025` window, where the accepted Board A root schedule has only `{schedule_crisis_2021_2025}` dominant `Crisis` days. The local source label panel has `{dominant_2021_2025}` dominant `Crisis` days in the same period but `{source['dominant_days_by_label'].get('Crisis', 0)}` dominant `Crisis` days across `2000-2026`, so the bottleneck is the current tradeable panel/window, not the source-label corpus.

## Provider Readback

- `provider-status --agent`: `{next((item['summary_line'] for item in providers if item['artifact'].endswith('provider-status-agent.json')), '')}`
- `yfinance`: ready for market data and live runtime.
- `tradingview_mcp`: ready.
- `ibkr`: gateway reachable but runtime dependencies missing.
- `kraken_public`: Python provider dependencies missing.
- `kraken_cli`: ready local runtime, but it does not resolve the current tradfi crisis-panel need.

## yfinance Fetch Readback

{fetch_lines}

## Coverage Readback

- Source CSV rows: `{source['total_rows']}`
- Source tickers: `{source['ticker_count']}`
- Dominant Crisis days by useful older windows: `2000={source['dominant_crisis_days_by_year'].get('2000', 0)}`, `2001={source['dominant_crisis_days_by_year'].get('2001', 0)}`, `2002={source['dominant_crisis_days_by_year'].get('2002', 0)}`, `2008={source['dominant_crisis_days_by_year'].get('2008', 0)}`, `2009={source['dominant_crisis_days_by_year'].get('2009', 0)}`, `2020={source['dominant_crisis_days_by_year'].get('2020', 0)}`.
- Current Board A root schedule days by root: `{schedule['root_days']}`
- Current Board A root schedule days by root for `2021-2025`: `{schedule['root_days_2021_2025']}`

## Artifact Path Check

- Board current row referenced report exists: `{CURRENT_BOARD_REFERENCED_REPORT.exists()}` at `{CURRENT_BOARD_REFERENCED_REPORT}`
- Actual dense readback report exists: `{ACTUAL_DENSE_REPORT.exists()}` at `{ACTUAL_DENSE_REPORT}`

## Next

B2R-repeat: convert the broader `2000-2020` tradfi crisis panel into an Auto-Quant-compatible backtest input, or select a recipe that can trade older crisis windows before any downstream branch promotion.
"""
    (OUT_DIR / "board_b_crisis_coverage_probe_v1.md").write_text(md)
    print(summary_path)
    print(OUT_DIR / "board_b_crisis_coverage_probe_v1.md")


if __name__ == "__main__":
    main()
