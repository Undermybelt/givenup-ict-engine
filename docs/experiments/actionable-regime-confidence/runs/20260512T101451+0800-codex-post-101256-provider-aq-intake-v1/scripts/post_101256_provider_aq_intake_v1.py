#!/usr/bin/env python3
"""Register latest provider acquisition / Auto-Quant preseed roots.

Read-only aggregation over 101040, 101138, 101221, and 101256. 101138 is
duplicate-guard context when already registered by another agent; the useful
count here is 101221 data-ready / seed-required and 101256 Yahoo NQ zero-trade.
The result is explicitly non-promoting for Board A: data acquisition and AQ
readiness improved, but no source/control unlock, selected-history approval, or
execution promotion was created.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T101451+0800-codex-post-101256-provider-aq-intake-v1"
REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "post-101256-provider-aq-intake-v1"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

ROOT_101040 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T101040+0800-codex-board-b-093854-local-cache-seed-v1"
ROOT_101138 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T101138+0800-codex-board-b-provider-acquisition-reroute-v1"
ROOT_101221 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T101221+0800-codex-board-b-093854-local-cache-seed-v2"
ROOT_101256 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T101256+0800-codex-board-b-provider-yahoo-nq-aq-preseed-v1"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> Any:
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError:
        return None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def exit_code(path: Path) -> str:
    return read_text(path).strip()


def line_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def parse_metric(text: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    status_after = read_json(ROOT_101221 / "command-output/02_auto_quant_status_after.out") or {}
    harness = read_json(ROOT_101138 / "command-output/01_market_data_harness_fetch.out") or {}
    harness_results = [
        {
            "role": item.get("role"),
            "provider": item.get("provider"),
            "ok": item.get("ok"),
            "error": (item.get("error") or {}).get("message"),
        }
        for item in harness.get("results", [])
    ]
    tomac_out = read_text(ROOT_101256 / "command-output/03_run_tomac_provider_yahoo_nq_abs.out")

    kraken_csv = ROOT_101138 / "provider-data/kraken_XBTUSD_1h.csv"
    bybit_csv = ROOT_101138 / "provider-data/bybit_BTCUSDT_linear_1h.csv"
    provider_nq_feathers = [
        ROOT_101256 / "workspace/auto-quant-yahoo-nq/user_data/data/NQ_USD-1h.feather",
        ROOT_101256 / "workspace/auto-quant-yahoo-nq/user_data/data/NQ_USD-4h.feather",
        ROOT_101256 / "workspace/auto-quant-yahoo-nq/user_data/data/NQ_USD-1d.feather",
    ]

    reviewed_roots = [
        {
            "run": "101040_local_cache_seed_v1",
            "path": rel(ROOT_101040),
            "exists": ROOT_101040.exists(),
            "gate": "superseded_by_101221_local_cache_seed_v2",
            "promotion": False,
        },
        {
            "run": "101138_provider_acquisition_reroute",
            "path": rel(ROOT_101138),
            "exists": ROOT_101138.exists(),
            "gate": "provider_data_acquired_partial_non_promoting",
            "provider_status_exit": exit_code(ROOT_101138 / "checks/00_provider_status_agent.exit"),
            "harness_exit": exit_code(ROOT_101138 / "checks/01_market_data_harness_fetch.exit"),
            "kraken_exit": exit_code(ROOT_101138 / "checks/02_kraken_xbtusd_1h.exit"),
            "bybit_exit": exit_code(ROOT_101138 / "checks/03_bybit_btcusdt_1h.exit"),
            "harness_results": harness_results,
            "kraken_csv_rows_including_header": line_count(kraken_csv),
            "bybit_csv_rows_including_header": line_count(bybit_csv),
            "promotion": False,
        },
        {
            "run": "101221_local_cache_seed_v2",
            "path": rel(ROOT_101221),
            "exists": ROOT_101221.exists(),
            "gate": "autoquant_data_ready_seed_strategies_required_non_promoting",
            "status_before_exit": exit_code(ROOT_101221 / "checks/00_auto_quant_status_before.exit"),
            "seed_exit": exit_code(ROOT_101221 / "checks/01_seed_local_cache.exit"),
            "status_after_exit": exit_code(ROOT_101221 / "checks/02_auto_quant_status_after.exit"),
            "auto_quant_status": status_after.get("status"),
            "healthy": status_after.get("healthy"),
            "data_ready": status_after.get("data_ready"),
            "next_blocker": (status_after.get("next_step") or {}).get("blocked_reason"),
            "promotion": False,
        },
        {
            "run": "101256_yahoo_nq_aq_preseed",
            "path": rel(ROOT_101256),
            "exists": ROOT_101256.exists(),
            "gate": "provider_yahoo_nq_preseed_zero_trade_non_promoting",
            "prepare_initial_exit": exit_code(ROOT_101256 / "checks/00_prepare_provider_csv.exit"),
            "run_initial_exit": exit_code(ROOT_101256 / "checks/01_run_tomac_provider_yahoo_nq.exit"),
            "prepare_abs_exit": exit_code(ROOT_101256 / "checks/02_prepare_provider_csv_abs.exit"),
            "run_abs_exit": exit_code(ROOT_101256 / "checks/03_run_tomac_provider_yahoo_nq_abs.exit"),
            "provider_feathers_present": all(path.exists() for path in provider_nq_feathers),
            "trade_count": parse_metric(tomac_out, "trade_count"),
            "total_profit_pct": parse_metric(tomac_out, "total_profit_pct"),
            "profit_factor": parse_metric(tomac_out, "profit_factor"),
            "promotion": False,
        },
    ]

    checklist = [
        {
            "requirement": "real provider data beyond yfinance only",
            "evidence": "101138 acquired Kraken XBTUSD 1h and Bybit BTCUSDT 1h CSVs; yfinance QQQ harness succeeded while TradingView/IBKR failed",
            "status": "partial_non_promoting",
        },
        {
            "requirement": "Auto-Quant data readiness",
            "evidence": "101221 status_after is dependency_ready_seed_required with data_ready true, but seed strategies are still required",
            "status": "partial_non_promoting",
        },
        {
            "requirement": "Auto-Quant measured provider NQ run",
            "evidence": "101256 generated NQ_USD 1h/4h/1d feathers and ran TOMAC successfully, but trade_count=0",
            "status": "non_promoting",
        },
        {
            "requirement": "every regime 95%-99% plus cross-market/timeframe validation",
            "evidence": "no new accepted regime packet, no source/control unlock, no selected-history approval",
            "status": "not_complete",
        },
        {
            "requirement": "do not disturb concurrent agents",
            "evidence": "append-only aggregation; no existing root edited; promotion flags false",
            "status": "pass",
        },
    ]

    gates = {
        "accepted_rows_added": 0,
        "source_control_evidence_acquired": False,
        "explicit_user_selected_history": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
    }

    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_file": rel(BOARD),
        "board_sha256_before": sha256(BOARD),
        "reviewed_roots": reviewed_roots,
        "checklist": checklist,
        "gates": gates,
        "gate_result": "post_101256_provider_aq_intake_v1=101221_data_ready_101256_zero_trade_101138_duplicate_guard_non_promoting_goal_not_complete",
        "next": "Do not repeat these provider/preseed shapes; proceed only with a changed source/control surface, explicit selected-history choice, or non-overlapping branch improvement.",
    }

    write_json(OUT / "post_101256_provider_aq_intake_v1.json", payload)
    write_csv(OUT / "prompt_to_artifact_checklist_post_101256_v1.csv", checklist, ["requirement", "evidence", "status"])

    report = f"""# Post-101256 Provider / Auto-Quant Intake v1

Run id: `{RUN_ID}`

Mode: `append_only_readonly_non_promoting`

## Scope

This audit registers latest file-backed Auto-Quant preseed roots `101221` and `101256`, treats `101040` as superseded, and treats `101138` as duplicate-guard provider context when it has already been registered by another agent. It does not select `HTF`, `MTF`, or `LTF`, does not approve source/control evidence, does not mutate canonical intake, does not promote Auto-Quant / BBN / CatBoost / execution-tree output, and does not call `update_goal`.

## Readback

- `101040`: local-cache seed v1 exists but is superseded by `101221`.
- `101138`: provider status exit `{reviewed_roots[1]['provider_status_exit']}`; market-data harness exit `{reviewed_roots[1]['harness_exit']}`; Kraken exit `{reviewed_roots[1]['kraken_exit']}`; Bybit exit `{reviewed_roots[1]['bybit_exit']}`. Kraken CSV rows including header `{reviewed_roots[1]['kraken_csv_rows_including_header']}`; Bybit CSV rows including header `{reviewed_roots[1]['bybit_csv_rows_including_header']}`.
- `101221`: Auto-Quant status after seeding is `{reviewed_roots[2]['auto_quant_status']}`, healthy `{reviewed_roots[2]['healthy']}`, data_ready `{reviewed_roots[2]['data_ready']}`, next blocker `{reviewed_roots[2]['next_blocker']}`.
- `101256`: provider Yahoo/NQ preseed wrote `NQ_USD` 1h/4h/1d feathers and the absolute-path TOMAC run exited `{reviewed_roots[3]['run_abs_exit']}` with trade_count `{reviewed_roots[3]['trade_count']}`, total_profit `{reviewed_roots[3]['total_profit_pct']}`, profit_factor `{reviewed_roots[3]['profit_factor']}`.

Harness detail:
"""
    for item in harness_results:
        report += f"- `{item['role']}` via `{item['provider']}`: ok={item['ok']}, error={item['error']}.\n"
    report += f"""
## Decision

Gate: `{payload['gate_result']}`.

Provider acquisition and Auto-Quant data readiness improved, but no accepted regime packet, no source/control unlock, no explicit selected-history approval, no canonical merge, no selected-data AutoQuant promotion, no downstream promotion, and no trade claim were produced.

Accepted rows added `0`; source/control evidence acquired false; explicit user-selected history false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion false; strict full objective false; trade usable false; promotion allowed false; `update_goal=false`.

## Next

Do not repeat these provider/preseed shapes. Continue only after a changed source/control surface, an explicit `HTF`/`MTF`/`LTF` selected-history choice, or a non-overlapping branch improvement.
"""
    (OUT / "post_101256_provider_aq_intake_v1.md").write_text(report, encoding="utf-8")

    assertions = {
        "all_roots_present": all(item["exists"] for item in reviewed_roots),
        "kraken_fetch_exit_0": reviewed_roots[1]["kraken_exit"] == "0",
        "bybit_fetch_exit_0": reviewed_roots[1]["bybit_exit"] == "0",
        "auto_quant_seed_exit_0": reviewed_roots[2]["seed_exit"] == "0",
        "auto_quant_data_ready_true": reviewed_roots[2]["data_ready"] is True,
        "provider_nq_feathers_present": reviewed_roots[3]["provider_feathers_present"] is True,
        "provider_nq_run_exit_0": reviewed_roots[3]["run_abs_exit"] == "0",
        "provider_nq_trade_count_zero": reviewed_roots[3]["trade_count"] == "0",
        "promotion_allowed_false": gates["promotion_allowed"] is False,
        "update_goal_false": gates["update_goal"] is False,
    }
    write_json(CHECKS / "post_101256_provider_aq_intake_v1_assertions.json", assertions)
    (CHECKS / "post_101256_provider_aq_intake_v1_assertions.out").write_text(
        "\n".join(f"{key}={value}" for key, value in sorted(assertions.items())) + "\n",
        encoding="utf-8",
    )
    return 0 if all(assertions.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
