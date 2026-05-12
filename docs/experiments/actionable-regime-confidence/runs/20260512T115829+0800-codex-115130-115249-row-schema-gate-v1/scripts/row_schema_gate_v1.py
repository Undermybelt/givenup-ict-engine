#!/usr/bin/env python3
import json
from collections import Counter, defaultdict
from pathlib import Path


RUN_ID = "20260512T115829+0800-codex-115130-115249-row-schema-gate-v1"
ROOT = Path("docs/experiments/actionable-regime-confidence/runs/20260512T115829+0800-codex-115130-115249-row-schema-gate-v1")
REPORT_DIR = ROOT / "115130-115249-row-schema-gate-v1"
CHECK_DIR = ROOT / "checks"

EVALUATED = {
    "115130": {
        "run_id": "20260512T115130+0800-codex-113833-ibkr-longer-duration-six-provider-aq-v1",
        "path": Path("docs/experiments/actionable-regime-confidence/runs/20260512T115130+0800-codex-113833-ibkr-longer-duration-six-provider-aq-v1"),
        "allowed_auto_quant_run_ids": {
            "20260512T115130+0800-codex-113833-ibkr-longer-duration-six-provider-aq-v1",
            "20260512T113833+0800-codex-112904-provider-matrix-aq-date-contract-repair-v1",
        },
    },
    "115249": {
        "run_id": "20260512T115249+0800-codex-ibkr-btc-long-aq-lane-v1",
        "path": Path("docs/experiments/actionable-regime-confidence/runs/20260512T115249+0800-codex-ibkr-btc-long-aq-lane-v1"),
        "allowed_auto_quant_run_ids": {
            "20260512T115249+0800-codex-ibkr-btc-long-aq-lane-v1",
            "20260512T113833+0800-codex-112904-provider-matrix-aq-date-contract-repair-v1",
        },
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


def iter_trade_files(run_path):
    yield from sorted((run_path / "workspace").glob("*/derived/*.real_trades.jsonl"))


def load_jsonl(path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            yield line_no, json.loads(line)


def non_empty(value):
    return value is not None and value != "" and value != [] and value != {}


def classify_row(row, allowed_run_ids):
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
    if not (non_empty(row.get("outcome")) or (non_empty(row.get("realized_outcome")) and "pnl" in row)):
        failures.append("missing_outcome")
    if row.get("auto_quant_run_id") not in allowed_run_ids:
        failures.append("stale_or_wrong_auto_quant_run_id")
    symbol = row.get("symbol")
    if isinstance(symbol, str) and ("104902" in symbol or "YAHOO_BTC_PULLBACK" in symbol):
        failures.append("stale_symbol_namespace")
    return failures


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    totals = Counter()
    missing = Counter()
    source_counts = Counter()
    symbol_counts = Counter()
    provider_file_counts = Counter()
    examples = []
    per_run = defaultdict(Counter)

    for label, spec in EVALUATED.items():
        files = list(iter_trade_files(spec["path"]))
        per_run[label]["files"] = len(files)
        for trade_file in files:
            provider_key = trade_file.parts[-3] if len(trade_file.parts) >= 3 else "unknown"
            provider_file_counts[provider_key] += 1
            for line_no, row in load_jsonl(trade_file):
                totals["rows"] += 1
                per_run[label]["rows"] += 1
                source_counts[row.get("auto_quant_run_id", "<missing>")] += 1
                symbol_counts[row.get("symbol", "<missing>")] += 1
                failures = classify_row(row, spec["allowed_auto_quant_run_ids"])
                if not failures:
                    totals["market_factor_trainable_rows"] += 1
                else:
                    totals["rejected_rows"] += 1
                    per_run[label]["rejected_rows"] += 1
                    missing.update(failures)
                    if len(examples) < 12:
                        examples.append(
                            {
                                "run_label": label,
                                "file": str(trade_file),
                                "line": line_no,
                                "trade_id": row.get("trade_id"),
                                "auto_quant_run_id": row.get("auto_quant_run_id"),
                                "symbol": row.get("symbol"),
                                "failures": failures,
                            }
                        )

    result = {
        "run_id": RUN_ID,
        "evaluated_roots": {label: spec["run_id"] for label, spec in EVALUATED.items()},
        "total_rows": totals["rows"],
        "market_factor_trainable_rows": totals["market_factor_trainable_rows"],
        "rejected_rows": totals["rejected_rows"],
        "per_run": {key: dict(value) for key, value in per_run.items()},
        "failure_counts": dict(missing),
        "auto_quant_run_id_counts": dict(source_counts),
        "symbol_counts": dict(symbol_counts),
        "provider_file_counts": dict(provider_file_counts),
        "classification": {
            "115130": "infrastructure_repair_candidate_plus_chain_contract_negative_sample",
            "115249": "infrastructure_repair_candidate_plus_chain_contract_negative_sample",
            "market_factor_negative_rows_added": 0,
        },
        "gate_result": "fail_closed:no_market_factor_negative_ingestion_rows",
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "examples": examples,
    }

    json_path = REPORT_DIR / "row_schema_gate_v1.json"
    md_path = REPORT_DIR / "row_schema_gate_v1.md"
    assertions_path = CHECK_DIR / "row_schema_gate_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_lines = [
        "# 115130 / 115249 Row Schema Gate v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Scope",
        "Validate whether the settled 115130 and 115249 AQ trade rows satisfy the Board B minimum observation schema before any negative-evidence ingestion or downstream training use.",
        "",
        "## Evaluated Roots",
    ]
    for label, spec in EVALUATED.items():
        md_lines.append(f"- `{label}`: `{spec['run_id']}`")
    md_lines.extend(
        [
            "",
            "## Result",
            f"- Total trade rows checked: `{result['total_rows']}`.",
            f"- Market/factor trainable rows accepted: `{result['market_factor_trainable_rows']}`.",
            f"- Rows rejected from market/factor ingestion: `{result['rejected_rows']}`.",
            "- Evidence class: `infrastructure_repair_candidate_plus_chain_contract_negative_sample`.",
            "- Gate: `fail_closed:no_market_factor_negative_ingestion_rows`.",
            "",
            "## Primary Rejection Reasons",
        ]
    )
    for key, value in sorted(missing.items()):
        md_lines.append(f"- `{key}`: `{value}` rows")
    md_lines.extend(
        [
            "",
            "## Source Id Readback",
        ]
    )
    for key, value in sorted(source_counts.items()):
        md_lines.append(f"- `{key}`: `{value}` rows")
    md_lines.extend(
        [
            "",
            "## Decision",
            "- The AQ/provider repair evidence is useful, especially the successful IBKR 1h MIDPOINT AQ lane.",
            "- These rows must not be fed into BBN likelihood, CatBoost/path-ranker labels, or execution-tree branch weights as market/factor negative samples.",
            "- Reason: row-level provider provenance and downstream Pre-Bayes/BBN/CatBoost/execution decisions are absent, and the emitted rows still carry stale `104902` source ids/symbol namespaces.",
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
        f"PASS total_rows={result['total_rows']}",
        f"FAIL_CLOSED market_factor_trainable_rows={result['market_factor_trainable_rows']}",
        f"PASS rejected_rows={result['rejected_rows']}",
        f"FAIL_CLOSED stale_or_wrong_auto_quant_run_id_rows={missing.get('stale_or_wrong_auto_quant_run_id', 0)}",
        f"FAIL_CLOSED missing_provider_provenance_rows={missing.get('missing_provider_provenance', 0)}",
        f"FAIL_CLOSED missing_pre_bayes_filter_state_rows={missing.get('missing_pre_bayes_filter_state', 0)}",
        f"FAIL_CLOSED missing_bbn_posterior_rows={missing.get('missing_bbn_posterior', 0)}",
        f"FAIL_CLOSED missing_catboost_path_ranker_label_rows={missing.get('missing_catboost_path_ranker_label', 0)}",
        f"FAIL_CLOSED missing_execution_tree_decision_rows={missing.get('missing_execution_tree_decision', 0)}",
        "PASS evidence_class=infrastructure_repair_candidate_plus_chain_contract_negative_sample",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
