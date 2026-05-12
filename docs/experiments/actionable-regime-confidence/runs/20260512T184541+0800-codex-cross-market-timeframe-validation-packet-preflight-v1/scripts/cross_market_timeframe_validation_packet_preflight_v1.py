#!/usr/bin/env python3
"""Build a fail-closed Board A validation-packet preflight from existing artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "cross-market-timeframe-validation-packet-preflight-v1"
CHECK_DIR = RUN_ROOT / "checks"
SOURCE_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1"
SOURCE_PACKET = SOURCE_ROOT / "feasible-window-same-root-aq-packet-v1/feasible_window_same_root_aq_packet_v1.json"
STATE_ROOT = SOURCE_ROOT / "state_downstream_v1/BOARD_A_BTC_172142"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def csv_row_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return sum(1 for _ in reader)


def jsonl_row_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def provider_rows(packet: dict) -> list[dict]:
    rows = []
    provider_copy_rows = packet.get("provider_copy_rows") or {}
    for key, info in sorted(provider_copy_rows.items()):
        rows.append(
            {
                "provider_key": key,
                "provider_label": info.get("provider_label", ""),
                "symbol": info.get("symbol", ""),
                "timeframe": "1h",
                "rows": int(info.get("rows") or 0),
                "first": info.get("first", ""),
                "last": info.get("last", ""),
                "copied": bool(info.get("copied")),
                "provider_requested": True,
                "provider_data_acquired": bool(info.get("copied")) and int(info.get("rows") or 0) > 0,
                "independent_downstream_validation": False,
                "notes": "provider/AQ provenance only; not an independent downstream market/timeframe acceptance row",
            }
        )
    return rows


def inspect_source_state() -> dict:
    summary = load_json(STATE_ROOT / "policy_training/structural_path_ranking_target_summary.json")
    execution_candidate = load_json(STATE_ROOT / "execution_candidate.json")
    workflow = load_json(STATE_ROOT / "workflow_snapshot.json")
    history_csv = STATE_ROOT / "policy_training/structural_path_ranking_target_history.csv"
    current_csv = STATE_ROOT / "policy_training/structural_path_ranking_target.csv"
    real_trades = SOURCE_ROOT / "derived/downstream-v1/real_trades_172142_same_root.jsonl"
    cleaned = sorted(str(path.relative_to(REPO)) for path in (SOURCE_ROOT / "data").glob("**/*") if path.is_file())
    return {
        "summary": summary,
        "execution_candidate": execution_candidate,
        "workflow_snapshot_keys": sorted(workflow.keys()),
        "current_target_rows_by_file": csv_row_count(current_csv),
        "history_rows_by_file": csv_row_count(history_csv),
        "real_trade_rows_by_file": jsonl_row_count(real_trades),
        "cleaned_data_files": cleaned,
        "cleaned_data_file_count": len(cleaned),
    }


def existing_candidate_packets() -> list[dict]:
    roots = [
        "20260512T124245+0800-codex-local-nonbtc-mtf-chain-probe-v1",
        "20260512T112650+0800-codex-104703-history-catboost-path-ranker-v1",
        "20260510T224014-codex-cross-timeframe-regime-validation",
        "20260512T121106+0800-codex-115700-same-root-six-provider-aq-chain-v1",
        "20260512T120746+0800-codex-115500-same-root-six-provider-aq-chain-v1",
    ]
    rows = []
    for root_name in roots:
        root = REPO / "docs/experiments/actionable-regime-confidence/runs" / root_name
        rows.append(
            {
                "run_root": str(root.relative_to(REPO)),
                "exists": root.exists(),
                "has_path_ranker": (root / "path-ranker").exists(),
                "has_checks": (root / "checks").exists(),
                "support_counted": False,
                "reason": "inventory only; not a fresh full Board A downstream validation packet for the current claim",
            }
        )
    return rows


def gate_rows(packet: dict, source: dict, providers: list[dict]) -> list[dict]:
    summary = source["summary"]
    cleaned_count = source["cleaned_data_file_count"]
    unique_timeframes = {"1h"} if cleaned_count else set()
    unique_markets = {row["provider_label"] for row in providers if row["provider_data_acquired"]}
    real_trade_rows = source["real_trade_rows_by_file"]
    gates = [
        ("six_provider_aq_surface", bool(packet.get("same_root_six_provider_aq_authority")), "provider/AQ surface present"),
        ("aq_trade_rows_present", real_trade_rows >= 30, f"real_trade_rows={real_trade_rows}"),
        ("independent_cross_market_downstream", False, f"provider_markets={len(unique_markets)} but downstream validation rows=0"),
        ("independent_cross_timeframe_downstream", False, f"cleaned_timeframes={','.join(sorted(unique_timeframes)) or 'none'}"),
        ("raw_scored_mature_min30", int(summary.get("history_mature_rows") or 0) >= 30 and int(summary.get("history_rows_with_raw_path_score") or 0) >= 30, f"history_mature_rows={summary.get('history_mature_rows', 0)} history_raw_score_rows={summary.get('history_rows_with_raw_path_score', 0)}"),
        ("production_validation_min30", int(summary.get("mature_rows") or 0) >= 30, f"mature_rows={summary.get('mature_rows', 0)}"),
        ("observation_validation_min30", real_trade_rows >= 30, f"observation trade rows from AQ feedback={real_trade_rows}; still not production validation"),
        ("per_regime_calibrated_95", False, "no artifact proves every visible regime calibrated >=0.95"),
        ("catboost_path_ranker_ready", int(summary.get("history_mature_rows") or 0) >= 30 and int(summary.get("history_rows_with_calibrated_path_prob") or 0) >= 30, f"calibrated_rows={summary.get('history_rows_with_calibrated_path_prob', 0)}"),
        ("execution_tree_non_observe", False, "latest execution candidate remains non-promoting/no-trade in source packet"),
    ]
    return [
        {
            "gate": name,
            "passed": bool(passed),
            "status": "pass" if passed else "fail_closed",
            "evidence": evidence,
        }
        for name, passed, evidence in gates
    ]


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    packet = load_json(SOURCE_PACKET)
    providers = provider_rows(packet)
    source = inspect_source_state()
    candidates = existing_candidate_packets()
    gates = gate_rows(packet, source, providers)
    promotion_allowed = all(row["passed"] for row in gates)

    payload = {
        "schema_version": "board-a-cross-market-timeframe-validation-packet-preflight-v1",
        "source_packet": str(SOURCE_PACKET.relative_to(REPO)),
        "run_root": str(RUN_ROOT.relative_to(REPO)),
        "promotion_allowed": promotion_allowed,
        "trade_usable": promotion_allowed,
        "accepted_95_contexts_added": 0,
        "provider_rows": providers,
        "source_state": source,
        "existing_candidate_packets_inventory": candidates,
        "gates": gates,
        "next_required_action": "Open a new isolated full-chain validation run only after independent cross-market/timeframe inputs can produce >=30 mature production-validation rows and per-regime calibrated >=95% evidence.",
    }
    (OUT_DIR / "cross_market_timeframe_validation_packet_preflight_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(OUT_DIR / "provider_validation_inventory_v1.csv", providers)
    write_csv(OUT_DIR / "gate_matrix_v1.csv", gates)
    write_csv(OUT_DIR / "existing_candidate_packets_inventory_v1.csv", candidates)

    assertions = []
    for row in gates:
        prefix = "PASS" if row["passed"] else "FAIL_CLOSED"
        assertions.append(f"{prefix} {row['gate']} {row['evidence']}")
    assertions.extend(
        [
            f"PASS accepted_95_contexts_added={payload['accepted_95_contexts_added']}",
            f"PASS promotion_allowed={str(payload['promotion_allowed']).lower()}",
            f"PASS trade_usable={str(payload['trade_usable']).lower()}",
        ]
    )
    (CHECK_DIR / "cross_market_timeframe_validation_packet_preflight_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )

    md = [
        "# Cross-Market Timeframe Validation Packet Preflight v1",
        "",
        f"- Source packet: `{payload['source_packet']}`",
        f"- Provider rows inventoried: `{len(providers)}`",
        f"- Real AQ feedback rows: `{source['real_trade_rows_by_file']}`",
        f"- Cleaned downstream data files: `{source['cleaned_data_file_count']}`",
        f"- Promotion allowed: `{str(promotion_allowed).lower()}`",
        f"- Trade usable: `{str(promotion_allowed).lower()}`",
        "- Gate decision: `fail_closed`",
        "",
        "## Gate Matrix",
        "",
        "| Gate | Status | Evidence |",
        "|---|---|---|",
    ]
    for row in gates:
        md.append(f"| `{row['gate']}` | `{row['status']}` | {row['evidence']} |")
    md.extend(
        [
            "",
            "## Readback",
            "",
            "The six-provider AQ surface and real AQ trade feedback are present, but this preflight does not find independent downstream cross-market/timeframe validation rows, mature production-validation rows, or per-regime calibrated `>=95%` acceptance evidence.",
            "",
            "Existing related packets are recorded as inventory only and are not counted as support for this claim because they are not a fresh full Board A downstream validation packet under the current acceptance contract.",
            "",
            "## Next",
            "",
            payload["next_required_action"],
            "",
            "Do not promote Board A from this preflight.",
        ]
    )
    (OUT_DIR / "cross_market_timeframe_validation_packet_preflight_v1.md").write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"promotion_allowed": promotion_allowed, "gates": gates}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
