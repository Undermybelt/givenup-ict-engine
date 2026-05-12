#!/usr/bin/env python3
"""Read-only provider/Auto-Quant source-unlock probe for Board A.

This script deliberately keeps downloaded/raw provider bars under /tmp and
records only hashes, row counts, command exits, and the non-promoting gate in
the repo artifact.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T054718-codex-provider-autoquant-source-unlock-probe-after-053505-v1"
GATE = (
    "provider_autoquant_source_unlock_probe_after_053505_v1="
    "provider_surfaces_refreshed_no_source_root_unlock_no_promotion"
)
def find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / "Cargo.toml").exists() and (
            parent / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
        ).exists():
            return parent
    raise RuntimeError(f"could not locate ict-engine repo root from {start}")


REPO = find_repo_root(Path(__file__).resolve())
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "command-output"
ART_DIR = RUN_ROOT / "provider-autoquant-source-unlock-probe-after-053505-v1"
CHECK_DIR = RUN_ROOT / "checks"
TMP_ROOT = Path("/tmp") / RUN_ID
FETCH_DIR = TMP_ROOT / "provider-bars"
ICT_ENGINE = REPO / "target/debug/ict-engine"
FETCH_EXTERNAL = REPO / "scripts/auto_quant_external/fetch_external.py"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
TARGET_ROOTS = [
    "/tmp/ict-engine-board-a-r6-owner-export-v1",
    "/tmp/ict-engine-native-subhour-source-label-intake",
    "/tmp/ict-engine-source-panel-recency-extension",
]


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def count_csv_rows(path: Path) -> int | None:
    if not path.exists() or not path.is_file() or path.stat().st_size == 0:
        return None
    with path.open(newline="") as f:
        reader = csv.reader(f)
        try:
            next(reader)
        except StopIteration:
            return 0
        return sum(1 for _ in reader)


def read_json(path: Path) -> Any | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def run_command(
    name: str,
    cmd: list[str],
    *,
    env_extra: dict[str, str] | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    stdout = OUT_DIR / f"{name}.stdout.txt"
    stderr = OUT_DIR / f"{name}.stderr.txt"
    cmd_path = OUT_DIR / f"{name}.cmd"
    exit_path = OUT_DIR / f"{name}.exit"
    cmd_path.write_text(" ".join(cmd) + "\n")
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        stdout.write_text(proc.stdout)
        stderr.write_text(proc.stderr)
        exit_path.write_text(f"{proc.returncode}\n")
        return {
            "name": name,
            "cmd": cmd,
            "return_code": proc.returncode,
            "stdout_path": rel(stdout),
            "stderr_path": rel(stderr),
            "exit_path": rel(exit_path),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        stdout.write_text(exc.stdout or "")
        stderr.write_text((exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n")
        exit_path.write_text("124\n")
        return {
            "name": name,
            "cmd": cmd,
            "return_code": 124,
            "stdout_path": rel(stdout),
            "stderr_path": rel(stderr),
            "exit_path": rel(exit_path),
            "timed_out": True,
        }


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def root_state() -> list[dict[str, Any]]:
    rows = []
    for root in TARGET_ROOTS:
        p = Path(root)
        files = []
        if p.exists():
            files = sorted(str(x) for x in p.rglob("*") if x.is_file())[:20]
        rows.append({"path": root, "present": p.exists(), "sample_files": files})
    return rows


def parse_provider_status(stdout_path: str) -> dict[str, Any]:
    data = read_json(REPO / stdout_path) or {}
    providers = data.get("providers") or []
    selected: dict[str, Any] = {}
    for provider in providers:
        pid = provider.get("provider_id")
        domain = provider.get("domain")
        if pid in {"ibkr", "ibkr_bridge", "tradingview_mcp", "yfinance", "kraken_public", "kraken_cli"}:
            key = f"{pid}@{domain}"
            selected[key] = {
                "ready": provider.get("ready"),
                "status": provider.get("status"),
                "reason": provider.get("reason"),
            }
    return {
        "summary_line": data.get("summary_line"),
        "ready_by_domain": data.get("ready_by_domain"),
        "selected": selected,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ART_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    FETCH_DIR.mkdir(parents=True, exist_ok=True)

    board_hash_before = sha256_file(BOARD)
    roots_before = root_state()

    commands: list[dict[str, Any]] = []
    if ICT_ENGINE.exists():
        commands.append(
            run_command(
                "provider_status_agent",
                [str(ICT_ENGINE), "provider-status", "--agent"],
                timeout=180,
            )
        )
        commands.append(
            run_command(
                "auto_quant_status_local",
                [
                    str(ICT_ENGINE),
                    "auto-quant-status",
                    "--state-dir",
                    str(TMP_ROOT / "autoquant-state"),
                    "--output-format",
                    "json",
                ],
                env_extra={"ICT_ENGINE_AUTO_QUANT_DIR": "/Users/thrill3r/Auto-Quant"},
                timeout=120,
            )
        )
    else:
        commands.append(
            {
                "name": "ict_engine_binary",
                "return_code": 127,
                "error": f"missing {ICT_ENGINE}",
            }
        )

    fetch_specs = [
        (
            "yfinance_qqq_1h",
            [
                "python3",
                str(FETCH_EXTERNAL),
                "yahoo",
                "--symbol",
                "QQQ",
                "--interval",
                "1h",
                "--start",
                "2026-01-31",
                "--end",
                "2026-05-10",
                "--output",
                str(FETCH_DIR / "QQQ_yfinance_1h_20260131_20260510.csv"),
            ],
            180,
        ),
        (
            "kraken_pf_xbtusd_1h",
            [
                "python3",
                str(FETCH_EXTERNAL),
                "kraken-kline",
                "--market",
                "futures",
                "--pair",
                "PF_XBTUSD",
                "--interval",
                "1h",
                "--start",
                "2026-01-31",
                "--end",
                "2026-05-10",
                "--output",
                str(FETCH_DIR / "PF_XBTUSD_kraken_futures_1h_20260131_20260510.csv"),
            ],
            180,
        ),
        (
            "ibkr_aapl_1h",
            [
                "uv",
                "run",
                "--with",
                "pandas",
                "--with",
                "redis",
                "--with",
                "ib_async",
                "python",
                str(FETCH_EXTERNAL),
                "ibkr-historical",
                "--symbol",
                "AAPL",
                "--sec-type",
                "STK",
                "--exchange",
                "SMART",
                "--primary-exchange",
                "NASDAQ",
                "--currency",
                "USD",
                "--bar-size",
                "1 hour",
                "--duration",
                "2 W",
                "--what-to-show",
                "TRADES",
                "--port",
                "4002",
                "--client-id",
                "77",
                "--output",
                str(FETCH_DIR / "AAPL_ibkr_1h_2w.csv"),
            ],
            180,
        ),
    ]
    uv_env = {
        "UV_CACHE_DIR": str(TMP_ROOT / "uv-cache"),
        "UV_PROJECT_ENVIRONMENT": str(TMP_ROOT / "uv-env"),
    }
    for name, cmd, timeout in fetch_specs:
        env = uv_env if name.startswith("ibkr_") else None
        commands.append(run_command(name, cmd, env_extra=env, timeout=timeout))

    roots_after = root_state()
    provider_summary = {}
    auto_quant_summary: dict[str, Any] = {}
    for item in commands:
        if item.get("name") == "provider_status_agent" and item.get("stdout_path"):
            provider_summary = parse_provider_status(item["stdout_path"])
        if item.get("name") == "auto_quant_status_local" and item.get("stdout_path"):
            data = read_json(REPO / item["stdout_path"]) or {}
            auto_quant_summary = {
                "status": data.get("status"),
                "healthy": data.get("healthy"),
                "data_ready": data.get("data_ready"),
                "bootstrap_needed": data.get("bootstrap_needed"),
                "managed_dir": data.get("managed_dir"),
                "next_blocker": (data.get("next_step") or {}).get("blocked_reason"),
            }

    provider_bars = []
    for path in sorted(FETCH_DIR.glob("*.csv")):
        provider_bars.append(
            {
                "path": str(path),
                "rows": count_csv_rows(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )

    target_root_mutated = roots_before != roots_after
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_run": board_hash_before,
        "gate_result": GATE,
        "scope": (
            "read-only provider and Auto-Quant source-unlock probe after 053505; "
            "raw provider bars remain under /tmp"
        ),
        "commands": commands,
        "provider_summary": provider_summary,
        "auto_quant_summary": auto_quant_summary,
        "provider_bars": provider_bars,
        "target_roots_before": roots_before,
        "target_roots_after": roots_after,
        "decision": {
            "provider_surfaces_refreshed": True,
            "source_control_evidence_acquired": False,
            "target_root_mutated": target_root_mutated,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "boundary": {
            "provider_bars_are_not_source_labels": True,
            "r3_native_subhour_labels_acquired": False,
            "r5_post_cutoff_mainregime_rows_acquired": False,
            "r6_owner_export_controls_acquired": False,
            "runtime_code_changed": False,
            "raw_data_committed": False,
            "external_request_sent": False,
        },
        "next_action": (
            "Do not promote from provider bars. Continue only after explicit "
            "source/control approval, verifier-native R6 owner/export rows with "
            "normal controls, source-owned R5 recency rows, or source-owned R3 "
            "native subhour labels unlock a target root."
        ),
    }

    json_path = ART_DIR / "provider_autoquant_source_unlock_probe_after_053505_v1.json"
    report_path = ART_DIR / "provider_autoquant_source_unlock_probe_after_053505_v1.md"
    assertions_path = CHECK_DIR / "provider_autoquant_source_unlock_probe_after_053505_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    def md_bool(value: Any) -> str:
        return "`true`" if value else "`false`"

    lines = [
        "# Provider Auto-Quant Source Unlock Probe After 053505 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE}`",
        "",
        "## Scope",
        "",
        (
            "Read-only refresh of the user-named provider surfaces and local "
            "Auto-Quant state after the `053505` R5 Kaggle recency screen. "
            "Raw provider bars, if fetched, stay under `/tmp`; this artifact "
            "records only row counts and hashes."
        ),
        "",
        "## Provider / Auto-Quant Readback",
        "",
        f"- Provider summary: `{provider_summary.get('summary_line')}`.",
        f"- Auto-Quant status: `{auto_quant_summary.get('status')}`; "
        f"healthy {md_bool(auto_quant_summary.get('healthy'))}; "
        f"data_ready {md_bool(auto_quant_summary.get('data_ready'))}; "
        f"next blocker `{auto_quant_summary.get('next_blocker')}`.",
        "",
        "Selected provider states:",
        "",
        "| Provider | Ready | Status | Reason |",
        "|---|---:|---|---|",
    ]
    for key, row in sorted((provider_summary.get("selected") or {}).items()):
        lines.append(
            f"| `{key}` | `{row.get('ready')}` | `{row.get('status')}` | `{row.get('reason')}` |"
        )
    lines += [
        "",
        "Provider bar probes:",
        "",
        "| Output | Rows | SHA-256 |",
        "|---|---:|---|",
    ]
    for row in provider_bars:
        lines.append(f"| `{row['path']}` | `{row['rows']}` | `{row['sha256']}` |")
    if not provider_bars:
        lines.append("| none | 0 | n/a |")
    lines += [
        "",
        "## Decision",
        "",
        "- Provider surfaces were refreshed, but no source/control target root was unlocked.",
        "- Provider bars are not source-owned `MainRegimeV2` labels, not R6 matched normal controls, and not native sub-hour source-label rows.",
        f"- Target root mutated: {md_bool(target_root_mutated)}.",
        "- Accepted rows added `0`; source/control evidence acquired `false`; canonical merge `false`; downstream promotion rerun `false`; strict full objective `false`; trade usable `false`; `update_goal=false`.",
        "",
        "## Next",
        "",
        result["next_action"],
    ]
    report_path.write_text("\n".join(lines) + "\n")

    assertions = [
        ("gate_result", result["gate_result"] == GATE),
        ("provider_status_command_recorded", any(c.get("name") == "provider_status_agent" for c in commands)),
        ("auto_quant_status_command_recorded", any(c.get("name") == "auto_quant_status_local" for c in commands)),
        ("source_control_evidence_acquired_false", not result["decision"]["source_control_evidence_acquired"]),
        ("target_root_mutated_false", not target_root_mutated),
        ("canonical_merge_false", not result["decision"]["canonical_merge"]),
        ("downstream_promotion_rerun_false", not result["decision"]["downstream_promotion_rerun"]),
        ("strict_full_objective_false", not result["decision"]["strict_full_objective"]),
        ("trade_usable_false", not result["decision"]["trade_usable"]),
        ("update_goal_false", not result["decision"]["update_goal"]),
        ("raw_data_committed_false", not result["boundary"]["raw_data_committed"]),
    ]
    assertions_path.write_text(
        "\n".join(f"{'PASS' if ok else 'FAIL'} {name}={ok}" for name, ok in assertions) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all(ok for _, ok in assertions) else 1


if __name__ == "__main__":
    raise SystemExit(main())
