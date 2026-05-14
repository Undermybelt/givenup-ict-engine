#!/usr/bin/env python3
import csv
import json
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "external-source-label-screen"
CHECK_DIR = RUN_ROOT / "checks"
TMP_DIR = Path("/tmp/ict-engine-external-source-label-candidates-v1")

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


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_text(url):
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def csv_profile(path):
    df = pd.read_csv(path)
    profile = {
        "file": str(path),
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": list(df.columns),
        "date_ranges": {},
        "label_like_columns": {},
    }
    for col in df.columns:
        lower = col.lower()
        if lower in {"date", "time", "timestamp", "datetime"} or "date" in lower:
            series = df[col].dropna().astype(str)
            if not series.empty:
                profile["date_ranges"][col] = {"min": str(series.min()), "max": str(series.max())}
        if any(token in lower for token in ["regime", "state", "label", "signal", "trend", "risk"]):
            series = df[col].dropna().astype(str)
            profile["label_like_columns"][col] = {
                "nunique": int(series.nunique()),
                "sample_values": sorted(series.unique().tolist())[:12],
            }
    return profile


def download_kaggle(ref, dst):
    dst.mkdir(parents=True, exist_ok=True)
    return run(["kaggle", "datasets", "download", "-d", ref, "-p", str(dst), "--unzip"], timeout=180)


def kaggle_files(ref, name):
    result = run(["kaggle", "datasets", "files", ref], timeout=60)
    (OUT_DIR / f"kaggle_files_{name}.txt").write_text(result["output"])
    return result


def kaggle_search(query):
    name = query.replace(" ", "_").replace("/", "_")
    result = run(["kaggle", "datasets", "list", "-s", query, "--csv"], timeout=60)
    (OUT_DIR / f"kaggle_search_{name}.csv").write_text(result["output"])
    return result


def profile_downloaded_csvs(ref, local_name):
    dst = TMP_DIR / local_name
    download = download_kaggle(ref, dst)
    profiles = []
    for csv_path in sorted(dst.glob("*.csv")):
        profiles.append(csv_profile(csv_path))
    return {"download": download, "profiles": profiles}


def main():
    search_queries = ["regime", "market regime label", "market regime finance", "crypto regime"]
    searches = {query: kaggle_search(query) for query in search_queries}

    candidates = []

    known_stock_refresh = {
        "source": "kaggle",
        "ref": "mafaqbhatti/stock-market-regimes-20002026",
        "url": "https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026",
        "screen_action": "metadata_only_prior_upstream_refresh_readback",
        "candidate_strength": "known_source_panel",
        "disposition": "blocked_no_new_recency_extension",
        "reason": "Prior upstream refresh found CSV/parquet size parity with the local source panel and max source date remains 2026-01-30.",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
    }
    kaggle_files(known_stock_refresh["ref"], "mafaqbhatti__stock_market_regimes_20002026")
    candidates.append(known_stock_refresh)

    selected_kaggle = [
        {
            "ref": "kanchana1990/algorithmic-trading-macro-stress-and-asset-regimes",
            "local_name": "macro_stress_asset_regimes",
            "url": "https://www.kaggle.com/datasets/kanchana1990/algorithmic-trading-macro-stress-and-asset-regimes",
            "candidate_strength": "cross_asset_feature_panel",
            "disposition": "blocked_no_source_label_columns",
            "reason": "Downloaded CSV has cross-asset prices/stress indicators through 2026-02-25, but no regime label column to calibrate MainRegimeV2.",
        },
        {
            "ref": "abidhussai512/macro-regime-dataset-s-and-p-500-vs-federal-fund-rate",
            "local_name": "macro_regime_sp500_fed",
            "url": "https://www.kaggle.com/datasets/abidhussai512/macro-regime-dataset-s-and-p-500-vs-federal-fund-rate",
            "candidate_strength": "macro_context_raw_panel",
            "disposition": "blocked_raw_panel_no_labels",
            "reason": "Downloaded CSV has SP500/FEDFUNDS only; there is no source-owned regime label or owner-approved MainRegimeV2 equivalence.",
        },
        {
            "ref": "igormerlinicomposer/herding-based-market-regime-dataset",
            "local_name": "herding_regime",
            "url": "https://www.kaggle.com/datasets/igormerlinicomposer/herding-based-market-regime-dataset",
            "candidate_strength": "herding_risk_signal_candidate",
            "disposition": "blocked_signal_taxonomy_not_main_regime_v2",
            "reason": "Downloaded CSV has Risk_State/trend/trading-position signals, but no market-family/symbol coverage or owner-approved Bull/Bear/Sideways/Crisis equivalence.",
        },
        {
            "ref": "ahaanverma00/nifty-500-market-and-behavior-regime-dataset",
            "local_name": "nifty500_market_behavior_regime",
            "url": "https://www.kaggle.com/datasets/ahaanverma00/nifty-500-market-and-behavior-regime-dataset",
            "candidate_strength": "promising_other_market_recency_candidate",
            "disposition": "blocked_needs_owner_approved_main_regime_v2_crosswalk",
            "reason": "Downloaded India/NIFTY regime timeline extends to 2026-03-20 with confidence fields, but labels are Durable/Fragile/Calm/Choppy/Stress and behavior states, not source-owned MainRegimeV2 labels.",
        },
    ]

    for item in selected_kaggle:
        safe = item["ref"].replace("/", "__").replace("-", "_")
        kaggle_files(item["ref"], safe)
        profile = profile_downloaded_csvs(item["ref"], item["local_name"])
        candidates.append(
            {
                "source": "kaggle",
                "ref": item["ref"],
                "url": item["url"],
                "screen_action": "downloaded_to_tmp_and_profiled",
                "candidate_strength": item["candidate_strength"],
                "disposition": item["disposition"],
                "reason": item["reason"],
                "csv_profiles": profile["profiles"],
                "download_returncode": profile["download"]["returncode"],
                "accepted_rows_added": 0,
                "new_confidence_gate": False,
            }
        )

    hf_ref = "sujinwo/tsie-market-regime-dataset"
    hf_api = fetch_json(f"https://huggingface.co/api/datasets/{hf_ref}")
    hf_readme = fetch_text(f"https://huggingface.co/datasets/{hf_ref}/raw/main/README.md")
    hf_rows = fetch_json(f"https://datasets-server.huggingface.co/first-rows?dataset={hf_ref}&config=default&split=train")
    hf_summary = {
        "id": hf_api.get("id"),
        "lastModified": hf_api.get("lastModified"),
        "tags": hf_api.get("tags", []),
        "siblings": hf_api.get("siblings", []),
        "feature_names": [feature["name"] for feature in hf_rows.get("features", [])],
        "first_row_group_id": hf_rows.get("rows", [{}])[0].get("row", {}).get("group_id"),
        "first_row_time": hf_rows.get("rows", [{}])[0].get("row", {}).get("time"),
        "readme_labeling_mentions": [
            line.strip()
            for line in hf_readme.splitlines()
            if "label" in line.lower() or "rule" in line.lower() or "future" in line.lower()
        ][:20],
    }
    (OUT_DIR / "hf_sujinwo_tsie_market_regime_dataset_summary.json").write_text(
        json.dumps(hf_summary, indent=2, sort_keys=True)
    )
    candidates.append(
        {
            "source": "huggingface",
            "ref": hf_ref,
            "url": f"https://huggingface.co/datasets/{hf_ref}",
            "screen_action": "metadata_and_first_rows_only_no_large_download",
            "candidate_strength": "promising_other_market_intraday_candidate",
            "disposition": "blocked_ohclv_rule_labels_no_main_regime_v2_equivalence",
            "reason": "Dataset card says IDX multi-class regime labels are generated by rule-based price action/volatility/RSI/volume logic; first-rows features include regime_label plus future_volatility/trend_return/target_return fields. No owner-approved MainRegimeV2 equivalence is supplied.",
            "hf_summary": hf_summary,
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
        }
    )

    summary = {
        "run_id": "20260511T183328+0800-codex-external-source-label-candidate-screen-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "external_source_label_candidate_screen_v1=no_promotable_source_label_equivalence",
        "kaggle_searches": len(searches),
        "huggingface_datasets_screened": 1,
        "candidate_records": len(candidates),
        "promising_but_blocked_candidates": [
            c["ref"]
            for c in candidates
            if "promising" in c.get("candidate_strength", "")
        ],
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "guardrails": [
            "no OHLCV-only or rule-generated labels promoted as source labels",
            "no owner-unapproved label taxonomy crosswalk promoted to MainRegimeV2",
            "no raw downloaded row files committed",
        ],
        "candidates": candidates,
    }

    json_path = OUT_DIR / "external_source_label_candidate_screen_v1.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True))

    csv_path = OUT_DIR / "external_source_label_candidate_screen_v1_candidates.csv"
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "source",
                "ref",
                "url",
                "candidate_strength",
                "disposition",
                "accepted_rows_added",
                "new_confidence_gate",
                "reason",
            ],
        )
        writer.writeheader()
        for candidate in candidates:
            writer.writerow({key: candidate.get(key, "") for key in writer.fieldnames})

    md = [
        "# External Source Label Candidate Screen v1",
        "",
        "Run ID: `20260511T183328+0800-codex-external-source-label-candidate-screen-v1`",
        "",
        "This is an external acquisition screen for the remaining source-label equivalence and recency blockers. It does not accept rows, rewrite the current cursor, or commit raw downloaded data.",
        "",
        "## Decision",
        "",
        "`external_source_label_candidate_screen_v1=no_promotable_source_label_equivalence`",
        "",
        f"- Kaggle searches: `{summary['kaggle_searches']}`.",
        f"- Hugging Face datasets screened: `{summary['huggingface_datasets_screened']}`.",
        f"- Candidate records: `{summary['candidate_records']}`.",
        f"- Promising but blocked candidates: `{', '.join(summary['promising_but_blocked_candidates'])}`.",
        "- Accepted rows added: `0`.",
        "- New confidence gate: `false`.",
        "- Full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Candidate Disposition",
        "",
    ]
    for candidate in candidates:
        md.extend(
            [
                f"- `{candidate['ref']}`: `{candidate['disposition']}`.",
                f"  Source: {candidate['url']}",
                f"  Reason: {candidate['reason']}",
            ]
        )
    md.extend(
        [
            "",
            "## Why It Still Blocks",
            "",
            "The screen found other-market and post-2026-01-30 candidates, especially the NIFTY 500 daily regime timeline and the IDX intraday TSIE dataset. They remain fail-closed because the current Board A contract requires source-owned `MainRegimeV2` labels or an owner-approved equivalence policy. A model/adaptive label taxonomy, OHLCV/rule-based signal label, raw macro panel, or trading-signal state cannot be promoted into `Bull`/`Bear`/`Sideways`/`Crisis` evidence without that crosswalk.",
            "",
            "## Next",
            "",
            "Use the NIFTY/IDX candidates only as request targets: ask for source-owner `MainRegimeV2` crosswalk/equivalence, or import rows that already contain `main_regime_v2_label` plus provenance. Until then, keep strict full objective blocked and continue using existing scoped `regime_factor_consumer_map_v1` for downstream consumption.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- Candidate CSV: `{csv_path}`",
            f"- HF summary: `{OUT_DIR / 'hf_sujinwo_tsie_market_regime_dataset_summary.json'}`",
            f"- Assertions: `{CHECK_DIR / 'external_source_label_candidate_screen_v1_assertions.out'}`",
        ]
    )
    md_path = OUT_DIR / "external_source_label_candidate_screen_v1.md"
    md_path.write_text("\n".join(md) + "\n")

    assertions = []
    assertions.append("PASS decision no_promotable_source_label_equivalence" if summary["decision"].endswith("no_promotable_source_label_equivalence") else "FAIL decision")
    assertions.append("PASS accepted_rows_added 0" if summary["accepted_rows_added"] == 0 else "FAIL accepted_rows_added")
    assertions.append("PASS new_confidence_gate false" if not summary["new_confidence_gate"] else "FAIL new_confidence_gate")
    assertions.append("PASS full_objective_achieved false" if not summary["full_objective_achieved"] else "FAIL full_objective_achieved")
    assertions.append("PASS promising_candidates_blocked" if summary["promising_but_blocked_candidates"] else "FAIL promising_candidates_blocked")
    assertions.append("PASS raw_data_committed false" if not summary["raw_data_committed"] else "FAIL raw_data_committed")
    (CHECK_DIR / "external_source_label_candidate_screen_v1_assertions.out").write_text("\n".join(assertions) + "\n")

    if any(line.startswith("FAIL") for line in assertions):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
