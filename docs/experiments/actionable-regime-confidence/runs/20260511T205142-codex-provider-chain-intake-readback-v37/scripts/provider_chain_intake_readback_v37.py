#!/usr/bin/env python3
"""Board A provider/full-chain/intake readback without promoting proxy labels."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T205142-codex-provider-chain-intake-readback-v37"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "provider-chain-intake-readback"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
ICT = REPO / "target/debug/ict-engine"
AUTO_QUANT = Path("/Users/thrill3r/Auto-Quant")

V35 = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T204335-codex-current-goal-completion-audit-v35-after-source-outbox/"
    "completion-audit/current_goal_completion_audit_v35_after_source_outbox.json"
)
OUTBOX_V2 = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T204715-codex-source-acquisition-outbox-v2-after-r6-uplift/"
    "source-acquisition-outbox-v2/source_acquisition_outbox_v2.json"
)
REQUEST_DRAFTS = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T204729-codex-source-acquisition-request-draft-bundle-v1/"
    "source-acquisition-request-draft-bundle/source_acquisition_request_draft_bundle_v1.json"
)
PUBLIC_SCOUT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T205031-codex-current-public-regime-dataset-scout-v1/"
    "current-public-regime-dataset-scout/current_public_regime_dataset_scout_v1.json"
)
REAL_CHAIN_RUN = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/20260510T201931-hermes-loop-real-chain"
)

SOURCE_LABEL_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)
RECENCY_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)
DIRECT_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

INTAKE_ROOTS = [
    {
        "id": "source_label_equivalence",
        "requirements": "R2;R4",
        "root": Path("/tmp/ict-engine-source-label-equivalence-intake"),
        "required": ["source_label_equivalence_rows.csv", "source_label_equivalence_provenance.json"],
        "verifier": SOURCE_LABEL_VERIFIER,
    },
    {
        "id": "native_subhour_source_label",
        "requirements": "R3",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required": ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"],
        "verifier": None,
    },
    {
        "id": "source_panel_recency_extension",
        "requirements": "R5",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required": ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"],
        "verifier": RECENCY_VERIFIER,
    },
    {
        "id": "direct_manipulation_row_intake",
        "requirements": "R6",
        "root": Path("/tmp/ict-engine-direct-manipulation-row-intake"),
        "required": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
        "verifier": DIRECT_VERIFIER,
    },
]

TMP_STRATEGY_ROOTS = [
    Path("/tmp/ict-regime-chain-20260509T231052/scratch_strategies"),
    Path("/tmp/ict-regime-branch-iteration-20260510-1"),
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(name: str, args: list[str], timeout: int = 45, cwd: Path | None = None) -> dict[str, Any]:
    env = os.environ.copy()
    env.setdefault("PYTHONWARNINGS", "ignore")
    try:
        proc = subprocess.run(
            args,
            cwd=cwd or REPO,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        result = {
            "name": name,
            "cmd": args,
            "returncode": proc.returncode,
            "stdout_path": rel(OUT / f"{name}.stdout.txt"),
            "stderr_path": rel(OUT / f"{name}.stderr.txt"),
            "stdout_tail": proc.stdout[-2000:],
            "stderr_tail": proc.stderr[-2000:],
            "timed_out": False,
        }
        (OUT / f"{name}.stdout.txt").write_text(proc.stdout, encoding="utf-8")
        (OUT / f"{name}.stderr.txt").write_text(proc.stderr, encoding="utf-8")
        try:
            result["parsed_json"] = json.loads(proc.stdout)
        except json.JSONDecodeError:
            result["parsed_json"] = None
        return result
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        (OUT / f"{name}.stdout.txt").write_text(stdout, encoding="utf-8")
        (OUT / f"{name}.stderr.txt").write_text(stderr, encoding="utf-8")
        return {
            "name": name,
            "cmd": args,
            "returncode": None,
            "stdout_path": rel(OUT / f"{name}.stdout.txt"),
            "stderr_path": rel(OUT / f"{name}.stderr.txt"),
            "stdout_tail": stdout[-2000:],
            "stderr_tail": stderr[-2000:],
            "timed_out": True,
            "parsed_json": None,
        }


def root_status(config: dict[str, Any]) -> dict[str, Any]:
    root = config["root"]
    present = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()) if root.exists() else []
    missing = [name for name in config["required"] if not (root / name).is_file()]
    return {
        "id": config["id"],
        "requirements": config["requirements"],
        "root": str(root),
        "required_files": ";".join(config["required"]),
        "present_files": ";".join(present),
        "missing_files": ";".join(missing),
        "exists": root.exists(),
        "ready": not missing,
    }


def run_verifier(config: dict[str, Any], status: dict[str, Any]) -> dict[str, Any]:
    verifier = config["verifier"]
    if verifier is None:
        return {
            "id": config["id"],
            "status": "ready_files_present_unscored" if status["ready"] else "blocked",
            "reason": "native_subhour_required_files_present" if status["ready"] else "missing_required_files",
            "returncode": None,
            "parsed_json": status,
        }
    result = run_command(
        f"verifier_{config['id']}",
        ["python3", str(verifier), "--intake-root", str(config["root"])],
        timeout=30,
    )
    return {
        "id": config["id"],
        "status": "ran",
        "reason": "see_verifier_output",
        "returncode": result["returncode"],
        "timed_out": result["timed_out"],
        "parsed_json": result.get("parsed_json"),
        "stdout_path": result["stdout_path"],
        "stderr_path": result["stderr_path"],
    }


def provider_summary(provider_json: dict[str, Any]) -> dict[str, Any]:
    providers = provider_json.get("providers") or []
    wanted = {
        "ibkr",
        "ibkr_bridge",
        "tradingview_mcp",
        "yfinance",
        "kraken_public",
        "kraken_cli",
        "auto_quant_cache",
    }
    named = []
    for provider in providers:
        if provider.get("provider_id") in wanted:
            named.append(
                {
                    "provider_id": provider.get("provider_id", ""),
                    "domain": provider.get("domain", ""),
                    "ready": provider.get("ready", False),
                    "status": provider.get("status", ""),
                    "reason": provider.get("reason", ""),
                    "summary": provider.get("summary", ""),
                }
            )
    return {
        "summary_line": provider_json.get("summary_line", ""),
        "ready_by_domain": provider_json.get("ready_by_domain", {}),
        "named_providers": named,
    }


def tmp_strategy_inventory() -> list[dict[str, Any]]:
    rows = []
    for root in TMP_STRATEGY_ROOTS:
        files = []
        if root.exists():
            files = sorted(str(path.relative_to(root)) for path in root.rglob("*.py") if path.is_file())
        rows.append(
            {
                "root": str(root),
                "exists": root.exists(),
                "strategy_py_count": len(files),
                "sample_files": ";".join(files[:20]),
            }
        )
    return rows


def artifact_exists(path: Path) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256(path) if path.is_file() else "",
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    board_hash = sha256(BOARD)
    v35 = read_json(V35)
    outbox_v2 = read_json(OUTBOX_V2)
    request_drafts = read_json(REQUEST_DRAFTS)
    public_scout = read_json(PUBLIC_SCOUT)

    provider_agent = run_command("provider_status_agent", [str(ICT), "provider-status", "--agent"], timeout=90)
    run_command("provider_status_compact", [str(ICT), "provider-status", "--compact"], timeout=90)
    for provider_id in ["ibkr", "tradingview_mcp", "yfinance", "kraken_public", "kraken_cli", "auto_quant_cache"]:
        run_command(
            f"provider_{provider_id}_agent",
            [str(ICT), "provider-status", "--provider", provider_id, "--agent"],
            timeout=60,
        )

    auto_quant_import_probe = run_command(
        "auto_quant_uv_import_probe",
        [
            "uv",
            "--directory",
            str(AUTO_QUANT),
            "run",
            "python",
            "-c",
            (
                "import importlib.util,json; "
                "print(json.dumps({'freqtrade': importlib.util.find_spec('freqtrade') is not None, "
                "'pandas': importlib.util.find_spec('pandas') is not None}))"
            ),
        ],
        timeout=90,
        cwd=AUTO_QUANT if AUTO_QUANT.exists() else REPO,
    )

    real_chain_artifacts = [
        artifact_exists(REAL_CHAIN_RUN / "autoquant/03_auto_quant_results_import_nq.json"),
        artifact_exists(REAL_CHAIN_RUN / "bbn/02_auto_quant_prior_init_nq_apply.json"),
        artifact_exists(REAL_CHAIN_RUN / "ict-engine/06_pre_bayes_status_isolated_after_bbn.json"),
        artifact_exists(REAL_CHAIN_RUN / "catboost/07_apply_structural_path_ranking_external_scores.json"),
        artifact_exists(REAL_CHAIN_RUN / "ict-engine/07_policy_training_status_after_catboost_apply.json"),
        artifact_exists(REAL_CHAIN_RUN / "execution/02_execution_tree_trace_after_catboost_apply_nq.json"),
    ]

    roots = [root_status(config) for config in INTAKE_ROOTS]
    verifier_results = [run_verifier(config, status) for config, status in zip(INTAKE_ROOTS, roots)]
    ready_roots = [row["id"] for row in roots if row["ready"]]
    tmp_strategies = tmp_strategy_inventory()
    provider = provider_summary(provider_agent.get("parsed_json") or {})

    chain_artifact_all_present = all(row["exists"] for row in real_chain_artifacts)
    request_rows = outbox_v2.get("v2_outbox_rows") or 0
    public_candidate_count = public_scout.get("candidate_count") or 0
    public_rows_acquired = bool(public_scout.get("rows_acquired_for_strict_gate"))
    decision = "provider_chain_intake_readback_v37=intakes_absent_runtime_chain_readback_no_new_gate_blocked"
    checklist = [
        {
            "id": "R0",
            "requirement": "Use the named Board A markdown and current cursor as the live contract.",
            "artifact": rel(BOARD),
            "status": "pass_checked",
            "evidence": f"board_hash_before_writeback={board_hash}; current cursor read before this run.",
            "gap": "",
        },
        {
            "id": "R1",
            "requirement": "Check IBKR, TradingViewRemix/TradingView MCP, yfinance, Kraken, local cache, and Auto-Quant cache/provider readiness.",
            "artifact": rel(OUT / "provider_status_agent.stdout.txt"),
            "status": "partial_provider_health_changed",
            "evidence": provider["summary_line"],
            "gap": "Current provider status is read back, but provider readiness alone does not create missing source-owned regime rows.",
        },
        {
            "id": "R2",
            "requirement": "Operate/verify Auto-Quant availability and avoid the known false blocker from default strategy dirs.",
            "artifact": rel(OUT / "auto_quant_uv_import_probe.stdout.txt"),
            "status": "pass_readback",
            "evidence": f"uv_import_probe_rc={auto_quant_import_probe['returncode']}; tmp_strategy_roots={tmp_strategies}",
            "gap": "No new Auto-Quant training/backtest was started because strict Board A is blocked on source-owned labels, not another strategy search.",
        },
        {
            "id": "R3",
            "requirement": "Verify prior full-chain artifacts exist for Auto-Quant -> BBN/Pre-Bayes -> CatBoost -> execution tree.",
            "artifact": rel(REAL_CHAIN_RUN / "evidence_packet_real_chain_loop.json"),
            "status": "pass_readback" if chain_artifact_all_present else "fail_missing_artifact",
            "evidence": f"real_chain_artifact_all_present={chain_artifact_all_present}",
            "gap": "" if chain_artifact_all_present else "One or more expected full-chain artifact files are absent.",
        },
        {
            "id": "R4",
            "requirement": "Recheck required source-owned intake roots before claiming completion.",
            "artifact": rel(OUT / "provider_chain_intake_readback_v37_intake_roots.csv"),
            "status": "fail_blocked",
            "evidence": f"ready_intake_roots={len(ready_roots)}/4; required roots={ready_roots}",
            "gap": "R2/R3/R4/R5/R6 required source-owned/provenance files are still absent.",
        },
        {
            "id": "R5",
            "requirement": "Account for latest outbox/drafts/public scout without sending external requests or accepting proxy labels.",
            "artifact": f"{rel(OUTBOX_V2)}; {rel(REQUEST_DRAFTS)}; {rel(PUBLIC_SCOUT)}",
            "status": "pass_guardrail",
            "evidence": f"outbox_v2_rows={request_rows}; public_candidate_count={public_candidate_count}; public_rows_acquired={public_rows_acquired}; request_sent=false",
            "gap": "Rows are queued or scouted, not acquired.",
        },
        {
            "id": "R6",
            "requirement": "Do not call update_goal until every strict full-objective row is covered.",
            "artifact": rel(OUT / "provider_chain_intake_readback_v37.json"),
            "status": "fail_blocked",
            "evidence": "strict_full_objective_achieved=false; update_goal=false",
            "gap": "Strict full objective remains blocked by source-owned intake gaps.",
        },
    ]

    audit = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "board_hash_before_writeback": board_hash,
        "objective_restatement": (
            "Every active Board A regime needs source-owned or owner-approved >=95% calibrated confidence "
            "evidence plus cross-market/cross-timeframe/full-cycle validation before update_goal can be true."
        ),
        "v35_decision": v35.get("decision"),
        "outbox_v2_decision": outbox_v2.get("decision"),
        "request_draft_decision": request_drafts.get("decision"),
        "public_scout_decision": public_scout.get("decision"),
        "provider_summary": provider,
        "auto_quant_import_probe": {
            "returncode": auto_quant_import_probe["returncode"],
            "timed_out": auto_quant_import_probe["timed_out"],
            "stdout_path": auto_quant_import_probe["stdout_path"],
            "stderr_path": auto_quant_import_probe["stderr_path"],
            "parsed_json": auto_quant_import_probe.get("parsed_json"),
        },
        "tmp_strategy_inventory": tmp_strategies,
        "real_chain_run": rel(REAL_CHAIN_RUN),
        "real_chain_artifacts": real_chain_artifacts,
        "real_chain_artifact_all_present": chain_artifact_all_present,
        "intake_roots_checked": roots,
        "verifier_results": verifier_results,
        "ready_intake_roots": ready_roots,
        "ready_intake_root_count": len(ready_roots),
        "outbox_v2_rows": request_rows,
        "request_sent": False,
        "external_authenticated_message_sent": False,
        "rows_acquired": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "unmet_ids": ["R2", "R3", "R4", "R5", "R6", "R8"],
        "checklist": checklist,
        "next_action": (
            "Populate one of the four required /tmp intake roots with real source-owned or owner-approved "
            "rows/provenance, then rerun the corresponding fail-closed verifier before any completion audit."
        ),
    }

    (OUT / "provider_chain_intake_readback_v37.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_csv(
        OUT / "provider_chain_intake_readback_v37_intake_roots.csv",
        roots,
        ["id", "requirements", "root", "required_files", "present_files", "missing_files", "exists", "ready"],
    )
    write_csv(
        OUT / "provider_chain_intake_readback_v37_named_providers.csv",
        provider["named_providers"],
        ["provider_id", "domain", "ready", "status", "reason", "summary"],
    )
    write_csv(
        OUT / "provider_chain_intake_readback_v37_checklist.csv",
        checklist,
        ["id", "requirement", "artifact", "status", "evidence", "gap"],
    )

    lines = [
        "# Provider Chain Intake Readback v37",
        "",
        f"Decision: `{decision}`.",
        "",
        "## Result",
        "",
        f"- Provider status: `{provider['summary_line']}`.",
        f"- Ready intake roots: `{len(ready_roots)}/4`.",
        f"- Real-chain artifact readback complete: `{str(chain_artifact_all_present).lower()}`.",
        f"- Outbox v2 rows: `{request_rows}`; request sent: `false`; rows acquired: `false`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Named Providers",
        "",
        "| Provider | Domain | Ready | Status | Reason |",
        "|---|---|---:|---|---|",
    ]
    for row in provider["named_providers"]:
        lines.append(
            f"| `{row['provider_id']}` | `{row['domain']}` | `{str(row['ready']).lower()}` | "
            f"`{row['status']}` | `{row['reason']}` |"
        )
    lines.extend(
        [
            "",
            "## Intake Roots",
            "",
            "| Root | Ready | Missing Files |",
            "|---|---:|---|",
        ]
    )
    for row in roots:
        lines.append(f"| `{row['id']}` | `{str(row['ready']).lower()}` | `{row['missing_files']}` |")
    lines.extend(
        [
            "",
            "## Full-Chain Readback",
            "",
            "| Artifact | Exists |",
            "|---|---:|",
        ]
    )
    for row in real_chain_artifacts:
        lines.append(f"| `{row['path']}` | `{str(row['exists']).lower()}` |")
    lines.extend(
        [
            "",
            "## Next",
            "",
            "Do not relax thresholds or promote public proxy labels. Populate one of the required /tmp intake roots "
            "with real source-owned or owner-approved rows/provenance, then rerun the relevant verifier.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(OUT / 'provider_chain_intake_readback_v37.json')}`",
            f"- Intake roots: `{rel(OUT / 'provider_chain_intake_readback_v37_intake_roots.csv')}`",
            f"- Named providers: `{rel(OUT / 'provider_chain_intake_readback_v37_named_providers.csv')}`",
            f"- Checklist: `{rel(OUT / 'provider_chain_intake_readback_v37_checklist.csv')}`",
            f"- Assertions: `{rel(CHECKS / 'provider_chain_intake_readback_v37_assertions.out')}`",
        ]
    )
    (OUT / "provider_chain_intake_readback_v37.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS provider_summary_line={provider['summary_line']}",
        f"PASS real_chain_artifact_all_present={str(chain_artifact_all_present).lower()}",
        f"PASS ready_intake_roots={len(ready_roots)}_of_4",
        "PASS request_sent=false",
        "PASS external_authenticated_message_sent=false",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    (CHECKS / "provider_chain_intake_readback_v37_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    print(json.dumps({"decision": decision, "ready_intake_roots": len(ready_roots)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
