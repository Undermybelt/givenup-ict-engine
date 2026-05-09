from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import factor_payoff_shape_report as payoff
import labeling_triple_barrier as labeling
import payoff_to_path_ranker_target as path_target


DEFAULT_PROFILE: dict[str, Any] = {
    "profile_id": "ict-default-v1",
    "enabled": True,
    "pt_mult": 0.02,
    "sl_mult": 0.01,
    "max_holding_bars": 16,
    "cost_bps": 0.0,
    "nb_trials": 1,
    "periods_per_year": 252,
    "auxiliary_fields": [
        "qqq_hv_level",
        "nq_vs_200d_pct",
        "vix3m_level",
        "qqq_hv_pct_rank_252",
        "vvix_over_vix",
    ],
    "artifact_names": {
        "labels": "labels.jsonl",
        "payoff_report": "payoff_report.json",
        "handoff_summary": "handoff_summary.json",
    },
}


def _load_profile(path: Path | None) -> dict[str, Any]:
    profile = dict(DEFAULT_PROFILE)
    profile["artifact_names"] = dict(DEFAULT_PROFILE["artifact_names"])
    if path is None:
        return profile
    override = json.loads(path.read_text(encoding="utf-8"))
    profile.update(override)
    if "artifact_names" in override:
        artifact_names = dict(DEFAULT_PROFILE["artifact_names"])
        artifact_names.update(override["artifact_names"])
        profile["artifact_names"] = artifact_names
    return profile


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=False) + "\n")


def run_pipeline(
    *,
    input_csv: Path,
    output_dir: Path,
    symbol: str,
    candidate_id: str,
    profile_json: Path | None = None,
) -> dict[str, Any]:
    """Run zero-config payoff labeling into an isolated output directory."""
    profile = _load_profile(profile_json)
    if not bool(profile.get("enabled", True)):
        result = {
            "ok": True,
            "skipped": True,
            "reason": "profile_disabled",
            "symbol": symbol,
            "candidate_id": candidate_id,
            "profile": profile,
        }
        _write_json(output_dir / "handoff_summary.json", result)
        return result

    rows = _read_csv(input_csv)
    labels = labeling.triple_barrier_labels(
        rows,
        pt_mult=float(profile["pt_mult"]),
        sl_mult=float(profile["sl_mult"]),
        max_holding_bars=int(profile["max_holding_bars"]),
        cost_bps=float(profile.get("cost_bps", 0.0)),
    )
    report = payoff.build_payoff_shape_report(
        candidate_id=candidate_id,
        trades=labels,
        nb_trials=int(profile.get("nb_trials", 1)),
        periods_per_year=int(profile.get("periods_per_year", 252)),
    )

    artifact_names = profile["artifact_names"]
    labels_path = output_dir / artifact_names["labels"]
    report_path = output_dir / artifact_names["payoff_report"]
    summary_path = output_dir / artifact_names["handoff_summary"]
    _write_jsonl(labels_path, labels)
    _write_json(report_path, report)
    path_ranker_handoff = path_target.export_targets(
        labels_jsonl=labels_path,
        payoff_report_json=report_path,
        output_dir=output_dir,
        symbol=symbol,
        auxiliary_fields=list(profile.get("auxiliary_fields", [])),
    )

    result = {
        "ok": True,
        "skipped": False,
        "symbol": symbol,
        "candidate_id": candidate_id,
        "profile": profile,
        "input_csv": str(input_csv),
        "output_dir": str(output_dir),
        "artifact_paths": {
            "labels": str(labels_path),
            "payoff_report": str(report_path),
            "handoff_summary": str(summary_path),
        },
        "label_count": len(labels),
        "payoff_gate": report["promotion_gate"],
        "failure_tags": report["failure_tags"],
        "path_ranker_handoff": path_ranker_handoff,
        "next_recommended_layer": "regime_bbn_path_ranker" if report["promotion_gate"] != "reject" else "rewrite_factor_or_data",
    }
    _write_json(summary_path, result)
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Zero-config heuristic payoff labeling pipeline.")
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--profile-json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_pipeline(
        input_csv=Path(args.input_csv).resolve(),
        output_dir=Path(args.output_dir).resolve(),
        symbol=args.symbol,
        candidate_id=args.candidate_id,
        profile_json=Path(args.profile_json).resolve() if args.profile_json else None,
    )
    print(json.dumps(result, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())