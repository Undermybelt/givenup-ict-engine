#!/usr/bin/env python3
"""Live Kaggle source-label extension discovery for Board A after 041423."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20260512T041846-codex-live-source-label-extension-discovery-after-041423-v1"
SLUG = "live-source-label-extension-discovery-after-041423-v1"
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"
COMMAND_OUT = RUN_ROOT / "command-output"
TMP_ROOT = Path("/tmp/ict-engine-live-source-label-extension-discovery-after-041423-v1")
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
KAGGLE = Path("/Users/thrill3r/.local/bin/kaggle")

SEARCH_QUERIES = [
    "market regime",
    "stock market regime",
    "regime classification",
    "volatility regime",
]

DOWNLOAD_CANDIDATES = {
    "igormerlinicomposer/herding-based-market-regime-dataset": {
        "slug": "herding",
        "gate": "recency_label_like_single_panel_mapping_insufficient_no_promotion",
    },
    "kanchana1990/algorithmic-trading-macro-stress-and-asset-regimes": {
        "slug": "macro_asset",
        "gate": "feature_panel_no_source_regime_labels_no_promotion",
    },
    "nickdatak/us-market-regimes-dataset-1995-2024": {
        "slug": "us_regimes_1995_2024",
        "gate": "explicit_regime_source_stale_2024_no_r5_recency_no_promotion",
    },
}

EXISTING_RECENCY_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T040919-codex-stock-regime-kaggle-live-recency-recheck-after-040311-v1/"
    "stock-regime-kaggle-live-recency-recheck-after-040311-v1/"
    "stock_regime_kaggle_live_recency_recheck_after_040311_v1.json"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(args: list[str], stem: str, timeout: int = 120) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    (COMMAND_OUT / f"{stem}.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (COMMAND_OUT / f"{stem}.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    (COMMAND_OUT / f"{stem}.exit").write_text(str(proc.returncode), encoding="utf-8")
    return {
        "stem": stem,
        "args": args,
        "return_code": proc.returncode,
        "stdout_path": str(COMMAND_OUT / f"{stem}.stdout.txt"),
        "stderr_path": str(COMMAND_OUT / f"{stem}.stderr.txt"),
    }


def read_csv_text(text: str) -> list[dict[str, str]]:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    return list(csv.DictReader(lines))


def read_csv_file(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, str):
        return json.loads(payload)
    return payload


def date_bounds(rows: list[dict[str, str]], date_col: str = "Date") -> tuple[str, str]:
    values = sorted(row.get(date_col, "") for row in rows if row.get(date_col, ""))
    if not values:
        return "", ""
    return values[0], values[-1]


def value_counts(rows: list[dict[str, str]], col: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = row.get(col, "")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def csv_summary(path: Path) -> dict[str, Any]:
    rows = read_csv_file(path)
    fieldnames = list(rows[0].keys()) if rows else []
    date_col = "Date" if "Date" in fieldnames else "date" if "date" in fieldnames else ""
    date_min, date_max = date_bounds(rows, date_col) if date_col else ("", "")
    label_like_cols = [
        col
        for col in fieldnames
        if any(token in col.lower() for token in ["regime", "state", "position", "trend", "label"])
    ]
    return {
        "file": str(path),
        "file_name": path.name,
        "sha256": sha256_file(path),
        "rows": len(rows),
        "columns": fieldnames,
        "date_col": date_col,
        "date_min": date_min,
        "date_max": date_max,
        "label_like_cols": label_like_cols,
        "label_like_counts": {
            col: value_counts(rows, col) for col in label_like_cols[:8]
        },
    }


def current_cursor(board_text: str) -> str:
    marker = "| last_loop_id |"
    for line in board_text.splitlines():
        if line.startswith(marker):
            return line.split("|")[2].strip()
    return "unknown"


def load_existing_recency() -> dict[str, Any]:
    if not EXISTING_RECENCY_JSON.exists():
        return {}
    return json.loads(EXISTING_RECENCY_JSON.read_text(encoding="utf-8"))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)

    if not KAGGLE.exists():
        raise FileNotFoundError(KAGGLE)

    board_text = BOARD.read_text(encoding="utf-8")
    commands: list[dict[str, Any]] = []
    search_rows: list[dict[str, Any]] = []

    for query in SEARCH_QUERIES:
        stem = "kaggle_search_" + query.replace(" ", "_")
        result = run_command([str(KAGGLE), "datasets", "list", "-s", query, "--csv"], stem)
        commands.append(result)
        stdout = (COMMAND_OUT / f"{stem}.stdout.txt").read_text(encoding="utf-8")
        for rank, row in enumerate(read_csv_text(stdout), start=1):
            row_out: dict[str, Any] = {"query": query, "rank": rank}
            row_out.update(row)
            search_rows.append(row_out)

    file_summaries: list[dict[str, Any]] = []
    metadata_by_ref: dict[str, dict[str, Any]] = {}
    files_by_ref: dict[str, list[str]] = {}
    candidate_rows: list[dict[str, Any]] = []

    for ref, config in DOWNLOAD_CANDIDATES.items():
        slug = config["slug"]
        meta_dir = TMP_ROOT / f"metadata-{slug}"
        data_dir = TMP_ROOT / f"data-{slug}"
        meta_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

        commands.append(
            run_command([str(KAGGLE), "datasets", "metadata", ref, "-p", str(meta_dir)], f"metadata_{slug}")
        )
        commands.append(
            run_command([str(KAGGLE), "datasets", "files", ref], f"files_{slug}")
        )
        commands.append(
            run_command([str(KAGGLE), "datasets", "download", ref, "-p", str(data_dir), "--unzip"], f"download_{slug}")
        )

        metadata = parse_metadata(meta_dir / "dataset-metadata.json")
        metadata_by_ref[ref] = metadata
        files_by_ref[ref] = []
        for path in sorted(data_dir.glob("*.csv")):
            summary = csv_summary(path)
            summary["dataset_ref"] = ref
            summary["raw_committed_to_repo"] = False
            file_summaries.append(summary)
            files_by_ref[ref].append(path.name)

        label_cols = sorted({col for item in file_summaries if item["dataset_ref"] == ref for col in item["label_like_cols"]})
        date_maxes = [item["date_max"] for item in file_summaries if item["dataset_ref"] == ref and item["date_max"]]
        row_count = sum(int(item["rows"]) for item in file_summaries if item["dataset_ref"] == ref)
        candidate_rows.append(
            {
                "dataset_ref": ref,
                "title": metadata.get("title", ""),
                "last_updated": next(
                    (row.get("lastUpdated", "") for row in search_rows if row.get("ref") == ref),
                    "",
                ),
                "license": ";".join(lic.get("name", "") for lic in metadata.get("licenses", [])),
                "downloaded_files": ";".join(files_by_ref[ref]),
                "rows_scanned": row_count,
                "date_max": max(date_maxes) if date_maxes else "",
                "label_like_columns": ";".join(label_cols),
                "r3_native_subhour_root_satisfied": False,
                "r5_recency_extension_root_satisfied": False,
                "r6_owner_export_root_satisfied": False,
                "raw_data_committed": False,
                "accepted_rows_added": 0,
                "gate": config["gate"],
            }
        )

    existing_recency = load_existing_recency()
    if existing_recency:
        candidate_rows.insert(
            0,
            {
                "dataset_ref": "mafaqbhatti/stock-market-regimes-20002026",
                "title": "Stock Market Regimes (2000-2026)",
                "last_updated": next(
                    (
                        row.get("lastUpdated", "")
                        for row in search_rows
                        if row.get("ref") == "mafaqbhatti/stock-market-regimes-20002026"
                    ),
                    "",
                ),
                "license": "see_prior_040919_kaggle_metadata",
                "downloaded_files": "not_redownloaded_prior_040919_recheck_used",
                "rows_scanned": existing_recency.get("total_rows", ""),
                "date_max": existing_recency.get("max_date", ""),
                "label_like_columns": "regime_label;regime_confidence",
                "r3_native_subhour_root_satisfied": False,
                "r5_recency_extension_root_satisfied": False,
                "r6_owner_export_root_satisfied": False,
                "raw_data_committed": False,
                "accepted_rows_added": 0,
                "gate": "prior_live_recheck_upstream_unchanged_no_r5_recency_tail_repair_no_promotion",
            },
        )

    write_csv(
        OUT / "live_source_label_extension_search_results_v1.csv",
        search_rows,
        ["query", "rank", "ref", "title", "size", "lastUpdated", "downloadCount", "voteCount", "usabilityRating"],
    )
    write_csv(
        OUT / "live_source_label_extension_candidate_summary_v1.csv",
        candidate_rows,
        [
            "dataset_ref",
            "title",
            "last_updated",
            "license",
            "downloaded_files",
            "rows_scanned",
            "date_max",
            "label_like_columns",
            "r3_native_subhour_root_satisfied",
            "r5_recency_extension_root_satisfied",
            "r6_owner_export_root_satisfied",
            "raw_data_committed",
            "accepted_rows_added",
            "gate",
        ],
    )
    flat_file_rows = [
        {
            "dataset_ref": item["dataset_ref"],
            "file_name": item["file_name"],
            "sha256": item["sha256"],
            "rows": item["rows"],
            "date_col": item["date_col"],
            "date_min": item["date_min"],
            "date_max": item["date_max"],
            "label_like_columns": ";".join(item["label_like_cols"]),
            "raw_committed_to_repo": item["raw_committed_to_repo"],
        }
        for item in file_summaries
    ]
    write_csv(
        OUT / "live_source_label_extension_file_summary_v1.csv",
        flat_file_rows,
        [
            "dataset_ref",
            "file_name",
            "sha256",
            "rows",
            "date_col",
            "date_min",
            "date_max",
            "label_like_columns",
            "raw_committed_to_repo",
        ],
    )

    result = {
        "run_id": RUN_ID,
        "decision": (
            "live_source_label_extension_discovery_after_041423_v1="
            "candidates_found_no_target_root_unlock_no_promotion"
        ),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact": sha256_file(BOARD),
        "current_cursor_observed": current_cursor(board_text),
        "queries": SEARCH_QUERIES,
        "download_candidates": list(DOWNLOAD_CANDIDATES.keys()),
        "candidate_count": len(candidate_rows),
        "new_candidate_refs": [
            row["dataset_ref"]
            for row in candidate_rows
            if row["dataset_ref"] != "mafaqbhatti/stock-market-regimes-20002026"
        ],
        "candidate_summary": candidate_rows,
        "file_summary": flat_file_rows,
        "command_results": commands,
        "tmp_root": str(TMP_ROOT),
        "raw_data_committed": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r3_native_subhour_root_present": Path("/tmp/ict-engine-native-subhour-source-label-intake").exists(),
        "r5_recency_extension_root_present": Path("/tmp/ict-engine-source-panel-recency-extension").exists(),
        "r6_owner_export_root_present": Path("/tmp/ict-engine-board-a-r6-owner-export-v1").exists(),
        "r3_native_subhour_root_satisfied": False,
        "r5_recency_extension_root_satisfied": False,
        "r6_owner_export_root_satisfied": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "update_goal": False,
        "blockers": [
            "herding_candidate_has_recency_and_label_like_states_but_single_panel_no_target_symbols_no_MainRegimeV2_cross_market_contract",
            "macro_asset_candidate_has_current_features_but_no_source_owned_regime_labels",
            "us_regimes_candidate_is_explicit_regime_source_but_date_stale_2024",
            "required_target_roots_absent",
        ],
        "next": (
            "Preserve Current Cursor next_action; continue only after source-owned recency/native-subhour rows, "
            "verifier-native R6 controls, owner-export delivery, or explicit approval unlocks a target root."
        ),
    }

    (OUT / "live_source_label_extension_discovery_after_041423_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    report = [
        f"# Live Source Label Extension Discovery After 041423 v1",
        "",
        f"- Run id: `{RUN_ID}`",
        f"- Decision: `{result['decision']}`",
        f"- Current cursor observed: `{result['current_cursor_observed']}`",
        f"- Raw downloaded CSV roots stayed under `{TMP_ROOT}`; raw data committed: `false`.",
        f"- Required roots present after scan: R3=`{result['r3_native_subhour_root_present']}`, "
        f"R5=`{result['r5_recency_extension_root_present']}`, "
        f"R6=`{result['r6_owner_export_root_present']}`.",
        "",
        "## Candidate Readback",
    ]
    for row in candidate_rows:
        report.append(
            "- `{dataset_ref}`: date_max=`{date_max}`, rows=`{rows_scanned}`, "
            "label_like=`{label_like_columns}`, gate=`{gate}`.".format(**row)
        )
    report.extend(
        [
            "",
            "## Result",
            "",
            "No target root was unlocked. The herding dataset is the only new candidate with post-2026-01-30 label-like states, "
            "but it is a single-panel risk-state export without target-symbol source-panel rows, native sub-hour evidence, "
            "R6 owner controls, or a MainRegimeV2 cross-market contract. The macro/asset candidate is a useful feature panel "
            "but has no source-owned regime labels in the downloaded CSV. The older US-regime source is stale to 2024.",
            "",
            "No canonical merge, downstream provider/AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, or execution-tree promotion was run.",
        ]
    )
    (OUT / "live_source_label_extension_discovery_after_041423_v1.md").write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )

    assertions = [
        f"decision={result['decision']}",
        f"accepted_rows_added={result['accepted_rows_added']}",
        f"new_confidence_gate={result['new_confidence_gate']}",
        f"strict_full_objective_achieved={result['strict_full_objective_achieved']}",
        f"update_goal={result['update_goal']}",
        f"raw_data_committed={result['raw_data_committed']}",
        f"r3_native_subhour_root_present={result['r3_native_subhour_root_present']}",
        f"r5_recency_extension_root_present={result['r5_recency_extension_root_present']}",
        f"r6_owner_export_root_present={result['r6_owner_export_root_present']}",
    ]
    (CHECKS / "live_source_label_extension_discovery_after_041423_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
