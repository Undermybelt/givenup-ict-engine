#!/usr/bin/env python3
"""Bounded Hugging Face TSIE label-source mapping audit.

This script uses Hugging Face metadata/preview endpoints only. It does not
download the large parquet file and does not treat rule-based labels as
accepted MainRegimeV2 source labels.
"""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T074300+0800-codex-hf-tsie-source-label-mapping-audit"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T074300-codex-hf-tsie-source-label-mapping-audit"
OUT_DIR = RUN_ROOT / "hf-tsie-mapping"
CHECK_DIR = RUN_ROOT / "checks"

DATASET = "sujinwo/tsie-market-regime-dataset"
API_DATASET = f"https://huggingface.co/api/datasets/{DATASET}"
API_SPLITS = f"https://datasets-server.huggingface.co/splits?dataset={DATASET}"
API_INFO = f"https://datasets-server.huggingface.co/info?dataset={DATASET}&config=default"
API_FIRST_ROWS = f"https://datasets-server.huggingface.co/first-rows?dataset={DATASET}&config=default&split=train"
README_RAW = f"https://huggingface.co/datasets/{DATASET}/raw/main/README.md"


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def fetch_json(url: str, limit: int = 2_000_000) -> Any:
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.loads(response.read(limit))


def fetch_text(url: str, limit: int = 200_000) -> str:
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read(limit).decode("utf-8", errors="replace")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    dataset_meta = fetch_json(API_DATASET)
    splits = fetch_json(API_SPLITS)
    info = fetch_json(API_INFO)
    first_rows = fetch_json(API_FIRST_ROWS)
    readme = fetch_text(README_RAW)

    features = list(info["dataset_info"]["features"].keys())
    sample_rows = first_rows.get("rows", [])[:10]
    sample_label_values = sorted({row["row"].get("regime_label") for row in sample_rows})
    group_id_examples = sorted({row["row"].get("group_id", "") for row in sample_rows})

    readme_lower = readme.lower()
    rule_based = "rule-based" in readme_lower
    seven_class = "7 classes" in readme_lower
    label_map = {
        "0": "STRONG SELL",
        "1": "WEAK SELL",
        "2": "BEAR TRAP",
        "3": "FLAT / NOISE",
        "4": "BULL TRAP",
        "5": "WEAK BUY",
        "6": "STRONG BUY",
    }

    mapping_candidates = [
        {
            "tsie_label": "STRONG SELL / WEAK SELL",
            "mainregimev2_candidate": "Bear",
            "status": "candidate_only_not_accepted",
            "reason": "rule-based IDX signal class is not an independent source-backed Bear root label for the requested yfinance/Kraken matrix",
        },
        {
            "tsie_label": "FLAT / NOISE",
            "mainregimev2_candidate": "Sideways",
            "status": "candidate_only_not_accepted",
            "reason": "rule-based IDX flat/noise class may resemble Sideways but is not source-backed cross-market/cross-timeframe root evidence",
        },
        {
            "tsie_label": "WEAK BUY / STRONG BUY",
            "mainregimev2_candidate": "Bull",
            "status": "candidate_only_not_accepted",
            "reason": "rule-based IDX buy/breakout class is not an accepted Bull root label panel",
        },
        {
            "tsie_label": "BEAR TRAP / BULL TRAP",
            "mainregimev2_candidate": "UnknownOrMixed or child/provenance",
            "status": "candidate_only_not_accepted",
            "reason": "trap labels are subtype/event-shape evidence, not active MainRegimeV2 root labels",
        },
        {
            "tsie_label": "none",
            "mainregimev2_candidate": "Crisis",
            "status": "missing",
            "reason": "README/schema expose no direct Crisis root class",
        },
        {
            "tsie_label": "none",
            "mainregimev2_candidate": "Manipulation",
            "status": "missing",
            "reason": "dataset has no direct manipulation event/order-flow/order-lifecycle source labels",
        },
    ]

    report = {
        "run_id": RUN_ID,
        "goal_achieved": False,
        "objective": "Bounded metadata/schema/sample audit of Hugging Face TSIE as a possible MainRegimeV2 source-label candidate.",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "dataset": DATASET,
            "api_dataset": API_DATASET,
            "api_splits": API_SPLITS,
            "api_info": API_INFO,
            "api_first_rows": API_FIRST_ROWS,
            "readme": README_RAW,
            "sha": dataset_meta.get("sha"),
            "last_modified": dataset_meta.get("lastModified"),
            "license": (dataset_meta.get("cardData") or {}).get("license"),
            "used_storage_bytes": dataset_meta.get("usedStorage"),
        },
        "bounded_fetch": {
            "downloaded_full_parquet": False,
            "metadata_only": True,
            "sample_rows_read": len(sample_rows),
        },
        "dataset_shape": {
            "splits": splits.get("splits", []),
            "num_examples": info["dataset_info"]["splits"]["train"]["num_examples"],
            "download_size": info["dataset_info"].get("download_size"),
            "dataset_size": info["dataset_info"].get("dataset_size"),
            "features": features,
            "sample_label_values": sample_label_values,
            "sample_group_ids": group_id_examples,
        },
        "readme_claims": {
            "rule_based_signal_logic": rule_based,
            "seven_class_labels": seven_class,
            "label_map": label_map,
        },
        "mapping_candidates": mapping_candidates,
        "completion_accounting": {
            "accepted_mainregimev2_full_universe_full_cycle": False,
            "accepted_root_labels_added": 0,
            "why_not_accepted": [
                "Dataset is IDX-specific and does not attach to the ready yfinance/Kraken provider matrix.",
                "Labels are described as rule-based signal logic, not independent external root annotations.",
                "Schema includes future_volatility and target_return fields, so leakage-safe usage would need a separate causal feature audit.",
                "No direct Crisis or Manipulation source label is available in the inspected schema/README.",
            ],
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_dataset_committed": False,
            "trade_usable": False,
        },
        "gate_result": "blocked_hf_tsie_not_attachable_as_mainregimev2_source_label_panel",
        "next_action": "Acquire a provenance-backed MainRegimeV2 label panel that directly covers the ready yfinance/Kraken/local cells, or keep full-universe completion blocked.",
        "artifacts": {
            "summary_json": rel(OUT_DIR / "hf_tsie_source_label_mapping_audit.json"),
            "summary_md": rel(OUT_DIR / "hf_tsie_source_label_mapping_audit.md"),
            "assertions": rel(CHECK_DIR / "hf_tsie_source_label_mapping_audit_assertions.out"),
            "script": rel(Path(__file__)),
        },
    }

    (OUT_DIR / "hf_tsie_source_label_mapping_audit.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )

    md = [
        "# HF TSIE Source Label Mapping Audit",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Goal achieved: `false`",
        "",
        "## Source",
        "",
        f"- Dataset: `{DATASET}`",
        f"- Last modified: `{dataset_meta.get('lastModified')}`",
        f"- Train examples: `{info['dataset_info']['splits']['train']['num_examples']}`",
        f"- Full parquet downloaded: `false`",
        f"- Sample rows inspected: `{len(sample_rows)}`",
        f"- Sample `regime_label` values: `{', '.join(str(x) for x in sample_label_values)}`",
        "",
        "## Mapping Disposition",
        "",
        "| TSIE Label | MainRegimeV2 Candidate | Status |",
        "|---|---|---|",
    ]
    for item in mapping_candidates:
        md.append(f"| `{item['tsie_label']}` | `{item['mainregimev2_candidate']}` | `{item['status']}` |")
    md.extend(
        [
            "",
            "## Decision",
            "",
            "- This is not accepted as a MainRegimeV2 source-label panel.",
            "- Labels are rule-based IDX signal classes, not independent labels attached to the yfinance/Kraken full matrix.",
            "- `Crisis` and direct `Manipulation` labels are missing from the inspected source.",
            "- Runtime code changed: false. Thresholds relaxed: false. Raw dataset committed: false. Trade usable: false.",
            "",
            "Gate result: `blocked_hf_tsie_not_attachable_as_mainregimev2_source_label_panel`",
        ]
    )
    (OUT_DIR / "hf_tsie_source_label_mapping_audit.md").write_text("\n".join(md) + "\n")

    assertions = [
        "goal_achieved=false",
        "downloaded_full_parquet=false",
        "metadata_only=true",
        f"sample_rows_read={len(sample_rows)}",
        f"train_examples={info['dataset_info']['splits']['train']['num_examples']}",
        f"rule_based_signal_logic={str(rule_based).lower()}",
        "accepted_root_labels_added=0",
        "accepted_mainregimev2_full_universe_full_cycle=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_dataset_committed=false",
        "trade_usable=false",
        "gate_result=blocked_hf_tsie_not_attachable_as_mainregimev2_source_label_panel",
    ]
    (CHECK_DIR / "hf_tsie_source_label_mapping_audit_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )
    print(rel(OUT_DIR / "hf_tsie_source_label_mapping_audit.json"))


if __name__ == "__main__":
    main()
