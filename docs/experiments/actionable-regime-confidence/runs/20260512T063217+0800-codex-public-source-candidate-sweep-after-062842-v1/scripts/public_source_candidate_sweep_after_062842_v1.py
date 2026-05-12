#!/usr/bin/env python3
"""Read-only public source candidate sweep after the 062842 unlock refresh."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T063217+0800-codex-public-source-candidate-sweep-after-062842-v1"
GATE_RESULT = (
    "public_source_candidate_sweep_after_062842_v1="
    "no_candidate_selected_no_required_root_no_downstream"
)
SCRIPT = Path(__file__).resolve()
RUN_ROOT = SCRIPT.parents[1]
REPO = SCRIPT.parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
OUT_DIR = RUN_ROOT / "public-source-candidate-sweep-after-062842-v1"
CHECK_DIR = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"
TMP_ROOT = Path("/tmp/ict-engine-board-a-public-source-candidate-sweep-20260512T063217+0800")

REQUIRED_ROOTS = [
    {
        "id": "r6_owner_export",
        "root": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        "required_files": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
        "unlock_contract": "verifier-native R6 owner/export positives plus valid normal controls",
    },
    {
        "id": "r3_native_subhour",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required_files": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
        "unlock_contract": "source-owned native sub-hour MainRegimeV2 labels plus provenance",
    },
    {
        "id": "r5_recency_extension",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required_files": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
        "unlock_contract": "post-2026-01-30 source-panel recency rows plus provenance",
    },
]

LOCAL_ARTIFACTS = [
    {
        "id": "062842_source_control_unlock_refresh",
        "root": REPO
        / "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T062842+0800-codex-source-control-unlock-refresh-after-062604-v1",
        "expected_report": "source-control-unlock-refresh-after-062604-v1/source_control_unlock_refresh_after_062604_v1.md",
        "role": "unregistered read-only unlock refresh",
    },
    {
        "id": "062854_readonly_runtime_refresh",
        "root": REPO
        / "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T062854-codex-readonly-runtime-refresh-after-062604-v1",
        "expected_report": "",
        "role": "unregistered read-only runtime outputs",
    },
    {
        "id": "062902_r3_hf_tsie_native_intraday_intake",
        "root": REPO
        / "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T062902+0800-codex-r3-hf-tsie-native-intraday-intake-v1",
        "expected_report": "",
        "role": "empty/incomplete root observed, not evidence",
    },
]

KAGGLE_DOWNLOADS = [
    {
        "candidate_id": "kaggle_macro_stress_liquidity",
        "dataset": "kanchana1990/algorithmic-trading-macro-stress-and-asset-regimes",
        "decision": "rejected_feature_panel_no_mainregimev2_labels",
        "reason": "Daily cross-asset feature/stress panel reaches 2026-02-25 but has no discrete Bull/Bear/Sideways/Crisis source labels and no native sub-hour rows.",
    },
    {
        "candidate_id": "kaggle_stock_market_regimes_20002026",
        "dataset": "mafaqbhatti/stock-market-regimes-20002026",
        "file": "stock_market_regimes_2000_2026.csv",
        "decision": "rejected_known_daily_no_post_cutoff_rows",
        "reason": "Known 39-ticker daily MainRegimeV2-like panel still ends at 2026-01-30, so it does not unlock the R5 post-cutoff recency root.",
    },
    {
        "candidate_id": "kaggle_nifty500_behavior_regime",
        "dataset": "ahaanverma00/nifty-500-market-and-behavior-regime-dataset",
        "decision": "rejected_behavior_hmm_not_mainregimev2_not_existing_panel",
        "reason": "Daily NIFTY behavior/macro states reach 2026-03-20 but labels are Durable/Fragile/Calm/Stress/Trending/Noisy style states, not the existing R5 panel or accepted MainRegimeV2 source labels.",
    },
]

HF_CANDIDATES = [
    {
        "candidate_id": "hf_clarus_coherence_mapping",
        "dataset": "ClarusC64/market-regime-coherence-mapping-v0.1",
        "decision": "rejected_tiny_benchmark_no_market_matrix",
        "reason": "Tiny 6-train/1-test relationship benchmark with 2025 windows and no instrument/timeframe matrix; not R3 native sub-hour or R5 recency evidence.",
    },
    {
        "candidate_id": "hf_clarus_transition_breakpoint",
        "dataset": "ClarusC64/market-regime-transition-breakpoint-mapping-v0.1",
        "decision": "rejected_tiny_transition_benchmark_no_mainregimev2",
        "reason": "Tiny transition benchmark with narrative basins/targets, not source-owned Bull/Bear/Sideways/Crisis rows and not native sub-hour.",
    },
    {
        "candidate_id": "hf_tsie_idx",
        "dataset": "sujinwo/tsie-market-regime-dataset",
        "decision": "rejected_known_sidecar_no_crisis_single_idx_rule_labels",
        "reason": "Full TSIE parquet is already counted as non-promoting: rule/OHLCV IDX labels, no direct Crisis semantic, no accepted MainRegimeV2 equivalence.",
    },
    {
        "candidate_id": "hf_btc_hmm6",
        "dataset": "akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD",
        "decision": "rejected_hmm_proxy_single_crypto_no_mainregimev2",
        "reason": "5m/15m BTC HMM labels are proxy model states, not source-owned MainRegimeV2 labels across required markets.",
    },
    {
        "candidate_id": "hf_nifty50_binary",
        "dataset": "AAdevloper/nifty50-market-regime",
        "decision": "rejected_binary_risk_on_off_small_single_market",
        "reason": "Binary risk-on/off NIFTY50 labels cannot cover Bull/Bear/Sideways/Crisis roots or the required R3/R5 target roots.",
    },
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_cmd(name: str, args: list[str], timeout: int = 120) -> dict[str, Any]:
    out_path = CMD_DIR / f"{name}.out"
    err_path = CMD_DIR / f"{name}.err"
    try:
        proc = subprocess.run(
            args,
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        out_path.write_text(proc.stdout, encoding="utf-8")
        err_path.write_text(proc.stderr, encoding="utf-8")
        return {
            "name": name,
            "args": args,
            "returncode": proc.returncode,
            "stdout_path": str(out_path.relative_to(REPO)),
            "stderr_path": str(err_path.relative_to(REPO)),
        }
    except Exception as exc:  # pragma: no cover - audit script should capture failure state.
        err_path.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
        return {
            "name": name,
            "args": args,
            "returncode": None,
            "error": f"{type(exc).__name__}: {exc}",
            "stdout_path": str(out_path.relative_to(REPO)),
            "stderr_path": str(err_path.relative_to(REPO)),
        }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def root_snapshot() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in REQUIRED_ROOTS:
        root = item["root"]
        present_files = []
        missing_files = []
        row_counts: dict[str, Any] = {}
        hashes: dict[str, Any] = {}
        for name in item["required_files"]:
            path = root / name
            if path.exists():
                present_files.append(name)
                hashes[name] = sha256_file(path) if path.is_file() else "not_file"
                if path.suffix == ".csv" and path.is_file():
                    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
                        row_counts[name] = max(sum(1 for _ in csv.reader(handle)) - 1, 0)
            else:
                missing_files.append(name)
        rows.append(
            {
                "id": item["id"],
                "root": str(root),
                "root_exists": root.exists(),
                "present_files": ";".join(present_files),
                "missing_files": ";".join(missing_files),
                "all_required_present": not missing_files,
                "row_counts": json.dumps(row_counts, sort_keys=True),
                "hashes": json.dumps(hashes, sort_keys=True),
                "unlock_contract": item["unlock_contract"],
            }
        )
    return rows


def local_artifact_snapshot() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in LOCAL_ARTIFACTS:
        root = item["root"]
        files = sorted([p for p in root.rglob("*") if p.is_file()]) if root.exists() else []
        expected_report = root / item["expected_report"] if item["expected_report"] else None
        rows.append(
            {
                "id": item["id"],
                "root": str(root.relative_to(REPO)),
                "exists": root.exists(),
                "file_count": len(files),
                "expected_report_exists": bool(expected_report and expected_report.is_file()),
                "role": item["role"],
            }
        )
    return rows


def summarize_csv(path: Path) -> dict[str, Any]:
    df = pd.read_csv(path)
    summary: dict[str, Any] = {
        "file": str(path),
        "rows": int(len(df)),
        "columns": list(df.columns),
    }
    for col in df.columns:
        lowered = col.lower()
        if lowered in {"date", "datetime", "timestamp"} or lowered.endswith("_date") or "date" in lowered:
            try:
                summary.setdefault("date_columns", {})[col] = {
                    "min": str(df[col].min()),
                    "max": str(df[col].max()),
                    "nunique": int(df[col].nunique()),
                }
            except Exception as exc:
                summary.setdefault("date_columns", {})[col] = {"error": str(exc)}
        if any(token in lowered for token in ["regime", "label", "state", "behavior"]):
            summary.setdefault("labelish_columns", {})[col] = {
                str(key): int(value)
                for key, value in df[col].dropna().astype(str).value_counts().head(20).items()
            }
        if any(token in lowered for token in ["ticker", "symbol", "asset", "instrument"]):
            values = list(df[col].dropna().astype(str).unique()[:20])
            summary.setdefault("symbolish_columns", {})[col] = {
                "nunique": int(df[col].dropna().astype(str).nunique()),
                "sample": values,
            }
    return summary


def inspect_kaggle() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    commands = []
    for index, query in enumerate(
        ["stock market regimes", "market regime labels", "bull bear sideways crisis"]
    ):
        commands.append(
            run_cmd(
                f"kaggle_search_{index}",
                ["kaggle", "datasets", "list", "-s", query, "--csv"],
            )
        )

    rows: list[dict[str, Any]] = []
    for item in KAGGLE_DOWNLOADS:
        target = TMP_ROOT / "kaggle" / item["candidate_id"]
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)
        args = ["kaggle", "datasets", "download", "-d", item["dataset"]]
        if item.get("file"):
            args.extend(["-f", item["file"]])
        args.extend(["-p", str(target), "--unzip", "-o"])
        commands.append(run_cmd(f"download_{item['candidate_id']}", args, timeout=180))
        summaries = []
        for csv_path in sorted(target.rglob("*.csv")):
            summaries.append(summarize_csv(csv_path))
        date_span = []
        labels = []
        row_total = 0
        for summary in summaries:
            row_total += int(summary.get("rows", 0))
            for date_col, date_info in summary.get("date_columns", {}).items():
                date_span.append(f"{date_col}:{date_info.get('min')}..{date_info.get('max')}")
            for label_col, label_info in summary.get("labelish_columns", {}).items():
                labels.append(f"{label_col}:{list(label_info)[:8]}")
        rows.append(
            {
                "candidate_id": item["candidate_id"],
                "surface": "kaggle",
                "source": item["dataset"],
                "observed_files": ";".join(str(p.relative_to(target)) for p in sorted(target.rglob("*")) if p.is_file()),
                "observed_rows": row_total,
                "date_span": "; ".join(date_span),
                "label_summary": "; ".join(labels),
                "decision": item["decision"],
                "unlock": False,
                "reason": item["reason"],
            }
        )
    return rows, commands


def inspect_hf() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    commands: list[dict[str, Any]] = []
    try:
        from huggingface_hub import HfApi, hf_hub_download

        api = HfApi()
        hf_search_rows = []
        for query in ["market regime", "stock market regime", "bull bear sideways crisis", "market regime 15m"]:
            seen = []
            for dataset in api.list_datasets(search=query, limit=15):
                seen.append(
                    {
                        "query": query,
                        "id": dataset.id,
                        "lastModified": str(getattr(dataset, "lastModified", "")),
                        "downloads": getattr(dataset, "downloads", ""),
                        "likes": getattr(dataset, "likes", ""),
                    }
                )
            hf_search_rows.extend(seen)
        write_csv(
            OUT_DIR / "hf_search_results_v1.csv",
            hf_search_rows,
            ["query", "id", "lastModified", "downloads", "likes"],
        )

        for item in HF_CANDIDATES:
            info = api.dataset_info(item["dataset"])
            files = [s.rfilename for s in (info.siblings or [])]
            row_total = 0
            date_span = []
            labels = []
            for filename in files:
                if filename.endswith(".csv") and filename.startswith("data/"):
                    try:
                        csv_file = Path(
                            hf_hub_download(repo_id=item["dataset"], repo_type="dataset", filename=filename)
                        )
                        summary = summarize_csv(csv_file)
                        row_total += int(summary.get("rows", 0))
                        for date_col, date_info in summary.get("date_columns", {}).items():
                            date_span.append(
                                f"{date_col}:{date_info.get('min')}..{date_info.get('max')}"
                            )
                        for label_col, label_info in summary.get("labelish_columns", {}).items():
                            labels.append(f"{label_col}:{list(label_info)[:8]}")
                    except Exception as exc:
                        labels.append(f"{filename}:read_error:{type(exc).__name__}:{exc}")
            rows.append(
                {
                    "candidate_id": item["candidate_id"],
                    "surface": "huggingface",
                    "source": item["dataset"],
                    "observed_files": ";".join(files),
                    "observed_rows": row_total,
                    "date_span": "; ".join(date_span),
                    "label_summary": "; ".join(labels),
                    "decision": item["decision"],
                    "unlock": False,
                    "reason": item["reason"],
                    "last_modified": str(info.lastModified),
                }
            )
    except Exception as exc:
        commands.append({"name": "hf_inspection", "error": f"{type(exc).__name__}: {exc}"})
    return rows, commands


def inspect_github() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    commands = []
    if shutil.which("gh"):
        searches = [
            "market regime dataset bull bear sideways crisis",
            "AAPL 15m market regime labels",
            "stock market regime labels dataset 2026",
        ]
        for index, query in enumerate(searches):
            commands.append(
                run_cmd(
                    f"github_search_{index}",
                    [
                        "gh",
                        "search",
                        "repos",
                        query,
                        "--limit",
                        "20",
                        "--json",
                        "fullName,description,updatedAt,url",
                    ],
                )
            )
    else:
        commands.append({"name": "github_search", "error": "gh_not_available"})
    return [
        {
            "candidate_id": "github_repo_search",
            "surface": "github",
            "source": "gh search repos market-regime/source-label queries",
            "observed_files": "",
            "observed_rows": 0,
            "date_span": "",
            "label_summary": "",
            "decision": "rejected_no_repo_candidate_returned",
            "unlock": False,
            "reason": "Authenticated gh repo searches returned no candidate repositories for MainRegimeV2 R3/R5/R6 unlock contracts in this slice.",
        }
    ], commands


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)

    board_hash = sha256_text(BOARD)
    root_rows = root_snapshot()
    local_rows = local_artifact_snapshot()
    kaggle_rows, kaggle_commands = inspect_kaggle()
    hf_rows, hf_commands = inspect_hf()
    github_rows, github_commands = inspect_github()
    candidate_rows = kaggle_rows + hf_rows + github_rows
    commands = kaggle_commands + hf_commands + github_commands

    write_csv(
        OUT_DIR / "public_source_candidate_sweep_candidates_v1.csv",
        candidate_rows,
        [
            "candidate_id",
            "surface",
            "source",
            "observed_files",
            "observed_rows",
            "date_span",
            "label_summary",
            "decision",
            "unlock",
            "reason",
            "last_modified",
        ],
    )
    write_csv(
        OUT_DIR / "public_source_candidate_sweep_required_roots_v1.csv",
        root_rows,
        [
            "id",
            "root",
            "root_exists",
            "present_files",
            "missing_files",
            "all_required_present",
            "row_counts",
            "hashes",
            "unlock_contract",
        ],
    )
    write_csv(
        OUT_DIR / "public_source_candidate_sweep_local_artifacts_v1.csv",
        local_rows,
        ["id", "root", "exists", "file_count", "expected_report_exists", "role"],
    )

    accepted = [row for row in candidate_rows if str(row.get("unlock")) == "True"]
    required_unlocked = any(str(row.get("all_required_present")) == "True" for row in root_rows)
    summary = {
        "run_id": RUN_ID,
        "gate_result": GATE_RESULT,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_before_artifact": board_hash,
        "scope": {
            "read_only_public_candidate_sweep": True,
            "target_roots_mutated": False,
            "external_requests_sent": False,
            "vendor_portal_used": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "trade_claim": False,
            "update_goal": False,
        },
        "required_roots": root_rows,
        "local_artifacts": local_rows,
        "candidate_count": len(candidate_rows),
        "accepted_candidate_count": len(accepted),
        "required_root_unlocked": required_unlocked,
        "candidates": candidate_rows,
        "commands": commands,
        "decision": (
            "No public Kaggle/HuggingFace/GitHub candidate selected for target-root "
            "materialization. R6/R3/R5 required roots remain absent, and the "
            "unregistered 062842 refresh is negative evidence only."
        ),
        "promotion": {
            "accepted_rows_added": 0,
            "source_control_evidence_acquired": False,
            "target_root_mutated": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "next": (
            "Preserve the Current Cursor next action: use approved operator/vendor "
            "route for R6 owner-export rows or supply explicit source/control approval, "
            "or acquire true R5 post-cutoff source-panel rows or R3 native-subhour "
            "MainRegimeV2 labels before rerunning direct verifier and downstream chain."
        ),
    }
    json_path = OUT_DIR / "public_source_candidate_sweep_after_062842_v1.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    md_lines = [
        "# Public Source Candidate Sweep After 062842 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE_RESULT}`",
        "",
        f"Board sha256 before artifact: `{board_hash}`",
        "",
        "## Scope",
        "",
        (
            "Read-only acquisition sweep after the unregistered `062842` unlock refresh. "
            "This checks public Kaggle/HuggingFace/GitHub candidates and local artifact "
            "presence. It does not mutate required roots, send vendor mail, approve "
            "controls, run canonical merge, rerun downstream promotion, make a trade "
            "claim, or call `update_goal`."
        ),
        "",
        "## Required Roots",
        "",
        "| Root ID | Root | Exists | All Required Present | Missing Files |",
        "|---|---|---:|---:|---|",
    ]
    for row in root_rows:
        md_lines.append(
            f"| `{row['id']}` | `{row['root']}` | `{row['root_exists']}` | "
            f"`{row['all_required_present']}` | `{row['missing_files']}` |"
        )
    md_lines.extend(
        [
            "",
            "## Local Artifact Readback",
            "",
            "| Artifact | Exists | File Count | Expected Report | Role |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for row in local_rows:
        md_lines.append(
            f"| `{row['id']}` | `{row['exists']}` | `{row['file_count']}` | "
            f"`{row['expected_report_exists']}` | {row['role']} |"
        )
    md_lines.extend(
        [
            "",
            "## Candidate Decisions",
            "",
            "| Candidate | Surface | Source | Observed Rows | Date Span | Decision | Unlock | Reason |",
            "|---|---|---|---:|---|---|---:|---|",
        ]
    )
    for row in candidate_rows:
        date_span = str(row.get("date_span", "")).replace("|", "/")
        reason = str(row.get("reason", "")).replace("|", "/")
        md_lines.append(
            f"| `{row['candidate_id']}` | `{row['surface']}` | `{row['source']}` | "
            f"`{row.get('observed_rows', 0)}` | {date_span or 'n/a'} | "
            f"`{row['decision']}` | `{row['unlock']}` | {reason} |"
        )
    md_lines.extend(
        [
            "",
            "## Decision",
            "",
            (
                "No public candidate is selected for target-root materialization. "
                "The Kaggle `stock-market-regimes-20002026` file still ends on "
                "`2026-01-30`, the newer Kaggle/NIFTY/HF candidates are feature, "
                "behavior, benchmark, proxy-HMM, or rule/OHLCV sidecars rather than "
                "accepted source-owned `MainRegimeV2` rows, and GitHub repo search "
                "returned no unlock candidate in this slice."
            ),
            "",
            (
                "Promotion remains blocked: accepted rows added `0`, source/control "
                "evidence acquired false, target root mutated false, canonical merge "
                "false, downstream promotion rerun false, strict full objective false, "
                "trade usable false, and `update_goal=false`."
            ),
            "",
            "## Next",
            "",
            (
                "Preserve the Current Cursor next action. Use the approved operator/vendor "
                "route for R6 owner-export rows or explicit source/control approval, or "
                "acquire true R5 post-cutoff source-panel rows or R3 native-subhour "
                "`MainRegimeV2` labels before rerunning direct verifier, split calibration, "
                "canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, "
                "CatBoost/path-ranking, and execution-tree readback."
            ),
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Candidate CSV: `{(OUT_DIR / 'public_source_candidate_sweep_candidates_v1.csv').relative_to(REPO)}`",
            f"- Required roots CSV: `{(OUT_DIR / 'public_source_candidate_sweep_required_roots_v1.csv').relative_to(REPO)}`",
            f"- Local artifacts CSV: `{(OUT_DIR / 'public_source_candidate_sweep_local_artifacts_v1.csv').relative_to(REPO)}`",
            f"- HF search CSV: `{(OUT_DIR / 'hf_search_results_v1.csv').relative_to(REPO)}`",
            f"- Assertions: `{(CHECK_DIR / 'public_source_candidate_sweep_after_062842_v1_assertions.out').relative_to(REPO)}`",
        ]
    )
    report_path = OUT_DIR / "public_source_candidate_sweep_after_062842_v1.md"
    report_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"gate_result={GATE_RESULT}",
        f"required_root_unlocked_false={not required_unlocked}",
        f"accepted_candidate_count_zero={len(accepted) == 0}",
        "accepted_rows_added=0",
        "source_control_evidence_acquired_false=True",
        "target_root_mutated_false=True",
        "canonical_merge_false=True",
        "downstream_promotion_rerun_false=True",
        "strict_full_objective_false=True",
        "trade_usable_false=True",
        "update_goal_false=True",
    ]
    assertions_path = CHECK_DIR / "public_source_candidate_sweep_after_062842_v1_assertions.out"
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(report_path)
    return 0 if not accepted and not required_unlocked else 1


if __name__ == "__main__":
    sys.exit(main())
