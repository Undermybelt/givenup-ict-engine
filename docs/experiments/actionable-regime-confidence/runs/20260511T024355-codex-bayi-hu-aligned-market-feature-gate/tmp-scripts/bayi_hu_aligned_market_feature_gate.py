#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import os
import random
import re
import sys
import tarfile
import time
from pathlib import Path

import numpy as np


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T024355+0800-codex-bayi-hu-aligned-market-feature-gate"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T024355-codex-bayi-hu-aligned-market-feature-gate"
SAMPLE_ROOT = Path(os.environ.get("BAYI_GDRIVE_SAMPLE_ROOT", "/private/tmp/ict-regime-bayi-gdrive"))
SOURCE_REPO = Path(os.environ.get("BAYI_SOURCE_REPO", "/tmp/ict-regime-bayi-pd"))
SOURCE_URL = "https://github.com/Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency"
TRAIN_ARCHIVE = SAMPLE_ROOT / "train_sample.tar.gz"
TEST_ARCHIVE = SAMPLE_ROOT / "test_sample.tar.gz"
TRAIN_MEMBER = "train_sample.csv"
TEST_MEMBER = "test_sample.csv"
RNG_SEED = 20260511
RESERVOIR_MAX = 200_000
TOP_CANDIDATES = 120
FIT_SUPPORT_MIN = 120
CALIBRATION_SUPPORT_MIN = 120
TEST_SUPPORT_MIN = 60
COVERAGE_MIN = 0.03
QUANTILES = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.98, 0.99, 0.995, 0.998, 0.999]


def log(message: str) -> None:
    print(f"[bayi-hu-gate] {message}", file=sys.stderr, flush=True)


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024 * 8), b""):
            h.update(chunk)
    return h.hexdigest()


def load_columns() -> list[str]:
    loader = SOURCE_REPO / "TargetCoinPrediction/SeqModel/data_loader.py"
    if loader.exists():
        text = loader.read_text(encoding="utf-8", errors="replace")
        match = re.search(r'column_list = "([^"]+)"\.split', text)
        if match:
            return match.group(1).split(",")
    return ["label", "channel_id", "channel_id_new", "coin", "coin_id", "timestamp_unix", "length", "coin_id_seq", "feature_seq"] + [f"target_feature_{idx}" for idx in range(138)]


def wilson_lcb(successes: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    phat = successes / n
    denom = 1 + z * z / n
    center = phat + z * z / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return max(0.0, (center - margin) / denom)


def stat_block(positives: int, support: int, total_rows: int) -> dict:
    return {
        "support": int(support),
        "positives": int(positives),
        "precision": positives / support if support else 0.0,
        "wilson95_lcb": wilson_lcb(positives, support),
        "coverage": support / total_rows if total_rows else 0.0,
    }


def archive_lines(archive: Path, member: str):
    with tarfile.open(archive, "r:gz") as tf:
        extracted = tf.extractfile(member)
        if extracted is None:
            raise RuntimeError(f"missing member {member} in {archive}")
        for raw in extracted:
            yield raw.decode("utf-8", errors="replace").rstrip("\n")


def parse_meta(line: str) -> tuple[int, str, int] | None:
    parts = line.split(",", 9)
    if len(parts) < 10:
        return None
    try:
        return int(parts[0]), f"{parts[1]}|{parts[5]}", int(parts[5])
    except ValueError:
        return None


def parse_features(line: str, feature_count: int) -> tuple[int, str, np.ndarray] | None:
    parts = line.split(",")
    if len(parts) != 9 + feature_count:
        return None
    try:
        label = int(parts[0])
        event = f"{parts[1]}|{parts[5]}"
        values = [float(parts[6])]
        values.extend(float(value) for value in parts[9:])
        return label, event, np.array(values, dtype=np.float32)
    except ValueError:
        return None


def collect_train_events() -> dict:
    log("pass1 collecting train event chronology")
    events: dict[str, int] = {}
    rows = positives = bad_rows = 0
    ts_min = ts_max = None
    for row_number, line in enumerate(archive_lines(TRAIN_ARCHIVE, TRAIN_MEMBER), start=1):
        parsed = parse_meta(line)
        if parsed is None:
            bad_rows += 1
            continue
        label, event, timestamp = parsed
        rows += 1
        positives += 1 if label == 1 else 0
        previous = events.get(event)
        if previous is None or timestamp < previous:
            events[event] = timestamp
        ts_min = timestamp if ts_min is None else min(ts_min, timestamp)
        ts_max = timestamp if ts_max is None else max(ts_max, timestamp)
        if row_number % 250_000 == 0:
            log(f"pass1 rows_seen={row_number} events={len(events)}")
    event_order = sorted(events, key=lambda key: (events[key], key))
    split_at = int(len(event_order) * 0.70)
    return {
        "rows": rows,
        "positives": positives,
        "negatives": rows - positives,
        "bad_rows": bad_rows,
        "timestamp_min": ts_min,
        "timestamp_max": ts_max,
        "events": len(event_order),
        "fit_events": split_at,
        "calibration_events": len(event_order) - split_at,
        "fit_event_set": set(event_order[:split_at]),
    }


def collect_test_meta() -> dict:
    log("collecting test metadata")
    rows = positives = bad_rows = 0
    ts_min = ts_max = None
    for row_number, line in enumerate(archive_lines(TEST_ARCHIVE, TEST_MEMBER), start=1):
        parsed = parse_meta(line)
        if parsed is None:
            bad_rows += 1
            continue
        label, _, timestamp = parsed
        rows += 1
        positives += 1 if label == 1 else 0
        ts_min = timestamp if ts_min is None else min(ts_min, timestamp)
        ts_max = timestamp if ts_max is None else max(ts_max, timestamp)
        if row_number % 250_000 == 0:
            log(f"test meta rows_seen={row_number}")
    return {"rows": rows, "positives": positives, "negatives": rows - positives, "bad_rows": bad_rows, "timestamp_min": ts_min, "timestamp_max": ts_max}


def fit_reservoir(feature_count: int, fit_events: set[str]) -> tuple[np.ndarray, np.ndarray, dict]:
    log("pass2 sampling fit reservoir")
    rng = random.Random(RNG_SEED)
    sample_x: list[np.ndarray] = []
    sample_y: list[int] = []
    fit_rows = fit_pos = cal_rows = cal_pos = bad_rows = seen_fit = 0
    for row_number, line in enumerate(archive_lines(TRAIN_ARCHIVE, TRAIN_MEMBER), start=1):
        parsed = parse_features(line, feature_count)
        if parsed is None:
            bad_rows += 1
            continue
        label, event, values = parsed
        if event in fit_events:
            fit_rows += 1
            fit_pos += 1 if label == 1 else 0
            seen_fit += 1
            if len(sample_x) < RESERVOIR_MAX:
                sample_x.append(values)
                sample_y.append(label)
            else:
                j = rng.randrange(seen_fit)
                if j < RESERVOIR_MAX:
                    sample_x[j] = values
                    sample_y[j] = label
        else:
            cal_rows += 1
            cal_pos += 1 if label == 1 else 0
        if row_number % 250_000 == 0:
            log(f"pass2 rows_seen={row_number} fit={fit_rows} cal={cal_rows} reservoir={len(sample_x)}")
    return np.vstack(sample_x), np.array(sample_y, dtype=np.int8), {
        "fit_rows": fit_rows,
        "fit_positives": fit_pos,
        "fit_negatives": fit_rows - fit_pos,
        "calibration_rows": cal_rows,
        "calibration_positives": cal_pos,
        "calibration_negatives": cal_rows - cal_pos,
        "bad_rows": bad_rows,
        "reservoir_rows": len(sample_x),
        "reservoir_positives": int(sum(sample_y)),
    }


def sample_stats(mask: np.ndarray, y: np.ndarray) -> dict:
    support = int(mask.sum())
    positives = int(((y == 1) & mask).sum())
    return stat_block(positives, support, len(y))


def select_candidates(x: np.ndarray, y: np.ndarray, feature_names: list[str]) -> list[dict]:
    log("selecting threshold candidates from reservoir")
    candidates: list[dict] = []
    for feature_index, feature in enumerate(feature_names):
        values = x[:, feature_index]
        finite = values[np.isfinite(values)]
        if finite.size == 0:
            continue
        thresholds = sorted(set(float(value) for value in np.quantile(finite, QUANTILES)))
        for threshold in thresholds:
            for direction in ("ge", "le"):
                mask = values >= threshold if direction == "ge" else values <= threshold
                s = sample_stats(mask, y)
                if s["support"] < FIT_SUPPORT_MIN:
                    continue
                candidates.append({
                    "feature": feature,
                    "feature_index": feature_index,
                    "direction": direction,
                    "threshold": threshold,
                    "reservoir": s,
                    "rank_key": (s["wilson95_lcb"], s["precision"], s["positives"], s["support"]),
                })
    candidates.sort(key=lambda item: item["rank_key"], reverse=True)
    for rank, candidate in enumerate(candidates[:TOP_CANDIDATES], start=1):
        candidate["rank"] = rank
    log(f"selected {min(len(candidates), TOP_CANDIDATES)} / {len(candidates)} supported reservoir candidates")
    return candidates[:TOP_CANDIDATES]


def init_counts(candidates: list[dict]) -> list[dict]:
    return [{"support": 0, "positives": 0} for _ in candidates]


def update_counts(values: np.ndarray, label: int, candidates: list[dict], counts: list[dict]) -> None:
    for idx, candidate in enumerate(candidates):
        value = float(values[candidate["feature_index"]])
        if not math.isfinite(value):
            continue
        hit = value >= candidate["threshold"] if candidate["direction"] == "ge" else value <= candidate["threshold"]
        if hit:
            counts[idx]["support"] += 1
            counts[idx]["positives"] += 1 if label == 1 else 0


def evaluate_train(feature_count: int, fit_events: set[str], candidates: list[dict]) -> tuple[list[dict], list[dict], dict]:
    log("pass3 evaluating candidates on full train fit/calibration")
    fit_counts = init_counts(candidates)
    cal_counts = init_counts(candidates)
    rows = bad_rows = fit_rows = cal_rows = 0
    for row_number, line in enumerate(archive_lines(TRAIN_ARCHIVE, TRAIN_MEMBER), start=1):
        parsed = parse_features(line, feature_count)
        if parsed is None:
            bad_rows += 1
            continue
        label, event, values = parsed
        rows += 1
        if event in fit_events:
            fit_rows += 1
            update_counts(values, label, candidates, fit_counts)
        else:
            cal_rows += 1
            update_counts(values, label, candidates, cal_counts)
        if row_number % 250_000 == 0:
            log(f"pass3 train rows_seen={row_number}")
    return fit_counts, cal_counts, {"rows": rows, "bad_rows": bad_rows, "fit_rows": fit_rows, "calibration_rows": cal_rows}


def evaluate_test(feature_count: int, candidates: list[dict]) -> tuple[list[dict], dict]:
    log("pass4 evaluating candidates on official test")
    test_counts = init_counts(candidates)
    rows = bad_rows = 0
    for row_number, line in enumerate(archive_lines(TEST_ARCHIVE, TEST_MEMBER), start=1):
        parsed = parse_features(line, feature_count)
        if parsed is None:
            bad_rows += 1
            continue
        label, _, values = parsed
        rows += 1
        update_counts(values, label, candidates, test_counts)
        if row_number % 250_000 == 0:
            log(f"pass4 test rows_seen={row_number}")
    return test_counts, {"rows": rows, "bad_rows": bad_rows}


def summarize(candidates: list[dict], fit_counts: list[dict], cal_counts: list[dict], test_counts: list[dict], totals: dict) -> list[dict]:
    rows = []
    for idx, candidate in enumerate(candidates):
        fit = stat_block(fit_counts[idx]["positives"], fit_counts[idx]["support"], totals["fit_rows"])
        cal = stat_block(cal_counts[idx]["positives"], cal_counts[idx]["support"], totals["calibration_rows"])
        test = stat_block(test_counts[idx]["positives"], test_counts[idx]["support"], totals["test_rows"])
        accepted = (
            fit["support"] >= FIT_SUPPORT_MIN
            and cal["support"] >= CALIBRATION_SUPPORT_MIN
            and test["support"] >= TEST_SUPPORT_MIN
            and cal["coverage"] >= COVERAGE_MIN
            and test["coverage"] >= COVERAGE_MIN
            and fit["wilson95_lcb"] >= 0.95
            and cal["wilson95_lcb"] >= 0.95
            and test["wilson95_lcb"] >= 0.95
        )
        rows.append({
            "gate": "reservoir_selected_single_feature_threshold",
            "rank": candidate["rank"],
            "rule": f"{candidate['feature']} {'>=' if candidate['direction'] == 'ge' else '<='} {candidate['threshold']:.12g}",
            "feature": candidate["feature"],
            "direction": candidate["direction"],
            "threshold": candidate["threshold"],
            "reservoir": candidate["reservoir"],
            "fit": fit,
            "calibration": cal,
            "test": test,
            "accepted_95": accepted,
            "blocker": "accepted_95" if accepted else "fit_calibration_or_test_wilson_support_or_coverage_below_gate",
        })
    rows.sort(key=lambda row: (
        min(row["fit"]["wilson95_lcb"], row["calibration"]["wilson95_lcb"], row["test"]["wilson95_lcb"]),
        row["test"]["wilson95_lcb"],
        row["test"]["precision"],
        row["test"]["support"],
    ), reverse=True)
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = ["rank", "rule", "accepted_95", "blocker"]
    for split in ["reservoir", "fit", "calibration", "test"]:
        for key in ["support", "positives", "precision", "wilson95_lcb", "coverage"]:
            fields.append(f"{split}_{key}")
    with path.open("w", encoding="utf-8") as handle:
        handle.write(",".join(fields) + "\n")
        for row in rows:
            values = {
                "rank": row["rank"],
                "rule": json.dumps(row["rule"]),
                "accepted_95": str(row["accepted_95"]).lower(),
                "blocker": row["blocker"],
            }
            for split in ["reservoir", "fit", "calibration", "test"]:
                for key in ["support", "positives", "precision", "wilson95_lcb", "coverage"]:
                    values[f"{split}_{key}"] = row[split][key]
            handle.write(",".join(str(values[field]) for field in fields) + "\n")


def main() -> None:
    started = time.time()
    columns = load_columns()
    feature_count = len(columns) - 9
    feature_names = ["length"] + columns[9:]
    if feature_count != 138 or len(feature_names) != 139:
        raise RuntimeError(f"unexpected feature count: target={feature_count} names={len(feature_names)}")
    if not TRAIN_ARCHIVE.exists() or not TEST_ARCHIVE.exists():
        raise RuntimeError(f"missing Bayi-Hu archives under {SAMPLE_ROOT}")

    train_meta = collect_train_events()
    test_meta = collect_test_meta()
    reservoir_x, reservoir_y, split_meta = fit_reservoir(feature_count, train_meta["fit_event_set"])
    candidates = select_candidates(reservoir_x, reservoir_y, feature_names)
    fit_counts, cal_counts, train_eval_meta = evaluate_train(feature_count, train_meta["fit_event_set"], candidates)
    test_counts, test_eval_meta = evaluate_test(feature_count, candidates)
    totals = {"fit_rows": train_eval_meta["fit_rows"], "calibration_rows": train_eval_meta["calibration_rows"], "test_rows": test_eval_meta["rows"]}
    evaluations = summarize(candidates, fit_counts, cal_counts, test_counts, totals)
    accepted_gates = [row["rule"] for row in evaluations if row["accepted_95"]]
    accepted_95 = bool(accepted_gates)
    best = evaluations[0] if evaluations else None
    best_min_lcb = min(best["fit"]["wilson95_lcb"], best["calibration"]["wilson95_lcb"], best["test"]["wilson95_lcb"]) if best else 0.0

    decision = {
        "board_state": "blocked",
        "active_axis": "MainRegimeV3",
        "candidate_regime": "Manipulation",
        "accepted_95": accepted_95,
        "accepted_gates": accepted_gates,
        "manipulation_input_state": "accepted_direct_event_aligned_target_coin_samples" if accepted_95 else "direct_event_aligned_target_coin_samples_below_95",
        "thresholds_relaxed": False,
        "runtime_code_changed": False,
        "trade_usable": False,
        "gate": "accepted_95" if accepted_95 else "blocked_bayi_hu_aligned_market_features_below_95",
        "blocker": "accepted_95" if accepted_95 else "Bayi-Hu aligned target-coin samples are direct event-aligned manipulation evidence, but the bounded streaming scalar target-feature gate did not pass unchanged 95% Wilson lower bounds with support and 3% coverage floors on calibration and official test.",
        "next_action": "Materialize the full MainRegimeV3 schema/crosswalk and rerun unchanged 95% chronological root gates for BullExpansion, BearExpansion, SidewaysConsolidation, CrisisStress, and Manipulation; for Manipulation, the next non-proxy slice should use a sequence/ranking gate over coin_id_seq and feature_seq rather than only scalar target features.",
    }

    out_dir = RUN_ROOT / "aligned-feature-gate"
    checks_dir = RUN_ROOT / "checks"
    out_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)
    report_json = out_dir / "bayi_hu_aligned_market_feature_gate_report.json"
    report_md = out_dir / "bayi_hu_aligned_market_feature_gate_report.md"
    summary_csv = out_dir / "bayi_hu_aligned_market_feature_gate_summary.csv"
    assertions = checks_dir / "bayi_hu_aligned_market_feature_gate_assertions.out"

    source = {
        "url": SOURCE_URL,
        "sample_root": str(SAMPLE_ROOT),
        "train_archive_bytes": TRAIN_ARCHIVE.stat().st_size,
        "test_archive_bytes": TEST_ARCHIVE.stat().st_size,
        "train_member_uncompressed_bytes": 5712551648,
        "test_member_uncompressed_bytes": 2704964353,
        "train_archive_sha256": sha256_file(TRAIN_ARCHIVE),
        "test_archive_sha256": sha256_file(TEST_ARCHIVE),
        "raw_csv_extracted_to_repo": False,
    }
    train_public = {key: value for key, value in train_meta.items() if key != "fit_event_set"}
    report = {
        "run_id": RUN_ID,
        "source": source,
        "dataset": {
            "axis_note": "Executed after the MainRegimeV3 reset. This run evaluates only direct-event-aligned Manipulation evidence and does not reissue BullExpansion, BearExpansion, SidewaysConsolidation, or CrisisStress.",
            "columns": len(columns),
            "target_features_used": len(feature_names),
            "train_archive": train_public,
            "test_archive": test_meta,
            "train_calibration_split": split_meta,
            "train_eval": train_eval_meta,
            "test_eval": test_eval_meta,
            "chronology_note": "Official test archive is held out. Fit/calibration split is by sorted channel_id|timestamp event within the official train sample.",
            "reservoir_seed": RNG_SEED,
            "reservoir_max": RESERVOIR_MAX,
            "top_candidates": TOP_CANDIDATES,
        },
        "gate_contract": {
            "fit_support_min": FIT_SUPPORT_MIN,
            "calibration_support_min": CALIBRATION_SUPPORT_MIN,
            "test_support_min": TEST_SUPPORT_MIN,
            "coverage_min": COVERAGE_MIN,
            "required_lcb": 0.95,
            "future_or_target_leakage_allowed": False,
            "thresholds_relaxed": False,
        },
        "evaluations": evaluations,
        "decision": decision,
        "elapsed_seconds": round(time.time() - started, 3),
    }
    report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_csv(summary_csv, evaluations)

    lines = [
        "# Bayi-Hu Aligned Market-Feature Manipulation Gate",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Source",
        f"- URL: `{SOURCE_URL}`",
        f"- Sample root in tmp: `{SAMPLE_ROOT}`",
        f"- Train archive SHA-256: `{source['train_archive_sha256']}`",
        f"- Test archive SHA-256: `{source['test_archive_sha256']}`",
        "- Raw CSV extracted or committed to repo: false.",
        "",
        "## Dataset",
        f"- Train rows: {train_meta['rows']} with {train_meta['positives']} positives and {train_meta['negatives']} negatives.",
        f"- Test rows: {test_meta['rows']} with {test_meta['positives']} positives and {test_meta['negatives']} negatives.",
        f"- Train timestamp range: {train_meta['timestamp_min']} to {train_meta['timestamp_max']}.",
        f"- Test timestamp range: {test_meta['timestamp_min']} to {test_meta['timestamp_max']}.",
        f"- Fit/calibration event split: {train_meta['fit_events']} / {train_meta['calibration_events']} events.",
        f"- Fit rows: {split_meta['fit_rows']}; calibration rows: {split_meta['calibration_rows']}; reservoir rows: {split_meta['reservoir_rows']}.",
        f"- Target features used: {len(feature_names)}; sequence fields not used in this bounded target-feature gate.",
        "- Axis note: this is a MainRegimeV3 `Manipulation` readback only; it does not reissue `BullExpansion`, `BearExpansion`, `SidewaysConsolidation`, or `CrisisStress`.",
        "",
        "## Best Gate Rows",
        "",
    ]
    for row in evaluations[:10]:
        lines.append(
            "- rank={rank} accepted_95={accepted} rule=`{rule}` min_lcb={min_lcb:.6f} fit_lcb={fit_lcb:.6f} cal_lcb={cal_lcb:.6f} test_lcb={test_lcb:.6f} cal_support={cal_support} test_support={test_support} cal_cov={cal_cov:.6f} test_cov={test_cov:.6f}".format(
                rank=row["rank"],
                accepted=str(row["accepted_95"]).lower(),
                rule=row["rule"],
                min_lcb=min(row["fit"]["wilson95_lcb"], row["calibration"]["wilson95_lcb"], row["test"]["wilson95_lcb"]),
                fit_lcb=row["fit"]["wilson95_lcb"],
                cal_lcb=row["calibration"]["wilson95_lcb"],
                test_lcb=row["test"]["wilson95_lcb"],
                cal_support=row["calibration"]["support"],
                test_support=row["test"]["support"],
                cal_cov=row["calibration"]["coverage"],
                test_cov=row["test"]["coverage"],
            )
        )
    lines.extend([
        "",
        "## Decision",
        f"- Accepted 95 MainRegimeV3 `Manipulation` root: {str(accepted_95).lower()}.",
        f"- Best min full-split LCB: `{best_min_lcb:.6f}`.",
        f"- Best rule: `{best['rule'] if best else 'none'}`.",
        "- Runtime code changed: false.",
        "- Thresholds relaxed: false.",
        "- Trade usable: false.",
        "",
        decision["blocker"],
        "",
        f"Next: {decision['next_action']}",
    ])
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    checks = [
        f"RUN_ID {RUN_ID}",
        "ACTIVE_AXIS MainRegimeV3",
        "CANDIDATE_REGIME Manipulation",
        f"TRAIN_ROWS {train_meta['rows']}",
        f"TRAIN_POSITIVES {train_meta['positives']}",
        f"TEST_ROWS {test_meta['rows']}",
        f"TEST_POSITIVES {test_meta['positives']}",
        f"RESERVOIR_ROWS {split_meta['reservoir_rows']}",
        f"CANDIDATES_EVALUATED {len(evaluations)}",
        f"BEST_RULE {best['rule'] if best else 'none'}",
        f"BEST_MIN_LCB {best_min_lcb:.6f}",
        f"BEST_CAL_LCB {best['calibration']['wilson95_lcb'] if best else 0.0:.6f}",
        f"BEST_TEST_LCB {best['test']['wilson95_lcb'] if best else 0.0:.6f}",
        f"ACCEPTED_95 {str(accepted_95).lower()}",
        "THRESHOLDS_RELAXED false",
        "RUNTIME_CODE_CHANGED false",
        "TRADE_USABLE false",
        f"GATE {decision['gate']}",
    ]
    assertions.write_text("\n".join(checks) + "\n", encoding="utf-8")
    (RUN_ROOT / "README.md").write_text(
        "\n".join([
            "# Bayi-Hu Aligned Market-Feature Manipulation Gate",
            "",
            f"Run id: `{RUN_ID}`",
            f"- report: `{repo_rel(report_json)}`",
            f"- summary: `{repo_rel(summary_csv)}`",
            f"- assertions: `{repo_rel(assertions)}`",
            f"- sample root in tmp: `{SAMPLE_ROOT}`",
        ]) + "\n",
        encoding="utf-8",
    )
    log(f"done accepted_95={accepted_95} best_min_lcb={best_min_lcb:.6f} elapsed={report['elapsed_seconds']}s")


if __name__ == "__main__":
    main()
