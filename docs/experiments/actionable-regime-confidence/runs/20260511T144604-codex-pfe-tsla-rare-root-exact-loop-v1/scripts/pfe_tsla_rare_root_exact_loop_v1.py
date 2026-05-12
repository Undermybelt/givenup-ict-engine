#!/usr/bin/env python3
"""Package the selected PFE+TSLA rare-root exact-source loop.

This consumes accepted strict ticker/root rows from the 39-ticker yfinance 1h
universe expansion. It does not redownload provider bars or add a new model.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


RUN_ID = "20260511T144604+0800-codex-pfe-tsla-rare-root-exact-loop-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T144604-codex-pfe-tsla-rare-root-exact-loop-v1"
)
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
UNIVERSE_ROWS = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T141910-codex-exact-1h-source-universe-expansion-v1/"
    "exact-1h-universe/exact_1h_source_universe_expansion_v1_rows.csv"
)
SELECTOR_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T142858-codex-positive-target-selector-v1/"
    "positive-target-selector/positive_target_selector_v1.json"
)
OUT_JSON = RUN_ROOT / "rare-root-loop/pfe_tsla_rare_root_exact_loop_v1.json"
OUT_MD = RUN_ROOT / "rare-root-loop/pfe_tsla_rare_root_exact_loop_v1.md"
OUT_CSV = RUN_ROOT / "rare-root-loop/pfe_tsla_rare_root_exact_loop_v1_rows.csv"
OUT_ASSERT = RUN_ROOT / "checks/pfe_tsla_rare_root_exact_loop_v1_assertions.out"

SELECTED = ["PFE", "TSLA"]
TARGET_RARE_ROOTS = ["Bear", "Sideways", "Crisis"]
ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]


def main() -> int:
    board_sha = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    rows = pd.read_csv(UNIVERSE_ROWS)
    selector = json.loads(SELECTOR_JSON.read_text(encoding="utf-8"))
    selected_rows = rows[rows["instrument"].isin(SELECTED)].copy()
    accepted = selected_rows[selected_rows["accepted_95_strict_ticker_root_attachment"].astype(bool)].copy()
    accepted_roots = [root for root in ROOTS if root in set(accepted["root"])]
    rare_roots_closed = [root for root in TARGET_RARE_ROOTS if root in set(accepted["root"])]
    blocked = selected_rows[~selected_rows["accepted_95_strict_ticker_root_attachment"].astype(bool)].copy()

    accepted_by_ticker = {
        ticker: accepted[accepted["instrument"].eq(ticker)]["root"].tolist() for ticker in SELECTED
    }
    support_floor_by_accepted_root = {}
    for root in accepted_roots:
        root_rows = accepted[accepted["root"].eq(root)]
        support_floor_by_accepted_root[root] = int(
            root_rows[["calibration_2024_support", "heldout_time_2025_support"]].min(axis=1).max()
        )

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD),
        "board_sha256_at_run": board_sha,
        "inputs": {
            "universe_rows": str(UNIVERSE_ROWS),
            "selector_json": str(SELECTOR_JSON),
            "selector_top_pair": selector.get("decision", {}).get("top_pair", "PFE+TSLA"),
        },
        "policy": {
            "active_taxonomy": "MainRegimeV2",
            "selected_tickers": SELECTED,
            "timeframe": "1h",
            "consumer_scope": "intraday_parent_day_context_not_intraday_micro_regime",
            "no_new_provider_download": True,
            "no_crosswalk": True,
            "no_subregime_promotion": True,
        },
        "decision": {
            "selected_rows": int(len(selected_rows)),
            "accepted_rows": int(len(accepted)),
            "blocked_rows": int(len(blocked)),
            "accepted_roots": accepted_roots,
            "rare_roots_targeted": TARGET_RARE_ROOTS,
            "rare_roots_closed": rare_roots_closed,
            "accepted_by_ticker": accepted_by_ticker,
            "support_floor_by_accepted_root": support_floor_by_accepted_root,
            "accepted_gate": "pfe_tsla_rare_root_exact_loop_v1=accepted3_rare_roots_bear_sideways_crisis_no_new_download",
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_objective_achieved": False,
            "runtime_code_changed": False,
            "raw_data_committed": False,
            "thresholds_relaxed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Use a separate abundant-root exact-source pair for Bull if a two-market loop artifact is still needed; "
            "do not force Bull into the PFE+TSLA rare-root loop. Then run a completion audit against full objective "
            "coverage instead of rerunning proxy/no-source scans."
        ),
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_ASSERT.parent.mkdir(parents=True, exist_ok=True)
    selected_rows.to_csv(OUT_CSV, index=False)
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# PFE/TSLA Rare-Root Exact Loop v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This loop executes the positive selector's next target without another provider download.",
        "It consumes accepted strict exact-source `1h` rows from `141910`.",
        "",
        "## Result",
        "",
        f"- Selected pair: `{'+'.join(SELECTED)}`.",
        "- Purpose: close rare-root exact-source supply for `Bear`, `Sideways`, and `Crisis` in a two-market loop.",
        f"- Selected pair rows: `{len(selected_rows)}`.",
        f"- Accepted strict rows: `{len(accepted)}`.",
        f"- Blocked non-target rows retained: `{len(blocked)}`.",
        f"- Accepted roots: `{', '.join(accepted_roots)}`.",
        f"- Rare roots closed: `{', '.join(rare_roots_closed)}`.",
        "- Full objective achieved: `false`.",
        "- Runtime code changed: `false`.",
        "- Thresholds relaxed: `false`.",
        "- Raw data committed: `false`.",
        "- Trade usable: `false`.",
        "- Gate result: `pfe_tsla_rare_root_exact_loop_v1=accepted3_rare_roots_bear_sideways_crisis_no_new_download`.",
        "",
        "## Accepted Rows",
        "",
        "| Ticker | Root | 2024 Cal Support | 2024 Cal Wilson95 | 2025 Heldout Support | 2025 Heldout Wilson95 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in accepted.itertuples(index=False):
        lines.append(
            f"| `{row.instrument}` | `{row.root}` | {row.calibration_2024_support} | "
            f"{row.calibration_2024_wilson95_lcb:.6f} | {row.heldout_time_2025_support} | "
            f"{row.heldout_time_2025_wilson95_lcb:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Non-Target Blocked Rows",
            "",
            "- `PFE:Bull`, `PFE:Crisis`, `TSLA:Bull`, `TSLA:Bear`, and `TSLA:Sideways` remain blocked in this pair.",
            "- That is expected: this loop is the rare-root pair selected by `142858`, not a forced all-root pair.",
            "",
            "## Next",
            "",
            "- Use a separate abundant-root exact-source pair for `Bull` if a two-market loop artifact is still needed.",
            "- Then run a completion audit against full objective coverage instead of rerunning proxy/no-source scans.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    failures = []
    if accepted_roots != TARGET_RARE_ROOTS:
        failures.append(f"expected_rare_roots_{','.join(TARGET_RARE_ROOTS)}_got_{','.join(accepted_roots)}")
    if len(accepted) != 3:
        failures.append(f"expected_accepted_rows_3_got_{len(accepted)}")
    if result["decision"]["full_objective_achieved"]:
        failures.append("full_objective_should_remain_false")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={board_sha}",
        "selected_pair=PFE+TSLA",
        f"accepted_rows={len(accepted)}",
        f"blocked_rows={len(blocked)}",
        f"accepted_roots={','.join(accepted_roots)}",
        f"rare_roots_closed={','.join(rare_roots_closed)}",
        "new_provider_downloads=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "full_objective_achieved=false",
        "assertion_status=PASS" if not failures else "assertion_status=FAIL",
    ]
    assertions.extend(f"FAIL {failure}" for failure in failures)
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    if failures:
        raise RuntimeError("; ".join(failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
