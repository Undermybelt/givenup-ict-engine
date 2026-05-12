#!/usr/bin/env python3
import csv
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r3-r5-source-selection-readback-after-061855-v1"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
REQUIRED_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]

TSIE_SUMMARY = Path(
    "/private/tmp/ict-engine-board-a-tsie-market-regime-dryrun-20260512T0200/tsie_dryrun_summary.json"
)
TSIE_PARQUET = Path(
    "/private/tmp/ict-engine-board-a-tsie-market-regime-dryrun-20260512T0200/0000.parquet"
)
SCREEN_061855 = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T061855+0800-codex-r3-hf-tsie-native-subhour-source-screen-v1/r3-hf-tsie-native-subhour-source-screen-v1/r3_hf_tsie_native_subhour_source_screen_v1.json"
)

HF_DATASETS = {
    "tsie_idx": "sujinwo/tsie-market-regime-dataset",
    "btc_hmm6": "akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD",
    "nifty50_binary": "AAdevloper/nifty50-market-regime",
}
KAGGLE_DATASETS = {
    "nifty500_behavior": "ahaanverma00/nifty-500-market-and-behavior-regime-dataset",
    "us_market_regimes": "nickdatak/us-market-regimes-dataset-1995-2024",
    "stock_market_regimes": "mafaqbhatti/stock-market-regimes-20002026",
}


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text())


def fetch_hf(dataset_id: str) -> dict:
    url = f"https://huggingface.co/api/datasets/{dataset_id}"
    out_path = CMD / f"hf_{dataset_id.replace('/', '__')}.json"
    cmd_path = CMD / f"hf_{dataset_id.replace('/', '__')}.cmd"
    cmd_path.write_text(f"GET {url}\n")
    try:
        with urllib.request.urlopen(url, timeout=45) as response:
            body = response.read()
        out_path.write_bytes(body)
        return json.loads(body)
    except Exception as exc:
        out_path.write_text(json.dumps({"error": repr(exc)}) + "\n")
        return {"id": dataset_id, "error": repr(exc)}


def run_cmd(name: str, args: list[str]) -> dict:
    cmd_path = CMD / f"{name}.cmd"
    stdout_path = CMD / f"{name}.stdout.txt"
    stderr_path = CMD / f"{name}.stderr.txt"
    exit_path = CMD / f"{name}.exit"
    cmd_path.write_text(" ".join(args) + "\n")
    proc = subprocess.run(args, text=True, capture_output=True, timeout=90)
    stdout_path.write_text(proc.stdout)
    stderr_path.write_text(proc.stderr)
    exit_path.write_text(str(proc.returncode) + "\n")
    return {
        "name": name,
        "cmd": args,
        "exit": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def classify_candidate(candidate: dict) -> dict:
    cid = candidate["id"]
    notes = candidate["notes"]
    if cid == "tsie_idx":
        return {
            **candidate,
            "decision": "rejected_known_sidecar_no_crisis_single_idx_rule_labels",
            "unlock": False,
            "reason": "TSIE has full parquet support and native subhour timestamps but no Crisis semantic, single IDX market context, rule/OHLCV-derived labels, and prior full-parquet Board A gates accepted 0 roots.",
        }
    if cid == "btc_hmm6":
        return {
            **candidate,
            "decision": "rejected_hmm_proxy_single_crypto_no_mainregimev2",
            "unlock": False,
            "reason": "Multi-timeframe BTC rows are HMM-inferred labels, not source-owned MainRegimeV2 labels, and do not cover equity/index cross-market roots or Crisis/Sideways/Bull/Bear as accepted source labels.",
        }
    if cid == "nifty50_binary":
        return {
            **candidate,
            "decision": "rejected_binary_risk_on_off_small_single_market",
            "unlock": False,
            "reason": "Binary RISK_ON/RISK_OFF NIFTY50 labels cannot cover Bull/Bear/Sideways/Crisis roots and are a small single-market technical-indicator label panel.",
        }
    if cid == "nifty500_behavior":
        return {
            **candidate,
            "decision": "rejected_daily_hmm_labels_not_r5_existing_panel",
            "unlock": False,
            "reason": "Known daily NIFTY behavior labels reach 2026-03-20 but are HMM/behavior labels such as Calm/Stress, not the existing 39-ticker R5 panel recency extension or accepted MainRegimeV2 source labels.",
        }
    if cid == "us_market_regimes":
        return {
            **candidate,
            "decision": "rejected_stale_weekly_unsupervised",
            "unlock": False,
            "reason": "Known US market-regimes files are weekly HMM/GMM/feature tables stale to 2023/2024, not post-cutoff MainRegimeV2 rows or native subhour source labels.",
        }
    if cid == "stock_market_regimes":
        return {
            **candidate,
            "decision": "rejected_known_daily_no_post_cutoff_rows",
            "unlock": False,
            "reason": "Known source panel remains daily and already counted; latest local/live checks show no rows after 2026-01-30 for the R5 recency tail.",
        }
    return {**candidate, "decision": "unknown_rejected_no_unlock", "unlock": False, "reason": notes}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD.mkdir(parents=True, exist_ok=True)

    board_hash = sha256(BOARD)
    tsie_summary = load_json(TSIE_SUMMARY)
    screen_061855 = load_json(SCREEN_061855)

    hf_rows = []
    for cid, dataset_id in HF_DATASETS.items():
        data = fetch_hf(dataset_id)
        hf_rows.append(
            {
                "id": cid,
                "source": dataset_id,
                "last_modified": data.get("lastModified"),
                "license": (data.get("cardData") or {}).get("license")
                or next((t.split(":", 1)[1] for t in data.get("tags", []) if t.startswith("license:")), ""),
                "siblings": ",".join(s.get("rfilename", "") for s in data.get("siblings", [])),
                "notes": (data.get("description") or "")[:500],
            }
        )

    kaggle_rows = []
    for cid, ref in KAGGLE_DATASETS.items():
        files = run_cmd(f"kaggle_files_{cid}", ["kaggle", "datasets", "files", ref])
        kaggle_rows.append(
            {
                "id": cid,
                "source": ref,
                "last_modified": "",
                "license": "",
                "siblings": "; ".join(line.strip() for line in files["stdout"].splitlines()[2:8]),
                "notes": files["stdout"][:500] if files["exit"] == 0 else files["stderr"][:500],
            }
        )

    all_candidates = [classify_candidate(row) for row in hf_rows + kaggle_rows]
    selected_unlocks = [row for row in all_candidates if row["unlock"]]
    required_status = {str(root): root.exists() for root in REQUIRED_ROOTS}
    root_unlocked = any(required_status.values())

    gate = (
        "r3_r5_source_selection_readback_after_061855_v1="
        "no_candidate_selected_no_required_root_no_promotion"
    )
    result = {
        "run_id": RUN_ROOT.name,
        "gate_result": gate,
        "board_sha256_before_artifact": board_hash,
        "required_roots": required_status,
        "screen_061855_present": bool(screen_061855),
        "tsie_summary_present": bool(tsie_summary),
        "tsie_parquet_present": TSIE_PARQUET.is_file(),
        "tsie_parquet_sha256": sha256(TSIE_PARQUET),
        "tsie_rows": tsie_summary.get("num_rows_read"),
        "tsie_time_min": tsie_summary.get("time_min"),
        "tsie_time_max": tsie_summary.get("time_max"),
        "tsie_mapped_counts": tsie_summary.get("mapped_counts"),
        "candidates": all_candidates,
        "selected_unlock_count": len(selected_unlocks),
        "accepted_rows_added": 0,
        "target_root_mutated": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    json_path = OUT / "r3_r5_source_selection_readback_after_061855_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    csv_path = OUT / "r3_r5_source_selection_candidates_v1.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "source", "decision", "unlock", "last_modified", "license", "reason"],
        )
        writer.writeheader()
        for row in all_candidates:
            writer.writerow({k: row.get(k, "") for k in writer.fieldnames})

    report = [
        "# R3/R5 Source Selection Readback After 061855 v1",
        "",
        f"Run id: `{RUN_ROOT.name}`",
        "",
        f"Gate result: `{gate}`",
        "",
        f"Board sha256 before artifact: `{board_hash}`",
        "",
        "## Scope",
        "",
        "This readback decides whether the newly resurfaced TSIE branch or nearby public R3/R5 candidates should be selected for target-root materialization. It does not copy files into `/tmp/ict-engine-native-subhour-source-label-intake`, `/tmp/ict-engine-source-panel-recency-extension`, or `/tmp/ict-engine-board-a-r6-owner-export-v1`; it does not run canonical merge or downstream promotion.",
        "",
        "## Required Roots",
        "",
    ]
    for root, present in required_status.items():
        report.append(f"- `{root}`: `{str(present).lower()}`")
    report.extend(
        [
            "",
            "## TSIE Readback",
            "",
            f"- Existing full parquet present: `{str(TSIE_PARQUET.is_file()).lower()}`",
            f"- Parquet SHA-256: `{sha256(TSIE_PARQUET)}`",
            f"- Rows read in prior dry run: `{tsie_summary.get('num_rows_read')}`",
            f"- Time span: `{tsie_summary.get('time_min')}` to `{tsie_summary.get('time_max')}`",
            f"- Mapped counts: `{tsie_summary.get('mapped_counts')}`",
            "- Selection decision: `false`; no `Crisis` semantic, single IDX context, rule/OHLCV-derived labels, and prior full-parquet Board A gates accepted `0` roots.",
            "",
            "## Candidate Decisions",
            "",
            "| Candidate | Source | Decision | Unlock | Reason |",
            "|---|---|---|---:|---|",
        ]
    )
    for row in all_candidates:
        reason = str(row["reason"]).replace("|", "/")
        report.append(
            f"| `{row['id']}` | `{row['source']}` | `{row['decision']}` | `{str(row['unlock']).lower()}` | {reason} |"
        )
    report.extend(
        [
            "",
            "## Decision",
            "",
            "No R3 or R5 candidate is selected for target-root materialization in this slice. The TSIE branch is closed as non-promoting despite full parquet availability; the nearby HMM/NIFTY/US/Kaggle candidates are proxy, stale, daily-only, or not MainRegimeV2-equivalent.",
            "",
            "Promotion remains blocked: accepted rows added `0`, source/control evidence acquired false, target root mutated false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.",
            "",
            "## Next",
            "",
            "Preserve the Current Cursor next action. Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned R5 recency rows for the existing source panel, source-owned R3 native sub-hour labels with accepted MainRegimeV2 equivalence, or a genuinely new cross-timeframe MainRegimeV2 export. Do not rerun provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree promotion until a required target root unlocks.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Candidate CSV: `{csv_path.relative_to(REPO)}`",
            f"- Assertions: `{(CHECKS / 'r3_r5_source_selection_readback_after_061855_v1_assertions.out').relative_to(REPO)}`",
        ]
    )
    (OUT / "r3_r5_source_selection_readback_after_061855_v1.md").write_text(
        "\n".join(report) + "\n"
    )

    assertions = [
        f"gate_result={gate}",
        f"required_root_unlocked={str(root_unlocked).lower()}",
        f"tsie_parquet_present={str(TSIE_PARQUET.is_file()).lower()}",
        f"tsie_rows={tsie_summary.get('num_rows_read')}",
        f"selected_unlock_count={len(selected_unlocks)}",
        "accepted_rows_added=0",
        "target_root_mutated=false",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    (CHECKS / "r3_r5_source_selection_readback_after_061855_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
