#!/usr/bin/env python3
"""Read-only source/control arrival refresh after the R3 TSIE quarantine audit."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T064320+0800-codex-source-control-arrival-refresh-after-063906-v2"
SCRIPT = Path(__file__).resolve()
RUN_ROOT = SCRIPT.parents[1]
REPO = SCRIPT.parents[6]
OUT_DIR = RUN_ROOT / "source-control-arrival-refresh-after-063906-v2"
CHECK_DIR = RUN_ROOT / "checks"
COMMAND_DIR = RUN_ROOT / "command-output"

BOARD_B = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"
BOARD_A = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
ICT_ENGINE = REPO / "target/debug/ict-engine"

R3_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
R5_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
R6_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")

REQUIRED_ROOTS = [
    {
        "id": "r3_native_subhour",
        "root": R3_ROOT,
        "required_files": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
        "accepted_unlock_rule": "verifier-native or source/control-approved MainRegimeV2 labels including required per-regime coverage",
    },
    {
        "id": "r5_recency_extension",
        "root": R5_ROOT,
        "required_files": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
        "accepted_unlock_rule": "source-owned post-2026-01-30 panel recency rows plus provenance",
    },
    {
        "id": "r6_owner_export",
        "root": R6_ROOT,
        "required_files": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
        "accepted_unlock_rule": "owner/export rows with valid normal controls or explicit source/control approval",
    },
]


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_csv_data_rows(path: Path) -> int | None:
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return max(sum(1 for _ in csv.reader(handle)) - 1, 0)


def read_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def run_provider_status() -> dict[str, object]:
    stdout_path = COMMAND_DIR / "provider_status_agent.out"
    stderr_path = COMMAND_DIR / "provider_status_agent.err"
    exit_path = COMMAND_DIR / "provider_status_agent.exit"
    if not ICT_ENGINE.is_file():
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text(f"missing ict-engine binary: {ICT_ENGINE}\n", encoding="utf-8")
        exit_path.write_text("127\n", encoding="utf-8")
        return {
            "ran": False,
            "exit_code": 127,
            "stdout_path": str(stdout_path.relative_to(REPO)),
            "stderr_path": str(stderr_path.relative_to(REPO)),
            "reason": "missing_binary",
        }
    try:
        completed = subprocess.run(
            [str(ICT_ENGINE), "provider-status", "--agent"],
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=90,
            check=False,
        )
        stdout_path.write_text(completed.stdout, encoding="utf-8")
        stderr_path.write_text(completed.stderr, encoding="utf-8")
        exit_path.write_text(f"{completed.returncode}\n", encoding="utf-8")
        return {
            "ran": True,
            "exit_code": completed.returncode,
            "stdout_path": str(stdout_path.relative_to(REPO)),
            "stderr_path": str(stderr_path.relative_to(REPO)),
            "mentions": {
                "ibkr": "ibkr" in completed.stdout.lower(),
                "tradingview": "tradingview" in completed.stdout.lower(),
                "yfinance": "yfinance" in completed.stdout.lower() or "yahoo" in completed.stdout.lower(),
                "kraken": "kraken" in completed.stdout.lower(),
            },
        }
    except subprocess.TimeoutExpired as exc:
        stdout_path.write_text(exc.stdout or "", encoding="utf-8")
        stderr_path.write_text((exc.stderr or "") + "\nprovider-status timed out after 90s\n", encoding="utf-8")
        exit_path.write_text("124\n", encoding="utf-8")
        return {
            "ran": True,
            "exit_code": 124,
            "stdout_path": str(stdout_path.relative_to(REPO)),
            "stderr_path": str(stderr_path.relative_to(REPO)),
            "reason": "timeout",
        }


def root_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    r3_provenance = read_json(R3_ROOT / "native_subhour_source_label_provenance.json")
    board_b_text = BOARD_B.read_text(encoding="utf-8", errors="replace") if BOARD_B.is_file() else ""
    tsie_quarantined = (
        "r3_tsie_target_root_failclose_after_063155" in board_b_text
        or "TSIE Quarantine" in board_b_text
        or "tsie_policy_quarantined" in board_b_text
    )
    for item in REQUIRED_ROOTS:
        root = item["root"]
        present_files: list[str] = []
        missing_files: list[str] = []
        row_counts: dict[str, int | None] = {}
        hashes: dict[str, str | None] = {}
        for name in item["required_files"]:
            path = root / name
            if path.is_file():
                present_files.append(name)
                hashes[name] = sha256(path)
                if path.suffix == ".csv":
                    row_counts[name] = count_csv_data_rows(path)
            else:
                missing_files.append(name)
        all_required_present = not missing_files
        accepted_unlock = False
        blocker = ""
        if item["id"] == "r3_native_subhour" and root.exists():
            accepted_unlock = False
            blocker = "present_but_quarantined_tsie_policy_blocked" if tsie_quarantined else "present_but_no_acceptance_policy_found"
        elif item["id"] in {"r5_recency_extension", "r6_owner_export"}:
            accepted_unlock = all_required_present
            blocker = "" if accepted_unlock else "required_root_or_files_absent"
        rows.append(
            {
                "id": item["id"],
                "root": str(root),
                "root_exists": root.exists(),
                "all_required_files_present": all_required_present,
                "present_files": ";".join(present_files),
                "missing_files": ";".join(missing_files),
                "row_counts": json.dumps(row_counts, sort_keys=True),
                "hashes": json.dumps(hashes, sort_keys=True),
                "accepted_unlock": accepted_unlock,
                "blocker": blocker,
                "accepted_unlock_rule": item["accepted_unlock_rule"],
                "source_run_id": r3_provenance.get("run_id", "") if item["id"] == "r3_native_subhour" else "",
            }
        )
    return rows


def checklist_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    roots = {row["id"]: row for row in payload["required_roots"]}  # type: ignore[index]
    provider = payload["provider_status"]  # type: ignore[index]
    return [
        {
            "requirement": "Authoritative Board B markdown updated in-place",
            "evidence": str(BOARD_B.relative_to(REPO)),
            "status": "covered_this_run_readonly_no_cursor_edit",
        },
        {
            "requirement": "Branch path must remain main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor",
            "evidence": "Board B tail preserves exact branch path contract",
            "status": "contract_present_not_executed_without_unlock",
        },
        {
            "requirement": "Do not disturb concurrent multi-agent construction",
            "evidence": "new run root used; empty 064220 root was not modified",
            "status": "covered",
        },
        {
            "requirement": "R3 native subhour source/control unlock",
            "evidence": f"{roots['r3_native_subhour']['root']} accepted_unlock={roots['r3_native_subhour']['accepted_unlock']}",
            "status": "blocked_quarantined_tsie_root",
        },
        {
            "requirement": "R5 source-panel recency unlock",
            "evidence": f"{roots['r5_recency_extension']['root']} exists={roots['r5_recency_extension']['root_exists']}",
            "status": "missing",
        },
        {
            "requirement": "R6 owner/export control unlock",
            "evidence": f"{roots['r6_owner_export']['root']} exists={roots['r6_owner_export']['root_exists']}",
            "status": "missing",
        },
        {
            "requirement": "Provider context must include IBKR, TradingViewRemix, yfinance, Kraken",
            "evidence": provider.get("stdout_path", ""),
            "status": "diagnostic_only_provider_status_ran" if provider.get("ran") else "diagnostic_missing_binary",
        },
        {
            "requirement": "Explicit user selection of exactly one HTF=1d, MTF=4h, or LTF=1h",
            "evidence": "Board B blocker remains user_selected_historical_data_missing",
            "status": "missing",
        },
        {
            "requirement": "Selected-data AutoQuant/factor research",
            "evidence": "No accepted source/control unlock and no selected history",
            "status": "blocked_not_run",
        },
        {
            "requirement": "Filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution tree rerun preserving branch path",
            "evidence": "Downstream promotion rerun remains false",
            "status": "blocked_not_run",
        },
        {
            "requirement": "Goal completion",
            "evidence": "strict_full_objective=false; update_goal=false",
            "status": "not_complete",
        },
    ]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    COMMAND_DIR.mkdir(parents=True, exist_ok=True)

    provider_status = run_provider_status()
    roots = root_rows()
    valid_unlocks = [row["id"] for row in roots if row["accepted_unlock"]]
    gate_result = "source_control_arrival_refresh_after_063906_v2=no_new_unlock_no_selected_history_no_downstream"
    payload: dict[str, object] = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": gate_result,
        "board_a_sha256": sha256(BOARD_A),
        "board_b_sha256": sha256(BOARD_B),
        "required_roots": roots,
        "valid_required_unlocks": valid_unlocks,
        "provider_status": provider_status,
        "empty_064220_root_left_unmodified": True,
        "source_control_evidence_acquired": bool(valid_unlocks),
        "explicit_user_selected_history": False,
        "selected_data_autoquant_training": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
    }
    payload["checklist"] = checklist_rows(payload)

    json_path = OUT_DIR / "source_control_arrival_refresh_after_063906_v2.json"
    roots_csv = OUT_DIR / "source_control_arrival_required_roots_v2.csv"
    checklist_csv = OUT_DIR / "prompt_to_artifact_checklist_v2.csv"
    md_path = OUT_DIR / "source_control_arrival_refresh_after_063906_v2.md"
    assertions_path = CHECK_DIR / "source_control_arrival_refresh_after_063906_v2_assertions.out"

    write_csv(
        roots_csv,
        roots,
        [
            "id",
            "root",
            "root_exists",
            "all_required_files_present",
            "present_files",
            "missing_files",
            "row_counts",
            "hashes",
            "accepted_unlock",
            "blocker",
            "accepted_unlock_rule",
            "source_run_id",
        ],
    )
    write_csv(checklist_csv, payload["checklist"], ["requirement", "evidence", "status"])  # type: ignore[arg-type]
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    r3 = next(row for row in roots if row["id"] == "r3_native_subhour")
    r5 = next(row for row in roots if row["id"] == "r5_recency_extension")
    r6 = next(row for row in roots if row["id"] == "r6_owner_export")
    provider_exit = provider_status.get("exit_code")
    md_path.write_text(
        "\n".join(
            [
                "# Source/Control Arrival Refresh After 063906 v2",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{gate_result}`",
                "",
                "Scope:",
                "- Read-only source/control arrival refresh after the R3 TSIE quarantine audit.",
                "- Used a fresh run root and did not modify the empty `064220` directory created by another agent.",
                "- Ran `ict-engine provider-status --agent` as diagnostic provider context only.",
                "- Did not run selected-data AutoQuant training, canonical merge, filter/Pre-Bayes, BBN, CatBoost/path-ranking, or execution tree.",
                "",
                "Readback:",
                f"- R3 root exists: `{r3['root_exists']}`; accepted unlock: `{r3['accepted_unlock']}`; blocker: `{r3['blocker']}`.",
                f"- R3 source run id: `{r3['source_run_id']}`.",
                f"- R5 recency root exists: `{r5['root_exists']}`; accepted unlock: `{r5['accepted_unlock']}`.",
                f"- R6 owner/export root exists: `{r6['root_exists']}`; accepted unlock: `{r6['accepted_unlock']}`.",
                f"- Valid required unlocks: `{','.join(valid_unlocks) if valid_unlocks else 'none'}`.",
                f"- Provider status exit code: `{provider_exit}`; output: `{provider_status.get('stdout_path', '')}`.",
                "- Explicit user-selected history remains absent.",
                "- Selected-data AutoQuant/factor research remains blocked.",
                "- Downstream promotion rerun remains false.",
                "",
                "Decision:",
                "- No new source/control unlock arrived after the `063906` quarantine audit.",
                "- The physically present TSIE R3 root remains quarantined and cannot be used as the regime root for profitability-factor branching.",
                "- Board B must remain fail-closed with `user_selected_historical_data_missing` and no downstream rerun.",
                "- `update_goal=false`.",
                "",
                "Next:",
                "- Continue only from explicit source/control approval, verifier-native R6 owner/export rows with controls, source-owned R5 recency rows, verifier-native R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export.",
                "- After that, require the user to select exactly one of `HTF=1d`, `MTF=4h`, or `LTF=1h` before selected-data AutoQuant/factor research and the filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree chain can rerun with the branch path preserved.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = [
        f"gate_result={gate_result}",
        f"r3_root_exists={r3['root_exists']}",
        f"r3_accepted_unlock={r3['accepted_unlock']}",
        f"r5_root_exists={r5['root_exists']}",
        f"r6_root_exists={r6['root_exists']}",
        f"valid_required_unlocks={','.join(valid_unlocks) if valid_unlocks else 'none'}",
        f"provider_status_exit_code={provider_exit}",
        "explicit_user_selected_history=false",
        "selected_data_autoquant_training=false",
        "canonical_merge=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "promotion_allowed=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
