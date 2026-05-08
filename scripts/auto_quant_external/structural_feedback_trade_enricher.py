from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def load_pending_templates(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return raw
    raise ValueError(f"pending update history at {path} must be a JSON array")


def attach_structural_feedback(
    trade: dict[str, Any],
    pending_template: dict[str, Any],
) -> dict[str, Any]:
    feedback = pending_template.get("template_feedback", {})
    structural_feedback = feedback.get("structural_feedback")
    if not structural_feedback:
        raise ValueError("pending template missing template_feedback.structural_feedback")

    enriched = dict(trade)
    enriched["structural_feedback"] = structural_feedback
    if "model_probabilities_before_trade" not in enriched and feedback.get(
        "model_probabilities_before_trade"
    ):
        enriched["model_probabilities_before_trade"] = feedback["model_probabilities_before_trade"]
    return enriched


def enrich_real_trades_jsonl(
    trades_path: Path,
    pending_update_history_path: Path,
    output_path: Path,
) -> dict[str, int]:
    trades = load_jsonl(trades_path)
    templates = load_pending_templates(pending_update_history_path)

    matched = min(len(trades), len(templates))
    enriched_rows = [
        attach_structural_feedback(trades[index], templates[index])
        for index in range(matched)
    ]
    output_path.write_text(
        "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in enriched_rows),
        encoding="utf-8",
    )
    return {
        "total_trades": len(trades),
        "templates": len(templates),
        "matched": matched,
        "unmatched": max(0, len(trades) - matched),
    }
