# AutoQuant AioDNS Resolver Diagnostic After 032658 v1

Run id: `20260512T033216-codex-autoquant-aiodns-resolver-diagnostic-after-032658-v1`

Gate result: `autoquant_aiodns_resolver_diagnostic_after_032658_v1=threaded_resolver_reaches_binance_aiodns_loopback_fails_prepare_still_no_promotion`

## Scope

This packet follows up the `032658` Auto-Quant bootstrap/prepare readback by isolating whether the Binance failure is a general network problem or the Python async DNS path used by Freqtrade/CCXT. It records diagnostics only. It does not mutate source roots, edit runtime code, accept labels, approve `FLIP` rows, run canonical merge, rerun downstream promotion, or call `update_goal`.

## Command Readback

- `socket.getaddrinfo("api.binance.com", 443)` succeeded and returned `198.18.0.57`.
- `curl -I --max-time 10 https://api.binance.com/api/v3/exchangeInfo` returned HTTP `200`.
- `aiodns.DNSResolver()` reported nameservers `["127.0.0.1"]` and failed with `DNSError(11, "Could not contact DNS servers")`.
- `aiohttp.ClientSession()` with default resolver failed with `ClientConnectorDNSError`.
- `aiohttp.ClientSession()` with `aiohttp.resolver.ThreadedResolver()` reached Binance and returned HTTP `200`.
- Re-running `auto-quant-prepare` with the same isolated output-dir override still exited `1`, with the same aiohttp/aiodns DNS failure while loading Binance markets.

## Diagnosis

The failure is not plain host reachability. The host socket resolver and curl can reach Binance, and aiohttp can reach Binance when forced to use `ThreadedResolver`. The failing path is the default aiohttp/aiodns resolver inside the Auto-Quant/Freqtrade/CCXT environment, which is trying to use loopback DNS at `127.0.0.1` and cannot contact that resolver.

## Decision

- Auto-Quant dependency healthy: `true`.
- Auto-Quant prepare data ready: `false`.
- Root cause narrowed: `aiodns_loopback_resolver_failure`.
- Safe no-code workaround identified: `force_threaded_resolver_or_remove_aiodns_from_prepare_environment`, not implemented in this packet.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Canonical merge allowed: `false`.
- Downstream promotion rerun allowed: `false`.
- Strict full objective achieved: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Next

If the Auto-Quant runtime lane is reopened, test a bounded no-runtime-code workaround that forces aiohttp/Freqtrade/CCXT onto the threaded resolver or removes `aiodns` from the prepare environment inside an isolated `/tmp` state. Do not treat that as Board A acceptance unless source/control gates also unlock and the full downstream chain reruns.
