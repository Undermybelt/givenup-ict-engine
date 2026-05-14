#!/usr/bin/env python3
"""Materialize and verify the HF TSIE native-intraday R3 source candidate."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import requests


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20260512T062902+0800-codex-r3-hf-tsie-native-intraday-intake-v1"
SLUG = "r3-hf-tsie-native-intraday-intake-v1"
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"
COMMAND_OUT = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

SOURCE_ID = "sujinwo/tsie-market-regime-dataset"
SOURCE_FILE = "tft_dataset_labeled.parquet"
SOURCE_COMMIT = "75e7e2f86c37f8f28204651dcccf8338ca50aa6b"
SOURCE_LICENSE = "mit"
SOURCE_PAGE = f"https://huggingface.co/datasets/{SOURCE_ID}"
SOURCE_API = f"https://huggingface.co/api/datasets/{SOURCE_ID}"
SOURCE_INFO = f"https://datasets-server.huggingface.co/info?dataset={SOURCE_ID}"
SOURCE_FIRST_ROWS = f"https://datasets-server.huggingface.co/first-rows?dataset={SOURCE_ID}&config=default&split=train"
SOURCE_README = f"{SOURCE_PAGE}/raw/main/README.md"

RAW_ROOT = Path("/tmp/ict-engine-hf-tsie-native-intraday-source-v1")
RAW_PATH = RAW_ROOT / SOURCE_FILE
PREFETCH_PATH = Path("/tmp/ict-engine-tsie-download-test") / SOURCE_FILE
TARGET_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
TMP_TARGET_ROOT = Path(f"/tmp/ict-engine-native-subhour-source-label-intake.tmp.{RUN_ID}")
ROWS_FILE = "native_subhour_source_label_rows.csv"
PROVENANCE_FILE = "native_subhour_source_label_provenance.json"

ROOT_LABELS = ["Bear", "Bull", "Crisis", "Sideways"]
REQUIRED_SPLITS = ["calibration", "heldout_market", "heldout_time", "test"]
TIMEFRAME_MAP = {"60": "1h", "240": "4h", "1D": "1d"}
REGIME_NAMES = {
    0: "STRONG SELL",
    1: "WEAK SELL",
    2: "BEAR TRAP",
    3: "FLAT / NOISE",
    4: "BULL TRAP",
    5: "WEAK BUY",
    6: "STRONG BUY",
}
FAIL_CLOSED_MAPPING = {
    0: "Bear",
    1: "Bear",
    3: "Sideways",
    5: "Bull",
    6: "Bull",
}
ABSTAINED_LABELS = {
    2: "BEAR TRAP is reversal/false-breakdown semantics, not a stable parent root.",
    4: "BULL TRAP is reversal/false-breakout semantics, not a stable parent root.",
}
ROW_FIELDS = [
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
    "source_regime_label",
    "source_regime_name",
    "source_group_id",
]


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def command_record(name: str, proc: subprocess.CompletedProcess[str]) -> None:
    (COMMAND_OUT / f"{name}.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (COMMAND_OUT / f"{name}.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    (COMMAND_OUT / f"{name}.exit").write_text(str(proc.returncode) + "\n", encoding="utf-8")


def fetch_text(url: str, name: str) -> str:
    try:
        response = requests.get(url, timeout=45)
        response.raise_for_status()
        text = response.text
    except Exception as exc:  # noqa: BLE001
        text = json.dumps({"error": type(exc).__name__, "message": str(exc), "url": url})
    (COMMAND_OUT / name).write_text(text, encoding="utf-8")
    return text


def ensure_raw_source() -> dict[str, Any]:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    if not RAW_PATH.exists() and PREFETCH_PATH.exists():
        try:
            os.link(PREFETCH_PATH, RAW_PATH)
        except OSError:
            shutil.copy2(PREFETCH_PATH, RAW_PATH)

    download_proc: subprocess.CompletedProcess[str] | None = None
    if not RAW_PATH.exists():
        download_proc = subprocess.run(
            [
                "hf",
                "download",
                "--repo-type",
                "dataset",
                SOURCE_ID,
                SOURCE_FILE,
                "--local-dir",
                str(RAW_ROOT),
            ],
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
        )
        command_record("hf_download", download_proc)

    return {
        "raw_path": str(RAW_PATH),
        "download_command_ran": download_proc is not None,
        "download_return_code": download_proc.returncode if download_proc else 0,
        "raw_exists": RAW_PATH.exists(),
        "raw_size_bytes": RAW_PATH.stat().st_size if RAW_PATH.exists() else 0,
        "raw_sha256": sha256_file(RAW_PATH) if RAW_PATH.exists() else "",
    }


def parse_group_id(group_id: str) -> tuple[str, str]:
    parts = group_id.split("_")
    if len(parts) < 4:
        return group_id, "unknown"
    return parts[2], TIMEFRAME_MAP.get(parts[-1], parts[-1])


def split_role(symbol: str, ts: datetime) -> str:
    market_hash = int(hashlib.sha256(symbol.encode("utf-8")).hexdigest()[:8], 16)
    if market_hash % 10 == 0:
        return "heldout_market"
    if ts.year < 2018:
        return "calibration"
    if ts.year < 2022:
        return "heldout_time"
    return "test"


def is_intraday(timeframe: str) -> bool:
    return timeframe in {"1h", "4h"}


def is_strict_subhour(timeframe: str) -> bool:
    return timeframe.endswith("m") and int(timeframe[:-1]) < 60


def materialize_rows() -> dict[str, Any]:
    if TARGET_ROOT.exists():
        raise FileExistsError(
            f"target root already exists, refusing to overwrite concurrent intake: {TARGET_ROOT}"
        )
    if TMP_TARGET_ROOT.exists():
        shutil.rmtree(TMP_TARGET_ROOT)
    TMP_TARGET_ROOT.mkdir(parents=True, exist_ok=True)

    rows_path = TMP_TARGET_ROOT / ROWS_FILE
    pf = pq.ParquetFile(RAW_PATH)
    label_counts = Counter()
    mapped_label_counts = Counter()
    abstained_counts = Counter()
    excluded_timeframe_counts = Counter()
    timeframe_counts = Counter()
    split_counts = Counter()
    label_split_counts = Counter()
    symbol_counts = Counter()
    source_label_timeframe_counts = Counter()
    date_min: str | None = None
    date_max: str | None = None
    mapped_rows = 0
    raw_rows_seen = 0
    intraday_rows = 0
    strict_subhour_rows = 0
    sample_rows: list[dict[str, str]] = []

    with rows_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ROW_FIELDS)
        writer.writeheader()
        for rg_idx in range(pf.metadata.num_row_groups):
            table = pf.read_row_group(rg_idx, columns=["group_id", "time_idx", "time", "regime_label"])
            group_ids = table.column("group_id").to_pylist()
            time_indices = table.column("time_idx").to_pylist()
            times = table.column("time").to_pylist()
            labels = table.column("regime_label").to_pylist()
            for group_id, time_idx, ts, source_label in zip(group_ids, time_indices, times, labels):
                raw_rows_seen += 1
                source_label = int(source_label)
                label_counts[source_label] += 1
                symbol_root, timeframe = parse_group_id(group_id)
                source_label_timeframe_counts[(source_label, timeframe)] += 1
                if source_label not in FAIL_CLOSED_MAPPING:
                    abstained_counts[source_label] += 1
                    continue
                if not is_intraday(timeframe):
                    excluded_timeframe_counts[timeframe] += 1
                    continue
                symbol = f"IDX:{symbol_root}"
                role = split_role(symbol, ts)
                target_label = FAIL_CLOSED_MAPPING[source_label]
                timestamp = ts.isoformat()
                if date_min is None or timestamp < date_min:
                    date_min = timestamp
                if date_max is None or timestamp > date_max:
                    date_max = timestamp
                row_id = f"hf_tsie:{group_id}:{time_idx}:{timestamp}:{source_label}"
                row = {
                    "package_id": "r3_hf_tsie_native_intraday_source_labels",
                    "source_owner": SOURCE_ID,
                    "source_report_or_dataset": f"{SOURCE_PAGE}@{SOURCE_COMMIT}:{SOURCE_FILE}",
                    "source_pull_date": date.today().isoformat(),
                    "market_family": "indonesia_equity",
                    "symbol": symbol,
                    "source_symbol": f"{group_id}:regime_label",
                    "equivalence_policy": (
                        "hf_tsie_regime_label_to_MainRegimeV2_fail_closed_v1;"
                        "trap_labels_abstained;crisis_no_direct_mapping;source_confidence_absent"
                    ),
                    "event_species": "native_intraday_idx_market_regime_label",
                    "timestamp_or_date": timestamp,
                    "timeframe": timeframe,
                    "main_regime_v2_label": target_label,
                    "direct_label": "",
                    "matched_negative_group_id": "",
                    "split_role": role,
                    "source_row_id": row_id,
                    "provenance_hash": sha256_text(row_id),
                    "redaction_notes": "public_mit_hf_dataset_raw_parquet_hashed_raw_not_committed",
                    "source_regime_label": source_label,
                    "source_regime_name": REGIME_NAMES[source_label],
                    "source_group_id": group_id,
                }
                writer.writerow(row)
                mapped_rows += 1
                intraday_rows += int(is_intraday(timeframe))
                strict_subhour_rows += int(is_strict_subhour(timeframe))
                mapped_label_counts[target_label] += 1
                timeframe_counts[timeframe] += 1
                split_counts[role] += 1
                label_split_counts[(target_label, role)] += 1
                symbol_counts[symbol] += 1
                if len(sample_rows) < 5:
                    sample_rows.append(row)

    rows_sha = sha256_file(rows_path)
    missing_labels = sorted(set(ROOT_LABELS) - set(mapped_label_counts))
    label_summary = [
        {
            "main_regime_v2_label": label,
            "rows": mapped_label_counts.get(label, 0),
            "present": label in mapped_label_counts,
            "source_confidence_available": False,
            "accepted_source_confidence_95": False,
            "blocker": (
                "missing_label"
                if label in missing_labels
                else "source_confidence_absent;split_calibration_not_accepted"
            ),
        }
        for label in ROOT_LABELS
    ]
    split_summary = [
        {
            "main_regime_v2_label": label,
            "split_role": split,
            "rows": label_split_counts.get((label, split), 0),
            "support_present": label_split_counts.get((label, split), 0) > 0,
            "source_confidence_available": False,
            "accepted_source_confidence_95": False,
        }
        for label in ROOT_LABELS
        for split in REQUIRED_SPLITS
    ]

    provenance = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "dataset_id": SOURCE_ID,
            "page_url": SOURCE_PAGE,
            "api_url": SOURCE_API,
            "info_url": SOURCE_INFO,
            "first_rows_url": SOURCE_FIRST_ROWS,
            "readme_url": SOURCE_README,
            "commit": SOURCE_COMMIT,
            "license": SOURCE_LICENSE,
            "file": SOURCE_FILE,
            "raw_path": str(RAW_PATH),
            "raw_size_bytes": RAW_PATH.stat().st_size,
            "raw_sha256": sha256_file(RAW_PATH),
        },
        "target_root": str(TARGET_ROOT),
        "rows_file": ROWS_FILE,
        "rows_sha256": rows_sha,
        "row_count": mapped_rows,
        "raw_rows_seen": raw_rows_seen,
        "raw_label_counts": {str(k): v for k, v in sorted(label_counts.items())},
        "mapped_main_regime_v2_counts": dict(sorted(mapped_label_counts.items())),
        "abstained_source_label_counts": {str(k): v for k, v in sorted(abstained_counts.items())},
        "excluded_timeframe_counts": dict(sorted(excluded_timeframe_counts.items())),
        "timeframe_counts": dict(sorted(timeframe_counts.items())),
        "split_counts": dict(sorted(split_counts.items())),
        "symbol_count": len(symbol_counts),
        "date_min": date_min,
        "date_max": date_max,
        "label_mapping": {str(k): v for k, v in sorted(FAIL_CLOSED_MAPPING.items())},
        "abstained_label_policy": {str(k): v for k, v in sorted(ABSTAINED_LABELS.items())},
        "split_policy": (
            "sha256(symbol)%10==0 heldout_market; otherwise timestamp year <2018 calibration, "
            "2018-2021 heldout_time, >=2022 test"
        ),
        "strict_subhour_interval_present": strict_subhour_rows > 0,
        "native_intraday_interval_present": intraday_rows > 0,
        "source_confidence_available": False,
        "missing_main_regime_v2_labels": missing_labels,
        "sample_rows": sample_rows,
        "raw_data_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
    }
    (TMP_TARGET_ROOT / PROVENANCE_FILE).write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.rename(TMP_TARGET_ROOT, TARGET_ROOT)

    return {
        "provenance": provenance,
        "label_summary": label_summary,
        "split_summary": split_summary,
        "required_files": [
            {
                "file": ROWS_FILE,
                "path": str(TARGET_ROOT / ROWS_FILE),
                "present": True,
                "size_bytes": (TARGET_ROOT / ROWS_FILE).stat().st_size,
                "sha256": rows_sha,
                "data_rows": mapped_rows,
            },
            {
                "file": PROVENANCE_FILE,
                "path": str(TARGET_ROOT / PROVENANCE_FILE),
                "present": True,
                "size_bytes": (TARGET_ROOT / PROVENANCE_FILE).stat().st_size,
                "sha256": sha256_file(TARGET_ROOT / PROVENANCE_FILE),
                "data_rows": 0,
            },
        ],
    }


def direct_verifier(materialized: dict[str, Any]) -> dict[str, Any]:
    provenance = materialized["provenance"]
    labels_present = sorted(provenance["mapped_main_regime_v2_counts"].keys())
    missing_labels = provenance["missing_main_regime_v2_labels"]
    required_files_present = all(row["present"] for row in materialized["required_files"])
    blockers = []
    if missing_labels:
        blockers.append("missing_main_regime_v2_labels=" + ",".join(missing_labels))
    if not provenance["source_confidence_available"]:
        blockers.append("source_confidence_absent")
    if not provenance["strict_subhour_interval_present"]:
        blockers.append("strict_subhour_interval_absent")
    verifier_status = "schema_ready_unscored_no_acceptance" if required_files_present else "blocked_missing_required_files"
    return {
        "run_id": RUN_ID,
        "artifact_type": "r3_hf_tsie_native_intraday_direct_verifier_v1",
        "status": verifier_status,
        "required_files_present": required_files_present,
        "target_root": str(TARGET_ROOT),
        "row_count": provenance["row_count"],
        "labels_present": labels_present,
        "missing_labels": missing_labels,
        "timeframe_counts": provenance["timeframe_counts"],
        "split_counts": provenance["split_counts"],
        "strict_subhour_interval_present": provenance["strict_subhour_interval_present"],
        "native_intraday_interval_present": provenance["native_intraday_interval_present"],
        "source_confidence_available": provenance["source_confidence_available"],
        "blockers": blockers,
        "accepted_rows_added": 0,
        "canonical_merge_allowed_now": False,
        "downstream_rerun_allowed_now": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }


def build_report(
    *,
    download: dict[str, Any],
    materialized: dict[str, Any],
    verifier: dict[str, Any],
    board_hash: str,
) -> dict[str, Any]:
    gate_result = "r3_hf_tsie_native_intraday_intake_v1=raw_downloaded_target_root_materialized_no_acceptance"
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact": board_hash,
        "gate_result": gate_result,
        "source": materialized["provenance"]["source"],
        "target_root": str(TARGET_ROOT),
        "raw_download": download,
        "materialization": {
            "row_count": materialized["provenance"]["row_count"],
            "raw_rows_seen": materialized["provenance"]["raw_rows_seen"],
            "raw_label_counts": materialized["provenance"]["raw_label_counts"],
            "mapped_main_regime_v2_counts": materialized["provenance"]["mapped_main_regime_v2_counts"],
            "abstained_source_label_counts": materialized["provenance"]["abstained_source_label_counts"],
            "excluded_timeframe_counts": materialized["provenance"]["excluded_timeframe_counts"],
            "timeframe_counts": materialized["provenance"]["timeframe_counts"],
            "split_counts": materialized["provenance"]["split_counts"],
            "date_min": materialized["provenance"]["date_min"],
            "date_max": materialized["provenance"]["date_max"],
            "strict_subhour_interval_present": materialized["provenance"]["strict_subhour_interval_present"],
            "native_intraday_interval_present": materialized["provenance"]["native_intraday_interval_present"],
            "source_confidence_available": materialized["provenance"]["source_confidence_available"],
            "missing_main_regime_v2_labels": materialized["provenance"]["missing_main_regime_v2_labels"],
        },
        "direct_verifier": verifier,
        "split_calibration": {
            "status": "blocked_no_source_confidence_no_full_root_set",
            "required_splits": REQUIRED_SPLITS,
            "accepted_source_confidence_95_labels": [],
            "new_confidence_gate": False,
            "label_summary": materialized["label_summary"],
            "split_summary": materialized["split_summary"],
        },
        "decision": {
            "accepted_rows_added": 0,
            "target_root_mutated": True,
            "canonical_merge_allowed_now": False,
            "downstream_rerun_allowed_now": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
            "raw_data_committed": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
        },
        "next_action": (
            "Do not run canonical merge or downstream promotion from this R3 intake. "
            "Acquire a direct Crisis mapping or a separate source-owned Crisis-native intraday label source, "
            "and acquire source confidence or an approved calibration rule before promotion."
        ),
    }
    return result


def write_outputs(result: dict[str, Any], materialized: dict[str, Any], verifier: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)

    result_json = OUT / "r3_hf_tsie_native_intraday_intake_v1.json"
    verifier_json = OUT / "r3_hf_tsie_native_intraday_direct_verifier_v1.json"
    report_md = OUT / "r3_hf_tsie_native_intraday_intake_v1.md"
    label_csv = OUT / "r3_hf_tsie_native_intraday_label_summary_v1.csv"
    split_csv = OUT / "r3_hf_tsie_native_intraday_split_summary_v1.csv"
    required_csv = OUT / "r3_hf_tsie_native_intraday_required_files_v1.csv"
    assertions = CHECKS / "r3_hf_tsie_native_intraday_intake_v1_assertions.out"

    write_json(result_json, result)
    write_json(verifier_json, verifier)
    write_csv(label_csv, materialized["label_summary"], list(materialized["label_summary"][0].keys()))
    write_csv(split_csv, materialized["split_summary"], list(materialized["split_summary"][0].keys()))
    write_csv(required_csv, materialized["required_files"], list(materialized["required_files"][0].keys()))

    lines = [
        "# R3 HF TSIE Native Intraday Intake v1",
        "",
        f"- Run ID: `{RUN_ID}`",
        f"- Gate result: `{result['gate_result']}`",
        f"- Source: `{SOURCE_ID}` commit `{SOURCE_COMMIT}`, license `{SOURCE_LICENSE}`.",
        f"- Raw parquet downloaded to `/tmp`: `{result['raw_download']['raw_exists']}`; SHA-256 `{result['raw_download']['raw_sha256']}`.",
        f"- Target root materialized: `{TARGET_ROOT}`.",
        f"- Verifier status: `{verifier['status']}`.",
        f"- Rows materialized: `{result['materialization']['row_count']}` from `{result['materialization']['raw_rows_seen']}` raw rows.",
        f"- MainRegimeV2 labels present: `{result['materialization']['mapped_main_regime_v2_counts']}`.",
        f"- Missing MainRegimeV2 labels: `{result['materialization']['missing_main_regime_v2_labels']}`.",
        f"- Timeframes: `{result['materialization']['timeframe_counts']}`.",
        f"- Strict sub-hour interval present: `{str(result['materialization']['strict_subhour_interval_present']).lower()}`; native intraday interval present: `{str(result['materialization']['native_intraday_interval_present']).lower()}`.",
        f"- Source confidence available: `{str(result['materialization']['source_confidence_available']).lower()}`.",
        "",
        "## Boundary",
        "",
        "The public TSIE labels are fail-closed mapped only where the source taxonomy is directional or sideways. `BEAR TRAP` and `BULL TRAP` are abstained, `Crisis` has no direct mapping, and no source confidence field exists. The source contains hourly and 4-hour native intraday rows plus daily rows; daily rows are excluded from this R3 intake, and strict sub-hour rows are absent.",
        "",
        "## Decision",
        "",
        "- Accepted rows added: `0`.",
        "- Canonical merge allowed now: `false`.",
        "- Downstream rerun allowed now: `false`.",
        "- Strict full objective: `false`.",
        "- Trade usable: `false`.",
        "- `update_goal=false`.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{repo_rel(result_json)}`",
        f"- Direct verifier JSON: `{repo_rel(verifier_json)}`",
        f"- Label summary CSV: `{repo_rel(label_csv)}`",
        f"- Split summary CSV: `{repo_rel(split_csv)}`",
        f"- Required files CSV: `{repo_rel(required_csv)}`",
        f"- Target rows: `{TARGET_ROOT / ROWS_FILE}`",
        f"- Target provenance: `{TARGET_ROOT / PROVENANCE_FILE}`",
        f"- Assertions: `{repo_rel(assertions)}`",
    ]
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"gate_result={result['gate_result']}",
        "raw_data_downloaded=true",
        "target_root_mutated=true",
        "target_required_files_present=true",
        f"mapped_rows={result['materialization']['row_count']}",
        "accepted_label_count=0",
        "labels_present=" + ",".join(verifier["labels_present"]),
        "missing_labels=" + ",".join(verifier["missing_labels"]),
        f"source_confidence_available={str(verifier['source_confidence_available']).lower()}",
        f"strict_subhour_interval_present={str(verifier['strict_subhour_interval_present']).lower()}",
        "canonical_merge_allowed_now=false",
        "downstream_rerun_allowed_now=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    assertions.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)

    board_hash = sha256_file(BOARD)
    fetch_text(SOURCE_API, "hf_api_dataset.json")
    fetch_text(SOURCE_INFO, "hf_datasets_server_info.json")
    fetch_text(SOURCE_FIRST_ROWS, "hf_datasets_server_first_rows.json")
    fetch_text(SOURCE_README, "hf_readme.md")

    download = ensure_raw_source()
    if not download["raw_exists"]:
        raise FileNotFoundError(f"raw source download failed: {RAW_PATH}")

    materialized = materialize_rows()
    verifier = direct_verifier(materialized)
    result = build_report(
        download=download,
        materialized=materialized,
        verifier=verifier,
        board_hash=board_hash,
    )
    write_outputs(result, materialized, verifier)

    print(
        json.dumps(
            {
                "ok": True,
                "run_id": RUN_ID,
                "gate_result": result["gate_result"],
                "target_root": str(TARGET_ROOT),
                "row_count": result["materialization"]["row_count"],
                "missing_labels": result["materialization"]["missing_main_regime_v2_labels"],
                "canonical_merge_allowed_now": False,
                "downstream_rerun_allowed_now": False,
                "update_goal": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
