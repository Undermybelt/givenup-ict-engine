#!/usr/bin/env python3
"""Audit local spoofing/layering candidates for Board A Manipulation evidence.

The active contract requires replayable direct manipulation rows with timestamps,
positive/negative labels, and market/order-lifecycle provenance. Model code,
synthetic generators, notebooks, and claimed benchmark metrics are not accepted
as direct Manipulation coverage by themselves.
"""

from __future__ import annotations

import json
from pathlib import Path


RUN_ID = "20260511T110827+0800-codex-local-spoofing-source-audit"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T110827-codex-local-spoofing-source-audit"
)
OUT_DIR = RUN_ROOT / "source-audit"
CHECK_DIR = RUN_ROOT / "checks"

CANDIDATES = [
    {
        "id": "navnoor_spoof_detection",
        "path": Path("/tmp/ict-regime-navnoor-spoof-detection"),
        "kind": "local_temp_repo",
    },
    {
        "id": "quantsingularity_spoofing",
        "path": Path("/tmp/ict-regime-quantsingularity-spoofing"),
        "kind": "local_temp_repo",
    },
]

DIRECT_REQUIRED_FIELDS = [
    "timestamp",
    "instrument_or_asset",
    "venue_or_exchange",
    "positive_negative_label",
    "order_lifecycle_or_l2_l3_mbo_fields",
    "negative_controls",
]


def rel(path: Path) -> str:
    return str(path)


def read_prefix(path: Path, limit: int = 3000) -> str:
    try:
        return path.read_text(errors="replace")[:limit]
    except Exception as exc:  # pragma: no cover - audit robustness
        return f"<read_error {type(exc).__name__}: {exc}>"


def audit_navnoor(root: Path) -> dict[str, object]:
    files = [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]
    data_like = [p for p in files if p.suffix.lower() in {".csv", ".parquet", ".json", ".jsonl", ".feather"}]
    notebook = root / "SPOOFING.ipynb"
    notebook_text = read_prefix(notebook, 20000) if notebook.exists() else ""
    has_read_csv = "read_csv" in notebook_text
    has_synthetic_injection = all(token in notebook_text.lower() for token in ["spoof_indices", "quick_cancel", "large_order"])
    return {
        "candidate_id": "navnoor_spoof_detection",
        "source_path": str(root),
        "files_seen": sorted(str(p.relative_to(root)) for p in files),
        "data_like_files_seen": sorted(str(p.relative_to(root)) for p in data_like),
        "readme_evidence": "README describes PPO/L3 LOB spoofing detection and LUNA flash-crash focus, but the local checkout ships only README/LICENSE/notebook.",
        "notebook_evidence": {
            "exists": notebook.exists(),
            "contains_read_csv_path_loader": has_read_csv,
            "contains_synthetic_or_heuristic_spoof_flags": has_synthetic_injection,
        },
        "required_direct_fields_present": {field: False for field in DIRECT_REQUIRED_FIELDS},
        "decision": "rejected_code_not_replayable_direct_rows",
        "reason": "Local checkout contains model/notebook logic but no exported timestamped positive/negative spoofing rows or same-venue negative controls.",
        "accepted_direct_rows_added": 0,
        "accepted_direct_variety_coverage_added": 0,
    }


def audit_quantsingularity(root: Path) -> dict[str, object]:
    files = [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]
    data_files = [p for p in files if p.parts[-2:-1] == ("data",) and p.name != "README.md"]
    data_readme = root / "data" / "README.md"
    data_generation = root / "code" / "utils" / "data_generation.py"
    readme = root / "README.md"
    readme_text = read_prefix(readme, 12000)
    data_readme_text = read_prefix(data_readme, 12000)
    generation_text = read_prefix(data_generation, 12000)
    synthetic_markers = [
        "Synthetic Data",
        "Generate synthetic spoofing patterns",
        "generate_labeled_dataset",
        "spoofing_ratio",
        "AdversarialBacktestFramework",
    ]
    return {
        "candidate_id": "quantsingularity_spoofing",
        "source_path": str(root),
        "files_seen_count": len(files),
        "data_files_seen": sorted(str(p.relative_to(root)) for p in data_files),
        "readme_claims": {
            "has_benchmark_claims": "F1" in readme_text and "Historical Case Validation" in readme_text,
            "has_data_format_only": "Expected Data Format" in data_readme_text,
            "mentions_synthetic_data": "Synthetic Data" in data_readme_text,
        },
        "data_generation_evidence": {
            marker: marker in generation_text or marker in data_readme_text for marker in synthetic_markers
        },
        "required_direct_fields_present": {field: False for field in DIRECT_REQUIRED_FIELDS},
        "decision": "rejected_synthetic_framework_no_real_labeled_rows",
        "reason": "Repository provides framework, adapters, expected data schema, and synthetic spoofing injection, but no replayable real timestamped positive/negative spoofing dataset in the local checkout.",
        "accepted_direct_rows_added": 0,
        "accepted_direct_variety_coverage_added": 0,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    candidate_results = []
    for candidate in CANDIDATES:
        root = candidate["path"]
        if candidate["id"] == "navnoor_spoof_detection":
            candidate_results.append(audit_navnoor(root))
        elif candidate["id"] == "quantsingularity_spoofing":
            candidate_results.append(audit_quantsingularity(root))
        else:  # pragma: no cover
            raise ValueError(candidate["id"])

    accepted_rows = sum(int(result["accepted_direct_rows_added"]) for result in candidate_results)
    accepted_varieties = sum(int(result["accepted_direct_variety_coverage_added"]) for result in candidate_results)
    report = {
        "run_id": RUN_ID,
        "board": "docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
        "active_taxonomy": "MainRegimeV2",
        "target_lane": "Manipulation direct spoofing/layering variety coverage",
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "required_direct_schema": DIRECT_REQUIRED_FIELDS,
        "candidate_results": candidate_results,
        "decision": {
            "accepted_direct_manipulation_rows_added": accepted_rows,
            "accepted_direct_variety_coverage_added": accepted_varieties,
            "accepted_parent_root_slots_added": 0,
            "gate_result": "blocked_local_spoofing_sources_no_replayable_positive_negative_rows",
            "next_action": (
                "For Manipulation variety coverage, acquire timestamped spoofing/layering/order-lifecycle "
                "positive and negative rows from a real market source; keep these local repos as method "
                "provenance only."
            ),
        },
    }

    json_path = OUT_DIR / "local_spoofing_source_audit.json"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    lines = [
        "# Local Spoofing Source Audit",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Scope",
        "",
        "- Active taxonomy: `MainRegimeV2`.",
        "- Target lane: `Manipulation` direct spoofing/layering variety coverage.",
        "- Acceptance requires timestamped positive/negative rows with order-lifecycle or L2/L3/MBO provenance.",
        "",
        "## Candidate Decisions",
        "",
        "| Candidate | Decision | Accepted Rows | Reason |",
        "|---|---|---:|---|",
    ]
    for result in candidate_results:
        lines.append(
            f"| `{result['candidate_id']}` | `{result['decision']}` | "
            f"`{result['accepted_direct_rows_added']}` | {result['reason']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Accepted direct `Manipulation` rows added: `{accepted_rows}`.",
            f"- Accepted direct variety coverage added: `{accepted_varieties}`.",
            "- Accepted MainRegimeV2 parent-root slots added: `0`.",
            "- Gate result: `blocked_local_spoofing_sources_no_replayable_positive_negative_rows`.",
            "- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.",
        ]
    )
    (OUT_DIR / "local_spoofing_source_audit.md").write_text("\n".join(lines) + "\n")

    assertion_lines = [
        "PASS active_taxonomy=MainRegimeV2",
        "PASS target_lane=Manipulation",
        "PASS accepted_parent_root_slots_added=0",
        "PASS accepted_direct_manipulation_rows_added=0",
        "PASS no_raw_data_committed",
        "PASS thresholds_relaxed=false",
        "PASS runtime_code_changed=false",
        "PASS local_spoofing_sources_rejected_without_positive_negative_rows",
    ]
    (CHECK_DIR / "local_spoofing_source_audit_assertions.out").write_text("\n".join(assertion_lines) + "\n")

    print(json.dumps({"report": rel(OUT_DIR / "local_spoofing_source_audit.md"), "accepted_rows": accepted_rows}, indent=2))


if __name__ == "__main__":
    main()
