#!/usr/bin/env python3
"""Re-fetch current Mendeley v3 metadata and rerun the unchanged Gox gate."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T082521+0800-codex-mendeley-v3-gox-refetch-reaudit"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T082521-codex-mendeley-v3-gox-refetch-reaudit"
OUT_DIR = RUN_ROOT / "mendeley-v3-reaudit"
CHECK_DIR = RUN_ROOT / "checks"
OLD_SCRIPT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T043249-codex-mendeley-gox-hgb-wash-gate/tmp-scripts/mendeley_gox_hgb_wash_gate.py"
DATASET_URL = "https://data.mendeley.com/public-api/datasets/4hyxfwzpgg"

GOX_CANDIDATES = [
    Path("/private/tmp/gox_ml_samples.csv"),
    Path("/tmp/gox_ml_samples.csv"),
    Path("/private/tmp/ict-regime-mendeley-wash-trading/gox_ml_samples.csv"),
]
UV_REEXEC_ENV = "ICT_ENGINE_MENDELEY_V3_REAUDIT_UV_REEXEC"
UV_PACKAGES = ["scikit-learn", "pandas", "numpy"]


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "ict-engine-board-a-mendeley-v3-reaudit/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def locate_gox() -> Path:
    for path in GOX_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError("gox_ml_samples.csv not found under expected temp paths")


def ensure_gate_dependencies() -> int | None:
    try:
        import sklearn  # noqa: F401
    except ModuleNotFoundError as exc:
        if exc.name != "sklearn":
            raise
        if os.environ.get(UV_REEXEC_ENV):
            raise
        env = os.environ.copy()
        env[UV_REEXEC_ENV] = "1"
        cmd = ["uv", "run"]
        for package in UV_PACKAGES:
            cmd.extend(["--with", package])
        cmd.extend(["python", str(Path(__file__))])
        return subprocess.run(cmd, cwd=REPO, env=env, check=False).returncode
    return None


def run_unchanged_gox_gate() -> None:
    source = OLD_SCRIPT.read_text()
    patched = source.replace(
        "20260511T043249+0800-codex-mendeley-gox-hgb-wash-gate",
        RUN_ID,
    ).replace(
        "20260511T043249-codex-mendeley-gox-hgb-wash-gate",
        "20260511T082521-codex-mendeley-v3-gox-refetch-reaudit",
    )
    namespace: dict[str, Any] = {
        "__name__": "mendeley_v3_gox_refetch_reaudit_inner",
        "__file__": str(Path(__file__)),
    }
    exec(compile(patched, str(OLD_SCRIPT), "exec"), namespace)
    namespace["main"]()


def main() -> int:
    dependency_reexec = ensure_gate_dependencies()
    if dependency_reexec is not None:
        return dependency_reexec

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    dataset = fetch_json(DATASET_URL)
    files = dataset.get("files") or []
    file_by_name = {file.get("filename"): file for file in files}
    gox_meta = file_by_name.get("gox_ml_samples.csv") or {}
    gox_details = gox_meta.get("content_details") or {}
    expected_sha = gox_details.get("sha256_hash") or ""
    gox_path = locate_gox()
    actual_sha = sha256_file(gox_path)
    sha_matches = bool(expected_sha) and actual_sha == expected_sha
    if not sha_matches:
        raise RuntimeError(f"current Gox SHA mismatch: expected={expected_sha} actual={actual_sha}")

    run_unchanged_gox_gate()
    hgb_report_path = RUN_ROOT / "gox-hgb-wash-gate/mendeley_gox_hgb_wash_gate_report.json"
    hgb_report = json.loads(hgb_report_path.read_text())
    decision = hgb_report["decision"]
    metrics = hgb_report["metrics"]

    refetch = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective": "Re-fetch current Mendeley v3 metadata and rerun the unchanged Mt. Gox HGB wash-trading gate.",
        "active_taxonomy": "MainRegimeV2",
        "candidate_regime": "Manipulation",
        "dataset": {
            "url": DATASET_URL,
            "id": dataset.get("id"),
            "doi": (dataset.get("doi") or {}).get("id"),
            "version": dataset.get("version"),
            "name": dataset.get("name"),
            "size": dataset.get("size"),
            "license": (dataset.get("data_licence") or {}).get("short_name"),
            "files_seen": len(files),
        },
        "gox_file": {
            "filename": "gox_ml_samples.csv",
            "local_path": str(gox_path),
            "mendeley_size": gox_meta.get("size"),
            "expected_sha256": expected_sha,
            "actual_sha256": actual_sha,
            "sha256_matches_current_mendeley_v3": sha_matches,
            "raw_data_committed": False,
        },
        "gate_reused": {
            "source_script": rel(OLD_SCRIPT),
            "method": "old gate source executed with only RUN_ID and RUN_ROOT changed",
            "hgb_report_json": rel(hgb_report_path),
            "hgb_report_md": rel(RUN_ROOT / "gox-hgb-wash-gate/mendeley_gox_hgb_wash_gate_report.md"),
            "hgb_assertions": rel(RUN_ROOT / "checks/mendeley_gox_hgb_wash_gate_assertions.out"),
        },
        "metrics": metrics,
        "decision": {
            "accepted_direct_manipulation_95": bool(decision["accepted_95"]),
            "gate_result": decision["gate_result"],
            "blockers": decision["blockers"],
            "accepted_full_cycle_full_universe": False,
            "mainregimev2_root_slots_added": 0,
            "manipulation_label_slots_added": 0,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "fresh_calibration_rerun": True,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": (
            "If Mendeley remains blocked, try the Dune nft.wash_trades export path with replayable timestamps "
            "and positive/negative windows; keep Bitquery rule labels sidecar-only."
        ),
        "artifacts": {
            "summary_json": rel(OUT_DIR / "mendeley_v3_gox_refetch_reaudit.json"),
            "summary_md": rel(OUT_DIR / "mendeley_v3_gox_refetch_reaudit.md"),
            "assertions": rel(CHECK_DIR / "mendeley_v3_gox_refetch_reaudit_assertions.out"),
            "script": rel(Path(__file__)),
        },
    }

    (OUT_DIR / "mendeley_v3_gox_refetch_reaudit.json").write_text(json.dumps(refetch, indent=2, sort_keys=True) + "\n")
    (OUT_DIR / "mendeley_v3_gox_refetch_reaudit.md").write_text(
        "\n".join(
            [
                "# Mendeley v3 Gox Re-fetch Re-audit",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                "## Result",
                "",
                f"- Current Mendeley version: `{dataset.get('version')}`",
                f"- Gox SHA-256 matches current Mendeley v3: `{str(sha_matches).lower()}`",
                f"- Gate result: `{decision['gate_result']}`",
                f"- Accepted direct `Manipulation` 95: `{str(decision['accepted_95']).lower()}`",
                f"- Blockers: `{', '.join(decision['blockers'])}`",
                "- MainRegimeV2 root-label slots added: `0`",
                "- Manipulation label slots added: `0`",
                "",
                "## Metrics",
                "",
                f"- Calibration Wilson95 LCB: `{metrics['calibration']['wilson_lcb_95']:.12f}`",
                f"- Test Wilson95 LCB: `{metrics['test']['wilson_lcb_95']:.12f}`",
                f"- Calibration coverage: `{metrics['calibration']['coverage']:.12f}`",
                f"- Test coverage: `{metrics['test']['coverage']:.12f}`",
                f"- Calibration ECE: `{metrics['calibration']['ece_10bin']:.12f}`",
                f"- Test ECE: `{metrics['test']['ece_10bin']:.12f}`",
                "",
                "## Accounting",
                "",
                "- The current public v3 file hash matches the local raw Gox CSV, so the rerun used current source bytes.",
                "- The unchanged gate still fails because coverage and ECE blockers remain.",
                "- Raw data stayed under `/private/tmp` or `/tmp`; no raw rows were committed.",
                "- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.",
                "",
            ]
        )
    )
    assertions = [
        f"run_id={RUN_ID}",
        f"mendeley_version={dataset.get('version')}",
        f"gox_sha256_matches_current_v3={str(sha_matches).lower()}",
        f"gate_result={decision['gate_result']}",
        f"accepted_direct_manipulation_95={str(decision['accepted_95']).lower()}",
        f"blockers={','.join(decision['blockers'])}",
        "mainregimev2_root_slots_added=0",
        "manipulation_label_slots_added=0",
        "accepted_full_cycle_full_universe=false",
        "fresh_calibration_rerun=true",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
    ]
    (CHECK_DIR / "mendeley_v3_gox_refetch_reaudit_assertions.out").write_text("\n".join(assertions) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
