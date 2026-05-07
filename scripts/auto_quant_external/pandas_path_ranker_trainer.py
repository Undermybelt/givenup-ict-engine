#!/usr/bin/env python3
"""
Structural Path Ranking External Trainer
==========================================

热插拔外部训练器，用于训练 CatBoost/XGBoost 路径排名模型。

特性：
- 零配置：默认行为可直接运行
- 热插拔：用户可选择是否沿用预训练模型
- Token 友好：输出简洁
- 无污染：不修改仓库代码

用法：
    # 从导出的 target 训练新模型
    python pandas_path_ranker_trainer.py \\
        --target-csv /tmp/state/NQ/policy_training/structural_path_ranking_target.csv \\
        --output-dir /tmp/path_ranker_model

    # 应用预训练模型
    python pandas_path_ranker_trainer.py \\
        --apply \\
        --model-dir /tmp/path_ranker_model \\
        --target-csv /tmp/state/NQ/policy_training/structural_path_ranking_target.csv \\
        --output-scores /tmp/scores.csv

用户特定数据内容（VRP V2 相关特征）：
- qqq_hv_level, qqq_hv_pct_rank_252
- nq_vs_200d_pct
- vix3m_level, vix_level
- vvix_over_vix
- IV/HV 压缩状态
- 多周期共振状态
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import numpy as np
    import pandas as pd
except ImportError:
    print("ERROR: numpy and pandas required. pip install numpy pandas")
    sys.exit(1)

# 可选依赖
try:
    import catboost as cb
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

# 用户特定特征（VRP V2 相关）
VRP_V2_FEATURES = [
    # 波动率状态
    "qqq_hv_level",
    "qqq_hv_pct_rank_252",
    "qqq_iv_level",
    "qqq_iv_pct_rank_252",
    "vix_level",
    "vix3m_level",
    "vvix_level",
    "vvix_over_vix",
    
    # 价格位置
    "nq_vs_200d_pct",
    "nq_drawdown_from_high",
    
    # 多周期共振
    "htf_alignment_score",
    "mtf_alignment_score",
    "ltf_alignment_score",
    
    # 结构特征
    "evidence_quality_score",
    "risk_reward",
    "kelly_fraction",
    "setup_quality",
    
    # ICT 结构计数
    "fvgs_open",
    "order_blocks_nearby",
    "liquidity_sweep_count",
    "cisd_ltf_confirmed",
    "cisd_htf_confirmed",
    
    # HMM 状态
    "hmm_accumulation_prob",
    "hmm_manipulation_expansion_prob",
    "hmm_distribution_prob",
    
    # 执行特征
    "atr_consumption_ratio",
    "displacement_strength",
    "sweep_depth_bps",
]

# 分类特征
CATEGORICAL_FEATURES = [
    "gating_status",
    "selected_direction",
    "factor_alignment",
    "setup_family",
    "entry_style",
    "session_model",
    "htf_rb_type",
    "ltf_path_label",
    "pda_survival_regime",
]


def load_target_csv(path: str) -> pd.DataFrame:
    """加载导出的 target CSV"""
    df = pd.read_csv(path)
    print(f"[load] {path}: {len(df)} rows, {len(df.columns)} columns")
    return df


def prepare_features(df: pd.DataFrame) -> tuple:
    """
    准备特征矩阵。
    返回 (X, y, weights, available_features)
    """
    # 检测可用特征
    available_features = []
    for f in VRP_V2_FEATURES:
        if f in df.columns:
            available_features.append(f)
    
    # 添加分类特征
    for f in CATEGORICAL_FEATURES:
        if f in df.columns:
            available_features.append(f)
    
    # 检测标签列
    label_col = None
    for col in ["calibrated_label", "path_label", "label"]:
        if col in df.columns:
            label_col = col
            break
    
    if label_col is None:
        raise ValueError("No label column found (expected calibrated_label/path_label/label)")
    
    # 过滤成熟样本
    if "maturity_mask" in df.columns:
        df_train = df[df["maturity_mask"] == True].copy()
    else:
        df_train = df.copy()
    
    # 构建特征矩阵
    X = df_train[available_features].copy()
    y = df_train[label_col].values
    
    # 权重
    if "training_weight" in df_train.columns:
        weights = df_train["training_weight"].fillna(1.0).values
    elif "ips_weight" in df_train.columns:
        weights = df_train["ips_weight"].fillna(1.0).values
    else:
        weights = np.ones(len(df_train))
    
    # 填充缺失
    for col in available_features:
        if col in CATEGORICAL_FEATURES:
            X[col] = X[col].fillna("unknown")
        else:
            X[col] = X[col].fillna(0.0)
    
    print(f"[features] {len(available_features)} features, {len(df_train)} training samples")
    print(f"[features] label dist: {np.bincount(y.astype(int)) if y.dtype == int else 'continuous'}")
    
    return X, y, weights, available_features


def train_catboost(X, y, weights, output_dir: Path, cat_features: list = None):
    """训练 CatBoost 模型"""
    if not HAS_CATBOOST:
        print("ERROR: catboost not installed. pip install catboost")
        return None
    
    # 检测分类特征索引
    cat_indices = []
    if cat_features:
        for i, col in enumerate(X.columns):
            if col in cat_features:
                cat_indices.append(i)
    
    # 训练
    model = cb.CatBoostClassifier(
        iterations=100,
        depth=4,
        learning_rate=0.1,
        loss_function="Logloss" if len(np.unique(y)) == 2 else "MultiClass",
        verbose=False,
        cat_features=cat_indices if cat_indices else None,
    )
    
    model.fit(X, y, sample_weight=weights)
    
    # 保存
    model_path = output_dir / "catboost_model.cbm"
    model.save_model(str(model_path))
    
    # 特征重要性
    importance = model.get_feature_importance(prettified=True)
    importance_path = output_dir / "feature_importance.csv"
    pd.DataFrame(importance, columns=["feature", "importance"]).to_csv(importance_path, index=False)
    
    print(f"[train] CatBoost saved to {model_path}")
    print(f"[train] top features: {importance[:5]}")
    
    return model


def train_xgboost(X, y, weights, output_dir: Path):
    """训练 XGBoost 模型"""
    if not HAS_XGBOOST:
        print("ERROR: xgboost not installed. pip install xgboost")
        return None
    
    # 分类特征需要编码
    X_encoded = X.copy()
    for col in CATEGORICAL_FEATURES:
        if col in X_encoded.columns:
            X_encoded[col] = X_encoded[col].astype("category").cat.codes
    
    # 训练
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        use_label_encoder=False,
        eval_metric="logloss",
    )
    
    model.fit(X_encoded, y, sample_weight=weights)
    
    # 保存
    model_path = output_dir / "xgboost_model.json"
    model.save_model(str(model_path))
    
    # 特征重要性
    importance = model.feature_importances_
    importance_path = output_dir / "feature_importance_xgb.csv"
    pd.DataFrame({
        "feature": X.columns,
        "importance": importance
    }).sort_values("importance", ascending=False).to_csv(importance_path, index=False)
    
    print(f"[train] XGBoost saved to {model_path}")
    
    return model


def apply_model(model_dir: Path, target_csv: str, output_scores: str):
    """应用预训练模型生成 scores.csv"""
    # 加载 target
    df = load_target_csv(target_csv)
    X, _, _, features = prepare_features(df)
    
    # 加载模型
    catboost_path = model_dir / "catboost_model.cbm"
    xgboost_path = model_dir / "xgboost_model.json"
    
    if catboost_path.exists() and HAS_CATBOOST:
        model = cb.CatBoostClassifier()
        model.load_model(str(catboost_path))
        scores = model.predict_proba(X)[:, 1] if model.classes_.shape[0] == 2 else model.predict_proba(X).argmax(axis=1)
        print(f"[apply] CatBoost predictions: {len(scores)}")
    elif xgboost_path.exists() and HAS_XGBOOST:
        model = xgb.XGBClassifier()
        model.load_model(str(xgboost_path))
        X_encoded = X.copy()
        for col in CATEGORICAL_FEATURES:
            if col in X_encoded.columns:
                X_encoded[col] = X_encoded[col].astype("category").cat.codes
        scores = model.predict_proba(X_encoded)[:, 1] if len(model.classes_) == 2 else model.predict_proba(X_encoded).argmax(axis=1)
        print(f"[apply] XGBoost predictions: {len(scores)}")
    else:
        # 回退到简单加权
        print("[apply] No trained model found, using weighted sum fallback")
        scores = weighted_sum_fallback(X)
    
    # 输出 scores.csv
    scores_df = pd.DataFrame({
        "candidate_set_id": df["candidate_set_id"] if "candidate_set_id" in df.columns else ["unknown"] * len(df),
        "path_id": df["path_id"] if "path_id" in df.columns else [f"path_{i}" for i in range(len(df))],
        "raw_path_score": scores,
    })
    scores_df.to_csv(output_scores, index=False)
    print(f"[apply] Scores saved to {output_scores}")
    
    return scores_df


def weighted_sum_fallback(X: pd.DataFrame) -> np.ndarray:
    """
    无训练模型时的回退：简单加权求和。
    用户可配置权重文件。
    """
    weights = {
        "evidence_quality_score": 0.20,
        "risk_reward": 0.15,
        "kelly_fraction": 0.10,
        "htf_alignment_score": 0.15,
        "mtf_alignment_score": 0.10,
        "hmm_manipulation_expansion_prob": 0.10,
        "fvgs_open": -0.05,  # 更多未填补缺口 = 风险
        "atr_consumption_ratio": -0.10,  # 高 ATR 消耗 = 风险
    }
    
    score = np.zeros(len(X))
    for feat, w in weights.items():
        if feat in X.columns:
            score += X[feat].values * w
    
    # 归一化到 [0, 1]
    score = (score - score.min()) / (score.max() - score.min() + 1e-9)
    
    return score


def create_user_weights_template(output_dir: Path):
    """创建用户可编辑的权重模板（热插拔）"""
    template_path = output_dir / "user_weights.json"
    
    template = {
        "_comment": "用户可编辑此文件自定义加权求和回退权重",
        "evidence_quality_score": 0.20,
        "risk_reward": 0.15,
        "kelly_fraction": 0.10,
        "htf_alignment_score": 0.15,
        "mtf_alignment_score": 0.10,
        "hmm_manipulation_expansion_prob": 0.10,
        "fvgs_open": -0.05,
        "atr_consumption_ratio": -0.10,
        "_notes": [
            "正值 = 正向贡献",
            "负值 = 风险惩罚",
            "总和应约等于 1.0（自动归一化）",
        ]
    }
    
    with open(template_path, "w") as f:
        json.dump(template, f, indent=2)
    
    print(f"[template] User weights template saved to {template_path}")


def main():
    parser = argparse.ArgumentParser(description="Structural Path Ranking External Trainer")
    parser.add_argument("--target-csv", required=True, help="Path to exported target CSV")
    parser.add_argument("--output-dir", default="./path_ranker_model", help="Output directory for model")
    parser.add_argument("--apply", action="store_true", help="Apply existing model instead of training")
    parser.add_argument("--model-dir", help="Directory with existing model (for --apply)")
    parser.add_argument("--output-scores", default="./scores.csv", help="Output scores CSV (for --apply)")
    parser.add_argument("--model-family", default="catboost", choices=["catboost", "xgboost", "both"])
    parser.add_argument("--create-template", action="store_true", help="Create user weights template")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.create_template:
        create_user_weights_template(output_dir)
        return
    
    if args.apply:
        model_dir = Path(args.model_dir) if args.model_dir else output_dir
        apply_model(model_dir, args.target_csv, args.output_scores)
        return
    
    # 训练模式
    df = load_target_csv(args.target_csv)
    X, y, weights, features = prepare_features(df)
    
    # 保存特征列表
    features_path = output_dir / "features.json"
    with open(features_path, "w") as f:
        json.dump({
            "features": features,
            "created_at": datetime.now().isoformat(),
            "n_samples": len(X),
        }, f, indent=2)
    
    # 创建用户权重模板
    create_user_weights_template(output_dir)
    
    # 训练
    if args.model_family in ["catboost", "both"]:
        train_catboost(X, y, weights, output_dir, cat_features=CATEGORICAL_FEATURES)
    
    if args.model_family in ["xgboost", "both"]:
        train_xgboost(X, y, weights, output_dir)
    
    print(f"\n[done] Model saved to {output_dir}")
    print(f"[done] To apply: python {sys.argv[0]} --apply --model-dir {output_dir} --target-csv <new_target.csv> --output-scores scores.csv")


if __name__ == "__main__":
    main()
