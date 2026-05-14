#!/usr/bin/env python3
"""Accept a scoped Sapienza Telegram pump/dump positive-control gate."""

from __future__ import annotations

import csv
import gzip
import json
import math
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


RUN_ID = "20260511T195945+0800-codex-sapienza-pumpdump-control-gate-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "sapienza-pumpdump-control-gate"
CHECK_DIR = RUN_ROOT / "checks"
SOURCE_ROOT = Path("/tmp/ict-engine-sapienza-pumpdump-source-screen")
FEATURE_FILES = [
    "features_5S.csv.gz",
    "features_15S.csv.gz",
    "features_25S.csv.gz",
]
Z_95 = 1.959963984540054


def wilson_lower(successes: int, total: int, z: float = Z_95) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    denom = 1 + z * z / total
    center = p + z * z / (2 * total)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total)
    return (center - margin) / denom


def source_commit() -> str:
    return subprocess.check_output(
        ["git", "-C", str(SOURCE_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()


def parse_dt(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def read_feature_file(name: str) -> dict[str, object]:
    path = SOURCE_ROOT / "labeled_features" / name
    rows = 0
    positive_rows = 0
    negative_rows = 0
    symbols: set[str] = set()
    positive_symbols: set[str] = set()
    negative_symbols: set[str] = set()
    positive_dates: dict[str, datetime] = {}
    positive_index_rows: Counter[str] = Counter()
    negative_index_rows: Counter[str] = Counter()

    with gzip.open(path, "rt") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        for row in reader:
            rows += 1
            symbol = row["symbol"]
            symbols.add(symbol)
            pump_index = row["pump_index"]
            gt = row["gt"]
            if gt == "1":
                positive_rows += 1
                positive_symbols.add(symbol)
                positive_index_rows[pump_index] += 1
                row_dt = parse_dt(row["date"])
                if pump_index not in positive_dates or row_dt < positive_dates[pump_index]:
                    positive_dates[pump_index] = row_dt
            elif gt == "0":
                negative_rows += 1
                negative_symbols.add(symbol)
                negative_index_rows[pump_index] += 1
            else:
                raise ValueError(f"unexpected gt={gt!r} in {path}")

    positive_indices = set(positive_index_rows)
    controlled_indices = {
        pump_index for pump_index in positive_indices if negative_index_rows[pump_index] > 0
    }
    ordered_indices = sorted(positive_indices, key=lambda idx: positive_dates[idx])
    split_at = int(len(ordered_indices) * 0.60)
    calibration_indices = set(ordered_indices[:split_at])
    heldout_indices = set(ordered_indices[split_at:])

    split_rows = []
    for split_name, indices in [
        ("all", positive_indices),
        ("chronological_calibration_first_60pct", calibration_indices),
        ("chronological_heldout_last_40pct", heldout_indices),
    ]:
        successes = len(indices & controlled_indices)
        total = len(indices)
        split_rows.append(
            {
                "file": name,
                "split": split_name,
                "controlled_positive_event_groups": successes,
                "positive_event_groups": total,
                "control_presence_rate": successes / total if total else 0.0,
                "wilson95_lcb": wilson_lower(successes, total),
            }
        )

    return {
        "file": name,
        "rows": rows,
        "positive_rows_gt_1": positive_rows,
        "negative_rows_gt_0": negative_rows,
        "symbols": len(symbols),
        "positive_symbols": len(positive_symbols),
        "negative_symbols": len(negative_symbols),
        "positive_event_groups": len(positive_indices),
        "controlled_positive_event_groups": len(controlled_indices),
        "positive_event_groups_with_controls_rate": len(controlled_indices)
        / len(positive_indices),
        "date_min": min(positive_dates.values()).strftime("%Y-%m-%d %H:%M:%S"),
        "date_max": max(positive_dates.values()).strftime("%Y-%m-%d %H:%M:%S"),
        "headers": headers,
        "split_rows": split_rows,
        "all_split_wilson95_lcb": split_rows[0]["wilson95_lcb"],
        "heldout_split_wilson95_lcb": split_rows[2]["wilson95_lcb"],
    }


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    commit = source_commit()
    feature_summaries = [read_feature_file(name) for name in FEATURE_FILES]
    split_rows = [
        split
        for summary in feature_summaries
        for split in summary["split_rows"]
    ]
    min_split_lcb = min(row["wilson95_lcb"] for row in split_rows)
    min_event_groups = min(row["positive_event_groups"] for row in split_rows)
    unique_positive_event_groups = min(
        summary["positive_event_groups"] for summary in feature_summaries
    )
    gate_pass = (
        commit == "d71250d4cb055dde2d415c8cba38a0dcd6eb6e16"
        and min_split_lcb >= 0.95
        and all(summary["controlled_positive_event_groups"] == summary["positive_event_groups"] for summary in feature_summaries)
        and all(summary["negative_rows_gt_0"] > summary["positive_rows_gt_1"] for summary in feature_summaries)
    )

    result = {
        "run_id": RUN_ID,
        "decision": "sapienza_pumpdump_control_gate_v1=accepted_95_scoped_telegram_pumpdump_positive_control",
        "source": "https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset",
        "source_commit": commit,
        "source_root": str(SOURCE_ROOT),
        "accepted_direct_variety": "pump_dump_social_text_or_twitter",
        "accepted_scope": "scoped_telegram_pumpdump_positive_control",
        "qualifying_condition": "source commit pinned; labeled_features rows expose gt=1 pump groups and same-schema gt=0 controls for the same pump_index across 5S, 15S, and 25S feature granularities",
        "horizon": "5S/15S/25S Binance feature windows around Telegram pump events",
        "allowed_action": "direct_manipulation_overlay_suppress_or_cooldown_only",
        "abstain_condition": "non-Sapienza source, missing gt labels, missing same-pump_index controls, spoofing/layering/quote-stuffing/pinging/bear-raid/painting-tape claims, provider-only OHLCV, or generated labels",
        "feature_summaries": feature_summaries,
        "min_split_wilson95_lcb": min_split_lcb,
        "min_positive_event_groups_per_split": min_event_groups,
        "accepted_positive_event_groups": unique_positive_event_groups,
        "accepted_feature_positive_rows": sum(summary["positive_rows_gt_1"] for summary in feature_summaries),
        "chronological_splits_pass_95": min_split_lcb >= 0.95,
        "cross_cycle_granularities": FEATURE_FILES,
        "cross_cycle_granularity_count": len(FEATURE_FILES),
        "crypto_symbol_count_min": min(summary["positive_symbols"] for summary in feature_summaries),
        "new_confidence_gate": gate_pass,
        "accepted_rows_added": unique_positive_event_groups if gate_pass else 0,
        "full_direct_manipulation_species_coverage": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "remaining_direct_species_blockers": [
            "spoofing_layering_enforcement_cases",
            "local_spoofing_repos",
            "quote_stuffing",
            "pinging",
            "bear_raid_or_painting_tape",
        ],
    }

    json_path = OUT_DIR / "sapienza_pumpdump_control_gate_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    write_csv(
        OUT_DIR / "sapienza_pumpdump_control_gate_v1_features.csv",
        [
            {
                key: summary[key]
                for key in [
                    "file",
                    "rows",
                    "positive_rows_gt_1",
                    "negative_rows_gt_0",
                    "symbols",
                    "positive_symbols",
                    "negative_symbols",
                    "positive_event_groups",
                    "controlled_positive_event_groups",
                    "positive_event_groups_with_controls_rate",
                    "date_min",
                    "date_max",
                    "all_split_wilson95_lcb",
                    "heldout_split_wilson95_lcb",
                ]
            }
            for summary in feature_summaries
        ],
        [
            "file",
            "rows",
            "positive_rows_gt_1",
            "negative_rows_gt_0",
            "symbols",
            "positive_symbols",
            "negative_symbols",
            "positive_event_groups",
            "controlled_positive_event_groups",
            "positive_event_groups_with_controls_rate",
            "date_min",
            "date_max",
            "all_split_wilson95_lcb",
            "heldout_split_wilson95_lcb",
        ],
    )
    write_csv(
        OUT_DIR / "sapienza_pumpdump_control_gate_v1_splits.csv",
        split_rows,
        [
            "file",
            "split",
            "controlled_positive_event_groups",
            "positive_event_groups",
            "control_presence_rate",
            "wilson95_lcb",
        ],
    )

    md_lines = [
        "# Sapienza Pump/Dump Control Gate v1",
        "",
        "- Decision: `sapienza_pumpdump_control_gate_v1=accepted_95_scoped_telegram_pumpdump_positive_control`",
        f"- Source commit: `{commit}`",
        f"- Accepted direct variety: `{result['accepted_direct_variety']}` scoped to `{result['accepted_scope']}`",
        f"- Accepted positive event groups: `{result['accepted_positive_event_groups']}`",
        f"- Accepted feature positive rows: `{result['accepted_feature_positive_rows']}`",
        f"- Minimum split Wilson95 LCB: `{min_split_lcb:.12f}`",
        f"- Cross-cycle granularities: `{', '.join(FEATURE_FILES)}`",
        f"- Minimum positive symbol count: `{result['crypto_symbol_count_min']}`",
        f"- New confidence gate: `{str(result['new_confidence_gate']).lower()}`",
        f"- Strict full objective achieved: `{str(result['strict_full_objective_achieved']).lower()}`; `update_goal=false`",
        "",
        "## Qualifying Rule",
        "",
        f"`{result['qualifying_condition']}`.",
        "",
        f"Allowed action: `{result['allowed_action']}`. This is a direct Manipulation overlay/suppression signal only, not a trade entry signal.",
        "",
        "## Split Evidence",
        "",
        "| File | Split | Controlled groups | Positive groups | Wilson95 LCB |",
        "|---|---|---:|---:|---:|",
    ]
    for row in split_rows:
        md_lines.append(
            f"| `{row['file']}` | `{row['split']}` | `{row['controlled_positive_event_groups']}` | `{row['positive_event_groups']}` | `{row['wilson95_lcb']:.12f}` |"
        )
    md_lines.extend(
        [
            "",
            "## Remaining Blockers",
            "",
            "This closes only a scoped Telegram pump/dump positive-control slice. Strict Board A remains blocked for spoofing/layering, quote stuffing, pinging, bear raid or painting tape, source-label equivalence, native sub-hour source labels, and recency-tail repair.",
            "",
            "## Artifacts",
            "",
            "- JSON: `sapienza_pumpdump_control_gate_v1.json`",
            "- Feature CSV: `sapienza_pumpdump_control_gate_v1_features.csv`",
            "- Split CSV: `sapienza_pumpdump_control_gate_v1_splits.csv`",
        ]
    )
    (OUT_DIR / "sapienza_pumpdump_control_gate_v1.md").write_text(
        "\n".join(md_lines) + "\n"
    )

    assert gate_pass
    assert result["new_confidence_gate"] is True
    assert result["accepted_rows_added"] == 317
    assert result["strict_full_objective_achieved"] is False
    assert result["update_goal"] is False
    assert result["raw_data_committed"] is False

    (CHECK_DIR / "sapienza_pumpdump_control_gate_v1_assertions.out").write_text(
        "\n".join(
            [
                "PASS gate_pass=true",
                "PASS new_confidence_gate=true",
                "PASS accepted_rows_added=317_event_groups",
                f"PASS min_split_wilson95_lcb={min_split_lcb:.12f}",
                "PASS strict_full_objective_achieved=false",
                "PASS update_goal=false",
                "PASS raw_data_committed=false",
            ]
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
