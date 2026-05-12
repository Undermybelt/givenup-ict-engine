#!/usr/bin/env python3
"""Post-request intake arrival and recent board-reference integrity readback."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T010906-codex-post-request-intake-arrival-and-ref-integrity-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT = RUN_ROOT / "post-request-intake-arrival-and-ref-integrity-v1"
CHECKS = RUN_ROOT / "checks"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
RUNS_ROOT = Path("docs/experiments/actionable-regime-confidence/runs")

RECENT_RUN_IDS = [
    "20260512T010127-codex-r6-owner-route-entitlement-readback-v1",
    "20260512T005913-codex-r6-owner-export-sendable-requests-v3",
    "20260512T010201-codex-non-r6-source-intake-outbound-request-messages-v1",
    "20260512T010212-codex-r6-owner-export-access-route-preflight-v1",
    "20260512T010506-codex-r6-owner-export-official-contact-route-check-v1",
]

INTAKE_ROOTS = [
    {
        "id": "r6_owner_export",
        "root": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        "required": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
    },
    {
        "id": "source_label_equivalence",
        "root": Path("/tmp/ict-engine-source-label-equivalence-intake"),
        "required": [
            "source_label_equivalence_rows.csv",
            "source_label_equivalence_provenance.json",
        ],
    },
    {
        "id": "r3_native_subhour",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
    },
    {
        "id": "r5_source_panel_recency",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
    },
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_rows(path: Path) -> int:
    if path.suffix.lower() != ".csv" or not path.exists():
        return 0
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return max(sum(1 for _ in csv.reader(handle)) - 1, 0)


def root_status() -> list[dict[str, object]]:
    rows = []
    for item in INTAKE_ROOTS:
        root = item["root"]
        for required in item["required"]:
            path = root / required
            exists = path.exists()
            rows.append(
                {
                    "root_id": item["id"],
                    "root": str(root),
                    "required_file": required,
                    "path": str(path),
                    "root_exists": root.exists(),
                    "file_exists": exists,
                    "size_bytes": path.stat().st_size if exists else 0,
                    "sha256": sha256_file(path) if exists and path.is_file() else "",
                    "csv_rows": csv_rows(path) if exists else 0,
                }
            )
    return rows


def recent_ref_status() -> list[dict[str, object]]:
    rows = []
    for run_id in RECENT_RUN_IDS:
        root = RUNS_ROOT / run_id
        exists = root.exists()
        file_count = 0
        if exists:
            file_count = sum(1 for path in root.iterdir() if path.is_file())
        rows.append(
            {
                "run_id": run_id,
                "root": str(root),
                "exists": exists,
                "file_count": file_count,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def source_label_verifier_payload() -> dict[str, object]:
    stdout_path = RUN_ROOT / "command-output/source_label_equivalence_verifier.stdout.txt"
    exit_path = RUN_ROOT / "command-output/source_label_equivalence_verifier.exit"
    if not stdout_path.exists():
        return {"status": "not_run", "return_code": ""}
    try:
        payload = json.loads(stdout_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = {"status": "stdout_not_json"}
    payload["return_code"] = exit_path.read_text(encoding="utf-8").strip() if exit_path.exists() else ""
    return payload


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    roots = root_status()
    refs = recent_ref_status()
    hits = [
        {
            "required_file": row["required_file"],
            "path": row["path"],
            "size_bytes": row["size_bytes"],
            "sha256": row["sha256"],
            "csv_rows": row["csv_rows"],
        }
        for row in roots
        if row["file_exists"]
    ]

    required_present = sum(1 for row in roots if row["file_exists"])
    required_total = len(roots)
    broken_refs = [row for row in refs if not row["exists"]]
    exact_hits = len(hits)
    source_rows_present = sum(int(row["csv_rows"]) for row in roots if row["file_exists"])
    verifier_payload = source_label_verifier_payload()
    gate = (
        "post_request_intake_arrival_and_ref_integrity_v1="
        "partial_intake_files_present_schema_ready_no_confidence_no_promotion"
        if required_present
        else "post_request_intake_arrival_and_ref_integrity_v1="
        "no_intake_files_present_no_promotion"
    )

    write_csv(
        OUT / "post_request_intake_required_file_status_v1.csv",
        roots,
        [
            "root_id",
            "root",
            "required_file",
            "path",
            "root_exists",
            "file_exists",
            "size_bytes",
            "sha256",
            "csv_rows",
        ],
    )
    write_csv(
        OUT / "post_request_recent_board_reference_status_v1.csv",
        refs,
        ["run_id", "root", "exists", "file_count"],
    )
    write_csv(
        OUT / "post_request_required_file_name_hits_v1.csv",
        hits,
        ["required_file", "path", "size_bytes", "sha256", "csv_rows"],
    )

    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256_file(BOARD),
        "gate_result": gate,
        "required_files_present": required_present,
        "required_files_total": required_total,
        "required_file_name_hits": exact_hits,
        "source_rows_present": source_rows_present,
        "source_label_equivalence_verifier_status": verifier_payload.get("status"),
        "source_label_equivalence_verifier_return_code": verifier_payload.get("return_code"),
        "recent_run_refs_checked": len(refs),
        "broken_recent_run_refs": len(broken_refs),
        "broken_recent_run_ids": [row["run_id"] for row in broken_refs],
        "external_requests_sent": False,
        "source_rows_acquired": 0,
        "accepted_rows_added": 0,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }
    (OUT / "post_request_intake_arrival_and_ref_integrity_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Post-Request Intake Arrival and Reference Integrity v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Gate result: `{gate}`.",
        f"- Required intake files present: `{required_present}/{required_total}`.",
        f"- Exact target-root required-file hits: `{exact_hits}`.",
        f"- Source rows present in arrived files: `{source_rows_present}`.",
        f"- Source-label equivalence verifier: `{verifier_payload.get('status')}` return code `{verifier_payload.get('return_code')}`.",
        f"- Recent board run references checked: `{len(refs)}`; broken refs: `{len(broken_refs)}`.",
        f"- Broken recent run ids: `{', '.join(row['run_id'] for row in broken_refs) if broken_refs else 'none'}`.",
        "- External requests sent: false; source rows acquired: `0`; accepted rows added: `0`.",
        "- Canonical merge allowed: false; downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun allowed: false.",
        "- Strict full objective achieved: false. `update_goal=false`.",
        "- Runtime code changed: false. Shared intake mutated: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.",
        "",
        "## Boundary",
        "",
        "This readback is presence/integrity evidence only. It does not create, copy, repair, or promote any intake files.",
        "",
        "## Next",
        "",
        "Acquire or approve the exact source-owned R6/non-R6 files, then rerun the fail-closed verifiers in Board A order. The missing recent board reference should be repaired by the owner of that artifact or superseded by a present replacement before relying on it.",
    ]
    (OUT / "post_request_intake_arrival_and_ref_integrity_v1.md").write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )

    assertions = [
        f"run_id={RUN_ID}",
        f"gate_result={gate}",
        f"required_files_present={required_present}",
        f"required_files_total={required_total}",
        f"required_file_name_hits={exact_hits}",
        f"source_rows_present={source_rows_present}",
        f"source_label_equivalence_verifier_status={verifier_payload.get('status')}",
        f"source_label_equivalence_verifier_return_code={verifier_payload.get('return_code')}",
        f"broken_recent_run_refs={len(broken_refs)}",
        "external_requests_sent=false",
        "source_rows_acquired=0",
        "accepted_rows_added=0",
        "canonical_merge_allowed=false",
        "downstream_chain_rerun_allowed=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
    ]
    (CHECKS / "post_request_intake_arrival_and_ref_integrity_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
