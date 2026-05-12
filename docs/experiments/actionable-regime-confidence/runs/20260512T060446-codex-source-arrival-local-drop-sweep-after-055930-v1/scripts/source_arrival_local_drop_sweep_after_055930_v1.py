#!/usr/bin/env python3
"""Read-only source arrival and local drop sweep after the 055930 audit."""

from __future__ import annotations

import csv
import hashlib
import json
import shlex
import subprocess
import time
from pathlib import Path


RUN_ID = "20260512T060446-codex-source-arrival-local-drop-sweep-after-055930-v1"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
RUN_ROOT = Path(__file__).resolve().parents[1]
CMD_DIR = RUN_ROOT / "command-output"
OUT_DIR = RUN_ROOT / "source-arrival-local-drop-sweep-after-055930-v1"
CHECK_DIR = RUN_ROOT / "checks"

TARGET_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]

KNOWN_SIDE_ROOTS = [
    Path("/private/tmp/20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1.staging"),
    Path("/private/tmp/ict-engine-direct-manipulation-row-intake"),
    Path("/private/tmp/ict-engine-r6-direct-intake-reconstruction-v55/intake"),
    Path("/private/tmp/ict-engine-r6-direct-intake-v56-clean-readback/intake"),
]

REQUIRED_TRIPLET = [
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
]

DOWNLOADS_REGIME_ROOT = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026")


def board_hash() -> str | None:
    if not BOARD.exists():
        return None
    return hashlib.sha256(BOARD.read_bytes()).hexdigest()


def run_cmd(key: str, command: list[str], timeout: int = 90) -> dict[str, object]:
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    (CMD_DIR / f"{key}.cmd").write_text(shlex.join(command) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        code = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        code = 124
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout}s"
    (CMD_DIR / f"{key}.stdout").write_text(stdout, encoding="utf-8")
    (CMD_DIR / f"{key}.stderr").write_text(stderr, encoding="utf-8")
    (CMD_DIR / f"{key}.exit").write_text(f"{code}\n", encoding="utf-8")
    return {
        "key": key,
        "command": command,
        "exit_code": code,
        "stdout_path": str(CMD_DIR / f"{key}.stdout"),
        "stderr_path": str(CMD_DIR / f"{key}.stderr"),
    }


def csv_count(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def summarize_side_root(root: Path) -> dict[str, object]:
    files = {name: root / name for name in REQUIRED_TRIPLET}
    manifest = files["provenance_manifest.json"]
    manifest_summary: dict[str, object] = {}
    if manifest.exists():
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            for key in (
                "source_type",
                "source",
                "owner",
                "control_policy",
                "approval_status",
                "projection_only",
                "canonical_merge",
            ):
                if key in payload:
                    manifest_summary[key] = payload[key]
        except json.JSONDecodeError:
            manifest_summary["json_decode_error"] = True
    return {
        "root": str(root),
        "exists": root.exists(),
        "required_files_present": {name: path.exists() for name, path in files.items()},
        "positive_rows": csv_count(files["positive_spoofing_layering_rows.csv"]),
        "matched_control_rows": csv_count(files["matched_negative_normal_activity_rows.csv"]),
        "manifest_summary": manifest_summary,
        "disposition": "known_non_target_sidecar_do_not_copy_without_explicit_approval",
    }


def summarize_downloads_regime_dataset() -> dict[str, object]:
    csv_path = DOWNLOADS_REGIME_ROOT / "stock_market_regimes_2000_2026.csv"
    summary_path = DOWNLOADS_REGIME_ROOT / "dataset_summary.txt"
    result: dict[str, object] = {
        "root": str(DOWNLOADS_REGIME_ROOT),
        "exists": DOWNLOADS_REGIME_ROOT.exists(),
        "csv_exists": csv_path.exists(),
        "summary_exists": summary_path.exists(),
    }
    if summary_path.exists():
        result["summary_text"] = summary_path.read_text(encoding="utf-8")[:4000]
    if not csv_path.exists():
        return result

    rows = 0
    min_date = None
    max_date = None
    after_cutoff = 0
    tickers: set[str] = set()
    regime_counts: dict[str, int] = {}
    columns: list[str] | None = None
    sample_rows: list[dict[str, str]] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        for row in reader:
            rows += 1
            if len(sample_rows) < 3:
                sample_rows.append(dict(row))
            date = row.get("date", "")
            if date:
                min_date = date if min_date is None or date < min_date else min_date
                max_date = date if max_date is None or date > max_date else max_date
                if date > "2026-01-30":
                    after_cutoff += 1
            ticker = row.get("ticker")
            if ticker:
                tickers.add(ticker)
            label = row.get("regime_label")
            if label:
                regime_counts[label] = regime_counts.get(label, 0) + 1
    result.update(
        {
            "rows": rows,
            "columns": columns,
            "min_date": min_date,
            "max_date": max_date,
            "rows_after_2026_01_30": after_cutoff,
            "ticker_count": len(tickers),
            "sample_tickers": sorted(tickers)[:12],
            "regime_counts": regime_counts,
            "sample_rows": sample_rows,
            "r5_unlock": False,
            "r3_unlock": False,
            "disposition": "daily_stock_panel_through_2026_01_30_no_post_cutoff_rows_no_native_subhour_labels",
        }
    )
    return result


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    commands = [
        run_cmd(
            "downloads_desktop_arrival_sweep",
            [
                "bash",
                "-lc",
                "find /Users/thrill3r/Downloads /Users/thrill3r/Desktop -maxdepth 5 "
                "\\( -iname 'positive_spoofing_layering_rows.csv' "
                "-o -iname 'matched_negative_normal_activity_rows.csv' "
                "-o -iname 'provenance_manifest.json' "
                "-o -iname '*owner*export*' "
                "-o -iname '*native*subhour*' "
                "-o -iname '*recency*extension*' "
                "-o -iname '*MainRegimeV2*' \\) 2>/dev/null | sort",
            ],
        ),
        run_cmd(
            "private_tmp_near_triplet_sweep",
            [
                "bash",
                "-lc",
                "find /private/tmp -maxdepth 4 "
                "\\( -iname 'positive_spoofing_layering_rows.csv' "
                "-o -iname 'matched_negative_normal_activity_rows.csv' "
                "-o -iname 'provenance_manifest.json' \\) 2>/dev/null | sort",
            ],
        ),
    ]

    side_roots = [summarize_side_root(root) for root in KNOWN_SIDE_ROOTS]
    downloads_regime = summarize_downloads_regime_dataset()
    target_roots = {str(root): root.exists() for root in TARGET_ROOTS}
    exact_roots_unlocked = any(target_roots.values())
    accepted_rows_added = 0
    source_control_evidence_acquired = False
    gate = "source_arrival_local_drop_sweep_after_055930_v1=no_required_root_or_approved_source_drop_no_promotion"

    result = {
        "run_id": RUN_ID,
        "generated_at_epoch": int(time.time()),
        "board_hash_before_artifact": board_hash(),
        "gate_result": gate,
        "target_roots": target_roots,
        "known_side_roots": side_roots,
        "downloads_regime_dataset": downloads_regime,
        "commands": commands,
        "decision": {
            "accepted_rows_added": accepted_rows_added,
            "source_control_evidence_acquired": source_control_evidence_acquired,
            "required_root_unlocked": exact_roots_unlocked,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
    }

    json_path = OUT_DIR / "source_arrival_local_drop_sweep_after_055930_v1.json"
    report_path = OUT_DIR / "source_arrival_local_drop_sweep_after_055930_v1.md"
    side_csv_path = OUT_DIR / "source_arrival_local_drop_side_roots_v1.csv"
    assertions_path = CHECK_DIR / "source_arrival_local_drop_sweep_after_055930_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with side_csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "root",
                "exists",
                "positive_rows",
                "matched_control_rows",
                "positive_file",
                "matched_file",
                "provenance_file",
                "disposition",
            ],
        )
        writer.writeheader()
        for row in side_roots:
            present = row["required_files_present"]
            writer.writerow(
                {
                    "root": row["root"],
                    "exists": row["exists"],
                    "positive_rows": row["positive_rows"],
                    "matched_control_rows": row["matched_control_rows"],
                    "positive_file": present["positive_spoofing_layering_rows.csv"],
                    "matched_file": present["matched_negative_normal_activity_rows.csv"],
                    "provenance_file": present["provenance_manifest.json"],
                    "disposition": row["disposition"],
                }
            )

    report = f"""# Source Arrival Local Drop Sweep After 055930 v1

Run id: `{RUN_ID}`

Gate result: `{gate}`

## Scope

Read-only current-state sweep after the `055930` completion audit. This checks exact target roots, nearby verifier-shaped private-tmp sidecars, likely human-drop locations, and the local `stock-market-regimes-20002026` dataset. It does not copy files, mutate target roots, approve controls, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Readback

- Exact required roots: `{target_roots}`.
- Known verifier-shaped sidecar roots checked: `{len(side_roots)}`.
- Downloads/Desktop arrival command exit: `{commands[0]['exit_code']}`.
- Private tmp triplet sweep exit: `{commands[1]['exit_code']}`.
- Local stock-market-regimes rows: `{downloads_regime.get('rows')}`.
- Local stock-market-regimes max date: `{downloads_regime.get('max_date')}`.
- Local stock-market-regimes rows after `2026-01-30`: `{downloads_regime.get('rows_after_2026_01_30')}`.
- Local stock-market-regimes disposition: `{downloads_regime.get('disposition')}`.

## Decision

No required source/control root is unlocked. The known verifier-shaped triplets remain non-target sidecars and must not be copied into `/tmp/ict-engine-board-a-r6-owner-export-v1` without explicit approval or source-owned control provenance. The local `stock-market-regimes-20002026` dataset remains daily stock-panel evidence through `2026-01-30`; it has no post-cutoff rows and no native sub-hour source labels, so it does not unlock R5 or R3.

Promotion remains blocked: accepted rows added `0`, source/control evidence acquired `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.

## Next

Preserve the Current Cursor next action. Continue only after explicit approval, verifier-native R6 owner/export rows plus source-owned broad normal controls, source-owned R5 recency-extension rows, native sub-hour source-label rows, or genuinely source-owned cross-timeframe `MainRegimeV2` exports unlock a required target root; then rerun direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback in order.
"""
    report_path.write_text(report, encoding="utf-8")

    assertions = [
        f"gate_result={gate}",
        f"required_root_unlocked={str(exact_roots_unlocked).lower()}",
        f"source_control_evidence_acquired={str(source_control_evidence_acquired).lower()}",
        "accepted_rows_added=0",
        f"downloads_regime_rows={downloads_regime.get('rows')}",
        f"downloads_regime_max_date={downloads_regime.get('max_date')}",
        f"downloads_regime_rows_after_2026_01_30={downloads_regime.get('rows_after_2026_01_30')}",
        "canonical_merge=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
