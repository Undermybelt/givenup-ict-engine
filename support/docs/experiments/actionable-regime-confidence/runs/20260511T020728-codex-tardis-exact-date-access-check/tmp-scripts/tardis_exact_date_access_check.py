from __future__ import annotations

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T020728-codex-tardis-exact-date-access-check"
)
SOURCE_ALIGNMENT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T015848-codex-tardis-pump-event-alignment-audit/"
    "alignment/tardis_pump_event_alignment_audit.json"
)
OUT_DIR = RUN_ROOT / "access-check"
CHECKS_DIR = RUN_ROOT / "checks"
LOOP_ID = "20260511T020728+0800-codex-tardis-exact-date-access-check"
DATA_TYPES = ("trades", "book_snapshot_5", "incremental_book_L2")
READ_BYTES = 200


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_exact_date_candidates() -> list[dict[str, Any]]:
    alignment = json.loads(SOURCE_ALIGNMENT.read_text(encoding="utf-8"))
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in alignment.get("notable_alignment_rows", []):
        event_dt = str(row.get("event_dt", ""))
        if not event_dt:
            continue
        event_date = datetime.fromisoformat(event_dt).date()
        for pair in row.get("exact_date_available_pairs", []):
            symbol = str(pair.get("pair", "")).upper()
            key = (str(row.get("symbol", "")), event_dt, symbol)
            if not symbol or key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "pump_symbol": row.get("symbol"),
                    "event_dt": event_dt,
                    "event_date": event_date.isoformat(),
                    "tardis_symbol": symbol,
                }
            )
    return out


def build_url(data_type: str, event_date: str, symbol: str) -> str:
    year, month, day = event_date.split("-")
    # Binance spot public dataset paths accept lowercase symbols; use the same
    # casing emitted by the Tardis exchange metadata crosswalk.
    return f"https://datasets.tardis.dev/v1/binance/{data_type}/{year}/{month}/{day}/{symbol.lower()}.csv.gz"


def probe_url(url: str) -> dict[str, Any]:
    try:
        proc = subprocess.Popen(
            [
                "curl",
                "-L",
                "-sS",
                "--connect-timeout",
                "3",
                "--max-time",
                "20",
                url,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert proc.stdout is not None
        body = proc.stdout.read(READ_BYTES)
        proc.terminate()
        try:
            _, stderr = proc.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            _, stderr = proc.communicate(timeout=2)
        return_code = proc.returncode
    except Exception as exc:  # noqa: BLE001 - audit needs concrete network failure text.
        return {
            "url": url,
            "status": "network_error",
            "error": type(exc).__name__,
            "message": str(exc)[:240],
            "accessible_without_credentials": False,
        }

    text = body.decode("utf-8", errors="replace")
    lower = text.lower()
    unauthorized = "unauthorized" in lower or "authorization" in lower or "api_key" in lower
    gzip_magic = body.startswith(b"\x1f\x8b")
    return {
        "url": url,
        "status": "body_prefix_probe",
        "curl_return_code": return_code,
        "curl_stderr": stderr.decode("utf-8", errors="replace")[:240],
        "body_prefix": text[:200],
        "gzip_magic": gzip_magic,
        "unauthorized_message": unauthorized,
        "accessible_without_credentials": bool(gzip_magic),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    candidates = load_exact_date_candidates()
    tasks: list[dict[str, Any]] = []
    for item in candidates:
        for data_type in DATA_TYPES:
            tasks.append({**item, "data_type": data_type, "url": build_url(data_type, item["event_date"], item["tardis_symbol"])})
    probes: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {executor.submit(probe_url, item["url"]): item for item in tasks}
        for future in as_completed(future_map):
            item = future_map[future]
            probes.append({**item, **future.result()})
    probes.sort(key=lambda row: (row["event_date"], row["tardis_symbol"], row["data_type"]))

    accessible = [p for p in probes if p["accessible_without_credentials"]]
    unauthorized = [p for p in probes if p.get("unauthorized_message")]
    decision = {
        "board_state": "blocked",
        "active_axis": "MainRegimeV2",
        "candidate_regime": "Manipulation",
        "accepted_95": False,
        "thresholds_relaxed": False,
        "runtime_code_changed": False,
        "fresh_calibration_rerun": False,
        "trade_usable": False,
        "event_candidates": len(candidates),
        "url_probes": len(probes),
        "accessible_without_credentials": len(accessible),
        "unauthorized_or_authorization_required": len(unauthorized),
        "manipulation_input_state": (
            "credentialed_exact_date_export_required"
            if not accessible
            else "partial_exact_date_public_access_found_needs_calibration"
        ),
        "blocker": (
            "Exact-date Tardis Binance URLs for labeled pump events did not return usable gzip market data "
            "without credentials; the probes returned no usable market payload and require credentialed export before calibration."
            if not accessible
            else "Some exact-date Tardis URLs are accessible, but no chronological manipulation calibration was run yet."
        ),
        "next_action": (
            "Provide a Tardis API key or pre-export the exact-date Binance trades/L2 files for the labeled pump events, "
            "then rerun the Manipulation calibration gate; continue Bull/Bear/Sideways only with materially new signed-direction/sideways inputs."
        ),
    }
    result = {
        "schema_version": "tardis-exact-date-access-check/v1",
        "loop_id": LOOP_ID,
        "run_root": repo_rel(RUN_ROOT),
        "source_alignment": repo_rel(SOURCE_ALIGNMENT),
        "read_bytes_per_probe": READ_BYTES,
        "data_types_checked": list(DATA_TYPES),
        "candidates": candidates,
        "probes": probes,
        "decision": decision,
    }

    report_json = OUT_DIR / "tardis_exact_date_access_check.json"
    report_md = OUT_DIR / "tardis_exact_date_access_check.md"
    assertions = CHECKS_DIR / "tardis_exact_date_access_check_assertions.out"
    report_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    report_md.write_text(
        "# Tardis Exact-Date Access Check\n\n"
        f"Run id: `{LOOP_ID}`\n\n"
        "This audit probes exact-date Tardis Binance URLs for labeled pump-event candidates. "
        "It reads only small response prefixes and does not save raw market data.\n\n"
        f"- Event candidates: {len(candidates)}\n"
        f"- URL probes: {len(probes)}\n"
        f"- Accessible without credentials: {len(accessible)}\n"
        f"- Unauthorized / authorization required responses: {len(unauthorized)}\n"
        f"- Manipulation input state: `{decision['manipulation_input_state']}`\n\n"
        f"Decision: {decision['blocker']}\n\n"
        f"Next action: {decision['next_action']}\n",
        encoding="utf-8",
    )
    assertions.write_text(
        "\n".join(
            [
                f"RUN_ID {LOOP_ID}",
                f"REPORT {repo_rel(report_json)}",
                f"EVENT_CANDIDATES {len(candidates)}",
                f"URL_PROBES {len(probes)}",
                f"ACCESSIBLE_WITHOUT_CREDENTIALS {len(accessible)}",
                f"UNAUTHORIZED_OR_AUTHORIZATION_REQUIRED {len(unauthorized)}",
                f"MANIPULATION_INPUT_STATE {decision['manipulation_input_state']}",
                "ACCEPTED_95 false",
                "THRESHOLDS_RELAXED false",
                "RUNTIME_CODE_CHANGED false",
                "FRESH_CALIBRATION_RERUN false",
                "TRADE_USABLE false",
                "RAW_MARKET_DATA_SAVED false",
                "GATE blocked_exact_date_tardis_requires_credentials",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (RUN_ROOT / "README.md").write_text(
        "# Tardis Exact-Date Access Check\n\n"
        "Run-local audit for exact-date Tardis access on labeled pump-event candidates. "
        "No raw market data is retained.\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
