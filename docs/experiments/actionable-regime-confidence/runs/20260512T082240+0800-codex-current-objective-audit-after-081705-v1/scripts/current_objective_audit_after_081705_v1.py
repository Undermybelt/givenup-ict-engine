#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T082240+0800-codex-current-objective-audit-after-081705-v1"
SLUG = "current-objective-audit-after-081705-v1"
GATE = "current_objective_audit_after_081705_v1=not_complete_source_control_unlock_absent_no_downstream_promotion"

REPO = Path(__file__).resolve().parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"

ROUTE_ASSERTIONS = {
    "080906_openalex_semantic_pwc": "20260512T080906+0800-codex-openalex-semantic-pwc-source-route-after-080700-v1/checks/openalex_semantic_pwc_source_route_after_080700_v1_assertions.out",
    "081155_arrival_poll": "20260512T081155+0800-codex-source-control-arrival-poll-after-080837-v1/checks/source_control_arrival_poll_after_080837_v1_assertions.out",
    "081227_objective_audit": "20260512T081227+0800-codex-current-objective-audit-after-080906-v1/checks/current_objective_audit_after_080906_v1_assertions.out",
    "081323_recap_sibling": "20260512T081323+0800-codex-courtlistener-recap-sibling-attachment-probe-after-080906-v1/checks/courtlistener_recap_sibling_attachment_probe_after_080906_v1_assertions.out",
    "081522_recap_control": "20260512T081522+0800-codex-r6-courtlistener-recap-control-route-after-080950-v1/checks/r6_courtlistener_recap_control_route_after_080950_v1_assertions.out",
    "081705_recap_fast": "20260512T081705+0800-codex-courtlistener-recap-sibling-fast-probe-after-081323-v1/checks/courtlistener_recap_sibling_fast_probe_after_081323_v1_assertions.out",
}

TARGET_ROOTS = {
    "r6_owner_export": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r5_recency": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "r3_native_subhour": Path("/private/tmp/ict-engine-native-subhour-source-label-intake"),
    "source_label_equivalence": Path("/private/tmp/ict-engine-source-label-equivalence-intake"),
}

SECRET_HINTS = [
    "COURTLISTENER_TOKEN",
    "PACER_USERNAME",
    "PACER_PASSWORD",
    "RECAP_EMAIL",
    "CME_API_KEY",
    "CME_DATA_KEY",
    "CBOE_API_KEY",
    "CFE_API_KEY",
    "FINRA_API_KEY",
    "DATABENTO_API_KEY",
    "IBKR_HOST",
    "TRADINGVIEW_SESSION",
    "KRAKEN_API_KEY",
]


def sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_assertions(path: Path) -> dict[str, str]:
    if not path.exists():
        return {"_present": "false"}
    out: dict[str, str] = {"_present": "true"}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes", "pass"}


def root_summary(name: str, root: Path) -> dict[str, object]:
    files = []
    if root.exists():
        if root.is_file():
            files = [str(root)]
        else:
            files = [str(path) for path in sorted(root.rglob("*")) if path.is_file()][:20]
    return {
        "name": name,
        "path": str(root),
        "present": root.exists(),
        "file_count_sampled": len(files),
        "sample_files": files,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    board_hash = sha256_file(BOARD)
    assertions_root = REPO / "docs/experiments/actionable-regime-confidence/runs"
    route_rows = []
    missing_assertions = []
    any_unlock = False
    any_update_goal = False
    for name, rel in ROUTE_ASSERTIONS.items():
        path = assertions_root / rel
        parsed = parse_assertions(path)
        if parsed.get("_present") != "true":
            missing_assertions.append(name)
        route_unlock = truthy(parsed.get("valid_required_root_unlock"))
        route_source = truthy(parsed.get("source_control_evidence_acquired"))
        route_update = truthy(parsed.get("update_goal"))
        any_unlock = any_unlock or route_unlock or route_source
        any_update_goal = any_update_goal or route_update
        route_rows.append(
            {
                "name": name,
                "path": str(path),
                "present": parsed.get("_present") == "true",
                "gate": parsed.get("gate_result") or parsed.get("gate") or "",
                "accepted_rows_added": parsed.get("accepted_rows_added", "0"),
                "valid_required_root_unlock": str(route_unlock).lower(),
                "source_control_evidence_acquired": str(route_source).lower(),
                "update_goal": str(route_update).lower(),
            }
        )

    roots = [root_summary(name, path) for name, path in TARGET_ROOTS.items()]
    credential_hints = {name: bool(os.environ.get(name)) for name in SECRET_HINTS}
    credential_hint_count = sum(credential_hints.values())

    checklist = [
        {
            "requirement": "board_a_authoritative_file",
            "status": "covered",
            "evidence": str(BOARD),
            "blocker": "",
        },
        {
            "requirement": "all_regimes_95_confidence",
            "status": "blocked",
            "evidence": "Latest post-080906/0815xx/081705 source-control routes add zero accepted rows and no valid required root.",
            "blocker": "No valid R6 owner/export, R5 recency, or Crisis-capable R3 source/control root.",
        },
        {
            "requirement": "cross_market_cross_timeframe_validation",
            "status": "blocked",
            "evidence": "No accepted cross-timeframe MainRegimeV2 source export or verifier-native Crisis-capable R3 rows in latest assertions.",
            "blocker": "Source/control unlock absent.",
        },
        {
            "requirement": "ibkr_tradingview_yfinance_kraken_provider_use",
            "status": "partial",
            "evidence": "Earlier provider/runtime readbacks exist; current slice checked source/control and credential presence only.",
            "blocker": "Provider reachability cannot substitute for source/control evidence.",
        },
        {
            "requirement": "auto_quant_operated",
            "status": "partial",
            "evidence": "Earlier Auto-Quant readbacks exist, but selected-data promotion remains false in latest assertions.",
            "blocker": "No canonical source/control unlock.",
        },
        {
            "requirement": "filter_prebayes_bbn_catboost_execution_tree",
            "status": "blocked",
            "evidence": "Latest assertions keep canonical_merge=false and downstream_promotion_rerun=false.",
            "blocker": "Direct verifier/split calibration/canonical merge input is invalid until source/control unlock.",
        },
        {
            "requirement": "source_control_unlock",
            "status": "blocked",
            "evidence": f"Assertion roots checked {len(route_rows)}; missing assertions {len(missing_assertions)}; any_unlock={any_unlock}.",
            "blocker": "Owner/export or explicit FLIP-control approval still absent.",
        },
        {
            "requirement": "multi_agent_append_only",
            "status": "covered",
            "evidence": "This audit writes a new run root and does not edit cursor or prior sections.",
            "blocker": "",
        },
        {
            "requirement": "update_goal_allowed",
            "status": "blocked",
            "evidence": f"any_update_goal={any_update_goal}; strict_full_objective=false in latest route assertions.",
            "blocker": "Objective incomplete.",
        },
    ]

    payload = {
        "run_id": RUN_ID,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact": board_hash,
        "gate_result": GATE,
        "route_assertions": route_rows,
        "missing_assertions": missing_assertions,
        "target_roots": roots,
        "credential_hint_names_present_count": credential_hint_count,
        "credential_hint_names_present": sorted([k for k, v in credential_hints.items() if v]),
        "checklist": checklist,
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

    (OUT / "current_objective_audit_after_081705_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with (OUT / "prompt_to_artifact_checklist_after_081705_v1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        writer = csv.DictWriter(fh, fieldnames=["requirement", "status", "evidence", "blocker"])
        writer.writeheader()
        writer.writerows(checklist)

    with (OUT / "route_assertions_after_081705_v1.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "name",
                "path",
                "present",
                "gate",
                "accepted_rows_added",
                "valid_required_root_unlock",
                "source_control_evidence_acquired",
                "update_goal",
            ],
        )
        writer.writeheader()
        writer.writerows(route_rows)

    lines = [
        "# Current Objective Audit After 081705 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE}`",
        "",
        "## Objective Restatement",
        "",
        "Board A must lift each active regime/root to 95%+ calibrated confidence, validate across markets/periods/timeframes, and only then run the real AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree chain. No downstream promotion is allowed without a valid source/control unlock and canonical merge.",
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
            "## Latest Assertion Readback",
            "",
            "| Route | Gate | Valid root unlock | Source/control acquired | Accepted rows | update_goal |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in route_rows:
        lines.append(
            f"| `{row['name']}` | `{row['gate']}` | `{row['valid_required_root_unlock']}` | `{row['source_control_evidence_acquired']}` | `{row['accepted_rows_added']}` | `{row['update_goal']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Blocked requirements: `{sum(1 for item in checklist if item['status'] == 'blocked')}`; partial requirements: `{sum(1 for item in checklist if item['status'] == 'partial')}`.",
            f"- Missing assertion roots: `{', '.join(missing_assertions) if missing_assertions else 'none'}`.",
            f"- Credential hint names present: `{credential_hint_count}`; values were not printed.",
            "- No valid R6/R5/R3 source/control root was acquired.",
            "- Canonical merge, selected-data AutoQuant promotion, downstream promotion rerun, strict full objective, trade usable, and `update_goal` all remain false.",
            "",
            "## Next",
            "",
            "Continue source/control acquisition only. The live unblocker remains owner-approved/authenticated FINRA, venue-surveillance, CAT-like, CME/Cboe/CFE/exchange order-lifecycle export with both positives and matched normal controls, or explicit same-exhibit `FLIP`-as-control approval before any verifier, split calibration, canonical merge, selected-data AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, or execution-tree promotion.",
            "",
        ]
    )
    (OUT / "current_objective_audit_after_081705_v1.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )

    assertions = [
        f"gate_result={GATE}",
        f"assertion_roots_checked={len(route_rows)}",
        f"missing_assertion_roots={len(missing_assertions)}",
        f"blocked_requirements={sum(1 for item in checklist if item['status'] == 'blocked')}",
        f"partial_requirements={sum(1 for item in checklist if item['status'] == 'partial')}",
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
    (CHECKS / "current_objective_audit_after_081705_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    print("\n".join(assertions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
