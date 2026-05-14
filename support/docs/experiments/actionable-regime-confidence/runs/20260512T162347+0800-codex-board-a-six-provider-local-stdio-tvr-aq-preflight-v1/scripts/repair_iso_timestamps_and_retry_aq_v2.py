from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T162347+0800-codex-board-a-six-provider-local-stdio-tvr-aq-preflight-v1"
)
STATE_DIR = RUN_ROOT / "state_iso_v2"
SYMBOL_ID = "BOARD_A_6PROV_162347_ISO"
ICT_ENGINE = "./target/debug/ict-engine"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def run_cmd(label: str, args: list[str], timeout: int = 900) -> int:
    write_text(RUN_ROOT / f"command-output/{label}.cmd", " ".join(args) + "\n")
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        write_text(RUN_ROOT / f"command-output/{label}.out", proc.stdout)
        write_text(RUN_ROOT / f"command-output/{label}.err", proc.stderr)
        code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        write_text(RUN_ROOT / f"command-output/{label}.out", exc.stdout or "")
        write_text(
            RUN_ROOT / f"command-output/{label}.err",
            (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n",
        )
        code = 124
    write_text(RUN_ROOT / f"checks/{label}.exit", f"{code}\n")
    return code


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    original_materials = sorted((RUN_ROOT / "agent-material").glob("board-a-sixprov-*-v1.material.json"))
    repaired_rows = []
    repaired_materials = []
    failures = []
    for original in original_materials:
        package = json.loads(original.read_text())
        src = Path(package["data_path"])
        if not src.exists():
            failures.append(f"{original}: data_path missing: {src}")
            continue
        df = pd.read_csv(src)
        if "timestamp" not in df.columns:
            failures.append(f"{src}: missing timestamp column")
            continue
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        dst = src.with_name(src.stem + ".iso.csv")
        df.to_csv(dst, index=False)

        repaired = dict(package)
        repaired["package_id"] = package["package_id"] + "-iso-v2"
        repaired["title"] = package["title"] + " ISO timestamp retry"
        repaired["data_path"] = str(dst)
        repaired.setdefault("notes", []).append("data_path_repaired_for_ict_engine_loader=iso_utc_timestamp")
        repaired_path = original.with_name(original.stem + "-iso-v2.material.json")
        write_json(repaired_path, repaired)
        repaired_materials.append(repaired_path)
        repaired_rows.append(
            {
                "original_material": str(original),
                "repaired_material": str(repaired_path),
                "source_csv": str(src),
                "repaired_csv": str(dst),
                "rows": int(len(df)),
                "first": str(df["timestamp"].iloc[0]) if not df.empty else "",
                "last": str(df["timestamp"].iloc[-1]) if not df.empty else "",
            }
        )

    with (RUN_ROOT / "summaries/csv_timestamp_iso_repair_v2.csv").open("w", newline="") as fh:
        fieldnames = ["original_material", "repaired_material", "source_csv", "repaired_csv", "rows", "first", "last"]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(repaired_rows)
    write_text(
        RUN_ROOT / "summaries/material_paths_iso_v2.txt",
        "".join(str(path) + "\n" for path in repaired_materials),
    )

    material_args = []
    for path in repaired_materials:
        material_args.extend(["--material", str(path)])
    batch_exit = 2
    dispatch_exit = -1
    rank_exit = -1
    if len(repaired_materials) == 6 and not failures:
        batch_exit = run_cmd(
            "10_auto_quant_agent_material_batch_iso_v2",
            [
                ICT_ENGINE,
                "auto-quant-agent-material-batch",
                "--symbol",
                SYMBOL_ID,
                "--state-dir",
                str(STATE_DIR),
                "--max-parallel",
                "1",
                "--repo-url",
                "/Users/thrill3r/Auto-Quant",
            ]
            + material_args,
            timeout=420,
        )
        if batch_exit == 0:
            dispatch_exit = run_cmd(
                "11_auto_quant_agent_material_dispatch_iso_v2",
                [
                    ICT_ENGINE,
                    "auto-quant-agent-material-dispatch",
                    "--symbol",
                    SYMBOL_ID,
                    "--state-dir",
                    str(STATE_DIR),
                    "--group-indices",
                    "0,1,2,3,4,5",
                ],
                timeout=1200,
            )
            if dispatch_exit == 0:
                rank_exit = run_cmd(
                    "12_auto_quant_agent_material_rank_iso_v2",
                    [
                        ICT_ENGINE,
                        "auto-quant-agent-material-rank",
                        "--symbol",
                        SYMBOL_ID,
                        "--state-dir",
                        str(STATE_DIR),
                    ],
                    timeout=420,
                )

    final_summary = json.loads((RUN_ROOT / "summaries/final_preflight_summary_v1.json").read_text())
    material_by_provider = {
        "yfinance/YF": "board-a-sixprov-yf-spy-1h-v1-iso-v2.material.json",
        "Binance": "board-a-sixprov-binance-btcusdt-1h-v1-iso-v2.material.json",
        "Bybit": "board-a-sixprov-bybit-btcusdt-1h-v1-iso-v2.material.json",
        "Kraken": "board-a-sixprov-kraken-pfxbtusd-1h-v1-iso-v2.material.json",
        "IBKR": "board-a-sixprov-ibkr-spy-1h-v1-iso-v2.material.json",
        "TradingViewRemix/TVR": "board-a-sixprov-tvr-btc-usd-1h-v1-iso-v2.material.json",
    }
    for row in final_summary["provider_rows"]:
        expected = material_by_provider.get(row["provider"])
        row["aq_material_created"] = bool(expected and (RUN_ROOT / "agent-material" / expected).exists())
    final_summary.update(
        {
            "iso_timestamp_repair_v2": True,
            "repaired_material_paths": [str(path) for path in repaired_materials],
            "repair_failures": failures,
            "batch_exit_v2": batch_exit,
            "dispatch_exit_v2": dispatch_exit,
            "rank_exit_v2": rank_exit,
            "auto_quant_dispatch_completed": dispatch_exit == 0,
            "accepted_95_contexts_added": 0,
            "pre_bayes_bbn_catboost_execution_tree_ran": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
        }
    )
    write_json(RUN_ROOT / "summaries/final_preflight_summary_v2.json", final_summary)

    manifest_paths = [
        RUN_ROOT / "summaries/csv_timestamp_iso_repair_v2.csv",
        RUN_ROOT / "summaries/material_paths_iso_v2.txt",
        RUN_ROOT / "summaries/final_preflight_summary_v2.json",
    ] + repaired_materials
    write_text(
        RUN_ROOT / "checks/sha256_manifest_iso_v2.out",
        "".join(f"{sha256(path)}  {path}\n" for path in manifest_paths if path.exists()),
    )
    assertions = [
        ("materials_repaired_6", len(repaired_materials) == 6),
        ("repair_failures_empty", not failures),
        ("batch_exit_0", batch_exit == 0),
        ("dispatch_exit_0", dispatch_exit == 0),
        ("rank_exit_0", rank_exit == 0),
        ("promotion_allowed_false", not final_summary["promotion_allowed"]),
        ("trade_usable_false", not final_summary["trade_usable"]),
        ("update_goal_false", not final_summary["update_goal"]),
    ]
    write_text(
        RUN_ROOT / "checks/final_preflight_assertions_iso_v2.out",
        "\n".join(f"{'PASS' if ok else 'FAIL'} {name}" for name, ok in assertions) + "\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
