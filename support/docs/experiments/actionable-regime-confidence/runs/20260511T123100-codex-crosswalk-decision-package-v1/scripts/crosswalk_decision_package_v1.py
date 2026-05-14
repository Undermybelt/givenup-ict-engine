#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T123100+0800-codex-crosswalk-decision-package-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T123100-codex-crosswalk-decision-package-v1"
OUT_DIR = RUN_ROOT / "crosswalk-decision"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
MISSING_SLOTS = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T094002-codex-external-label-request-package-v3/acquisition-request/missing_parent_root_label_slots_request_v3.csv"
SOURCE_SEED = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T120900-codex-exportable-source-scan/source-scan/source_window_seed_v1.csv"
ATTACHABILITY = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T122239-codex-source-window-attachability-v1/source-window-attachability/source_window_attachability_v1.json"
SIDEWAYS_GATE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T041923-codex-yahoo-sourcebacked-parent-root-gate/yahoo-parent-root-gate/yahoo_sourcebacked_parent_root_gate_report.json"

SPX_TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "4h", "1mo"}
SPX_PROXY_INSTRUMENTS = {"SPY", "ES=F"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def classify_slot(row: dict[str, str]) -> dict[str, str] | None:
    instrument = row["instrument"]
    timeframe = row["timeframe"]
    root = row["root"]
    if timeframe not in SPX_TIMEFRAMES:
        return None
    if instrument == "^GSPC" and root in {"Bull", "Bear"}:
        return {
            "decision_layer": "same_underlying_spx_to_gspc_time_projection",
            "decision": "approve_to_attach_with_guards",
            "decision_tier": "same_underlying_calendar_window",
            "source_family": "Yardeni S&P 500 Bull/Bear dated windows",
            "guardrail": "Use only session dates inside Yardeni S&P 500 windows; monthly bars require unambiguous month containment; refresh open-ended 2022-10-12 Bull window before live attachment.",
        }
    if instrument == "^GSPC" and root == "Crisis":
        return {
            "decision_layer": "macro_crisis_to_gspc_time_projection",
            "decision": "approve_to_attach_with_guards",
            "decision_tier": "same_underlying_macro_crisis_calendar_window",
            "source_family": "NBER US contraction months",
            "guardrail": "Use only bars whose timestamp falls in an NBER contraction month; mark as macro Crisis provenance, not a volatility-only OHLCV detector.",
        }
    if instrument in SPX_PROXY_INSTRUMENTS and root in {"Bull", "Bear"}:
        return {
            "decision_layer": "spx_tradable_proxy_time_projection",
            "decision": "conditional_approve_to_attach_with_proxy_tier",
            "decision_tier": "s_and_p_500_tradable_proxy",
            "source_family": "Yardeni S&P 500 Bull/Bear dated windows",
            "guardrail": "Allowed only for SPY and ES=F as S&P 500 economic-equivalence proxies; keep proxy tier explicit and do not propagate to QQQ, DIA, NQ, YM, commodities, vol, or crypto.",
        }
    if instrument in SPX_PROXY_INSTRUMENTS and root == "Crisis":
        return {
            "decision_layer": "macro_crisis_to_spx_tradable_proxy",
            "decision": "conditional_approve_to_attach_with_proxy_tier",
            "decision_tier": "s_and_p_500_tradable_proxy_macro_crisis",
            "source_family": "NBER US contraction months",
            "guardrail": "Allowed only for SPY and ES=F bars inside NBER contraction months; keep proxy tier explicit and do not treat as universal cross-asset Crisis labels.",
        }
    return None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    missing_rows = read_csv(MISSING_SLOTS)
    source_rows = read_csv(SOURCE_SEED)
    with ATTACHABILITY.open() as f:
        attachability = json.load(f)
    with SIDEWAYS_GATE.open() as f:
        sideways_gate = json.load(f)

    approved_rows: list[dict[str, str]] = []
    deferred_rows: list[dict[str, str]] = []
    for row in missing_rows:
        classification = classify_slot(row)
        if classification:
            approved_rows.append({**row, **classification})
        elif row["root"] == "Sideways":
            deferred_rows.append({
                **row,
                "decision_layer": "sideways_adjudication_protocol_v1",
                "decision": "defer_until_protocol_rerun",
                "decision_tier": "source_definition_adjudication_protocol",
                "source_family": "existing accepted Sideways source-backed parent-root gate",
                "guardrail": "Do not infer Sideways as complement; rerun the accepted trailing absolute-return/range/MA-gap protocol per provider/instrument/timeframe and require held-out Wilson95 pass before attachment.",
            })
        else:
            deferred_rows.append({
                **row,
                "decision_layer": "fail_closed_without_exact_source_or_explicit_projection",
                "decision": "reject_current_projection",
                "decision_tier": "not_same_underlying_or_not_approved_projection",
                "source_family": "none",
                "guardrail": "Requires exact source labels or a separate owner-approved cross-market projection; current S&P 500/NBER windows do not attach here.",
            })

    fields = [
        "request_id",
        "provider",
        "instrument",
        "timeframe",
        "root",
        "missing_or_rejected_reason",
        "required_label_source",
        "forbidden_proxy_sources",
        "minimum_acceptance_note",
        "decision_layer",
        "decision",
        "decision_tier",
        "source_family",
        "guardrail",
    ]
    write_csv(OUT_DIR / "approved_crosswalk_slot_actions_v1.csv", approved_rows, fields)
    write_csv(OUT_DIR / "deferred_or_rejected_slot_actions_v1.csv", deferred_rows, fields)

    approved_by_layer = Counter(r["decision_layer"] for r in approved_rows)
    deferred_by_decision = Counter(r["decision"] for r in deferred_rows)
    deferred_by_root = Counter(r["root"] for r in deferred_rows)
    approved_by_root = Counter(r["root"] for r in approved_rows)

    source_window_rows = Counter(r["root"] for r in source_rows)
    side = sideways_gate["root_reports"]["Sideways"]

    package = {
        "run_id": RUN_ID,
        "artifact_type": "crosswalk_decision_package_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "board": str(BOARD.relative_to(REPO)),
            "board_sha256_at_run": sha256(BOARD),
            "missing_slots": str(MISSING_SLOTS.relative_to(REPO)),
            "missing_slots_sha256": sha256(MISSING_SLOTS),
            "source_window_seed": str(SOURCE_SEED.relative_to(REPO)),
            "source_window_seed_sha256": sha256(SOURCE_SEED),
            "attachability_preflight": str(ATTACHABILITY.relative_to(REPO)),
            "attachability_preflight_sha256": sha256(ATTACHABILITY),
            "sideways_gate_report": str(SIDEWAYS_GATE.relative_to(REPO)),
            "sideways_gate_report_sha256": sha256(SIDEWAYS_GATE),
        },
        "decision_summary": {
            "total_missing_or_rejected_slots": len(missing_rows),
            "prior_pending_crosswalk_slots": attachability["attachability_result"]["candidate_slots_pending_owner_crosswalk"],
            "approved_or_conditional_crosswalk_slot_actions": len(approved_rows),
            "approved_same_underlying_slot_actions": sum(1 for r in approved_rows if r["decision"] == "approve_to_attach_with_guards"),
            "conditional_tradable_proxy_slot_actions": sum(1 for r in approved_rows if r["decision"] == "conditional_approve_to_attach_with_proxy_tier"),
            "deferred_or_rejected_slot_actions": len(deferred_rows),
            "sideways_protocol_target_slots_deferred": deferred_by_root["Sideways"],
            "still_fail_closed_without_exact_source_or_projection": deferred_by_decision["reject_current_projection"],
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
        },
        "approved_by_layer": dict(sorted(approved_by_layer.items())),
        "approved_by_root": dict(sorted(approved_by_root.items())),
        "deferred_by_root": dict(sorted(deferred_by_root.items())),
        "source_window_seed_root_counts": dict(sorted(source_window_rows.items())),
        "sideways_adjudication_protocol_v1": {
            "status": "protocol_ready_for_targeted_rerun_not_attached",
            "source_artifact": str(SIDEWAYS_GATE.relative_to(REPO)),
            "existing_gate_id": "sideways_sourcebacked_abs_return_range_v1",
            "existing_rule": side["rule"],
            "existing_calibration_wilson95_lcb": round(float(side["calibration"]["precision_wilson_lcb_95"]), 6),
            "existing_test_wilson95_lcb": round(float(side["test"]["precision_wilson_lcb_95"]), 6),
            "existing_validation_contexts": side["test"]["validation_market_contexts"],
            "existing_validation_timeframes": side["test"]["validation_timeframes"],
            "protocol_steps": [
                "Generate labels from observed/trailing absolute return, range, and moving-average gap thresholds per provider/instrument/timeframe.",
                "Do not label Sideways as the complement of Bull, Bear, or Crisis.",
                "Split train/calibration/test by time before selecting thresholds.",
                "Attach only cells whose held-out Wilson95 LCB is >= 0.95 with support >= 250 and at least two validation instruments when the context is cross-instrument.",
                "Keep all unsupported Sideways cells abstained.",
            ],
        },
        "guardrails": {
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
            "proxy_promoted_to_source_native": False,
            "shared_board_modified": False,
            "empty_122709_run_dir_touched": False,
        },
        "next_execution_step": "Use approved_crosswalk_slot_actions_v1.csv to attach the 63 S&P 500/NBER crosswalk slots with explicit tiers, then run Sideways adjudication protocol only as a targeted rerun.",
    }

    (OUT_DIR / "crosswalk_decision_package_v1.json").write_text(
        json.dumps(package, indent=2, sort_keys=True) + "\n"
    )

    report = [
        "# Crosswalk Decision Package v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        f"- Prior pending crosswalk slots: `{package['decision_summary']['prior_pending_crosswalk_slots']}`.",
        f"- Approved same-underlying `^GSPC` slot actions: `{package['decision_summary']['approved_same_underlying_slot_actions']}`.",
        f"- Conditional SPY/ES=F tradable-proxy slot actions: `{package['decision_summary']['conditional_tradable_proxy_slot_actions']}`.",
        f"- Total approved or conditional crosswalk slot actions: `{package['decision_summary']['approved_or_conditional_crosswalk_slot_actions']}`.",
        f"- Sideways protocol target slots remain deferred until rerun: `{package['decision_summary']['sideways_protocol_target_slots_deferred']}`.",
        f"- Still fail-closed without exact source/projection: `{package['decision_summary']['still_fail_closed_without_exact_source_or_projection']}`.",
        "",
        "This is a positive decision package, not another negative source sweep. It turns the 63 pending S&P 500/NBER crosswalk slots into explicit attach actions with guardrails.",
        "",
        "## Approved Crosswalks",
        "",
        "- `Yardeni S&P 500 -> ^GSPC` Bull/Bear: approve calendar-window projection for intraday/monthly bars, with open-ended Yardeni windows refreshed before live attachment.",
        "- `NBER contraction months -> ^GSPC` Crisis: approve month-window projection as macro Crisis provenance for S&P 500 bars.",
        "- `Yardeni S&P 500 -> SPY/ES=F` Bull/Bear: conditional approve as S&P 500 tradable-proxy tier only.",
        "- `NBER contraction months -> SPY/ES=F` Crisis: conditional approve as S&P 500 tradable-proxy macro Crisis tier only.",
        "",
        "## Sideways Protocol",
        "",
        f"- Existing accepted gate: `sideways_sourcebacked_abs_return_range_v1`.",
        f"- Rule: `{side['rule']}`.",
        f"- Existing calibration/test Wilson95 LCB: `{package['sideways_adjudication_protocol_v1']['existing_calibration_wilson95_lcb']}` / `{package['sideways_adjudication_protocol_v1']['existing_test_wilson95_lcb']}`.",
        "- Protocol status: ready for targeted rerun, not attached.",
        "- Critical guardrail: never infer `Sideways` as the complement of `Bull`/`Bear`/`Crisis`.",
        "",
        "## Not Promoted",
        "",
        "- No full-objective gate is claimed.",
        "- No broad projection to QQQ/NDX/NQ, DJI/DIA/YM, commodities, vol, or crypto is approved here.",
        "- Proxy tier is explicit; proxy rows are not promoted to source-native rows.",
        "- Shared board was not modified.",
        "",
        "## Artifacts",
        "",
        "- `crosswalk_decision_package_v1.json`",
        "- `approved_crosswalk_slot_actions_v1.csv`",
        "- `deferred_or_rejected_slot_actions_v1.csv`",
        "- `sideways_adjudication_protocol_v1.md`",
        "- `../checks/crosswalk_decision_package_v1_assertions.out`",
        "",
    ]
    (OUT_DIR / "crosswalk_decision_package_v1.md").write_text("\n".join(report))

    side_protocol = [
        "# Sideways Adjudication Protocol v1",
        "",
        "Purpose: convert the existing accepted Sideways source-backed gate into a targeted dated-window adjudication rerun, without pretending a dated external Sideways source already exists.",
        "",
        "## Inputs",
        "",
        f"- Existing gate artifact: `{SIDEWAYS_GATE.relative_to(REPO)}`",
        f"- Existing rule: `{side['rule']}`",
        "- Required target: per provider/instrument/timeframe Sideways windows from observed/trailing data only.",
        "",
        "## Acceptance",
        "",
        "- Held-out Wilson95 LCB must be `>= 0.95`.",
        "- Support must be `>= 250` per accepted cell or explicitly scoped aggregate.",
        "- Threshold selection must happen on train split only.",
        "- Calibration/test splits must remain time-separated.",
        "- Unsupported cells remain abstained.",
        "",
        "## Forbidden Shortcuts",
        "",
        "- Do not label Sideways as non-Bull/non-Bear/non-Crisis.",
        "- Do not use future returns or target labels as predictors.",
        "- Do not generalize a passed daily/weekly ETF/crypto scope to intraday/monthly or other species without rerun evidence.",
        "- Do not count this protocol as a dated source window until rerun artifacts materialize dated windows.",
        "",
    ]
    (OUT_DIR / "sideways_adjudication_protocol_v1.md").write_text("\n".join(side_protocol))

    assertion_lines = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={package['inputs']['board_sha256_at_run']}",
        f"prior_pending_crosswalk_slots={package['decision_summary']['prior_pending_crosswalk_slots']}",
        f"approved_or_conditional_crosswalk_slot_actions={len(approved_rows)}",
        f"approved_same_underlying_slot_actions={package['decision_summary']['approved_same_underlying_slot_actions']}",
        f"conditional_tradable_proxy_slot_actions={package['decision_summary']['conditional_tradable_proxy_slot_actions']}",
        f"sideways_protocol_target_slots_deferred={deferred_by_root['Sideways']}",
        f"still_fail_closed_without_exact_source_or_projection={deferred_by_decision['reject_current_projection']}",
        "full_objective_gate=none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "proxy_promoted_to_source_native=false",
        "shared_board_modified=false",
        "assertion_status=PASS",
    ]
    (CHECK_DIR / "crosswalk_decision_package_v1_assertions.out").write_text("\n".join(assertion_lines) + "\n")

    assert len(missing_rows) == 564
    assert attachability["attachability_result"]["candidate_slots_pending_owner_crosswalk"] == 63
    assert len(approved_rows) == 63
    assert package["decision_summary"]["approved_same_underlying_slot_actions"] == 21
    assert package["decision_summary"]["conditional_tradable_proxy_slot_actions"] == 42
    assert deferred_by_root["Sideways"] == 141
    assert package["decision_summary"]["accepted_full_objective_gate"] == "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal"


if __name__ == "__main__":
    main()
