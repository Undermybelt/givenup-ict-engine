#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T082629+0800-codex-local-databento-archive-readback-after-082240-v1"
SLUG = "local-databento-archive-readback-after-082240-v1"
GATE = "local_databento_archive_readback_after_082240_v1=ohlcv_only_no_source_control_unlock"

REPO = Path(__file__).resolve().parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_ROOT = RUN_ROOT / SLUG
CHECK_ROOT = RUN_ROOT / "checks"

ARCHIVE = Path("/Users/thrill3r/Downloads/Tomac/gc future 2021-2025/databento.rar")
SIDE_ROOT = ARCHIVE.parent
MANIFEST = SIDE_ROOT / "manifest.json"
METADATA = SIDE_ROOT / "metadata.json"

CONTROL_COLUMNS = {
    "order_id",
    "side",
    "bid_px",
    "ask_px",
    "bid_sz",
    "ask_sz",
    "price",
    "size",
    "action",
    "channel_id",
    "sequence",
    "participant",
    "source_section",
    "label",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_text(args: list[str], timeout: int = 60) -> str:
    completed = subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
    return completed.stdout


def sample_member(member: str) -> dict[str, object]:
    process = subprocess.Popen(
        ["bsdtar", "-xOf", str(ARCHIVE), member],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    sample = []
    assert process.stdout is not None
    try:
        for _ in range(5):
            line = process.stdout.readline()
            if not line:
                break
            sample.append(line.rstrip("\n"))
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    header = sample[0] if sample else ""
    columns = [part.strip() for part in header.split(",") if part.strip()]
    lower_columns = {col.lower() for col in columns}
    return {
        "member": member,
        "header": header,
        "sample_rows": len(sample) - 1 if sample else 0,
        "columns": columns,
        "has_order_lifecycle_columns": bool(CONTROL_COLUMNS & lower_columns),
        "missing_control_columns": sorted(CONTROL_COLUMNS - lower_columns),
        "sample": sample,
    }


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    CHECK_ROOT.mkdir(parents=True, exist_ok=True)

    members = [line.strip() for line in run_text(["bsdtar", "-tf", str(ARCHIVE)]).splitlines() if line.strip()]
    metadata = json.loads(METADATA.read_text()) if METADATA.exists() else {}
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    member_rows = [sample_member(member) for member in members]

    schema = metadata.get("query", {}).get("schema")
    dataset = metadata.get("query", {}).get("dataset")
    symbols = metadata.get("query", {}).get("symbols", [])
    no_order_lifecycle = all(not row["has_order_lifecycle_columns"] for row in member_rows)
    accepted_rows_added = 0
    valid_required_root_unlock = False
    source_control_evidence_acquired = False

    payload = {
        "run_id": RUN_ID,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact": sha256_file(BOARD),
        "gate_result": GATE,
        "archive": str(ARCHIVE),
        "archive_exists": ARCHIVE.exists(),
        "archive_size_bytes": ARCHIVE.stat().st_size if ARCHIVE.exists() else 0,
        "archive_sha256": sha256_file(ARCHIVE) if ARCHIVE.exists() else "",
        "dataset": dataset,
        "schema": schema,
        "symbols": symbols,
        "manifest_job_id": manifest.get("job_id", ""),
        "members": member_rows,
        "no_order_lifecycle_columns": no_order_lifecycle,
        "accepted_rows_added": accepted_rows_added,
        "valid_required_root_unlock": valid_required_root_unlock,
        "source_control_evidence_acquired": source_control_evidence_acquired,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    json_path = OUT_ROOT / "local_databento_archive_readback_after_082240_v1.json"
    member_csv = OUT_ROOT / "local_databento_archive_members_v1.csv"
    md_path = OUT_ROOT / "local_databento_archive_readback_after_082240_v1.md"
    assertions_path = CHECK_ROOT / "local_databento_archive_readback_after_082240_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with member_csv.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["member", "header", "has_order_lifecycle_columns", "sample_rows"])
        for row in member_rows:
            writer.writerow([row["member"], row["header"], row["has_order_lifecycle_columns"], row["sample_rows"]])

    member_table = "\n".join(
        f"| `{row['member']}` | `{row['header']}` | `{row['has_order_lifecycle_columns']}` |"
        for row in member_rows
    )
    md_path.write_text(
        "\n".join(
            [
                "# Local Databento Archive Readback After 082240 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{GATE}`",
                "",
                "## Scope",
                "",
                "Read-only inspection of the local `databento.rar` archive found under Downloads. This packet checks whether the archive can satisfy the current Board A R6 source/control blocker. It does not extract files into repo state, mutate target roots, accept rows, run verifier/split calibration, rerun provider/Auto-Quant/Pre-Bayes/BBN/CatBoost/execution-tree, make a trade claim, or call `update_goal`.",
                "",
                "## Archive Readback",
                "",
                f"- Archive: `{ARCHIVE}`",
                f"- Manifest job id: `{manifest.get('job_id', '')}`",
                f"- Dataset: `{dataset}`",
                f"- Schema: `{schema}`",
                f"- Symbols: `{', '.join(symbols) if symbols else 'none'}`",
                f"- Archive SHA-256: `{payload['archive_sha256']}`",
                "",
                "## Member Headers",
                "",
                "| Member | Header | Has order-lifecycle/control columns |",
                "|---|---|---|",
                member_table,
                "",
                "## Decision",
                "",
                "- The archive is real local Databento/CME data, but it is `ohlcv-1m` bar data only.",
                "- It contains GC/NQ OHLCV headers (`ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol`) and no order-id, side, quote, book-depth, participant, source-section, or label columns needed for R6 source-owned positive/control rows.",
                "- Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.",
                "",
                "## Next",
                "",
                "Continue source/control acquisition only. This archive can remain local market context, not the required R6 owner/export source-control root. The live unblocker remains owner-approved/authenticated FINRA, venue-surveillance, CAT-like, CME/Cboe/CFE order-lifecycle export with positives and matched normal controls, or explicit same-exhibit FLIP-as-control approval.",
                "",
            ]
        )
    )

    assertions = [
        f"gate_result={GATE}",
        f"archive_exists={str(ARCHIVE.exists()).lower()}",
        f"dataset={dataset}",
        f"schema={schema}",
        f"members={len(member_rows)}",
        f"no_order_lifecycle_columns={str(no_order_lifecycle).lower()}",
        "accepted_rows_added=0",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n")
    print("\n".join(assertions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
