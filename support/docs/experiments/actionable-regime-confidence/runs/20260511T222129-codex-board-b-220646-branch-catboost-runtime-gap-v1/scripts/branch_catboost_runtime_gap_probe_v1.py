#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import pandas as pd
from catboost import CatBoostClassifier, Pool


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch-features", required=True)
    parser.add_argument("--runtime-target", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    branch_features = Path(args.branch_features)
    runtime_target = Path(args.runtime_target)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(branch_features)
    runtime_df = pd.read_csv(runtime_target)
    required = {"regime_profit_branch_path", "target_positive_net", "year_fold"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise SystemExit(f"missing required branch feature columns: {missing}")

    df["target_positive_net"] = df["target_positive_net"].astype(int)
    df["year_fold"] = pd.to_numeric(df["year_fold"], errors="coerce")
    df = df.dropna(subset=["year_fold", "regime_profit_branch_path", "target_positive_net"]).copy()
    df["year_fold"] = df["year_fold"].astype(int)

    train_df = df[df["year_fold"] <= 2020].copy()
    test_df = df[df["year_fold"] > 2020].copy()
    if train_df["target_positive_net"].nunique() < 2:
        raise SystemExit("training fold lacks both positive and negative labels")
    if test_df.empty:
        raise SystemExit("chronological holdout is empty")

    feature_cols = [
        "parent_regime_root",
        "selected_variant_id",
        "market",
        "timeframe",
        "direction",
        "year_fold",
        "root_confidence",
        "vol_proxy",
        "carry_proxy",
        "regime_profit_branch_path",
    ]
    feature_cols = [c for c in feature_cols if c in df.columns]
    cat_features = [feature_cols.index("regime_profit_branch_path")]

    train_pool = Pool(
        train_df[feature_cols],
        label=train_df["target_positive_net"],
        cat_features=cat_features,
    )
    test_pool = Pool(
        test_df[feature_cols],
        label=test_df["target_positive_net"],
        cat_features=cat_features,
    )

    model = CatBoostClassifier(
        iterations=120,
        depth=4,
        learning_rate=0.05,
        loss_function="Logloss",
        eval_metric="AUC",
        random_seed=20260511,
        verbose=False,
        allow_writing_files=False,
    )
    model.fit(train_pool, eval_set=test_pool, use_best_model=False)
    model_path = output_dir / "branch_catboost_model_v1.cbm"
    model.save_model(model_path)

    df["catboost_predicted_win_prob"] = model.predict_proba(Pool(df[feature_cols], cat_features=cat_features))[:, 1]
    test_df = df[df["year_fold"] > 2020].copy()
    branch_scores = (
        test_df.groupby("regime_profit_branch_path")
        .agg(
            raw_path_score=("catboost_predicted_win_prob", "mean"),
            holdout_rows=("target_positive_net", "size"),
            holdout_win_rate=("target_positive_net", "mean"),
            min_year=("year_fold", "min"),
            max_year=("year_fold", "max"),
        )
        .reset_index()
    )
    all_counts = df.groupby("regime_profit_branch_path").size().rename("observed_rows").reset_index()
    train_counts = train_df.groupby("regime_profit_branch_path").size().rename("train_rows").reset_index()
    branch_scores = branch_scores.merge(all_counts, on="regime_profit_branch_path", how="left")
    branch_scores = branch_scores.merge(train_counts, on="regime_profit_branch_path", how="left")
    branch_scores["model_family"] = "catboost"
    branch_scores["score_source_kind"] = "branch_catboost_chronological_holdout"
    branch_scores["model_artifact_uri"] = str(model_path)
    branch_scores = branch_scores[
        [
            "regime_profit_branch_path",
            "raw_path_score",
            "observed_rows",
            "train_rows",
            "holdout_rows",
            "holdout_win_rate",
            "min_year",
            "max_year",
            "model_family",
            "score_source_kind",
            "model_artifact_uri",
        ]
    ]
    branch_scores_path = output_dir / "branch_catboost_scores_v1.csv"
    branch_scores.to_csv(branch_scores_path, index=False)

    target_candidate_set_id = runtime_df["candidate_set_id"].dropna().iloc[0] if "candidate_set_id" in runtime_df else ""
    exact_apply = branch_scores[["regime_profit_branch_path", "raw_path_score"]].copy()
    exact_apply.insert(0, "candidate_set_id", target_candidate_set_id)
    exact_apply = exact_apply.rename(columns={"regime_profit_branch_path": "path_id"})
    exact_apply_path = output_dir / "runtime_external_scores_exact_branch_paths_v1.csv"
    exact_apply.to_csv(exact_apply_path, index=False)

    runtime_path_ids = sorted(runtime_df.get("path_id", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
    branch_paths = sorted(branch_scores["regime_profit_branch_path"].astype(str).unique().tolist())
    matching_paths = sorted(set(runtime_path_ids).intersection(branch_paths))

    summary = {
        "schema_version": "board-b-branch-catboost-runtime-gap-probe/v1",
        "source_branch_features": str(branch_features),
        "source_runtime_target": str(runtime_target),
        "model_family": "catboost",
        "catboost_model": str(model_path),
        "branch_scores": str(branch_scores_path),
        "runtime_exact_branch_scores": str(exact_apply_path),
        "train_rows": int(len(train_df)),
        "holdout_rows": int(len(test_df)),
        "total_rows": int(len(df)),
        "branch_score_rows": int(len(branch_scores)),
        "branch_paths": branch_paths,
        "runtime_target_rows": int(len(runtime_df)),
        "runtime_candidate_set_id": target_candidate_set_id,
        "runtime_path_ids": runtime_path_ids,
        "runtime_path_ids_matching_regime_profit_branch_paths": matching_paths,
        "runtime_can_consume_exact_branch_paths_without_mapping": bool(matching_paths),
        "promotion_status": "not_promoted:runtime_target_path_ids_do_not_match_regime_profit_branch_paths"
        if not matching_paths
        else "needs_apply_readback",
    }
    summary_path = output_dir / "branch_catboost_runtime_gap_summary_v1.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    md_path = output_dir / "branch_catboost_runtime_gap_summary_v1.md"
    md_path.write_text(
        "\n".join(
            [
                "# Branch CatBoost Runtime Gap Probe v1",
                "",
                f"- Branch rows: `{len(df)}`; chronological train rows: `{len(train_df)}`; holdout rows: `{len(test_df)}`.",
                f"- CatBoost model: `{model_path}`.",
                f"- Branch score rows: `{len(branch_scores)}`.",
                f"- Runtime target rows: `{len(runtime_df)}`.",
                f"- Exact branch paths matching runtime `path_id`: `{len(matching_paths)}`.",
                f"- Promotion status: `{summary['promotion_status']}`.",
                "",
                "## Branch Paths",
                *(f"- `{p}`" for p in branch_paths),
                "",
                "## Runtime Path IDs",
                *(f"- `{p}`" for p in runtime_path_ids),
                "",
            ]
        )
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
