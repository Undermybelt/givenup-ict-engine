#!/usr/bin/env python3
"""Current objective audit after the 085612 public source/control route triage."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = RUN_ROOT / "current-objective-audit-after-085612-v1"
CHECKS_DIR = RUN_ROOT / "checks"

RUN_ID = "20260512T090006+0800-codex-current-objective-audit-after-085612-v1"
GATE = (
    "current_objective_audit_after_085612_v1="
    "not_complete_source_control_absent_no_selected_history_no_downstream_promotion"
)

BOARD_A = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
BOARD_B = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"

ASSERTION_FILES = {
    "085042_current_objective_audit": REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T085042+0800-codex-current-objective-audit-after-083703-v1"
    / "checks/current_objective_audit_after_083703_v1_assertions.out",
    "085131_dropzone_dispatch_refresh": REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T085131+0800-codex-source-control-dropzone-dispatch-refresh-after-083703-v1"
    / "checks/source_control_dropzone_dispatch_refresh_after_083703_v1_assertions.out",
    "085612_public_route_triage": REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T085612+0800-codex-public-spoofing-source-control-route-triage-after-085131-v1"
    / "checks/public_spoofing_source_control_route_triage_after_085131_v1_assertions.out",
}

SOURCE_FILES = {
    "085042_report": REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T085042+0800-codex-current-objective-audit-after-083703-v1"
    / "current-objective-audit-after-083703-v1/current_objective_audit_after_083703_v1.md",
    "085042_json": REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T085042+0800-codex-current-objective-audit-after-083703-v1"
    / "current-objective-audit-after-083703-v1/current_objective_audit_after_083703_v1.json",
    "085131_report": REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T085131+0800-codex-source-control-dropzone-dispatch-refresh-after-083703-v1"
    / "source-control-dropzone-dispatch-refresh-after-083703-v1/source_control_dropzone_dispatch_refresh_after_083703_v1.md",
    "085612_report": REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T085612+0800-codex-public-spoofing-source-control-route-triage-after-085131-v1"
    / "public-spoofing-source-control-route-triage-after-085131-v1/public_spoofing_source_control_route_triage_after_085131_v1.md",
}

TARGET_ROOTS = {
    "r6_owner_export_tmp": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r6_owner_export_private_tmp": Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r5_recency_tmp": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "r5_recency_private_tmp": Path("/private/tmp/ict-engine-source-panel-recency-extension"),
    "r3_native_subhour_tmp": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "r3_native_subhour_private_tmp": Path("/private/tmp/ict-engine-native-subhour-source-label-intake"),
}


def sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def parse_assertions(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" not in line or not line.strip():
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def boolish(value: str | None) -> bool:
    return str(value).lower() in {"true", "1", "yes"}


def root_status(name: str, root: Path) -> dict:
    files = []
    if root.exists():
        for item in sorted(root.rglob("*")):
            if item.is_file():
                try:
                    files.append({"path": str(item), "size": item.stat().st_size})
                except OSError:
                    files.append({"path": str(item), "size": None})
    return {
        "name": name,
        "path": str(root),
        "exists": root.exists(),
        "file_count": len(files),
        "sample_files": files[:12],
    }


def status_from_assertions(assertion_maps: dict[str, dict[str, str]]) -> dict:
    merged: dict[str, str] = {}
    for prefix, assertions in assertion_maps.items():
        for key, value in assertions.items():
            merged[f"{prefix}.{key}"] = value
    return {
        "valid_required_root_unlock": any(
            boolish(assertions.get("valid_required_root_unlock"))
            for assertions in assertion_maps.values()
        ),
        "source_control_evidence_acquired": any(
            boolish(assertions.get("source_control_evidence_acquired"))
            for assertions in assertion_maps.values()
        ),
        "canonical_merge": any(boolish(assertions.get("canonical_merge")) for assertions in assertion_maps.values()),
        "selected_data_autoquant_promotion": any(
            boolish(assertions.get("selected_data_autoquant_promotion"))
            for assertions in assertion_maps.values()
        ),
        "downstream_promotion_rerun": any(
            boolish(assertions.get("downstream_promotion_rerun"))
            for assertions in assertion_maps.values()
        ),
        "strict_full_objective": any(
            boolish(assertions.get("strict_full_objective"))
            for assertions in assertion_maps.values()
        ),
        "trade_usable": any(boolish(assertions.get("trade_usable")) for assertions in assertion_maps.values()),
        "update_goal": any(boolish(assertions.get("update_goal")) for assertions in assertion_maps.values()),
        "accepted_rows_added": sum(
            int(assertions.get("accepted_rows_added", "0"))
            for assertions in assertion_maps.values()
            if str(assertions.get("accepted_rows_added", "0")).isdigit()
        ),
        "merged_assertions": merged,
    }


def checklist_rows(status: dict) -> list[dict[str, str]]:
    blocked = "blocked"
    partial = "partial"
    passed = "pass"
    return [
        {
            "requirement": "Every regime reaches >=95 calibrated confidence",
            "status": blocked,
            "evidence": "085042/085131/085612 all keep valid_required_root_unlock=false and source_control_evidence_acquired=false",
            "gap": "No accepted R6/R5/R3 source-control root; R3 Crisis absent",
        },
        {
            "requirement": "Validate confidence across other markets / periods / timeframes",
            "status": blocked,
            "evidence": "source-control unlock false; explicit selected history false; canonical merge false",
            "gap": "No qualifying source-owned cross-axis packet after 085612",
        },
        {
            "requirement": "Use real AutoQuant -> filter / Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution tree chain",
            "status": blocked,
            "evidence": "selected_data_autoquant_promotion=false and downstream_promotion_rerun=false in latest assertion set",
            "gap": "Chain is intentionally not authorized until source/control and selected-history gates unlock",
        },
        {
            "requirement": "Remember IBKR, TradingViewRemix, yfinance, Kraken provider surfaces",
            "status": partial,
            "evidence": "Provider surfaces are historically observed in earlier Board A packets, but 085612 is only source/control triage",
            "gap": "Provider operation is not sufficient without source/control unlock and selected-history gate",
        },
        {
            "requirement": "Acquire source/control evidence",
            "status": blocked,
            "evidence": "085612 official_owner_export_package_hits=0 and verifier_native_positive_control_provenance_packages_acquired=0",
            "gap": "Need owner-approved/authenticated FINRA / venue-surveillance / CAT-like / CME-Cboe-CFE rows or explicit FLIP approval",
        },
        {
            "requirement": "Explicit user-selected historical path before non-promotional factor research",
            "status": blocked,
            "evidence": "latest board gates still include no_explicit_user_selected_history / user_selected_historical_data_missing",
            "gap": "No explicit HTF/MTF/LTF selection in current evidence",
        },
        {
            "requirement": "Do not disturb concurrent work",
            "status": passed,
            "evidence": "This audit is append-only and reads current hashes/tails; it does not rewrite cursor or older sections",
            "gap": "",
        },
        {
            "requirement": "Do not make trade claim or complete goal prematurely",
            "status": passed,
            "evidence": "trade_usable=false, strict_full_objective=false, update_goal=false",
            "gap": "",
        },
    ]


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    assertion_maps = {name: parse_assertions(path) for name, path in ASSERTION_FILES.items()}
    status = status_from_assertions(assertion_maps)
    roots = [root_status(name, root) for name, root in TARGET_ROOTS.items()]
    rows = checklist_rows(status)

    packet = {
        "run_id": RUN_ID,
        "generated_at_local": datetime.now(timezone(timedelta(hours=8))).isoformat(),
        "gate_result": GATE,
        "board_a_sha256_before_artifact": sha256_file(BOARD_A),
        "board_b_sha256_before_artifact": sha256_file(BOARD_B),
        "scope": {
            "mode": "read_only_current_objective_audit_after_085612",
            "no_root_mutation": True,
            "no_external_requests": True,
            "no_verifier": True,
            "no_selected_data_autoquant": True,
            "no_downstream_promotion": True,
            "update_goal": False,
        },
        "source_files": {name: rel(path) for name, path in SOURCE_FILES.items()},
        "assertion_files": {name: rel(path) for name, path in ASSERTION_FILES.items()},
        "target_roots": roots,
        "checklist": rows,
        "status": status,
        "decision": (
            "Objective is not complete after 085612. The latest route triage adds no owner-export, "
            "no matched-control source rows, no FLIP approval, no selected-history gate, and no downstream promotion authorization."
        ),
        "next": (
            "Continue source/control acquisition only: obtain owner-approved/authenticated FINRA, venue-surveillance, "
            "CAT-like, CME/Cboe/CFE order-lifecycle export rows with positives and matched normal controls, "
            "source-owned post-2026-01-30 R5 MainRegimeV2 rows, verifier-native Crisis-capable R3 native-subhour labels, "
            "or explicit same-exhibit FLIP-as-control approval before verifier, split calibration, canonical merge, "
            "selected-data AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, execution-tree promotion, trade claims, or update_goal."
        ),
    }

    json_path = ARTIFACT_DIR / "current_objective_audit_after_085612_v1.json"
    checklist_path = ARTIFACT_DIR / "prompt_to_artifact_checklist_after_085612_v1.csv"
    assertions_readback_path = ARTIFACT_DIR / "counted_assertion_readback_after_085612_v1.csv"
    target_roots_path = ARTIFACT_DIR / "target_roots_after_085612_v1.csv"
    report_path = ARTIFACT_DIR / "current_objective_audit_after_085612_v1.md"
    checks_path = CHECKS_DIR / "current_objective_audit_after_085612_v1_assertions.out"

    json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(checklist_path, rows, ["requirement", "status", "evidence", "gap"])
    readback_rows = [
        {"source": source, "assertion": key, "value": value}
        for source, assertions in assertion_maps.items()
        for key, value in sorted(assertions.items())
    ]
    write_csv(assertions_readback_path, readback_rows, ["source", "assertion", "value"])
    write_csv(
        target_roots_path,
        [
            {
                "name": row["name"],
                "path": row["path"],
                "exists": row["exists"],
                "file_count": row["file_count"],
            }
            for row in roots
        ],
        ["name", "path", "exists", "file_count"],
    )

    blocked_count = sum(1 for row in rows if row["status"] == "blocked")
    partial_count = sum(1 for row in rows if row["status"] == "partial")
    pass_count = sum(1 for row in rows if row["status"] == "pass")

    report_path.write_text(
        "\n".join(
            [
                "# Current Objective Audit After 085612 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{GATE}`",
                "",
                "## Scope",
                "",
                "Read-only prompt-to-artifact audit after terminal `085612` public source/control route triage. This packet does not mutate target roots, send external requests, run verifier, run selected-data AutoQuant, run filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Objective Restatement",
                "",
                "Every regime must reach 95%+ calibrated confidence, remain suitable across other markets, periods, and timeframes, and only then flow through real AutoQuant -> filter / Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution tree with provider evidence. Multi-agent board updates must stay append-only.",
                "",
                "## Readback",
                "",
                f"- Board A SHA-256 before artifact: `{packet['board_a_sha256_before_artifact']}`.",
                f"- Board B SHA-256 before artifact: `{packet['board_b_sha256_before_artifact']}`.",
                f"- Requirements: blocked `{blocked_count}`, partial `{partial_count}`, pass `{pass_count}`.",
                f"- Accepted rows added across latest assertion files: `{status['accepted_rows_added']}`.",
                f"- Valid required-root unlock: `{status['valid_required_root_unlock']}`.",
                f"- Source/control evidence acquired: `{status['source_control_evidence_acquired']}`.",
                f"- Canonical merge: `{status['canonical_merge']}`.",
                f"- Selected-data AutoQuant promotion: `{status['selected_data_autoquant_promotion']}`.",
                f"- Downstream promotion rerun: `{status['downstream_promotion_rerun']}`.",
                f"- Strict full objective: `{status['strict_full_objective']}`.",
                f"- Trade usable: `{status['trade_usable']}`.",
                f"- update_goal: `{status['update_goal']}`.",
                "",
                "## Decision",
                "",
                packet["decision"],
                "",
                "## Artifacts",
                "",
                f"- JSON: `{rel(json_path)}`",
                f"- Prompt-to-artifact checklist CSV: `{rel(checklist_path)}`",
                f"- Counted assertion readback CSV: `{rel(assertions_readback_path)}`",
                f"- Target roots CSV: `{rel(target_roots_path)}`",
                f"- Assertions: `{rel(checks_path)}`",
                "",
                "## Next",
                "",
                packet["next"],
                "",
            ]
        ),
        encoding="utf-8",
    )

    checks_path.write_text(
        "\n".join(
            [
                f"gate_result={GATE}",
                f"blocked_requirements={blocked_count}",
                f"partial_requirements={partial_count}",
                f"pass_requirements={pass_count}",
                f"accepted_rows_added={status['accepted_rows_added']}",
                f"valid_required_root_unlock={str(status['valid_required_root_unlock']).lower()}",
                f"source_control_evidence_acquired={str(status['source_control_evidence_acquired']).lower()}",
                f"canonical_merge={str(status['canonical_merge']).lower()}",
                f"selected_data_autoquant_promotion={str(status['selected_data_autoquant_promotion']).lower()}",
                f"downstream_promotion_rerun={str(status['downstream_promotion_rerun']).lower()}",
                f"strict_full_objective={str(status['strict_full_objective']).lower()}",
                f"trade_usable={str(status['trade_usable']).lower()}",
                f"promotion_allowed=false",
                f"update_goal={str(status['update_goal']).lower()}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
