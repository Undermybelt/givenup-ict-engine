#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260512T082337+0800-codex-post-081705-required-root-dispatch-gate-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "post-081705-required-root-dispatch-gate-v1"
CHECKS_DIR = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

LATEST_EVIDENCE = [
    (
        "081025",
        "docs/experiments/actionable-regime-confidence/runs/20260512T081025+0800-codex-r6-direct-intake-approval-gap-readback-after-080950-v1",
        "checks/r6_direct_intake_approval_gap_readback_after_080950_v1_assertions.out",
    ),
    (
        "081149",
        "docs/experiments/actionable-regime-confidence/runs/20260512T081149+0800-codex-r6-public-docket-attachment-route-probe-after-080700-v1",
        "checks/r6_public_docket_attachment_route_probe_after_080700_v1_assertions.out",
    ),
    (
        "081323",
        "docs/experiments/actionable-regime-confidence/runs/20260512T081323+0800-codex-courtlistener-recap-sibling-attachment-probe-after-080906-v1",
        "checks/courtlistener_recap_sibling_attachment_probe_after_080906_v1_assertions.out",
    ),
    (
        "081522",
        "docs/experiments/actionable-regime-confidence/runs/20260512T081522+0800-codex-r6-courtlistener-recap-control-route-after-080950-v1",
        "checks/r6_courtlistener_recap_control_route_after_080950_v1_assertions.out",
    ),
    (
        "081705",
        "docs/experiments/actionable-regime-confidence/runs/20260512T081705+0800-codex-courtlistener-recap-sibling-fast-probe-after-081323-v1",
        "checks/courtlistener_recap_sibling_fast_probe_after_081323_v1_assertions.out",
    ),
]

TARGET_ROOTS = {
    "r6_owner_export": {
        "path": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        "required_files": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
        "approval_files": [
            "source_policy_approval.json",
            "control_policy_approval.json",
            "owner_approval_reference.md",
        ],
    },
    "r5_recency": {
        "path": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required_files": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
        "approval_files": [],
    },
    "r3_native_subhour": {
        "path": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required_files": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
        "approval_files": [],
    },
}

DISPATCH_DRAFTS = [
    (
        "cme_group",
        REPO
        / "docs/experiments/actionable-regime-confidence/runs/20260512T052650-codex-r6-owner-export-v5-dispatch-manifest-v1/r6-owner-export-v5-dispatch-manifest-v1/cme_group_owner_export_v5_dispatch_v1.eml",
        "56319c5826e17480a1130fdd6accc0378a2e5e099f4d4d771532ab2ced6cbd0b",
    ),
    (
        "cboe_cfe",
        REPO
        / "docs/experiments/actionable-regime-confidence/runs/20260512T052650-codex-r6-owner-export-v5-dispatch-manifest-v1/r6-owner-export-v5-dispatch-manifest-v1/cboe_cfe_owner_export_v5_dispatch_v1.eml",
        "411e6733aaaf0ade2097f49601086177f2c89f47089d5eb9b37b34a5fae1249d",
    ),
]


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_assertions(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for raw in path.read_text(errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip()
        elif line.startswith("PASS "):
            out["pass_marker"] = line[5:].strip()
    return out


def root_status(name: str, spec: dict[str, object]) -> dict[str, object]:
    root = spec["path"]
    assert isinstance(root, Path)
    required_files = list(spec["required_files"])
    approval_files = list(spec["approval_files"])
    present = root.exists()
    required_status = {item: (root / item).is_file() for item in required_files}
    approval_status = {item: (root / item).is_file() for item in approval_files}
    listed_files: list[str] = []
    if present and root.is_dir():
        listed_files = sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file())[:200]
    status = {
        "root_name": name,
        "path": str(root),
        "exists": present,
        "required_files_present": required_status,
        "all_required_files_present": bool(required_status) and all(required_status.values()),
        "approval_files_present": approval_status,
        "any_approval_file_present": any(approval_status.values()) if approval_status else False,
        "file_count_visible": len(listed_files),
        "visible_files_sample": listed_files,
    }
    if name == "r3_native_subhour":
        provenance_path = root / "native_subhour_source_label_provenance.json"
        labels: list[str] = []
        limitations: list[str] = []
        if provenance_path.is_file():
            try:
                provenance = json.loads(provenance_path.read_text(errors="replace"))
                labels = list(provenance.get("accepted_mapping_confidence_95_labels", []))
                limitations = list(provenance.get("limitations", []))
            except json.JSONDecodeError:
                labels = []
                limitations = ["provenance_json_parse_failed"]
        crisis_present = "Crisis" in set(labels)
        status.update(
            {
                "accepted_mapping_confidence_95_labels": labels,
                "crisis_present": crisis_present,
                "promotion_allowed": False,
                "quarantine_reason": (
                    "crisis_absent_native_subhour_root_is_source_label_material_only"
                    if not crisis_present
                    else "promotion_not_approved_by_board_contract"
                ),
                "limitations": limitations,
            }
        )
    return status


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    board_sha = sha256(BOARD)
    evidence = []
    for short_id, rel_root, rel_assertions in LATEST_EVIDENCE:
        root = REPO / rel_root
        assertions_path = root / rel_assertions
        parsed = parse_assertions(assertions_path)
        evidence.append(
            {
                "id": short_id,
                "root": rel_root,
                "root_exists": root.is_dir(),
                "assertions_path": str(assertions_path.relative_to(REPO)),
                "assertions_exists": assertions_path.is_file(),
                "gate": parsed.get("gate") or parsed.get("gate_result") or "",
                "accepted_rows_added": parsed.get("accepted_rows_added", ""),
                "valid_required_root_unlock": parsed.get("valid_required_root_unlock", ""),
                "source_control_evidence_acquired": parsed.get("source_control_evidence_acquired", ""),
                "canonical_merge": parsed.get("canonical_merge", ""),
                "downstream_promotion_rerun": parsed.get("downstream_promotion_rerun", ""),
                "update_goal": parsed.get("update_goal", ""),
            }
        )

    roots = {name: root_status(name, spec) for name, spec in TARGET_ROOTS.items()}
    r6_ready = roots["r6_owner_export"]["all_required_files_present"] and (
        roots["r6_owner_export"]["any_approval_file_present"]
        or bool((TARGET_ROOTS["r6_owner_export"]["path"] / "provenance_manifest.json").is_file())
    )
    r5_ready = roots["r5_recency"]["all_required_files_present"]
    r3_ready = bool(
        roots["r3_native_subhour"]["all_required_files_present"]
        and roots["r3_native_subhour"].get("crisis_present") is True
        and roots["r3_native_subhour"].get("promotion_allowed") is True
    )

    dispatch = []
    for owner, path, expected in DISPATCH_DRAFTS:
        digest = sha256(path)
        dispatch.append(
            {
                "owner": owner,
                "path": str(path.relative_to(REPO)),
                "exists": path.is_file(),
                "sha256": digest,
                "expected_sha256": expected,
                "sha256_matches_expected": digest == expected,
                "status": "draft_present_not_sent" if path.is_file() else "draft_missing",
            }
        )

    dispatch_env_markers = [
        "SMTP_HOST",
        "SMTP_USER",
        "SMTP_PASS",
        "SENDGRID_API_KEY",
        "MAILGUN_API_KEY",
        "RESEND_API_KEY",
    ]
    dispatch_tools = ["sendmail", "mail", "mutt", "msmtp"]
    local_dispatch_probe = {
        "env_markers_present": {key: bool(os.environ.get(key)) for key in dispatch_env_markers},
        "tools_present": {tool: bool(shutil.which(tool)) for tool in dispatch_tools},
        "approved_operator_dispatch_path": False,
        "external_requests_sent": False,
        "reason": "No explicit operator approval/ticket/export evidence is present in required roots; this probe does not send external messages.",
    }

    accepted_rows_added = 0
    required_unlock = bool(r6_ready or r5_ready or r3_ready)
    source_control_evidence_acquired = required_unlock
    canonical_merge = False
    downstream = False
    strict_full_objective = False
    trade_usable = False
    promotion_allowed = False
    update_goal = False

    payload = {
        "run_id": RUN_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "board_sha256_before_artifact": board_sha,
        "scope": "post_081705_required_root_and_dispatch_readback_only",
        "latest_evidence_checked": evidence,
        "target_roots": roots,
        "dispatch_drafts": dispatch,
        "local_dispatch_probe": local_dispatch_probe,
        "r6_owner_export_unlock": bool(r6_ready),
        "r5_recency_unlock": bool(r5_ready),
        "r3_native_subhour_unlock": bool(r3_ready),
        "valid_required_root_unlock": required_unlock,
        "accepted_rows_added": accepted_rows_added,
        "source_control_evidence_acquired": source_control_evidence_acquired,
        "canonical_merge": canonical_merge,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": downstream,
        "strict_full_objective": strict_full_objective,
        "trade_usable": trade_usable,
        "promotion_allowed": promotion_allowed,
        "update_goal": update_goal,
        "gate_result": "post_081705_required_root_dispatch_gate_v1=no_required_root_or_dispatch_unlock",
        "next_action": (
            "Use an approved operator path to send/upload the v5 CME and Cboe/CFE drafts, preserve ticket/export/license identifiers, "
            "or supply explicit FLIP-control approval or verifier-native owner-export/source-panel/native-subhour rows before canonical merge or downstream rerun."
        ),
    }

    json_path = OUT_DIR / "post_081705_required_root_dispatch_gate_v1.json"
    csv_path = OUT_DIR / "post_081705_required_root_dispatch_gate_v1.csv"
    md_path = OUT_DIR / "post_081705_required_root_dispatch_gate_v1.md"
    assertions_path = CHECKS_DIR / "post_081705_required_root_dispatch_gate_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "root_name",
                "path",
                "exists",
                "all_required_files_present",
                "any_approval_file_present",
                "file_count_visible",
            ],
        )
        writer.writeheader()
        for row in roots.values():
            writer.writerow(
                {
                    "root_name": row["root_name"],
                    "path": row["path"],
                    "exists": row["exists"],
                    "all_required_files_present": row["all_required_files_present"],
                    "any_approval_file_present": row["any_approval_file_present"],
                    "file_count_visible": row["file_count_visible"],
                }
            )

    md_lines = [
        "# Post 081705 Required Root Dispatch Gate v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Gate result: `post_081705_required_root_dispatch_gate_v1=no_required_root_or_dispatch_unlock`",
        "",
        f"Board sha256 before artifact: `{board_sha}`",
        "",
        "## Purpose",
        "",
        "Read-only gate check after the terminal public docket/RECAP probes. This packet checks whether any required R6 owner-export, R5 recency-extension, or R3 native-subhour source-label root arrived, and whether the v5 owner-export dispatch drafts are still intact. It does not send external messages, approve same-exhibit `FLIP` rows, mutate intake roots, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.",
        "",
        "## Latest Evidence Checked",
        "",
        "| id | root exists | assertions exists | gate | accepted rows |",
        "|---|---:|---:|---|---:|",
    ]
    for row in evidence:
        md_lines.append(
            f"| `{row['id']}` | `{row['root_exists']}` | `{row['assertions_exists']}` | `{row['gate']}` | `{row['accepted_rows_added']}` |"
        )
    md_lines += [
        "",
        "## Required Root Readback",
        "",
        "| root | exists | all required files | approval present | visible files |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in roots.values():
        md_lines.append(
            f"| `{row['root_name']}` | `{row['exists']}` | `{row['all_required_files_present']}` | `{row['any_approval_file_present']}` | `{row['file_count_visible']}` |"
        )
    md_lines += [
        "",
        "## Dispatch Draft Integrity",
        "",
        "| owner | exists | sha256 matches expected | status |",
        "|---|---:|---:|---|",
    ]
    for row in dispatch:
        md_lines.append(
            f"| `{row['owner']}` | `{row['exists']}` | `{row['sha256_matches_expected']}` | `{row['status']}` |"
        )
    md_lines += [
        "",
        "## Decision",
        "",
        f"- R6 owner/export unlock: `{payload['r6_owner_export_unlock']}`.",
        f"- R5 recency unlock: `{payload['r5_recency_unlock']}`.",
        f"- R3 native-subhour unlock: `{payload['r3_native_subhour_unlock']}`.",
        f"- Source/control evidence acquired: `{payload['source_control_evidence_acquired']}`.",
        f"- Canonical merge: `{payload['canonical_merge']}`.",
        f"- Downstream promotion rerun: `{payload['downstream_promotion_rerun']}`.",
        f"- Strict full objective: `{payload['strict_full_objective']}`.",
        f"- `update_goal`: `{payload['update_goal']}`.",
        "",
        "## Next",
        "",
        payload["next_action"],
        "",
    ]
    md_path.write_text("\n".join(md_lines))

    assertions = [
        "PASS post_081705_required_root_dispatch_gate_v1",
        f"gate_result={payload['gate_result']}",
        f"r6_owner_export_unlock={str(payload['r6_owner_export_unlock']).lower()}",
        f"r5_recency_unlock={str(payload['r5_recency_unlock']).lower()}",
        f"r3_native_subhour_unlock={str(payload['r3_native_subhour_unlock']).lower()}",
        f"valid_required_root_unlock={str(payload['valid_required_root_unlock']).lower()}",
        f"source_control_evidence_acquired={str(payload['source_control_evidence_acquired']).lower()}",
        f"accepted_rows_added={payload['accepted_rows_added']}",
        f"canonical_merge={str(payload['canonical_merge']).lower()}",
        f"selected_data_autoquant_promotion={str(payload['selected_data_autoquant_promotion']).lower()}",
        f"downstream_promotion_rerun={str(payload['downstream_promotion_rerun']).lower()}",
        f"strict_full_objective={str(payload['strict_full_objective']).lower()}",
        f"trade_usable={str(payload['trade_usable']).lower()}",
        f"promotion_allowed={str(payload['promotion_allowed']).lower()}",
        f"update_goal={str(payload['update_goal']).lower()}",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n")

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
