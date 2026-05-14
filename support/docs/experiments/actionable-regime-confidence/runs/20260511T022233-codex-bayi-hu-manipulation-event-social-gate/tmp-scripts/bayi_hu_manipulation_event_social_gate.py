#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import pickle
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Callable

import pandas as pd


class Message(object):
    def __init__(self) -> None:
        pass


class Session(object):
    def __init__(self) -> None:
        pass


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T022233+0800-codex-bayi-hu-manipulation-event-social-gate"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T022233-codex-bayi-hu-manipulation-event-social-gate"
DATA_ROOT = Path(os.environ.get("BAYI_PD_DATA_ROOT", "/tmp/ict-regime-bayi-pd"))
SOURCE_URL = "https://github.com/Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency"

PATTERNS = {
    "has_pump": r"\bpump(?:ing|ed|s)?\b",
    "has_target": r"\btarget\b",
    "has_coin": r"\bcoin\b|\$[a-z0-9]{2,10}\b",
    "has_buy": r"\bbuy\b|\bbuying\b",
    "has_signal": r"\bsignal\b",
    "has_announce": r"announc|next post|coin name",
    "has_countdown": r"\b\d+\s*(?:min|mins|minute|minutes|hour|hours)\b|\b\d+\s*(?:m|h)\s*(?:left|until)\b|\buntil the pump\b",
    "has_time": r"\b(?:utc|gmt|est|cet)\b|\b\d{1,2}:\d{2}\b|\b\d{3,4}\s*(?:utc|gmt)?\b",
    "has_exchange": r"\bbinance\b|\byobit\b|\bkucoin\b|\bbittrex\b|\bhotbit\b|\bpoloniex\b|\bhuobi\b|\bhitbtc\b",
    "has_pair": r"\bbtc\b|\beth\b|\busdt\b|\bbnb\b|pair(?:ing)?",
    "has_vip": r"\bvip\b|pay2win|free for all|ffa",
    "has_hold_sell": r"\bhold\b|\bsell\b",
    "has_profit": r"profit|moon|\b[0-9]+%",
}

STOPWORDS = set(
    "the a an and or to of in for on at with from by is are be this that will we you our your it if as have has do not no all can get more after before until today tomorrow pm am gmt utc".split()
)


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def source_commit() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(DATA_ROOT), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def wilson_lcb(successes: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    phat = successes / n
    denom = 1 + z * z / n
    center = phat + z * z / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return max(0.0, (center - margin) / denom)


def precision_stats(mask: pd.Series, label: pd.Series) -> dict:
    support = int(mask.sum())
    positives = int((mask & (label == 1)).sum())
    return {
        "support": support,
        "positives": positives,
        "precision": positives / support if support else 0.0,
        "wilson95_lcb": wilson_lcb(positives, support),
    }


def split_chronological(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    ordered = df.sort_values("date").reset_index(drop=True)
    train_end = int(len(ordered) * 0.50)
    cal_end = int(len(ordered) * 0.75)
    return {
        "train": ordered.iloc[:train_end].copy(),
        "calibration": ordered.iloc[train_end:cal_end].copy(),
        "test": ordered.iloc[cal_end:].copy(),
    }


def tokens(text: str) -> list[str]:
    return [tok for tok in re.findall(r"[a-z0-9]{2,}", text.lower()) if tok not in STOPWORDS and not tok.isdigit()]


def load_manual_message_rows() -> tuple[pd.DataFrame, dict]:
    telegram_root = DATA_ROOT / "Data/Telegram"
    label_path = telegram_root / "Labeled/label.txt"
    labels = []
    for line in label_path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) >= 3:
            labels.append((parts[0], parts[1], parts[2]))

    label_channels = sorted({channel for _, channel, _ in labels})
    raw_index = {}
    missing_channels = []
    for channel in label_channels:
        raw_path = telegram_root / "raw" / f"{channel}.pkl"
        if not raw_path.exists():
            missing_channels.append(channel)
            continue
        with raw_path.open("rb") as handle:
            messages = pickle.load(handle)
        for message in messages:
            if isinstance(message, dict) and message.get("_") == "Message":
                raw_index[(channel, str(message.get("id")))] = message

    rows = []
    skipped_unknown = 0
    unmapped = 0
    for label, channel, sample_id in labels:
        if label == "?":
            skipped_unknown += 1
            continue
        message = raw_index.get((channel, sample_id))
        if not message or not message.get("date"):
            unmapped += 1
            continue
        rows.append(
            {
                "label": label,
                "y": 1 if label in {"1", "2"} else 0,
                "channel": channel,
                "message_id": sample_id,
                "date": message["date"],
                "text": message.get("message") or "",
            }
        )

    df = pd.DataFrame(rows).dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    metadata = {
        "label_rows_total": len(labels),
        "skipped_unknown_label_rows": skipped_unknown,
        "mapped_rows": int(len(df)),
        "unmapped_rows": unmapped,
        "missing_label_channels": missing_channels,
        "labels_mapped": {str(k): int(v) for k, v in Counter(df["label"]).items()},
        "positive_rows": int(df["y"].sum()),
        "negative_control_rows": int((1 - df["y"]).sum()),
        "channels_mapped": int(df["channel"].nunique()),
        "date_min": str(df["date"].min()),
        "date_max": str(df["date"].max()),
    }
    return df, metadata


def add_regex_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    lower = out["text"].str.lower()
    for name, pattern in PATTERNS.items():
        out[name] = lower.str.contains(pattern, regex=True, na=False).astype(int)
    out["text_len"] = out["text"].str.split().apply(len)
    out["num_count"] = out["text"].str.count(r"\d+")
    out["upper_token_count"] = out["text"].apply(lambda text: sum(1 for tok in re.findall(r"\b[A-Z0-9]{2,10}\b", text) if not tok.isdigit()))
    return out


def evaluate_regex_gate(df: pd.DataFrame, support_min: int = 50) -> dict:
    featured = add_regex_features(df)
    parts = split_chronological(featured)
    candidate_fns: list[tuple[str, Callable[[pd.DataFrame], pd.Series]]] = []
    for feature in PATTERNS:
        candidate_fns.append((feature, lambda data, feature=feature: data[feature].astype(bool)))

    pattern_names = list(PATTERNS)
    for i, left in enumerate(pattern_names):
        for right in pattern_names[i + 1 :]:
            candidate_fns.append((f"{left} & {right}", lambda data, left=left, right=right: data[left].astype(bool) & data[right].astype(bool)))
    for i, left in enumerate(pattern_names):
        for j, middle in enumerate(pattern_names[i + 1 :], start=i + 1):
            for right in pattern_names[j + 1 :]:
                candidate_fns.append(
                    (
                        f"{left} & {middle} & {right}",
                        lambda data, left=left, middle=middle, right=right: data[left].astype(bool) & data[middle].astype(bool) & data[right].astype(bool),
                    )
                )

    for feature in ["text_len", "num_count", "upper_token_count"]:
        quantiles = parts["train"][feature].quantile([0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95])
        for threshold in sorted(set(float(value) for value in quantiles.dropna().tolist())):
            candidate_fns.append((f"{feature} >= {threshold:g}", lambda data, feature=feature, threshold=threshold: data[feature] >= threshold))
            candidate_fns.append((f"{feature} <= {threshold:g}", lambda data, feature=feature, threshold=threshold: data[feature] <= threshold))

    best = None
    for rule_name, fn in candidate_fns:
        train_stats = precision_stats(fn(parts["train"]), parts["train"]["y"])
        if train_stats["support"] < support_min:
            continue
        key = (train_stats["wilson95_lcb"], train_stats["precision"], train_stats["positives"], train_stats["support"])
        if best is None or key > best["key"]:
            best = {"key": key, "rule": rule_name, "fn": fn, "train": train_stats}

    if best is None:
        return {"rule": None, "accepted_95": False, "blocker": "no_train_rule_met_support_floor"}

    calibration_stats = precision_stats(best["fn"](parts["calibration"]), parts["calibration"]["y"])
    test_stats = precision_stats(best["fn"](parts["test"]), parts["test"]["y"])
    accepted = (
        calibration_stats["support"] >= support_min
        and test_stats["support"] >= support_min
        and calibration_stats["wilson95_lcb"] >= 0.95
        and test_stats["wilson95_lcb"] >= 0.95
    )
    return {
        "gate": "manual_message_regex_rule",
        "support_min": support_min,
        "split": split_metadata(parts),
        "rule": best["rule"],
        "train": best["train"],
        "calibration": calibration_stats,
        "test": test_stats,
        "accepted_95": accepted,
        "blocker": "accepted_95" if accepted else "calibration_or_test_wilson_below_95_or_support_below_floor",
    }


def evaluate_naive_bayes_gate(df: pd.DataFrame, support_min: int = 50) -> dict:
    parts = split_chronological(df)
    train = parts["train"]
    pos_counts: Counter[str] = Counter()
    neg_counts: Counter[str] = Counter()
    pos_total = 0
    neg_total = 0
    for label, text in zip(train["y"], train["text"]):
        row_tokens = tokens(text)
        if int(label) == 1:
            pos_counts.update(row_tokens)
            pos_total += len(row_tokens)
        else:
            neg_counts.update(row_tokens)
            neg_total += len(row_tokens)

    vocab = {token for token, count in (pos_counts + neg_counts).items() if count >= 3}
    alpha = 1.0
    vocab_size = len(vocab)
    prior = math.log((int(train["y"].sum()) + 1) / (len(train) - int(train["y"].sum()) + 1))

    def score_text(text: str) -> float:
        score = prior
        for token in tokens(text):
            if token not in vocab:
                continue
            score += math.log((pos_counts[token] + alpha) / (pos_total + alpha * vocab_size))
            score -= math.log((neg_counts[token] + alpha) / (neg_total + alpha * vocab_size))
        return score

    for key in parts:
        parts[key]["score"] = parts[key]["text"].apply(score_text)

    thresholds = sorted(set(float(value) for value in parts["train"]["score"].dropna().tolist()))
    best = None
    for threshold in thresholds:
        train_stats = precision_stats(parts["train"]["score"] >= threshold, parts["train"]["y"])
        if train_stats["support"] < support_min:
            continue
        key = (train_stats["wilson95_lcb"], train_stats["precision"], train_stats["positives"], train_stats["support"])
        if best is None or key > best["key"]:
            best = {"key": key, "threshold": threshold, "train": train_stats}

    if best is None:
        return {"gate": "manual_message_multinomial_nb", "accepted_95": False, "blocker": "no_train_threshold_met_support_floor"}

    calibration_stats = precision_stats(parts["calibration"]["score"] >= best["threshold"], parts["calibration"]["y"])
    test_stats = precision_stats(parts["test"]["score"] >= best["threshold"], parts["test"]["y"])
    accepted = (
        calibration_stats["support"] >= support_min
        and test_stats["support"] >= support_min
        and calibration_stats["wilson95_lcb"] >= 0.95
        and test_stats["wilson95_lcb"] >= 0.95
    )
    top_tokens = []
    for token in vocab:
        token_score = math.log((pos_counts[token] + alpha) / (pos_total + alpha * vocab_size))
        token_score -= math.log((neg_counts[token] + alpha) / (neg_total + alpha * vocab_size))
        top_tokens.append((token_score, token, int(pos_counts[token]), int(neg_counts[token])))
    top_tokens = sorted(top_tokens, reverse=True)[:20]

    return {
        "gate": "manual_message_multinomial_nb",
        "support_min": support_min,
        "split": split_metadata(parts),
        "vocab_size": vocab_size,
        "threshold": best["threshold"],
        "train": best["train"],
        "calibration": calibration_stats,
        "test": test_stats,
        "top_positive_tokens": [
            {"token": token, "log_odds": score, "positive_count": pos_count, "negative_count": neg_count}
            for score, token, pos_count, neg_count in top_tokens
        ],
        "accepted_95": accepted,
        "blocker": "accepted_95" if accepted else "calibration_or_test_wilson_below_95_or_support_below_floor",
    }


def split_metadata(parts: dict[str, pd.DataFrame]) -> dict:
    return {
        name: {
            "rows": int(len(part)),
            "positives": int(part["y"].sum()),
            "negatives": int(len(part) - part["y"].sum()),
            "date_min": str(part["date"].min()),
            "date_max": str(part["date"].max()),
        }
        for name, part in parts.items()
    }


def load_event_log_summary() -> tuple[pd.DataFrame, dict]:
    path = DATA_ROOT / "Data/Telegram/Labeled/PD_logs_cleaned.txt"
    df = pd.read_csv(path, sep="\t")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    numeric_session = df["session_id"].astype(str).str.fullmatch(r"\d+")
    summary = {
        "event_rows": int(len(df)),
        "numeric_session_rows": int(numeric_session.sum()),
        "unknown_session_rows": int((~numeric_session).sum()),
        "exchanges": int(df["exchange"].nunique()),
        "coins": int(df["coin"].nunique()),
        "largest_exchange": str(df["exchange"].value_counts().idxmax()),
        "largest_exchange_rows": int(df["exchange"].value_counts().max()),
        "date_min": str(df["timestamp"].min()),
        "date_max": str(df["timestamp"].max()),
    }
    return df, summary


def load_session_rows(event_log: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    labeled_root = DATA_ROOT / "Data/Telegram/Labeled"
    numeric_events = event_log[event_log["session_id"].astype(str).str.fullmatch(r"\d+")].copy()
    positive_keys = {(str(row.channel_id), int(row.session_id)) for row in numeric_events.itertuples(index=False)}
    rows = []
    for path in sorted(labeled_root.glob("*_session.pkl")):
        channel = path.name.split("_")[0]
        with path.open("rb") as handle:
            sessions = pickle.load(handle)
        for session in sessions:
            session_id = int(getattr(session, "id", -1))
            messages = getattr(session, "message_list", []) or []
            dates = [message.date for message in messages if getattr(message, "date", None)]
            if not dates:
                continue
            rows.append(
                {
                    "channel": channel,
                    "session_id": session_id,
                    "y": 1 if (channel, session_id) in positive_keys else 0,
                    "date": min(dates),
                    "last_date": max(dates),
                    "text": "\n".join(getattr(message, "content", "") or "" for message in messages),
                    "pred_pump_cnt": int(getattr(session, "pred_pump_cnt", 0) or 0),
                    "message_count": int(len(messages)),
                    "duration_minutes": (max(dates) - min(dates)).total_seconds() / 60.0,
                }
            )

    df = pd.DataFrame(rows).dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    metadata = {
        "candidate_sessions": int(len(df)),
        "positive_sessions_covered": int(df["y"].sum()),
        "negative_control_sessions": int(len(df) - df["y"].sum()),
        "channels": int(df["channel"].nunique()),
        "event_log_numeric_rows": int(len(numeric_events)),
        "event_log_numeric_rows_not_covered_by_session_pickles": int(len(numeric_events) - df["y"].sum()),
        "negative_control_semantics": "predicted-pump sessions absent from cleaned event log; weaker than manual negative labels",
        "date_min": str(df["date"].min()),
        "date_max": str(df["date"].max()),
    }
    return df, metadata


def evaluate_session_gate(df: pd.DataFrame, support_min: int = 50) -> dict:
    featured = add_regex_features(df)
    parts = split_chronological(featured)
    candidate_fns: list[tuple[str, Callable[[pd.DataFrame], pd.Series]]] = []
    for feature in PATTERNS:
        candidate_fns.append((feature, lambda data, feature=feature: data[feature].astype(bool)))
    for feature in ["pred_pump_cnt", "message_count", "duration_minutes"]:
        quantiles = parts["train"][feature].quantile([0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95])
        for threshold in sorted(set(float(value) for value in quantiles.dropna().tolist())):
            candidate_fns.append((f"{feature} >= {threshold:g}", lambda data, feature=feature, threshold=threshold: data[feature] >= threshold))
            candidate_fns.append((f"{feature} <= {threshold:g}", lambda data, feature=feature, threshold=threshold: data[feature] <= threshold))

    best = None
    for rule_name, fn in candidate_fns:
        train_stats = precision_stats(fn(parts["train"]), parts["train"]["y"])
        if train_stats["support"] < support_min:
            continue
        key = (train_stats["wilson95_lcb"], train_stats["precision"], train_stats["positives"], train_stats["support"])
        if best is None or key > best["key"]:
            best = {"key": key, "rule": rule_name, "fn": fn, "train": train_stats}

    if best is None:
        return {"gate": "cleaned_event_session_candidate_rule", "accepted_95": False, "blocker": "no_train_rule_met_support_floor"}

    calibration_stats = precision_stats(best["fn"](parts["calibration"]), parts["calibration"]["y"])
    test_stats = precision_stats(best["fn"](parts["test"]), parts["test"]["y"])
    accepted = (
        calibration_stats["support"] >= support_min
        and test_stats["support"] >= support_min
        and calibration_stats["wilson95_lcb"] >= 0.95
        and test_stats["wilson95_lcb"] >= 0.95
    )
    return {
        "gate": "cleaned_event_session_candidate_rule",
        "support_min": support_min,
        "split": split_metadata(parts),
        "rule": best["rule"],
        "train": best["train"],
        "calibration": calibration_stats,
        "test": test_stats,
        "accepted_95": accepted,
        "blocker": "accepted_95" if accepted else "calibration_or_test_wilson_below_95_or_support_below_floor",
    }


def flatten_eval_rows(evaluations: list[dict]) -> pd.DataFrame:
    rows = []
    for evaluation in evaluations:
        row = {
            "gate": evaluation.get("gate"),
            "rule_or_threshold": evaluation.get("rule", evaluation.get("threshold")),
            "accepted_95": evaluation.get("accepted_95"),
            "blocker": evaluation.get("blocker"),
        }
        for split in ["train", "calibration", "test"]:
            stats = evaluation.get(split, {})
            for key in ["support", "positives", "precision", "wilson95_lcb"]:
                row[f"{split}_{key}"] = stats.get(key)
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    if not DATA_ROOT.exists():
        raise SystemExit(f"missing DATA_ROOT: {DATA_ROOT}")

    event_log, event_log_summary = load_event_log_summary()
    manual_messages, manual_metadata = load_manual_message_rows()
    session_rows, session_metadata = load_session_rows(event_log)

    nb_gate = evaluate_naive_bayes_gate(manual_messages)
    regex_gate = evaluate_regex_gate(manual_messages)
    session_gate = evaluate_session_gate(session_rows)
    evaluations = [nb_gate, regex_gate, session_gate]
    accepted_gates = [item["gate"] for item in evaluations if item.get("accepted_95")]
    accepted_95 = bool(accepted_gates)

    decision = {
        "board_state": "blocked",
        "active_axis": "MainRegimeV2",
        "candidate_regime": "Manipulation",
        "accepted_95": accepted_95,
        "accepted_gates": accepted_gates,
        "manipulation_input_state": "partial_crypto_event_social_dataset_below_95",
        "thresholds_relaxed": False,
        "runtime_code_changed": False,
        "trade_usable": False,
        "gate": "accepted_95" if accepted_95 else "blocked_bayi_hu_event_social_gate_below_95",
        "blocker": "Bayi-Hu provides direct crypto P&D event/social evidence and manual negative message controls, but the unchanged chronological gates failed held-out 95% Wilson lower bounds; no aligned market-feature samples were acquired in this bounded run.",
        "next_action": "Acquire or regenerate Bayi-Hu aligned market-feature samples with explicit positive/negative controls, then rerun the unchanged Manipulation gate before trying another source.",
    }

    report = {
        "run_id": RUN_ID,
        "source": {
            "url": SOURCE_URL,
            "commit": source_commit(),
            "local_clone": str(DATA_ROOT),
            "paper": "Sequence-based Target Coin Prediction for Cryptocurrency Pump-and-Dump",
            "paper_url": "https://arxiv.org/pdf/2204.12929.pdf",
        },
        "dataset": {
            "event_log": event_log_summary,
            "manual_message_labels": manual_metadata,
            "event_sessions": session_metadata,
            "github_market_feature_samples_present": False,
            "notes": "The README points generated train/test target-coin samples to external Google Drive archives; this bounded run did not acquire them and did not commit raw data.",
        },
        "evaluations": evaluations,
        "decision": decision,
    }

    out_dir = RUN_ROOT / "manipulation-gate"
    checks_dir = RUN_ROOT / "checks"
    out_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)
    report_json = out_dir / "bayi_hu_manipulation_event_social_gate_report.json"
    report_md = out_dir / "bayi_hu_manipulation_event_social_gate_report.md"
    summary_csv = out_dir / "bayi_hu_manipulation_event_social_gate_summary.csv"
    assertions = checks_dir / "bayi_hu_manipulation_event_social_gate_assertions.out"

    report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    flatten_eval_rows(evaluations).to_csv(summary_csv, index=False)

    md_lines = [
        "# Bayi-Hu Manipulation Event/Social Gate",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Source",
        "",
        f"- URL: `{SOURCE_URL}`",
        f"- Commit inspected in `/tmp`: `{report['source']['commit']}`",
        "- Dataset type: Telegram P&D event log, manual message labels, predicted pump-message/session artifacts.",
        "- Raw data committed to repo: false.",
        "",
        "## Dataset",
        "",
        f"- P&D event rows: {event_log_summary['event_rows']} across {event_log_summary['exchanges']} exchanges and {event_log_summary['coins']} coins.",
        f"- Largest exchange: {event_log_summary['largest_exchange']} with {event_log_summary['largest_exchange_rows']} rows.",
        f"- Manual message rows mapped: {manual_metadata['mapped_rows']} with {manual_metadata['positive_rows']} positive and {manual_metadata['negative_control_rows']} negative controls.",
        f"- Candidate event sessions: {session_metadata['candidate_sessions']} with {session_metadata['positive_sessions_covered']} cleaned-log positives and {session_metadata['negative_control_sessions']} weaker absent-from-log controls.",
        "- GitHub-shipped aligned market feature train/test samples: false.",
        "",
        "## Gate Results",
        "",
    ]
    for evaluation in evaluations:
        md_lines.append(
            "- {gate}: accepted_95={accepted}, rule_or_threshold=`{rule}`, cal_lcb={cal_lcb:.6f}, test_lcb={test_lcb:.6f}, cal_support={cal_support}, test_support={test_support}, blocker={blocker}".format(
                gate=evaluation.get("gate"),
                accepted=evaluation.get("accepted_95"),
                rule=evaluation.get("rule", evaluation.get("threshold")),
                cal_lcb=evaluation.get("calibration", {}).get("wilson95_lcb", 0.0),
                test_lcb=evaluation.get("test", {}).get("wilson95_lcb", 0.0),
                cal_support=evaluation.get("calibration", {}).get("support", 0),
                test_support=evaluation.get("test", {}).get("support", 0),
                blocker=evaluation.get("blocker"),
            )
        )
    md_lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Accepted 95 `Manipulation` root: false.",
            "- State: `partial_crypto_event_social_dataset_below_95`.",
            "- Runtime code changed: false.",
            "- Thresholds relaxed: false.",
            "- Trade usable: false.",
            "",
            decision["blocker"],
            "",
            f"Next: {decision['next_action']}",
        ]
    )
    report_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    checks = [
        f"RUN_ID {RUN_ID}",
        "ACTIVE_AXIS MainRegimeV2",
        "CANDIDATE_REGIME Manipulation",
        f"SOURCE_COMMIT {report['source']['commit']}",
        f"EVENT_ROWS {event_log_summary['event_rows']}",
        f"EVENT_EXCHANGES {event_log_summary['exchanges']}",
        f"MANUAL_MESSAGE_ROWS_MAPPED {manual_metadata['mapped_rows']}",
        f"MANUAL_MESSAGE_NEGATIVE_CONTROLS {manual_metadata['negative_control_rows']}",
        f"NB_CAL_LCB {nb_gate.get('calibration', {}).get('wilson95_lcb', 0.0):.6f}",
        f"NB_TEST_LCB {nb_gate.get('test', {}).get('wilson95_lcb', 0.0):.6f}",
        f"REGEX_CAL_LCB {regex_gate.get('calibration', {}).get('wilson95_lcb', 0.0):.6f}",
        f"REGEX_TEST_LCB {regex_gate.get('test', {}).get('wilson95_lcb', 0.0):.6f}",
        f"SESSION_CAL_LCB {session_gate.get('calibration', {}).get('wilson95_lcb', 0.0):.6f}",
        f"SESSION_TEST_LCB {session_gate.get('test', {}).get('wilson95_lcb', 0.0):.6f}",
        f"ACCEPTED_95 {str(accepted_95).lower()}",
        "THRESHOLDS_RELAXED false",
        "RUNTIME_CODE_CHANGED false",
        "TRADE_USABLE false",
        f"GATE {decision['gate']}",
    ]
    assertions.write_text("\n".join(checks) + "\n", encoding="utf-8")

    (RUN_ROOT / "README.md").write_text(
        "\n".join(
            [
                "# Bayi-Hu Manipulation Event/Social Gate",
                "",
                f"Run id: `{RUN_ID}`",
                f"- report: `{repo_rel(report_json)}`",
                f"- summary: `{repo_rel(summary_csv)}`",
                f"- assertions: `{repo_rel(assertions)}`",
                f"- source inspected in tmp: `{DATA_ROOT}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
