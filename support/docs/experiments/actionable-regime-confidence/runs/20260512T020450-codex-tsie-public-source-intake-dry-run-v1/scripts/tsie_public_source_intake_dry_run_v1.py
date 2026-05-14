#!/usr/bin/env python3
"""Metadata-level TSIE public source-label intake rehearsal.

The full Parquet aggregate path was observed to fail intermittently at the
remote SSL/httpfs boundary in this environment. This fallback records only
metadata, schema, mapping rules, and a non-promoting blocker.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import requests


RUN_ID = "20260512T020450-codex-tsie-public-source-intake-dry-run-v1"
BOARD_HASH_BEFORE_ARTIFACT = "968acaf8c749ed01a0fb14330562408afe12757b173452862ffdf0f9b7af39a8"
DATASET_ID = "sujinwo/tsie-market-regime-dataset"
DATASET_URL = f"https://huggingface.co/datasets/{DATASET_ID}"
DATASET_API_URL = f"https://huggingface.co/api/datasets/{DATASET_ID}"
SIZE_API_URL = "https://datasets-server.huggingface.co/size"
FIRST_ROWS_API_URL = "https://datasets-server.huggingface.co/first-rows"
PARQUET_URL = (
    "https://huggingface.co/datasets/sujinwo/tsie-market-regime-dataset/"
    "resolve/refs%2Fconvert%2Fparquet/default/train/0000.parquet"
)
TMP_ROOT = Path("/tmp/ict-engine-tsie-market-regime-dry-run-v1")
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T020450-codex-tsie-public-source-intake-dry-run-v1"
)
ARTIFACT_DIR = RUN_ROOT / "tsie-public-source-intake-dry-run-v1"
CHECK_DIR = RUN_ROOT / "checks"


LABEL_MAP = {
    0: ("STRONG SELL", "Bear", "mapped_unambiguous", "published high-confidence bearish breakdown"),
    1: ("WEAK SELL", "Bear", "mapped_unambiguous", "published mild bearish movement"),
    2: ("BEAR TRAP", "Abstain", "abstain_trap", "false-breakdown class is directionally ambiguous"),
    3: ("FLAT / NOISE", "Sideways", "mapped_unambiguous", "published sideways / low-volatility class"),
    4: ("BULL TRAP", "Abstain", "abstain_trap", "false-breakout class is directionally ambiguous"),
    5: ("WEAK BUY", "Bull", "mapped_unambiguous", "published mild bullish movement"),
    6: ("STRONG BUY", "Bull", "mapped_unambiguous", "published high-confidence breakout"),
}


def get_json(url: str, params: dict[str, str] | None = None) -> dict[str, Any]:
    response = requests.get(url, params=params, timeout=45)
    response.raise_for_status()
    return response.json()


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def main() -> None:
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    dataset_meta = get_json(DATASET_API_URL)
    size_meta = get_json(SIZE_API_URL, {"dataset": DATASET_ID})
    first_rows = get_json(
        FIRST_ROWS_API_URL,
        {"dataset": DATASET_ID, "config": "default", "split": "train"},
    )
    (TMP_ROOT / "first_rows_sample.json").write_text(
        json.dumps(first_rows.get("rows", [])[:10], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    size_dataset = size_meta.get("size", {}).get("dataset", {})
    size_split = (size_meta.get("size", {}).get("splits") or [{}])[0]
    features = [
        {"name": item.get("name"), "type": item.get("type")}
        for item in first_rows.get("features", [])
    ]
    feature_names = [item["name"] for item in features]
    license_tags = [tag for tag in dataset_meta.get("tags", []) if tag.startswith("license:")]

    label_rows = []
    for code, (published_label, mapping, mapping_status, reason) in LABEL_MAP.items():
        label_rows.append(
            {
                "regime_label": code,
                "published_label": published_label,
                "mapping": mapping,
                "mapping_status": mapping_status,
                "support_status": "not_computed_transport_blocked",
                "reason": reason,
            }
        )

    candidate_rows = [
        {
            "main_regime_v2_candidate": "Bear",
            "source_labels": "0 STRONG SELL; 1 WEAK SELL",
            "support_status": "metadata_mapping_only_transport_blocked",
            "acceptance_status": "blocked_no_aggregate_no_canonical_merge",
        },
        {
            "main_regime_v2_candidate": "Sideways",
            "source_labels": "3 FLAT / NOISE",
            "support_status": "metadata_mapping_only_transport_blocked",
            "acceptance_status": "blocked_no_aggregate_no_canonical_merge",
        },
        {
            "main_regime_v2_candidate": "Bull",
            "source_labels": "5 WEAK BUY; 6 STRONG BUY",
            "support_status": "metadata_mapping_only_transport_blocked",
            "acceptance_status": "blocked_no_aggregate_no_canonical_merge",
        },
        {
            "main_regime_v2_candidate": "Crisis",
            "source_labels": "none",
            "support_status": "no_candidate_class",
            "acceptance_status": "blocked_no_source_label",
        },
    ]

    decision = {
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r3_r5_r6_roots_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "raw_dataset_files_committed": False,
        "external_vendor_contact_sent": False,
        "trade_usable": False,
    }
    gate_result = (
        "tsie_public_source_intake_dry_run_v1="
        "metadata_mapping_transport_blocked_no_acceptance_no_merge"
    )

    result = {
        "run_id": RUN_ID,
        "gate_result": gate_result,
        "board_hash_before_artifact": BOARD_HASH_BEFORE_ARTIFACT,
        "dataset": {
            "id": DATASET_ID,
            "url": DATASET_URL,
            "api_url": DATASET_API_URL,
            "size_api_url": SIZE_API_URL,
            "first_rows_api_url": FIRST_ROWS_API_URL,
            "parquet_url": PARQUET_URL,
            "license_tags": license_tags,
            "private": dataset_meta.get("private"),
            "gated": dataset_meta.get("gated"),
            "disabled": dataset_meta.get("disabled"),
            "tags": dataset_meta.get("tags", []),
        },
        "size": {
            "dataset_num_rows": size_dataset.get("num_rows"),
            "dataset_num_bytes_parquet_files": size_dataset.get("num_bytes_parquet_files"),
            "split_num_rows": size_split.get("num_rows"),
            "split_num_columns": size_split.get("num_columns"),
        },
        "schema": {
            "feature_count": len(feature_names),
            "feature_names": feature_names,
            "features": features,
        },
        "tmp_root": str(TMP_ROOT),
        "tmp_sample_rows": str(TMP_ROOT / "first_rows_sample.json"),
        "label_mapping_rows": label_rows,
        "candidate_rows": candidate_rows,
        "transport_blocker": {
            "status": "full_parquet_aggregate_blocked",
            "observed_error": "DuckDB/httpfs and curl attempts hit SSL connect errors against the Hugging Face/Xet Parquet transport",
            "fallback_used": "Hugging Face dataset metadata, size API, and first-rows API only",
        },
        "acceptance_blockers": [
            "full Parquet aggregate support was not produced in this artifact",
            "dataset labels are rule-based source labels, not accepted MainRegimeV2 rows",
            "trap classes are abstained rather than force-mapped",
            "Crisis has no candidate class",
            "dataset is IDX hourly/session-aware only, not cross-market or cross-timeframe evidence by itself",
            "R6 owner-export/control root is absent and canonical merge remains blocked",
            "no downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion rerun is allowed",
        ],
        **decision,
    }

    json_path = ARTIFACT_DIR / "tsie_public_source_intake_dry_run_v1.json"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    write_csv(
        ARTIFACT_DIR / "tsie_label_mapping_support_v1.csv",
        label_rows,
        ["regime_label", "published_label", "mapping", "mapping_status", "support_status", "reason"],
    )
    write_csv(
        ARTIFACT_DIR / "tsie_candidate_regime_mapping_v1.csv",
        candidate_rows,
        ["main_regime_v2_candidate", "source_labels", "support_status", "acceptance_status"],
    )
    write_csv(
        ARTIFACT_DIR / "tsie_dataset_metadata_v1.csv",
        [
            {
                "dataset_id": DATASET_ID,
                "license_tags": ";".join(license_tags),
                "num_rows": size_dataset.get("num_rows"),
                "num_columns": size_split.get("num_columns"),
                "num_bytes_parquet_files": size_dataset.get("num_bytes_parquet_files"),
                "feature_count": len(feature_names),
                "tmp_sample_rows": str(TMP_ROOT / "first_rows_sample.json"),
            }
        ],
        [
            "dataset_id",
            "license_tags",
            "num_rows",
            "num_columns",
            "num_bytes_parquet_files",
            "feature_count",
            "tmp_sample_rows",
        ],
    )

    md = f"""# TSIE Public Source Intake Dry Run v1

Run id: `{RUN_ID}`
Gate result: `{gate_result}`
Board hash before artifact: `{BOARD_HASH_BEFORE_ARTIFACT}`

Purpose:
- Continue the non-R6 public source-label branch from the latest board next action.
- Rehearse a conservative MainRegimeV2 mapping for `sujinwo/tsie-market-regime-dataset`.
- Record the current transport blocker without mutating shared intake roots or accepting rows.

Source readback:
- Dataset: `{DATASET_ID}`.
- Source URL: `{DATASET_URL}`.
- API URL: `{DATASET_API_URL}`.
- License tags: `{', '.join(license_tags) if license_tags else 'none_observed'}`.
- Hugging Face metadata says private=`{dataset_meta.get('private')}`, gated=`{dataset_meta.get('gated')}`, disabled=`{dataset_meta.get('disabled')}`.
- Size API rows: `{size_dataset.get('num_rows')}`.
- Size API parquet bytes: `{size_dataset.get('num_bytes_parquet_files')}`.
- First-rows API feature count: `{len(feature_names)}`.
- Tmp-only first-row sample path: `{TMP_ROOT / 'first_rows_sample.json'}`.

Mapping rehearsal:
- `0 STRONG SELL` and `1 WEAK SELL` -> `Bear`.
- `3 FLAT / NOISE` -> `Sideways`.
- `5 WEAK BUY` and `6 STRONG BUY` -> `Bull`.
- `2 BEAR TRAP` and `4 BULL TRAP` -> `Abstain`.
- `Crisis` has no source candidate in this dataset.

Transport blocker:
- Full Parquet aggregate support was not produced in this artifact.
- DuckDB/httpfs and curl attempts in this environment hit SSL connect errors against the Hugging Face/Xet Parquet transport.
- This artifact therefore uses only Hugging Face metadata, size, and first-row APIs.

Decision:
- This remains a candidate-only mapping rehearsal, not acceptance evidence.
- It does not unlock R3/R5/R6, canonical merge, or any downstream chain rerun.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Canonical merge allowed: `false`.
- Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree rerun allowed: `false`.
- Strict full objective achieved: `false`.
- `update_goal=false`.

No mutation claims:
- Runtime code changed: `false`.
- Shared intake mutated: `false`.
- R3/R5/R6 roots mutated: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- External vendor/contact request sent: `false`.
- Trade usable: `false`.

Next:
- Preserve the Current Cursor next action for R6.
- If TSIE continues, first fix the Parquet transport/read path into `/tmp`; only then emit verifier-shaped candidate rows for Bull/Bear/Sideways, still blocked from acceptance until R6/canonical merge gates are satisfied.
"""
    (ARTIFACT_DIR / "tsie_public_source_intake_dry_run_v1.md").write_text(md, encoding="utf-8")

    assertions = [
        f"gate_result={gate_result}",
        f"size_api_rows={size_dataset.get('num_rows')}",
        f"feature_count={len(feature_names)}",
        "full_parquet_aggregate_status=blocked",
        "accepted_rows_added=0",
        "canonical_merge_allowed=false",
        "downstream_chain_rerun_allowed=false",
        "update_goal=false",
    ]
    (CHECK_DIR / "tsie_public_source_intake_dry_run_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "run_id": RUN_ID,
        "gate_result": gate_result,
        "json": str(json_path),
        "report": str(ARTIFACT_DIR / "tsie_public_source_intake_dry_run_v1.md"),
        "accepted_rows_added": 0,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
    }, indent=2))


if __name__ == "__main__":
    main()
