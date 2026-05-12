#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path


RUN_ID = "20260512T160838+0800-codex-board-a-current-blocker-refresh-v1"
BOARD_REL = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
OWNER_EXPORT_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
REQUIRED_OWNER_FILES = [
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
]
PROVIDERS = [
    "yfinance",
    "ibkr",
    "tradingview_mcp",
    "kraken_public",
    "kraken_cli",
    "binance_public",
    "bybit_public",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[6]


def run_root() -> Path:
    return Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_cursor(board_text: str) -> dict[str, str]:
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


def run_command(
    name: str,
    argv: list[str],
    output_dir: Path,
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 120,
) -> dict[str, object]:
    try:
        proc = subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        exit_code = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n"

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
        "status": parsed.get("status", ""),
        "healthy": parsed.get("healthy", ""),
        "data_ready": parsed.get("data_ready", ""),
        "ready_by_domain": parsed.get("ready_by_domain", {}),
        "ready_providers": parsed.get("ready_providers", []),
        "pending_providers": parsed.get("pending_providers", []),
    }


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_exit(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip() if path.exists() else ""


def list_latest_roots(base: Path) -> list[dict[str, str]]:
    roots: list[dict[str, str]] = []
    if not base.exists():
        return roots
    for item in base.iterdir():
        if not item.is_dir():
            continue
        stat = item.stat()
        roots.append(
            {
                "path": str(item),
                "mtime_ns": str(stat.st_mtime_ns),
                "name": item.name,
            }
        )
    roots.sort(key=lambda row: row["mtime_ns"])
    return roots[-20:]


def active_process_rows() -> list[dict[str, str]]:
    proc = subprocess.run(
        ["ps", "-axo", "pid,ppid,etime,stat,command"],
        text=True,
        capture_output=True,
        check=False,
    )
    needles = [
        "ict-engine",
        "run_tomac",
        "auto-quant",
        "Auto-Quant",
        "catboost",
        "CatBoost",
        "target/debug/ict-engine",
        "target/release/ict-engine",
        "cargo run",
    ]
    rows: list[dict[str, str]] = []
    for line in proc.stdout.splitlines()[1:]:
        if any(needle in line for needle in needles) and "board_a_current_blocker_refresh_v1.py" not in line:
            rows.append({"process_line": line.strip()})
    return rows


def main() -> int:
    root = repo_root()
    run = run_root()
    artifact_dir = run / "board-a-current-blocker-refresh-v1"
    checks_dir = run / "checks"
    output_dir = run / "command-output"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    board_path = root / BOARD_REL
    board_text = board_path.read_text(encoding="utf-8")
    cursor = parse_cursor(board_text)
    board_hash = sha256_file(board_path)

    owner_rows = []
    for filename in REQUIRED_OWNER_FILES:
        path = OWNER_EXPORT_ROOT / filename
        owner_rows.append(
            {
                "required_file": filename,
                "path": str(path),
                "present": path.exists(),
                "bytes": path.stat().st_size if path.exists() else 0,
            }
        )

    commands: list[dict[str, object]] = []
    commands.append(run_command("provider_status_agent", ["./target/debug/ict-engine", "provider-status", "--agent"], output_dir, cwd=root))
    for provider in PROVIDERS:
        commands.append(
            run_command(
                f"provider_status_{provider}",
                ["./target/debug/ict-engine", "provider-status", "--agent", "--provider", provider],
                output_dir,
                cwd=root,
            )
        )
    commands.append(
        run_command(
            "auto_quant_status_json",
            [
                "./target/debug/ict-engine",
                "auto-quant-status",
                "--state-dir",
                "/tmp/ict-engine-board-a-current-blocker-refresh-v1-state",
                "--output-format",
                "json",
            ],
            output_dir,
            cwd=root,
            env={**os.environ, "ICT_ENGINE_AUTO_QUANT_DIR": "/Users/thrill3r/Auto-Quant"},
        )
    )
    commands.append(
        run_command(
            "direct_verifier_owner_export_root",
            [
                "python3",
                "docs/experiments/actionable-regime-confidence/runs/"
                "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
                "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py",
                "--intake-root",
                str(OWNER_EXPORT_ROOT),
            ],
            output_dir,
            cwd=root,
        )
    )

    provider_map = {row["name"]: row for row in commands if str(row["name"]).startswith("provider_status")}
    owner_files_all_present = all(row["present"] for row in owner_rows)
    direct_verifier_exit = next(row["exit_code"] for row in commands if row["name"] == "direct_verifier_owner_export_root")
    provider_agent = provider_map.get("provider_status_agent", {})
    provider_ready = provider_agent.get("ready_providers", [])
    provider_pending = provider_agent.get("pending_providers", [])

    status_by_provider: dict[str, str] = {}
    for provider in PROVIDERS:
        cmd = provider_map.get(f"provider_status_{provider}", {})
        pending = cmd.get("pending_providers", [])
        ready = cmd.get("ready_providers", [])
        if ready:
            status_by_provider[provider] = "ready"
        elif pending:
            status_by_provider[provider] = ";".join(str(item) for item in pending)
        else:
            status_by_provider[provider] = str(cmd.get("summary_line", "unknown"))

    checklist_rows = [
        {
            "requirement_id": "R1",
            "requirement": "use Board A markdown as authoritative plan without disturbing concurrent edits",
            "evidence": f"board_hash_before={board_hash}; current_cursor={cursor.get('last_loop_id', '')}",
            "status": "pass_readonly_artifact_only",
            "blocker": "",
        },
        {
            "requirement_id": "R2",
            "requirement": "every regime reaches confidence >=95%",
            "evidence": f"confidence_lane={cursor.get('confidence_lane', '')}; accepted_gate={cursor.get('accepted_gate', '')}",
            "status": "fail_closed",
            "blocker": "current cursor remains blocked; no new accepted >=95 context",
        },
        {
            "requirement_id": "R3",
            "requirement": "verify accepted confidence on other markets and other timeframes",
            "evidence": cursor.get("active_timeframes", ""),
            "status": "fail_closed",
            "blocker": "R6 event/order-lifecycle rows are blocked; no cross-market/timeframe promotion rerun allowed",
        },
        {
            "requirement_id": "R4",
            "requirement": "operate provider -> Auto-Quant -> filter/pre-Bayes -> BBN -> CatBoost/path-ranker -> execution tree",
            "evidence": f"owner_files_all_present={owner_files_all_present}; direct_verifier_exit={direct_verifier_exit}",
            "status": "blocked_before_downstream_chain",
            "blocker": "owner-export controls or explicit FLIP approval absent, so downstream rerun would be invalid",
        },
        {
            "requirement_id": "R5",
            "requirement": "include IBKR, TradingViewRemix/TVR, yfinance/YF, Kraken, Binance, and Bybit provider authority",
            "evidence": json.dumps(status_by_provider, sort_keys=True),
            "status": "fail_closed",
            "blocker": "same-root six-provider AQ authority absent; provider readiness remains incomplete",
        },
        {
            "requirement_id": "R6",
            "requirement": "record real command evidence under docs/experiments instead of speculation",
            "evidence": str(output_dir.relative_to(root)),
            "status": "pass",
            "blocker": "",
        },
        {
            "requirement_id": "R7",
            "requirement": "do not claim trade usability or call update_goal unless strict objective is achieved",
            "evidence": "strict_full_objective_achieved=false; trade_usable=false; update_goal=false",
            "status": "pass",
            "blocker": "",
        },
    ]

    latest_roots = list_latest_roots(root / "docs/experiments/actionable-regime-confidence/runs")
    process_rows = active_process_rows()

    strict_full_objective_achieved = False
    summary = {
        "run_id": RUN_ID,
        "board_hash_before": board_hash,
        "current_cursor": cursor,
        "owner_export_root": str(OWNER_EXPORT_ROOT),
        "owner_export_root_present": OWNER_EXPORT_ROOT.exists(),
        "required_owner_files": owner_rows,
        "owner_files_all_present": owner_files_all_present,
        "direct_verifier_exit_code": direct_verifier_exit,
        "provider_status_by_provider": status_by_provider,
        "provider_agent_ready_providers": provider_ready,
        "provider_agent_pending_providers": provider_pending,
        "auto_quant_status_exit": next(row["exit_code"] for row in commands if row["name"] == "auto_quant_status_json"),
        "same_root_six_provider_aq_authority": False,
        "accepted_95_contexts_added": 0,
        "new_confidence_gate": False,
        "cross_market_timeframe_validation_passed": False,
        "downstream_rerun_allowed": False,
        "canonical_merge_allowed": False,
        "strict_full_objective_achieved": strict_full_objective_achieved,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "board_a_edited": False,
        "active_process_rows": process_rows,
        "latest_run_roots": latest_roots,
        "checklist": checklist_rows,
        "decision": "fail_closed_current_blocker_refresh_only",
        "next_action": (
            "Acquire source-owned R6 normal controls or explicit FLIP-as-control approval, "
            "then populate the owner-export root under shared lock and rerun verifier, "
            "provider/AQ, pre-Bayes/BBN, CatBoost/path-ranker, and execution-tree evidence."
        ),
    }

    summary_path = artifact_dir / "board_a_current_blocker_refresh_v1.json"
    checklist_path = artifact_dir / "prompt_to_artifact_checklist_current_blocker_refresh_v1.csv"
    provider_path = artifact_dir / "provider_status_current_blocker_refresh_v1.csv"
    owner_path = artifact_dir / "owner_export_required_files_current_blocker_refresh_v1.csv"
    roots_path = artifact_dir / "latest_run_roots_current_blocker_refresh_v1.csv"
    proc_path = artifact_dir / "active_processes_current_blocker_refresh_v1.csv"
    report_path = artifact_dir / "board_a_current_blocker_refresh_v1.md"
    assertions_path = checks_dir / "board_a_current_blocker_refresh_v1_assertions.out"

    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(checklist_path, checklist_rows, ["requirement_id", "requirement", "evidence", "status", "blocker"])
    write_csv(
        provider_path,
        [
            {"provider": provider, "status": status_by_provider.get(provider, "")}
            for provider in PROVIDERS
        ],
        ["provider", "status"],
    )
    write_csv(owner_path, owner_rows, ["required_file", "path", "present", "bytes"])
    write_csv(roots_path, latest_roots, ["path", "mtime_ns", "name"])
    write_csv(proc_path, process_rows, ["process_line"] if process_rows else ["process_line"])

    report_lines = [
        "# Board A Current Blocker Refresh v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Board hash before: `{board_hash}`.",
        f"- Current cursor: `{cursor.get('last_loop_id', '')}`.",
        f"- Board state: `{cursor.get('board_state', '')}`.",
        f"- Confidence lane: `{cursor.get('confidence_lane', '')}`.",
        f"- Owner-export root present: `{str(OWNER_EXPORT_ROOT.exists()).lower()}`.",
        f"- Required owner files all present: `{str(owner_files_all_present).lower()}`.",
        f"- Direct verifier exit: `{direct_verifier_exit}`.",
        "- Accepted `>=95%` contexts added: `0`.",
        "- Same-root six-provider AQ authority: `false`.",
        "- Downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun allowed: `false`.",
        "- Strict full objective achieved: `false`; trade usable: `false`; promotion allowed: `false`; `update_goal=false`.",
        "",
        "## Prompt-To-Artifact Checklist",
    ]
    for row in checklist_rows:
        report_lines.append(f"- `{row['requirement_id']}` {row['status']}: {row['requirement']} -- {row['blocker'] or row['evidence']}")
    report_lines.extend(
        [
            "",
            "## Provider Status",
            f"- Aggregate: `{provider_agent.get('summary_line', '')}`.",
        ]
    )
    for provider in PROVIDERS:
        report_lines.append(f"- `{provider}`: `{status_by_provider.get(provider, '')}`.")
    report_lines.extend(
        [
            "",
            "## Evidence",
            f"- Summary JSON: `{summary_path.relative_to(root)}`",
            f"- Checklist CSV: `{checklist_path.relative_to(root)}`",
            f"- Provider CSV: `{provider_path.relative_to(root)}`",
            f"- Owner-export file CSV: `{owner_path.relative_to(root)}`",
            f"- Latest roots CSV: `{roots_path.relative_to(root)}`",
            f"- Active processes CSV: `{proc_path.relative_to(root)}`",
            f"- Command outputs: `{output_dir.relative_to(root)}/`",
            f"- Assertions: `{assertions_path.relative_to(root)}`",
            "",
            "## Next",
            summary["next_action"],
            "",
        ]
    )
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    assertions = [
        f"pass:board_hash_captured:{board_hash}",
        f"pass:cursor_observed:{cursor.get('last_loop_id', '')}",
        f"fail_closed:owner_files_all_present_{str(owner_files_all_present).lower()}",
        f"fail_closed:direct_verifier_exit_{direct_verifier_exit}",
        "fail_closed:same_root_six_provider_aq_authority_false",
        "fail_closed:accepted_95_contexts_added_0",
        "fail_closed:strict_full_objective_achieved_false",
        "promotion_allowed=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    sha_manifest = checks_dir / "sha256_manifest.out"
    manifest_targets = [
        report_path,
        summary_path,
        checklist_path,
        provider_path,
        owner_path,
        roots_path,
        proc_path,
        assertions_path,
    ]
    sha_manifest.write_text(
        "".join(f"{sha256_file(path)}  {path.relative_to(root)}\n" for path in manifest_targets),
        encoding="utf-8",
    )

    print(json.dumps({"run_id": RUN_ID, "report": str(report_path), "strict_full_objective_achieved": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
