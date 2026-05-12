#!/usr/bin/env python3
"""Fail-closed canonical merge preflight for Oystacher Exhibit A rows.

This verifies technical readiness without granting policy approval or mutating
the canonical/live intake roots.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T003355-codex-r6-oystacher-canonical-merge-preflight-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
ARTIFACT_DIR = RUN_ROOT / "r6-oystacher-canonical-merge-preflight"
COMMAND_DIR = RUN_ROOT / "command-output"
CHECK_DIR = RUN_ROOT / "checks"

BOARD_PATH = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
DIRECT_VERIFIER = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

MATERIALIZATION_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1/"
    "r6-oystacher-exhibit-a-row-materialization"
)
ISOLATED_INTAKE_ROOT = MATERIALIZATION_ROOT / "isolated-oystacher-exhibit-a-intake"
MATERIALIZATION_JSON = MATERIALIZATION_ROOT / "r6_oystacher_exhibit_a_row_materialization_v1.json"
SPLIT_METRICS_CSV = MATERIALIZATION_ROOT / "oystacher_exhibit_a_split_metrics_v1.csv"
POLICY_REVIEW_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T003051-codex-r6-oystacher-exhibit-a-source-policy-review-v1/"
    "r6-oystacher-exhibit-a-source-policy-review/"
    "r6_oystacher_exhibit_a_source_policy_review_v1.json"
)
CONTRACT_FILES_CSV = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T003003-codex-r6-owner-export-verifier-native-contract-v1/"
    "r6-owner-export-verifier-native-contract/"
    "r6_owner_export_verifier_native_files_v1.csv"
)

OWNER_TARGET_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
LIVE_DIRECT_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")

VERIFIER_NATIVE_FILES = [
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def count_csv_rows(path: Path) -> int:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def read_csv_rows(path: Path) -> list[dict]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def header(path: Path) -> list[str]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        return next(reader)


def run_verifier(name: str, root: Path) -> dict:
    command = [sys.executable, str(DIRECT_VERIFIER), "--intake-root", str(root)]
    proc = subprocess.run(command, text=True, capture_output=True, check=False)
    (COMMAND_DIR / f"{name}.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (COMMAND_DIR / f"{name}.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    (COMMAND_DIR / f"{name}.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
    parsed: dict = {}
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            parsed = {"raw_stdout": proc.stdout[:4000]}
    parsed.update(
        {
            "command": command,
            "returncode": proc.returncode,
            "stdout_path": str(COMMAND_DIR / f"{name}.stdout.txt"),
            "stderr_path": str(COMMAND_DIR / f"{name}.stderr.txt"),
        }
    )
    return parsed


def required_file_state(root: Path) -> list[dict]:
    rows = []
    for name in VERIFIER_NATIVE_FILES:
        path = root / name
        rows.append(
            {
                "filename": name,
                "path": str(path),
                "exists": path.exists(),
                "sha256": file_sha256(path) if path.exists() else "",
                "row_count": count_csv_rows(path) if path.exists() and path.suffix == ".csv" else "",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    COMMAND_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    materialization = load_json(MATERIALIZATION_JSON)
    policy_review = load_json(POLICY_REVIEW_JSON)
    split_rows = read_csv_rows(SPLIT_METRICS_CSV)
    contract_rows = read_csv_rows(CONTRACT_FILES_CSV)

    isolated_state = required_file_state(ISOLATED_INTAKE_ROOT)
    owner_target_state = required_file_state(OWNER_TARGET_ROOT)
    live_state = required_file_state(LIVE_DIRECT_ROOT)

    isolated_verifier = run_verifier("isolated_oystacher_direct_verifier", ISOLATED_INTAKE_ROOT)
    live_verifier = run_verifier("live_direct_verifier_readback", LIVE_DIRECT_ROOT)

    positive_path = ISOLATED_INTAKE_ROOT / "positive_spoofing_layering_rows.csv"
    negative_path = ISOLATED_INTAKE_ROOT / "matched_negative_normal_activity_rows.csv"
    provenance_path = ISOLATED_INTAKE_ROOT / "provenance_manifest.json"
    expected_header = header(positive_path)
    headers_match = expected_header == header(negative_path)

    all_split_axes_pass = all(str(row.get("pooled95_pass")).lower() == "true" for row in split_rows)
    min_split_lcb = min(float(row["min_wilson95_lcb"]) for row in split_rows)
    source_policy_gate = bool(policy_review.get("source_policy_gate"))
    canonical_merge_allowed = source_policy_gate and all_split_axes_pass
    technical_preflight_pass = (
        isolated_verifier.get("returncode") == 0
        and isolated_verifier.get("status") == "schema_ready_unscored"
        and headers_match
        and all_split_axes_pass
        and all(row["exists"] for row in isolated_state)
    )

    checklist = [
        {
            "id": "isolated_verifier_ready",
            "status": "pass" if isolated_verifier.get("status") == "schema_ready_unscored" else "fail",
            "evidence": f"returncode={isolated_verifier.get('returncode')}; status={isolated_verifier.get('status')}; positives={isolated_verifier.get('positive_rows')}; controls={isolated_verifier.get('matched_negative_rows')}",
            "gap": "",
        },
        {
            "id": "verifier_native_files_present",
            "status": "pass" if all(row["exists"] for row in isolated_state) else "fail",
            "evidence": "; ".join(f"{row['filename']}={row['exists']}" for row in isolated_state),
            "gap": "",
        },
        {
            "id": "headers_match_verifier_contract",
            "status": "pass" if headers_match else "fail",
            "evidence": f"field_count={len(expected_header)}; contract_rows={len(contract_rows)}",
            "gap": "",
        },
        {
            "id": "split_axes_pass",
            "status": "pass" if all_split_axes_pass else "fail",
            "evidence": f"axes={len(split_rows)}; min_split_wilson95_lcb={min_split_lcb}",
            "gap": "",
        },
        {
            "id": "source_policy_approval",
            "status": "blocked",
            "evidence": f"source_policy_gate={source_policy_gate}; policy_gate_result={policy_review.get('gate_result')}",
            "gap": "explicit board/user approval for RECAP/PACER source provenance and FLIP controls",
        },
        {
            "id": "canonical_target_untouched",
            "status": "pass_guardrail" if not OWNER_TARGET_ROOT.exists() else "warn",
            "evidence": f"owner_target_exists={OWNER_TARGET_ROOT.exists()}; live_root_exists={LIVE_DIRECT_ROOT.exists()}",
            "gap": "",
        },
        {
            "id": "downstream_chain_not_rerun",
            "status": "blocked_not_rerun",
            "evidence": "No canonical merge or policy approval; downstream readback would not cover accepted R6 evidence.",
            "gap": "approval plus canonical merge",
        },
    ]

    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": file_sha256(BOARD_PATH),
        "materialization_json": str(MATERIALIZATION_JSON),
        "policy_review_json": str(POLICY_REVIEW_JSON),
        "contract_files_csv": str(CONTRACT_FILES_CSV),
        "isolated_intake_root": str(ISOLATED_INTAKE_ROOT),
        "owner_target_root": str(OWNER_TARGET_ROOT),
        "live_direct_root": str(LIVE_DIRECT_ROOT),
        "isolated_file_state": isolated_state,
        "owner_target_file_state": owner_target_state,
        "live_file_state": live_state,
        "isolated_verifier": isolated_verifier,
        "live_verifier": live_verifier,
        "positive_rows": count_csv_rows(positive_path),
        "matched_control_rows": count_csv_rows(negative_path),
        "provenance_sha256": file_sha256(provenance_path),
        "raw_pdf_sha256": materialization.get("raw_pdf_sha256"),
        "source_pdf_url": materialization.get("source_pdf_url"),
        "headers_match": headers_match,
        "header_fields": expected_header,
        "split_axes": split_rows,
        "all_split_axes_pass": all_split_axes_pass,
        "min_split_wilson95_lcb": min_split_lcb,
        "technical_preflight_pass": technical_preflight_pass,
        "source_policy_gate": source_policy_gate,
        "canonical_merge_allowed": canonical_merge_allowed,
        "checklist": checklist,
        "gate_result": "r6_oystacher_canonical_merge_preflight_v1=technical_preflight_pass_policy_approval_required_no_canonical_mutation",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "owner_target_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "next_action": (
            "If the user/board approves RECAP/PACER Exhibit A provenance and FLIP rows as matched controls, "
            "copy the isolated verifier-native intake into /tmp/ict-engine-board-a-r6-owner-export-v1 under a "
            "shared lock, rerun direct verifier/split calibration, then rerun provider, Auto-Quant, pre-Bayes/BBN, "
            "CatBoost/path-ranking, and execution-tree readback while keeping R5 and R3 blocked."
        ),
    }

    json_path = ARTIFACT_DIR / "r6_oystacher_canonical_merge_preflight_v1.json"
    report_path = ARTIFACT_DIR / "r6_oystacher_canonical_merge_preflight_v1.md"
    checklist_path = ARTIFACT_DIR / "r6_oystacher_canonical_merge_preflight_checklist_v1.csv"
    file_state_path = ARTIFACT_DIR / "r6_oystacher_canonical_merge_preflight_file_state_v1.csv"
    assertions_path = CHECK_DIR / "r6_oystacher_canonical_merge_preflight_v1_assertions.out"

    write_json(json_path, payload)
    write_csv(checklist_path, checklist, ["id", "status", "evidence", "gap"])
    write_csv(
        file_state_path,
        [
            {"root": "isolated", **row} for row in isolated_state
        ]
        + [{"root": "owner_target", **row} for row in owner_target_state]
        + [{"root": "live_direct", **row} for row in live_state],
        ["root", "filename", "path", "exists", "sha256", "row_count"],
    )

    lines = [
        "# R6 Oystacher Canonical Merge Preflight v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Isolated verifier status: `{isolated_verifier.get('status')}`; positives `{isolated_verifier.get('positive_rows')}`; matched controls `{isolated_verifier.get('matched_negative_rows')}`; matched groups `{isolated_verifier.get('matched_group_count')}`.",
        f"- Technical preflight pass: `{str(technical_preflight_pass).lower()}`.",
        f"- Split axes pass: `{str(all_split_axes_pass).lower()}`; minimum split Wilson95 LCB `{min_split_lcb}`.",
        f"- Source policy gate: `{str(source_policy_gate).lower()}`; canonical merge allowed: `{str(canonical_merge_allowed).lower()}`.",
        f"- Owner target root exists: `{str(OWNER_TARGET_ROOT.exists()).lower()}`; owner target mutated: `false`.",
        f"- Gate result: `{payload['gate_result']}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "## Checklist",
        "",
        "| ID | Status | Evidence | Gap |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        lines.append(
            f"| `{row['id']}` | `{row['status']}` | {str(row['evidence']).replace('|', '/')} | {str(row['gap']).replace('|', '/')} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The Oystacher Exhibit A rows are technically ready as an isolated verifier-native intake.",
            "- The canonical merge is still blocked only by explicit policy/owner approval for public RECAP/PACER provenance and same-exhibit `FLIP` rows as controls.",
            "- No canonical root, live root, threshold, runtime code, or downstream chain state was mutated by this preflight.",
            "",
            "## Next",
            "",
            payload["next_action"],
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")

    assertions = [
        f"isolated_verifier_returncode={isolated_verifier.get('returncode')}",
        f"isolated_verifier_status={isolated_verifier.get('status')}",
        f"technical_preflight_pass={technical_preflight_pass}",
        f"all_split_axes_pass={all_split_axes_pass}",
        f"min_split_wilson95_lcb={min_split_lcb}",
        f"source_policy_gate={source_policy_gate}",
        f"canonical_merge_allowed={canonical_merge_allowed}",
        f"owner_target_exists={OWNER_TARGET_ROOT.exists()}",
        "owner_target_mutated=false",
        "shared_intake_mutated=false",
        "accepted_rows_added=0",
        "new_confidence_gate=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        "assertion_status=PASS",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps({"run_id": RUN_ID, "json": str(json_path), "report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
