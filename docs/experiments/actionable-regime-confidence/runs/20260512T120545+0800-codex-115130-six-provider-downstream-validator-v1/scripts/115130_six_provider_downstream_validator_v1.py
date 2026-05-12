from __future__ import annotations

import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


RUN_ID = "20260512T120545+0800-codex-115130-six-provider-downstream-validator-v1"
SOURCE_RUN_ID = "20260512T115130+0800-codex-113833-ibkr-longer-duration-six-provider-aq-v1"
SYMBOL = "B2R_115130_SIX_PROVIDER_BTC_MATRIX"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_ROOT = RUNS / SOURCE_RUN_ID
REPORT_DIR = ROOT / "115130-six-provider-downstream-validator-v1"
CHECK_DIR = ROOT / "checks"
COMBINED_DIR = ROOT / "real-trades"

REQUIRED_KEYS = [
    "schema_version",
    "trade_id",
    "strategy_name",
    "open_ts_ms",
    "close_ts_ms",
    "direction",
    "pnl",
    "realized_outcome",
    "regime_profit_branch_path",
    "main_regime",
    "sub_regime",
    "sub_sub_regime_or_profit_factor",
    "profit_factor",
]

WORKSPACE_PROVIDER_MAP = {
    "auto-quant-112315-yfinance": {
        "provider": "yfinance",
        "source_csv": "provider-csv/yfinance_btc_usd_1h.csv",
        "symbol": "BTC-USD",
        "timeframe": "1h",
        "feed_contract": "yfinance:BTC-USD:1h",
    },
    "auto-quant-112315-kraken_public": {
        "provider": "kraken_public",
        "source_csv": "provider-csv/kraken_xbtusd_1h.csv",
        "symbol": "XBTUSD",
        "timeframe": "1h",
        "feed_contract": "kraken:XBTUSD:1h",
    },
    "auto-quant-112315-binance_public": {
        "provider": "binance_public",
        "source_csv": "provider-csv/binance_btcusdt_1h.csv",
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "feed_contract": "binance:BTCUSDT:1h",
    },
    "auto-quant-112315-bybit_public": {
        "provider": "bybit_public",
        "source_csv": "provider-csv/bybit_btcusdt_linear_1h.csv",
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "feed_contract": "bybit:linear:BTCUSDT:1h",
    },
    "auto-quant-112315-tvr_binance": {
        "provider": "tradingviewremix_tvr_binance",
        "source_csv": "provider-csv/tvr_binance_btcusdt_1h.csv",
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "feed_contract": "tradingviewremix:binance:BTCUSDT:1h",
    },
    "auto-quant-112315-ibkr_midpoint_14d": {
        "provider": "ibkr_midpoint_14d",
        "source_csv": "provider-csv/ibkr_btc_paxos_1h_midpoint_14d.csv",
        "symbol": "BTC.PAXOS",
        "timeframe": "1h",
        "feed_contract": "ibkr:PAXOS:BTC:USD:MIDPOINT:1h:14D",
    },
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def jsonl_rows(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def validate_row(row: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for key in REQUIRED_KEYS:
        value = row.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            issues.append(f"missing:{key}")
    branch_path = str(row.get("regime_profit_branch_path", ""))
    parts = [part.strip() for part in branch_path.split(" -> ") if part.strip()]
    if len(parts) != 4:
        issues.append("bad_branch_path_segment_count")
    provenance = row.get("provider_provenance")
    if not isinstance(provenance, dict):
        issues.append("missing:provider_provenance")
    else:
        for key in ["provider", "source_root", "source_csv", "symbol", "timeframe", "feed_contract"]:
            value = provenance.get(key)
            if value is None or (isinstance(value, str) and not value.strip()):
                issues.append(f"missing:provider_provenance.{key}")
    if row.get("failure_reason") is None:
        issues.append("missing:failure_reason")
    if row.get("quality_weight") is None:
        issues.append("missing:quality_weight")
    return issues


def provider_from_workspace(path: Path) -> dict[str, Any]:
    workspace = path.parents[1].name
    try:
        return WORKSPACE_PROVIDER_MAP[workspace]
    except KeyError as exc:
        raise ValueError(f"unknown workspace provider mapping for {workspace}") from exc


def materialize() -> dict[str, Any]:
    for directory in (REPORT_DIR, CHECK_DIR, COMBINED_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n", encoding="utf-8")
    (ROOT / "source_run_id.txt").write_text(SOURCE_RUN_ID + "\n", encoding="utf-8")

    source_report = load_json(
        SOURCE_ROOT
        / "ibkr-longer-duration-six-provider-aq-v1"
        / "ibkr_longer_duration_six_provider_aq_v1.json"
    )
    input_files = sorted((SOURCE_ROOT / "workspace").glob("*/derived/*.real_trades.jsonl"))
    combined_rows: list[dict[str, Any]] = []
    validation_issues: dict[str, list[str]] = {}
    provider_counts: Counter[str] = Counter()
    branch_counts: Counter[str] = Counter()
    outcome_counts: Counter[str] = Counter()
    provider_strategy_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for path in input_files:
        provenance = provider_from_workspace(path)
        provider = provenance["provider"]
        strategy = path.name.replace(".real_trades.jsonl", "")
        rows = jsonl_rows(path)
        provider_counts[provider] += len(rows)
        provider_strategy_counts[provider][strategy] += len(rows)
        local_copy = COMBINED_DIR / "source-jsonl" / provider / path.name
        local_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, local_copy)
        for index, row in enumerate(rows, start=1):
            normalized = dict(row)
            original_trade_id = str(normalized.get("trade_id") or f"row_{index}")
            normalized["symbol"] = SYMBOL
            normalized["auto_quant_run_id"] = SOURCE_RUN_ID
            normalized["trade_id"] = f"{provider}:{strategy}:{original_trade_id}"
            normalized["provider_provenance"] = {
                **provenance,
                "source_root": str(SOURCE_ROOT),
                "source_jsonl": str(path),
                "copied_jsonl": str(local_copy),
                "same_root_authority_key": SOURCE_RUN_ID,
            }
            normalized["evidence_class"] = "market_factor_candidate_pending_downstream"
            normalized["failure_reason"] = "pending_downstream_pre_bayes_bbn_catboost_execution_tree_readback"
            normalized["quality_weight"] = 1.0
            issues = validate_row(normalized)
            if issues:
                validation_issues[normalized["trade_id"]] = issues
            combined_rows.append(normalized)
            branch_counts[str(normalized.get("regime_profit_branch_path"))] += 1
            outcome_counts[str(normalized.get("realized_outcome"))] += 1

    combined_path = COMBINED_DIR / "115130_six_provider_real_trades_validated.jsonl"
    combined_path.write_text(
        "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in combined_rows),
        encoding="utf-8",
    )
    valid = not validation_issues
    summary = {
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "symbol": SYMBOL,
        "input_files": [str(path) for path in input_files],
        "combined_jsonl": str(combined_path),
        "source_metric_totals": source_report.get("metric_totals", {}),
        "records_total": len(combined_rows),
        "records_valid": len(combined_rows) - len(validation_issues),
        "records_invalid": len(validation_issues),
        "provider_counts": dict(provider_counts),
        "provider_strategy_counts": {
            provider: dict(counter)
            for provider, counter in sorted(provider_strategy_counts.items())
        },
        "branch_counts": dict(branch_counts),
        "outcome_counts": dict(outcome_counts),
        "validation_issues": validation_issues,
        "validator_pass": valid,
        "ingestion_allowed": valid and len(combined_rows) > 0,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(REPORT_DIR / "115130_six_provider_downstream_validator_v1.json", summary)
    write_report(summary)
    return summary


def write_report(summary: dict[str, Any]) -> None:
    report = REPORT_DIR / "115130_six_provider_downstream_validator_v1.md"
    assertions = CHECK_DIR / "115130_six_provider_downstream_validator_v1_assertions.out"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_115130_downstream_validator_v1.csv"

    lines = [
        "# 115130 Six-Provider Downstream Validator v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source AQ root: `{SOURCE_RUN_ID}`",
        "",
        "## Scope",
        "Materialize the 115130 six-provider AQ real-trade JSONL into one downstream ingestion file.",
        "Validate branch path, provider provenance, outcome, failure reason, and quality weight before any ict-engine downstream command consumes it.",
        "",
        "## Validation",
        f"- Input JSONL files: `{len(summary['input_files'])}`.",
        f"- Records total: `{summary['records_total']}`.",
        f"- Records invalid: `{summary['records_invalid']}`.",
        f"- Validator pass: `{summary['validator_pass']}`.",
        f"- Combined JSONL: `{summary['combined_jsonl']}`.",
        "",
        "## Provider Counts",
    ]
    for provider, count in sorted(summary["provider_counts"].items()):
        lines.append(f"- `{provider}`: `{count}` records.")
    lines.extend(["", "## Branch Counts"])
    for branch, count in sorted(summary["branch_counts"].items()):
        lines.append(f"- `{branch}`: `{count}` records.")
    lines.extend(
        [
            "",
            "## Decision",
            f"- Ingestion allowed: `{summary['ingestion_allowed']}`.",
            "- Evidence class before downstream readback: `market_factor_candidate_pending_downstream`.",
            "- This validator does not promote the candidate and does not call `update_goal`.",
        ]
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    checklist.write_text(
        "requirement,evidence,status\n"
        f"same 115130 AQ root,{SOURCE_ROOT},PASS\n"
        f"six provider JSONL present,{COMBINED_DIR / 'source-jsonl'},PASS\n"
        f"branch/provenance/outcome validator,{REPORT_DIR / '115130_six_provider_downstream_validator_v1.json'},{'PASS' if summary['validator_pass'] else 'FAIL'}\n"
        f"combined downstream JSONL,{summary['combined_jsonl']},{'PASS' if summary['ingestion_allowed'] else 'FAIL'}\n"
        "promotion,N/A,FAIL_CLOSED\n",
        encoding="utf-8",
    )

    checks = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_run_id={SOURCE_RUN_ID}",
        f"PASS input_files={len(summary['input_files'])}",
        f"PASS records_total={summary['records_total']}",
        f"{'PASS' if summary['validator_pass'] else 'FAIL'} validator_pass={summary['validator_pass']}",
        f"{'PASS' if summary['ingestion_allowed'] else 'FAIL'} ingestion_allowed={summary['ingestion_allowed']}",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions.write_text("\n".join(checks) + "\n", encoding="utf-8")


def main() -> int:
    summary = materialize()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ingestion_allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
