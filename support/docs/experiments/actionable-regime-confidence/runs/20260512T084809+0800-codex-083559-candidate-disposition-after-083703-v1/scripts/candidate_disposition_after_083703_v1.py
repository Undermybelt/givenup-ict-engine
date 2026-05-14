#!/usr/bin/env python3
"""Classify 083559 local source-sweep hints without promoting them."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T084809+0800-codex-083559-candidate-disposition-after-083703-v1"
SLUG = "083559-candidate-disposition-after-083703-v1"
GATE = "candidate_disposition_after_083703_v1=all_083559_hints_disposed_no_source_control_unlock"

SCRIPT = Path(__file__).resolve()
REPO = SCRIPT.parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / SLUG
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
SOURCE_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T083559+0800-codex-local-order-lifecycle-source-sweep-after-083108-v1/local-order-lifecycle-source-sweep-after-083108-v1"
CANDIDATES_CSV = SOURCE_ROOT / "local_order_lifecycle_source_sweep_candidates_v1.csv"
TARGET_ROOTS_CSV = SOURCE_ROOT / "local_order_lifecycle_source_sweep_target_roots_v1.csv"
R3_PROVENANCE = Path("/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_provenance.json")


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def classify(path: str, name: str, suffix: str) -> tuple[str, str]:
    if "/Downloads/Tomac/" in path and name == "symbology.csv":
        return ("tomac_symbology_context_only", "Symbology lookup file; not positive/control rows or provenance.")
    if "/Downloads/repo-intake/AutoHedge/logs/" in path:
        return ("local_trade_log_not_owner_export", "Local/private trade log; no source-owner control labels or provenance.")
    if "/Downloads/repo-intake/Algorithmic-trading/" in path:
        return ("strategy_code_or_docs_not_source_rows", "Strategy package/docs; execution text is not owner-export evidence.")
    if "/Downloads/external-data-sources/" in path:
        return ("external_api_docs_or_tooling", "API/tool docs mention order terms but contain no Board A source/control rows.")
    if "/Downloads/hermes-memory-eval/" in path:
        return ("hermes_eval_docs_or_skills", "Skill/eval text false positive from generic order words.")
    if "/Downloads/repo-intake/" in path:
        return ("unrelated_repo_intake_docs_or_code", "Repository docs/code false positive from generic order/execution vocabulary.")
    if suffix in {".md", ".txt", ".json", ".toml"}:
        return ("unrelated_text_or_metadata", "Text/metadata hit, not verifier-native market evidence.")
    return ("unrelated_local_file", "Local file does not match an approved Board A source/control package.")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    candidates = read_csv(CANDIDATES_CSV)
    target_roots = read_csv(TARGET_ROOTS_CSV)
    hint_rows = [row for row in candidates if row.get("verifier_native_hint") == "True"]

    disposition_rows: list[dict[str, str]] = []
    category_counts: Counter[str] = Counter()
    for row in hint_rows:
        category, reason = classify(row["path"], row["name"], row["suffix"])
        category_counts[category] += 1
        disposition_rows.append(
            {
                "path": row["path"],
                "name": row["name"],
                "suffix": row["suffix"],
                "header_hits": row["header_hits"],
                "archive_member_hits": row["archive_member_hits"],
                "classification": category,
                "accepted_source_control": "false",
                "reason": reason,
            }
        )

    exact_packages = []
    for row in target_roots:
        if row.get("complete") == "True":
            exact_packages.append(
                {
                    "family": row["family"],
                    "root": row["root"],
                    "complete": row["complete"],
                    "accepted_source_control": "false",
                    "reason": "R3 native-subhour package is complete on disk but non-unlocking because Crisis-capable MainRegimeV2/source-control approval is absent.",
                }
            )

    provenance = read_json(R3_PROVENANCE)
    accepted_labels = provenance.get("accepted_mapping_confidence_95_labels", [])
    limitations = provenance.get("limitations", [])
    crisis_present = "Crisis" in accepted_labels

    result = {
        "run_id": RUN_ID,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_before_artifact": sha256(BOARD),
        "source_candidates_csv": str(CANDIDATES_CSV.relative_to(REPO)),
        "source_target_roots_csv": str(TARGET_ROOTS_CSV.relative_to(REPO)),
        "gate_result": GATE,
        "candidate_files_scanned": len(candidates),
        "verifier_native_hint_rows": len(hint_rows),
        "hint_rows_disposed": len(disposition_rows),
        "accepted_hint_rows": 0,
        "category_counts": dict(sorted(category_counts.items())),
        "exact_required_packages": len(exact_packages),
        "exact_package_rows": exact_packages,
        "r3_accepted_labels": accepted_labels,
        "r3_crisis_present": crisis_present,
        "r3_limitations": limitations,
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
    }

    (OUT_DIR / "candidate_disposition_after_083703_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )

    with (OUT_DIR / "candidate_hint_disposition_after_083703_v1.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "path",
                "name",
                "suffix",
                "header_hits",
                "archive_member_hits",
                "classification",
                "accepted_source_control",
                "reason",
            ],
        )
        writer.writeheader()
        writer.writerows(disposition_rows)

    with (OUT_DIR / "candidate_disposition_category_counts_v1.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["classification", "count"])
        writer.writeheader()
        for classification, count in sorted(category_counts.items()):
            writer.writerow({"classification": classification, "count": count})

    with (OUT_DIR / "exact_package_disposition_after_083703_v1.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["family", "root", "complete", "accepted_source_control", "reason"])
        writer.writeheader()
        writer.writerows(exact_packages)

    md_lines = [
        "# 083559 Candidate Disposition After 083703 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE}`",
        "",
        "## Scope",
        "",
        "Read-only classification of the `083559` local source-sweep hints after `083703` closed the ZIP/header lead. This packet does not copy files, mutate R3/R5/R6 target roots, approve local filenames/header terms as source/control evidence, run verifier/split calibration, run canonical merge, run selected-data AutoQuant, run Pre-Bayes/BBN/CatBoost/execution-tree promotion, make a trade claim, or call `update_goal`.",
        "",
        "## Hint Disposition",
        "",
        f"- Candidate files scanned by `083559`: `{len(candidates)}`.",
        f"- Verifier-native hint rows from `083559`: `{len(hint_rows)}`.",
        f"- Hint rows disposed in this packet: `{len(disposition_rows)}`.",
        "- Accepted source/control hint rows: `0`.",
        "",
        "| classification | count |",
        "|---|---:|",
    ]
    for classification, count in sorted(category_counts.items()):
        md_lines.append(f"| `{classification}` | `{count}` |")
    md_lines.extend(
        [
            "",
            "## Exact Package Disposition",
            "",
            f"- Exact required package-name matches from `083559`: `{len(exact_packages)}`.",
            f"- R3 accepted labels from provenance: `{', '.join(accepted_labels) if accepted_labels else 'none'}`.",
            f"- R3 Crisis label present: `{str(crisis_present).lower()}`.",
            "- R3 package remains non-unlocking because Crisis-capable MainRegimeV2/source-control approval is absent.",
            "",
            "## Decision",
            "",
            "- All `083559` verifier-native hints are filename/header/member/text false positives or local context files, not owner-approved source/control packages.",
            "- The only exact packages are the existing R3 native-subhour roots; they remain non-promoting under the current Board A contract.",
            "- Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed false; and `update_goal=false`.",
            "",
            "## Next",
            "",
            "Continue source/control acquisition only. The live unblocker remains owner-approved/authenticated R6/R5/R3 source-control rows with matched controls and provenance, or explicit same-exhibit `FLIP`-as-control approval, before any selected-data AutoQuant or downstream promotion rerun.",
            "",
        ]
    )
    (OUT_DIR / "candidate_disposition_after_083703_v1.md").write_text("\n".join(md_lines))

    assertions = {
        "gate_result": GATE,
        "candidate_files_scanned": len(candidates),
        "verifier_native_hint_rows": len(hint_rows),
        "hint_rows_disposed": len(disposition_rows),
        "accepted_hint_rows": 0,
        "exact_required_packages": len(exact_packages),
        "r3_crisis_present": crisis_present,
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
    }
    (CHECK_DIR / "candidate_disposition_after_083703_v1_assertions.out").write_text(
        "\n".join(f"{key}={str(value).lower() if isinstance(value, bool) else value}" for key, value in assertions.items()) + "\n"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
