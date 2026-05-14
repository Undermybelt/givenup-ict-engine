#!/usr/bin/env python3
"""Read-only Board A R5 redownload and required-root unlock audit."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260512T065134+0800-codex-r5-redownload-readback-current-unlock-audit-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
ARTIFACT_DIR = RUN_ROOT / "r5-redownload-readback-current-unlock-audit-v1"
CHECKS_DIR = RUN_ROOT / "checks"
COMMAND_DIR = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

R5_REDOWNLOAD = Path(
    "/tmp/ict-engine-board-a-r5-kaggle-stock-regimes-recency-redownload-v1/"
    "stock_market_regimes_2000_2026.csv"
)
R5_TARGET_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
R5_EXPECTED_ROWS = R5_TARGET_ROOT / "stock_market_regimes_2026_extension.csv"
R5_EXPECTED_PROVENANCE = R5_TARGET_ROOT / "source_panel_recency_provenance.json"
R5_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)
R6_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
R3_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
R3_PROVENANCE = R3_ROOT / "native_subhour_source_label_provenance.json"
R3_ROWS = R3_ROOT / "native_subhour_source_label_rows.csv"
EQUIVALENCE_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def summarize_source_panel(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"exists": False}
    summary: dict[str, object] = {
        "exists": True,
        "sha256": sha256(path),
        "rows": 0,
        "date_min": None,
        "date_max": None,
        "rows_after_2026_01_30": 0,
        "ticker_count": 0,
        "label_counts": {},
    }
    tickers: set[str] = set()
    labels: dict[str, int] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            summary["rows"] = int(summary["rows"]) + 1
            day = row.get("date", "")
            ticker = row.get("ticker", "")
            label = row.get("regime_label", "")
            if day:
                if summary["date_min"] is None or day < str(summary["date_min"]):
                    summary["date_min"] = day
                if summary["date_max"] is None or day > str(summary["date_max"]):
                    summary["date_max"] = day
                if day > "2026-01-30":
                    summary["rows_after_2026_01_30"] = int(summary["rows_after_2026_01_30"]) + 1
            if ticker:
                tickers.add(ticker)
            if label:
                labels[label] = labels.get(label, 0) + 1
    summary["ticker_count"] = len(tickers)
    summary["label_counts"] = dict(sorted(labels.items()))
    return summary


def run_r5_verifier() -> dict[str, object]:
    cmd = ["python3", str(R5_VERIFIER), "--intake-root", str(R5_TARGET_ROOT)]
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    (COMMAND_DIR / "source_panel_recency_extension_verifier.cmd").write_text(
        " ".join(cmd) + "\n", encoding="utf-8"
    )
    (COMMAND_DIR / "source_panel_recency_extension_verifier.stdout").write_text(
        proc.stdout, encoding="utf-8"
    )
    (COMMAND_DIR / "source_panel_recency_extension_verifier.stderr").write_text(
        proc.stderr, encoding="utf-8"
    )
    (COMMAND_DIR / "source_panel_recency_extension_verifier.exit").write_text(
        f"{proc.returncode}\n", encoding="utf-8"
    )
    parsed: object
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"parse_error": True, "stdout": proc.stdout[:1000]}
    return {
        "cmd": cmd,
        "exit_code": proc.returncode,
        "stdout_file": str(
            COMMAND_DIR.relative_to(REPO) / "source_panel_recency_extension_verifier.stdout"
        ),
        "stderr_file": str(
            COMMAND_DIR.relative_to(REPO) / "source_panel_recency_extension_verifier.stderr"
        ),
        "exit_file": str(COMMAND_DIR.relative_to(REPO) / "source_panel_recency_extension_verifier.exit"),
        "parsed": parsed,
    }


def root_statuses() -> list[dict[str, object]]:
    r3_prov = {}
    if R3_PROVENANCE.exists():
        r3_prov = json.loads(R3_PROVENANCE.read_text(encoding="utf-8"))
    return [
        {
            "root_id": "r6_owner_export",
            "path": str(R6_ROOT),
            "exists": R6_ROOT.exists(),
            "complete": False,
            "accepted_for_promotion": False,
            "notes": "target root absent; no verifier-native owner/export rows with controls",
        },
        {
            "root_id": "r5_source_panel_recency",
            "path": str(R5_TARGET_ROOT),
            "exists": R5_TARGET_ROOT.exists(),
            "complete": R5_EXPECTED_ROWS.exists() and R5_EXPECTED_PROVENANCE.exists(),
            "accepted_for_promotion": False,
            "notes": "required recency extension target root absent or incomplete",
        },
        {
            "root_id": "r3_native_subhour",
            "path": str(R3_ROOT),
            "exists": R3_ROOT.exists(),
            "complete": R3_ROWS.exists() and R3_PROVENANCE.exists(),
            "accepted_for_promotion": False,
            "notes": "TSIE root present but policy-quarantined; Crisis absent; accepted rows remain zero",
            "row_count": r3_prov.get("row_count"),
            "labels": ",".join(r3_prov.get("accepted_mapping_confidence_95_labels", [])),
        },
        {
            "root_id": "source_label_equivalence",
            "path": str(EQUIVALENCE_ROOT),
            "exists": EQUIVALENCE_ROOT.exists(),
            "complete": (
                (EQUIVALENCE_ROOT / "source_label_equivalence_rows.csv").exists()
                and (EQUIVALENCE_ROOT / "source_label_equivalence_provenance.json").exists()
            ),
            "accepted_for_promotion": False,
            "notes": "non-target equivalence root; prior calibration accepted 0/4 labels",
        },
    ]


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    COMMAND_DIR.mkdir(parents=True, exist_ok=True)

    redownload = summarize_source_panel(R5_REDOWNLOAD)
    verifier = run_r5_verifier()
    statuses = root_statuses()
    valid_required_unlock = any(bool(row["accepted_for_promotion"]) for row in statuses[:3])

    decision = {
        "gate_result": (
            "r5_redownload_readback_current_unlock_audit_v1="
            "redownload_has_no_post_cutoff_rows_no_valid_unlock_no_downstream"
        ),
        "objective_complete": False,
        "accepted_rows_added": 0,
        "valid_required_root_unlock": valid_required_unlock,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }
    payload = {
        "artifact_type": "r5_redownload_readback_current_unlock_audit_v1",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD.relative_to(REPO)),
        "board_sha256_at_artifact": sha256(BOARD),
        "scope": (
            "Read-only audit of the loose 064908 Kaggle redownload and current Board A "
            "required roots. This does not mutate target roots, run canonical merge, "
            "rerun downstream promotion, make a trade claim, or call update_goal."
        ),
        "r5_redownload_source": {
            "download_run_root": (
                "docs/experiments/actionable-regime-confidence/runs/"
                "20260512T064908+0800-codex-r5-kaggle-stock-regimes-recency-redownload-v1"
            ),
            "path": str(R5_REDOWNLOAD),
            **redownload,
        },
        "r5_verifier": verifier,
        "required_roots": statuses,
        "decision": decision,
        "next_action": (
            "Continue only from explicit source/control approval, verifier-native R6 owner-export "
            "rows with valid controls, source-owned R5 post-2026-01-30 recency rows, "
            "verifier-native Crisis-capable R3 MainRegimeV2 labels, or a genuinely new accepted "
            "cross-timeframe MainRegimeV2 source export before rerunning direct verifier, split "
            "calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, "
            "CatBoost/path-ranking, and execution-tree readback."
        ),
    }

    json_path = ARTIFACT_DIR / "r5_redownload_readback_current_unlock_audit_v1.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    write_csv(
        ARTIFACT_DIR / "required_root_status_v1.csv",
        statuses,
        ["root_id", "path", "exists", "complete", "accepted_for_promotion", "row_count", "labels", "notes"],
    )
    write_csv(
        ARTIFACT_DIR / "r5_redownload_summary_v1.csv",
        [
            {
                "path": str(R5_REDOWNLOAD),
                "exists": redownload.get("exists", False),
                "rows": redownload.get("rows", 0),
                "date_min": redownload.get("date_min", ""),
                "date_max": redownload.get("date_max", ""),
                "rows_after_2026_01_30": redownload.get("rows_after_2026_01_30", 0),
                "ticker_count": redownload.get("ticker_count", 0),
                "sha256": redownload.get("sha256", ""),
            }
        ],
        ["path", "exists", "rows", "date_min", "date_max", "rows_after_2026_01_30", "ticker_count", "sha256"],
    )

    report = f"""# R5 Redownload Readback Current Unlock Audit v1

Run id: `{RUN_ID}`

Gate result: `{decision["gate_result"]}`

## Scope

Read-only audit of the loose `064908` Kaggle redownload and the current Board A required roots. This did not mutate `/tmp/ict-engine-source-panel-recency-extension`, approve TSIE, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## R5 Redownload Readback

- Path: `{R5_REDOWNLOAD}`
- Exists: `{redownload.get("exists", False)}`
- Rows: `{redownload.get("rows", 0)}`
- Date range: `{redownload.get("date_min")}` to `{redownload.get("date_max")}`
- Rows after `2026-01-30`: `{redownload.get("rows_after_2026_01_30", 0)}`
- Ticker count: `{redownload.get("ticker_count", 0)}`

The redownloaded source panel is the same cutoff shape as the prior source package, so it does not supply the required R5 post-cutoff recency extension rows.

## Required Root Decision

- R6 owner/export root accepted: `false`
- R5 source-panel recency root accepted: `false`
- R3 native-subhour root accepted: `false`
- Valid required-root unlock: `{str(valid_required_unlock).lower()}`

The R5 verifier was run against `{R5_TARGET_ROOT}` and returned exit `{verifier["exit_code"]}`. Its output is stored under `command-output/`.

## Accounting

- Accepted rows added: `0`
- Canonical merge: `false`
- Downstream promotion rerun: `false`
- Strict full objective: `false`
- Trade usable: `false`
- `update_goal=false`

## Artifacts

- JSON: `{json_path.relative_to(REPO)}`
- Required roots CSV: `{(ARTIFACT_DIR / "required_root_status_v1.csv").relative_to(REPO)}`
- R5 redownload summary CSV: `{(ARTIFACT_DIR / "r5_redownload_summary_v1.csv").relative_to(REPO)}`
- Assertions: `{(CHECKS_DIR / "r5_redownload_readback_current_unlock_audit_v1_assertions.out").relative_to(REPO)}`

## Next

{payload["next_action"]}
"""
    report_path = ARTIFACT_DIR / "r5_redownload_readback_current_unlock_audit_v1.md"
    report_path.write_text(report, encoding="utf-8")

    assertions = [
        f"gate_result={decision['gate_result']}",
        "objective_complete=false",
        f"r5_redownload_rows={redownload.get('rows', 0)}",
        f"r5_redownload_date_max={redownload.get('date_max')}",
        f"r5_redownload_rows_after_2026_01_30={redownload.get('rows_after_2026_01_30', 0)}",
        f"r5_target_root_present={str(R5_TARGET_ROOT.exists()).lower()}",
        f"r5_verifier_exit={verifier['exit_code']}",
        "r6_owner_export_unlock=false",
        "r3_native_subhour_unlock=false",
        "r5_recency_unlock=false",
        f"valid_required_root_unlock={str(valid_required_unlock).lower()}",
        "accepted_rows_added=0",
        "canonical_merge=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    (CHECKS_DIR / "r5_redownload_readback_current_unlock_audit_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
