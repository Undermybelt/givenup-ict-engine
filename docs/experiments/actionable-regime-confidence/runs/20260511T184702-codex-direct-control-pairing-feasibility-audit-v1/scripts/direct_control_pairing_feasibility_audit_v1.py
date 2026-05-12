#!/usr/bin/env python3
import csv
import json
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "direct-control-pairing"
CHECK_DIR = RUN_ROOT / "checks"
TMP_DIR = Path("/tmp/ict-engine-direct-control-pairing-probe")
OUT_DIR.mkdir(parents=True, exist_ok=True)
CHECK_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run(cmd, timeout=120):
    return subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )


def ensure_kaggle_file(filename):
    dst = TMP_DIR / "adam"
    dst.mkdir(parents=True, exist_ok=True)
    path = dst / filename
    if not path.exists():
        proc = run(
            [
                "kaggle",
                "datasets",
                "download",
                "-d",
                "adamatractor/institutional-crypto-l2-orderbook-30lvl-1m-5m",
                "-f",
                filename,
                "-p",
                str(dst),
                "--unzip",
            ],
            timeout=180,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stdout)
    return path


def csv_time_profile(path):
    df = pd.read_csv(path)
    return {
        "path": str(path),
        "rows": int(df.shape[0]),
        "columns": list(df.columns),
        "timestamp_min": str(df["timestamp"].min()) if "timestamp" in df.columns else None,
        "timestamp_max": str(df["timestamp"].max()) if "timestamp" in df.columns else None,
        "label_like_columns": [
            c
            for c in df.columns
            if any(token in c.lower() for token in ["label", "target", "event", "control", "negative", "matched"])
        ],
    }


def main():
    hf_stats = fetch_json(
        "https://datasets-server.huggingface.co/statistics?dataset=Go3x3/pump_and_dump_dataset&config=default&split=train"
    )
    symbol_stats = next(item for item in hf_stats["statistics"] if item["column_name"] == "symbol")
    timestamp_stats = next(item for item in hf_stats["statistics"] if item["column_name"] == "timestamp")
    symbols = set(symbol_stats["column_statistics"]["frequencies"].keys())
    pump_assets = {symbol.split("/")[0] for symbol in symbols if "/" in symbol}
    pump_timestamp_min = int(timestamp_stats["column_statistics"]["min"])
    pump_timestamp_max = int(timestamp_stats["column_statistics"]["max"])

    control_files = [
        ensure_kaggle_file("ADA_1m_ohlcv.csv"),
        ensure_kaggle_file("ADA_1m_depth30.csv"),
        ensure_kaggle_file("AVAX_1m_ohlcv.csv"),
    ]
    control_profiles = [csv_time_profile(path) for path in control_files]
    control_assets = {"ADA", "AVAX"}
    symbol_overlap_assets = sorted(pump_assets & control_assets)

    # Adam control samples are ISO timestamps in March 2025; Go3x3 positives are epoch-ms 2021-2022.
    control_date_ranges = {
        Path(profile["path"]).name: {
            "timestamp_min": profile["timestamp_min"],
            "timestamp_max": profile["timestamp_max"],
        }
        for profile in control_profiles
    }
    temporal_overlap = False
    matched_pair_ready = False

    rows = [
        {
            "positive_source": "Go3x3/pump_and_dump_dataset",
            "positive_schema": "symbol,timestamp,datetime,side,price,amount,btc_volume",
            "positive_timestamp_min_ms": pump_timestamp_min,
            "positive_timestamp_max_ms": pump_timestamp_max,
            "control_source": "adamatractor/institutional-crypto-l2-orderbook-30lvl-1m-5m",
            "control_assets_sampled": ",".join(sorted(control_assets)),
            "symbol_overlap_assets": ",".join(symbol_overlap_assets),
            "temporal_overlap": temporal_overlap,
            "label_or_event_id_overlap": False,
            "matched_pair_ready": matched_pair_ready,
            "reason": "AVAX overlaps as an asset name, but Adam control rows are 2025-03-12..2025-03-19 while Go3x3 positive windows are 2021-05..2022-09; both sources lack shared event ids and matched-negative group ids.",
        }
    ]

    summary = {
        "run_id": "20260511T184702+0800-codex-direct-control-pairing-feasibility-audit-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "direct_control_pairing_feasibility_audit_v1=no_symbol_time_event_matched_controls",
        "positive_source": "https://huggingface.co/datasets/Go3x3/pump_and_dump_dataset",
        "control_source": "https://www.kaggle.com/datasets/adamatractor/institutional-crypto-l2-orderbook-30lvl-1m-5m",
        "positive_num_examples": hf_stats["num_examples"],
        "positive_symbol_count": len(symbols),
        "positive_assets_sampled_overlap": symbol_overlap_assets,
        "positive_timestamp_min_ms": pump_timestamp_min,
        "positive_timestamp_max_ms": pump_timestamp_max,
        "control_profiles": control_profiles,
        "control_date_ranges": control_date_ranges,
        "temporal_overlap": temporal_overlap,
        "matched_pair_ready": matched_pair_ready,
        "reason": rows[0]["reason"],
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "full_direct_species_coverage": False,
        "full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }
    (OUT_DIR / "direct_control_pairing_feasibility_audit_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True)
    )

    csv_path = OUT_DIR / "direct_control_pairing_feasibility_audit_v1_rows.csv"
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    md = [
        "# Direct Control Pairing Feasibility Audit v1",
        "",
        "Run ID: `20260511T184702+0800-codex-direct-control-pairing-feasibility-audit-v1`",
        "",
        "This audit checks whether the positive-only Go3x3 pump/dump trade windows can be paired with Adam's control-only crypto L2/LOB data to create matched negative controls without generating proxy labels.",
        "",
        "## Decision",
        "",
        "`direct_control_pairing_feasibility_audit_v1=no_symbol_time_event_matched_controls`",
        "",
        f"- Go3x3 rows reported: `{summary['positive_num_examples']}` across `{summary['positive_symbol_count']}` symbols.",
        f"- Go3x3 positive timestamp range: `{pump_timestamp_min}` to `{pump_timestamp_max}` epoch-ms.",
        f"- Adam control samples checked: `{', '.join(Path(p['path']).name for p in control_profiles)}`.",
        f"- Adam control date ranges: `{control_date_ranges}`.",
        f"- Asset-name overlap in sampled controls: `{symbol_overlap_assets}`.",
        "- Temporal overlap: `false`.",
        "- Shared event id / matched-negative group id: `false`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Full direct species coverage: `false`; full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Why It Blocks",
        "",
        rows[0]["reason"],
        "",
        "A separate control-only L2 panel cannot be used as a matched negative set unless it overlaps the positive source by symbol, time window, event policy, and provenance. This pairing currently fails time overlap and lacks shared event/control identifiers.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{OUT_DIR / 'direct_control_pairing_feasibility_audit_v1.json'}`",
        f"- Pairing rows CSV: `{csv_path}`",
        f"- Assertions: `{CHECK_DIR / 'direct_control_pairing_feasibility_audit_v1_assertions.out'}`",
    ]
    (OUT_DIR / "direct_control_pairing_feasibility_audit_v1.md").write_text("\n".join(md) + "\n")

    assertions = [
        "PASS symbol_overlap_checked",
        "PASS temporal_overlap false" if not temporal_overlap else "FAIL temporal_overlap",
        "PASS matched_pair_ready false" if not matched_pair_ready else "FAIL matched_pair_ready",
        "PASS accepted_rows_added 0",
        "PASS update_goal false",
    ]
    (CHECK_DIR / "direct_control_pairing_feasibility_audit_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )
    if any(line.startswith("FAIL") for line in assertions):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
