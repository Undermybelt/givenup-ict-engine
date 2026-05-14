#!/usr/bin/env python3
"""Read back direct Manipulation coverage after recent source screens."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T184630+0800-codex-direct-manipulation-coverage-readback-v2"
RUN_ROOT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T184630-codex-direct-manipulation-coverage-readback-v2"
)
OUT_DIR = RUN_ROOT / "direct-manipulation-readback"
CHECK_DIR = RUN_ROOT / "checks"
OUT_JSON = OUT_DIR / "direct_manipulation_coverage_readback_v2.json"
OUT_MD = OUT_DIR / "direct_manipulation_coverage_readback_v2.md"
OUT_CSV = OUT_DIR / "direct_manipulation_coverage_readback_v2_rows.csv"
OUT_ASSERT = CHECK_DIR / "direct_manipulation_coverage_readback_v2_assertions.out"

VARIETY_MATRIX_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T131311-codex-direct-manipulation-variety-matrix-v1/"
    "direct-manipulation/direct_manipulation_variety_matrix_v1.json"
)
SPOOFING_READINESS_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151720-codex-spoofing-layering-matched-row-readiness-v1/"
    "matched-row-readiness/spoofing_layering_matched_row_readiness_v1.json"
)
WEB_SCREEN_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T184212-codex-direct-manipulation-web-source-screen-v1/"
    "direct-web-source-screen/direct_manipulation_web_source_screen_v1.json"
)
ROW_INTAKE_MANIFEST_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_manifest_v1.json"
)


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rows_from_matrix(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in matrix.get("coverage_matrix", []):
        state = str(item.get("state", ""))
        rows.append(
            {
                "variety": item.get("variety", ""),
                "state": state,
                "accepted_scoped_95": state.startswith("accepted_95"),
                "remaining_gap": item.get("remaining_gap", ""),
                "primary_artifact": item.get("primary_artifact", ""),
            }
        )
    return rows


def write_csv(rows: list[dict[str, Any]]) -> None:
    fields = ["variety", "state", "accepted_scoped_95", "remaining_gap", "primary_artifact"]
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# Direct Manipulation Coverage Readback v2",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This readback merges existing direct `Manipulation` artifacts with the latest web source screen. It does not edit source artifacts or the shared Current Cursor.",
        "",
        "## Decision",
        "",
        f"`{payload['decision']['gate_result']}`",
        "",
        f"- Scoped accepted direct varieties: `{payload['accepted_scoped_variety_count']}`.",
        f"- Remaining unaccepted varieties: `{payload['remaining_unaccepted_variety_count']}`.",
        f"- Web-screen ready real matched-negative candidates: `{payload['web_screen_ready_source_candidate_count']}`.",
        f"- Spoofing/layering matched negatives available: `{payload['spoofing_layering_matched_negative_cases_available']}`.",
        "- Accepted rows added: `0`.",
        "- Full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Coverage Rows",
        "",
        "| Variety | State | Remaining Gap |",
        "|---|---|---|",
    ]
    for row in payload["coverage_rows"]:
        lines.append(
            f"| `{row['variety']}` | `{row['state']}` | {row['remaining_gap']} |"
        )
    lines.extend(
        [
            "",
            "## Readback",
            "",
            "- Existing direct accepted slices remain scoped: Telegram pump/dump, DEX self-trade, DEX consecutive self-trade, BSC wash-maker, and multichain wash-maker.",
            "- Full direct `Manipulation` still fails because spoofing/layering has positive cases but zero matched negatives, and quote stuffing, pinging, bear raid, and painting tape remain missing.",
            "- The latest web/GitHub/arXiv/Kaggle/HF screen adds no real matched-negative source candidate.",
            "- This cannot be promoted into a parent-root or full objective completion claim.",
            "",
            "## Artifacts Used",
            "",
            f"- Variety matrix: `{repo_rel(VARIETY_MATRIX_JSON)}`",
            f"- Spoofing/layering readiness: `{repo_rel(SPOOFING_READINESS_JSON)}`",
            f"- Web source screen: `{repo_rel(WEB_SCREEN_JSON)}`",
            f"- Row intake manifest: `{repo_rel(ROW_INTAKE_MANIFEST_JSON)}`",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    matrix = load_json(VARIETY_MATRIX_JSON)
    spoof = load_json(SPOOFING_READINESS_JSON)
    web = load_json(WEB_SCREEN_JSON)
    intake = load_json(ROW_INTAKE_MANIFEST_JSON)
    coverage_rows = rows_from_matrix(matrix)
    accepted = [row for row in coverage_rows if row["accepted_scoped_95"]]
    remaining = [row for row in coverage_rows if not row["accepted_scoped_95"]]
    payload = {
        "run_id": RUN_ID,
        "artifact_type": "direct_manipulation_coverage_readback_v2",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "current_cursor_edited": False,
        "coverage_rows": coverage_rows,
        "accepted_scoped_variety_count": len(accepted),
        "remaining_unaccepted_variety_count": len(remaining),
        "web_screen_ready_source_candidate_count": web.get("ready_source_candidate_count"),
        "spoofing_layering_matched_negative_cases_available": spoof.get("decision", {}).get("matched_negative_cases_available"),
        "row_intake_gate": intake.get("decision", {}).get("gate_result"),
        "source_artifacts": {
            "variety_matrix": repo_rel(VARIETY_MATRIX_JSON),
            "spoofing_layering_readiness": repo_rel(SPOOFING_READINESS_JSON),
            "web_source_screen": repo_rel(WEB_SCREEN_JSON),
            "row_intake_manifest": repo_rel(ROW_INTAKE_MANIFEST_JSON),
        },
        "decision": {
            "gate_result": "direct_manipulation_coverage_readback_v2=scoped_varieties_present_full_species_blocked",
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "full_direct_manipulation_variety_coverage": False,
            "full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(coverage_rows)
    write_markdown(payload)
    assertions = [
        "PASS accepted_scoped_variety_count=5" if len(accepted) == 5 else "FAIL accepted_scoped_variety_count",
        "PASS remaining_unaccepted_variety_count>=5" if len(remaining) >= 5 else "FAIL remaining_unaccepted_variety_count",
        "PASS web_ready_source_candidate_count=0" if web.get("ready_source_candidate_count") == 0 else "FAIL web_ready_source_candidate_count",
        "PASS spoofing_matched_negative_cases_available=0" if spoof.get("decision", {}).get("matched_negative_cases_available") == 0 else "FAIL spoofing_matched_negative_cases_available",
        "PASS full_objective=false" if not payload["decision"]["full_objective_achieved"] else "FAIL full_objective",
        "PASS current_cursor_edited=false" if not payload["current_cursor_edited"] else "FAIL current_cursor_edited",
    ]
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    if any(line.startswith("FAIL") for line in assertions):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
