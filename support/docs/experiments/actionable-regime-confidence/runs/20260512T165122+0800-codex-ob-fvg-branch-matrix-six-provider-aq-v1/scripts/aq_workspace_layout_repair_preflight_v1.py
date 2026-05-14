from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = ROOT / "summaries/provider_provenance_matrix.csv"
OUT_DIR = ROOT / "agent-material-repair-v1"
SUMMARY = ROOT / "summaries/aq_workspace_layout_repair_preflight_v1.json"


def yyyymmdd(value: str) -> str:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y%m%d")


def load_rows() -> list[dict[str, str]]:
    with PROVENANCE.open(newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_rows()
    outputs = []
    for row in rows:
        material_path = ROOT.parent.parent.parent.parent / row["material_path"]
        if not material_path.exists():
            material_path = Path(row["material_path"])
        material = json.loads(material_path.read_text())
        start = yyyymmdd(row["first"])
        end = yyyymmdd(row["last"])
        timerange = f"{start}-{end}"
        material["timerange"] = timerange
        notes = list(material.get("notes", []))
        notes.append("repair_v1_explicit_timerange_from_provider_rows=true")
        notes.append(f"repair_v1_timerange={timerange}")
        material["notes"] = notes
        output_path = OUT_DIR / material_path.name
        output_path.write_text(json.dumps(material, indent=2, sort_keys=True) + "\n")
        branch_paths = material.get("consumer_evidence_profile", {}).get("branch_paths", [])
        outputs.append(
            {
                "provider": row["provider"],
                "input_material_path": str(material_path),
                "output_material_path": str(output_path),
                "rows": int(row["rows"]),
                "first": row["first"],
                "last": row["last"],
                "timerange": timerange,
                "symbol": material.get("symbol"),
                "timeframe": material.get("timeframe"),
                "branch_path_count": len(branch_paths),
                "branch_paths": branch_paths,
                "provider_authority_state": row["provider_authority_state"],
                "local_cache_replay": row["local_cache_replay"],
            }
        )

    providers = {item["provider"] for item in outputs}
    branch_counts = {item["branch_path_count"] for item in outputs}
    summary = {
        "run_id": ROOT.name,
        "source": "165122 provider/AQ fail-closed no-data repair preflight",
        "repair_scope": "material_json_timerange_only",
        "provider_refetch_started": False,
        "aq_dispatch_started": False,
        "output_dir": str(OUT_DIR),
        "summary_path": str(SUMMARY),
        "material_count": len(outputs),
        "provider_rows_current_same_root": len(outputs),
        "provider_rows_current_same_root_6_of_6": providers
        == {"yfinance/YF", "Binance", "Bybit", "Kraken", "IBKR", "TradingViewRemix/TVR"},
        "branch_paths_preserved_6_of_6": branch_counts == {6} and len(outputs) == 6,
        "outputs": outputs,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["provider_rows_current_same_root_6_of_6"] and summary["branch_paths_preserved_6_of_6"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
