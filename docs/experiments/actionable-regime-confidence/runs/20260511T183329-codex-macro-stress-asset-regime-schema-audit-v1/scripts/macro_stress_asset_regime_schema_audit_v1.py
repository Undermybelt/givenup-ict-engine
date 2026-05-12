#!/usr/bin/env python3
"""Audit Kaggle macro stress/asset-regime candidate for source-label suitability."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T183329+0800-codex-macro-stress-asset-regime-schema-audit-v1"
DATASET = "kanchana1990/algorithmic-trading-macro-stress-and-asset-regimes"
DATASET_URL = f"https://www.kaggle.com/datasets/{DATASET}"
CSV_NAME = "Global_Market_Stress_and_Liquidity_Regimes.csv"
TMP_ROOT = Path("/tmp/ict-engine-macro-stress-asset-regimes-audit-v1")
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T183329-codex-macro-stress-asset-regime-schema-audit-v1"
)
OUT_DIR = RUN_ROOT / "macro-stress-schema"
CHECK_DIR = RUN_ROOT / "checks"
OUT_JSON = OUT_DIR / "macro_stress_asset_regime_schema_audit_v1.json"
OUT_MD = OUT_DIR / "macro_stress_asset_regime_schema_audit_v1.md"
OUT_FIELDS = OUT_DIR / "macro_stress_asset_regime_schema_audit_v1_fields.csv"
OUT_ASSERT = CHECK_DIR / "macro_stress_asset_regime_schema_audit_v1_assertions.out"

LABEL_TOKENS = ("regime", "label", "class", "state", "target", "signal")
SOURCE_LABEL_FORBIDDEN_HINTS = ("Rolling", "RSI", "Drawdown", "Corr", "Spread", "Stress", "Vol")


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def load_metadata(path: Path) -> dict[str, Any]:
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, str):
        raw = json.loads(raw)
    if not isinstance(raw, dict):
        raise TypeError(f"unexpected metadata type: {type(raw).__name__}")
    return raw


def classify_field(name: str) -> dict[str, str]:
    lower = name.lower()
    is_label_like = any(token in lower for token in LABEL_TOKENS)
    is_feature_hint = any(token.lower() in lower for token in SOURCE_LABEL_FORBIDDEN_HINTS)
    if name == "Date":
        role = "timestamp"
    elif is_label_like and not is_feature_hint:
        role = "label_like_name"
    else:
        role = "feature_or_price_context"
    return {
        "field": name,
        "role": role,
        "accepted_as_main_regime_v2_label": "false",
        "notes": "no explicit Bull/Bear/Sideways/Crisis or direct Manipulation label field",
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)

    files = run(["kaggle", "datasets", "files", DATASET]).stdout
    run(["kaggle", "datasets", "metadata", DATASET, "-p", str(TMP_ROOT)])
    run(
        [
            "kaggle",
            "datasets",
            "download",
            DATASET,
            "-f",
            CSV_NAME,
            "-p",
            str(TMP_ROOT),
            "-o",
            "--quiet",
        ]
    )

    metadata_path = TMP_ROOT / "dataset-metadata.json"
    csv_path = TMP_ROOT / CSV_NAME
    metadata = load_metadata(metadata_path)

    row_count = 0
    dates: list[str] = []
    fields: list[str] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        for row in reader:
            row_count += 1
            dates.append(row.get("Date", ""))

    field_rows = [classify_field(field) for field in fields]
    label_like_fields = [row["field"] for row in field_rows if row["role"] == "label_like_name"]
    post_source_tail_rows = sum(date > "2026-01-30" for date in dates)
    cross_asset_columns = [
        field
        for field in fields
        if field
        in {
            "Equities_US",
            "Equities_Tech",
            "Equities_Emerging",
            "Bonds_LongTerm",
            "Gold",
            "Oil",
            "Volatility_Index",
            "Crypto_Bitcoin",
            "Yield_Curve_Spread",
            "High_Yield_Spread",
            "Financial_Stress_Index",
        }
    ]

    artifact = {
        "run_id": RUN_ID,
        "artifact_type": "macro_stress_asset_regime_schema_audit_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": DATASET,
        "dataset_url": DATASET_URL,
        "purpose": (
            "Check whether this public cross-asset Kaggle package can satisfy Board A "
            "source-label equivalence or recency-extension requirements."
        ),
        "kaggle_files_listing": files,
        "metadata": {
            "title": metadata.get("title"),
            "subtitle": metadata.get("subtitle"),
            "ownerUser": metadata.get("ownerUser"),
            "totalDownloads": metadata.get("totalDownloads"),
            "totalViews": metadata.get("totalViews"),
            "totalVotes": metadata.get("totalVotes"),
            "licenses": metadata.get("licenses"),
        },
        "schema": {
            "file": CSV_NAME,
            "row_count": row_count,
            "field_count": len(fields),
            "date_min": min(dates) if dates else None,
            "date_max": max(dates) if dates else None,
            "post_source_tail_rows_after_2026_01_30": post_source_tail_rows,
            "fields": fields,
            "label_like_fields": label_like_fields,
            "cross_asset_columns": cross_asset_columns,
        },
        "decision": "blocked_feature_context_only_no_source_regime_labels",
        "reason": (
            "The package has useful cross-asset prices and macro stress features, including "
            "QQQ/BTC/GLD/USO/TLT/FRED-derived context, but the CSV contains no explicit "
            "source-owned MainRegimeV2 labels, no direct Manipulation labels, and no "
            "matched negative/control groups. Its post-2026-01-30 rows are features, not "
            "source-label recency extension rows."
        ),
        "gate_result": (
            "macro_stress_asset_regime_schema_audit_v1="
            "feature_context_only_no_source_label_equivalence"
        ),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": (
            "Do not use this package as Board A source labels. It can only be sidecar "
            "macro/cross-asset context unless a source owner supplies explicit regime "
            "labels and equivalence provenance."
        ),
    }

    OUT_JSON.write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    with OUT_FIELDS.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["field", "role", "accepted_as_main_regime_v2_label", "notes"],
        )
        writer.writeheader()
        writer.writerows(field_rows)

    md = [
        "# Macro Stress Asset Regime Schema Audit v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        "- Decision: `blocked_feature_context_only_no_source_regime_labels`.",
        "- Gate result: `macro_stress_asset_regime_schema_audit_v1=feature_context_only_no_source_label_equivalence`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Candidate",
        "",
        f"- Dataset: `{DATASET}`.",
        f"- URL: {DATASET_URL}.",
        f"- File: `{CSV_NAME}`.",
        f"- Rows: `{row_count}`; fields: `{len(fields)}`.",
        f"- Date range: `{min(dates) if dates else None}` to `{max(dates) if dates else None}`.",
        f"- Rows after source-panel tail `2026-01-30`: `{post_source_tail_rows}`.",
        f"- Cross-asset columns: `{', '.join(cross_asset_columns)}`.",
        f"- Label-like fields: `{', '.join(label_like_fields) if label_like_fields else 'none'}`.",
        "",
        "## Guardrail",
        "",
        "This dataset is feature/context evidence only. It has no explicit `Bull`/`Bear`/`Sideways`/`Crisis` source labels, no direct `Manipulation` labels, and no matched negative/control groups. Do not promote its post-tail feature rows into source-panel recency labels.",
    ]
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    OUT_ASSERT.write_text(
        "\n".join(
            [
                f"run_id={RUN_ID}",
                f"row_count={row_count}",
                f"field_count={len(fields)}",
                f"date_min={min(dates) if dates else ''}",
                f"date_max={max(dates) if dates else ''}",
                f"post_source_tail_rows_after_2026_01_30={post_source_tail_rows}",
                f"label_like_field_count={len(label_like_fields)}",
                "accepted_rows_added=0",
                "new_confidence_gate=false",
                "full_objective_achieved=false",
                "update_goal=false",
                "runtime_code_changed=false",
                "thresholds_relaxed=false",
                "raw_data_committed=false",
                "trade_usable=false",
                "assertion_status=PASS",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(artifact["gate_result"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
