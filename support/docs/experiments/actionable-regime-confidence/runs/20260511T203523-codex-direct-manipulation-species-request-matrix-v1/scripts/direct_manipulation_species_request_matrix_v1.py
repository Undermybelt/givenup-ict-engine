#!/usr/bin/env python3
"""Build a fail-closed request matrix for remaining direct Manipulation species."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T203523-codex-direct-manipulation-species-request-matrix-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = RUN_ROOT / "direct-manipulation-species-request-matrix"
CHECK_DIR = RUN_ROOT / "checks"

SOURCE_SCREEN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T191642-codex-direct-missing-species-source-screen-v2/direct-missing-species-screen"
)
SOURCE_SCREEN_JSON = SOURCE_SCREEN_ROOT / "direct_missing_species_source_screen_v2.json"
SOURCE_SCREEN_CANDIDATES = SOURCE_SCREEN_ROOT / "direct_missing_species_source_screen_v2_candidates.csv"

CURRENT_INTAKE_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
CURRENT_REQUIRED_FILES = [
    CURRENT_INTAKE_ROOT / "positive_spoofing_layering_rows.csv",
    CURRENT_INTAKE_ROOT / "matched_negative_normal_activity_rows.csv",
    CURRENT_INTAKE_ROOT / "provenance_manifest.json",
]

TARGET_SPECIES = [
    "spoofing_layering",
    "quote_spoofing",
    "quote_stuffing",
    "pinging",
    "bear_raid",
    "painting_tape",
]

REQUIRED_FIELDS = [
    "source_row_id",
    "source_name",
    "owner_or_licensor",
    "species",
    "positive_or_control",
    "symbol",
    "venue_or_market_center",
    "trade_date",
    "session_bucket",
    "event_start_ts_utc",
    "event_end_ts_utc",
    "order_or_message_count",
    "quantity_or_notional",
    "activity_description",
    "matched_negative_group_id",
    "provenance_url_or_path",
    "source_version_hash",
    "license_or_permission",
    "forbidden_proxy_flag",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def split_species(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def build_species_matrix(candidates: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    candidate_species: set[str] = set()
    for candidate in candidates:
        species_list = split_species(candidate.get("species", ""))
        candidate_species.update(species_list)
        for species in species_list:
            rows.append(
                {
                    "species": species,
                    "source_family": candidate.get("source_family", ""),
                    "ref": candidate.get("ref", ""),
                    "url": candidate.get("url", ""),
                    "row_surface": candidate.get("row_surface", ""),
                    "candidate_disposition": candidate.get("disposition", ""),
                    "real_market_rows": candidate.get("real_market_rows", ""),
                    "explicit_positive_labels": candidate.get("explicit_positive_labels", ""),
                    "matched_negative_controls": candidate.get("matched_negative_controls", ""),
                    "provenance_rows": candidate.get("provenance_rows", ""),
                    "request_positive_rows": "yes",
                    "request_matched_controls": "yes",
                    "request_provenance_manifest": "yes",
                    "current_acceptance_state": "blocked_rows_not_acquired",
                    "required_next_artifact": "source_owned_positive_rows_plus_matched_controls_plus_provenance",
                    "notes": candidate.get("incremental_note", ""),
                }
            )

    for species in TARGET_SPECIES:
        if species in candidate_species:
            continue
        rows.append(
            {
                "species": species,
                "source_family": "no_candidate_in_v2_screen",
                "ref": "",
                "url": "",
                "row_surface": "",
                "candidate_disposition": "blocked_no_candidate_source_surface",
                "real_market_rows": "False",
                "explicit_positive_labels": "False",
                "matched_negative_controls": "False",
                "provenance_rows": "False",
                "request_positive_rows": "yes",
                "request_matched_controls": "yes",
                "request_provenance_manifest": "yes",
                "current_acceptance_state": "blocked_no_source_surface",
                "required_next_artifact": "identify_source_owner_then_acquire_positive_control_rows",
                "notes": "No source surface was retained by v2 for this required direct Manipulation species.",
            }
        )
    rows.sort(key=lambda row: (str(row["species"]), str(row["source_family"]), str(row["ref"])))
    return rows


def build_species_summary(matrix: list[dict[str, object]]) -> list[dict[str, object]]:
    summary: dict[str, dict[str, object]] = {}
    for row in matrix:
        species = str(row["species"])
        item = summary.setdefault(
            species,
            {
                "species": species,
                "candidate_surfaces": 0,
                "ready_positive_control_sources": 0,
                "has_explicit_positive_label_surface": False,
                "has_matched_control_surface": False,
                "has_provenance_surface": False,
                "gate_state": "blocked",
            },
        )
        if row["source_family"] != "no_candidate_in_v2_screen":
            item["candidate_surfaces"] = int(item["candidate_surfaces"]) + 1
        if str(row["explicit_positive_labels"]).lower() == "true":
            item["has_explicit_positive_label_surface"] = True
        if str(row["matched_negative_controls"]).lower() == "true":
            item["has_matched_control_surface"] = True
        if str(row["provenance_rows"]).lower() == "true":
            item["has_provenance_surface"] = True
    return [summary[species] for species in TARGET_SPECIES]


def write_report(payload: dict[str, object], summary: list[dict[str, object]]) -> None:
    lines = [
        "# Direct Manipulation Species Request Matrix v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        f"- Gate result: `{payload['decision']}`.",
        "- Purpose: convert the remaining direct Manipulation species blocker into an owner/export request matrix without promoting raw LOB, paper, method, or library surfaces.",
        f"- Candidate rows consumed: `{payload['candidate_count']}`.",
        f"- Matrix rows written: `{payload['matrix_row_count']}`.",
        f"- Target species: `{', '.join(TARGET_SPECIES)}`.",
        f"- Current intake root: `{CURRENT_INTAKE_ROOT}`.",
        f"- Accepted rows added: `{payload['accepted_rows_added']}`; new confidence gate: `{str(payload['new_confidence_gate']).lower()}`.",
        f"- Strict full objective achieved: `{str(payload['strict_full_objective_achieved']).lower()}`; `update_goal={str(payload['update_goal']).lower()}`.",
        "",
        "## Species Summary",
        "",
        "| Species | Candidate surfaces | Positive surface | Matched controls | Provenance surface | Gate |",
        "|---|---:|---|---|---|---|",
    ]
    for row in summary:
        lines.append(
            f"| `{row['species']}` | `{row['candidate_surfaces']}` | `{str(row['has_explicit_positive_label_surface']).lower()}` | `{str(row['has_matched_control_surface']).lower()}` | `{str(row['has_provenance_surface']).lower()}` | `{row['gate_state']}` |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This run does not send requests, create intake rows, change verifiers, or claim direct `Manipulation` completion.",
            "- Raw order-book providers can support controls or future probes, but cannot satisfy Board A without source-owned positive labels and matched controls.",
            "- Paper/method/library surfaces remain provenance for request language only.",
            "",
            "## Artifacts",
            "",
            "- JSON: `direct_manipulation_species_request_matrix_v1.json`",
            "- Matrix CSV: `direct_manipulation_species_request_matrix_v1.csv`",
            "- Species summary CSV: `direct_manipulation_species_summary_v1.csv`",
            "- Required fields CSV: `direct_manipulation_species_required_fields_v1.csv`",
            "- Request template: `direct_manipulation_species_request_template_v1.md`",
            "- Assertions: `../checks/direct_manipulation_species_request_matrix_v1_assertions.out`",
            "",
        ]
    )
    (OUT_DIR / "direct_manipulation_species_request_matrix_v1.md").write_text("\n".join(lines))


def write_template() -> None:
    lines = [
        "# Direct Manipulation Species Row Request Template v1",
        "",
        "We need source-owned or owner-approved direct market-manipulation rows for strict regime-confidence validation.",
        "",
        "Required species:",
    ]
    lines.extend(f"- {species}" for species in TARGET_SPECIES)
    lines.extend(
        [
            "",
            "Required row package:",
            "- Positive manipulation rows for each species.",
            "- Matched same-schema normal-activity controls.",
            "- Provenance manifest with source owner, license or permission, source version, venue, symbol, date/session, and row ids.",
            "",
            "Current direct-intake verifier still requires:",
        ]
    )
    lines.extend(f"- `{path}`" for path in CURRENT_REQUIRED_FILES)
    lines.extend(
        [
            "",
            "Forbidden:",
            "- Generated, simulated, synthetic, future-return, classifier, or OHLCV-only labels.",
            "- Raw order-book data without source-owned positive labels.",
            "- Paper/method/library evidence without replayable positive and matched-control rows.",
            "",
        ]
    )
    (OUT_DIR / "direct_manipulation_species_request_template_v1.md").write_text("\n".join(lines))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    source_screen = load_json(SOURCE_SCREEN_JSON)
    candidates = read_csv(SOURCE_SCREEN_CANDIDATES)
    matrix = build_species_matrix(candidates)
    summary = build_species_summary(matrix)

    matrix_fields = [
        "species",
        "source_family",
        "ref",
        "url",
        "row_surface",
        "candidate_disposition",
        "real_market_rows",
        "explicit_positive_labels",
        "matched_negative_controls",
        "provenance_rows",
        "request_positive_rows",
        "request_matched_controls",
        "request_provenance_manifest",
        "current_acceptance_state",
        "required_next_artifact",
        "notes",
    ]
    write_csv(OUT_DIR / "direct_manipulation_species_request_matrix_v1.csv", matrix, matrix_fields)
    write_csv(
        OUT_DIR / "direct_manipulation_species_summary_v1.csv",
        summary,
        [
            "species",
            "candidate_surfaces",
            "ready_positive_control_sources",
            "has_explicit_positive_label_surface",
            "has_matched_control_surface",
            "has_provenance_surface",
            "gate_state",
        ],
    )
    write_csv(
        OUT_DIR / "direct_manipulation_species_required_fields_v1.csv",
        [{"field": field, "required": True} for field in REQUIRED_FIELDS],
        ["field", "required"],
    )
    write_template()

    candidate_species = sorted({row["species"] for row in matrix if row["source_family"] != "no_candidate_in_v2_screen"})
    no_candidate_species = sorted({row["species"] for row in matrix if row["source_family"] == "no_candidate_in_v2_screen"})
    payload: dict[str, object] = {
        "run_id": RUN_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decision": "direct_manipulation_species_request_matrix_v1=request_ready_rows_not_acquired",
        "input_source_screen_json": str(SOURCE_SCREEN_JSON),
        "input_source_screen_candidates": str(SOURCE_SCREEN_CANDIDATES),
        "source_screen_decision": source_screen.get("decision", {}),
        "candidate_count": len(candidates),
        "matrix_row_count": len(matrix),
        "target_species": TARGET_SPECIES,
        "candidate_species": candidate_species,
        "no_candidate_species": no_candidate_species,
        "current_required_intake_files": [str(path) for path in CURRENT_REQUIRED_FILES],
        "required_field_count": len(REQUIRED_FIELDS),
        "request_sent": False,
        "rows_acquired": False,
        "direct_manipulation_intake_files_created": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "r6_direct_species_closed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }
    (OUT_DIR / "direct_manipulation_species_request_matrix_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    write_report(payload, summary)

    assertions = [
        ("source_screen_json_present", SOURCE_SCREEN_JSON.exists()),
        ("source_screen_candidates_present", SOURCE_SCREEN_CANDIDATES.exists()),
        ("candidate_count_7", len(candidates) == 7),
        ("target_species_count_6", len(TARGET_SPECIES) == 6),
        ("matrix_rows_ge_target_species", len(matrix) >= len(TARGET_SPECIES)),
        ("has_quote_stuffing", "quote_stuffing" in {row["species"] for row in matrix}),
        ("has_pinging", "pinging" in {row["species"] for row in matrix}),
        ("has_bear_raid_no_candidate", "bear_raid" in no_candidate_species),
        ("has_painting_tape_no_candidate", "painting_tape" in no_candidate_species),
        ("rows_acquired_false", payload["rows_acquired"] is False),
        ("accepted_rows_added_zero", payload["accepted_rows_added"] == 0),
        ("r6_closed_false", payload["r6_direct_species_closed"] is False),
        ("strict_full_objective_achieved_false", payload["strict_full_objective_achieved"] is False),
        ("update_goal_false", payload["update_goal"] is False),
        ("raw_data_committed_false", payload["raw_data_committed"] is False),
    ]
    failed = [name for name, ok in assertions if not ok]
    (CHECK_DIR / "direct_manipulation_species_request_matrix_v1_assertions.out").write_text(
        "\n".join(f"{name}=PASS" if ok else f"{name}=FAIL" for name, ok in assertions)
        + "\n"
    )
    if failed:
        raise SystemExit(f"failed assertions: {', '.join(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
