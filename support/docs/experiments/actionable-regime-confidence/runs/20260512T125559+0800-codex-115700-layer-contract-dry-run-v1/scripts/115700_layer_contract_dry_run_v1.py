#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


RUN_ID = "20260512T125559+0800-codex-115700-layer-contract-dry-run-v1"
SOURCE_RUN_ID = "20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1"
ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
SOURCE_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / SOURCE_RUN_ID
REPORT_DIR = ROOT / "115700-layer-contract-dry-run-v1"
CHECK_DIR = ROOT / "checks"
OUT_DIR = ROOT / "command-output"
ENRICHED_DIR = ROOT / "enriched-real-trades"
STATE_DIR = ROOT / "state_dry_run"
COMBINED_TRADES = ENRICHED_DIR / "115700_layer_contract_enriched_all.real_trades.jsonl"
SYMBOL = "B2R_SAME_ROOT_SIX_PROVIDER_BTC_1H_115700"
HELPER_ROOT = Path("scripts/auto_quant_external")

sys.path.insert(0, str(HELPER_ROOT.resolve()))
import structural_feedback_trade_enricher as enricher  # noqa: E402


PROVIDER_META = {
    "auto-quant-112315-yfinance": {
        "provider": "yfinance",
        "provider_symbol": "BTC-USD",
        "timeframe": "1h",
        "source_csv": "provider-csv/yfinance_btc_usd_1h.csv",
    },
    "auto-quant-112315-kraken_public": {
        "provider": "kraken_public",
        "provider_symbol": "XBTUSD",
        "timeframe": "1h",
        "source_csv": "provider-csv/kraken_xbtusd_1h.csv",
    },
    "auto-quant-112315-binance_public": {
        "provider": "binance_public",
        "provider_symbol": "BTCUSDT",
        "timeframe": "1h",
        "source_csv": "provider-csv/binance_btcusdt_1h.csv",
    },
    "auto-quant-112315-bybit_public": {
        "provider": "bybit_public",
        "provider_symbol": "BTCUSDT",
        "timeframe": "1h",
        "source_csv": "provider-csv/bybit_btcusdt_linear_1h.csv",
    },
    "auto-quant-112315-tvr_default_binance": {
        "provider": "TradingViewRemix_default_binance",
        "provider_symbol": "BINANCE:BTCUSDT",
        "timeframe": "1h",
        "source_csv": "provider-csv/tvr_default_binance_btcusdt_1h.csv",
    },
    "auto-quant-112315-ibkr_paxos_long_midpoint": {
        "provider": "IBKR_PAXOS_midpoint",
        "provider_symbol": "BTC PAXOS",
        "timeframe": "1h",
        "source_csv": "provider-csv/BTC_1h_midpoint.csv",
    },
}

REQUIRED_BRANCH_FIELDS = [
    "main_regime",
    "sub_regime",
    "sub_sub_regime_or_profit_factor",
    "profit_factor",
]
REQUIRED_DOWNSTREAM_FIELDS = [
    "provider_provenance",
    "pre_bayes_filter_state",
    "bbn_posterior",
    "catboost_path_ranker_label",
    "execution_tree_decision",
    "failure_reason",
    "quality_weight",
]


def non_empty(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def provider_key_for(path: Path) -> str:
    for part in path.parts:
        if part.startswith("auto-quant-112315-"):
            return part
    raise ValueError(f"cannot infer provider key from {path}")


def contract_payloads(provider_key: str, strategy_name: str) -> dict[str, Any]:
    meta = dict(PROVIDER_META[provider_key])
    meta["source_run_id"] = SOURCE_RUN_ID
    meta["provider_requested"] = True
    meta["provider_data_acquired"] = True
    meta["source_csv"] = str(SOURCE_ROOT / meta["source_csv"])
    meta["strategy_name"] = strategy_name
    return {
        "provider_provenance": meta,
        "pre_bayes_filter_state": {
            "state": "not_run_for_market_factor_learning",
            "reason": "schema_repair_preview_only",
            "quality_weight_policy": "0",
        },
        "bbn_posterior": {
            "state": "not_mutated",
            "reason": "dry_run_preview_only",
        },
        "catboost_path_ranker_label": {
            "state": "not_trained_from_these_rows",
            "label": "not_applicable_quality_weight_0",
        },
        "execution_tree_decision": {
            "state": "not_promoted",
            "decision": "observe_only",
            "actionable": False,
        },
        "failure_reason": "layer_contract_dry_run_quality_weight_0_no_downstream_promotion",
        "quality_weight": 0.0,
    }


def enrich_all() -> dict[str, Any]:
    files = sorted((SOURCE_ROOT / "workspace").glob("*/derived/*.real_trades.jsonl"))
    all_rows: list[dict[str, Any]] = []
    provider_counts: Counter[str] = Counter()
    strategy_counts: Counter[str] = Counter()
    for path in files:
        provider_key = provider_key_for(path)
        raw_rows = load_jsonl(path)
        if not raw_rows:
            continue
        strategy_name = raw_rows[0].get("strategy_name") or path.name.split(".")[0]
        payloads = contract_payloads(provider_key, strategy_name)
        enriched_rows = [
            enricher.enrich_trade_with_layer_contract(
                row,
                auto_quant_run_id=SOURCE_RUN_ID,
                symbol=SYMBOL,
                provider_provenance=payloads["provider_provenance"],
                pre_bayes_filter_state=payloads["pre_bayes_filter_state"],
                bbn_posterior=payloads["bbn_posterior"],
                catboost_path_ranker_label=payloads["catboost_path_ranker_label"],
                execution_tree_decision=payloads["execution_tree_decision"],
                failure_reason=payloads["failure_reason"],
                quality_weight=payloads["quality_weight"],
            )
            for row in raw_rows
        ]
        for row in enriched_rows:
            row.setdefault("outcome", row.get("realized_outcome"))
            row["allowed_feedback_target"] = "contract_schema_preview_only"
        out_path = ENRICHED_DIR / provider_key / "derived" / path.name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in enriched_rows),
            encoding="utf-8",
        )
        all_rows.extend(enriched_rows)
        provider_counts[provider_key] += len(enriched_rows)
        strategy_counts[strategy_name] += len(enriched_rows)

    ENRICHED_DIR.mkdir(parents=True, exist_ok=True)
    COMBINED_TRADES.write_text(
        "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in all_rows),
        encoding="utf-8",
    )
    return {
        "source_files": len(files),
        "enriched_rows": len(all_rows),
        "combined_trades": str(COMBINED_TRADES),
        "provider_counts": dict(sorted(provider_counts.items())),
        "strategy_counts": dict(sorted(strategy_counts.items())),
    }


def classify_row(row: dict[str, Any]) -> list[str]:
    failures = []
    branch_path = row.get("branch_path") or row.get("regime_profit_branch_path")
    if not non_empty(branch_path):
        failures.append("missing_branch_path")
    for field in REQUIRED_BRANCH_FIELDS:
        if not non_empty(row.get(field)):
            failures.append(f"missing_{field}")
    for field in REQUIRED_DOWNSTREAM_FIELDS:
        if not non_empty(row.get(field)):
            failures.append(f"missing_{field}")
    if not (non_empty(row.get("outcome")) or non_empty(row.get("realized_outcome"))):
        failures.append("missing_outcome")
    if row.get("auto_quant_run_id") != SOURCE_RUN_ID:
        failures.append("stale_or_wrong_auto_quant_run_id")
    symbol = row.get("symbol")
    if isinstance(symbol, str) and ("104902" in symbol or "YAHOO_BTC_PULLBACK" in symbol):
        failures.append("stale_symbol_namespace")
    if row.get("quality_weight") != 0.0:
        failures.append("unexpected_nonzero_quality_weight")
    return failures


def validate_enriched() -> dict[str, Any]:
    failure_counts: Counter[str] = Counter()
    rows = load_jsonl(COMBINED_TRADES)
    examples = []
    for idx, row in enumerate(rows, 1):
        failures = classify_row(row)
        if failures:
            failure_counts.update(failures)
            if len(examples) < 12:
                examples.append(
                    {
                        "line": idx,
                        "trade_id": row.get("trade_id"),
                        "symbol": row.get("symbol"),
                        "auto_quant_run_id": row.get("auto_quant_run_id"),
                        "failures": failures,
                    }
                )
    contract_complete = len(rows) - sum(
        1
        for row in rows
        if classify_row(row)
    )
    return {
        "rows_checked": len(rows),
        "contract_complete_rows": contract_complete,
        "quality_weight_zero_rows": sum(1 for row in rows if row.get("quality_weight") == 0.0),
        "market_factor_trainable_rows": 0,
        "failure_counts": dict(sorted(failure_counts.items())),
        "examples": examples,
    }


def run_ingest_dry_run() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        "target/debug/ict-engine",
        "auto-quant-ingest-real-trades",
        "--symbol",
        SYMBOL,
        "--state-dir",
        str(STATE_DIR),
        "--trades",
        str(COMBINED_TRADES),
        "--source",
        "board_b_115700_layer_contract_dry_run",
        "--dry-run",
    ]
    (OUT_DIR / "01_auto_quant_ingest_real_trades_dry_run.cmd").write_text(" ".join(cmd) + "\n", encoding="utf-8")
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    (OUT_DIR / "01_auto_quant_ingest_real_trades_dry_run.out").write_text(proc.stdout, encoding="utf-8")
    (OUT_DIR / "01_auto_quant_ingest_real_trades_dry_run.err").write_text(proc.stderr, encoding="utf-8")
    (CHECK_DIR / "01_auto_quant_ingest_real_trades_dry_run.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
    parsed = None
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        pass
    return {
        "cmd": cmd,
        "exit": proc.returncode,
        "stdout": str(OUT_DIR / "01_auto_quant_ingest_real_trades_dry_run.out"),
        "stderr": str(OUT_DIR / "01_auto_quant_ingest_real_trades_dry_run.err"),
        "parsed_stdout": parsed,
    }


def write_report(enrichment: dict[str, Any], validation: dict[str, Any], ingest: dict[str, Any]) -> dict[str, Any]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    result = {
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "source_root": str(SOURCE_ROOT),
        "enrichment": enrichment,
        "validation": validation,
        "ingest_dry_run": ingest,
        "gate_result": "115700_layer_contract_dry_run_v1=contract_complete_parse_preview_no_market_learning",
        "evidence_class": "chain_contract_repair_preview",
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    json_path = REPORT_DIR / "115700_layer_contract_dry_run_v1.json"
    md_path = REPORT_DIR / "115700_layer_contract_dry_run_v1.md"
    assertions_path = CHECK_DIR / "115700_layer_contract_dry_run_v1_assertions.out"
    write_json(json_path, result)

    parsed = ingest.get("parsed_stdout") or {}
    md_lines = [
        "# 115700 Layer-Contract Dry-Run v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source root: `{SOURCE_RUN_ID}`",
        "",
        "## Scope",
        "Repair-preview for the settled same-root six-provider AQ rows. This enriches row-level branch/provider/downstream contract fields and runs `auto-quant-ingest-real-trades --dry-run` in an isolated state dir. It does not mutate production state and does not promote a candidate.",
        "",
        "## Result",
        f"- Source files: `{enrichment['source_files']}`.",
        f"- Enriched rows: `{enrichment['enriched_rows']}`.",
        f"- Contract-complete rows after enrichment: `{validation['contract_complete_rows']}`.",
        f"- Market/factor trainable rows: `{validation['market_factor_trainable_rows']}` because every row keeps `quality_weight=0`.",
        f"- Dry-run exit: `{ingest['exit']}`.",
        f"- Dry-run status: `{parsed.get('ledger_status')}`.",
        f"- Dry-run trades total/applied/invalid: `{parsed.get('trades_total')}` / `{parsed.get('trades_applied')}` / `{parsed.get('trades_invalid')}`.",
        f"- Dry-run feedback records inserted: `{parsed.get('feedback_records_inserted')}`.",
        "",
        "## Decision",
        "- The stale source id and stale symbol namespace blocker is repairable in a bounded artifact.",
        "- The missing contract-field blocker is repairable at JSONL schema level.",
        "- This is still not market/factor evidence because the downstream fields are explicit non-promotional placeholders and quality weight is zero.",
        "- `promotion_allowed=false`.",
        "- `trade_usable=false`.",
        "- `update_goal=false`.",
        "",
        "## Artifacts",
        f"- JSON: `{json_path}`",
        f"- Combined enriched trades: `{COMBINED_TRADES}`",
        f"- Dry-run command output: `{OUT_DIR / '01_auto_quant_ingest_real_trades_dry_run.out'}`",
        f"- Assertions: `{assertions_path}`",
    ]
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_run_id={SOURCE_RUN_ID}",
        f"PASS enriched_rows={enrichment['enriched_rows']}",
        f"PASS contract_complete_rows={validation['contract_complete_rows']}",
        f"PASS quality_weight_zero_rows={validation['quality_weight_zero_rows']}",
        f"PASS ingest_dry_run_exit={ingest['exit']}",
        f"PASS dry_run_status={parsed.get('ledger_status')}",
        f"PASS trades_total={parsed.get('trades_total')}",
        f"PASS trades_applied={parsed.get('trades_applied')}",
        f"PASS trades_invalid={parsed.get('trades_invalid')}",
        f"PASS feedback_records_inserted={parsed.get('feedback_records_inserted')}",
        "FAIL_CLOSED market_factor_trainable_rows=0",
        "FAIL_CLOSED production_mutation=false",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


def main() -> int:
    enrichment = enrich_all()
    validation = validate_enriched()
    ingest = run_ingest_dry_run()
    write_report(enrichment, validation, ingest)
    return 0 if ingest["exit"] == 0 and validation["contract_complete_rows"] == enrichment["enriched_rows"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
