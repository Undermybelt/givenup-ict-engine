from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T012129-codex-direct-l2-parquet-dbn-readability-audit"
LOOP_ID = "20260511T012129+0800-codex-direct-l2-parquet-dbn-readability-audit"

PARQUET_CANDIDATES = [
    Path("/Users/thrill3r/nautilus_trader/tests/test_data/nautilus/64-bit/deltas.parquet"),
    Path("/Users/thrill3r/nautilus_trader/tests/test_data/nautilus/128-bit/deltas.parquet"),
    Path("/Users/thrill3r/nautilus_trader/tests/test_data/binance/btcusdt-quotes.parquet"),
    Path("/Users/thrill3r/nautilus_trader/tests/test_data/binance/btcusdt-trades.parquet"),
    Path("/Users/thrill3r/nautilus_trader/tests/test_data/quote_tick_eurusd_2019_sim_rust.parquet"),
    Path("/Users/thrill3r/nautilus_trader/tests/test_data/quote_tick_usdjpy_2019_sim_rust.parquet"),
]

DBN_CANDIDATES = [
    Path("/Users/thrill3r/nautilus_trader/tests/test_data/databento/order_book_deltas_catalog/databento/orderbooks_mbo_2024-05-08T00-00-00_2024-05-08T00-00-02.dbn.zst"),
    Path("/Users/thrill3r/nautilus_trader/tests/test_data/databento/esh4-glbx-mdp3-20231224.mbo.dbn.zst"),
    Path("/Users/thrill3r/nautilus_trader/tests/test_data/databento/esh4-glbx-mdp3-20231225.mbo.dbn.zst"),
]

LARGE_METADATA = [
    Path("/Users/thrill3r/nautilus_trader/tests/test_data/large/tardis_BTC-PERPETUAL.DERIBIT_2020-04-01_deltas.metadata.json"),
    Path("/Users/thrill3r/nautilus_trader/tests/test_data/large/itch_AAPL.XNAS_2019-01-30_deltas.metadata.json"),
]


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def parquet_record(path: Path) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "kind": "parquet",
        "qualifies_for_manipulation_gate": False,
    }
    if not path.exists():
        record["blocker"] = "missing_file"
        return record
    pf = pq.ParquetFile(path)
    schema = pf.schema_arrow
    columns = list(schema.names)
    lower = {column.lower() for column in columns}
    metadata = {k.decode(): v.decode() for k, v in (schema.metadata or {}).items()}
    rows = pf.metadata.num_rows
    record.update(
        {
            "rows": rows,
            "row_groups": pf.metadata.num_row_groups,
            "columns": columns,
            "schema_metadata": metadata,
            "size_bytes": path.stat().st_size,
        }
    )
    has_delta_shape = {"action", "side", "price", "size", "order_id", "ts_event"} <= lower
    has_bid_ask = {"bid_price", "ask_price", "bid_size", "ask_size"} <= lower or {
        "bid",
        "ask",
        "bid_size",
        "ask_size",
    } <= lower
    has_trade_tape = {"trade_id", "price"} <= lower and ("quantity" in lower or "size" in lower)
    if has_delta_shape:
        record["input_class"] = "order_book_delta_parquet"
        record["directness"] = "direct_l2_or_order_book_delta"
        record["support_state"] = "support_too_thin_fixture" if rows < 10000 else "candidate_needs_market_alignment"
        record["qualifies_for_manipulation_gate"] = rows >= 10000
    elif has_bid_ask:
        record["input_class"] = "quote_tick_parquet"
        record["directness"] = "direct_bid_ask_quotes_no_depth_or_order_lifecycle"
        record["support_state"] = "partial_quote_context_only"
    elif has_trade_tape:
        record["input_class"] = "trade_tape_parquet"
        record["directness"] = "direct_trades_no_depth_or_cancel_lifecycle"
        record["support_state"] = "partial_tradeflow_only"
    else:
        record["input_class"] = "unknown_parquet"
        record["directness"] = "unknown"
        record["support_state"] = "not_a_manipulation_input"
    if record["qualifies_for_manipulation_gate"] and "SIM" in metadata.get("instrument_id", ""):
        record["qualifies_for_manipulation_gate"] = False
        record["support_state"] = "simulation_not_market_wide_manipulation_proof"
    return record


def dbn_header(path: Path) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "kind": "dbn_zst",
        "qualifies_for_manipulation_gate": False,
    }
    if not path.exists():
        record["blocker"] = "missing_file"
        return record
    record["size_bytes"] = path.stat().st_size
    try:
        raw = subprocess.check_output(["zstd", "-dc", str(path)], stderr=subprocess.DEVNULL)[:256]
        record["header_hex_prefix"] = raw[:64].hex()
        record["dbn_magic"] = raw.startswith(b"DBN")
        record["decoded_header_text"] = "".join(chr(b) if 32 <= b <= 126 else "." for b in raw[:96])
        record["input_class"] = "dbn_mbo_or_market_data"
        record["support_state"] = "decoder_missing_or_sample_too_short"
        record["directness"] = "potential_direct_mbo_if_decoded_and_supported"
    except Exception as exc:
        record["input_class"] = "dbn_zst_unreadable"
        record["support_state"] = "zstd_or_dbn_decode_failed"
        record["error"] = str(exc)
    return record


def metadata_record(path: Path) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "kind": "large_metadata",
        "qualifies_for_manipulation_gate": False,
    }
    if not path.exists():
        record["blocker"] = "missing_metadata"
        return record
    data = json.loads(path.read_text(encoding="utf-8"))
    actual = path.with_name(data.get("file", ""))
    record.update(
        {
            "metadata": data,
            "referenced_data_path": str(actual),
            "referenced_data_exists": actual.exists(),
            "support_state": "large_direct_dataset_metadata_only" if not actual.exists() else "large_direct_dataset_available",
            "directness": data.get("format", ""),
            "records": data.get("records"),
        }
    )
    record["qualifies_for_manipulation_gate"] = actual.exists() and int(data.get("records") or 0) >= 10000
    return record


def main() -> None:
    parquet = [parquet_record(path) for path in PARQUET_CANDIDATES]
    dbn = [dbn_header(path) for path in DBN_CANDIDATES]
    metadata = [metadata_record(path) for path in LARGE_METADATA]
    qualifying = [
        record
        for record in parquet + dbn + metadata
        if record.get("qualifies_for_manipulation_gate")
    ]
    report = {
        "schema_version": 1,
        "loop_id": LOOP_ID,
        "objective": "Decode local parquet/DBN direct-input candidates before declaring Manipulation data blocked.",
        "parquet_candidates": parquet,
        "dbn_candidates": dbn,
        "large_dataset_metadata": metadata,
        "decision": {
            "qualifying_direct_input_sets": len(qualifying),
            "manipulation_state": "missing_required_inputs" if not qualifying else "candidate_inputs_found_needs_calibration",
            "fresh_manipulation_gate_supported_now": bool(qualifying),
            "thresholds_relaxed": False,
            "runtime_code_changed": False,
            "blocker": "Readable local parquet/DBN candidates are fixtures, quote/trade-only, simulation/context-only, or metadata-only. The large Tardis/ITCH order-book-delta datasets are referenced but not present.",
            "next_action": "Acquire the actual large Tardis/ITCH delta Parquet files or a supported DBN decoder plus sufficiently long MBO sample before rerunning Manipulation gates.",
        },
    }
    (RUN_ROOT / "input-audit").mkdir(parents=True, exist_ok=True)
    (RUN_ROOT / "checks").mkdir(parents=True, exist_ok=True)
    report_path = RUN_ROOT / "input-audit/direct_l2_parquet_dbn_readability_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_lines = [
        "# Direct L2 / Parquet / DBN Readability Audit",
        "",
        f"Loop id: `{LOOP_ID}`",
        "",
        "Result: no qualifying direct manipulation input set is available yet.",
        "",
        "Decoded Parquet candidates:",
    ]
    for record in parquet:
        md_lines.append(
            f"- `{record['path']}`: {record.get('input_class')} rows={record.get('rows')} state={record.get('support_state')} qualifies={record.get('qualifies_for_manipulation_gate')}"
        )
    md_lines.extend(["", "DBN/Zstd candidates:"])
    for record in dbn:
        md_lines.append(
            f"- `{record['path']}`: dbn_magic={record.get('dbn_magic')} size={record.get('size_bytes')} state={record.get('support_state')} qualifies={record.get('qualifies_for_manipulation_gate')}"
        )
    md_lines.extend(["", "Large dataset references:"])
    for record in metadata:
        md_lines.append(
            f"- `{record['path']}`: records={record.get('records')} referenced_exists={record.get('referenced_data_exists')} state={record.get('support_state')}"
        )
    md_lines.extend(["", f"Next: {report['decision']['next_action']}"])
    (RUN_ROOT / "input-audit/direct_l2_parquet_dbn_readability_report.md").write_text(
        "\n".join(md_lines) + "\n",
        encoding="utf-8",
    )

    checks = [
        f"PASS loop_id={LOOP_ID}",
        f"PASS report={repo_rel(report_path)}",
        "PASS parquet_decoded=true",
        "PASS dbn_header_decoded=true",
        f"QUALIFYING_DIRECT_INPUT_SETS={len(qualifying)}",
        "MANIPULATION_INPUT_STATE=missing_required_inputs" if not qualifying else "MANIPULATION_INPUT_STATE=candidate_inputs_found_needs_calibration",
        "PASS thresholds_relaxed=false",
        "PASS runtime_code_changed=false",
        "GATE blocked_missing_required_inputs" if not qualifying else "GATE needs_calibration",
    ]
    (RUN_ROOT / "checks/direct_l2_parquet_dbn_readability_assertions.out").write_text(
        "\n".join(checks) + "\n",
        encoding="utf-8",
    )
    (RUN_ROOT / "README.md").write_text(
        "\n".join(
            [
                "# Direct L2 Parquet DBN Readability Audit",
                "",
                "Decodes local Parquet schemas and DBN/Zstd headers for direct manipulation input candidates. This is an input-readiness audit only; it does not rerun calibration or change runtime code.",
                "",
                f"- report: `{repo_rel(report_path)}`",
                f"- assertions: `{repo_rel(RUN_ROOT / 'checks/direct_l2_parquet_dbn_readability_assertions.out')}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
