#!/usr/bin/env python3
"""Screen a public current-regime source route without promoting rows."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T210411+0800-codex-vantmacro-current-regime-route-screen-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
REPO = RUN_ROOT.parents[4]
OUT = RUN_ROOT / "vantmacro-current-regime-route-screen"
CHECKS = RUN_ROOT / "checks"
SCRATCH = Path("/tmp/ict-engine-vantmacro-current-regime-route-screen-v1")
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    / "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)
URL = "https://vantmacro.com/"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm_text(html: str) -> str:
    text = re.sub(r"<script\b.*?</script>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())


def download(url: str, path: Path) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ict-engine-board-a-source-route-screen/1.0"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:  # noqa: S310 - public source screen.
        body = response.read()
        path.write_bytes(body)
        return {
            "url": url,
            "status": getattr(response, "status", 200),
            "content_type": response.headers.get("content-type", ""),
            "bytes": len(body),
            "sha256": sha256_bytes(body),
            "path": str(path),
        }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    SCRATCH.mkdir(parents=True, exist_ok=True)

    board_hash_before = sha256_file(BOARD)
    html_path = SCRATCH / "vantmacro-homepage.html"
    download_meta = download(URL, html_path)
    text = norm_text(html_path.read_text(encoding="utf-8", errors="ignore"))
    lower = text.lower()
    text_checks = {
        "mentions_current_regime": "current regime" in lower,
        "mentions_dashboard": "dashboard" in lower,
        "mentions_daily_weekly": "daily" in lower and "weekly" in lower,
        "mentions_2003_2026": "2003" in lower and "2026" in lower,
        "mentions_market_regime": "market regime" in lower,
        "mentions_pro": "pro" in lower,
    }
    snippets = []
    for marker in ["Current Regime", "Data from", "Daily", "Weekly", "Dashboard", "Market Regime"]:
        idx = text.lower().find(marker.lower())
        if idx >= 0:
            snippets.append({"marker": marker, "snippet": text[max(0, idx - 140) : idx + 360]})

    verifier_proc = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE_ROOT)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        verifier_payload = json.loads(verifier_proc.stdout)
    except json.JSONDecodeError:
        verifier_payload = {"status": "unparseable", "stdout": verifier_proc.stdout}

    candidate_rows = [
        {
            "requirement": "R2/R5",
            "source_route": "VantMacro public current-regime / dashboard source route",
            "url": URL,
            "source_owner": "VantMacro",
            "observed_public_surface": "homepage/dashboard marketing surface",
            "possible_fit": "current macro/asset regime labels with daily/weekly and 2026 coverage if row export or owner approval is available",
            "rows_acquired": False,
            "intake_files_created": False,
            "accepted_rows_added": 0,
            "candidate_disposition": "route_found_rows_not_acquired",
            "blocking_reason": "public page exposes source route and coverage claims but no source-owned row export, MainRegimeV2 crosswalk, split roles, provenance hashes, or owner-approved equivalence file was acquired",
        }
    ]
    write_csv(
        OUT / "vantmacro_current_regime_route_screen_v1_candidates.csv",
        candidate_rows,
        [
            "requirement",
            "source_route",
            "url",
            "source_owner",
            "observed_public_surface",
            "possible_fit",
            "rows_acquired",
            "intake_files_created",
            "accepted_rows_added",
            "candidate_disposition",
            "blocking_reason",
        ],
    )

    decision = "vantmacro_current_regime_route_screen_v1=source_route_found_rows_not_acquired"
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": board_hash_before,
        "decision": decision,
        "source_url": URL,
        "download": download_meta,
        "text_checks": text_checks,
        "snippets": snippets[:8],
        "candidate_rows": candidate_rows,
        "source_label_equivalence_verifier": {
            "command": f"python3 {VERIFIER.relative_to(REPO)} --intake-root {INTAKE_ROOT}",
            "returncode": verifier_proc.returncode,
            "stdout": verifier_proc.stdout,
            "stderr": verifier_proc.stderr,
            "payload": verifier_payload,
        },
        "request_sent": False,
        "rows_acquired": False,
        "intake_files_created": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next": "Use this as a contact/API route only if owner-approved row export or crosswalk can be acquired; source-label equivalence intake remains blocked until exact rows and provenance exist.",
    }
    (OUT / "vantmacro_current_regime_route_screen_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# VantMacro Current Regime Route Screen v1",
        "",
        f"- Gate result: `{decision}`.",
        f"- Public URL: `{URL}`.",
        f"- HTTP status: `{download_meta['status']}`; bytes: `{download_meta['bytes']}`.",
        f"- Text checks: `{json.dumps(text_checks, sort_keys=True)}`.",
        "- Rows acquired: `false`; intake files created: `false`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Boundary",
        "",
        "This is a route screen only. The page is a plausible source-owner/contact or product route for current macro/asset regime labels, "
        "but this run did not acquire row-level labels, MainRegimeV2 crosswalks, split roles, or provenance hashes. "
        "The source-label equivalence intake verifier remains fail-closed.",
        "",
        "## Verifier Readback",
        "",
        f"- Status: `{verifier_payload.get('status')}`.",
        f"- Reason: `{verifier_payload.get('reason', '')}`.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{OUT / 'vantmacro_current_regime_route_screen_v1.json'}`",
        f"- Candidate CSV: `{OUT / 'vantmacro_current_regime_route_screen_v1_candidates.csv'}`",
        f"- Assertions: `{CHECKS / 'vantmacro_current_regime_route_screen_v1_assertions.out'}`",
    ]
    (OUT / "vantmacro_current_regime_route_screen_v1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS public_page_status={download_meta['status']}",
        f"PASS text_mentions_market_regime={str(text_checks['mentions_market_regime']).lower()}",
        f"PASS verifier_status={verifier_payload.get('status')}",
        f"PASS rows_acquired={str(False).lower()}",
        f"PASS accepted_rows_added={0}",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "vantmacro_current_regime_route_screen_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"decision": decision, "verifier_status": verifier_payload.get("status")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
