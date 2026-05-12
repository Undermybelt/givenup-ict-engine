#!/usr/bin/env python3
"""Audit the TSIE R3 target-root materialization without promoting it."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T063851+0800-codex-post-tsie-materialization-gate-audit-v1"
GATE_RESULT = (
    "post_tsie_materialization_gate_audit_v1="
    "target_root_present_but_crisis_absent_policy_blocked_no_downstream"
)
SCRIPT = Path(__file__).resolve()
RUN_ROOT = SCRIPT.parents[1]
REPO = SCRIPT.parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
OUT_DIR = RUN_ROOT / "post-tsie-materialization-gate-audit-v1"
CHECK_DIR = RUN_ROOT / "checks"

R3_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
R3_ROWS = R3_ROOT / "native_subhour_source_label_rows.csv"
R3_PROVENANCE = R3_ROOT / "native_subhour_source_label_provenance.json"
R6_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
R5_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")

SOURCE_063155 = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T063155+0800-codex-r3-tsie-native-subhour-intake-materialization-v1"
)
GUARD_063215 = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T063215+0800-codex-r3-tsie-native-intraday-materializer-preflight-v1"
)
SOURCE_062902 = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T062902+0800-codex-r3-hf-tsie-native-intraday-intake-v1"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def ps_matches() -> list[dict[str, str]]:
    proc = subprocess.run(
        ["ps", "-axo", "pid,ppid,stat,etime,command"],
        text=True,
        capture_output=True,
        check=False,
    )
    rows: list[dict[str, str]] = []
    for line in proc.stdout.splitlines()[1:]:
        if not any(
            token in line
            for token in [
                "98181",
                "062902",
                "063155",
                "r3_hf_tsie",
                "r3_tsie_native",
                "native-subhour-source-label-intake",
            ]
        ):
            continue
        if "post_tsie_materialization_gate_audit_v1.py" in line:
            continue
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        rows.append(
            {
                "pid": parts[0],
                "ppid": parts[1],
                "stat": parts[2],
                "etime": parts[3],
                "command": parts[4],
            }
        )
    return rows


def root_snapshot() -> list[dict[str, Any]]:
    specs = [
        {
            "id": "r6_owner_export",
            "root": R6_ROOT,
            "required": [
                "positive_spoofing_layering_rows.csv",
                "matched_negative_normal_activity_rows.csv",
                "provenance_manifest.json",
            ],
        },
        {
            "id": "r3_native_subhour",
            "root": R3_ROOT,
            "required": [
                "native_subhour_source_label_rows.csv",
                "native_subhour_source_label_provenance.json",
            ],
        },
        {
            "id": "r5_recency_extension",
            "root": R5_ROOT,
            "required": [
                "stock_market_regimes_2026_extension.csv",
                "source_panel_recency_provenance.json",
            ],
        },
    ]
    rows: list[dict[str, Any]] = []
    for spec in specs:
        root = spec["root"]
        present = []
        missing = []
        sizes: dict[str, int] = {}
        for name in spec["required"]:
            path = root / name
            if path.is_file():
                present.append(name)
                sizes[name] = path.stat().st_size
            else:
                missing.append(name)
        rows.append(
            {
                "id": spec["id"],
                "root": str(root),
                "root_exists": root.exists(),
                "present_files": ";".join(present),
                "missing_files": ";".join(missing),
                "all_required_present": len(missing) == 0,
                "sizes_json": json.dumps(sizes, sort_keys=True),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    board_hash = sha256_file(BOARD)
    provenance = read_json(R3_PROVENANCE)
    root_rows = root_snapshot()
    active_processes = ps_matches()
    guard_assertions = read_text(
        GUARD_063215
        / "checks/r3_tsie_native_intraday_materializer_preflight_v1_assertions.out"
    )
    source_assertions = read_text(
        SOURCE_063155
        / "checks/r3_tsie_native_subhour_intake_materialization_v1_assertions.out"
    )

    accepted_labels = provenance.get("accepted_mapping_confidence_95_labels", [])
    missing_labels = [
        label
        for label in ["Bull", "Bear", "Sideways", "Crisis"]
        if label not in accepted_labels
    ]
    r3_required_present = R3_ROWS.is_file() and R3_PROVENANCE.is_file()
    policy_blockers = [
        "Crisis absent from TSIE source taxonomy",
        "063215 preflight gate says do_not_run_target_root_materializer_proxy_blocked",
        "prior Board A TSIE policy rejected rule/OHLCV proxy labels as promoting evidence",
        "canonical merge not run",
        "provider/AutoQuant/Pre-Bayes/BBN/CatBoost/execution-tree not rerun",
        "R6 owner/export and R5 recency roots remain absent",
    ]
    promotion_allowed = False
    decision = {
        "gate_result": GATE_RESULT,
        "r3_root_present": R3_ROOT.exists(),
        "r3_required_files_present": r3_required_present,
        "r3_target_root_mutated_by_063155": True,
        "r3_rows_path": str(R3_ROWS),
        "r3_rows_size_bytes": R3_ROWS.stat().st_size if R3_ROWS.is_file() else 0,
        "r3_rows_sha256_from_provenance": provenance.get("rows_sha256", ""),
        "mapped_rows": provenance.get("row_count", 0),
        "raw_rows": provenance.get("raw_row_count", 0),
        "accepted_mapping_confidence_95_labels": accepted_labels,
        "missing_main_regime_v2_labels": missing_labels,
        "policy_blockers": policy_blockers,
        "source_control_evidence_acquired": False,
        "r3_unlock_accepted_for_promotion": False,
        "canonical_merge_allowed_now": promotion_allowed,
        "canonical_merge": False,
        "downstream_promotion_rerun_allowed_now": promotion_allowed,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }
    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_before_artifact": board_hash,
        "decision": decision,
        "required_roots": root_rows,
        "active_processes": active_processes,
        "source_artifacts": {
            "063155_root": rel(SOURCE_063155),
            "063155_report_exists": (
                SOURCE_063155
                / "r3-tsie-native-subhour-intake-materialization-v1/"
                "r3_tsie_native_subhour_intake_materialization_v1.md"
            ).is_file(),
            "063215_guard_root": rel(GUARD_063215),
            "063215_guard_assertions_present": bool(guard_assertions),
            "062902_root": rel(SOURCE_062902),
            "062902_terminal_report_present": any(
                p.is_file() and p.suffix in {".md", ".json"}
                for p in (SOURCE_062902 / "r3-hf-tsie-native-intraday-intake-v1").glob("*")
            )
            if (SOURCE_062902 / "r3-hf-tsie-native-intraday-intake-v1").exists()
            else False,
        },
        "guard_assertions": guard_assertions.splitlines(),
        "source_assertions": source_assertions.splitlines(),
    }

    json_path = OUT_DIR / "post_tsie_materialization_gate_audit_v1.json"
    roots_csv = OUT_DIR / "post_tsie_materialization_required_roots_v1.csv"
    processes_csv = OUT_DIR / "post_tsie_materialization_active_processes_v1.csv"
    report_path = OUT_DIR / "post_tsie_materialization_gate_audit_v1.md"
    assertions_path = CHECK_DIR / "post_tsie_materialization_gate_audit_v1_assertions.out"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        roots_csv,
        root_rows,
        [
            "id",
            "root",
            "root_exists",
            "present_files",
            "missing_files",
            "all_required_present",
            "sizes_json",
        ],
    )
    write_csv(processes_csv, active_processes, ["pid", "ppid", "stat", "etime", "command"])

    md = [
        "# Post TSIE Materialization Gate Audit v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE_RESULT}`",
        "",
        f"Board sha256 before artifact: `{board_hash}`",
        "",
        "## Readback",
        "",
        f"- R3 root present: `{decision['r3_root_present']}`.",
        f"- R3 required files present: `{decision['r3_required_files_present']}`.",
        f"- Mapped rows from provenance: `{decision['mapped_rows']}`.",
        f"- Accepted mapping-confidence labels: `{', '.join(accepted_labels)}`.",
        f"- Missing MainRegimeV2 labels: `{', '.join(missing_labels)}`.",
        f"- Rows SHA-256 from provenance: `{decision['r3_rows_sha256_from_provenance']}`.",
        "",
        "## Gate Decision",
        "",
        (
            "The R3 filesystem root is now present, but this audit does not treat it "
            "as a promotion unlock. `063215` already classified the TSIE materializer "
            "as proxy-blocked, and `063155` still leaves `Crisis` absent while canonical "
            "merge and downstream promotion remain false."
        ),
        "",
        "Promotion remains blocked: source/control evidence acquired `false`, "
        "canonical merge `false`, downstream promotion rerun `false`, strict full "
        "objective `false`, trade usable `false`, and `update_goal=false`.",
        "",
        "## Active Same-Scope Processes",
        "",
    ]
    if active_processes:
        md.extend(
            [
                "| PID | Stat | Elapsed | Command |",
                "|---:|---|---:|---|",
            ]
        )
        for row in active_processes[:20]:
            command = row["command"].replace("|", "/")
            md.append(f"| `{row['pid']}` | `{row['stat']}` | `{row['etime']}` | `{command}` |")
    else:
        md.append("No active same-scope TSIE/materialization process was observed.")
    md.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(json_path)}`",
            f"- Required roots CSV: `{rel(roots_csv)}`",
            f"- Active processes CSV: `{rel(processes_csv)}`",
            f"- Assertions: `{rel(assertions_path)}`",
            "",
            "## Next",
            "",
            (
                "Do not run canonical merge or provider/AutoQuant -> filter/Pre-Bayes "
                "-> BBN -> CatBoost/path-ranking -> execution-tree promotion from this "
                "TSIE root. Continue only from explicit source/control approval, real "
                "R6 owner/export rows with controls, source-owned R5 recency rows, or a "
                "new verifier-native R3 source that covers all required MainRegimeV2 labels."
            ),
            "",
        ]
    )
    report_path.write_text("\n".join(md), encoding="utf-8")

    assertions = [
        f"gate_result={GATE_RESULT}",
        f"r3_root_present={decision['r3_root_present']}",
        f"r3_required_files_present={decision['r3_required_files_present']}",
        f"mapped_rows={decision['mapped_rows']}",
        f"missing_main_regime_v2_labels={','.join(missing_labels)}",
        "source_control_evidence_acquired_false=True",
        "r3_unlock_accepted_for_promotion_false=True",
        "canonical_merge_allowed_now_false=True",
        "canonical_merge_false=True",
        "downstream_promotion_rerun_allowed_now_false=True",
        "downstream_promotion_rerun_false=True",
        "strict_full_objective_false=True",
        "trade_usable_false=True",
        "update_goal_false=True",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
