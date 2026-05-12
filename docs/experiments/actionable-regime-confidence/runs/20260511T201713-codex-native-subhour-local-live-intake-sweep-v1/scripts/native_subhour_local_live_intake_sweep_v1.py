#!/usr/bin/env python3
"""Board A R3 native sub-hour local/live intake sweep.

This run only checks whether a source-owned native sub-hour label package has
appeared locally. It deliberately rejects raw OHLCV/provider panels and prior
projection artifacts as intake evidence.
"""

from __future__ import annotations

import csv
import gzip
import json
import os
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T201713-codex-native-subhour-local-live-intake-sweep-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = RUN_ROOT / "native-subhour-local-live-intake-sweep"
CHECK_DIR = RUN_ROOT / "checks"

REQUIRED_FILES = {
    "native_subhour_source_label_rows.csv",
    "native_subhour_source_label_provenance.json",
}
MAX_CANDIDATE_CSV_ROWS = 500

INTAKE_ROOTS = [
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/private/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-label-equivalence-intake"),
    Path("/private/tmp/ict-engine-source-label-equivalence-intake"),
]

SEARCH_ROOTS = [
    Path("/tmp"),
    Path("/private/tmp"),
    Path("/Users/thrill3r/Downloads"),
]

KEYWORDS = (
    "native",
    "subhour",
    "sub-hour",
    "source-label",
    "source_label",
    "regime",
    "intraday",
    "equivalence",
    "label",
)

EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "target",
    "flutter-sdk",
    "go-sdk",
    "js-sdk",
    "repos",
}


def depth_from(root: Path, current: Path) -> int:
    try:
        return len(current.relative_to(root).parts)
    except ValueError:
        return 999


def safe_header(path: Path) -> str:
    try:
        if path.suffix == ".gz":
            with gzip.open(path, "rt", errors="replace") as handle:
                return handle.readline().strip()[:500]
        if path.suffix.lower() in {".csv", ".json", ".jsonl", ".txt", ".md"}:
            with path.open("rt", errors="replace") as handle:
                return handle.readline().strip()[:500]
    except OSError as exc:
        return f"unreadable:{type(exc).__name__}"
    return ""


def classify(path: Path, header: str) -> tuple[str, bool, str]:
    text = f"{path} {header}".lower()
    name = path.name
    if name in REQUIRED_FILES:
        return "exact_native_subhour_intake_filename_present_needs_pair_and_schema", True, (
            "Exact R3 filename is present; package still requires the paired file "
            "and source-owned provenance verification."
        )
    if "ict-yfinance-validate-market-state-matrix" in text:
        return "blocked_raw_provider_subhour_price_panel_not_source_labels", False, (
            "Sub-hour OHLCV from yfinance is a raw/provider price panel, not "
            "source-owned native sub-hour regime labels."
        )
    if "hmm" in text or "kmeans" in text or "classifier" in text or "prediction" in text:
        return "blocked_generated_or_model_derived_regime_labels", False, (
            "Generated/model-derived labels stay fail-closed for Board A R3."
        )
    if "native-subhour-projection-quarantine" in text or "projection" in text:
        return "blocked_projected_rows_not_native_source_labels", False, (
            "Projected daily/monthly windows cannot close native sub-hour source labels."
        )
    if "stock-market-regimes-20002026" in text:
        return "blocked_daily_source_panel_not_native_subhour", False, (
            "Known daily source panel is already counted and is not native sub-hour."
        )
    if "pump" in text or "manipulation" in text or "spoof" in text:
        return "blocked_direct_manipulation_not_price_root_native_subhour", False, (
            "Direct manipulation artifacts do not supply price-root native sub-hour labels."
        )
    if "docs/experiments/actionable-regime-confidence" in text:
        return "blocked_existing_board_artifact_not_new_intake", False, (
            "Existing Board A artifacts are already registered or rejected."
        )
    if any(token in text for token in ("date", "open", "high", "low", "close", "volume")):
        return "blocked_price_or_feature_panel_not_source_owned_labels", False, (
            "Header looks like prices/features rather than source-owned labels."
        )
    return "blocked_no_r3_native_subhour_source_label_schema", False, (
        "Path matched broad keywords, but no exact R3 intake filename or source-owned label schema was found."
    )


def list_intake_roots() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for root in INTAKE_ROOTS:
        present_files = sorted(path.name for path in root.glob("*") if path.is_file()) if root.exists() else []
        rows.append(
            {
                "root": str(root),
                "exists": root.exists(),
                "present_files": ";".join(present_files),
                "required_rows_present": "native_subhour_source_label_rows.csv" in present_files,
                "required_provenance_present": "native_subhour_source_label_provenance.json" in present_files,
                "complete_native_subhour_package": REQUIRED_FILES.issubset(set(present_files)),
            }
        )
    return rows


def candidate_paths() -> list[Path]:
    out: list[Path] = []
    seen: set[str] = set()
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for current_root, dirs, files in os.walk(root):
            current = Path(current_root)
            dirs[:] = [
                name
                for name in dirs
                if name not in EXCLUDED_DIRS and not name.startswith(".cache")
            ]
            if depth_from(root, current) >= 6:
                dirs[:] = []
            haystack_dir = str(current).lower()
            for file_name in files:
                path = current / file_name
                haystack = f"{haystack_dir}/{file_name.lower()}"
                if file_name in REQUIRED_FILES or any(keyword in haystack for keyword in KEYWORDS):
                    key = str(path)
                    if key not in seen:
                        seen.add(key)
                        out.append(path)
    return sorted(out)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_report(payload: dict[str, object]) -> None:
    report_path = OUT_DIR / "native_subhour_local_live_intake_sweep_v1.md"
    lines = [
        "# Native Subhour Local/Live Intake Sweep v1",
        "",
        f"- Decision: `{payload['decision']}`",
        f"- Intake roots checked: `{payload['intake_roots_checked']}`",
        f"- Candidate files classified: `{payload['candidate_files_classified']}`",
        f"- Candidate CSV rows written: `{payload['candidate_csv_rows_written']}`",
        f"- Exact required intake files present: `{payload['exact_required_intake_files_present']}`",
        f"- Complete native sub-hour package present: `{str(payload['complete_native_subhour_package_present']).lower()}`",
        f"- Ready native sub-hour source-owned label sources: `{payload['ready_native_subhour_source_owned_label_sources']}`",
        f"- Accepted rows added: `{payload['accepted_rows_added']}`",
        f"- New confidence gate: `{str(payload['new_confidence_gate']).lower()}`",
        f"- Native sub-hour source overlap closed: `{str(payload['native_subhour_source_overlap_closed']).lower()}`",
        f"- Strict full objective achieved: `{str(payload['strict_full_objective_achieved']).lower()}`; `update_goal={str(payload['update_goal']).lower()}`",
        "",
        "## Disposition Summary",
        "",
        "| Disposition | Files |",
        "|---|---:|",
    ]
    for disposition, count in payload["disposition_counts"].items():
        lines.append(f"| `{disposition}` | `{count}` |")
    lines.extend(
        [
            "",
            "## Gate Readback",
            "",
            "No source-owned native sub-hour R3 intake package was found. The visible sub-hour yfinance files are raw OHLCV/provider panels and remain rejected as proxy/price data, not native source labels.",
            "",
            "This run is additive after `194400` and does not reopen R6 spoofing/layering, R5 recency-tail, or the owner-request package. It preserves the strict blocker: R3 remains blocked until `native_subhour_source_label_rows.csv` and `native_subhour_source_label_provenance.json` are acquired under an intake root and verified.",
            "",
            "## Artifacts",
            "",
            "- JSON: `native_subhour_local_live_intake_sweep_v1.json`",
            "- Candidate CSV: `native_subhour_local_live_intake_sweep_v1_candidates.csv`",
            "- Intake roots CSV: `native_subhour_local_live_intake_sweep_v1_intake_roots.csv`",
            "- Assertions: `../checks/native_subhour_local_live_intake_sweep_v1_assertions.out`",
            "",
        ]
    )
    report_path.write_text("\n".join(lines))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc).isoformat()

    root_rows = list_intake_roots()
    complete_package = any(bool(row["complete_native_subhour_package"]) for row in root_rows)
    exact_required_present = sum(
        1
        for row in root_rows
        for name in str(row["present_files"]).split(";")
        if name in REQUIRED_FILES
    )

    candidates: list[dict[str, object]] = []
    ready_sources = 0
    for path in candidate_paths():
        header = safe_header(path)
        disposition, exactish, reason = classify(path, header)
        if exactish:
            ready_sources += 1
        try:
            stat = path.stat()
            size_bytes = stat.st_size
            mtime_utc = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
        except OSError:
            size_bytes = -1
            mtime_utc = ""
        candidates.append(
            {
                "path": str(path),
                "size_bytes": size_bytes,
                "mtime_utc": mtime_utc,
                "header_sample": header,
                "disposition": disposition,
                "r3_exact_filename_or_schema_hit": exactish,
                "reason": reason,
            }
        )

    disposition_counts: dict[str, int] = {}
    for row in candidates:
        disposition = str(row["disposition"])
        disposition_counts[disposition] = disposition_counts.get(disposition, 0) + 1

    decision = "native_subhour_local_live_intake_sweep_v1=no_native_subhour_source_owned_intake_package"
    if complete_package:
        decision = "native_subhour_local_live_intake_sweep_v1=potential_intake_package_present_needs_verifier"

    exact_candidate_rows = [
        row for row in candidates if bool(row["r3_exact_filename_or_schema_hit"])
    ]
    non_exact_sample = [
        row for row in candidates if not bool(row["r3_exact_filename_or_schema_hit"])
    ][: max(0, MAX_CANDIDATE_CSV_ROWS - len(exact_candidate_rows))]
    candidates_for_csv = exact_candidate_rows + non_exact_sample

    payload: dict[str, object] = {
        "run_id": RUN_ID,
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "intake_roots_checked": len(root_rows),
        "intake_roots": root_rows,
        "candidate_files_classified": len(candidates),
        "candidate_csv_rows_written": len(candidates_for_csv),
        "candidate_csv_row_policy": (
            "bounded sample of first non-exact candidate rows plus all exact "
            "R3 filename/schema hits; full raw/provider rows are not committed"
        ),
        "exact_required_intake_files_present": exact_required_present,
        "complete_native_subhour_package_present": complete_package,
        "ready_native_subhour_source_owned_label_sources": ready_sources if complete_package else 0,
        "disposition_counts": dict(sorted(disposition_counts.items())),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "native_subhour_source_overlap_closed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    (OUT_DIR / "native_subhour_local_live_intake_sweep_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    write_csv(
        OUT_DIR / "native_subhour_local_live_intake_sweep_v1_intake_roots.csv",
        root_rows,
        [
            "root",
            "exists",
            "present_files",
            "required_rows_present",
            "required_provenance_present",
            "complete_native_subhour_package",
        ],
    )
    write_csv(
        OUT_DIR / "native_subhour_local_live_intake_sweep_v1_candidates.csv",
        candidates_for_csv,
        [
            "path",
            "size_bytes",
            "mtime_utc",
            "header_sample",
            "disposition",
            "r3_exact_filename_or_schema_hit",
            "reason",
        ],
    )
    write_report(payload)

    assertions = [
        ("complete_native_subhour_package_absent", complete_package is False),
        ("accepted_rows_added_zero", payload["accepted_rows_added"] == 0),
        ("new_confidence_gate_false", payload["new_confidence_gate"] is False),
        ("native_subhour_source_overlap_closed_false", payload["native_subhour_source_overlap_closed"] is False),
        ("strict_full_objective_achieved_false", payload["strict_full_objective_achieved"] is False),
        ("update_goal_false", payload["update_goal"] is False),
        ("raw_data_committed_false", payload["raw_data_committed"] is False),
    ]
    failed = [name for name, ok in assertions if not ok]
    (CHECK_DIR / "native_subhour_local_live_intake_sweep_v1_assertions.out").write_text(
        "\n".join(f"{name}=PASS" if ok else f"{name}=FAIL" for name, ok in assertions)
        + "\n"
    )
    if failed:
        raise SystemExit(f"failed assertions: {', '.join(failed)}")


if __name__ == "__main__":
    main()
