from __future__ import annotations

import csv
import json
import urllib.request
from collections import Counter
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T021647-codex-bayi-hu-event-social-manipulation-gate"
)
OUT_DIR = RUN_ROOT / "event-social-gate"
CHECKS_DIR = RUN_ROOT / "checks"
LOOP_ID = "20260511T021647+0800-codex-bayi-hu-event-social-manipulation-gate"

PD_LOGS_URL = (
    "https://raw.githubusercontent.com/Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency/"
    "master/Data/Telegram/Labeled/PD_logs_cleaned.txt"
)
LABEL_URL = (
    "https://raw.githubusercontent.com/Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency/"
    "master/Data/Telegram/Labeled/label.txt"
)
PRED_MESSAGE_URL = (
    "https://raw.githubusercontent.com/Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency/"
    "master/Data/Telegram/Labeled/pred_pump_message.csv"
)


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/plain,text/csv",
            "User-Agent": "curl/8.7.1",
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_pd_events(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(StringIO(text), delimiter="\t"))


def parse_pred_messages(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(StringIO(text), delimiter="\t"))


def parse_label_counts(text: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for line in text.splitlines():
        parts = line.split()
        if parts:
            counts[parts[0]] += 1
    return counts


def chronological_support(events: list[dict[str, str]]) -> dict[str, Any]:
    parsed = sorted(
        datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")).replace(tzinfo=None)
        for row in events
        if row.get("timestamp")
    )
    if not parsed:
        return {}
    n = len(parsed)
    train = parsed[: n // 2]
    calibration = parsed[n // 2 : n * 3 // 4]
    test = parsed[n * 3 // 4 :]
    return {
        "first_timestamp": parsed[0].isoformat(),
        "last_timestamp": parsed[-1].isoformat(),
        "train_positive_events": len(train),
        "calibration_positive_events": len(calibration),
        "test_positive_events": len(test),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    events = parse_pd_events(fetch_text(PD_LOGS_URL))
    pred_messages = parse_pred_messages(fetch_text(PRED_MESSAGE_URL))
    label_counts = parse_label_counts(fetch_text(LABEL_URL))
    exchange_counts = Counter(row.get("exchange", "") for row in events)
    coin_counts = Counter(row.get("coin", "") for row in events)
    pair_counts = Counter(row.get("pair", "") for row in events)
    pred_label_counts = Counter(row.get("pred_label", "") for row in pred_messages)
    chrono = chronological_support(events)

    has_positive_events = bool(events)
    has_message_labels = bool(label_counts)
    has_negative_event_controls = False
    has_aligned_market_features = False
    accepted_95 = False
    decision = {
        "board_state": "blocked",
        "active_axis": "MainRegimeV2",
        "candidate_regime": "Manipulation",
        "accepted_95": accepted_95,
        "manipulation_input_state": "event_social_positive_events_available_negative_controls_missing",
        "positive_event_source_ready": has_positive_events,
        "message_labels_available": has_message_labels,
        "negative_event_controls_available": has_negative_event_controls,
        "aligned_market_features_available": has_aligned_market_features,
        "thresholds_relaxed": False,
        "runtime_code_changed": False,
        "fresh_calibration_rerun": False,
        "trade_usable": False,
        "blocker": (
            "Bayi-Hu provides directly downloadable positive pump/dump event and message-label evidence, "
            "but this source does not include explicit negative event controls or aligned market features. "
            "A calibrated 95% Manipulation precision gate cannot be computed without them."
        ),
        "next_action": (
            "Add explicit negative controls or aligned market features for the Bayi-Hu event windows, "
            "then rerun the unchanged chronological Manipulation gate."
        ),
    }
    result = {
        "schema_version": "bayi-hu-event-social-manipulation-gate/v1",
        "loop_id": LOOP_ID,
        "run_root": repo_rel(RUN_ROOT),
        "sources": {
            "pd_logs_cleaned": PD_LOGS_URL,
            "label_txt": LABEL_URL,
            "pred_pump_message": PRED_MESSAGE_URL,
        },
        "event_support": {
            "positive_events": len(events),
            "exchanges": len([key for key in exchange_counts if key]),
            "coins": len([key for key in coin_counts if key]),
            "pairs": dict(pair_counts),
            "top_exchanges": exchange_counts.most_common(10),
            **chrono,
        },
        "message_support": {
            "manual_label_rows": sum(label_counts.values()),
            "manual_label_counts": dict(label_counts),
            "pred_pump_message_rows": len(pred_messages),
            "pred_label_counts": dict(pred_label_counts),
        },
        "calibration_attempt": {
            "chronological_split_materialized_for_positive_events": bool(chrono),
            "precision_wilson_lcb_95": None,
            "ece": None,
            "reason_not_computed": "missing_negative_controls_or_aligned_market_features",
        },
        "raw_data_policy": "no_raw_event_or_message_files_committed; counts_only",
        "decision": decision,
    }

    report_json = OUT_DIR / "bayi_hu_event_social_manipulation_gate.json"
    report_md = OUT_DIR / "bayi_hu_event_social_manipulation_gate.md"
    report_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    report_md.write_text(
        "# Bayi-Hu Event/Social Manipulation Gate\n\n"
        f"Run id: `{LOOP_ID}`\n\n"
        "This bounded gate used directly downloadable Bayi-Hu P&D event and message-label files. "
        "It kept only counts and split metadata in the repo; no raw event/message files were committed.\n\n"
        "Support:\n"
        f"- Positive P&D events: {len(events)}\n"
        f"- Exchanges: {result['event_support']['exchanges']}\n"
        f"- Coins: {result['event_support']['coins']}\n"
        f"- Chronological split positive events: train {chrono.get('train_positive_events')}, "
        f"calibration {chrono.get('calibration_positive_events')}, test {chrono.get('test_positive_events')}\n"
        f"- Manual message labels: {sum(label_counts.values())}, counts {dict(label_counts)}\n"
        f"- Predicted pump-message rows: {len(pred_messages)}\n\n"
        f"Decision: `{decision['manipulation_input_state']}`. Accepted 95: `{accepted_95}`. "
        f"Blocker: {decision['blocker']}\n\n"
        f"Next action: {decision['next_action']}\n",
        encoding="utf-8",
    )
    (CHECKS_DIR / "bayi_hu_event_social_manipulation_gate_assertions.out").write_text(
        "\n".join(
            [
                f"RUN_ID {LOOP_ID}",
                f"REPORT {repo_rel(report_json)}",
                f"POSITIVE_PD_EVENTS {len(events)}",
                f"EXCHANGES {result['event_support']['exchanges']}",
                f"COINS {result['event_support']['coins']}",
                f"CALIBRATION_POSITIVE_EVENTS {chrono.get('calibration_positive_events')}",
                f"TEST_POSITIVE_EVENTS {chrono.get('test_positive_events')}",
                f"MANUAL_MESSAGE_LABEL_ROWS {sum(label_counts.values())}",
                f"PRED_PUMP_MESSAGE_ROWS {len(pred_messages)}",
                "NEGATIVE_EVENT_CONTROLS_AVAILABLE false",
                "ALIGNED_MARKET_FEATURES_AVAILABLE false",
                "ACCEPTED_95 false",
                "THRESHOLDS_RELAXED false",
                "RUNTIME_CODE_CHANGED false",
                "FRESH_CALIBRATION_RERUN false",
                "TRADE_USABLE false",
                "RAW_DATA_COMMITTED false",
                "GATE blocked_negative_controls_missing",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (RUN_ROOT / "README.md").write_text(
        "# Bayi-Hu Event/Social Manipulation Gate\n\n"
        "- report: `event-social-gate/bayi_hu_event_social_manipulation_gate.md`\n"
        "- json: `event-social-gate/bayi_hu_event_social_manipulation_gate.json`\n"
        "- assertions: `checks/bayi_hu_event_social_manipulation_gate_assertions.out`\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
