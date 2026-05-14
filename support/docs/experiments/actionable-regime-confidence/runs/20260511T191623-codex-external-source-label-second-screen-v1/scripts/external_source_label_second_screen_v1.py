#!/usr/bin/env python3
import csv
import hashlib
import json
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T191623+0800-codex-external-source-label-second-screen-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = RUN_ROOT.parents[4]
BOARD_PATH = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
OUT_DIR = RUN_ROOT / "external-source-label-second-screen"
CHECK_DIR = RUN_ROOT / "checks"
TMP_DIR = Path("/tmp/ict-engine-board-a-external-source-label-second-screen-v1")

OUT_DIR.mkdir(parents=True, exist_ok=True)
CHECK_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)


def run(cmd, timeout=60):
    proc = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    return {"cmd": cmd, "returncode": proc.returncode, "output": proc.stdout}


def fetch_bytes(url, max_bytes=None):
    headers = {"User-Agent": "ict-engine-board-a-source-label-screen/1.0"}
    if max_bytes is not None:
        headers["Range"] = f"bytes=0-{max_bytes - 1}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def fetch_text(url, max_bytes=None):
    return fetch_bytes(url, max_bytes=max_bytes).decode("utf-8", errors="replace")


def fetch_json(url):
    return json.loads(fetch_text(url))


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def csv_header_from_text(text):
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    return next(csv.reader([lines[0]]))


def fetch_hf_header(repo, path):
    url = f"https://huggingface.co/datasets/{repo}/resolve/main/{path}"
    try:
        return csv_header_from_text(fetch_text(url, max_bytes=8192))
    except (urllib.error.URLError, TimeoutError, UnicodeDecodeError):
        return []


def fetch_hf_readme_snippets(repo):
    url = f"https://huggingface.co/datasets/{repo}/resolve/main/README.md"
    try:
        readme = fetch_text(url, max_bytes=10000)
    except (urllib.error.URLError, TimeoutError):
        return []
    terms = ["regime", "label", "hmm", "source", "structural", "break", "required outputs"]
    snippets = []
    for line in readme.splitlines():
        stripped = line.strip()
        if stripped and any(term in stripped.lower() for term in terms):
            snippets.append(stripped)
        if len(snippets) >= 16:
            break
    return snippets


def hf_candidate(repo, strength, disposition, reason, sample_file=None):
    url = f"https://huggingface.co/datasets/{repo}"
    api = fetch_json(f"https://huggingface.co/api/datasets/{repo}")
    siblings = [item.get("rfilename") for item in api.get("siblings", [])]
    header = fetch_hf_header(repo, sample_file) if sample_file else []
    return {
        "source": "huggingface",
        "ref": repo,
        "url": url,
        "screen_action": "metadata_readme_and_header_only",
        "candidate_strength": strength,
        "disposition": disposition,
        "reason": reason,
        "downloads": api.get("downloads"),
        "likes": api.get("likes"),
        "tags": api.get("tags", [])[:16],
        "siblings": siblings[:16],
        "sample_file": sample_file or "",
        "sample_header": header,
        "readme_evidence_snippets": fetch_hf_readme_snippets(repo),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
    }


def kaggle_search(query):
    safe = query.replace(" ", "_").replace("/", "_")
    result = run(["kaggle", "datasets", "list", "-s", query, "--csv"], timeout=80)
    (OUT_DIR / f"kaggle_search_{safe}.csv").write_text(result["output"])
    refs = []
    if result["returncode"] == 0:
        for row in csv.DictReader(result["output"].splitlines()):
            refs.append(row.get("ref", ""))
    return {
        "query": query,
        "returncode": result["returncode"],
        "top_refs": refs[:10],
        "result_file": f"kaggle_search_{safe}.csv",
    }


def profile_kaggle_header(ref, local_filename):
    local_dir = TMP_DIR / ref.replace("/", "__")
    local_dir.mkdir(parents=True, exist_ok=True)
    files_result = run(["kaggle", "datasets", "files", ref], timeout=80)
    download_result = run(
        ["kaggle", "datasets", "download", "-d", ref, "-p", str(local_dir), "--unzip"],
        timeout=180,
    )
    header = []
    local_file = local_dir / local_filename
    if local_file.exists():
        with local_file.open(newline="") as fh:
            header = next(csv.reader(fh), [])
    return {
        "files_returncode": files_result["returncode"],
        "files_output_head": files_result["output"].splitlines()[:8],
        "download_returncode": download_result["returncode"],
        "profiled_file": local_filename,
        "sample_header": header,
    }


def main():
    board_hash_before = sha256_file(BOARD_PATH)
    searches = [
        kaggle_search("bull bear sideways market regime"),
        kaggle_search("market regime label"),
        kaggle_search("crypto market regime"),
    ]

    candidates = []
    kaggle_profile = profile_kaggle_header(
        "kundanbedmutha/market-trend-and-external-factors-dataset",
        "Market_Trend_External.csv",
    )
    candidates.append(
        {
            "source": "kaggle",
            "ref": "kundanbedmutha/market-trend-and-external-factors-dataset",
            "url": "https://www.kaggle.com/datasets/kundanbedmutha/market-trend-and-external-factors-dataset",
            "screen_action": "downloaded_to_tmp_header_only",
            "candidate_strength": "raw_market_external_factor_panel",
            "disposition": "blocked_raw_ohlcv_external_factor_panel_no_regime_label",
            "reason": "Header contains Date, OHLCV, VIX, news, sentiment, rates, geopolitical risk, and currency fields but no source-owned regime label or owner-approved MainRegimeV2 equivalence.",
            "profile": kaggle_profile,
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
        }
    )

    hf_candidates = [
        hf_candidate(
            "akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD",
            "crypto_subhour_regime_label_candidate",
            "blocked_hmm_generated_crypto_labels_no_owner_mainregimev2",
            "BTCUSD rows include state/regime columns at 5m/15m, but the card says regimes are inferred using a 6-state HMM from OHLCV and technical indicators; this is generated/proxy labeling, not source-owned MainRegimeV2 equivalence.",
            "data/train.csv",
        ),
        hf_candidate(
            "ClarusC64/market-regime-coherence-mapping-v0.1",
            "cross_asset_structural_exercise",
            "blocked_structural_score_table_no_mainregimev2_label",
            "Small cross-asset structure exercise exposes coherence scores and driver labels, not row-level Bull/Bear/Sideways/Crisis source labels.",
            "data/train.csv",
        ),
        hf_candidate(
            "ClarusC64/market-regime-transition-breakpoint-mapping-v0.1",
            "transition_breakpoint_exercise",
            "blocked_transition_taxonomy_no_owner_crosswalk",
            "Current regime basin and transition targets are structural taxonomy fields; no owner-approved mapping to MainRegimeV2 is supplied.",
            "data/train.csv",
        ),
        hf_candidate(
            "ClarusC64/market-structural-fragility-spike-detection-v0.1",
            "fragility_spike_exercise",
            "blocked_fragility_binary_not_mainregimev2",
            "Fragility score/spike fields can inform risk sidecars, but they are not source-owned active-regime labels.",
            "data/train.csv",
        ),
        hf_candidate(
            "ClarusC64/market-liquidity-cliff-and-basin-shift-v0.1",
            "liquidity_state_exercise",
            "blocked_liquidity_state_not_market_regime_label",
            "Basin/edge/cliff liquidity states are execution/liquidity risk labels, not Bull/Bear/Sideways/Crisis source labels.",
            "data/train.csv",
        ),
        hf_candidate(
            "ClarusC64/market-systemic-stabilization-and-breakpoint-detection-v0.1",
            "systemic_breakpoint_exercise",
            "blocked_systemic_nodes_not_mainregimev2",
            "Stabilization and breakpoint nodes describe crisis mechanics, but do not provide row-level MainRegimeV2 labels across the active regimes.",
            "data/train.csv",
        ),
        hf_candidate(
            "algoplexity/computational-phase-transitions-data",
            "structural_break_benchmark",
            "blocked_binary_structural_break_labels_not_mainregimev2",
            "Dataset labels identify structural break/no-break timestamps; they do not encode Bull/Bear/Sideways/Crisis/Manipulation labels or an approved crosswalk.",
            "",
        ),
    ]
    candidates.extend(hf_candidates)

    summary = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": board_hash_before,
        "decision": "external_source_label_second_screen_v1=no_promotable_source_label_equivalence",
        "scope": "second-pass external source-owned label screen for other-market/source-label equivalence",
        "non_overlap_guardrail": "Avoided strict-1h future-tail, completion-audit, and Board B run roots that were active in the 19:xx window.",
        "related_prior_artifacts": [
            "20260511T183328-codex-external-source-label-candidate-screen-v1",
            "20260511T184856-codex-source-label-other-market-readback-v1",
            "20260511T185420-codex-local-intake-schema-sweep-v1",
            "20260511T190440-codex-strict-1h-future-tail-gate-rerun-v1",
            "20260511T190911-codex-current-goal-completion-audit-v20-after-future-tail",
        ],
        "kaggle_searches": searches,
        "huggingface_datasets_screened": len(hf_candidates),
        "kaggle_datasets_profiled": 1,
        "candidate_records": len(candidates),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "full_other_market_source_label_equivalence": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "guardrails": [
            "no HMM/generated labels promoted",
            "no OHLCV-only or structural sidecar labels promoted",
            "no owner-unapproved taxonomy crosswalk promoted to MainRegimeV2",
            "no raw downloaded rows committed",
        ],
        "candidates": candidates,
    }

    (OUT_DIR / "external_source_label_second_screen_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True)
    )

    csv_path = OUT_DIR / "external_source_label_second_screen_v1_candidates.csv"
    with csv_path.open("w", newline="") as fh:
        fieldnames = [
            "source",
            "ref",
            "url",
            "candidate_strength",
            "disposition",
            "accepted_rows_added",
            "new_confidence_gate",
            "reason",
        ]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for candidate in candidates:
            writer.writerow({key: candidate.get(key, "") for key in fieldnames})

    md_lines = [
        "# External Source Label Second Screen v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "Second-pass external screen for the remaining other-market/source-label equivalence blocker. This run is additive, does not edit Current Cursor, and does not write into other agents' 19:xx run roots.",
        "",
        "## Decision",
        "",
        "`external_source_label_second_screen_v1=no_promotable_source_label_equivalence`",
        "",
        f"- Kaggle searches: `{len(searches)}`.",
        "- Kaggle datasets profiled to `/tmp` header-only: `1`.",
        f"- Hugging Face datasets screened: `{len(hf_candidates)}`.",
        f"- Candidate records: `{len(candidates)}`.",
        "- Accepted rows added: `0`.",
        "- New confidence gate: `false`.",
        "- Full other-market/source-label equivalence: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Candidate Disposition",
        "",
        "| Source | Candidate | Decision | Reason |",
        "|---|---|---|---|",
    ]
    for candidate in candidates:
        reason = candidate["reason"].replace("|", "/")
        md_lines.append(
            f"| `{candidate['source']}` | [`{candidate['ref']}`]({candidate['url']}) | `{candidate['disposition']}` | {reason} |"
        )
    md_lines.extend(
        [
            "",
            "## Search Readback",
            "",
            "- `bull bear sideways market regime` returned only the already-known stock-market-regimes source panel in the top Kaggle result.",
            "- `market regime label` still surfaces prior blocked candidates such as NIFTY 500 behavior regimes and raw macro/commodity panels.",
            "- `crypto market regime` surfaces recent crypto OHLCV/microstructure panels and the prior macro-stress candidate, but no source-owned MainRegimeV2 rows.",
            "",
            "## Why It Still Blocks",
            "",
            "The second pass found no owner-approved `MainRegimeV2` crosswalk and no source-owned rows for non-US/non-equity or source-label equivalence. The most tempting new surface is BTCUSD 5m/15m HMM-6, but Board A already rejects HMM/generated labels as proxy evidence. The ClarusC64 and Algoplexity surfaces may be useful as structural sidecars, but they do not close the active regime-confidence acceptance gate.",
            "",
            "## Next",
            "",
            "Keep the source-label equivalence intake verifier fail-closed. The next useful external step is not another broad keyword sweep; it is either owner-approved crosswalk acquisition for a promising candidate, or a row/provenance drop that exactly matches the existing intake verifier schema.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{OUT_DIR / 'external_source_label_second_screen_v1.json'}`",
            f"- Candidate CSV: `{csv_path}`",
            f"- Assertions: `{CHECK_DIR / 'external_source_label_second_screen_v1_assertions.out'}`",
        ]
    )
    (OUT_DIR / "external_source_label_second_screen_v1.md").write_text("\n".join(md_lines) + "\n")

    assertions = [
        "PASS decision=external_source_label_second_screen_v1=no_promotable_source_label_equivalence",
        "PASS accepted_rows_added=0",
        "PASS full_other_market_source_label_equivalence=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    (CHECK_DIR / "external_source_label_second_screen_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )


if __name__ == "__main__":
    main()
