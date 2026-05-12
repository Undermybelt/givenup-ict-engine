#!/usr/bin/env python3
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T033524-codex-autoquant-noaiodns-prepare-workaround-after-033216-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "autoquant-noaiodns-prepare-workaround-after-033216-v1"
CHECKS = RUN_ROOT / "checks"
COMMAND = RUN_ROOT / "command-output"


def read_text(path):
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def read_int(path):
    text = read_text(path).strip()
    return int(text) if text else None


def read_json(path):
    return json.loads(read_text(path)) if path.exists() else {}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    uninstall_exit = read_int(COMMAND / "uv_pip_uninstall_aiodns.exitcode")
    import_exit = read_int(COMMAND / "noaiodns_import_check.exitcode")
    prepare_exit = read_int(COMMAND / "auto_quant_prepare_noaiodns.exitcode")
    status_exit = read_int(COMMAND / "auto_quant_status_noaiodns_after_prepare.exitcode")
    prepare = read_json(COMMAND / "auto_quant_prepare_noaiodns.stdout.txt")
    status_after = read_json(COMMAND / "auto_quant_status_noaiodns_after_prepare.stdout.json")
    import_stdout = read_text(COMMAND / "noaiodns_import_check.stdout.txt")
    uninstall_stderr = read_text(COMMAND / "uv_pip_uninstall_aiodns.stderr.txt")

    gate = "autoquant_noaiodns_prepare_workaround_after_033216_v1=prepare_succeeded_but_noaiodns_uninstall_failed_state_already_data_ready_no_promotion"
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": gate,
        "objective_mapping": "Settle the no-aiodns Auto-Quant prepare workaround attempt after 033216.",
        "inputs": {
            "uninstall_exit": str((COMMAND / "uv_pip_uninstall_aiodns.exitcode").relative_to(REPO)),
            "import_check": str((COMMAND / "noaiodns_import_check.stdout.txt").relative_to(REPO)),
            "prepare_stdout": str((COMMAND / "auto_quant_prepare_noaiodns.stdout.txt").relative_to(REPO)),
            "status_after": str((COMMAND / "auto_quant_status_noaiodns_after_prepare.stdout.json").relative_to(REPO)),
        },
        "command": {
            "uv_pip_uninstall_aiodns_exit_code": uninstall_exit,
            "uv_pip_uninstall_aiodns_error": "unexpected argument '-y'" in uninstall_stderr,
            "aiodns_still_importable": "aiodns_present True" in import_stdout,
            "import_check_exit_code": import_exit,
            "auto_quant_prepare_exit_code": prepare_exit,
            "auto_quant_status_after_exit_code": status_exit,
        },
        "prepare": {
            "status": prepare.get("status"),
            "data_ready": prepare.get("data_ready"),
            "dependency_status_before": prepare.get("dependency_status_before"),
            "dependency_status_after": prepare.get("dependency_status_after"),
        },
        "status_after": {
            "status": status_after.get("status"),
            "healthy": status_after.get("healthy"),
            "dependency_healthy": status_after.get("dependency_healthy"),
            "data_ready": status_after.get("data_ready"),
            "blocked_reason": status_after.get("blocked_reason"),
        },
        "promotion": {
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "canonical_merge_allowed": False,
            "downstream_promotion_rerun_allowed": False,
            "strict_full_objective_achieved": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "non_mutations": {
            "runtime_code_changed": False,
            "source_roots_mutated": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
        },
        "decision": "The no-aiodns uninstall did not actually remove aiodns, but the prepare command exited 0 because the isolated Auto-Quant state was already data-ready/dependency_ready_seed_required. This is runtime-readiness corroboration only, not Board A acceptance.",
        "next_action": "Continue Board A only from source/control unlock. Auto-Quant runtime follow-up may seed active strategies in isolated state, but cannot promote without verifier rerun and downstream chain.",
    }

    json_path = OUT / "autoquant_noaiodns_prepare_workaround_after_033216_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    csv_path = OUT / "autoquant_noaiodns_prepare_workaround_after_033216_v1.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["field", "value"])
        writer.writerow(["gate_result", gate])
        writer.writerow(["uninstall_exit_code", uninstall_exit])
        writer.writerow(["aiodns_still_importable", result["command"]["aiodns_still_importable"]])
        writer.writerow(["prepare_exit_code", prepare_exit])
        writer.writerow(["status_after", result["status_after"]["status"]])
        writer.writerow(["data_ready", result["status_after"]["data_ready"]])
        writer.writerow(["update_goal", False])

    md = [
        "# AutoQuant No-AioDNS Prepare Workaround After 033216 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{gate}`",
        "",
        "## Readback",
        "",
        f"- `uv pip uninstall aiodns -y` exit code: `{uninstall_exit}`; error was the unsupported `-y` argument.",
        f"- Import check exit code: `{import_exit}`; `aiodns` still importable: `{str(result['command']['aiodns_still_importable']).lower()}`.",
        f"- `auto-quant-prepare` exit code: `{prepare_exit}`; prepare status `{prepare.get('status')}`; data ready `{prepare.get('data_ready')}`.",
        f"- Status after exit code: `{status_exit}`; status `{status_after.get('status')}`; healthy `{status_after.get('healthy')}`; data ready `{status_after.get('data_ready')}`.",
        "",
        "## Decision",
        "",
        result["decision"],
        "",
        "- Accepted rows added: `0`",
        "- New confidence gate: `false`",
        "- Canonical merge allowed: `false`",
        "- Downstream promotion rerun allowed: `false`",
        "- Strict full objective achieved: `false`",
        "- Trade usable: `false`",
        "- `update_goal=false`",
        "",
        "## Next",
        "",
        result["next_action"],
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- CSV: `{csv_path.relative_to(REPO)}`",
    ]
    md_path = OUT / "autoquant_noaiodns_prepare_workaround_after_033216_v1.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    assertions = [
        ("gate_result", result["gate_result"] == gate),
        ("uninstall_exit_code_2", uninstall_exit == 2),
        ("aiodns_still_importable_true", result["command"]["aiodns_still_importable"] is True),
        ("prepare_exit_code_0", prepare_exit == 0),
        ("status_after_exit_code_0", status_exit == 0),
        ("status_after_data_ready_true", result["status_after"]["data_ready"] is True),
        ("status_after_dependency_ready_seed_required", result["status_after"]["status"] == "dependency_ready_seed_required"),
        ("accepted_rows_added_0", result["promotion"]["accepted_rows_added"] == 0),
        ("canonical_merge_allowed_false", result["promotion"]["canonical_merge_allowed"] is False),
        ("downstream_promotion_rerun_allowed_false", result["promotion"]["downstream_promotion_rerun_allowed"] is False),
        ("strict_full_objective_false", result["promotion"]["strict_full_objective_achieved"] is False),
        ("trade_usable_false", result["promotion"]["trade_usable"] is False),
        ("update_goal_false", result["promotion"]["update_goal"] is False),
        ("runtime_code_changed_false", result["non_mutations"]["runtime_code_changed"] is False),
        ("source_roots_mutated_false", result["non_mutations"]["source_roots_mutated"] is False),
        ("thresholds_relaxed_false", result["non_mutations"]["thresholds_relaxed"] is False),
        ("raw_data_committed_false", result["non_mutations"]["raw_data_committed"] is False),
    ]
    failures = []
    lines = []
    for name, ok in assertions:
        lines.append(f"{'PASS' if ok else 'FAIL'} {name}={str(ok).lower()}")
        if not ok:
            failures.append(name)
    assertion_path = CHECKS / "autoquant_noaiodns_prepare_workaround_after_033216_v1_assertions.out"
    assertion_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("assertions failed: " + ",".join(failures))


if __name__ == "__main__":
    main()
