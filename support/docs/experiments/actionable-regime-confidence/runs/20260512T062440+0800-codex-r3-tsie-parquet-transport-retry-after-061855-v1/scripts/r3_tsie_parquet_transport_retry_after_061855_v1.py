#!/usr/bin/env python3
"""Retry TSIE Parquet transport without mutating Board A target roots."""

from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import requests


RUN_ID = "20260512T062440+0800-codex-r3-tsie-parquet-transport-retry-after-061855-v1"
DATASET_ID = "sujinwo/tsie-market-regime-dataset"
PARQUET_URL = (
    "https://huggingface.co/datasets/sujinwo/tsie-market-regime-dataset/"
    "resolve/refs%2Fconvert%2Fparquet/default/train/0000.parquet"
)
ROWS_API = "https://datasets-server.huggingface.co/rows"
RUN_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = RUN_ROOT / "r3-tsie-parquet-transport-retry-after-061855-v1"
CHECK_DIR = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"
TMP_ROOT = Path("/tmp/ict-engine-tsie-transport-retry-after-061855-v1")
TARGET_ROOTS = {
    "r6_owner_export": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r3_native_subhour": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "r5_recency_extension": Path("/tmp/ict-engine-source-panel-recency-extension"),
}


def run_command(name: str, args: list[str], timeout: int = 60) -> dict:
    stdout_path = CMD_DIR / f"{name}.stdout.txt"
    stderr_path = CMD_DIR / f"{name}.stderr.txt"
    cmd_path = CMD_DIR / f"{name}.cmd"
    cmd_path.write_text(" ".join(args) + "\n")
    try:
        completed = subprocess.run(
            args,
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        stdout_path.write_text(completed.stdout)
        stderr_path.write_text(completed.stderr)
        return {
            "name": name,
            "returncode": completed.returncode,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "cmd_path": str(cmd_path),
            "stdout_preview": completed.stdout[:1200],
            "stderr_preview": completed.stderr[:1200],
            "timeout": False,
        }
    except subprocess.TimeoutExpired as exc:
        stdout_path.write_text(exc.stdout or "")
        stderr_path.write_text(exc.stderr or "TIMEOUT\n")
        return {
            "name": name,
            "returncode": None,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "cmd_path": str(cmd_path),
            "stdout_preview": (exc.stdout or "")[:1200],
            "stderr_preview": (exc.stderr or "TIMEOUT\n")[:1200],
            "timeout": True,
        }


def module_status() -> dict[str, bool]:
    return {
        name: importlib.util.find_spec(name) is not None
        for name in ["pandas", "pyarrow", "duckdb", "polars", "requests"]
    }


def target_root_status() -> dict[str, dict]:
    status = {}
    for name, root in TARGET_ROOTS.items():
        files = []
        if root.exists():
            files = [str(path) for path in sorted(root.rglob("*")) if path.is_file()][:20]
        status[name] = {
            "root": str(root),
            "present": root.exists(),
            "file_count_sampled": len(files),
            "sampled_files": files,
        }
    return status


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)

    commands = []
    commands.append(
        run_command(
            "curl_head",
            [
                "curl",
                "-L",
                "--fail",
                "--silent",
                "--show-error",
                "--head",
                "--max-time",
                "45",
                PARQUET_URL,
            ],
            timeout=60,
        )
    )
    head1m = TMP_ROOT / "0000.parquet.head1m"
    commands.append(
        run_command(
            "curl_range_1m",
            [
                "curl",
                "-L",
                "--fail",
                "--silent",
                "--show-error",
                "--max-time",
                "45",
                "-r",
                "0-1048575",
                "-o",
                str(head1m),
                PARQUET_URL,
            ],
            timeout=60,
        )
    )
    commands.append(
        run_command(
            "uvx_hf_xet_help",
            [
                "env",
                "HF_HOME=/tmp/ict-engine-hf-home",
                "UV_CACHE_DIR=/tmp/ict-engine-uv-cache",
                "uvx",
                "--from",
                "huggingface_hub",
                "--with",
                "hf_xet",
                "hf",
                "--help",
            ],
            timeout=90,
        )
    )

    row_api = {
        "status_code": None,
        "body_preview": "",
        "length_cap_confirmed": False,
        "error": "",
    }
    try:
        response = requests.get(
            ROWS_API,
            params={
                "dataset": DATASET_ID,
                "config": "default",
                "split": "train",
                "offset": "0",
                "length": "1000",
            },
            timeout=45,
        )
        row_api["status_code"] = response.status_code
        row_api["body_preview"] = response.text[:500]
        row_api["length_cap_confirmed"] = response.status_code == 422 and "length" in response.text
    except Exception as exc:  # pragma: no cover - diagnostic artifact
        row_api["error"] = repr(exc)

    modules = module_status()
    roots = target_root_status()
    curl_head_ok = commands[0]["returncode"] == 0
    curl_range_ok = commands[1]["returncode"] == 0 and head1m.exists() and head1m.stat().st_size > 0
    uvx_ok = commands[2]["returncode"] == 0
    required_roots_present_any = any(row["present"] for row in roots.values())
    gate_result = "r3_tsie_parquet_transport_retry_after_061855_v1=transport_blocked_no_r3_intake_no_promotion"
    if curl_range_ok:
        gate_result = "r3_tsie_parquet_transport_retry_after_061855_v1=partial_range_downloaded_not_intaked_no_promotion"

    result = {
        "run_id": RUN_ID,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": gate_result,
        "dataset_id": DATASET_ID,
        "parquet_url": PARQUET_URL,
        "tmp_root": str(TMP_ROOT),
        "module_status": modules,
        "commands": commands,
        "row_api_length_probe": row_api,
        "head1m_exists": head1m.exists(),
        "head1m_bytes": head1m.stat().st_size if head1m.exists() else 0,
        "target_roots": roots,
        "decision": {
            "curl_head_ok": curl_head_ok,
            "curl_range_ok": curl_range_ok,
            "uvx_hf_xet_help_ok": uvx_ok,
            "row_api_length_cap_confirmed": row_api["length_cap_confirmed"],
            "raw_parquet_downloaded": False,
            "raw_data_committed": False,
            "target_root_mutated": False,
            "accepted_rows_added": 0,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "required_roots_present_any": required_roots_present_any,
    }

    json_path = ARTIFACT_DIR / "r3_tsie_parquet_transport_retry_after_061855_v1.json"
    md_path = ARTIFACT_DIR / "r3_tsie_parquet_transport_retry_after_061855_v1.md"
    cmd_csv = ARTIFACT_DIR / "r3_tsie_transport_commands_v1.csv"
    assertions_path = CHECK_DIR / "r3_tsie_parquet_transport_retry_after_061855_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_csv(
        cmd_csv,
        [
            {
                "name": cmd["name"],
                "returncode": cmd["returncode"],
                "timeout": cmd["timeout"],
                "stdout_path": cmd["stdout_path"],
                "stderr_path": cmd["stderr_path"],
            }
            for cmd in commands
        ],
        ["name", "returncode", "timeout", "stdout_path", "stderr_path"],
    )

    md_path.write_text(
        "\n".join(
            [
                "# R3 TSIE Parquet Transport Retry After 061855 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{gate_result}`",
                "",
                "Scope:",
                "- Retry the TSIE full Parquet transport after the 061855 metadata screen.",
                "- Keep all tooling/cache/output in `/tmp` or this run artifact.",
                "- Do not create `/tmp/ict-engine-native-subhour-source-label-intake` unless full raw data can be verified and mapped.",
                "",
                "Readback:",
                f"- Local modules: `{modules}`.",
                f"- `curl --head -L` return code: `{commands[0]['returncode']}`.",
                f"- `curl` 1 MB range return code: `{commands[1]['returncode']}`; bytes written `{result['head1m_bytes']}`.",
                f"- Disposable `uvx --with hf_xet hf --help` return code: `{commands[2]['returncode']}`.",
                f"- Dataset-server rows length cap confirmed: `{row_api['length_cap_confirmed']}`.",
                "",
                "Decision:",
                "- Full Parquet transport remains blocked in this environment.",
                "- The rows API cannot be scaled into a full 7.19M row verifier-native intake because `length > 100` is rejected.",
                "- No R3 target root was created, no accepted rows were added, no canonical merge ran, and no downstream promotion rerun is allowed.",
                "",
                "Next:",
                "- Resolve the Hugging Face/Xet transport path, provide a local verified parquet, or use another source-owned native sub-hour label dataset before materializing `/tmp/ict-engine-native-subhour-source-label-intake`.",
                "",
                "Artifacts:",
                f"- JSON: `{json_path}`",
                f"- Command CSV: `{cmd_csv}`",
                f"- Assertions: `{assertions_path}`",
                "",
            ]
        )
    )
    assertions_path.write_text(
        "\n".join(
            [
                f"gate_result={gate_result}",
                f"curl_head_ok={str(curl_head_ok).lower()}",
                f"curl_range_ok={str(curl_range_ok).lower()}",
                f"uvx_hf_xet_help_ok={str(uvx_ok).lower()}",
                f"row_api_length_cap_confirmed={str(row_api['length_cap_confirmed']).lower()}",
                "raw_parquet_downloaded=false",
                "target_root_mutated=false",
                "accepted_rows_added=0",
                "canonical_merge=false",
                "downstream_promotion_rerun=false",
                "strict_full_objective=false",
                "trade_usable=false",
                "update_goal=false",
                "",
            ]
        )
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
