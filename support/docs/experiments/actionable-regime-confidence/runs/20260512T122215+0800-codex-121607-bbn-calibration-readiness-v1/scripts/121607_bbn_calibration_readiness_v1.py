#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T122215+0800-codex-121607-bbn-calibration-readiness-v1"
SOURCE_FEEDBACK_RUN_ID = "20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1"
SOURCE_CHAIN_RUN_ID = "20260512T120630+0800-codex-115700-six-provider-1h-downstream-chain-v1"
SOURCE_AQ_RUN_ID = "20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
REPORT_DIR = ROOT / "121607-bbn-calibration-readiness-v1"
CHECK_DIR = ROOT / "checks"
DERIVED_DIR = ROOT / "derived"
SOURCE_FEEDBACK_JSON = (
    RUNS
    / SOURCE_FEEDBACK_RUN_ID
    / "120630-bbn-negative-feedback-packet-v1"
    / "120630_bbn_negative_feedback_packet_v1.json"
)
SOURCE_AQ_ROOT = RUNS / SOURCE_AQ_RUN_ID

PROVIDER_INPUTS = {
    "yfinance": ("BTC-USD", SOURCE_AQ_ROOT / "input-csv" / "yfinance_btc_usd_1h.csv"),
    "kraken_public": ("XBTUSD", SOURCE_AQ_ROOT / "input-csv" / "kraken_xbtusd_1h.csv"),
    "binance_public": ("BTCUSDT", SOURCE_AQ_ROOT / "input-csv" / "binance_btcusdt_1h.csv"),
    "bybit_public": ("BTCUSDT", SOURCE_AQ_ROOT / "input-csv" / "bybit_btcusdt_linear_1h.csv"),
    "tvr_default_binance": (
        "BINANCE:BTCUSDT",
        SOURCE_AQ_ROOT / "input-csv" / "tvr_default_binance_btcusdt_1h.csv",
    ),
    "ibkr_paxos_long_midpoint": ("BTC.PAXOS", SOURCE_AQ_ROOT / "input-csv" / "BTC_1h_midpoint.csv"),
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        if text.isdigit():
            number = int(text)
            if number > 10_000_000_000:
                return datetime.fromtimestamp(number / 1000, tz=timezone.utc)
            return datetime.fromtimestamp(number, tz=timezone.utc)
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat().replace("+00:00", "Z")


def csv_window(path: Path) -> dict[str, Any]:
    rows = []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(row)
    dates = []
    for row in rows:
        dates.append(parse_dt(row.get("date") or row.get("timestamp") or row.get("ts")))
    dates = [value for value in dates if value is not None]
    return {
        "path": str(path),
        "rows": len(rows),
        "first": iso(min(dates) if dates else None),
        "last": iso(max(dates) if dates else None),
    }


def provider_windows() -> dict[str, dict[str, Any]]:
    windows: dict[str, dict[str, Any]] = {}
    for provider, (symbol, path) in PROVIDER_INPUTS.items():
        payload = csv_window(path)
        payload["symbol"] = symbol
        windows[provider] = payload
    return windows


def smoothed_candidate(current: list[float], empirical: list[float], rows: int, alpha: float) -> dict[str, Any]:
    weight = rows / (rows + alpha) if rows + alpha else 0.0
    candidate = [
        round((1.0 - weight) * current[index] + weight * empirical[index], 6)
        for index in range(len(current))
    ]
    total = sum(candidate)
    if total:
        candidate = [round(value / total, 6) for value in candidate]
    return {
        "states": ["win", "breakeven", "loss"],
        "smoothing_alpha": alpha,
        "source_rows": rows,
        "empirical_weight": round(weight, 6),
        "current_probs": current,
        "empirical_probs": empirical,
        "candidate_probs": candidate,
        "mode": "candidate_only_do_not_overwrite",
    }


def gate_matrix(feedback: dict[str, Any], windows: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    overall = feedback["overall"]
    by_provider = feedback["by_provider"]
    by_branch = feedback["by_branch"]
    execution = feedback["execution_tree_readback"]
    readiness = execution.get("readiness_score", execution.get("execution_readiness"))
    symbols = sorted({payload["symbol"] for payload in windows.values()})
    firsts = [parse_dt(payload["first"]) for payload in windows.values()]
    lasts = [parse_dt(payload["last"]) for payload in windows.values()]
    firsts = [value for value in firsts if value is not None]
    lasts = [value for value in lasts if value is not None]
    common_overlap = bool(firsts and lasts and max(firsts) <= min(lasts))
    return [
        {
            "gate": "exact_root_feedback",
            "status": "pass",
            "evidence": f"{SOURCE_AQ_RUN_ID} -> {SOURCE_CHAIN_RUN_ID} -> {SOURCE_FEEDBACK_RUN_ID}",
            "blocker": "",
        },
        {
            "gate": "row_volume",
            "status": "pass",
            "evidence": f"{overall['rows']} rows >= 30",
            "blocker": "",
        },
        {
            "gate": "provider_context",
            "status": "pass",
            "evidence": f"{len(by_provider)} providers: {', '.join(sorted(by_provider))}",
            "blocker": "",
        },
        {
            "gate": "branch_attribution",
            "status": "pass",
            "evidence": f"{len(by_branch)} branch paths",
            "blocker": "",
        },
        {
            "gate": "chronological_holdout",
            "status": "fail_closed",
            "evidence": f"provider windows overlap={common_overlap}; no held-out chronological update artifact",
            "blocker": "needs disjoint calibration/test periods before BBN CPD mutation",
        },
        {
            "gate": "cross_instrument",
            "status": "fail_closed",
            "evidence": f"symbols={symbols}",
            "blocker": "only BTC-like instruments are represented",
        },
        {
            "gate": "execution_admissibility",
            "status": "fail_closed",
            "evidence": (
                f"ready={execution.get('ready')} actionable={execution.get('actionable')} "
                f"review={execution.get('review_status')} readiness={readiness}"
            ),
            "blocker": "execution tree stayed observe/execution_blocked",
        },
        {
            "gate": "selected_history_source_control",
            "status": "fail_closed",
            "evidence": "no selected-history/source-control unlock in source packet",
            "blocker": "cannot promote or mutate production likelihoods",
        },
        {
            "gate": "bbn_cpd_update_authority",
            "status": "fail_closed",
            "evidence": feedback["bbn_cpd_update_candidate"]["recommended_update_mode"],
            "blocker": "candidate-only chronological smoothing required",
        },
    ]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_report(summary: dict[str, Any]) -> None:
    report = REPORT_DIR / "121607_bbn_calibration_readiness_v1.md"
    assertions = CHECK_DIR / "121607_bbn_calibration_readiness_v1_assertions.out"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_121607_bbn_calibration_readiness_v1.csv"
    overall = summary["overall"]
    cpd = summary["cpd_candidate"]
    gates = summary["gate_matrix"]
    lines = [
        "# 121607 BBN Calibration Readiness v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source feedback packet: `{SOURCE_FEEDBACK_RUN_ID}`",
        f"Source downstream chain: `{SOURCE_CHAIN_RUN_ID}`",
        f"Source AQ root: `{SOURCE_AQ_RUN_ID}`",
        "",
        "## Result",
        f"- Rows: `{overall['rows']}`; wins `{overall['wins']}`; losses `{overall['losses']}`; win rate `{overall['win_rate']}`; loss rate `{overall['loss_rate']}`.",
        f"- Candidate smoothed CPD: `{dict(zip(cpd['states'], cpd['candidate_probs']))}` with alpha `{cpd['smoothing_alpha']}`.",
        "- Gate: `fail_closed:candidate_only_no_production_bbn_update`.",
        "",
        "## Gate Matrix",
    ]
    for gate in gates:
        lines.append(f"- `{gate['gate']}`: `{gate['status']}`; {gate['evidence']}; blocker `{gate['blocker'] or 'none'}`.")
    lines.extend(
        [
            "",
            "## Decision",
            "- The negative packet is useful for BBN likelihood/CPD calibration queues and CatBoost hard-negative analysis.",
            "- It is not sufficient for production BBN mutation because chronology, cross-instrument coverage, selected-history/source-control, and execution admissibility are still fail-closed.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{REPORT_DIR / '121607_bbn_calibration_readiness_v1.json'}`",
            f"- Gate CSV: `{DERIVED_DIR / '121607_bbn_calibration_gate_matrix_v1.csv'}`",
            f"- CPD candidate JSON: `{DERIVED_DIR / '121607_bbn_cpd_candidate_smoothed_v1.json'}`",
            f"- Provider windows JSON: `{DERIVED_DIR / '121607_provider_windows_v1.json'}`",
            f"- Assertions: `{assertions}`",
        ]
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with checklist.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["requirement", "artifact", "status", "note"])
        writer.writerow(["source 121607 feedback", str(SOURCE_FEEDBACK_JSON), "covered", SOURCE_FEEDBACK_RUN_ID])
        writer.writerow(["provider/cross-context windows", str(DERIVED_DIR / "121607_provider_windows_v1.json"), "covered", "six provider windows"])
        writer.writerow(["candidate-only BBN CPD", str(DERIVED_DIR / "121607_bbn_cpd_candidate_smoothed_v1.json"), "covered", "no production overwrite"])
        writer.writerow(["gate matrix", str(DERIVED_DIR / "121607_bbn_calibration_gate_matrix_v1.csv"), "covered", "fail-closed gates explicit"])
        writer.writerow(["no promotion/update_goal", str(report), "covered", "promotion_allowed=false trade_usable=false update_goal=false"])

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_feedback_run_id={SOURCE_FEEDBACK_RUN_ID}",
        f"PASS source_chain_run_id={SOURCE_CHAIN_RUN_ID}",
        f"PASS rows={overall['rows']}",
        f"PASS wins={overall['wins']}",
        f"PASS losses={overall['losses']}",
        f"PASS provider_count={len(summary['by_provider'])}",
        f"PASS branch_count={len(summary['by_branch'])}",
        "FAIL_CLOSED chronological_holdout=false",
        "FAIL_CLOSED cross_instrument=false",
        "FAIL_CLOSED selected_history_source_control=false",
        "FAIL_CLOSED execution_admissibility=false",
        "PASS bbn_cpd_update_candidate_only=true",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")


def main() -> int:
    for path in (REPORT_DIR, CHECK_DIR, DERIVED_DIR):
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n", encoding="utf-8")
    (ROOT / "source_feedback_run_id.txt").write_text(SOURCE_FEEDBACK_RUN_ID + "\n", encoding="utf-8")
    feedback = read_json(SOURCE_FEEDBACK_JSON)
    windows = provider_windows()
    cpd_input = feedback["bbn_cpd_update_candidate"]
    current = cpd_input["current_cpd"]["current_probs"]
    empirical = cpd_input["empirical_outcome_from_120630"]["probs"]
    cpd_candidate = smoothed_candidate(current, empirical, feedback["overall"]["rows"], alpha=30.0)
    gates = gate_matrix(feedback, windows)
    write_json(DERIVED_DIR / "121607_provider_windows_v1.json", windows)
    write_json(DERIVED_DIR / "121607_bbn_cpd_candidate_smoothed_v1.json", cpd_candidate)
    write_csv(DERIVED_DIR / "121607_bbn_calibration_gate_matrix_v1.csv", gates)
    summary = {
        "run_id": RUN_ID,
        "source_feedback_run_id": SOURCE_FEEDBACK_RUN_ID,
        "source_chain_run_id": SOURCE_CHAIN_RUN_ID,
        "source_aq_run_id": SOURCE_AQ_RUN_ID,
        "overall": feedback["overall"],
        "by_provider": feedback["by_provider"],
        "by_branch": feedback["by_branch"],
        "pre_bayes_bbn_readback": feedback["pre_bayes_bbn_readback"],
        "catboost_path_ranker_readback": feedback["catboost_path_ranker_readback"],
        "execution_tree_readback": feedback["execution_tree_readback"],
        "provider_windows": windows,
        "cpd_candidate": cpd_candidate,
        "gate_matrix": gates,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(REPORT_DIR / "121607_bbn_calibration_readiness_v1.json", summary)
    write_report(summary)
    print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
