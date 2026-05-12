#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
import tarfile
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T043519+0800-codex-bayi-sequence-manipulation-gate"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T043519-codex-bayi-sequence-manipulation-gate"
SAMPLE_ROOT = Path(os.environ.get("BAYI_GDRIVE_SAMPLE_ROOT", "/private/tmp/ict-regime-bayi-gdrive"))
SOURCE_REPO = Path(os.environ.get("BAYI_SOURCE_REPO", "/tmp/ict-regime-bayi-pd"))
SOURCE_URL = "https://github.com/Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency"
TRAIN_ARCHIVE = SAMPLE_ROOT / "train_sample.tar.gz"
TEST_ARCHIVE = SAMPLE_ROOT / "test_sample.tar.gz"
TRAIN_MEMBER = "train_sample.csv"
TEST_MEMBER = "test_sample.csv"

MAX_SEQ_EVENTS = 10
FIT_EVENT_FRACTION = 0.70
ROW_FIT_SUPPORT_MIN = 120
ROW_CALIBRATION_SUPPORT_MIN = 120
ROW_TEST_SUPPORT_MIN = 60
EVENT_SUPPORT_MIN = 75
COVERAGE_MIN = 0.03
REQUIRED_LCB = 0.95
Z95 = 1.959963984540054
RNG_SEED = 20260511
ROW_THRESHOLD_QUANTILES = [
    0.50,
    0.60,
    0.70,
    0.80,
    0.90,
    0.95,
    0.975,
    0.99,
    0.995,
    0.998,
    0.999,
    0.9995,
    0.9999,
]
EVENT_SCORE_QUANTILES = [0.00, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95]
EVENT_MARGIN_QUANTILES = [0.00, 0.25, 0.50, 0.75, 0.90, 0.95]
HIT_K_VALUES = [1, 3, 5, 10, 20, 30, 50]
LOG_ODDS_FEATURE_QUANTILES = [0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.98, 0.99]
LOG_ODDS_BIN_QUANTILES = [0.0, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.0]
MAX_LOG_ODDS_FEATURES = 80
CALIBRATION_BINS = 20


@dataclass
class Dataset:
    name: str
    labels: np.ndarray
    events: np.ndarray
    timestamps: np.ndarray
    sequence_x: np.ndarray
    combined_x: np.ndarray
    rows: int
    positives: int
    bad_rows: int
    timestamp_min: int | None
    timestamp_max: int | None
    event_count: int


@dataclass
class LogOddsScorer:
    name: str
    feature_set: str
    feature_indices: list[int]
    feature_names: list[str]
    bin_edges: list[np.ndarray]
    bin_deltas: list[np.ndarray]
    base_logit: float
    feature_rankings: list[dict[str, Any]]

    def score(self, x: np.ndarray) -> np.ndarray:
        scores = np.full(len(x), self.base_logit, dtype=np.float64)
        for feature_index, edges, deltas in zip(self.feature_indices, self.bin_edges, self.bin_deltas):
            values = x[:, feature_index]
            bins = np.searchsorted(edges[1:-1], values, side="right")
            bins = np.clip(bins, 0, len(deltas) - 1)
            scores += deltas[bins]
        return scores


@dataclass
class ProbabilityCalibrator:
    edges: np.ndarray
    probabilities: np.ndarray
    raw_bin_stats: list[dict[str, Any]]

    def transform(self, scores: np.ndarray) -> np.ndarray:
        bins = np.searchsorted(self.edges[1:-1], scores, side="right")
        bins = np.clip(bins, 0, len(self.probabilities) - 1)
        return self.probabilities[bins]


def log(message: str) -> None:
    print(f"[bayi-sequence-gate] {message}", file=sys.stderr, flush=True)


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
    return ["label", "channel_id", "channel_id_new", "coin", "coin_id", "timestamp_unix", "length", "coin_id_seq", "feature_seq"] + [f"pre_feature_{idx}" for idx in range(138)]


def wilson_lcb(successes: int, n: int, z: float = Z95) -> float:
    if n <= 0:
        return 0.0
    phat = successes / n
    denom = 1.0 + z * z / n
    center = phat + z * z / (2.0 * n)
    margin = z * math.sqrt((phat * (1.0 - phat) + z * z / (4.0 * n)) / n)
    return max(0.0, (center - margin) / denom)


def stat_block(positives: int, support: int, total_rows: int) -> dict[str, Any]:
    return {
        "support": int(support),
        "positives": int(positives),
        "precision": positives / support if support else 0.0,
        "wilson95_lcb": wilson_lcb(positives, support),
        "coverage": support / total_rows if total_rows else 0.0,
    }


def ece_10bin(proba: np.ndarray, y: np.ndarray) -> float:
    if len(proba) == 0:
        return 0.0
    bins = np.linspace(0.0, 1.0, 11)
    ece = 0.0
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (proba >= lo) & (proba <= hi) if hi == 1.0 else (proba >= lo) & (proba < hi)
        if not mask.any():
            continue
        ece += float(mask.mean()) * abs(float(y[mask].mean()) - float(proba[mask].mean()))
    return ece


def calibration_summary(proba: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    bins = np.linspace(0.0, 1.0, 11)
    points = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (proba >= lo) & (proba <= hi) if hi == 1.0 else (proba >= lo) & (proba < hi)
        if not mask.any():
            continue
        points.append(
            {
                "lo": float(lo),
                "hi": float(hi),
                "rows": int(mask.sum()),
                "mean_predicted": float(proba[mask].mean()),
                "fraction_positive": float(y[mask].mean()),
            }
        )
    return {"ece_10bin": ece_10bin(proba, y), "curve_points": points}


def archive_lines(archive: Path, member: str):
    with tarfile.open(archive, "r:gz") as tf:
        extracted = tf.extractfile(member)
        if extracted is None:
            raise RuntimeError(f"missing member {member} in {archive}")
        for raw in extracted:
            yield raw.decode("utf-8", errors="replace").rstrip("\n")


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 1e-12:
        return 0.0
    return float(np.dot(a, b) / denom)


def parse_float_tail(entry: str) -> np.ndarray | None:
    parts = entry.rsplit("\x02", 9)
    tail = parts[-9:] if len(parts) >= 10 else entry.split("\x02")[-9:]
    if len(tail) != 9:
        return None
    try:
        values = np.array([float(value) for value in tail], dtype=np.float32)
    except ValueError:
        return None
    return np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)


def sequence_feature_names() -> list[str]:
    names = [
        "seq_len_raw",
        "seq_len_used",
        "seq_has_history",
        "seq_coin_match_count_all",
        "seq_coin_match_count_recent",
        "seq_coin_match_any",
        "seq_coin_match_recent_weight",
        "seq_coin_match_first_position_norm",
        "seq_coin_match_last_position_norm",
    ]
    for prefix in [
        "target_tail9",
        "seq_recent_tail9",
        "seq_mean_tail9",
        "seq_std_tail9",
        "seq_max_tail9",
        "seq_min_tail9",
        "seq_weighted_mean_tail9",
        "target_minus_seq_mean_tail9",
        "abs_target_minus_seq_mean_tail9",
    ]:
        names.extend(f"{prefix}_{idx}" for idx in range(9))
    names.extend(
        [
            "target_seq_recent_cosine",
            "target_seq_mean_cosine",
            "target_seq_weighted_mean_cosine",
            "target_seq_min_l2",
            "target_seq_mean_l2",
            "target_seq_recent_l2",
            "target_seq_max_cosine",
            "target_seq_mean_abs_diff",
            "target_seq_max_abs_diff",
        ]
    )
    return names


SEQ_FEATURE_NAMES = sequence_feature_names()


def parse_sequence_features(coin_id: str, length: int, coin_id_seq: str, feature_seq: str, target_values: np.ndarray) -> np.ndarray:
    target_tail = np.nan_to_num(target_values[-9:].astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    coin_tokens = [] if coin_id_seq in ("", "0") else coin_id_seq.split("\t")
    feature_entries = [] if feature_seq in ("", "0") else feature_seq.split("\t")
    used_entries = feature_entries[:MAX_SEQ_EVENTS]

    rows: list[np.ndarray] = []
    for entry in used_entries:
        if not entry or entry == "0":
            continue
        parsed = parse_float_tail(entry)
        if parsed is not None:
            rows.append(parsed)

    match_positions_all = [idx for idx, token in enumerate(coin_tokens) if token == coin_id]
    match_positions_recent = [idx for idx, token in enumerate(coin_tokens[:MAX_SEQ_EVENTS]) if token == coin_id]
    match_weight = sum(1.0 / (idx + 1.0) for idx in match_positions_recent)
    first_pos_norm = 1.0 / (match_positions_recent[0] + 1.0) if match_positions_recent else 0.0
    last_pos_norm = 1.0 / (match_positions_recent[-1] + 1.0) if match_positions_recent else 0.0

    if rows:
        seq = np.vstack(rows).astype(np.float32)
        recent = seq[0]
        mean = seq.mean(axis=0)
        std = seq.std(axis=0)
        max_v = seq.max(axis=0)
        min_v = seq.min(axis=0)
        weights = 1.0 / (np.arange(len(seq), dtype=np.float32) + 1.0)
        weighted_mean = (seq * weights[:, None]).sum(axis=0) / weights.sum()
        diffs = seq - target_tail[None, :]
        l2_values = np.linalg.norm(diffs, axis=1)
        cos_values = np.array([cosine(target_tail, row) for row in seq], dtype=np.float32)
    else:
        seq = np.zeros((0, 9), dtype=np.float32)
        recent = np.zeros(9, dtype=np.float32)
        mean = np.zeros(9, dtype=np.float32)
        std = np.zeros(9, dtype=np.float32)
        max_v = np.zeros(9, dtype=np.float32)
        min_v = np.zeros(9, dtype=np.float32)
        weighted_mean = np.zeros(9, dtype=np.float32)
        l2_values = np.array([], dtype=np.float32)
        cos_values = np.array([], dtype=np.float32)

    abs_diff_mean = np.abs(target_tail - mean)
    scalar_values = np.array(
        [
            float(length),
            float(len(rows)),
            1.0 if rows else 0.0,
            float(len(match_positions_all)),
            float(len(match_positions_recent)),
            1.0 if match_positions_all else 0.0,
            float(match_weight),
            float(first_pos_norm),
            float(last_pos_norm),
        ],
        dtype=np.float32,
    )
    tail_blocks = np.concatenate(
        [
            target_tail,
            recent,
            mean,
            std,
            max_v,
            min_v,
            weighted_mean,
            target_tail - mean,
            abs_diff_mean,
        ]
    ).astype(np.float32)
    similarity_values = np.array(
        [
            cosine(target_tail, recent),
            cosine(target_tail, mean),
            cosine(target_tail, weighted_mean),
            float(l2_values.min()) if l2_values.size else 0.0,
            float(np.linalg.norm(target_tail - mean)),
            float(np.linalg.norm(target_tail - recent)),
            float(cos_values.max()) if cos_values.size else 0.0,
            float(abs_diff_mean.mean()),
            float(abs_diff_mean.max()),
        ],
        dtype=np.float32,
    )
    return np.nan_to_num(np.concatenate([scalar_values, tail_blocks, similarity_values]), nan=0.0, posinf=0.0, neginf=0.0)


def parse_line(line: str, target_feature_count: int) -> tuple[int, str, int, np.ndarray, np.ndarray] | None:
    parts = line.split(",", 9)
    if len(parts) != 10:
        return None
    try:
        label = int(parts[0])
        coin_id = parts[4]
        timestamp = int(parts[5])
        length = int(float(parts[6]))
        target_values = np.fromstring(parts[9], sep=",", dtype=np.float32)
    except ValueError:
        return None
    if target_values.size != target_feature_count:
        return None
    target_values = np.nan_to_num(target_values, nan=0.0, posinf=0.0, neginf=0.0)
    sequence_values = parse_sequence_features(coin_id, length, parts[7], parts[8], target_values)
    event = f"{parts[1]}|{parts[5]}"
    return label, event, timestamp, sequence_values, np.concatenate([target_values, sequence_values]).astype(np.float32)


def load_dataset(name: str, archive: Path, member: str, target_feature_count: int) -> Dataset:
    labels: list[int] = []
    events: list[str] = []
    timestamps: list[int] = []
    sequence_rows: list[np.ndarray] = []
    combined_rows: list[np.ndarray] = []
    bad_rows = 0
    ts_min = None
    ts_max = None
    log(f"loading {name} from {archive}")
    for row_number, line in enumerate(archive_lines(archive, member), start=1):
        parsed = parse_line(line, target_feature_count)
        if parsed is None:
            bad_rows += 1
            continue
        label, event, timestamp, sequence_values, combined_values = parsed
        labels.append(label)
        events.append(event)
        timestamps.append(timestamp)
        sequence_rows.append(sequence_values)
        combined_rows.append(combined_values)
        ts_min = timestamp if ts_min is None else min(ts_min, timestamp)
        ts_max = timestamp if ts_max is None else max(ts_max, timestamp)
        if row_number % 25_000 == 0:
            log(f"{name} rows_seen={row_number} parsed={len(labels)}")

    y = np.array(labels, dtype=np.int8)
    event_array = np.array(events, dtype=object)
    timestamp_array = np.array(timestamps, dtype=np.int64)
    sequence_x = np.vstack(sequence_rows).astype(np.float32) if sequence_rows else np.zeros((0, len(SEQ_FEATURE_NAMES)), dtype=np.float32)
    combined_x = np.vstack(combined_rows).astype(np.float32) if combined_rows else np.zeros((0, target_feature_count + len(SEQ_FEATURE_NAMES)), dtype=np.float32)
    return Dataset(
        name=name,
        labels=y,
        events=event_array,
        timestamps=timestamp_array,
        sequence_x=sequence_x,
        combined_x=combined_x,
        rows=int(len(y)),
        positives=int(y.sum()),
        bad_rows=bad_rows,
        timestamp_min=ts_min,
        timestamp_max=ts_max,
        event_count=int(len(set(events))),
    )


def build_fit_mask(train: Dataset) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    event_min_ts: dict[str, int] = {}
    for event, timestamp in zip(train.events, train.timestamps):
        previous = event_min_ts.get(event)
        if previous is None or int(timestamp) < previous:
            event_min_ts[event] = int(timestamp)
    ordered_events = sorted(event_min_ts, key=lambda event: (event_min_ts[event], event))
    fit_count = int(len(ordered_events) * FIT_EVENT_FRACTION)
    fit_events = set(ordered_events[:fit_count])
    fit_mask = np.array([event in fit_events for event in train.events], dtype=bool)
    calibration_mask = ~fit_mask
    meta = {
        "events": len(ordered_events),
        "fit_events": fit_count,
        "calibration_events": len(ordered_events) - fit_count,
        "fit_rows": int(fit_mask.sum()),
        "fit_positives": int(train.labels[fit_mask].sum()),
        "fit_negatives": int(fit_mask.sum() - train.labels[fit_mask].sum()),
        "calibration_rows": int(calibration_mask.sum()),
        "calibration_positives": int(train.labels[calibration_mask].sum()),
        "calibration_negatives": int(calibration_mask.sum() - train.labels[calibration_mask].sum()),
    }
    return fit_mask, calibration_mask, meta


def row_threshold_grid(scores: np.ndarray) -> list[float]:
    finite = scores[np.isfinite(scores)]
    if finite.size == 0:
        return [1.0]
    values = set(float(v) for v in np.quantile(finite, ROW_THRESHOLD_QUANTILES))
    values.update(float(v) for v in np.unique(finite))
    return sorted(values)


def score_threshold(scores: np.ndarray, y: np.ndarray, threshold: float, total_rows: int | None = None) -> dict[str, Any]:
    total = len(scores) if total_rows is None else total_rows
    mask = scores >= threshold
    support = int(mask.sum())
    positives = int(y[mask].sum()) if support else 0
    block = stat_block(positives, support, total)
    block["threshold"] = float(threshold)
    return block


def select_row_gate(
    model_name: str,
    feature_set: str,
    fit_scores: np.ndarray,
    fit_y: np.ndarray,
    cal_scores: np.ndarray,
    cal_y: np.ndarray,
    test_scores: np.ndarray,
    test_y: np.ndarray,
) -> dict[str, Any]:
    candidates = []
    for threshold in row_threshold_grid(cal_scores):
        fit = score_threshold(fit_scores, fit_y, threshold)
        cal = score_threshold(cal_scores, cal_y, threshold)
        test = score_threshold(test_scores, test_y, threshold)
        row = {
            "gate": "row_probability_threshold",
            "model": model_name,
            "feature_set": feature_set,
            "rule": f"calibrated_probability >= {threshold:.12g}",
            "threshold": float(threshold),
            "fit": fit,
            "calibration": cal,
            "test": test,
        }
        row["accepted_95"] = (
            fit["support"] >= ROW_FIT_SUPPORT_MIN
            and cal["support"] >= ROW_CALIBRATION_SUPPORT_MIN
            and test["support"] >= ROW_TEST_SUPPORT_MIN
            and cal["coverage"] >= COVERAGE_MIN
            and test["coverage"] >= COVERAGE_MIN
            and fit["wilson95_lcb"] >= REQUIRED_LCB
            and cal["wilson95_lcb"] >= REQUIRED_LCB
            and test["wilson95_lcb"] >= REQUIRED_LCB
        )
        row["blocker"] = "accepted_95" if row["accepted_95"] else "fit_calibration_or_test_wilson_support_or_coverage_below_gate"
        candidates.append(row)

    supported = [
        row
        for row in candidates
        if row["calibration"]["support"] >= ROW_CALIBRATION_SUPPORT_MIN
        and row["calibration"]["coverage"] >= COVERAGE_MIN
    ]
    pool = supported if supported else candidates
    best = max(
        pool,
        key=lambda row: (
            row["calibration"]["wilson95_lcb"],
            row["calibration"]["precision"],
            row["calibration"]["positives"],
            row["test"]["wilson95_lcb"],
            row["test"]["precision"],
            row["test"]["support"],
        ),
    )
    best["selection_note"] = "threshold selected on calibration split only"
    return best


def event_groups(events: np.ndarray, y: np.ndarray, scores: np.ndarray) -> list[dict[str, Any]]:
    grouped: dict[str, list[tuple[float, int]]] = defaultdict(list)
    for event, label, score in zip(events, y, scores):
        grouped[str(event)].append((float(score), int(label)))
    summaries: list[dict[str, Any]] = []
    for event, rows in grouped.items():
        rows.sort(key=lambda item: item[0], reverse=True)
        top_score = rows[0][0]
        second_score = rows[1][0] if len(rows) > 1 else 0.0
        hit_at = {}
        for k in HIT_K_VALUES:
            hit_at[str(k)] = int(any(label == 1 for _, label in rows[: min(k, len(rows))]))
        summaries.append(
            {
                "event": event,
                "candidates": len(rows),
                "top_score": top_score,
                "margin": top_score - second_score,
                "top_label": rows[0][1],
                "positive_count": sum(label for _, label in rows),
                "hit_at": hit_at,
            }
        )
    return summaries


def event_stat(selected: list[dict[str, Any]], total_events: int, k: int = 1) -> dict[str, Any]:
    successes = int(sum(event["hit_at"][str(k)] for event in selected))
    support = len(selected)
    return stat_block(successes, support, total_events)


def unconditional_hit_rates(model_name: str, feature_set: str, summaries: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    total = len(summaries)
    rows = []
    for k in HIT_K_VALUES:
        stats = event_stat(summaries, total, k)
        rows.append(
            {
                "split": split,
                "model": model_name,
                "feature_set": feature_set,
                "gate": f"event_hit_at_{k}_diagnostic",
                "root_eligible": k == 1,
                "support": stats["support"],
                "hits": stats["positives"],
                "hit_rate": stats["precision"],
                "wilson95_lcb": stats["wilson95_lcb"],
                "coverage": stats["coverage"],
            }
        )
    return rows


def select_event_gate(
    model_name: str,
    feature_set: str,
    cal_summaries: list[dict[str, Any]],
    test_summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    cal_scores = np.array([event["top_score"] for event in cal_summaries], dtype=np.float64)
    cal_margins = np.array([event["margin"] for event in cal_summaries], dtype=np.float64)
    score_thresholds = sorted(set(float(value) for value in np.quantile(cal_scores, EVENT_SCORE_QUANTILES))) if cal_scores.size else [1.0]
    margin_thresholds = sorted(set(float(value) for value in np.quantile(cal_margins, EVENT_MARGIN_QUANTILES))) if cal_margins.size else [0.0]
    candidates = []
    for score_threshold in score_thresholds:
        for margin_threshold in margin_thresholds:
            cal_selected = [
                event
                for event in cal_summaries
                if event["top_score"] >= score_threshold and event["margin"] >= margin_threshold
            ]
            test_selected = [
                event
                for event in test_summaries
                if event["top_score"] >= score_threshold and event["margin"] >= margin_threshold
            ]
            cal = event_stat(cal_selected, len(cal_summaries), 1)
            test = event_stat(test_selected, len(test_summaries), 1)
            row = {
                "gate": "event_top1_score_margin_threshold",
                "model": model_name,
                "feature_set": feature_set,
                "root_eligible": True,
                "rule": f"event_top1_score >= {score_threshold:.12g} AND event_top1_margin >= {margin_threshold:.12g}",
                "top1_score_threshold": score_threshold,
                "top1_margin_threshold": margin_threshold,
                "calibration": cal,
                "test": test,
            }
            row["accepted_95"] = (
                cal["support"] >= EVENT_SUPPORT_MIN
                and test["support"] >= EVENT_SUPPORT_MIN
                and cal["coverage"] >= COVERAGE_MIN
                and test["coverage"] >= COVERAGE_MIN
                and cal["wilson95_lcb"] >= REQUIRED_LCB
                and test["wilson95_lcb"] >= REQUIRED_LCB
            )
            row["blocker"] = "accepted_95" if row["accepted_95"] else "calibration_or_test_event_top1_wilson_support_or_coverage_below_gate"
            candidates.append(row)
    supported = [
        row
        for row in candidates
        if row["calibration"]["support"] >= EVENT_SUPPORT_MIN and row["calibration"]["coverage"] >= COVERAGE_MIN
    ]
    pool = supported if supported else candidates
    best = max(
        pool,
        key=lambda row: (
            row["calibration"]["wilson95_lcb"],
            row["calibration"]["precision"],
            row["calibration"]["positives"],
            row["test"]["wilson95_lcb"],
            row["test"]["precision"],
            row["test"]["support"],
        ),
    )
    best["selection_note"] = "score and margin thresholds selected on calibration events only"
    return best


def clipped_logit(p: float) -> float:
    p = min(max(p, 1e-9), 1.0 - 1e-9)
    return math.log(p / (1.0 - p))


def feature_threshold_rankings(x: np.ndarray, y: np.ndarray, feature_names: list[str]) -> list[dict[str, Any]]:
    rankings: list[dict[str, Any]] = []
    total_rows = len(y)
    for feature_index, feature_name in enumerate(feature_names):
        values = x[:, feature_index]
        finite = values[np.isfinite(values)]
        if finite.size < ROW_FIT_SUPPORT_MIN or float(np.nanstd(finite)) <= 1e-12:
            continue
        thresholds = sorted(set(float(value) for value in np.quantile(finite, LOG_ODDS_FEATURE_QUANTILES)))
        best: dict[str, Any] | None = None
        for threshold in thresholds:
            for direction in ("ge", "le"):
                mask = values >= threshold if direction == "ge" else values <= threshold
                support = int(mask.sum())
                if support < ROW_FIT_SUPPORT_MIN or support / total_rows < COVERAGE_MIN:
                    continue
                positives = int(y[mask].sum())
                stats = stat_block(positives, support, total_rows)
                candidate = {
                    "feature_index": feature_index,
                    "feature": feature_name,
                    "direction": direction,
                    "threshold": threshold,
                    "fit": stats,
                }
                if best is None or (
                    stats["wilson95_lcb"],
                    stats["precision"],
                    stats["positives"],
                    -stats["support"],
                ) > (
                    best["fit"]["wilson95_lcb"],
                    best["fit"]["precision"],
                    best["fit"]["positives"],
                    -best["fit"]["support"],
                ):
                    best = candidate
        if best is not None:
            rankings.append(best)
    rankings.sort(
        key=lambda item: (
            item["fit"]["wilson95_lcb"],
            item["fit"]["precision"],
            item["fit"]["positives"],
            -item["fit"]["support"],
        ),
        reverse=True,
    )
    for rank, item in enumerate(rankings, start=1):
        item["rank"] = rank
    return rankings


def fit_log_odds_scorer(name: str, feature_set: str, x: np.ndarray, y: np.ndarray, feature_names: list[str]) -> LogOddsScorer:
    rankings = feature_threshold_rankings(x, y, feature_names)
    selected = rankings[:MAX_LOG_ODDS_FEATURES]
    base_rate = (float(y.sum()) + 0.5) / (len(y) + 1.0)
    base_logit = clipped_logit(base_rate)
    feature_indices: list[int] = []
    selected_names: list[str] = []
    bin_edges: list[np.ndarray] = []
    bin_deltas: list[np.ndarray] = []
    for item in selected:
        feature_index = int(item["feature_index"])
        values = x[:, feature_index]
        finite = values[np.isfinite(values)]
        edges = np.array(sorted(set(float(value) for value in np.quantile(finite, LOG_ODDS_BIN_QUANTILES))), dtype=np.float64)
        if edges.size < 2:
            continue
        bins = np.searchsorted(edges[1:-1], values, side="right")
        bins = np.clip(bins, 0, edges.size - 2)
        deltas = []
        for bin_index in range(edges.size - 1):
            mask = bins == bin_index
            n = int(mask.sum())
            pos = int(y[mask].sum()) if n else 0
            rate = (pos + 0.5) / (n + 1.0) if n else base_rate
            deltas.append(clipped_logit(rate) - base_logit)
        feature_indices.append(feature_index)
        selected_names.append(feature_names[feature_index])
        bin_edges.append(edges)
        bin_deltas.append(np.array(deltas, dtype=np.float64))
    return LogOddsScorer(
        name=name,
        feature_set=feature_set,
        feature_indices=feature_indices,
        feature_names=selected_names,
        bin_edges=bin_edges,
        bin_deltas=bin_deltas,
        base_logit=base_logit,
        feature_rankings=rankings[: min(len(rankings), 120)],
    )


def fit_probability_calibrator(raw_scores: np.ndarray, y: np.ndarray) -> ProbabilityCalibrator:
    finite = raw_scores[np.isfinite(raw_scores)]
    if finite.size == 0:
        return ProbabilityCalibrator(np.array([0.0, 1.0], dtype=np.float64), np.array([float(y.mean())], dtype=np.float64), [])
    quantiles = np.linspace(0.0, 1.0, CALIBRATION_BINS + 1)
    edges = np.array(sorted(set(float(value) for value in np.quantile(finite, quantiles))), dtype=np.float64)
    if edges.size < 2:
        edges = np.array([float(finite.min()) - 1e-9, float(finite.max()) + 1e-9], dtype=np.float64)
    bins = np.searchsorted(edges[1:-1], raw_scores, side="right")
    bins = np.clip(bins, 0, edges.size - 2)
    probabilities = []
    stats = []
    for bin_index in range(edges.size - 1):
        mask = bins == bin_index
        n = int(mask.sum())
        pos = int(y[mask].sum()) if n else 0
        probability = (pos + 0.5) / (n + 1.0) if n else (float(y.sum()) + 0.5) / (len(y) + 1.0)
        probabilities.append(probability)
        stats.append(
            {
                "bin": bin_index,
                "lo": float(edges[bin_index]),
                "hi": float(edges[bin_index + 1]),
                "rows": n,
                "positives": pos,
                "smoothed_probability": probability,
            }
        )
    return ProbabilityCalibrator(edges=edges, probabilities=np.array(probabilities, dtype=np.float64), raw_bin_stats=stats)


def score_with_calibration(
    scorer: LogOddsScorer,
    fit_x: np.ndarray,
    fit_y: np.ndarray,
    cal_x: np.ndarray,
    cal_y: np.ndarray,
    test_x: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    fit_raw = scorer.score(fit_x)
    cal_raw = scorer.score(cal_x)
    test_raw = scorer.score(test_x)
    calibrator = fit_probability_calibrator(cal_raw, cal_y)
    fit_scores = calibrator.transform(fit_raw)
    cal_scores = calibrator.transform(cal_raw)
    test_scores = calibrator.transform(test_raw)
    meta = {
        "raw_calibration": calibration_summary(1.0 / (1.0 + np.exp(-np.clip(cal_raw, -40.0, 40.0))), cal_y),
        "quantile_probability_calibration": calibration_summary(cal_scores, cal_y),
        "calibration_bins": calibrator.raw_bin_stats,
        "selected_feature_count": len(scorer.feature_indices),
    }
    return fit_scores, cal_scores, test_scores, meta


def scorer_specs(target_feature_names: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "name": "sequence_tail_logodds",
            "feature_set": "sequence_tail",
            "matrix": "sequence_x",
            "feature_names": SEQ_FEATURE_NAMES,
        },
        {
            "name": "combined_target_sequence_logodds",
            "feature_set": "target_pre_features_plus_sequence_tail",
            "matrix": "combined_x",
            "feature_names": target_feature_names + SEQ_FEATURE_NAMES,
        },
    ]


def evaluate_models(train: Dataset, test: Dataset, fit_mask: np.ndarray, calibration_mask: np.ndarray, target_feature_names: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    model_reports: list[dict[str, Any]] = []
    row_gates: list[dict[str, Any]] = []
    event_gates: list[dict[str, Any]] = []
    hit_rate_rows: list[dict[str, Any]] = []
    for spec in scorer_specs(target_feature_names):
        name = spec["name"]
        feature_set = spec["feature_set"]
        matrix_name = spec["matrix"]
        feature_names = spec["feature_names"]
        train_x = getattr(train, matrix_name)
        test_x = getattr(test, matrix_name)
        fit_x = train_x[fit_mask]
        fit_y = train.labels[fit_mask]
        cal_x = train_x[calibration_mask]
        cal_y = train.labels[calibration_mask]
        log(f"fitting {name} fit_rows={len(fit_y)} cal_rows={len(cal_y)} test_rows={len(test.labels)}")
        scorer = fit_log_odds_scorer(name, feature_set, fit_x, fit_y, feature_names)
        fit_scores, cal_scores, test_scores, calibration_meta = score_with_calibration(scorer, fit_x, fit_y, cal_x, cal_y, test_x)
        row_gate = select_row_gate(name, feature_set, fit_scores, fit_y, cal_scores, cal_y, test_scores, test.labels)
        row_gates.append(row_gate)
        cal_events = event_groups(train.events[calibration_mask], cal_y, cal_scores)
        test_events = event_groups(test.events, test.labels, test_scores)
        event_gate = select_event_gate(name, feature_set, cal_events, test_events)
        event_gates.append(event_gate)
        hit_rate_rows.extend(unconditional_hit_rates(name, feature_set, cal_events, "calibration"))
        hit_rate_rows.extend(unconditional_hit_rates(name, feature_set, test_events, "test"))
        model_reports.append(
            {
                "name": name,
                "feature_set": feature_set,
                "matrix": matrix_name,
                "fit_rows": int(len(fit_y)),
                "fit_positives": int(fit_y.sum()),
                "calibration_rows": int(len(cal_y)),
                "calibration_positives": int(cal_y.sum()),
                "test_rows": int(len(test.labels)),
                "test_positives": int(test.labels.sum()),
                "top_feature_rankings": scorer.feature_rankings[:25],
                "calibration_meta": calibration_meta,
                "row_gate": row_gate,
                "event_gate": event_gate,
            }
        )
        log(
            f"{name} row_cal_lcb={row_gate['calibration']['wilson95_lcb']:.6f} "
            f"row_test_lcb={row_gate['test']['wilson95_lcb']:.6f} "
            f"event_cal_lcb={event_gate['calibration']['wilson95_lcb']:.6f} "
            f"event_test_lcb={event_gate['test']['wilson95_lcb']:.6f}"
        )
    row_gates.sort(
        key=lambda row: (
            min(row["fit"]["wilson95_lcb"], row["calibration"]["wilson95_lcb"], row["test"]["wilson95_lcb"]),
            row["test"]["wilson95_lcb"],
            row["test"]["precision"],
            row["test"]["support"],
        ),
        reverse=True,
    )
    event_gates.sort(
        key=lambda row: (
            min(row["calibration"]["wilson95_lcb"], row["test"]["wilson95_lcb"]),
            row["test"]["wilson95_lcb"],
            row["test"]["precision"],
            row["test"]["support"],
        ),
        reverse=True,
    )
    return model_reports, row_gates, event_gates, hit_rate_rows


def write_csv(path: Path, row_gates: list[dict[str, Any]], event_gates: list[dict[str, Any]], hit_rates: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write("section,model,feature_set,rule,accepted_95,cal_lcb,test_lcb,cal_precision,test_precision,cal_support,test_support,cal_coverage,test_coverage\n")
        for row in row_gates:
            handle.write(
                ",".join(
                    [
                        "row_gate",
                        row["model"],
                        row["feature_set"],
                        json.dumps(row["rule"]),
                        str(row["accepted_95"]).lower(),
                        f"{row['calibration']['wilson95_lcb']:.12g}",
                        f"{row['test']['wilson95_lcb']:.12g}",
                        f"{row['calibration']['precision']:.12g}",
                        f"{row['test']['precision']:.12g}",
                        str(row["calibration"]["support"]),
                        str(row["test"]["support"]),
                        f"{row['calibration']['coverage']:.12g}",
                        f"{row['test']['coverage']:.12g}",
                    ]
                )
                + "\n"
            )
        for row in event_gates:
            handle.write(
                ",".join(
                    [
                        "event_top1_gate",
                        row["model"],
                        row["feature_set"],
                        json.dumps(row["rule"]),
                        str(row["accepted_95"]).lower(),
                        f"{row['calibration']['wilson95_lcb']:.12g}",
                        f"{row['test']['wilson95_lcb']:.12g}",
                        f"{row['calibration']['precision']:.12g}",
                        f"{row['test']['precision']:.12g}",
                        str(row["calibration"]["support"]),
                        str(row["test"]["support"]),
                        f"{row['calibration']['coverage']:.12g}",
                        f"{row['test']['coverage']:.12g}",
                    ]
                )
                + "\n"
            )
        for row in hit_rates:
            handle.write(
                ",".join(
                    [
                        row["gate"],
                        row["model"],
                        row["feature_set"],
                        row["split"],
                        "false",
                        f"{row['wilson95_lcb']:.12g}",
                        "",
                        f"{row['hit_rate']:.12g}",
                        "",
                        str(row["support"]),
                        "",
                        f"{row['coverage']:.12g}",
                        "",
                    ]
                )
                + "\n"
            )


def write_markdown(
    path: Path,
    source: dict[str, Any],
    train: Dataset,
    test: Dataset,
    split_meta: dict[str, Any],
    row_gates: list[dict[str, Any]],
    event_gates: list[dict[str, Any]],
    hit_rates: list[dict[str, Any]],
    decision: dict[str, Any],
) -> None:
    best_row = row_gates[0] if row_gates else None
    best_event = event_gates[0] if event_gates else None
    lines = [
        "# Bayi-Hu Sequence/Ranking Manipulation Gate",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Source",
        f"- URL: `{SOURCE_URL}`",
        f"- Sample root in tmp: `{SAMPLE_ROOT}`",
        f"- Train archive SHA-256: `{source['train_archive_sha256']}`",
        f"- Test archive SHA-256: `{source['test_archive_sha256']}`",
        "- Raw CSV extracted or committed to repo: false.",
        "- External source-review posture: public repo/data schema inspected; no external repo code executed; generated archives parsed as untrusted input.",
        "",
        "## Dataset",
        f"- Train rows: {train.rows} with {train.positives} positives and {train.rows - train.positives} negatives across {train.event_count} events.",
        f"- Test rows: {test.rows} with {test.positives} positives and {test.rows - test.positives} negatives across {test.event_count} events.",
        f"- Train timestamp range: {train.timestamp_min} to {train.timestamp_max}.",
        f"- Test timestamp range: {test.timestamp_min} to {test.timestamp_max}.",
        f"- Fit/calibration event split: {split_meta['fit_events']} / {split_meta['calibration_events']} events.",
        f"- Fit rows: {split_meta['fit_rows']}; calibration rows: {split_meta['calibration_rows']}.",
        f"- Sequence fields used: `coin_id_seq` plus the recent {MAX_SEQ_EVENTS} entries of `feature_seq`; each sequence entry uses the source model's last 9 market/social dimensions.",
        "- Blocked predictors: source label, raw channel id, raw channel embedding id, raw coin string/id, raw timestamp, future/next fields.",
        "",
        "## Best Row Gates",
        "",
    ]
    for row in row_gates:
        lines.append(
            "- model={model} accepted_95={accepted} rule=`{rule}` min_lcb={min_lcb:.6f} "
            "fit_lcb={fit_lcb:.6f} cal_lcb={cal_lcb:.6f} test_lcb={test_lcb:.6f} "
            "cal_support={cal_support} test_support={test_support} cal_cov={cal_cov:.6f} test_cov={test_cov:.6f}".format(
                model=row["model"],
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
    lines.extend(["", "## Best Event Top-1 Gates", ""])
    for row in event_gates:
        lines.append(
            "- model={model} accepted_95={accepted} rule=`{rule}` min_lcb={min_lcb:.6f} "
            "cal_lcb={cal_lcb:.6f} test_lcb={test_lcb:.6f} cal_hit={cal_hit:.6f} test_hit={test_hit:.6f} "
            "cal_events={cal_support} test_events={test_support}".format(
                model=row["model"],
                accepted=str(row["accepted_95"]).lower(),
                rule=row["rule"],
                min_lcb=min(row["calibration"]["wilson95_lcb"], row["test"]["wilson95_lcb"]),
                cal_lcb=row["calibration"]["wilson95_lcb"],
                test_lcb=row["test"]["wilson95_lcb"],
                cal_hit=row["calibration"]["precision"],
                test_hit=row["test"]["precision"],
                cal_support=row["calibration"]["support"],
                test_support=row["test"]["support"],
            )
        )
    lines.extend(["", "## Diagnostic Hit Rates", ""])
    for row in hit_rates:
        if row["split"] == "test" and row["gate"] in {"event_hit_at_1_diagnostic", "event_hit_at_3_diagnostic", "event_hit_at_5_diagnostic", "event_hit_at_10_diagnostic", "event_hit_at_20_diagnostic", "event_hit_at_30_diagnostic", "event_hit_at_50_diagnostic"}:
            lines.append(
                f"- split={row['split']} model={row['model']} gate={row['gate']} hit_rate={row['hit_rate']:.6f} wilson95_lcb={row['wilson95_lcb']:.6f} support={row['support']}"
            )
    lines.extend(
        [
            "",
            "## Decision",
            f"- Accepted 95 MainRegimeV2 direct-input-gated `Manipulation`: {str(decision['accepted_95']).lower()}.",
            f"- Best row rule: `{best_row['rule'] if best_row else 'none'}`.",
            f"- Best row min LCB: `{decision['best_row_min_lcb']:.6f}`.",
            f"- Best event top-1 rule: `{best_event['rule'] if best_event else 'none'}`.",
            f"- Best event top-1 min LCB: `{decision['best_event_min_lcb']:.6f}`.",
            "- Runtime code changed: false.",
            "- Thresholds relaxed: false.",
            "- Trade usable: false.",
            "",
            decision["blocker"],
            "",
            f"Next: {decision['next_action']}",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    started = time.time()
    columns = load_columns()
    target_feature_names = columns[9:]
    if len(target_feature_names) != 138:
        raise RuntimeError(f"unexpected target feature count: {len(target_feature_names)}")
    if len(SEQ_FEATURE_NAMES) != 99:
        raise RuntimeError(f"unexpected sequence feature count: {len(SEQ_FEATURE_NAMES)}")
    if not TRAIN_ARCHIVE.exists() or not TEST_ARCHIVE.exists():
        raise RuntimeError(f"missing Bayi-Hu archives under {SAMPLE_ROOT}")

    train = load_dataset("train", TRAIN_ARCHIVE, TRAIN_MEMBER, len(target_feature_names))
    test = load_dataset("test", TEST_ARCHIVE, TEST_MEMBER, len(target_feature_names))
    fit_mask, calibration_mask, split_meta = build_fit_mask(train)
    model_reports, row_gates, event_gates, hit_rates = evaluate_models(train, test, fit_mask, calibration_mask, target_feature_names)
    accepted_rows = [row for row in row_gates if row["accepted_95"]]
    accepted_events = [row for row in event_gates if row["accepted_95"]]
    accepted_95 = bool(accepted_rows or accepted_events)
    best_row = row_gates[0] if row_gates else None
    best_event = event_gates[0] if event_gates else None
    best_row_min_lcb = min(best_row["fit"]["wilson95_lcb"], best_row["calibration"]["wilson95_lcb"], best_row["test"]["wilson95_lcb"]) if best_row else 0.0
    best_event_min_lcb = min(best_event["calibration"]["wilson95_lcb"], best_event["test"]["wilson95_lcb"]) if best_event else 0.0

    out_dir = RUN_ROOT / "sequence-ranking-gate"
    checks_dir = RUN_ROOT / "checks"
    out_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)
    report_json = out_dir / "bayi_sequence_manipulation_gate_report.json"
    report_md = out_dir / "bayi_sequence_manipulation_gate_report.md"
    summary_csv = out_dir / "bayi_sequence_manipulation_gate_summary.csv"
    assertions = checks_dir / "bayi_sequence_manipulation_gate_assertions.out"

    source = {
        "url": SOURCE_URL,
        "source_repo": str(SOURCE_REPO),
        "sample_root": str(SAMPLE_ROOT),
        "train_archive_bytes": TRAIN_ARCHIVE.stat().st_size,
        "test_archive_bytes": TEST_ARCHIVE.stat().st_size,
        "train_archive_sha256": sha256_file(TRAIN_ARCHIVE),
        "test_archive_sha256": sha256_file(TEST_ARCHIVE),
        "raw_csv_extracted_to_repo": False,
        "external_code_executed": False,
        "security_review_verdict": "low_for_schema_read_and_data_parse_medium_if_source_scripts_were_executed",
    }
    decision = {
        "board_state": "blocked" if not accepted_95 else "accepted_95",
        "active_axis": "MainRegimeV2",
        "candidate_regime": "Manipulation",
        "accepted_95": accepted_95,
        "accepted_row_gates": [row["rule"] for row in accepted_rows],
        "accepted_event_gates": [row["rule"] for row in accepted_events],
        "manipulation_input_state": "direct_event_sequence_ranking_passed_95" if accepted_95 else "direct_event_sequence_ranking_below_95",
        "thresholds_relaxed": False,
        "runtime_code_changed": False,
        "trade_usable": False,
        "gate": "accepted_95" if accepted_95 else "blocked_bayi_sequence_ranking_below_95",
        "best_row_min_lcb": best_row_min_lcb,
        "best_event_min_lcb": best_event_min_lcb,
        "blocker": "accepted_95"
        if accepted_95
        else "Bayi-Hu supplies explicit positive pump-target rows, explicit negative candidate rows, and sequence fields (`coin_id_seq`, `feature_seq`), but the chronological sequence/ranking gates did not pass unchanged 95% Wilson lower bounds with support and coverage floors on calibration and official test.",
        "next_action": "Do not repeat scalar or Bayi-Hu sequence thresholding; acquire a stronger direct manipulation source with richer order-lifecycle/L2/L3/MBO/social/on-chain positives and negatives, or train a full sequence model only if it can preserve chronological calibration and the same 95 Wilson gate.",
    }

    report = {
        "run_id": RUN_ID,
        "source": source,
        "dataset": {
            "axis_note": "MainRegimeV2 direct-input-gated Manipulation only; Bull/Bear/Sideways/Crisis are preserved and not reissued.",
            "label_polarity": "1=source positive pump target, 0=source negative non-target candidate",
            "target_feature_count": len(target_feature_names),
            "sequence_feature_count": len(SEQ_FEATURE_NAMES),
            "sequence_feature_names": SEQ_FEATURE_NAMES,
            "target_feature_names": target_feature_names,
            "max_sequence_events_used": MAX_SEQ_EVENTS,
            "train": {
                "rows": train.rows,
                "positives": train.positives,
                "negatives": train.rows - train.positives,
                "bad_rows": train.bad_rows,
                "events": train.event_count,
                "timestamp_min": train.timestamp_min,
                "timestamp_max": train.timestamp_max,
            },
            "test": {
                "rows": test.rows,
                "positives": test.positives,
                "negatives": test.rows - test.positives,
                "bad_rows": test.bad_rows,
                "events": test.event_count,
                "timestamp_min": test.timestamp_min,
                "timestamp_max": test.timestamp_max,
            },
            "train_calibration_split": split_meta,
            "chronology_note": "Official test archive is held out. Fit/calibration split is by sorted channel_id|timestamp event inside the official train archive.",
        },
        "gate_contract": {
            "row_fit_support_min": ROW_FIT_SUPPORT_MIN,
            "row_calibration_support_min": ROW_CALIBRATION_SUPPORT_MIN,
            "row_test_support_min": ROW_TEST_SUPPORT_MIN,
            "event_support_min": EVENT_SUPPORT_MIN,
            "coverage_min": COVERAGE_MIN,
            "required_lcb": REQUIRED_LCB,
            "future_or_target_leakage_allowed": False,
            "thresholds_relaxed": False,
            "blocked_predictors": [
                "label",
                "channel_id",
                "channel_id_new",
                "coin",
                "raw_coin_id",
                "timestamp_unix",
                "future_*",
                "next_*",
            ],
        },
        "models": model_reports,
        "row_gates": row_gates,
        "event_top1_gates": event_gates,
        "diagnostic_hit_rates": hit_rates,
        "decision": decision,
        "elapsed_seconds": round(time.time() - started, 3),
    }
    report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_csv(summary_csv, row_gates, event_gates, hit_rates)
    write_markdown(report_md, source, train, test, split_meta, row_gates, event_gates, hit_rates, decision)
    assertions.write_text(
        "\n".join(
            [
                f"RUN_ID {RUN_ID}",
                "ACTIVE_AXIS MainRegimeV2",
                "CANDIDATE_REGIME Manipulation",
                f"TRAIN_ROWS {train.rows}",
                f"TRAIN_POSITIVES {train.positives}",
                f"TRAIN_EVENTS {train.event_count}",
                f"FIT_ROWS {split_meta['fit_rows']}",
                f"CALIBRATION_ROWS {split_meta['calibration_rows']}",
                f"TEST_ROWS {test.rows}",
                f"TEST_POSITIVES {test.positives}",
                f"TEST_EVENTS {test.event_count}",
                f"SEQUENCE_FEATURES {len(SEQ_FEATURE_NAMES)}",
                f"BEST_ROW_RULE {best_row['rule'] if best_row else 'none'}",
                f"BEST_ROW_MIN_LCB {best_row_min_lcb:.6f}",
                f"BEST_ROW_CAL_LCB {best_row['calibration']['wilson95_lcb'] if best_row else 0.0:.6f}",
                f"BEST_ROW_TEST_LCB {best_row['test']['wilson95_lcb'] if best_row else 0.0:.6f}",
                f"BEST_EVENT_RULE {best_event['rule'] if best_event else 'none'}",
                f"BEST_EVENT_MIN_LCB {best_event_min_lcb:.6f}",
                f"BEST_EVENT_CAL_LCB {best_event['calibration']['wilson95_lcb'] if best_event else 0.0:.6f}",
                f"BEST_EVENT_TEST_LCB {best_event['test']['wilson95_lcb'] if best_event else 0.0:.6f}",
                f"ACCEPTED_95 {str(accepted_95).lower()}",
                "THRESHOLDS_RELAXED false",
                "RUNTIME_CODE_CHANGED false",
                "TRADE_USABLE false",
                f"GATE {decision['gate']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (RUN_ROOT / "README.md").write_text(
        "\n".join(
            [
                "# Bayi-Hu Sequence/Ranking Manipulation Gate",
                "",
                f"Run id: `{RUN_ID}`",
                f"- report: `{repo_rel(report_json)}`",
                f"- summary: `{repo_rel(summary_csv)}`",
                f"- assertions: `{repo_rel(assertions)}`",
                f"- sample root in tmp: `{SAMPLE_ROOT}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    log(
        f"done accepted_95={accepted_95} "
        f"best_row_min_lcb={best_row_min_lcb:.6f} best_event_min_lcb={best_event_min_lcb:.6f} "
        f"elapsed={report['elapsed_seconds']}s"
    )


if __name__ == "__main__":
    main()
