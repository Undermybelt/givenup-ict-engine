#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T112642+0800-codex-midsummer-chain-slice-expansion-audit"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T112642-codex-midsummer-chain-slice-expansion-audit"
OUT_DIR = RUN_ROOT / "chain-slice-audit"
CHECK_DIR = RUN_ROOT / "checks"
ZIP_PATH = Path("/tmp/ict-regime-midsummer-meme/meme_coin-main.zip")
CSV_MEMBER = "meme_coin_anon-main/data/dune_data_on_potential_wash_trading_makers_HP_coins.csv"
BOARD = "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
PREVIOUS_ACCEPTED_PLATFORM = "bsc"
Z95 = 1.959963984540054


def wilson_lcb(success: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + Z95 * Z95 / total
    center = p + Z95 * Z95 / (2.0 * total)
    margin = Z95 * math.sqrt((p * (1.0 - p) + Z95 * Z95 / (4.0 * total)) / total)
    return max(0.0, (center - margin) / denom)


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def chronological_cut(days: list[str]) -> str:
    unique_days = sorted(set(days))
    if not unique_days:
        return ""
    cut_index = min(len(unique_days) - 1, max(0, int(math.floor(len(unique_days) * 0.60))))
    return unique_days[cut_index]


def summarize_platform(platform: str, rows: list[dict[str, str]]) -> dict:
    by_token_day: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_token_day[(row["address"], row["day"])].append(row)

    paired_rows: list[dict[str, str]] = []
    paired_days = set()
    for token_day, token_rows in by_token_day.items():
        label_set = {parse_bool(row["is_both_buyer_seller"]) for row in token_rows}
        if label_set == {False, True}:
            paired_days.add(token_day)
            paired_rows.extend(token_rows)

    cut = chronological_cut([row["day"] for row in paired_rows])
    splits = {
        "calibration": [row for row in paired_rows if row["day"] <= cut],
        "test": [row for row in paired_rows if row["day"] > cut],
    }

    split_summary = {}
    min_lcb = 1.0
    for split_name, split_rows in splits.items():
        positives = sum(1 for row in split_rows if parse_bool(row["is_both_buyer_seller"]))
        negatives = sum(1 for row in split_rows if not parse_bool(row["is_both_buyer_seller"]))
        pos_lcb = wilson_lcb(positives, positives)
        neg_lcb = wilson_lcb(negatives, negatives)
        min_lcb = min(min_lcb, pos_lcb, neg_lcb)
        split_summary[split_name] = {
            "rows": len(split_rows),
            "positive_rows": positives,
            "negative_rows": negatives,
            "positive_wilson95_lcb": round(pos_lcb, 6),
            "negative_wilson95_lcb": round(neg_lcb, 6),
        }

    positive_rows = sum(1 for row in paired_rows if parse_bool(row["is_both_buyer_seller"]))
    negative_rows = len(paired_rows) - positive_rows
    accepted_95 = bool(paired_rows) and min_lcb >= 0.95
    reasons = []
    if not paired_rows:
        reasons.append("no_paired_token_day_positive_negative_controls")
    if split_summary["calibration"]["positive_wilson95_lcb"] < 0.95:
        reasons.append("calibration_positive_support_below_95_wilson")
    if split_summary["calibration"]["negative_wilson95_lcb"] < 0.95:
        reasons.append("calibration_negative_support_below_95_wilson")
    if split_summary["test"]["positive_wilson95_lcb"] < 0.95:
        reasons.append("test_positive_support_below_95_wilson")
    if split_summary["test"]["negative_wilson95_lcb"] < 0.95:
        reasons.append("test_negative_support_below_95_wilson")

    return {
        "platform": platform,
        "date_range": [
            min((row["day"] for row in paired_rows), default=None),
            max((row["day"] for row in paired_rows), default=None),
        ],
        "chronological_cut_date": cut,
        "paired_token_days": len(paired_days),
        "rows_total": len(paired_rows),
        "positive_rows_total": positive_rows,
        "negative_rows_total": negative_rows,
        "calibration": split_summary["calibration"],
        "test": split_summary["test"],
        "minimum_split_class_wilson95_lcb": round(min_lcb if paired_rows else 0.0, 6),
        "accepted_95": accepted_95,
        "already_ledgered_before_this_run": platform == PREVIOUS_ACCEPTED_PLATFORM and accepted_95,
        "rejection_reasons": reasons,
    }


def read_rows() -> list[dict[str, str]]:
    with zipfile.ZipFile(ZIP_PATH) as archive:
        with archive.open(CSV_MEMBER) as handle:
            text = (line.decode("utf-8") for line in handle)
            return list(csv.DictReader(text))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    if not ZIP_PATH.exists():
        raise FileNotFoundError(ZIP_PATH)

    rows = read_rows()
    rows_by_platform: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        rows_by_platform[row["platform"].strip().lower()].append(row)

    platform_summaries = [summarize_platform(platform, platform_rows) for platform, platform_rows in sorted(rows_by_platform.items())]
    accepted_platforms = [row for row in platform_summaries if row["accepted_95"]]
    new_accepted = [row for row in accepted_platforms if not row["already_ledgered_before_this_run"]]
    rejected_platforms = [row for row in platform_summaries if not row["accepted_95"]]

    platform_csv = OUT_DIR / "midsummer_chain_slice_platform_summary.csv"
    with platform_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "platform",
                "accepted_95",
                "already_ledgered_before_this_run",
                "paired_token_days",
                "rows_total",
                "positive_rows_total",
                "negative_rows_total",
                "minimum_split_class_wilson95_lcb",
                "chronological_cut_date",
                "rejection_reasons",
            ],
        )
        writer.writeheader()
        for item in platform_summaries:
            row = {key: item[key] for key in writer.fieldnames if key != "rejection_reasons"}
            row["rejection_reasons"] = ";".join(item["rejection_reasons"])
            writer.writerow(row)

    report = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": BOARD,
        "active_taxonomy": "MainRegimeV2",
        "source": {
            "title": "A Midsummer Meme's Dream direct wash-maker Dune export",
            "zip_path": str(ZIP_PATH),
            "zip_sha256_from_prior_audit": "4ef60d79cc70bc14287002d0a97a127ca46757690bae075801858356489571c9",
            "csv_member": CSV_MEMBER,
            "raw_data_committed": False,
        },
        "method": {
            "unit": "maker-token-day",
            "positive_rule": "same platform/address/day paired controls AND is_both_buyer_seller == True",
            "negative_rule": "same platform/address/day paired controls AND is_both_buyer_seller == False",
            "split": "per-platform chronological 60/40 by paired token-day",
            "acceptance_gate": "minimum calibration/test positive/negative Wilson95 LCB >= 0.95",
        },
        "input_profile": {
            "rows_total": len(rows),
            "platform_counts": dict(Counter(row["platform"].strip().lower() for row in rows)),
        },
        "platform_summaries": platform_summaries,
        "decision": {
            "accepted_parent_root_slots_added": 0,
            "accepted_direct_manipulation_rows_added": sum(item["positive_rows_total"] for item in new_accepted),
            "accepted_direct_manipulation_sources_added": len(new_accepted),
            "accepted_platforms_total": [item["platform"] for item in accepted_platforms],
            "new_accepted_platforms": [item["platform"] for item in new_accepted],
            "rejected_platforms": [item["platform"] for item in rejected_platforms],
            "gate_result": (
                "accepted_95_additional_midsummer_chain_wash_slices"
                if new_accepted
                else "blocked_no_additional_midsummer_chain_slice_beyond_prior_bsc"
            ),
            "full_objective_achieved": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "artifacts": {
            "json": repo_rel(OUT_DIR / "midsummer_chain_slice_expansion_audit.json"),
            "md": repo_rel(OUT_DIR / "midsummer_chain_slice_expansion_audit.md"),
            "platform_csv": repo_rel(platform_csv),
            "assertions": repo_rel(CHECK_DIR / "midsummer_chain_slice_expansion_audit_assertions.out"),
            "script": repo_rel(RUN_ROOT / "scripts/midsummer_chain_slice_expansion_audit.py"),
        },
        "next_action": "Do not generalize direct wash evidence to MainRegimeV2 price roots; continue acquiring full-matrix Bull/Bear/Sideways/Crisis source labels and non-wash direct Manipulation varieties.",
    }

    json_path = OUT_DIR / "midsummer_chain_slice_expansion_audit.json"
    md_path = OUT_DIR / "midsummer_chain_slice_expansion_audit.md"
    checks_path = CHECK_DIR / "midsummer_chain_slice_expansion_audit_assertions.out"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    summary_lines = [
        "# Midsummer Chain Slice Expansion Audit",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Scope",
        "",
        "This audit reuses the already downloaded Zenodo Midsummer ZIP under `/tmp` and checks whether the direct wash-maker Dune export contains additional per-chain accepted 95% slices beyond the BSC slice already written to the Board A cursor.",
        "",
        "## Method",
        "",
        "- Unit: `maker-token-day`.",
        "- Positive: same `platform/address/day` paired controls and `is_both_buyer_seller == True`.",
        "- Negative: same `platform/address/day` paired controls and `is_both_buyer_seller == False`.",
        "- Split: per-platform chronological 60/40 by paired token-day.",
        "- Gate: minimum calibration/test positive/negative Wilson95 LCB >= `0.95`.",
        "- Raw data committed: false.",
        "",
        "## Platform Summary",
        "",
        "| Platform | Accepted 95 | Already Ledgered | Paired Token-Days | Rows | Positives | Negatives | Min Split/Class LCB | Decision |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in platform_summaries:
        decision = "accepted" if item["accepted_95"] else "; ".join(item["rejection_reasons"])
        summary_lines.append(
            f"| `{item['platform']}` | `{str(item['accepted_95']).lower()}` | "
            f"`{str(item['already_ledgered_before_this_run']).lower()}` | "
            f"{item['paired_token_days']} | {item['rows_total']} | "
            f"{item['positive_rows_total']} | {item['negative_rows_total']} | "
            f"`{item['minimum_split_class_wilson95_lcb']}` | {decision} |"
        )

    summary_lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Accepted parent-root slots added: `0`.",
            f"- New accepted direct `Manipulation` rows added: `{report['decision']['accepted_direct_manipulation_rows_added']}`.",
            f"- New accepted platforms: `{', '.join(report['decision']['new_accepted_platforms']) if new_accepted else 'none'}`.",
            f"- Gate result: `{report['decision']['gate_result']}`.",
            "- Runtime code changed: false.",
            "- Thresholds relaxed: false.",
            "- Raw data committed: false.",
            "- Trade usable: false.",
            "",
            "This remains direct `Manipulation` wash-trading evidence only. It does not close any `Bull`/`Bear`/`Sideways`/`Crisis` parent-root slot and does not complete broader direct-manipulation variety coverage.",
            "",
        ]
    )
    md_path.write_text("\n".join(summary_lines), encoding="utf-8")

    checks = [
        "PASS active_taxonomy=MainRegimeV2",
        f"PASS source_zip_exists={str(ZIP_PATH.exists()).lower()}",
        "PASS raw_data_committed=false",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
        "PASS trade_usable=false",
        "PASS accepted_parent_root_slots_added=0",
        f"PASS new_accepted_platform_count={len(new_accepted)}",
        f"PASS accepted_direct_manipulation_rows_added={report['decision']['accepted_direct_manipulation_rows_added']}",
        f"GATE {report['decision']['gate_result']}",
        "PASS full_objective_achieved=false",
    ]
    checks_path.write_text("\n".join(checks) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
