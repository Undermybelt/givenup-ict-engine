#!/usr/bin/env python3
import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from zipfile import BadZipFile, ZipFile


RUN_ID = "20260512T083703+0800-codex-local-order-lifecycle-zip-header-sweep-after-083450-v1"
REPO = Path(__file__).resolve().parents[5]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "local-order-lifecycle-zip-header-sweep-after-083450-v1"
CHECK_DIR = RUN_ROOT / "checks"

TOMAC = Path("/Users/thrill3r/Downloads/Tomac")
TARGET_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"),
]
REQUIRED = {
    "direct_manipulation_positive_rows.csv",
    "direct_manipulation_matched_controls.csv",
    "direct_manipulation_provenance.json",
}

ORDER_HINTS = {
    "order_id",
    "orderid",
    "client_order_id",
    "side",
    "buy_sell",
    "aggressor",
    "aggressor_side",
    "bid_px",
    "ask_px",
    "bid_price",
    "ask_price",
    "bid_size",
    "ask_size",
    "book",
    "depth",
    "level",
    "action",
    "event_type",
    "order_type",
    "sequence",
    "seqnum",
    "participant",
    "trader",
    "account",
    "mpid",
    "maker",
    "taker",
    "label",
    "source_section",
    "matched_control",
    "control_group",
}
BAR_HINTS = {"open", "high", "low", "close", "volume", "ohlcv"}
SYMBOLOGY_HINTS = {"instrument_id", "raw_symbol", "stype", "symbol", "expiration", "asset"}


def sha256_file(path: Path, limit_bytes: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        remaining = limit_bytes
        while remaining > 0:
            chunk = f.read(min(1024 * 1024, remaining))
            if not chunk:
                break
            h.update(chunk)
            remaining -= len(chunk)
    return h.hexdigest()


def normalize_headers(line: bytes) -> list[str]:
    text = line.decode("utf-8", errors="replace").strip("\ufeff\r\n")
    if not text:
        return []
    try:
        row = next(csv.reader([text]))
    except Exception:
        row = text.split(",")
    return [c.strip() for c in row if c.strip()]


def classify(headers: list[str], name: str) -> tuple[str, list[str]]:
    lowered = {h.lower().strip() for h in headers}
    name_l = name.lower()
    order_hits = sorted(h for h in lowered if h in ORDER_HINTS)
    bar_hits = sorted(h for h in lowered if h in BAR_HINTS)
    sym_hits = sorted(h for h in lowered if h in SYMBOLOGY_HINTS)
    if len(order_hits) >= 2:
        return "order_lifecycle_candidate", order_hits
    if "ohlcv" in name_l or {"open", "high", "low", "close"}.issubset(lowered):
        return "ohlcv_or_bar_context", bar_hits
    if "symbology" in name_l or len(sym_hits) >= 2:
        return "symbology_context", sym_hits
    if "backtest" in name_l or "results" in name_l or "summary" in name_l:
        return "strategy_or_backtest_context", []
    return "unknown_context", order_hits or bar_hits or sym_hits


def read_plain_header(path: Path) -> list[str]:
    try:
        with path.open("rb") as f:
            return normalize_headers(f.readline())
    except Exception:
        return []


def scan_zip(path: Path) -> list[dict]:
    rows = []
    try:
        with ZipFile(path) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                member = info.filename
                headers = []
                if member.lower().endswith(".csv"):
                    try:
                        with zf.open(info) as f:
                            headers = normalize_headers(f.readline())
                    except Exception:
                        headers = []
                cls, hits = classify(headers, member)
                rows.append(
                    {
                        "container": str(path),
                        "member": member,
                        "size": info.file_size,
                        "kind": "zip_member",
                        "class": cls,
                        "hits": "|".join(hits),
                        "headers": "|".join(headers[:40]),
                    }
                )
    except BadZipFile:
        rows.append(
            {
                "container": str(path),
                "member": "",
                "size": path.stat().st_size if path.exists() else 0,
                "kind": "bad_zip",
                "class": "unreadable_archive",
                "hits": "",
                "headers": "",
            }
        )
    return rows


def scan_plain(path: Path) -> dict:
    headers = read_plain_header(path) if path.suffix.lower() == ".csv" else []
    cls, hits = classify(headers, path.name)
    return {
        "container": str(path),
        "member": "",
        "size": path.stat().st_size if path.exists() else 0,
        "kind": path.suffix.lower().lstrip(".") or "file",
        "class": cls,
        "hits": "|".join(hits),
        "headers": "|".join(headers[:40]),
    }


def target_root_status() -> list[dict]:
    statuses = []
    for root in TARGET_ROOTS:
        present = {p.name for p in root.iterdir()} if root.exists() and root.is_dir() else set()
        statuses.append(
            {
                "path": str(root),
                "exists": root.exists(),
                "file_count": len(present),
                "required_present": sorted(present & REQUIRED),
                "exact_required_package": REQUIRED.issubset(present),
            }
        )
    return statuses


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    candidates = []
    if TOMAC.exists():
        for path in sorted(TOMAC.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".zip", ".csv", ".json", ".rar"}:
                continue
            if path.suffix.lower() == ".zip":
                candidates.extend(scan_zip(path))
            else:
                candidates.append(scan_plain(path))

    targets = target_root_status()
    order_candidates = [r for r in candidates if r["class"] == "order_lifecycle_candidate"]
    exact_required = any(t["exact_required_package"] for t in targets)

    summary = {
        "run_id": RUN_ID,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "tomac_root": str(TOMAC),
        "candidate_rows_scanned": len(candidates),
        "zip_member_rows_scanned": sum(1 for r in candidates if r["kind"] == "zip_member"),
        "order_lifecycle_candidate_rows": len(order_candidates),
        "exact_required_package_present": exact_required,
        "target_roots": targets,
        "accepted_rows_added": 0,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
        "gate_result": "local_order_lifecycle_zip_header_sweep_after_083450_v1=no_verifier_native_order_lifecycle_package_no_unlock",
    }

    csv_path = OUT_DIR / "local_order_lifecycle_zip_header_candidates_v1.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["container", "member", "size", "kind", "class", "hits", "headers"],
        )
        writer.writeheader()
        writer.writerows(candidates)

    target_csv = OUT_DIR / "local_order_lifecycle_target_roots_v1.csv"
    with target_csv.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["path", "exists", "file_count", "required_present", "exact_required_package"],
        )
        writer.writeheader()
        for row in targets:
            out = dict(row)
            out["required_present"] = "|".join(row["required_present"])
            writer.writerow(out)

    json_path = OUT_DIR / "local_order_lifecycle_zip_header_sweep_after_083450_v1.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    report_path = OUT_DIR / "local_order_lifecycle_zip_header_sweep_after_083450_v1.md"
    order_lines = [
        f"- `{r['container']}` member `{r['member']}` hits `{r['hits']}`"
        for r in order_candidates[:20]
    ]
    if not order_lines:
        order_lines = ["- None."]
    report_path.write_text(
        "\n".join(
            [
                "# Local Order-Lifecycle Zip/Header Sweep After 083450 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{summary['gate_result']}`",
                "",
                "## Scope",
                "",
                "Read-only local sweep of Tomac CSV/JSON/ZIP/RAR candidates after the `083450` schema classifier. The script reads file names, ZIP member names, and CSV headers only. It does not extract files into target roots, copy evidence, mutate state, run verifier/split calibration, run selected-data AutoQuant, run Pre-Bayes/BBN/CatBoost/execution-tree promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Summary",
                "",
                f"- Candidate/header rows scanned: `{summary['candidate_rows_scanned']}`.",
                f"- ZIP member rows scanned: `{summary['zip_member_rows_scanned']}`.",
                f"- Order-lifecycle candidate rows: `{summary['order_lifecycle_candidate_rows']}`.",
                f"- Exact required R6 package present in target roots: `{str(summary['exact_required_package_present']).lower()}`.",
                "",
                "## Order-Lifecycle Candidates",
                "",
                *order_lines,
                "",
                "## Target Roots",
                "",
                "| Path | Exists | File Count | Required Files Present | Exact Package |",
                "|---|---:|---:|---|---:|",
                *[
                    f"| `{t['path']}` | `{t['exists']}` | `{t['file_count']}` | `{', '.join(t['required_present']) or 'none'}` | `{t['exact_required_package']}` |"
                    for t in targets
                ],
                "",
                "## Decision",
                "",
                "No verifier-native positive/control/provenance package was found. Local Tomac archives and extracted files remain market-data, symbology, strategy, or backtest context unless an owner-approved/source-owned order-lifecycle export with matched normal controls is placed in the required target root or same-exhibit `FLIP` is explicitly approved as control.",
                "",
                "Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed false; `update_goal=false`.",
                "",
                "## Next",
                "",
                "Continue source/control acquisition only. Do not run selected-data AutoQuant or the ordered AutoQuant -> filter / Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution tree chain until source/control unlock and selected-history gates are both satisfied.",
                "",
            ]
        )
    )

    assertion_path = CHECK_DIR / "local_order_lifecycle_zip_header_sweep_after_083450_v1_assertions.out"
    assertion_path.write_text(
        "\n".join(
            [
                f"gate_result={summary['gate_result']}",
                f"candidate_rows_scanned={summary['candidate_rows_scanned']}",
                f"zip_member_rows_scanned={summary['zip_member_rows_scanned']}",
                f"order_lifecycle_candidate_rows={summary['order_lifecycle_candidate_rows']}",
                f"exact_required_package_present={str(summary['exact_required_package_present']).lower()}",
                "accepted_rows_added=0",
                "valid_required_root_unlock=false",
                "source_control_evidence_acquired=false",
                "canonical_merge=false",
                "selected_data_autoquant_promotion=false",
                "downstream_promotion_rerun=false",
                "strict_full_objective=false",
                "trade_usable=false",
                "promotion_allowed=false",
                "update_goal=false",
                "",
            ]
        )
    )

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
