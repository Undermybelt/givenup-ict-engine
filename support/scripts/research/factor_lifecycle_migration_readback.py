#!/usr/bin/env python3
"""Read-only migration readback for old Board B factor evidence packets."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


PAPER_VALIDATION_MIN_ROWS = 30
LIVE_EXECUTION_READINESS_FLOOR = 0.65
DECLARED_FRICTION_KEYS = (
    "net_after_declared_friction_pct",
    "instrument_cost_total_profit_pct",
    "net_after_5bps_side_pct",
    "net_after_5bps_per_side_pct",
    "5bps_per_side_total_profit_pct",
    "net_5bps",
    "net_5bps_side",
    "cost_5bps_net_ret",
)
RAW_PROFIT_KEYS = ("total_profit_pct",)
SUMMARY_CSV_NAME_MARKERS = ("cost", "gate", "rank", "terminal", "summary")


def _read_key_value_summary(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip().lstrip("-").strip()
        if not line:
            continue
        delimiter = "=" if "=" in line else ":" if ":" in line else None
        if delimiter is None:
            continue
        key, value = line.split(delimiter, 1)
        values[key.strip().lower()] = _strip_markdown_value(value)
    return values


def _strip_markdown_value(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] == "`":
        return stripped[1:-1].strip()
    return stripped


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _merge_missing(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    for key, value in extra.items():
        if key not in base and value is not None:
            base[key] = value
    return base


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _floatish(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def _intish(value: Any) -> int | None:
    parsed = _floatish(value)
    if parsed is None:
        return None
    return int(parsed)


def _first_float_from_rows(rows: list[dict[str, str]], keys: tuple[str, ...]) -> float | None:
    for row in rows:
        for key in keys:
            parsed = _floatish(row.get(key))
            if parsed is not None:
                return parsed
    return None


def _max_float_from_rows(rows: list[dict[str, str]], keys: tuple[str, ...]) -> float | None:
    values: list[float] = []
    for row in rows:
        for key in keys:
            parsed = _floatish(row.get(key))
            if parsed is not None:
                values.append(parsed)
    return max(values) if values else None


def _summary_csv_paths(summaries_dir: Path) -> list[Path]:
    if not summaries_dir.exists():
        return []
    paths: dict[Path, None] = {}
    for name in ("gate1_cost_stress.csv", "rank_rows_cost_stress.csv"):
        path = summaries_dir / name
        if path.exists():
            paths[path] = None
    for path in sorted(summaries_dir.glob("*.csv")):
        lowered = path.name.lower()
        if any(marker in lowered for marker in SUMMARY_CSV_NAME_MARKERS):
            paths[path] = None
    return sorted(paths)


def _legacy_root_csv_paths(root: Path) -> list[Path]:
    paths: dict[Path, None] = {}
    for name in ("leaderboard.csv", "summary.csv"):
        path = root / name
        if path.exists():
            paths[path] = None
    for path in sorted(root.glob("*.csv")):
        lowered = path.name.lower()
        if any(marker in lowered for marker in SUMMARY_CSV_NAME_MARKERS):
            paths[path] = None
    return sorted(paths)


def _check_json_paths(checks_dir: Path) -> list[Path]:
    if not checks_dir.exists():
        return []
    paths: dict[Path, None] = {}
    terminal_metrics = checks_dir / "terminal_metrics.json"
    if terminal_metrics.exists():
        paths[terminal_metrics] = None
    for path in sorted(checks_dir.glob("*.json")):
        paths[path] = None
    return sorted(paths)


def _legacy_summary_json_values(root: Path) -> tuple[dict[str, Any], Path | None]:
    path = root / "summary.json"
    payload = _read_json(path)
    if not payload:
        return {}, None
    values: dict[str, Any] = {}
    best = payload.get("best") if isinstance(payload.get("best"), dict) else {}
    cost_stress = best.get("cost_stress") if isinstance(best.get("cost_stress"), dict) else {}
    five_bps = cost_stress.get("5bps") if isinstance(cost_stress.get("5bps"), dict) else {}
    for key in (
        "decision",
        "regime_confidence",
        "leakage_check",
        "downstream_allowed",
        "promotion_allowed",
        "trade_usable",
    ):
        if key in payload:
            values[key] = payload[key]
    if "decision" in best:
        values["decision"] = best["decision"]
    if "trade_count" in best:
        values.setdefault("raw_scored_mature", best["trade_count"])
    if "net_ret" in five_bps:
        values["net_5bps"] = five_bps["net_ret"]
    if "trades" in five_bps:
        values.setdefault("raw_scored_mature", five_bps["trades"])
    return values, path


def _read_check_values(checks_dir: Path) -> tuple[dict[str, Any], list[Path]]:
    values: dict[str, Any] = {}
    paths = _check_json_paths(checks_dir)
    for path in paths:
        payload = _read_json(path)
        if payload:
            _merge_missing(values, payload)
            terminal_values = _terminal_metrics_values(payload)
            _merge_missing(values, terminal_values)
    return values, paths


def _expectancy_after_friction(
    *,
    rows: list[dict[str, str]],
    material_values: dict[str, Any],
    check_values: dict[str, Any],
) -> tuple[float | None, list[str]]:
    blockers: list[str] = []
    declared_sources: list[float] = []
    for row in rows:
        for key in DECLARED_FRICTION_KEYS:
            parsed = _floatish(row.get(key))
            if parsed is not None:
                declared_sources.append(parsed)
    for values in (material_values, check_values):
        for key in DECLARED_FRICTION_KEYS:
            parsed = _floatish(values.get(key))
            if parsed is not None:
                declared_sources.append(parsed)
    if declared_sources:
        return max(declared_sources), blockers

    raw_sources: list[float] = []
    for row in rows:
        for key in RAW_PROFIT_KEYS:
            parsed = _floatish(row.get(key))
            if parsed is not None:
                raw_sources.append(parsed)
    for values in (material_values, check_values):
        for key in RAW_PROFIT_KEYS:
            parsed = _floatish(values.get(key))
            if parsed is not None:
                raw_sources.append(parsed)
    if raw_sources:
        blockers.append("declared_friction_missing_raw_profit_only")
        return max(raw_sources), blockers

    return None, blockers


def _terminal_metrics_values(metrics: dict[str, Any]) -> dict[str, Any]:
    validation = metrics.get("validation") if isinstance(metrics.get("validation"), dict) else {}
    return {
        "raw_scored_mature": _first_present(
            validation.get("raw_scored_mature"),
            validation.get("raw_scored_mature_rows"),
            metrics.get("raw_scored_mature"),
            metrics.get("raw_scored_mature_rows"),
            metrics.get("mature_rows"),
        ),
        "production": _first_present(
            validation.get("production"),
            validation.get("production_validation"),
            validation.get("production_validation_rows"),
            metrics.get("production_validation"),
            metrics.get("production_validation_rows"),
        ),
        "observation": _first_present(
            validation.get("observation"),
            validation.get("observation_validation"),
            validation.get("observation_validation_rows"),
            metrics.get("observation_validation"),
            metrics.get("observation_validation_rows"),
        ),
        "execution_readiness": _first_present(
            metrics.get("execution_readiness"),
            metrics.get("readiness"),
            metrics.get("execution_candidate_readiness"),
        ),
        "transition_hazard": _first_present(
            metrics.get("transition_hazard"),
            metrics.get("hybrid_transition_hazard"),
        ),
        "regime_confidence": metrics.get("regime_confidence"),
        "leakage_check": metrics.get("leakage_check"),
    }


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _read_material_values(materials_dir: Path) -> dict[str, Any]:
    values: dict[str, Any] = {}
    if not materials_dir.exists():
        return values
    for path in sorted(materials_dir.glob("*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        for key in (
            "regime_confidence",
            "leakage_check",
            "long_run_expectancy_after_declared_friction",
            *DECLARED_FRICTION_KEYS,
            *RAW_PROFIT_KEYS,
        ):
            if key in payload and key not in values:
                values[key] = payload[key]
    return values


def _validation_rows(metrics: dict[str, Any]) -> dict[str, int]:
    values = _terminal_metrics_values(metrics)
    return {
        "raw_scored_mature": _intish(values["raw_scored_mature"]) or 0,
        "production": _intish(values["production"]) or 0,
        "observation": _intish(values["observation"]) or 0,
    }


def _learning_admitted(
    *,
    regime_confidence: float | None,
    leakage_check: str | None,
    expectancy_after_friction: float | None,
    blockers: list[str],
) -> bool:
    return (
        not blockers
        and
        regime_confidence is not None
        and regime_confidence >= 0.95
        and (leakage_check or "").lower() == "pass"
        and expectancy_after_friction is not None
        and expectancy_after_friction > 0.0
    )


def _paper_status(learning_status: str, validation_rows: dict[str, int]) -> str:
    if learning_status != "admitted":
        return "blocked"
    if all(value >= PAPER_VALIDATION_MIN_ROWS for value in validation_rows.values()):
        return "ready"
    return "observe"


def _live_status(paper_status: str, metrics: dict[str, Any]) -> str:
    values = _terminal_metrics_values(metrics)
    readiness = _floatish(values["execution_readiness"])
    if (
        paper_status == "ready"
        and readiness is not None
        and readiness >= LIVE_EXECUTION_READINESS_FLOOR
    ):
        return "ready"
    return "blocked"


def build_migration_readback(run_root: Path | str) -> dict[str, Any]:
    root = Path(run_root)
    summaries_dir = root / "summaries"
    summary_paths = [
        root / "summaries" / "terminal_decision_summary.md",
        root / "terminal_decision_summary.md",
    ]
    checks_dir = root / "checks"
    materials_dir = root / "materials"

    evidence_paths: list[str] = []
    summary: dict[str, str] = {}
    for summary_path in summary_paths:
        if not summary_path.exists():
            continue
        _merge_missing(summary, _read_key_value_summary(summary_path))
        evidence_paths.append(str(summary_path.relative_to(root)))
    rows: list[dict[str, str]] = []
    for path in [*_summary_csv_paths(summaries_dir), *_legacy_root_csv_paths(root)]:
        rows.extend(_read_csv_rows(path))
        evidence_paths.append(str(path.relative_to(root)))
    check_values, check_paths = _read_check_values(checks_dir)
    for path in check_paths:
        evidence_paths.append(str(path.relative_to(root)))
    legacy_values, legacy_summary_path = _legacy_summary_json_values(root)
    if legacy_summary_path is not None:
        _merge_missing(check_values, legacy_values)
        evidence_paths.append(str(legacy_summary_path.relative_to(root)))
    material_values = _read_material_values(materials_dir)
    if materials_dir.exists():
        evidence_paths.extend(
            str(path.relative_to(root)) for path in sorted(materials_dir.glob("*.json"))
        )

    old_decision = summary.get("decision") or str(check_values.get("decision") or "unknown")
    regime_confidence = _first_present(
        _floatish(summary.get("regime_confidence")),
        _floatish(material_values.get("regime_confidence")),
        _floatish(check_values.get("regime_confidence")),
    )
    leakage_check = _first_present(
        summary.get("leakage_check"),
        material_values.get("leakage_check"),
        check_values.get("leakage_check"),
        "unknown",
    )
    expectancy_after_friction, blockers = _expectancy_after_friction(
        rows=rows,
        material_values=material_values,
        check_values=check_values,
    )

    learning_status = (
        "admitted"
        if _learning_admitted(
            regime_confidence=regime_confidence,
            leakage_check=str(leakage_check),
            expectancy_after_friction=expectancy_after_friction,
            blockers=blockers,
        )
        else "blocked"
    )
    validation_rows = _validation_rows(check_values)
    paper_status = _paper_status(learning_status, validation_rows)
    live_status = _live_status(paper_status, check_values)
    old_drop_reclassified_paper_observe = (
        old_decision.startswith("drop_")
        and learning_status == "admitted"
        and paper_status == "observe"
        and live_status == "blocked"
    )
    migration_decision = (
        "old_drop_reclassified_learning_admitted_paper_observe"
        if old_drop_reclassified_paper_observe
        else "migration_readback_observe"
    )

    return {
        "schema_version": "factor-lifecycle-migration-readback/v1",
        "run_root": str(root),
        "old_decision": old_decision,
        "migration_decision": migration_decision,
        "learning_admission_status": learning_status,
        "paper_admission_status": paper_status,
        "live_trade_status": live_status,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "writes_old_artifacts": False,
        "regime_confidence": regime_confidence,
        "long_run_expectancy_after_declared_friction": expectancy_after_friction,
        "leakage_check": leakage_check,
        "validation_rows": validation_rows,
        "blockers": blockers,
        "evidence_paths": evidence_paths,
    }


def render_compact_markdown(result: dict[str, Any]) -> str:
    fields = [
        ("schema_version", result["schema_version"]),
        ("run_root", result["run_root"]),
        ("old_decision", result["old_decision"]),
        ("migration_decision", result["migration_decision"]),
        ("learning_admission_status", result["learning_admission_status"]),
        ("paper_admission_status", result["paper_admission_status"]),
        ("live_trade_status", result["live_trade_status"]),
        ("promotion_allowed", str(result["promotion_allowed"]).lower()),
        ("trade_usable", str(result["trade_usable"]).lower()),
        ("writes_old_artifacts", str(result["writes_old_artifacts"]).lower()),
    ]
    lines = ["# Factor Lifecycle Migration Readback", ""]
    lines.extend(f"{key}: {value}" for key, value in fields)
    lines.append("")
    lines.append("## Evidence Paths")
    lines.extend(f"- {path}" for path in result["evidence_paths"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--jsonl-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    result = build_migration_readback(args.run_root)
    if args.jsonl_output:
        args.jsonl_output.parent.mkdir(parents=True, exist_ok=True)
        args.jsonl_output.write_text(json.dumps(result, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_compact_markdown(result), encoding="utf-8")
    if args.pretty:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif not args.jsonl_output and not args.markdown_output:
        print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
