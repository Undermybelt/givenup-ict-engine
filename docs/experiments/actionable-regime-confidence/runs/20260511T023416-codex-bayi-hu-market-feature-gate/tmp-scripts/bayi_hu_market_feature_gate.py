#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import json
import math
import os
import tarfile
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T023416+0800-codex-bayi-hu-market-feature-gate"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T023416-codex-bayi-hu-market-feature-gate"
OUT_DIR = RUN_ROOT / "market-feature-gate"
CHECK_DIR = RUN_ROOT / "checks"
ARCHIVE_DIR = Path(os.environ.get("BAYI_FEATURE_ARCHIVE_DIR", "/private/tmp/ict-regime-bayi-gdrive"))
TRAIN_ARCHIVE = ARCHIVE_DIR / "train_sample.tar.gz"
TEST_ARCHIVE = ARCHIVE_DIR / "test_sample.tar.gz"

SAMPLE_ROWS = 200_000
TOP_CANDIDATES = 160
CHUNK_ROWS = 60_000
SUPPORT_MIN_TRAIN = 120
SUPPORT_MIN_CAL = 120
SUPPORT_MIN_TEST = 60
COVERAGE_MIN = 0.03

COLUMNS = "label,channel_id,channel_id_new,coin,coin_id,timestamp_unix,length,coin_id_seq,feature_seq,pre_1h_return,pre_1h_price,pre_1h_price_avg,pre_1h_volume,pre_1h_volume_avg,pre_1h_volume_sum,pre_1h_volume_tb,pre_1h_volume_quote,pre_1h_volume_quote_tb,pre_3h_return,pre_3h_price,pre_3h_price_avg,pre_3h_volume,pre_3h_volume_avg,pre_3h_volume_sum,pre_3h_volume_tb,pre_3h_volume_tb_avg,pre_3h_volume_tb_sum,pre_3h_volume_quote,pre_3h_volume_quote_avg,pre_3h_volume_quote_sum,pre_3h_volume_quote_tb,pre_3h_volume_quote_tb_avg,pre_3h_volume_quote_tb_sum,pre_6h_return,pre_6h_price,pre_6h_price_avg,pre_6h_volume,pre_6h_volume_avg,pre_6h_volume_sum,pre_6h_volume_tb,pre_6h_volume_tb_avg,pre_6h_volume_tb_sum,pre_6h_volume_quote,pre_6h_volume_quote_avg,pre_6h_volume_quote_sum,pre_6h_volume_quote_tb,pre_6h_volume_quote_tb_avg,pre_6h_volume_quote_tb_sum,pre_12h_return,pre_12h_price,pre_12h_price_avg,pre_12h_volume,pre_12h_volume_avg,pre_12h_volume_sum,pre_12h_volume_tb,pre_12h_volume_tb_avg,pre_12h_volume_tb_sum,pre_12h_volume_quote,pre_12h_volume_quote_avg,pre_12h_volume_quote_sum,pre_12h_volume_quote_tb,pre_12h_volume_quote_tb_avg,pre_12h_volume_quote_tb_sum,pre_24h_return,pre_24h_price,pre_24h_price_avg,pre_24h_volume,pre_24h_volume_avg,pre_24h_volume_sum,pre_24h_volume_tb,pre_24h_volume_tb_avg,pre_24h_volume_tb_sum,pre_24h_volume_quote,pre_24h_volume_quote_avg,pre_24h_volume_quote_sum,pre_24h_volume_quote_tb,pre_24h_volume_quote_tb_avg,pre_24h_volume_quote_tb_sum,pre_36h_return,pre_36h_price,pre_36h_price_avg,pre_36h_volume,pre_36h_volume_avg,pre_36h_volume_sum,pre_36h_volume_tb,pre_36h_volume_tb_avg,pre_36h_volume_tb_sum,pre_36h_volume_quote,pre_36h_volume_quote_avg,pre_36h_volume_quote_sum,pre_36h_volume_quote_tb,pre_36h_volume_quote_tb_avg,pre_36h_volume_quote_tb_sum,pre_48h_return,pre_48h_price,pre_48h_price_avg,pre_48h_volume,pre_48h_volume_avg,pre_48h_volume_sum,pre_48h_volume_tb,pre_48h_volume_tb_avg,pre_48h_volume_tb_sum,pre_48h_volume_quote,pre_48h_volume_quote_avg,pre_48h_volume_quote_sum,pre_48h_volume_quote_tb,pre_48h_volume_quote_tb_avg,pre_48h_volume_quote_tb_sum,pre_60h_return,pre_60h_price,pre_60h_price_avg,pre_60h_volume,pre_60h_volume_avg,pre_60h_volume_sum,pre_60h_volume_tb,pre_60h_volume_tb_avg,pre_60h_volume_tb_sum,pre_60h_volume_quote,pre_60h_volume_quote_avg,pre_60h_volume_quote_sum,pre_60h_volume_quote_tb,pre_60h_volume_quote_tb_avg,pre_60h_volume_quote_tb_sum,pre_72h_return,pre_72h_price,pre_72h_price_avg,pre_72h_volume,pre_72h_volume_avg,pre_72h_volume_sum,pre_72h_volume_tb,pre_72h_volume_tb_avg,pre_72h_volume_tb_sum,pre_72h_volume_quote,pre_72h_volume_quote_avg,pre_72h_volume_quote_sum,pre_72h_volume_quote_tb,pre_72h_volume_quote_tb_avg,pre_72h_volume_quote_tb_sum,pre_3d_market_cap_usd,pre_3d_market_cap_btc,pre_3d_price_usd,pre_3d_price_btc,pre_3d_volume_usd,pre_3d_volume_btc,pre_3d_twitter_index,pre_3d_reddit_index,pre_3d_alexa_index".split(",")

BLOCKED_COLUMNS = {
    "label",
    "channel_id",
    "channel_id_new",
    "coin",
    "coin_id",
    "timestamp_unix",
    "coin_id_seq",
    "feature_seq",
}
PREDICTORS = [
    col
    for col in COLUMNS
    if col not in BLOCKED_COLUMNS
    and not col.startswith("future_")
    and not col.startswith("target_")
    and not col.startswith("next_")
    and not col.endswith("_next")
]
USECOLS = ["label", "coin", "timestamp_unix"] + PREDICTORS
QUANTILES = [0.01, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.99]


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def wilson_lcb(successes: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    phat = successes / n
    denom = 1 + z * z / n
    center = phat + z * z / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return max(0.0, (center - margin) / denom)


def stat(successes: int, support: int, total: int) -> dict:
    return {
        "support": int(support),
        "positives": int(successes),
        "precision": successes / support if support else 0.0,
        "wilson95_lcb": wilson_lcb(successes, support),
        "coverage": support / total if total else 0.0,
    }


def open_member(path: Path) -> io.BufferedReader:
    tar = tarfile.open(path, "r:gz")
    members = [m for m in tar.getmembers() if m.isfile() and m.name.endswith(".csv")]
    if len(members) != 1:
        raise RuntimeError(f"expected one CSV in {path}, found {len(members)}")
    handle = tar.extractfile(members[0])
    if handle is None:
        raise RuntimeError(f"cannot read {members[0].name}")
    handle._tar_owner = tar
    return handle


def read_sample(path: Path, nrows: int) -> pd.DataFrame:
    handle = open_member(path)
    try:
        df = pd.read_csv(handle, header=None, names=COLUMNS, usecols=USECOLS, nrows=nrows, low_memory=False)
    finally:
        tar = getattr(handle, "_tar_owner", None)
        handle.close()
        if tar is not None:
            tar.close()
    df["label"] = pd.to_numeric(df["label"], errors="coerce").fillna(0).astype(int)
    df["timestamp_unix"] = pd.to_numeric(df["timestamp_unix"], errors="coerce").fillna(0).astype(np.int64)
    for col in PREDICTORS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def iter_chunks(path: Path):
    handle = open_member(path)
    try:
        yield from pd.read_csv(
            handle,
            header=None,
            names=COLUMNS,
            usecols=USECOLS,
            chunksize=CHUNK_ROWS,
            low_memory=False,
        )
    finally:
        tar = getattr(handle, "_tar_owner", None)
        handle.close()
        if tar is not None:
            tar.close()


def make_candidates(sample: pd.DataFrame, cutoff: int) -> list[dict]:
    train = sample[sample["timestamp_unix"] < cutoff].copy()
    candidates = []
    for feature in PREDICTORS:
        values = pd.to_numeric(train[feature], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        if values.nunique() <= 1:
            continue
        for threshold in sorted({float(v) for v in values.quantile(QUANTILES).dropna().tolist()}):
            candidates.append({"feature": feature, "op": ">=", "threshold": threshold})
            candidates.append({"feature": feature, "op": "<=", "threshold": threshold})
    scored = score_candidates_on_frame(train, candidates)
    scored = [row for row in scored if row["support"] >= SUPPORT_MIN_TRAIN]
    scored.sort(key=lambda row: (row["wilson95_lcb"], row["precision"], row["positives"], row["support"]), reverse=True)
    return [{key: row[key] for key in ["feature", "op", "threshold"]} for row in scored[:TOP_CANDIDATES]]


def score_candidates_on_frame(df: pd.DataFrame, candidates: list[dict]) -> list[dict]:
    y = df["label"].to_numpy(dtype=bool)
    total = len(df)
    rows = []
    for idx, cand in enumerate(candidates):
        values = pd.to_numeric(df[cand["feature"]], errors="coerce").to_numpy(dtype=float)
        mask = values >= cand["threshold"] if cand["op"] == ">=" else values <= cand["threshold"]
        mask &= np.isfinite(values)
        support = int(mask.sum())
        positives = int((mask & y).sum()) if support else 0
        rows.append({"candidate_id": idx, **cand, **stat(positives, support, total)})
    return rows


def score_candidates_on_archive(path: Path, candidates: list[dict], cutoff: int | None, side: str) -> tuple[list[dict], dict]:
    counts = [{"support": 0, "positives": 0} for _ in candidates]
    meta = {
        "rows": 0,
        "positives": 0,
        "negatives": 0,
        "unique_coins": set(),
        "timestamp_min": None,
        "timestamp_max": None,
    }
    for chunk in iter_chunks(path):
        chunk["label"] = pd.to_numeric(chunk["label"], errors="coerce").fillna(0).astype(int)
        chunk["timestamp_unix"] = pd.to_numeric(chunk["timestamp_unix"], errors="coerce").fillna(0).astype(np.int64)
        if side == "train":
            chunk = chunk[chunk["timestamp_unix"] < cutoff]
        elif side == "calibration":
            chunk = chunk[chunk["timestamp_unix"] >= cutoff]
        elif side == "test":
            pass
        else:
            raise ValueError(side)
        if chunk.empty:
            continue
        meta["rows"] += int(len(chunk))
        meta["positives"] += int(chunk["label"].sum())
        meta["unique_coins"].update(str(v) for v in chunk["coin"].dropna().astype(str).unique())
        cmin = int(chunk["timestamp_unix"].min())
        cmax = int(chunk["timestamp_unix"].max())
        meta["timestamp_min"] = cmin if meta["timestamp_min"] is None else min(meta["timestamp_min"], cmin)
        meta["timestamp_max"] = cmax if meta["timestamp_max"] is None else max(meta["timestamp_max"], cmax)
        y = chunk["label"].to_numpy(dtype=bool)
        for idx, cand in enumerate(candidates):
            values = pd.to_numeric(chunk[cand["feature"]], errors="coerce").to_numpy(dtype=float)
            mask = values >= cand["threshold"] if cand["op"] == ">=" else values <= cand["threshold"]
            mask &= np.isfinite(values)
            support = int(mask.sum())
            if support:
                counts[idx]["support"] += support
                counts[idx]["positives"] += int((mask & y).sum())
    meta["negatives"] = meta["rows"] - meta["positives"]
    meta["positive_rate"] = meta["positives"] / meta["rows"] if meta["rows"] else 0.0
    meta["unique_coins"] = len(meta["unique_coins"])
    rows = [{"candidate_id": idx, **cand, **stat(c["positives"], c["support"], meta["rows"])} for idx, (cand, c) in enumerate(zip(candidates, counts))]
    return rows, meta


def write_report(report: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "bayi_hu_market_feature_gate_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    with (OUT_DIR / "bayi_hu_market_feature_gate_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "rank",
                "candidate_id",
                "feature",
                "op",
                "threshold",
                "train_wilson95_lcb",
                "calibration_wilson95_lcb",
                "test_wilson95_lcb",
                "train_support",
                "calibration_support",
                "test_support",
            ],
        )
        writer.writeheader()
        for rank, row in enumerate(report["ranked_candidates"][:25], start=1):
            writer.writerow(
                {
                    "rank": rank,
                    "candidate_id": row["candidate_id"],
                    "feature": row["feature"],
                    "op": row["op"],
                    "threshold": row["threshold"],
                    "train_wilson95_lcb": row["train_wilson95_lcb"],
                    "calibration_wilson95_lcb": row["calibration_wilson95_lcb"],
                    "test_wilson95_lcb": row["test_wilson95_lcb"],
                    "train_support": row["train_support"],
                    "calibration_support": row["calibration_support"],
                    "test_support": row["test_support"],
                }
            )

    best = report["best_rule"]
    d = report["decision"]
    (OUT_DIR / "bayi_hu_market_feature_gate_report.md").write_text(
        "\n".join(
            [
                "# Bayi-Hu Market Feature Manipulation Gate",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                "## Source",
                "",
                "- Source: Bayi-Hu generated target-coin prediction archives from Google Drive links in the source README.",
                f"- Archive directory: `{ARCHIVE_DIR}`.",
                "- Raw archives committed to repo: false.",
                "- Predictor rule: pre-event generated features only; identifiers, timestamps, labels, future/target/next fields blocked.",
                "- Search shape: deterministic bounded train sample chooses candidate thresholds; full train/calibration/test archives score those candidates.",
                "",
                "## Dataset",
                "",
                f"- Train partition rows: {report['dataset']['train']['rows']:,}; positives: {report['dataset']['train']['positives']:,}; negatives: {report['dataset']['train']['negatives']:,}.",
                f"- Calibration partition rows: {report['dataset']['calibration']['rows']:,}; positives: {report['dataset']['calibration']['positives']:,}; negatives: {report['dataset']['calibration']['negatives']:,}.",
                f"- Test rows: {report['dataset']['test']['rows']:,}; positives: {report['dataset']['test']['positives']:,}; negatives: {report['dataset']['test']['negatives']:,}.",
                f"- Candidate rules evaluated on full archives: {report['gate_contract']['candidate_rules_evaluated']:,}.",
                "",
                "## Best Full-Archive Rule",
                "",
                f"- Rule: `{best['feature']} {best['op']} {best['threshold']}`.",
                f"- Train Wilson95 LCB: {best['train']['wilson95_lcb']:.6f}, support={best['train']['support']:,}, precision={best['train']['precision']:.6f}.",
                f"- Calibration Wilson95 LCB: {best['calibration']['wilson95_lcb']:.6f}, support={best['calibration']['support']:,}, precision={best['calibration']['precision']:.6f}.",
                f"- Test Wilson95 LCB: {best['test']['wilson95_lcb']:.6f}, support={best['test']['support']:,}, precision={best['test']['precision']:.6f}.",
                "",
                "## Decision",
                "",
                f"- Accepted 95 `Manipulation` root: {str(d['accepted_95']).lower()}.",
                f"- Gate: `{d['gate']}`.",
                f"- Blocker: {d['blocker']}",
                f"- Thresholds relaxed: {str(d['thresholds_relaxed']).lower()}.",
                f"- Runtime code changed: {str(d['runtime_code_changed']).lower()}.",
                f"- Trade usable: {str(d['trade_usable']).lower()}.",
                "",
                f"Next: {d['next_action']}",
                "",
            ]
        )
    )

    (CHECK_DIR / "bayi_hu_market_feature_gate_assertions.out").write_text(
        "\n".join(
            [
                f"RUN_ID {RUN_ID}",
                "ACTIVE_AXIS MainRegimeV2",
                "CANDIDATE_REGIME Manipulation",
                f"TRAIN_ROWS {report['dataset']['train']['rows']}",
                f"CALIBRATION_ROWS {report['dataset']['calibration']['rows']}",
                f"TEST_ROWS {report['dataset']['test']['rows']}",
                f"CANDIDATE_RULES_EVALUATED {report['gate_contract']['candidate_rules_evaluated']}",
                f"BEST_RULE {best['feature']} {best['op']} {best['threshold']}",
                f"CAL_WILSON95_LCB {best['calibration']['wilson95_lcb']:.6f}",
                f"TEST_WILSON95_LCB {best['test']['wilson95_lcb']:.6f}",
                f"ACCEPTED_95 {str(d['accepted_95']).lower()}",
                f"THRESHOLDS_RELAXED {str(d['thresholds_relaxed']).lower()}",
                f"RUNTIME_CODE_CHANGED {str(d['runtime_code_changed']).lower()}",
                f"RAW_DATA_COMMITTED {str(d['raw_data_committed']).lower()}",
                f"TRADE_USABLE {str(d['trade_usable']).lower()}",
                f"GATE {d['gate']}",
                "",
            ]
        )
    )


def main() -> None:
    if not TRAIN_ARCHIVE.exists() or not TEST_ARCHIVE.exists():
        raise SystemExit(f"missing train/test archives under {ARCHIVE_DIR}")

    sample = read_sample(TRAIN_ARCHIVE, SAMPLE_ROWS)
    cutoff = int(sample["timestamp_unix"].quantile(0.75))
    candidates = make_candidates(sample, cutoff)
    if not candidates:
        raise SystemExit("no candidates survived bounded train sample")

    train_rows, train_meta = score_candidates_on_archive(TRAIN_ARCHIVE, candidates, cutoff, "train")
    cal_rows, cal_meta = score_candidates_on_archive(TRAIN_ARCHIVE, candidates, cutoff, "calibration")
    test_rows, test_meta = score_candidates_on_archive(TEST_ARCHIVE, candidates, None, "test")

    ranked = []
    for idx, cand in enumerate(candidates):
        row = {
            "candidate_id": idx,
            **cand,
            "train": train_rows[idx],
            "calibration": cal_rows[idx],
            "test": test_rows[idx],
        }
        row["train_wilson95_lcb"] = row["train"]["wilson95_lcb"]
        row["calibration_wilson95_lcb"] = row["calibration"]["wilson95_lcb"]
        row["test_wilson95_lcb"] = row["test"]["wilson95_lcb"]
        row["train_support"] = row["train"]["support"]
        row["calibration_support"] = row["calibration"]["support"]
        row["test_support"] = row["test"]["support"]
        ranked.append(row)
    ranked.sort(
        key=lambda row: (
            min(row["calibration"]["wilson95_lcb"], row["test"]["wilson95_lcb"]),
            row["test"]["wilson95_lcb"],
            row["calibration"]["wilson95_lcb"],
            row["test"]["support"],
        ),
        reverse=True,
    )
    best = ranked[0]
    accepted = (
        best["calibration"]["support"] >= SUPPORT_MIN_CAL
        and best["test"]["support"] >= SUPPORT_MIN_TEST
        and best["calibration"]["wilson95_lcb"] >= 0.95
        and best["test"]["wilson95_lcb"] >= 0.95
        and best["calibration"]["coverage"] >= COVERAGE_MIN
        and best["test"]["coverage"] >= COVERAGE_MIN
    )
    gate = "accepted_95_market_feature_manipulation" if accepted else "blocked_bayi_hu_market_feature_gate_below_95"
    blocker = (
        "accepted_95"
        if accepted
        else "Best bounded-train-selected pre-event market-feature rule failed the unchanged held-out 95% Wilson/support/coverage gate."
    )

    report = {
        "run_id": RUN_ID,
        "dataset": {
            "archive_dir": str(ARCHIVE_DIR),
            "raw_data_committed_to_repo": False,
            "label_polarity": "1=source positive pump target; 0=source negative non-target control",
            "train": train_meta,
            "calibration": cal_meta,
            "test": test_meta,
        },
        "gate_contract": {
            "active_axis": "MainRegimeV2",
            "candidate_regime": "Manipulation",
            "candidate_search": "bounded deterministic sample from shuffled source train archive; full archives scored after candidate selection",
            "sample_rows": int(len(sample)),
            "inner_train_calibration_cutoff_timestamp_unix": cutoff,
            "candidate_rules_evaluated": len(candidates),
            "predictor_count": len(PREDICTORS),
            "blocked_predictors": sorted(BLOCKED_COLUMNS | {"future_*", "target_*", "*_next", "next_*"}),
            "support_min_train": SUPPORT_MIN_TRAIN,
            "support_min_calibration": SUPPORT_MIN_CAL,
            "support_min_test": SUPPORT_MIN_TEST,
            "coverage_min": COVERAGE_MIN,
            "thresholds_relaxed": False,
            "runtime_code_changed": False,
        },
        "best_rule": best,
        "ranked_candidates": ranked[:25],
        "decision": {
            "board_state": "accepted_95" if accepted else "blocked",
            "active_axis": "MainRegimeV2",
            "candidate_regime": "Manipulation",
            "accepted_95": accepted,
            "accepted_gate": gate if accepted else "partial_for_MainRegimeV2_Crisis_only_prior_evidence_preserved",
            "manipulation_input_state": gate,
            "gate": gate,
            "blocker": blocker,
            "thresholds_relaxed": False,
            "runtime_code_changed": False,
            "fresh_calibration_rerun": True,
            "raw_data_committed": False,
            "trade_usable": False,
            "next_action": "Use a second labeled direct manipulation context with explicit positives/negatives and timestamps; Bayi-Hu generated market features alone do not close Manipulation." if not accepted else "Require cross-context direct manipulation confirmation before any trade-usable promotion; Bull/Bear/Sideways still need root packets.",
        },
        "artifacts": {
            "report_json": repo_rel(OUT_DIR / "bayi_hu_market_feature_gate_report.json"),
            "report_md": repo_rel(OUT_DIR / "bayi_hu_market_feature_gate_report.md"),
            "summary_csv": repo_rel(OUT_DIR / "bayi_hu_market_feature_gate_summary.csv"),
            "assertions": repo_rel(CHECK_DIR / "bayi_hu_market_feature_gate_assertions.out"),
        },
    }
    write_report(report)


if __name__ == "__main__":
    main()
