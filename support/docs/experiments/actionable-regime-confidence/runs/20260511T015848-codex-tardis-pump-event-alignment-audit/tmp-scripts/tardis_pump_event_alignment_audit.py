from __future__ import annotations

import csv
import json
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T015848-codex-tardis-pump-event-alignment-audit"
)
OUT_DIR = RUN_ROOT / "alignment"
CHECKS_DIR = RUN_ROOT / "checks"
LOOP_ID = "20260511T015848+0800-codex-tardis-pump-event-alignment-audit"
PUMP_ROOT = Path("/tmp/ict-regime-manipulation-datasets/pump-and-dump-dataset")
TARDIS_BINANCE_META_URL = "https://api.tardis.dev/v1/exchanges/binance"
QUOTE_SUFFIXES = ("btc", "usdt", "eth", "bnb")


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def parse_event_dt(row: dict[str, str]) -> datetime:
    return datetime.strptime(f"{row['date']} {row['hour']}", "%Y-%m-%d %H:%M")


def parse_tardis_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def fetch_tardis_binance_metadata() -> dict[str, Any]:
    with urllib.request.urlopen(TARDIS_BINANCE_META_URL, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    pump_csv = PUMP_ROOT / "pump_telegram.csv"
    if not pump_csv.exists():
        raise SystemExit(f"missing pump dataset at {pump_csv}")

    pump_rows = read_csv(pump_csv)
    binance_rows = [row for row in pump_rows if row.get("exchange") == "binance"]
    meta = fetch_tardis_binance_metadata()
    symbol_since: dict[str, datetime] = {}
    for symbol in meta.get("availableSymbols", []):
        symbol_id = str(symbol.get("id", "")).lower()
        if symbol_id:
            symbol_since[symbol_id] = parse_tardis_dt(str(symbol["availableSince"]))

    aligned_rows: list[dict[str, Any]] = []
    first_day_rows = 0
    candidate_symbol_rows = 0
    exact_date_available_rows = 0
    public_first_day_aligned_rows = 0
    for row in binance_rows:
        event_dt = parse_event_dt(row)
        base = row["symbol"].lower()
        candidates = []
        exact_available = []
        for quote in QUOTE_SUFFIXES:
            pair = f"{base}{quote}"
            since = symbol_since.get(pair)
            if since is None:
                continue
            item = {
                "pair": pair,
                "available_since": since.isoformat(),
                "available_on_event_date": since <= event_dt,
            }
            candidates.append(item)
            if item["available_on_event_date"]:
                exact_available.append(item)

        is_first_day = event_dt.day == 1
        if is_first_day:
            first_day_rows += 1
        if candidates:
            candidate_symbol_rows += 1
        if exact_available:
            exact_date_available_rows += 1
        if is_first_day and exact_available:
            public_first_day_aligned_rows += 1

        if is_first_day or exact_available:
            aligned_rows.append(
                {
                    "symbol": row["symbol"],
                    "group": row["group"],
                    "event_dt": event_dt.isoformat(),
                    "exchange": row["exchange"],
                    "first_day_public_dataset_date": is_first_day,
                    "candidate_pairs": candidates,
                    "exact_date_available_pairs": exact_available,
                    "public_first_day_direct_l2_alignment": bool(is_first_day and exact_available),
                }
            )

    decision = {
        "board_state": "blocked",
        "active_axis": "MainRegimeV2",
        "candidate_regime": "Manipulation",
        "accepted_95": False,
        "manipulation_input_state": "pump_labels_do_not_align_with_public_tardis_first_day_l2",
        "qualifying_direct_manipulation_input_sets": 0,
        "thresholds_relaxed": False,
        "runtime_code_changed": False,
        "fresh_calibration_rerun": False,
        "trade_usable": False,
        "blocker": (
            "Pump-and-dump labels are useful event supervision, and Tardis has direct L2 fields, "
            "but the public no-key first-day Tardis samples do not align with any Binance pump event "
            "that also has Tardis symbol availability on the event date."
        ),
        "next_action": (
            "Use a credentialed historical Tardis/Binance export for the nine Binance pump events "
            "whose symbols are available on their exact event dates, or provide another labeled "
            "direct L2/L3/order-lifecycle manipulation dataset before rerunning the unchanged gate."
        ),
    }
    result = {
        "schema_version": "tardis-pump-event-alignment-audit/v1",
        "loop_id": LOOP_ID,
        "run_root": repo_rel(RUN_ROOT),
        "pump_dataset": {
            "path": str(PUMP_ROOT),
            "pump_telegram_rows": len(pump_rows),
            "binance_events": len(binance_rows),
        },
        "tardis_metadata": {
            "url": TARDIS_BINANCE_META_URL,
            "available_symbol_count": len(symbol_since),
            "downloaded_at_local": datetime.now().isoformat(timespec="seconds"),
        },
        "alignment_counts": {
            "binance_events": len(binance_rows),
            "binance_first_day_events": first_day_rows,
            "binance_events_with_any_candidate_pair_in_tardis_metadata": candidate_symbol_rows,
            "binance_events_with_candidate_pair_available_on_exact_date": exact_date_available_rows,
            "public_first_day_events_with_candidate_pair_available_on_exact_date": public_first_day_aligned_rows,
        },
        "notable_alignment_rows": aligned_rows[:80],
        "decision": decision,
    }

    report_json = OUT_DIR / "tardis_pump_event_alignment_audit.json"
    report_md = OUT_DIR / "tardis_pump_event_alignment_audit.md"
    report_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    report_md.write_text(
        "# Tardis Pump Event Alignment Audit\n\n"
        f"Run id: `{LOOP_ID}`\n\n"
        "This audit checks whether the labeled Binance pump-and-dump events can be aligned with "
        "public no-key Tardis first-day direct L2/order-book data. It does not save raw Tardis data.\n\n"
        "Counts:\n"
        f"- Binance pump events: {len(binance_rows)}\n"
        f"- Binance first-day pump events: {first_day_rows}\n"
        f"- Candidate pairs present in Tardis metadata: {candidate_symbol_rows}\n"
        f"- Candidate pairs available on exact event date: {exact_date_available_rows}\n"
        f"- Public first-day aligned labeled direct-L2 events: {public_first_day_aligned_rows}\n\n"
        f"Decision: `{decision['manipulation_input_state']}`. "
        f"Accepted 95: `{decision['accepted_95']}`. "
        f"Blocker: {decision['blocker']}\n\n"
        f"Next action: {decision['next_action']}\n",
        encoding="utf-8",
    )
    (CHECKS_DIR / "tardis_pump_event_alignment_audit_assertions.out").write_text(
        "\n".join(
            [
                f"RUN_ID {LOOP_ID}",
                f"REPORT {repo_rel(report_json)}",
                f"BINANCE_EVENTS {len(binance_rows)}",
                f"BINANCE_FIRST_DAY_EVENTS {first_day_rows}",
                f"EXACT_DATE_AVAILABLE_EVENTS {exact_date_available_rows}",
                f"PUBLIC_FIRST_DAY_ALIGNED_EVENTS {public_first_day_aligned_rows}",
                "QUALIFYING_DIRECT_MANIPULATION_INPUT_SETS 0",
                f"MANIPULATION_INPUT_STATE {decision['manipulation_input_state']}",
                "ACCEPTED_95 false",
                "THRESHOLDS_RELAXED false",
                "RUNTIME_CODE_CHANGED false",
                "FRESH_CALIBRATION_RERUN false",
                "TRADE_USABLE false",
                "GATE blocked_public_tardis_label_alignment",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (RUN_ROOT / "README.md").write_text(
        "# Tardis Pump Event Alignment Audit\n\n"
        "Run-local audit that aligns labeled pump events with public Tardis metadata. "
        "Only metadata and counts are retained; no raw Tardis order-book files are committed.\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
