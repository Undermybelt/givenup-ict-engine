#!/usr/bin/env python3
"""Read-only Board A source/control unlock refresh after the 071346 R3 readback."""

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
ARTIFACT_DIR = RUN_ROOT / "source-control-unlock-refresh-after-071346-v1"
CHECKS_DIR = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

RUN_ID = "20260512T071630+0800-codex-source-control-unlock-refresh-after-071346-v1"
GATE = "source_control_unlock_refresh_after_071346_v1=no_required_unlock_no_dispatch_no_downstream"

TARGET_ROOTS = {
    "r6_owner_export": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r5_recency_extension": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "r3_native_subhour": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "source_label_equivalence": Path("/tmp/ict-engine-source-label-equivalence-intake"),
    "r5_kaggle_redownload": Path("/tmp/ict-engine-board-a-r5-kaggle-stock-regimes-recency-redownload-v1"),
}

REQUIRED_R6 = [
    "direct_manipulation_positive_rows.csv",
    "direct_manipulation_matched_controls.csv",
    "direct_manipulation_provenance.json",
]

R3_SETTLED_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T071346+0800-codex-r3-label-count-settled-readback-after-071032-v1/"
    "r3-label-count-settled-readback-after-071032-v1/"
    "r3_label_count_settled_readback_after_071032_v1.json"
)

R6_DEPTH_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T071316+0800-codex-local-order-lifecycle-depth-source-scan-after-070840-v1/"
    "local-order-lifecycle-depth-source-scan-after-070840-v1/"
    "local_order_lifecycle_depth_source_scan_after_070840_v1.json"
)

DISPATCH_ASSETS = [
    REPO / (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T052650-codex-r6-owner-export-v5-dispatch-manifest-v1/"
        "r6-owner-export-v5-dispatch-manifest-v1/"
        "cme_group_owner_export_v5_dispatch_v1.eml"
    ),
    REPO / (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T052650-codex-r6-owner-export-v5-dispatch-manifest-v1/"
        "r6-owner-export-v5-dispatch-manifest-v1/"
        "cboe_cfe_owner_export_v5_dispatch_v1.eml"
    ),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def root_status(root: Path) -> dict:
    files = []
    if root.exists():
        for item in sorted(root.rglob("*")):
            if item.is_file():
                files.append(str(item))
    required_present = [name for name in REQUIRED_R6 if (root / name).is_file()]
    return {
        "root": str(root),
        "exists": root.exists(),
        "file_count": len(files),
        "required_r6_files_present": required_present,
        "accepted_unlock": False,
    }


def dispatch_asset(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    has_from = any(line.lower().startswith("from:") for line in text.splitlines()[:40])
    sent_evidence = "ticket" in text.lower() and "sent evidence" in text.lower()
    return {
        "path": str(path.relative_to(REPO)) if path.exists() else str(path),
        "exists": path.exists(),
        "sha256": sha256_file(path) if path.exists() else None,
        "has_from": has_from,
        "sent_evidence": sent_evidence,
    }


def env_names_present() -> list[str]:
    markers = ("DATABENTO", "CME", "CBOE", "CFE", "KAGGLE", "HF_", "HUGGING", "IBKR", "TRADINGVIEW", "KRAKEN")
    return sorted(k for k in os.environ if any(marker in k for marker in markers))


def tool_paths() -> dict:
    names = ["databento", "dbn", "kaggle", "huggingface-cli", "sendmail", "mail", "msmtp", "mutt", "swaks"]
    return {name: shutil.which(name) for name in names}


def write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    board_sha = sha256_file(BOARD)
    r3 = load_json(R3_SETTLED_JSON)
    r6_depth = load_json(R6_DEPTH_JSON)
    roots = {name: root_status(path) for name, path in TARGET_ROOTS.items()}
    dispatch = [dispatch_asset(path) for path in DISPATCH_ASSETS]
    tools = tool_paths()
    env_keys = env_names_present()

    r6_required_files = roots["r6_owner_export"]["required_r6_files_present"]
    r5_unlock = roots["r5_recency_extension"]["exists"]
    r3_unlock = bool(r3.get("crisis_capable")) and r3.get("source_status") != "tsie_quarantined"
    dispatch_sent = any(item["sent_evidence"] for item in dispatch)
    owner_data_cli_ready = bool(tools["databento"] or tools["dbn"])
    owner_data_env_ready = any("DATABENTO" in key or "CME" in key or "CBOE" in key or "CFE" in key for key in env_keys)

    assertions = {
        "r6_required_files_present_count": len(r6_required_files),
        "r6_owner_export_unlock": False,
        "r5_recency_unlock": False,
        "r3_native_subhour_unlock": False,
        "r3_crisis_rows": r3.get("crisis_rows"),
        "r3_source_status": r3.get("source_status"),
        "r6_depth_or_order_lifecycle_files_found": r6_depth.get("local_scan", {}).get("depth_or_order_lifecycle_data_files_found"),
        "dispatch_sent_evidence": dispatch_sent,
        "owner_data_cli_ready": owner_data_cli_ready,
        "owner_data_env_ready": owner_data_env_ready,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    packet = {
        "run_id": RUN_ID,
        "generated_at_local": datetime.now(timezone(timedelta(hours=8))).isoformat(),
        "board_sha256_before_artifact": board_sha,
        "gate_result": GATE,
        "scope": {
            "mode": "read_only_unlock_refresh_after_071346",
            "no_root_mutation": True,
            "no_dispatch": True,
            "no_canonical_merge": True,
            "no_downstream_promotion": True,
            "update_goal": False,
        },
        "inputs": {
            "r3_settled_readback_json": str(R3_SETTLED_JSON.relative_to(REPO)),
            "r6_depth_scan_json": str(R6_DEPTH_JSON.relative_to(REPO)),
            "dispatch_assets_checked": [str(path.relative_to(REPO)) for path in DISPATCH_ASSETS],
        },
        "target_roots": roots,
        "dispatch_assets": dispatch,
        "tool_paths": tools,
        "env_keys_present_without_values": env_keys,
        "assertions": assertions,
        "decision": (
            "No fresh Board A source/control unlock appeared after the 071346 R3 readback. "
            "R6 required files remain absent, R5 recency root remains absent, R3 remains "
            "TSIE-quarantined and Crisis-absent, v5 dispatch assets remain drafts without "
            "sent/ticket/export evidence, and no owner-data CLI/env path is ready in this shell."
        ),
        "next": (
            "Continue only from explicit source/control approval, verifier-native R6 owner-export "
            "rows with valid controls, source-owned post-2026-01-30 R5 rows matching the source-panel "
            "schema, verifier-native Crisis-capable R3 MainRegimeV2 labels, or a genuinely new accepted "
            "cross-timeframe MainRegimeV2 source export. After that, rerun the ordered chain."
        ),
    }

    json_path = ARTIFACT_DIR / "source_control_unlock_refresh_after_071346_v1.json"
    csv_path = ARTIFACT_DIR / "source_control_unlock_refresh_after_071346_v1.csv"
    md_path = ARTIFACT_DIR / "source_control_unlock_refresh_after_071346_v1.md"
    assertions_path = CHECKS_DIR / "source_control_unlock_refresh_after_071346_v1_assertions.out"

    json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        csv_path,
        [
            {
                "check": key,
                "value": value,
            }
            for key, value in assertions.items()
        ],
    )
    md_path.write_text(
        "\n".join(
            [
                "# Source/Control Unlock Refresh After 071346 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{GATE}`",
                "",
                "## Scope",
                "",
                "Read-only refresh after the `071316` local depth/order-lifecycle scan and the `071346` settled R3 label-count readback. This packet does not mutate R3/R5/R6 roots, send dispatch drafts, approve TSIE, approve FLIP controls, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Readback",
                "",
                f"- Board SHA-256 before artifact: `{board_sha}`.",
                f"- R6 required owner-export files present: `{len(r6_required_files)}`.",
                f"- R5 recency root exists: `{r5_unlock}`.",
                f"- R3 source status: `{r3.get('source_status')}`; data rows `{r3.get('data_rows')}`; Crisis rows `{r3.get('crisis_rows')}`.",
                f"- Local depth/order-lifecycle data files found by `071316`: `{r6_depth.get('local_scan', {}).get('depth_or_order_lifecycle_data_files_found')}`.",
                f"- Dispatch sent evidence: `{dispatch_sent}`.",
                f"- Owner-data CLI ready: `{owner_data_cli_ready}`; owner-data env key present: `{owner_data_env_ready}`.",
                "",
                "## Decision",
                "",
                packet["decision"],
                "",
                "Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path.relative_to(REPO)}`",
                f"- CSV: `{csv_path.relative_to(REPO)}`",
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
                f"r6_required_files_present_count={len(r6_required_files)}",
                "r6_owner_export_unlock=false",
                "r5_recency_unlock=false",
                "r3_native_subhour_unlock=false",
                f"r3_crisis_rows={r3.get('crisis_rows')}",
                f"r3_source_status={r3.get('source_status')}",
                f"dispatch_sent_evidence={str(dispatch_sent).lower()}",
                f"owner_data_cli_ready={str(owner_data_cli_ready).lower()}",
                f"owner_data_env_ready={str(owner_data_env_ready).lower()}",
                "valid_required_root_unlock=false",
                "source_control_evidence_acquired=false",
                "canonical_merge=false",
                "downstream_promotion_rerun=false",
                "strict_full_objective=false",
                "trade_usable=false",
                "update_goal=false",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
