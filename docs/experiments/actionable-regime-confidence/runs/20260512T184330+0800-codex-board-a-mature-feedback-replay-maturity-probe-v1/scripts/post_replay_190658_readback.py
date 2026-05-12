#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "post-replay-190658"
CHECK_DIR = RUN_ROOT / "checks" / "post-replay-190658"
CMD_DIR = RUN_ROOT / "command-output" / "post-replay-190658"
STATE_DIR = RUN_ROOT / "replay" / "state"
SYMBOL = "BTCUSD"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_exit(name: str) -> int | None:
    path = CHECK_DIR / f"{name}.exit"
    if not path.exists():
        return None
    return int(path.read_text(encoding="utf-8").strip())


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    replay = load_json(RUN_ROOT / "replay" / "replay_summary.json")
    policy = load_json(CMD_DIR / "07_policy_training_status_after_runtime.out")
    execution = load_json(CMD_DIR / "08_workflow_status_execution_candidate.out")
    pre_bayes = load_json(CMD_DIR / "09_pre_bayes_status.out")
    target = load_json(CMD_DIR / "11_export_structural_path_target_after_runtime.out")
    artifact = load_json(STATE_DIR / SYMBOL / "policy_training" / "path_ranker_catboost_post_replay_190658_v1" / "trainer_artifact.json")

    exits = {path.stem: read_exit(path.stem) for path in sorted(CHECK_DIR.glob("*.exit"))}
    validation = policy.get("structural_path_ranking_validation", {})
    runtime = policy.get("structural_path_ranking_runtime", {})
    confidence = float(pre_bayes.get("latest_canonical_structural_confidence") or 0.0)
    probs = pre_bayes.get("latest_canonical_structural_probabilities") or {}

    gates = [
        ("commands_zero", all(v == 0 for v in exits.values()) and len(exits) >= 11, f"exit_count={len(exits)} nonzero={[k for k,v in exits.items() if v != 0]}"),
        ("replay_observations_min30", int(replay.get("count") or 0) >= 30, f"observations={replay.get('count')}"),
        ("catboost_trained_rows_min30", int(artifact.get("trained_rows") or 0) >= 30, f"trained_rows={artifact.get('trained_rows')}"),
        ("path_ranker_runtime_ready", bool(runtime.get("ready")), runtime.get("summary_line", "")),
        ("raw_scored_mature_min30", int(validation.get("raw_scored_mature_rows") or 0) >= 30, f"raw_scored_mature={validation.get('raw_scored_mature_rows')}/30"),
        ("production_validation_min30", bool(validation.get("production_validation_ready")), f"production_validation={validation.get('production_validation_rows')}/30"),
        ("observation_validation_min30", bool(validation.get("observation_validation_ready")), f"observation_validation={validation.get('observation_validation_rows')}/30"),
        ("current_pre_bayes_confidence_95", confidence >= 0.95, f"confidence={confidence}"),
        ("every_regime_95", all(float(probs.get(k, 0.0)) >= 0.95 for k in ("trend", "range", "transition", "stress")), f"probabilities={probs}"),
        ("independent_cross_market_validation", False, "replay used BTCUSD from the 172142 YF 1h candle file only"),
        ("independent_cross_timeframe_validation", False, "replay windows were generated from the same 1h source and passed as ltf/mtf/htf"),
        ("execution_tree_non_observe", bool(execution.get("actionable")) and execution.get("review_status") != "observe", f"actionable={execution.get('actionable')} ready={execution.get('ready')} gate={execution.get('execution_gate_status')} review={execution.get('review_status')}"),
        ("path_probability_95", float(execution.get("path_ranker_calibrated_path_prob") or 0.0) >= 0.95, f"path_prob={execution.get('path_ranker_calibrated_path_prob')} lower_bound={execution.get('path_ranker_path_prob_lower_bound')}"),
    ]
    payload = {
        "schema_version": "board-a-post-replay-190658-readback-v1",
        "run_root": str(RUN_ROOT),
        "symbol": SYMBOL,
        "exits": exits,
        "replay": {
            "ok": replay.get("ok"),
            "count": replay.get("count"),
            "final_mature_rows": replay.get("final_mature_rows"),
            "lookback": replay.get("lookback"),
            "horizon": replay.get("horizon"),
            "threshold": replay.get("threshold"),
        },
        "path_ranker": {
            "runtime_ready": runtime.get("ready"),
            "runtime_status": runtime.get("status"),
            "runtime_mode": runtime.get("reuse_mode"),
            "trained_rows": artifact.get("trained_rows"),
            "calibration_rows": artifact.get("calibration_rows"),
            "raw_scored_mature_rows": validation.get("raw_scored_mature_rows"),
            "production_validation_rows": validation.get("production_validation_rows"),
            "observation_validation_rows": validation.get("observation_validation_rows"),
            "target_summary": target.get("summary_line"),
        },
        "pre_bayes": {
            "active_regime": pre_bayes.get("latest_canonical_structural_active_regime"),
            "confidence": confidence,
            "probabilities": probs,
            "gate_status": pre_bayes.get("latest_gate_status"),
        },
        "execution": {
            "candidate_status": execution.get("candidate_status"),
            "actionable": execution.get("actionable"),
            "ready": execution.get("ready"),
            "execution_gate_status": execution.get("execution_gate_status"),
            "review_status": execution.get("review_status"),
            "review_reason": execution.get("review_reason"),
            "execution_readiness": execution.get("execution_readiness"),
            "path_ranker_calibrated_path_prob": execution.get("path_ranker_calibrated_path_prob"),
            "path_ranker_path_prob_lower_bound": execution.get("path_ranker_path_prob_lower_bound"),
            "path_ranker_raw_score": execution.get("path_ranker_raw_score"),
        },
        "gates": [
            {"gate": name, "passed": bool(passed), "status": "pass" if passed else "fail_closed", "evidence": evidence}
            for name, passed, evidence in gates
        ],
        "accepted_95_contexts_added": 0,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    (OUT_DIR / "post_replay_190658_readback.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    assertion_lines = []
    for gate in payload["gates"]:
        prefix = "PASS" if gate["passed"] else "FAIL_CLOSED"
        assertion_lines.append(f"{prefix} {gate['gate']} {gate['evidence']}")
    assertion_lines.extend([
        "PASS accepted_95_contexts_added=0",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ])
    (CHECK_DIR / "post_replay_190658_readback_assertions.out").write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")

    md = [
        "# Post-Replay 190658 Readback",
        "",
        f"- Run root: `{RUN_ROOT}`",
        f"- Symbol: `{SYMBOL}`",
        f"- Replay observations: `{payload['replay']['count']}`",
        f"- CatBoost trained rows: `{payload['path_ranker']['trained_rows']}`",
        f"- Raw scored mature rows: `{payload['path_ranker']['raw_scored_mature_rows']}/30`",
        f"- Production validation rows: `{payload['path_ranker']['production_validation_rows']}/30`",
        f"- Observation validation rows: `{payload['path_ranker']['observation_validation_rows']}/30`",
        f"- Pre-Bayes confidence: `{payload['pre_bayes']['confidence']}`",
        f"- Execution status: `{payload['execution']['candidate_status']}` / `{payload['execution']['execution_gate_status']}` / `{payload['execution']['review_status']}`",
        f"- Promotion allowed: `{str(payload['promotion_allowed']).lower()}`",
        "",
        "## Gate Matrix",
        "",
        "| Gate | Status | Evidence |",
        "|---|---|---|",
    ]
    for gate in payload["gates"]:
        md.append(f"| `{gate['gate']}` | `{gate['status']}` | {gate['evidence']} |")
    md.extend([
        "",
        "## Readback",
        "",
        "The replay produced enough structural-feedback observations and the CatBoost/path-ranker validation floor is now ready in this isolated BTCUSD replay state.",
        "",
        "Board A still fails closed because the current Pre-Bayes confidence is below `0.95`, the evidence covers only the replayed BTCUSD/YF 1h source, not independent cross-market/cross-timeframe validation, and the execution candidate remains `execution_blocked` / `observe`.",
        "",
        "Do not promote Board A from this packet.",
    ])
    (OUT_DIR / "post_replay_190658_readback.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"promotion_allowed": False, "gates": payload["gates"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
