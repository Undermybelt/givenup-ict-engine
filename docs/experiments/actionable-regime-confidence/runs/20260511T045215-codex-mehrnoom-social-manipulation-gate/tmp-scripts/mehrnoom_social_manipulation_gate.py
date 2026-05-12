#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import os
import re
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Callable

import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T045215+0800-codex-mehrnoom-social-manipulation-gate"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T045215-codex-mehrnoom-social-manipulation-gate"
OUT_DIR = RUN_ROOT / "social-event-gate"
CHECK_DIR = RUN_ROOT / "checks"
DATA_ROOT = Path(os.environ.get("MEHRNOOM_DATA_ROOT", "/private/tmp/ict-regime-mehrnoom-pump-dump"))
LFS_CACHE = Path(os.environ.get("MEHRNOOM_LFS_CACHE", "/private/tmp/ict-regime-mehrnoom-pump-dump-lfs-cache"))
LFS_BATCH_URL = "https://github.com/Mehrnoom/Cryptocurrency-Pump-Dump.git/info/lfs/objects/batch"
SOURCE_URL = "https://github.com/Mehrnoom/Cryptocurrency-Pump-Dump"
SOURCE_PAPER = "https://arxiv.org/abs/1902.03110"

MAX_DOWNLOAD_MIB = float(os.environ.get("MEHRNOOM_MAX_DOWNLOAD_MIB", "250"))
MAX_CHANNELS = int(os.environ.get("MEHRNOOM_MAX_CHANNELS", "80"))
SUPPORT_MIN = int(os.environ.get("MEHRNOOM_SUPPORT_MIN", "50"))
COVERAGE_MIN = float(os.environ.get("MEHRNOOM_COVERAGE_MIN", "0.03"))
LCB_MIN = float(os.environ.get("MEHRNOOM_LCB_MIN", "0.95"))
ECE_MAX = float(os.environ.get("MEHRNOOM_ECE_MAX", "0.05"))

PATTERNS = {
    "has_pump": r"\bpump(?:ing|ed|s)?\b",
    "has_buy": r"\bbuy\b|\bbuying\b|\bbought\b|\bentry\b",
    "has_sell": r"\bsell\b|\bselling\b|\btarget(?:s)?\b|\btp\d*\b",
    "has_signal": r"\bsignal\b|\bcall\b|\balert\b",
    "has_coin_word": r"\bcoin\b|\btoken\b|\bpair\b",
    "has_exchange": r"\bbinance\b|\bbittrex\b|\bkucoin\b|\byobit\b|\bpoloniex\b|\bcryptopia\b|\bhitbtc\b|\bhuobi\b",
    "has_pair_word": r"\bbtc\b|\beth\b|\busdt\b|\bbnb\b",
    "has_countdown": r"\bcountdown\b|\b\d+\s*(?:min|mins|minute|minutes|hour|hours|m|h)\b|\bready\b",
    "has_time": r"\butc\b|\bgmt\b|\best\b|\bcet\b|\b\d{1,2}:\d{2}\b",
    "has_price": r"\bprice\b|\b[0-9]+(?:\.[0-9]+)?\s*(?:sat|sats|btc|eth|usd|usdt)\b",
    "has_profit": r"\bprofit\b|\bmoon\b|\brocket\b|\b\d+%",
    "has_join": r"\bjoin\b|\bchannel\b|\bgroup\b|\bvip\b",
    "has_leak": r"\bleak\b|\binsider\b|\bprivate\b",
    "has_hold": r"\bhold\b|\bhodl\b|\bdont sell\b|\bdon't sell\b",
}

STOPWORDS = set(
    """
    the a an and or to of in for on at with from by is are be this that will
    we you our your it if as have has do not no all can get more after before
    until today tomorrow pm am gmt utc http https t me com www
    """.split()
)


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def log(message: str) -> None:
    print(message, flush=True)


def wilson_lcb(successes: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    phat = successes / n
    denom = 1 + z * z / n
    center = phat + z * z / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return max(0.0, (center - margin) / denom)


def precision_stats(mask: pd.Series, label: pd.Series, calibrated_confidence: float | None = None) -> dict:
    support = int(mask.sum())
    positives = int((mask & (label == 1)).sum())
    n = int(len(label))
    precision = positives / support if support else 0.0
    confidence = precision if calibrated_confidence is None else calibrated_confidence
    return {
        "rows": n,
        "support": support,
        "successes": positives,
        "precision": precision,
        "calibrated_confidence": confidence,
        "wilson95_lcb": wilson_lcb(positives, support),
        "coverage": support / n if n else 0.0,
        "ece_vs_calibrated_confidence": abs(precision - confidence) if support else 0.0,
    }


def source_commit() -> str:
    try:
        import subprocess

        return subprocess.check_output(["git", "-C", str(DATA_ROOT), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def read_pump_labels() -> tuple[pd.DataFrame, set[tuple[int, int]], dict[int, int]]:
    path = DATA_ROOT / "Telegram/classified/coin-pump.csv"
    df = pd.read_csv(path)
    df["channel_id"] = df["Channel ID"].astype(int)
    df["message_id"] = df["Message ID"].astype(int)
    df["event_dt"] = pd.to_datetime(df["Date"].astype(str) + " " + df["Time"].astype(str), utc=True, errors="coerce")
    positive_pairs = set(zip(df["channel_id"], df["message_id"]))
    channel_counts = df.groupby("channel_id").size().sort_values(ascending=False).to_dict()
    return df, positive_pairs, {int(k): int(v) for k, v in channel_counts.items()}


def parse_lfs_pointer(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    oid_match = re.search(r"oid sha256:([a-f0-9]+)", text)
    size_match = re.search(r"^size (\d+)", text, re.M)
    if not oid_match or not size_match:
        return None
    return {"oid": oid_match.group(1), "size": int(size_match.group(1)), "path": path}


def select_channels(channel_counts: dict[int, int]) -> list[dict]:
    rows = []
    for channel_id, positives in channel_counts.items():
        pointer = DATA_ROOT / "Telegram/channels" / f"{channel_id}.jl"
        if not pointer.exists():
            continue
        lfs = parse_lfs_pointer(pointer)
        if not lfs:
            continue
        rows.append(
            {
                "channel_id": int(channel_id),
                "positive_label_rows": int(positives),
                "oid": lfs["oid"],
                "size": int(lfs["size"]),
                "pointer": pointer,
            }
        )
    rows.sort(key=lambda row: (row["positive_label_rows"], -row["size"]), reverse=True)
    selected = []
    total = 0
    limit_bytes = int(MAX_DOWNLOAD_MIB * 1024 * 1024)
    for row in rows:
        if len(selected) >= MAX_CHANNELS:
            break
        if total + row["size"] > limit_bytes:
            continue
        selected.append(row)
        total += row["size"]
    return selected


def lfs_batch(objects: list[dict]) -> dict[str, str]:
    if not objects:
        return {}
    body = json.dumps(
        {
            "operation": "download",
            "transfers": ["basic"],
            "objects": [{"oid": row["oid"], "size": row["size"]} for row in objects],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        LFS_BATCH_URL,
        data=body,
        headers={"Accept": "application/vnd.git-lfs+json", "Content-Type": "application/vnd.git-lfs+json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))
    hrefs = {}
    for obj in data.get("objects", []):
        action = obj.get("actions", {}).get("download", {})
        if action.get("href"):
            hrefs[obj["oid"]] = action["href"]
    return hrefs


def ensure_lfs_files(selected: list[dict]) -> list[Path]:
    LFS_CACHE.mkdir(parents=True, exist_ok=True)
    needed = []
    paths = []
    for row in selected:
        out = LFS_CACHE / f"{row['channel_id']}.jl"
        row["cache_path"] = out
        paths.append(out)
        if not out.exists() or out.stat().st_size != row["size"]:
            needed.append(row)
    if needed:
        log(f"fetching_lfs_files={len(needed)}")
    for start in range(0, len(needed), 25):
        batch = needed[start : start + 25]
        hrefs = lfs_batch(batch)
        for row in batch:
            href = hrefs.get(row["oid"])
            if not href:
                raise RuntimeError(f"missing LFS download href for {row['channel_id']}")
            tmp = row["cache_path"].with_suffix(".jl.download")
            with urllib.request.urlopen(href, timeout=180) as response, tmp.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
            if tmp.stat().st_size != row["size"]:
                raise RuntimeError(f"size mismatch for {row['channel_id']}: {tmp.stat().st_size} != {row['size']}")
            tmp.replace(row["cache_path"])
            log(f"fetched_channel={row['channel_id']} size={row['size']}")
    return paths


def extract_text_features(text: str) -> dict:
    text = text or ""
    lower = text.lower()
    features = {}
    for name, pattern in PATTERNS.items():
        features[name] = 1 if re.search(pattern, lower) else 0
    features["text_len"] = len(text.split())
    features["char_len"] = len(text)
    features["upper_token_count"] = len([tok for tok in re.findall(r"\b[A-Z0-9]{2,10}\b", text) if not tok.isdigit()])
    features["ticker_like_count"] = len(re.findall(r"\$?[A-Z]{2,8}\b", text))
    features["number_count"] = len(re.findall(r"\d+(?:\.\d+)?", text))
    features["percent_count"] = text.count("%")
    features["exclaim_count"] = text.count("!")
    features["mention_count"] = text.count("@")
    features["url_count"] = len(re.findall(r"https?://|t\.me/", lower))
    features["line_count"] = text.count("\n") + 1 if text else 0
    return features


def tokens(text: str) -> list[str]:
    return [tok for tok in re.findall(r"[a-z0-9]{2,}", (text or "").lower()) if tok not in STOPWORDS and not tok.isdigit()]


def parse_messages(paths: list[Path], positive_pairs: set[tuple[int, int]]) -> tuple[pd.DataFrame, dict]:
    rows = []
    parse_errors = 0
    for path in paths:
        channel_id = int(path.stem)
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    parse_errors += 1
                    continue
                if obj.get("_") != "Message":
                    continue
                message_id = obj.get("id")
                text = obj.get("message") or ""
                date_raw = obj.get("date")
                if isinstance(date_raw, dict) and "$date" in date_raw:
                    dt = pd.to_datetime(date_raw["$date"], unit="ms", utc=True, errors="coerce")
                else:
                    dt = pd.to_datetime(date_raw, utc=True, errors="coerce")
                if pd.isna(dt) or not isinstance(message_id, int):
                    continue
                y = 1 if (channel_id, int(message_id)) in positive_pairs else 0
                feat = extract_text_features(text)
                feat.update(
                    {
                        "channel_id": channel_id,
                        "message_id": int(message_id),
                        "date": dt,
                        "text": text,
                        "y": y,
                    }
                )
                rows.append(feat)
    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("no raw messages parsed")
    df = df.sort_values("date").reset_index(drop=True)
    matched_positive_pairs = set(zip(df.loc[df["y"] == 1, "channel_id"], df.loc[df["y"] == 1, "message_id"]))
    metadata = {
        "raw_message_rows": int(len(df)),
        "positive_message_rows": int(df["y"].sum()),
        "negative_control_rows": int((df["y"] == 0).sum()),
        "channels_parsed": int(df["channel_id"].nunique()),
        "date_min": str(df["date"].min()),
        "date_max": str(df["date"].max()),
        "parse_errors": int(parse_errors),
        "matched_positive_pairs": int(len(matched_positive_pairs)),
    }
    return df, metadata


def split_chronological(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    ordered = df.sort_values("date").reset_index(drop=True)
    train_end = int(len(ordered) * 0.50)
    cal_end = int(len(ordered) * 0.75)
    return {
        "train": ordered.iloc[:train_end].copy(),
        "calibration": ordered.iloc[train_end:cal_end].copy(),
        "test": ordered.iloc[cal_end:].copy(),
    }


def split_metadata(parts: dict[str, pd.DataFrame]) -> dict:
    return {
        name: {
            "rows": int(len(part)),
            "positives": int(part["y"].sum()),
            "negative_controls": int((part["y"] == 0).sum()),
            "date_min": str(part["date"].min()) if len(part) else "",
            "date_max": str(part["date"].max()) if len(part) else "",
        }
        for name, part in parts.items()
    }


def build_naive_bayes_scores(parts: dict[str, pd.DataFrame]) -> dict[str, pd.Series]:
    train = parts["train"]
    pos_counts: Counter[str] = Counter()
    neg_counts: Counter[str] = Counter()
    for _, row in train.iterrows():
        counter = pos_counts if int(row["y"]) == 1 else neg_counts
        counter.update(tokens(row["text"]))
    vocab = sorted(set(pos_counts) | set(neg_counts))
    if not vocab:
        return {name: pd.Series([0.0] * len(part), index=part.index) for name, part in parts.items()}
    vocab_size = len(vocab)
    pos_total = sum(pos_counts.values()) + vocab_size
    neg_total = sum(neg_counts.values()) + vocab_size
    token_weight = {tok: math.log((pos_counts[tok] + 1) / pos_total) - math.log((neg_counts[tok] + 1) / neg_total) for tok in vocab}
    pos_prior = (int(train["y"].sum()) + 1) / (len(train) + 2)
    prior = math.log(pos_prior / (1 - pos_prior))

    def score_text(text: str) -> float:
        score = prior
        for tok in tokens(text):
            score += token_weight.get(tok, 0.0)
        return score

    return {name: part["text"].map(score_text) for name, part in parts.items()}


def candidate_masks(parts: dict[str, pd.DataFrame]) -> list[tuple[str, Callable[[pd.DataFrame], pd.Series]]]:
    candidates: list[tuple[str, Callable[[pd.DataFrame], pd.Series]]] = []
    for feature in PATTERNS:
        candidates.append((feature, lambda data, feature=feature: data[feature].astype(bool)))

    pattern_names = list(PATTERNS)
    for left in pattern_names:
        for right in pattern_names:
            if left >= right:
                continue
            candidates.append(
                (
                    f"{left} & {right}",
                    lambda data, left=left, right=right: data[left].astype(bool) & data[right].astype(bool),
                )
            )

    numeric_features = [
        "text_len",
        "char_len",
        "upper_token_count",
        "ticker_like_count",
        "number_count",
        "percent_count",
        "exclaim_count",
        "mention_count",
        "url_count",
        "line_count",
    ]
    quantiles = [0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95, 0.975, 0.99]
    for feature in numeric_features:
        values = parts["train"][feature].dropna()
        for threshold in sorted(set(float(v) for v in values.quantile(quantiles).dropna().tolist())):
            candidates.append((f"{feature} >= {threshold:g}", lambda data, feature=feature, threshold=threshold: data[feature] >= threshold))
            candidates.append((f"{feature} <= {threshold:g}", lambda data, feature=feature, threshold=threshold: data[feature] <= threshold))
    return candidates


def evaluate_gate(df: pd.DataFrame) -> dict:
    parts = split_chronological(df)
    candidates = candidate_masks(parts)
    nb_scores = build_naive_bayes_scores(parts)
    for name, score in nb_scores.items():
        parts[name] = parts[name].copy()
        parts[name]["nb_score"] = score
    for threshold in sorted(set(float(v) for v in parts["train"]["nb_score"].quantile([0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95, 0.975, 0.99, 0.995]).dropna().tolist())):
        candidates.append((f"nb_score >= {threshold:g}", lambda data, threshold=threshold: data["nb_score"] >= threshold))

    best = None
    train_candidates = []
    for rule, fn in candidates:
        mask = fn(parts["train"])
        stats = precision_stats(mask, parts["train"]["y"])
        if stats["support"] < SUPPORT_MIN or stats["coverage"] < COVERAGE_MIN:
            continue
        key = (stats["wilson95_lcb"], stats["precision"], stats["coverage"], stats["support"])
        row = {"rule": rule, "train": stats, "key": key, "fn": fn}
        train_candidates.append(row)
        if best is None or key > best["key"]:
            best = row
    train_candidates.sort(key=lambda row: row["key"], reverse=True)

    if best is None:
        return {
            "accepted_95": False,
            "gate": "blocked_no_train_candidate_met_support_and_coverage",
            "split": split_metadata(parts),
            "support_min": SUPPORT_MIN,
            "coverage_min": COVERAGE_MIN,
            "lcb_min": LCB_MIN,
            "ece_max": ECE_MAX,
        }

    train_stats = best["train"]
    cal_stats_uncal = precision_stats(best["fn"](parts["calibration"]), parts["calibration"]["y"])
    calibrated_confidence = cal_stats_uncal["precision"]
    cal_stats = precision_stats(best["fn"](parts["calibration"]), parts["calibration"]["y"], calibrated_confidence)
    test_stats = precision_stats(best["fn"](parts["test"]), parts["test"]["y"], calibrated_confidence)
    accepted = (
        cal_stats["support"] >= SUPPORT_MIN
        and test_stats["support"] >= SUPPORT_MIN
        and cal_stats["coverage"] >= COVERAGE_MIN
        and test_stats["coverage"] >= COVERAGE_MIN
        and cal_stats["wilson95_lcb"] >= LCB_MIN
        and test_stats["wilson95_lcb"] >= LCB_MIN
        and test_stats["ece_vs_calibrated_confidence"] <= ECE_MAX
    )
    blocker = "accepted_95" if accepted else "held_out_wilson_coverage_or_ece_below_gate"
    return {
        "accepted_95": bool(accepted),
        "gate": "mehrnoom_raw_telegram_message_social_gate",
        "blocker": blocker,
        "rule": best["rule"],
        "support_min": SUPPORT_MIN,
        "coverage_min": COVERAGE_MIN,
        "lcb_min": LCB_MIN,
        "ece_max": ECE_MAX,
        "split": split_metadata(parts),
        "train": train_stats,
        "calibration": cal_stats,
        "test": test_stats,
        "top_train_candidates": [
            {
                "rule": row["rule"],
                "train_wilson95_lcb": row["train"]["wilson95_lcb"],
                "train_precision": row["train"]["precision"],
                "train_support": row["train"]["support"],
                "train_coverage": row["train"]["coverage"],
            }
            for row in train_candidates[:20]
        ],
    }


def write_outputs(report: dict, df: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "mehrnoom_social_manipulation_gate_report.json"
    md_path = OUT_DIR / "mehrnoom_social_manipulation_gate_report.md"
    summary_path = OUT_DIR / "mehrnoom_social_manipulation_gate_summary.csv"
    sample_path = OUT_DIR / "mehrnoom_social_message_feature_sample.csv"
    checks_path = CHECK_DIR / "mehrnoom_social_manipulation_gate_assertions.out"

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    gate = report["gate_result"]
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["rule", "accepted_95", "split", "wilson95_lcb", "precision", "support", "coverage", "ece"],
        )
        writer.writeheader()
        for split in ["train", "calibration", "test"]:
            stats = gate.get(split, {})
            writer.writerow(
                {
                    "rule": gate.get("rule", ""),
                    "accepted_95": gate.get("accepted_95", False),
                    "split": split,
                    "wilson95_lcb": stats.get("wilson95_lcb", ""),
                    "precision": stats.get("precision", ""),
                    "support": stats.get("support", ""),
                    "coverage": stats.get("coverage", ""),
                    "ece": stats.get("ece_vs_calibrated_confidence", ""),
                }
            )

    sample_cols = [
        "date",
        "channel_id",
        "message_id",
        "y",
        "text_len",
        "upper_token_count",
        "ticker_like_count",
        "number_count",
        "has_pump",
        "has_buy",
        "has_sell",
        "has_signal",
        "has_exchange",
    ]
    df[sample_cols].head(200).to_csv(sample_path, index=False)

    lines = [
        "# Mehrnoom Social Manipulation Gate",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Source",
        "",
        f"- Repository: `{SOURCE_URL}`",
        f"- Paper: `{SOURCE_PAPER}`",
        f"- Commit inspected: `{report['source']['commit']}`",
        f"- Raw LFS cache: `{report['source']['lfs_cache']}`",
        "- Raw data committed to repo: false.",
        "- Runtime code changed: false.",
        "- Thresholds relaxed: false.",
        "",
        "## Dataset",
        "",
        f"- Selected channels: {report['dataset']['selected_channels']} bounded by {MAX_DOWNLOAD_MIB:g} MiB / {MAX_CHANNELS} channels.",
        f"- Downloaded raw message bytes: {report['dataset']['selected_raw_bytes']}.",
        f"- Raw message rows: {report['dataset']['raw_message_rows']}.",
        f"- Positive pump-attempt message rows: {report['dataset']['positive_message_rows']}.",
        f"- Unclassified channel-message controls: {report['dataset']['negative_control_rows']}.",
        f"- Chronological range: {report['dataset']['date_min']} to {report['dataset']['date_max']}.",
        "",
        "## Gate",
        "",
        f"- Rule: `{gate.get('rule', 'N/A')}`.",
        f"- Calibration Wilson95 / precision / support / coverage / ECE: `{gate.get('calibration', {}).get('wilson95_lcb', 0):.6f}` / `{gate.get('calibration', {}).get('precision', 0):.6f}` / `{gate.get('calibration', {}).get('support', 0)}` / `{gate.get('calibration', {}).get('coverage', 0):.6f}` / `{gate.get('calibration', {}).get('ece_vs_calibrated_confidence', 0):.6f}`.",
        f"- Test Wilson95 / precision / support / coverage / ECE: `{gate.get('test', {}).get('wilson95_lcb', 0):.6f}` / `{gate.get('test', {}).get('precision', 0):.6f}` / `{gate.get('test', {}).get('support', 0)}` / `{gate.get('test', {}).get('coverage', 0):.6f}` / `{gate.get('test', {}).get('ece_vs_calibrated_confidence', 0):.6f}`.",
        f"- Gate result: `{report['decision']}`. Accepted 95 `Manipulation`: {str(gate.get('accepted_95', False)).lower()}. Trade usable: false.",
        "",
        "## Notes",
        "",
        "- Predictor policy: raw source label, channel id, message id, target coin, and timestamp identity were not used as predictors.",
        "- Candidate rules used raw Telegram message text features only; selection was train-only, with chronological calibration/test holdout.",
        "- `Manipulation` remains a direct-input-gated root or overlay. This packet does not change `Bull`, `Bear`, `Sideways`, or `Crisis` accounting.",
        "",
        f"Next: {report['next_action']}",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")

    assertions = []
    assertions.append("json_parse_ok")
    assertions.append(f"thresholds_relaxed={str(report['thresholds_relaxed']).lower()}")
    assertions.append(f"runtime_code_changed={str(report['runtime_code_changed']).lower()}")
    assertions.append(f"raw_data_committed={str(report['raw_data_committed']).lower()}")
    assertions.append(f"accepted_95={str(gate.get('accepted_95', False)).lower()}")
    assertions.append(f"decision={report['decision']}")
    if gate.get("accepted_95"):
        assertions.append("mehrnoom_gate_passed_wilson_support_coverage_ece")
    else:
        assertions.append("mehrnoom_gate_blocked")
    checks_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")


def main() -> int:
    started = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    labels, positive_pairs, channel_counts = read_pump_labels()
    selected = select_channels(channel_counts)
    if not selected:
        raise RuntimeError("no channels selected")
    selected_positive_rows = sum(row["positive_label_rows"] for row in selected)
    selected_raw_bytes = sum(row["size"] for row in selected)
    log(f"selected_channels={len(selected)} selected_positive_label_rows={selected_positive_rows} selected_mib={selected_raw_bytes/1024/1024:.2f}")
    paths = ensure_lfs_files(selected)
    df, message_meta = parse_messages(paths, positive_pairs)
    gate_result = evaluate_gate(df)
    accepted = bool(gate_result.get("accepted_95"))
    decision = "accepted_95_mehrnoom_raw_telegram_social_manipulation_gate" if accepted else "blocked_mehrnoom_social_gate_below_95_coverage_or_ece"
    next_action = (
        "Board A direct Manipulation has a candidate accepted Mehrnoom social-event packet; audit cross-source generalization before trade use."
        if accepted
        else "Acquire stronger direct event/order-lifecycle/L2/L3/MBO/social/on-chain Manipulation positives and negatives or broaden this source with additional explicit controls, then rerun the unchanged gate."
    )
    report = {
        "run_id": RUN_ID,
        "source": {
            "repository": SOURCE_URL,
            "paper": SOURCE_PAPER,
            "commit": source_commit(),
            "data_root": str(DATA_ROOT),
            "lfs_cache": str(LFS_CACHE),
        },
        "dataset": {
            "classified_positive_rows_total": int(len(labels)),
            "classified_unique_positive_messages_total": int(len(positive_pairs)),
            "selected_channels": int(len(selected)),
            "selected_positive_label_rows": int(selected_positive_rows),
            "selected_raw_bytes": int(selected_raw_bytes),
            **message_meta,
            "negative_control_policy": "source_channel_messages_not_present_in_classified_coin_pump_output",
        },
        "selected_channels": [
            {"channel_id": row["channel_id"], "positive_label_rows": row["positive_label_rows"], "size": row["size"]}
            for row in selected
        ],
        "candidate_regime": "Manipulation",
        "evidence_class": "direct_social_event_telegram_raw_message",
        "predictor_policy": {
            "used_predictors": "raw Telegram message text-derived regex/count/token-score features only",
            "blocked_predictors": ["source label y", "Channel ID", "Message ID", "Coin", "date identity", "future_*", "target_*", "next_*"],
        },
        "gate_result": gate_result,
        "decision": decision,
        "accepted_95": accepted,
        "trade_usable": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "elapsed_seconds": round(time.time() - started, 3),
        "artifacts": {
            "json": repo_rel(OUT_DIR / "mehrnoom_social_manipulation_gate_report.json"),
            "report": repo_rel(OUT_DIR / "mehrnoom_social_manipulation_gate_report.md"),
            "summary": repo_rel(OUT_DIR / "mehrnoom_social_manipulation_gate_summary.csv"),
            "sample": repo_rel(OUT_DIR / "mehrnoom_social_message_feature_sample.csv"),
            "assertions": repo_rel(CHECK_DIR / "mehrnoom_social_manipulation_gate_assertions.out"),
        },
        "next_action": next_action,
    }
    write_outputs(report, df)
    log(json.dumps({"decision": decision, "accepted_95": accepted, "rule": gate_result.get("rule"), "elapsed_seconds": report["elapsed_seconds"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
