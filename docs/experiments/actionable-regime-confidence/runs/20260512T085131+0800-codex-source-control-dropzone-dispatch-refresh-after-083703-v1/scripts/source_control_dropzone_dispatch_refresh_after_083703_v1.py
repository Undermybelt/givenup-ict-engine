#!/usr/bin/env python3
"""Read-only source/control dropzone and dispatch refresh after 083703."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = RUN_ROOT / "source-control-dropzone-dispatch-refresh-after-083703-v1"
CHECKS_DIR = RUN_ROOT / "checks"

BOARD_A = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
BOARD_B = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"

RUN_ID = "20260512T085131+0800-codex-source-control-dropzone-dispatch-refresh-after-083703-v1"
GATE = (
    "source_control_dropzone_dispatch_refresh_after_083703_v1="
    "no_new_owner_export_or_approved_dispatch_no_unlock"
)

POST_083703_CUTOFF = datetime(2026, 5, 12, 8, 37, 3, tzinfo=timezone(timedelta(hours=8)))

TARGET_ROOTS = {
    "r6_owner_export_tmp": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r6_owner_export_private_tmp": Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r5_recency_tmp": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "r5_recency_private_tmp": Path("/private/tmp/ict-engine-source-panel-recency-extension"),
    "r3_native_subhour_tmp": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "r3_native_subhour_private_tmp": Path("/private/tmp/ict-engine-native-subhour-source-label-intake"),
}

CURRENT_R6_REQUIRED = [
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
]

LEGACY_R6_REQUIRED = [
    "direct_manipulation_positive_rows.csv",
    "direct_manipulation_matched_controls.csv",
    "direct_manipulation_provenance.json",
]

DISPATCH_DRAFTS = [
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T052650-codex-r6-owner-export-v5-dispatch-manifest-v1"
    / "r6-owner-export-v5-dispatch-manifest-v1"
    / "cme_group_owner_export_v5_dispatch_v1.eml",
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T052650-codex-r6-owner-export-v5-dispatch-manifest-v1"
    / "r6-owner-export-v5-dispatch-manifest-v1"
    / "cboe_cfe_owner_export_v5_dispatch_v1.eml",
]

DISPATCH_ROOTS = [
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T052650-codex-r6-owner-export-v5-dispatch-manifest-v1",
    Path("/tmp"),
    Path("/private/tmp"),
    Path("/Users/thrill3r/Downloads"),
    Path("/Users/thrill3r/Desktop"),
]

DROPZONE_ROOTS = [
    Path("/Users/thrill3r/Downloads"),
    Path("/Users/thrill3r/Desktop"),
]

MATCH_TERMS = [
    "cme",
    "cboe",
    "cfe",
    "cat",
    "finra",
    "databento",
    "oystacher",
    "source",
    "control",
    "owner",
    "export",
    "market_depth",
    "market-depth",
    "market by order",
    "market_by_order",
    "order_lifecycle",
    "order-lifecycle",
    "ticket",
    "license",
]

DISPATCH_TERMS = [
    "approved",
    "sent",
    "ticket",
    "export",
    "license",
    "receipt",
    "vendor",
    "portal",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_sha256_small(path: Path, max_bytes: int = 64 * 1024 * 1024) -> str:
    try:
        if path.stat().st_size > max_bytes:
            return ""
        return sha256_file(path)
    except OSError:
        return ""


def rel_or_abs(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def path_terms(path: Path, terms: list[str]) -> list[str]:
    lowered = str(path).lower().replace(" ", "_")
    return [term for term in terms if term.replace(" ", "_") in lowered]


def root_status(name: str, root: Path) -> dict:
    files = []
    if root.exists():
        for item in sorted(root.rglob("*")):
            if item.is_file():
                try:
                    files.append(
                        {
                            "path": str(item),
                            "size": item.stat().st_size,
                            "mtime": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                        }
                    )
                except OSError:
                    files.append({"path": str(item), "size": None, "mtime": None})
    current_present = [file_name for file_name in CURRENT_R6_REQUIRED if (root / file_name).is_file()]
    legacy_present = [file_name for file_name in LEGACY_R6_REQUIRED if (root / file_name).is_file()]
    return {
        "name": name,
        "path": str(root),
        "exists": root.exists(),
        "file_count": len(files),
        "sample_files": files[:20],
        "current_r6_required_present": current_present,
        "legacy_r6_required_present": legacy_present,
        "current_r6_complete": len(current_present) == len(CURRENT_R6_REQUIRED),
        "legacy_r6_complete": len(legacy_present) == len(LEGACY_R6_REQUIRED),
    }


def scan_dropzones() -> list[dict]:
    rows: list[dict] = []
    cutoff_ts = POST_083703_CUTOFF.timestamp()
    for root in DROPZONE_ROOTS:
        if not root.exists():
            continue
        for base, dirnames, filenames in os.walk(root):
            depth = Path(base).relative_to(root).parts
            if len(depth) >= 5:
                dirnames[:] = []
            for filename in filenames:
                path = Path(base) / filename
                terms = path_terms(path, MATCH_TERMS)
                if not terms:
                    continue
                try:
                    stat = path.stat()
                except OSError:
                    continue
                if stat.st_mtime < cutoff_ts:
                    continue
                rows.append(
                    {
                        "path": str(path),
                        "root": str(root),
                        "size": stat.st_size,
                        "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "matched_terms": ";".join(terms),
                        "sha256_if_small": safe_sha256_small(path),
                    }
                )
    return sorted(rows, key=lambda row: (row["mtime"], row["path"]))


def dispatch_draft_status(path: Path) -> dict:
    exists = path.exists()
    text = path.read_text(encoding="utf-8", errors="replace") if exists else ""
    lowered = text.lower()
    ticket_like = any(term in lowered for term in ["ticket", "case", "request id", "export id", "license"])
    sent_like = any(term in lowered for term in ["sent:", "submitted", "accepted by", "receipt"])
    return {
        "path": rel_or_abs(path),
        "exists": exists,
        "sha256": sha256_file(path) if exists else "",
        "status": "draft_not_sent" if exists and not (ticket_like and sent_like) else "candidate_sent_or_ticketed",
        "ticket_or_license_text_present": ticket_like,
        "sent_or_receipt_text_present": sent_like,
    }


def scan_dispatch_evidence() -> list[dict]:
    rows: list[dict] = []
    cutoff_ts = POST_083703_CUTOFF.timestamp()
    for root in DISPATCH_ROOTS:
        if not root.exists():
            continue
        for base, dirnames, filenames in os.walk(root):
            depth = Path(base).relative_to(root).parts
            if len(depth) >= 3:
                dirnames[:] = []
            for filename in filenames:
                path = Path(base) / filename
                terms = path_terms(path, DISPATCH_TERMS)
                if not terms:
                    continue
                try:
                    stat = path.stat()
                except OSError:
                    continue
                if stat.st_mtime < cutoff_ts:
                    continue
                rows.append(
                    {
                        "path": str(path),
                        "root": str(root),
                        "size": stat.st_size,
                        "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "matched_terms": ";".join(terms),
                        "sha256_if_small": safe_sha256_small(path),
                    }
                )
    return sorted(rows, key=lambda row: (row["mtime"], row["path"]))


def env_names_present() -> list[str]:
    markers = ("DATABENTO", "CME", "CBOE", "CFE", "FINRA", "CAT", "IBKR", "TRADINGVIEW", "KRAKEN")
    return sorted(k for k in os.environ if any(marker in k.upper() for marker in markers))


def tool_paths() -> dict:
    names = [
        "databento",
        "dbn",
        "kaggle",
        "huggingface-cli",
        "sendmail",
        "mail",
        "mailx",
        "msmtp",
        "mutt",
        "swaks",
        "gh",
    ]
    return {name: shutil.which(name) or "" for name in names}


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    target_roots = [root_status(name, root) for name, root in TARGET_ROOTS.items()]
    dropzone_candidates = scan_dropzones()
    dispatch_candidates = scan_dispatch_evidence()
    dispatch_drafts = [dispatch_draft_status(path) for path in DISPATCH_DRAFTS]
    tools = tool_paths()
    env_keys = env_names_present()

    current_r6_complete = any(row["current_r6_complete"] for row in target_roots)
    legacy_r6_complete = any(row["legacy_r6_complete"] for row in target_roots)
    r5_root_present = any(row["exists"] for row in target_roots if row["name"].startswith("r5_"))
    r3_root_present = any(row["exists"] for row in target_roots if row["name"].startswith("r3_"))
    approved_dispatch = any(
        row["ticket_or_license_text_present"] and row["sent_or_receipt_text_present"]
        for row in dispatch_drafts
    )
    ticket_export_license_provenance = approved_dispatch or bool(dispatch_candidates)
    owner_data_env_ready = bool(env_keys)

    assertions = {
        "post_083703_dropzone_candidates": len(dropzone_candidates),
        "post_083703_dispatch_candidate_files": len(dispatch_candidates),
        "current_r6_required_package_complete": current_r6_complete,
        "legacy_r6_required_package_complete": legacy_r6_complete,
        "r5_recency_root_present": r5_root_present,
        "r3_native_subhour_root_present": r3_root_present,
        "approved_dispatch_channel_present": approved_dispatch,
        "dispatch_ticket_export_license_provenance_present": ticket_export_license_provenance,
        "owner_data_env_names_present_count": len(env_keys),
        "owner_data_cli_ready": bool(tools.get("databento") or tools.get("dbn")),
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

    packet = {
        "run_id": RUN_ID,
        "generated_at_local": datetime.now(timezone(timedelta(hours=8))).isoformat(),
        "gate_result": GATE,
        "board_a_sha256_before_artifact": sha256_file(BOARD_A),
        "board_b_sha256_before_artifact": sha256_file(BOARD_B),
        "scope": {
            "mode": "read_only_dropzone_dispatch_refresh_after_083703",
            "cutoff_local": POST_083703_CUTOFF.isoformat(),
            "no_root_mutation": True,
            "no_external_requests": True,
            "no_dispatch_sent": True,
            "no_verifier": True,
            "no_selected_data_autoquant": True,
            "no_downstream_promotion": True,
            "update_goal": False,
        },
        "target_roots": target_roots,
        "dispatch_drafts": dispatch_drafts,
        "dispatch_candidate_files_after_cutoff": dispatch_candidates,
        "dropzone_candidates_after_cutoff": dropzone_candidates,
        "tool_paths": tools,
        "env_keys_present_without_values": env_keys,
        "assertions": assertions,
        "decision": (
            "No post-083703 owner/export or approved dispatch evidence was acquired. "
            "The required R6 owner-export package is still incomplete or absent, R5 recency roots are absent, "
            "R3 native-subhour roots remain present but non-unlocking, and dispatch remains without ticket/export/license provenance."
        ),
        "next": (
            "Continue source/control acquisition only: obtain owner-approved/authenticated FINRA, venue-surveillance, "
            "CAT-like, CME/Cboe/CFE order-lifecycle export rows with positives and matched normal controls, "
            "source-owned post-2026-01-30 R5 MainRegimeV2 rows, verifier-native Crisis-capable R3 native-subhour labels, "
            "or explicit same-exhibit FLIP-as-control approval before verifier, split calibration, canonical merge, "
            "selected-data AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, execution-tree promotion, trade claims, or update_goal."
        ),
    }

    json_path = ARTIFACT_DIR / "source_control_dropzone_dispatch_refresh_after_083703_v1.json"
    roots_csv = ARTIFACT_DIR / "source_control_target_roots_after_083703_v1.csv"
    dropzone_csv = ARTIFACT_DIR / "source_control_dropzone_candidates_after_083703_v1.csv"
    dispatch_csv = ARTIFACT_DIR / "source_control_dispatch_candidates_after_083703_v1.csv"
    md_path = ARTIFACT_DIR / "source_control_dropzone_dispatch_refresh_after_083703_v1.md"
    assertions_path = CHECKS_DIR / "source_control_dropzone_dispatch_refresh_after_083703_v1_assertions.out"

    json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        roots_csv,
        [
            {
                "name": row["name"],
                "path": row["path"],
                "exists": row["exists"],
                "file_count": row["file_count"],
                "current_r6_required_present": ";".join(row["current_r6_required_present"]),
                "legacy_r6_required_present": ";".join(row["legacy_r6_required_present"]),
                "current_r6_complete": row["current_r6_complete"],
                "legacy_r6_complete": row["legacy_r6_complete"],
            }
            for row in target_roots
        ],
        [
            "name",
            "path",
            "exists",
            "file_count",
            "current_r6_required_present",
            "legacy_r6_required_present",
            "current_r6_complete",
            "legacy_r6_complete",
        ],
    )
    write_csv(
        dropzone_csv,
        dropzone_candidates,
        ["path", "root", "size", "mtime", "matched_terms", "sha256_if_small"],
    )
    write_csv(
        dispatch_csv,
        dispatch_candidates,
        ["path", "root", "size", "mtime", "matched_terms", "sha256_if_small"],
    )

    md_path.write_text(
        "\n".join(
            [
                "# Source/Control Dropzone Dispatch Refresh After 083703 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{GATE}`",
                "",
                "## Scope",
                "",
                "Read-only refresh after terminal `083703` and the empty `083711` root. This packet checks target roots, post-083703 Downloads/Desktop drops, and v5 dispatch/approval evidence. It does not mutate roots, send external requests, run verifier, run selected-data AutoQuant, run Pre-Bayes/BBN/CatBoost/execution-tree promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Readback",
                "",
                f"- Board A SHA-256 before artifact: `{packet['board_a_sha256_before_artifact']}`.",
                f"- Board B SHA-256 before artifact: `{packet['board_b_sha256_before_artifact']}`.",
                f"- Post-083703 dropzone candidates: `{len(dropzone_candidates)}`.",
                f"- Post-083703 dispatch candidate files: `{len(dispatch_candidates)}`.",
                f"- Current R6 required package complete in target roots: `{current_r6_complete}`.",
                f"- Legacy R6 required package complete in target roots: `{legacy_r6_complete}`.",
                f"- R5 recency root present: `{r5_root_present}`.",
                f"- R3 native-subhour root present: `{r3_root_present}`; still non-unlocking without accepted Crisis-capable source/control approval.",
                f"- Approved dispatch channel present: `{approved_dispatch}`.",
                f"- Dispatch ticket/export/license provenance present: `{ticket_export_license_provenance}`.",
                f"- Owner-data env-name indicators present: `{len(env_keys)}`.",
                "",
                "## Decision",
                "",
                packet["decision"],
                "",
                "Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed false; `update_goal=false`.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path.relative_to(REPO)}`",
                f"- Target roots CSV: `{roots_csv.relative_to(REPO)}`",
                f"- Dropzone CSV: `{dropzone_csv.relative_to(REPO)}`",
                f"- Dispatch CSV: `{dispatch_csv.relative_to(REPO)}`",
                f"- Assertions: `{assertions_path.relative_to(REPO)}`",
                "",
                "## Next",
                "",
                packet["next"],
                "",
            ]
        ),
        encoding="utf-8",
    )
    assertions_path.write_text(
        "\n".join(
            [
                f"gate_result={GATE}",
                f"post_083703_dropzone_candidates={len(dropzone_candidates)}",
                f"post_083703_dispatch_candidate_files={len(dispatch_candidates)}",
                f"current_r6_required_package_complete={str(current_r6_complete).lower()}",
                f"legacy_r6_required_package_complete={str(legacy_r6_complete).lower()}",
                f"r5_recency_root_present={str(r5_root_present).lower()}",
                f"r3_native_subhour_root_present={str(r3_root_present).lower()}",
                f"approved_dispatch_channel_present={str(approved_dispatch).lower()}",
                f"dispatch_ticket_export_license_provenance_present={str(ticket_export_license_provenance).lower()}",
                f"owner_data_env_names_present_count={len(env_keys)}",
                f"owner_data_cli_ready={str(assertions['owner_data_cli_ready']).lower()}",
                "valid_required_root_unlock=false",
                "source_control_evidence_acquired=false",
                "canonical_merge=false",
                "selected_data_autoquant_promotion=false",
                "downstream_promotion_rerun=false",
                "strict_full_objective=false",
                "trade_usable=false",
                "promotion_allowed=false",
                "update_goal=false",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
