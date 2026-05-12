#!/usr/bin/env python3
"""Reconstruct the source-label equivalence intake from source-owned inputs.

This is a supplemental Board A repair. It restores only the /tmp
source-label-equivalence root, reruns the unchanged schema verifier, and
re-scores source confidence fail-closed. It does not promote source-label
schema readiness into accepted confidence.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T010053-codex-source-label-equivalence-reconstruction-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "source-label-equivalence-reconstruction"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
ROWS_NAME = "source_label_equivalence_rows.csv"
PROVENANCE_NAME = "source_label_equivalence_provenance.json"
ROWS_PATH = INTAKE_ROOT / ROWS_NAME
PROVENANCE_PATH = INTAKE_ROOT / PROVENANCE_NAME

TMP_ROOT = Path("/tmp/ict-engine-source-label-equivalence-reconstruction-v1")
NIFTY_ROOT = TMP_ROOT / "nifty"
STAGING_ROOT = TMP_ROOT / "staging"
STAGING_ROWS = STAGING_ROOT / ROWS_NAME
STAGING_PROVENANCE = STAGING_ROOT / PROVENANCE_NAME

STOCK_SOURCE = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
STOCK_SUMMARY = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/dataset_summary.txt")
NIFTY_DATASET = "ahaanverma00/nifty-500-market-and-behavior-regime-dataset"
NIFTY_SOURCE = NIFTY_ROOT / "regime_timeline_history.csv"
NIFTY_METADATA = NIFTY_ROOT / "dataset-metadata.json"

VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)

FIELDS = [
    "package_id",
    "source_owner",
    "source_report_or_dataset",
    "source_pull_date",
    "market_family",
    "symbol",
    "source_symbol",
    "equivalence_policy",
    "event_species",
    "timestamp_or_date",
    "timeframe",
    "main_regime_v2_label",
    "direct_label",
    "matched_negative_group_id",
    "split_role",
    "source_row_id",
    "provenance_hash",
    "redaction_notes",
]

ROOT_LABELS = ["Bear", "Bull", "Crisis", "Sideways"]
ROOT_LABEL_SET = set(ROOT_LABELS)
REQUIRED_SPLITS = ["calibration", "heldout_market", "heldout_time", "test"]
CONFIDENCE_THRESHOLD = 0.95
MIN_SUPPORT = 50
WILSON_THRESHOLD = 0.95
Z95 = 1.959963984540054

EXPECTED_PRIOR = {
    "row_count": 248440,
    "rows_sha256": "915d8148a468798600d4357a60f6c322bd19f421ad7ed01632a5e1c00be2937f",
    "label_counts": {"Bear": 54939, "Bull": 104979, "Crisis": 30623, "Sideways": 57899},
    "split_counts": {
        "calibration": 148976,
        "heldout_market": 26236,
        "heldout_time": 45384,
        "test": 27844,
    },
    "source_owner_counts": {
        "ahaanverma00": 3435,
        "source-owned-stock-market-regimes-2000-2026": 245005,
    },
    "market_family_counts": {
        "india_equity_index": 3435,
        "us_index": 26236,
        "us_single_stock": 218769,
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def run_command(name: str, args: list[str], *, cwd: Path | None = None, timeout: int = 180) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        cwd=cwd or REPO,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    stdout_path = CMD / f"{name}.stdout.txt"
    stderr_path = CMD / f"{name}.stderr.txt"
    exit_path = CMD / f"{name}.exit"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    return {
        "name": name,
        "args": args,
        "returncode": proc.returncode,
        "stdout": rel(stdout_path),
        "stderr": rel(stderr_path),
        "exit": rel(exit_path),
        "stdout_prefix": proc.stdout[:500],
        "stderr_prefix": proc.stderr[:500],
    }


def run_verifier() -> dict[str, Any]:
    command = run_command(
        "source_label_equivalence_verifier",
        [sys.executable, str(VERIFIER), "--intake-root", str(INTAKE_ROOT)],
        timeout=180,
    )
    stdout = (REPO / command["stdout"]).read_text(encoding="utf-8")
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        parsed = {"status": "unparsed", "stdout_prefix": stdout[:500]}
    command["parsed"] = parsed
    return command


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_metadata(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, str):
        data = json.loads(data)
    return data if isinstance(data, dict) else {}


def row_hash(row: dict[str, str]) -> str:
    material = "|".join(f"{key}={row.get(key, '')}" for key in FIELDS if key != "provenance_hash")
    return sha256_text(material)


def stock_market_family(ticker: str) -> str:
    return "us_index" if ticker.startswith("^") else "us_single_stock"


def stock_split_role(day: str, ticker: str) -> str:
    if ticker.startswith("^"):
        return "heldout_market"
    if day < "2018-01-01":
        return "calibration"
    if day < "2023-01-01":
        return "heldout_time"
    return "test"


def nifty_split_role(day: str) -> str:
    parsed = datetime.strptime(day, "%Y-%m-%d").date()
    if parsed < date(2018, 1, 1):
        return "calibration"
    if parsed < date(2023, 1, 1):
        return "heldout_time"
    return "test"


def build_stock_rows() -> tuple[list[dict[str, str]], dict[str, Any]]:
    rows: list[dict[str, str]] = []
    skipped = Counter()
    confidence_values: list[float] = []
    with STOCK_SOURCE.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for line_no, source in enumerate(reader, start=2):
            label = source["regime_label"]
            if label not in ROOT_LABEL_SET:
                skipped[label] += 1
                continue
            day = source["date"]
            ticker = source["ticker"]
            out = {
                "package_id": "price_root_equivalence_us_index_futures",
                "source_owner": "source-owned-stock-market-regimes-2000-2026",
                "source_report_or_dataset": "local_source:stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv",
                "source_pull_date": "2026-05-11",
                "market_family": stock_market_family(ticker),
                "symbol": ticker,
                "source_symbol": f"{ticker}:regime_label",
                "equivalence_policy": "source_panel_regime_label_mapping_v1:regime_label_to_MainRegimeV2;High-volatility_unmapped_no_confidence_acceptance",
                "event_species": "source_panel_daily_market_regime_label",
                "timestamp_or_date": day,
                "timeframe": "1d",
                "main_regime_v2_label": label,
                "direct_label": "",
                "matched_negative_group_id": "",
                "split_role": stock_split_role(day, ticker),
                "source_row_id": f"stock_market_regimes_2000_2026:{line_no}:{ticker}:{day}:{label}",
                "provenance_hash": "",
                "redaction_notes": "reconstructed_schema_root_only_source_confidence_recalibrated_no_acceptance",
            }
            material = "|".join([
                "stock-market-regimes-20002026",
                day,
                ticker,
                label,
                source.get("regime_confidence", ""),
                source.get("macro_context", ""),
            ])
            out["provenance_hash"] = sha256_text(material)
            rows.append(out)
            try:
                confidence_values.append(float(source.get("regime_confidence") or 0.0))
            except ValueError:
                pass
    return rows, {
        "row_count": len(rows),
        "skipped_counts": dict(sorted(skipped.items())),
        "source_confidence_ge_95_count": sum(1 for value in confidence_values if value >= CONFIDENCE_THRESHOLD),
        "source_confidence_min": min(confidence_values) if confidence_values else None,
        "source_confidence_max": max(confidence_values) if confidence_values else None,
    }


def build_nifty_rows() -> tuple[list[dict[str, str]], dict[str, Any]]:
    rows: list[dict[str, str]] = []
    policy = (
        "owner_described_nifty_market_regime_mapping_v1:"
        "macro_state_Durable_to_Bull;"
        "fast_state_Calm_to_Sideways;"
        "fast_state_Stress_to_Crisis;"
        "Fragile_and_Choppy_unmapped_no_Bear_claim"
    )
    with NIFTY_SOURCE.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for source_index, source in enumerate(reader, start=2):
            day = source["Date"]
            candidates = [
                ("macro_state", source.get("macro_state", ""), "Durable", "Bull"),
                ("fast_state", source.get("fast_state", ""), "Calm", "Sideways"),
                ("fast_state", source.get("fast_state", ""), "Stress", "Crisis"),
            ]
            for field_name, observed, expected, label in candidates:
                if observed != expected:
                    continue
                out = {
                    "package_id": "price_root_equivalence_us_index_futures",
                    "source_owner": "ahaanverma00",
                    "source_report_or_dataset": f"kaggle:{NIFTY_DATASET}",
                    "source_pull_date": "2026-05-12",
                    "market_family": "india_equity_index",
                    "symbol": "NIFTY500",
                    "source_symbol": f"NIFTY500:{field_name}",
                    "equivalence_policy": policy,
                    "event_species": "owner_described_nifty_hmm_market_regime",
                    "timestamp_or_date": day,
                    "timeframe": "1d",
                    "main_regime_v2_label": label,
                    "direct_label": "",
                    "matched_negative_group_id": "",
                    "split_role": nifty_split_role(day),
                    "source_row_id": f"nifty_regime_timeline_history:{source_index}:{field_name}:{observed}",
                    "provenance_hash": "",
                    "redaction_notes": "partial_crosswalk_no_Bear_rows_no_strict_completion_claim",
                }
                out["provenance_hash"] = row_hash(out)
                rows.append(out)
    return rows, {"row_count": len(rows)}


def profile_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    labels = Counter(row.get("main_regime_v2_label", "") for row in rows)
    owners = Counter(row.get("source_owner", "") for row in rows)
    markets = Counter(row.get("market_family", "") for row in rows)
    packages = Counter(row.get("package_id", "") for row in rows)
    splits = Counter(row.get("split_role", "") for row in rows)
    symbols = {row.get("symbol", "") for row in rows if row.get("symbol")}
    dates = [row["timestamp_or_date"] for row in rows if row.get("timestamp_or_date")]
    return {
        "row_count": len(rows),
        "label_counts": dict(sorted(labels.items())),
        "source_owner_counts": dict(sorted(owners.items())),
        "market_family_counts": dict(sorted(markets.items())),
        "package_counts": dict(sorted(packages.items())),
        "split_counts": dict(sorted(splits.items())),
        "symbol_count": len(symbols),
        "date_min": min(dates) if dates else "",
        "date_max": max(dates) if dates else "",
    }


def dedupe(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    seen: set[tuple[str, str, str, str]] = set()
    kept: list[dict[str, str]] = []
    removed: list[dict[str, str]] = []
    for row in rows:
        key = (
            row.get("package_id", ""),
            row.get("source_owner", ""),
            row.get("source_row_id", ""),
            row.get("main_regime_v2_label", ""),
        )
        if key in seen:
            removed.append(row)
            continue
        seen.add(key)
        kept.append(row)
    return kept, removed


def stock_confidence_map() -> dict[tuple[str, str, str], float]:
    mapping: dict[tuple[str, str, str], float] = {}
    for row in read_csv(STOCK_SOURCE):
        try:
            confidence = float(row.get("regime_confidence", ""))
        except ValueError:
            continue
        mapping[(row["date"], row["ticker"], row["regime_label"])] = confidence
    return mapping


def nifty_confidence_map() -> dict[tuple[str, str, str, str], float]:
    mapping: dict[tuple[str, str, str, str], float] = {}
    for row in read_csv(NIFTY_SOURCE):
        day = row["Date"]
        symbol = "NIFTY500"
        if row.get("macro_state") == "Durable":
            mapping[(day, symbol, "NIFTY500:macro_state", "Bull")] = float(row.get("macro_confidence") or 0.0)
        if row.get("fast_state") == "Calm":
            mapping[(day, symbol, "NIFTY500:fast_state", "Sideways")] = float(row.get("fast_confidence") or 0.0)
        if row.get("fast_state") == "Stress":
            mapping[(day, symbol, "NIFTY500:fast_state", "Crisis")] = float(row.get("fast_confidence") or 0.0)
    return mapping


def confidence_for_row(
    row: dict[str, str],
    stock_map: dict[tuple[str, str, str], float],
    nifty_map: dict[tuple[str, str, str, str], float],
) -> float | None:
    owner = row.get("source_owner", "")
    label = row.get("main_regime_v2_label", "")
    if owner == "source-owned-stock-market-regimes-2000-2026":
        return stock_map.get((row.get("timestamp_or_date", ""), row.get("symbol", ""), label))
    if owner == "ahaanverma00":
        return nifty_map.get((row.get("timestamp_or_date", ""), row.get("symbol", ""), row.get("source_symbol", ""), label))
    return None


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    denom = 1 + Z95 * Z95 / total
    center = p + Z95 * Z95 / (2 * total)
    radius = Z95 * math.sqrt((p * (1 - p) + Z95 * Z95 / (4 * total)) / total)
    return (center - radius) / denom


def summarize(values: list[float]) -> dict[str, float]:
    if not values:
        return {"min": 0.0, "median": 0.0, "mean": 0.0, "max": 0.0}
    return {
        "min": min(values),
        "median": statistics.median(values),
        "mean": statistics.fmean(values),
        "max": max(values),
    }


def metric_row(label: str, split: str, source_owner: str, market_family: str, values: list[float]) -> dict[str, Any]:
    total = len(values)
    high = sum(1 for value in values if value >= CONFIDENCE_THRESHOLD)
    stats = summarize(values)
    return {
        "label": label,
        "split_role": split,
        "source_owner": source_owner,
        "market_family": market_family,
        "support": total,
        "rows_at_or_above_0_95": high,
        "share_at_or_above_0_95": round(high / total, 10) if total else 0.0,
        "wilson95_lcb": round(wilson_lcb(high, total), 10),
        "confidence_min": round(stats["min"], 10),
        "confidence_median": round(stats["median"], 10),
        "confidence_mean": round(stats["mean"], 10),
        "confidence_max": round(stats["max"], 10),
    }


def gate_for_label(label: str, split_rows: list[dict[str, Any]]) -> dict[str, Any]:
    blockers: list[str] = []
    by_split = {
        row["split_role"]: row
        for row in split_rows
        if row["label"] == label and row["source_owner"] == "ALL" and row["market_family"] == "ALL"
    }
    for split in REQUIRED_SPLITS:
        row = by_split.get(split)
        if row is None:
            blockers.append(f"{split}_missing")
            continue
        if int(row["support"]) < MIN_SUPPORT:
            blockers.append(f"{split}_support_below_{MIN_SUPPORT}")
        if float(row["wilson95_lcb"]) < WILSON_THRESHOLD:
            blockers.append(f"{split}_source_confidence_wilson95_below_{WILSON_THRESHOLD}")
    return {
        "label": label,
        "accepted_source_confidence_95": not blockers,
        "blockers": blockers,
        "required_splits": REQUIRED_SPLITS,
        "min_support": MIN_SUPPORT,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "wilson_threshold": WILSON_THRESHOLD,
    }


def calibrate(rows: list[dict[str, str]]) -> dict[str, Any]:
    stock_map = stock_confidence_map()
    nifty_map = nifty_confidence_map()
    values_by_label_split: dict[tuple[str, str], list[float]] = defaultdict(list)
    values_by_owner_label: dict[tuple[str, str], list[float]] = defaultdict(list)
    values_by_market_label: dict[tuple[str, str], list[float]] = defaultdict(list)
    missing_confidence: list[dict[str, str]] = []
    for row in rows:
        label = row.get("main_regime_v2_label", "")
        split = row.get("split_role", "")
        owner = row.get("source_owner", "")
        market = row.get("market_family", "")
        confidence = confidence_for_row(row, stock_map, nifty_map)
        if confidence is None:
            missing_confidence.append({
                "source_owner": owner,
                "source_row_id": row.get("source_row_id", ""),
                "symbol": row.get("symbol", ""),
                "timestamp_or_date": row.get("timestamp_or_date", ""),
                "label": label,
            })
            continue
        values_by_label_split[(label, split)].append(confidence)
        values_by_owner_label[(owner, label)].append(confidence)
        values_by_market_label[(market, label)].append(confidence)

    split_rows = [
        metric_row(label, split, "ALL", "ALL", values_by_label_split.get((label, split), []))
        for label in ROOT_LABELS
        for split in REQUIRED_SPLITS
    ]
    owner_rows = [
        metric_row(label, "ALL", owner, "ALL", values)
        for (owner, label), values in sorted(values_by_owner_label.items())
    ]
    market_rows = [
        metric_row(label, "ALL", "ALL", market, values)
        for (market, label), values in sorted(values_by_market_label.items())
    ]
    gates = [gate_for_label(label, split_rows) for label in ROOT_LABELS]
    accepted_labels = [gate["label"] for gate in gates if gate["accepted_source_confidence_95"]]
    write_csv(OUT / "source_label_equivalence_reconstruction_label_split_v1.csv", split_rows, list(split_rows[0].keys()))
    write_csv(OUT / "source_label_equivalence_reconstruction_owner_v1.csv", owner_rows, list(owner_rows[0].keys()))
    write_csv(OUT / "source_label_equivalence_reconstruction_market_v1.csv", market_rows, list(market_rows[0].keys()))
    gate_rows = [
        {
            **gate,
            "blockers": ";".join(gate["blockers"]),
            "required_splits": ";".join(gate["required_splits"]),
        }
        for gate in gates
    ]
    write_csv(
        OUT / "source_label_equivalence_reconstruction_gates_v1.csv",
        gate_rows,
        ["label", "accepted_source_confidence_95", "blockers", "required_splits", "min_support", "confidence_threshold", "wilson_threshold"],
    )
    return {
        "split_rows": split_rows,
        "owner_rows": owner_rows,
        "market_rows": market_rows,
        "gates": gates,
        "accepted_source_confidence_95_labels": accepted_labels,
        "missing_confidence_rows": len(missing_confidence),
        "missing_confidence_examples": missing_confidence[:10],
        "new_confidence_gate": len(accepted_labels) == len(ROOT_LABELS) and not missing_confidence,
    }


def write_provenance(profile: dict[str, Any], source_summaries: dict[str, Any]) -> None:
    metadata = parse_metadata(NIFTY_METADATA)
    provenance = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "updated_by": RUN_ID,
        "reconstruction_reason": "current_tmp_source_label_equivalence_root_absent_reconstructed_from_source_owned_inputs",
        "raw_payload_committed_to_repo": False,
        "rows_path": str(ROWS_PATH),
        "rows_sha256": sha256_file(STAGING_ROWS),
        "row_count": profile["row_count"],
        "label_counts": profile["label_counts"],
        "source_owner_counts": profile["source_owner_counts"],
        "market_family_counts": profile["market_family_counts"],
        "package_counts": profile["package_counts"],
        "split_counts": profile["split_counts"],
        "symbol_count": profile["symbol_count"],
        "date_min": profile["date_min"],
        "date_max": profile["date_max"],
        "sources": [
            {
                "source_owner": "source-owned-stock-market-regimes-2000-2026",
                "source_report_or_dataset": "local_source:stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv",
                "source_path": str(STOCK_SOURCE),
                "source_sha256": sha256_file(STOCK_SOURCE),
                "source_summary_path": str(STOCK_SUMMARY),
                "source_summary_sha256": sha256_file(STOCK_SUMMARY) if STOCK_SUMMARY.exists() else None,
                "source_pull_date": "2026-05-11",
                "row_count": source_summaries["stock"]["row_count"],
                "skipped_counts": source_summaries["stock"]["skipped_counts"],
                "license_or_permission": [{"name": "local_download_metadata_missing"}],
            },
            {
                "source_owner": "ahaanverma00",
                "source_report_or_dataset": f"kaggle:{NIFTY_DATASET}",
                "source_path": str(NIFTY_SOURCE),
                "source_sha256": sha256_file(NIFTY_SOURCE),
                "metadata_path": str(NIFTY_METADATA),
                "metadata_sha256": sha256_file(NIFTY_METADATA),
                "source_pull_date": "2026-05-12",
                "row_count": source_summaries["nifty"]["row_count"],
                "license_or_permission": metadata.get("licenses"),
                "title": metadata.get("title"),
            },
        ],
        "limitations": [
            "schema readiness is not Board A confidence acceptance",
            "source confidence calibration remains fail-closed at 0 accepted labels",
            "daily source-label equivalence rows do not satisfy native sub-hour validation",
            "R5 source-panel recency extension remains a separate missing intake root",
            "R6 direct Manipulation controls remain a separate direct-event root",
        ],
    }
    STAGING_PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def copy_to_shared_root() -> dict[str, Any]:
    INTAKE_ROOT.mkdir(parents=True, exist_ok=True)
    existing = [str(path) for path in [ROWS_PATH, PROVENANCE_PATH] if path.exists()]
    if existing:
        return {
            "shared_root_written": False,
            "shared_root_write_status": "blocked_existing_required_files",
            "existing_required_files": existing,
            "shared_root": str(INTAKE_ROOT),
        }
    tmp_rows = INTAKE_ROOT / f".{ROWS_NAME}.{RUN_ID}.tmp"
    tmp_provenance = INTAKE_ROOT / f".{PROVENANCE_NAME}.{RUN_ID}.tmp"
    shutil.copy2(STAGING_ROWS, tmp_rows)
    shutil.copy2(STAGING_PROVENANCE, tmp_provenance)
    tmp_rows.replace(ROWS_PATH)
    tmp_provenance.replace(PROVENANCE_PATH)
    return {
        "shared_root_written": True,
        "shared_root_write_status": "created_required_files",
        "shared_root": str(INTAKE_ROOT),
        "rows_sha256": sha256_file(ROWS_PATH),
        "provenance_sha256": sha256_file(PROVENANCE_PATH),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD.mkdir(parents=True, exist_ok=True)
    STAGING_ROOT.mkdir(parents=True, exist_ok=True)
    if NIFTY_ROOT.exists():
        shutil.rmtree(NIFTY_ROOT)
    NIFTY_ROOT.mkdir(parents=True, exist_ok=True)

    missing_static = [str(path) for path in [BOARD, STOCK_SOURCE, VERIFIER] if not path.exists()]
    if missing_static:
        raise FileNotFoundError(missing_static)

    board_hash_before = sha256_file(BOARD)
    metadata_command = run_command("kaggle_nifty_metadata", ["kaggle", "datasets", "metadata", NIFTY_DATASET, "-p", str(NIFTY_ROOT)])
    download_command = run_command(
        "kaggle_nifty_download",
        ["kaggle", "datasets", "download", NIFTY_DATASET, "-p", str(NIFTY_ROOT), "--force", "--unzip"],
        timeout=300,
    )
    if metadata_command["returncode"] != 0 or download_command["returncode"] != 0:
        raise RuntimeError("NIFTY Kaggle acquisition failed; see command-output")
    missing_nifty = [str(path) for path in [NIFTY_SOURCE, NIFTY_METADATA] if not path.exists()]
    if missing_nifty:
        raise FileNotFoundError(missing_nifty)

    stock_rows, stock_summary = build_stock_rows()
    nifty_rows, nifty_summary = build_nifty_rows()
    merged_rows, removed_rows = dedupe([*stock_rows, *nifty_rows])
    profile = profile_rows(merged_rows)
    write_csv(STAGING_ROWS, merged_rows, FIELDS)
    write_provenance(profile, {"stock": stock_summary, "nifty": nifty_summary})
    shared_write = copy_to_shared_root()

    verifier = run_verifier()
    verifier_status = verifier["parsed"].get("status")
    verifier_returncode = verifier["returncode"]
    rows_for_calibration = read_csv(ROWS_PATH)
    calibration = calibrate(rows_for_calibration)

    reconstructed_hash = sha256_file(ROWS_PATH)
    comparisons = {
        "matches_prior_row_count": profile["row_count"] == EXPECTED_PRIOR["row_count"],
        "matches_prior_rows_sha256": reconstructed_hash == EXPECTED_PRIOR["rows_sha256"],
        "matches_prior_label_counts": profile["label_counts"] == EXPECTED_PRIOR["label_counts"],
        "matches_prior_split_counts": profile["split_counts"] == EXPECTED_PRIOR["split_counts"],
        "matches_prior_source_owner_counts": profile["source_owner_counts"] == EXPECTED_PRIOR["source_owner_counts"],
        "matches_prior_market_family_counts": profile["market_family_counts"] == EXPECTED_PRIOR["market_family_counts"],
        "expected_prior_rows_sha256": EXPECTED_PRIOR["rows_sha256"],
        "reconstructed_rows_sha256": reconstructed_hash,
    }
    decision = "source_label_equivalence_reconstruction_v1=reconstructed_schema_ready_source_confidence_no_acceptance"
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": board_hash_before,
        "decision": decision,
        "intake_root": str(INTAKE_ROOT),
        "tmp_root": str(TMP_ROOT),
        "nifty_dataset": NIFTY_DATASET,
        "kaggle_commands": [metadata_command, download_command],
        "source_summaries": {"stock": stock_summary, "nifty": nifty_summary},
        "dedupe_removed_rows": len(removed_rows),
        "profile": profile,
        "shared_write": shared_write,
        "verifier": verifier,
        "calibration": {
            "accepted_source_confidence_95_labels": calibration["accepted_source_confidence_95_labels"],
            "new_confidence_gate": calibration["new_confidence_gate"],
            "missing_confidence_rows": calibration["missing_confidence_rows"],
            "gates": calibration["gates"],
        },
        "prior_comparison": comparisons,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_source_label_root_mutated": shared_write["shared_root_written"],
        "r6_canonical_intake_mutated": False,
        "owner_export_root_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": True,
        "trade_usable": False,
        "blocker": "Source-label equivalence root is schema-ready again, but source-confidence accepted labels remain 0/4; R5 recency, R3 native sub-hour, and R6 source-owned normal controls remain blocked.",
        "next_action": "Preserve active V71 R6 source-owned control acquisition next action; do not rerun downstream promotion until R6 controls or explicit FLIP approval and canonical merge exist.",
    }

    json_path = OUT / "source_label_equivalence_reconstruction_v1.json"
    report_path = OUT / "source_label_equivalence_reconstruction_v1.md"
    assertions_path = CHECKS / "source_label_equivalence_reconstruction_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report_lines = [
        "# Source Label Equivalence Reconstruction v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Shared root write: `{shared_write['shared_root_write_status']}`.",
        f"- Rows reconstructed: `{profile['row_count']}`; labels: `{profile['label_counts']}`.",
        f"- Source owners: `{profile['source_owner_counts']}`.",
        f"- Market families: `{profile['market_family_counts']}`.",
        f"- Split counts: `{profile['split_counts']}`.",
        f"- Verifier status: `{verifier_status}`; return code `{verifier_returncode}`.",
        f"- Accepted source-confidence labels: `{calibration['accepted_source_confidence_95_labels']}`.",
        f"- Prior row-count match: `{comparisons['matches_prior_row_count']}`; prior split-count match: `{comparisons['matches_prior_split_counts']}`; prior rows hash match: `{comparisons['matches_prior_rows_sha256']}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; R6 canonical intake mutated: `false`; owner-export root mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Boundary",
        "",
        "This reconstructs a missing `/tmp` source-label equivalence intake from the local stock-regime source file and a fresh Kaggle NIFTY public pull. It is schema repair only. The confidence gate remains fail-closed, and this does not authorize R6 canonical merge or downstream promotion.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{rel(json_path)}`",
        f"- Report: `{rel(report_path)}`",
        f"- Label split CSV: `{rel(OUT / 'source_label_equivalence_reconstruction_label_split_v1.csv')}`",
        f"- Source owner CSV: `{rel(OUT / 'source_label_equivalence_reconstruction_owner_v1.csv')}`",
        f"- Market family CSV: `{rel(OUT / 'source_label_equivalence_reconstruction_market_v1.csv')}`",
        f"- Gate CSV: `{rel(OUT / 'source_label_equivalence_reconstruction_gates_v1.csv')}`",
        f"- Verifier stdout: `{verifier['stdout']}`",
        f"- Kaggle metadata stdout: `{metadata_command['stdout']}`",
        f"- Kaggle download stdout: `{download_command['stdout']}`",
        f"- Assertions: `{rel(assertions_path)}`",
        f"- Reproduction script: `{rel(Path(__file__))}`",
    ]
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"PASS decision={decision}",
        f"PASS shared_root_write_status={shared_write['shared_root_write_status']}",
        f"PASS row_count={profile['row_count']}",
        f"PASS matches_prior_row_count={str(comparisons['matches_prior_row_count']).lower()}",
        f"PASS matches_prior_label_counts={str(comparisons['matches_prior_label_counts']).lower()}",
        f"PASS matches_prior_split_counts={str(comparisons['matches_prior_split_counts']).lower()}",
        f"PASS verifier_status={verifier_status}",
        f"PASS verifier_returncode={verifier_returncode}",
        f"PASS accepted_source_confidence_95_labels={','.join(calibration['accepted_source_confidence_95_labels']) or 'none'}",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS runtime_code_changed=false",
        "PASS r6_canonical_intake_mutated=false",
        "PASS owner_export_root_mutated=false",
        "PASS thresholds_relaxed=false",
        "PASS raw_data_committed=false",
        "PASS trade_usable=false",
    ]
    if verifier_status != "schema_ready_unscored" or verifier_returncode != 0:
        raise AssertionError("source-label verifier did not return schema_ready_unscored")
    if calibration["new_confidence_gate"]:
        raise AssertionError("unexpected source-confidence acceptance")
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "decision": decision,
        "row_count": profile["row_count"],
        "verifier_status": verifier_status,
        "accepted_source_confidence_95_labels": calibration["accepted_source_confidence_95_labels"],
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "report": rel(report_path),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
