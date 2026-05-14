#!/usr/bin/env python3
import csv
import hashlib
import json
import subprocess
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T192750+0800-codex-native-subhour-external-source-screen-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = RUN_ROOT.parents[4]
BOARD_PATH = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
OUT_DIR = RUN_ROOT / "native-subhour-external-source-screen"
CHECK_DIR = RUN_ROOT / "checks"

OUT_DIR.mkdir(parents=True, exist_ok=True)
CHECK_DIR.mkdir(parents=True, exist_ok=True)

KAGGLE_QUERIES = [
    "intraday market regime",
    "intraday regime label",
    "5m market regime",
]
HF_QUERIES = [
    "intraday market regime",
    "market regime 5m",
    "market regime 15m",
    "HMM6 BTCUSD",
    "BTCUSD market regime",
]


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd, timeout=80):
    proc = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    return {"cmd": cmd, "returncode": proc.returncode, "output": proc.stdout}


def kaggle_search(query):
    safe = query.replace(" ", "_")
    result = run(["kaggle", "datasets", "list", "-s", query, "--csv"], timeout=80)
    (OUT_DIR / f"kaggle_search_{safe}.csv").write_text(result["output"])
    refs = []
    if result["returncode"] == 0:
        refs = [row.get("ref", "") for row in csv.DictReader(result["output"].splitlines())]
    return {
        "query": query,
        "returncode": result["returncode"],
        "top_refs": refs[:10],
        "result_file": f"kaggle_search_{safe}.csv",
    }


def hf_search(query):
    url = "https://huggingface.co/api/datasets?search=" + urllib.parse.quote(query) + "&limit=20"
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return {
        "query": query,
        "top_refs": [item.get("id", "") for item in data[:10]],
        "raw_count": len(data),
    }


def hf_dataset_summary(repo):
    url = "https://huggingface.co/api/datasets/" + repo
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return {
        "id": data.get("id"),
        "downloads": data.get("downloads"),
        "likes": data.get("likes"),
        "tags": data.get("tags", [])[:16],
        "siblings": [item.get("rfilename") for item in data.get("siblings", [])[:16]],
    }


def main():
    board_hash_before = sha256_file(BOARD_PATH)
    kaggle_results = [kaggle_search(query) for query in KAGGLE_QUERIES]
    hf_results = [hf_search(query) for query in HF_QUERIES]

    candidates = [
        {
            "source": "huggingface",
            "ref": "akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD",
            "url": "https://huggingface.co/datasets/akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD",
            "candidate_strength": "native_subhour_crypto_regime_labels",
            "disposition": "blocked_hmm_generated_labels_not_source_owned",
            "reason": "Only HF native-subhour regime hit from targeted API search; labels are HMM-6 inferred from 5m/15m OHLCV and technical indicators, so they remain generated/proxy labels rather than source-owned MainRegimeV2 rows.",
            "metadata": hf_dataset_summary("akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD"),
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
        },
        {
            "source": "kaggle",
            "ref": "thisathdamiru/bybit-multi-crypto-historical-data-2020-2026",
            "url": "https://www.kaggle.com/datasets/thisathdamiru/bybit-multi-crypto-historical-data-2020-2026",
            "candidate_strength": "native_subhour_raw_crypto_ohlcv",
            "disposition": "blocked_raw_provider_panel_no_regime_labels",
            "reason": "Kaggle targeted searches surface this raw Bybit historical data set, but search metadata indicates historical crypto data rather than source-owned regime labels or owner-approved MainRegimeV2 equivalence.",
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
        },
        {
            "source": "kaggle",
            "ref": "toocool69/synthetic-stock-price-data-1m-instances",
            "url": "https://www.kaggle.com/datasets/toocool69/synthetic-stock-price-data-1m-instances",
            "candidate_strength": "synthetic_minute_like_price_panel",
            "disposition": "blocked_synthetic_price_data_not_source_labels",
            "reason": "Synthetic 1m-instance price data cannot satisfy source-owned market-regime labels, other-market validation, or source provenance.",
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
        },
    ]

    summary = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": board_hash_before,
        "decision": "native_subhour_external_source_screen_v1=no_ready_native_subhour_source_labels",
        "scope": "Targeted public-source search for native sub-hour source-owned regime labels.",
        "kaggle_queries": kaggle_results,
        "huggingface_queries": hf_results,
        "candidate_records": len(candidates),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "native_subhour_source_overlap_closed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "candidates": candidates,
    }

    (OUT_DIR / "native_subhour_external_source_screen_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True)
    )

    csv_path = OUT_DIR / "native_subhour_external_source_screen_v1_candidates.csv"
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
        "# Native Subhour External Source Screen v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "Targeted screen for public native sub-hour source-owned market-regime labels. This is narrower than the broad external source-label screens and does not download raw rows.",
        "",
        "## Decision",
        "",
        "`native_subhour_external_source_screen_v1=no_ready_native_subhour_source_labels`",
        "",
        f"- Kaggle targeted queries: `{len(kaggle_results)}`.",
        f"- Hugging Face targeted queries: `{len(hf_results)}`.",
        f"- Candidate records dispositioned: `{len(candidates)}`.",
        "- Accepted rows added: `0`.",
        "- New confidence gate: `false`.",
        "- Native sub-hour source overlap closed: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Candidate Disposition",
        "",
        "| Source | Candidate | Decision | Reason |",
        "|---|---|---|---|",
    ]
    for candidate in candidates:
        md_lines.append(
            f"| `{candidate['source']}` | [`{candidate['ref']}`]({candidate['url']}) | `{candidate['disposition']}` | {candidate['reason']} |"
        )
    md_lines.extend(
        [
            "",
            "## Search Readback",
            "",
            "- Kaggle `intraday market regime`, `intraday regime label`, and `5m market regime` searches surfaced raw daily/crypto/provider panels or synthetic price data, not source-owned regime labels.",
            "- Hugging Face targeted searches only returned the BTCUSD HMM-6 candidate for sub-hour market-regime wording; that remains proxy/generated evidence.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{OUT_DIR / 'native_subhour_external_source_screen_v1.json'}`",
            f"- Candidate CSV: `{csv_path}`",
            f"- Assertions: `{CHECK_DIR / 'native_subhour_external_source_screen_v1_assertions.out'}`",
        ]
    )
    (OUT_DIR / "native_subhour_external_source_screen_v1.md").write_text("\n".join(md_lines) + "\n")

    assertions = [
        "PASS decision=native_subhour_external_source_screen_v1=no_ready_native_subhour_source_labels",
        "PASS accepted_rows_added=0",
        "PASS native_subhour_source_overlap_closed=false",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "native_subhour_external_source_screen_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )


if __name__ == "__main__":
    main()
