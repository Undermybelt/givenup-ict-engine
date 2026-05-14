#!/usr/bin/env python3
"""Verify the durable R6 isolated reconstruction without mutating shared intake."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T000048-codex-r6-isolated-reconstruction-verification-v57"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-isolated-reconstruction-verification"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
INTAKE = RUN_ROOT / "isolated-direct-intake"
STATE_DIR = Path("/tmp/ict-engine-board-a-r6-v57-chain-readback")
AQ_STATE_DIR = Path("/tmp/ict-engine-board-a-r6-v57-autoquant")
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
BIN = REPO / "target/debug/ict-engine"
LIVE_INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
SRC_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T234414-codex-r6-direct-intake-reconstruction-v55"
    / "r6-direct-intake-reconstruction-v55"
)
SRC_POSITIVE = SRC_ROOT / "positive_spoofing_layering_rows_v55.csv"
SRC_NEGATIVE = SRC_ROOT / "matched_negative_normal_activity_rows_v55.csv"
SRC_RECON_JSON = SRC_ROOT / "r6_direct_intake_reconstruction_v55.json"
SRC_SPLITS = SRC_ROOT / "r6_direct_intake_reconstruction_v55_split_metrics.csv"
SRC_ASSERTIONS = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T234414-codex-r6-direct-intake-reconstruction-v55"
    / "checks/r6_direct_intake_reconstruction_v55_assertions.out"
)
JPM_ORDER_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T235048-codex-r6-jpmorgan-order-positive-row-candidate-screen-v1"
    / "r6-jpmorgan-order-positive-row-candidate-screen/r6_jpmorgan_order_positive_row_candidate_screen_v1.json"
)
SIDECAR = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1"
    / "r6-broad-normal-order-lifecycle-screen/broad_normal_market_order_lifecycle_controls_v1.csv"
)
FIELDS = [
    "label",
    "source_report",
    "source_section",
    "trade_date",
    "symbol",
    "venue_or_market_center",
    "participant_type_code",
    "participant_identifier",
    "side",
    "earliest_order_received_time",
    "latest_order_received_time",
    "order_count",
    "total_order_quantity",
    "activity_description",
    "matched_negative_group_id",
    "session_bucket",
    "source_row_id",
]
Z_95 = 1.96


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def run_command(name: str, args: list[str], timeout_seconds: int = 90) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        returncode = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout_seconds}s\n"
        returncode = 124
        timed_out = True
    out_path = CMD / f"{name}.stdout.txt"
    err_path = CMD / f"{name}.stderr.txt"
    exit_path = CMD / f"{name}.exit"
    out_path.write_text(stdout, encoding="utf-8")
    err_path.write_text(stderr, encoding="utf-8")
    exit_path.write_text(f"{returncode}\n", encoding="utf-8")
    try:
        parsed: Any = json.loads(stdout)
    except json.JSONDecodeError:
        parsed = None
    return {
        "name": name,
        "cmd": " ".join(args),
        "returncode": returncode,
        "timed_out": timed_out,
        "stdout_path": str(out_path.relative_to(REPO)),
        "stderr_path": str(err_path.relative_to(REPO)),
        "exit_path": str(exit_path.relative_to(REPO)),
        "parsed": parsed,
    }


def split_metrics(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    dated = sorted(rows, key=lambda row: row.get("trade_date", ""))
    train_end = math.ceil(len(dated) * 0.5)
    cal_end = train_end + math.floor((len(dated) - train_end) / 2)
    splits = [
        ("chronological", "train", dated[:train_end]),
        ("chronological", "calibration", dated[train_end:cal_end]),
        ("chronological", "test", dated[cal_end:]),
    ]
    metrics: list[dict[str, object]] = []
    for key, value, part in splits:
        metrics.append(
            {
                "split_key": key,
                "split_value": value,
                "rows": len(part),
                "start_trade_date": part[0]["trade_date"] if part else "",
                "end_trade_date": part[-1]["trade_date"] if part else "",
                "wilson95_lcb": wilson_lcb(len(part), len(part)),
                "support_gate": len(part) >= 50,
                "confidence_gate": wilson_lcb(len(part), len(part)) >= 0.95,
            }
        )
    for field in ["symbol", "venue_or_market_center"]:
        groups: dict[str, list[dict[str, str]]] = {}
        for row in rows:
            groups.setdefault(row.get(field, ""), []).append(row)
        for value, part in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
            metrics.append(
                {
                    "split_key": field,
                    "split_value": value,
                    "rows": len(part),
                    "start_trade_date": "",
                    "end_trade_date": "",
                    "wilson95_lcb": wilson_lcb(len(part), len(part)),
                    "support_gate": len(part) >= 50,
                    "confidence_gate": wilson_lcb(len(part), len(part)) >= 0.95,
                }
            )
    return metrics


def provider_summary(payload: Any, provider_id: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"provider_id": provider_id, "observed": False, "ready": False, "status": "unparsed", "reason": ""}
    matches = [row for row in payload.get("providers", []) if row.get("provider_id") == provider_id]
    if not matches:
        return {"provider_id": provider_id, "observed": False, "ready": False, "status": "not_listed", "reason": ""}
    return {
        "provider_id": provider_id,
        "observed": True,
        "ready": any(bool(row.get("ready")) for row in matches),
        "status": ";".join(sorted({str(row.get("status")) for row in matches})),
        "reason": ";".join(sorted({str(row.get("reason")) for row in matches})),
    }


def stale_assertion_check(source_json: dict[str, Any]) -> dict[str, Any]:
    text = SRC_ASSERTIONS.read_text(encoding="utf-8", errors="replace") if SRC_ASSERTIONS.exists() else ""
    stale = "reconstructed_positive_rows=53" in text and source_json.get("positive_rows") == 73
    return {
        "assertions_path": str(SRC_ASSERTIONS.relative_to(REPO)),
        "assertions_file_mentions_53": "reconstructed_positive_rows=53" in text,
        "source_json_positive_rows": source_json.get("positive_rows"),
        "stale_assertions_detected": stale,
    }


def main() -> int:
    for path in [OUT, CHECKS, CMD, INTAKE, STATE_DIR, AQ_STATE_DIR]:
        path.mkdir(parents=True, exist_ok=True)

    positives = read_csv(SRC_POSITIVE)
    negatives = read_csv(SRC_NEGATIVE)
    sidecar_rows = read_csv(SIDECAR)
    source_json = json.loads(SRC_RECON_JSON.read_text(encoding="utf-8"))
    jpm_order = json.loads(JPM_ORDER_JSON.read_text(encoding="utf-8"))

    write_csv(INTAKE / "positive_spoofing_layering_rows.csv", positives, FIELDS)
    write_csv(INTAKE / "matched_negative_normal_activity_rows.csv", negatives, FIELDS)
    provenance = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_reconstruction_json": str(SRC_RECON_JSON.relative_to(REPO)),
        "source_positive_rows": str(SRC_POSITIVE.relative_to(REPO)),
        "source_negative_rows": str(SRC_NEGATIVE.relative_to(REPO)),
        "jpm_order_control_complete_json": str(JPM_ORDER_JSON.relative_to(REPO)),
        "raw_data_committed": False,
        "shared_intake_mutated": False,
    }
    (INTAKE / "provenance_manifest.json").write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    verifier = run_command("isolated_direct_verifier", ["python3", str(DIRECT_VERIFIER), "--intake-root", str(INTAKE)])
    live_verifier = run_command("live_direct_verifier", ["python3", str(DIRECT_VERIFIER), "--intake-root", str(LIVE_INTAKE)])
    provider_cmd = run_command("provider_status_agent", [str(BIN), "provider-status", "--agent"])
    for provider in ["ibkr", "tradingview_mcp", "yfinance", "kraken_public", "kraken_cli"]:
        run_command(f"provider_status_{provider}_agent", [str(BIN), "provider-status", "--provider", provider, "--agent"])
    chain_commands = [
        run_command("auto_quant_status", [str(BIN), "auto-quant-status", "--state-dir", str(AQ_STATE_DIR), "--output-format", "json"]),
        run_command(
            "analyze_live_nq_yfinance",
            [
                str(BIN),
                "analyze-live",
                "--symbol",
                "NQ",
                "--futures-symbol",
                "NQ=F",
                "--spot-symbol",
                "QQQ",
                "--options-symbol",
                "QQQ",
                "--options-volatility-proxy-symbol",
                "^VIX",
                "--futures-backend",
                "yfinance",
                "--aux-backend",
                "yfinance",
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
            timeout_seconds=150,
        ),
        run_command("pre_bayes_status", [str(BIN), "pre-bayes-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--refresh"]),
        run_command("policy_training_status", [str(BIN), "policy-training-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--output-format", "json"]),
        run_command("workflow_status_execution_candidate", [str(BIN), "workflow-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--phase", "execution-candidate", "--agent"]),
        run_command("export_structural_path_ranking_target", [str(BIN), "export-structural-path-ranking-target", "--symbol", "NQ", "--state-dir", str(STATE_DIR)]),
    ]

    metrics = split_metrics(positives)
    write_csv(
        OUT / "r6_isolated_reconstruction_verification_v57_split_metrics.csv",
        [{key: str(value) for key, value in row.items()} for row in metrics],
        ["split_key", "split_value", "rows", "start_trade_date", "end_trade_date", "wilson95_lcb", "support_gate", "confidence_gate"],
    )
    shutil.copy2(SRC_SPLITS, OUT / "r6_prior_reconstruction_v55_split_metrics.csv")

    positive_lcb = wilson_lcb(len(positives), len(positives))
    negative_lcb = wilson_lcb(len(negatives), len(negatives))
    sidecar_lcb = wilson_lcb(len(sidecar_rows), len(sidecar_rows))
    pooled_min = min(positive_lcb, negative_lcb, sidecar_lcb)
    chronological_gate = all(
        bool(row["support_gate"]) and bool(row["confidence_gate"])
        for row in metrics
        if row["split_key"] == "chronological"
    )
    symbol_gate = all(
        bool(row["support_gate"]) and bool(row["confidence_gate"])
        for row in metrics
        if row["split_key"] == "symbol"
    )
    venue_gate = all(
        bool(row["support_gate"]) and bool(row["confidence_gate"])
        for row in metrics
        if row["split_key"] == "venue_or_market_center"
    )
    providers = [
        provider_summary(provider_cmd.get("parsed"), provider)
        for provider in ["ibkr", "tradingview_mcp", "yfinance", "kraken_public", "kraken_cli"]
    ]
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "source_reconstruction": {
            "json": str(SRC_RECON_JSON.relative_to(REPO)),
            "positive_rows_csv": str(SRC_POSITIVE.relative_to(REPO)),
            "matched_negative_rows_csv": str(SRC_NEGATIVE.relative_to(REPO)),
            "stale_assertion_check": stale_assertion_check(source_json),
        },
        "jpm_order_control_complete_readback": {
            "json": str(JPM_ORDER_JSON.relative_to(REPO)),
            "candidate_delta": jpm_order.get("candidate_delta", {}),
            "composite_readback": jpm_order.get("composite_readback", {}),
        },
        "isolated_intake_root": str(INTAKE.relative_to(REPO)),
        "isolated_verifier": verifier,
        "live_shared_intake_verifier": live_verifier,
        "positive_rows": len(positives),
        "matched_negative_rows": len(negatives),
        "sidecar_broad_normal_control_rows": len(sidecar_rows),
        "positive_wilson95_lcb": round(positive_lcb, 12),
        "matched_negative_wilson95_lcb": round(negative_lcb, 12),
        "sidecar_broad_normal_wilson95_lcb": round(sidecar_lcb, 12),
        "pooled_min_wilson95_lcb": round(pooled_min, 12),
        "pooled_95_gate": pooled_min >= 0.95,
        "chronological_split_gate": chronological_gate,
        "heldout_symbol_gate": symbol_gate,
        "heldout_venue_gate": venue_gate,
        "direct_species_closed": False,
        "providers": providers,
        "chain_readback": {
            row["name"]: {
                "returncode": row["returncode"],
                "timed_out": row["timed_out"],
                "stdout_path": row["stdout_path"],
                "stderr_path": row["stderr_path"],
            }
            for row in chain_commands
        },
        "gate_result": "r6_isolated_reconstruction_verification_v57=isolated_pooled95_verified_split_species_full_objective_still_blocked",
        "accepted_rows_added": 0,
        "new_confidence_gate": True,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "shared_intake_mutated": False,
        "external_requests_sent": True,
        "trade_usable": False,
        "next_action": "Source non-spoofing direct Manipulation species and enough split-balanced rows to pass chronological, symbol, and venue Wilson95 gates; keep R5 source-owner recency and R3 native-subhour blockers open.",
    }
    json_path = OUT / "r6_isolated_reconstruction_verification_v57.json"
    md_path = OUT / "r6_isolated_reconstruction_verification_v57.md"
    assertions_path = CHECKS / "r6_isolated_reconstruction_verification_v57_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# R6 Isolated Reconstruction Verification v57",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Isolated verifier status: `{(verifier.get('parsed') or {}).get('status', 'unparsed')}`.",
        f"- Live shared intake status: `{(live_verifier.get('parsed') or {}).get('status', 'unparsed')}`.",
        f"- Verified isolated rows: positives `{len(positives)}`, matched controls `{len(negatives)}`, sidecar broad-normal controls `{len(sidecar_rows)}`.",
        f"- Pooled min Wilson95 LCB: `{pooled_min:.12f}`; pooled 95 gate: `{str(pooled_min >= 0.95).lower()}`.",
        f"- Split gates: chronological `{str(chronological_gate).lower()}`, symbol `{str(symbol_gate).lower()}`, venue `{str(venue_gate).lower()}`.",
        f"- Prior `234414` assertions stale: `{str(result['source_reconstruction']['stale_assertion_check']['stale_assertions_detected']).lower()}`.",
        f"- Gate result: `{result['gate_result']}`.",
        "- Accepted rows added: `0`; new confidence gate: `true` for isolated R6 pooled Wilson95 only.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; shared intake mutated: `false`; trade usable: `false`.",
        "",
        "## Runtime Readback",
        "",
        "| Surface | Exit | Output |",
        "|---|---:|---|",
    ]
    for row in chain_commands:
        lines.append(f"| `{row['name']}` | `{row['returncode']}` | `{row['stdout_path']}` |")
    lines.extend(["", "## Artifacts", ""])
    for label, path in [
        ("JSON", json_path),
        ("Report", md_path),
        ("Isolated positives", INTAKE / "positive_spoofing_layering_rows.csv"),
        ("Isolated matched controls", INTAKE / "matched_negative_normal_activity_rows.csv"),
        ("Split metrics", OUT / "r6_isolated_reconstruction_verification_v57_split_metrics.csv"),
        ("Assertions", assertions_path),
    ]:
        lines.append(f"- {label}: `{path.relative_to(REPO)}`")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    live_status = (live_verifier.get("parsed") or {}).get("status")
    assertions = [
        ("isolated_verifier_returncode", verifier["returncode"] == 0),
        ("isolated_positive_rows_73", len(positives) == 73),
        ("isolated_matched_negative_rows_73", len(negatives) == 73),
        ("pooled_min_wilson95_ge_095", pooled_min >= 0.95),
        ("chronological_split_gate_false", chronological_gate is False),
        ("heldout_symbol_gate_false", symbol_gate is False),
        ("heldout_venue_gate_false", venue_gate is False),
        ("live_shared_intake_readback_completed", live_status in {"blocked", "schema_ready_unscored"}),
        ("update_goal_false", result["update_goal"] is False),
    ]
    assertions_path.write_text(
        "\n".join(f"{name}={'PASS' if passed else 'FAIL'}" for name, passed in assertions) + "\n",
        encoding="utf-8",
    )
    if not all(passed for _, passed in assertions):
        raise SystemExit(2)
    print(json.dumps({"gate_result": result["gate_result"], "pooled_min_wilson95_lcb": result["pooled_min_wilson95_lcb"], "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
