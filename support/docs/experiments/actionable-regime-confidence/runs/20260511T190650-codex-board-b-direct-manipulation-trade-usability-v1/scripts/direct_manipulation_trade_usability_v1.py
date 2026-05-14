#!/usr/bin/env python3
"""Board B direct Manipulation trade-usability audit.

This additive artifact checks whether already accepted Board A direct
Manipulation sources can be converted into Board B profitability rows without
inventing market PnL. It does not modify ict-engine runtime code, Auto-Quant,
or raw source data.
"""

from __future__ import annotations

import ast
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T190650+0800-codex-board-b-direct-manipulation-trade-usability-v1"
RUN_SLUG = "20260511T190650-codex-board-b-direct-manipulation-trade-usability-v1"


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_SLUG
OUT_DIR = RUN_ROOT / "direct-manipulation-trade-usability"
CHECK_DIR = RUN_ROOT / "checks"

BOARD_B = REPO_ROOT / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"
CONSUMER_MAP_CSV = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/"
    "regime_factor_consumer_map_v1.csv"
)
AUTO_QUANT_DATA = Path("/Users/thrill3r/Auto-Quant/user_data/data")

MEHRNOOM_JSON = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T045102-codex-mehrnoom-telegram-direct-manipulation-gate/"
    "direct-event-gate/mehrnoom_telegram_direct_manipulation_gate_report.json"
)
MEHRNOOM_PANEL_SAMPLE = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T045102-codex-mehrnoom-telegram-direct-manipulation-gate/"
    "direct-event-gate/mehrnoom_telegram_direct_manipulation_gate_panel_sample.csv"
)
ZENODO_SELF_JSON = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T101019-codex-zenodo-dex-selftrade-direct-gate/"
    "direct-gate/zenodo_dex_selftrade_direct_gate_report.json"
)
ZENODO_SELF_SAMPLE = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T101019-codex-zenodo-dex-selftrade-direct-gate/"
    "direct-gate/direct_manipulation_rows_sample.csv"
)
ZENODO_CONSEC_JSON = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T102332-codex-zenodo-dex-consecutive-selftrade-gate/"
    "direct-gate/zenodo_dex_consecutive_selftrade_gate.json"
)
ZENODO_CONSEC_SAMPLE = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T102332-codex-zenodo-dex-consecutive-selftrade-gate/"
    "direct-gate/direct_manipulation_rows_zenodo_dex_consecutive_sample.csv"
)
MIDSUMMER_BSC_JSON = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T111122-codex-midsummer-meme-direct-wash-audit/"
    "midsummer-meme-audit/midsummer_meme_direct_wash_audit.json"
)
MIDSUMMER_CHAIN_JSON = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T112642-codex-midsummer-chain-slice-expansion-audit/"
    "chain-slice-audit/midsummer_chain_slice_expansion_audit.json"
)

MEHRNOOM_RAW_ROOT = Path("/private/tmp/ict-regime-mehrnoom-pump-dump")
MEHRNOOM_COIN_PUMP = MEHRNOOM_RAW_ROOT / "Telegram/classified/coin-pump.csv"
MEHRNOOM_PRICE_EXTRACT = MEHRNOOM_RAW_ROOT / "Telegram/classified/price_extract.csv"

REPORT_JSON = OUT_DIR / "direct_manipulation_trade_usability_v1.json"
REPORT_MD = OUT_DIR / "direct_manipulation_trade_usability_v1.md"
SOURCE_CSV = OUT_DIR / "direct_manipulation_trade_usability_sources_v1.csv"
ASSERTIONS = CHECK_DIR / "direct_manipulation_trade_usability_v1_assertions.out"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def csv_header(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        try:
            return next(reader)
        except StopIteration:
            return []


def csv_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return max(0, sum(1 for _ in handle) - 1)


def has_pnl_columns(header: list[str]) -> bool:
    candidates = {
        "profit",
        "pnl",
        "return",
        "profit_ratio",
        "realized_r",
        "open_rate",
        "close_rate",
        "entry_price",
        "exit_price",
    }
    lowered = {item.strip().lower() for item in header}
    return bool(candidates & lowered)


def parse_list(value: str) -> list[float]:
    if not value:
        return []
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []
    out: list[float] = []
    for item in parsed:
        try:
            number = float(item)
        except (TypeError, ValueError):
            continue
        if number > 0.0:
            out.append(number)
    return out


def mehrnoom_price_profile() -> dict[str, Any]:
    profile = {
        "raw_root_exists": MEHRNOOM_RAW_ROOT.exists(),
        "coin_pump_rows": csv_count(MEHRNOOM_COIN_PUMP),
        "price_extract_rows": csv_count(MEHRNOOM_PRICE_EXTRACT),
        "buy_rows": 0,
        "sell_rows": 0,
        "both_buy_sell_rows": 0,
        "source_owned_entry_exit_pnl_rows": 0,
    }
    if not MEHRNOOM_PRICE_EXTRACT.exists():
        return profile
    with MEHRNOOM_PRICE_EXTRACT.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            buys = parse_list(row.get("Buy", ""))
            sells = parse_list(row.get("Sell", ""))
            if buys:
                profile["buy_rows"] += 1
            if sells:
                profile["sell_rows"] += 1
            if buys and sells:
                profile["both_buy_sell_rows"] += 1
                profile["source_owned_entry_exit_pnl_rows"] += 1
    return profile


def local_auto_quant_symbols() -> dict[str, Any]:
    files = sorted(path.name for path in AUTO_QUANT_DATA.glob("*.feather")) if AUTO_QUANT_DATA.exists() else []
    symbols = sorted({name.split("_", 1)[0] for name in files if "_" in name})
    return {
        "data_dir": str(AUTO_QUANT_DATA),
        "feather_files": files,
        "symbol_prefixes": symbols,
        "has_2017_2018_local_crypto_panel": False,
        "note": "local crypto OHLCV files start in 2021 for BTC/ETH/BNB/SOL/AVAX; Mehrnoom/Zenodo direct rows are 2017-2018.",
    }


def source_entry(
    name: str,
    json_path: Path,
    sample_path: Path | None,
    accepted_rows: int,
    negative_controls: int,
    event_range: str,
    trade_usable: bool,
    blockers: list[str],
) -> dict[str, Any]:
    header = csv_header(sample_path) if sample_path else []
    return {
        "source": name,
        "accepted_direct_rows": accepted_rows,
        "negative_control_rows": negative_controls,
        "event_range": event_range,
        "trade_usable_claimed_by_source_artifact": trade_usable,
        "sample_rows_committed": csv_count(sample_path) if sample_path else 0,
        "sample_has_pnl_or_entry_exit_columns": has_pnl_columns(header),
        "json_artifact": rel(json_path),
        "sample_artifact": rel(sample_path) if sample_path else "",
        "board_b_profitability_status": "blocked:not_trade_pnl_usable",
        "blockers": "; ".join(blockers),
    }


def load_consumer_map_manipulation() -> dict[str, Any]:
    with CONSUMER_MAP_CSV.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("regime") == "Manipulation":
                return row
    raise RuntimeError("Manipulation row missing from consumer map")


def build_report() -> dict[str, Any]:
    consumer_map_row = load_consumer_map_manipulation()
    mehrnoom = read_json(MEHRNOOM_JSON)
    zenodo_self = read_json(ZENODO_SELF_JSON)
    zenodo_consec = read_json(ZENODO_CONSEC_JSON)
    midsummer_bsc = read_json(MIDSUMMER_BSC_JSON)
    midsummer_chain = read_json(MIDSUMMER_CHAIN_JSON)
    mehrnoom_prices = mehrnoom_price_profile()

    zenodo_self_rows = int(zenodo_self.get("positive_self_trade_rows", 0))
    zenodo_self_controls = int(zenodo_self.get("negative_control_rows", 0))
    zenodo_consec_rows = int(zenodo_consec.get("positive_self_trade_rows", 0))
    zenodo_consec_controls = int(zenodo_consec.get("negative_control_rows", 0))
    midsummer_bsc_decision = midsummer_bsc.get("decision", {})
    midsummer_chain_decision = midsummer_chain.get("decision", {})

    sources = [
        source_entry(
            "mehrnoom_telegram_pump_events",
            MEHRNOOM_JSON,
            MEHRNOOM_PANEL_SAMPLE,
            int(mehrnoom["source_stats"]["coin_pump_csv"]["rows_after_dedupe"]),
            int(mehrnoom["source_stats"]["negative_controls"]["rows"]),
            f"{mehrnoom['source_stats']['coin_pump_csv']['date_min']}..{mehrnoom['source_stats']['coin_pump_csv']['date_max']}",
            bool(mehrnoom.get("trade_usable", False)),
            [
                "source says trade_usable=false",
                "price sidecar has buy levels but zero sell/exit rows",
                "local Auto-Quant crypto panel has no 2017-2018 overlap",
            ],
        ),
        source_entry(
            "zenodo_dex_self_trade",
            ZENODO_SELF_JSON,
            ZENODO_SELF_SAMPLE,
            zenodo_self_rows,
            zenodo_self_controls,
            "2017-02-09..2018-02-01",
            bool(zenodo_self.get("trade_usable", False)),
            [
                "source says trade_usable=false",
                "sample rows are order-lifecycle labels without realized PnL",
                "DEX token addresses are not mapped to local Auto-Quant pairs",
            ],
        ),
        source_entry(
            "zenodo_dex_consecutive_self_trade",
            ZENODO_CONSEC_JSON,
            ZENODO_CONSEC_SAMPLE,
            zenodo_consec_rows,
            zenodo_consec_controls,
            "2017-02-09..2018-02-01",
            bool(zenodo_consec.get("trade_usable", False)),
            [
                "source says trade_usable=false",
                "streamed rows are direct signatures, not source-owned trade PnL",
                "DEX token addresses are not mapped to local Auto-Quant pairs",
            ],
        ),
        source_entry(
            "midsummer_bsc_wash_maker",
            MIDSUMMER_BSC_JSON,
            None,
            int(midsummer_bsc_decision.get("accepted_direct_manipulation_rows_added", 0)),
            0,
            "2021-09-28..2025-02-04",
            bool(midsummer_bsc_decision.get("trade_usable", False)),
            [
                "source says trade_usable=false",
                "unit is maker-token-day direct wash evidence",
                "no source-owned executable entry/exit PnL artifact",
            ],
        ),
        source_entry(
            "midsummer_multichain_wash_maker",
            MIDSUMMER_CHAIN_JSON,
            None,
            int(midsummer_chain_decision.get("accepted_direct_manipulation_rows_added", 0)),
            0,
            "2023-05-01..2025-02-04 across accepted slices",
            bool(midsummer_chain_decision.get("trade_usable", False)),
            [
                "source says trade_usable=false",
                "unit is maker-token-day direct wash evidence",
                "no source-owned executable entry/exit PnL artifact",
            ],
        ),
    ]

    accepted_rows = sum(row["accepted_direct_rows"] for row in sources)
    trade_usable_sources = [row for row in sources if row["trade_usable_claimed_by_source_artifact"]]
    pnl_sample_sources = [row for row in sources if row["sample_has_pnl_or_entry_exit_columns"]]
    board_b_trade_usable = bool(trade_usable_sources and pnl_sample_sources and mehrnoom_prices["source_owned_entry_exit_pnl_rows"] > 0)
    decision = {
        "gate_result": "blocked:accepted_direct_manipulation_sources_not_board_b_trade_pnl_usable",
        "accepted_direct_rows_seen": accepted_rows,
        "sources_checked": len(sources),
        "trade_usable_sources": len(trade_usable_sources),
        "sample_sources_with_pnl_or_entry_exit_columns": len(pnl_sample_sources),
        "board_b_profitability_rows_added": 0,
        "board_b_trade_usable": board_b_trade_usable,
        "downstream_consumption": "not_started:no_trade_usable_manipulation_profit_rows",
        "next_action": (
            "For scoped Manipulation, require a source-owned or provider-reconstructed "
            "entry/exit PnL bridge before adding Board B RC-SPA rows; otherwise keep "
            "accepted direct rows as suppression/abstain overlay only."
        ),
    }
    return {
        "schema_version": "board-b-direct-manipulation-trade-usability/v1",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_b": rel(BOARD_B),
        "consumer_map": rel(CONSUMER_MAP_CSV),
        "consumer_map_manipulation_row": consumer_map_row,
        "local_auto_quant": local_auto_quant_symbols(),
        "mehrnoom_price_profile": mehrnoom_prices,
        "sources": sources,
        "decision": decision,
        "completion": {
            "runtime_code_changed": False,
            "auto_quant_checkout_changed": False,
            "raw_data_committed": False,
            "thresholds_relaxed": False,
            "board_b_cursor_superseded": False,
        },
        "artifacts": {
            "json": rel(REPORT_JSON),
            "md": rel(REPORT_MD),
            "sources_csv": rel(SOURCE_CSV),
            "assertions": rel(ASSERTIONS),
        },
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_md(report: dict[str, Any]) -> None:
    decision = report["decision"]
    lines = [
        "# Direct Manipulation Trade-Usability v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Accepted direct rows seen: `{decision['accepted_direct_rows_seen']}`",
        f"- Sources checked: `{decision['sources_checked']}`",
        f"- Trade-usable sources: `{decision['trade_usable_sources']}`",
        f"- Board B profitability rows added: `{decision['board_b_profitability_rows_added']}`",
        f"- Downstream consumption: `{decision['downstream_consumption']}`",
        "",
        "## Why This Does Not Repair RC-SPA",
        "",
        "- Board A has accepted direct `Manipulation` context rows.",
        "- The accepted source artifacts mark them as `trade_usable=false` or provide labels without executable entry/exit PnL.",
        "- The Mehrnoom price sidecar has buy levels but no sell/exit rows, so source-owned realized PnL cannot be computed from it.",
        "- Local Auto-Quant crypto OHLCV coverage starts in 2021, while the Telegram/Zenodo direct rows are 2017-2018; Midsummer rows are maker-token-day wash evidence without local pair mapping.",
        "",
        "## Source Checks",
        "",
        "| Source | Accepted Rows | Controls | Trade Usable | Sample Has PnL Columns | Status |",
        "|---|---:|---:|---|---|---|",
    ]
    for row in report["sources"]:
        lines.append(
            f"| `{row['source']}` | {row['accepted_direct_rows']} | {row['negative_control_rows']} | "
            f"`{row['trade_usable_claimed_by_source_artifact']}` | "
            f"`{row['sample_has_pnl_or_entry_exit_columns']}` | `{row['board_b_profitability_status']}` |"
        )
    profile = report["mehrnoom_price_profile"]
    lines.extend(
        [
            "",
            "## Mehrnoom Price Sidecar",
            "",
            f"- Rows: `{profile['price_extract_rows']}`",
            f"- Buy rows: `{profile['buy_rows']}`",
            f"- Sell rows: `{profile['sell_rows']}`",
            f"- Both buy/sell rows: `{profile['both_buy_sell_rows']}`",
            "",
            "## Next",
            "",
            f"- {decision['next_action']}",
        ]
    )
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    for required in [
        CONSUMER_MAP_CSV,
        MEHRNOOM_JSON,
        ZENODO_SELF_JSON,
        ZENODO_CONSEC_JSON,
        MIDSUMMER_BSC_JSON,
        MIDSUMMER_CHAIN_JSON,
    ]:
        if not required.exists():
            raise FileNotFoundError(required)

    report = build_report()
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    write_csv(SOURCE_CSV, report["sources"])
    write_md(report)

    decision = report["decision"]
    assertions = [
        f"run_id={RUN_ID}",
        f"sources_checked={decision['sources_checked']}",
        f"accepted_direct_rows_seen={decision['accepted_direct_rows_seen']}",
        f"board_b_profitability_rows_added={decision['board_b_profitability_rows_added']}",
        f"gate_result={decision['gate_result']}",
        f"downstream_consumption={decision['downstream_consumption']}",
        f"report_json={rel(REPORT_JSON)}",
        f"report_md={rel(REPORT_MD)}",
    ]
    ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "decision": decision, "report": rel(REPORT_MD)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
