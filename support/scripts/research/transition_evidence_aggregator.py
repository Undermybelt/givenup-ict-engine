from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_THRESHOLDS = {
    "alert_transition_prob": 0.95,
    "max_stable_transition_prob": 0.2,
    "max_stable_flip_rate": 0.2,
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _float(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return default


def _regime_label(row: dict[str, Any]) -> str:
    for key in ("regime", "active_regime", "final_label", "label", "state"):
        value = str(row.get(key, "")).strip()
        if value:
            return value
    return ""


def _drift_flags(drift_rows: list[dict[str, Any]], alert_threshold: float) -> list[str]:
    flags: list[str] = []
    for row in drift_rows:
        source = str(row.get("source", "drift")).strip() or "drift"
        if bool(row.get("drift_flag", False)) or _float(row, "transition_prob") >= alert_threshold:
            flags.append(source)
    return sorted(set(flags))


def _hazard(regime_report: dict[str, Any], drift_rows: list[dict[str, Any]]) -> float:
    values = [
        _float(regime_report, "transition_prob"),
        _float(regime_report, "flip_rate"),
    ]
    for row in drift_rows:
        values.append(_float(row, "transition_prob"))
        values.append(_float(row, "severity"))
    return max(values) if values else 0.0


def _matrix_vector_multiply(
    distribution: dict[str, float],
    transition_matrix: dict[str, dict[str, float]],
    states: list[str],
) -> dict[str, float]:
    result = {state: 0.0 for state in states}
    for from_state, probability in distribution.items():
        row = transition_matrix.get(from_state, {})
        for to_state in states:
            result[to_state] += probability * row.get(to_state, 0.0)
    return result


def _stationary_distribution(
    transition_matrix: dict[str, dict[str, float]],
    states: list[str],
    *,
    iterations: int = 100,
) -> dict[str, float]:
    if not states:
        return {}
    distribution = {state: 1.0 / len(states) for state in states}
    for _ in range(iterations):
        distribution = _matrix_vector_multiply(distribution, transition_matrix, states)
    total = sum(distribution.values())
    if total <= 0.0:
        return {state: 1.0 / len(states) for state in states}
    return {state: distribution[state] / total for state in states}


def _markov_evidence(
    *,
    regime_report: dict[str, Any],
    sequence_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    sequence = [_regime_label(row) for row in sequence_rows]
    sequence = [label for label in sequence if label]
    states = sorted(set(sequence))
    if len(sequence) < 2 or not states:
        return {
            "markov_state_sequence_length": len(sequence),
            "markov_transition_count": 0,
            "markov_transition_matrix": {},
            "markov_two_step_probabilities": {},
            "markov_stationary_distribution": {},
            "markov_current_regime_exit_probability": None,
        }

    counts = {state: {to_state: 0 for to_state in states} for state in states}
    transition_count = 0
    for from_state, to_state in zip(sequence, sequence[1:]):
        counts[from_state][to_state] += 1
        transition_count += 1

    transition_matrix: dict[str, dict[str, float]] = {}
    for state in states:
        row_count = sum(counts[state].values())
        if row_count == 0:
            transition_matrix[state] = {to_state: 0.0 for to_state in states}
            transition_matrix[state][state] = 1.0
            continue
        transition_matrix[state] = {
            to_state: counts[state][to_state] / row_count for to_state in states
        }

    active_regime = (
        str(
            regime_report.get("active_regime")
            or regime_report.get("final_label")
            or regime_report.get("label")
            or regime_report.get("regime")
            or ""
        ).strip()
        or sequence[-1]
    )
    if active_regime in transition_matrix:
        one_step = transition_matrix[active_regime]
        two_step = _matrix_vector_multiply(one_step, transition_matrix, states)
        exit_probability: float | None = 1.0 - one_step.get(active_regime, 0.0)
    else:
        two_step = {}
        exit_probability = None

    return {
        "markov_state_sequence_length": len(sequence),
        "markov_transition_count": transition_count,
        "markov_transition_matrix": transition_matrix,
        "markov_two_step_probabilities": two_step,
        "markov_stationary_distribution": _stationary_distribution(transition_matrix, states),
        "markov_current_regime": active_regime,
        "markov_current_regime_exit_probability": exit_probability,
    }


def build_transition_evidence(
    *,
    regime_report: dict[str, Any],
    drift_rows: list[dict[str, Any]] | None = None,
    regime_sequence_rows: list[dict[str, Any]] | None = None,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    merged = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        merged.update(thresholds)
    rows = drift_rows or []
    markov = _markov_evidence(
        regime_report=regime_report,
        sequence_rows=regime_sequence_rows or [],
    )
    hazard = _hazard(regime_report, rows)
    markov_exit_probability = markov.get("markov_current_regime_exit_probability")
    if isinstance(markov_exit_probability, (int, float)):
        hazard = max(hazard, float(markov_exit_probability))
    flags = _drift_flags(rows, float(merged["alert_transition_prob"]))
    regime_confidence_ok = bool(regime_report.get("confidence_95", False))
    regime_gate = str(regime_report.get("regime_confidence_gate", ""))
    transition_alert_95 = hazard >= float(merged["alert_transition_prob"])

    return {
        "schema_version": "transition-evidence-aggregator/v1",
        "candidate_id": regime_report.get("candidate_id", ""),
        "transition_alert_95": transition_alert_95,
        "transition_hazard": hazard,
        "drift_flags": flags,
        "execution_tree_block_hint": "none",
        "transition_hazard_role": "telemetry_only",
        "regime_confidence_gate": regime_gate,
        "regime_confidence_95": regime_confidence_ok,
        "source_count": len(rows),
        "thresholds": merged,
        **markov,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate regime confidence and drift rows into transition evidence.")
    parser.add_argument("--regime-report-json", required=True)
    parser.add_argument("--drift-jsonl")
    parser.add_argument(
        "--regime-sequence-jsonl",
        help="Optional JSONL rows carrying regime/active_regime/final_label labels for Markov transition evidence.",
    )
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--alert-transition-prob", type=float, default=DEFAULT_THRESHOLDS["alert_transition_prob"])
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = build_transition_evidence(
        regime_report=_load_json(Path(args.regime_report_json)),
        drift_rows=_load_jsonl(Path(args.drift_jsonl)) if args.drift_jsonl else [],
        regime_sequence_rows=_load_jsonl(Path(args.regime_sequence_jsonl)) if args.regime_sequence_jsonl else [],
        thresholds={
            "alert_transition_prob": args.alert_transition_prob,
        },
    )
    _write_json(Path(args.output_json), result)
    print(json.dumps({"ok": True, "output": args.output_json, "execution_tree_block_hint": result["execution_tree_block_hint"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
