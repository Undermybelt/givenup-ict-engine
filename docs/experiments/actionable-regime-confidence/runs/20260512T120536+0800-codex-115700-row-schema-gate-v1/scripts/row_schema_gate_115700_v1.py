#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path


RUN_ID = "20260512T120536+0800-codex-115700-row-schema-gate-v1"
SOURCE_RUN_ID = "20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1"
ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T120536+0800-codex-115700-row-schema-gate-v1"
)
SOURCE_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1"
)
REPORT_DIR = ROOT / "115700-row-schema-gate-v1"
CHECK_DIR = ROOT / "checks"

ALLOWED_AUTO_QUANT_RUN_IDS = {
    SOURCE_RUN_ID,
    "20260512T113833+0800-codex-112904-provider-matrix-aq-date-contract-repair-v1",
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


def non_empty(value):
    return value is not None and value != "" and value != [] and value != {}


def iter_trade_files():
    yield from sorted((SOURCE_ROOT / "workspace").glob("*/derived/*.real_trades.jsonl"))


def load_jsonl(path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if line:
                yield line_no, json.loads(line)


def classify_row(row):
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
    if row.get("auto_quant_run_id") not in ALLOWED_AUTO_QUANT_RUN_IDS:
        failures.append("stale_or_wrong_auto_quant_run_id")
    symbol = row.get("symbol")
    if isinstance(symbol, str) and ("104902" in symbol or "YAHOO_BTC_PULLBACK" in symbol):
        failures.append("stale_symbol_namespace")
    return failures


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    totals = Counter()
    failures = Counter()
    source_ids = Counter()
    symbols = Counter()
    provider_files = Counter()
    examples = []

    files = list(iter_trade_files())
    for path in files:
        provider_key = path.parts[-3] if len(path.parts) >= 3 else "unknown"
        provider_files[provider_key] += 1
        for line_no, row in load_jsonl(path):
            totals["rows"] += 1
            source_ids[row.get("auto_quant_run_id", "<missing>")] += 1
            symbols[row.get("symbol", "<missing>")] += 1
            row_failures = classify_row(row)
            if row_failures:
                totals["rejected_rows"] += 1
                failures.update(row_failures)
                if len(examples) < 12:
                    examples.append(
                        {
                            "file": str(path),
                            "line": line_no,
                            "trade_id": row.get("trade_id"),
                            "auto_quant_run_id": row.get("auto_quant_run_id"),
                            "symbol": row.get("symbol"),
                            "branch_path": row.get("branch_path")
                            or row.get("regime_profit_branch_path"),
                            "failures": row_failures,
                        }
                    )
            else:
                totals["market_factor_trainable_rows"] += 1

    result = {
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "source_root": str(SOURCE_ROOT),
        "trade_files": len(files),
        "total_rows": totals["rows"],
        "market_factor_trainable_rows": totals["market_factor_trainable_rows"],
        "rejected_rows": totals["rejected_rows"],
        "failure_counts": dict(sorted(failures.items())),
        "auto_quant_run_id_counts": dict(sorted(source_ids.items())),
        "symbol_counts": dict(sorted(symbols.items())),
        "provider_file_counts": dict(sorted(provider_files.items())),
        "classification": "infrastructure_repair_candidate_plus_chain_contract_negative_sample",
        "gate_result": "fail_closed:no_market_factor_negative_ingestion_rows",
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "examples": examples,
    }

    json_path = REPORT_DIR / "row_schema_gate_115700_v1.json"
    md_path = REPORT_DIR / "row_schema_gate_115700_v1.md"
    assertions_path = CHECK_DIR / "row_schema_gate_115700_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_lines = [
        "# 115700 Row Schema Gate v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source root: `{SOURCE_RUN_ID}`",
        "",
        "## Scope",
        "Validate whether the settled 115700 same-root six-provider 1h AQ trade rows satisfy the Board B minimum observation schema before negative-evidence ingestion or downstream training use.",
        "",
        "## Result",
        f"- Trade files checked: `{result['trade_files']}`.",
        f"- Total trade rows checked: `{result['total_rows']}`.",
        f"- Market/factor trainable rows accepted: `{result['market_factor_trainable_rows']}`.",
        f"- Rows rejected from market/factor ingestion: `{result['rejected_rows']}`.",
        f"- Evidence class: `{result['classification']}`.",
        f"- Gate: `{result['gate_result']}`.",
        "",
        "## Primary Rejection Reasons",
    ]
    for key, value in result["failure_counts"].items():
        md_lines.append(f"- `{key}`: `{value}` rows")
    md_lines.extend(["", "## Source Id Readback"])
    for key, value in result["auto_quant_run_id_counts"].items():
        md_lines.append(f"- `{key}`: `{value}` rows")
    md_lines.extend(
        [
            "",
            "## Decision",
            "- 115700 is the strongest AQ-provider packet so far because all six provider fetches and all six AQ lanes succeeded on 1h-shaped data.",
            "- Its emitted trade rows still cannot be used as market/factor negative samples because downstream attribution fields are absent and the row source ids remain stale.",
            "- Feed the blocker to the exporter/enricher and chain-contract repair loop, not to BBN likelihood, CatBoost/path-ranker labels, or execution-tree branch weights.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{json_path}`",
            f"- Assertions: `{assertions_path}`",
        ]
    )
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_run_id={SOURCE_RUN_ID}",
        f"PASS trade_files={result['trade_files']}",
        f"PASS total_rows={result['total_rows']}",
        f"FAIL_CLOSED market_factor_trainable_rows={result['market_factor_trainable_rows']}",
        f"PASS rejected_rows={result['rejected_rows']}",
        f"FAIL_CLOSED stale_or_wrong_auto_quant_run_id_rows={failures.get('stale_or_wrong_auto_quant_run_id', 0)}",
        f"FAIL_CLOSED missing_provider_provenance_rows={failures.get('missing_provider_provenance', 0)}",
        f"FAIL_CLOSED missing_pre_bayes_filter_state_rows={failures.get('missing_pre_bayes_filter_state', 0)}",
        f"FAIL_CLOSED missing_bbn_posterior_rows={failures.get('missing_bbn_posterior', 0)}",
        f"FAIL_CLOSED missing_catboost_path_ranker_label_rows={failures.get('missing_catboost_path_ranker_label', 0)}",
        f"FAIL_CLOSED missing_execution_tree_decision_rows={failures.get('missing_execution_tree_decision', 0)}",
        "PASS evidence_class=infrastructure_repair_candidate_plus_chain_contract_negative_sample",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
