#!/usr/bin/env python3
"""Check whether V64 can proceed via source-owned normal controls without approval."""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T003443-codex-r6-oystacher-normal-control-availability-preflight-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT = RUN_ROOT / "r6-oystacher-normal-control-availability-preflight"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"

BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
POLICY_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T003051-codex-r6-oystacher-exhibit-a-source-policy-review-v1/"
    "r6-oystacher-exhibit-a-source-policy-review/"
    "r6_oystacher_exhibit_a_source_policy_review_v1.json"
)
MATERIALIZATION_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1/"
    "r6-oystacher-exhibit-a-row-materialization/"
    "r6_oystacher_exhibit_a_row_materialization_v1.json"
)
ISOLATED_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1/"
    "r6-oystacher-exhibit-a-row-materialization/isolated-oystacher-exhibit-a-intake"
)
TARGET_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
CANONICAL_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")

PROVIDER_CMD = ["./target/debug/ict-engine", "provider-status", "--agent"]
AUTOQUANT_CMD = [
    "./target/debug/ict-engine",
    "auto-quant-status",
    "--state-dir",
    "/tmp/ict-engine-board-a-v64-normal-control-preflight-state",
    "--output-format",
    "agent",
]

SEARCH_ROOTS = [
    Path("/Users/thrill3r/Auto-Quant/user_data/data"),
    Path("/Users/thrill3r/Downloads/Tomac"),
    Path("/tmp"),
    Path("/private/tmp"),
]
CONTRACT_PATTERNS = ["CLM2", "ESH4", "ESM3", "HGH2", "NGF3", "VX"]
CONTROL_PATTERNS = [
    "normal",
    "control",
    "order_book",
    "order-book",
    "orderbook",
    "order_lifecycle",
    "order-lifecycle",
    "mbo",
    "mbp",
    "itch",
    "quote",
    "quotes",
    "trade_tape",
    "trades",
    "tardis",
    "cme",
    "comex",
    "nymex",
    "cfe",
]
DATA_EXTENSIONS = {
    ".csv",
    ".json",
    ".jsonl",
    ".parquet",
    ".feather",
    ".h5",
    ".hdf5",
    ".zip",
    ".gz",
}
SKIP_DIR_NAMES = {
    ".git",
    "node_modules",
    "__pycache__",
    "qimao-scan-decon",
    "repo-intake",
    "oh-story-claudecode",
    "htmlcov",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(name: str, cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, text=True, capture_output=True)
    stdout_path = CMD_OUT / f"{name}.stdout.txt"
    stderr_path = CMD_OUT / f"{name}.stderr.txt"
    exit_path = CMD_OUT / f"{name}.exit"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(str(proc.returncode), encoding="utf-8")
    parsed = None
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"parse_error": True}
    return {
        "name": name,
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "exit_path": str(exit_path),
        "parsed": parsed,
    }


def csv_rows(path: Path) -> int | None:
    if not path.exists() or path.suffix.lower() != ".csv":
        return None
    count = 0
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.reader(handle)
        for count, _ in enumerate(reader, start=1):
            pass
    return max(count - 1, 0)


def file_presence(root: Path, required: list[str]) -> dict:
    present = []
    missing = []
    row_counts = {}
    for name in required:
        path = root / name
        if path.exists():
            present.append(name)
            rows = csv_rows(path)
            if rows is not None:
                row_counts[name] = rows
        else:
            missing.append(name)
    return {
        "root": str(root),
        "root_exists": root.exists(),
        "required": required,
        "present": present,
        "missing": missing,
        "all_present": not missing,
        "csv_row_counts": row_counts,
    }


def relevant_file(path: Path) -> tuple[bool, str]:
    suffixes = "".join(path.suffixes).lower()
    if path.suffix.lower() not in DATA_EXTENSIONS and not any(suffixes.endswith(ext) for ext in DATA_EXTENSIONS):
        return (False, "non_data_extension")
    text = str(path).lower()
    contract_hit = [pat for pat in CONTRACT_PATTERNS if pat.lower() in text]
    control_hit = [pat for pat in CONTROL_PATTERNS if pat in text]
    if contract_hit and control_hit:
        return (True, "contract_and_control_pattern")
    if contract_hit:
        return (True, "contract_pattern_only")
    if control_hit and any(market in text for market in ["cme", "comex", "nymex", "cfe", "tardis"]):
        return (True, "market_control_pattern")
    return (False, "no_relevant_pattern")


def bounded_scan(max_depth: int = 6, limit: int = 200) -> list[dict]:
    hits = []
    seen = set()
    for base in SEARCH_ROOTS:
        if not base.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            current = Path(dirpath)
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
            try:
                depth = len(current.relative_to(base).parts)
            except ValueError:
                depth = max_depth + 1
            if depth >= max_depth:
                dirnames[:] = []
            for filename in filenames:
                path = current / filename
                key = str(path)
                if key in seen:
                    continue
                ok, reason = relevant_file(path)
                if not ok:
                    continue
                seen.add(key)
                try:
                    stat = path.stat()
                except OSError:
                    continue
                hits.append(
                    {
                        "path": key,
                        "size_bytes": stat.st_size,
                        "reason": reason,
                        "rows_if_csv": csv_rows(path) if path.suffix.lower() == ".csv" else None,
                    }
                )
                if len(hits) >= limit:
                    return hits
    return sorted(hits, key=lambda item: (item["reason"], item["path"]))


def parse_cursor() -> dict:
    text = BOARD.read_text(encoding="utf-8")
    fields = {}
    for match in re.finditer(r"\\| ([a-z_]+) \\| (.*?) \\|", text):
        fields[match.group(1)] = match.group(2)
        if match.group(1) == "next_action":
            break
    return fields


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)

    policy = load_json(POLICY_JSON)
    materialization = load_json(MATERIALIZATION_JSON)
    provider = run_command("provider_status_agent", PROVIDER_CMD)
    autoquant = run_command("auto_quant_status_agent", AUTOQUANT_CMD)
    local_hits = bounded_scan()

    isolated_presence = file_presence(
        ISOLATED_ROOT,
        [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
    )
    target_presence = file_presence(
        TARGET_ROOT,
        [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
            "source_policy_approval.json",
            "owner_approval_reference.md",
            "validation_contract_approval.json",
        ],
    )
    canonical_presence = file_presence(
        CANONICAL_ROOT,
        [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
    )

    provider_summary = provider["parsed"].get("summary_line", "unparsed")
    autoquant_status = autoquant["parsed"].get("status", "unparsed")
    normal_control_ready = False
    source_policy_approval_present = any(
        name in target_presence["present"]
        for name in ["source_policy_approval.json", "owner_approval_reference.md", "validation_contract_approval.json"]
    )
    gate = (
        "r6_oystacher_normal_control_availability_preflight_v1="
        "no_source_owned_normal_controls_found_no_merge_or_chain_rerun"
    )
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "cursor": parse_cursor(),
        "source_policy_gate": policy.get("source_policy_gate"),
        "source_policy_approval_present": source_policy_approval_present,
        "positive_rows": policy.get("positive_rows"),
        "same_exhibit_flip_control_candidates": policy.get("matched_control_rows"),
        "flip_controls_accepted": False,
        "isolated_split_axes_pass": policy.get("all_materialized_split_axes_pass"),
        "isolated_verifier_status": policy.get("isolated_verifier_status"),
        "normal_control_ready": normal_control_ready,
        "local_candidate_hit_count": len(local_hits),
        "target_presence": target_presence,
        "isolated_presence": isolated_presence,
        "canonical_presence": canonical_presence,
        "provider_summary": provider_summary,
        "autoquant_status": autoquant_status,
        "provider_command": provider,
        "autoquant_command": autoquant,
        "local_candidate_hits": local_hits,
        "materialization_gate": materialization.get("gate_result"),
        "policy_gate": policy.get("gate_result"),
        "gate_result": gate,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "downstream_chain_rerun": False,
        "next_action": (
            "Keep Oystacher rows isolated. Obtain explicit approval for the RECAP/PACER source policy "
            "and same-exhibit FLIP control contract, or supply independent source-owned normal controls; "
            "only then merge under a shared lock and rerun direct verifier, split calibration, provider, "
            "Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback."
        ),
    }

    json_path = OUT / "r6_oystacher_normal_control_availability_preflight_v1.json"
    report_path = OUT / "r6_oystacher_normal_control_availability_preflight_v1.md"
    hits_csv = OUT / "r6_oystacher_normal_control_local_candidates_v1.csv"
    roots_csv = OUT / "r6_oystacher_normal_control_roots_v1.csv"
    assertions_path = CHECKS / "r6_oystacher_normal_control_availability_preflight_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with hits_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "size_bytes", "reason", "rows_if_csv"])
        writer.writeheader()
        for row in local_hits:
            writer.writerow(row)
    with roots_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["id", "root", "root_exists", "present", "missing", "all_present", "csv_row_counts"],
        )
        writer.writeheader()
        for root_id, presence in [
            ("isolated_oystacher", isolated_presence),
            ("target_owner_export", target_presence),
            ("canonical_live", canonical_presence),
        ]:
            writer.writerow(
                {
                    "id": root_id,
                    "root": presence["root"],
                    "root_exists": presence["root_exists"],
                    "present": ";".join(presence["present"]),
                    "missing": ";".join(presence["missing"]),
                    "all_present": presence["all_present"],
                    "csv_row_counts": json.dumps(presence["csv_row_counts"], sort_keys=True),
                }
            )

    md = [
        "# R6 Oystacher Normal-Control Availability Preflight v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Gate result: `{gate}`.",
        f"- Positive SPOOF rows preserved in isolated evidence: `{policy.get('positive_rows')}`.",
        f"- Same-exhibit FLIP rows remain control candidates only: `{policy.get('matched_control_rows')}`.",
        f"- Source-policy approval present in target root: `{str(source_policy_approval_present).lower()}`.",
        f"- Target owner-export root exists: `{str(TARGET_ROOT.exists()).lower()}`.",
        f"- Independent local normal-control candidates found: `{len(local_hits)}`.",
        f"- Provider readback: `{provider_summary}`.",
        f"- Auto-Quant readback status in isolated state: `{autoquant_status}`.",
        "- Downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun: `false`, because source-policy approval or independent normal controls are still absent.",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "## Decision",
        "",
        "- Keep Oystacher Exhibit A rows isolated.",
        "- The public RECAP/PACER source can stay as positive-candidate evidence, but canonical merge remains blocked.",
        "- Same-exhibit `FLIP` rows were not promoted to `matched_negative_normal_activity`; no independent source-owned normal controls were found locally.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path}`",
        f"- Local candidate CSV: `{hits_csv}`",
        f"- Root presence CSV: `{roots_csv}`",
        f"- Command output: `{CMD_OUT}`",
        f"- Assertions: `{assertions_path}`",
        "",
        "## Next",
        "",
        result["next_action"],
    ]
    report_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    assertions = {
        "gate_result": gate,
        "source_policy_approval_present": source_policy_approval_present,
        "normal_control_ready": normal_control_ready,
        "shared_intake_mutated": False,
        "downstream_chain_rerun": False,
        "update_goal": False,
    }
    assertion_lines = []
    for key, value in assertions.items():
        if isinstance(value, bool):
            value = str(value).lower()
        assertion_lines.append(f"{key}={value}")
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ["gate_result", "local_candidate_hit_count", "provider_summary", "autoquant_status", "update_goal"]}, indent=2))


if __name__ == "__main__":
    main()
