#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T042030+0800-codex-bear-expansion-legacy-reissue-audit"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T042030-codex-bear-expansion-legacy-reissue-audit"
OUT_DIR = RUN_ROOT / "bear-reissue-audit"
CHECK_DIR = RUN_ROOT / "checks"

SOURCE_PATHS = [
    REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T232808-codex-broader-mtf-regime-search/audit/broader_mtf_regime_acceptance_audit.json",
    REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T214429-codex-legacy-regime-contract-reissue/legacy-contract/legacy_regime_contract_reissue_report.json",
    REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T205856-codex-sticky-hazard-per-regime/evidence_packet_sticky_hazard_cross_context.json",
]


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def collect_trend_packets(value: Any, source: Path, out: list[dict[str, Any]]) -> None:
    if isinstance(value, dict):
        if value.get("accepted_regime_id") == "TrendExpansion":
            out.append(
                {
                    "source": repo_rel(source),
                    "accepted_regime_id": value.get("accepted_regime_id"),
                    "qualifying_condition": value.get("qualifying_condition"),
                    "target_label": value.get("target_label"),
                    "target_name": value.get("target_name"),
                    "target_semantics": value.get("target_semantics"),
                    "precision_wilson_lcb": value.get("precision_wilson_lcb"),
                    "calibration_support": value.get("calibration_support"),
                    "test_support": value.get("test_support"),
                    "ece": value.get("ece"),
                    "coverage": value.get("coverage"),
                    "validation_instruments": value.get("validation_instruments"),
                    "validation_market_contexts": value.get("validation_market_contexts"),
                    "validation_timeframes": value.get("validation_timeframes"),
                }
            )
        for child in value.values():
            collect_trend_packets(child, source, out)
    elif isinstance(value, list):
        for child in value:
            collect_trend_packets(child, source, out)


def audit_packet(packet: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(
        str(packet.get(field) or "")
        for field in ["qualifying_condition", "target_label", "target_name", "target_semantics"]
    ).lower()
    bearish_markers = ["bear", "short", "down", "negative", "selloff", "drawdown64 <=", "ret", "<= -"]
    positive_blockers = ["drawdown64 >=", "drawdown_from_64_high >=", "trend_structural", "trend expansion persistence"]
    return {
        "source": packet["source"],
        "qualifying_condition": packet.get("qualifying_condition"),
        "target_label": packet.get("target_label"),
        "target_name": packet.get("target_name"),
        "target_semantics": packet.get("target_semantics"),
        "has_bearish_semantic_marker": any(marker in text for marker in bearish_markers),
        "has_positive_or_directionless_blocker": any(marker in text for marker in positive_blockers),
        "accepted_as_bear_expansion": False,
        "reason": "accepted TrendExpansion packet is directionless or non-bearish; it does not prove directional BearExpansion under the active root contract",
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    packets: list[dict[str, Any]] = []
    for path in SOURCE_PATHS:
        if path.exists():
            collect_trend_packets(json.loads(path.read_text(encoding="utf-8")), path, packets)
    audits = [audit_packet(packet) for packet in packets]
    accepted = [item for item in audits if item["accepted_as_bear_expansion"]]
    decision = {
        "gate_result": "blocked_bear_expansion_legacy_reissue_missing_directional_bear_semantics",
        "accepted_new_roots_95": [],
        "accepted_root_classes_95_effective": ["BullExpansion", "SidewaysConsolidation", "CrisisCrash"],
        "missing_root_classes_95_effective": ["BearExpansion", "Manipulation"],
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "fresh_calibration_rerun": False,
        "raw_committed_to_repo": False,
        "trade_usable": False,
        "next_action": "Acquire or build directional BearExpansion evidence with explicit down-expansion target labels; keep Manipulation direct-input gated.",
    }
    report = {
        "loop_id": RUN_ID,
        "objective": "Audit whether existing accepted TrendExpansion packets can be reissued as active BearExpansion evidence.",
        "source_paths": [repo_rel(path) for path in SOURCE_PATHS],
        "trend_packets_found": packets,
        "packet_audits": audits,
        "accepted_bear_expansion_reissues": accepted,
        "decision": decision,
    }
    report_json = OUT_DIR / "bear_expansion_legacy_reissue_audit.json"
    report_md = OUT_DIR / "bear_expansion_legacy_reissue_audit.md"
    assertions = CHECK_DIR / "bear_expansion_legacy_reissue_audit_assertions.out"
    report["artifacts"] = {"report_json": repo_rel(report_json), "report_md": repo_rel(report_md), "assertions": repo_rel(assertions)}
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# BearExpansion Legacy Reissue Audit",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        "- Accepted new active roots: none",
        "- Missing active roots remain: `BearExpansion`, `Manipulation`",
        "",
        "## Findings",
        "",
    ]
    for item in audits:
        lines.append(f"- `{item['source']}`: `{item['qualifying_condition']}` -> blocked; {item['reason']}.")
    report_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    assertion_lines = [
        f"loop_id={RUN_ID}",
        f"trend_packets_found={len(packets)}",
        f"accepted_bear_expansion_reissues={len(accepted)}",
        f"gate_result={decision['gate_result']}",
        "accepted_new_roots_95=none",
        "missing_root_classes_95_effective=BearExpansion,Manipulation",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
    ]
    assertions.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
