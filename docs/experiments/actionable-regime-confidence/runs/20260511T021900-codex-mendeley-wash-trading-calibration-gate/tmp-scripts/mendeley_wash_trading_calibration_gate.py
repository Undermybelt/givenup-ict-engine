#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T021900+0800-codex-mendeley-wash-trading-calibration-gate"
RUN_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T021900-codex-mendeley-wash-trading-calibration-gate"
)
OUT_DIR = RUN_ROOT / "wash-gate"
CHECKS_DIR = RUN_ROOT / "checks"
TMP_ROOT = Path("/tmp/ict-regime-mendeley-wash-trading")
DATASET_URL = "https://data.mendeley.com/public-api/datasets/4hyxfwzpgg"

QUANTILES = [0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.98, 0.99]
CHUNKSIZE = 200_000
SAMPLE_LIMIT_PER_FILE = 250_000
SUPPORT_FLOOR = 50
TARGET_LCB = 0.95


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def wilson_lcb(successes: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    phat = successes / n
    denom = 1 + z * z / n
    center = phat + z * z / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return max(0.0, (center - margin) / denom)


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "curl/8.7.1"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_label(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.astype(bool)
    lowered = series.astype(str).str.lower().str.strip()
    return lowered.isin({"1", "true", "t", "yes", "y"})


def download_file(file_info: dict[str, Any], force: bool = False) -> Path:
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    path = TMP_ROOT / file_info["filename"]
    expected_size = int(file_info["size"])
    if path.exists() and path.stat().st_size == expected_size and not force:
        return path
    tmp_path = path.with_suffix(path.suffix + ".part")
    if tmp_path.exists():
        tmp_path.unlink()
    url = file_info["download_url"]
    request = urllib.request.Request(
        url,
        headers={"Accept": "text/csv", "User-Agent": "curl/8.7.1"},
    )
    with urllib.request.urlopen(request, timeout=120) as response, tmp_path.open("wb") as out:
        shutil.copyfileobj(response, out, length=1024 * 1024)
    if tmp_path.stat().st_size != expected_size:
        raise RuntimeError(
            f"Downloaded size mismatch for {file_info['filename']}: "
            f"{tmp_path.stat().st_size} != {expected_size}"
        )
    tmp_path.replace(path)
    return path


def iter_chunks(path: Path, usecols: list[str]) -> Any:
    return pd.read_csv(path, usecols=usecols, chunksize=CHUNKSIZE)


def count_rows(path: Path, label: str, features: list[str]) -> dict[str, Any]:
    rows = 0
    positives = 0
    for chunk in iter_chunks(path, features + [label]):
        labels = normalize_label(chunk[label])
        rows += len(chunk)
        positives += int(labels.sum())
    return {"rows": rows, "positives": positives, "negatives": rows - positives}


def sample_train_values(path: Path, label: str, features: list[str], train_end: int) -> pd.DataFrame:
    sample_parts: list[pd.DataFrame] = []
    collected = 0
    offset = 0
    for chunk in iter_chunks(path, features + [label]):
        start = offset
        end = offset + len(chunk)
        offset = end
        if start >= train_end:
            break
        train_chunk = chunk.iloc[: max(0, min(end, train_end) - start)]
        if train_chunk.empty:
            continue
        remaining = SAMPLE_LIMIT_PER_FILE - collected
        if remaining <= 0:
            break
        take = min(remaining, len(train_chunk))
        if len(train_chunk) > take:
            train_chunk = train_chunk.sample(n=take, random_state=42)
        sample_parts.append(train_chunk[features].copy())
        collected += len(train_chunk)
    if not sample_parts:
        return pd.DataFrame(columns=features)
    return pd.concat(sample_parts, ignore_index=True)


def candidate_rules(train_sample: pd.DataFrame, features: list[str]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for feature in features:
        values = pd.to_numeric(train_sample[feature], errors="coerce").dropna()
        if values.empty:
            continue
        for threshold in sorted(set(float(x) for x in values.quantile(QUANTILES).dropna().tolist())):
            rules.append({"feature": feature, "direction": "ge", "threshold": threshold})
            rules.append({"feature": feature, "direction": "le", "threshold": threshold})
    return rules


def empty_stats() -> dict[str, int]:
    return {"support": 0, "positives": 0}


def update_stats(stats: dict[str, int], mask: pd.Series, labels: pd.Series) -> None:
    support = int(mask.sum())
    stats["support"] += support
    if support:
        stats["positives"] += int(labels[mask].sum())


def finalize_stats(stats: dict[str, int]) -> dict[str, Any]:
    support = stats["support"]
    positives = stats["positives"]
    return {
        "support": support,
        "positives": positives,
        "precision": positives / support if support else 0.0,
        "wilson95_lcb": wilson_lcb(positives, support),
    }


def evaluate_rules(path: Path, label: str, features: list[str], split: dict[str, int], rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    state = [
        {
            **rule,
            "train": empty_stats(),
            "calibration": empty_stats(),
            "test": empty_stats(),
        }
        for rule in rules
    ]
    offset = 0
    for chunk in iter_chunks(path, features + [label]):
        start = offset
        end = offset + len(chunk)
        offset = end
        labels = normalize_label(chunk[label]).reset_index(drop=True)
        chunk = chunk[features].apply(pd.to_numeric, errors="coerce").reset_index(drop=True)
        idx = pd.RangeIndex(start, end)
        train_mask = pd.Series(idx < split["train_end"]).reset_index(drop=True)
        cal_mask = pd.Series((idx >= split["train_end"]) & (idx < split["cal_end"])).reset_index(drop=True)
        test_mask = pd.Series(idx >= split["cal_end"]).reset_index(drop=True)
        for row in state:
            values = chunk[row["feature"]]
            if row["direction"] == "ge":
                mask = values >= row["threshold"]
            else:
                mask = values <= row["threshold"]
            mask = mask.fillna(False)
            update_stats(row["train"], mask & train_mask, labels)
            update_stats(row["calibration"], mask & cal_mask, labels)
            update_stats(row["test"], mask & test_mask, labels)
    out: list[dict[str, Any]] = []
    for row in state:
        out.append(
            {
                "feature": row["feature"],
                "direction": row["direction"],
                "threshold": row["threshold"],
                "train": finalize_stats(row["train"]),
                "calibration": finalize_stats(row["calibration"]),
                "test": finalize_stats(row["test"]),
            }
        )
    return out


def source_chronology(filename: str) -> dict[str, Any]:
    if filename == "gox_ml_samples.csv":
        return {
            "global_chronological_order_evidence": True,
            "evidence": "gox_ml_sample.py sorts by `time` immediately before writing ML samples.",
            "acceptance_allowed": True,
        }
    return {
        "global_chronological_order_evidence": False,
        "evidence": "nft_ml_sample.py writes after sorting by `contractAddress`, `timestamp`; timestamp is omitted from public ML samples, so a global chronological split cannot be verified from the public CSV alone.",
        "acceptance_allowed": False,
    }


def evaluate_file(file_info: dict[str, Any], force_download: bool = False) -> dict[str, Any]:
    filename = file_info["filename"]
    label = "wash" if filename == "gox_ml_samples.csv" else "filter_1234"
    features = [column for column in file_info["header"] if column != label]
    path = download_file(file_info, force=force_download)
    counts = count_rows(path, label, features)
    split = {
        "train_end": int(counts["rows"] * 0.50),
        "cal_end": int(counts["rows"] * 0.75),
        "train_rows": int(counts["rows"] * 0.50),
        "calibration_rows": int(counts["rows"] * 0.75) - int(counts["rows"] * 0.50),
        "test_rows": counts["rows"] - int(counts["rows"] * 0.75),
    }
    train_sample = sample_train_values(path, label, features, split["train_end"])
    rules = candidate_rules(train_sample, features)
    evaluated = evaluate_rules(path, label, features, split, rules)
    eligible = [item for item in evaluated if item["train"]["support"] >= SUPPORT_FLOOR]
    best = max(
        eligible,
        key=lambda item: (
            item["train"]["wilson95_lcb"],
            item["train"]["precision"],
            item["train"]["positives"],
            item["train"]["support"],
        ),
        default=None,
    )
    chronology = source_chronology(filename)
    accepted = False
    blocker = "no_train_rule_with_support_floor"
    if best is not None:
        accepted = (
            chronology["acceptance_allowed"]
            and best["calibration"]["support"] >= SUPPORT_FLOOR
            and best["test"]["support"] >= SUPPORT_FLOOR
            and best["calibration"]["wilson95_lcb"] >= TARGET_LCB
            and best["test"]["wilson95_lcb"] >= TARGET_LCB
        )
        if accepted:
            blocker = "accepted_95_context"
        elif not chronology["acceptance_allowed"]:
            blocker = "source_order_not_global_chronological_for_public_ml_sample"
        else:
            blocker = "calibration_or_test_wilson_below_95_or_support_below_50"
    return {
        "filename": filename,
        "tmp_path": str(path),
        "tmp_size_bytes": path.stat().st_size,
        "label": label,
        "features": features,
        "counts": counts,
        "split": split,
        "chronology": chronology,
        "candidate_rules": len(rules),
        "best_rule": best,
        "accepted_95_context": accepted,
        "blocker": blocker,
    }


def build_file_infos(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    infos: list[dict[str, Any]] = []
    for file in dataset.get("files", []):
        details = file["content_details"]
        filename = file["filename"]
        if filename == "gox_ml_samples.csv":
            header = [
                "bitcoins",
                "round_level",
                "cumu_wash_percent_opt",
                "buyer_24h_trade_count",
                "buyer_7d_trade_count",
                "seller_24h_trade_count",
                "seller_7d_trade_count",
                "buyer_24h_btc_sum",
                "buyer_7d_btc_sum",
                "seller_24h_btc_sum",
                "seller_7d_btc_sum",
                "buyer_all_btc_sum",
                "seller_all_btc_sum",
                "price_deviation",
                "time_since_last_trade",
                "hours",
                "wash",
            ]
        else:
            header = [
                "sellerFee_amount",
                "round_level",
                "cumu_wash_percent_opt",
                "buyer_24h_trade_count",
                "buyer_7d_trade_count",
                "seller_24h_trade_count",
                "seller_7d_trade_count",
                "buyer_24h_nfttrade_count",
                "buyer_7d_nfttrade_count",
                "seller_24h_nfttrade_count",
                "seller_7d_nfttrade_count",
                "buyer_nft_all_trade_count",
                "seller_nft_all_trade_count",
                "price_deviation",
                "time_since_last_trade",
                "hours",
                "filter_1234",
            ]
        infos.append(
            {
                "filename": filename,
                "size": int(file["size"]),
                "download_url": details["download_url"],
                "sha256_hash": details.get("sha256_hash"),
                "content_type": details.get("content_type"),
                "header": header,
            }
        )
    return infos


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", action="append", help="Evaluate only the named CSV file. Can be passed multiple times.")
    parser.add_argument("--force-download", action="store_true")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    dataset = fetch_json(DATASET_URL)
    file_infos = build_file_infos(dataset)
    if args.only:
        wanted = set(args.only)
        file_infos = [item for item in file_infos if item["filename"] in wanted]
    evaluations = [evaluate_file(info, force_download=args.force_download) for info in file_infos]

    accepted_contexts = [item for item in evaluations if item["accepted_95_context"]]
    chronology_blocked = [item for item in evaluations if item["blocker"] == "source_order_not_global_chronological_for_public_ml_sample"]
    decision = {
        "board_state": "blocked",
        "active_axis": "MainRegimeV2",
        "candidate_regime": "Manipulation",
        "accepted_95": False,
        "accepted_contexts": [item["filename"] for item in accepted_contexts],
        "accepted_95_context_count": len(accepted_contexts),
        "manipulation_input_state": (
            "partial_context_pass_not_root_complete"
            if accepted_contexts
            else "raw_wash_labels_calibration_failed_or_blocked"
        ),
        "thresholds_relaxed": False,
        "runtime_code_changed": False,
        "fresh_calibration_rerun": True,
        "trade_usable": False,
        "blocker": (
            "At least one context reached the 95% held-out rule gate, but Board A root completion still requires active-root coverage and cross-context/chronology sufficiency; NFT public ML samples lack globally verifiable chronological order."
            if accepted_contexts
            else "No Mendeley wash-trading file produced an accepted active-root packet under the unchanged chronological 95% gate."
        ),
        "next_action": (
            "Recover or stream source raw rows with timestamps for NFT marketplace samples, or run a second direct/event manipulation source so Manipulation has cross-context chronological evidence; keep Bull/Bear/Sideways on non-OHLCV signed-direction/sideways inputs."
        ),
    }
    report = {
        "run_id": RUN_ID,
        "dataset": {
            "url": DATASET_URL,
            "id": dataset.get("id"),
            "doi": dataset.get("doi", {}).get("id"),
            "version": dataset.get("version"),
            "name": dataset.get("name"),
            "license": dataset.get("data_licence", {}).get("short_name"),
            "size": dataset.get("size"),
            "fetched_at_local": datetime.now().isoformat(timespec="seconds"),
        },
        "gate_contract": {
            "split": "row-order train 50%, calibration 25%, test 25%; acceptance only allowed when source script proves global chronological output order",
            "rule_selection": "single-feature threshold rule selected on train split by Wilson95 lower bound",
            "support_floor": SUPPORT_FLOOR,
            "target_lcb": TARGET_LCB,
            "target_or_future_predictors_used": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "tmp_root": str(TMP_ROOT),
        },
        "evaluations": evaluations,
        "decision": decision,
    }
    report_json = OUT_DIR / "mendeley_wash_trading_calibration_gate_report.json"
    report_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    summary_rows = []
    for item in evaluations:
        best = item.get("best_rule") or {}
        summary_rows.append(
            {
                "filename": item["filename"],
                "rows": item["counts"]["rows"],
                "positives": item["counts"]["positives"],
                "label": item["label"],
                "chronology_acceptance_allowed": item["chronology"]["acceptance_allowed"],
                "best_rule": None
                if not best
                else f"{best['feature']} {'>=' if best['direction'] == 'ge' else '<='} {best['threshold']:.12g}",
                "train_support": (best.get("train") or {}).get("support"),
                "train_lcb": (best.get("train") or {}).get("wilson95_lcb"),
                "calibration_support": (best.get("calibration") or {}).get("support"),
                "calibration_lcb": (best.get("calibration") or {}).get("wilson95_lcb"),
                "test_support": (best.get("test") or {}).get("support"),
                "test_lcb": (best.get("test") or {}).get("wilson95_lcb"),
                "accepted_95_context": item["accepted_95_context"],
                "blocker": item["blocker"],
            }
        )
    pd.DataFrame(summary_rows).to_csv(OUT_DIR / "mendeley_wash_trading_calibration_gate_summary.csv", index=False)
    report_md = OUT_DIR / "mendeley_wash_trading_calibration_gate_report.md"
    lines = [
        "# Mendeley Wash Trading Calibration Gate",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Gate",
        "",
        "- Active axis: MainRegimeV2.",
        "- Candidate regime: direct-input-gated `Manipulation`.",
        "- Split: row-order train 50%, calibration 25%, test 25%; acceptance only allowed when source script proves global chronological output order.",
        "- Rule shape: train-selected single-feature threshold, held-out calibration/test Wilson95 lower bounds.",
        "- Runtime code changed: false.",
        "- Thresholds relaxed: false.",
        "- Raw CSV committed: false.",
        "",
        "## Results",
        "",
    ]
    for row in summary_rows:
        lines.append(
            "- {filename}: rows={rows}, positives={positives}, rule=`{best_rule}`, cal_lcb={cal_lcb}, test_lcb={test_lcb}, accepted_95_context={accepted}, blocker={blocker}".format(
                filename=row["filename"],
                rows=row["rows"],
                positives=row["positives"],
                best_rule=row["best_rule"],
                cal_lcb="NA" if row["calibration_lcb"] is None else f"{row['calibration_lcb']:.6f}",
                test_lcb="NA" if row["test_lcb"] is None else f"{row['test_lcb']:.6f}",
                accepted=row["accepted_95_context"],
                blocker=row["blocker"],
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"Gate result: `{decision['manipulation_input_state']}`.",
            f"Accepted 95 root: `{decision['accepted_95']}`.",
            f"Blocker: {decision['blocker']}",
            "",
            f"Next: {decision['next_action']}",
        ]
    )
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (CHECKS_DIR / "mendeley_wash_trading_calibration_gate_assertions.out").write_text(
        "\n".join(
            [
                f"RUN_ID {RUN_ID}",
                f"REPORT {repo_rel(report_json)}",
                "ACTIVE_AXIS MainRegimeV2",
                "CANDIDATE_REGIME Manipulation",
                f"FILES_EVALUATED {len(evaluations)}",
                f"ACCEPTED_95_CONTEXT_COUNT {len(accepted_contexts)}",
                f"CHRONOLOGY_BLOCKED_CONTEXT_COUNT {len(chronology_blocked)}",
                f"ACCEPTED_95 {str(decision['accepted_95']).lower()}",
                f"MANIPULATION_INPUT_STATE {decision['manipulation_input_state']}",
                "THRESHOLDS_RELAXED false",
                "RUNTIME_CODE_CHANGED false",
                "FRESH_CALIBRATION_RERUN true",
                "TRADE_USABLE false",
                "RAW_DATA_COMMITTED false",
                f"GATE {decision['manipulation_input_state']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (RUN_ROOT / "README.md").write_text(
        "# Mendeley Wash Trading Calibration Gate\n\n"
        f"- report: `{repo_rel(report_md)}`\n"
        f"- json: `{repo_rel(report_json)}`\n"
        f"- assertions: `{repo_rel(CHECKS_DIR / 'mendeley_wash_trading_calibration_gate_assertions.out')}`\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
