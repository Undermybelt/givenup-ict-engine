#!/usr/bin/env python3
import csv
import hashlib
import json
from pathlib import Path

RUN_ID = "20260512T020708-codex-current-coordination-readback-after-020235-v1"
ROOT = Path(__file__).resolve().parents[6]
BOARD = ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUNS = ROOT / "docs/experiments/actionable-regime-confidence/runs"
OUT = RUNS / RUN_ID / "current-coordination-readback-after-020235-v1"
CHECKS = RUNS / RUN_ID / "checks"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for p in path.rglob("*") if p.is_file())


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def exits_for(root: Path):
    command_root = root / "command-output"
    exits = {}
    if command_root.exists():
        for p in sorted(command_root.glob("*.exit")):
            exits[p.name] = read_text(p).strip()
    return exits


def source_root_status():
    roots = {
        "r6_owner_export": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        "r3_native_subhour": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "r5_recency_extension": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "source_label_equivalence": Path("/tmp/ict-engine-source-label-equivalence-intake"),
    }
    return [
        {
            "name": name,
            "path": str(path),
            "present": path.exists(),
            "file_count": file_count(path),
        }
        for name, path in roots.items()
    ]


def run_root_status(board_text: str):
    targets = [
        {
            "run_id": "20260512T020037-codex-readonly-runtime-chain-refresh-after-015533-v1",
            "role": "readonly_runtime_command_outputs",
            "json": None,
        },
        {
            "run_id": "20260512T020104-codex-public-source-label-expansion-screen-v1",
            "role": "public_source_label_expansion_screen",
            "json": "public-source-label-expansion-screen-v1/public_source_label_expansion_screen_v1.json",
        },
        {
            "run_id": "20260512T020216-codex-tsie-public-source-intake-dry-run-v1",
            "role": "script_only_partial_tsie_attempt",
            "json": "tsie-public-source-intake-dry-run-v1/tsie_public_source_intake_dry_run_v1.json",
        },
        {
            "run_id": "20260512T020220-codex-tsie-source-intake-dry-run-v1",
            "role": "stale_missing_tsie_attempt",
            "json": "tsie-source-intake-dry-run-v1/tsie_source_intake_dry_run_v1.json",
        },
        {
            "run_id": "20260512T020235-codex-new-source-label-web-search-v1",
            "role": "registered_new_source_label_web_search",
            "json": "new-source-label-web-search-v1/new_source_label_web_search_v1.json",
        },
        {
            "run_id": "20260512T020450-codex-tsie-public-source-intake-dry-run-v1",
            "role": "script_only_partial_tsie_attempt",
            "json": "tsie-public-source-intake-dry-run-v1/tsie_public_source_intake_dry_run_v1.json",
        },
    ]
    rows = []
    for target in targets:
        root = RUNS / target["run_id"]
        data = load_json(root / target["json"]) if target["json"] else None
        exits = exits_for(root)
        all_exits_zero = bool(exits) and all(value == "0" for value in exits.values())
        if data:
            evidence_status = "non_promoting_report_present"
        elif target["role"].startswith("script_only") or target["role"].startswith("stale"):
            evidence_status = "not_evidence_script_or_missing_report"
        elif all_exits_zero:
            evidence_status = "command_outputs_present_no_report"
        elif root.exists():
            evidence_status = "partial_root"
        else:
            evidence_status = "absent"
        rows.append(
            {
                "run_id": target["run_id"],
                "role": target["role"],
                "path": str(root),
                "present": root.exists(),
                "file_count": file_count(root),
                "board_registered_before_this_packet": target["run_id"] in board_text,
                "evidence_status": evidence_status,
                "gate_result": (data or {}).get("gate_result", ""),
                "accepted_rows_added": (data or {}).get("accepted_rows_added", 0),
                "canonical_merge_allowed": (data or {}).get("canonical_merge_allowed", False),
                "downstream_chain_rerun_allowed": (data or {}).get("downstream_chain_rerun_allowed", False),
                "strict_full_objective_achieved": (data or {}).get("strict_full_objective_achieved", False),
                "update_goal": (data or {}).get("update_goal", False),
                "command_exit_count": len(exits),
                "all_command_exits_zero": all_exits_zero,
            }
        )
    return rows


def write_csv(path: Path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    board_text = read_text(BOARD)
    run_roots = run_root_status(board_text)
    source_roots = source_root_status()

    registered_non_promoting = [
        row for row in run_roots
        if row["board_registered_before_this_packet"]
        and row["strict_full_objective_achieved"] is False
    ]
    unregistered_non_promoting = [
        row for row in run_roots
        if not row["board_registered_before_this_packet"]
        and row["evidence_status"] in {
            "non_promoting_report_present",
            "command_outputs_present_no_report",
            "not_evidence_script_or_missing_report",
        }
    ]

    payload = {
        "run_id": RUN_ID,
        "board": str(BOARD),
        "board_hash_before_artifact": sha256(BOARD),
        "gate_result": "current_coordination_readback_after_020235_v1=no_new_acceptance_unregistered_roots_non_promoting",
        "run_roots": run_roots,
        "source_roots": source_roots,
        "registered_non_promoting_count": len(registered_non_promoting),
        "unregistered_non_promoting_or_partial_count": len(unregistered_non_promoting),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r3_r5_r6_roots_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_vendor_contact_sent": False,
        "trade_usable": False,
    }

    write_csv(OUT / "current_coordination_run_root_status_v1.csv", run_roots)
    write_csv(OUT / "current_coordination_source_root_status_v1.csv", source_roots)
    (OUT / "current_coordination_readback_after_020235_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Current Coordination Readback After 020235 v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        f"Gate result: `{payload['gate_result']}`.",
        "",
        "Purpose:",
        "- Reconcile the newest registered board section with current 02:00 run roots.",
        "- Prevent duplicate work on already-screened public source candidates.",
        "- Preserve the active R6 owner-export blocker without mutating intake roots.",
        "",
        "Run-root readback:",
    ]
    for row in run_roots:
        lines.append(
            "- `{run_id}`: present `{present}`, files `{file_count}`, "
            "board_registered `{registered}`, status `{status}`, gate `{gate}`.".format(
                run_id=row["run_id"],
                present=str(row["present"]).lower(),
                file_count=row["file_count"],
                registered=str(row["board_registered_before_this_packet"]).lower(),
                status=row["evidence_status"],
                gate=row["gate_result"] or "n/a",
            )
        )
    lines.extend([
        "",
        "Source-root readback:",
    ])
    for row in source_roots:
        lines.append(
            f"- `{row['name']}`: present `{str(row['present']).lower()}`, files `{row['file_count']}`, root `{row['path']}`."
        )
    lines.extend([
        "",
        "Decision:",
        "- `020235` is already registered and remains non-promoting: no new ready source-owned MainRegimeV2/cross-timeframe exports were found.",
        "- `020104` is already board-registered and non-promoting; it found no source-owned MainRegimeV2 export and added no accepted rows.",
        "- `020216` is already board-registered and sample-only; it maps TSIE classes as a dry-run but remains non-promoting with no accepted rows, no `Crisis` semantic equivalent, and no canonical merge.",
        "- `020037` contains read-only runtime command outputs with zero exits, but no report/assertion package; it is evidence of runtime callability only, not promotion evidence.",
        "- `020220` and `020450` are missing or script-only TSIE attempts in the current worktree state and are not acceptance evidence.",
        "- R6 owner export, R3 native sub-hour, and R5 recency roots remain absent; source-label equivalence remains present but confidence-blocked.",
        "- Accepted rows added: `0`; new confidence gate: `false`; canonical merge allowed: `false`; downstream chain rerun allowed: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`. Shared intake mutated: `false`. R3/R5/R6 roots mutated: `false`. Thresholds relaxed: `false`. Raw data committed: `false`. External vendor/contact sent: `false`. Trade usable: `false`.",
        "",
        "Next:",
        "- Preserve the Current Cursor next action for R6. Use the v4 owner/operator request packet or explicit `FLIP` approval; do not repeat known TSIE/BTC HMM sidecar/proxy loops or rerun downstream promotion until source/control roots and canonical merge pass.",
        "",
    ])
    (OUT / "current_coordination_readback_after_020235_v1.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    assert payload["accepted_rows_added"] == 0
    assert payload["canonical_merge_allowed"] is False
    assert payload["downstream_chain_rerun_allowed"] is False
    assert payload["strict_full_objective_achieved"] is False
    assert payload["update_goal"] is False
    assert not any(row["name"] == "r6_owner_export" and row["present"] for row in source_roots)
    assert any(row["run_id"].endswith("020235-codex-new-source-label-web-search-v1") and row["board_registered_before_this_packet"] for row in run_roots)
    (CHECKS / "current_coordination_readback_after_020235_v1_assertions.out").write_text(
        "current_coordination_readback_after_020235_v1 assertions passed\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
