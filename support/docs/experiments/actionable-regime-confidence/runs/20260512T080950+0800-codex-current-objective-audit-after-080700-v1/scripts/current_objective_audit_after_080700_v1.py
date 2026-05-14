#!/usr/bin/env python3
"""Post-080700 Board A completion audit.

This script only reads existing Board A artifacts and writes a compact audit
packet into this run root. It does not mutate target roots or run promotion.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "current-objective-audit-after-080700-v1"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUNS = REPO / "docs/experiments/actionable-regime-confidence/runs"


RELATED_ASSERTIONS = {
    "075925_public_dataset_hub": RUNS / "20260512T075925+0800-codex-public-dataset-hub-source-route-probe-after-075420-v1/checks/public_dataset_hub_source_route_probe_after_075420_v1_assertions.out",
    "075932_figshare_osf": RUNS / "20260512T075932+0800-codex-figshare-osf-source-route-probe-after-075818-v1/checks/figshare_osf_source_route_probe_after_075818_v1_assertions.out",
    "080333_openml_dataverse": RUNS / "20260512T080333+0800-codex-openml-dataverse-source-route-probe-after-075932-v1/checks/openml_dataverse_source_route_probe_after_075932_v1_assertions.out",
    "080336_arrival_poll": RUNS / "20260512T080336+0800-codex-source-control-arrival-poll-after-080054-v1/checks/source_control_arrival_poll_after_080054_v1_assertions.out",
    "080411_regulator_exchange": RUNS / "20260512T080411+0800-codex-r6-regulator-exchange-source-route-probe-after-080054-v1/checks/r6_regulator_exchange_source_route_probe_after_080054_v1_assertions.out",
    "080425_target_approval": RUNS / "20260512T080425+0800-codex-target-root-approval-readback-after-075925-v1/checks/target_root_approval_readback_after_075925_v1_assertions.out",
    "080452_dryad": RUNS / "20260512T080452+0800-codex-dryad-source-route-probe-after-080054-v1/checks/dryad_source_route_probe_after_080054_v1_assertions.out",
    "080700_exact_web_search": RUNS / "20260512T080700+0800-codex-openml-dryad-mendeley-exact-web-search-after-080054-v1/checks/openml_dryad_mendeley_exact_web_search_after_080054_v1_assertions.out",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_assertions(path: Path) -> dict[str, str]:
    data: dict[str, str] = {"exists": str(path.exists()).lower()}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("PASS "):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    return data


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    route_readbacks = []
    for name, path in RELATED_ASSERTIONS.items():
        parsed = parse_assertions(path)
        route_readbacks.append(
            {
                "name": name,
                "assertions": repo_rel(path),
                "exists": parsed.get("exists") == "true",
                "gate_result": parsed.get("gate_result", ""),
                "valid_required_root_unlock": parsed.get("valid_required_root_unlock", "false"),
                "source_control_evidence_acquired": parsed.get("source_control_evidence_acquired", "false"),
                "accepted_rows_added": parsed.get("accepted_rows_added", "0"),
                "update_goal": parsed.get("update_goal", "false"),
            }
        )

    checklist = [
        {
            "requirement": "board_a_authoritative_file",
            "status": "covered",
            "evidence": repo_rel(BOARD),
            "blocker": "",
        },
        {
            "requirement": "all_regimes_95_confidence",
            "status": "blocked",
            "evidence": "Latest post-080054 route probes add zero accepted rows and no valid required source/control root.",
            "blocker": "R6/R5/R3 required source/control unlock absent; scoped prior 95 evidence does not close full objective.",
        },
        {
            "requirement": "cross_market_cross_timeframe_validation",
            "status": "blocked",
            "evidence": "080333/080452/080700 public source routes found no exact MainRegimeV2/R5/R3/R6 unlock.",
            "blocker": "No accepted cross-timeframe MainRegimeV2 source export or verifier-native Crisis-capable R3 rows.",
        },
        {
            "requirement": "ibkr_tradingview_yfinance_kraken_provider_use",
            "status": "partial",
            "evidence": "Prior provider/cache and runtime readbacks cover provider visibility only.",
            "blocker": "Provider diagnostics are not source/control acceptance and promotion remains blocked.",
        },
        {
            "requirement": "auto_quant_operated",
            "status": "partial",
            "evidence": "Prior Auto-Quant status/readback exists, but selected-data promotion is blocked.",
            "blocker": "No canonical source/control unlock, so Auto-Quant cannot be promoted for this objective.",
        },
        {
            "requirement": "filter_prebayes_bbn_catboost_execution_tree",
            "status": "blocked",
            "evidence": "Downstream chain is explicitly forbidden before source/control unlock and canonical merge.",
            "blocker": "No direct verifier/split-calibration/canonical merge input is valid yet.",
        },
        {
            "requirement": "source_control_unlock",
            "status": "blocked",
            "evidence": "080336 arrival poll and 080425 target approval readback both report valid_required_root_unlock=false.",
            "blocker": "R6 owner/export absent, R5 recency absent, R3 Crisis absent, approval false.",
        },
        {
            "requirement": "multi_agent_append_only",
            "status": "covered",
            "evidence": "This audit writes a new run root and appends only; Current Cursor is not edited.",
            "blocker": "",
        },
        {
            "requirement": "update_goal_allowed",
            "status": "blocked",
            "evidence": "strict_full_objective=false and update_goal=false across latest route assertions.",
            "blocker": "Objective incomplete.",
        },
    ]

    summary = {
        "run_id": "20260512T080950+0800-codex-current-objective-audit-after-080700-v1",
        "board_sha256": sha256(BOARD),
        "gate_result": "current_objective_audit_after_080700_v1=not_complete_latest_public_routes_no_required_unlock_no_downstream_promotion",
        "blocked_requirements": sum(1 for item in checklist if item["status"] == "blocked"),
        "partial_requirements": sum(1 for item in checklist if item["status"] == "partial"),
        "covered_requirements": sum(1 for item in checklist if item["status"] == "covered"),
        "accepted_rows_added": 0,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    payload = {
        "summary": summary,
        "checklist": checklist,
        "route_readbacks": route_readbacks,
    }
    (OUT / "current_objective_audit_after_080700_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with (OUT / "prompt_to_artifact_checklist_after_080700_v1.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["requirement", "status", "evidence", "blocker"])
        writer.writeheader()
        writer.writerows(checklist)

    lines = [
        "# Current Objective Audit After 080700 v1",
        "",
        "Run id: `20260512T080950+0800-codex-current-objective-audit-after-080700-v1`",
        "",
        "Gate result: `current_objective_audit_after_080700_v1=not_complete_latest_public_routes_no_required_unlock_no_downstream_promotion`",
        "",
        "## Objective Restatement",
        "",
        "Board A must lift every active regime/root to 95%+ calibrated confidence, validate across other markets and periods/timeframes, then run the real AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree chain. No downstream promotion is allowed without a valid source/control unlock and canonical merge.",
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence | Blocker |",
        "|---|---|---|---|",
    ]
    for item in checklist:
        lines.append(
            f"| `{item['requirement']}` | `{item['status']}` | {item['evidence']} | {item['blocker']} |"
        )
    lines.extend(
        [
            "",
            "## Latest Route Readbacks",
            "",
            "| Route | Gate | Valid root unlock | Source/control acquired | Accepted rows | update_goal |",
            "|---|---|---|---|---|---|",
        ]
    )
    for item in route_readbacks:
        lines.append(
            f"| `{item['name']}` | `{item['gate_result']}` | `{item['valid_required_root_unlock']}` | `{item['source_control_evidence_acquired']}` | `{item['accepted_rows_added']}` | `{item['update_goal']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Blocked requirements: `{summary['blocked_requirements']}`; partial requirements: `{summary['partial_requirements']}`.",
            "- Latest public/source-route probes still add `0` accepted rows and no required source/control unlock.",
            "- R6 owner/export remains absent, R5 post-cutoff recency remains absent, and R3 native-subhour remains Crisis-absent.",
            "- Canonical merge, selected-data AutoQuant promotion, downstream promotion rerun, strict full objective, trade usable, and `update_goal` all remain false.",
            "",
            "## Next",
            "",
            "Continue source/control acquisition only. The live next unblocker remains owner-approved/authenticated FINRA, venue-surveillance, CAT-like, CME/Cboe/CFE/exchange order-lifecycle export with both positives and matched normal controls, or explicit approval of the same-exhibit FLIP-as-control exception before any verifier, split calibration, canonical merge, selected-data AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, or execution-tree promotion.",
            "",
        ]
    )
    (OUT / "current_objective_audit_after_080700_v1.md").write_text("\n".join(lines), encoding="utf-8")

    assertion_lines = [
        "gate_result=current_objective_audit_after_080700_v1=not_complete_latest_public_routes_no_required_unlock_no_downstream_promotion",
        f"blocked_requirements={summary['blocked_requirements']}",
        f"partial_requirements={summary['partial_requirements']}",
        "accepted_rows_added=0",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    (CHECKS / "current_objective_audit_after_080700_v1_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
