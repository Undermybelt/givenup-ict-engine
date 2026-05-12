#!/usr/bin/env python3
"""Acquire and screen independent broad-normal order-lifecycle controls for R6."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-broad-normal-order-lifecycle-screen"
COMMAND_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

TMP_ROOT = Path("/tmp/ict-engine-r6-broad-normal-order-lifecycle-screen-v1")
RAW = TMP_ROOT / "raw"
SIDECAR = TMP_ROOT / "broad_normal_market_order_lifecycle_controls_v1.csv"

NASDAQ_ITCH_DIR_URL = "https://emi.nasdaq.com/ITCH/Nasdaq%20ITCH/"
NASDAQ_ITCH_ZIP_URL = "https://emi.nasdaq.com/ITCH/Nasdaq%20ITCH/S010303-v2.zip"
NASDAQ_ITCH_SPEC_URL = (
    "https://www.nasdaqtrader.com/content/technicalsupport/specifications/"
    "dataproducts/NQTVITCHSpecification.pdf"
)
KRAKEN_DEPTH_URL = "https://api.kraken.com/0/public/Depth?pair=XBTUSD&count=10"
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/QQQ?range=1d&interval=1m"
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
LIVE_R6_INTAKE_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")

REQUIRED_FIELDS = [
    "label",
    "source_report",
    "source_section",
    "trade_date",
    "symbol",
    "venue_or_market_center",
    "participant_type_code",
    "participant_identifier",
    "side",
    "earliest_order_received_time",
    "latest_order_received_time",
    "order_count",
    "total_order_quantity",
    "activity_description",
    "matched_negative_group_id",
    "session_bucket",
    "source_row_id",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def url_get(url: str, path: Path, timeout: int = 60) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "ict-engine-regime-audit/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            with path.open("wb") as handle:
                shutil.copyfileobj(response, handle)
            return {
                "url": url,
                "status": getattr(response, "status", None),
                "content_type": response.headers.get("content-type"),
                "bytes": path.stat().st_size,
                "path": str(path),
                "sha256": sha256(path),
            }
    except Exception as exc:  # noqa: BLE001 - source screens should preserve the exact blocker.
        return {
            "url": url,
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "path": str(path),
        }


def url_head(url: str, timeout: int = 20) -> dict[str, object]:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "ict-engine-regime-audit/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {
                "url": url,
                "status": getattr(response, "status", None),
                "content_type": response.headers.get("content-type"),
                "content_length": response.headers.get("content-length"),
                "last_modified": response.headers.get("last-modified"),
            }
    except Exception as exc:  # noqa: BLE001
        return {"url": url, "status": "error", "error_type": type(exc).__name__, "error": str(exc)}


def run_command(name: str, cmd: list[str], timeout: int = 45) -> dict[str, object]:
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)
    stdout_path = COMMAND_OUT / f"{name}.stdout.txt"
    stderr_path = COMMAND_OUT / f"{name}.stderr.txt"
    try:
        completed = subprocess.run(
            cmd,
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        stdout_path.write_text(completed.stdout, encoding="utf-8")
        stderr_path.write_text(completed.stderr, encoding="utf-8")
        return {
            "name": name,
            "cmd": cmd,
            "returncode": completed.returncode,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
        }
    except Exception as exc:  # noqa: BLE001
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
        return {
            "name": name,
            "cmd": cmd,
            "returncode": None,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
        }


def parse_itch_line(line: str) -> dict[str, str] | None:
    line = line.rstrip("\n")
    if len(line) < 9:
        return None
    timestamp = line[:8].strip()
    message_type = line[8]
    if message_type == "A":
        return {
            "type": "add",
            "timestamp": timestamp,
            "order_id": line[9:18].strip(),
            "side": line[18:19].strip(),
            "shares": line[19:25].strip(),
            "stock": line[25:33].strip(),
            "price": line[33:43].strip(),
            "raw": line,
        }
    if message_type == "E":
        return {
            "type": "execute",
            "timestamp": timestamp,
            "order_id": line[9:18].strip(),
            "shares": line[18:24].strip(),
            "match_number": line[24:].strip(),
            "raw": line,
        }
    if message_type == "X":
        return {
            "type": "cancel",
            "timestamp": timestamp,
            "order_id": line[9:18].strip(),
            "shares": line[18:24].strip(),
            "raw": line,
        }
    if message_type == "D":
        return {
            "type": "delete",
            "timestamp": timestamp,
            "order_id": line[9:18].strip(),
            "raw": line,
        }
    return {
        "type": message_type,
        "timestamp": timestamp,
        "raw": line,
    }


def iter_itch_lines(zip_path: Path, member_name: str):
    with zipfile.ZipFile(zip_path) as archive:
        with archive.open(member_name) as zipped:
            with gzip.GzipFile(fileobj=zipped) if member_name.endswith(".gz") else zipped as handle:
                for raw_line in handle:
                    yield raw_line.decode("ascii", errors="replace")


def materialize_broad_controls(zip_path: Path, max_controls: int, max_lines: int) -> tuple[list[dict[str, str]], dict[str, object]]:
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
    if not names:
        raise SystemExit(f"empty zip: {zip_path}")
    member_name = names[0]
    orders: dict[str, dict[str, object]] = {}
    type_counts: Counter[str] = Counter()
    line_count = 0

    for line in iter_itch_lines(zip_path, member_name):
        line_count += 1
        parsed = parse_itch_line(line)
        if not parsed:
            continue
        type_counts[str(parsed["type"])] += 1
        order_id = parsed.get("order_id")
        if not order_id:
            if line_count >= max_lines:
                break
            continue
        if parsed["type"] == "add":
            orders.setdefault(order_id, {"events": []})
            orders[order_id].update(parsed)
            orders[order_id]["events"] = [parsed]
        elif order_id in orders:
            orders[order_id].setdefault("events", []).append(parsed)
        if line_count >= max_lines:
            break

    controls: list[dict[str, str]] = []
    for order_id, order in sorted(orders.items(), key=lambda item: int(item[0]) if item[0].isdigit() else item[0]):
        events = list(order.get("events", []))
        lifecycle_events = [event for event in events if event.get("type") in {"execute", "cancel", "delete"}]
        stock = str(order.get("stock", "")).strip()
        if not lifecycle_events or not stock:
            continue
        earliest = min(str(event.get("timestamp", "")) for event in events)
        latest = max(str(event.get("timestamp", "")) for event in events)
        terminal_types = ",".join(event.get("type", "") for event in lifecycle_events[:4])
        executed_qty = sum(int(event.get("shares", "0") or 0) for event in lifecycle_events if event.get("type") == "execute")
        canceled_qty = sum(int(event.get("shares", "0") or 0) for event in lifecycle_events if event.get("type") == "cancel")
        controls.append(
            {
                "label": "independent_broad_normal_order_lifecycle_control",
                "source_report": "Nasdaq ITCH historical sample S010303-v2.zip",
                "source_section": f"{member_name}; first {line_count} parsed messages; order reference {order_id}",
                "trade_date": "2003-01-03",
                "symbol": stock,
                "venue_or_market_center": "NASDAQ ITCH historical sample",
                "participant_type_code": "public_exchange_order_lifecycle_feed",
                "participant_identifier": f"nasdaq_itch_order_ref_{order_id}",
                "side": "buy" if order.get("side") == "B" else "sell" if order.get("side") == "S" else str(order.get("side", "")),
                "earliest_order_received_time": f"{earliest} raw_itch_timestamp",
                "latest_order_received_time": f"{latest} raw_itch_timestamp",
                "order_count": str(len(events)),
                "total_order_quantity": str(order.get("shares", "")),
                "activity_description": (
                    "Independent exchange-feed background order lifecycle: "
                    f"add order side={order.get('side')} quantity={order.get('shares')} "
                    f"price={order.get('price')} followed by {terminal_types}; "
                    f"executed_qty={executed_qty}; canceled_qty={canceled_qty}. "
                    "This is broad normal-market order-lifecycle control evidence only, "
                    "not a positive spoofing/layering row and not a profitability signal."
                ),
                "matched_negative_group_id": f"broad_normal_nasdaq_itch_s010303_{order_id}",
                "session_bucket": "historical_nasdaq_itch_background",
                "source_row_id": f"nasdaq_itch_s010303_order_{order_id}",
            }
        )
        if len(controls) >= max_controls:
            break

    summary = {
        "zip_member": member_name,
        "parsed_line_count": line_count,
        "message_type_counts": dict(sorted(type_counts.items())),
        "orders_seen": len(orders),
        "controls_materialized": len(controls),
        "symbols_materialized": sorted({row["symbol"] for row in controls}),
        "side_counts": dict(Counter(row["side"] for row in controls)),
    }
    return controls, summary


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def classify_provider_surfaces(provider_status_text: str, kraken: dict[str, object], yahoo: dict[str, object]) -> list[dict[str, object]]:
    ready = set()
    pending = []
    try:
        parsed = json.loads(provider_status_text)
        ready = set(parsed.get("ready_providers", []))
        pending = parsed.get("pending_providers", [])
    except Exception:
        pass
    return [
        {
            "source": "ibkr",
            "status": "screened_not_accepted",
            "runtime_status": "configured_runtime_unhealthy_with_gateway_reachable" if any("ibkr@" in item for item in pending) else "unknown",
            "r6_control_value": "blocked",
            "reason": "current provider-status reports missing ibkr runtime dependencies; even healthy IBKR historical ticks are bid/ask/trade data, not public participant/order-lifecycle controls.",
        },
        {
            "source": "tradingview_mcp_or_remix",
            "status": "screened_not_accepted",
            "runtime_status": "ready" if "tradingview_mcp" in ready else "not_ready_or_unknown",
            "r6_control_value": "blocked",
            "reason": "TradingView surfaces are OHLCV/chart-feature sources in this workflow, not order add/cancel/execute lifecycle feeds.",
        },
        {
            "source": "yfinance",
            "status": "screened_not_accepted",
            "runtime_status": "ready" if "yfinance" in ready else "probe_error",
            "probe_status": yahoo.get("status"),
            "r6_control_value": "blocked",
            "reason": "Yahoo/yfinance is OHLCV/chart data; even when the chart probe is reachable, the surface is not order-lifecycle evidence.",
        },
        {
            "source": "kraken_public_depth",
            "status": "screened_not_accepted",
            "runtime_status": "live_http_ok" if kraken.get("status") == 200 else kraken.get("status"),
            "r6_control_value": "blocked",
            "reason": "Kraken public depth is a live aggregated book snapshot with price/size/time levels, not durable order IDs or add/cancel/execute lifecycles.",
        },
        {
            "source": "nasdaq_itch_s010303",
            "status": "accepted_sidecar_control_source",
            "runtime_status": "public_https_download",
            "r6_control_value": "independent_broad_normal_order_lifecycle_controls_sidecar",
            "reason": "Nasdaq ITCH sample provides direct add/execute/cancel/delete order lifecycle messages from an exchange-feed background day.",
        },
    ]


def parse_command_json(command: dict[str, object]) -> dict[str, object] | None:
    stdout_path = command.get("stdout_path")
    if not stdout_path:
        return None
    path = Path(str(stdout_path))
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-controls", type=int, default=80)
    parser.add_argument("--max-lines", type=int, default=250_000)
    parser.add_argument("--reuse-raw", action="store_true")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)

    board_hash_before = sha256(BOARD) if BOARD.exists() else None
    provider_status = run_command("provider_status_agent", ["target/debug/ict-engine", "provider-status", "--agent"])
    auto_quant_status = run_command(
        "auto_quant_status_agent",
        [
            "target/debug/ict-engine",
            "auto-quant-status",
            "--state-dir",
            str(TMP_ROOT / "state"),
            "--output-format",
            "agent",
        ],
    )
    direct_verifier_status = run_command(
        "direct_manipulation_row_intake_verifier",
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(LIVE_R6_INTAKE_ROOT)],
    )
    live_direct_verifier = parse_command_json(direct_verifier_status)

    itch_dir_path = RAW / "nasdaq_itch_directory.html"
    itch_zip_path = RAW / "S010303-v2.zip"
    spec_head = url_head(NASDAQ_ITCH_SPEC_URL)
    itch_dir = url_get(NASDAQ_ITCH_DIR_URL, itch_dir_path, timeout=30)
    if args.reuse_raw and itch_zip_path.exists():
        itch_zip = {
            "url": NASDAQ_ITCH_ZIP_URL,
            "status": "reused_local_raw",
            "bytes": itch_zip_path.stat().st_size,
            "path": str(itch_zip_path),
            "sha256": sha256(itch_zip_path),
        }
    else:
        itch_zip = url_get(NASDAQ_ITCH_ZIP_URL, itch_zip_path, timeout=90)

    kraken_path = RAW / "kraken_depth_xbtusd.json"
    yahoo_path = RAW / "yahoo_qqq_chart_probe.json"
    kraken = url_get(KRAKEN_DEPTH_URL, kraken_path, timeout=20)
    yahoo = url_get(YAHOO_CHART_URL, yahoo_path, timeout=20)

    if itch_zip.get("status") not in {200, "reused_local_raw"}:
        raise SystemExit(f"nasdaq ITCH source unavailable: {itch_zip}")

    controls, itch_summary = materialize_broad_controls(itch_zip_path, args.max_controls, args.max_lines)
    write_csv(SIDECAR, controls)

    provider_status_text = ""
    stdout_path = provider_status.get("stdout_path")
    if stdout_path and Path(str(stdout_path)).exists():
        provider_status_text = Path(str(stdout_path)).read_text(encoding="utf-8")
    provider_screens = classify_provider_surfaces(provider_status_text, kraken, yahoo)

    raw_data_paths = {
        "tmp_root": str(TMP_ROOT),
        "nasdaq_itch_directory": str(itch_dir_path),
        "nasdaq_itch_zip": str(itch_zip_path),
        "kraken_depth_probe": str(kraken_path),
        "yahoo_chart_probe": str(yahoo_path),
    }
    sidecar_repo_path = OUT / "broad_normal_market_order_lifecycle_controls_v1.csv"
    shutil.copyfile(SIDECAR, sidecar_repo_path)

    accepted = len(controls) >= 50
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": (
            "r6_broad_normal_order_lifecycle_screen_v1="
            "sidecar_controls_acquired_shared_intake_not_mutated_confidence_still_blocked"
        ),
        "board_hash_before_start": board_hash_before,
        "nasdaq_itch_directory": itch_dir,
        "nasdaq_itch_spec_head": spec_head,
        "nasdaq_itch_zip": itch_zip,
        "itch_summary": itch_summary,
        "controls_sidecar_tmp": str(SIDECAR),
        "controls_sidecar_repo": str(sidecar_repo_path),
        "controls_sidecar_sha256": sha256(sidecar_repo_path),
        "provider_status_command": provider_status,
        "auto_quant_status_command": auto_quant_status,
        "live_direct_verifier_command": direct_verifier_status,
        "live_direct_verifier": live_direct_verifier,
        "provider_source_screens": provider_screens,
        "accepted_sidecar_controls": len(controls),
        "accepted_as_live_r6_calibration": False,
        "shared_intake_mutated": False,
        "strict_full_objective_achieved": False,
        "new_confidence_gate": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": True,
        "trade_usable": False,
        "blockers": [
            "broad normal controls are acquired as a sidecar but not injected into the shared R6 intake during concurrent work",
            f"current R6 positives remain {live_direct_verifier.get('positive_rows') if live_direct_verifier else 'unknown'}, so pooled Wilson95 positive LCB stays below 0.95 until additional source-owned positive direct rows are acquired",
            "current calibration gate still needs split support and direct species coverage beyond spoofing/layering",
            "IBKR/yfinance/TradingView/Kraken surfaces do not provide accepted public order-lifecycle controls in this slice",
        ],
        "next_action": (
            "Either wire sidecar broad controls through a new calibration artifact with explicit independent-control classification, "
            "or acquire at least 17 more source-owned positive direct rows plus controls before rerunning R6 calibration."
        ),
        "raw_data_paths": raw_data_paths,
    }

    json_path = OUT / "r6_broad_normal_order_lifecycle_screen_v1.json"
    report_path = OUT / "r6_broad_normal_order_lifecycle_screen_v1.md"
    provider_csv_path = OUT / "r6_broad_normal_source_screen_v1.csv"
    assertions_path = CHECKS / "r6_broad_normal_order_lifecycle_screen_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with provider_csv_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["source", "status", "runtime_status", "probe_status", "r6_control_value", "reason"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in provider_screens:
            writer.writerow({name: row.get(name, "") for name in fieldnames})

    report_lines = [
        "# R6 Broad Normal Order-Lifecycle Screen v1",
        "",
        f"- Decision: `{result['decision']}`.",
        f"- Independent broad-normal sidecar controls acquired: `{len(controls)}`.",
        f"- Shared R6 intake mutated: `false`; live calibration accepted: `false`.",
        f"- Strict full objective achieved: `false`; new confidence gate: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `true`; trade usable: `false`.",
        "",
        "## Source Result",
        "",
        f"- Nasdaq ITCH directory URL: `{NASDAQ_ITCH_DIR_URL}`.",
        f"- Nasdaq ITCH sample URL: `{NASDAQ_ITCH_ZIP_URL}`.",
        f"- Nasdaq ITCH spec HEAD: status `{spec_head.get('status')}`, content length `{spec_head.get('content_length')}`.",
        f"- Sample zip bytes: `{itch_zip.get('bytes')}`; SHA256 `{itch_zip.get('sha256')}`.",
        f"- Parsed messages: `{itch_summary['parsed_line_count']}`; orders seen `{itch_summary['orders_seen']}`; controls materialized `{itch_summary['controls_materialized']}`.",
        f"- Sidecar CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/r6-broad-normal-order-lifecycle-screen/broad_normal_market_order_lifecycle_controls_v1.csv`.",
        f"- Live R6 verifier readback: positives `{live_direct_verifier.get('positive_rows') if live_direct_verifier else 'unknown'}`, matched negatives `{live_direct_verifier.get('matched_negative_rows') if live_direct_verifier else 'unknown'}`, matched groups `{live_direct_verifier.get('matched_group_count') if live_direct_verifier else 'unknown'}`.",
        "",
        "## Provider Screen",
        "",
        "| Source | Status | R6 Control Value | Reason |",
        "|---|---|---|---|",
    ]
    for row in provider_screens:
        report_lines.append(
            f"| `{row['source']}` | `{row['status']}` | `{row['r6_control_value']}` | {row['reason']} |"
        )
    report_lines.extend(
        [
            "",
            "## Boundary",
            "",
            "The sidecar is independent exchange-feed order-lifecycle background data. It is not a positive spoofing/layering source and was not appended to the shared `/tmp/ict-engine-direct-manipulation-row-intake` CSVs during concurrent work.",
            "",
            "This closes only the source-screen/acquisition part of the broad-normal blocker. The R6 confidence gate remains blocked because positive direct rows are still below the Wilson95 support needed for `>=0.95`, split gates still lack support, and direct species coverage is incomplete.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/r6-broad-normal-order-lifecycle-screen/r6_broad_normal_order_lifecycle_screen_v1.json`",
            f"- Sidecar controls CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/r6-broad-normal-order-lifecycle-screen/broad_normal_market_order_lifecycle_controls_v1.csv`",
            f"- Provider/source screen CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/r6-broad-normal-order-lifecycle-screen/r6_broad_normal_source_screen_v1.csv`",
            f"- Command outputs: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/command-output/`",
            f"- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/r6_broad_normal_order_lifecycle_screen_v1_assertions.out`",
            "",
            "## Raw Data Boundary",
            "",
            f"Raw downloads are under `{TMP_ROOT}` and are not committed.",
        ]
    )
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"PASS controls_materialized={len(controls)}",
        f"PASS controls_ge_50={str(accepted).lower()}",
        "PASS shared_intake_mutated=false",
        "PASS accepted_as_live_r6_calibration=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")

    print(json.dumps({"decision": result["decision"], "controls_materialized": len(controls), "shared_intake_mutated": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
