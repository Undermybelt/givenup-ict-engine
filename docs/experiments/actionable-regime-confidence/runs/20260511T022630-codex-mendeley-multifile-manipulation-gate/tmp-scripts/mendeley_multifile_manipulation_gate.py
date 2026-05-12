#!/usr/bin/env python3
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


RUN_ID = "20260511T022630+0800-codex-mendeley-multifile-manipulation-gate"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs/20260511T022630-codex-mendeley-multifile-manipulation-gate")
OUT_DIR = RUN_ROOT / "manipulation-gate"
CHECK_DIR = RUN_ROOT / "checks"

FILES = [
    {
        "venue": "LooksRare",
        "path": Path("/tmp/LooksRare_ml_samples.csv"),
        "expected_sha256": "b50e57907f9c5602f251c261cc4f29889d2f3ceeeaf9cbcfcca447a1fa566c3f",
        "label": "filter_1234",
        "amount": "sellerFee_amount",
        "chronology_grade": "blocked_file_order_not_global_chronology",
        "chronology_reason": "nft_ml_sample.py writes rows sorted by contractAddress,timestamp after dropping timestamp",
    },
    {
        "venue": "Blur",
        "path": Path("/tmp/Blur_ml_samples.csv"),
        "expected_sha256": "51e41acafc574fd4f7853b4a64676775e9695e8dd9fd2eb937e1587f9a41678b",
        "label": "filter_1234",
        "amount": "sellerFee_amount",
        "chronology_grade": "blocked_file_order_not_global_chronology",
        "chronology_reason": "nft_ml_sample.py writes rows sorted by contractAddress,timestamp after dropping timestamp",
    },
    {
        "venue": "Gox",
        "path": Path("/tmp/gox_ml_samples.csv"),
        "expected_sha256": "28cd2a2cca5aed49964e7e75043f9a79f773018d1e891add17319f7541716bff",
        "label": "wash",
        "amount": "bitcoins",
        "chronology_grade": "indirect_source_script_chronology",
        "chronology_reason": "gox_ml_sample.py sorts by time immediately before writing features, but timestamp is absent from the ML CSV",
    },
    {
        "venue": "OpenSea",
        "path": Path("/tmp/OpenSea_ml_samples.csv"),
        "expected_sha256": "9b04bec65d083053b02ea82eb8432f48fdc2d8e27fe1a45565847a35c355e32f",
        "label": "filter_1234",
        "amount": "sellerFee_amount",
        "chronology_grade": "blocked_file_order_not_global_chronology",
        "chronology_reason": "nft_ml_sample.py writes rows sorted by contractAddress,timestamp after dropping timestamp",
    },
]

COMMON_SOURCE_COLUMNS = [
    "round_level",
    "cumu_wash_percent_opt",
    "buyer_24h_trade_count",
    "buyer_7d_trade_count",
    "seller_24h_trade_count",
    "seller_7d_trade_count",
    "price_deviation",
    "time_since_last_trade",
    "hours",
]

STRICT_FEATURES = [
    "amount",
    "log_amount",
    "round_level",
    "buyer_24h_trade_count",
    "buyer_7d_trade_count",
    "seller_24h_trade_count",
    "seller_7d_trade_count",
    "abs_price_deviation",
    "log_time_since_last_trade",
    "hours",
    "buyer_seller_24h_count_ratio",
    "buyer_seller_7d_count_ratio",
]

DIAGNOSTIC_LEAKY_FEATURES = [
    "cumu_wash_percent_opt",
]


def wilson_lcb(positive, support, z=1.959963984540054):
    if support <= 0:
        return 0.0
    phat = positive / support
    denom = 1.0 + z * z / support
    center = phat + z * z / (2.0 * support)
    margin = z * math.sqrt((phat * (1.0 - phat) + z * z / (4.0 * support)) / support)
    return (center - margin) / denom


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def count_rows(path):
    with path.open("rb") as f:
        return max(0, sum(1 for _ in f) - 1)


def bool_series(s):
    if s.dtype == bool:
        return s
    return s.astype(str).str.lower().isin(["true", "1", "yes"])


def normalize_frame(df, meta):
    out = pd.DataFrame(index=df.index)
    amount = pd.to_numeric(df[meta["amount"]], errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
    out["amount"] = amount
    out["log_amount"] = np.log1p(np.abs(amount))
    for col in COMMON_SOURCE_COLUMNS:
        if col in df.columns:
            out[col] = pd.to_numeric(df[col], errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
        else:
            out[col] = 0.0
    out["abs_price_deviation"] = np.abs(out["price_deviation"])
    out["log_time_since_last_trade"] = np.log1p(np.abs(out["time_since_last_trade"]))
    out["buyer_seller_24h_count_ratio"] = (out["buyer_24h_trade_count"] + 1.0) / (out["seller_24h_trade_count"] + 1.0)
    out["buyer_seller_7d_count_ratio"] = (out["buyer_7d_trade_count"] + 1.0) / (out["seller_7d_trade_count"] + 1.0)
    out["label"] = bool_series(df[meta["label"]]).astype(bool)
    return out


def split_name(row_index, n_rows):
    train_end = int(n_rows * 0.60)
    cal_end = int(n_rows * 0.80)
    if row_index < train_end:
        return "train"
    if row_index < cal_end:
        return "calibration"
    return "test"


def stats_for_mask(mask, labels):
    support = int(mask.sum())
    positives = int(labels[mask].sum()) if support else 0
    precision = positives / support if support else 0.0
    return {
        "support": support,
        "positives": positives,
        "precision": precision,
        "wilson95_lcb": wilson_lcb(positives, support),
    }


def build_candidates(train_df, feature_names, candidate_class, min_support=120, top_n=80):
    candidates = []
    y = train_df["label"].to_numpy(dtype=bool)
    n_train = len(train_df)
    quantiles = np.linspace(0.01, 0.99, 33)
    for feature in feature_names:
        values = train_df[feature].replace([np.inf, -np.inf], np.nan).dropna()
        if values.empty or values.nunique(dropna=True) <= 1:
            continue
        thresholds = np.unique(values.quantile(quantiles).to_numpy(dtype=float))
        x = train_df[feature].to_numpy(dtype=float)
        for op in [">=", "<="]:
            for threshold in thresholds:
                if not np.isfinite(threshold):
                    continue
                mask = x >= threshold if op == ">=" else x <= threshold
                st = stats_for_mask(mask, y)
                if st["support"] < min_support:
                    continue
                candidates.append({
                    "candidate_class": candidate_class,
                    "rule_type": "univariate",
                    "clauses": [{"feature": feature, "op": op, "threshold": float(threshold)}],
                    "train": st,
                    "train_coverage": st["support"] / n_train if n_train else 0.0,
                })
    candidates.sort(key=lambda c: (c["train"]["wilson95_lcb"], c["train"]["precision"], c["train"]["support"]), reverse=True)
    base = candidates[:top_n]

    pair_candidates = []
    max_pair_base = min(35, len(base))
    for i in range(max_pair_base):
        for j in range(i + 1, max_pair_base):
            left = base[i]["clauses"][0]
            right = base[j]["clauses"][0]
            if left["feature"] == right["feature"]:
                continue
            mask = apply_clauses(train_df, [left, right])
            st = stats_for_mask(mask, y)
            if st["support"] < min_support:
                continue
            pair_candidates.append({
                "candidate_class": candidate_class,
                "rule_type": "and2",
                "clauses": [left, right],
                "train": st,
                "train_coverage": st["support"] / n_train if n_train else 0.0,
            })
    pair_candidates.sort(key=lambda c: (c["train"]["wilson95_lcb"], c["train"]["precision"], c["train"]["support"]), reverse=True)
    return (base + pair_candidates[:top_n])[: top_n * 2]


def apply_clauses(df, clauses):
    mask = np.ones(len(df), dtype=bool)
    for clause in clauses:
        x = df[clause["feature"]].to_numpy(dtype=float)
        if clause["op"] == ">=":
            mask &= x >= clause["threshold"]
        else:
            mask &= x <= clause["threshold"]
    return mask


def read_normalized(meta, n_rows=None, skiprows=None):
    usecols = [meta["amount"], meta["label"]] + COMMON_SOURCE_COLUMNS
    usecols = list(dict.fromkeys(usecols))
    return normalize_frame(pd.read_csv(meta["path"], usecols=usecols, nrows=n_rows, skiprows=skiprows), meta)


def evaluate_candidates(meta, n_rows, candidates):
    split_counts = {
        name: {"support": 0, "positives": 0, "rows": 0, "label_positives": 0}
        for name in ["train", "calibration", "test"]
    }
    cand_stats = [
        {
            "candidate_class": c["candidate_class"],
            "rule_type": c["rule_type"],
            "clauses": c["clauses"],
            "splits": {
                name: {"support": 0, "positives": 0}
                for name in ["train", "calibration", "test"]
            },
        }
        for c in candidates
    ]

    usecols = [meta["amount"], meta["label"]] + COMMON_SOURCE_COLUMNS
    usecols = list(dict.fromkeys(usecols))
    row_offset = 0
    for raw in pd.read_csv(meta["path"], usecols=usecols, chunksize=200_000):
        df = normalize_frame(raw, meta)
        labels = df["label"].to_numpy(dtype=bool)
        row_indices = np.arange(row_offset, row_offset + len(df))
        split_masks = {
            "train": row_indices < int(n_rows * 0.60),
            "calibration": (row_indices >= int(n_rows * 0.60)) & (row_indices < int(n_rows * 0.80)),
            "test": row_indices >= int(n_rows * 0.80),
        }
        for split, split_mask in split_masks.items():
            split_counts[split]["rows"] += int(split_mask.sum())
            split_counts[split]["label_positives"] += int(labels[split_mask].sum()) if split_mask.any() else 0
        for idx, candidate in enumerate(candidates):
            mask = apply_clauses(df, candidate["clauses"])
            for split, split_mask in split_masks.items():
                m = mask & split_mask
                support = int(m.sum())
                cand_stats[idx]["splits"][split]["support"] += support
                cand_stats[idx]["splits"][split]["positives"] += int(labels[m].sum()) if support else 0
        row_offset += len(df)

    for c in cand_stats:
        for split in ["train", "calibration", "test"]:
            support = c["splits"][split]["support"]
            positives = c["splits"][split]["positives"]
            c["splits"][split]["precision"] = positives / support if support else 0.0
            c["splits"][split]["wilson95_lcb"] = wilson_lcb(positives, support)
            c["splits"][split]["coverage"] = support / split_counts[split]["rows"] if split_counts[split]["rows"] else 0.0
        c["min_wilson95_lcb"] = min(c["splits"][s]["wilson95_lcb"] for s in ["train", "calibration", "test"])
        c["min_support"] = min(c["splits"][s]["support"] for s in ["calibration", "test"])
        c["passes_support"] = c["splits"]["calibration"]["support"] >= 120 and c["splits"]["test"]["support"] >= 60
        c["passes_wilson95"] = c["splits"]["calibration"]["wilson95_lcb"] >= 0.95 and c["splits"]["test"]["wilson95_lcb"] >= 0.95
        c["passes_train_selection"] = c["splits"]["train"]["wilson95_lcb"] >= 0.95
        c["passes_coverage"] = c["splits"]["calibration"]["coverage"] >= 0.03 and c["splits"]["test"]["coverage"] >= 0.03
        c["accepted_95_rule_only"] = (
            c["passes_support"]
            and c["passes_wilson95"]
            and c["passes_train_selection"]
            and c["passes_coverage"]
            and c["candidate_class"] == "strict_non_leaky"
        )
    cand_stats.sort(key=lambda c: (c["accepted_95_rule_only"], c["min_wilson95_lcb"], c["splits"]["test"]["wilson95_lcb"], c["min_support"]), reverse=True)
    return split_counts, cand_stats


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    file_reports = []
    accepted_files = []

    for meta in FILES:
        report = {
            "venue": meta["venue"],
            "path": str(meta["path"]),
            "exists": meta["path"].exists(),
            "expected_sha256": meta["expected_sha256"],
            "chronology_grade": meta["chronology_grade"],
            "chronology_reason": meta["chronology_reason"],
        }
        if not meta["path"].exists():
            report["skipped_reason"] = "raw_file_not_present_in_tmp"
            file_reports.append(report)
            continue

        report["actual_sha256"] = sha256_file(meta["path"])
        report["sha256_matches"] = report["actual_sha256"] == meta["expected_sha256"]
        n_rows = count_rows(meta["path"])
        report["rows"] = n_rows
        train_rows = int(n_rows * 0.60)
        train_df = read_normalized(meta, n_rows=train_rows)

        strict_candidates = build_candidates(train_df, STRICT_FEATURES, "strict_non_leaky", min_support=120, top_n=80)
        diagnostic_candidates = build_candidates(train_df, DIAGNOSTIC_LEAKY_FEATURES, "diagnostic_leaky", min_support=120, top_n=20)
        candidates = strict_candidates + diagnostic_candidates
        split_counts, evaluated = evaluate_candidates(meta, n_rows, candidates)
        report["label_counts"] = {
            split: {
                "rows": split_counts[split]["rows"],
                "positives": split_counts[split]["label_positives"],
                "positive_rate": split_counts[split]["label_positives"] / split_counts[split]["rows"] if split_counts[split]["rows"] else 0.0,
            }
            for split in ["train", "calibration", "test"]
        }
        report["candidate_counts"] = {
            "strict_non_leaky": len(strict_candidates),
            "diagnostic_leaky": len(diagnostic_candidates),
        }
        report["best_rules"] = evaluated[:20]
        accepted = [c for c in evaluated if c["accepted_95_rule_only"]]
        report["accepted_95_rule_only"] = bool(accepted)
        report["accepted_95_chronology_grade"] = bool(accepted) and meta["chronology_grade"] == "indirect_source_script_chronology"
        if report["accepted_95_chronology_grade"]:
            accepted_files.append(meta["venue"])
        file_reports.append(report)
        del train_df

    accepted_95 = len(accepted_files) >= 2
    blocked_reasons = []
    if len(accepted_files) < 2:
        blocked_reasons.append("no strict non-leaky rule passed train/calibration/test 95% Wilson lower-bound support and coverage gates with chronology-grade evidence")
    nft_files = [r["venue"] for r in file_reports if r.get("exists") and r.get("chronology_grade") == "blocked_file_order_not_global_chronology"]
    if nft_files:
        blocked_reasons.append("NFT ML samples drop timestamp and are written in contractAddress,timestamp order, so file-order splits are not global chronological evidence")
    missing_files = [r["venue"] for r in file_reports if not r.get("exists")]
    if missing_files:
        blocked_reasons.append(f"missing raw files in /tmp: {', '.join(missing_files)}")

    result = {
        "run_id": RUN_ID,
        "active_axis": "MainRegimeV2",
        "candidate_regime": "Manipulation",
        "source": {
            "name": "Mendeley Data: Detecting Crypto Wash Trades via Machine Learning",
            "doi": "10.17632/4hyxfwzpgg.3",
            "url": "https://data.mendeley.com/datasets/4hyxfwzpgg/3",
            "github": "https://github.com/niuniu-zhang/nft_wash_trading",
        },
        "raw_data_policy": "raw_csvs_read_from_/tmp_only; no raw rows committed to repo",
        "feature_policy": {
            "strict_features": STRICT_FEATURES,
            "excluded_from_acceptance_as_leakage_or_label": ["filter_1234", "wash", "cumu_wash_percent_opt"],
            "diagnostic_only_features": DIAGNOSTIC_LEAKY_FEATURES,
        },
        "gate_thresholds": {
            "train_wilson95_lcb_min": 0.95,
            "calibration_wilson95_lcb_min": 0.95,
            "test_wilson95_lcb_min": 0.95,
            "calibration_support_min": 120,
            "test_support_min": 60,
            "calibration_coverage_min": 0.03,
            "test_coverage_min": 0.03,
        },
        "files": file_reports,
        "decision": {
            "accepted_95": accepted_95,
            "accepted_files": accepted_files,
            "gate": "accepted_95_manipulation_mendeley_multifile" if accepted_95 else "blocked_mendeley_multifile_no_chronology_grade_95_rule",
            "blockers": blocked_reasons,
            "thresholds_relaxed": False,
            "runtime_code_changed": False,
            "fresh_calibration_rerun": True,
            "trade_usable": False,
            "raw_data_committed": False,
        },
    }

    (OUT_DIR / "mendeley_multifile_manipulation_gate_report.json").write_text(json.dumps(result, indent=2, sort_keys=True))

    summary_path = OUT_DIR / "mendeley_multifile_rule_summary.csv"
    with summary_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "venue",
            "candidate_class",
            "rule_type",
            "clauses",
            "train_lcb",
            "cal_lcb",
            "test_lcb",
            "cal_support",
            "test_support",
            "cal_coverage",
            "test_coverage",
            "accepted_rule_only",
        ])
        for fr in file_reports:
            for rule in fr.get("best_rules", [])[:20]:
                writer.writerow([
                    fr["venue"],
                    rule["candidate_class"],
                    rule["rule_type"],
                    json.dumps(rule["clauses"], sort_keys=True),
                    f"{rule['splits']['train']['wilson95_lcb']:.12f}",
                    f"{rule['splits']['calibration']['wilson95_lcb']:.12f}",
                    f"{rule['splits']['test']['wilson95_lcb']:.12f}",
                    rule["splits"]["calibration"]["support"],
                    rule["splits"]["test"]["support"],
                    f"{rule['splits']['calibration']['coverage']:.12f}",
                    f"{rule['splits']['test']['coverage']:.12f}",
                    rule["accepted_95_rule_only"],
                ])

    report_lines = [
        "# Mendeley Multifile Manipulation Gate",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This gate streams Mendeley row-level wash-trading ML samples from `/tmp` and keeps only aggregate metrics, rule summaries, and hashes in the repo.",
        "",
        "## Result",
        "",
        f"- Accepted 95 `Manipulation`: {accepted_95}",
        f"- Gate: `{result['decision']['gate']}`",
        f"- Raw data committed: false",
        f"- Thresholds relaxed: false",
        f"- Runtime code changed: false",
        f"- Fresh calibration rerun: true",
        "",
        "## Files Evaluated",
        "",
    ]
    for fr in file_reports:
        if not fr.get("exists"):
            report_lines.append(f"- {fr['venue']}: missing in `/tmp`, skipped")
            continue
        best = fr.get("best_rules", [{}])[0]
        best_min = best.get("min_wilson95_lcb", 0.0)
        report_lines.append(
            f"- {fr['venue']}: rows {fr['rows']}, sha256_match {fr['sha256_matches']}, chronology `{fr['chronology_grade']}`, "
            f"accepted_rule_only {fr['accepted_95_rule_only']}, best_min_wilson95_lcb {best_min:.6f}"
        )
    report_lines.extend([
        "",
        "## Blockers",
        "",
    ])
    for blocker in blocked_reasons or ["none"]:
        report_lines.append(f"- {blocker}")
    report_lines.extend([
        "",
        "## Artifacts",
        "",
        "- Report JSON: `manipulation-gate/mendeley_multifile_manipulation_gate_report.json`",
        "- Rule summary CSV: `manipulation-gate/mendeley_multifile_rule_summary.csv`",
        "- Assertions: `checks/mendeley_multifile_manipulation_gate_assertions.out`",
    ])
    (OUT_DIR / "mendeley_multifile_manipulation_gate_report.md").write_text("\n".join(report_lines) + "\n")

    assertions = [
        f"RUN_ID {RUN_ID}",
        f"RAW_FILES_PRESENT {sum(1 for r in file_reports if r.get('exists'))}",
        f"ACCEPTED_95 {str(accepted_95).lower()}",
        f"GATE {result['decision']['gate']}",
        "THRESHOLDS_RELAXED false",
        "RUNTIME_CODE_CHANGED false",
        "FRESH_CALIBRATION_RERUN true",
        "TRADE_USABLE false",
        "RAW_DATA_COMMITTED false",
    ]
    for fr in file_reports:
        if fr.get("exists"):
            assertions.append(f"{fr['venue'].upper()}_ROWS {fr['rows']}")
            assertions.append(f"{fr['venue'].upper()}_SHA256_MATCH {str(fr['sha256_matches']).lower()}")
            assertions.append(f"{fr['venue'].upper()}_ACCEPTED_RULE_ONLY {str(fr['accepted_95_rule_only']).lower()}")
    (CHECK_DIR / "mendeley_multifile_manipulation_gate_assertions.out").write_text("\n".join(assertions) + "\n")


if __name__ == "__main__":
    main()
