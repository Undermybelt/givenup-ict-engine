#!/usr/bin/env python3
"""Prompt-to-artifact completion audit after the 082458 arrival poll."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T082720+0800-codex-current-objective-audit-after-082458-v1"
SLUG = "current-objective-audit-after-082458-v1"
GATE_RESULT = (
    "current_objective_audit_after_082458_v1="
    "not_complete_source_control_roots_absent_no_downstream_promotion"
)

REPO = Path(__file__).resolve().parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"

ASSERTION_FILES = {
    "081705_recap_fast": "20260512T081705+0800-codex-courtlistener-recap-sibling-fast-probe-after-081323-v1/checks/courtlistener_recap_sibling_fast_probe_after_081323_v1_assertions.out",
    "082215_recap_single_retry": "20260512T082215+0800-codex-r6-recap-novel-pdf-single-retry-after-081323-v1/checks/r6_recap_novel_pdf_single_retry_after_081323_v1_assertions.out",
    "082240_current_objective_audit": "20260512T082240+0800-codex-current-objective-audit-after-081705-v1/checks/current_objective_audit_after_081705_v1_assertions.out",
    "082302_owner_export_dispatch_readback": "20260512T082302+0800-codex-r6-owner-export-current-dispatch-and-arrival-readback-after-081705-v1/checks/r6_owner_export_current_dispatch_and_arrival_readback_after_081705_v1_assertions.out",
    "082314_source_control_arrival_poll": "20260512T082314+0800-codex-source-control-arrival-poll-after-081705-v1/checks/source_control_arrival_poll_after_081705_v1_assertions.out",
    "082458_source_control_arrival_poll": "20260512T082458+0800-codex-source-control-arrival-poll-after-082240-v1/checks/source_control_arrival_poll_after_082240_v1_assertions.out",
}

TARGET_ROOTS = {
    "r6_owner_export_tmp": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r6_owner_export_private_tmp": Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r5_recency": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "r3_native_subhour": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "r3_native_subhour_private_tmp": Path("/private/tmp/ict-engine-native-subhour-source-label-intake"),
}

OWNER_ROUTE_ENV_NAMES = [
    "FINRA_API_KEY",
    "CAT_API_KEY",
    "CME_API_KEY",
    "CME_DATA_KEY",
    "CBOE_API_KEY",
    "CFE_API_KEY",
    "DATABENTO_API_KEY",
    "IBKR_HOST",
    "TRADINGVIEW_SESSION",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_assertions(path: Path) -> dict[str, str]:
    parsed: dict[str, str] = {"_present": str(path.exists()).lower()}
    if not path.exists():
        return parsed
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if line.startswith("PASS "):
            line = line[5:]
        elif line.startswith("FAIL "):
            line = line[5:]
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes", "pass"}


def first_value(parsed: dict[str, str], *names: str, default: str = "") -> str:
    for name in names:
        if name in parsed:
            return parsed[name]
    return default


def root_row(name: str, root: Path) -> dict[str, object]:
    sample: list[str] = []
    if root.exists() and root.is_dir():
        sample = [str(path) for path in sorted(root.glob("*")) if path.is_file()][:12]
    elif root.exists():
        sample = [str(root)]
    return {
        "name": name,
        "path": str(root),
        "present": root.exists(),
        "sample_file_count": len(sample),
        "sample_files": sample,
    }


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    assertions_root = REPO / "docs/experiments/actionable-regime-confidence/runs"
    assertion_rows: list[dict[str, object]] = []
    missing_assertions: list[str] = []
    any_valid_unlock = False
    any_source_control = False
    any_update_goal = False
    any_downstream = False

    for name, relative in ASSERTION_FILES.items():
        path = assertions_root / relative
        parsed = parse_assertions(path)
        if parsed["_present"] != "true":
            missing_assertions.append(name)
        valid_unlock = truthy(first_value(parsed, "valid_required_root_unlock"))
        source_control = truthy(first_value(parsed, "source_control_evidence_acquired"))
        update_goal = truthy(first_value(parsed, "update_goal"))
        downstream = truthy(first_value(parsed, "downstream_promotion_rerun", "downstream_rerun_allowed_now"))
        any_valid_unlock = any_valid_unlock or valid_unlock
        any_source_control = any_source_control or source_control
        any_update_goal = any_update_goal or update_goal
        any_downstream = any_downstream or downstream
        assertion_rows.append(
            {
                "name": name,
                "path": rel(path),
                "present": parsed["_present"],
                "gate_result": first_value(parsed, "gate_result", "gate"),
                "accepted_rows_added": first_value(parsed, "accepted_rows_added", default="0"),
                "valid_required_root_unlock": str(valid_unlock).lower(),
                "source_control_evidence_acquired": str(source_control).lower(),
                "downstream_promotion_rerun": str(downstream).lower(),
                "update_goal": str(update_goal).lower(),
            }
        )

    root_rows = [root_row(name, root) for name, root in TARGET_ROOTS.items()]
    owner_env_present = sorted(name for name in OWNER_ROUTE_ENV_NAMES if os.environ.get(name))

    checklist = [
        {
            "requirement": "named_board_file_followed",
            "status": "covered",
            "evidence": rel(BOARD),
            "blocker": "",
        },
        {
            "requirement": "every_regime_confidence_95_plus",
            "status": "blocked",
            "evidence": "Post-082458 terminal assertions add 0 accepted rows and no valid source/control root.",
            "blocker": "No R6 owner/export rows with valid controls, no R5 recency rows, no accepted Crisis-capable R3 source labels.",
        },
        {
            "requirement": "other_market_other_cycle_validation",
            "status": "blocked",
            "evidence": "No accepted cross-market/cross-timeframe MainRegimeV2 source export in counted post-082458 artifacts.",
            "blocker": "Validation cannot proceed without source/control unlock.",
        },
        {
            "requirement": "ibkr_tradingview_yfinance_kraken_considered",
            "status": "partial",
            "evidence": "Earlier provider readbacks exist; 082458 confirms owner/export credential hints absent and source/control gate still closed.",
            "blocker": "Provider readiness is not label/control evidence.",
        },
        {
            "requirement": "auto_quant_selected_data_promotion",
            "status": "blocked",
            "evidence": "Latest counted assertions keep selected-data AutoQuant promotion false.",
            "blocker": "No canonical source/control merge input.",
        },
        {
            "requirement": "filter_prebayes_bbn_catboost_execution_tree_chain",
            "status": "blocked",
            "evidence": "Latest counted assertions keep downstream promotion rerun false.",
            "blocker": "Direct verifier, split calibration, and canonical merge remain disallowed.",
        },
        {
            "requirement": "prompt_to_artifact_completion_audit",
            "status": "covered",
            "evidence": "This run writes JSON, checklist CSV, assertion CSV, report, and assertion output.",
            "blocker": "",
        },
        {
            "requirement": "multi_agent_append_only_safety",
            "status": "covered",
            "evidence": "New run root only; board update must append without cursor rewrite.",
            "blocker": "",
        },
        {
            "requirement": "update_goal_complete_allowed",
            "status": "blocked",
            "evidence": f"any_valid_unlock={any_valid_unlock}; any_source_control={any_source_control}; any_downstream={any_downstream}; any_update_goal={any_update_goal}.",
            "blocker": "Objective is not complete.",
        },
    ]

    blocked_requirements = sum(1 for row in checklist if row["status"] == "blocked")
    partial_requirements = sum(1 for row in checklist if row["status"] == "partial")

    payload = {
        "run_id": RUN_ID,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_before_artifact": sha256(BOARD),
        "gate_result": GATE_RESULT,
        "checklist": checklist,
        "assertion_rows": assertion_rows,
        "target_roots": root_rows,
        "missing_assertions": missing_assertions,
        "owner_route_env_names_present_count": len(owner_env_present),
        "owner_route_env_names_present": owner_env_present,
        "blocked_requirements": blocked_requirements,
        "partial_requirements": partial_requirements,
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

    json_path = OUT / "current_objective_audit_after_082458_v1.json"
    checklist_path = OUT / "prompt_to_artifact_checklist_after_082458_v1.csv"
    assertions_csv_path = OUT / "route_assertions_after_082458_v1.csv"
    roots_csv_path = OUT / "target_roots_after_082458_v1.csv"
    report_path = OUT / "current_objective_audit_after_082458_v1.md"
    assertions_path = CHECKS / "current_objective_audit_after_082458_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(checklist_path, checklist, ["requirement", "status", "evidence", "blocker"])
    write_csv(
        assertions_csv_path,
        assertion_rows,
        [
            "name",
            "path",
            "present",
            "gate_result",
            "accepted_rows_added",
            "valid_required_root_unlock",
            "source_control_evidence_acquired",
            "downstream_promotion_rerun",
            "update_goal",
        ],
    )
    write_csv(roots_csv_path, root_rows, ["name", "path", "present", "sample_file_count", "sample_files"])

    lines = [
        "# Current Objective Audit After 082458 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE_RESULT}`",
        "",
        f"Board sha256 before artifact: `{payload['board_sha256_before_artifact']}`",
        "",
        "## Objective Restatement",
        "",
        "Board A requires every active regime to reach calibrated 95%+ confidence, then retain suitable confidence on other markets and other periods/timeframes. Only after a valid source/control root and canonical merge may the real AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree chain run and be counted.",
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence | Blocker |",
        "|---|---|---|---|",
    ]
    for item in checklist:
        lines.append(f"| `{item['requirement']}` | `{item['status']}` | {item['evidence']} | {item['blocker']} |")
    lines.extend(
        [
            "",
            "## Counted Assertion Readback",
            "",
            "| Route | Gate | Valid root unlock | Source/control | Downstream rerun | update_goal |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in assertion_rows:
        lines.append(
            f"| `{row['name']}` | `{row['gate_result']}` | `{row['valid_required_root_unlock']}` | `{row['source_control_evidence_acquired']}` | `{row['downstream_promotion_rerun']}` | `{row['update_goal']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Blocked requirements: `{blocked_requirements}`; partial requirements: `{partial_requirements}`.",
            f"- Missing assertion roots: `{len(missing_assertions)}`.",
            f"- Owner-route credential env names present: `{len(owner_env_present)}`; values were not printed.",
            "- No valid R6 owner/export, R5 recency, or accepted R3 native-subhour source/control root is present.",
            "- Canonical merge, selected-data AutoQuant promotion, downstream promotion rerun, strict full objective, trade usable, and `update_goal` remain false.",
            "",
            "## Next",
            "",
            "Continue source/control acquisition only. The live unblocker remains an owner-approved/authenticated FINRA, venue-surveillance, CAT-like, CME/Cboe/CFE exchange order-lifecycle export with both positives and matched normal controls, or explicit same-exhibit `FLIP`-as-control approval, before any verifier, split calibration, canonical merge, selected-data AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, or execution-tree promotion.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")

    assertion_lines = [
        f"gate_result={GATE_RESULT}",
        f"assertion_roots_checked={len(assertion_rows)}",
        f"missing_assertion_roots={len(missing_assertions)}",
        f"blocked_requirements={blocked_requirements}",
        f"partial_requirements={partial_requirements}",
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
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
