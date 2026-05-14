#!/usr/bin/env python3
"""Read back the completed TSIE local download without promoting it."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260512T062519+0800-codex-tsie-local-download-rejection-readback-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "tsie-local-download-rejection-readback-v1"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

LOCAL_HF_PARQUET = Path(
    "/tmp/ict-engine-hf-tsie-native-subhour-v1/hf-download/tft_dataset_labeled.parquet"
)
PRIOR_PARQUET = Path(
    "/private/tmp/ict-engine-board-a-tsie-market-regime-dryrun-20260512T0200/0000.parquet"
)
DRYRUN_SUMMARY = Path(
    "/private/tmp/ict-engine-board-a-tsie-market-regime-dryrun-20260512T0200/tsie_dryrun_summary.json"
)
PROVENANCE_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T062201+0800-codex-r3-hf-tsie-provenance-decision-v1/"
    "r3-hf-tsie-provenance-decision-v1/r3_hf_tsie_provenance_decision_v1.json"
)
PRIOR_RECON_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T062253-codex-tsie-prior-evidence-reconciliation-v1/"
    "tsie-prior-evidence-reconciliation/tsie_prior_evidence_reconciliation_v1.json"
)

REQUIRED_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def file_count(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return 1
    return sum(1 for item in path.rglob("*") if item.is_file())


def board_sha256() -> str:
    return hashlib.sha256(BOARD.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    dryrun = load_json(DRYRUN_SUMMARY)
    provenance = load_json(PROVENANCE_JSON)
    prior_recon = load_json(PRIOR_RECON_JSON)

    local_sha = sha256_file(LOCAL_HF_PARQUET)
    prior_sha = sha256_file(PRIOR_PARQUET)
    local_size = LOCAL_HF_PARQUET.stat().st_size if LOCAL_HF_PARQUET.exists() else 0
    prior_size = PRIOR_PARQUET.stat().st_size if PRIOR_PARQUET.exists() else 0

    required_roots = {
        str(root): {"present": root.exists(), "file_count": file_count(root)}
        for root in REQUIRED_ROOTS
    }
    required_roots_absent = all(not item["present"] for item in required_roots.values())

    same_payload = bool(local_sha and prior_sha and local_sha == prior_sha)
    provenance_rejected = (
        provenance.get("gate_result")
        == "r3_hf_tsie_provenance_decision_v1=rejected_rule_based_proxy_labels_no_intake_no_promotion"
    )
    prior_rejected = (
        prior_recon.get("decision")
        == "tsie_prior_evidence_reconciliation_v1=duplicate_candidate_prior_full_data_and_mapping_failures_no_intake"
    )

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": (
            "tsie_local_download_rejection_readback_v1="
            "download_present_same_hash_provenance_rejected_no_intake_no_promotion"
        ),
        "board_sha256_before_artifact": board_sha256(),
        "local_download": {
            "path": str(LOCAL_HF_PARQUET),
            "present": LOCAL_HF_PARQUET.exists(),
            "size_bytes": local_size,
            "sha256": local_sha,
        },
        "prior_private_tmp_download": {
            "path": str(PRIOR_PARQUET),
            "present": PRIOR_PARQUET.exists(),
            "size_bytes": prior_size,
            "sha256": prior_sha,
        },
        "same_payload_as_prior_dryrun": same_payload,
        "dryrun_summary": {
            "num_rows_read": dryrun.get("num_rows_read"),
            "time_min": dryrun.get("time_min"),
            "time_max": dryrun.get("time_max"),
            "unique_group_id": dryrun.get("unique_group_id"),
            "mapped_counts": dryrun.get("mapped_counts"),
            "non_abstain_rows": dryrun.get("non_abstain_rows"),
        },
        "provenance_decision": {
            "path": str(PROVENANCE_JSON.relative_to(REPO)),
            "present": PROVENANCE_JSON.exists(),
            "rejected_rule_based_proxy_labels": provenance_rejected,
            "rejection_reasons": provenance.get("provenance_rejection_reasons", []),
        },
        "prior_evidence_reconciliation": {
            "path": str(PRIOR_RECON_JSON.relative_to(REPO)),
            "present": PRIOR_RECON_JSON.exists(),
            "duplicate_prior_failures": prior_rejected,
        },
        "required_target_roots": required_roots,
        "decision": {
            "accepted_rows_added": 0,
            "source_control_evidence_acquired": False,
            "target_root_mutated": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "assertions": {
            "local_download_present": LOCAL_HF_PARQUET.exists(),
            "same_payload_as_prior_dryrun": same_payload,
            "provenance_rejected": provenance_rejected,
            "prior_rejected": prior_rejected,
            "required_roots_absent": required_roots_absent,
            "target_root_mutated": False,
            "accepted_rows_added": 0,
            "update_goal": False,
        },
        "next_action": (
            "Do not materialize TSIE into the R3 target root. Continue with "
            "owner/source-native R3 labels, R5 recency rows, or R6 owner/export controls."
        ),
    }

    json_path = OUT_DIR / "tsie_local_download_rejection_readback_v1.json"
    md_path = OUT_DIR / "tsie_local_download_rejection_readback_v1.md"
    roots_csv = OUT_DIR / "tsie_local_download_rejection_roots_v1.csv"
    assertions_path = CHECK_DIR / "tsie_local_download_rejection_readback_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_csv(
        roots_csv,
        [
            {
                "root": root,
                "present": item["present"],
                "file_count": item["file_count"],
            }
            for root, item in required_roots.items()
        ],
        ["root", "present", "file_count"],
    )

    md_path.write_text(
        "\n".join(
            [
                "# TSIE Local Download Rejection Readback v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                "Gate result: `"
                + result["gate_result"]
                + "`",
                "",
                "## Scope",
                "",
                "This readback reconciles the completed local Hugging Face CLI download with the Board A TSIE provenance decision. It does not copy rows into `/tmp/ict-engine-native-subhour-source-label-intake`, does not mutate any required target root, does not run canonical merge or downstream promotion, does not make a trade claim, and does not call `update_goal`.",
                "",
                "## Download Readback",
                "",
                f"- Local HF parquet present: `{LOCAL_HF_PARQUET.exists()}`",
                f"- Local HF parquet bytes: `{local_size}`",
                f"- Local HF parquet sha256: `{local_sha}`",
                f"- Matches prior private-tmp dry-run parquet: `{same_payload}`",
                f"- Prior dry-run rows: `{dryrun.get('num_rows_read')}`",
                f"- Prior dry-run groups: `{dryrun.get('unique_group_id')}`",
                f"- Prior dry-run window: `{dryrun.get('time_min')}` to `{dryrun.get('time_max')}`",
                "",
                "## Provenance Decision",
                "",
                f"- 062201 provenance rejected TSIE as rule-based proxy labels: `{provenance_rejected}`",
                f"- 062253 prior-evidence reconciliation blocked the same dataset/commit: `{prior_rejected}`",
                "- TSIE remains useful research metadata, but not source-owned `MainRegimeV2` R3 intake evidence.",
                "",
                "## Required Roots",
                "",
                "| Root | Present | File count |",
                "|---|---:|---:|",
                *[
                    f"| `{root}` | `{item['present']}` | `{item['file_count']}` |"
                    for root, item in required_roots.items()
                ],
                "",
                "## Decision",
                "",
                "- Accepted rows added: `0`.",
                "- Source/control evidence acquired: `false`.",
                "- Target root mutated: `false`.",
                "- Canonical merge: `false`.",
                "- Downstream promotion rerun: `false`.",
                "- Strict full objective: `false`.",
                "- Trade usable: `false`.",
                "- `update_goal=false`.",
                "",
                "## Next",
                "",
                "Do not materialize TSIE into the R3 target root. Continue with owner/source-native R3 labels, R5 recency rows, or R6 owner/export controls before any direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree readback.",
                "",
            ]
        )
    )

    assertions = result["assertions"]
    assertion_lines = [f"{key}={value}" for key, value in assertions.items()]
    assertions_path.write_text("\n".join(assertion_lines) + "\n")

    failed = [key for key, value in assertions.items() if value not in (True, 0, False)]
    hard_failed = [
        key
        for key in [
            "local_download_present",
            "same_payload_as_prior_dryrun",
            "provenance_rejected",
            "prior_rejected",
            "required_roots_absent",
        ]
        if not assertions.get(key)
    ]
    if hard_failed:
        print("ASSERTION_FAILED", ",".join(hard_failed))
        return 1

    print(json.dumps({"run_id": RUN_ID, "gate_result": result["gate_result"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
