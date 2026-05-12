#!/usr/bin/env python3
"""Select positive next targets from already accepted exact-source rows."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any


RUN_ID = "20260511T142858+0800-codex-positive-target-selector-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T142858-codex-positive-target-selector-v1"
)
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
SOURCE_ROWS = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T141910-codex-exact-1h-source-universe-expansion-v1/"
    "exact-1h-universe/exact_1h_source_universe_expansion_v1_rows.csv"
)
OUT_JSON = RUN_ROOT / "positive-target-selector/positive_target_selector_v1.json"
OUT_MD = RUN_ROOT / "positive-target-selector/positive_target_selector_v1.md"
OUT_CSV = RUN_ROOT / "positive-target-selector/positive_target_selector_v1_targets.csv"
OUT_ASSERT = RUN_ROOT / "checks/positive_target_selector_v1_assertions.out"

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
ROOT_WEIGHTS = {"Bull": 1, "Sideways": 2, "Bear": 4, "Crisis": 5}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def load_rows() -> list[dict[str, Any]]:
    with SOURCE_ROWS.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    accepted: list[dict[str, Any]] = []
    for row in rows:
        if not parse_bool(row["accepted_95_strict_ticker_root_attachment"]):
            continue
        cal_support = int(row["calibration_2024_support"])
        heldout_support = int(row["heldout_time_2025_support"])
        cal_lcb = float(row["calibration_2024_wilson95_lcb"])
        heldout_lcb = float(row["heldout_time_2025_wilson95_lcb"])
        row["support_floor"] = min(cal_support, heldout_support)
        row["lcb_floor"] = min(cal_lcb, heldout_lcb)
        row["root_weight"] = ROOT_WEIGHTS[row["root"]]
        accepted.append(row)
    return accepted


def top_anchor_rows(accepted: list[dict[str, Any]], limit_per_root: int = 5) -> dict[str, list[dict[str, Any]]]:
    by_root: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in accepted:
        by_root[row["root"]].append(row)
    return {
        root: sorted(
            by_root[root],
            key=lambda item: (
                int(item["support_floor"]),
                float(item["lcb_floor"]),
                item["instrument"],
            ),
            reverse=True,
        )[:limit_per_root]
        for root in ROOTS
    }


def pair_targets(accepted: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    by_ticker: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in accepted:
        by_ticker[row["instrument"]][row["root"]] = row

    pairs: list[dict[str, Any]] = []
    for left, right in combinations(sorted(by_ticker), 2):
        roots = sorted(set(by_ticker[left]) | set(by_ticker[right]), key=lambda root: ROOTS.index(root))
        rare_roots = [root for root in roots if root in {"Bear", "Crisis"}]
        support_sum = 0
        support_floor = None
        for root in roots:
            candidates = [by_ticker[ticker][root] for ticker in (left, right) if root in by_ticker[ticker]]
            best = max(candidates, key=lambda item: int(item["support_floor"]))
            support_sum += int(best["support_floor"])
            support_floor = int(best["support_floor"]) if support_floor is None else min(support_floor, int(best["support_floor"]))
        score = (
            sum(ROOT_WEIGHTS[root] for root in roots) * 1000
            + len(roots) * 100
            + len(rare_roots) * 50
            + support_sum / 10
        )
        pairs.append(
            {
                "left": left,
                "right": right,
                "roots_covered": roots,
                "rare_roots_covered": rare_roots,
                "root_count": len(roots),
                "rare_root_count": len(rare_roots),
                "support_floor_min": int(support_floor or 0),
                "support_floor_sum": int(support_sum),
                "score": round(score, 3),
            }
        )
    return sorted(
        pairs,
        key=lambda item: (
            item["score"],
            item["rare_root_count"],
            item["root_count"],
            item["support_floor_sum"],
        ),
        reverse=True,
    )[:limit]


def write_targets_csv(anchor_rows: dict[str, list[dict[str, Any]]], pairs: list[dict[str, Any]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "rank",
        "target_type",
        "instrument_set",
        "roots",
        "rare_roots",
        "support_floor_min",
        "support_floor_sum",
        "score",
        "action",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        rank = 1
        for pair in pairs:
            writer.writerow(
                {
                    "rank": rank,
                    "target_type": "two_market_pair",
                    "instrument_set": f"{pair['left']}+{pair['right']}",
                    "roots": ",".join(pair["roots_covered"]),
                    "rare_roots": ",".join(pair["rare_roots_covered"]),
                    "support_floor_min": pair["support_floor_min"],
                    "support_floor_sum": pair["support_floor_sum"],
                    "score": pair["score"],
                    "action": "use_as_next_positive_exact_source_pair",
                }
            )
            rank += 1
        for root in ROOTS:
            for row in anchor_rows[root]:
                writer.writerow(
                    {
                        "rank": rank,
                        "target_type": "single_root_anchor",
                        "instrument_set": row["instrument"],
                        "roots": row["root"],
                        "rare_roots": row["root"] if row["root"] in {"Bear", "Crisis"} else "",
                        "support_floor_min": row["support_floor"],
                        "support_floor_sum": row["support_floor"],
                        "score": row["root_weight"],
                        "action": "keep_as_positive_anchor_not_negative_probe",
                    }
                )
                rank += 1


def main() -> int:
    board_sha = sha256(BOARD)
    accepted = load_rows()
    anchor_rows = top_anchor_rows(accepted)
    pairs = pair_targets(accepted)
    pair_covering_all_roots = [
        pair for pair in pairs if set(pair["roots_covered"]) == set(ROOTS)
    ]
    top_pair = pairs[0]

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD),
        "board_sha256_at_run": board_sha,
        "input": {
            "source_rows": str(SOURCE_ROWS),
            "source_run": "20260511T141910+0800-codex-exact-1h-source-universe-expansion-v1",
            "new_provider_downloads": False,
            "runtime_code_changed": False,
        },
        "decision": {
            "accepted_strict_rows_consumed": len(accepted),
            "accepted_roots_present": sorted({row["root"] for row in accepted}, key=lambda root: ROOTS.index(root)),
            "top_two_market_pair": top_pair,
            "two_market_pair_can_cover_all_four_roots": bool(pair_covering_all_roots),
            "full_objective_achieved": False,
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "gate_result": "positive_target_selector_v1_rare_root_anchors_selected_no_new_confidence_gate",
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "anchor_rows": {
            root: [
                {
                    "instrument": row["instrument"],
                    "root": row["root"],
                    "calibration_2024_support": int(row["calibration_2024_support"]),
                    "heldout_time_2025_support": int(row["heldout_time_2025_support"]),
                    "support_floor": int(row["support_floor"]),
                    "lcb_floor": float(row["lcb_floor"]),
                }
                for row in rows
            ]
            for root, rows in anchor_rows.items()
        },
        "next_action": (
            "Use PFE+TSLA as the next two-market positive exact-source loop because it covers "
            "Bear, Sideways, and Crisis from accepted strict 1h rows; keep Bull on a separate "
            "abundant-root pair instead of forcing one loop to cover all four roots."
        ),
        "do_not_repeat": [
            "Do not rerun broad no-source filename scans.",
            "Do not use ^IXIC as a QQQ/NQ proxy without explicit owner-approved policy.",
            "Do not promote OHLCV/provider bars, HMM/model labels, generated labels, or future-return labels.",
            "Do not call update_goal from this selector.",
        ],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_ASSERT.parent.mkdir(parents=True, exist_ok=True)
    write_targets_csv(anchor_rows, pairs)
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Positive Target Selector v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This is a selector, not another source sweep. It consumes the already accepted strict exact-source `1h` rows from `141910` and ranks only positive next targets.",
        "",
        "## Result",
        "",
        f"- Accepted strict rows consumed: `{len(accepted)}`.",
        f"- Accepted roots present: `{', '.join(result['decision']['accepted_roots_present'])}`.",
        f"- Top two-market pair: `{top_pair['left']}+{top_pair['right']}`.",
        f"- Top pair roots: `{', '.join(top_pair['roots_covered'])}`.",
        f"- Top pair rare roots: `{', '.join(top_pair['rare_roots_covered'])}`.",
        f"- Two-market pair can cover all four roots under strict rows: `{str(bool(pair_covering_all_roots)).lower()}`.",
        "- Gate result: `positive_target_selector_v1_rare_root_anchors_selected_no_new_confidence_gate`.",
        "- Full objective achieved: `false`.",
        "- Runtime code changed: `false`.",
        "- Thresholds relaxed: `false`.",
        "- Raw data committed: `false`.",
        "- Trade usable: `false`.",
        "",
        "## Top Pairs",
        "",
        "| Rank | Pair | Roots | Rare Roots | Support Floor Min | Score |",
        "|---:|---|---|---|---:|---:|",
    ]
    for rank, pair in enumerate(pairs[:8], start=1):
        lines.append(
            "| {rank} | `{left}+{right}` | `{roots}` | `{rare}` | {floor} | {score:.3f} |".format(
                rank=rank,
                left=pair["left"],
                right=pair["right"],
                roots=",".join(pair["roots_covered"]),
                rare=",".join(pair["rare_roots_covered"]),
                floor=pair["support_floor_min"],
                score=pair["score"],
            )
        )
    lines.extend(
        [
            "",
            "## Root Anchors",
            "",
            "| Root | Best Anchors |",
            "|---|---|",
        ]
    )
    for root in ROOTS:
        anchors = ", ".join(
            f"`{row['instrument']}`({row['support_floor']})"
            for row in anchor_rows[root]
        )
        lines.append(f"| `{root}` | {anchors} |")
    lines.extend(
        [
            "",
            "## Next",
            "",
            "- Use `PFE+TSLA` as the next rare-root exact-source loop: `PFE` supplies strict `Bear` and `Sideways`; `TSLA` supplies strict `Crisis`.",
            "- Keep `Bull` separate because it is already abundant; forcing all four roots into a two-market strict loop creates a false bottleneck.",
            "- Do not return to NQ/QQQ proxy work unless a Nasdaq-100-grade source-label panel or explicit owner-approved `^IXIC` policy appears.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={board_sha}",
        f"accepted_strict_rows_consumed={len(accepted)}",
        f"accepted_roots_present={result['decision']['accepted_roots_present']}",
        f"top_pair={top_pair['left']}+{top_pair['right']}",
        f"top_pair_roots={top_pair['roots_covered']}",
        f"two_market_pair_can_cover_all_four_roots={str(bool(pair_covering_all_roots)).lower()}",
        "new_provider_downloads=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "full_objective_achieved=false",
        "update_goal=false",
    ]
    failures = []
    if len(accepted) <= 0:
        failures.append("no_accepted_rows_consumed")
    if set(result["decision"]["accepted_roots_present"]) != set(ROOTS):
        failures.append("not_all_roots_present_in_accepted_supply")
    if not {"Bear", "Crisis"}.issubset(set(top_pair["rare_roots_covered"])):
        failures.append("top_pair_does_not_prioritize_bear_and_crisis")
    if result["decision"]["full_objective_achieved"]:
        failures.append("selector_must_not_mark_full_objective_complete")
    assertions.append(f"assertion_status={'FAIL' if failures else 'PASS'}")
    if failures:
        assertions.append("failures=" + ",".join(failures))
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
