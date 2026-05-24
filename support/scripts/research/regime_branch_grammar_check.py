#!/usr/bin/env python3
"""Validate Board B branch paths against regime/profit-factor grammar."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import regime_factor_tree_normalizer as tree_normalizer
import regime_ontology_manifest as ontology


KNOWN_SUB_REGIME_LABELS = (
    set(ontology.SECONDARY_LABELS)
    | set(ontology.TRANSITION_LABELS)
    | set(ontology.DIMENSION_LABELS.get("volatility", []))
    | set(ontology.DIMENSION_LABELS.get("liquidity", []))
    | set(ontology.DIMENSION_LABELS.get("structure", []))
    | set(ontology.DIMENSION_LABELS.get("behavior", []))
    | {
        "AthleticApparelOpeningDrive",
        "BrokerDealerUltimateTrixReclaim",
        "BybitLayer2KeltnerAtrPullback",
        "BybitLiquiditySweep",
        "CreativeSoftwareKlingerVolumeFlow",
        "CryptoDeMarkerOscillatorReclaim",
        "CryptoForceIndexDisplacementReclaim",
        "CryptoKstCoppockMomentum",
        "EcommerceMassIndexRangeBulgeReversal",
        "LiquiditySweepRejectShort",
        "MomentumPersistence",
        "OpeningDrive",
        "PullbackContinuation",
        "RootEvidencePullbackMssCisd",
        "SessionLiquidity",
        "SemiconductorEquipmentHeikinAshiAtrTrend",
    }
)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def is_profit_factor_segment(segment: str) -> bool:
    stripped = segment.strip()
    if not stripped:
        return False
    if "_" in stripped or "-" in stripped:
        return True
    if any(char.isdigit() for char in stripped):
        return True
    return stripped[:1].islower()


def segment_role(index: int, segment: str, profit_started: bool) -> str:
    if index == 0:
        return "main_regime"
    if profit_started:
        return "profit_factor"
    if segment in KNOWN_SUB_REGIME_LABELS and not is_profit_factor_segment(segment):
        return "sub_regime"
    if segment in tree_normalizer.KNOWN_MAIN_REGIMES:
        return "sub_regime"
    if is_profit_factor_segment(segment):
        return "profit_factor"
    return "sub_regime"


def check_branch_path(
    branch_path: str | None,
    labels: dict[str, str] | None = None,
) -> dict[str, Any]:
    normalized = tree_normalizer.normalize_branch_path(branch_path, labels or {})
    canonical = normalized["canonical_branch_path"]
    parts = tree_normalizer.split_path(canonical)
    violations: list[str] = []

    if not normalized["canonical_root_ok"]:
        violations.extend(
            f"canonical_root_violation:{violation}"
            for violation in normalized["violations"]
        )
    if (branch_path or "") != canonical:
        violations.append("branch_path_not_canonical_regime_root")
    if len(parts) < 3:
        violations.append("branch_path_too_short_for_regime_profit_branch")

    roles: list[str] = []
    profit_started = False
    for index, segment in enumerate(parts):
        if index == 0 and segment not in tree_normalizer.KNOWN_MAIN_REGIMES:
            violations.append(f"missing_main_regime_root:value={segment}")
        if profit_started and (
            segment in tree_normalizer.KNOWN_MAIN_REGIMES
            or segment in KNOWN_SUB_REGIME_LABELS
        ):
            violations.append(
                f"regime_segment_after_profit_factor:index={index}:value={segment}"
            )
        role = segment_role(index, segment, profit_started)
        roles.append(role)
        if role == "profit_factor":
            profit_started = True

    if "profit_factor" not in roles:
        violations.append("missing_profit_factor_segment")

    return {
        "ok": not violations,
        "decision": "branch_grammar_ok" if not violations else "branch_grammar_violation",
        "violations": sorted(set(violations)),
        "branch_path": branch_path or "",
        "canonical_branch_path": canonical,
        "normalized": normalized,
        "segments": parts,
        "segment_roles": roles,
    }


def branch_path_field_violations(
    payload: dict[str, Any],
    labels: dict[str, str],
    canonical_branch_path: str,
) -> list[str]:
    violations: list[str] = []
    for key in (
        "branch_path",
        "regime_profit_branch_path",
        "rooted_branch_path",
        "branch_path_template",
    ):
        value = payload.get(key)
        if not isinstance(value, str) or not value:
            continue
        normalized = tree_normalizer.normalize_branch_path(value, labels)
        if value != normalized["canonical_branch_path"]:
            violations.append(f"branch_path_field_not_canonical:{key}")
        if normalized["canonical_branch_path"] != canonical_branch_path:
            violations.append(f"branch_path_field_mismatch:{key}")

    branch_paths = payload.get("branch_paths")
    if isinstance(branch_paths, list):
        for index, value in enumerate(branch_paths):
            if not isinstance(value, str) or not value:
                continue
            normalized = tree_normalizer.normalize_branch_path(value, labels)
            if value != normalized["canonical_branch_path"]:
                violations.append(f"branch_paths_field_not_canonical:{index}")
            if normalized["canonical_branch_path"] != canonical_branch_path:
                violations.append(f"branch_paths_field_mismatch:{index}")
    return violations


def check_metrics_file(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    labels = tree_normalizer.extract_portability_labels(payload)
    report = check_branch_path(tree_normalizer.metrics_branch_path(payload), labels)
    report["violations"] = sorted(
        set(
            report["violations"]
            + branch_path_field_violations(
                payload,
                labels,
                report["canonical_branch_path"],
            )
        )
    )
    report["ok"] = not report["violations"]
    report["file"] = str(path)
    report["decision"] = payload.get("decision") or report["decision"]
    if report["violations"] and report["decision"] == "branch_grammar_ok":
        report["decision"] = "branch_grammar_violation"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path, help="Metrics JSON files to check")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    reports = [check_metrics_file(path) for path in args.files]
    print(json.dumps(reports, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0 if all(report["ok"] for report in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
