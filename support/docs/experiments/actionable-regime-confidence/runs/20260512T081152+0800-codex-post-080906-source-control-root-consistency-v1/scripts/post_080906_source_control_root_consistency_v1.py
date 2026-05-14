#!/usr/bin/env python3
"""Read back Board A source/control roots after the 080906 route probe.

This script is intentionally read-only. It inventories target roots and recent
artifact roots, records checksums for unstable race-readbacks, and refuses all
promotion gates unless the required source/control roots are present.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = RUN_ROOT / "post-080906-source-control-root-consistency-v1"
CHECK_ROOT = RUN_ROOT / "checks"
BOARD = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

OPENALEX_ROOT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T080906+0800-codex-openalex-semantic-pwc-source-route-after-080700-v1"
)
OPENALEX_JSON = (
    OPENALEX_ROOT
    / "openalex-semantic-pwc-source-route-after-080700-v1/"
    "openalex_semantic_pwc_source_route_after_080700_v1.json"
)
OPENALEX_ASSERTIONS = (
    OPENALEX_ROOT
    / "checks/openalex_semantic_pwc_source_route_after_080700_v1_assertions.out"
)

ROOT_080446 = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T080446+0800-codex-required-root-arrival-poll-after-080054-v1"
)
ASSERTIONS_080446 = ROOT_080446 / "checks/required_root_arrival_poll_after_080054_v1_assertions.out"

ROOT_080950 = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T080950+0800-codex-current-objective-audit-after-080700-v1"
)

TARGETS = {
    "r6_owner_export_root": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r5_recency_root": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "r3_native_subhour_root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "r6_approval_package": Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_key_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in raw_line:
            continue
        key, value = raw_line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def path_record(name: str, path: Path) -> dict[str, Any]:
    record: dict[str, Any] = {
        "name": name,
        "path": str(path),
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "is_file": path.is_file(),
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else "",
    }
    if path.exists() and path.is_file() and path.stat().st_size <= 10_000_000:
        record["sha256"] = sha256_file(path)
    else:
        record["sha256"] = ""
    return record


def board_hash() -> str:
    return sha256_file(BOARD)


def target_summary() -> dict[str, Any]:
    r3_provenance = TARGETS["r3_native_subhour_root"] / "native_subhour_source_label_provenance.json"
    r3_rows = TARGETS["r3_native_subhour_root"] / "native_subhour_source_label_rows.csv"
    provenance = read_json(r3_provenance)
    labels = provenance.get("accepted_mapping_confidence_95_labels") or []
    approval = read_json(TARGETS["r6_approval_package"])
    approval_assertions = approval.get("assertions", {}) if isinstance(approval, dict) else {}
    return {
        "r6_owner_export_root_present": TARGETS["r6_owner_export_root"].exists(),
        "r5_recency_root_present": TARGETS["r5_recency_root"].exists(),
        "r3_native_subhour_root_present": TARGETS["r3_native_subhour_root"].exists(),
        "r3_native_subhour_rows_present": r3_rows.exists(),
        "r3_native_subhour_provenance_sha256": sha256_file(r3_provenance)
        if r3_provenance.exists()
        else "",
        "r3_native_subhour_row_count": provenance.get("row_count", ""),
        "r3_native_subhour_labels": labels,
        "r3_native_subhour_crisis_present": "Crisis" in labels,
        "r6_approval_package_present": TARGETS["r6_approval_package"].exists(),
        "r6_approval_present": bool(approval_assertions.get("approval_present", False)),
        "r6_canonical_merge_allowed_now": bool(
            approval_assertions.get("canonical_merge_allowed_now", False)
        ),
        "r6_downstream_rerun_allowed_now": bool(
            approval_assertions.get("downstream_rerun_allowed_now", False)
        ),
    }


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    CHECK_ROOT.mkdir(parents=True, exist_ok=True)

    openalex = read_json(OPENALEX_JSON)
    assertion_080446 = read_key_values(ASSERTIONS_080446)
    board_text = BOARD.read_text(encoding="utf-8")
    targets = target_summary()

    run_records = [
        path_record("080906_openalex_semantic_pwc_root", OPENALEX_ROOT),
        path_record("080906_openalex_semantic_pwc_assertions", OPENALEX_ASSERTIONS),
        path_record("080446_required_root_arrival_poll_root", ROOT_080446),
        path_record("080446_required_root_arrival_poll_assertions", ASSERTIONS_080446),
        path_record("080950_current_objective_audit_root", ROOT_080950),
        path_record(
            "080950_current_objective_audit_assertions",
            ROOT_080950 / "checks/current_objective_audit_after_080700_v1_assertions.out",
        ),
    ]
    target_records = [path_record(name, path) for name, path in TARGETS.items()]

    root_080950_complete = (
        ROOT_080950 / "checks/current_objective_audit_after_080700_v1_assertions.out"
    ).exists() and (
        ROOT_080950
        / "current-objective-audit-after-080700-v1/current_objective_audit_after_080700_v1.md"
    ).exists()

    summary: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": "20260512T081152+0800-codex-post-080906-source-control-root-consistency-v1",
        "board_sha256_at_readback": board_hash(),
        "gate_result": "post_080906_source_control_root_consistency_v1=no_required_source_control_unlock",
        "board_contains_080906_before_writeback": "080906" in board_text
        or "openalex_semantic_pwc_source_route_after_080700" in board_text,
        "openalex_080906_gate": openalex.get("gate_result", ""),
        "openalex_080906_requests_sent": openalex.get("requests_sent", ""),
        "openalex_080906_failed_or_parse_failed": openalex.get("failed_or_parse_failed", ""),
        "openalex_080906_candidate_rows": openalex.get("candidate_rows", ""),
        "openalex_080906_required_filename_or_token_hits": openalex.get(
            "required_filename_or_token_hits", ""
        ),
        "openalex_080906_exact_mainregimev2_hits": openalex.get("exact_mainregimev2_hits", ""),
        "openalex_080906_r5_post_cutoff_route_hits": openalex.get(
            "r5_post_cutoff_route_hits", ""
        ),
        "openalex_080906_r3_native_subhour_crisis_hits": openalex.get(
            "r3_native_subhour_crisis_hits", ""
        ),
        "openalex_080906_r6_owner_control_route_hits": openalex.get(
            "r6_owner_control_route_hits", ""
        ),
        "openalex_080906_broad_context_hits": openalex.get("broad_context_hits", ""),
        "root_080446_present_now": ROOT_080446.exists(),
        "root_080446_assertion_sha256": sha256_file(ASSERTIONS_080446)
        if ASSERTIONS_080446.exists()
        else "",
        "root_080446_gate": assertion_080446.get("gate_result", ""),
        "root_080446_valid_required_root_unlock": assertion_080446.get(
            "valid_required_root_unlock", ""
        ),
        "root_080950_present_now": ROOT_080950.exists(),
        "root_080950_complete_now": root_080950_complete,
        **targets,
        "accepted_rows_added": 0,
        "r6_owner_export_unlock": False,
        "r5_recency_unlock": False,
        "r3_native_subhour_unlock": False,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
    }

    (OUT_ROOT / "post_080906_source_control_root_consistency_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    with (OUT_ROOT / "post_080906_source_control_root_consistency_targets_v1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        fieldnames = ["name", "path", "exists", "is_dir", "is_file", "size_bytes", "sha256"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(target_records + run_records)

    md = f"""# Post-080906 Source/Control Root Consistency v1

Gate result: `{summary["gate_result"]}`.

This is a read-only source/control inventory. It does not approve public paper
metadata, TSIE-derived labels, approval-package presence, or run-root existence
as source/control evidence.

## Metrics

- Board hash at readback: `{summary["board_sha256_at_readback"]}`
- Board contained `080906` before writeback: `{summary["board_contains_080906_before_writeback"]}`
- `080906` gate: `{summary["openalex_080906_gate"]}`
- `080906` requests sent: `{summary["openalex_080906_requests_sent"]}`
- `080906` failed or parse-failed: `{summary["openalex_080906_failed_or_parse_failed"]}`
- `080906` candidate rows: `{summary["openalex_080906_candidate_rows"]}`
- `080906` required filename/token hits: `{summary["openalex_080906_required_filename_or_token_hits"]}`
- `080906` exact `MainRegimeV2` hits: `{summary["openalex_080906_exact_mainregimev2_hits"]}`
- `080906` R5 route hits: `{summary["openalex_080906_r5_post_cutoff_route_hits"]}`
- `080906` R3 native-subhour Crisis hits: `{summary["openalex_080906_r3_native_subhour_crisis_hits"]}`
- `080906` R6 owner/control route hits: `{summary["openalex_080906_r6_owner_control_route_hits"]}`
- `080906` broad context hits: `{summary["openalex_080906_broad_context_hits"]}`
- `080446` present now: `{summary["root_080446_present_now"]}`
- `080446` assertion checksum: `{summary["root_080446_assertion_sha256"]}`
- `080950` complete now: `{summary["root_080950_complete_now"]}`
- R6 owner/export root present: `{summary["r6_owner_export_root_present"]}`
- R5 recency root present: `{summary["r5_recency_root_present"]}`
- R3 native-subhour labels: `{", ".join(summary["r3_native_subhour_labels"])}`
- R3 Crisis present: `{summary["r3_native_subhour_crisis_present"]}`
- R6 approval present: `{summary["r6_approval_present"]}`

## Decision

- Accepted rows added: `0`.
- No valid required R3/R5/R6 source/control root was acquired.
- No canonical merge, selected-data AutoQuant promotion, or downstream promotion
  rerun is allowed.
- `update_goal=false`.
"""
    (OUT_ROOT / "post_080906_source_control_root_consistency_v1.md").write_text(
        md, encoding="utf-8"
    )

    assertions = [
        "PASS post_080906_source_control_root_consistency_v1",
        f"gate_result={summary['gate_result']}",
        f"board_contains_080906_before_writeback={str(summary['board_contains_080906_before_writeback']).lower()}",
        f"openalex_080906_gate={summary['openalex_080906_gate']}",
        f"openalex_080906_requests_sent={summary['openalex_080906_requests_sent']}",
        f"openalex_080906_failed_or_parse_failed={summary['openalex_080906_failed_or_parse_failed']}",
        f"openalex_080906_candidate_rows={summary['openalex_080906_candidate_rows']}",
        f"openalex_080906_required_filename_or_token_hits={summary['openalex_080906_required_filename_or_token_hits']}",
        f"openalex_080906_exact_mainregimev2_hits={summary['openalex_080906_exact_mainregimev2_hits']}",
        f"openalex_080906_r5_post_cutoff_route_hits={summary['openalex_080906_r5_post_cutoff_route_hits']}",
        f"openalex_080906_r3_native_subhour_crisis_hits={summary['openalex_080906_r3_native_subhour_crisis_hits']}",
        f"openalex_080906_r6_owner_control_route_hits={summary['openalex_080906_r6_owner_control_route_hits']}",
        f"root_080446_present_now={str(summary['root_080446_present_now']).lower()}",
        f"root_080446_gate={summary['root_080446_gate']}",
        f"root_080950_complete_now={str(summary['root_080950_complete_now']).lower()}",
        f"r6_owner_export_root_present={str(summary['r6_owner_export_root_present']).lower()}",
        f"r5_recency_root_present={str(summary['r5_recency_root_present']).lower()}",
        f"r3_native_subhour_crisis_present={str(summary['r3_native_subhour_crisis_present']).lower()}",
        f"r6_approval_present={str(summary['r6_approval_present']).lower()}",
        "accepted_rows_added=0",
        "r6_owner_export_unlock=false",
        "r5_recency_unlock=false",
        "r3_native_subhour_unlock=false",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "promotion_allowed=false",
        "update_goal=false",
    ]
    (CHECK_ROOT / "post_080906_source_control_root_consistency_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    print(summary["gate_result"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
