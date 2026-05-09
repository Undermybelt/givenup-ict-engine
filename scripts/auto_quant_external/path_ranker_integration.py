#!/usr/bin/env python3
"""
Path Ranker 一键集成脚本
========================

从导出 target → 训练模型 → 应用 scores 的完整流程。

用法：
    # 完整流程
    python path_ranker_integration.py --state-dir /tmp/vrp-v2-runtime-closure --symbol NQ

    # 仅训练
    python path_ranker_integration.py --train-only --state-dir /tmp/state --symbol NQ

    # 仅应用
    python path_ranker_integration.py --apply-only --model-dir /tmp/model --target-csv target.csv

零配置：默认行为可直接运行
热插拔：用户可通过 user_weights.json 自定义
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
TRAINER_SCRIPT = SCRIPT_DIR / "pandas_path_ranker_trainer.py"
REPO_ROOT = SCRIPT_DIR.parents[1]
ICT_ENGINE_BIN = REPO_ROOT / "target" / "debug" / "ict-engine"

sys.path.insert(0, str(SCRIPT_DIR))
import pandas_path_ranker_trainer as trainer  # noqa: E402


def find_target_csv(state_dir: str, symbol: str) -> Path:
    """查找导出的 target CSV"""
    target_path = Path(state_dir) / symbol / "policy_training" / "structural_path_ranking_target.csv"
    if target_path.exists():
        return target_path
    
    # 备用路径
    alt_path = Path(state_dir) / symbol / "structural_path_ranking_target.csv"
    if alt_path.exists():
        return alt_path
    
    raise FileNotFoundError(f"No target CSV found in {state_dir}/{symbol}")


def run_trainer(target_csv: str, output_dir: str, model_family: str = "catboost"):
    """运行训练器"""
    cmd = [
        sys.executable,
        str(TRAINER_SCRIPT),
        "--target-csv", target_csv,
        "--output-dir", output_dir,
        "--model-family", model_family,
    ]
    
    print(f"[run] {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"[error] {result.stderr}")
        raise RuntimeError("Trainer failed")
    
    print(result.stdout)
    return result


def run_apply(
    model_dir: str,
    target_csv: str,
    output_scores: str,
    user_weights: str | None = None,
):
    """运行应用"""
    cmd = [
        sys.executable,
        str(TRAINER_SCRIPT),
        "--apply",
        "--model-dir", model_dir,
        "--target-csv", target_csv,
        "--output-scores", output_scores,
    ]
    if user_weights:
        cmd.extend(["--user-weights", user_weights])
    
    print(f"[run] {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"[error] {result.stderr}")
        raise RuntimeError("Apply failed")
    
    print(result.stdout)
    return result


def ensure_runtime_artifact(model_dir: str, target_csv: str) -> str:
    """Backfill a direct-model artifact for legacy model dirs before repo registration."""
    model_path = Path(model_dir)
    artifact_path = model_path / "path_ranker_direct_model.json"
    if artifact_path.exists():
        return str(artifact_path)

    df = trainer.load_target_csv(target_csv)
    _, _, _, features = trainer.prepare_features(df)
    trainer.create_direct_model_artifact(
        output_dir=model_path,
        features=features,
        trained_rows=len(df),
    )
    return str(artifact_path)


def register_runtime_artifact(
    state_dir: str,
    symbol: str,
    model_dir: str,
    target_csv: str,
    score_column: str = "raw_path_score",
    reuse_mode: str = "candidate_set_only",
):
    """Opt in to repo-side runtime reuse using the emitted direct-model artifact."""
    artifact_path = ensure_runtime_artifact(model_dir=model_dir, target_csv=target_csv)
    register_cmd = [
        str(ICT_ENGINE_BIN),
        "register-structural-path-ranking-trainer-artifact",
        "--symbol",
        symbol,
        "--state-dir",
        state_dir,
        "--artifact-uri",
        str(artifact_path),
        "--model-family",
        "weighted_feature_sum_v1",
        "--score-column",
        score_column,
    ]
    enable_cmd = [
        str(ICT_ENGINE_BIN),
        "enable-structural-path-ranking-runtime",
        "--symbol",
        symbol,
        "--state-dir",
        state_dir,
        "--reuse-mode",
        reuse_mode,
    ]
    for cmd in (register_cmd, enable_cmd):
        print(f"[run] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[error] {result.stderr}")
            raise RuntimeError("Runtime artifact registration failed")
        print(result.stdout)


def main():
    parser = argparse.ArgumentParser(description="Path Ranker Integration")
    parser.add_argument("--state-dir", required=False, help="State directory")
    parser.add_argument("--symbol", default="NQ", help="Symbol")
    parser.add_argument("--target-csv", help="Direct path to target CSV")
    parser.add_argument("--output-dir", default=None, help="Model output directory")
    parser.add_argument("--model-dir", default=None, help="Existing model directory (for apply)")
    parser.add_argument("--output-scores", default=None, help="Scores output path")
    parser.add_argument("--model-family", default="catboost", choices=["catboost", "xgboost", "both"])
    parser.add_argument("--train-only", action="store_true", help="Only train, skip apply")
    parser.add_argument("--apply-only", action="store_true", help="Only apply, skip train")
    parser.add_argument(
        "--reuse-model-dir",
        help="Reuse an existing model directory and skip training",
    )
    parser.add_argument(
        "--user-weights",
        help="Optional user_weights.json used when fallback scoring is needed",
    )
    parser.add_argument(
        "--register-runtime-artifact",
        action="store_true",
        help="Opt in to register the emitted direct-model artifact and enable repo runtime reuse",
    )
    parser.add_argument(
        "--reuse-mode",
        default="candidate_set_only",
        help="Runtime reuse mode used with --register-runtime-artifact",
    )
    
    args = parser.parse_args()
    
    # 确定路径
    if args.target_csv:
        target_csv = args.target_csv
    elif args.state_dir:
        target_csv = str(find_target_csv(args.state_dir, args.symbol))
    else:
        print("ERROR: Need --state-dir or --target-csv")
        sys.exit(1)
    
    if args.output_dir:
        output_dir = args.output_dir
    elif args.state_dir:
        output_dir = str(Path(args.state_dir) / args.symbol / "policy_training" / "path_ranker_model")
    else:
        output_dir = "./path_ranker_model"
    
    if args.output_scores:
        output_scores = args.output_scores
    elif args.state_dir:
        output_scores = str(Path(args.state_dir) / args.symbol / "policy_training" / "scores.csv")
    else:
        output_scores = "./scores.csv"
    
    # 执行
    if args.apply_only:
        model_dir = args.model_dir or output_dir
        run_apply(model_dir, target_csv, output_scores, args.user_weights)
    elif args.reuse_model_dir:
        run_apply(args.reuse_model_dir, target_csv, output_scores, args.user_weights)
    else:
        # 训练
        run_trainer(target_csv, output_dir, args.model_family)
        
        if not args.train_only:
            # 应用
            run_apply(output_dir, target_csv, output_scores, args.user_weights)

    if args.register_runtime_artifact:
        if not args.state_dir:
            print("ERROR: --register-runtime-artifact requires --state-dir")
            sys.exit(1)
        register_runtime_artifact(
            state_dir=args.state_dir,
            symbol=args.symbol,
            model_dir=output_dir,
            target_csv=target_csv,
            score_column="raw_path_score",
            reuse_mode=args.reuse_mode,
        )
    
    print(f"\n[done] Model: {output_dir}")
    print(f"[done] Scores: {output_scores}")
    print(f"\n[next] Apply to runtime:")
    print(f"  ./target/debug/ict-engine apply-structural-path-ranking-external-scores \\")
    print(f"    --symbol {args.symbol} --state-dir {args.state_dir} --scores-file {output_scores}")


if __name__ == "__main__":
    main()
