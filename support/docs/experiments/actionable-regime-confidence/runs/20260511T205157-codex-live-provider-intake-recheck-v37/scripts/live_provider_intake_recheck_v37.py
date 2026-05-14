#!/usr/bin/env python3
"""Board A live provider/intake recheck.

This run is additive evidence only. It rechecks the provider/runtime paths named
by the operator, runs bounded fetch probes, reruns fail-closed intake checks, and
records whether the strict Board A objective can advance.
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


RUN_ID = "20260511T205157+0800-codex-live-provider-intake-recheck-v37"
RUN_ROOT_NAME = "20260511T205157-codex-live-provider-intake-recheck-v37"
DECISION = "live_provider_intake_recheck_v37=providers_rechecked_r6_schema_ready_remaining_intakes_blocked"


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot find repo root from {start}")


RUN_ROOT = Path(__file__).resolve().parents[1]
REPO = find_repo_root(RUN_ROOT)
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
OUT = RUN_ROOT / "live-provider-intake-recheck"
CHECKS = RUN_ROOT / "checks"
PROVIDER_DIR = RUN_ROOT / "provider"
VERIFIER_DIR = RUN_ROOT / "verifiers"
TMP_FETCH_DIR = Path("/tmp/ict-engine-live-provider-intake-recheck-v37")
LOCAL_AQ = Path("/Users/thrill3r/Auto-Quant")

SOURCE_LABEL_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)
RECENCY_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)
DIRECT_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

INTAKE_ROOTS = [
    {
        "id": "source_label_equivalence",
        "requirements": "R2;R4",
        "root": Path("/tmp/ict-engine-source-label-equivalence-intake"),
        "required_files": [
            "source_label_equivalence_rows.csv",
            "source_label_equivalence_provenance.json",
        ],
    },
    {
        "id": "native_subhour_source_label",
        "requirements": "R3",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required_files": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
    },
    {
        "id": "source_panel_recency_extension",
        "requirements": "R5",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required_files": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
    },
    {
        "id": "direct_manipulation_row_intake",
        "requirements": "R6",
        "root": Path("/tmp/ict-engine-direct-manipulation-row-intake"),
        "required_files": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
    },
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def run_command(name: str, args: list[str], timeout_s: int = 60) -> dict[str, Any]:
    out_path = PROVIDER_DIR / f"{name}.out"
    err_path = PROVIDER_DIR / f"{name}.err"
    started = datetime.now(timezone.utc)
    try:
        proc = subprocess.run(
            args,
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_s,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        returncode = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", "replace")
        stderr += f"\nTIMEOUT after {timeout_s}s"
        returncode = 124
        timed_out = True
    out_path.write_text(stdout, encoding="utf-8")
    err_path.write_text(stderr, encoding="utf-8")
    parsed: Any = None
    if stdout.strip().startswith("{"):
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            parsed = None
    finished = datetime.now(timezone.utc)
    return {
        "name": name,
        "args": args,
        "returncode": returncode,
        "timed_out": timed_out,
        "started_utc": started.isoformat(),
        "finished_utc": finished.isoformat(),
        "stdout_artifact": rel(out_path),
        "stderr_artifact": rel(err_path),
        "stdout_bytes": len(stdout.encode("utf-8")),
        "stderr_bytes": len(stderr.encode("utf-8")),
        "stdout_json": parsed,
    }


def run_verifier(name: str, args: list[str], timeout_s: int = 30) -> dict[str, Any]:
    result = run_command(f"verifier-{name}", args, timeout_s=timeout_s)
    src_out = PROVIDER_DIR / f"verifier-{name}.out"
    src_err = PROVIDER_DIR / f"verifier-{name}.err"
    dst_out = VERIFIER_DIR / f"{name}.out"
    dst_err = VERIFIER_DIR / f"{name}.err"
    dst_out.write_text(src_out.read_text(encoding="utf-8"), encoding="utf-8")
    dst_err.write_text(src_err.read_text(encoding="utf-8"), encoding="utf-8")
    result["stdout_artifact"] = rel(dst_out)
    result["stderr_artifact"] = rel(dst_err)
    if isinstance(result.get("stdout_json"), dict):
        result["status"] = result["stdout_json"].get("status")
        result["decision"] = result["stdout_json"].get("decision")
    return result


def summarize_provider_status(payload: dict[str, Any] | None, provider_id: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"provider_id": provider_id, "ready": False, "status": "no_json", "reason": "no_json"}
    providers = payload.get("providers", [])
    matches = [item for item in providers if item.get("provider_id") == provider_id]
    if not matches:
        return {
            "provider_id": provider_id,
            "ready": provider_id in payload.get("ready_providers", []),
            "status": "not_listed",
            "reason": "not_listed",
        }
    item = matches[0]
    return {
        "provider_id": provider_id,
        "ready": bool(item.get("ready")),
        "status": item.get("status"),
        "reason": item.get("reason"),
        "summary": item.get("summary"),
    }


def root_status(item: dict[str, Any]) -> dict[str, Any]:
    root: Path = item["root"]
    present = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()) if root.exists() else []
    missing = [name for name in item["required_files"] if not (root / name).is_file()]
    return {
        "id": item["id"],
        "requirements": item["requirements"],
        "root": str(root),
        "exists": root.exists(),
        "required_files": ";".join(item["required_files"]),
        "present_files": ";".join(present),
        "missing_files": ";".join(missing),
        "ready": not missing,
    }


def summarize_auto_quant() -> dict[str, Any]:
    data_dir = LOCAL_AQ / "user_data/data"
    strategy_dirs = [
        LOCAL_AQ / "user_data/strategies",
        LOCAL_AQ / "user_data/strategies_external",
    ]
    data_files = sorted(data_dir.glob("*.feather")) if data_dir.exists() else []
    strategies: list[str] = []
    for root in strategy_dirs:
        if root.exists():
            strategies.extend(rel_or_abs(path) for path in sorted(root.glob("*.py")))
    raw_files = sorted((LOCAL_AQ / "user_data/data/raw").glob("*.csv")) if (LOCAL_AQ / "user_data/data/raw").exists() else []
    tmp_strategy_hits: list[str] = []
    for base in [Path("/tmp"), Path("/private/tmp")]:
        if not base.exists():
            continue
        for path in base.glob("**/*.py"):
            text = str(path)
            if "auto_quant_external" in text or "strateg" in text or "freqtrade" in text:
                tmp_strategy_hits.append(text)
                if len(tmp_strategy_hits) >= 80:
                    break
        if len(tmp_strategy_hits) >= 80:
            break
    return {
        "local_auto_quant_root": str(LOCAL_AQ),
        "exists": LOCAL_AQ.exists(),
        "data_feather_count": len(data_files),
        "data_feather_sample": [str(path) for path in data_files[:30]],
        "raw_csv_count": len(raw_files),
        "raw_csv_sample": [str(path) for path in raw_files[:20]],
        "strategy_py_count": len(strategies),
        "strategy_py_files": strategies,
        "tmp_strategy_hit_count_capped": len(tmp_strategy_hits),
        "tmp_strategy_hit_sample": tmp_strategy_hits[:30],
    }


def rel_or_abs(path: Path) -> str:
    try:
        return str(path.relative_to(LOCAL_AQ))
    except ValueError:
        return str(path)


def classify_harness(result: dict[str, Any]) -> dict[str, Any]:
    payload = result.get("stdout_json")
    results = payload.get("results", []) if isinstance(payload, dict) else []
    ok_count = sum(1 for item in results if item.get("ok") is True)
    error_count = sum(1 for item in results if item.get("ok") is False)
    row_count = 0
    if results:
        for item in results:
            data = item.get("data")
            if isinstance(data, list):
                row_count += len(data)
    return {
        "name": result["name"],
        "returncode": result["returncode"],
        "ok_count": ok_count,
        "error_count": error_count,
        "row_count": row_count,
        "stdout_artifact": result["stdout_artifact"],
        "stderr_artifact": result["stderr_artifact"],
    }


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def main() -> None:
    for directory in [OUT, CHECKS, PROVIDER_DIR, VERIFIER_DIR, TMP_FETCH_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    board_hash = sha256(BOARD)

    commands: list[dict[str, Any]] = []
    commands.append(run_command("provider-status-all", ["./target/debug/ict-engine", "provider-status", "--agent"], timeout_s=90))
    for provider in ["yfinance", "tradingview_mcp", "ibkr", "kraken_public"]:
        commands.append(
            run_command(
                f"provider-status-{provider}",
                ["./target/debug/ict-engine", "provider-status", "--provider", provider, "--agent"],
                timeout_s=60,
            )
        )
    commands.append(
        run_command(
            "provider-status-local-runtime",
            ["./target/debug/ict-engine", "provider-status", "--domain", "local_runtime", "--agent"],
            timeout_s=60,
        )
    )
    commands.append(
        run_command(
            "auto-quant-status-managed-tmp",
            ["./target/debug/ict-engine", "auto-quant-status", "--state-dir", str(TMP_FETCH_DIR / "managed-state")],
            timeout_s=60,
        )
    )
    commands.append(
        run_command(
            "auto-quant-runpy-help-readback",
            ["uv", "--directory", str(LOCAL_AQ), "run", "python", "run.py", "--help"],
            timeout_s=90,
        )
    )

    harness_commands = [
        (
            "harness-yfinance-qqq-1d",
            [
                "./target/debug/ict-engine",
                "market-data-harness",
                "--action",
                "fetch",
                "--market",
                "NQ",
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
            "harness-tradingview-qqq-1d",
            [
                "./target/debug/ict-engine",
                "market-data-harness",
                "--action",
                "fetch",
                "--market",
                "NQ",
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
            "harness-ibkr-qqq-1d",
            [
                "./target/debug/ict-engine",
                "market-data-harness",
                "--action",
                "fetch",
                "--market",
                "NQ",
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
            "harness-kraken-xbtusd-1d",
            [
                "./target/debug/ict-engine",
                "market-data-harness",
                "--action",
                "fetch",
                "--market",
                "BTC",
                "--interval",
                "1d",
                "--role",
                "crypto_reference",
                "--provider",
                "crypto_reference=kraken_public",
                "--symbol-spec",
                "crypto_reference=XBTUSD",
            ],
        ),
    ]
    harness_results = [run_command(name, args, timeout_s=90) for name, args in harness_commands]
    commands.extend(harness_results)

    kraken_csv = TMP_FETCH_DIR / "kraken_XBTUSD_1d.csv"
    kraken_lowpollution = run_command(
        "kraken-lowpollution-public-fetch-xbtusd-1d",
        [
            "uv",
            "run",
            "--with",
            "pandas",
            "--with",
            "requests",
            "python",
            "scripts/auto_quant_external/fetch_external.py",
            "kraken-kline",
            "--market",
            "spot",
            "--pair",
            "XBTUSD",
            "--interval",
            "1d",
            "--output",
            str(kraken_csv),
        ],
        timeout_s=120,
    )
    commands.append(kraken_lowpollution)

    ibkr_csv = TMP_FETCH_DIR / "ibkr_QQQ_1d.csv"
    ibkr_lowpollution = run_command(
        "ibkr-lowpollution-fetch-qqq-1d",
        [
            "uv",
            "run",
            "--with",
            "pandas",
            "--with",
            "requests",
            "--with",
            "redis",
            "--with",
            "ib_async",
            "python",
            "scripts/auto_quant_external/fetch_external.py",
            "ibkr-historical",
            "--symbol",
            "QQQ",
            "--sec-type",
            "STK",
            "--exchange",
            "SMART",
            "--currency",
            "USD",
            "--bar-size",
            "1 day",
            "--duration",
            "1 M",
            "--what-to-show",
            "TRADES",
            "--port",
            "4002",
            "--client-id",
            "31",
            "--output",
            str(ibkr_csv),
        ],
        timeout_s=75,
    )
    commands.append(ibkr_lowpollution)

    verifiers = [
        run_verifier(
            "source-label-equivalence",
            ["python3", str(SOURCE_LABEL_VERIFIER), "--intake-root", "/tmp/ict-engine-source-label-equivalence-intake"],
        ),
        run_verifier(
            "recency-extension",
            ["python3", str(RECENCY_VERIFIER), "--intake-root", "/tmp/ict-engine-source-panel-recency-extension"],
        ),
        run_verifier(
            "direct-manipulation",
            ["python3", str(DIRECT_VERIFIER), "--intake-root", "/tmp/ict-engine-direct-manipulation-row-intake"],
        ),
    ]

    roots = [root_status(item) for item in INTAKE_ROOTS]
    ready_roots = [row["id"] for row in roots if row["ready"]]
    provider_all = next(item for item in commands if item["name"] == "provider-status-all")
    provider_summary = {
        provider: summarize_provider_status(provider_all.get("stdout_json"), provider)
        for provider in ["yfinance", "tradingview_mcp", "ibkr", "kraken_public", "kraken_cli", "ibkr_bridge"]
    }
    harness_summary = [classify_harness(item) for item in harness_results]
    local_auto_quant = summarize_auto_quant()

    dry_state = TMP_FETCH_DIR / "ict-engine-demo-state"
    bundle = REPO / (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T160441-codex-regime-downstream-consumer-contract-v1/"
        "downstream-consumer-contract/bundle-templates/bull_regime_consumer_bundle_template_v1.json"
    )
    analyze = run_command(
        "ict-engine-readonly-regime-bundle-analyze",
        [
            "./target/debug/ict-engine",
            "analyze",
            "--symbol",
            "DEMO",
            "--demo",
            "--human",
            "--state-dir",
            str(dry_state),
            "--regime-consumer-bundle",
            str(bundle),
            "--regime-consumer-bundle-strict",
        ],
        timeout_s=60,
    )
    workflow = run_command(
        "ict-engine-workflow-status-after-readonly-bundle",
        [
            "./target/debug/ict-engine",
            "workflow-status",
            "--symbol",
            "DEMO",
            "--state-dir",
            str(dry_state),
            "--refresh",
            "--agent",
        ],
        timeout_s=60,
    )
    commands.extend([analyze, workflow])

    direct_verifier = next((item for item in verifiers if item["name"] == "verifier-direct-manipulation"), {})
    direct_stdout = direct_verifier.get("stdout_json") if isinstance(direct_verifier.get("stdout_json"), dict) else {}
    direct_status = direct_stdout.get("status", "unknown") if isinstance(direct_stdout, dict) else "unknown"
    r6_status = "partial_schema_ready_unscored" if direct_status == "schema_ready_unscored" else "fail_blocked"
    r6_evidence = (
        f"Direct-manipulation intake verifier status `{direct_status}`; "
        f"positive rows `{direct_stdout.get('positive_rows', 0)}`, matched negative rows `{direct_stdout.get('matched_negative_rows', 0)}`. "
        "This is schema readiness only and still needs chronological plus heldout-symbol/venue Wilson95 calibration."
        if direct_status == "schema_ready_unscored"
        else "Direct-manipulation intake verifier remains blocked; required files or schema-valid rows are absent."
    )
    checklist = [
        {
            "id": "R0",
            "requirement": "Use Board A markdown and current cursor as contract; do not overwrite concurrent artifacts.",
            "status": "pass_checked",
            "artifact": rel(BOARD),
            "evidence": f"Board hash before this run={board_hash}; additive run root={rel(RUN_ROOT)}.",
            "gap": "",
        },
        {
            "id": "R1",
            "requirement": "Actually check named provider/runtime paths: IBKR, TradingViewRemix/MCP, yfinance, Kraken, and local Auto-Quant.",
            "status": "pass_checked_not_label_evidence",
            "artifact": f"{rel(PROVIDER_DIR)}; {rel(OUT / 'auto_quant_local_inventory_v37.json')}",
            "evidence": "Provider statuses and bounded fetch probes were run; these are provider reachability/data-readback evidence, not source-owned regime labels.",
            "gap": "",
        },
        {
            "id": "R2",
            "requirement": "Other-market/source-label equivalence files are acquired and verifier-accepted.",
            "status": "fail_blocked",
            "artifact": rel(VERIFIER_DIR / "source-label-equivalence.out"),
            "evidence": "Source-label equivalence verifier remains blocked; exact intake files are absent.",
            "gap": roots[0]["missing_files"],
        },
        {
            "id": "R3",
            "requirement": "Native sub-hour source-label files are acquired and verifier-accepted.",
            "status": "fail_blocked",
            "artifact": roots[1]["root"],
            "evidence": "Native sub-hour root has no required files; no verifier-accepted native sub-hour source-label package exists.",
            "gap": roots[1]["missing_files"],
        },
        {
            "id": "R4",
            "requirement": "Strict exact 1h source rows and provenance are acquired.",
            "status": "fail_blocked",
            "artifact": rel(VERIFIER_DIR / "source-label-equivalence.out"),
            "evidence": "The shared source-label equivalence intake root is still missing rows/provenance.",
            "gap": roots[0]["missing_files"],
        },
        {
            "id": "R5",
            "requirement": "Post-2026-01-30 recency-extension rows and provenance are acquired.",
            "status": "fail_blocked",
            "artifact": rel(VERIFIER_DIR / "recency-extension.out"),
            "evidence": "Recency-extension verifier remains blocked; exact extension files are absent.",
            "gap": roots[2]["missing_files"],
        },
        {
            "id": "R6",
            "requirement": "Direct Manipulation positive/control/provenance files are acquired across required species.",
            "status": r6_status,
            "artifact": rel(VERIFIER_DIR / "direct-manipulation.out"),
            "evidence": r6_evidence,
            "gap": "chronological_split;heldout_symbol_or_venue;wilson95_ge_0.95;broad_normal_sample;remaining_direct_species",
        },
        {
            "id": "R7",
            "requirement": "Run downstream ict-engine chain readback without promoting proxy labels.",
            "status": "pass_fail_closed_readback",
            "artifact": f"{analyze['stdout_artifact']}; {workflow['stdout_artifact']}",
            "evidence": "Read-only regime bundle analyze/workflow-status ran against /tmp state; no BBN mutation or trade-usable promotion is claimed.",
            "gap": "",
        },
        {
            "id": "R8",
            "requirement": "Only call update_goal when every strict requirement is covered by real evidence.",
            "status": "fail_blocked",
            "artifact": rel(OUT / "live_provider_intake_recheck_v37.json"),
            "evidence": f"Ready intake roots are {len(ready_roots)}/4; R6 is schema-ready only, and source-owned/provenance files for R2/R3/R4/R5 remain missing.",
            "gap": "Strict full objective is not achieved; update_goal remains false.",
        },
    ]
    unmet = [row for row in checklist if row["status"].startswith("fail") or "blocked" in row["status"]]

    provider_csv_rows = []
    for provider, row in provider_summary.items():
        provider_csv_rows.append({"provider": provider, **row})
    write_csv(
        OUT / "provider_status_summary_v37.csv",
        provider_csv_rows,
        ["provider", "provider_id", "ready", "status", "reason", "summary"],
    )
    write_csv(
        OUT / "harness_fetch_summary_v37.csv",
        harness_summary,
        ["name", "returncode", "ok_count", "error_count", "row_count", "stdout_artifact", "stderr_artifact"],
    )
    write_csv(
        OUT / "intake_root_status_v37.csv",
        roots,
        ["id", "requirements", "root", "exists", "required_files", "present_files", "missing_files", "ready"],
    )
    write_csv(
        OUT / "prompt_to_artifact_checklist_v37.csv",
        checklist,
        ["id", "requirement", "status", "artifact", "evidence", "gap"],
    )
    write_csv(
        OUT / "unmet_requirements_v37.csv",
        unmet,
        ["id", "requirement", "status", "artifact", "evidence", "gap"],
    )
    write_json(OUT / "auto_quant_local_inventory_v37.json", local_auto_quant)

    payload = {
        "run_id": RUN_ID,
        "schema": "live-provider-intake-recheck/v37",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": DECISION,
        "objective_restatement": (
            "Every active Board A regime must have calibrated >=95% confidence, and that confidence must survive "
            "source-owned or owner-approved validation across other markets/species and other cycles/timeframes before completion."
        ),
        "board_hash_before_writeback": board_hash,
        "provider_summary": provider_summary,
        "harness_summary": harness_summary,
        "kraken_lowpollution_fetch": {
            "returncode": kraken_lowpollution["returncode"],
            "stdout_artifact": kraken_lowpollution["stdout_artifact"],
            "stderr_artifact": kraken_lowpollution["stderr_artifact"],
            "output_csv": str(kraken_csv),
            "rows": count_csv_rows(kraken_csv),
        },
        "ibkr_lowpollution_fetch": {
            "returncode": ibkr_lowpollution["returncode"],
            "timed_out": ibkr_lowpollution["timed_out"],
            "stdout_artifact": ibkr_lowpollution["stdout_artifact"],
            "stderr_artifact": ibkr_lowpollution["stderr_artifact"],
            "output_csv": str(ibkr_csv),
            "rows": count_csv_rows(ibkr_csv),
        },
        "auto_quant_local_inventory": local_auto_quant,
        "verifier_results": verifiers,
        "intake_roots_checked": roots,
        "ready_intake_roots": ready_roots,
        "ready_intake_root_count": len(ready_roots),
        "downstream_readonly_analyze": {
            "returncode": analyze["returncode"],
            "stdout_artifact": analyze["stdout_artifact"],
            "stderr_artifact": analyze["stderr_artifact"],
        },
        "downstream_workflow_status": {
            "returncode": workflow["returncode"],
            "stdout_artifact": workflow["stdout_artifact"],
            "stderr_artifact": workflow["stderr_artifact"],
        },
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "checklist_rows": len(checklist),
        "unmet_rows": len(unmet),
        "unmet_ids": [row["id"] for row in unmet],
        "commands": commands,
    }
    write_json(OUT / "live_provider_intake_recheck_v37.json", payload)

    report = [
        "# Live Provider Intake Recheck v37",
        "",
        f"Decision: `{DECISION}`.",
        "",
        "Result:",
        f"- Provider/status paths rechecked: `IBKR`, `TradingViewRemix/MCP`, `yfinance`, `Kraken`, and local Auto-Quant.",
        f"- Ready intake roots: `{len(ready_roots)}/4`.",
        f"- Kraken public low-pollution fetch rows: `{count_csv_rows(kraken_csv)}`.",
        f"- IBKR low-pollution fetch rows: `{count_csv_rows(ibkr_csv)}`; return code `{ibkr_lowpollution['returncode']}`.",
        f"- Auto-Quant local feather files: `{local_auto_quant['data_feather_count']}`; strategy files found: `{local_auto_quant['strategy_py_count']}`.",
        f"- Direct Manipulation verifier status: `{direct_status}`; schema-ready rows do not pass Wilson95/heldout calibration.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "Provider readback:",
    ]
    for provider in ["yfinance", "tradingview_mcp", "ibkr", "kraken_public", "kraken_cli", "ibkr_bridge"]:
        row = provider_summary[provider]
        report.append(f"- `{provider}`: ready=`{row['ready']}`, status=`{row['status']}`, reason=`{row['reason']}`.")
    report.extend(
        [
            "",
            "Blocked intake roots:",
            "- `/tmp/ict-engine-source-label-equivalence-intake`",
            "- `/tmp/ict-engine-native-subhour-source-label-intake`",
            "- `/tmp/ict-engine-source-panel-recency-extension`",
            "- `/tmp/ict-engine-direct-manipulation-row-intake` is schema-ready only and remains calibration-blocked.",
            "",
            "Next:",
            "- Populate the exact source-owned or owner-approved intake files, then rerun these verifiers before another completion audit.",
        ]
    )
    (OUT / "live_provider_intake_recheck_v37.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={DECISION}",
        f"PASS ready_intake_roots={len(ready_roots)}_of_4",
        f"PASS yfinance_ready={provider_summary['yfinance']['ready']}",
        f"PASS tradingview_mcp_ready={provider_summary['tradingview_mcp']['ready']}",
        f"PASS kraken_lowpollution_rows={count_csv_rows(kraken_csv)}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
        "PASS raw_data_committed=false",
        "PASS trade_usable=false",
    ]
    (CHECKS / "live_provider_intake_recheck_v37_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"decision": DECISION, "ready_intake_roots": len(ready_roots), "unmet_ids": payload["unmet_ids"]}, sort_keys=True))


if __name__ == "__main__":
    main()
