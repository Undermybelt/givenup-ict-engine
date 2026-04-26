# IBKR live data bridge

> **⚠️ IBKR is optional and disabled by default.**
>
> ict-engine works completely without IBKR. All free providers (Yahoo
> Finance, Kraken, Bybit, Binance) plus paid optional ones (Polygon, NSE)
> function on a fresh clone with zero IBKR setup.
>
> Enable IBKR only if you:
> 1. Have an IBKR account
> 2. Are running IB Gateway or TWS locally
> 3. Want real-time or historical data from IBKR feeds
>
> When enabled, all IBKR I/O is **localhost-only**. No data, credentials,
> or telemetry leaves your machine. See bilingual disclaimer below.

## What this is

Auto-Quant strategies and ict-engine research scripts both need IBKR market
data, but TWS / IB Gateway is single-login-per-account. The bridge solves
this by being the **only** persistent IBKR client in the system. It
publishes everything it sees to local Redis Streams, and any number of
downstream consumers read from Redis instead of opening their own IBKR
connections.

```
TWS / IB Gateway (single login session)
        ↑ socket, clientId=20
        │
   ibkr-bridge.py  (this directory)
        ↓ XADD ticks/bars
   Redis (localhost:6379)
        │
        ↓ XREAD / HGETALL
  Auto-Quant strategy        ict-engine research script
  consumer.IbkrConsumer      consumer.IbkrConsumer
```

Same Redis also coordinates account-level rate limiting across processes,
so `bridge.py` and `fetch_external.py ibkr-historical` cannot accidentally
exceed IBKR's 6 s/contract or 60-distinct/10-min budgets when run together.

## Layout

| File | Role |
| --- | --- |
| `setup.py` | First-run consent + Redis ping + Gateway ping. Run **once**. |
| `consent.py` | `require_ibkr_enabled()` gate used by every IBKR-touching entry point. |
| `rate_limiter.py` | Redis-backed adaptive token bucket / sliding window. |
| `account_prober.py` | One-shot static account identification (`reqManagedAccts`). |
| `bridge.py` | Persistent producer. Connects, subscribes, publishes. |
| `consumer.py` | Read-only helper imported by Auto-Quant + ict-engine. |
| `example_config.yaml` | Empty default, with commented subscription examples. |

User-local files (gitignored, **never enter the repo**):

| Path | Contents |
| --- | --- |
| `~/.ict-engine/ibkr_consent.json` | Your opt-in record. Delete to revoke. |
| `~/.ict-engine/ibkr_capabilities.json` | Adaptive limits learned from real account behaviour. |

## Quick start

### Prerequisites

```bash
# 1. Local Redis daemon (used for fan-out + cross-process rate-limit coord)
brew install redis
brew services start redis

# 2. IB Gateway or TWS, logged in to a paper account.
#    https://www.interactivebrokers.com/en/trading/ib-gateway-stable.php
#    Settings → API → Settings:
#       [✓] Enable ActiveX and Socket Clients
#       [✓] Allow connections from localhost only
#       [✓] Read-only API   ← strongly recommended
#       Socket port = 7497  (paper) or 7496 (live)

# 3. Python deps (already installed if you use Auto-Quant's venv via uv):
#    ib_async>=2.0
#    redis>=5.0
#    pyyaml
```

### One-time setup

```bash
cd ~/Auto-Quant
.venv/bin/python -m scripts.ibkr_bridge.setup --enable
```

You will see the bilingual disclaimer below, be asked to opt in, and the
script will check Redis + Gateway reachability and (if Gateway is up) run
the one-shot account probe to populate `ibkr_capabilities.json`.

To re-print current state at any time:

```bash
.venv/bin/python -m scripts.ibkr_bridge.setup status
```

To revoke and clean local state:

```bash
.venv/bin/python -m scripts.ibkr_bridge.setup revoke --clean-redis
```

### Run the bridge

```bash
cp scripts/ibkr_bridge/example_config.yaml scripts/ibkr_bridge/my_config.yaml
# Edit my_config.yaml — uncomment a few subscriptions
.venv/bin/python -m scripts.ibkr_bridge.bridge --config scripts/ibkr_bridge/my_config.yaml
```

### Consume from a strategy / notebook

```python
from ibkr_bridge.consumer import IbkrConsumer

c = IbkrConsumer()  # defaults to redis://localhost:6379

# Snapshot (last known values)
print(c.snapshot("AAPL"))
# {'ts': 1745683123.456, 'bid': 187.42, 'ask': 187.45, 'last': 187.43, ...}

# Recent bars as DataFrame
bars = c.bars("AAPL", bar_size="5sec", lookback=300)
print(bars.tail())

# Live tail (async)
async for entry in c.stream_bars(["AAPL", "SPY"]):
    print(entry["symbol"], entry["close"])
```

The consumer **does not** require IBKR consent — it only reads Redis.

## Rate-limit policy (canonical IBKR)

| Rule | Default | Adaptation |
| --- | --- | --- |
| Same `(contract, bar_size, what_to_show)` | ≥ 6.5 s | bumps to 8 / 10 / … on each `162` |
| Distinct historical contracts in 10 min | 55 (cap 60 with 5 buffer) | -5 after 3× `162` in 24 h |
| Simultaneous historical reqs | 40 (cap 50) | semaphore |
| Streaming market-data lines | 80 (probed up to ceiling) | hard ceiling lowered on `354/322/1100` |
| Snapshot per contract | ≥ 11 s | per-contract token bucket |
| Outbound msg/sec to TWS | 45 (limit 50) | drops to 30 on connection-reset |

Capabilities live in `~/.ict-engine/ibkr_capabilities.json`. Inspect via:

```bash
.venv/bin/python -m scripts.ibkr_bridge.rate_limiter
```

## Privacy & connectivity disclaimer (verbatim)

```
IBKR live data — privacy & connectivity notice
──────────────────────────────────────────────
This feature reads real-time data from your *locally running* IB Gateway
or TWS application. Everything stays on this machine.

What this code DOES:
  • Connect to localhost:7497 (paper) or :7496 (live) — your local IB Gateway
  • Subscribe to instruments listed in ibkr_bridge/<your>_config.yaml
  • Write market data to your local Redis (localhost:6379)
  • Honor IBKR's pacing rules (6 s/contract historical, 100 streaming lines)
  • Learn your account capabilities passively from observed errors;
    no proactive probing of your data quota at startup

What this code DOES NOT:
  • Send your IBKR credentials anywhere — they stay in IB Gateway / TWS
  • Contact ict-engine.com, OpenAlice, or any third-party server
  • Place orders, close positions, or modify your IBKR account state
  • Collect telemetry, analytics, or crash reports

Auditable source:  scripts/ibkr_bridge/{bridge,consumer,rate_limiter}.py
Capabilities file: ~/.ict-engine/ibkr_capabilities.json (gitignored, local)
Revoke any time:   python scripts/ibkr_bridge/setup.py --revoke

═════════════════════════════════════════════════════════════════════
中文版
═════════════════════════════════════════════════════════════════════

IBKR 实时数据 — 隐私与连接说明
──────────────────────────────────
本功能从你**本机运行**的 IB Gateway 或 TWS 读取实时数据。所有内容均不离开本机。

本代码会做：
  • 连接 localhost:7497 (paper) 或 :7496 (live) — 你本地的 IB Gateway
  • 订阅 ibkr_bridge/<你的>_config.yaml 列出的合约
  • 写入你本地的 Redis (localhost:6379)
  • 遵守 IBKR 流控规则 (6 秒/合约 历史限制，100 条流式数据线)
  • 通过观察实际错误被动学习账户能力；启动时不做主动配额探测

本代码绝不会：
  • 把你的 IBKR 凭据传到任何地方 — 凭据一直在 IB Gateway / TWS 里
  • 联系 ict-engine.com、OpenAlice 或任何第三方服务
  • 下单、平仓或修改你的 IBKR 账户状态
  • 收集遥测、分析或崩溃报告

源代码可审：    scripts/ibkr_bridge/{bridge,consumer,rate_limiter}.py
能力文件：      ~/.ict-engine/ibkr_capabilities.json (gitignored, 本地)
随时撤回同意：  python scripts/ibkr_bridge/setup.py --revoke
```

## Troubleshooting

**`Cannot reach IBKR Gateway at 127.0.0.1:7497`**
Open Gateway, verify "Connected" status, check Settings → API → Settings →
Socket port matches. Make sure no firewall blocks loopback.

**`error 162` (pacing violation)**
Already self-correcting. After 3 within 24 h the limiter will tighten the
historical window cap. Check `rate_limiter.py` diagnostic to see current
state.

**`error 354` (no live subscription)**
Your account doesn't have the right market-data subscription for that
instrument. The bridge keeps writing the delayed feed (`market_data_type=3`)
and notes the symbol in `feeds_observed_delayed`.

**Bridge crash, consumers see stale data**
The bridge periodically writes its state to `ibkr:bridge:status`. Consumers
should check `IbkrConsumer().bridge_status()["state"]` and fall back to a
non-IBKR provider when state is `absent`, `disconnected`, or older than 60s.

**Want to re-probe the account**
`rm ~/.ict-engine/ibkr_capabilities.json` and either restart the bridge or
re-run `python -m scripts.ibkr_bridge.setup enable`.

## Limitations (v0)

- macOS-tested only; Linux should work but unverified.
- Single Gateway / single account per bridge instance. Multi-account
  scenarios are gracefully detected (see `n_subaccounts` in capabilities)
  but only the first account is observed for now.
- No SQLite spool: if Redis crashes mid-tick the unsent burst is dropped.
  v1 may add durable spool.
- `tick-by-tick` feed is intentionally disabled (IBKR caps it at 5
  simultaneous globally — too tight to share with other clientIds).
