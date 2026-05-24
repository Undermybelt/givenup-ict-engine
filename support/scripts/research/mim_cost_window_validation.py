from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from math import ceil
from typing import Sequence


@dataclass(frozen=True)
class PurgedSplit:
    name: str
    train_indices: list[int]
    test_indices: list[int]
    train_dates: list[date]
    test_dates: list[date]
    purge_days: int
    embargo_days: int


def purged_walk_forward_splits(
    events: Sequence[dict[str, object]],
    *,
    n_splits: int = 3,
    purge_days: int = 1,
    embargo_days: int = 1,
) -> list[PurgedSplit]:
    dated = sorted(
        ((idx, _parse_date(row.get("event_date"))) for idx, row in enumerate(events)),
        key=lambda item: (item[1], item[0]),
    )
    if not dated:
        return []
    if n_splits <= 0:
        raise ValueError("n_splits must be positive")
    fold_size = max(1, ceil(len(dated) / n_splits))
    splits: list[PurgedSplit] = []
    for fold_idx in range(n_splits):
        start = fold_idx * fold_size
        stop = min(len(dated), start + fold_size)
        test = dated[start:stop]
        if not test:
            break
        test_indices = [idx for idx, _ in test]
        test_dates = [event_date for _, event_date in test]
        first_test = min(test_dates)
        last_test = max(test_dates)
        purge_start = first_test - timedelta(days=purge_days)
        embargo_stop = last_test + timedelta(days=embargo_days)
        train = [
            (idx, event_date)
            for idx, event_date in dated
            if idx not in test_indices and (event_date < purge_start or event_date > embargo_stop)
        ]
        splits.append(
            PurgedSplit(
                name=f"fold_{fold_idx + 1}",
                train_indices=[idx for idx, _ in train],
                test_indices=test_indices,
                train_dates=[event_date for _, event_date in train],
                test_dates=test_dates,
                purge_days=purge_days,
                embargo_days=embargo_days,
            )
        )
    return splits


def build_validation_summary(splits: Sequence[PurgedSplit], *, branch_path: str) -> dict[str, object]:
    return {
        "branch_path": branch_path,
        "split_count": len(splits),
        "folds": [
            {
                "name": split.name,
                "train_count": len(split.train_indices),
                "test_count": len(split.test_indices),
                "purge_days": split.purge_days,
                "embargo_days": split.embargo_days,
            }
            for split in splits
        ],
        "promotion_allowed": False,
        "trade_usable": False,
        "downstream_allowed": False,
    }


def _parse_date(value: object) -> date:
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        raise ValueError("event row missing event_date")
    return date.fromisoformat(value.strip()[:10])
