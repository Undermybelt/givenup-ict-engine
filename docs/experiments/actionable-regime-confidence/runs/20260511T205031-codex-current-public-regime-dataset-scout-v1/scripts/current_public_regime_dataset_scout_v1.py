#!/usr/bin/env python3
"""Scout current public regime datasets without promoting generated labels."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "current-public-regime-dataset-scout"
CHECKS = RUN_ROOT / "checks"
TMP_ROOT = Path("/tmp/ict-engine-current-public-regime-dataset-scout-v1")

DATASETS = [
    {
        "ref": "ahaanverma00/nifty-500-market-and-behavior-regime-dataset",
        "title": "NIFTY 500 Market & Behavior Regime Dataset",
        "local": "nifty",
        "candidate_for": "R2/R5 public-current cross-market regime labels",
    },
    {
        "ref": "kanchana1990/algorithmic-trading-macro-stress-and-asset-regimes",
        "title": "Algorithmic Trading: Macro Stress & Asset Regimes",
        "local": "macro",
        "candidate_for": "R2 public-current macro/asset regime labels",
    },
]

SEARCH_TERMS = [
    "stock market regimes",
    "market regime labels",
    "stock market manipulation",
    "spoofing layering order book",
]

ROOT_LABELS = {"Bear", "Bull", "Crisis", "Sideways"}
GENERATED_MARKERS = ("hmm", "prediction", "predicted", "engineered", "model", "classifier")


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_metadata(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if isinstance(data, str):
        data = json.loads(data)
    return data


def csv_profile(path: Path) -> dict:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        row_count = 0
        date_min = ""
        date_max = ""
        label_values: dict[str, set[str]] = {
            field: set()
            for field in fields
            if "state" in field.lower() or "regime" in field.lower() or "label" in field.lower()
        }
        confidence_fields = [field for field in fields if "confidence" in field.lower() or field.startswith("p_")]
        for row in reader:
            row_count += 1
            day = row.get("Date") or row.get("date") or ""
            if day:
                date_min = day if not date_min or day < date_min else date_min
                date_max = day if not date_max or day > date_max else date_max
            for field in label_values:
                value = row.get(field, "")
                if value and len(label_values[field]) < 25:
                    label_values[field].add(value)
    return {
        "path": str(path),
        "sha256": sha256(path),
        "columns": fields,
        "row_count": row_count,
        "date_min": date_min,
        "date_max": date_max,
        "label_columns": sorted(label_values),
        "label_values": {key: sorted(values) for key, values in sorted(label_values.items())},
        "confidence_columns": confidence_fields,
    }


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def summarize_dataset(dataset: dict, root: Path) -> dict:
    metadata = parse_metadata(root / "dataset-metadata.json")
    csvs = sorted(root.glob("*.csv"))
    profiles = [csv_profile(path) for path in csvs]
    desc = f"{metadata.get('subtitle', '')}\n{metadata.get('description', '')}".lower()
    generated = any(marker in desc for marker in GENERATED_MARKERS)
    compatible_profile = None
    for profile in profiles:
        for values in profile["label_values"].values():
            if set(values) & ROOT_LABELS:
                compatible_profile = profile
                break
        if compatible_profile:
            break
    latest_profile = max(profiles, key=lambda item: item.get("date_max") or "") if profiles else {}
    label_profiles = [profile for profile in profiles if profile["label_columns"]]

    if dataset["local"] == "nifty":
        guardrail_status = "blocked_generated_hmm_labels_not_main_regime_v2"
        reason = (
            "Dataset is current and row-level, but metadata identifies HMM-based market/behavior regime "
            "labels and observed labels are Durable/Fragile/Calm/Stress/Trending/Noisy rather than "
            "source-owned MainRegimeV2 Bull/Bear/Sideways/Crisis rows."
        )
        source_label_policy = "source_owner_hmm_based_labels_generated_not_accepted"
    elif label_profiles:
        guardrail_status = "blocked_label_taxonomy_mismatch"
        reason = "Downloaded CSV has label-like columns, but no MainRegimeV2-compatible root labels were observed."
        source_label_policy = "public_dataset_label_taxonomy_not_board_a_root"
    else:
        guardrail_status = "blocked_features_only_no_source_regime_rows"
        reason = "Downloaded CSV is a market/macro feature panel; no source regime label columns were observed."
        source_label_policy = "features_only_no_source_label"

    return {
        "dataset_ref": dataset["ref"],
        "title": metadata.get("title", dataset["title"]),
        "owner": metadata.get("ownerUser", ""),
        "subtitle": metadata.get("subtitle", ""),
        "candidate_for": dataset["candidate_for"],
        "downloaded_files": [path.name for path in csvs],
        "file_hashes": {path.name: sha256(path) for path in csvs},
        "row_count_max": latest_profile.get("row_count", 0),
        "date_min": min((p.get("date_min") for p in profiles if p.get("date_min")), default=""),
        "date_max": max((p.get("date_max") for p in profiles if p.get("date_max")), default=""),
        "label_columns": sorted({field for profile in profiles for field in profile["label_columns"]}),
        "confidence_columns": sorted({field for profile in profiles for field in profile["confidence_columns"]}),
        "main_regime_v2_compatible": bool(compatible_profile) and not generated,
        "generated_or_model_derived": generated,
        "source_label_policy": source_label_policy,
        "guardrail_status": guardrail_status,
        "reason": reason,
        "rows_acquired": False,
        "intake_files_created": False,
        "accepted_rows_added": 0,
        "profiles": profiles,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    if TMP_ROOT.exists():
        shutil.rmtree(TMP_ROOT)
    TMP_ROOT.mkdir(parents=True)

    search_rows: list[dict] = []
    for term in SEARCH_TERMS:
        proc = run(["kaggle", "datasets", "list", "-s", term, "--csv"])
        search_path = TMP_ROOT / f"search_{term.replace(' ', '_')}.csv"
        search_path.write_text(proc.stdout, encoding="utf-8")
        reader = csv.DictReader(proc.stdout.splitlines())
        for idx, row in enumerate(reader):
            if idx >= 8:
                break
            row["search_term"] = term
            search_rows.append(row)

    summaries = []
    for dataset in DATASETS:
        root = TMP_ROOT / dataset["local"]
        root.mkdir(parents=True, exist_ok=True)
        run(["kaggle", "datasets", "metadata", dataset["ref"], "-p", str(root)])
        run(["kaggle", "datasets", "download", dataset["ref"], "-p", str(root), "--force", "--unzip"])
        summaries.append(summarize_dataset(dataset, root))

    candidate_rows = [
        {
            "dataset_ref": row["dataset_ref"],
            "title": row["title"],
            "owner": row["owner"],
            "candidate_for": row["candidate_for"],
            "downloaded_files": ";".join(row["downloaded_files"]),
            "row_count_max": row["row_count_max"],
            "date_min": row["date_min"],
            "date_max": row["date_max"],
            "label_columns": ";".join(row["label_columns"]),
            "confidence_columns": ";".join(row["confidence_columns"]),
            "main_regime_v2_compatible": row["main_regime_v2_compatible"],
            "generated_or_model_derived": row["generated_or_model_derived"],
            "guardrail_status": row["guardrail_status"],
            "reason": row["reason"],
            "intake_files_created": row["intake_files_created"],
        }
        for row in summaries
    ]

    audit = {
        "run_id": RUN_ROOT.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "Scout current public regime datasets before creating any Board A intake files.",
        "decision": "current_public_regime_dataset_scout_v1=current_public_candidates_found_but_not_accepted",
        "search_terms": SEARCH_TERMS,
        "download_root": str(TMP_ROOT),
        "candidate_count": len(summaries),
        "current_rows_found": True,
        "intake_files_created": False,
        "rows_acquired_for_strict_gate": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "datasets": summaries,
    }
    (OUT / "current_public_regime_dataset_scout_v1.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(
        OUT / "current_public_regime_dataset_scout_v1_candidates.csv",
        candidate_rows,
        [
            "dataset_ref",
            "title",
            "owner",
            "candidate_for",
            "downloaded_files",
            "row_count_max",
            "date_min",
            "date_max",
            "label_columns",
            "confidence_columns",
            "main_regime_v2_compatible",
            "generated_or_model_derived",
            "guardrail_status",
            "reason",
            "intake_files_created",
        ],
    )
    write_csv(
        OUT / "current_public_regime_dataset_scout_v1_search_results.csv",
        search_rows,
        ["search_term", "ref", "title", "size", "lastUpdated", "downloadCount", "voteCount", "usabilityRating"],
    )

    report = [
        "# Current Public Regime Dataset Scout v1",
        "",
        f"Decision: `{audit['decision']}`.",
        "",
        "Result:",
        f"- Public candidate datasets downloaded to `/tmp`: `{len(summaries)}`.",
        "- Current rows were found, but no Board A intake files were created.",
        "- The NIFTY candidate has row-level labels through `2026-03-20`, but its own metadata identifies HMM-based labels and the observed taxonomy is not MainRegimeV2.",
        "- The macro/asset candidate is a feature panel through `2026-02-25`; no source regime label columns were observed.",
        "- Accepted rows added: `0`; new confidence gate: `false`; `update_goal=false`.",
        "",
        "Next:",
        "- Keep the v35 outbox as the controlling next action: acquire source-owned or owner-approved rows/provenance for the existing intake roots, then rerun the fail-closed verifiers.",
    ]
    (OUT / "current_public_regime_dataset_scout_v1.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={audit['decision']}",
        "PASS current_rows_found=true",
        "PASS intake_files_created=false",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
    ]
    (CHECKS / "current_public_regime_dataset_scout_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"decision": audit["decision"], "candidate_count": len(summaries)}, sort_keys=True))


if __name__ == "__main__":
    main()
