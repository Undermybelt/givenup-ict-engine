#!/usr/bin/env python3
"""Post-065506 read-only Board A source/control and runtime refresh."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


RUN_ID = "20260512T065822+0800-codex-source-control-provider-refresh-after-065506-v1"
GATE = (
    "source_control_provider_refresh_after_065506_v1="
    "autoquant_ready_source_control_still_blocked_no_promotion"
)
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
PACKET = RUN_ROOT / "source-control-provider-refresh-after-065506-v1"
OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
STATE_DIR = Path("/tmp/ict-engine-board-a-064259-runtime-v1")
R6_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
R3_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
R5_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
EQUIV_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")


def run_cmd(key: str, args: list[str], timeout: int = 120) -> dict[str, Any]:
    cmd_path = OUT / f"{key}.cmd"
    stdout_path = OUT / f"{key}.stdout"
    stderr_path = OUT / f"{key}.stderr"
    exit_path = OUT / f"{key}.exit"
    cmd_path.write_text(" ".join(args) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(
            args,
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        stdout_path.write_text(proc.stdout, encoding="utf-8")
        stderr_path.write_text(proc.stderr, encoding="utf-8")
        exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
        return {
            "key": key,
            "args": args,
            "returncode": proc.returncode,
            "timeout": False,
            "stdout_path": str(stdout_path.relative_to(REPO)),
            "stderr_path": str(stderr_path.relative_to(REPO)),
        }
    except subprocess.TimeoutExpired as exc:
        stdout_path.write_text(exc.stdout or "", encoding="utf-8")
        stderr_path.write_text(exc.stderr or "", encoding="utf-8")
        exit_path.write_text("timeout\n", encoding="utf-8")
        return {
            "key": key,
            "args": args,
            "returncode": None,
            "timeout": True,
            "stdout_path": str(stdout_path.relative_to(REPO)),
            "stderr_path": str(stderr_path.relative_to(REPO)),
        }


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def command_json(key: str) -> dict[str, Any]:
    return load_json(OUT / f"{key}.stdout")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_status(root: Path, required: list[str]) -> dict[str, Any]:
    present = sorted(p.name for p in root.iterdir() if p.is_file()) if root.exists() else []
    required_present = {name: (root / name).exists() for name in required}
    return {
        "root": str(root),
        "root_exists": root.exists(),
        "present_files": present,
        "required_present": required_present,
        "physical_complete": root.exists() and all(required_present.values()),
    }


def source_roots() -> list[dict[str, Any]]:
    r6 = file_status(
        R6_ROOT,
        [
            "direct_manipulation_positive_rows.csv",
            "direct_manipulation_matched_controls.csv",
            "direct_manipulation_provenance.json",
        ],
    )
    r6.update(
        {
            "id": "r6_owner_export",
            "policy": "verifier-native owner/export rows plus valid normal controls",
            "accepted_for_promotion": False,
            "notes": "target root absent or incomplete",
        }
    )

    r3_prov = load_json(R3_ROOT / "native_subhour_source_label_provenance.json")
    r3 = file_status(
        R3_ROOT,
        [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
    )
    r3_labels = r3_prov.get("accepted_mapping_confidence_95_labels", [])
    r3.update(
        {
            "id": "r3_native_subhour",
            "policy": "verifier-native MainRegimeV2 labels including Crisis; TSIE proxy stays quarantined",
            "accepted_for_promotion": False,
            "row_count": r3_prov.get("row_count"),
            "labels": r3_labels,
            "provenance_run_id": r3_prov.get("run_id"),
            "limitations": r3_prov.get("limitations", []),
            "notes": "physical files present but TSIE-derived, Crisis absent, policy accepted false",
        }
    )

    r5 = file_status(
        R5_ROOT,
        [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
    )
    r5.update(
        {
            "id": "r5_recency_extension",
            "policy": "source-owned rows after 2026-01-30",
            "accepted_for_promotion": False,
            "notes": "target root absent or incomplete",
        }
    )

    equiv_prov = load_json(EQUIV_ROOT / "source_label_equivalence_provenance.json")
    equiv = file_status(
        EQUIV_ROOT,
        [
            "source_label_equivalence_rows.csv",
            "source_label_equivalence_provenance.json",
        ],
    )
    equiv.update(
        {
            "id": "source_label_equivalence",
            "policy": "schema/equivalence context only; does not satisfy native subhour or recency root",
            "accepted_for_promotion": False,
            "row_count": equiv_prov.get("row_count"),
            "labels": sorted((equiv_prov.get("label_counts") or {}).keys()),
            "provenance_run_id": equiv_prov.get("run_id"),
            "limitations": equiv_prov.get("limitations", []),
            "notes": "non-target/non-promoting equivalence root",
        }
    )

    return [r6, r3, r5, equiv]


def bounded_candidates() -> list[dict[str, Any]]:
    roots = [
        Path("/tmp"),
        Path("/private/tmp"),
        Path.home() / "Downloads",
        Path.home() / "Desktop",
        Path.home() / "Documents",
        Path.home() / "Auto-Quant/user_data",
    ]
    tokens = [
        "oystacher",
        "spoof",
        "flip",
        "cme",
        "cboe",
        "cfe",
        "vix",
        "market_depth",
        "market depth",
        "market_by_order",
        "market by order",
        "databento",
        "dbn",
        "source_label",
        "mainregime",
        "stock_market_regimes",
    ]
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        base_depth = len(root.parts)
        for dirpath, dirnames, filenames in os.walk(root):
            cur = Path(dirpath)
            depth = len(cur.parts) - base_depth
            if depth > 5:
                dirnames[:] = []
                continue
            dirnames[:] = [
                d
                for d in dirnames
                if d not in {".git", "node_modules", "target", ".venv", "__pycache__"}
            ]
            for filename in filenames:
                lower = filename.lower().replace("-", "_")
                full_lower = str(cur / filename).lower().replace("-", "_")
                if not any(token.replace(" ", "_") in full_lower for token in tokens):
                    continue
                path = cur / filename
                key = str(path)
                if key in seen:
                    continue
                seen.add(key)
                try:
                    stat = path.stat()
                except OSError:
                    continue
                decision = "context_only_not_valid_unlock"
                if str(path).startswith(str(R6_ROOT)):
                    decision = "target_r6_root_member"
                elif str(path).startswith(str(R5_ROOT)):
                    decision = "target_r5_root_member"
                elif str(path).startswith(str(R3_ROOT)):
                    decision = "target_r3_root_member_policy_quarantined"
                rows.append(
                    {
                        "path": str(path),
                        "size_bytes": stat.st_size,
                        "mtime_epoch": int(stat.st_mtime),
                        "decision": decision,
                    }
                )
    rows.sort(key=lambda item: (item["decision"], item["path"]))
    return rows[:500]


def parse_provider() -> dict[str, Any]:
    data = command_json("provider_status_agent")
    return {
        "summary_line": data.get("summary_line"),
        "ready_by_domain": data.get("ready_by_domain", {}),
        "ready_providers": data.get("ready_providers", []),
        "pending_providers": data.get("pending_providers", []),
    }


def parse_auto_quant() -> dict[str, Any]:
    data = command_json("auto_quant_status_after_065506")
    dep = data.get("dependency_status") or {}
    return {
        "status": data.get("status"),
        "healthy": data.get("healthy"),
        "dependency_healthy": data.get("dependency_healthy"),
        "data_ready": data.get("data_ready"),
        "bootstrap_needed": data.get("bootstrap_needed"),
        "current_commit": dep.get("current_commit"),
        "recommended_next_command": data.get("recommended_next_command"),
    }


def parse_analyze() -> dict[str, Any]:
    data = command_json("analyze_live_nq_yfinance_agent")
    triage = data.get("execution_triage") or {}
    return {
        "command_returncode": read_exit("analyze_live_nq_yfinance_agent"),
        "decision_summary": data.get("decision_summary"),
        "direction": data.get("direction"),
        "pre_bayes_gate": data.get("pre_bayes_gate"),
        "execution_gate": triage.get("gate_status"),
        "next_step": data.get("next_step", {}),
    }


def parse_pre_bayes() -> dict[str, Any]:
    data = command_json("pre_bayes_status_nq")
    return {
        "latest_gate_status": data.get("latest_gate_status"),
        "latest_canonical_structural_active_regime": data.get(
            "latest_canonical_structural_active_regime"
        ),
        "latest_canonical_structural_confidence": data.get(
            "latest_canonical_structural_confidence"
        ),
    }


def parse_workflow() -> dict[str, Any]:
    data = command_json("workflow_status_nq_agent")
    branch = data.get("closed_loop_branch_admission") or {}
    return {
        "blocking_status": data.get("blocking_status"),
        "blocking_reason": data.get("blocking_reason"),
        "ensemble_final_action": (data.get("ensemble") or {}).get("final_action"),
        "branch_status": branch.get("status"),
        "branch_actionable": branch.get("actionable"),
    }


def parse_path_ranking() -> dict[str, Any]:
    data = command_json("export_structural_path_ranking_target_nq")
    return {
        "rows": data.get("rows"),
        "mature_rows": data.get("mature_rows"),
        "rows_with_calibrated_path_prob": data.get("rows_with_calibrated_path_prob"),
        "rows_with_raw_path_score": data.get("rows_with_raw_path_score"),
        "summary_line": data.get("summary_line"),
    }


def read_exit(key: str) -> int | str | None:
    path = OUT / f"{key}.exit"
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8").strip()
    try:
        return int(raw)
    except ValueError:
        return raw


def write_candidates(candidates: list[dict[str, Any]]) -> str:
    path = PACKET / "source_control_candidate_scan_after_065506_v1.csv"
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["path", "size_bytes", "mtime_epoch", "decision"],
        )
        writer.writeheader()
        writer.writerows(candidates)
    return str(path.relative_to(REPO))


def write_root_csv(roots: list[dict[str, Any]]) -> str:
    path = PACKET / "required_root_status_after_065506_v1.csv"
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "id",
                "root",
                "root_exists",
                "physical_complete",
                "accepted_for_promotion",
                "row_count",
                "labels",
                "provenance_run_id",
                "notes",
            ],
        )
        writer.writeheader()
        for root in roots:
            row = {
                "id": root.get("id"),
                "root": root.get("root"),
                "root_exists": root.get("root_exists"),
                "physical_complete": root.get("physical_complete"),
                "accepted_for_promotion": root.get("accepted_for_promotion"),
                "row_count": root.get("row_count", ""),
                "labels": ";".join(root.get("labels") or []),
                "provenance_run_id": root.get("provenance_run_id", ""),
                "notes": root.get("notes", ""),
            }
            writer.writerow(row)
    return str(path.relative_to(REPO))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    PACKET.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    commands = [
        run_cmd("board_sha256_before", ["shasum", "-a", "256", str(BOARD.relative_to(REPO))]),
        run_cmd("provider_status_agent", ["target/debug/ict-engine", "provider-status", "--agent"]),
        run_cmd(
            "auto_quant_status_after_065506",
            [
                "target/debug/ict-engine",
                "auto-quant-status",
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
        ),
        run_cmd(
            "analyze_live_nq_yfinance_agent",
            [
                "target/debug/ict-engine",
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
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "agent",
            ],
            timeout=180,
        ),
        run_cmd(
            "pre_bayes_status_nq",
            [
                "target/debug/ict-engine",
                "pre-bayes-status",
                "--symbol",
                "NQ",
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--output-format",
                "json",
            ],
        ),
        run_cmd(
            "policy_training_status_nq",
            [
                "target/debug/ict-engine",
                "policy-training-status",
                "--symbol",
                "NQ",
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
        ),
        run_cmd(
            "workflow_status_nq_agent",
            [
                "target/debug/ict-engine",
                "workflow-status",
                "--symbol",
                "NQ",
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--agent",
            ],
        ),
        run_cmd(
            "export_structural_path_ranking_target_nq",
            [
                "target/debug/ict-engine",
                "export-structural-path-ranking-target",
                "--symbol",
                "NQ",
                "--state-dir",
                str(STATE_DIR),
            ],
        ),
    ]

    roots = source_roots()
    candidates = bounded_candidates()
    candidate_csv = write_candidates(candidates)
    root_csv = write_root_csv(roots)
    valid_required_root_unlock = any(
        root.get("id") in {"r6_owner_export", "r3_native_subhour", "r5_recency_extension"}
        and root.get("accepted_for_promotion")
        for root in roots
    )
    new_owner_control_candidates = [
        item for item in candidates if item["decision"].startswith("target_r6_root")
    ]
    auto_quant = parse_auto_quant()
    provider = parse_provider()
    analyze = parse_analyze()
    pre_bayes = parse_pre_bayes()
    workflow = parse_workflow()
    path_ranking = parse_path_ranking()

    summary = {
        "run_id": RUN_ID,
        "generated_at_epoch": int(time.time()),
        "gate_result": GATE,
        "board_sha256_before_artifact": (
            (OUT / "board_sha256_before.stdout").read_text(encoding="utf-8").split()[0]
            if (OUT / "board_sha256_before.stdout").exists()
            else ""
        ),
        "commands": commands,
        "required_roots": roots,
        "bounded_local_arrival_scan": {
            "candidate_count": len(candidates),
            "candidate_csv": candidate_csv,
            "new_owner_control_arrival_candidates": len(new_owner_control_candidates),
        },
        "runtime_readback": {
            "provider": provider,
            "auto_quant": auto_quant,
            "analyze_live": analyze,
            "pre_bayes": pre_bayes,
            "workflow": workflow,
            "path_ranking": path_ranking,
        },
        "accounting": {
            "accepted_rows_added": 0,
            "valid_required_root_unlock": valid_required_root_unlock,
            "source_control_evidence_acquired": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "decision": (
            "Auto-Quant is dependency/data ready in the isolated runtime state after "
            "065506, but the required Board A source/control roots remain blocked: "
            "R6 owner-export controls are absent, R5 post-cutoff recency root is "
            "absent, and R3 remains TSIE-derived/quarantined without Crisis."
        ),
        "next_action": (
            "Continue only from explicit source/control approval, verifier-native "
            "R6 owner-export rows with controls, source-owned post-2026-01-30 R5 "
            "recency rows, verifier-native Crisis-capable R3 MainRegimeV2 labels, "
            "or a genuinely new accepted cross-timeframe MainRegimeV2 source export."
        ),
        "artifacts": {
            "json": str((PACKET / "source_control_provider_refresh_after_065506_v1.json").relative_to(REPO)),
            "report": str((PACKET / "source_control_provider_refresh_after_065506_v1.md").relative_to(REPO)),
            "required_root_csv": root_csv,
            "candidate_csv": candidate_csv,
            "assertions": str((CHECKS / "source_control_provider_refresh_after_065506_v1_assertions.out").relative_to(REPO)),
        },
    }

    json_path = PACKET / "source_control_provider_refresh_after_065506_v1.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report_lines = [
        "# Source Control Provider Refresh After 065506 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE}`",
        "",
        "## Scope",
        "",
        "Read-only Board A refresh after the `065506` Auto-Quant local-cache seed. This run captures provider, Auto-Quant, analyze-live, Pre-Bayes, workflow, and path-ranking status, plus current source/control root presence. It does not mutate R3/R5/R6 target roots, approve controls, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.",
        "",
        "## Source/Control Readback",
        "",
        f"- R6 owner/export root exists: `{str(R6_ROOT.exists()).lower()}`.",
        f"- R5 recency root exists: `{str(R5_ROOT.exists()).lower()}`.",
        f"- R3 native-subhour root exists: `{str(R3_ROOT.exists()).lower()}` but remains TSIE-derived/quarantined and lacks `Crisis`.",
        f"- Bounded local candidates scanned: `{len(candidates)}`; target R6 arrival candidates: `{len(new_owner_control_candidates)}`.",
        "",
        "## Runtime Readback",
        "",
        f"- Provider summary: `{provider.get('summary_line')}`.",
        f"- Auto-Quant status: `{auto_quant.get('status')}`, healthy `{str(bool(auto_quant.get('healthy'))).lower()}`, data_ready `{str(bool(auto_quant.get('data_ready'))).lower()}`.",
        f"- analyze-live: rc `{analyze.get('command_returncode')}`, decision `{analyze.get('decision_summary')}`, pre-Bayes `{analyze.get('pre_bayes_gate')}`, execution `{analyze.get('execution_gate')}`.",
        f"- Pre-Bayes latest gate: `{pre_bayes.get('latest_gate_status')}`.",
        f"- Workflow: `{workflow.get('blocking_status')}` / `{workflow.get('blocking_reason')}`.",
        f"- Path-ranking: rows `{path_ranking.get('rows')}`, mature rows `{path_ranking.get('mature_rows')}`, calibrated rows `{path_ranking.get('rows_with_calibrated_path_prob')}`.",
        "",
        "## Accounting",
        "",
        "- Accepted rows added: `0`.",
        "- Valid required-root unlock: `false`.",
        "- Source/control evidence acquired: `false`.",
        "- Canonical merge: `false`.",
        "- Downstream promotion rerun: `false`.",
        "- Strict full objective: `false`.",
        "- Trade usable: `false`.",
        "- `update_goal=false`.",
        "",
        "## Decision",
        "",
        summary["decision"],
        "",
        "## Next",
        "",
        summary["next_action"],
        "",
        "## Artifacts",
        "",
        f"- JSON: `{summary['artifacts']['json']}`",
        f"- Required-root CSV: `{root_csv}`",
        f"- Candidate CSV: `{candidate_csv}`",
        f"- Assertions: `{summary['artifacts']['assertions']}`",
        "- Command output: `docs/experiments/actionable-regime-confidence/runs/20260512T065822+0800-codex-source-control-provider-refresh-after-065506-v1/command-output/`",
        "",
    ]
    (PACKET / "source_control_provider_refresh_after_065506_v1.md").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )

    assertions = [
        f"gate_result={GATE}",
        f"provider_status_called={str(read_exit('provider_status_agent') == 0).lower()}",
        f"auto_quant_status_called={str(read_exit('auto_quant_status_after_065506') == 0).lower()}",
        f"auto_quant_data_ready={str(bool(auto_quant.get('data_ready'))).lower()}",
        f"analyze_live_called={str(read_exit('analyze_live_nq_yfinance_agent') == 0).lower()}",
        f"pre_bayes_status_called={str(read_exit('pre_bayes_status_nq') == 0).lower()}",
        f"policy_training_status_called={str(read_exit('policy_training_status_nq') == 0).lower()}",
        f"workflow_status_called={str(read_exit('workflow_status_nq_agent') == 0).lower()}",
        f"path_ranking_export_called={str(read_exit('export_structural_path_ranking_target_nq') == 0).lower()}",
        "accepted_rows_added=0",
        f"valid_required_root_unlock={str(valid_required_root_unlock).lower()}",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
        "",
    ]
    (CHECKS / "source_control_provider_refresh_after_065506_v1_assertions.out").write_text(
        "\n".join(assertions), encoding="utf-8"
    )

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
