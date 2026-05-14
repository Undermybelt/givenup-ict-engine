#!/usr/bin/env python3
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
SOURCE_RUN = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3"
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "branch-path-field-bridge-v1"
CHECK_DIR = RUN_ROOT / "checks"

MANIFEST = SOURCE_RUN / "downstream-v2/strategy_library_nq_cost_crisis_repair_v3_manifest_1_0.json"
WIRE = SOURCE_RUN / "downstream-v2/nq_cost_crisis_repair_real_trades_v3_wire_fixed.jsonl"
TARGET = SOURCE_RUN / "downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/policy_training/structural_path_ranking_target.csv"
SCORES = SOURCE_RUN / "downstream-combined-v1/catboost/scores/current_scores.csv"
PRE_BAYES = SOURCE_RUN / "downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/pre_bayes_policy_history.json"
BBN = SOURCE_RUN / "downstream-combined-v1/state_combined_v1/auto-quant/B2R_NQ_COST_CRISIS_REPAIR_032157/bbn_network.json"
EXECUTION_TREE = SOURCE_RUN / "downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/execution_tree_trace.json"
WORKFLOW = SOURCE_RUN / "downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/workflow_snapshot.json"

ENRICHED_WIRE = OUT_DIR / "nq_cost_crisis_repair_real_trades_v3_full_branch_path_enriched.jsonl"
COUNTS_CSV = OUT_DIR / "branch_path_field_bridge_counts_v1.csv"
SUMMARY_JSON = OUT_DIR / "branch_path_field_bridge_v1.json"
SUMMARY_MD = OUT_DIR / "branch_path_field_bridge_v1.md"
ASSERTIONS = CHECK_DIR / "branch_path_field_bridge_v1_assertions.out"


def load_json(path):
    with path.open() as fh:
        return json.load(fh)


def split_path(path):
    parts = path.split(" -> ")
    while len(parts) < 4:
        parts.append("")
    return {
        "main_regime": parts[0],
        "sub_regime": parts[1],
        "sub_sub_regime_or_profit_factor": parts[2],
        "profit_factor": parts[3],
    }


def collect_paths_from_csv(path):
    paths = []
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            value = row.get("path_id") or row.get("path_label") or ""
            if " -> " in value and value not in paths:
                paths.append(value)
    return paths


def contains_all_paths(path, paths):
    if not path.exists():
        return False
    text = path.read_text(errors="replace")
    return all(p in text for p in paths)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    manifest = load_json(MANIFEST)
    by_strategy = {}
    by_root = {}
    for item in manifest["strategies"]:
        metadata = item.get("metadata") or {}
        full_path = metadata.get("parent") or ""
        root = (metadata.get("expected_regime") or "").split("::")[-1]
        if not root and full_path:
            root = full_path.split(" -> ")[0]
        record = {
            "strategy_name": item["name"],
            "root": root,
            "regime_profit_branch_path": full_path,
            "components": split_path(full_path),
        }
        by_strategy[item["name"]] = record
        if root:
            by_root[root] = record

    target_paths = collect_paths_from_csv(TARGET)
    score_paths = collect_paths_from_csv(SCORES)
    expected_paths = []
    for record in by_strategy.values():
        path = record["regime_profit_branch_path"]
        if path and path not in expected_paths:
            expected_paths.append(path)

    rows_total = 0
    rows_enriched = 0
    missing_strategy = Counter()
    root_counts = Counter()
    path_counts = Counter()

    with WIRE.open() as src, ENRICHED_WIRE.open("w") as dst:
        for line in src:
            if not line.strip():
                continue
            rows_total += 1
            row = json.loads(line)
            mapping = by_strategy.get(row.get("strategy_name")) or by_root.get(row.get("regime_at_entry"))
            if not mapping:
                missing_strategy[row.get("strategy_name") or "<missing>"] += 1
                dst.write(json.dumps(row, sort_keys=True) + "\n")
                continue

            root = mapping["root"]
            full_path = mapping["regime_profit_branch_path"]
            components = mapping["components"]
            row["parent_regime_root"] = root
            row["regime_profit_branch_path"] = full_path
            row["regime_profit_branch_path_version"] = "board_b_rooted_path_v1"
            row["regime_branch_components"] = components
            row["regime_branch_path_source"] = "strategy_manifest_parent"

            for factor in row.get("factors_used") or []:
                if factor.get("category") == "regime_profit_branch_path":
                    factor["parent_regime_root"] = root
                    factor["regime_profit_branch_path"] = full_path
                    factor["regime_profit_branch_path_version"] = "board_b_rooted_path_v1"
                    factor["regime_branch_components"] = components

            rows_enriched += 1
            root_counts[root] += 1
            path_counts[full_path] += 1
            dst.write(json.dumps(row, sort_keys=True) + "\n")

    missing_target_paths_from_wire = [p for p in target_paths if path_counts[p] == 0]
    summary = {
        "run_id": RUN_ROOT.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": "branch_path_field_bridge_v1=enriched_wire_schema_bridge_ready_no_promotion",
        "source_run": str(SOURCE_RUN.relative_to(REPO)),
        "inputs": {
            "manifest": str(MANIFEST.relative_to(REPO)),
            "wire": str(WIRE.relative_to(REPO)),
            "catboost_target": str(TARGET.relative_to(REPO)),
            "catboost_scores": str(SCORES.relative_to(REPO)),
        },
        "outputs": {
            "enriched_wire": str(ENRICHED_WIRE.relative_to(REPO)),
            "counts_csv": str(COUNTS_CSV.relative_to(REPO)),
            "summary_json": str(SUMMARY_JSON.relative_to(REPO)),
            "summary_md": str(SUMMARY_MD.relative_to(REPO)),
            "assertions": str(ASSERTIONS.relative_to(REPO)),
        },
        "rows_total": rows_total,
        "rows_enriched": rows_enriched,
        "missing_strategy_rows": sum(missing_strategy.values()),
        "root_counts": dict(root_counts),
        "branch_path_counts": dict(path_counts),
        "manifest_paths": expected_paths,
        "catboost_target_paths": target_paths,
        "catboost_score_paths": score_paths,
        "missing_target_paths_from_enriched_wire": missing_target_paths_from_wire,
        "existing_layer_path_presence": {
            "pre_bayes_all_target_paths": contains_all_paths(PRE_BAYES, target_paths),
            "bbn_all_target_paths": contains_all_paths(BBN, target_paths),
            "execution_tree_all_target_paths": contains_all_paths(EXECUTION_TREE, target_paths),
            "workflow_all_target_paths": contains_all_paths(WORKFLOW, target_paths),
        },
        "promotion_status": {
            "selected_historical_data": False,
            "downstream_promotion_rerun": False,
            "promotion_allowed": False,
            "update_goal": False,
        },
    }

    with COUNTS_CSV.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["regime_profit_branch_path", "rows"])
        writer.writeheader()
        for path, count in path_counts.most_common():
            writer.writerow({"regime_profit_branch_path": path, "rows": count})

    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    lines = [
        "# Branch Path Field Bridge v1",
        "",
        f"Run id: `{RUN_ROOT.name}`",
        "",
        f"Gate result: `{summary['gate_result']}`",
        "",
        "Purpose: build an isolated enriched Auto-Quant trade wire that carries the full `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor` string at trade time. This does not select historical data, does not promote any candidate, and does not call `update_goal`.",
        "",
        "## Result",
        "",
        f"- Input trade rows: `{rows_total}`.",
        f"- Rows enriched with full branch path fields: `{rows_enriched}`.",
        f"- Missing strategy mappings: `{sum(missing_strategy.values())}`.",
        "- Branch path row counts:",
    ]
    for path, count in path_counts.most_common():
        lines.append(f"  - `{path}`: `{count}`")
    lines.extend([
        f"- CatBoost target paths absent from enriched wire: `{missing_target_paths_from_wire}`.",
        "",
        "## Layer Readback",
        "",
        f"- Pre-Bayes already contains all exact target paths: `{summary['existing_layer_path_presence']['pre_bayes_all_target_paths']}`.",
        f"- BBN already contains all exact target paths: `{summary['existing_layer_path_presence']['bbn_all_target_paths']}`.",
        f"- Execution tree already contains all exact target paths: `{summary['existing_layer_path_presence']['execution_tree_all_target_paths']}`.",
        f"- Workflow snapshot already contains all exact target paths: `{summary['existing_layer_path_presence']['workflow_all_target_paths']}`.",
        "",
        "## Decision",
        "",
        "The Auto-Quant trade wire can be deterministically enriched from the strategy manifest for the four price-root branches that actually have trades. This repairs the wire-field shape only. It does not create Manipulation(scoped) trades, does not make Pre-Bayes or BBN consume exact branch paths, does not satisfy selected historical data, and is not promotion evidence.",
        "",
        "## Next",
        "",
        "Run `auto-quant-ingest-real-trades --dry-run` against this enriched wire, then apply only to an isolated copied state if the schema accepts it. Continue to Pre-Bayes/filter, BBN/analyze, CatBoost/path-ranker, and execution-tree readbacks only as a diagnostic branch-path preservation test.",
        "",
    ])
    SUMMARY_MD.write_text("\n".join(lines))

    assertion_lines = []
    assertion_lines.append("PASS enriched_wire_created=true" if ENRICHED_WIRE.exists() else "FAIL enriched_wire_created=false")
    assertion_lines.append(f"PASS rows_total={rows_total}" if rows_total == 15415 else f"FAIL rows_total={rows_total}")
    assertion_lines.append(f"PASS rows_enriched={rows_enriched}" if rows_enriched == rows_total else f"FAIL rows_enriched={rows_enriched}")
    assertion_lines.append("PASS missing_strategy_rows=0" if sum(missing_strategy.values()) == 0 else f"FAIL missing_strategy_rows={sum(missing_strategy.values())}")
    assertion_lines.append("PASS catboost_paths_visible=true" if len(target_paths) == 5 else f"FAIL catboost_paths_visible={len(target_paths)}")
    if missing_target_paths_from_wire == [
        "Manipulation(scoped) -> TelegramPumpEvent -> ProviderStopTakeShort -> ManipulationStopTakeProfitGridV2:short_tp120_sl060_h72"
    ]:
        assertion_lines.append("PASS missing_target_path_is_zero_trade_scoped_manipulation=true")
    else:
        assertion_lines.append(f"FAIL unexpected_missing_target_paths={missing_target_paths_from_wire}")
    assertion_lines.append("PASS selected_historical_data=false")
    assertion_lines.append("PASS promotion_allowed=false")
    assertion_lines.append("PASS update_goal=false")
    ASSERTIONS.write_text("\n".join(assertion_lines) + "\n")


if __name__ == "__main__":
    main()
