#!/usr/bin/env python3
"""Board A R2/R3/R5 intake-root and local source-label gap readback."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T211112-codex-r2-r3-r5-source-intake-gap-readback-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r2-r3-r5-source-intake-gap-readback"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
SOURCE_LABEL_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T182922-codex-source-label-equivalence-intake-verifier-v1/equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)
RECENCY_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T165405-codex-source-panel-recency-extension-manifest-v1/source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

INTAKE_ROOTS = {
    "source_label_equivalence": {
        "requirements": ["R2", "R4"],
        "root": Path("/tmp/ict-engine-source-label-equivalence-intake"),
        "required_files": [
            "source_label_equivalence_rows.csv",
            "source_label_equivalence_provenance.json",
        ],
    },
    "native_subhour_source_label": {
        "requirements": ["R3"],
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required_files": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
    },
    "source_panel_recency_extension": {
        "requirements": ["R5"],
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required_files": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
    },
    "direct_manipulation_row_intake": {
        "requirements": ["R6"],
        "root": Path("/tmp/ict-engine-direct-manipulation-row-intake"),
        "required_files": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
    },
}

EXACT_REQUIRED_FILENAMES = sorted(
    {
        name
        for spec in INTAKE_ROOTS.values()
        if spec["requirements"] != ["R6"]
        for name in spec["required_files"]
    }
)

SEARCH_ROOTS = [Path("/tmp"), Path("/Users/thrill3r/Downloads")]
MAX_DEPTH = 5


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def json_loads_or_none(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return None


def bounded_walk(root: Path, max_depth: int):
    if not root.exists():
        return
    root_parts = len(root.parts)
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        depth = len(current_path.parts) - root_parts
        if depth >= max_depth:
            dirs[:] = []
        yield current_path, files


def exact_required_file_search() -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    wanted = set(EXACT_REQUIRED_FILENAMES)
    for root in SEARCH_ROOTS:
        for current, files in bounded_walk(root, MAX_DEPTH):
            for filename in files:
                if filename in wanted:
                    path = current / filename
                    hits.append(
                        {
                            "filename": filename,
                            "path": str(path),
                            "size_bytes": path.stat().st_size,
                            "sha256": sha256(path),
                        }
                    )
    return sorted(hits, key=lambda row: (row["filename"], row["path"]))


def source_candidate_inventory() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    known_paths = [
        Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv"),
        Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.parquet"),
        Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/regime_analysis_by_ticker.csv"),
        Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/regime_by_year.csv"),
        Path("/Users/thrill3r/Downloads/ictscripts/ICT Market Regime Detector"),
    ]
    for path in known_paths:
        if not path.exists():
            continue
        row: dict[str, Any] = {
            "path": str(path),
            "kind": "dir" if path.is_dir() else "file",
            "size_bytes": path.stat().st_size if path.is_file() else None,
            "sha256": sha256(path) if path.is_file() else None,
            "closes_required_intake": False,
            "reason": "not an exact required R2/R3/R5 intake file",
        }
        if path.name == "stock_market_regimes_2000_2026.csv":
            row.update(stock_regime_csv_summary(path))
            row["reason"] = (
                "source panel exists locally but max source date is not a post-2026-01-30 "
                "recency extension and it is not copied into the R5 intake root with provenance"
            )
        candidates.append(row)
    return candidates


def stock_regime_csv_summary(path: Path) -> dict[str, Any]:
    rows = 0
    date_min: str | None = None
    date_max: str | None = None
    tickers: set[str] = set()
    regimes: set[str] = set()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows += 1
            day = row.get("date") or row.get("Date")
            ticker = row.get("ticker") or row.get("symbol") or row.get("Ticker")
            regime = row.get("regime_label") or row.get("regime") or row.get("Market_Regime")
            if day:
                date_min = day if date_min is None or day < date_min else date_min
                date_max = day if date_max is None or day > date_max else date_max
            if ticker:
                tickers.add(ticker)
            if regime:
                regimes.add(regime)
    return {
        "rows": rows,
        "date_min": date_min,
        "date_max": date_max,
        "ticker_count": len(tickers),
        "regime_count": len(regimes),
        "post_2026_01_30_rows_available": bool(date_max and date_max > "2026-01-30"),
    }


def intake_root_status() -> list[dict[str, Any]]:
    rows = []
    for intake_id, spec in INTAKE_ROOTS.items():
        root = spec["root"]
        present = []
        missing = []
        row_counts = {}
        for filename in spec["required_files"]:
            path = root / filename
            if path.exists():
                present.append(filename)
                if path.suffix == ".csv":
                    with path.open(newline="", encoding="utf-8") as handle:
                        row_counts[filename] = max(sum(1 for _ in handle) - 1, 0)
            else:
                missing.append(filename)
        rows.append(
            {
                "id": intake_id,
                "requirements": ";".join(spec["requirements"]),
                "root": str(root),
                "exists": root.exists(),
                "required_files": ";".join(spec["required_files"]),
                "present_files": ";".join(present),
                "missing_files": ";".join(missing),
                "csv_row_counts": json.dumps(row_counts, sort_keys=True),
                "ready": root.exists() and not missing,
            }
        )
    return rows


def run_command(name: str, args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=REPO, text=True, capture_output=True, check=False)
    (CMD_OUT / f"{name}.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (CMD_OUT / f"{name}.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    return {
        "name": name,
        "command": " ".join(args),
        "returncode": proc.returncode,
        "stdout_path": rel(CMD_OUT / f"{name}.stdout.txt"),
        "stderr_path": rel(CMD_OUT / f"{name}.stderr.txt"),
        "payload": json_loads_or_none(proc.stdout),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def current_cursor_summary() -> dict[str, str]:
    lines = BOARD.read_text(encoding="utf-8").splitlines()
    in_cursor = False
    cursor: dict[str, str] = {}
    for line in lines:
        if line.strip() == "## Current Cursor":
            in_cursor = True
            continue
        if in_cursor and line.startswith("## "):
            break
        if in_cursor and line.startswith("|") and not line.startswith("|---"):
            parts = [part.strip() for part in line.strip("|").split("|")]
            if len(parts) >= 2 and parts[0] != "Field":
                cursor[parts[0]] = parts[1]
    return cursor


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)

    board_hash_before = sha256(BOARD)
    exact_hits = exact_required_file_search()
    candidates = source_candidate_inventory()
    roots = intake_root_status()

    verifier_results = [
        run_command(
            "source_label_equivalence_verifier",
            [
                "python3",
                str(SOURCE_LABEL_VERIFIER),
                "--intake-root",
                "/tmp/ict-engine-source-label-equivalence-intake",
            ],
        ),
        run_command(
            "source_panel_recency_verifier",
            [
                "python3",
                str(RECENCY_VERIFIER),
                "--intake-root",
                "/tmp/ict-engine-source-panel-recency-extension",
            ],
        ),
        run_command(
            "direct_manipulation_verifier",
            [
                "python3",
                str(DIRECT_VERIFIER),
                "--intake-root",
                "/tmp/ict-engine-direct-manipulation-row-intake",
            ],
        ),
    ]

    source_label_blocked = verifier_results[0]["returncode"] == 2
    recency_blocked = verifier_results[1]["returncode"] == 2
    direct_payload = verifier_results[2]["payload"] or {}
    direct_schema_ready = direct_payload.get("status") == "schema_ready_unscored"
    native_root = next(row for row in roots if row["id"] == "native_subhour_source_label")
    source_root = next(row for row in roots if row["id"] == "source_label_equivalence")
    recency_root = next(row for row in roots if row["id"] == "source_panel_recency_extension")
    direct_root = next(row for row in roots if row["id"] == "direct_manipulation_row_intake")

    result = {
        "run_id": "20260511T211112+0800-codex-r2-r3-r5-source-intake-gap-readback-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": board_hash_before,
        "current_cursor": current_cursor_summary(),
        "exact_required_filenames_searched": EXACT_REQUIRED_FILENAMES,
        "search_roots": [str(path) for path in SEARCH_ROOTS],
        "max_search_depth": MAX_DEPTH,
        "exact_required_hits": exact_hits,
        "source_candidate_inventory": candidates,
        "intake_roots": roots,
        "verifier_results": verifier_results,
        "ready_intake_roots": sum(1 for row in roots if row["ready"]),
        "ready_intake_root_ids": [row["id"] for row in roots if row["ready"]],
        "decision": "r2_r3_r5_source_intake_gap_readback_v1=no_required_source_label_or_recency_rows_found",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next": (
            "Acquire source-owned or owner-approved R2/R3/R5 row exports and provenance; "
            "then populate the exact fail-closed intake roots and rerun verifiers."
        ),
    }

    (OUT / "r2_r3_r5_source_intake_gap_readback_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    write_csv(OUT / "r2_r3_r5_source_intake_gap_required_file_hits_v1.csv", exact_hits)
    write_csv(OUT / "r2_r3_r5_source_intake_gap_candidate_inventory_v1.csv", candidates)
    write_csv(OUT / "r2_r3_r5_source_intake_gap_roots_v1.csv", roots)

    md = [
        "# R2/R3/R5 Source Intake Gap Readback v1",
        "",
        "- Gate result: `r2_r3_r5_source_intake_gap_readback_v1=no_required_source_label_or_recency_rows_found`.",
        f"- Board hash before run: `{board_hash_before}`.",
        f"- Exact required filenames searched under `/tmp` and `Downloads`: `{len(EXACT_REQUIRED_FILENAMES)}`.",
        f"- Exact required file hits: `{len(exact_hits)}`.",
        f"- Source-label equivalence verifier blocked: `{str(source_label_blocked).lower()}`.",
        f"- Native sub-hour intake root ready: `{str(native_root['ready']).lower()}`.",
        f"- Source-panel recency verifier blocked: `{str(recency_blocked).lower()}`.",
        f"- Direct R6 root schema-ready/unscored: `{str(direct_schema_ready).lower()}`.",
        f"- Ready intake roots: `{result['ready_intake_roots']}/4` (`{';'.join(result['ready_intake_root_ids'])}`).",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Boundary",
        "",
        "This is a readback-only slice for R2/R3/R5. It does not promote the local stock-regime dataset, VantMacro page text, OHLCV provider output, or any generated labels into source-owned MainRegimeV2 rows.",
        "",
        "## Local Inventory",
        "",
        f"- Source-label equivalence root ready: `{str(source_root['ready']).lower()}`; missing `{source_root['missing_files']}`.",
        f"- Native sub-hour root ready: `{str(native_root['ready']).lower()}`; missing `{native_root['missing_files']}`.",
        f"- Recency-extension root ready: `{str(recency_root['ready']).lower()}`; missing `{recency_root['missing_files']}`.",
        "- The local stock-market-regimes panel is still the known `2000-01-03..2026-01-30` source panel, not a post-cutoff R5 extension.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{rel(OUT / 'r2_r3_r5_source_intake_gap_readback_v1.json')}`",
        f"- Required-file hits CSV: `{rel(OUT / 'r2_r3_r5_source_intake_gap_required_file_hits_v1.csv')}`",
        f"- Candidate inventory CSV: `{rel(OUT / 'r2_r3_r5_source_intake_gap_candidate_inventory_v1.csv')}`",
        f"- Intake roots CSV: `{rel(OUT / 'r2_r3_r5_source_intake_gap_roots_v1.csv')}`",
        f"- Verifier command outputs: `{rel(CMD_OUT)}`",
        f"- Assertions: `{rel(CHECKS / 'r2_r3_r5_source_intake_gap_readback_v1_assertions.out')}`",
        "",
        "## Next",
        "",
        "Acquire source-owned or owner-approved R2/R3/R5 row exports and provenance, populate the exact fail-closed intake roots, then rerun source-label and recency verifiers before another completion audit.",
        "",
    ]
    (OUT / "r2_r3_r5_source_intake_gap_readback_v1.md").write_text("\n".join(md), encoding="utf-8")

    assertions = [
        f"PASS exact_required_hits={len(exact_hits)}",
        f"PASS source_label_verifier_blocked={source_label_blocked}",
        f"PASS native_subhour_ready={native_root['ready']}",
        f"PASS recency_verifier_blocked={recency_blocked}",
        f"PASS direct_schema_ready_unscored={direct_schema_ready}",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
    ]
    assert not exact_hits
    assert source_label_blocked
    assert not native_root["ready"]
    assert recency_blocked
    assert direct_schema_ready
    (CHECKS / "r2_r3_r5_source_intake_gap_readback_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    print("\n".join(assertions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
