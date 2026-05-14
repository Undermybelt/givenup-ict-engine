#!/usr/bin/env python3
"""Board/root readback after 064732 public-source triage."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


RUN_ID = "20260512T065025+0800-codex-board-artifact-link-readback-after-064732-v1"
GATE_RESULT = (
    "board_artifact_link_readback_after_064732_v1="
    "no_valid_unlock_064325_reference_missing_064908_no_recency_no_downstream"
)
SCRIPT = Path(__file__).resolve()
RUN_ROOT = SCRIPT.parents[1]
REPO = SCRIPT.parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUNS_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs"
OUT_DIR = RUN_ROOT / "board-artifact-link-readback-after-064732-v1"
CHECK_DIR = RUN_ROOT / "checks"

REQUIRED_ROOTS = [
    {
        "id": "r6_owner_export",
        "root": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        "required": [
            "direct_manipulation_positive_rows.csv",
            "direct_manipulation_matched_controls.csv",
            "direct_manipulation_provenance.json",
        ],
        "policy": "must be verifier-native owner/export rows with valid controls",
    },
    {
        "id": "r3_native_subhour",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
        "policy": "must be verifier-native MainRegimeV2 labels, not TSIE proxy",
    },
    {
        "id": "r5_recency_extension",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
        "policy": "must be source-owned rows after 2026-01-30",
    },
]

RECENT_REFERENCED_RUNS = [
    "20260512T064230+0800-codex-current-objective-prompt-artifact-audit-after-063926-v1",
    "20260512T064254+0800-codex-source-control-arrival-scan-after-063906-v1",
    "20260512T064259+0800-codex-current-objective-arrival-poll-after-063906-v1",
    "20260512T064309+0800-codex-source-control-arrival-refresh-after-063906-v2",
    "20260512T064315+0800-codex-source-control-gate-refresh-after-r3-postwriter-v1",
    "20260512T064320+0800-codex-source-control-arrival-refresh-after-063906-v2",
    "20260512T064325+0800-codex-source-control-arrival-refresh-after-063906-v2",
    "20260512T064426+0800-codex-r6-local-cfe-sample-control-applicability-v1",
    "20260512T064732+0800-codex-public-regime-source-web-triage-after-064426-v1",
    "20260512T064908+0800-codex-r5-kaggle-stock-regimes-recency-redownload-v1",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"read_error": f"{type(exc).__name__}: {exc}"}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def root_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in REQUIRED_ROOTS:
        root = spec["root"]
        present_files = [name for name in spec["required"] if (root / name).is_file()]
        missing_files = [name for name in spec["required"] if not (root / name).is_file()]
        provenance = {}
        if spec["id"] == "r3_native_subhour":
            provenance = read_json(root / "native_subhour_source_label_provenance.json")
        labels = provenance.get("accepted_mapping_confidence_95_labels", [])
        if not isinstance(labels, list):
            labels = []
        physical_complete = root.exists() and not missing_files
        accepted_for_promotion = False
        notes = []
        if spec["id"] == "r3_native_subhour" and physical_complete:
            notes.append("physical TSIE-derived files present")
            notes.append("policy accepted false")
            if "Crisis" not in labels:
                notes.append("Crisis absent")
        rows.append(
            {
                "id": spec["id"],
                "root": str(root),
                "root_exists": root.exists(),
                "present_files": ";".join(present_files),
                "missing_files": ";".join(missing_files),
                "physical_complete": physical_complete,
                "accepted_for_promotion": accepted_for_promotion,
                "policy": spec["policy"],
                "provenance_run_id": provenance.get("run_id", ""),
                "row_count": provenance.get("row_count", ""),
                "labels": ";".join(labels),
                "notes": "; ".join(notes),
            }
        )
    return rows


def referenced_run_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run_id in RECENT_REFERENCED_RUNS:
        root = RUNS_ROOT / run_id
        json_files = sorted(root.rglob("*.json")) if root.is_dir() else []
        check_files = sorted((root / "checks").glob("*.out")) if root.is_dir() else []
        rows.append(
            {
                "run_id": run_id,
                "path": rel(root),
                "exists": root.is_dir(),
                "json_count": len(json_files),
                "assertion_count": len(check_files),
                "decision": (
                    "missing_referenced_root_do_not_count_as_evidence"
                    if not root.is_dir()
                    else "present"
                ),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    board_hash = sha256_file(BOARD)
    roots = root_rows()
    runs = referenced_run_rows()
    missing_referenced_runs = [row for row in runs if not row["exists"]]
    valid_required_unlock = any(row["accepted_for_promotion"] for row in roots)

    result = {
        "run_id": RUN_ID,
        "gate_result": GATE_RESULT,
        "board_sha256_before_artifact": board_hash,
        "required_roots": roots,
        "referenced_runs": runs,
        "missing_referenced_run_count": len(missing_referenced_runs),
        "missing_referenced_runs": [row["run_id"] for row in missing_referenced_runs],
        "valid_required_root_unlock": valid_required_unlock,
        "accepted_rows_added": 0,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
        "decision": (
            "No valid required root is available. The board currently references "
            "064325 as a source/control refresh v2 run, but no matching run root "
            "exists under docs/experiments or bounded tmp readback, so that "
            "reference must not be counted as evidence. The 064908 R5 Kaggle "
            "redownload root is present and confirms no post-2026-01-30 rows."
        ),
    }

    json_path = OUT_DIR / "board_artifact_link_readback_after_064732_v1.json"
    roots_path = OUT_DIR / "required_root_status_after_064732_v1.csv"
    runs_path = OUT_DIR / "recent_referenced_run_status_after_064732_v1.csv"
    report_path = OUT_DIR / "board_artifact_link_readback_after_064732_v1.md"
    assertions_path = CHECK_DIR / "board_artifact_link_readback_after_064732_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(roots_path, roots)
    write_csv(runs_path, runs)

    report = [
        "# Board Artifact Link Readback After 064732 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE_RESULT}`",
        "",
        f"Board sha256 before artifact: `{board_hash}`",
        "",
        "## Scope",
        "",
        "Read-only Board A continuation readback after the `064732` public-source triage, "
        "the concurrent `064309`/`064320`/`064325` source-control refresh v2 board references, "
        "and the `064908` R5 Kaggle recency redownload that landed before board registration. "
        "This artifact checks required intake roots and recent board-linked run roots only. It "
        "does not mutate `/tmp` roots, approve TSIE, run canonical merge, rerun downstream "
        "promotion, make a trade claim, or call `update_goal`.",
        "",
        "## Required Root Status",
        "",
        "| Root | Exists | Physical Complete | Accepted For Promotion | Notes |",
        "|---|---:|---:|---:|---|",
    ]
    for row in roots:
        report.append(
            f"| `{row['id']}` | `{str(row['root_exists']).lower()}` | "
            f"`{str(row['physical_complete']).lower()}` | "
            f"`{str(row['accepted_for_promotion']).lower()}` | {row['notes'] or row['policy']} |"
        )
    report.extend(
        [
            "",
            "## Referenced Run Link Status",
            "",
            "| Run | Exists | JSON Count | Assertion Count | Decision |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for row in runs:
        report.append(
            f"| `{row['run_id']}` | `{str(row['exists']).lower()}` | "
            f"`{row['json_count']}` | `{row['assertion_count']}` | `{row['decision']}` |"
        )
    report.extend(
        [
            "",
            "## Decision",
            "",
            "No valid required source/control unlock is available. R6 owner/export remains absent, "
            "R5 recency remains absent, and R3 is physically present only as TSIE-derived "
            "non-promoting evidence with no `Crisis` label. The `064908` redownload confirms "
            "the known Kaggle daily source has no rows after `2026-01-30`. The `064325` run "
            "root referenced by the board is not present on disk and must not be counted as evidence.",
            "",
            "Promotion remains blocked: accepted rows added `0`, valid required root unlock false, "
            "source/control evidence acquired false, canonical merge false, downstream promotion "
            "rerun false, strict full objective false, trade usable false, and `update_goal=false`.",
            "",
            "## Next",
            "",
            "Continue only from explicit source/control approval, verifier-native R6 owner-export "
            "rows with valid controls, source-owned R5 recency rows, verifier-native R3 "
            "`MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` "
            "source export before rerunning direct verifier, split calibration, canonical merge, "
            "provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree "
            "readback.",
        ]
    )
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = {
        "gate_result": GATE_RESULT,
        "missing_referenced_run_count": len(missing_referenced_runs),
        "missing_referenced_runs": ",".join(row["run_id"] for row in missing_referenced_runs),
        "valid_required_root_unlock": str(valid_required_unlock).lower(),
        "accepted_rows_added": "0",
        "source_control_evidence_acquired": "false",
        "canonical_merge": "false",
        "downstream_promotion_rerun": "false",
        "strict_full_objective": "false",
        "trade_usable": "false",
        "update_goal": "false",
    }
    assertions_path.write_text(
        "\n".join(f"{key}={value}" for key, value in assertions.items()) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
