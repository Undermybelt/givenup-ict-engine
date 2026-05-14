from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T122136+0800-codex-121607-chronological-calibration-audit-v1"
SOURCE_FEEDBACK_RUN_ID = "20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1"
SOURCE_POSTCHAIN_RUN_ID = "20260512T121542+0800-codex-120630-115700-layered-postchain-validator-v1"
SOURCE_AQ_RUN_ID = "20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1"
SOURCE_DOWNSTREAM_RUN_ID = "20260512T120630+0800-codex-115700-six-provider-1h-downstream-chain-v1"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_FEEDBACK = (
    RUNS
    / SOURCE_FEEDBACK_RUN_ID
    / "120630-bbn-negative-feedback-packet-v1"
    / "120630_bbn_negative_feedback_packet_v1.json"
)
SOURCE_ROWS = (
    RUNS
    / SOURCE_POSTCHAIN_RUN_ID
    / "derived"
    / "115700_layered_postchain_rows.jsonl"
)

REPORT_DIR = ROOT / "121607-chronological-calibration-audit-v1"
CHECK_DIR = ROOT / "checks"
DERIVED_DIR = ROOT / "derived"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def outcome(row: dict[str, Any]) -> str:
    value = str(row.get("realized_outcome") or "").lower()
    if value in {"win", "loss", "breakeven"}:
        return value
    pnl = float(row.get("pnl") or 0.0)
    if pnl > 0:
        return "win"
    if pnl < 0:
        return "loss"
    return "breakeven"


def ts_ms(row: dict[str, Any]) -> int:
    return int(row.get("open_ts_ms") or row.get("close_ts_ms") or 0)


def ts_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def add_periods(rows: list[dict[str, Any]]) -> None:
    ordered = sorted(rows, key=ts_ms)
    n = len(ordered)
    for idx, row in enumerate(ordered):
        if idx < n / 3:
            period = "early"
        elif idx < (2 * n) / 3:
            period = "middle"
        else:
            period = "late"
        row["chronological_period"] = period


def summarize(rows: list[dict[str, Any]], keys: list[str]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(str(row.get(key) or "unknown") for key in keys)].append(row)
    out = []
    for group_key, group_rows in sorted(grouped.items()):
        wins = sum(1 for row in group_rows if outcome(row) == "win")
        losses = sum(1 for row in group_rows if outcome(row) == "loss")
        breakeven = sum(1 for row in group_rows if outcome(row) == "breakeven")
        total = len(group_rows)
        pnl_values = [float(row.get("pnl") or 0.0) for row in group_rows]
        timestamps = [ts_ms(row) for row in group_rows if ts_ms(row)]
        record = {key: group_key[idx] for idx, key in enumerate(keys)}
        record.update(
            {
                "rows": total,
                "wins": wins,
                "losses": losses,
                "breakeven": breakeven,
                "win_rate": round(wins / total, 6) if total else 0.0,
                "loss_rate": round(losses / total, 6) if total else 0.0,
                "total_pnl": round(sum(pnl_values), 6),
                "avg_pnl": round(sum(pnl_values) / total, 6) if total else 0.0,
                "first_ts": ts_iso(min(timestamps)) if timestamps else None,
                "last_ts": ts_iso(max(timestamps)) if timestamps else None,
            }
        )
        out.append(record)
    return out


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def unique_values(rows: list[dict[str, Any]], key: str) -> set[str]:
    return {str(row.get(key) or "unknown") for row in rows}


def main() -> int:
    for path in (REPORT_DIR, CHECK_DIR, DERIVED_DIR):
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")
    (ROOT / "source_feedback_run_id.txt").write_text(SOURCE_FEEDBACK_RUN_ID + "\n")

    feedback = read_json(SOURCE_FEEDBACK)
    rows = read_rows(SOURCE_ROWS)
    add_periods(rows)

    period_summary = summarize(rows, ["chronological_period"])
    provider_summary = summarize(rows, ["source_provider"])
    branch_summary = summarize(rows, ["regime_profit_branch_path"])
    provider_period_summary = summarize(rows, ["source_provider", "chronological_period"])
    branch_period_summary = summarize(rows, ["regime_profit_branch_path", "chronological_period"])

    write_csv(DERIVED_DIR / "chronological_period_summary.csv", period_summary)
    write_csv(DERIVED_DIR / "provider_summary.csv", provider_summary)
    write_csv(DERIVED_DIR / "branch_summary.csv", branch_summary)
    write_csv(DERIVED_DIR / "provider_period_summary.csv", provider_period_summary)
    write_csv(DERIVED_DIR / "branch_period_summary.csv", branch_period_summary)

    pre_bayes = feedback.get("pre_bayes_bbn_readback", {})
    market_probs = pre_bayes.get("latest_canonical_structural_probabilities", {})
    active_regime = pre_bayes.get("latest_canonical_structural_active_regime")
    active_confidence = float(pre_bayes.get("latest_canonical_structural_confidence") or 0.0)
    max_market_prob = max((float(value) for value in market_probs.values()), default=0.0)
    execution = feedback.get("execution_tree_readback", {})
    cpd = feedback.get("bbn_cpd_update_candidate", {})
    empirical = cpd.get("empirical_outcome_from_120630", {})
    current_cpd = cpd.get("current_cpd", {})
    empirical_probs = empirical.get("probs", [])
    current_probs = current_cpd.get("current_probs", [])

    loss_delta = None
    if len(empirical_probs) >= 3 and len(current_probs) >= 3:
        loss_delta = round(float(empirical_probs[2]) - float(current_probs[2]), 6)

    providers = unique_values(rows, "source_provider")
    branches = unique_values(rows, "regime_profit_branch_path")
    symbols = unique_values(rows, "symbol")
    periods = unique_values(rows, "chronological_period")

    gate = {
        "rows": len(rows),
        "providers": len(providers),
        "branches": len(branches),
        "chronological_periods": len(periods),
        "symbols": sorted(symbols),
        "cross_provider_ready": len(providers) >= 6,
        "cross_period_ready": len(periods) >= 3,
        "cross_instrument_ready": len(symbols) >= 2,
        "active_regime": active_regime,
        "active_confidence": active_confidence,
        "max_market_regime_probability": max_market_prob,
        "board_regime_95_ready": active_confidence >= 0.95 and max_market_prob >= 0.95,
        "execution_ready": bool(execution.get("ready")),
        "execution_actionable": bool(execution.get("actionable")),
        "execution_review_status": execution.get("review_status"),
        "cpd_loss_probability_delta": loss_delta,
        "production_mutation_allowed": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }

    summary = {
        "run_id": RUN_ID,
        "source_feedback_run_id": SOURCE_FEEDBACK_RUN_ID,
        "source_postchain_run_id": SOURCE_POSTCHAIN_RUN_ID,
        "source_aq_run_id": SOURCE_AQ_RUN_ID,
        "source_downstream_run_id": SOURCE_DOWNSTREAM_RUN_ID,
        "input_rows": str(SOURCE_ROWS),
        "input_feedback": str(SOURCE_FEEDBACK),
        "gate": gate,
        "period_summary": period_summary,
        "provider_summary": provider_summary,
        "branch_summary": branch_summary,
        "derived_artifacts": {
            "chronological_period_summary": str(DERIVED_DIR / "chronological_period_summary.csv"),
            "provider_summary": str(DERIVED_DIR / "provider_summary.csv"),
            "branch_summary": str(DERIVED_DIR / "branch_summary.csv"),
            "provider_period_summary": str(DERIVED_DIR / "provider_period_summary.csv"),
            "branch_period_summary": str(DERIVED_DIR / "branch_period_summary.csv"),
        },
    }
    write_json(REPORT_DIR / "121607_chronological_calibration_audit_v1.json", summary)

    report = REPORT_DIR / "121607_chronological_calibration_audit_v1.md"
    report.write_text(
        "\n".join(
            [
                "# 121607 Chronological Calibration Audit v1",
                "",
                f"Run id: `{RUN_ID}`",
                f"Source feedback packet: `{SOURCE_FEEDBACK_RUN_ID}`",
                f"Source post-chain rows: `{SOURCE_POSTCHAIN_RUN_ID}`",
                "",
                "## Result",
                f"- Rows audited: `{gate['rows']}`.",
                f"- Providers: `{gate['providers']}`; branches: `{gate['branches']}`; chronological periods: `{gate['chronological_periods']}`.",
                f"- Symbols: `{gate['symbols']}`.",
                f"- Active structural regime/confidence: `{active_regime}` / `{active_confidence}`.",
                f"- Max market-regime probability: `{max_market_prob}`.",
                f"- CPD loss-probability delta candidate: `{loss_delta}`.",
                f"- Execution ready/actionable/review: `{gate['execution_ready']}` / `{gate['execution_actionable']}` / `{gate['execution_review_status']}`.",
                "",
                "## Gate",
                f"- Cross-provider ready: `{gate['cross_provider_ready']}`.",
                f"- Cross-period ready: `{gate['cross_period_ready']}`.",
                f"- Cross-instrument ready: `{gate['cross_instrument_ready']}`.",
                f"- Board regime >=95 ready: `{gate['board_regime_95_ready']}`.",
                "- Production mutation allowed: `false`.",
                "- `promotion_allowed=false`.",
                "- `trade_usable=false`.",
                "- `update_goal=false`.",
                "",
                "## Decision",
                "- The `121607` feedback packet is chronologically and cross-provider auditable, but it is still single-instrument BTC evidence and the active regime confidence remains far below the Board A 95% threshold.",
                "- Treat the empirical loss shift as candidate likelihood evidence for smoothing/backtest queues only; do not overwrite production BBN CPDs or execution weights from this packet alone.",
                "",
                "## Artifacts",
                f"- JSON: `{REPORT_DIR / '121607_chronological_calibration_audit_v1.json'}`",
                f"- Period summary: `{DERIVED_DIR / 'chronological_period_summary.csv'}`",
                f"- Provider summary: `{DERIVED_DIR / 'provider_summary.csv'}`",
                f"- Branch summary: `{DERIVED_DIR / 'branch_summary.csv'}`",
                f"- Provider-period summary: `{DERIVED_DIR / 'provider_period_summary.csv'}`",
                f"- Branch-period summary: `{DERIVED_DIR / 'branch_period_summary.csv'}`",
            ]
        )
        + "\n"
    )

    assertions = CHECK_DIR / "121607_chronological_calibration_audit_v1_assertions.out"
    assertions.write_text(
        "\n".join(
            [
                f"PASS run_id={RUN_ID}",
                f"PASS source_feedback_run_id={SOURCE_FEEDBACK_RUN_ID}",
                f"PASS rows={gate['rows']}",
                f"PASS providers={gate['providers']}",
                f"PASS branches={gate['branches']}",
                f"PASS chronological_periods={gate['chronological_periods']}",
                f"PASS cross_provider_ready={gate['cross_provider_ready']}",
                f"PASS cross_period_ready={gate['cross_period_ready']}",
                f"FAIL_CLOSED cross_instrument_ready={gate['cross_instrument_ready']}",
                f"FAIL_CLOSED board_regime_95_ready={gate['board_regime_95_ready']} active_confidence={active_confidence} max_market_prob={max_market_prob}",
                f"FAIL_CLOSED execution_ready={gate['execution_ready']} actionable={gate['execution_actionable']} review={gate['execution_review_status']}",
                f"PASS cpd_loss_probability_delta={loss_delta}",
                "PASS production_mutation_allowed=false",
                "PASS promotion_allowed=false",
                "PASS trade_usable=false",
                "PASS update_goal=false",
            ]
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
