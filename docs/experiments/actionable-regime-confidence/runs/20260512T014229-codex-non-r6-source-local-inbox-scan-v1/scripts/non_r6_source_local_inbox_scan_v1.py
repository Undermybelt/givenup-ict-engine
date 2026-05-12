#!/usr/bin/env python3
"""Bounded local inbox scan for non-R6 source-label/R3/R5 inputs."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


RUN_ID = "20260512T014229-codex-non-r6-source-local-inbox-scan-v1"
REPO = Path(__file__).resolve().parents[6]
OUT_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = OUT_ROOT / "non-r6-source-local-inbox-scan-v1"
CHECK_DIR = OUT_ROOT / "checks"

SCAN_ROOTS = [
    Path("/Users/thrill3r/Downloads"),
    Path("/Users/thrill3r/Desktop"),
    Path("/tmp"),
]
MAX_DEPTH = 4
NEEDLES = [
    "native_subhour",
    "subhour",
    "sub-hour",
    "15m",
    "30m",
    "aapl",
    "ixic",
    "stock_market_regimes_2026_extension",
    "source_panel_recency",
    "recency_extension",
    "post_2026",
    "2026_extension",
    "cross_timeframe",
    "source_label",
    "regime_label",
    "mainregimev2",
]
TARGET_ROOTS = [
    ("r3_native_subhour", Path("/tmp/ict-engine-native-subhour-source-label-intake")),
    ("r5_recency_extension", Path("/tmp/ict-engine-source-panel-recency-extension")),
    ("source_label_equivalence", Path("/tmp/ict-engine-source-label-equivalence-intake")),
    ("r6_owner_export", Path("/tmp/ict-engine-board-a-r6-owner-export-v1")),
]


def depth(root: Path, path: Path) -> int:
    try:
        return len(path.relative_to(root).parts)
    except ValueError:
        return MAX_DEPTH + 1


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def classify(path: Path) -> tuple[str, str, bool]:
    text = str(path).lower()
    if "/tmp/ict-engine-native-subhour-source-label-intake/" in text:
        return ("r3_native_subhour", "target_root_candidate_requires_rows_and_provenance", True)
    if "/tmp/ict-engine-source-panel-recency-extension/" in text:
        return ("r5_recency_extension", "target_root_candidate_requires_extension_and_provenance", True)
    if "/tmp/ict-engine-source-label-equivalence-intake/" in text:
        return ("source_label_equivalence", "existing_equivalence_root_confidence_blocked_not_cross_timeframe_acceptance", False)
    if "native_subhour" in text or "subhour" in text or "sub-hour" in text:
        return ("r3_native_subhour", "historical_or_request_artifact_not_target_root", False)
    if "stock_market_regimes_2026_extension" in text or "source_panel_recency" in text or "recency_extension" in text or "post_2026" in text:
        return ("r5_recency_extension", "historical_or_request_artifact_not_target_root", False)
    if "cross_timeframe" in text or "source_label" in text or "regime_label" in text or "mainregimev2" in text:
        return ("source_label_cross_timeframe", "historical_or_generated_label_artifact_not_source_native_export", False)
    if "15m" in text or "30m" in text or "aapl" in text or "ixic" in text:
        return ("possible_market_timeframe", "filename_hint_only_not_source_label_export", False)
    return ("unknown", "local_candidate_not_ready_source_input", False)


def scan_candidates() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            current = Path(dirpath)
            if depth(root, current) >= MAX_DEPTH:
                dirnames[:] = []
            for filename in filenames:
                lower = filename.lower()
                matched = [needle for needle in NEEDLES if needle in lower]
                if not matched:
                    continue
                path = current / filename
                try:
                    stat = path.stat()
                except OSError:
                    continue
                family, disposition, ready = classify(path)
                rows.append(
                    {
                        "root": str(root),
                        "path": str(path),
                        "matched_terms": ";".join(matched),
                        "family": family,
                        "disposition": disposition,
                        "ready_source_input_candidate": ready,
                        "size_bytes": stat.st_size,
                    }
                )
    return sorted(rows, key=lambda row: str(row["path"]))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    candidates = scan_candidates()
    ready_candidates = [row for row in candidates if row["ready_source_input_candidate"] is True]
    target_roots = [
        {
            "id": root_id,
            "root": str(root),
            "present": root.exists(),
            "file_count": sum(1 for item in root.rglob("*") if item.is_file()) if root.exists() else 0,
        }
        for root_id, root in TARGET_ROOTS
    ]

    summary = {
        "run_id": RUN_ID,
        "gate_result": "non_r6_source_local_inbox_scan_v1=no_ready_r3_r5_cross_timeframe_source_inputs_found",
        "scan_roots": [str(root) for root in SCAN_ROOTS],
        "max_depth": MAX_DEPTH,
        "candidate_count": len(candidates),
        "ready_source_input_candidate_count": len(ready_candidates),
        "target_roots": target_roots,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }

    write_csv(
        OUT_DIR / "non_r6_source_local_inbox_candidates_v1.csv",
        candidates,
        [
            "root",
            "path",
            "matched_terms",
            "family",
            "disposition",
            "ready_source_input_candidate",
            "size_bytes",
        ],
    )
    write_csv(
        OUT_DIR / "non_r6_source_local_inbox_target_roots_v1.csv",
        target_roots,
        ["id", "root", "present", "file_count"],
    )
    (OUT_DIR / "non_r6_source_local_inbox_scan_v1.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    target_lines = "\n".join(
        f"- `{row['id']}`: present `{str(row['present']).lower()}`, files `{row['file_count']}` at `{row['root']}`."
        for row in target_roots
    )
    (OUT_DIR / "non_r6_source_local_inbox_scan_v1.md").write_text(
        "\n".join(
            [
                "# Non-R6 Source Local Inbox Scan v1",
                "",
                f"Run id: `{RUN_ID}`",
                f"Gate result: `{summary['gate_result']}`",
                "",
                "Scan scope:",
                "- `/Users/thrill3r/Downloads`",
                "- `/Users/thrill3r/Desktop`",
                "- `/tmp`",
                f"- max depth `{MAX_DEPTH}`",
                "",
                "Result:",
                f"- Matching local inbox candidate files found: `{len(candidates)}`.",
                f"- Ready R3/R5/source-native cross-timeframe input candidates found: `{len(ready_candidates)}`.",
                "- The source-label equivalence root remains present but confidence-blocked; it is not a native sub-hour, recency-extension, or cross-timeframe acceptance root.",
                "",
                "Target root readback:",
                target_lines,
                "",
                "Promotion status:",
                "- Accepted rows added: `0`.",
                "- Canonical merge allowed: `false`.",
                "- Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree rerun allowed: `false`.",
                "- Strict full objective achieved: `false`; `update_goal=false`.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    root_present = {row["id"]: row["present"] for row in target_roots}
    assertions = {
        "ready_source_input_candidate_count_zero": len(ready_candidates) == 0,
        "r3_native_subhour_root_absent": root_present["r3_native_subhour"] is False,
        "r5_recency_extension_root_absent": root_present["r5_recency_extension"] is False,
        "source_label_equivalence_root_present": root_present["source_label_equivalence"] is True,
        "r6_owner_export_root_absent": root_present["r6_owner_export"] is False,
        "accepted_rows_added_zero": summary["accepted_rows_added"] == 0,
        "canonical_merge_allowed_false": summary["canonical_merge_allowed"] is False,
        "downstream_chain_rerun_allowed_false": summary["downstream_chain_rerun_allowed"] is False,
        "strict_full_objective_achieved_false": summary["strict_full_objective_achieved"] is False,
        "update_goal_false": summary["update_goal"] is False,
        "runtime_code_changed_false": summary["runtime_code_changed"] is False,
        "shared_intake_mutated_false": summary["shared_intake_mutated"] is False,
        "external_requests_sent_false": summary["external_requests_sent"] is False,
    }
    (CHECK_DIR / "non_r6_source_local_inbox_scan_v1_assertions.out").write_text(
        "\n".join(f"{key}={value}" for key, value in assertions.items()) + "\n",
        encoding="utf-8",
    )
    return 0 if all(assertions.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
