#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T063734+0800-codex-r3-tsie-target-root-failclose-after-063155-v1"
SLUG = "r3-tsie-target-root-failclose-after-063155-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

TARGET_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
R6_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
R5_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
EQUIV_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")

RUN_063155 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T063155+0800-codex-r3-tsie-native-subhour-intake-materialization-v1"
RUN_062902 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T062902+0800-codex-r3-hf-tsie-native-intraday-intake-v1"
RUN_063215 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T063215+0800-codex-r3-tsie-native-intraday-materializer-preflight-v1"


def sha256_file(path: Path, *, max_bytes: int | None = None) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        remaining = max_bytes
        while True:
            if remaining is None:
                chunk = handle.read(1024 * 1024)
            elif remaining <= 0:
                break
            else:
                chunk = handle.read(min(1024 * 1024, remaining))
                remaining -= len(chunk)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"missing": True, "path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path, limit: int = 20000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[:limit]


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def run_ps_snapshot() -> str:
    proc = subprocess.run(
        ["ps", "-axo", "pid,ppid,stat,etime,%cpu,%mem,command"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    needles = (
        "062902",
        "063155",
        "063217",
        "native-subhour",
        "source-label-intake",
        "public_source_candidate",
        "target/debug/ict-engine",
        "auto-quant",
        "catboost",
        "pre-bayes",
        "bbn",
        "execution-tree",
    )
    lines = [line for line in proc.stdout.splitlines() if any(needle in line for needle in needles)]
    return "\n".join(lines) + ("\n" if lines else "")


def root_status(path: Path, name: str) -> dict[str, Any]:
    files = []
    if path.exists():
        for file_path in sorted(path.rglob("*")):
            if file_path.is_file():
                stat = file_path.stat()
                item = {
                    "path": str(file_path),
                    "name": file_path.name,
                    "size_bytes": stat.st_size,
                    "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                }
                if stat.st_size <= 10_000_000:
                    item["sha256"] = sha256_file(file_path)
                files.append(item)
    return {
        "root_name": name,
        "path": str(path),
        "exists": path.exists(),
        "file_count": len(files),
        "files": files,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)

    process_snapshot = run_ps_snapshot()
    (CMD_OUT / "process_snapshot.txt").write_text(process_snapshot, encoding="utf-8")

    board_hash = sha256_file(BOARD)
    target_provenance = load_json(TARGET_ROOT / "native_subhour_source_label_provenance.json")
    materializer_json = load_json(
        RUN_063155
        / "r3-tsie-native-subhour-intake-materialization-v1"
        / "r3_tsie_native_subhour_intake_materialization_v1.json"
    )
    materializer_assertions = read_text(
        RUN_063155 / "checks" / "r3_tsie_native_subhour_intake_materialization_v1_assertions.out"
    )
    preflight_json = load_json(
        RUN_063215
        / "r3-tsie-native-intraday-materializer-preflight-v1"
        / "r3_tsie_native_intraday_materializer_preflight_v1.json"
    )
    intraday_stdout = read_text(
        RUN_062902 / "command-output" / "r3_hf_tsie_native_intraday_intake_v1.stdout.txt"
    )
    intraday_stderr = read_text(
        RUN_062902 / "command-output" / "r3_hf_tsie_native_intraday_intake_v1.stderr.txt"
    )
    intraday_exit = read_text(RUN_062902 / "command-output" / "r3_hf_tsie_native_intraday_intake_v1.exit")

    root_statuses = [
        root_status(R6_ROOT, "r6_owner_export"),
        root_status(TARGET_ROOT, "r3_native_subhour"),
        root_status(R5_ROOT, "r5_source_panel_recency"),
        root_status(EQUIV_ROOT, "source_label_equivalence_non_target"),
    ]

    rows_file = TARGET_ROOT / "native_subhour_source_label_rows.csv"
    target_rows_status = {
        "path": str(rows_file),
        "exists": rows_file.exists(),
        "size_bytes": rows_file.stat().st_size if rows_file.exists() else 0,
        "sha256_from_provenance": target_provenance.get("rows_sha256", ""),
        "row_count_from_provenance": target_provenance.get("row_count", 0),
    }

    disqualified_reasons = [
        "target_root_created_by_tsie_materializer_after_preflight_warned_do_not_run",
        "tsie_labels_are_rule_ohlcv_derived_idx_labels_not_verifier_native_source_control",
        "crisis_absent_from_tsie_source_taxonomy",
        "prior_tsie_policy_packets_count_tsie_as_non_promoting",
        "063155_claimed_accepted_rows_but_board_contract_requires_zero_promotion_without_source_control_approval",
        "canonical_merge_not_allowed",
        "downstream_provider_autoquant_prebayes_bbn_catboost_execution_tree_rerun_not_allowed",
    ]
    if "062902" in process_snapshot:
        disqualified_reasons.append("concurrent_062902_materializer_still_active_at_audit")
    if "063217" in process_snapshot:
        disqualified_reasons.append("concurrent_public_source_candidate_sweep_still_active_at_audit")

    gate_result = (
        "r3_tsie_target_root_failclose_after_063155_v1="
        "target_root_present_but_tsie_policy_blocked_no_unlock"
    )
    decision = {
        "gate_result": gate_result,
        "target_root_present": TARGET_ROOT.exists(),
        "target_root_mutated_by_063155": TARGET_ROOT.exists()
        and target_provenance.get("run_id", "").startswith("20260512T063155"),
        "target_root_valid_required_unlock": False,
        "logical_quarantine": True,
        "accepted_rows_added_by_audit": 0,
        "materializer_claimed_accepted_rows": materializer_json.get("decision", {}).get("accepted_rows_added", ""),
        "materializer_claimed_labels": materializer_json.get("decision", {}).get(
            "accepted_mapping_confidence_95_labels", []
        ),
        "canonical_merge_allowed_now": False,
        "downstream_rerun_allowed_now": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
        "disqualified_reasons": disqualified_reasons,
    }

    required_root_rows = []
    for status in root_statuses:
        valid_unlock = False
        reason = "absent"
        if status["root_name"] == "r3_native_subhour" and status["exists"]:
            reason = "present_but_tsie_policy_blocked_logical_quarantine"
        elif status["root_name"] == "source_label_equivalence_non_target" and status["exists"]:
            reason = "present_but_non_target_equivalence_only"
        elif status["exists"]:
            reason = "present_unverified"
        required_root_rows.append(
            {
                "root_name": status["root_name"],
                "path": status["path"],
                "exists": status["exists"],
                "file_count": status["file_count"],
                "valid_required_unlock": valid_unlock,
                "reason": reason,
            }
        )

    checklist_rows = [
        {"requirement": "required_root_rechecked", "status": "pass", "evidence": "root status CSV"},
        {
            "requirement": "tsie_target_root_promoted",
            "status": "fail_closed",
            "evidence": "logical_quarantine=true accepted_rows_added_by_audit=0",
        },
        {
            "requirement": "canonical_merge_allowed",
            "status": "blocked",
            "evidence": "source/control policy blocked",
        },
        {
            "requirement": "downstream_chain_allowed",
            "status": "blocked",
            "evidence": "no valid required-root unlock",
        },
        {"requirement": "update_goal_allowed", "status": "blocked", "evidence": "strict_full_objective=false"},
    ]

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact": board_hash,
        "gate_result": gate_result,
        "decision": decision,
        "target_rows_status": target_rows_status,
        "target_provenance": target_provenance,
        "root_statuses": root_statuses,
        "required_root_rows": required_root_rows,
        "materializer_063155": {
            "run_root": repo_rel(RUN_063155),
            "decision": materializer_json.get("decision", {}),
            "assertions_excerpt": materializer_assertions,
        },
        "preflight_063215": {
            "run_root": repo_rel(RUN_063215),
            "gate_result": preflight_json.get("decision", {}).get("gate_result", preflight_json.get("gate_result", "")),
        },
        "intraday_062902_snapshot": {
            "run_root": repo_rel(RUN_062902),
            "exit_file": intraday_exit.strip(),
            "stdout_excerpt": intraday_stdout,
            "stderr_excerpt": intraday_stderr,
        },
        "process_snapshot": process_snapshot,
        "next_action": (
            "Treat /tmp/ict-engine-native-subhour-source-label-intake as TSIE-quarantined and non-promoting. "
            "Do not run canonical merge or downstream provider/AutoQuant/Pre-Bayes/BBN/CatBoost/execution-tree "
            "until explicit source/control approval or a verifier-native R3/R5/R6 target root unlock is available."
        ),
    }

    result_json = OUT / "r3_tsie_target_root_failclose_after_063155_v1.json"
    report_md = OUT / "r3_tsie_target_root_failclose_after_063155_v1.md"
    roots_csv = OUT / "r3_tsie_target_root_failclose_required_roots_v1.csv"
    checklist_csv = OUT / "prompt_to_artifact_checklist_v1.csv"
    assertions = CHECKS / "r3_tsie_target_root_failclose_after_063155_v1_assertions.out"

    result_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        roots_csv,
        required_root_rows,
        ["root_name", "path", "exists", "file_count", "valid_required_unlock", "reason"],
    )
    write_csv(checklist_csv, checklist_rows, ["requirement", "status", "evidence"])

    report_md.write_text(
        "\n".join(
            [
                "# R3 TSIE Target Root Fail-Close After 063155 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{gate_result}`",
                "",
                "## Readback",
                "",
                f"- Target root present: `{str(decision['target_root_present']).lower()}`.",
                f"- Target root mutated by `063155`: `{str(decision['target_root_mutated_by_063155']).lower()}`.",
                f"- Rows from target provenance: `{target_rows_status['row_count_from_provenance']}`.",
                f"- Rows SHA-256 from target provenance: `{target_rows_status['sha256_from_provenance']}`.",
                f"- Materializer claimed accepted rows: `{decision['materializer_claimed_accepted_rows']}`.",
                f"- Audit accepted rows: `{decision['accepted_rows_added_by_audit']}`.",
                "",
                "## Decision",
                "",
                "- The required R3 target root exists, but it is logically quarantined and non-promoting.",
                "- TSIE remains policy-blocked: rule/OHLCV-derived IDX labels, no direct `Crisis`, no source confidence, and prior TSIE gates were non-promoting.",
                "- The `063155` materializer claim that Bull/Bear/Sideways rows are accepted is not counted for Board A promotion.",
                "- Canonical merge is blocked; downstream provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree rerun is blocked.",
                "- `update_goal=false`.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{repo_rel(result_json)}`",
                f"- Required roots CSV: `{repo_rel(roots_csv)}`",
                f"- Checklist CSV: `{repo_rel(checklist_csv)}`",
                f"- Process snapshot: `{repo_rel(CMD_OUT / 'process_snapshot.txt')}`",
                f"- Assertions: `{repo_rel(assertions)}`",
                "",
                "## Next",
                "",
                result["next_action"],
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions.write_text(
        "\n".join(
            [
                f"gate_result={gate_result}",
                f"target_root_present={str(decision['target_root_present']).lower()}",
                f"target_root_valid_required_unlock={str(decision['target_root_valid_required_unlock']).lower()}",
                "logical_quarantine=true",
                "accepted_rows_added_by_audit=0",
                f"materializer_claimed_accepted_rows={decision['materializer_claimed_accepted_rows']}",
                "canonical_merge_allowed_now=false",
                "downstream_rerun_allowed_now=false",
                "strict_full_objective=false",
                "trade_usable=false",
                "update_goal=false",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(json.dumps({"ok": True, "gate_result": gate_result, "json": repo_rel(result_json)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
