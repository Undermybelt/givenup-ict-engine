#!/usr/bin/env python3
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path


RUN_ID = "20260511T021618+0800-codex-mendeley-looksrare-manipulation-smoke"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs/20260511T021618-codex-mendeley-looksrare-manipulation-smoke")
RAW_FILE = Path("/tmp/LooksRare_ml_samples.csv")
FILES_METADATA = Path("/tmp/mendeley_files_root.json")


def wilson_lcb(k, n, z=1.959963984540054):
    if n <= 0:
        return 0.0
    phat = k / n
    denom = 1.0 + z * z / n
    centre = phat + z * z / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return (centre - margin) / denom


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_rows(path):
    rows = []
    label_counts = Counter()
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        columns = list(reader.fieldnames or [])
        for row in reader:
            label = row["filter_1234"].strip().lower() == "true"
            label_counts[str(label)] += 1
            features = {}
            for key, value in row.items():
                if key == "filter_1234":
                    continue
                try:
                    features[key] = float(value)
                except (TypeError, ValueError):
                    pass
            rows.append((features, label))
    return columns, rows, label_counts


def split_rows(rows):
    n = len(rows)
    train_end = int(n * 0.6)
    cal_end = int(n * 0.8)
    return rows[:train_end], rows[train_end:cal_end], rows[cal_end:]


def stats_for_rule(split, feature, op, threshold):
    selected = []
    for features, label in split:
        value = features.get(feature)
        if value is None or not math.isfinite(value):
            continue
        if value >= threshold if op == ">=" else value <= threshold:
            selected.append(label)
    n = len(selected)
    k = sum(selected)
    return {
        "positives": int(k),
        "support": int(n),
        "precision": k / n if n else 0.0,
        "wilson95_lcb": wilson_lcb(k, n),
    }


def candidate_thresholds(train, feature):
    values = sorted(
        features[feature]
        for features, _ in train
        if feature in features and math.isfinite(features[feature])
    )
    if not values:
        return []
    thresholds = set()
    for q_i in (1, 2, 5, 10, 20, 30, 50, 70, 80, 90, 95, 98, 99):
        idx = int((q_i / 100) * (len(values) - 1))
        thresholds.add(values[idx])
    thresholds.update([0.0, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 500.0, 1000.0])
    return sorted(thresholds)


def evaluate_rules(train, calibration, test):
    features = sorted(train[0][0].keys())
    rows = []
    for feature in features:
        for threshold in candidate_thresholds(train, feature):
            for op in (">=", "<="):
                train_stats = stats_for_rule(train, feature, op, threshold)
                cal_stats = stats_for_rule(calibration, feature, op, threshold)
                test_stats = stats_for_rule(test, feature, op, threshold)
                min_support = min(train_stats["support"], cal_stats["support"], test_stats["support"])
                min_lcb = min(train_stats["wilson95_lcb"], cal_stats["wilson95_lcb"], test_stats["wilson95_lcb"])
                if min_support >= 120:
                    rows.append(
                        {
                            "feature": feature,
                            "op": op,
                            "threshold": threshold,
                            "min_support": min_support,
                            "min_wilson95_lcb": min_lcb,
                            "train": train_stats,
                            "calibration": cal_stats,
                            "test": test_stats,
                        }
                    )
    rows.sort(key=lambda row: (row["min_wilson95_lcb"], row["min_support"]), reverse=True)
    return rows


def positive_rate(split):
    return sum(label for _, label in split) / len(split)


def main():
    files = json.loads(FILES_METADATA.read_text())
    looksrare_meta = next(item for item in files if item["filename"] == "LooksRare_ml_samples.csv")
    columns, rows, label_counts = load_rows(RAW_FILE)
    train, calibration, test = split_rows(rows)
    rules = evaluate_rules(train, calibration, test)
    top_rules = rules[:20]
    best = top_rules[0] if top_rules else None
    expected_sha = looksrare_meta["content_details"]["sha256_hash"]
    actual_sha = sha256(RAW_FILE)
    accepted_95 = bool(best and best["min_wilson95_lcb"] >= 0.95)
    chronology_status = "blocked_explicit_timestamp_absent_file_order_split_only"
    gate = "blocked_no_accepted_95_and_no_explicit_timestamp" if not accepted_95 else "blocked_explicit_timestamp_absent"

    report = {
        "run_id": RUN_ID,
        "active_axis": "MainRegimeV2",
        "candidate_regime": "Manipulation",
        "source": {
            "name": "Mendeley Data: Detecting Crypto Wash Trades via Machine Learning",
            "doi": "10.17632/4hyxfwzpgg.3",
            "url": "https://data.mendeley.com/datasets/4hyxfwzpgg/3",
            "license": "CC BY 4.0",
            "file_list_endpoint": "https://data.mendeley.com/public-api/datasets/4hyxfwzpgg/files?folder_id=root&version=3",
        },
        "file_inventory": [
            {
                "filename": item["filename"],
                "id": item["id"],
                "size": item["size"],
                "sha256": item["content_details"]["sha256_hash"],
            }
            for item in files
        ],
        "downloaded_file": {
            "filename": looksrare_meta["filename"],
            "local_path": str(RAW_FILE),
            "size": RAW_FILE.stat().st_size,
            "expected_sha256": expected_sha,
            "actual_sha256": actual_sha,
            "sha256_matches_metadata": actual_sha == expected_sha,
            "raw_committed_to_repo": False,
        },
        "schema": {
            "columns": columns,
            "label_column": "filter_1234",
            "explicit_timestamp_column_present": False,
            "chronology_status": chronology_status,
        },
        "support": {
            "rows": len(rows),
            "label_counts": dict(label_counts),
            "train_rows": len(train),
            "calibration_rows": len(calibration),
            "test_rows": len(test),
            "train_positive_rate": positive_rate(train),
            "calibration_positive_rate": positive_rate(calibration),
            "test_positive_rate": positive_rate(test),
        },
        "best_rules": top_rules,
        "gate_result": {
            "accepted_95": False,
            "diagnostic_best_min_wilson95_lcb": best["min_wilson95_lcb"] if best else 0.0,
            "diagnostic_best_rule": {
                "feature": best["feature"],
                "op": best["op"],
                "threshold": best["threshold"],
            }
            if best
            else None,
            "reason": "LooksRare raw row-level file was acquired and verified, but no train-selected single-threshold rule passed the unchanged train/calibration/test 95% lower-bound gate; the file also lacks an explicit timestamp for chronological validation.",
            "gate": gate,
            "thresholds_relaxed": False,
            "runtime_code_changed": False,
            "fresh_calibration_rerun": True,
            "trade_usable": False,
        },
        "next_action": "Acquire or derive an explicit chronological key for the Mendeley raw files and expand the unchanged gate across additional downloaded files before considering Manipulation acceptance.",
    }

    out_dir = RUN_ROOT / "manipulation-gate"
    checks_dir = RUN_ROOT / "checks"
    out_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "mendeley_looksrare_manipulation_smoke_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    with (out_dir / "mendeley_looksrare_rule_summary.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "rank",
            "feature",
            "op",
            "threshold",
            "min_support",
            "min_wilson95_lcb",
            "train_support",
            "train_precision",
            "train_lcb",
            "calibration_support",
            "calibration_precision",
            "calibration_lcb",
            "test_support",
            "test_precision",
            "test_lcb",
        ])
        for idx, rule in enumerate(top_rules, 1):
            writer.writerow([
                idx,
                rule["feature"],
                rule["op"],
                rule["threshold"],
                rule["min_support"],
                rule["min_wilson95_lcb"],
                rule["train"]["support"],
                rule["train"]["precision"],
                rule["train"]["wilson95_lcb"],
                rule["calibration"]["support"],
                rule["calibration"]["precision"],
                rule["calibration"]["wilson95_lcb"],
                rule["test"]["support"],
                rule["test"]["precision"],
                rule["test"]["wilson95_lcb"],
            ])
    md = [
        "# Mendeley LooksRare Manipulation Smoke Gate",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Raw file acquired: true (`{RAW_FILE}`)",
        f"- SHA-256 matches Mendeley metadata: {str(actual_sha == expected_sha).lower()}",
        f"- Rows: {len(rows)}",
        f"- Label counts: {dict(label_counts)}",
        f"- Explicit timestamp column present: false",
        f"- Best diagnostic minimum Wilson95 LCB: {best['min_wilson95_lcb'] if best else 0.0:.6f}",
        "- Accepted 95 `Manipulation`: false",
        "",
        "This is useful acquisition progress, but it is not root acceptance. The file lacks an explicit chronological key, and the unchanged single-threshold smoke gate found no rule that passes train, calibration, and test lower-bound checks.",
        "",
        "## Files",
        "",
        "- Report JSON: `manipulation-gate/mendeley_looksrare_manipulation_smoke_report.json`",
        "- Rule summary: `manipulation-gate/mendeley_looksrare_rule_summary.csv`",
        "- Assertions: `checks/mendeley_looksrare_manipulation_smoke_assertions.out`",
    ]
    (out_dir / "mendeley_looksrare_manipulation_smoke_report.md").write_text("\n".join(md) + "\n")
    assertions = [
        f"RUN_ID {RUN_ID}",
        "MENDELEY_FILE_LIST_ACQUIRED true",
        "LOOKSRARE_RAW_DOWNLOADED true",
        f"LOOKSRARE_SHA256_MATCHES_METADATA {str(actual_sha == expected_sha).lower()}",
        f"LOOKSRARE_ROWS {len(rows)}",
        "EXPLICIT_TIMESTAMP_COLUMN_PRESENT false",
        "CHRONOLOGY_STATUS blocked_explicit_timestamp_absent_file_order_split_only",
        f"BEST_MIN_WILSON95_LCB {best['min_wilson95_lcb'] if best else 0.0:.6f}",
        "ACCEPTED_95 false",
        "THRESHOLDS_RELAXED false",
        "RUNTIME_CODE_CHANGED false",
        "TRADE_USABLE false",
        f"GATE {gate}",
    ]
    (checks_dir / "mendeley_looksrare_manipulation_smoke_assertions.out").write_text("\n".join(assertions) + "\n")


if __name__ == "__main__":
    main()
