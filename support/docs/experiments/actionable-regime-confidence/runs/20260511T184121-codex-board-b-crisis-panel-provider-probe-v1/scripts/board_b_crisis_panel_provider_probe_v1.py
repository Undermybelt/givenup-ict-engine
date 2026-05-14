#!/usr/bin/env python3
"""Board B crisis/root panel provider feasibility probe.

This additive artifact does not score a profitability recipe. It checks whether
the next B2R-repeat path should broaden the regime-root panel before another
Auto-Quant recipe is promoted into downstream stages.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf


RUN_ID = "20260511T184121+0800-codex-board-b-crisis-panel-provider-probe-v1"
SCHEMA_VERSION = "board-b-crisis-panel-provider-probe/v1"


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot find repo root from {start}")


RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = find_repo_root(RUN_ROOT)
PANEL_DIR = RUN_ROOT / "panel"
PROVIDER_DIR = RUN_ROOT / "provider"
CHECK_DIR = RUN_ROOT / "checks"
SOURCE_PANEL = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
BOARD = REPO_ROOT / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"
LOCAL_AQ_SUMMARY = PANEL_DIR / "local_autoquant_feather_summary.json"

YF_SYMBOLS = [
    "^GSPC",
    "^IXIC",
    "^RUT",
    "AAPL",
    "AMD",
    "AMZN",
    "MSFT",
    "NVDA",
    "TSLA",
    "XOM",
    "JPM",
    "BTC-USD",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    if not path.exists():
        return {"missing": True, "path": str(path)}
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {"empty": True, "path": str(path)}
    return json.loads(text)


def summarize_provider_artifacts() -> dict[str, Any]:
    providers: dict[str, Any] = {}
    for provider in ["yfinance", "tradingview_mcp", "ibkr", "kraken_public"]:
        status_path = PROVIDER_DIR / f"provider-status-{provider}.agent.json"
        err_path = PROVIDER_DIR / f"provider-status-{provider}.err"
        payload = load_json(status_path)
        providers[provider] = {
            "status_artifact": rel(status_path),
            "stderr_artifact": rel(err_path),
            "summary_line": payload.get("summary_line"),
            "ready_providers": payload.get("ready_providers", []),
            "pending_providers": payload.get("pending_providers", []),
            "install_prompts": payload.get("install_prompts", []),
        }

    harness = {}
    for name in [
        "harness-yfinance-qqq-1d",
        "harness-tradingview-qqq-1d",
        "harness-ibkr-qqq-1d",
        "harness-kraken-xbtusd-1d",
    ]:
        out_path = PROVIDER_DIR / f"{name}.out"
        err_path = PROVIDER_DIR / f"{name}.err"
        parsed: dict[str, Any]
        try:
            parsed = load_json(out_path)
        except json.JSONDecodeError as exc:
            parsed = {"json_error": f"{type(exc).__name__}:{exc}"}
        results = parsed.get("results", []) if isinstance(parsed, dict) else []
        ok_count = sum(1 for item in results if item.get("ok") is True)
        error_count = sum(1 for item in results if item.get("ok") is False)
        harness[name] = {
            "stdout_artifact": rel(out_path),
            "stderr_artifact": rel(err_path),
            "stdout_bytes": out_path.stat().st_size if out_path.exists() else 0,
            "stderr_bytes": err_path.stat().st_size if err_path.exists() else 0,
            "ok_count": ok_count,
            "error_count": error_count,
            "stderr_excerpt": err_path.read_text(encoding="utf-8")[:500] if err_path.exists() else "",
        }
    return {"provider_status": providers, "harness_fetches": harness}


def summarize_source_panel() -> dict[str, Any]:
    root_rows: Counter[str] = Counter()
    root_dates: dict[str, set[str]] = defaultdict(set)
    root_tickers: dict[str, set[str]] = defaultdict(set)
    root_rows_2021_2025: Counter[str] = Counter()
    root_dates_2021_2025: dict[str, set[str]] = defaultdict(set)
    ticker_root_rows: dict[str, Counter[str]] = defaultdict(Counter)
    daily_roots: dict[str, Counter[str]] = defaultdict(Counter)
    daily_roots_2021_2025: dict[str, Counter[str]] = defaultdict(Counter)

    with SOURCE_PANEL.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            label = row["regime_label"]
            date = row["date"]
            ticker = row["ticker"]
            root_rows[label] += 1
            root_dates[label].add(date)
            root_tickers[label].add(ticker)
            ticker_root_rows[ticker][label] += 1
            daily_roots[date][label] += 1
            if "2021-01-01" <= date <= "2025-12-31":
                root_rows_2021_2025[label] += 1
                root_dates_2021_2025[label].add(date)
                daily_roots_2021_2025[date][label] += 1

    def pack_counts(counter: Counter[str], dates: dict[str, set[str]]) -> dict[str, Any]:
        return {
            key: {
                "rows": int(counter[key]),
                "unique_dates": len(dates.get(key, set())),
                "unique_tickers": len(root_tickers.get(key, set())),
            }
            for key in sorted(counter)
        }

    def dominant_counts(daily: dict[str, Counter[str]]) -> dict[str, int]:
        out: Counter[str] = Counter()
        for counts in daily.values():
            if counts:
                out[counts.most_common(1)[0][0]] += 1
        return dict(sorted(out.items()))

    source_overlap = {}
    for symbol in YF_SYMBOLS:
        if symbol in ticker_root_rows:
            source_overlap[symbol] = dict(sorted(ticker_root_rows[symbol].items()))

    return {
        "source_panel": str(SOURCE_PANEL),
        "overall_by_root": pack_counts(root_rows, root_dates),
        "window_2021_2025_by_root": pack_counts(root_rows_2021_2025, root_dates_2021_2025),
        "dominant_daily_by_root": dominant_counts(daily_roots),
        "dominant_daily_2021_2025_by_root": dominant_counts(daily_roots_2021_2025),
        "yf_symbol_source_overlap": source_overlap,
    }


def summarize_local_autoquant_data() -> dict[str, Any]:
    payload = load_json(LOCAL_AQ_SUMMARY)
    files = payload.get("files", []) if isinstance(payload, dict) else []
    by_interval: Counter[str] = Counter()
    by_instrument: dict[str, list[str]] = defaultdict(list)
    for item in files:
        if item.get("ok"):
            by_interval[item.get("interval", "")] += 1
            by_instrument[item.get("instrument", "")].append(item.get("interval", ""))
    return {
        "summary_artifact": rel(LOCAL_AQ_SUMMARY),
        "file_count": len(files),
        "ok_file_count": sum(1 for item in files if item.get("ok")),
        "by_interval": dict(sorted(by_interval.items())),
        "instruments": {k: sorted(v) for k, v in sorted(by_instrument.items())},
    }


def yfinance_panel_fetch() -> dict[str, Any]:
    rows = []
    for symbol in YF_SYMBOLS:
        item: dict[str, Any] = {"symbol": symbol}
        try:
            df = yf.download(
                symbol,
                start="2000-01-01",
                end="2026-05-12",
                interval="1d",
                progress=False,
                auto_adjust=False,
                threads=False,
            )
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] for col in df.columns]
            item["ok"] = not df.empty
            item["rows"] = int(len(df))
            if not df.empty:
                idx = pd.to_datetime(df.index, utc=True, errors="coerce")
                item["start"] = str(idx.min())
                item["end"] = str(idx.max())
                item["last_close"] = float(df["Close"].dropna().iloc[-1])
            else:
                item["start"] = None
                item["end"] = None
        except Exception as exc:
            item["ok"] = False
            item["error"] = f"{type(exc).__name__}:{exc}"
        rows.append(item)

    out_path = PANEL_DIR / "yfinance_panel_fetch_summary_v1.json"
    summary = {
        "symbols": rows,
        "ok_symbols": [item["symbol"] for item in rows if item.get("ok")],
        "failed_symbols": [item for item in rows if not item.get("ok")],
    }
    out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"artifact": rel(out_path), **summary}


def build_completion_audit(
    source_panel: dict[str, Any],
    provider_summary: dict[str, Any],
    local_aq: dict[str, Any],
    yf_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    harness = provider_summary["harness_fetches"]
    provider_status = provider_summary["provider_status"]
    return [
        {
            "requirement": "Board B file remains the authoritative execution board.",
            "evidence": rel(BOARD),
            "status": "covered",
        },
        {
            "requirement": "Profitability factors must emit root-first branch paths.",
            "evidence": "Current board cursor and 183244 branch matrix preserve Bull/Bear/Sideways/Crisis branch rows.",
            "status": "covered_but_rejected",
        },
        {
            "requirement": "Auto-Quant evidence must be real, not inferred.",
            "evidence": "Prior 183244 branch matrix has 5198 real Auto-Quant/Freqtrade rows; this probe does not create a recipe.",
            "status": "covered_for_prior_candidate",
        },
        {
            "requirement": "Downstream filter/BBN/CatBoost/execution-tree branch promotion must only happen after RC-SPA pass.",
            "evidence": "Current branch matrix failed RC-SPA; downstream remains fail-closed.",
            "status": "blocked_correctly",
        },
        {
            "requirement": "Use provider evidence from yfinance, TradingViewRemix, IBKR, and Kraken before declaring data blocked.",
            "evidence": {
                "yfinance_status": provider_status["yfinance"]["summary_line"],
                "tradingview_status": provider_status["tradingview_mcp"]["summary_line"],
                "ibkr_status": provider_status["ibkr"]["summary_line"],
                "kraken_status": provider_status["kraken_public"]["summary_line"],
                "harness": harness,
            },
            "status": "covered",
        },
        {
            "requirement": "Broader crisis-capable panel must be available before another crisis-depth claim.",
            "evidence": {
                "source_panel_2021_2025": source_panel["window_2021_2025_by_root"],
                "dominant_daily_2021_2025": source_panel["dominant_daily_2021_2025_by_root"],
                "local_autoquant": local_aq,
                "yfinance_fetch": {
                    "artifact": yf_summary["artifact"],
                    "ok_symbols": yf_summary["ok_symbols"],
                    "failed_symbols": yf_summary["failed_symbols"],
                },
            },
            "status": "available_for_next_recipe_but_not_yet_scored",
        },
        {
            "requirement": "Objective can be marked complete.",
            "evidence": "No branch has passed RC-SPA and no promoted branch path has completed downstream consumption.",
            "status": "not_achieved",
        },
    ]


def write_markdown(report: dict[str, Any]) -> Path:
    md_path = RUN_ROOT / "crisis_panel_provider_probe_v1.md"
    providers = report["provider_summary"]["provider_status"]
    harness = report["provider_summary"]["harness_fetches"]
    decision = report["decision"]
    source = report["source_panel"]
    local = report["local_autoquant"]
    yf_summary = report["yfinance_panel_fetch"]

    lines = [
        "# Board B Crisis Panel Provider Probe v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Downstream: `{decision['downstream']}`",
        f"- Next action: {decision['next_action']}",
        f"- Completion: `{decision['completion_status']}`",
        "",
        "## Provider Readback",
        "",
        "| Provider | provider-status | harness fetch | Artifact |",
        "|---|---|---|---|",
    ]
    for provider, harness_name in [
        ("yfinance", "harness-yfinance-qqq-1d"),
        ("tradingview_mcp", "harness-tradingview-qqq-1d"),
        ("ibkr", "harness-ibkr-qqq-1d"),
        ("kraken_public", "harness-kraken-xbtusd-1d"),
    ]:
        h = harness[harness_name]
        fetch_status = f"ok={h['ok_count']} error={h['error_count']} stderr_bytes={h['stderr_bytes']}"
        lines.append(
            f"| `{provider}` | `{providers[provider]['summary_line']}` | `{fetch_status}` | `{h['stdout_artifact']}` |"
        )

    lines.extend(
        [
            "",
            "## Crisis Panel Coverage",
            "",
            f"- Source panel 2021-2025 by root: `{source['window_2021_2025_by_root']}`",
            f"- Dominant daily 2021-2025 by root: `{source['dominant_daily_2021_2025_by_root']}`",
            f"- Local Auto-Quant data files: `{local['ok_file_count']}/{local['file_count']}` readable; intervals `{local['by_interval']}`",
            f"- yfinance full-history fetch ok symbols: `{yf_summary['ok_symbols']}`",
            f"- yfinance full-history fetch failed symbols: `{yf_summary['failed_symbols']}`",
            "",
            "## Prompt-To-Artifact Checklist",
            "",
            "| Requirement | Status | Evidence |",
            "|---|---|---|",
        ]
    )
    for row in report["completion_audit"]:
        evidence = row["evidence"]
        if not isinstance(evidence, str):
            evidence = json.dumps(evidence, sort_keys=True)[:300]
        lines.append(f"| {row['requirement']} | `{row['status']}` | {evidence} |")

    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Report JSON: `{rel(RUN_ROOT / 'crisis_panel_provider_probe_v1.json')}`",
            f"- Provider status directory: `{rel(PROVIDER_DIR)}`",
            f"- Source panel counts: `{rel(PANEL_DIR / 'source_regime_root_counts_v1.json')}`",
            f"- Local Auto-Quant feather summary: `{rel(LOCAL_AQ_SUMMARY)}`",
            f"- yfinance fetch summary: `{yf_summary['artifact']}`",
            f"- Assertions: `{rel(CHECK_DIR / 'crisis_panel_provider_probe_v1_assertions.out')}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path


def main() -> int:
    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    provider_summary = summarize_provider_artifacts()
    source_panel = summarize_source_panel()
    (PANEL_DIR / "source_regime_root_counts_v1.json").write_text(
        json.dumps(source_panel, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    local_aq = summarize_local_autoquant_data()
    yf_summary = yfinance_panel_fetch()
    audit = build_completion_audit(source_panel, provider_summary, local_aq, yf_summary)

    yfinance_ok = provider_summary["harness_fetches"]["harness-yfinance-qqq-1d"]["ok_count"] > 0
    tv_ok = provider_summary["harness_fetches"]["harness-tradingview-qqq-1d"]["ok_count"] > 0
    local_ok = local_aq["ok_file_count"] > 0
    yf_panel_ok = len(yf_summary["ok_symbols"]) >= 6

    decision = {
        "gate_result": "not_started:panel_probe_no_recipe_scored",
        "downstream": "not_started:no_rc_spa_passing_recipe",
        "completion_status": "not_achieved",
        "fresh_provider_panel_available": bool(yfinance_ok and tv_ok and local_ok and yf_panel_ok),
        "next_action": (
            "B2R-repeat: synthesize and score a second root-aware recipe on the broader "
            "source-panel/yfinance equity-index daily universe with per-instrument roots; "
            "treat IBKR/Kraken as recorded support/unhealthy paths, not as blockers, and do "
            "not run downstream promotion unless branch RC-SPA passes."
        ),
    }

    report = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_root": rel(RUN_ROOT),
        "provider_summary": provider_summary,
        "source_panel": source_panel,
        "local_autoquant": local_aq,
        "yfinance_panel_fetch": yf_summary,
        "completion_audit": audit,
        "decision": decision,
    }
    report_path = RUN_ROOT / "crisis_panel_provider_probe_v1.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path = write_markdown(report)

    assertions = [
        f"run_id={RUN_ID}",
        f"report_json={rel(report_path)}",
        f"report_md={rel(md_path)}",
        f"yfinance_harness_ok={yfinance_ok}",
        f"tradingview_harness_ok={tv_ok}",
        f"local_autoquant_ok_files={local_aq['ok_file_count']}",
        f"yfinance_panel_ok_symbols={len(yf_summary['ok_symbols'])}",
        f"decision_gate={decision['gate_result']}",
        f"completion_status={decision['completion_status']}",
    ]
    if not yfinance_ok:
        assertions.append("ASSERT_FAIL:yfinance_harness_fetch_failed")
    if not local_ok:
        assertions.append("ASSERT_FAIL:local_autoquant_data_unreadable")
    if not yf_panel_ok:
        assertions.append("ASSERT_FAIL:yfinance_panel_fetch_too_thin")
    (CHECK_DIR / "crisis_panel_provider_probe_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 1 if any(line.startswith("ASSERT_FAIL") for line in assertions) else 0


if __name__ == "__main__":
    raise SystemExit(main())
