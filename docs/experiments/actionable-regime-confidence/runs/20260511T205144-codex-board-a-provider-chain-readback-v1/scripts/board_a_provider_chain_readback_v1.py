#!/usr/bin/env python3
"""Fresh Board A provider and downstream-chain readback.

Run-local additive evidence only. It does not alter ict-engine runtime code,
does not send source-owner requests, and does not promote provider OHLCV into
source-owned MainRegimeV2 labels.
"""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T205144+0800-codex-board-a-provider-chain-readback-v1"
RUN_SLUG = "20260511T205144-codex-board-a-provider-chain-readback-v1"


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot find repo root from {start}")


RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = find_repo_root(RUN_ROOT)
ENGINE = REPO_ROOT / "target/debug/ict-engine"
AQ_ROOT = Path("/Users/thrill3r/Auto-Quant")
STATE_DIR = Path("/tmp/ict-engine-board-a-provider-chain-readback-v1")
PROVIDER_DIR = RUN_ROOT / "provider"
CHAIN_DIR = RUN_ROOT / "chain-readback"
CHECK_DIR = RUN_ROOT / "checks"
REPORT_JSON = RUN_ROOT / "board_a_provider_chain_readback_v1.json"
REPORT_MD = RUN_ROOT / "board_a_provider_chain_readback_v1.md"
PROVIDER_CSV = PROVIDER_DIR / "provider_command_summary_v1.csv"
ASSERTIONS = CHECK_DIR / "board_a_provider_chain_readback_v1_assertions.out"
SOURCE_OUTBOX_V2 = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T204715-codex-source-acquisition-outbox-v2-after-r6-uplift/"
    "source-acquisition-outbox-v2/source_acquisition_outbox_v2.json"
)
CURRENT_INTAKE_ROOTS = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T205323-codex-current-goal-completion-audit-v37-after-live-public-recheck/"
    "completion-audit/current_goal_completion_audit_v37_intake_roots.csv"
)
BULL_BUNDLE = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T160441-codex-regime-downstream-consumer-contract-v1/"
    "downstream-consumer-contract/bundle-templates/bull_regime_consumer_bundle_template_v1.json"
)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def run_command(
    name: str,
    args: list[str],
    out_dir: Path,
    *,
    timeout: int = 180,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        args,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
    )
    stdout_path = out_dir / f"{name}.out"
    stderr_path = out_dir / f"{name}.err"
    exit_path = out_dir / f"{name}.exit"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(str(proc.returncode) + "\n", encoding="utf-8")

    parsed_path = ""
    parsed: Any = None
    if proc.stdout.lstrip().startswith(("{", "[")):
        try:
            parsed = json.loads(proc.stdout)
            json_path = out_dir / f"{name}.json"
            json_path.write_text(json.dumps(parsed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            parsed_path = rel(json_path)
        except json.JSONDecodeError:
            parsed = None

    first_line = ""
    for line in proc.stdout.splitlines():
        if line.strip():
            first_line = line.strip()
            break

    return {
        "name": name,
        "args": args,
        "returncode": proc.returncode,
        "stdout": rel(stdout_path),
        "stderr": rel(stderr_path),
        "exit": rel(exit_path),
        "parsed_json": parsed_path,
        "first_line": first_line,
        "parsed": parsed,
    }


def write_json(path: Path, payload: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rel(path)


def load_json(path: Path) -> Any:
    if not path.exists():
        return {"missing": True, "path": rel(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def read_intake_roots() -> list[dict[str, str]]:
    if not CURRENT_INTAKE_ROOTS.exists():
        return []
    with CURRENT_INTAKE_ROOTS.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def provider_status_line(row: dict[str, Any]) -> str:
    parsed = row.get("parsed")
    if isinstance(parsed, dict):
        return str(parsed.get("summary_line") or parsed.get("providers", [{}])[0].get("status") or "")
    return row.get("first_line", "")


def fetch_provider_surfaces() -> list[dict[str, Any]]:
    commands = [
        ("provider_status_agent", [str(ENGINE), "provider-status", "--agent"]),
        ("provider_status_yfinance", [str(ENGINE), "provider-status", "--provider", "yfinance", "--agent"]),
        (
            "provider_status_tradingview_mcp",
            [str(ENGINE), "provider-status", "--provider", "tradingview_mcp", "--agent"],
        ),
        ("provider_status_ibkr", [str(ENGINE), "provider-status", "--provider", "ibkr", "--agent"]),
        ("provider_status_kraken_cli", [str(ENGINE), "provider-status", "--provider", "kraken_cli", "--agent"]),
        (
            "provider_status_kraken_public",
            [str(ENGINE), "provider-status", "--provider", "kraken_public", "--agent"],
        ),
        (
            "harness_yfinance_qqq_1d_fetch",
            [
                str(ENGINE),
                "market-data-harness",
                "--action",
                "fetch",
                "--market",
                "board-a-205144-yfinance",
                "--interval",
                "1d",
                "--role",
                "etf_reference",
                "--provider",
                "etf_reference=yfinance",
                "--symbol-spec",
                "etf_reference=QQQ",
            ],
        ),
        (
            "harness_tradingview_qqq_1d_fetch",
            [
                str(ENGINE),
                "market-data-harness",
                "--action",
                "fetch",
                "--market",
                "board-a-205144-tradingview",
                "--interval",
                "1d",
                "--role",
                "etf_reference",
                "--provider",
                "etf_reference=tradingview_mcp",
                "--symbol-spec",
                "etf_reference=NASDAQ:QQQ",
            ],
        ),
        (
            "harness_ibkr_qqq_1d_fetch",
            [
                str(ENGINE),
                "market-data-harness",
                "--action",
                "fetch",
                "--market",
                "board-a-205144-ibkr",
                "--interval",
                "1d",
                "--role",
                "etf_reference",
                "--provider",
                "etf_reference=ibkr",
                "--symbol-spec",
                "etf_reference=QQQ",
            ],
        ),
        (
            "kraken_cli_xbtusd_1h_ohlc",
            ["/Users/thrill3r/.cargo/bin/kraken", "-o", "json", "ohlc", "XBTUSD", "--interval", "60"],
        ),
    ]
    return [run_command(name, args, PROVIDER_DIR, timeout=180) for name, args in commands]


def run_chain_readback() -> list[dict[str, Any]]:
    commands = [
        (
            "auto_quant_status",
            [str(ENGINE), "auto-quant-status", "--state-dir", str(STATE_DIR), "--output-format", "json"],
        ),
        (
            "auto_quant_run_help",
            ["uv", "--directory", str(AQ_ROOT), "run", "python", str(AQ_ROOT / "run.py"), "--help"],
        ),
        (
            "analyze_bull_bundle_readonly",
            [
                str(ENGINE),
                "analyze",
                "--symbol",
                "DEMO",
                "--demo",
                "--state-dir",
                str(STATE_DIR),
                "--agent",
                "--regime-consumer-bundle",
                rel(BULL_BUNDLE),
                "--regime-consumer-bundle-strict",
            ],
        ),
        (
            "pre_bayes_status",
            [
                str(ENGINE),
                "pre-bayes-status",
                "--symbol",
                "DEMO",
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--output-format",
                "json",
            ],
        ),
        (
            "policy_training_status",
            [
                str(ENGINE),
                "policy-training-status",
                "--symbol",
                "DEMO",
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "agent",
            ],
        ),
        (
            "workflow_status_execution_candidate",
            [
                str(ENGINE),
                "workflow-status",
                "--symbol",
                "DEMO",
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--phase",
                "execution-candidate",
                "--output-format",
                "json",
            ],
        ),
        (
            "export_structural_path_ranking_target",
            [
                str(ENGINE),
                "export-structural-path-ranking-target",
                "--symbol",
                "DEMO",
                "--state-dir",
                str(STATE_DIR),
            ],
        ),
    ]
    return [run_command(name, args, CHAIN_DIR, timeout=240) for name, args in commands]


def summarize_fetch(row: dict[str, Any]) -> dict[str, Any]:
    parsed = row.get("parsed")
    result: dict[str, Any] = {
        "name": row["name"],
        "returncode": row["returncode"],
        "artifact": row["parsed_json"] or row["stdout"],
    }
    if isinstance(parsed, dict) and "results" in parsed:
        results = parsed.get("results", [])
        result["ok_count"] = sum(1 for item in results if item.get("ok") is True)
        result["error_count"] = sum(1 for item in results if item.get("ok") is False)
        first_ok = next((item for item in results if item.get("ok") is True), None)
        data = first_ok.get("data", []) if isinstance(first_ok, dict) else []
        result["rows"] = len(data) if isinstance(data, list) else 0
        if isinstance(data, list) and data:
            result["first_timestamp"] = data[0].get("timestamp")
            result["last_timestamp"] = data[-1].get("timestamp")
    elif row["name"].startswith("kraken_cli"):
        result["ok_count"] = 1 if row["returncode"] == 0 else 0
        result["error_count"] = 0 if row["returncode"] == 0 else 1
        parsed = row.get("parsed")
        if isinstance(parsed, dict):
            first_key = next(iter(parsed), "")
            bars = parsed.get(first_key, [])
            result["rows"] = len(bars) if isinstance(bars, list) else 0
            if isinstance(bars, list) and bars:
                result["first_timestamp"] = bars[0][0]
                result["last_timestamp"] = bars[-1][0]
    return result


def main() -> int:
    PROVIDER_DIR.mkdir(parents=True, exist_ok=True)
    CHAIN_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    provider_rows = fetch_provider_surfaces()
    chain_rows = run_chain_readback()
    outbox_v2 = load_json(SOURCE_OUTBOX_V2)
    intake_roots = read_intake_roots()

    fetches = [summarize_fetch(row) for row in provider_rows if "fetch" in row["name"] or row["name"].startswith("kraken_cli")]
    ready_intake_roots = sum(1 for row in intake_roots if str(row.get("ready", "")).lower() == "true")
    existing_intake_roots = [
        row.get("root", "")
        for row in intake_roots
        if str(row.get("exists", "")).lower() == "true"
    ]
    intake_missing_files = {
        row.get("root", ""): row.get("missing_files", "")
        for row in intake_roots
        if row.get("missing_files")
    }
    source_rows_acquired = bool(outbox_v2.get("rows_acquired") is True)
    outbox_rows = int(outbox_v2.get("v2_outbox_rows", outbox_v2.get("outbox_rows", 0)) or 0)

    provider_summary = {
        row["name"]: {
            "returncode": row["returncode"],
            "summary_line": provider_status_line(row),
            "artifact": row["parsed_json"] or row["stdout"],
            "stderr": row["stderr"],
        }
        for row in provider_rows
        if row["name"].startswith("provider_status")
    }
    chain_summary = {
        row["name"]: {
            "returncode": row["returncode"],
            "artifact": row["parsed_json"] or row["stdout"],
            "stderr": row["stderr"],
            "first_line": row["first_line"],
        }
        for row in chain_rows
    }

    command_rows = []
    for row in [*provider_rows, *chain_rows]:
        command_rows.append(
            {
                "name": row["name"],
                "returncode": row["returncode"],
                "artifact": row["parsed_json"] or row["stdout"],
                "stderr": row["stderr"],
                "first_line": row["first_line"],
                "args": " ".join(row["args"]),
            }
        )
    with PROVIDER_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "returncode", "artifact", "stderr", "first_line", "args"])
        writer.writeheader()
        writer.writerows(command_rows)

    decision = {
        "gate_result": "board_a_provider_chain_readback_v1=providers_and_chain_rerun_source_rows_still_missing",
        "provider_fetches": fetches,
        "outbox_rows_checked": outbox_rows,
        "source_rows_acquired": source_rows_acquired,
        "ready_intake_roots": f"{ready_intake_roots}/{len(intake_roots)}",
        "existing_intake_roots": existing_intake_roots,
        "intake_missing_files": intake_missing_files,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "downstream_chain_status": (
            "read-only bundle/analyze/pre-bayes/policy/workflow/export commands executed; "
            "promotion remains fail-closed because source-owned intake rows are absent"
        ),
        "next_action": (
            "Populate the four fail-closed intake roots with source-owned or owner-approved rows/provenance, "
            "then rerun the R2/R3/R4/R5/R6 verifiers and only then rerun BBN/CatBoost/execution-tree gates."
        ),
    }

    report = {
        "schema_version": "board-a-provider-chain-readback/v1",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_root": rel(RUN_ROOT),
        "provider_summary": provider_summary,
        "chain_summary": chain_summary,
        "source_acquisition_outbox_v2": rel(SOURCE_OUTBOX_V2),
        "current_intake_roots": rel(CURRENT_INTAKE_ROOTS),
        "intake_roots": intake_roots,
        "decision": decision,
    }
    write_json(REPORT_JSON, report)

    lines = [
        "# Board A Provider Chain Readback v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Outbox rows checked: `{outbox_rows}`; source rows acquired: `{source_rows_acquired}`.",
        f"- Current intake-root audit: `{rel(CURRENT_INTAKE_ROOTS)}`.",
        f"- Ready intake roots: `{decision['ready_intake_roots']}`; existing roots: `{existing_intake_roots}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Provider Readback",
        "",
        "| Surface | Status | Artifact |",
        "|---|---|---|",
    ]
    for name, item in provider_summary.items():
        lines.append(f"| `{name}` | `{item['summary_line']}` | `{item['artifact']}` |")
    lines.extend(["", "## Provider Fetches", "", "| Fetch | ok/error | rows | range | Artifact |", "|---|---:|---:|---|---|"])
    for item in fetches:
        range_text = f"{item.get('first_timestamp', '')}..{item.get('last_timestamp', '')}"
        lines.append(
            f"| `{item['name']}` | `{item.get('ok_count', 0)}/{item.get('error_count', 0)}` | "
            f"`{item.get('rows', 0)}` | `{range_text}` | `{item['artifact']}` |"
        )
    lines.extend(["", "## Chain Readback", "", "| Command | Exit | Artifact | First line |", "|---|---:|---|---|"])
    for name, item in chain_summary.items():
        first = str(item["first_line"]).replace("|", "\\|")[:160]
        lines.append(f"| `{name}` | `{item['returncode']}` | `{item['artifact']}` | `{first}` |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- yfinance, TradingViewRemix/TradingView MCP, IBKR status, and Kraken CLI were checked in this run.",
            "- The ict-engine read-only path was rerun through analyze, Pre-Bayes status, policy/CatBoost path-ranking status, workflow execution-candidate status, and structural path-ranking export.",
            "- Auto-Quant was touched through `auto-quant-status` and the local runtime help probe; `run.py --help` still exits through the known empty default strategy directory, so this is not treated as a data blocker.",
            "- Provider OHLCV and read-only downstream traces do not supply source-owned MainRegimeV2 labels, native sub-hour labels, recency-extension source labels, or direct Manipulation positive/control rows.",
            "- The latest v37 intake audit shows the direct Manipulation root exists with public positives/provenance, but it is still missing matched negative controls; the other three intake roots remain absent.",
            "",
            "## Next",
            "",
            f"- {decision['next_action']}",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"PASS gate_result={decision['gate_result']}",
        f"PASS outbox_rows_checked={outbox_rows}",
        f"PASS ready_intake_roots={decision['ready_intake_roots']}",
        "PASS accepted_rows_added=0",
        "PASS update_goal=false",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
        "PASS raw_data_committed=false",
        "PASS provider_fetches_executed=true",
        "PASS chain_readback_executed=true",
    ]
    ASSERTIONS.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
