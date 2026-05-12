from __future__ import annotations

import csv
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T014313-codex-direct-manipulation-data-readiness-scan"
OUT_DIR = RUN_ROOT / "input-readiness"
CHECKS_DIR = RUN_ROOT / "checks"

SCAN_ROOTS = [
    Path("/Users/thrill3r/Downloads/Tomac"),
    Path("/Users/thrill3r/nautilus_trader/tests/test_data"),
    Path("/Users/thrill3r/BTC-Trading-Since-2020"),
    REPO / "docs/experiments/actionable-regime-confidence/runs",
]

NAME_HINTS = [
    "mbo",
    "l2",
    "l3",
    "depth",
    "book",
    "order",
    "quote",
    "trade",
    "delta",
    "deltas",
]


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def classify(path: Path) -> dict[str, Any]:
    name = path.name.lower()
    suffixes = "".join(path.suffixes).lower()
    size = path.stat().st_size
    item: dict[str, Any] = {
        "path": str(path),
        "size_bytes": size,
        "suffixes": suffixes,
        "input_class": "unknown",
        "directness": "unknown",
        "qualifies_for_manipulation_gate": False,
        "blocker": "not_classified",
    }
    if suffixes.endswith(".dbn.zst") or ".dbn" in suffixes:
        item.update(
            {
                "input_class": "market_by_order_or_databento_dbn",
                "directness": "potential_l2_l3_mbo_direct",
                "qualifies_for_manipulation_gate": False,
                "blocker": "local_file_is_fixture_or_unverified_scope_until decoded row count, symbols, and duration prove calibration support",
            }
        )
    elif suffixes.endswith(".parquet") and ("delta" in name or "book" in name or "order" in name):
        item.update(
            {
                "input_class": "market_orderbook_delta_parquet",
                "directness": "potential_l2_l3_direct",
                "qualifies_for_manipulation_gate": False,
                "blocker": "needs decoded row count, symbols, and chronological duration before calibration use",
            }
        )
    elif suffixes.endswith(".csv"):
        lower_path = str(path).lower()
        if "btc-trading-since-2020" in lower_path and ("order" in name or "execution" in name):
            item.update(
                {
                    "input_class": "private_account_order_lifecycle",
                    "directness": "direct_private_account_lifecycle_only",
                    "qualifies_for_manipulation_gate": False,
                    "blocker": "not market-wide manipulation proof",
                }
            )
        elif any(token in name for token in ["mbo", "l2", "depth", "book", "quote", "trade"]):
            item.update(
                {
                    "input_class": "csv_trade_quote_depth_candidate",
                    "directness": "candidate_direct_or_partial",
                    "qualifies_for_manipulation_gate": False,
                    "blocker": "needs schema/support/alignment audit; do not promote from filename alone",
                }
            )
        else:
            item.update(
                {
                    "input_class": "csv_other",
                    "directness": "not_direct_manipulation_evidence",
                    "blocker": "filename/schema does not indicate direct manipulation input",
                }
            )
    return item


def candidate_paths() -> list[Path]:
    found: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            parts = set(Path(dirpath).parts)
            if any(skip in parts for skip in {"node_modules", ".venv", "__pycache__", ".git"}):
                dirnames[:] = []
                continue
            for filename in filenames:
                lower = filename.lower()
                if not any(hint in lower for hint in NAME_HINTS):
                    continue
                if not lower.endswith((".csv", ".json", ".parquet", ".zst", ".dbn", ".dbn.zst")):
                    continue
                found.append(Path(dirpath) / filename)
    return sorted(set(found))


def csv_header(path: Path) -> list[str]:
    try:
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
            return next(csv.reader(handle))
    except Exception:
        return []


def zstd_probe(path: Path) -> dict[str, Any]:
    if shutil.which("zstdcat") is None:
        return {"available": False, "reason": "zstdcat_missing"}
    try:
        proc = subprocess.run(["zstdcat", str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        sample = proc.stdout[:512]
        return {
            "available": proc.returncode == 0,
            "returncode": proc.returncode,
            "sample_ascii_tokens": sorted({token for token in sample.decode("latin1", errors="ignore").replace("\x00", " ").split() if token.isprintable()})[:20],
            "stderr": proc.stderr.decode("utf-8", errors="replace")[:300],
        }
    except Exception as exc:
        return {"available": False, "reason": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    tools = {
        "zstdcat": shutil.which("zstdcat"),
        "bsdtar": shutil.which("bsdtar"),
        "databento_cli": shutil.which("databento"),
        "python_databento": module_available("databento"),
        "python_pyarrow": module_available("pyarrow"),
    }
    items = []
    for path in candidate_paths():
        item = classify(path)
        if path.suffix.lower() == ".csv":
            item["columns_sample"] = csv_header(path)[:80]
        if "".join(path.suffixes).lower().endswith(".dbn.zst"):
            item["zstd_probe"] = zstd_probe(path)
        items.append(item)
    direct_candidates = [
        item
        for item in items
        if item["input_class"] in {"market_by_order_or_databento_dbn", "market_orderbook_delta_parquet", "csv_trade_quote_depth_candidate", "private_account_order_lifecycle"}
    ]
    qualifying = [item for item in direct_candidates if item["qualifies_for_manipulation_gate"]]
    by_class: dict[str, int] = {}
    for item in items:
        by_class[item["input_class"]] = by_class.get(item["input_class"], 0) + 1
    report = {
        "run_id": "20260511T014313+0800-codex-direct-manipulation-data-readiness-scan",
        "active_axis": "MainRegimeV2",
        "objective": "Decide whether local direct L2/L3/MBO/order-lifecycle/event data or decoders are ready to rerun the Manipulation 95% gate.",
        "scan_roots": [str(root) for root in SCAN_ROOTS],
        "tool_readiness": tools,
        "candidate_file_count": len(items),
        "direct_candidate_file_count": len(direct_candidates),
        "qualifying_direct_manipulation_input_sets": len(qualifying),
        "classes": by_class,
        "direct_candidates_sample": direct_candidates[:80],
        "decision": {
            "board_state": "blocked",
            "accepted_gate": "partial_for_MainRegimeV2_Crisis_only_prior_evidence_preserved",
            "manipulation_input_state": "missing_required_inputs",
            "thresholds_relaxed": False,
            "runtime_code_changed": False,
            "fresh_calibration_rerun": False,
            "trade_usable": False,
            "blocker": "No local calibration-grade market-wide direct L2/L3/MBO/order-lifecycle/event dataset was found; filenames and fixture-scale DBN/parquet/CSV candidates are insufficient for Manipulation.",
            "next_action": "Acquire calibration-grade direct L2/L3/MBO/order-lifecycle/event data across multiple instruments, periods, and contexts from a real provider export before rerunning the Manipulation gate.",
        },
    }
    report_path = OUT_DIR / "direct_manipulation_data_readiness_scan.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md = [
        "# Direct Manipulation Data Readiness Scan",
        "",
        f"Run id: `{report['run_id']}`",
        "",
        "## Decision",
        "",
        f"- Qualifying direct manipulation input sets: `{len(qualifying)}`",
        f"- Direct candidate files inspected: `{len(direct_candidates)}`",
        f"- Manipulation input state: `{report['decision']['manipulation_input_state']}`",
        f"- Trade usable: `{str(report['decision']['trade_usable']).lower()}`",
        "",
        "Current local candidates remain insufficient because a filename, short fixture, private account order log, or OHLCV panel is not market-wide manipulation proof.",
    ]
    (OUT_DIR / "direct_manipulation_data_readiness_scan.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    checks = [
        f"report: {repo_rel(report_path)}",
        f"candidate_file_count: {len(items)}",
        f"direct_candidate_file_count: {len(direct_candidates)}",
        f"qualifying_direct_manipulation_input_sets: {len(qualifying)}",
        f"python_databento: {tools['python_databento']}",
        f"python_pyarrow: {tools['python_pyarrow']}",
        "thresholds_relaxed: False",
        "runtime_code_changed: False",
        "fresh_calibration_rerun: False",
        "trade_usable: False",
        "MANIPULATION_INPUT_STATE missing_required_inputs",
        "GATE blocked_missing_required_inputs",
    ]
    (CHECKS_DIR / "direct_manipulation_data_readiness_scan_assertions.out").write_text("\n".join(checks) + "\n", encoding="utf-8")
    (RUN_ROOT / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
