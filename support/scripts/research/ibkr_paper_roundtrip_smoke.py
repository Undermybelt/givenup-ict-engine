#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import socket
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PAPER_PORTS = {7497: "TWS paper", 4002: "IB Gateway paper"}
LIVE_PORTS = {7496: "TWS live", 4001: "IB Gateway live"}


@dataclass(frozen=True)
class PaperOrderContext:
    account: str
    account_type: str
    managed_accounts: list[str]
    port: int
    port_label: str


def _support_scripts_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _import_ibkr_runtime() -> tuple[Any, Any, Any, Any, Any]:
    scripts_root = _support_scripts_root()
    if str(scripts_root) not in sys.path:
        sys.path.insert(0, str(scripts_root))
    try:
        from ibkr_bridge.client_id import connect_with_client_id_fallback
        from ibkr_bridge.consent import require_ibkr_enabled
        from ibkr_bridge.rate_limiter import IbkrRateLimiter
    except ImportError as exc:
        raise SystemExit(
            "ibkr_paper_roundtrip_smoke requires support/scripts/ibkr_bridge. "
            f"Underlying error: {exc}"
        )
    try:
        import ib_async
    except ImportError as exc:
        raise SystemExit(
            "ibkr_paper_roundtrip_smoke requires `ib_async`; install the same "
            f"IBKR bridge dependency set used by fetch_external.py. Underlying error: {exc}"
        )
    try:
        import ibkr_execution_readback
    except ImportError as exc:
        raise SystemExit(
            "ibkr_paper_roundtrip_smoke requires ibkr_execution_readback.py in the same directory. "
            f"Underlying error: {exc}"
        )
    return require_ibkr_enabled, IbkrRateLimiter, connect_with_client_id_fallback, ib_async, ibkr_execution_readback


def _probe_tcp_port(host: str, port: int, timeout: float = 0.15) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def resolve_paper_port(host: str, explicit_port: int | None) -> int:
    if explicit_port is not None:
        if explicit_port in LIVE_PORTS:
            raise ValueError(f"refusing live IBKR port {explicit_port} for paper roundtrip smoke")
        if explicit_port not in PAPER_PORTS:
            raise ValueError(
                f"refusing unknown IBKR port {explicit_port}; allowed paper ports are "
                + ", ".join(str(port) for port in sorted(PAPER_PORTS))
            )
        return explicit_port
    reachable = [port for port in PAPER_PORTS if _probe_tcp_port(host, port)]
    if not reachable:
        raise SystemExit(
            f"ibkr-paper-roundtrip-smoke: no reachable local paper IBKR API port on {host}; "
            "probed 7497 and 4002 only. Live ports are intentionally ignored."
        )
    return reachable[0]


def _is_paper_account(account: str) -> bool:
    normalized = account.strip().upper()
    return normalized.startswith("DU") or normalized.startswith("DF")


def validate_paper_order_context(
    *,
    port: int,
    managed_accounts: list[str],
    requested_account: str | None,
) -> PaperOrderContext:
    if port in LIVE_PORTS:
        raise ValueError(f"refusing live IBKR port {port} for paper roundtrip smoke")
    if port not in PAPER_PORTS:
        raise ValueError(f"refusing non-paper IBKR port {port}")

    accounts = [str(account).strip() for account in managed_accounts if str(account).strip()]
    paper_accounts = [account for account in accounts if _is_paper_account(account)]
    if requested_account:
        requested = requested_account.strip()
        if requested not in accounts:
            raise ValueError(f"requested account {requested} is not in managedAccounts")
        if not _is_paper_account(requested):
            raise ValueError(f"requested account {requested} is not a DU/DF paper account")
        selected = requested
    elif len(paper_accounts) == 1:
        selected = paper_accounts[0]
    elif len(paper_accounts) > 1:
        raise ValueError("multiple paper accounts found; pass --account explicitly")
    else:
        raise ValueError("no DU/DF paper account found in managedAccounts; refusing order placement")

    return PaperOrderContext(
        account=selected,
        account_type="paper",
        managed_accounts=accounts,
        port=port,
        port_label=PAPER_PORTS[port],
    )


def validate_execution_request(args: argparse.Namespace) -> None:
    if not args.execute_paper_roundtrip:
        return
    if not args.i_understand_paper_orders:
        raise ValueError(
            "paper order execution requires explicit confirmation via --i-understand-paper-orders"
        )
    if not (args.local_symbol or args.last_trade_date_or_contract_month):
        raise ValueError(
            "paper order execution requires an exact futures contract via --local-symbol "
            "or --last-trade-date-or-contract-month"
        )
    if float(args.quantity) <= 0:
        raise ValueError("--quantity must be positive")


def _contract_payload(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "symbol": args.symbol,
        "secType": "FUT",
        "exchange": args.exchange,
        "currency": args.currency,
        "localSymbol": args.local_symbol,
        "lastTradeDateOrContractMonth": args.last_trade_date_or_contract_month,
    }


def write_terminal_packet(
    *,
    root: Path,
    status: str,
    decision: str,
    account: str | None,
    port: int | None,
    client_id: int | None,
    contract: dict[str, Any],
    order_events: list[dict[str, Any]],
    execution_readback: dict[str, Any] | None,
    blockers: list[str],
) -> dict[str, Any]:
    packet = {
        "schema_version": "ibkr-paper-roundtrip-smoke/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "decision": decision,
        "account": account,
        "account_type": "paper" if account and _is_paper_account(account) else None,
        "port": port,
        "client_id": client_id,
        "contract": contract,
        "order_events": order_events,
        "execution_readback": execution_readback,
        "blockers": blockers,
        "funded_live_order_allowed": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "same_tree_practical_closure": None,
    }
    checks = root / "checks"
    summaries = root / "summaries"
    checks.mkdir(parents=True, exist_ok=True)
    summaries.mkdir(parents=True, exist_ok=True)
    text = json.dumps(packet, indent=2, sort_keys=True) + "\n"
    (checks / "terminal_metrics.json").write_text(text, encoding="utf-8")
    (summaries / "terminal_summary.json").write_text(text, encoding="utf-8")
    return packet


def _build_future_contract(args: argparse.Namespace, ib_async: Any) -> Any:
    return ib_async.Future(
        symbol=args.symbol,
        lastTradeDateOrContractMonth=args.last_trade_date_or_contract_month,
        exchange=args.exchange,
        localSymbol=args.local_symbol,
        currency=args.currency,
    )


def _market_order(ib_async: Any, action: str, args: argparse.Namespace, account: str) -> Any:
    return ib_async.MarketOrder(
        action,
        float(args.quantity),
        account=account,
        tif=args.tif,
        outsideRth=True,
        orderRef=args.order_ref,
    )


def order_status_event(trade: Any, action: str) -> dict[str, Any]:
    status = getattr(getattr(trade, "orderStatus", None), "status", "")
    fills = list(getattr(trade, "fills", []) or [])
    log_tail: list[dict[str, Any]] = []
    for entry in list(getattr(trade, "log", []) or [])[-5:]:
        log_tail.append(
            {
                "status": str(getattr(entry, "status", "") or ""),
                "message": str(getattr(entry, "message", "") or ""),
                "error_code": int(getattr(entry, "errorCode", 0) or 0),
            }
        )
    return {
        "action": action,
        "status": str(status),
        "is_done": bool(trade.isDone()),
        "filled": float(getattr(getattr(trade, "orderStatus", None), "filled", 0.0) or 0.0),
        "remaining": float(getattr(getattr(trade, "orderStatus", None), "remaining", 0.0) or 0.0),
        "fills": len(fills),
        "log_tail": log_tail,
    }


async def _wait_for_trade_done(trade: Any, timeout: float) -> dict[str, Any]:
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        if trade.isDone():
            break
        await asyncio.sleep(0.25)
    return order_status_event(trade, "wait_for_fill")


async def _request_execution_readback(
    *,
    ib: Any,
    ib_async: Any,
    readback_module: Any,
    args: argparse.Namespace,
    selected_client_id: int,
    attempted_client_id_conflicts: list[tuple[int, str]],
) -> dict[str, Any]:
    execution_filter = ib_async.ExecutionFilter(
        clientId=0,
        acctCode=args.account or "",
        time=args.execution_filter_time or "",
        symbol=args.symbol,
        secType="FUT",
        exchange=args.exchange,
        side="",
    )
    fills = await asyncio.wait_for(
        ib.reqExecutionsAsync(execution_filter),
        timeout=args.request_timeout,
    )
    raw_rows = [readback_module.fill_to_readback_row(fill) for fill in list(fills or [])]
    if args.local_symbol:
        filtered_rows = [
            row
            for row in raw_rows
            if row.get("contract", {}).get("localSymbol") == args.local_symbol
        ]
    else:
        filtered_rows = raw_rows
    rows = [row for row in filtered_rows if row.get("commission_report_present") is True]
    output = Path(args.root) / "checks" / "ibkr_execution_readback.json"
    return readback_module.write_readback_packet(
        output=output,
        rows=rows,
        args=argparse.Namespace(
            host=args.host,
            port=args.port,
            symbol=args.symbol,
            sec_type="FUT",
            exchange=args.exchange,
            side="",
            account=args.account,
            time=args.execution_filter_time,
            local_symbol=args.local_symbol,
            filter_client_id=0,
            require_commission_report=True,
        ),
        selected_client_id=selected_client_id,
        attempted_client_id_conflicts=attempted_client_id_conflicts,
        raw_execution_rows_total=len(raw_rows),
        rows_after_local_filters=len(filtered_rows),
        rows_filtered_without_commission_report=sum(
            1 for row in filtered_rows if row.get("commission_report_present") is not True
        ),
    )


async def run(args: argparse.Namespace) -> int:
    root = Path(args.root)
    validate_execution_request(args)
    contract_payload = _contract_payload(args)

    if not args.execute_paper_roundtrip and not args.connect_preflight:
        write_terminal_packet(
            root=root,
            status="dry_run_preflight_only",
            decision="paper_order_not_submitted",
            account=args.account or None,
            port=args.port,
            client_id=args.client_id,
            contract=contract_payload,
            order_events=[],
            execution_readback=None,
            blockers=["dry-run default; pass --execute-paper-roundtrip with paper-only confirmation to submit"],
        )
        print(json.dumps({"ok": True, "status": "dry_run_preflight_only", "root": str(root)}))
        return 0

    require_ibkr_enabled, IbkrRateLimiter, connect_with_client_id_fallback, ib_async, readback_module = _import_ibkr_runtime()
    require_ibkr_enabled()
    args.port = resolve_paper_port(args.host, args.port)

    limiter = IbkrRateLimiter(redis_url=args.redis_url)
    ib = ib_async.IB()
    selected_client_id: int | None = None
    attempted_client_id_conflicts: list[tuple[int, str]] = []
    order_events: list[dict[str, Any]] = []
    try:
        await limiter.wait_for_outbound_msg()
        selected_client_id, attempted_client_id_conflicts = await connect_with_client_id_fallback(
            ib,
            host=args.host,
            port=args.port,
            preferred_client_id=args.client_id,
            readonly=not args.execute_paper_roundtrip,
        )
        managed_accounts = list(ib.managedAccounts() or [])
        if not managed_accounts:
            await asyncio.sleep(1.0)
            managed_accounts = list(ib.managedAccounts() or [])
        context = validate_paper_order_context(
            port=args.port,
            managed_accounts=managed_accounts,
            requested_account=args.account or None,
        )
        args.account = context.account

        if not args.execute_paper_roundtrip:
            packet = write_terminal_packet(
                root=root,
                status="connected_paper_preflight_only",
                decision="paper_order_not_submitted",
                account=context.account,
                port=args.port,
                client_id=selected_client_id,
                contract=contract_payload,
                order_events=[],
                execution_readback=None,
                blockers=["connect preflight only"],
            )
            print(json.dumps({"ok": True, "status": packet["status"], "account": context.account, "root": str(root)}))
            return 0

        contract = _build_future_contract(args, ib_async)
        await limiter.wait_for_outbound_msg()
        qualified = await asyncio.wait_for(
            ib.qualifyContractsAsync(contract),
            timeout=args.request_timeout,
        )
        if not qualified:
            raise RuntimeError("IBKR did not qualify the requested exact futures contract")
        qualified_contract = qualified[0]
        contract_payload = {
            "conId": getattr(qualified_contract, "conId", 0),
            "symbol": getattr(qualified_contract, "symbol", args.symbol),
            "secType": getattr(qualified_contract, "secType", "FUT"),
            "exchange": getattr(qualified_contract, "exchange", args.exchange),
            "currency": getattr(qualified_contract, "currency", args.currency),
            "localSymbol": getattr(qualified_contract, "localSymbol", args.local_symbol),
            "lastTradeDateOrContractMonth": getattr(
                qualified_contract,
                "lastTradeDateOrContractMonth",
                args.last_trade_date_or_contract_month,
            ),
        }

        entry = ib.placeOrder(qualified_contract, _market_order(ib_async, args.entry_action, args, context.account))
        entry_event = await _wait_for_trade_done(entry, args.fill_timeout)
        entry_event["action"] = args.entry_action
        order_events.append(entry_event)
        if entry_event["filled"] <= 0:
            with contextlib.suppress(Exception):
                ib.cancelOrder(entry.order)
            await asyncio.sleep(args.cancel_wait)
            order_events.append(order_status_event(entry, "cancel_after_no_entry_fill"))
            packet = write_terminal_packet(
                root=root,
                status="paper_entry_not_filled",
                decision="paper_order_no_fill",
                account=context.account,
                port=args.port,
                client_id=selected_client_id,
                contract=contract_payload,
                order_events=order_events,
                execution_readback=None,
                blockers=["entry paper order did not fill before timeout"],
            )
            print(json.dumps({"ok": False, "status": packet["status"], "root": str(root)}))
            return 4

        exit_action = "SELL" if args.entry_action.upper() == "BUY" else "BUY"
        exit_trade = ib.placeOrder(qualified_contract, _market_order(ib_async, exit_action, args, context.account))
        exit_event = await _wait_for_trade_done(exit_trade, args.fill_timeout)
        exit_event["action"] = exit_action
        order_events.append(exit_event)
        if exit_event["filled"] <= 0:
            with contextlib.suppress(Exception):
                ib.cancelOrder(exit_trade.order)
            await asyncio.sleep(args.cancel_wait)
            order_events.append(order_status_event(exit_trade, "cancel_after_no_exit_fill"))
            packet = write_terminal_packet(
                root=root,
                status="paper_exit_not_filled",
                decision="paper_roundtrip_incomplete",
                account=context.account,
                port=args.port,
                client_id=selected_client_id,
                contract=contract_payload,
                order_events=order_events,
                execution_readback=None,
                blockers=["exit paper order did not fill before timeout; manual paper-account flatten check required"],
            )
            print(json.dumps({"ok": False, "status": packet["status"], "root": str(root)}))
            return 5

        await asyncio.sleep(args.post_fill_readback_delay)
        execution_readback = await _request_execution_readback(
            ib=ib,
            ib_async=ib_async,
            readback_module=readback_module,
            args=args,
            selected_client_id=selected_client_id,
            attempted_client_id_conflicts=attempted_client_id_conflicts,
        )
        readback_rows = int(execution_readback.get("execution_rows_total", 0))
        status = "paper_roundtrip_executed_readback_ready" if readback_rows >= 2 else "paper_roundtrip_executed_readback_incomplete"
        decision = "convert_readback_to_accepted_feedback" if readback_rows >= 2 else "await_commission_report_or_execution_readback"
        blockers = [] if readback_rows >= 2 else ["execution readback has fewer than two commission-backed rows"]
        packet = write_terminal_packet(
            root=root,
            status=status,
            decision=decision,
            account=context.account,
            port=args.port,
            client_id=selected_client_id,
            contract=contract_payload,
            order_events=order_events,
            execution_readback=execution_readback,
            blockers=blockers,
        )
        print(json.dumps({"ok": readback_rows >= 2, "status": packet["status"], "root": str(root)}))
        return 0 if readback_rows >= 2 else 6
    except Exception as exc:  # noqa: BLE001
        write_terminal_packet(
            root=root,
            status="paper_roundtrip_failed_closed",
            decision="paper_feedback_not_available",
            account=args.account or None,
            port=args.port,
            client_id=selected_client_id,
            contract=contract_payload,
            order_events=order_events,
            execution_readback=None,
            blockers=[f"{type(exc).__name__}: {exc}"],
        )
        print(json.dumps({"ok": False, "status": "paper_roundtrip_failed_closed", "error": str(exc), "root": str(root)}))
        return 3
    finally:
        with contextlib.suppress(Exception):
            if ib.isConnected():
                ib.disconnect()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Paper-account-only IBKR futures roundtrip smoke for accepted execution-feedback capture. "
            "Default mode writes a fail-closed dry-run packet and never places orders."
        )
    )
    parser.add_argument("--root", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=None, help="Paper ports only: 7497 or 4002")
    parser.add_argument("--client-id", type=int, default=37)
    parser.add_argument("--redis-url", default="redis://localhost:6379")
    parser.add_argument("--request-timeout", type=float, default=30.0)
    parser.add_argument("--fill-timeout", type=float, default=20.0)
    parser.add_argument("--post-fill-readback-delay", type=float, default=3.0)
    parser.add_argument("--cancel-wait", type=float, default=2.0)
    parser.add_argument("--connect-preflight", action="store_true")
    parser.add_argument("--execute-paper-roundtrip", action="store_true")
    parser.add_argument("--i-understand-paper-orders", action="store_true")
    parser.add_argument("--account", default="")
    parser.add_argument("--symbol", default="NQ")
    parser.add_argument("--exchange", default="CME")
    parser.add_argument("--currency", default="USD")
    parser.add_argument("--local-symbol", default="")
    parser.add_argument("--last-trade-date-or-contract-month", default="")
    parser.add_argument("--quantity", type=float, default=1.0)
    parser.add_argument("--entry-action", choices=["BUY", "SELL"], default="BUY")
    parser.add_argument("--tif", default="IOC")
    parser.add_argument("--order-ref", default="ict-engine-paper-feedback-smoke")
    parser.add_argument("--execution-filter-time", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(run(parse_args(argv)))


if __name__ == "__main__":
    raise SystemExit(main())
