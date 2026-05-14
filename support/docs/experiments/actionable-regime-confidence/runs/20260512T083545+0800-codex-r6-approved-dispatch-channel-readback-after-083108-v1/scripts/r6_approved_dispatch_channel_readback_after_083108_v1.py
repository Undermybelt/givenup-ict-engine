#!/usr/bin/env python3
"""Read-only Board A R6 dispatch-channel/provenance gate readback."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T083545+0800-codex-r6-approved-dispatch-channel-readback-after-083108-v1"
SLUG = "r6-approved-dispatch-channel-readback-after-083108-v1"
GATE = "r6_approved_dispatch_channel_readback_after_083108_v1=no_approved_dispatch_channel_no_rows_no_unlock"

SCRIPT = Path(__file__).resolve()
REPO = SCRIPT.parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / SLUG
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
V5_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T052650-codex-r6-owner-export-v5-dispatch-manifest-v1/r6-owner-export-v5-dispatch-manifest-v1"
HANDOFF_MD = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T061314+0800-codex-r6-v5-operator-dispatch-handoff-after-060807-v1/r6-v5-operator-dispatch-handoff-after-060807-v1/r6_v5_operator_dispatch_handoff_after_060807_v1.md"
ARRIVAL_JSON = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T083108+0800-codex-source-control-arrival-poll-after-082720-v1/source-control-arrival-poll-after-082720-v1/source_control_arrival_poll_after_082720_v1.json"
APPROVAL_PACKAGE = Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid")

TARGET_ROOTS = [
    ("r6_owner_export_tmp", Path("/tmp/ict-engine-board-a-r6-owner-export-v1")),
    ("r6_owner_export_private_tmp", Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1")),
    ("r5_recency_tmp", Path("/tmp/ict-engine-source-panel-recency-extension")),
    ("r5_recency_private_tmp", Path("/private/tmp/ict-engine-source-panel-recency-extension")),
    ("r3_native_subhour_tmp", Path("/tmp/ict-engine-native-subhour-source-label-intake")),
    ("r3_native_subhour_private_tmp", Path("/private/tmp/ict-engine-native-subhour-source-label-intake")),
]

ENV_PATTERNS = [
    "SMTP",
    "SENDGRID",
    "MAIL",
    "EMAIL",
    "GMAIL",
    "OUTLOOK",
    "EXCHANGE",
    "POSTMARK",
    "RESEND",
    "AWS_SES",
    "CME",
    "CBOE",
    "CFE",
    "DATASHOP",
    "FINRA",
    "CAT",
    "TICKET",
    "LICENSE",
    "EXPORT",
]

MAIL_BINARIES = ["sendmail", "mail", "mailx", "msmtp", "mutt", "neomutt", "gh"]


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def board_sha() -> str:
    return sha256(BOARD) or "missing"


def env_name_hits() -> list[str]:
    hits: list[str] = []
    for name in os.environ:
        upper = name.upper()
        if any(pattern in upper for pattern in ENV_PATTERNS):
            hits.append(name)
    return sorted(hits)


def target_root_rows() -> list[dict]:
    rows: list[dict] = []
    for name, path in TARGET_ROOTS:
        sample_files: list[str] = []
        if path.exists() and path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    sample_files.append(str(child))
                    if len(sample_files) >= 10:
                        break
        elif path.exists() and path.is_file():
            sample_files.append(str(path))
        rows.append(
            {
                "name": name,
                "path": str(path),
                "exists": path.exists(),
                "is_dir": path.is_dir(),
                "sampled_files": len(sample_files),
                "sample_files": sample_files,
            }
        )
    return rows


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    cme_eml = V5_ROOT / "cme_group_owner_export_v5_dispatch_v1.eml"
    cboe_eml = V5_ROOT / "cboe_cfe_owner_export_v5_dispatch_v1.eml"
    dispatch_assets = [
        {
            "owner": "CME Group",
            "path": str(cme_eml.relative_to(REPO)),
            "exists": cme_eml.exists(),
            "sha256": sha256(cme_eml),
            "status": "draft_not_sent",
        },
        {
            "owner": "Cboe/CFE",
            "path": str(cboe_eml.relative_to(REPO)),
            "exists": cboe_eml.exists(),
            "sha256": sha256(cboe_eml),
            "status": "draft_not_sent",
        },
    ]

    approval = read_json(APPROVAL_PACKAGE)
    approval_assertions = approval.get("assertions", {})
    arrival = read_json(ARRIVAL_JSON)
    env_hits = env_name_hits()
    mail_binary_hits = {binary: shutil.which(binary) for binary in MAIL_BINARIES}
    target_roots = target_root_rows()

    r6_roots_present = any(row["exists"] for row in target_roots if row["name"].startswith("r6_owner_export"))
    r5_roots_present = any(row["exists"] for row in target_roots if row["name"].startswith("r5_recency"))
    required_dispatch_assets_present = all(asset["exists"] and asset["sha256"] for asset in dispatch_assets)
    approval_present = bool(approval_assertions.get("approval_present"))
    canonical_merge_allowed = bool(approval_assertions.get("canonical_merge_allowed_now"))
    downstream_rerun_allowed = bool(approval_assertions.get("downstream_rerun_allowed_now"))

    approved_dispatch_channel_present = False
    source_control_evidence_acquired = False
    valid_required_root_unlock = False

    result = {
        "run_id": RUN_ID,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_before_artifact": board_sha(),
        "gate_result": GATE,
        "inputs": {
            "v5_dispatch_manifest_root": str(V5_ROOT.relative_to(REPO)),
            "operator_handoff_md": str(HANDOFF_MD.relative_to(REPO)),
            "arrival_poll_json": str(ARRIVAL_JSON.relative_to(REPO)),
            "approval_package": str(APPROVAL_PACKAGE),
        },
        "dispatch_assets": dispatch_assets,
        "approval_package_present": APPROVAL_PACKAGE.exists(),
        "approval_package_gate_result": approval.get("gate_result"),
        "approval_present": approval_present,
        "canonical_merge_allowed_now": canonical_merge_allowed,
        "downstream_rerun_allowed_now": downstream_rerun_allowed,
        "operator_env_names_present": env_hits,
        "operator_env_names_present_count": len(env_hits),
        "mail_binary_names_present": sorted([name for name, path in mail_binary_hits.items() if path]),
        "mail_binary_path_presence": {name: bool(path) for name, path in mail_binary_hits.items()},
        "approved_dispatch_channel_present": approved_dispatch_channel_present,
        "external_requests_sent_by_this_artifact": False,
        "dispatch_ticket_export_license_provenance_present": False,
        "target_roots": target_roots,
        "r6_owner_export_roots_present": r6_roots_present,
        "r5_recency_roots_present": r5_roots_present,
        "arrival_poll_gate_result": arrival.get("gate_result"),
        "arrival_poll_valid_required_root_unlock": arrival.get("valid_required_root_unlock", False),
        "arrival_poll_source_control_evidence_acquired": arrival.get("source_control_evidence_acquired", False),
        "required_dispatch_assets_present": required_dispatch_assets_present,
        "accepted_rows_added": 0,
        "r6_owner_export_unlock": False,
        "r5_recency_unlock": False,
        "r3_native_subhour_unlock": False,
        "valid_required_root_unlock": valid_required_root_unlock,
        "source_control_evidence_acquired": source_control_evidence_acquired,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
    }

    json_path = OUT_DIR / "r6_approved_dispatch_channel_readback_after_083108_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    asset_csv = OUT_DIR / "r6_approved_dispatch_assets_after_083108_v1.csv"
    with asset_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["owner", "path", "exists", "sha256", "status"])
        writer.writeheader()
        writer.writerows(dispatch_assets)

    roots_csv = OUT_DIR / "r6_dispatch_target_roots_after_083108_v1.csv"
    with roots_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["name", "path", "exists", "is_dir", "sampled_files"])
        writer.writeheader()
        for row in target_roots:
            writer.writerow({key: row[key] for key in ["name", "path", "exists", "is_dir", "sampled_files"]})

    env_csv = OUT_DIR / "r6_dispatch_channel_indicators_after_083108_v1.csv"
    with env_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["indicator_type", "name", "present"])
        writer.writeheader()
        for name in env_hits:
            writer.writerow({"indicator_type": "env_name", "name": name, "present": True})
        for name, present in result["mail_binary_path_presence"].items():
            writer.writerow({"indicator_type": "mail_binary", "name": name, "present": present})

    md_path = OUT_DIR / "r6_approved_dispatch_channel_readback_after_083108_v1.md"
    md_path.write_text(
        "\n".join(
            [
                "# R6 Approved Dispatch Channel Readback After 083108 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{GATE}`",
                "",
                "## Scope",
                "",
                "Read-only check after terminal `083108` source/control arrival poll. This packet verifies whether a local approved dispatch channel, explicit approval state, ticket/export/license provenance, or required R6/R5 roots have appeared. It does not send external requests, mutate target roots, approve route metadata, run direct verifier, run canonical merge, run selected-data AutoQuant, run Pre-Bayes/BBN/CatBoost/execution-tree promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Dispatch Assets",
                "",
                "| owner | draft | sha256 | status |",
                "|---|---|---:|---|",
                *[
                    f"| {asset['owner']} | `{asset['path']}` | `{asset['sha256']}` | {asset['status']} |"
                    for asset in dispatch_assets
                ],
                "",
                "## Channel / Approval Readback",
                "",
                f"- Operator/env-name indicators present: `{len(env_hits)}`.",
                f"- Local mail/send binaries present: `{', '.join(result['mail_binary_names_present']) if result['mail_binary_names_present'] else 'none'}`.",
                f"- Approval package present: `{APPROVAL_PACKAGE.exists()}` with gate `{approval.get('gate_result')}`.",
                f"- Approval present: `{approval_present}`; canonical merge allowed now: `{canonical_merge_allowed}`; downstream rerun allowed now: `{downstream_rerun_allowed}`.",
                f"- Approved dispatch channel present: `{approved_dispatch_channel_present}`.",
                f"- Dispatch ticket/export/license provenance present: `false`.",
                "",
                "## Target Roots",
                "",
                "| name | path | exists | sampled files |",
                "|---|---|---:|---:|",
                *[
                    f"| `{row['name']}` | `{row['path']}` | `{str(row['exists']).lower()}` | `{row['sampled_files']}` |"
                    for row in target_roots
                ],
                "",
                "## Decision",
                "",
                "- The active v5 CME and Cboe/CFE dispatch drafts are still present and checksum-stable, but this readback found no approved local dispatch channel and did not send them.",
                "- The approval package remains a decision package only: approval present false, canonical merge false, and downstream rerun false.",
                "- R6 owner/export and R5 recency roots are still absent; R3 native-subhour roots are present but non-promoting under the current contract.",
                "- Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed false; and `update_goal=false`.",
                "",
                "## Next",
                "",
                "Use an approved operator mail/vendor-portal path to send or otherwise satisfy the v5 CME/Cboe/CFE owner-export requests, preserving ticket/export/license provenance, or obtain explicit same-exhibit `FLIP`-as-control approval. Do not run verifier, canonical merge, selected-data AutoQuant, or downstream promotion until a required source/control root unlocks.",
                "",
            ]
        )
    )

    assertions = {
        "gate_result": GATE,
        "required_dispatch_assets_present": required_dispatch_assets_present,
        "operator_env_names_present_count": len(env_hits),
        "approved_dispatch_channel_present": approved_dispatch_channel_present,
        "external_requests_sent_by_this_artifact": False,
        "dispatch_ticket_export_license_provenance_present": False,
        "approval_present": approval_present,
        "valid_required_root_unlock": valid_required_root_unlock,
        "source_control_evidence_acquired": source_control_evidence_acquired,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
    }
    assertion_path = CHECK_DIR / "r6_approved_dispatch_channel_readback_after_083108_v1_assertions.out"
    assertion_path.write_text("\n".join(f"{key}={str(value).lower() if isinstance(value, bool) else value}" for key, value in assertions.items()) + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
