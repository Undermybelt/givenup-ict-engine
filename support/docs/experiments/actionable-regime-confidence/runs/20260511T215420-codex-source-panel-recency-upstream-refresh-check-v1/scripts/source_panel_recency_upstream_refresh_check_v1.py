#!/usr/bin/env python3
"""Check whether the source-panel dataset has owner-updated recency rows."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T215420+0800-codex-source-panel-recency-upstream-refresh-check-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T215420-codex-source-panel-recency-upstream-refresh-check-v1"
OUT_DIR = RUN_ROOT / "source-panel-recency-refresh"
CHECK_DIR = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
SOURCE_PANEL = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
INTAKE_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)

DATASET_REF = "mafaqbhatti/stock-market-regimes-20002026"
SEARCH_TERM = "Stock Market Regimes 2000 2026"
LAST_REQUIRED_SOURCE_DATE = date(2026, 1, 30)
AUDIT_DATE = date(2026, 5, 11)


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_command(name: str, args: list[str], cwd: Path | None = None) -> dict[str, Any]:
    result = subprocess.run(args, cwd=str(cwd or RUN_ROOT), text=True, capture_output=True, check=False)
    (CMD_DIR / f"{name}.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (CMD_DIR / f"{name}.stderr.txt").write_text(result.stderr, encoding="utf-8")
    return {
        "name": name,
        "args": args,
        "returncode": result.returncode,
        "stdout_path": repo_rel(CMD_DIR / f"{name}.stdout.txt"),
        "stderr_path": repo_rel(CMD_DIR / f"{name}.stderr.txt"),
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def source_panel_summary() -> dict[str, Any]:
    min_date: date | None = None
    max_date: date | None = None
    tickers: set[str] = set()
    row_count = 0
    columns: list[str] = []
    with SOURCE_PANEL.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        for row in reader:
            row_count += 1
            tickers.add(row["ticker"])
            day = datetime.strptime(row["date"], "%Y-%m-%d").date()
            min_date = day if min_date is None else min(min_date, day)
            max_date = day if max_date is None else max(max_date, day)
    return {
        "path": str(SOURCE_PANEL),
        "sha256": sha256(SOURCE_PANEL),
        "row_count": row_count,
        "ticker_count": len(tickers),
        "date_min": str(min_date),
        "date_max": str(max_date),
        "columns": columns,
    }


def parse_kaggle_list(stdout: str) -> dict[str, str]:
    line = next((ln for ln in stdout.splitlines() if ln.startswith(DATASET_REF)), "")
    match = re.search(r"(20\d{2}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)", line)
    return {
        "dataset_ref_line": line,
        "last_updated": match.group(1) if match else "",
    }


def parse_kaggle_files(stdout: str) -> dict[str, Any]:
    creation_dates = re.findall(r"(20\d{2}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)", stdout)
    return {
        "creation_dates": creation_dates,
        "max_creation_date": max(creation_dates) if creation_dates else "",
        "file_count": len([ln for ln in stdout.splitlines() if ln.strip() and not ln.startswith("-") and not ln.startswith("name")]),
    }


def load_metadata(metadata_dir: Path) -> dict[str, Any]:
    path = metadata_dir / "dataset-metadata.json"
    if not path.exists():
        return {"path": str(path), "loaded": False}
    raw = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(json.loads(raw))
    except json.JSONDecodeError:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw_parse_failed": True, "raw_sample": raw[:1000]}
    return {"path": str(path), "loaded": True, "payload": payload}


def parse_verifier(stdout: str, returncode: int) -> dict[str, Any]:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        payload = {"parse_failed": True, "stdout_sample": stdout[:1000]}
    return {"returncode": returncode, "payload": payload}


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)

    metadata_dir = Path("/tmp/ict-engine-source-panel-recency-upstream-refresh-check-v1-metadata")
    metadata_dir.mkdir(parents=True, exist_ok=True)

    commands = [
        run_command("kaggle_datasets_list", ["kaggle", "datasets", "list", "-s", SEARCH_TERM], Path("/tmp")),
        run_command("kaggle_datasets_files", ["kaggle", "datasets", "files", DATASET_REF], Path("/tmp")),
        run_command("kaggle_datasets_metadata", ["kaggle", "datasets", "metadata", DATASET_REF, "-p", str(metadata_dir)], Path("/tmp")),
        run_command("source_panel_recency_verifier", ["python3", str(VERIFIER), "--intake-root", str(INTAKE_ROOT)], REPO),
    ]
    local_panel = source_panel_summary()
    list_info = parse_kaggle_list(commands[0]["stdout"])
    files_info = parse_kaggle_files(commands[1]["stdout"])
    metadata = load_metadata(metadata_dir)
    verifier = parse_verifier(commands[3]["stdout"], commands[3]["returncode"])

    source_date_max = datetime.strptime(local_panel["date_max"], "%Y-%m-%d").date()
    upstream_last_updated = list_info["last_updated"]
    upstream_packaged_after_source_max = False
    upstream_updated_on_or_after_audit_date = False
    if upstream_last_updated:
        upstream_last_updated_date = datetime.strptime(upstream_last_updated[:10], "%Y-%m-%d").date()
        upstream_packaged_after_source_max = upstream_last_updated_date > source_date_max
        upstream_updated_on_or_after_audit_date = upstream_last_updated_date >= AUDIT_DATE
    source_has_required_recency = source_date_max > LAST_REQUIRED_SOURCE_DATE

    gate_rows = [
        {
            "gate": "local_source_panel_recency",
            "status": "fail",
            "evidence": f"date_max={local_panel['date_max']}; required_after={LAST_REQUIRED_SOURCE_DATE}",
        },
        {
            "gate": "kaggle_dataset_reachable",
            "status": "pass" if commands[0]["returncode"] == 0 and commands[1]["returncode"] == 0 else "fail",
            "evidence": f"list_rc={commands[0]['returncode']}; files_rc={commands[1]['returncode']}",
        },
        {
            "gate": "kaggle_owner_refresh_on_or_after_audit_date",
            "status": "pass" if upstream_updated_on_or_after_audit_date else "fail",
            "evidence": f"last_updated={upstream_last_updated}; max_file_creation={files_info['max_creation_date']}",
        },
        {
            "gate": "r5_intake_verifier",
            "status": "fail" if commands[3]["returncode"] != 0 else "pass",
            "evidence": json.dumps(verifier["payload"], sort_keys=True),
        },
    ]
    write_csv(
        OUT_DIR / "source_panel_recency_upstream_refresh_check_gates_v1.csv",
        gate_rows,
        ["gate", "status", "evidence"],
    )

    manifest = {
        "run_id": RUN_ID,
        "artifact_type": "source_panel_recency_upstream_refresh_check_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": repo_rel(BOARD),
        "board_sha256_at_run": sha256(BOARD),
        "purpose": "Check whether the owner source-panel dataset can fill the R5 post-2026-01-30 recency intake without proxy label generation.",
        "dataset_ref": DATASET_REF,
        "source_panel_local": local_panel,
        "kaggle": {
            "search_term": SEARCH_TERM,
            "list": list_info,
            "files": files_info,
            "metadata": metadata,
        },
        "verifier": verifier,
        "commands": [
            {k: v for k, v in command.items() if k not in {"stdout", "stderr"}}
            for command in commands
        ],
        "decision": {
            "gate_result": "source_panel_recency_upstream_refresh_check_v1=upstream_not_refreshed_r5_still_missing_required_files",
            "source_has_required_recency": source_has_required_recency,
            "upstream_packaged_after_source_max": upstream_packaged_after_source_max,
            "upstream_updated_on_or_after_audit_date": upstream_updated_on_or_after_audit_date,
            "extension_rows_added": 0,
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "external_requests_sent": True,
            "trade_usable": False,
        },
        "next_action": "Acquire owner-updated source-panel rows after 2026-01-30 or switch to native sub-hour/R6 direct expansion; do not synthesize source labels from OHLCV.",
    }
    (OUT_DIR / "source_panel_recency_upstream_refresh_check_v1.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Source Panel Recency Upstream Refresh Check v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This checks the original Kaggle source-panel owner path for a post-`2026-01-30` refresh. It does not generate or infer source labels.",
        "",
        "## Result",
        "",
        f"- Local source panel max date: `{local_panel['date_max']}`.",
        f"- Kaggle dataset ref checked: `{DATASET_REF}`.",
        f"- Kaggle lastUpdated from search: `{upstream_last_updated or 'unavailable'}`.",
        f"- Latest file creation date from `datasets files`: `{files_info['max_creation_date'] or 'unavailable'}`.",
        f"- R5 verifier status: `{verifier['payload'].get('status', 'unknown')}` / `{verifier['payload'].get('reason', 'n/a')}`.",
        "- Extension rows added: `0`.",
        "- Gate result: `source_panel_recency_upstream_refresh_check_v1=upstream_not_refreshed_r5_still_missing_required_files`.",
        "- Full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Guardrail",
        "",
        "R5 remains blocked because source-owned rows after `2026-01-30` were not available from the checked owner source. Fresh OHLCV-derived labels are still rejected for this source-panel recency lane.",
    ]
    (OUT_DIR / "source_panel_recency_upstream_refresh_check_v1.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    failures = []
    if source_has_required_recency:
        failures.append("unexpected_local_source_panel_recency_present")
    if upstream_updated_on_or_after_audit_date:
        failures.append("unexpected_upstream_audit_date_refresh_present")
    if verifier["payload"].get("status") != "blocked":
        failures.append("r5_verifier_not_blocked")
    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={manifest['board_sha256_at_run']}",
        f"local_source_panel_date_max={local_panel['date_max']}",
        f"kaggle_last_updated={upstream_last_updated}",
        f"kaggle_max_file_creation={files_info['max_creation_date']}",
        f"r5_verifier_status={verifier['payload'].get('status')}",
        f"r5_verifier_reason={verifier['payload'].get('reason')}",
        "extension_rows_added=0",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "external_requests_sent=true",
        "full_objective_achieved=false",
        "update_goal=false",
        f"assertion_status={'FAIL' if failures else 'PASS'}",
    ]
    if failures:
        assertions.append("failures=" + ",".join(failures))
    (CHECK_DIR / "source_panel_recency_upstream_refresh_check_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
