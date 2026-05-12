#!/usr/bin/env python3
"""Build a non-sending acquisition outbox v2 after the R6 source uplift."""

import csv
import json
from pathlib import Path


RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs/20260511T204715-codex-source-acquisition-outbox-v2-after-r6-uplift")
OUT_DIR = RUN_ROOT / "source-acquisition-outbox-v2"
CHECK_DIR = RUN_ROOT / "checks"

OUTBOX_V1_CSV = Path(
    "docs/experiments/actionable-regime-confidence/runs/20260511T204131-codex-source-acquisition-outbox-v1/source-acquisition-outbox/source_acquisition_outbox_v1.csv"
)
R6_UPLIFT_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/20260511T204159-codex-r6-bear-raid-painting-tape-source-uplift-v1/r6-source-uplift/r6_bear_raid_painting_tape_source_uplift_v1.json"
)
R6_UPLIFT_CSV = Path(
    "docs/experiments/actionable-regime-confidence/runs/20260511T204159-codex-r6-bear-raid-painting-tape-source-uplift-v1/r6-source-uplift/r6_bear_raid_painting_tape_source_uplift_v1_candidates.csv"
)

DIRECT_ROOT = "/tmp/ict-engine-direct-manipulation-row-intake"
DIRECT_FILES = "positive_spoofing_layering_rows.csv;matched_negative_normal_activity_rows.csv;provenance_manifest.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    outbox_v1 = read_csv(OUTBOX_V1_CSV)
    r6_candidates = read_csv(R6_UPLIFT_CSV)
    r6_payload = json.loads(R6_UPLIFT_JSON.read_text())

    base_rows = [
        row for row in outbox_v1 if row["outbox_id"] != "R6-direct-manipulation-remaining-species"
    ]
    expanded_r6_rows: list[dict[str, object]] = []
    for candidate in r6_candidates:
        species = candidate["species"]
        candidate_id = candidate["candidate_id"]
        expanded_r6_rows.append(
            {
                "outbox_id": f"R6-{species}-{candidate_id}",
                "requirements": "R6",
                "source_artifacts": str(R6_UPLIFT_JSON),
                "primary_contact_surface": candidate["source_url"],
                "required_intake_root": DIRECT_ROOT,
                "required_files": DIRECT_FILES,
                "request_payload": (
                    "Request source-owned row-level positives, same-schema normal controls, "
                    f"timestamps, labels, and provenance for {species}: {candidate['source_title']}"
                ),
                "lead_count": 1,
                "request_sent": False,
                "rows_acquired": False,
                "gate_after_request": "rerun direct_manipulation_row_intake_verifier_v1.py then strict R6 calibration",
                "species": species,
                "candidate_id": candidate_id,
                "source_title": candidate["source_title"],
                "surface_type": candidate["surface_type"],
                "board_a_gate": candidate["board_a_gate"],
                "url_probe_status": candidate["url_probe_status"],
                "url_probe_code": candidate["url_probe_code"],
            }
        )

    rows: list[dict[str, object]] = []
    for row in base_rows:
        out = dict(row)
        out.update(
            {
                "species": "",
                "candidate_id": "",
                "source_title": "",
                "surface_type": "",
                "board_a_gate": "",
                "url_probe_status": "",
                "url_probe_code": "",
            }
        )
        rows.append(out)
    rows.extend(expanded_r6_rows)

    fieldnames = [
        "outbox_id",
        "requirements",
        "source_artifacts",
        "primary_contact_surface",
        "required_intake_root",
        "required_files",
        "request_payload",
        "lead_count",
        "request_sent",
        "rows_acquired",
        "gate_after_request",
        "species",
        "candidate_id",
        "source_title",
        "surface_type",
        "board_a_gate",
        "url_probe_status",
        "url_probe_code",
    ]

    write_csv(OUT_DIR / "source_acquisition_outbox_v2.csv", rows, fieldnames)
    write_csv(
        OUT_DIR / "source_acquisition_outbox_v2_r6_candidate_surfaces.csv",
        expanded_r6_rows,
        fieldnames,
    )

    species_counts: dict[str, int] = {}
    for row in expanded_r6_rows:
        species_counts[str(row["species"])] = species_counts.get(str(row["species"]), 0) + 1

    decision = "source_acquisition_outbox_v2=r6_uplift_merged_rows_not_acquired"
    payload = {
        "decision": decision,
        "inputs": {
            "source_acquisition_outbox_v1_csv": str(OUTBOX_V1_CSV),
            "r6_uplift_json": str(R6_UPLIFT_JSON),
            "r6_uplift_csv": str(R6_UPLIFT_CSV),
        },
        "outbox_v1_rows": len(outbox_v1),
        "r6_candidate_surfaces": len(r6_candidates),
        "v2_outbox_rows": len(rows),
        "expanded_species_counts": species_counts,
        "required_intake_roots": sorted({str(row["required_intake_root"]) for row in rows}),
        "request_sent": False,
        "rows_acquired": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "r6_uplift_decision": r6_payload.get("decision"),
    }
    (OUT_DIR / "source_acquisition_outbox_v2.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )

    report = [
        "# Source Acquisition Outbox v2 After R6 Uplift",
        "",
        f"- Decision: `{decision}`.",
        f"- Input outbox rows: `{len(outbox_v1)}`.",
        f"- R6 candidate surfaces merged: `{len(r6_candidates)}`.",
        f"- V2 outbox rows: `{len(rows)}`.",
        f"- R6 species coverage added: `{', '.join(f'{k}={v}' for k, v in sorted(species_counts.items()))}`.",
        "- Request sent: `false`; rows acquired: `false`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Boundary",
        "",
        "This artifact is still a non-sending acquisition queue. It does not contact owners, use authenticated accounts, download private rows, create intake files, or promote public papers/methods into accepted direct Manipulation evidence.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{OUT_DIR / 'source_acquisition_outbox_v2.json'}`",
        f"- Outbox CSV: `{OUT_DIR / 'source_acquisition_outbox_v2.csv'}`",
        f"- R6 candidate surface CSV: `{OUT_DIR / 'source_acquisition_outbox_v2_r6_candidate_surfaces.csv'}`",
        f"- Assertions: `{CHECK_DIR / 'source_acquisition_outbox_v2_assertions.out'}`",
        "",
    ]
    (OUT_DIR / "source_acquisition_outbox_v2.md").write_text("\n".join(report))

    checks = [
        ("decision", payload["decision"] == decision, decision),
        ("outbox_v1_rows_5", len(outbox_v1) == 5, len(outbox_v1)),
        ("r6_candidate_surfaces_5", len(r6_candidates) == 5, len(r6_candidates)),
        ("v2_outbox_rows_9", len(rows) == 9, len(rows)),
        ("includes_bear_raid", species_counts.get("bear_raid") == 2, species_counts),
        ("includes_painting_tape", species_counts.get("painting_tape") == 3, species_counts),
        ("request_sent_false", payload["request_sent"] is False, payload["request_sent"]),
        ("rows_acquired_false", payload["rows_acquired"] is False, payload["rows_acquired"]),
        ("accepted_rows_added_zero", payload["accepted_rows_added"] == 0, payload["accepted_rows_added"]),
        (
            "strict_full_objective_achieved_false",
            payload["strict_full_objective_achieved"] is False,
            payload["strict_full_objective_achieved"],
        ),
        ("update_goal_false", payload["update_goal"] is False, payload["update_goal"]),
        ("raw_data_committed_false", payload["raw_data_committed"] is False, payload["raw_data_committed"]),
    ]
    CHECK_DIR.joinpath("source_acquisition_outbox_v2_assertions.out").write_text(
        "\n".join(f"{'PASS' if ok else 'FAIL'} {name}={value}" for name, ok, value in checks)
        + "\n"
    )
    if not all(ok for _, ok, _ in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
