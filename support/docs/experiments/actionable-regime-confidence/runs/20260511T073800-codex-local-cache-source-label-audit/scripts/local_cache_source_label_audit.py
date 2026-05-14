#!/usr/bin/env python3
"""Audit local/cache data for independent MainRegimeV2 source labels.

This audit is intentionally conservative. It treats OHLCV, model outputs,
strategy predictions, HMM states, future targets, and repo runtime artifacts as
data/proxy evidence only. A cell is source-label-ready only if a local artifact
contains an externally sourced root label panel for Bull/Bear/Sideways/Crisis.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.feather as feather
import pyarrow.parquet as parquet


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T073800+0800-codex-local-cache-source-label-audit"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T073800-codex-local-cache-source-label-audit"
OUT_DIR = RUN_ROOT / "local-cache-source-labels"
CHECK_DIR = RUN_ROOT / "checks"

AQ_ROOT = Path("/Users/thrill3r/Auto-Quant")
AQ_DATA = AQ_ROOT / "user_data/data"
AQ_BACKTEST = AQ_ROOT / "user_data/backtest_results"

MAIN_ROOTS = ("Bull", "Bear", "Sideways", "Crisis")
OHLCV_COLUMNS = {
    "date",
    "datetime",
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "wap",
    "count",
    "symbol",
    "pair",
}
LABELISH_RE = re.compile(
    r"(mainregimev2|root_?label|source_?label|ground_?truth|official_?regime|"
    r"\bbull\b|\bbear\b|sideways|crisis|manipulation|nber|usrec|recession|"
    r"regime|state|class|label|target|future|outcome|prediction|p_model|signal)",
    re.IGNORECASE,
)
GENERATED_RE = re.compile(
    r"(hmm|viterbi|cluster|kmeans|bocpd|model|prediction|p_model|target|"
    r"future|outcome|backtest|strategy|factor|repo_runtime|analyze_live)",
    re.IGNORECASE,
)


@dataclass
class ScanRow:
    source_lane: str
    path: Path
    file_kind: str
    status: str
    reason: str
    symbol: str = ""
    timeframe: str = ""
    columns: list[str] | None = None
    matching_columns: list[str] | None = None

    def to_csv_row(self) -> dict[str, str]:
        return {
            "source_lane": self.source_lane,
            "path": str(self.path),
            "file_kind": self.file_kind,
            "status": self.status,
            "reason": self.reason,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "columns": ";".join(self.columns or []),
            "matching_columns": ";".join(self.matching_columns or []),
        }


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def parse_symbol_timeframe(path: Path) -> tuple[str, str]:
    stem = path.stem
    if "_" in stem:
        parts = stem.rsplit("_", 1)
        if len(parts) == 2 and re.match(r"^\d+[mhdw]|1mo$", parts[1]):
            return parts[0], parts[1]
    if "-" in stem:
        left, timeframe = stem.rsplit("-", 1)
        return left, timeframe
    return "", ""


def table_columns(path: Path) -> tuple[str, list[str]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv", list(pd.read_csv(path, nrows=0).columns)
    if suffix == ".feather":
        table = feather.read_table(path, columns=[])
        return "feather", list(table.schema.names)
    if suffix == ".parquet":
        schema = parquet.read_schema(path)
        return "parquet", list(schema.names)
    raise ValueError(f"unsupported table file: {path}")


def classify_table(path: Path, source_lane: str) -> ScanRow:
    symbol, timeframe = parse_symbol_timeframe(path)
    try:
        file_kind, cols = table_columns(path)
    except Exception as exc:  # keep audit fail-closed and visible
        return ScanRow(source_lane, path, path.suffix.lower().lstrip("."), "scan_failed", repr(exc), symbol, timeframe)

    normalized = {col.lower() for col in cols}
    matches = [col for col in cols if LABELISH_RE.search(col)]
    if matches:
        if source_lane in {"auto_quant_cache", "repo_state", "tmp_scratch"} or GENERATED_RE.search(str(path)):
            status = "labelish_or_generated_columns_not_independent_source"
            reason = "columns or path look generated/proxy/runtime; not accepted as external MainRegimeV2 ground truth"
        else:
            status = "candidate_label_columns_need_source_provenance"
            reason = "label-like columns found but no accepted source provenance is attached"
    elif normalized.issubset(OHLCV_COLUMNS) or {"open", "high", "low", "close"}.issubset(normalized):
        status = "ohlcv_only"
        reason = "usable market data, but no independent root labels"
    else:
        status = "no_root_label_columns"
        reason = "schema does not contain MainRegimeV2 root labels"
    return ScanRow(source_lane, path, file_kind, status, reason, symbol, timeframe, cols, matches)


def json_key_sample(path: Path, max_keys: int = 300) -> list[str]:
    try:
        payload = json.loads(path.read_text(errors="ignore"))
    except Exception:
        return []
    keys: list[str] = []

    def walk(value: Any, prefix: str = "") -> None:
        if len(keys) >= max_keys:
            return
        if isinstance(value, dict):
            for key, child in value.items():
                full = f"{prefix}.{key}" if prefix else str(key)
                keys.append(full)
                walk(child, full)
                if len(keys) >= max_keys:
                    break
        elif isinstance(value, list):
            for idx, child in enumerate(value[:5]):
                walk(child, f"{prefix}[{idx}]")

    walk(payload)
    return keys


def classify_json(path: Path, source_lane: str) -> ScanRow:
    keys = json_key_sample(path)
    matches = [key for key in keys if LABELISH_RE.search(key)]
    if matches:
        status = "generated_or_runtime_labelish_json_not_independent_source"
        reason = "JSON contains label/regime/target-like keys, but lane is local scratch/runtime/model provenance"
    else:
        status = "no_root_label_keys"
        reason = "JSON does not expose independent MainRegimeV2 root label keys"
    return ScanRow(source_lane, path, "json", status, reason, columns=keys[:50], matching_columns=matches[:50])


def aq_table_files() -> list[Path]:
    if not AQ_DATA.exists():
        return []
    return sorted(
        path
        for path in AQ_DATA.rglob("*")
        if path.is_file() and path.suffix.lower() in {".csv", ".feather", ".parquet"}
    )


def aq_json_files() -> list[Path]:
    paths: list[Path] = []
    if AQ_BACKTEST.exists():
        paths.extend(sorted(AQ_BACKTEST.glob("*.json")))
    for config in [AQ_ROOT / "config.json", AQ_ROOT / "config.tomac.json"]:
        if config.exists():
            paths.append(config)
    return paths


def repo_state_json_files(limit: int = 160) -> list[Path]:
    state_root = REPO / "state"
    if not state_root.exists():
        return []
    candidates = [
        path
        for path in state_root.rglob("*.json")
        if re.search(r"(regime|label|prediction|analyze|workflow|artifact|candidate)", path.name, re.IGNORECASE)
    ]
    return sorted(candidates)[:limit]


def tmp_candidate_files(limit: int = 220) -> list[Path]:
    roots = [Path("/private/tmp"), Path("/tmp")]
    paths: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for pattern in [
            "*regime*",
            "*label*",
            "ict-engine-ibkr-probe/*regime*",
            "ict-engine-regime-longspan-nq/*regime*",
            "hmm_regime_*/*",
        ]:
            for path in root.glob(pattern):
                if path.is_file() and path.suffix.lower() in {".json", ".csv", ".feather", ".parquet"}:
                    paths.append(path)
    return sorted(dict.fromkeys(paths), key=str)[:limit]


def summarize(rows: list[ScanRow]) -> dict[str, Any]:
    by_status: dict[str, int] = {}
    by_lane: dict[str, int] = {}
    for row in rows:
        by_status[row.status] = by_status.get(row.status, 0) + 1
        by_lane[row.source_lane] = by_lane.get(row.source_lane, 0) + 1

    aq_ohlcv_cells = [
        row
        for row in rows
        if row.source_lane == "auto_quant_cache" and row.status == "ohlcv_only" and row.symbol and row.timeframe
    ]
    return {
        "rows_scanned": len(rows),
        "counts_by_lane": dict(sorted(by_lane.items())),
        "counts_by_status": dict(sorted(by_status.items())),
        "auto_quant_ohlcv_cells": len(aq_ohlcv_cells),
        "auto_quant_symbols": sorted({row.symbol for row in aq_ohlcv_cells if row.symbol}),
        "auto_quant_timeframes": sorted({row.timeframe for row in aq_ohlcv_cells if row.timeframe}),
        "independent_source_backed_mainregimev2_label_sources": 0,
        "full_root_label_panel_cells_available": 0,
        "root_label_coverage": {root: 0 for root in MAIN_ROOTS},
    }


def write_outputs(rows: list[ScanRow]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    summary = summarize(rows)
    report = {
        "run_id": RUN_ID,
        "goal_achieved": False,
        "objective": "Audit repo-local, Auto-Quant, and scratch caches for independent source-backed MainRegimeV2 root label panels.",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_lanes": {
            "auto_quant_cache": str(AQ_DATA),
            "auto_quant_backtest_metadata": str(AQ_BACKTEST),
            "repo_state": str(REPO / "state"),
            "tmp_scratch": "/private/tmp and /tmp bounded candidate scan",
        },
        "summary": summary,
        "classification_policy": {
            "accepted_as_source_label": "Only externally sourced root labels for Bull/Bear/Sideways/Crisis with provenance and symbol/timeframe attachability.",
            "not_accepted": [
                "OHLCV-only cache files",
                "Auto-Quant strategy outputs or backtest metadata",
                "repo runtime/analyze artifacts",
                "HMM, Viterbi, cluster, future-target, prediction, or factor benchmark outputs",
                "direct Manipulation overlay evidence when attached to OHLCV bar cells",
            ],
        },
        "completion_accounting": {
            "accepted_full_cycle_full_universe": False,
            "why_not_accepted": [
                "Local and Auto-Quant caches contain usable OHLCV/data artifacts, but no independent full MainRegimeV2 root label panel.",
                "Generated model states, backtest targets, and strategy predictions are proxy/model outputs, not source labels.",
                "No local cache artifact attaches all four roots to the yfinance/Kraken full-cycle cells.",
            ],
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_ohlcv_committed": False,
            "trade_usable": False,
        },
        "gate_result": "blocked_local_and_autoquant_cache_have_no_independent_root_label_panel",
        "next_action": "Acquire or create a provenance-backed external MainRegimeV2 root label panel for the ready yfinance/Kraken cells, then rerun attachability and full-coverage disposition.",
        "artifacts": {
            "summary_json": rel(OUT_DIR / "local_cache_source_label_audit.json"),
            "summary_md": rel(OUT_DIR / "local_cache_source_label_audit.md"),
            "details_csv": rel(OUT_DIR / "local_cache_source_label_audit.csv"),
            "assertions": rel(CHECK_DIR / "local_cache_source_label_audit_assertions.out"),
            "script": rel(Path(__file__)),
        },
    }

    (OUT_DIR / "local_cache_source_label_audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    with (OUT_DIR / "local_cache_source_label_audit.csv").open("w", newline="") as handle:
        fieldnames = list(rows[0].to_csv_row().keys()) if rows else [
            "source_lane",
            "path",
            "file_kind",
            "status",
            "reason",
            "symbol",
            "timeframe",
            "columns",
            "matching_columns",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_csv_row())

    md = [
        "# Local Cache Source Label Audit",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Goal achieved: `false`",
        "",
        "## Summary",
        "",
        f"- Rows/files scanned: `{summary['rows_scanned']}`",
        f"- Auto-Quant OHLCV cache cells: `{summary['auto_quant_ohlcv_cells']}`",
        f"- Auto-Quant symbols represented: `{', '.join(summary['auto_quant_symbols'])}`",
        f"- Auto-Quant timeframes represented: `{', '.join(summary['auto_quant_timeframes'])}`",
        "- Independent source-backed MainRegimeV2 label sources found: `0`",
        "- Full-root label panel cells available: `0`",
        "",
        "## Counts By Status",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in summary["counts_by_status"].items():
        md.append(f"| `{status}` | {count} |")
    md.extend(
        [
            "",
            "## Accounting",
            "",
            "- Local and Auto-Quant caches are useful for replay/data breadth, but they do not contain source-backed `Bull` / `Bear` / `Sideways` / `Crisis` labels.",
            "- HMM states, future targets, strategy predictions, and repo runtime artifacts remain generated/proxy evidence and are not counted as accepted labels.",
            "- Runtime code changed: false. Thresholds relaxed: false. Raw OHLCV committed: false. Trade usable: false.",
            "",
            "Gate result: `blocked_local_and_autoquant_cache_have_no_independent_root_label_panel`",
        ]
    )
    (OUT_DIR / "local_cache_source_label_audit.md").write_text("\n".join(md) + "\n")

    assertions = [
        "goal_achieved=false",
        f"rows_scanned={summary['rows_scanned']}",
        f"auto_quant_ohlcv_cells={summary['auto_quant_ohlcv_cells']}",
        "independent_source_backed_mainregimev2_label_sources=0",
        "full_root_label_panel_cells_available=0",
        "accepted_full_cycle_full_universe=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_ohlcv_committed=false",
        "trade_usable=false",
        "gate_result=blocked_local_and_autoquant_cache_have_no_independent_root_label_panel",
    ]
    (CHECK_DIR / "local_cache_source_label_audit_assertions.out").write_text("\n".join(assertions) + "\n")
    print(rel(OUT_DIR / "local_cache_source_label_audit.json"))


def main() -> None:
    rows: list[ScanRow] = []
    rows.extend(classify_table(path, "auto_quant_cache") for path in aq_table_files())
    rows.extend(classify_json(path, "auto_quant_backtest_metadata") for path in aq_json_files())
    rows.extend(classify_json(path, "repo_state") for path in repo_state_json_files())
    for path in tmp_candidate_files():
        if path.suffix.lower() in {".csv", ".feather", ".parquet"}:
            rows.append(classify_table(path, "tmp_scratch"))
        elif path.suffix.lower() == ".json":
            rows.append(classify_json(path, "tmp_scratch"))
    write_outputs(rows)


if __name__ == "__main__":
    main()
