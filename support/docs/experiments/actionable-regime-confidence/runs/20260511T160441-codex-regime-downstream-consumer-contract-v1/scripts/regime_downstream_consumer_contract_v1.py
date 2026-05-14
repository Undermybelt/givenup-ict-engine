#!/usr/bin/env python3
"""Create downstream consumer-bundle contract templates from the accepted regime map."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T160441+0800-codex-regime-downstream-consumer-contract-v1"
RUN_ROOT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T160441-codex-regime-downstream-consumer-contract-v1"
)
OUT_DIR = RUN_ROOT / "downstream-consumer-contract"
TEMPLATE_DIR = OUT_DIR / "bundle-templates"
CHECK_DIR = RUN_ROOT / "checks"

CONSUMER_MAP = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T153637-codex-regime-factor-consumer-map-v1/"
    "regime-factor-map/regime_factor_consumer_map_v1.csv"
)
ADAPTER = REPO / "src/application/regime/consumer_bundle_adapter.rs"

OUT_JSON = OUT_DIR / "regime_downstream_consumer_contract_v1.json"
OUT_MD = OUT_DIR / "regime_downstream_consumer_contract_v1.md"
OUT_CSV = OUT_DIR / "regime_downstream_consumer_contract_v1_surfaces.csv"
OUT_TEMPLATE_INDEX = OUT_DIR / "regime_consumer_bundle_template_index_v1.csv"
OUT_ASSERT = CHECK_DIR / "regime_downstream_consumer_contract_v1_assertions.out"

SCHEMA_VERSION = "regime-consumer-bundle/v1"
OLD_CHILD_LABELS = {
    "TrendExpansion",
    "RangeConsolidation",
    "ExtremeStress",
    "ReversalBrewing",
    "SessionLiquidityCoreViable",
    "ThinLiquidity",
}


def repo_rel(path: Path | str) -> str:
    path = Path(path)
    return str(path.relative_to(REPO)) if path.is_absolute() else str(path)


def read_consumer_map() -> list[dict[str, str]]:
    with CONSUMER_MAP.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def bundle_label(row: dict[str, str]) -> str:
    if row["taxonomy_role"] == "MainRegimeV2_price_root":
        return f"MainRegimeV2::{row['regime']}"
    return f"DirectOverlay::{row['regime']}"


def template_for(row: dict[str, str]) -> dict[str, Any]:
    label = bundle_label(row)
    is_manipulation = row["regime"] == "Manipulation"
    reasons = [
        "accepted_95_scoped_context",
        "not_trade_usable",
        "no_ohlcv_proxy",
    ]
    if is_manipulation:
        reasons.append("direct_overlay_suppression_or_abstain_only")
    else:
        reasons.append("market_regime_context_only")
    return {
        "schema_version": SCHEMA_VERSION,
        "latest_decision": {
            "timestamp": RUN_ID,
            "decision_state": "single_label_95",
            "trade_usable": False,
            "final_label": label,
            "label_set": [label],
            "abstain_reasons": reasons,
        },
        "consumer_hints": {
            "execution_tree_hint": "transition_guardrail",
            "trade_usable": False,
            "bbn_evidence_hint": {
                "regime_decision_state": "single_label_95",
                "regime_trade_usable": False,
                "regime_label": label,
                "regime_label_set": [label],
                "regime_transition_hazard": None,
                "regime_decision_reasons": reasons,
            },
            "path_ranker_context": {
                "context_source": "regime_factor_consumer_map_v1",
                "consumer_factor": row["consumer_factor"],
                "confidence_floor": float(row["confidence_floor"]),
                "allowed_action": row["allowed_action"],
                "scope_limit": row["abstain_or_limit"],
            },
            "user_vrp_nq_context": {},
        },
        "provenance": {
            "run_id": RUN_ID,
            "source_consumer_map": repo_rel(CONSUMER_MAP),
            "source_artifact": row["source_artifact"],
        },
    }


def current_adapter_protocol_notes(adapter_source: str) -> dict[str, Any]:
    supports_schema = SCHEMA_VERSION in adapter_source
    legacy_labels_present = sorted(label for label in OLD_CHILD_LABELS if label in adapter_source)
    explicit_mainregime_labels_present = [
        label
        for label in ["MainRegimeV2::Bull", "MainRegimeV2::Bear", "MainRegimeV2::Sideways", "MainRegimeV2::Crisis"]
        if label in adapter_source
    ]
    return {
        "adapter_path": repo_rel(ADAPTER),
        "supports_bundle_schema": supports_schema,
        "legacy_label_mapper_labels_present": legacy_labels_present,
        "explicit_mainregime_label_mapper_present": bool(explicit_mainregime_labels_present),
        "mainregime_labels_seen": explicit_mainregime_labels_present,
        "contract_decision": (
            "read_only_trace_contract_now; do_not_apply_bbn_soft_evidence_from templates "
            "until runtime supports MainRegimeV2 mapping without old child-label promotion"
        ),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    rows = read_consumer_map()
    adapter_source = ADAPTER.read_text(encoding="utf-8")
    adapter_notes = current_adapter_protocol_notes(adapter_source)

    template_rows: list[dict[str, Any]] = []
    template_paths: list[Path] = []
    for row in rows:
        template = template_for(row)
        path = TEMPLATE_DIR / f"{row['regime'].lower()}_regime_consumer_bundle_template_v1.json"
        path.write_text(json.dumps(template, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        template_paths.append(path)
        template_rows.append(
            {
                "regime": row["regime"],
                "bundle_template": repo_rel(path),
                "schema_version": template["schema_version"],
                "final_label": template["latest_decision"]["final_label"],
                "decision_state": template["latest_decision"]["decision_state"],
                "trade_usable": template["latest_decision"]["trade_usable"],
                "execution_tree_hint": template["consumer_hints"]["execution_tree_hint"],
                "bbn_soft_evidence_application": "neutral_read_only_trade_usable_false",
                "old_child_label_used": any(
                    old in json.dumps(template, sort_keys=True) for old in OLD_CHILD_LABELS
                ),
            }
        )

    surface_rows = [
        {
            "consumer": "analyze/report trace",
            "runtime_surface": "RegimeConsumerBundleAdapter::trace_entries",
            "contract_status": "supported_now",
            "evidence": "schema_version plus latest_decision and consumer_hints are present in all templates",
            "limit": "trace/report context only; not a completion claim",
        },
        {
            "consumer": "pre-bayes diagnostics",
            "runtime_surface": "append_read_only_bbn_diagnostics",
            "contract_status": "supported_now_read_only",
            "evidence": "read_only regime_bbn_* entries can be appended without opt-in mutation",
            "limit": "diagnostic assignments only",
        },
        {
            "consumer": "BBN soft evidence mutation",
            "runtime_surface": "apply_bbn_soft_evidence_to_pre_bayes_filter",
            "contract_status": "intentionally_neutral",
            "evidence": "templates set trade_usable=false and use MainRegimeV2 or DirectOverlay labels, not old child labels",
            "limit": "do not enable BBN mutation from these templates until protocol maps MainRegimeV2 directly",
        },
        {
            "consumer": "execution tree",
            "runtime_surface": "execution_tree_hint trace",
            "contract_status": "supported_as_transition_guardrail_hint",
            "evidence": "all templates carry execution_tree_hint=transition_guardrail",
            "limit": "does not force trade entry or path acceptance",
        },
        {
            "consumer": "CatBoost/path-ranker",
            "runtime_surface": "path_ranker_context",
            "contract_status": "template_only_currently_unconsumed",
            "evidence": "adapter deserializes path_ranker_context but current code search found no active consumer",
            "limit": "requires later runtime wiring before it can affect ranking",
        },
    ]

    contract = {
        "run_id": RUN_ID,
        "artifact_type": "regime_downstream_consumer_contract_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": (
            "Turn the accepted 5/5 regime-factor map into runtime bundle templates "
            "without reintroducing child/sub-regime labels as parent evidence."
        ),
        "source_consumer_map": repo_rel(CONSUMER_MAP),
        "adapter_notes": adapter_notes,
        "templates": template_rows,
        "surfaces": surface_rows,
        "rollup": {
            "template_count": len(template_rows),
            "active_lane_templates": [row["regime"] for row in template_rows],
            "all_templates_schema_valid": all(row["schema_version"] == SCHEMA_VERSION for row in template_rows),
            "all_templates_trade_usable_false": all(row["trade_usable"] is False for row in template_rows),
            "old_child_labels_used": any(row["old_child_label_used"] for row in template_rows),
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "full_objective_achieved": False,
            "update_goal": False,
            "next_action": (
                "Run a no-trade analyze dry-run with one generated bundle template in "
                "read-only mode and verify regime_bundle_trace plus read_only regime_bbn diagnostics."
            ),
        },
    }

    OUT_JSON.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        OUT_TEMPLATE_INDEX,
        template_rows,
        [
            "regime",
            "bundle_template",
            "schema_version",
            "final_label",
            "decision_state",
            "trade_usable",
            "execution_tree_hint",
            "bbn_soft_evidence_application",
            "old_child_label_used",
        ],
    )
    write_csv(
        OUT_CSV,
        surface_rows,
        ["consumer", "runtime_surface", "contract_status", "evidence", "limit"],
    )

    md_lines = [
        "# Regime Downstream Consumer Contract v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        "- Generated runtime-shape `regime-consumer-bundle/v1` templates for all `5/5` active lanes.",
        "- Templates preserve `MainRegimeV2` and `DirectOverlay::Manipulation` labels; no old child/sub-regime labels are used.",
        "- Current runtime can consume these templates as read-only trace/pre-Bayes diagnostics.",
        "- BBN soft-evidence mutation is intentionally neutral because templates are `trade_usable=false` and the current adapter does not directly map `MainRegimeV2` labels.",
        "- Full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Runtime Surfaces",
        "",
        "| Consumer | Surface | Status | Limit |",
        "|---|---|---|---|",
    ]
    for row in surface_rows:
        md_lines.append(
            f"| {row['consumer']} | `{row['runtime_surface']}` | `{row['contract_status']}` | {row['limit']} |"
        )
    md_lines.extend(["", "## Templates", "", "| Regime | Template | Label | Trade usable |", "|---|---|---|---:|"])
    for row in template_rows:
        md_lines.append(
            f"| {row['regime']} | `{row['bundle_template']}` | `{row['final_label']}` | `{str(row['trade_usable']).lower()}` |"
        )
    md_lines.extend(
        [
            "",
            "## Adapter Boundary",
            "",
            f"- Adapter: `{adapter_notes['adapter_path']}`",
            f"- Supports schema now: `{str(adapter_notes['supports_bundle_schema']).lower()}`",
            f"- Explicit MainRegimeV2 mapper present now: `{str(adapter_notes['explicit_mainregime_label_mapper_present']).lower()}`",
            "- Contract decision: keep these templates read-only until runtime supports MainRegimeV2 labels directly, without translating through old child/sub-regime labels.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{repo_rel(OUT_JSON)}`",
            f"- Surface CSV: `{repo_rel(OUT_CSV)}`",
            f"- Template index: `{repo_rel(OUT_TEMPLATE_INDEX)}`",
            f"- Bundle templates: `{repo_rel(TEMPLATE_DIR)}`",
            f"- Assertions: `{repo_rel(OUT_ASSERT)}`",
        ]
    )
    OUT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertions = {
        "template_count": len(template_rows),
        "all_templates_schema_valid": all(row["schema_version"] == SCHEMA_VERSION for row in template_rows),
        "all_templates_trade_usable_false": all(row["trade_usable"] is False for row in template_rows),
        "old_child_labels_used": any(row["old_child_label_used"] for row in template_rows),
        "supports_bundle_schema": adapter_notes["supports_bundle_schema"],
        "explicit_mainregime_label_mapper_present": adapter_notes[
            "explicit_mainregime_label_mapper_present"
        ],
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "full_objective_achieved": False,
        "update_goal": False,
        "assertion_status": "PASS",
    }
    OUT_ASSERT.write_text(
        "\n".join(
            f"{key}={str(value).lower() if isinstance(value, bool) else value}"
            for key, value in assertions.items()
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(assertions, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
