from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _float_or_none(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _label_to_primary(label: str) -> str:
    normalized = label.strip()
    if not normalized:
        return "primary::Unknown"
    return f"primary::{normalized}"


def load_recovered_assets(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def select_asset(rows: list[dict[str, str]], asset_id: str) -> dict[str, str]:
    for row in rows:
        if row.get("asset_id") == asset_id:
            return row
    raise ValueError(f"asset_id not found: {asset_id}")


def build_decision_from_asset(
    asset: dict[str, str],
    *,
    timestamp: str = "",
    allow_trade_usable: bool = False,
) -> dict[str, Any]:
    label = asset.get("label", "")
    min_lcb = _float_or_none(asset.get("min_split_wilson95_lcb"))
    calibration_lcb = _float_or_none(asset.get("calibration_wilson95_lcb"))
    test_lcb = _float_or_none(asset.get("test_wilson95_lcb"))
    best_lcb = min_lcb or min(
        value for value in (calibration_lcb, test_lcb) if value is not None
    )
    downstream_live_admitted = False
    scope_limited = "scope_limited" in asset.get("status", "") or asset.get("ingestion_state") != "promoted_runtime"
    trade_usable = False
    decision_state = "single_label_95" if trade_usable else "single_label_95_scope_limited"
    primary_label = _label_to_primary(label)
    branch_path = (
        f"{label or 'Unknown'} -> RecoveredRegimeAsset -> {asset.get('asset_id', 'unknown')} "
        "-> recovered_rule_replay"
    )
    reasons = [
        "recovered_95_confidence_asset",
        f"status={asset.get('status', '')}",
        f"ingestion_state={asset.get('ingestion_state', '')}",
    ]
    if scope_limited:
        reasons.append("scope_limited_no_runtime_promotion")
    if not downstream_live_admitted:
        reasons.append("recovered_regime_asset_requires_downstream_live_admission")
    return {
        "schema_version": "regime-high-confidence-decision/v1",
        "timestamp": timestamp,
        "decision_state": decision_state,
        "trade_usable": trade_usable,
        "final_label": primary_label,
        "label_set": [primary_label, branch_path],
        "abstain_reasons": reasons,
        "execution_tree_hint": "review_only_scope_limited_regime_asset",
        "bbn_evidence_hint": {
            "regime_decision_state": decision_state,
            "regime_trade_usable": trade_usable,
            "regime_label": primary_label,
            "regime_label_set": [primary_label, branch_path],
            "regime_transition_hazard": 0.0 if trade_usable else 1.0,
            "regime_decision_reasons": reasons,
        },
        "path_ranker_context": {
            "regime_profit_branch_path": branch_path,
            "main_regime": label,
            "sub_regime": "RecoveredRegimeAsset",
            "sub_sub_regime_or_profit_factor": asset.get("asset_id", ""),
            "profit_factor": "recovered_rule_replay",
            "stable_profit_score": best_lcb,
        },
        "recovered_asset": {
            "asset_id": asset.get("asset_id", ""),
            "label": label,
            "asset_class": asset.get("asset_class", ""),
            "status": asset.get("status", ""),
            "usable_as": asset.get("usable_as", ""),
            "rule_or_condition": asset.get("rule_or_condition", ""),
            "calibration_wilson95_lcb": calibration_lcb,
            "test_wilson95_lcb": test_lcb,
            "min_split_wilson95_lcb": min_lcb,
            "validation_scope": asset.get("validation_scope", ""),
            "source_run_root": asset.get("source_run_root", ""),
            "primary_artifact": asset.get("primary_artifact", ""),
            "ingestion_state": asset.get("ingestion_state", ""),
        },
    }


def build_bundle(decision: dict[str, Any], decision_path: Path) -> dict[str, Any]:
    return {
        "schema_version": "regime-consumer-bundle/v1",
        "artifact_count": 1,
        "missing_artifacts": [],
        "latest_decision": {
            "timestamp": decision.get("timestamp", ""),
            "decision_state": decision["decision_state"],
            "trade_usable": decision["trade_usable"],
            "final_label": decision["final_label"],
            "label_set": decision["label_set"],
            "abstain_reasons": decision["abstain_reasons"],
        },
        "consumer_hints": {
            "execution_tree_hint": decision["execution_tree_hint"],
            "bbn_evidence_hint": decision["bbn_evidence_hint"],
            "path_ranker_context": decision["path_ranker_context"],
            "user_vrp_nq_context": {},
            "trade_usable": decision["trade_usable"],
        },
        "artifacts": {
            "decision": {
                "status": "present",
                "path": str(decision_path),
                "schema_version": decision["schema_version"],
                "decision_state": decision["decision_state"],
                "trade_usable": decision["trade_usable"],
                "final_label": decision["final_label"],
                "label_set": decision["label_set"],
                "abstain_reasons": decision["abstain_reasons"],
            }
        },
        "consumer_contract": {
            "zero_config": False,
            "hotplug_scope": "explicit_recovered_asset",
            "main_runtime_mutation": "none",
            "optional_for_consumers": True,
            "token_friendly": True,
            "promotion_allowed": False,
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a fail-closed regime consumer bundle from one recovered 95% Board A asset."
    )
    parser.add_argument("--asset-ledger", required=True)
    parser.add_argument("--asset-id", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--timestamp", default="")
    parser.add_argument(
        "--allow-trade-usable",
        action="store_true",
        help="Only for already promoted runtime assets; scope-limited recovered assets still fail closed.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = Path(args.output_dir)
    asset = select_asset(load_recovered_assets(Path(args.asset_ledger)), args.asset_id)
    decision = build_decision_from_asset(
        asset,
        timestamp=args.timestamp,
        allow_trade_usable=args.allow_trade_usable,
    )
    decision_path = output_dir / "regime_high_confidence_decision.json"
    bundle_path = output_dir / "regime_consumer_bundle.json"
    _write_json(decision_path, decision)
    _write_json(bundle_path, build_bundle(decision, decision_path))
    print(
        json.dumps(
            {
                "ok": True,
                "asset_id": args.asset_id,
                "decision_state": decision["decision_state"],
                "trade_usable": decision["trade_usable"],
                "bundle_path": str(bundle_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
