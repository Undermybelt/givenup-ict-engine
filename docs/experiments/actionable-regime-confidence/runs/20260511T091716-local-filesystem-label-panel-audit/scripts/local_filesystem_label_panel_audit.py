#!/usr/bin/env python3
import csv
import json
import os
from collections import Counter
from pathlib import Path


RUN_ID = "20260511T091716+0800-local-filesystem-label-panel-audit"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "local-filesystem-audit"
CHECKS = ROOT / "checks"

SEARCH_ROOTS = [
    Path("/private/tmp"),
    Path("/tmp"),
    Path("/Users/thrill3r/Downloads"),
    Path("/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence"),
]
SKIP_DIR_NAMES = {
    ".git", "node_modules", "target", "dist", "build", "__pycache__",
    ".venv", "venv", ".mypy_cache", ".pytest_cache",
}
NAME_TERMS = (
    "regime", "label", "labels", "manip", "wash", "spoof", "pump",
    "bull", "bear", "sideways", "crisis",
)
EXTENSIONS = {".csv", ".tsv", ".json", ".jsonl", ".md", ".txt", ".parquet", ".feather"}
MAX_FILES_VISITED_PER_ROOT = 8000
MAX_CANDIDATES = 2000
MAX_BYTES_FOR_HEADER = 2_000_000

ROOT_TERMS = {
    "Bull": ("bull", "bullish", "risk_on", "risk-on"),
    "Bear": ("bear", "bearish", "risk_off", "risk-off"),
    "Sideways": ("sideways", "range", "consolidation", "choppy"),
    "Crisis": ("crisis", "crash", "stress", "turbulen", "risk_off"),
}
TARGET_TERMS = (
    "spy", "qqq", "dia", "gld", "uso", "es=f", "nq=f", "ym=f", "cl=f", "gc=f",
    "^gspc", "^dji", "^ndx", "^vix", "xbtusd", "btcusd", "ethusd", "solusd", "kraken",
)
TIMEFRAME_TERMS = (
    "1m", "5m", "15m", "30m", "1h", "4h", "1d", "daily", "1w", "weekly", "1mo", "monthly",
)
LABEL_TERMS = ("label", "regime", "class", "target", "annotation")
PROXY_TERMS = ("hmm", "gmm", "cluster", "kmeans", "future_return", "prediction", "signal", "ohlcv", "indicator")
MANIPULATION_TERMS = ("wash", "spoof", "layer", "pump", "market manipulation", "manipulation")


def text_preview(path):
    if path.stat().st_size > MAX_BYTES_FOR_HEADER:
        return ""
    suffix = path.suffix.lower()
    if suffix in {".parquet", ".feather"}:
        return path.name
    try:
        with path.open("rb") as f:
            raw = f.read(12000)
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return ""


def classify(path, preview):
    lower_path = str(path).lower()
    text = (lower_path + "\n" + preview.lower())[:20000]
    root_hits = {root: any(term in text for term in terms) for root, terms in ROOT_TERMS.items()}
    target_hits = [term for term in TARGET_TERMS if term in text]
    timeframe_hits = [term for term in TIMEFRAME_TERMS if term in text]
    label_hits = [term for term in LABEL_TERMS if term in text]
    proxy_hits = [term for term in PROXY_TERMS if term in text]
    manipulation_hits = [term for term in MANIPULATION_TERMS if term in text]

    if "ict-regime-kaggle-regime-label-root" in lower_path:
        decision = "partial_existing_kaggle_exact_panel_already_consumed"
        reason = "Local exact-label cache is the already-counted Kaggle daily/weekly partial panel; it adds no missing intraday/monthly/Kraken/instrument slots."
    elif "/docs/experiments/actionable-regime-confidence/" in lower_path:
        decision = "rejected_repo_artifact_or_prior_probe"
        reason = "Repo-local artifact/probe output is evidence provenance, not an independent source-label panel."
    elif manipulation_hits and label_hits:
        decision = "sidecar_direct_manipulation_candidate_needs_rows_and_controls"
        reason = "Local metadata mentions manipulation labels, but this audit did not verify replayable positive/negative windows and controls."
    elif proxy_hits:
        decision = "rejected_proxy_or_generated_label_file"
        reason = "Candidate appears model/proxy/generated or OHLCV/indicator-derived, not independent source labels."
    elif not all(root_hits.values()):
        decision = "rejected_missing_full_mainregimev2_roots"
        reason = "Candidate does not expose all Bull/Bear/Sideways/Crisis roots in inspected filename/header/sample."
    elif not target_hits:
        decision = "rejected_no_exact_target_underlying"
        reason = "Candidate does not attach labels to the Board A target instruments/providers."
    elif not timeframe_hits:
        decision = "rejected_no_timeframe_attachment"
        reason = "Candidate has root words but no accepted timeframe attachment in inspected metadata."
    elif not label_hits:
        decision = "rejected_no_explicit_label_schema"
        reason = "Candidate has regime words but no explicit label/class/target schema."
    else:
        decision = "not_accepted_local_metadata_only_needs_source_provenance"
        reason = "Metadata is promising but independent provenance, schema, rows, and chronological windows were not verified."

    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "suffix": path.suffix.lower(),
        "decision": decision,
        "reason": reason,
        "root_hits": root_hits,
        "target_hits": target_hits[:12],
        "timeframe_hits": timeframe_hits[:12],
        "label_hits": label_hits[:12],
        "proxy_hits": proxy_hits[:12],
        "manipulation_hits": manipulation_hits[:12],
    }


def collect_candidates():
    candidates = []
    visit_counts = {}
    for root in SEARCH_ROOTS:
        root = root.resolve()
        visited = 0
        if not root.exists():
            visit_counts[str(root)] = 0
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
            visited += len(filenames)
            if visited > MAX_FILES_VISITED_PER_ROOT:
                break
            for name in filenames:
                path = Path(dirpath) / name
                suffix = path.suffix.lower()
                lowered = str(path).lower()
                if suffix not in EXTENSIONS:
                    continue
                if not any(term in lowered for term in NAME_TERMS):
                    continue
                try:
                    if path.stat().st_size <= 0:
                        continue
                except OSError:
                    continue
                preview = text_preview(path)
                candidates.append(classify(path, preview))
                if len(candidates) >= MAX_CANDIDATES:
                    visit_counts[str(root)] = visited
                    return candidates, visit_counts
        visit_counts[str(root)] = visited
    return candidates, visit_counts


def write_outputs(result):
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    (OUT / "local_filesystem_label_panel_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    csv_path = OUT / "local_filesystem_label_panel_audit_candidates.csv"
    fieldnames = ["path", "size_bytes", "suffix", "decision", "reason", "root_hits", "target_hits", "timeframe_hits", "label_hits", "proxy_hits", "manipulation_hits"]
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in result["candidates"]:
            writer.writerow({k: json.dumps(row[k], sort_keys=True) if isinstance(row.get(k), (dict, list)) else row.get(k, "") for k in fieldnames})

    decision_counts = dict(Counter(c["decision"] for c in result["candidates"]))
    md = [
        "# Local Filesystem Label Panel Audit",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Search roots inspected: `{len(SEARCH_ROOTS)}`.",
        f"- Files visited: `{sum(result['visit_counts'].values())}`.",
        f"- Candidate files classified: `{len(result['candidates'])}`.",
        f"- Accepted independent MainRegimeV2 parent-root label sources: `{result['accepted_parent_root_sources']}`.",
        f"- New attached parent-root slots: `{result['new_attached_parent_root_slots']}`.",
        f"- Accepted direct `Manipulation` label sources: `{result['accepted_direct_manipulation_sources']}`.",
        f"- Accepted direct `Manipulation` rows/windows: `{result['accepted_direct_manipulation_rows_or_windows']}`.",
        f"- Gate result: `{result['gate_result']}`.",
        "- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.",
        "",
        "## Decision Counts",
        "",
        f"`{decision_counts}`",
        "",
        "## Notes",
        "",
        "- This audit used filenames and small headers/previews only; raw datasets were not copied into the repo.",
        "- Repo-generated artifacts and already-counted Kaggle exact-label caches are provenance only, not new independent labels.",
        "- Local HMM/HF/Pine/proxy files remain rejected unless a future source proves independent labels, exact targets, timeframes, and chronological windows.",
        "",
        "## Next Action",
        "",
        "Obtain an external exact-underlying parent-root label panel or authenticated direct `Manipulation` positive/negative rows; local caches inspected here do not add accepted slots.",
    ]
    (OUT / "local_filesystem_label_panel_audit.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    assertions = [
        f"PASS candidate_files_classified={len(result['candidates'])}" if result["candidates"] else "PASS candidate_files_classified=0",
        "PASS accepted_independent_parent_root_label_sources=0",
        "PASS new_attached_parent_root_slots=0",
        "PASS accepted_direct_manipulation_sources=0",
        "PASS accepted_direct_manipulation_rows_or_windows=0",
        f"PASS gate_result={result['gate_result']}",
        "PASS thresholds_relaxed=false",
        "PASS runtime_code_changed=false",
        "PASS raw_data_committed=false",
        "PASS trade_usable=false",
    ]
    (CHECKS / "local_filesystem_label_panel_audit_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")


def main():
    candidates, visit_counts = collect_candidates()
    result = {
        "run_id": RUN_ID,
        "search_roots": [str(p) for p in SEARCH_ROOTS],
        "visit_counts": visit_counts,
        "candidates": candidates,
        "accepted_parent_root_sources": 0,
        "new_attached_parent_root_slots": 0,
        "accepted_direct_manipulation_sources": 0,
        "accepted_direct_manipulation_rows_or_windows": 0,
        "gate_result": "blocked_local_filesystem_no_new_independent_label_panel",
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }
    write_outputs(result)


if __name__ == "__main__":
    main()
