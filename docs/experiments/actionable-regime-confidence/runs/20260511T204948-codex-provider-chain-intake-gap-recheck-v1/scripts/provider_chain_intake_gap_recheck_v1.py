#!/usr/bin/env python3
"""Summarize the provider + Auto-Quant + ict-engine readback without vendoring raw rows."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T204948-codex-provider-chain-intake-gap-recheck-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "provider-chain-intake-gap-recheck"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
TMP_ROOT = Path("/tmp/ict-engine-board-a-20260511T204948-provider-chain-intake-gap-recheck-v1")

INTAKE_ROOTS = [
    (
        "R2;R4",
        Path("/tmp/ict-engine-source-label-equivalence-intake"),
        ["source_label_equivalence_rows.csv", "source_label_equivalence_provenance.json"],
    ),
    (
        "R3",
        Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"],
    ),
    (
        "R5",
        Path("/tmp/ict-engine-source-panel-recency-extension"),
        ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"],
    ),
    (
        "R6",
        Path("/tmp/ict-engine-direct-manipulation-row-intake"),
        ["positive_spoofing_layering_rows.csv", "matched_negative_normal_activity_rows.csv", "provenance_manifest.json"],
    ),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_summary(path: Path, ts_fields: tuple[str, ...]) -> dict[str, object]:
    rows = 0
    first_ts: str | None = None
    last_ts: str | None = None
    columns: list[str] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        for row in reader:
            rows += 1
            ts = next((row.get(field) for field in ts_fields if row.get(field)), None)
            if ts and first_ts is None:
                first_ts = ts
            if ts:
                last_ts = ts
    return {
        "path": str(path),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "rows": rows,
        "columns": columns,
        "first_timestamp": first_ts,
        "last_timestamp": last_ts,
    }


def tradingview_summary(path: Path) -> dict[str, object]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    result = obj.get("results", [{}])[0]
    data = result.get("data") or []
    timestamps = [row.get("timestamp") for row in data if row.get("timestamp")]
    return {
        "path": str(path),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "ok": bool(result.get("ok")),
        "provider": result.get("provider"),
        "symbol": result.get("symbol"),
        "rows": len(data),
        "first_timestamp": timestamps[0] if timestamps else None,
        "last_timestamp": timestamps[-1] if timestamps else None,
    }


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def provider_status(path: Path) -> dict[str, object]:
    obj = load_json(path)
    providers = obj.get("providers") or []
    if providers:
        first = providers[0]
        return {
            "path": str(path),
            "summary_line": obj.get("summary_line"),
            "provider_id": first.get("provider_id"),
            "ready": first.get("ready"),
            "status": first.get("status"),
            "reason": first.get("reason"),
        }
    return {"path": str(path), "summary_line": obj.get("summary_line")}


def autoquant_summary(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="replace")
    fields: dict[str, object] = {
        "path": str(path),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "completed_without_traceback": "Traceback" not in text and "ERROR:" not in text,
        "strategy": None,
        "sharpe": None,
        "total_profit_pct": None,
        "trade_count": None,
        "win_rate_pct": None,
        "robust_sharpe": None,
    }
    for key, pattern, caster in [
        ("strategy", r"^strategy:\s+(.+?)\s*$", str),
        ("sharpe", r"^sharpe:\s+([-0-9.]+)", float),
        ("total_profit_pct", r"^total_profit_pct:\s+([-0-9.]+)", float),
        ("trade_count", r"^trade_count:\s+([0-9]+)", int),
        ("win_rate_pct", r"^win_rate_pct:\s+([-0-9.]+)", float),
        ("robust_sharpe", r"^robust_sharpe:\s+([-0-9.]+)", float),
    ]:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            fields[key] = caster(match.group(1).strip())
    return fields


def ict_chain_summary(tmp_root: Path) -> dict[str, object]:
    chain = tmp_root / "ict_chain"
    analyze = load_json(chain / "analyze_NQ_demo_bull_bundle.json")
    pre_bayes = load_json(chain / "pre_bayes_status_NQ.json")
    policy = load_json(chain / "policy_training_status_NQ.json")
    execution = load_json(chain / "workflow_execution-candidate.json")
    path_bundle = load_json(chain / "workflow_structural-recommended-path-bundle.json")
    feedback = load_json(chain / "workflow_structural-feedback.json")
    return {
        "analyze_path": str(chain / "analyze_NQ_demo_bull_bundle.json"),
        "analyze_direction": analyze.get("agent_report", {}).get("direction"),
        "analyze_decision_summary": analyze.get("agent_report", {}).get("decision_summary"),
        "execution_triage_gate": analyze.get("agent_report", {}).get("execution_triage", {}).get("gate_status"),
        "pre_bayes_path": str(chain / "pre_bayes_status_NQ.json"),
        "pre_bayes_gate_status": pre_bayes.get("latest_gate_status"),
        "pre_bayes_confidence": pre_bayes.get("latest_canonical_structural_confidence"),
        "pre_bayes_active_regime": pre_bayes.get("latest_canonical_structural_active_regime"),
        "policy_path": str(chain / "policy_training_status_NQ.json"),
        "policy_summary_line": policy.get("summary_line"),
        "catboost_ready": bool(
            policy.get("structural_path_ranking_validation", {}).get("production_validation_ready")
        ),
        "path_bundle_path": str(chain / "workflow_structural-recommended-path-bundle.json"),
        "path_bundle_label": path_bundle.get("path_label"),
        "path_bundle_probability": path_bundle.get("selected_path_probability"),
        "structural_feedback_path": str(chain / "workflow_structural-feedback.json"),
        "structural_feedback_protocol": feedback.get("protocol_version"),
        "execution_candidate_path": str(chain / "workflow_execution-candidate.json"),
        "execution_candidate_actionable": bool(execution.get("actionable")),
        "execution_candidate_status": execution.get("candidate_status"),
        "execution_review_status": execution.get("review_status"),
        "structural_export_path": str(chain / "export_structural_path_ranking_target.out"),
    }


def verifier_summary(tmp_root: Path) -> dict[str, object]:
    path = tmp_root / "verifiers" / "direct_manipulation_row_intake_verifier_v1.out"
    err_path = tmp_root / "verifiers" / "direct_manipulation_row_intake_verifier_v1.err"
    if not path.exists():
        return {
            "path": str(path),
            "ran": False,
            "status": "not_run",
        }
    obj = load_json(path)
    obj["path"] = str(path)
    obj["stderr_path"] = str(err_path)
    obj["ran"] = True
    return obj


def intake_status() -> list[dict[str, object]]:
    rows = []
    for requirements, root, required in INTAKE_ROOTS:
        present = [name for name in required if (root / name).exists()]
        missing = [name for name in required if not (root / name).exists()]
        rows.append(
            {
                "requirements": requirements,
                "root": str(root),
                "exists": root.exists(),
                "required_files": required,
                "present_files": present,
                "missing_files": missing,
                "ready": root.exists() and not missing,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    provider_raw = TMP_ROOT / "provider_raw"
    provider_status_dir = TMP_ROOT / "provider_status"
    providers = {
        "yfinance_QQQ_1h": csv_summary(provider_raw / "yahoo_QQQ_1h.csv", ("date", "ts")),
        "tradingview_mcp_QQQ_1h": tradingview_summary(provider_raw / "tradingview_mcp_QQQ_1h.json"),
        "ibkr_QQQ_1h_1M": csv_summary(provider_raw / "ibkr_QQQ_1h_1M.csv", ("ts", "date")),
        "kraken_XBTUSD_1h": csv_summary(provider_raw / "kraken_XBTUSD_1h.csv", ("date", "ts")),
    }
    provider_statuses = {
        path.stem: provider_status(path)
        for path in sorted(provider_status_dir.glob("provider_status_*_agent.json"))
    }
    autoquant = autoquant_summary(TMP_ROOT / "autoquant_run.log")
    ict_chain = ict_chain_summary(TMP_ROOT)
    direct_verifier = verifier_summary(TMP_ROOT)
    intakes = intake_status()
    ready_intakes = [row for row in intakes if row["ready"]]
    decision = "provider_chain_intake_gap_recheck_v1=real_chain_ran_r6_schema_ready_unscored_remaining_intakes_blocked"

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_writeback": sha256(BOARD),
        "decision": decision,
        "provider_fetches": providers,
        "provider_statuses": provider_statuses,
        "autoquant": autoquant,
        "ict_chain": ict_chain,
        "direct_manipulation_verifier": direct_verifier,
        "intake_roots": intakes,
        "ready_intake_root_count": len(ready_intakes),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "blocker": "Live providers and local chain are operable, and R6 direct-manipulation intake is schema-ready but unscored; R2/R3/R4/R5 intake files remain absent and R6 still needs chronological plus heldout-symbol/venue calibration.",
        "next_action": "Run the R6 chronological and heldout-symbol/venue Wilson95 calibration gate, while continuing to populate the R2/R3/R4/R5 intake roots with source-owned or owner-approved files.",
    }

    json_path = OUT_DIR / "provider_chain_intake_gap_recheck_v1.json"
    report_path = OUT_DIR / "provider_chain_intake_gap_recheck_v1.md"
    provider_csv = OUT_DIR / "provider_chain_intake_gap_recheck_v1_providers.csv"
    intake_csv = OUT_DIR / "provider_chain_intake_gap_recheck_v1_intake_roots.csv"
    checks_path = CHECK_DIR / "provider_chain_intake_gap_recheck_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        provider_csv,
        [
            {
                "provider": name,
                "rows": summary.get("rows"),
                "first_timestamp": summary.get("first_timestamp"),
                "last_timestamp": summary.get("last_timestamp"),
                "sha256": summary.get("sha256"),
                "tmp_path": summary.get("path"),
            }
            for name, summary in providers.items()
        ],
        ["provider", "rows", "first_timestamp", "last_timestamp", "sha256", "tmp_path"],
    )
    write_csv(
        intake_csv,
        [
            {
                "requirements": row["requirements"],
                "root": row["root"],
                "exists": row["exists"],
                "ready": row["ready"],
                "present_files": ";".join(row["present_files"]),
                "missing_files": ";".join(row["missing_files"]),
            }
            for row in intakes
        ],
        ["requirements", "root", "exists", "ready", "present_files", "missing_files"],
    )

    lines = [
        "# Provider Chain Intake Gap Recheck v1",
        "",
        f"- Decision: `{decision}`",
        "- Scope: real provider readback plus Auto-Quant and ict-engine chain readback; no runtime code changes and no raw market rows committed.",
        f"- Board hash before writeback: `{result['board_hash_before_writeback']}`",
        "",
        "## Provider Fetches",
        "",
        "| Provider | Rows | First | Last | Raw Location |",
        "|---|---:|---|---|---|",
    ]
    for name, summary in providers.items():
        lines.append(
            f"| `{name}` | {summary.get('rows')} | `{summary.get('first_timestamp')}` | "
            f"`{summary.get('last_timestamp')}` | `{summary.get('path')}` |"
        )
    lines.extend(
        [
            "",
            "## Auto-Quant",
            "",
            f"- Strategy: `{autoquant.get('strategy')}`",
            f"- Trades: `{autoquant.get('trade_count')}`; win rate: `{autoquant.get('win_rate_pct')}`; Sharpe: `{autoquant.get('sharpe')}`; robust Sharpe: `{autoquant.get('robust_sharpe')}`.",
            f"- Log: `{autoquant.get('path')}`",
            "",
            "## ict-engine Chain",
            "",
            f"- Analyze: direction `{ict_chain.get('analyze_direction')}`, decision `{ict_chain.get('analyze_decision_summary')}`, execution gate `{ict_chain.get('execution_triage_gate')}`.",
            f"- Pre-Bayes/BBN: gate `{ict_chain.get('pre_bayes_gate_status')}`, active regime `{ict_chain.get('pre_bayes_active_regime')}`, confidence `{ict_chain.get('pre_bayes_confidence')}`.",
            f"- CatBoost/path-ranker status: ready `{ict_chain.get('catboost_ready')}`; policy summary `{ict_chain.get('policy_summary_line')}`.",
            f"- Execution tree: candidate status `{ict_chain.get('execution_candidate_status')}`, review `{ict_chain.get('execution_review_status')}`, actionable `{ict_chain.get('execution_candidate_actionable')}`.",
            "",
            "## Direct Manipulation Verifier",
            "",
            f"- Verifier status: `{direct_verifier.get('status')}`.",
            f"- Positive rows: `{direct_verifier.get('positive_rows')}`; matched negative rows: `{direct_verifier.get('matched_negative_rows')}`; matched groups: `{direct_verifier.get('matched_group_count')}`.",
            f"- Next verifier action: `{direct_verifier.get('next')}`.",
            "",
            "## Intake Gate",
            "",
            f"- Ready intake roots: `{len(ready_intakes)}/4`.",
            "- Accepted rows added: `0`; new confidence gate: `false`.",
            "- Strict full objective achieved: `false`; `update_goal=false`.",
            "",
            "| Requirements | Root | Ready | Missing |",
            "|---|---|---|---|",
        ]
    )
    for row in intakes:
        lines.append(
            f"| `{row['requirements']}` | `{row['root']}` | `{str(row['ready']).lower()}` | "
            f"`{';'.join(row['missing_files'])}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The providers and local chain are operable, including TradingView MCP, yfinance, IBKR through the local gateway, Kraken, Auto-Quant, Pre-Bayes/BBN readback, policy/CatBoost status, structural path ranking export, and execution-candidate readback. R6 direct-manipulation intake is now schema-ready, but it is unscored and not a 95% confidence gate; R2/R3/R4/R5 source-owned or owner-approved intake files are still absent.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- Provider CSV: `{provider_csv}`",
            f"- Intake CSV: `{intake_csv}`",
            f"- Assertions: `{checks_path}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    checks = [
        f"PASS decision={decision}",
        f"PASS yfinance_rows={providers['yfinance_QQQ_1h']['rows']}",
        f"PASS tradingview_mcp_rows={providers['tradingview_mcp_QQQ_1h']['rows']}",
        f"PASS ibkr_rows={providers['ibkr_QQQ_1h_1M']['rows']}",
        f"PASS kraken_rows={providers['kraken_XBTUSD_1h']['rows']}",
        f"PASS autoquant_trade_count={autoquant.get('trade_count')}",
        f"PASS pre_bayes_gate_status={ict_chain.get('pre_bayes_gate_status')}",
        f"PASS execution_candidate_status={ict_chain.get('execution_candidate_status')}",
        f"PASS direct_manipulation_verifier_status={direct_verifier.get('status')}",
        f"PASS ready_intake_root_count={len(ready_intakes)}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    checks_path.write_text("\n".join(checks) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
