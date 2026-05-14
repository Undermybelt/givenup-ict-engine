#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T081227+0800-codex-current-objective-audit-after-080906-v1"
SLUG = "current-objective-audit-after-080906-v1"
GATE = "current_objective_audit_after_080906_v1=not_complete_latest_public_routes_no_required_unlock_no_downstream_promotion"

REPO = Path(__file__).resolve().parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_ROOT = RUN_ROOT / SLUG
CHECK_ROOT = RUN_ROOT / "checks"

ROUTES = [
    (
        "075925_public_dataset_hub",
        "20260512T075925+0800-codex-public-dataset-hub-source-route-probe-after-075420-v1",
        "public_dataset_hub_source_route_probe_after_075420_v1_assertions.out",
    ),
    (
        "075932_figshare_osf",
        "20260512T075932+0800-codex-figshare-osf-source-route-probe-after-075818-v1",
        "figshare_osf_source_route_probe_after_075818_v1_assertions.out",
    ),
    (
        "080333_openml_dataverse",
        "20260512T080333+0800-codex-openml-dataverse-source-route-probe-after-075932-v1",
        "openml_dataverse_source_route_probe_after_075932_v1_assertions.out",
    ),
    (
        "080336_arrival_poll",
        "20260512T080336+0800-codex-source-control-arrival-poll-after-080054-v1",
        "source_control_arrival_poll_after_080054_v1_assertions.out",
    ),
    (
        "080411_regulator_exchange",
        "20260512T080411+0800-codex-r6-regulator-exchange-source-route-probe-after-080054-v1",
        "r6_regulator_exchange_source_route_probe_after_080054_v1_assertions.out",
    ),
    (
        "080425_target_approval",
        "20260512T080425+0800-codex-target-root-approval-readback-after-075925-v1",
        "target_root_approval_readback_after_075925_v1_assertions.out",
    ),
    (
        "080446_required_root_poll",
        "20260512T080446+0800-codex-required-root-arrival-poll-after-080054-v1",
        "required_root_arrival_poll_after_080054_v1_assertions.out",
    ),
    (
        "080452_dryad",
        "20260512T080452+0800-codex-dryad-source-route-probe-after-080054-v1",
        "dryad_source_route_probe_after_080054_v1_assertions.out",
    ),
    (
        "080700_exact_web_search",
        "20260512T080700+0800-codex-openml-dryad-mendeley-exact-web-search-after-080054-v1",
        "openml_dryad_mendeley_exact_web_search_after_080054_v1_assertions.out",
    ),
    (
        "080906_openalex_semantic_pwc",
        "20260512T080906+0800-codex-openalex-semantic-pwc-source-route-after-080700-v1",
        "openalex_semantic_pwc_source_route_after_080700_v1_assertions.out",
    ),
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_assertions(run_id: str, filename: str) -> dict[str, str]:
    path = REPO / "docs/experiments/actionable-regime-confidence/runs" / run_id / "checks" / filename
    result: dict[str, str] = {"assertions_path": str(path.relative_to(REPO)), "present": str(path.exists()).lower()}
    if not path.exists():
        return result
    for line in path.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("PASS ") or line.startswith("REVIEW "):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            result[key.strip()] = value.strip()
    return result


def boolish(value: str | None) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    CHECK_ROOT.mkdir(parents=True, exist_ok=True)

    route_rows = []
    for name, run_id, assertion_file in ROUTES:
        values = read_assertions(run_id, assertion_file)
        route_rows.append(
            {
                "route": name,
                "run_id": run_id,
                "gate_result": values.get("gate_result", ""),
                "present": values.get("present", "false"),
                "valid_required_root_unlock": values.get("valid_required_root_unlock", "false"),
                "source_control_evidence_acquired": values.get("source_control_evidence_acquired", "false"),
                "accepted_rows_added": values.get("accepted_rows_added", "0"),
                "update_goal": values.get("update_goal", "false"),
                "assertions_path": values.get("assertions_path", ""),
            }
        )

    unlock = any(boolish(row["valid_required_root_unlock"]) for row in route_rows)
    source_control = any(boolish(row["source_control_evidence_acquired"]) for row in route_rows)
    accepted_rows = sum(int(row["accepted_rows_added"] or "0") for row in route_rows if (row["accepted_rows_added"] or "0").isdigit())
    missing_routes = [row["route"] for row in route_rows if row["present"] != "true"]

    checklist = [
        ("board_a_authoritative_file", "covered", str(BOARD.relative_to(REPO)), ""),
        (
            "all_regimes_95_confidence",
            "blocked",
            "Latest post-080700 route probes add zero accepted rows and no valid source/control root.",
            "Strict full objective still lacks R6/R5/R3 source/control unlock.",
        ),
        (
            "cross_market_cross_timeframe_validation",
            "blocked",
            "080906 OpenAlex/SemanticScholar/PapersWithCode plus prior public routes found no exact MainRegimeV2/R5/R3/R6 unlock.",
            "No accepted cross-timeframe MainRegimeV2 source export or verifier-native Crisis-capable R3 rows.",
        ),
        (
            "ibkr_tradingview_yfinance_kraken_provider_use",
            "partial",
            "Prior provider/cache/runtime readbacks exist; this audit only checks source/control promotion status.",
            "Provider diagnostics are not source/control acceptance.",
        ),
        (
            "auto_quant_operated",
            "partial",
            "Prior Auto-Quant status/readback exists, but selected-data promotion remains false.",
            "No canonical source/control unlock.",
        ),
        (
            "filter_prebayes_bbn_catboost_execution_tree",
            "blocked",
            "Downstream chain remains explicitly forbidden before source/control unlock and canonical merge.",
            "No direct verifier/split-calibration/canonical merge input is valid.",
        ),
        (
            "source_control_unlock",
            "blocked",
            "Latest route assertions all report valid_required_root_unlock=false.",
            "R6 owner/export absent or incomplete, R5 recency absent, R3 Crisis absent, approval false.",
        ),
        ("multi_agent_append_only", "covered", "New run root only; board writeback should be append-only.", ""),
        ("update_goal_allowed", "blocked", "strict_full_objective=false and update_goal=false.", "Objective incomplete."),
    ]
    blocked = sum(1 for _, status, _, _ in checklist if status == "blocked")
    partial = sum(1 for _, status, _, _ in checklist if status == "partial")

    payload = {
        "run_id": RUN_ID,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact": sha256_file(BOARD),
        "gate_result": GATE,
        "objective_complete": False,
        "blocked_requirements": blocked,
        "partial_requirements": partial,
        "missing_routes": missing_routes,
        "accepted_rows_added": accepted_rows,
        "valid_required_root_unlock": unlock,
        "source_control_evidence_acquired": source_control,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
        "routes": route_rows,
        "checklist": [
            {"requirement": req, "status": status, "evidence": evidence, "blocker": blocker}
            for req, status, evidence, blocker in checklist
        ],
    }

    json_path = OUT_ROOT / "current_objective_audit_after_080906_v1.json"
    checklist_path = OUT_ROOT / "prompt_to_artifact_checklist_after_080906_v1.csv"
    md_path = OUT_ROOT / "current_objective_audit_after_080906_v1.md"
    assertions_path = CHECK_ROOT / "current_objective_audit_after_080906_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with checklist_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["requirement", "status", "evidence", "blocker"])
        writer.writerows(checklist)

    route_table = "\n".join(
        "| `{route}` | `{gate_result}` | `{valid_required_root_unlock}` | `{source_control_evidence_acquired}` | `{accepted_rows_added}` | `{update_goal}` |".format(**row)
        for row in route_rows
    )
    checklist_table = "\n".join(
        f"| `{req}` | `{status}` | {evidence} | {blocker} |" for req, status, evidence, blocker in checklist
    )

    md_path.write_text(
        "\n".join(
            [
                "# Current Objective Audit After 080906 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{GATE}`",
                "",
                "## Objective Restatement",
                "",
                "Board A must lift every active regime/root to 95%+ calibrated confidence, validate across other markets and periods/timeframes, then run the real AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree chain. No downstream promotion is allowed without a valid source/control unlock and canonical merge.",
                "",
                "## Prompt-to-Artifact Checklist",
                "",
                "| Requirement | Status | Evidence | Blocker |",
                "|---|---|---|---|",
                checklist_table,
                "",
                "## Latest Route Readbacks",
                "",
                "| Route | Gate | Valid root unlock | Source/control acquired | Accepted rows | update_goal |",
                "|---|---|---|---|---|---|",
                route_table,
                "",
                "## Decision",
                "",
                f"- Blocked requirements: `{blocked}`; partial requirements: `{partial}`.",
                f"- Missing route assertion files: `{', '.join(missing_routes) if missing_routes else 'none'}`.",
                "- Latest public/source-route probes through `080906` still add `0` accepted rows and no required source/control unlock.",
                "- R6 owner/export remains absent or incomplete, R5 post-cutoff recency remains absent, and R3 native-subhour remains Crisis-absent.",
                "- Canonical merge, selected-data AutoQuant promotion, downstream promotion rerun, strict full objective, trade usable, and `update_goal` all remain false.",
                "",
                "## Next",
                "",
                "Continue source/control acquisition only. The live next unblocker remains owner-approved/authenticated FINRA, venue-surveillance, CAT-like, CME/Cboe/CFE/exchange order-lifecycle export with both positives and matched normal controls, or explicit approval of the same-exhibit FLIP-as-control exception before any verifier, split calibration, canonical merge, selected-data AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, or execution-tree promotion.",
                "",
            ]
        )
    )

    assertions = [
        f"gate_result={GATE}",
        f"blocked_requirements={blocked}",
        f"partial_requirements={partial}",
        f"missing_route_assertions={len(missing_routes)}",
        f"accepted_rows_added={accepted_rows}",
        f"valid_required_root_unlock={str(unlock).lower()}",
        f"source_control_evidence_acquired={str(source_control).lower()}",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
