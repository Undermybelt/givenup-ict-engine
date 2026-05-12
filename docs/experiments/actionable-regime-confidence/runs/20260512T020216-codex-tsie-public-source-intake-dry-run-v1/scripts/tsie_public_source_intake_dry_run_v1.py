#!/usr/bin/env python3
"""Bounded TSIE public-source intake dry run.

This intentionally uses Hugging Face metadata/row APIs instead of downloading
the full parquet file. The output is a derived source-readiness audit, not an
accepted Board A intake.
"""

from __future__ import annotations

import csv
import json
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests


RUN_ID = "20260512T020216-codex-tsie-public-source-intake-dry-run-v1"
DATASET_ID = "sujinwo/tsie-market-regime-dataset"
CONFIG = "default"
SPLIT = "train"
OFFSETS = [0, 500_000, 2_000_000, 4_000_000, 6_000_000]
PAGE_LENGTH = 100

LABEL_MAP = {
    0: {"source_label": "STRONG SELL", "main_regime_v2": "Bear", "decision": "map"},
    1: {"source_label": "WEAK SELL", "main_regime_v2": "Bear", "decision": "map"},
    2: {"source_label": "BEAR TRAP", "main_regime_v2": "Abstain", "decision": "abstain_trap"},
    3: {"source_label": "FLAT / NOISE", "main_regime_v2": "Sideways", "decision": "map"},
    4: {"source_label": "BULL TRAP", "main_regime_v2": "Abstain", "decision": "abstain_trap"},
    5: {"source_label": "WEAK BUY", "main_regime_v2": "Bull", "decision": "map"},
    6: {"source_label": "STRONG BUY", "main_regime_v2": "Bull", "decision": "map"},
}


def get_json(url: str, *, retries: int = 2) -> dict:
    response = requests.get(url, timeout=45)
    if response.status_code == 429 and retries > 0:
        time.sleep(15)
        return get_json(url, retries=retries - 1)
    response.raise_for_status()
    return response.json()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[6]


def rel(path: Path) -> str:
    return str(path.relative_to(repo_root()))


def count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for p in path.rglob("*") if p.is_file())


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    root = repo_root()
    run_root = Path(__file__).resolve().parents[1]
    out_dir = run_root / "tsie-public-source-intake-dry-run-v1"
    checks_dir = run_root / "checks"
    out_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    dataset_url = f"https://huggingface.co/datasets/{DATASET_ID}"
    api_url = f"https://huggingface.co/api/datasets/{DATASET_ID}"
    encoded_dataset = quote(DATASET_ID, safe="")
    splits_url = f"https://datasets-server.huggingface.co/splits?dataset={encoded_dataset}"
    parquet_url = f"https://datasets-server.huggingface.co/parquet?dataset={encoded_dataset}"
    size_url = f"https://datasets-server.huggingface.co/size?dataset={encoded_dataset}"

    dataset_meta = get_json(api_url)
    splits = get_json(splits_url)
    parquet = get_json(parquet_url)
    size = get_json(size_url)

    rows = []
    offset_status = []
    for offset in OFFSETS:
        row_url = (
            "https://datasets-server.huggingface.co/rows?"
            f"dataset={encoded_dataset}&config={CONFIG}&split={SPLIT}&offset={offset}&length={PAGE_LENGTH}"
        )
        try:
            payload = get_json(row_url, retries=1)
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "unknown"
            offset_status.append(
                {
                    "offset": offset,
                    "requested": PAGE_LENGTH,
                    "returned": 0,
                    "partial": True,
                    "num_rows_total": None,
                    "error": f"http_{status}",
                }
            )
            continue
        page_rows = payload.get("rows", [])
        offset_status.append(
            {
                "offset": offset,
                "requested": PAGE_LENGTH,
                "returned": len(page_rows),
                "partial": payload.get("partial", False),
                "num_rows_total": payload.get("num_rows_total"),
                "error": "",
            }
        )
        for item in page_rows:
            row = item["row"]
            label = int(row["regime_label"])
            mapping = LABEL_MAP.get(label, {"source_label": "UNKNOWN", "main_regime_v2": "Unknown", "decision": "reject_unknown"})
            timestamp = str(row.get("time", ""))
            year = timestamp[:4] if len(timestamp) >= 4 else "unknown"
            group_id = str(row.get("group_id", "unknown"))
            rows.append(
                {
                    "row_idx": item.get("row_idx"),
                    "group_id": group_id,
                    "symbol": group_id.split("_")[2] if len(group_id.split("_")) >= 3 else "unknown",
                    "timeframe_hint": group_id.split("_")[-1] if "_" in group_id else "unknown",
                    "year": year,
                    "regime_label": label,
                    "source_label": mapping["source_label"],
                    "main_regime_v2": mapping["main_regime_v2"],
                    "decision": mapping["decision"],
                }
            )

    label_counts = Counter(row["source_label"] for row in rows)
    regime_counts = Counter(row["main_regime_v2"] for row in rows)
    decision_counts = Counter(row["decision"] for row in rows)
    year_counts = Counter(row["year"] for row in rows)
    unique_symbols = sorted({row["symbol"] for row in rows})
    unique_timeframes = sorted({row["timeframe_hint"] for row in rows})

    source_roots = {
        "r6_owner_export": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        "r3_native_subhour": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "r5_recency_extension": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "source_label_equivalence": Path("/tmp/ict-engine-source-label-equivalence-intake"),
    }
    root_status = {
        key: {"path": str(path), "present": path.exists(), "file_count": count_files(path)}
        for key, path in source_roots.items()
    }

    license_tags = dataset_meta.get("tags", [])
    license_verified = "license:mit" in license_tags or dataset_meta.get("cardData", {}).get("license") == "mit"
    parquet_files = parquet.get("parquet_files", [])
    parquet_bytes = parquet_files[0].get("size") if parquet_files else None
    total_rows = size.get("size", {}).get("dataset", {}).get("num_rows")

    sampled_rows = len(rows)
    mapped_rows = sum(1 for row in rows if row["decision"] == "map")
    abstain_rows = sum(1 for row in rows if row["decision"].startswith("abstain"))
    mapped_regimes = sorted(regime for regime in regime_counts if regime not in {"Abstain", "Unknown"})
    mapped_regimes_from_contract = sorted(
        {mapping["main_regime_v2"] for mapping in LABEL_MAP.values() if mapping["decision"] == "map"}
    )
    row_api_errors = [row for row in offset_status if row.get("error")]

    result = {
        "run_id": RUN_ID,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "gate_result": "tsie_public_source_intake_dry_run_v1=sample_mapping_ready_no_acceptance_no_canonical_merge",
        "dataset": DATASET_ID,
        "dataset_url": dataset_url,
        "api_url": api_url,
        "license": "mit" if license_verified else dataset_meta.get("cardData", {}).get("license"),
        "license_verified": license_verified,
        "split_status": splits.get("splits", []),
        "parquet_file_size_bytes": parquet_bytes,
        "dataset_total_rows": total_rows,
        "raw_parquet_downloaded": False,
        "raw_data_committed": False,
        "sample_strategy": {"offsets": OFFSETS, "page_length": PAGE_LENGTH},
        "sampled_rows": sampled_rows,
        "unique_symbol_count_in_sample": len(unique_symbols),
        "unique_timeframes_in_sample": unique_timeframes,
        "label_counts": dict(label_counts),
        "main_regime_counts": dict(regime_counts),
        "decision_counts": dict(decision_counts),
        "year_counts": dict(year_counts),
        "row_api_errors": row_api_errors,
        "mapping_decision": {
            "Bear": "STRONG SELL + WEAK SELL",
            "Sideways": "FLAT / NOISE",
            "Bull": "WEAK BUY + STRONG BUY",
            "Abstain": "BEAR TRAP + BULL TRAP",
            "Crisis": "not represented by TSIE label semantics",
        },
        "mapped_rows": mapped_rows,
        "abstain_rows": abstain_rows,
        "mapped_regimes": mapped_regimes,
        "mapped_regimes_from_contract": mapped_regimes_from_contract,
        "root_status": root_status,
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
        "trade_usable": False,
        "blockers": [
            "full parquet not downloaded or calibrated in this dry run",
            "sample is API-offset derived and cannot support 95% acceptance",
            "trap classes require abstain behavior",
            "Crisis regime has no TSIE semantic equivalent",
            "R6 owner-export/control gate remains absent",
            "canonical merge is false",
        ],
    }

    mapping_rows = [
        {"regime_label": label, **mapping}
        for label, mapping in sorted(LABEL_MAP.items())
    ]
    offset_rows = offset_status
    summary_rows = [
        {"kind": "source_label", "name": name, "count": count}
        for name, count in sorted(label_counts.items())
    ] + [
        {"kind": "main_regime_v2", "name": name, "count": count}
        for name, count in sorted(regime_counts.items())
    ] + [
        {"kind": "year", "name": name, "count": count}
        for name, count in sorted(year_counts.items())
    ]

    json_path = out_dir / "tsie_public_source_intake_dry_run_v1.json"
    report_path = out_dir / "tsie_public_source_intake_dry_run_v1.md"
    mapping_path = out_dir / "tsie_label_mapping_v1.csv"
    offsets_path = out_dir / "tsie_offset_sample_status_v1.csv"
    summary_path = out_dir / "tsie_sample_summary_v1.csv"
    assertions_path = checks_dir / "tsie_public_source_intake_dry_run_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_csv(mapping_path, mapping_rows, ["regime_label", "source_label", "main_regime_v2", "decision"])
    write_csv(offsets_path, offset_rows, ["offset", "requested", "returned", "partial", "num_rows_total", "error"])
    write_csv(summary_path, summary_rows, ["kind", "name", "count"])

    report = f"""# TSIE Public Source Intake Dry Run v1

Run id: `{RUN_ID}`
Gate result: `{result['gate_result']}`

Scope:
- Candidate: `{DATASET_ID}`.
- Dataset URL: `{dataset_url}`.
- API-only dry run; full parquet download is explicitly `false`.
- Canonical intake roots were not mutated.

Source facts:
- License verified: `{license_verified}`.
- Total rows from dataset-server size API: `{total_rows}`.
- Parquet size from dataset-server parquet API: `{parquet_bytes}` bytes.
- Local parquet engines available for full read: `false` for pyarrow/duckdb/polars in this environment.

Sample dry run:
- Offsets sampled: `{OFFSETS}` with page length `{PAGE_LENGTH}`.
- Sampled rows: `{sampled_rows}`.
- Unique symbols in sample: `{len(unique_symbols)}`.
- Timeframe hints in sample: `{', '.join(unique_timeframes)}`.
- Source label counts: `{dict(label_counts)}`.
- MainRegimeV2 dry-run counts: `{dict(regime_counts)}`.
- Decision counts: `{dict(decision_counts)}`.
- Year counts: `{dict(year_counts)}`.
- Row API errors: `{row_api_errors}`.

Mapping posture:
- Bear: `STRONG SELL`, `WEAK SELL`.
- Sideways: `FLAT / NOISE`.
- Bull: `WEAK BUY`, `STRONG BUY`.
- Abstain: `BEAR TRAP`, `BULL TRAP`.
- Crisis: not represented by TSIE labels.

Decision:
- This is useful as a public non-US equity source-label dry run for Bull/Bear/Sideways mapping research.
- It is not Board A acceptance evidence because it is sample-only, not full calibrated split/market/time evidence, and R6/canonical merge remains blocked.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Canonical merge allowed: `false`.
- Downstream promotion rerun allowed: `false`.
- Strict full objective achieved: `false`.
- `update_goal=false`.

No mutation claims:
- Runtime code changed: `false`.
- Shared intake mutated: `false`.
- R3/R5/R6 roots mutated: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.

Next:
- If continuing this branch, acquire a parquet-capable reader in disposable `/tmp` tooling or use a bounded remote parquet scanner, then compute full split/year/symbol label support before any canonical intake proposal. Keep R6 and full objective blocked until owner-export/FLIP evidence and canonical merge exist.
"""
    report_path.write_text(report)

    assertions = {
        "run_id": result["run_id"] == RUN_ID,
        "gate_result": result["gate_result"].endswith("no_acceptance_no_canonical_merge"),
        "license_verified_mit": license_verified,
        "parquet_large_no_raw_download": parquet_bytes and parquet_bytes > 500_000_000 and not result["raw_parquet_downloaded"],
        "sampled_rows_positive": sampled_rows > 0,
        "mapping_contract_has_bear_bull_sideways": {"Bear", "Bull", "Sideways"}.issubset(set(mapped_regimes_from_contract)),
        "trap_classes_abstain": LABEL_MAP[2]["decision"] == "abstain_trap" and LABEL_MAP[4]["decision"] == "abstain_trap",
        "crisis_not_represented": "Crisis" not in mapped_regimes,
        "r6_owner_export_absent": not root_status["r6_owner_export"]["present"],
        "r3_native_subhour_absent": not root_status["r3_native_subhour"]["present"],
        "r5_recency_extension_absent": not root_status["r5_recency_extension"]["present"],
        "accepted_rows_added_zero": result["accepted_rows_added"] == 0,
        "canonical_merge_allowed_false": result["canonical_merge_allowed"] is False,
        "downstream_chain_rerun_allowed_false": result["downstream_chain_rerun_allowed"] is False,
        "strict_full_objective_achieved_false": result["strict_full_objective_achieved"] is False,
        "update_goal_false": result["update_goal"] is False,
        "runtime_code_changed_false": result["runtime_code_changed"] is False,
        "shared_intake_mutated_false": result["shared_intake_mutated"] is False,
        "r3_r5_r6_roots_mutated_false": result["r3_r5_r6_roots_mutated"] is False,
        "thresholds_relaxed_false": result["thresholds_relaxed"] is False,
        "raw_data_committed_false": result["raw_data_committed"] is False,
        "trade_usable_false": result["trade_usable"] is False,
    }
    assertions_path.write_text("\n".join(f"{key}={'PASS' if value else 'FAIL'}" for key, value in assertions.items()) + "\n")
    if not all(assertions.values()):
        raise SystemExit(f"assertion failure: {[key for key, value in assertions.items() if not value]}")

    print(result["gate_result"])
    print(f"sampled_rows={sampled_rows}")
    print(f"mapped_regimes={','.join(mapped_regimes)}")
    print(f"strict_full_objective_achieved={result['strict_full_objective_achieved']}")
    print(f"report={rel(report_path)}")


if __name__ == "__main__":
    main()
