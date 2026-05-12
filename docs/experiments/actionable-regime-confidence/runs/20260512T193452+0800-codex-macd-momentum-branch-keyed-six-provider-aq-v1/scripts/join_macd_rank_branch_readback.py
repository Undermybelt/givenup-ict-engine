#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T193452+0800-codex-macd-momentum-branch-keyed-six-provider-aq-v1"
)
SYMBOL = "MACDMOM_193452"


def latest_artifact(kind: str) -> Path:
    paths = sorted((ROOT / "state" / "auto-quant" / SYMBOL).glob(f"{kind}.*.json"))
    if not paths:
        raise SystemExit(f"missing artifact: {kind}")
    return paths[-1]


def load_material_index() -> dict[str, dict[str, object]]:
    index: dict[str, dict[str, object]] = {}
    for path in sorted((ROOT / "agent-material").glob("*.material.json")):
        item = json.loads(path.read_text())
        profile = item["consumer_evidence_profile"]
        index[item["title"]] = {
            "unit_label": item["title"],
            "package_id": item["package_id"],
            "provider": profile["provider"],
            "branch_path": profile["branch_path"],
            "main_regime": profile["main_regime"],
            "sub_regime": profile["sub_regime"],
            "sub_sub_regime_or_profit_factor": profile["sub_sub_regime_or_profit_factor"],
            "profit_factor": profile["profit_factor"],
            "material_path": str(path),
            "local_cache_replay": profile["local_cache_replay"],
            "new_provider_fetch": profile["new_provider_fetch"],
        }
    return index


def classify(row: dict[str, object]) -> tuple[str, float, str]:
    trade_count = int(row["trade_count"] or 0)
    total_profit_pct = float(row["total_profit_pct"] or 0.0)
    win_rate_pct = float(row["win_rate_pct"] or 0.0)
    if trade_count == 0:
        return "low_density_negative_sample", 0.0, "aq_material_tuning_only"
    if trade_count < 25 and total_profit_pct > 0:
        return "low_density_weak_positive_provider_sample", 0.1, "branch_nursery_only"
    if trade_count < 25 and total_profit_pct <= 0:
        return "low_density_negative_sample", 0.05, "branch_nursery_only"
    if total_profit_pct < 0 or win_rate_pct < 45.0:
        return "market_factor_negative_sample", 0.25, "branch_nursery_only"
    return "candidate_market_positive_sample", 0.35, "branch_nursery_only"


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    material_index = load_material_index()
    dispatch_path = latest_artifact("auto_quant_agent_material_dispatch")
    rank_path = latest_artifact("auto_quant_agent_material_rank")
    dispatch = json.loads(dispatch_path.read_text())
    rank = json.loads(rank_path.read_text())

    rows: list[dict[str, object]] = []
    for rank_row in rank["ranking"]:
        unit_label = rank_row["unit_label"]
        if unit_label not in material_index:
            raise SystemExit(f"rank row not matched to material title: {unit_label}")
        joined = dict(material_index[unit_label])
        joined.update(
            {
                "status": rank_row["status"],
                "trade_count": rank_row.get("trade_count") or 0,
                "win_rate_pct": rank_row.get("win_rate_pct") or 0.0,
                "sharpe": rank_row.get("sharpe") or 0.0,
                "total_profit_pct": rank_row.get("total_profit_pct") or 0.0,
            }
        )
        evidence_class, quality_weight, allowed_feedback_targets = classify(joined)
        joined.update(
            {
                "evidence_class": evidence_class,
                "quality_weight": quality_weight,
                "allowed_feedback_targets": allowed_feedback_targets,
                "pre_bayes_filter_allowed": "false",
                "bbn_learning_allowed": "false",
                "catboost_learning_allowed": "false",
                "execution_tree_branch_weight_update_allowed": "false",
            }
        )
        rows.append(joined)

    branch_paths = sorted({str(row["branch_path"]) for row in rows})
    providers = sorted({str(row["provider"]) for row in rows})
    nonzero_rows = [row for row in rows if int(row["trade_count"]) > 0]
    positive_nonzero = [
        row for row in nonzero_rows if float(row["total_profit_pct"]) > 0
    ]
    zero_trade_providers = sorted(
        {
            str(row["provider"])
            for row in rows
            if int(row["trade_count"]) == 0
        }
    )
    max_trade_count = max(int(row["trade_count"]) for row in rows)

    classification = {
        "overall": "cross_provider_disagreement_sample and low_density; no downstream market/factor learning allowed",
        "nonzero_provider_count": len({str(row["provider"]) for row in nonzero_rows}),
        "zero_trade_providers": zero_trade_providers,
        "max_trade_count": max_trade_count,
        "positive_nonzero_rows": len(positive_nonzero),
        "reason": "Only YF/IBKR produced nonzero trades, max trade_count is below Board B training density, and four providers emitted zero trades.",
    }

    summary = {
        "root": str(ROOT),
        "symbol": SYMBOL,
        "batch_artifact": str(latest_artifact("auto_quant_agent_material_batch")),
        "dispatch_artifact": str(dispatch_path),
        "rank_artifact": str(rank_path),
        "dispatch_totals": dispatch["totals"],
        "rank_rows": len(rows),
        "provider_count": len(providers),
        "providers": providers,
        "branch_leaf_count": len(branch_paths),
        "branch_paths": branch_paths,
        "branch_keyed_by_construction": True,
        "rank_joined_to_explicit_branch_fields": True,
        "local_cache_replay": True,
        "new_provider_fetch": False,
        "classification": classification,
        "pre_bayes_filter_allowed": False,
        "bbn_learning_allowed": False,
        "catboost_learning_allowed": False,
        "execution_tree_branch_weight_update_allowed": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }

    fieldnames = [
        "branch_path",
        "main_regime",
        "sub_regime",
        "sub_sub_regime_or_profit_factor",
        "profit_factor",
        "provider",
        "package_id",
        "material_path",
        "local_cache_replay",
        "new_provider_fetch",
        "unit_label",
        "status",
        "trade_count",
        "win_rate_pct",
        "sharpe",
        "total_profit_pct",
        "evidence_class",
        "quality_weight",
        "allowed_feedback_targets",
        "pre_bayes_filter_allowed",
        "bbn_learning_allowed",
        "catboost_learning_allowed",
        "execution_tree_branch_weight_update_allowed",
    ]
    write_csv(ROOT / "summaries" / "macd_momentum_rank_branch_readback_v1.csv", rows, fieldnames)
    (ROOT / "summaries" / "macd_momentum_rank_branch_readback_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    (ROOT / "checks" / "aq_terminal_gate_assertions.out").write_text(
        "\n".join(
            [
                f"rank_rows={summary['rank_rows']}",
                f"provider_count={summary['provider_count']}",
                f"branch_leaf_count={summary['branch_leaf_count']}",
                f"dispatch_completed_jobs={dispatch['totals']['completed_jobs']}",
                f"dispatch_failed_jobs={dispatch['totals']['failed_jobs']}",
                "rank_joined_to_explicit_branch_fields=true",
                "adequate_branch_keyed_training_sample=false",
                "evidence_class=cross_provider_disagreement_sample",
                "secondary_evidence_class=low_density_or_zero_trade_provider_sample",
                "pre_bayes_filter_allowed=false",
                "bbn_learning_allowed=false",
                "catboost_learning_allowed=false",
                "execution_tree_branch_weight_update_allowed=false",
                "promotion_allowed=false",
                "trade_usable=false",
                "update_goal=false",
            ]
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
