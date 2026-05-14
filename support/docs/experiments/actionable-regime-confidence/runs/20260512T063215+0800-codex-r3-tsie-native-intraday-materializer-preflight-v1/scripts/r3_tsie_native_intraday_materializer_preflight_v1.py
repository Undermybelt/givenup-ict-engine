#!/usr/bin/env python3
"""Preflight guardrail for the in-progress TSIE native-intraday materializer."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T063215+0800-codex-r3-tsie-native-intraday-materializer-preflight-v1"
SCRIPT = Path(__file__).resolve()
RUN_ROOT = SCRIPT.parents[1]
REPO = SCRIPT.parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
OUT = RUN_ROOT / "r3-tsie-native-intraday-materializer-preflight-v1"
CHECKS = RUN_ROOT / "checks"

TARGET_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
R6_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
R5_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
SOURCE_EQUIV_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")

MATERIALIZER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T062902+0800-codex-r3-hf-tsie-native-intraday-intake-v1/scripts/"
    "r3_hf_tsie_native_intraday_intake_v1.py"
)

PRIOR_BLOCKERS = [
    {
        "source": "062201",
        "gate": "r3_hf_tsie_provenance_decision_v1=rejected_rule_based_proxy_labels_no_intake_no_promotion",
        "reason": "TSIE labels are README-described rule-based price/volatility/RSI/volume signal labels.",
    },
    {
        "source": "062253",
        "gate": "tsie_prior_evidence_reconciliation_v1=duplicate_candidate_prior_full_data_and_mapping_failures_no_intake",
        "reason": "Prior full-data gates accepted zero roots and direct Crisis evidence is absent.",
    },
    {
        "source": "062409",
        "gate": "r3_r5_source_selection_readback_after_061855_v1=no_candidate_selected_no_required_root_no_promotion",
        "reason": "TSIE and five other candidates selected zero target-root unlocks.",
    },
    {
        "source": "062657",
        "gate": "tsie_negative_packet_reconciliation_after_062409_v1=tsie_packets_counted_or_scoped_no_required_root_no_promotion",
        "reason": "TSIE remains non-promoting for policy and validation reasons, not transport.",
    },
]


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_rows(path: Path) -> int | None:
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return max(sum(1 for _ in csv.reader(handle)) - 1, 0)


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    script_text = MATERIALIZER.read_text(encoding="utf-8", errors="replace") if MATERIALIZER.exists() else ""
    findings = [
        {
            "finding": "materializer_script_present",
            "value": MATERIALIZER.exists(),
            "evidence": str(MATERIALIZER),
        },
        {
            "finding": "would_write_target_root",
            "value": "os.rename(TMP_TARGET_ROOT, TARGET_ROOT)" in script_text,
            "evidence": "script contains final TMP_TARGET_ROOT to TARGET_ROOT rename",
        },
        {
            "finding": "declares_target_root_mutated_true",
            "value": '"target_root_mutated": True' in script_text,
            "evidence": "script result declares target_root_mutated true",
        },
        {
            "finding": "crisis_missing_or_no_direct_mapping",
            "value": "Crisis" in script_text and "crisis_no_direct_mapping" in script_text,
            "evidence": "script equivalence policy says crisis_no_direct_mapping",
        },
        {
            "finding": "source_confidence_absent",
            "value": '"source_confidence_available": False' in script_text,
            "evidence": "script provenance marks source_confidence_available false",
        },
        {
            "finding": "downstream_blocked_in_script",
            "value": '"downstream_rerun_allowed_now": False' in script_text,
            "evidence": "script itself does not allow downstream rerun",
        },
    ]
    risky_mutation = any(row["finding"] == "would_write_target_root" and row["value"] for row in findings)
    policy_blockers_present = all(
        any(row["finding"] == key and row["value"] for row in findings)
        for key in [
            "crisis_missing_or_no_direct_mapping",
            "source_confidence_absent",
            "downstream_blocked_in_script",
        ]
    )
    required_roots = {
        str(R6_ROOT): R6_ROOT.exists(),
        str(TARGET_ROOT): TARGET_ROOT.exists(),
        str(R5_ROOT): R5_ROOT.exists(),
        str(SOURCE_EQUIV_ROOT): SOURCE_EQUIV_ROOT.exists(),
    }
    gate_result = (
        "r3_tsie_native_intraday_materializer_preflight_v1="
        "do_not_run_target_root_materializer_proxy_blocked"
    )
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_before_artifact": sha256(BOARD),
        "gate_result": gate_result,
        "materializer": str(MATERIALIZER),
        "materializer_sha256": sha256(MATERIALIZER),
        "findings": findings,
        "prior_blockers": PRIOR_BLOCKERS,
        "required_roots": required_roots,
        "source_label_equivalence_rows": csv_rows(SOURCE_EQUIV_ROOT / "source_label_equivalence_rows.csv"),
        "risky_target_root_mutation": risky_mutation,
        "policy_blockers_present": policy_blockers_present,
        "recommended_action": "do_not_run_or_count_062902_as_unlock_without_explicit_source_control_policy_change",
        "accepted_rows_added": 0,
        "source_control_evidence_acquired": False,
        "target_root_mutated": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    json_path = OUT / "r3_tsie_native_intraday_materializer_preflight_v1.json"
    report_path = OUT / "r3_tsie_native_intraday_materializer_preflight_v1.md"
    findings_csv = OUT / "r3_tsie_native_intraday_materializer_preflight_findings_v1.csv"
    blockers_csv = OUT / "r3_tsie_native_intraday_prior_blockers_v1.csv"
    assertions_path = CHECKS / "r3_tsie_native_intraday_materializer_preflight_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(findings_csv, findings, ["finding", "value", "evidence"])
    write_csv(blockers_csv, PRIOR_BLOCKERS, ["source", "gate", "reason"])
    report_path.write_text(
        "\n".join(
            [
                "# R3 TSIE Native-Intraday Materializer Preflight v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{gate_result}`",
                "",
                "## Scope",
                "",
                "Read-only preflight for the in-progress `062902` materializer script. This artifact does not execute that script, does not write `/tmp/ict-engine-native-subhour-source-label-intake`, does not approve TSIE, does not run canonical merge, does not rerun downstream promotion, and does not call `update_goal`.",
                "",
                "## Decision",
                "",
                "- The `062902` script is present but should not be treated as a target-root unlock.",
                "- It contains a target-root materialization path and declares `target_root_mutated=true` if run.",
                "- Its own metadata preserves the blockers: `crisis_no_direct_mapping`, `source_confidence_available=false`, `canonical_merge_allowed_now=false`, and `downstream_rerun_allowed_now=false`.",
                "- Prior Board A TSIE packets already rejected TSIE as rule/OHLCV-derived, single-context, no direct `Crisis`, and accepted `0` roots.",
                "- Required target roots remain absent in this preflight; accepted rows added `0`; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; trade usable false; `update_goal=false`.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path.relative_to(REPO)}`",
                f"- Findings CSV: `{findings_csv.relative_to(REPO)}`",
                f"- Prior blockers CSV: `{blockers_csv.relative_to(REPO)}`",
                f"- Assertions: `{assertions_path.relative_to(REPO)}`",
                "",
                "## Next",
                "",
                "Do not run or count `062902` as an R3 unlock unless the user or board explicitly changes the source/control policy. Continue from real R6 owner/export rows, source-owned R5 recency rows, verifier-native R3 labels, or explicit source/control approval.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = {
        "gate_result": gate_result,
        "materializer_script_present": MATERIALIZER.exists(),
        "would_write_target_root_true": risky_mutation,
        "policy_blockers_present_true": policy_blockers_present,
        "r3_target_root_absent": TARGET_ROOT.exists() is False,
        "accepted_rows_added_zero": payload["accepted_rows_added"] == 0,
        "source_control_evidence_acquired_false": payload["source_control_evidence_acquired"] is False,
        "target_root_mutated_false": payload["target_root_mutated"] is False,
        "canonical_merge_false": payload["canonical_merge"] is False,
        "downstream_promotion_rerun_false": payload["downstream_promotion_rerun"] is False,
        "update_goal_false": payload["update_goal"] is False,
    }
    assertions_path.write_text("\n".join(f"{key}={value}" for key, value in assertions.items()) + "\n")
    return 0 if all(value for key, value in assertions.items() if key != "gate_result") else 1


if __name__ == "__main__":
    raise SystemExit(main())
