from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T221112-codex-field-complete-full-chain"
SOURCE_PACKET = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T212828-codex-legacy-regime-contract-reissue/evidence_packet_legacy_regime_contract_reissue.json"
OUT = RUN_ROOT / "regime-sidecar/regime_consumer_bundle.json"
DECISION_OUT = RUN_ROOT / "regime-sidecar/regime_high_confidence_decision.json"


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def main() -> None:
    source = json.loads(SOURCE_PACKET.read_text(encoding="utf-8"))
    packets = source["accepted_regime_packets"]
    labels = [packet["accepted_regime_id"] for packet in packets]
    min_lcb = min(packet["precision_wilson_lcb"] for packet in packets)
    max_transition_hazard = max(float(packet.get("transition_hazard") or 0.0) for packet in packets)
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    decision = {
        "timestamp": timestamp,
        "decision_state": "accepted_95_field_complete_6_of_6",
        "trade_usable": False,
        "final_label": "MultiRegimeFieldCompleteGuardrailSet",
        "label_set": labels,
        "abstain_reasons": [
            "board_a_confidence_only",
            "not_strategy_profitability",
            "board_b_must_prove_non_observe_release_and_path_specific_edge",
        ],
        "confidence_95": True,
        "confidence_99": False,
        "min_precision_wilson_lcb": min_lcb,
        "max_transition_hazard": max_transition_hazard,
        "source_packet": repo_rel(SOURCE_PACKET),
    }
    bundle = {
        "schema_version": "regime-consumer-bundle/v1",
        "artifact_count": len(packets) + 1,
        "missing_artifacts": [],
        "latest_decision": {
            "timestamp": decision["timestamp"],
            "decision_state": decision["decision_state"],
            "trade_usable": decision["trade_usable"],
            "final_label": decision["final_label"],
            "label_set": decision["label_set"],
            "abstain_reasons": decision["abstain_reasons"],
        },
        "consumer_hints": {
            "execution_tree_hint": "transition_guardrail",
            "bbn_evidence_hint": {
                "regime_decision_state": decision["decision_state"],
                "regime_trade_usable": False,
                "regime_label": decision["final_label"],
                "regime_label_set": labels,
                "regime_transition_hazard": max_transition_hazard,
                "regime_decision_reasons": decision["abstain_reasons"],
            },
            "path_ranker_context": {
                "regime_label": decision["final_label"],
                "regime_confidence_tier": "95",
                "precision_wilson_lcb_min": min_lcb,
                "accepted_regime_count": len(packets),
                "allowed_action": "context_guardrail_only_until_board_b_edge_gate_passes",
                "regime_trade_usable": False,
                "accepted_regimes": packets,
            },
            "user_vrp_nq_context": {},
            "trade_usable": False,
        },
        "artifacts": {
            "decision": {
                "status": "present",
                "path": repo_rel(DECISION_OUT),
                "schema_version": "regime-high-confidence-decision/v1",
            },
            "accepted_packet_set": {
                "status": "present",
                "path": repo_rel(SOURCE_PACKET),
                "schema_version": source["schema_version"],
            },
        },
        "consumer_contract": {
            "zero_config": True,
            "hotplug_scope": "include_artifact",
            "main_runtime_mutation": "none",
            "optional_for_consumers": True,
            "token_friendly": True,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    DECISION_OUT.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    OUT.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"bundle": repo_rel(OUT), "decision": repo_rel(DECISION_OUT), "labels": labels}, indent=2))


if __name__ == "__main__":
    main()
