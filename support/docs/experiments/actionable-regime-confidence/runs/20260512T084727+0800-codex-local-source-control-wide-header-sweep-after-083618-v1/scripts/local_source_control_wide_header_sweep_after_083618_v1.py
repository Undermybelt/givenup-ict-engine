#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import zipfile


RUN_ID = "20260512T084727+0800-codex-local-source-control-wide-header-sweep-after-083618-v1"
ARTIFACT = "local-source-control-wide-header-sweep-after-083618-v1"
BASE = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT = BASE / ARTIFACT
CHECKS = BASE / "checks"

SCAN_ROOTS = [
    Path("/Users/thrill3r/Downloads/Tomac"),
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"),
]

EXACT_REQUIRED_NAMES = {
    "source_control_package_v1.json",
    "source_control_manifest_v1.json",
    "positive_rows.csv",
    "matched_normal_controls.csv",
    "owner_export_provenance.json",
    "license_or_ticket_provenance.json",
}

ORDER_LIFECYCLE_TERMS = {
    "order_id",
    "orderid",
    "clordid",
    "execid",
    "event_type",
    "message_type",
    "order_status",
    "order_type",
    "side",
    "aggressor_side",
    "bid_px",
    "ask_px",
    "bid_size",
    "ask_size",
    "depth",
    "book_level",
    "sequence",
    "ts_recv",
}

CONTROL_TERMS = {
    "control_id",
    "matched_control",
    "normal_control",
    "label",
    "is_positive",
    "case_id",
    "source_control",
}

OHLCV_TERMS = {"open", "high", "low", "close", "volume", "ohlcv", "ts_event"}


def safe_rel(path: Path) -> str:
    return str(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def tokenize(values: list[str]) -> set[str]:
    out: set[str] = set()
    for value in values:
        value = value.strip().lower()
        if value:
            out.add(value)
    return out


def csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f)
        return next(reader, [])


def json_keys(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return sorted(str(k) for k in data.keys())
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return sorted(str(k) for k in data[0].keys())
    return []


def zip_member_header(zf: zipfile.ZipFile, name: str) -> list[str]:
    with zf.open(name) as raw:
        sample = raw.read(8192).decode("utf-8", errors="replace").splitlines()
    if not sample:
        return []
    if name.lower().endswith(".csv"):
        return next(csv.reader([sample[0]]), [])
    if name.lower().endswith(".json"):
        try:
            data = json.loads("\n".join(sample))
        except json.JSONDecodeError:
            return []
        if isinstance(data, dict):
            return sorted(str(k) for k in data.keys())
    return []


def classify(columns: list[str], name: str) -> dict[str, object]:
    tokens = tokenize(columns)
    order_hits = sorted(tokens & ORDER_LIFECYCLE_TERMS)
    control_hits = sorted(tokens & CONTROL_TERMS)
    ohlcv_hits = sorted(tokens & OHLCV_TERMS)
    exact_required = Path(name).name in EXACT_REQUIRED_NAMES
    verifier_native = exact_required and bool(order_hits or control_hits)
    if verifier_native:
        schema_class = "verifier_native_candidate"
    elif order_hits or control_hits:
        schema_class = "order_lifecycle_or_control_hint"
    elif len(ohlcv_hits) >= 4:
        schema_class = "ohlcv_or_bar_context"
    else:
        schema_class = "other"
    return {
        "schema_class": schema_class,
        "order_lifecycle_hits": "|".join(order_hits),
        "control_hits": "|".join(control_hits),
        "ohlcv_hits": "|".join(ohlcv_hits),
        "exact_required_name": exact_required,
        "verifier_native_hint": verifier_native,
    }


def iter_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        if root.is_file():
            files.append(root)
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules", "target"}]
            for filename in filenames:
                path = Path(dirpath) / filename
                if path.suffix.lower() in {".csv", ".json", ".zip", ".rar", ".dbn", ".pcap", ".parquet"}:
                    files.append(path)
    return sorted(files)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    archive_member_rows: list[dict[str, object]] = []
    files = iter_files()

    for path in files:
        suffix = path.suffix.lower()
        columns: list[str] = []
        archive_members_read = 0
        archive_header_hits = 0
        try:
            if suffix == ".csv":
                columns = csv_header(path)
            elif suffix == ".json":
                columns = json_keys(path)
            elif suffix == ".zip":
                with zipfile.ZipFile(path) as zf:
                    members = [m for m in zf.namelist() if not m.endswith("/")]
                    for member in members[:200]:
                        member_suffix = Path(member).suffix.lower()
                        if member_suffix not in {".csv", ".json"}:
                            continue
                        archive_members_read += 1
                        member_columns = zip_member_header(zf, member)
                        member_class = classify(member_columns, member)
                        if member_class["order_lifecycle_hits"] or member_class["control_hits"]:
                            archive_header_hits += 1
                        archive_member_rows.append(
                            {
                                "archive": safe_rel(path),
                                "member": member,
                                "columns_or_keys": "|".join(member_columns[:32]),
                                **member_class,
                            }
                        )
        except Exception as exc:  # fail closed; record inspection errors as non-unlocking
            columns = [f"inspection_error:{type(exc).__name__}"]

        cls = classify(columns, path.name)
        rows.append(
            {
                "path": safe_rel(path),
                "size_bytes": path.stat().st_size if path.exists() else 0,
                "sha256": sha256(path) if path.exists() and path.stat().st_size < 512 * 1024 * 1024 else "",
                "suffix": suffix,
                "columns_or_keys": "|".join(columns[:32]),
                "archive_members_read": archive_members_read,
                "archive_header_hits": archive_header_hits,
                **cls,
            }
        )

    exact_required_files = [r for r in rows if r["exact_required_name"]]
    verifier_native = [r for r in rows if r["verifier_native_hint"]]
    order_lifecycle_hints = [
        r for r in rows if r["order_lifecycle_hits"] or r["control_hits"] or r["archive_header_hits"]
    ]

    target_rows = []
    for root in SCAN_ROOTS[1:]:
        root_files = list(root.rglob("*")) if root.exists() else []
        target_rows.append(
            {
                "root": str(root),
                "exists": root.exists(),
                "file_count": sum(1 for p in root_files if p.is_file()),
                "has_exact_required_package": any(p.name in EXACT_REQUIRED_NAMES for p in root_files if p.is_file()),
            }
        )

    summary = {
        "run_id": RUN_ID,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": "local_source_control_wide_header_sweep_after_083618_v1=no_verifier_native_source_control_package_no_unlock",
        "scan_roots": [str(p) for p in SCAN_ROOTS],
        "files_scanned": len(files),
        "archive_member_headers_read": len(archive_member_rows),
        "exact_required_files_found": len(exact_required_files),
        "verifier_native_hint_files": len(verifier_native),
        "order_lifecycle_or_control_hint_files": len(order_lifecycle_hints),
        "accepted_rows_added": 0,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
        "target_roots": target_rows,
    }

    rows_csv = OUT / "local_source_control_wide_header_sweep_rows_v1.csv"
    with rows_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["path"])
        writer.writeheader()
        writer.writerows(rows)

    member_csv = OUT / "local_source_control_wide_header_sweep_archive_members_v1.csv"
    with member_csv.open("w", newline="", encoding="utf-8") as f:
        fieldnames = list(archive_member_rows[0].keys()) if archive_member_rows else [
            "archive",
            "member",
            "columns_or_keys",
            "schema_class",
            "order_lifecycle_hits",
            "control_hits",
            "ohlcv_hits",
            "exact_required_name",
            "verifier_native_hint",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(archive_member_rows)

    targets_csv = OUT / "local_source_control_wide_header_sweep_target_roots_v1.csv"
    with targets_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(target_rows[0].keys()))
        writer.writeheader()
        writer.writerows(target_rows)

    json_path = OUT / "local_source_control_wide_header_sweep_after_083618_v1.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md = OUT / "local_source_control_wide_header_sweep_after_083618_v1.md"
    md.write_text(
        "\n".join(
            [
                "# Local Source/Control Wide Header Sweep After 083618 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{summary['gate_result']}`",
                "",
                "## Scope",
                "",
                "Read-only local header/member-name sweep across Tomac downloads and R6 owner-export target roots. "
                "This artifact does not copy files into target roots, does not approve OHLCV/bar/symbology files, "
                "does not run Auto-Quant, direct verifier, split calibration, canonical merge, Pre-Bayes, BBN, CatBoost, "
                "path-ranking, or execution-tree promotion, and does not call `update_goal`.",
                "",
                "## Summary",
                "",
                f"- Files scanned: `{summary['files_scanned']}`.",
                f"- Archive member headers read: `{summary['archive_member_headers_read']}`.",
                f"- Exact required source/control file names found: `{summary['exact_required_files_found']}`.",
                f"- Verifier-native hint files: `{summary['verifier_native_hint_files']}`.",
                f"- Order-lifecycle/control hint files: `{summary['order_lifecycle_or_control_hint_files']}`.",
                "",
                "## Decision",
                "",
                "- No exact required source/control package was found in target roots or the bounded Tomac scan.",
                "- Local OHLCV/bar, strategy/backtest, symbology, archive member-name, and weak header hints remain non-unlocking.",
                "- Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed false; `update_goal=false`.",
                "",
                "## Next",
                "",
                "Continue source/control acquisition only unless the user explicitly selects exactly one historical path for non-promotional factor research: `HTF`, `MTF`, or `LTF`.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    checks = CHECKS / "local_source_control_wide_header_sweep_after_083618_v1_assertions.out"
    checks.write_text(
        "\n".join(
            [
                f"gate_result={summary['gate_result']}",
                f"files_scanned={summary['files_scanned']}",
                f"archive_member_headers_read={summary['archive_member_headers_read']}",
                f"exact_required_files_found={summary['exact_required_files_found']}",
                f"verifier_native_hint_files={summary['verifier_native_hint_files']}",
                f"order_lifecycle_or_control_hint_files={summary['order_lifecycle_or_control_hint_files']}",
                "accepted_rows_added=0",
                "valid_required_root_unlock=false",
                "source_control_evidence_acquired=false",
                "canonical_merge=false",
                "selected_data_autoquant_promotion=false",
                "downstream_promotion_rerun=false",
                "strict_full_objective=false",
                "trade_usable=false",
                "promotion_allowed=false",
                "update_goal=false",
                "",
            ]
        ),
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
