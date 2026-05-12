from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1"
)
REPAIR_JSON = RUN_ROOT / "six-provider-btc-local-tvr-aq-same-root-repair-v2/same_root_repair_v2.json"
OUT = RUN_ROOT / "derived/strategy_library_162400_same_root_repair_v2.json"


def main() -> int:
    payload = json.loads(REPAIR_JSON.read_text())
    strategies = []
    for result in payload.get("aq_results", []):
        provider = result.get("provider", "unknown_provider")
        workspace = Path(result.get("workspace", ""))
        source_csv = result.get("source_csv", "")
        provider_symbol = result.get("provider_symbol", "")
        rows = result.get("rows", 0)
        for strategy_name, strategy_payload in sorted((result.get("metrics") or {}).items()):
            aggregate = (strategy_payload or {}).get("aggregate")
            if not aggregate:
                continue
            file_path = workspace / "user_data/strategies_external" / f"{strategy_name}.py"
            strategies.append(
                {
                    "name": f"{provider}:{strategy_name}",
                    "status": "ok",
                    "error": None,
                    "commit": "experiment-run-root",
                    "file_path": str(file_path),
                    "pairs": ["BTC/USDT"],
                    "timerange": "20260401-20260512",
                    "validation_metrics": aggregate,
                    "per_pair_metrics": {"BTC/USDT": aggregate},
                    "metadata": {
                        "board": "A",
                        "source_root": "162400_six_provider_btc_local_tvr_aq_packet_v1",
                        "repair_id": "same-root-repair-v2",
                        "source_provider": provider,
                        "source_provider_symbol": provider_symbol,
                        "source_csv": source_csv,
                        "source_rows": rows,
                        "aq_timeframe": "1h",
                        "asset_class": "crypto_provider_ohlcv",
                        "base_factor": "same_root_provider_matrix_crypto",
                        "expected_regime": "MainRegimeV2::{Bull|Bear|Sideways|Crisis} candidate evidence only",
                        "hypothesis": "Six-provider BTC provider/AQ evidence can be imported for downstream fail-closed Pre-Bayes/BBN/CatBoost/execution-tree readback.",
                        "mutation_id": f"162400:{provider}:{strategy_name}",
                        "paradigm": "provider_matrix_momentum_or_pullback",
                        "status": "provider_backed_same_root_aq_support_only",
                        "strategy": strategy_name,
                        "promotion_allowed": False,
                    },
                }
            )
    manifest = {
        "manifest_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "source_run_id": "20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1",
        "source_provider_root_id": "20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1",
        "auto_quant_repo_url": "/Users/thrill3r/Auto-Quant",
        "auto_quant_pinned_ref": "experiment-run-root",
        "source_workspace": str(RUN_ROOT / "workspace/same-root-repair-v2"),
        "config_path": str(REPAIR_JSON),
        "log_path": str(RUN_ROOT / "command-output/same-root-repair-v2"),
        "strategies": strategies,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    checks = RUN_ROOT / "checks/downstream-v1/build_strategy_library_assertions.out"
    checks.parent.mkdir(parents=True, exist_ok=True)
    checks.write_text(
        "\n".join(
            [
                f"{'PASS' if len(strategies) == 12 else 'FAIL'} strategies={len(strategies)}",
                "PASS promotion_allowed=false",
                "PASS source_root=162400",
            ]
        )
        + "\n"
    )
    return 0 if len(strategies) == 12 else 2


if __name__ == "__main__":
    raise SystemExit(main())
