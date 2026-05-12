#!/usr/bin/env python3
"""Screen official CFTC Optiver marking-close facts for R6 candidate rows.

This run is deliberately proposal-only. It fetches official CFTC source
documents into /tmp, records compact row/provenance artifacts, and does not
mutate the shared direct Manipulation intake because matched normal controls
are not present in the public source package.
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T001100-codex-r6-optiver-marking-close-positive-row-candidate-screen-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-optiver-marking-close-positive-row-candidate-screen"
CMD_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RAW_ROOT = Path("/tmp/ict-engine-r6-optiver-marking-close-positive-row-candidate-screen-v1")

LIVE_INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
CHAIN_STATE = Path("/tmp/ict-engine-r6-optiver-marking-close-chain-state-001100")
ICT_ENGINE = REPO / "target/debug/ict-engine"
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

SOURCES = [
    {
        "id": "cftc_press_5521_08",
        "url": "https://www.cftc.gov/PressRoom/PressReleases/5521-08",
        "filename": "press_5521_08.html",
        "purpose": "CFTC press release describing the Optiver NYMEX energy futures manipulation complaint.",
    },
    {
        "id": "cftc_optiver_complaint_pdf",
        "url": "https://www.cftc.gov/sites/default/files/idc/groups/public/%40lrenforcementactions/documents/legalpleading/enfoptiveruscomplaint072408.pdf",
        "filename": "enfoptiveruscomplaint072408.pdf",
        "purpose": "Official CFTC complaint; paragraph 256 lists the March 2007 futures-contract instances.",
    },
    {
        "id": "cftc_optiver_chart_pdf",
        "url": "https://www.cftc.gov/sites/default/files/idc/groups/public/%40newsroom/documents/file/enfoptiverchart.pdf",
        "filename": "enfoptiverchart.pdf",
        "purpose": "Official CFTC chart link from the press packet; retained as source provenance only.",
    },
]

ROWS = [
    ("2007-03-02", "New York Harbor Gasoline futures", 1),
    ("2007-03-02", "New York Harbor Gasoline futures", 2),
    ("2007-03-06", "Light Sweet Crude Oil futures", 1),
    ("2007-03-08", "New York Harbor Gasoline futures", 1),
    ("2007-03-08", "New York Harbor Gasoline futures", 2),
    ("2007-03-09", "Heating Oil futures", 1),
    ("2007-03-09", "Heating Oil futures", 2),
    ("2007-03-13", "New York Harbor Gasoline futures", 1),
    ("2007-03-13", "Light Sweet Crude Oil futures", 2),
    ("2007-03-14", "New York Harbor Gasoline futures", 1),
    ("2007-03-14", "New York Harbor Gasoline futures", 2),
    ("2007-03-15", "Light Sweet Crude Oil futures", 1),
    ("2007-03-15", "New York Harbor Gasoline futures", 2),
    ("2007-03-16", "Light Sweet Crude Oil futures", 1),
    ("2007-03-16", "New York Harbor Gasoline futures", 2),
    ("2007-03-19", "Light Sweet Crude Oil futures", 1),
    ("2007-03-19", "Heating Oil futures", 2),
    ("2007-03-20", "Heating Oil futures", 1),
    ("2007-03-21", "New York Harbor Gasoline futures", 1),
]

FIELDS = [
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


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def fetch_sources() -> list[dict[str, Any]]:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    fetched = []
    for source in SOURCES:
        dest = RAW_ROOT / source["filename"]
        request = urllib.request.Request(source["url"], headers={"User-Agent": "ict-engine-board-a-source-screen/1.0"})
        status = "blocked"
        error = ""
        try:
            with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
                body = response.read()
                status = f"http_{getattr(response, 'status', 200)}"
            dest.write_bytes(body)
        except Exception as exc:  # noqa: BLE001
            body = b""
            error = f"{type(exc).__name__}: {exc}"
        fetched.append(
            {
                **source,
                "raw_path": str(dest),
                "status": status,
                "bytes": len(body) if body else (dest.stat().st_size if dest.exists() else 0),
                "sha256": sha256(dest) if dest.exists() else "",
                "error": error,
            }
        )
    return fetched


def strings_text(path: Path) -> str:
    proc = subprocess.run(["strings", str(path)], text=True, capture_output=True, check=False, timeout=30)
    return proc.stdout


def html_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    return html.unescape(re.sub(r"<[^>]+>", " ", raw))


def build_rows(complaint_text: str) -> list[dict[str, str]]:
    source_report = "CFTC Complaint: CFTC v. Optiver US LLC et al., filed July 24 2008"
    rows = []
    for index, (date, symbol, ordinal) in enumerate(ROWS, start=1):
        product_key = symbol.replace(" futures", "")
        date_key = f"March {int(date[-2:])}"
        source_seen = date_key in complaint_text and product_key in complaint_text
        row_id = f"cftc_optiver_{date.replace('-', '')}_{re.sub(r'[^a-z0-9]+', '_', symbol.lower()).strip('_')}_{ordinal}"
        rows.append(
            {
                "label": "positive_marking_close_candidate",
                "source_report": source_report,
                "source_section": "Complaint paragraph 256 table; paragraphs 99-126 describe TAS/futures marking-close scheme",
                "trade_date": date,
                "symbol": symbol,
                "venue_or_market_center": "NYMEX",
                "participant_type_code": "CFTC respondent proprietary trading firm and supervised traders",
                "participant_identifier": "Optiver US LLC / Optiver Holding BV / Optiver VOF / Dowson / Meijer",
                "side": "large futures trading opposite accumulated TAS position during pre-close and close",
                "earliest_order_received_time": "14:25:00 America/Chicago",
                "latest_order_received_time": "14:30:00 America/Chicago",
                "order_count": "public complaint states large number/significant volume; instance-level order count not exported",
                "total_order_quantity": "public complaint table lists contract/date only; quantities require non-public exhibits",
                "activity_description": (
                    "Official CFTC complaint alleges a March 2007 NYMEX energy-futures marking/banging-the-close "
                    "scheme and lists this date/product as an instance with intent to affect prices. "
                    f"source_seen_in_pdf_strings={source_seen}"
                ),
                "matched_negative_group_id": f"candidate_only_no_public_matched_control_{row_id}",
                "session_bucket": "nymex_preclose_close",
                "source_row_id": row_id,
            }
        )
    return rows


def run_live_verifier() -> dict[str, Any]:
    CMD_OUT.mkdir(parents=True, exist_ok=True)
    if not DIRECT_VERIFIER.exists():
        return {"returncode": None, "status": "missing_direct_verifier", "path": rel(DIRECT_VERIFIER)}
    proc = subprocess.run(
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(LIVE_INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    stdout_path = CMD_OUT / "live_direct_verifier.stdout.txt"
    stderr_path = CMD_OUT / "live_direct_verifier.stderr.txt"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {"status": "parse_failed", "stdout_sample": proc.stdout[:500]}
    return {
        "returncode": proc.returncode,
        "payload": payload,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
    }


def run_chain_commands() -> list[dict[str, Any]]:
    CMD_OUT.mkdir(parents=True, exist_ok=True)
    commands = [
        ("provider_status", [str(ICT_ENGINE), "provider-status", "--agent"]),
        (
            "auto_quant_status",
            [str(ICT_ENGINE), "auto-quant-status", "--state-dir", str(CHAIN_STATE), "--output-format", "json"],
        ),
        ("analyze_demo", [str(ICT_ENGINE), "analyze", "--symbol", "DEMO", "--demo", "--human", "--state-dir", str(CHAIN_STATE)]),
        (
            "pre_bayes_status",
            [
                str(ICT_ENGINE),
                "pre-bayes-status",
                "--symbol",
                "DEMO",
                "--state-dir",
                str(CHAIN_STATE),
                "--refresh",
                "--output-format",
                "json",
            ],
        ),
        (
            "policy_training_status",
            [str(ICT_ENGINE), "policy-training-status", "--symbol", "DEMO", "--state-dir", str(CHAIN_STATE), "--output-format", "json"],
        ),
        (
            "workflow_status_execution_candidate",
            [
                str(ICT_ENGINE),
                "workflow-status",
                "--symbol",
                "DEMO",
                "--state-dir",
                str(CHAIN_STATE),
                "--refresh",
                "--phase",
                "execution-candidate",
                "--output-format",
                "json",
            ],
        ),
        (
            "structural_path_ranking_target",
            [str(ICT_ENGINE), "export-structural-path-ranking-target", "--symbol", "DEMO", "--state-dir", str(CHAIN_STATE)],
        ),
    ]
    results = []
    for name, cmd in commands:
        stdout_path = CMD_OUT / f"{name}.stdout.txt"
        stderr_path = CMD_OUT / f"{name}.stderr.txt"
        if not ICT_ENGINE.exists():
            result = {
                "name": name,
                "returncode": None,
                "status": "missing_ict_engine_binary",
                "command": cmd,
                "stdout_path": rel(stdout_path),
                "stderr_path": rel(stderr_path),
            }
            stdout_path.write_text("", encoding="utf-8")
            stderr_path.write_text("missing target/debug/ict-engine\n", encoding="utf-8")
            results.append(result)
            continue
        proc = subprocess.run(cmd, cwd=REPO, text=True, capture_output=True, check=False, timeout=120)
        stdout_path.write_text(proc.stdout, encoding="utf-8")
        stderr_path.write_text(proc.stderr, encoding="utf-8")
        stdout = proc.stdout.strip()
        parsed: Any = None
        if stdout.startswith("{") or stdout.startswith("["):
            try:
                parsed = json.loads(stdout)
            except json.JSONDecodeError:
                parsed = None
        result = {
            "name": name,
            "returncode": proc.returncode,
            "command": cmd,
            "stdout_path": rel(stdout_path),
            "stderr_path": rel(stderr_path),
            "stdout_sample": stdout[:500],
        }
        if parsed is not None:
            result["parsed_summary"] = summarize_chain_payload(name, parsed)
        results.append(result)
    return results


def summarize_chain_payload(name: str, payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"shape": type(payload).__name__}
    if name == "provider_status":
        return {
            "entry_model_ready": payload.get("entry_model", {}).get("ready_count"),
            "entry_model_total": payload.get("entry_model", {}).get("total_count"),
            "live_runtime_ready": payload.get("live_runtime", {}).get("ready_count"),
            "live_runtime_total": payload.get("live_runtime", {}).get("total_count"),
            "market_data_ready": payload.get("market_data", {}).get("ready_count"),
            "market_data_total": payload.get("market_data", {}).get("total_count"),
        }
    if name == "auto_quant_status":
        return {
            "status": payload.get("status"),
            "reason": payload.get("reason"),
            "strategies_found": payload.get("strategies_found"),
        }
    if name == "pre_bayes_status":
        return {
            "status": payload.get("status"),
            "latest_policy": payload.get("latest_policy"),
            "decision": payload.get("decision") or payload.get("gate_decision"),
        }
    if name == "policy_training_status":
        return {
            "status": payload.get("status"),
            "matched_rows": payload.get("matched_rows"),
            "model_ready": payload.get("model_ready"),
        }
    if name == "workflow_status_execution_candidate":
        return {
            "symbol": payload.get("symbol"),
            "action": payload.get("action") or payload.get("recommended_action"),
            "phase": payload.get("phase"),
        }
    return {"keys": sorted(payload.keys())[:20]}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    board_hash = sha256(BOARD)
    fetched = fetch_sources()
    fetch_by_id = {item["id"]: item for item in fetched}
    complaint_path = RAW_ROOT / "enfoptiveruscomplaint072408.pdf"
    press_path = RAW_ROOT / "press_5521_08.html"
    complaint_text = strings_text(complaint_path) if complaint_path.exists() else ""
    press_text = html_text(press_path) if press_path.exists() else ""
    proposed_rows = build_rows(complaint_text)
    source_screen_rows = [
        {
            "source_id": item["id"],
            "url": item["url"],
            "status": item["status"],
            "bytes": item["bytes"],
            "sha256": item["sha256"],
            "purpose": item["purpose"],
            "error": item["error"],
        }
        for item in fetched
    ]
    candidate_csv = OUT / "r6_optiver_marking_close_positive_row_candidates_v1.csv"
    source_csv = OUT / "r6_optiver_marking_close_source_screen_v1_sources.csv"
    write_csv(candidate_csv, proposed_rows, FIELDS)
    write_csv(source_csv, source_screen_rows, ["source_id", "url", "status", "bytes", "sha256", "purpose", "error"])
    live_verifier = run_live_verifier()
    chain_readback = run_chain_commands()

    complaint_table_terms = ["March 2", "March 6", "March 8", "March 9", "March 13", "March 14", "March 15", "March 16", "March 19", "March 20", "March 21"]
    source_checks = {
        "press_mentions_optiver": "Optiver" in press_text,
        "press_mentions_marking_close": "marking" in press_text.lower() and "close" in press_text.lower(),
        "complaint_mentions_paragraph_256": "256. During March 2007" in complaint_text,
        "complaint_has_all_table_dates": all(term in complaint_text for term in complaint_table_terms),
        "complaint_has_all_products": all(term in complaint_text for term in ["Light Sweet Crude Oil", "Heating Oil", "New York Harbor Gasoline"]),
    }
    result = {
        "accepted_rows_added": 0,
        "board_sha256_at_start": board_hash,
        "candidate_count": len(proposed_rows),
        "candidate_rows_csv": rel(candidate_csv),
        "decision": "r6_optiver_marking_close_positive_row_candidate_screen_v1=official_cftc_positive_rows_found_controls_missing",
        "direct_species": "painting_tape_marking_close",
        "external_requests_sent": True,
        "fetched_sources": fetched,
        "gate_result": "r6_optiver_marking_close_positive_row_candidate_screen_v1=proposed_rows_only_missing_matched_controls_split_species_still_blocked",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "ict_engine_chain_readback": chain_readback,
        "live_direct_verifier": live_verifier,
        "matched_controls_acquired": False,
        "new_confidence_gate": False,
        "next_action": "Find or owner-acquire same-schema normal controls for the Optiver marking-close rows before any intake mutation; otherwise continue R6 split-balanced direct species acquisition.",
        "positive_rows_acquired": True,
        "raw_data_committed": False,
        "raw_data_root": str(RAW_ROOT),
        "run_id": RUN_ID,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "source_checks": source_checks,
        "source_screen_csv": rel(source_csv),
        "strict_full_objective_achieved": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    json_path = OUT / "r6_optiver_marking_close_positive_row_candidate_screen_v1.json"
    report_path = OUT / "r6_optiver_marking_close_positive_row_candidate_screen_v1.md"
    write_json(json_path, result)
    report_path.write_text(
        "\n".join(
            [
                "# R6 Optiver Marking-Close Positive Row Candidate Screen v1",
                "",
                f"- Run id: `{RUN_ID}`",
                "- Source owner: CFTC public press release and complaint packet.",
                f"- Candidate direct species: `{result['direct_species']}`.",
                f"- Proposed positive rows: `{len(proposed_rows)}`.",
                "- Matched normal controls acquired: `false`.",
                "- Shared intake mutated: `false`.",
                f"- Gate result: `{result['gate_result']}`.",
                "- Strict full objective achieved: `false`; `update_goal=false`.",
                "",
                "## Sources",
                *[
                    f"- `{item['id']}`: {item['url']} status `{item['status']}`, sha256 `{item['sha256']}`"
                    for item in fetched
                ],
                "",
                "## Artifacts",
                f"- JSON: `{rel(json_path)}`",
                f"- Proposed rows CSV: `{rel(candidate_csv)}`",
                f"- Source screen CSV: `{rel(source_csv)}`",
                f"- Live direct verifier stdout/stderr: `{rel(CMD_OUT)}`",
                f"- Assertions: `{rel(CHECKS / 'r6_optiver_marking_close_positive_row_candidate_screen_v1_assertions.out')}`",
                "",
                "## Runtime Chain Readback",
                *[
                    f"- `{item['name']}` returned `{item['returncode']}`; stdout `{item['stdout_path']}`"
                    for item in chain_readback
                ],
                "",
                "## Decision",
                "The official CFTC complaint exposes a concrete 19-instance date/product table for a non-spoofing marking-close species. It still cannot be accepted into the canonical direct intake because the public packet does not expose same-schema matched normal controls, instance-level quantities, or a control provenance manifest.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    assertions = [
        ("sources_fetched", all(item["status"].startswith("http_") and item["bytes"] > 0 for item in fetched)),
        ("candidate_rows_19", len(proposed_rows) == 19),
        ("source_dates_present", source_checks["complaint_has_all_table_dates"]),
        ("products_present", source_checks["complaint_has_all_products"]),
        ("controls_missing_fail_closed", result["matched_controls_acquired"] is False),
        ("chain_commands_attempted", len(chain_readback) == 7),
        ("no_shared_intake_mutation", result["shared_intake_mutated"] is False),
        ("strict_full_objective_not_complete", result["strict_full_objective_achieved"] is False),
    ]
    assertion_text = "\n".join(f"{name}={'ok' if ok else 'FAIL'}" for name, ok in assertions) + "\n"
    (CHECKS / "r6_optiver_marking_close_positive_row_candidate_screen_v1_assertions.out").write_text(assertion_text, encoding="utf-8")
    return 0 if all(ok for _, ok in assertions) else 2


if __name__ == "__main__":
    raise SystemExit(main())
