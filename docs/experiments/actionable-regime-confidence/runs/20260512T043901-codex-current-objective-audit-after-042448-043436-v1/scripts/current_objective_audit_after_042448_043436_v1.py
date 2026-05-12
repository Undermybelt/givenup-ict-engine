#!/usr/bin/env python3
"""Build a current-objective audit after 042448 settled and 043436 was reconciled.

This is intentionally read-only with respect to source/control roots and runtime
state. It maps the active prompt to concrete artifacts and refuses completion
when any strict objective requirement is uncovered.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T043901-codex-current-objective-audit-after-042448-043436-v1"
GATE_RESULT = (
    "current_objective_audit_after_042448_043436_v1="
    "not_complete_histgb_no_acceptance_source_roots_absent_downstream_blocked"
)

BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = RUN_ROOT / "current-objective-audit-after-042448-043436-v1"
CHECK_DIR = RUN_ROOT / "checks"

HIST_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T042448-codex-source-label-histgb-confidence-screen-v1"
)
HIST_JSON = (
    HIST_ROOT
    / "source-label-histgb-confidence-screen-v1"
    / "source_label_histgb_confidence_screen_v1.json"
)
HIST_REPORT = (
    HIST_ROOT
    / "source-label-histgb-confidence-screen-v1"
    / "source_label_histgb_confidence_screen_v1.md"
)
HIST_GATES = (
    HIST_ROOT
    / "source-label-histgb-confidence-screen-v1"
    / "source_label_histgb_confidence_gates_v1.csv"
)
HIST_METRICS = (
    HIST_ROOT
    / "source-label-histgb-confidence-screen-v1"
    / "source_label_histgb_confidence_metrics_v1.csv"
)
HIST_FEATURES = (
    HIST_ROOT
    / "source-label-histgb-confidence-screen-v1"
    / "source_label_histgb_confidence_feature_importance_v1.csv"
)
HIST_ASSERTIONS = HIST_ROOT / "checks" / "source_label_histgb_confidence_screen_v1_assertions.out"
HIST_EXIT = HIST_ROOT / "command-output" / "source_label_histgb_confidence_screen.exit"
HIST_STDERR = HIST_ROOT / "command-output" / "source_label_histgb_confidence_screen.stderr.txt"

SOURCE_SCAN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T043436-codex-source-control-arrival-scan-after-043027-v1"
)
SOURCE_SCAN_JSON = (
    SOURCE_SCAN_ROOT
    / "source-control-arrival-scan-after-043027-v1"
    / "source_control_arrival_scan_after_043027_v1.json"
)
SOURCE_SCAN_ASSERTIONS = (
    SOURCE_SCAN_ROOT / "checks" / "source_control_arrival_scan_after_043027_v1_assertions.out"
)

AUTOQUANT_ASSERTIONS = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T042900-codex-autoquant-threaded-resolver-run-settlement-after-042222-v1/"
    "checks/autoquant_threaded_resolver_run_settlement_after_042222_v1_assertions.out"
)
PREV_OBJECTIVE_ASSERTIONS = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T043027-codex-current-objective-audit-after-042222-threaded-resolver-v1/"
    "checks/current_objective_audit_after_042222_threaded_resolver_v1_assertions.out"
)
DOWNSTREAM_ASSERTIONS = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T042857-codex-current-objective-audit-after-042603-v1/"
    "checks/current_objective_audit_after_042603_v1_assertions.out"
)

TARGET_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def parse_assertions(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in read_text(path).splitlines():
        line = line.strip()
        if not line.startswith("PASS ") or "=" not in line:
            continue
        key, value = line[5:].split("=", 1)
        values[key] = value
    return values


def file_count(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return 1
    return sum(1 for item in path.rglob("*") if item.is_file())


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    generated_at_utc = datetime.now(timezone.utc).isoformat()
    board_sha = sha256(BOARD)
    hist = load_json(HIST_JSON)
    source_scan = load_json(SOURCE_SCAN_JSON)
    hist_gates = read_csv(HIST_GATES)
    hist_metrics = read_csv(HIST_METRICS)
    autoquant_assertions = parse_assertions(AUTOQUANT_ASSERTIONS)
    prev_objective_assertions = parse_assertions(PREV_OBJECTIVE_ASSERTIONS)
    downstream_assertions = parse_assertions(DOWNSTREAM_ASSERTIONS)

    accepted_histgb_labels = hist.get("accepted_histgb_confidence_95_labels", [])
    gate_status_by_label = {
        row.get("label", ""): row.get("accepted_histgb_confidence_95", "")
        for row in hist_gates
    }
    heldout_market_metrics = [
        row for row in hist_metrics if row.get("split_role") == "heldout_market"
    ]
    heldout_market_zero_support_labels = [
        row.get("label", "")
        for row in heldout_market_metrics
        if row.get("high_confidence_support") in {"0", "0.0"}
    ]

    root_rows = []
    for root in TARGET_ROOTS:
        root_rows.append(
            {
                "path": str(root),
                "present": root.exists(),
                "file_count": file_count(root),
            }
        )

    evidence_rows = [
        {
            "artifact": "board",
            "path": str(BOARD),
            "present": BOARD.exists(),
            "status": "sha256=" + board_sha,
        },
        {
            "artifact": "042448_histgb_report",
            "path": str(HIST_REPORT),
            "present": HIST_REPORT.exists(),
            "status": hist.get("gate_result", ""),
        },
        {
            "artifact": "042448_histgb_json",
            "path": str(HIST_JSON),
            "present": HIST_JSON.exists(),
            "status": "accepted_labels=" + json.dumps(accepted_histgb_labels),
        },
        {
            "artifact": "042448_histgb_gates",
            "path": str(HIST_GATES),
            "present": HIST_GATES.exists(),
            "status": ";".join(f"{k}={v}" for k, v in sorted(gate_status_by_label.items())),
        },
        {
            "artifact": "042448_histgb_metrics",
            "path": str(HIST_METRICS),
            "present": HIST_METRICS.exists(),
            "status": "heldout_market_zero_support_labels="
            + ";".join(heldout_market_zero_support_labels),
        },
        {
            "artifact": "042448_histgb_feature_importance",
            "path": str(HIST_FEATURES),
            "present": HIST_FEATURES.exists(),
            "status": "diagnostic_only",
        },
        {
            "artifact": "042448_histgb_assertions",
            "path": str(HIST_ASSERTIONS),
            "present": HIST_ASSERTIONS.exists(),
            "status": "terminal_exit=" + read_text(HIST_EXIT).strip(),
        },
        {
            "artifact": "043436_source_control_scan",
            "path": str(SOURCE_SCAN_JSON),
            "present": SOURCE_SCAN_JSON.exists(),
            "status": source_scan.get("gate_result", ""),
        },
        {
            "artifact": "043436_source_control_assertions",
            "path": str(SOURCE_SCAN_ASSERTIONS),
            "present": SOURCE_SCAN_ASSERTIONS.exists(),
            "status": "new_source_unlock="
            + str(source_scan.get("decision", {}).get("new_source_unlock")).lower(),
        },
        {
            "artifact": "042900_autoquant_threaded_runtime",
            "path": str(AUTOQUANT_ASSERTIONS),
            "present": AUTOQUANT_ASSERTIONS.exists(),
            "status": "successful_backtests="
            + autoquant_assertions.get("autoquant_successful_backtests", ""),
        },
        {
            "artifact": "043027_previous_objective_audit",
            "path": str(PREV_OBJECTIVE_ASSERTIONS),
            "present": PREV_OBJECTIVE_ASSERTIONS.exists(),
            "status": prev_objective_assertions.get("gate_result", ""),
        },
        {
            "artifact": "042857_downstream_readback",
            "path": str(DOWNSTREAM_ASSERTIONS),
            "present": DOWNSTREAM_ASSERTIONS.exists(),
            "status": downstream_assertions.get("gate_result", ""),
        },
    ]

    source_decision = source_scan.get("decision", {})
    promotion_status = {
        "accepted_rows_added": 0,
        "source_control_evidence_acquired": False,
        "new_confidence_gate": bool(hist.get("promotion_status", {}).get("new_confidence_gate")),
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    checklist_rows = [
        {
            "requirement": "Use the named Board A plan as the active coordination surface without disrupting concurrent work.",
            "status": "pass",
            "evidence": f"{BOARD}; board_sha256={board_sha}; current audit is read-only except this run artifact.",
            "missing_or_next": "Append only if unregistered; do not rewrite Current Cursor.",
        },
        {
            "requirement": "Every active regime reaches calibrated confidence >=95%.",
            "status": "fail",
            "evidence": f"042448 accepted_histgb_confidence_95_labels={accepted_histgb_labels}; gates={gate_status_by_label}",
            "missing_or_next": "Need labels/regimes passing all required split gates with support >=50 and Wilson95 >=0.95.",
        },
        {
            "requirement": "Validate confidence on other markets.",
            "status": "fail",
            "evidence": "heldout_market_zero_support_labels="
            + ";".join(heldout_market_zero_support_labels),
            "missing_or_next": "Heldout-market high-confidence support/precision must pass, not just pooled rows.",
        },
        {
            "requirement": "Validate confidence on other cycles/timeframes.",
            "status": "fail",
            "evidence": "native_subhour_root_present="
            + str(TARGET_ROOTS[1].exists()).lower()
            + "; all 042448 labels failed at least one required split.",
            "missing_or_next": "Need native sub-hour/source-owned cross-timeframe evidence or accepted strict split gates.",
        },
        {
            "requirement": "Acquire source/control unlocks before canonical merge.",
            "status": "fail",
            "evidence": "required_roots_absent="
            + ";".join(str(row["path"]) for row in root_rows if not row["present"])
            + "; explicit_approval="
            + str(source_decision.get("explicit_approval")).lower(),
            "missing_or_next": "Need explicit approval, verifier-native R6 owner/export rows plus controls, R5 recency extension, R3 native sub-hour rows, or source-owned MainRegimeV2 exports.",
        },
        {
            "requirement": "Operate provider and AutoQuant surfaces with real artifacts.",
            "status": "partial",
            "evidence": "042900 autoquant_successful_backtests="
            + autoquant_assertions.get("autoquant_successful_backtests", "")
            + "; autoquant_failed_backtests="
            + autoquant_assertions.get("autoquant_failed_backtests", ""),
            "missing_or_next": "Runtime success is non-promoting until source/control and confidence gates unlock.",
        },
        {
            "requirement": "Run filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree promotion chain after unlock.",
            "status": "fail",
            "evidence": "canonical_merge=false; downstream_promotion_rerun=false; 042857 remains readback/non-promoting.",
            "missing_or_next": "Rerun full chain only after source/control unlock and accepted confidence evidence.",
        },
        {
            "requirement": "Do not claim trade usability or complete the active goal from proxy signals.",
            "status": "pass",
            "evidence": "trade_usable=false; strict_full_objective=false; update_goal=false.",
            "missing_or_next": "Keep goal active until every checklist row passes with direct evidence.",
        },
    ]

    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": generated_at_utc,
        "gate_result": GATE_RESULT,
        "board_sha256_before_audit_artifact": board_sha,
        "objective_restated": True,
        "prompt_to_artifact_checklist_present": True,
        "evidence": {
            "histgb_042448": {
                "gate_result": hist.get("gate_result"),
                "row_count": hist.get("row_count"),
                "verifier_status": hist.get("verifier", {}).get("status"),
                "verifier_return_code": hist.get("verifier", {}).get("return_code"),
                "command_exit": read_text(HIST_EXIT).strip(),
                "stderr_bytes": HIST_STDERR.stat().st_size if HIST_STDERR.exists() else None,
                "accepted_histgb_confidence_95_labels": accepted_histgb_labels,
                "gate_status_by_label": gate_status_by_label,
                "heldout_market_zero_support_labels": heldout_market_zero_support_labels,
            },
            "source_control_043436": {
                "gate_result": source_scan.get("gate_result"),
                "decision": source_decision,
            },
            "autoquant_042900": autoquant_assertions,
            "previous_objective_043027": prev_objective_assertions,
            "downstream_readback_042857": downstream_assertions,
            "target_roots": root_rows,
        },
        "promotion_status": promotion_status,
        "next": (
            "Continue only after explicit approval, verifier-native R6 owner/export rows plus "
            "source-owned broad normal controls, source-owned R5 recency-extension rows, "
            "native sub-hour source-label rows, or genuinely source-owned cross-timeframe "
            "MainRegimeV2 exports unlock a target root; then rerun the full chain in order."
        ),
    }

    json_path = OUT_DIR / "current_objective_audit_after_042448_043436_v1.json"
    md_path = OUT_DIR / "current_objective_audit_after_042448_043436_v1.md"
    checklist_path = OUT_DIR / "prompt_to_artifact_checklist_after_042448_043436_v1.csv"
    evidence_path = OUT_DIR / "evidence_presence_after_042448_043436_v1.csv"
    root_status_path = OUT_DIR / "root_status_after_042448_043436_v1.csv"
    assertions_path = CHECK_DIR / "current_objective_audit_after_042448_043436_v1_assertions.out"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        checklist_path,
        checklist_rows,
        ["requirement", "status", "evidence", "missing_or_next"],
    )
    write_csv(evidence_path, evidence_rows, ["artifact", "path", "present", "status"])
    write_csv(root_status_path, root_rows, ["path", "present", "file_count"])

    md_lines = [
        "# Current Objective Audit After 042448 and 043436 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE_RESULT}`",
        "",
        f"Board sha256 before audit artifact: `{board_sha}`",
        "",
        "## Objective Restatement",
        "",
        (
            "Board A is complete only if every active regime has calibrated >=95% "
            "confidence, remains suitable across other markets and cycles/timeframes, "
            "has per-regime qualifying evidence, and then passes the provider/AutoQuant "
            "-> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree chain "
            "without proxy promotion."
        ),
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence | Missing / Next |",
        "|---|---|---|---|",
    ]
    for row in checklist_rows:
        md_lines.append(
            "| {requirement} | `{status}` | {evidence} | {missing_or_next} |".format(
                **{k: str(v).replace("|", "\\|") for k, v in row.items()}
            )
        )
    md_lines.extend(
        [
            "",
            "## Key Evidence",
            "",
            f"- `042448` HistGB gate: `{hist.get('gate_result')}`.",
            f"- `042448` accepted HistGB confidence labels: `{accepted_histgb_labels}`.",
            f"- `042448` label gates: `{gate_status_by_label}`.",
            f"- Heldout-market zero-support labels: `{heldout_market_zero_support_labels}`.",
            f"- `043436` source/control gate: `{source_scan.get('gate_result')}`.",
            f"- Target roots present: `{root_rows}`.",
            (
                "- `042900` AutoQuant threaded runtime succeeded with "
                f"`{autoquant_assertions.get('autoquant_successful_backtests', '')}` successful "
                f"backtests and `{autoquant_assertions.get('autoquant_failed_backtests', '')}` "
                "failed backtests, but remains runtime-only/non-promoting."
            ),
            "",
            "## Decision",
            "",
            "- Accepted rows added: `0`.",
            "- Source/control evidence acquired: `false`.",
            "- New confidence gate: `false`.",
            "- Canonical merge: `false`.",
            "- Downstream promotion rerun: `false`.",
            "- Strict full objective: `false`.",
            "- Trade usable: `false`.",
            "- `update_goal=false`.",
            "",
            "## Next",
            "",
            summary["next"],
            "",
        ]
    )
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    assertions = {
        "gate_result": GATE_RESULT,
        "objective_restated": "true",
        "prompt_to_artifact_checklist_present": str(checklist_path.exists()).lower(),
        "histgb_exit": read_text(HIST_EXIT).strip(),
        "histgb_verifier_status": str(hist.get("verifier", {}).get("status")),
        "histgb_row_count": str(hist.get("row_count")),
        "histgb_accepted_labels": "none" if not accepted_histgb_labels else ";".join(accepted_histgb_labels),
        "histgb_all_label_gates_failed": str(
            all(str(value).lower() == "false" for value in gate_status_by_label.values())
        ).lower(),
        "heldout_market_zero_support_label_count": str(len(heldout_market_zero_support_labels)),
        "r6_owner_export_root_present": str(TARGET_ROOTS[0].exists()).lower(),
        "r3_native_subhour_root_present": str(TARGET_ROOTS[1].exists()).lower(),
        "r5_recency_extension_root_present": str(TARGET_ROOTS[2].exists()).lower(),
        "autoquant_successful_backtests": autoquant_assertions.get("autoquant_successful_backtests", ""),
        "autoquant_failed_backtests": autoquant_assertions.get("autoquant_failed_backtests", ""),
        "source_control_evidence_acquired": str(promotion_status["source_control_evidence_acquired"]).lower(),
        "new_confidence_gate": str(promotion_status["new_confidence_gate"]).lower(),
        "canonical_merge": str(promotion_status["canonical_merge"]).lower(),
        "downstream_promotion_rerun": str(promotion_status["downstream_promotion_rerun"]).lower(),
        "strict_full_objective": str(promotion_status["strict_full_objective"]).lower(),
        "trade_usable": str(promotion_status["trade_usable"]).lower(),
        "update_goal": str(promotion_status["update_goal"]).lower(),
    }

    expected = {
        "histgb_exit": "0",
        "histgb_accepted_labels": "none",
        "histgb_all_label_gates_failed": "true",
        "r6_owner_export_root_present": "false",
        "r3_native_subhour_root_present": "false",
        "r5_recency_extension_root_present": "false",
        "source_control_evidence_acquired": "false",
        "new_confidence_gate": "false",
        "canonical_merge": "false",
        "downstream_promotion_rerun": "false",
        "strict_full_objective": "false",
        "trade_usable": "false",
        "update_goal": "false",
    }
    for key, expected_value in expected.items():
        actual = assertions.get(key)
        if actual != expected_value:
            raise AssertionError(f"{key} expected {expected_value}, got {actual}")

    assertions_path.write_text(
        "".join(f"PASS {key}={value}\n" for key, value in assertions.items()),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
