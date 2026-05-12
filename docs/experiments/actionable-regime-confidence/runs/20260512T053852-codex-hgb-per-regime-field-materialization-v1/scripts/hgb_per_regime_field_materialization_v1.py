#!/usr/bin/env python3
"""Materialize per-regime field evidence from the accepted HGB screen."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np


RUN_ID = "20260512T053852-codex-hgb-per-regime-field-materialization-v1"
SLUG = "hgb-per-regime-field-materialization-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"
HGB_SCRIPT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T051844-codex-source-label-hgb-numeric-threshold-screen-v1/"
    "scripts/source_label_hgb_numeric_threshold_screen_v1.py"
)
HGB_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T051844-codex-source-label-hgb-numeric-threshold-screen-v1/"
    "source-label-hgb-numeric-threshold-screen-v1/"
    "source_label_hgb_numeric_threshold_screen_v1.json"
)
MIN_INSTRUMENTS = 2
MIN_PERIODS = 4
MIN_CONTEXTS = 2


def load_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("hgb_screen_module", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def compact_values(values: Any, limit: int = 20) -> dict[str, Any]:
    clean = sorted({str(value) for value in values if str(value) and str(value) != "nan"})
    return {
        "count": len(clean),
        "sample": clean[:limit],
        "truncated": len(clean) > limit,
    }


def split_summary(
    data: Any,
    selected: np.ndarray,
    label: str,
    split: str,
    base: Any,
) -> dict[str, Any]:
    split_mask = (data["split_role"].to_numpy() == split) & selected
    hit_mask = split_mask & (data["main_regime_v2_label"].to_numpy() == label)
    support = int(split_mask.sum())
    hits = int(hit_mask.sum())
    precision = hits / support if support else 0.0
    hit_rows = data.loc[hit_mask]
    split_rows = data.loc[split_mask]
    return {
        "split_role": split,
        "support": support,
        "label_hits": hits,
        "precision": round(float(precision), 10),
        "wilson95_lcb": round(float(base.wilson_lcb(hits, support)), 10),
        "hit_symbol_count": int(hit_rows["symbol"].nunique()) if not hit_rows.empty else 0,
        "hit_symbols": compact_values(hit_rows["symbol"]) if not hit_rows.empty else {"count": 0, "sample": [], "truncated": False},
        "hit_market_context_count": int(
            hit_rows[["source_owner", "market_family", "timeframe"]]
            .drop_duplicates()
            .shape[0]
        )
        if not hit_rows.empty
        else 0,
        "hit_market_contexts": compact_values(
            hit_rows["source_owner"].astype(str)
            + "|"
            + hit_rows["market_family"].astype(str)
            + "|"
            + hit_rows["timeframe"].astype(str)
        )
        if not hit_rows.empty
        else {"count": 0, "sample": [], "truncated": False},
        "selected_date_min": str(split_rows["timestamp_or_date"].min()) if not split_rows.empty else "",
        "selected_date_max": str(split_rows["timestamp_or_date"].max()) if not split_rows.empty else "",
        "hit_date_min": str(hit_rows["timestamp_or_date"].min()) if not hit_rows.empty else "",
        "hit_date_max": str(hit_rows["timestamp_or_date"].max()) if not hit_rows.empty else "",
        "sample_hit_source_row_ids": list(hit_rows["source_row_id"].astype(str).head(8)) if not hit_rows.empty else [],
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    hgb = load_module(HGB_SCRIPT)
    base = hgb.load_base()
    hgb_result = json.loads(HGB_JSON.read_text(encoding="utf-8"))

    data = base.build_dataset()
    features, feature_columns = hgb.add_numeric_features(data, base)
    train_mask = data["split_role"] == "calibration"
    y_train = data.loc[train_mask, "main_regime_v2_label"]
    model = hgb.HistGradientBoostingClassifier(
        max_iter=160,
        learning_rate=0.055,
        max_leaf_nodes=31,
        min_samples_leaf=120,
        l2_regularization=0.08,
        validation_fraction=0.12,
        n_iter_no_change=12,
        random_state=20260512,
    )
    model.fit(features.loc[train_mask], y_train, sample_weight=hgb.balanced_sample_weight(y_train))
    probabilities = model.predict_proba(features)
    classes = list(model.classes_)

    gate_by_label = {row["label"]: row for row in hgb_result["gates"]}
    field_rows: list[dict[str, Any]] = []
    split_rows: list[dict[str, Any]] = []
    sample_rows: list[dict[str, Any]] = []
    packets: dict[str, Any] = {}
    all_field_complete = True

    for label in base.ROOT_LABELS:
        gate = gate_by_label[label]
        threshold = float(gate["threshold"])
        label_index = classes.index(label)
        selected = probabilities[:, label_index] >= threshold
        selected_hits = selected & (data["main_regime_v2_label"].to_numpy() == label)
        hit_rows = data.loc[selected_hits].copy()
        split_details = [
            split_summary(data, selected, label, split, base)
            for split in base.REQUIRED_SPLITS
        ]
        instrument_values = compact_values(hit_rows["symbol"])
        period_rows = [
            {
                "split_role": detail["split_role"],
                "hit_date_min": detail["hit_date_min"],
                "hit_date_max": detail["hit_date_max"],
                "support": detail["support"],
                "label_hits": detail["label_hits"],
                "wilson95_lcb": detail["wilson95_lcb"],
            }
            for detail in split_details
        ]
        context_values = compact_values(
            hit_rows["source_owner"].astype(str)
            + "|"
            + hit_rows["market_family"].astype(str)
            + "|"
            + hit_rows["timeframe"].astype(str)
        )
        field_complete = (
            gate["accepted_extra_trees_confidence_95"] is True
            and instrument_values["count"] >= MIN_INSTRUMENTS
            and len([row for row in period_rows if row["label_hits"] > 0]) >= MIN_PERIODS
            and context_values["count"] >= MIN_CONTEXTS
        )
        all_field_complete = all_field_complete and field_complete
        packet = {
            "label": label,
            "qualifying_condition": f"hgb_numeric_probability({label}) >= {threshold}",
            "model_root": "20260512T051844-codex-source-label-hgb-numeric-threshold-screen-v1",
            "threshold": threshold,
            "accepted_95": bool(gate["accepted_extra_trees_confidence_95"]),
            "min_split_support": int(gate["min_split_support"]),
            "min_split_wilson95_lcb": float(gate["min_split_wilson95_lcb"]),
            "validation_instruments": instrument_values,
            "validation_periods": period_rows,
            "validation_market_contexts": context_values,
            "field_complete_diagnostic": bool(field_complete),
            "source_control_evidence_acquired": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "trade_usable": False,
            "update_goal": False,
        }
        packets[label] = packet
        field_rows.append(
            {
                "label": label,
                "qualifying_condition": packet["qualifying_condition"],
                "accepted_95": packet["accepted_95"],
                "min_split_support": packet["min_split_support"],
                "min_split_wilson95_lcb": packet["min_split_wilson95_lcb"],
                "validation_instrument_count": instrument_values["count"],
                "validation_instrument_sample": ";".join(instrument_values["sample"]),
                "validation_period_count": len([row for row in period_rows if row["label_hits"] > 0]),
                "validation_market_context_count": context_values["count"],
                "validation_market_context_sample": ";".join(context_values["sample"]),
                "field_complete_diagnostic": packet["field_complete_diagnostic"],
                "source_control_evidence_acquired": False,
                "canonical_merge": False,
                "downstream_promotion_rerun": False,
                "update_goal": False,
            }
        )
        for detail in split_details:
            split_rows.append(
                {
                    "label": label,
                    "qualifying_condition": packet["qualifying_condition"],
                    **{
                        key: value
                        for key, value in detail.items()
                        if key not in {"hit_symbols", "hit_market_contexts", "sample_hit_source_row_ids"}
                    },
                    "hit_symbols": ";".join(detail["hit_symbols"]["sample"]),
                    "hit_market_contexts": ";".join(detail["hit_market_contexts"]["sample"]),
                    "sample_hit_source_row_ids": ";".join(detail["sample_hit_source_row_ids"]),
                }
            )
        for _, row in hit_rows.head(16).iterrows():
            sample_rows.append(
                {
                    "label": label,
                    "qualifying_condition": packet["qualifying_condition"],
                    "source_owner": row["source_owner"],
                    "market_family": row["market_family"],
                    "symbol": row["symbol"],
                    "timeframe": row["timeframe"],
                    "timestamp_or_date": row["timestamp_or_date"],
                    "split_role": row["split_role"],
                    "source_row_id": row["source_row_id"],
                    "main_regime_v2_label": row["main_regime_v2_label"],
                }
            )

    gate_result = (
        "hgb_per_regime_field_materialization_v1=all_hgb_labels_field_complete_diagnostic_source_control_absent"
        if all_field_complete
        else "hgb_per_regime_field_materialization_v1=field_materialized_incomplete_or_source_control_absent"
    )
    result = {
        "run_id": RUN_ID,
        "gate_result": gate_result,
        "source_hgb_run": str(HGB_JSON),
        "row_count": int(len(data)),
        "rows_sha256": sha256_file(base.INTAKE_ROWS),
        "provenance_sha256": sha256_file(base.INTAKE_PROVENANCE),
        "feature_columns": feature_columns,
        "packets": packets,
        "diagnostic_field_complete_labels": [
            label for label, packet in packets.items() if packet["field_complete_diagnostic"]
        ],
        "promotion_status": {
            "accepted_rows_added": 0,
            "source_control_evidence_acquired": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
    }
    (OUT / "hgb_per_regime_field_materialization_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(OUT / "hgb_per_regime_field_summary_v1.csv", field_rows)
    write_csv(OUT / "hgb_per_regime_split_validation_v1.csv", split_rows)
    write_csv(OUT / "hgb_per_regime_sample_rows_v1.csv", sample_rows)

    lines = [
        "# HGB Per-Regime Field Materialization v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{gate_result}`",
        "",
        "## Scope",
        "",
        "This packet turns the accepted `051844` HGB diagnostic screen into explicit per-regime field evidence: qualifying condition, split validation, instruments, periods, and market contexts.",
        "",
        "It is diagnostic only. It does not create source/control evidence, canonical merge input, downstream promotion evidence, trade evidence, or `update_goal` authorization.",
        "",
        "## Summary",
        "",
        "| Label | Qualifying condition | 95 accepted | Min support | Min Wilson95 | Instruments | Periods | Contexts | Diagnostic field complete |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in field_rows:
        lines.append(
            f"| `{row['label']}` | `{row['qualifying_condition']}` | "
            f"`{str(row['accepted_95']).lower()}` | `{row['min_split_support']}` | "
            f"`{row['min_split_wilson95_lcb']}` | `{row['validation_instrument_count']}` | "
            f"`{row['validation_period_count']}` | `{row['validation_market_context_count']}` | "
            f"`{str(row['field_complete_diagnostic']).lower()}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Diagnostic field-complete labels: `{result['diagnostic_field_complete_labels']}`.",
            "- Source/control evidence acquired `false`; canonical merge `false`; downstream promotion rerun `false`; trade usable `false`; `update_goal=false`.",
            "- This packet can be used as per-regime diagnostic field evidence after source/control unlock, but it cannot unlock Board A promotion by itself.",
        ]
    )
    (OUT / "hgb_per_regime_field_materialization_v1.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS gate_result={gate_result}",
        f"PASS diagnostic_field_complete_labels={','.join(result['diagnostic_field_complete_labels'])}",
        f"PASS diagnostic_field_complete_label_count={len(result['diagnostic_field_complete_labels'])}",
        "PASS source_control_evidence_acquired=false",
        "PASS canonical_merge=false",
        "PASS downstream_promotion_rerun=false",
        "PASS strict_full_objective=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "hgb_per_regime_field_materialization_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "gate_result": gate_result,
                "diagnostic_field_complete_labels": result["diagnostic_field_complete_labels"],
                "promotion_status": result["promotion_status"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
