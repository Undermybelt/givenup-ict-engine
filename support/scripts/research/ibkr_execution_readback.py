#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


IBKR_GATEWAY_PORT_CANDIDATES = [
    ("TWS paper", 7497),
    ("TWS live", 7496),
    ("IB Gateway paper", 4002),
    ("IB Gateway live", 4001),
]


def _support_scripts_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _import_ibkr_bridge() -> tuple[Any, Any, Any, Any]:
    scripts_root = _support_scripts_root()
    if str(scripts_root) not in sys.path:
        sys.path.insert(0, str(scripts_root))
    try:
        from ibkr_bridge.client_id import connect_with_client_id_fallback
        from ibkr_bridge.consent import require_ibkr_enabled
        from ibkr_bridge.rate_limiter import IbkrRateLimiter
    except ImportError as exc:
        raise SystemExit(
            "ibkr_execution_readback requires support/scripts/ibkr_bridge. "
            f"Underlying error: {exc}"
        )
    try:
        import ib_async
    except ImportError as exc:
        raise SystemExit(
            "ibkr_execution_readback requires `ib_async`; install the same "
            f"IBKR bridge dependency set used by fetch_external.py. Underlying error: {exc}"
        )
    return require_ibkr_enabled, IbkrRateLimiter, connect_with_client_id_fallback, ib_async


def _probe_tcp_port(host: str, port: int, timeout: float = 0.15) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _resolve_ibkr_gateway_port(host: str, explicit_port: int | None) -> int:
    if explicit_port is not None:
        return explicit_port
    reachable = [
        (label, port)
        for label, port in IBKR_GATEWAY_PORT_CANDIDATES
        if _probe_tcp_port(host, port)
    ]
    if not reachable:
        candidates = ", ".join(f"{label}:{port}" for label, port in IBKR_GATEWAY_PORT_CANDIDATES)
        raise SystemExit(
            f"ibkr-execution-readback: no reachable local IBKR API port on {host}; "
            f"probed {candidates}. Launch TWS/IB Gateway with API enabled or pass --port."
        )
    selected_label, selected_port = reachable[0]
    if len(reachable) == 1:
        print(
            f"  ibkr-execution-readback: auto-selected {selected_label} port {selected_port}",
            file=sys.stderr,
        )
    return selected_port


def _get(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _time_text(value: Any) -> str:
    if isinstance(value, datetime):
        current = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return current.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    text = str(value or "").strip()
    return text


def _commission_report_present(report: Any) -> bool:
    if report is None:
        return False
    return any(
        [
            bool(str(_get(report, "execId", "") or "").strip()),
            bool(str(_get(report, "currency", "") or "").strip()),
            _float(_get(report, "commission", 0.0)) != 0.0,
            _float(_get(report, "realizedPNL", 0.0)) != 0.0,
        ]
    )


def fill_to_readback_row(fill: Any) -> dict[str, Any]:
    contract = _get(fill, "contract")
    execution = _get(fill, "execution")
    commission_report = _get(fill, "commissionReport")
    report_present = _commission_report_present(commission_report)
    execution_time = _get(execution, "time", None) or _get(fill, "time", None)
    return {
        "contract": {
            "conId": _int(_get(contract, "conId", _get(contract, "conid", 0))),
            "symbol": str(_get(contract, "symbol", "") or ""),
            "secType": str(_get(contract, "secType", "") or ""),
            "exchange": str(_get(contract, "exchange", "") or ""),
            "currency": str(_get(contract, "currency", "") or ""),
            "localSymbol": str(_get(contract, "localSymbol", "") or ""),
        },
        "exec_id": str(_get(execution, "execId", "") or ""),
        "time": _time_text(execution_time),
        "side": str(_get(execution, "side", "") or ""),
        "shares": _float(_get(execution, "shares", 0.0)),
        "price": _float(_get(execution, "price", 0.0)),
        "order_id": _int(_get(execution, "orderId", 0)),
        "perm_id": _int(_get(execution, "permId", 0)),
        "client_id": _int(_get(execution, "clientId", 0)),
        "exchange": str(_get(execution, "exchange", "") or ""),
        "commission": _float(_get(commission_report, "commission", 0.0)) if report_present else None,
        "realized_pnl": _float(_get(commission_report, "realizedPNL", 0.0)) if report_present else None,
        "currency": str(_get(commission_report, "currency", "") or "") if report_present else "",
        "commission_report_present": report_present,
        "broker_fill_evidence": report_present,
    }


def _build_execution_filter(args: argparse.Namespace, ib_async: Any) -> Any:
    return ib_async.ExecutionFilter(
        clientId=args.filter_client_id,
        acctCode=args.account or "",
        time=args.time or "",
        symbol=args.symbol or "",
        secType=args.sec_type or "",
        exchange=args.exchange or "",
        side=args.side or "",
    )


def _matches_local_row_filters(row: dict[str, Any], args: argparse.Namespace) -> bool:
    local_symbol = str(row.get("contract", {}).get("localSymbol") or "")
    if args.local_symbol and local_symbol != args.local_symbol:
        return False
    return True


def _matches_commission_filter(row: dict[str, Any], args: argparse.Namespace) -> bool:
    return not args.require_commission_report or row.get("commission_report_present") is True


def write_readback_packet(
    *,
    output: Path,
    rows: list[dict[str, Any]],
    args: argparse.Namespace,
    selected_client_id: int | None,
    attempted_client_id_conflicts: list[tuple[int, str]],
    raw_execution_rows_total: int | None = None,
    rows_after_local_filters: int | None = None,
    rows_filtered_without_commission_report: int = 0,
) -> dict[str, Any]:
    raw_total = len(rows) if raw_execution_rows_total is None else raw_execution_rows_total
    local_total = len(rows) if rows_after_local_filters is None else rows_after_local_filters
    rows_without_commission_after_local_filters = rows_filtered_without_commission_report + sum(
        1 for row in rows if not row.get("commission_report_present")
    )
    packet = {
        "schema_version": "ibkr-execution-readback/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "ibkr_reqExecutions_readonly",
        "readonly": True,
        "host": args.host,
        "port": args.port,
        "client_id": selected_client_id,
        "attempted_client_id_conflicts": attempted_client_id_conflicts,
        "filters": {
            "symbol": args.symbol,
            "sec_type": args.sec_type,
            "exchange": args.exchange,
            "side": args.side,
            "account": args.account,
            "time": args.time,
            "local_symbol": args.local_symbol,
            "filter_client_id": args.filter_client_id,
            "require_commission_report": args.require_commission_report,
        },
        "raw_execution_rows_total": raw_total,
        "rows_after_local_filters": local_total,
        "rows_filtered_by_local_filters": max(0, raw_total - local_total),
        "execution_rows_total": len(rows),
        "rows_with_commission_report": sum(1 for row in rows if row.get("commission_report_present")),
        "rows_without_commission_report_after_local_filters": rows_without_commission_after_local_filters,
        "rows_filtered_without_commission_report": rows_filtered_without_commission_report,
        "rows": rows,
        "accepted_feedback_requirement": "round-trip paired executions with broker_fill_evidence=true and commission_report_present=true",
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet


async def read_ibkr_executions(args: argparse.Namespace) -> int:
    require_ibkr_enabled, IbkrRateLimiter, connect_with_client_id_fallback, ib_async = _import_ibkr_bridge()
    require_ibkr_enabled()

    args.port = _resolve_ibkr_gateway_port(args.host, args.port)
    limiter = IbkrRateLimiter(redis_url=args.redis_url)
    ib = ib_async.IB()
    ib.RaiseRequestErrors = True
    selected_client_id: int | None = None
    attempted_client_id_conflicts: list[tuple[int, str]] = []
    try:
        await limiter.wait_for_outbound_msg()
        selected_client_id, attempted_client_id_conflicts = await connect_with_client_id_fallback(
            ib,
            host=args.host,
            port=args.port,
            preferred_client_id=args.client_id,
            readonly=True,
        )
        await limiter.wait_for_outbound_msg()
        fills = await asyncio.wait_for(
            ib.reqExecutionsAsync(_build_execution_filter(args, ib_async)),
            timeout=args.request_timeout,
        )
        raw_rows = [fill_to_readback_row(fill) for fill in list(fills or [])]
        local_filtered_rows = [row for row in raw_rows if _matches_local_row_filters(row, args)]
        rows_filtered_without_commission_report = sum(
            1
            for row in local_filtered_rows
            if args.require_commission_report and row.get("commission_report_present") is not True
        )
        rows = [row for row in local_filtered_rows if _matches_commission_filter(row, args)]
        packet = write_readback_packet(
            output=Path(args.output),
            rows=rows,
            args=args,
            selected_client_id=selected_client_id,
            attempted_client_id_conflicts=attempted_client_id_conflicts,
            raw_execution_rows_total=len(raw_rows),
            rows_after_local_filters=len(local_filtered_rows),
            rows_filtered_without_commission_report=rows_filtered_without_commission_report,
        )
        print(json.dumps({"ok": True, "execution_rows_total": packet["execution_rows_total"], "output": args.output}))
        return 0
    finally:
        try:
            if ib.isConnected():
                ib.disconnect()
        except Exception:
            pass


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only IBKR reqExecutions audit for accepted paper/broker feedback preflight."
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--client-id", type=int, default=24)
    parser.add_argument("--redis-url", default="redis://localhost:6379")
    parser.add_argument("--request-timeout", type=float, default=30.0)
    parser.add_argument("--symbol", default="")
    parser.add_argument("--sec-type", default="")
    parser.add_argument("--exchange", default="")
    parser.add_argument("--side", default="")
    parser.add_argument("--account", default="")
    parser.add_argument("--time", default="", help="IBKR execution filter time, e.g. 20260531 00:00:00")
    parser.add_argument("--local-symbol", default="")
    parser.add_argument("--filter-client-id", type=int, default=0)
    parser.add_argument(
        "--allow-missing-commission-report",
        action="store_true",
        help="Keep rows without commissionReport evidence for diagnostics only.",
    )
    args = parser.parse_args(argv)
    args.require_commission_report = not args.allow_missing_commission_report
    return args


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(read_ibkr_executions(parse_args(argv)))


if __name__ == "__main__":
    raise SystemExit(main())
