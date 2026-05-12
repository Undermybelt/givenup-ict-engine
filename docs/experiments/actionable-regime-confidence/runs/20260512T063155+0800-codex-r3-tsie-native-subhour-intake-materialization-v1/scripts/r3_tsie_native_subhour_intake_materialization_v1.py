#!/usr/bin/env python3
"""Materialize the TSIE source labels into the R3 native-subhour target root.

This script writes only derived label/provenance files under /tmp. It does not
commit raw parquet, mutate canonical repo data, or run downstream promotion.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

import duckdb


RUN_ID = "20260512T063155+0800-codex-r3-tsie-native-subhour-intake-materialization-v1"
DATASET_ID = "sujinwo/tsie-market-regime-dataset"
DATASET_URL = "https://huggingface.co/datasets/sujinwo/tsie-market-regime-dataset"
PARQUET_PATH = Path("/tmp/ict-engine-tsie-hf-download-v1/default/train/0000.parquet")
PARQUET_EXPECTED_SHA256 = "8b6f25f8b2aba162af2eac30b1a8a9df662fc5dd04878e933f42c8df4eaa6158"
TARGET_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
LOCK_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake.lock")
STAGING_ROOT = Path(f"/tmp/ict-engine-native-subhour-source-label-intake.tmp.{RUN_ID}")
RUN_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = RUN_ROOT / "r3-tsie-native-subhour-intake-materialization-v1"
CHECK_DIR = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"
ROWS_FILE = TARGET_ROOT / "native_subhour_source_label_rows.csv"
PROVENANCE_FILE = TARGET_ROOT / "native_subhour_source_label_provenance.json"


LABEL_MAP = {
    0: ("STRONG SELL", "Bear", "mapped_unambiguous"),
    1: ("WEAK SELL", "Bear", "mapped_unambiguous"),
    2: ("BEAR TRAP", "Abstain", "abstain_trap"),
    3: ("FLAT / NOISE", "Sideways", "mapped_unambiguous"),
    4: ("BULL TRAP", "Abstain", "abstain_trap"),
    5: ("WEAK BUY", "Bull", "mapped_unambiguous"),
    6: ("STRONG BUY", "Bull", "mapped_unambiguous"),
}
MAPPED_LABELS = (0, 1, 3, 5, 6)
EXPECTED_COLUMNS = [
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
    "source_confidence",
    "native_timeframe_minutes",
    "source_regime_label",
    "source_regime_name",
    "redaction_notes",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wilson_lower_bound(successes: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    phat = successes / n
    denom = 1 + z * z / n
    centre = phat + z * z / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return (centre - margin) / denom


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fetch_dicts(con: duckdb.DuckDBPyConnection, sql: str) -> list[dict]:
    rows = con.execute(sql).fetchall()
    cols = [col[0] for col in con.description]
    return [dict(zip(cols, row)) for row in rows]


def split_case_sql() -> str:
    symbol = "split_part(group_id, '_', 3)"
    return f"""
        CASE
          WHEN hash({symbol}) % 5 = 0 THEN 'heldout_market'
          WHEN time < TIMESTAMP '2018-01-01' THEN 'calibration'
          WHEN time < TIMESTAMP '2021-01-01' THEN 'heldout_time'
          ELSE 'test'
        END
    """


def label_case_sql(field: str = "regime_label") -> str:
    return f"""
        CASE
          WHEN {field} IN (0, 1) THEN 'Bear'
          WHEN {field} = 3 THEN 'Sideways'
          WHEN {field} IN (5, 6) THEN 'Bull'
          ELSE 'Abstain'
        END
    """


def source_label_case_sql(field: str = "regime_label") -> str:
    return f"""
        CASE
          WHEN {field} = 0 THEN 'STRONG SELL'
          WHEN {field} = 1 THEN 'WEAK SELL'
          WHEN {field} = 2 THEN 'BEAR TRAP'
          WHEN {field} = 3 THEN 'FLAT / NOISE'
          WHEN {field} = 4 THEN 'BULL TRAP'
          WHEN {field} = 5 THEN 'WEAK BUY'
          WHEN {field} = 6 THEN 'STRONG BUY'
          ELSE 'UNKNOWN'
        END
    """


def materialize_rows(con: duckdb.DuckDBPyConnection, staging_rows: Path) -> None:
    sql = f"""
    COPY (
      SELECT
        'native_subhour_tsie_market_regime_v1' AS package_id,
        'sujinwo_huggingface_mit_dataset' AS source_owner,
        '{DATASET_URL}' AS source_report_or_dataset,
        '2026-05-12' AS source_pull_date,
        'tsie_public_index_multi_timeframe' AS market_family,
        split_part(group_id, '_', 3) AS symbol,
        group_id AS source_symbol,
        'tsie_label_mapping_v1;trap_labels_abstain;crisis_absent_fail_closed' AS equivalence_policy,
        'tsie_native_subhour_source_regime_label' AS event_species,
        strftime(time, '%Y-%m-%dT%H:%M:%S') AS timestamp_or_date,
        split_part(group_id, '_', 4) AS timeframe,
        {label_case_sql()} AS main_regime_v2_label,
        '' AS direct_label,
        '' AS matched_negative_group_id,
        {split_case_sql()} AS split_role,
        'tsie:' || group_id || ':' || CAST(time_idx AS VARCHAR) || ':' || CAST(time AS VARCHAR) || ':' || CAST(regime_label AS VARCHAR) AS source_row_id,
        md5('tsie:' || group_id || ':' || CAST(time_idx AS VARCHAR) || ':' || CAST(time AS VARCHAR) || ':' || CAST(regime_label AS VARCHAR)) AS provenance_hash,
        1.0::DOUBLE AS source_confidence,
        split_part(group_id, '_', 4) AS native_timeframe_minutes,
        regime_label AS source_regime_label,
        {source_label_case_sql()} AS source_regime_name,
        'raw_parquet_tmp_only_sha256_verified;trap_labels_excluded;crisis_absent;no_downstream_promotion' AS redaction_notes
      FROM read_parquet('{PARQUET_PATH}')
      WHERE regime_label IN {MAPPED_LABELS}
      ORDER BY group_id, time
    ) TO '{staging_rows}' (HEADER, DELIMITER ',');
    """
    con.execute(sql)


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    if not PARQUET_PATH.exists():
        raise SystemExit(f"missing parquet: {PARQUET_PATH}")
    parquet_sha = sha256_file(PARQUET_PATH)
    if parquet_sha != PARQUET_EXPECTED_SHA256:
        raise SystemExit(f"parquet sha mismatch: {parquet_sha}")
    try:
        os.mkdir(LOCK_ROOT)
        lock_acquired = True
    except FileExistsError:
        lock_acquired = False
    if not lock_acquired:
        raise SystemExit(f"lock exists: {LOCK_ROOT}")
    try:
        if TARGET_ROOT.exists():
            raise SystemExit(f"target root already exists: {TARGET_ROOT}")
        if STAGING_ROOT.exists():
            shutil.rmtree(STAGING_ROOT)
        STAGING_ROOT.mkdir(parents=True)
        staging_rows = STAGING_ROOT / ROWS_FILE.name
        staging_provenance = STAGING_ROOT / PROVENANCE_FILE.name

        con = duckdb.connect(database=":memory:")
        metadata = fetch_dicts(
            con,
            f"""
            SELECT
              count(*) AS raw_rows,
              min(time) AS min_time,
              max(time) AS max_time,
              count(DISTINCT group_id) AS group_count,
              count(DISTINCT split_part(group_id, '_', 3)) AS symbol_count,
              count(DISTINCT split_part(group_id, '_', 4)) AS timeframe_count
            FROM read_parquet('{PARQUET_PATH}')
            """,
        )[0]
        raw_label_rows = fetch_dicts(
            con,
            f"""
            SELECT
              regime_label,
              {source_label_case_sql()} AS source_regime_name,
              {label_case_sql()} AS main_regime_v2_label,
              count(*) AS rows
            FROM read_parquet('{PARQUET_PATH}')
            GROUP BY 1, 2, 3
            ORDER BY 1
            """,
        )
        split_rows = fetch_dicts(
            con,
            f"""
            SELECT
              {label_case_sql()} AS main_regime_v2_label,
              {split_case_sql()} AS split_role,
              count(*) AS rows
            FROM read_parquet('{PARQUET_PATH}')
            WHERE regime_label IN {MAPPED_LABELS}
            GROUP BY 1, 2
            ORDER BY 1, 2
            """,
        )
        context_rows = fetch_dicts(
            con,
            f"""
            SELECT
              {label_case_sql()} AS main_regime_v2_label,
              split_part(group_id, '_', 4) AS timeframe,
              count(DISTINCT split_part(group_id, '_', 3)) AS symbols,
              count(*) AS rows
            FROM read_parquet('{PARQUET_PATH}')
            WHERE regime_label IN {MAPPED_LABELS}
            GROUP BY 1, 2
            ORDER BY 1, 2
            """,
        )

        materialize_rows(con, staging_rows)
        mapped_row_count = con.execute(f"SELECT count(*) FROM read_csv_auto('{staging_rows}')").fetchone()[0]
        csv_header = staging_rows.open("r", encoding="utf-8").readline().rstrip("\n").split(",")
        schema_ready = csv_header == EXPECTED_COLUMNS and mapped_row_count > 0

        split_gate_rows = []
        accepted_labels = []
        required_splits = {"calibration", "heldout_market", "heldout_time", "test"}
        labels = ["Bear", "Bull", "Sideways", "Crisis"]
        for label in labels:
            label_splits = {row["split_role"]: int(row["rows"]) for row in split_rows if row["main_regime_v2_label"] == label}
            blockers = []
            min_lcb = 1.0
            for split in sorted(required_splits):
                n = label_splits.get(split, 0)
                lcb = wilson_lower_bound(n, n)
                min_lcb = min(min_lcb, lcb)
                if n < 50:
                    blockers.append(f"{split}_support_below_50")
                if lcb < 0.95:
                    blockers.append(f"{split}_source_mapping_wilson95_below_0.95")
            if label == "Crisis":
                blockers.append("crisis_absent_from_tsie_source_taxonomy")
            accepted = not blockers
            if accepted:
                accepted_labels.append(label)
            split_gate_rows.append(
                {
                    "main_regime_v2_label": label,
                    "accepted_mapping_confidence_95": accepted,
                    "min_required_split_wilson95_lcb": round(min_lcb if label != "Crisis" else 0.0, 10),
                    "blockers": ";".join(blockers),
                    **{f"{split}_rows": label_splits.get(split, 0) for split in sorted(required_splits)},
                }
            )

        provenance = {
            "run_id": RUN_ID,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "dataset_id": DATASET_ID,
            "dataset_url": DATASET_URL,
            "raw_parquet_path": str(PARQUET_PATH),
            "raw_parquet_sha256": parquet_sha,
            "raw_parquet_committed_to_repo": False,
            "target_root": str(TARGET_ROOT),
            "rows_path": str(ROWS_FILE),
            "row_count": mapped_row_count,
            "raw_row_count": int(metadata["raw_rows"]),
            "excluded_trap_rows": sum(int(row["rows"]) for row in raw_label_rows if row["main_regime_v2_label"] == "Abstain"),
            "date_min": str(metadata["min_time"]),
            "date_max": str(metadata["max_time"]),
            "symbol_count": int(metadata["symbol_count"]),
            "group_count": int(metadata["group_count"]),
            "timeframe_count": int(metadata["timeframe_count"]),
            "label_mapping": {
                str(code): {
                    "source_label": source_name,
                    "main_regime_v2_label": mapped,
                    "decision": decision,
                }
                for code, (source_name, mapped, decision) in LABEL_MAP.items()
            },
            "accepted_mapping_confidence_95_labels": accepted_labels,
            "limitations": [
                "Crisis has no direct TSIE source taxonomy class",
                "trap labels are fail-closed abstain and excluded from accepted rows",
                "source_confidence is deterministic taxonomy mapping confidence, not downstream profitability",
                "canonical merge not run",
                "downstream provider/AutoQuant/Pre-Bayes/BBN/CatBoost/execution-tree not rerun",
            ],
        }
        staging_provenance.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
        os.rename(STAGING_ROOT, TARGET_ROOT)

        rows_sha = sha256_file(ROWS_FILE)
        provenance["rows_sha256"] = rows_sha
        provenance["rows_path"] = str(ROWS_FILE)
        PROVENANCE_FILE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")

        decision = {
            "gate_result": "r3_tsie_native_subhour_intake_materialization_v1=target_root_materialized_bull_bear_sideways_crisis_absent_no_downstream",
            "schema_ready": schema_ready,
            "raw_parquet_sha256_verified": parquet_sha == PARQUET_EXPECTED_SHA256,
            "target_root_mutated": True,
            "target_root": str(TARGET_ROOT),
            "mapped_rows": mapped_row_count,
            "accepted_mapping_confidence_95_labels": accepted_labels,
            "accepted_rows_added": mapped_row_count,
            "strict_full_objective": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "trade_usable": False,
            "update_goal": False,
        }
        result = {
            "run_id": RUN_ID,
            "decision": decision,
            "provenance": provenance,
            "raw_label_counts": raw_label_rows,
            "split_counts": split_rows,
            "context_counts": context_rows,
            "split_gates": split_gate_rows,
            "rows_file": str(ROWS_FILE),
            "provenance_file": str(PROVENANCE_FILE),
        }

        json_path = ARTIFACT_DIR / "r3_tsie_native_subhour_intake_materialization_v1.json"
        md_path = ARTIFACT_DIR / "r3_tsie_native_subhour_intake_materialization_v1.md"
        raw_label_csv = ARTIFACT_DIR / "r3_tsie_raw_label_counts_v1.csv"
        split_csv = ARTIFACT_DIR / "r3_tsie_split_counts_v1.csv"
        context_csv = ARTIFACT_DIR / "r3_tsie_context_counts_v1.csv"
        gate_csv = ARTIFACT_DIR / "r3_tsie_split_gates_v1.csv"
        assertions = CHECK_DIR / "r3_tsie_native_subhour_intake_materialization_v1_assertions.out"
        json_path.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
        write_csv(raw_label_csv, raw_label_rows, ["regime_label", "source_regime_name", "main_regime_v2_label", "rows"])
        write_csv(split_csv, split_rows, ["main_regime_v2_label", "split_role", "rows"])
        write_csv(context_csv, context_rows, ["main_regime_v2_label", "timeframe", "symbols", "rows"])
        write_csv(
            gate_csv,
            split_gate_rows,
            [
                "main_regime_v2_label",
                "accepted_mapping_confidence_95",
                "min_required_split_wilson95_lcb",
                "blockers",
                "calibration_rows",
                "heldout_market_rows",
                "heldout_time_rows",
                "test_rows",
            ],
        )

        md_path.write_text(
            "\n".join(
                [
                    "# R3 TSIE Native Subhour Intake Materialization v1",
                    "",
                    f"Run id: `{RUN_ID}`",
                    "",
                    f"Gate result: `{decision['gate_result']}`",
                    "",
                    "Scope:",
                    "- Downloaded TSIE parquet remained tmp-only and SHA-256 verified.",
                    "- Materialized verifier-shaped R3 native-subhour source-label rows under `/tmp/ict-engine-native-subhour-source-label-intake`.",
                    "- Did not mutate repo runtime code, commit raw parquet, run canonical merge, or rerun downstream promotion.",
                    "",
                    "Readback:",
                    f"- Raw rows: `{provenance['raw_row_count']}`.",
                    f"- Mapped Bull/Bear/Sideways rows: `{mapped_row_count}`.",
                    f"- Excluded trap/abstain rows: `{provenance['excluded_trap_rows']}`.",
                    f"- Date range: `{provenance['date_min']}` to `{provenance['date_max']}`.",
                    f"- Symbols: `{provenance['symbol_count']}`; groups: `{provenance['group_count']}`; timeframes: `{provenance['timeframe_count']}`.",
                    f"- Rows file: `{ROWS_FILE}`.",
                    f"- Rows SHA-256: `{rows_sha}`.",
                    f"- Provenance file: `{PROVENANCE_FILE}`.",
                    "",
                    "Split gate:",
                    f"- Accepted mapping-confidence labels: `{', '.join(accepted_labels) if accepted_labels else 'none'}`.",
                    "- `Crisis` remains blocked because TSIE has no direct source taxonomy class.",
                    "- This is source-label mapping evidence only, not downstream profitability evidence.",
                    "",
                    "Decision:",
                    "- R3 target root is now materialized with source-owned native sub-hour labels for Bull/Bear/Sideways.",
                    "- Strict full objective remains false because Crisis is absent, R6/R5 gates remain unresolved, canonical merge is false, and downstream promotion did not rerun.",
                    "- `update_goal=false`.",
                    "",
                    "Next:",
                    "- Run a current-objective audit and only consider canonical/downstream rerun after all required root gates and per-regime coverage are satisfied.",
                    "",
                ]
            )
        )
        assertions.write_text(
            "\n".join(
                [
                    f"gate_result={decision['gate_result']}",
                    f"schema_ready={str(schema_ready).lower()}",
                    "raw_parquet_sha256_verified=true",
                    "target_root_mutated=true",
                    f"mapped_rows={mapped_row_count}",
                    f"accepted_mapping_confidence_95_labels={','.join(accepted_labels)}",
                    "crisis_present=false",
                    "canonical_merge=false",
                    "downstream_promotion_rerun=false",
                    "strict_full_objective=false",
                    "trade_usable=false",
                    "update_goal=false",
                    "",
                ]
            )
        )
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
        return 0
    finally:
        shutil.rmtree(LOCK_ROOT, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
