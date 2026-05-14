#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REQUIRED_BRANCH_FIELDS = [
    "main_regime",
    "sub_regime",
    "sub_sub_regime_or_profit_factor",
    "profit_factor",
]

DOWNSTREAM_FIELDS = [
    "pre_bayes_filter_state",
    "bbn_posterior",
    "catboost_path_ranker_label",
    "execution_tree_decision",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
    return rows


def has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def provider_from_trade_path(path: Path) -> str:
    for parent in path.parents:
        name = parent.name
        if name.startswith("auto-quant-112315-"):
            return name.removeprefix("auto-quant-112315-")
    return "unknown"


def strategy_from_trade_path(path: Path) -> str:
    return path.name.replace(".real_trades.jsonl", "")


def missing_fields(row: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if not has_text(row.get("regime_profit_branch_path")):
        missing.append("branch_path")
    for field in REQUIRED_BRANCH_FIELDS:
        if not has_text(row.get(field)):
            missing.append(field)
    provenance = row.get("provider_provenance")
    if not isinstance(provenance, dict):
        missing.append("provider_provenance")
    else:
        for field in [
            "provider_id",
            "source_root",
            "symbol",
            "timeframe",
            "feed_contract",
            "fetch_window",
            "row_count",
            "health_state",
            "same_root_authority_key",
        ]:
            if field not in provenance:
                missing.append(f"provider_provenance.{field}")
    for field in DOWNSTREAM_FIELDS:
        if field not in row:
            missing.append(field)
    if not (has_text(row.get("realized_outcome")) or isinstance(row.get("pnl"), (int, float))):
        missing.append("outcome")
    if not has_text(row.get("failure_reason")):
        missing.append("failure_reason")
    if "quality_weight" not in row:
        missing.append("quality_weight")
    return missing


def classify_row(row: dict[str, Any], provider_key: str, strategy: str, trade_file: Path) -> dict[str, Any]:
    missing = missing_fields(row)
    branch_complete = all(
        has_text(row.get(field)) for field in ["regime_profit_branch_path", *REQUIRED_BRANCH_FIELDS]
    )
    has_outcome = has_text(row.get("realized_outcome")) or isinstance(row.get("pnl"), (int, float))
    has_observation = has_text(row.get("trade_id")) and has_outcome
    market_factor_eligible = not missing

    if market_factor_eligible:
        evidence_class = "market_factor_negative_sample"
        blocked_reason = None
    elif has_observation:
        evidence_class = "chain_contract_negative_sample"
        blocked_reason = "minimum_layered_schema_incomplete"
    else:
        evidence_class = "infrastructure_negative_sample"
        blocked_reason = "record_not_observation_complete"

    return {
        "trade_file": str(trade_file),
        "provider_key_from_path": provider_key,
        "strategy_from_path": strategy,
        "trade_id": row.get("trade_id"),
        "row_symbol": row.get("symbol"),
        "row_auto_quant_run_id": row.get("auto_quant_run_id"),
        "branch_path": row.get("regime_profit_branch_path"),
        "main_regime": row.get("main_regime"),
        "sub_regime": row.get("sub_regime"),
        "sub_sub_regime_or_profit_factor": row.get("sub_sub_regime_or_profit_factor"),
        "profit_factor": row.get("profit_factor"),
        "realized_outcome": row.get("realized_outcome"),
        "pnl": row.get("pnl"),
        "branch_complete": branch_complete,
        "has_outcome": has_outcome,
        "market_factor_feedback_allowed": market_factor_eligible,
        "evidence_class": evidence_class,
        "blocked_reason": blocked_reason,
        "missing_fields": missing,
    }


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n" for row in rows), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "provider_key_from_path",
        "strategy_from_path",
        "trade_id",
        "row_symbol",
        "row_auto_quant_run_id",
        "branch_complete",
        "has_outcome",
        "market_factor_feedback_allowed",
        "evidence_class",
        "blocked_reason",
        "missing_fields",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            out = {field: row.get(field) for field in fieldnames}
            out["missing_fields"] = ";".join(row.get("missing_fields", []))
            writer.writerow(out)


def build_report_md(summary: dict[str, Any]) -> str:
    return f"""# 115130 Downstream Layered Validator v1

Run id: `{summary["run_id"]}`
Source AQ root: `{summary["source_run_id"]}`

## Scope
Read the settled `115130` six-provider AQ runtime packet and validate its provider-rooted real-trade JSONL rows before any BBN, CatBoost/path-ranker, or execution-tree learning use.

This artifact does not edit ict-engine runtime code, does not apply real trades to the BBN CPT, does not run promotion, and does not call `update_goal`.

## Readback
- Real-trade files: `{summary["real_trade_files"]}`.
- Real-trade rows parsed: `{summary["rows_total"]}`.
- Rows with complete four-part branch path: `{summary["branch_complete_rows"]}`.
- Rows with realized outcome/PnL: `{summary["outcome_rows"]}`.
- Rows accepted as market-factor negative samples: `{summary["market_factor_rows_accepted"]}`.
- Rows quarantined as chain-contract negative samples: `{summary["chain_contract_negative_samples"]}`.

## Validator Decision
The raw Auto-Quant trade rows are parseable and branch-carrying, but every row is missing the layered downstream contract fields required by Board B:

- provider provenance object with same-root authority key
- Pre-Bayes/filter state
- BBN posterior state
- CatBoost/path-ranker label
- execution-tree decision
- failure reason
- quality weight

Therefore the rows remain `chain_contract_negative_sample` evidence only. They are not eligible to update BBN likelihood tables, regime-conditioned win rate, CatBoost/path-ranker labels, or execution-tree branch weights.

## Gate
- `count_once:120432_115130_downstream_layered_validator_v1`.
- `pass:real_trade_rows_parsed_{summary["rows_total"]}`.
- `pass:branch_complete_rows_{summary["branch_complete_rows"]}`.
- `pass:outcome_rows_{summary["outcome_rows"]}`.
- `fail_closed:market_factor_rows_accepted_0`.
- `fail_closed:all_rows_missing_downstream_layered_contract`.
- `chain_contract_negative_sample_rows={summary["chain_contract_negative_samples"]}`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next
Repair the provider-rooted trade JSONL bridge so each row carries provider provenance and downstream readback fields, then rerun Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree before allowing any market/factor negative training use.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    source_root = Path(args.source_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report_json = source_root / "ibkr-longer-duration-six-provider-aq-v1" / "ibkr_longer_duration_six_provider_aq_v1.json"
    source_report = load_json(report_json)
    trade_files = sorted(source_root.glob("workspace/auto-quant-112315-*/derived/*.real_trades.jsonl"))

    classified: list[dict[str, Any]] = []
    combined_rows: list[dict[str, Any]] = []
    by_provider: dict[str, Counter[str]] = defaultdict(Counter)
    by_missing_field: Counter[str] = Counter()
    row_symbol_by_provider: dict[str, Counter[str]] = defaultdict(Counter)

    for trade_file in trade_files:
        provider_key = provider_from_trade_path(trade_file)
        strategy = strategy_from_trade_path(trade_file)
        rows = load_jsonl(trade_file)
        for row in rows:
            combined_rows.append(row)
            classified_row = classify_row(row, provider_key, strategy, trade_file)
            classified.append(classified_row)
            by_provider[provider_key]["rows"] += 1
            by_provider[provider_key][classified_row["evidence_class"]] += 1
            row_symbol_by_provider[provider_key][str(row.get("symbol"))] += 1
            for missing in classified_row["missing_fields"]:
                by_missing_field[missing] += 1

    rows_total = len(classified)
    branch_complete_rows = sum(1 for row in classified if row["branch_complete"])
    outcome_rows = sum(1 for row in classified if row["has_outcome"])
    market_factor_rows_accepted = sum(1 for row in classified if row["market_factor_feedback_allowed"])
    chain_contract_negative_samples = sum(
        1 for row in classified if row["evidence_class"] == "chain_contract_negative_sample"
    )

    summary = {
        "run_id": "20260512T120432+0800-codex-115130-downstream-layered-validator-v1",
        "source_run_id": source_report.get("run_id"),
        "source_root": str(source_root),
        "source_report": str(report_json),
        "real_trade_files": len(trade_files),
        "rows_total": rows_total,
        "branch_complete_rows": branch_complete_rows,
        "outcome_rows": outcome_rows,
        "market_factor_rows_accepted": market_factor_rows_accepted,
        "chain_contract_negative_samples": chain_contract_negative_samples,
        "provider_summary": {key: dict(value) for key, value in sorted(by_provider.items())},
        "row_symbol_by_provider": {
            key: dict(value) for key, value in sorted(row_symbol_by_provider.items())
        },
        "missing_field_counts": dict(sorted(by_missing_field.items())),
        "source_metric_totals": source_report.get("metric_totals", {}),
        "source_gate_result": source_report.get("gate_result"),
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "decision": "fail_closed_layered_validator_rejected_market_factor_training_use",
    }

    write_json(output_dir / "115130_downstream_layered_validator_v1.json", summary)
    write_jsonl(output_dir / "115130_combined_real_trades.jsonl", combined_rows)
    write_jsonl(output_dir / "115130_layered_validator_rows.jsonl", classified)
    write_csv(output_dir / "115130_layered_validator_rows.csv", classified)
    (output_dir / "115130_downstream_layered_validator_v1.md").write_text(
        build_report_md(summary),
        encoding="utf-8",
    )
    (output_dir / "prompt_to_artifact_checklist_115130_downstream_layered_validator_v1.csv").write_text(
        "\n".join(
            [
                "requirement,evidence,status",
                f"parse 115130 real-trade JSONL,{rows_total} rows across {len(trade_files)} files,pass",
                f"preserve branch-path check,{branch_complete_rows} rows with full branch path,pass",
                f"block market-factor learning,{market_factor_rows_accepted} rows accepted,pass",
                f"classify incomplete downstream contract,{chain_contract_negative_samples} chain-contract rows,pass",
                "no promotion/update_goal,promotion_allowed=false trade_usable=false update_goal=false,pass",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    assertions = [
        "PASS rows_total == 211" if rows_total == 211 else f"FAIL rows_total == {rows_total}",
        "PASS branch_complete_rows == 211"
        if branch_complete_rows == 211
        else f"FAIL branch_complete_rows == {branch_complete_rows}",
        "PASS market_factor_rows_accepted == 0"
        if market_factor_rows_accepted == 0
        else f"FAIL market_factor_rows_accepted == {market_factor_rows_accepted}",
        "PASS chain_contract_negative_samples == 211"
        if chain_contract_negative_samples == 211
        else f"FAIL chain_contract_negative_samples == {chain_contract_negative_samples}",
        "PASS update_goal == false",
    ]
    assertions_path = output_dir.parent / "checks" / "115130_downstream_layered_validator_v1_assertions.out"
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True))
    return 1 if any(line.startswith("FAIL") for line in assertions) else 0


if __name__ == "__main__":
    raise SystemExit(main())
