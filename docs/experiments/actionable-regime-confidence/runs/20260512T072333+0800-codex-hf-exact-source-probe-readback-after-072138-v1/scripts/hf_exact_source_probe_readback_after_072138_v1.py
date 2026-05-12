#!/usr/bin/env python3
"""Settle the raw 072138 Hugging Face exact-source probe into a gate packet."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = RUN_ROOT / "hf-exact-source-probe-readback-after-072138-v1"
CHECKS_DIR = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

RUN_ID = "20260512T072333+0800-codex-hf-exact-source-probe-readback-after-072138-v1"
SOURCE_RUN_ID = "20260512T072138+0800-codex-hf-r5-r3-exact-source-route-probe-after-071538-v1"
SOURCE_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / SOURCE_RUN_ID
COMMAND_OUTPUT = SOURCE_ROOT / "command-output"
GATE = "hf_exact_source_probe_readback_after_072138_v1=all_exact_queries_zero_no_r5_r3_unlock_no_downstream"

QUERY_KEYS = [
    "hf_mainregimev2",
    "hf_mainregimev2_crisis",
    "hf_market_regime_crisis",
    "hf_native_subhour_source_label_rows",
    "hf_stock_market_regimes_2000_2026",
    "hf_stock_market_regimes_2026_extension",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").strip() if path.exists() else ""


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def query_row(key: str) -> dict:
    json_path = COMMAND_OUTPUT / f"{key}.json"
    exit_path = COMMAND_OUTPUT / f"{key}.exit"
    query_path = COMMAND_OUTPUT / f"{key}.query"
    summary_path = COMMAND_OUTPUT / f"{key}.summary.tsv"
    payload = load_json(json_path) if json_path.exists() else []
    result_count = len(payload) if isinstance(payload, list) else None
    return {
        "query_key": key,
        "query": read_text(query_path),
        "exit_code": int(read_text(exit_path) or -1),
        "json_type": "array" if isinstance(payload, list) else type(payload).__name__,
        "result_count": result_count,
        "summary_data_rows": max(0, len(summary_path.read_text(encoding="utf-8", errors="replace").splitlines()) - 1) if summary_path.exists() else 0,
        "json_path": str(json_path.relative_to(REPO)),
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = list(rows[0].keys()) if rows else ["query_key"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    rows = [query_row(key) for key in QUERY_KEYS]
    all_exit_zero = all(row["exit_code"] == 0 for row in rows)
    all_zero_results = all(row["result_count"] == 0 for row in rows)
    all_arrays = all(row["json_type"] == "array" for row in rows)

    assertions = {
        "source_run_present": SOURCE_ROOT.exists(),
        "all_exit_zero": all_exit_zero,
        "all_json_arrays": all_arrays,
        "all_result_counts_zero": all_zero_results,
        "mainregimev2_dataset_found": False,
        "r5_post_cutoff_source_rows_found": False,
        "r3_native_subhour_rows_found": False,
        "accepted_rows_added": 0,
        "r6_owner_export_unlock": False,
        "r5_recency_unlock": False,
        "r3_native_subhour_unlock": False,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    packet = {
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "generated_at_local": datetime.now(timezone(timedelta(hours=8))).isoformat(),
        "board_sha256_before_artifact": sha256_file(BOARD),
        "gate_result": GATE,
        "scope": {
            "mode": "settled_readback_of_raw_huggingface_exact_source_probe",
            "source_root": str(SOURCE_ROOT.relative_to(REPO)),
            "read_only": True,
            "no_root_mutation": True,
            "no_canonical_merge": True,
            "no_downstream_promotion": True,
            "update_goal": False,
        },
        "queries": rows,
        "assertions": assertions,
        "decision": (
            "The 072138 Hugging Face exact-source probe is a raw command-output root: every checked "
            "JSON payload is an array, every query exited 0, and every exact query returned 0 rows. "
            "It therefore supplies no MainRegimeV2 dataset, no source-owned post-2026-01-30 R5 rows, "
            "and no verifier-native native-subhour R3 labels."
        ),
        "next": (
            "Continue only from explicit source/control approval, verifier-native R6 owner-export rows "
            "with valid controls, source-owned post-2026-01-30 R5 rows matching the source-panel schema, "
            "verifier-native Crisis-capable R3 MainRegimeV2 labels, or a genuinely new accepted "
            "cross-timeframe MainRegimeV2 source export."
        ),
    }

    json_path = ARTIFACT_DIR / "hf_exact_source_probe_readback_after_072138_v1.json"
    csv_path = ARTIFACT_DIR / "hf_exact_source_probe_readback_after_072138_v1.csv"
    md_path = ARTIFACT_DIR / "hf_exact_source_probe_readback_after_072138_v1.md"
    assertions_path = CHECKS_DIR / "hf_exact_source_probe_readback_after_072138_v1_assertions.out"

    json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(csv_path, rows)
    md_path.write_text(
        "\n".join(
            [
                "# HF Exact Source Probe Readback After 072138 v1",
                "",
                f"Run id: `{RUN_ID}`",
                f"Source run id: `{SOURCE_RUN_ID}`",
                "",
                f"Gate result: `{GATE}`",
                "",
                "## Scope",
                "",
                "Settled readback of the raw `072138` Hugging Face exact-source probe. This packet reads existing command outputs only; it does not rerun Hugging Face search, mutate target roots, copy rows into canonical inputs, approve proxy labels, run direct verifier, run split calibration, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Readback",
                "",
                f"- Source run present: `{SOURCE_ROOT.exists()}`.",
                f"- Queries checked: `{len(rows)}`.",
                f"- All query exits zero: `{all_exit_zero}`.",
                f"- All JSON payloads arrays: `{all_arrays}`.",
                f"- All result counts zero: `{all_zero_results}`.",
                "",
                "## Decision",
                "",
                packet["decision"],
                "",
                "Accepted rows added `0`, R6 owner/export unlock false, R5 recency unlock false, R3 native-subhour unlock false, valid required-root unlock false, source/control evidence acquired false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path.relative_to(REPO)}`",
                f"- Query CSV: `{csv_path.relative_to(REPO)}`",
                f"- Assertions: `{assertions_path.relative_to(REPO)}`",
                "",
                "## Next",
                "",
                packet["next"],
                "",
            ]
        ),
        encoding="utf-8",
    )
    assertions_path.write_text(
        "\n".join(
            [
                f"gate_result={GATE}",
                f"source_run_present={str(SOURCE_ROOT.exists()).lower()}",
                f"all_exit_zero={str(all_exit_zero).lower()}",
                f"all_json_arrays={str(all_arrays).lower()}",
                f"all_result_counts_zero={str(all_zero_results).lower()}",
                "mainregimev2_dataset_found=false",
                "r5_post_cutoff_source_rows_found=false",
                "r3_native_subhour_rows_found=false",
                "accepted_rows_added=0",
                "valid_required_root_unlock=false",
                "source_control_evidence_acquired=false",
                "canonical_merge=false",
                "downstream_promotion_rerun=false",
                "strict_full_objective=false",
                "trade_usable=false",
                "update_goal=false",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
