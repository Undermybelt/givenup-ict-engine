#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path


RUN_ID = "20260512T013634-codex-r6-owner-export-contract-readback-v1"
TARGET_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
REQUIRED_FILES = [
    ("positive_rows", "positive_spoofing_layering_rows.csv", "direct_manipulation_positive_rows.csv"),
    ("matched_negative_rows", "matched_negative_normal_activity_rows.csv", "direct_manipulation_matched_controls.csv"),
    ("provenance_manifest", "provenance_manifest.json", "direct_manipulation_provenance.json"),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_current_cursor(board_text: str) -> dict[str, str]:
    cursor: dict[str, str] = {}
    in_cursor = False
    for raw_line in board_text.splitlines():
        line = raw_line.strip()
        if line == "## Current Cursor":
            in_cursor = True
            continue
        if in_cursor and line.startswith("## "):
            break
        if not in_cursor or not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 2 and cells[0] not in {"Field", "---"}:
            cursor[cells[0]] = cells[1]
    return cursor


def run_command(repo_root: Path, name: str, argv: list[str], output_dir: Path, env: dict[str, str] | None = None) -> dict[str, object]:
    try:
        proc = subprocess.run(
            argv,
            cwd=repo_root,
            env=env,
            text=True,
            capture_output=True,
            timeout=90,
            check=False,
        )
        exit_code = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + "\nTIMEOUT after 90s\n"

    (output_dir / f"{name}.cmd").write_text(" ".join(argv) + "\n", encoding="utf-8")
    (output_dir / f"{name}.exit").write_text(f"{exit_code}\n", encoding="utf-8")
    (output_dir / f"{name}.stdout.txt").write_text(stdout, encoding="utf-8")
    (output_dir / f"{name}.stderr.txt").write_text(stderr, encoding="utf-8")

    parsed: dict[str, object] = {}
    if stdout.strip().startswith("{"):
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            parsed = {}
    return {
        "name": name,
        "argv": argv,
        "exit_code": exit_code,
        "stdout_path": str(output_dir / f"{name}.stdout.txt"),
        "stderr_path": str(output_dir / f"{name}.stderr.txt"),
        "summary_line": parsed.get("summary_line", ""),
        "parsed_status": parsed.get("status", ""),
        "parsed_healthy": parsed.get("healthy", ""),
        "parsed_data_ready": parsed.get("data_ready", ""),
    }


def main() -> None:
    script_path = Path(__file__).resolve()
    run_root = script_path.parents[1]
    repo_root = script_path.parents[6]
    artifact_dir = run_root / "r6-owner-export-contract-readback-v1"
    checks_dir = run_root / "checks"
    output_dir = run_root / "command-output"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    board_path = repo_root / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
    board_text = board_path.read_text(encoding="utf-8")
    cursor = parse_current_cursor(board_text)

    contract_root = repo_root / (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T003003-codex-r6-owner-export-verifier-native-contract-v1/"
        "r6-owner-export-verifier-native-contract"
    )
    access_root = repo_root / (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T010212-codex-r6-owner-export-access-route-preflight-v1/"
        "r6-owner-export-access-route-preflight-v1"
    )
    entitlement_root = repo_root / (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T010127-codex-r6-owner-route-entitlement-readback-v1/"
        "r6-owner-route-entitlement-readback"
    )

    verifier_native_rows = read_csv(contract_root / "r6_owner_export_verifier_native_files_v1.csv")
    alias_mapping_rows = read_csv(contract_root / "r6_owner_export_to_verifier_mapping_v1.csv")
    required_status_rows = read_csv(access_root / "owner_export_required_file_status_v1.csv")
    entitlement_json = load_json(entitlement_root / "r6_owner_route_entitlement_readback_v1.json")

    file_rows: list[dict[str, object]] = []
    for logical_role, verifier_file, owner_alias in REQUIRED_FILES:
        verifier_path = TARGET_ROOT / verifier_file
        alias_path = TARGET_ROOT / owner_alias
        file_rows.append(
            {
                "logical_role": logical_role,
                "verifier_native_filename": verifier_file,
                "owner_request_alias": owner_alias,
                "target_path": str(verifier_path),
                "verifier_native_present": verifier_path.exists(),
                "owner_alias_present": alias_path.exists(),
                "accepted_without_adapter": False,
                "required_before_chain_rerun": True,
            }
        )

    commands = [
        run_command(
            repo_root,
            "direct_verifier_owner_export_root",
            [
                "python3",
                "docs/experiments/actionable-regime-confidence/runs/"
                "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
                "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py",
                "--intake-root",
                str(TARGET_ROOT),
            ],
            output_dir,
        ),
        run_command(repo_root, "provider_status_agent", ["./target/debug/ict-engine", "provider-status", "--agent"], output_dir),
        run_command(repo_root, "provider_status_yfinance", ["./target/debug/ict-engine", "provider-status", "--agent", "--provider", "yfinance"], output_dir),
        run_command(repo_root, "provider_status_ibkr", ["./target/debug/ict-engine", "provider-status", "--agent", "--provider", "ibkr"], output_dir),
        run_command(repo_root, "provider_status_tradingview_mcp", ["./target/debug/ict-engine", "provider-status", "--agent", "--provider", "tradingview_mcp"], output_dir),
        run_command(repo_root, "provider_status_kraken_public", ["./target/debug/ict-engine", "provider-status", "--agent", "--provider", "kraken_public"], output_dir),
        run_command(repo_root, "provider_status_kraken_cli", ["./target/debug/ict-engine", "provider-status", "--agent", "--provider", "kraken_cli"], output_dir),
        run_command(
            repo_root,
            "auto_quant_status_json",
            [
                "./target/debug/ict-engine",
                "auto-quant-status",
                "--state-dir",
                "/tmp/ict-engine-board-a-r6-owner-export-contract-readback-v1-state",
                "--output-format",
                "json",
            ],
            output_dir,
            {**os.environ, "ICT_ENGINE_AUTO_QUANT_DIR": "/Users/thrill3r/Auto-Quant"},
        ),
    ]

    verifier_required_all_present = all(row["verifier_native_present"] for row in file_rows)
    direct_verifier_exit = next(item["exit_code"] for item in commands if item["name"] == "direct_verifier_owner_export_root")
    canonical_merge_allowed = bool(verifier_required_all_present and direct_verifier_exit == 0 and False)
    downstream_rerun_allowed = False
    gate_result = "r6_owner_export_contract_readback_v1=verifier_native_contract_confirmed_owner_export_absent_no_promotion"

    provider_rows = [
        {
            "command": item["name"],
            "exit_code": item["exit_code"],
            "summary_line": item["summary_line"],
            "status": item["parsed_status"],
            "healthy": item["parsed_healthy"],
            "data_ready": item["parsed_data_ready"],
        }
        for item in commands
        if item["name"].startswith("provider_status") or item["name"] == "auto_quant_status_json"
    ]

    result = {
        "run_id": RUN_ID,
        "board_hash_before": sha256_file(board_path),
        "observed_cursor": cursor.get("last_loop_id", ""),
        "board_state": cursor.get("board_state", ""),
        "current_run_root": cursor.get("current_run_root", ""),
        "target_root": str(TARGET_ROOT),
        "target_root_present": TARGET_ROOT.exists(),
        "gate_result": gate_result,
        "existing_contract_artifact": str(contract_root / "r6_owner_export_verifier_native_contract_v1.md"),
        "existing_access_preflight": str(access_root / "r6_owner_export_access_route_preflight_v1.md"),
        "existing_entitlement_readback": str(entitlement_root / "r6_owner_route_entitlement_readback_v1.md"),
        "verifier_native_contract_rows": verifier_native_rows,
        "alias_mapping_rows": alias_mapping_rows,
        "access_preflight_required_status_rows": required_status_rows,
        "current_required_file_rows": file_rows,
        "source_owned_normal_controls_acquired": entitlement_json.get("source_owned_normal_controls_acquired", 0),
        "same_exhibit_flip_approval": entitlement_json.get("same_exhibit_flip_approval", False),
        "verifier_required_all_present": verifier_required_all_present,
        "direct_verifier_exit_code": direct_verifier_exit,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": canonical_merge_allowed,
        "downstream_rerun_allowed": downstream_rerun_allowed,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "owner_export_root_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "provider_autoquant_command_rows": provider_rows,
        "next_action": (
            "Satisfy the CME/Cboe owner-export requests with verifier-native files and provenance, "
            "or explicitly approve the same-exhibit FLIP-as-control exception; only then populate the "
            "owner-export root under shared lock and rerun direct verifier, calibration, provider, "
            "Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback."
        ),
    }

    report_lines = [
        "# R6 Owner Export Contract Readback v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Current cursor observed: `{result['observed_cursor']}`; board state: `{result['board_state']}`.",
        f"- Gate result: `{gate_result}`.",
        "- This is a readback/registration packet only: it does not create an adapter, mutate the owner-export root, approve `FLIP` rows, or rerun downstream promotion.",
        "",
        "## Result",
        "",
        f"- Target owner-export root: `{TARGET_ROOT}`; present: `{str(TARGET_ROOT.exists()).lower()}`.",
        f"- Verifier-native required files all present: `{str(verifier_required_all_present).lower()}`.",
        f"- Direct verifier exit code: `{direct_verifier_exit}`.",
        "- Canonical filename contract is already resolved by the `003003` artifact: verifier-native files are canonical; owner-facing `direct_manipulation_*` names are aliases only and are not accepted by the unchanged verifier without explicit adapter/contract approval.",
        f"- Source-owned normal controls acquired: `{result['source_owned_normal_controls_acquired']}`.",
        f"- Same-exhibit `FLIP` approval acquired: `{str(result['same_exhibit_flip_approval']).lower()}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; canonical merge allowed: `false`; downstream promotion rerun allowed: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`. Shared intake mutated: `false`. Owner-export root mutated: `false`. Thresholds relaxed: `false`. Raw data committed: `false`. External requests sent: `false`. Trade usable: `false`.",
        "",
        "## Provider / Auto-Quant Read-Only Commands",
        "",
    ]
    for row in provider_rows:
        report_lines.append(
            f"- `{row['command']}` exit `{row['exit_code']}`"
            + (f"; summary `{row['summary_line']}`" if row["summary_line"] else "")
            + (f"; status `{row['status']}`" if row["status"] else "")
            + "."
        )
    report_lines.extend(
        [
            "",
            "## Evidence",
            "",
            f"- JSON: `{artifact_dir / 'r6_owner_export_contract_readback_v1.json'}`",
            f"- Required-file CSV: `{artifact_dir / 'r6_owner_export_contract_required_files_v1.csv'}`",
            f"- Alias mapping CSV: `{artifact_dir / 'r6_owner_export_contract_alias_mapping_v1.csv'}`",
            f"- Provider/Auto-Quant command CSV: `{artifact_dir / 'provider_autoquant_readonly_commands_v1.csv'}`",
            f"- Direct verifier stdout/stderr: `{output_dir / 'direct_verifier_owner_export_root.stdout.txt'}` / `{output_dir / 'direct_verifier_owner_export_root.stderr.txt'}`",
            f"- Assertions: `{checks_dir / 'r6_owner_export_contract_readback_v1_assertions.out'}`",
            "",
            "## Next",
            "",
            f"- {result['next_action']}",
        ]
    )

    (artifact_dir / "r6_owner_export_contract_readback_v1.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    (artifact_dir / "r6_owner_export_contract_readback_v1.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        artifact_dir / "r6_owner_export_contract_required_files_v1.csv",
        file_rows,
        [
            "logical_role",
            "verifier_native_filename",
            "owner_request_alias",
            "target_path",
            "verifier_native_present",
            "owner_alias_present",
            "accepted_without_adapter",
            "required_before_chain_rerun",
        ],
    )
    write_csv(
        artifact_dir / "r6_owner_export_contract_alias_mapping_v1.csv",
        alias_mapping_rows,
        ["owner_file", "owner_field", "verifier_file", "verifier_field", "mapping_rule"],
    )
    write_csv(
        artifact_dir / "provider_autoquant_readonly_commands_v1.csv",
        provider_rows,
        ["command", "exit_code", "summary_line", "status", "healthy", "data_ready"],
    )

    assertions = [
        f"gate_result={gate_result}",
        f"observed_cursor={result['observed_cursor']}",
        f"target_root_present={str(TARGET_ROOT.exists()).lower()}",
        f"verifier_required_all_present={str(verifier_required_all_present).lower()}",
        f"direct_verifier_exit_code={direct_verifier_exit}",
        "accepted_rows_added=0",
        "canonical_merge_allowed=false",
        "downstream_rerun_allowed=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        "runtime_code_changed=false",
        "shared_intake_mutated=false",
        "owner_export_root_mutated=false",
        "raw_data_committed=false",
        "trade_usable=false",
    ]
    (checks_dir / "r6_owner_export_contract_readback_v1_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")

    if result["observed_cursor"] != "20260512T010127+0800-codex-r6-owner-route-entitlement-readback-v1":
        raise SystemExit("unexpected cursor drift; review before board writeback")
    if verifier_required_all_present:
        raise SystemExit("owner-export root unexpectedly complete; rerun with promotion path review")
    if direct_verifier_exit == 0:
        raise SystemExit("direct verifier unexpectedly passed; rerun with promotion path review")
    if result["canonical_merge_allowed"] or result["downstream_rerun_allowed"] or result["strict_full_objective_achieved"]:
        raise SystemExit("promotion flags must remain false")


if __name__ == "__main__":
    main()
