# Provider AQ Runtime Settled Readback v1

Run id: `20260512T103512+0800-codex-provider-aq-runtime-settled-readback-v1`

Gate result: `provider_aq_runtime_settled_readback_v1=latest_unregistered_provider_aq_roots_settled_no_board_a_promotion`

## Scope

This packet registers settled readback for the latest provider/AQ runtime roots that were present on disk but not yet recorded in the Board A markdown after the `102828` IBKR and `103057` structural-feedback sections.

It does not edit the Current Cursor, select `HTF`/`MTF`/`LTF`, approve source/control evidence, mutate canonical intake, promote Auto-Quant, BBN/CatBoost/path-ranking, structural feedback, or execution-tree output, make a trade claim, mark the objective complete, or call `update_goal`.

## Readback

- `102500` Yahoo crypto momentum AQ: fetch/prepare/run exits were `0`. `ProviderCryptoMomentumStateV1` produced `295` trades, `-18.73%` profit, Sharpe `-1.0287`, PF `0.7350`; `ProviderCryptoPullbackRevertV1` produced `109` trades, `-7.08%` profit, Sharpe `-0.4663`, PF `0.6898`.
- `102601` NQ canary engine debug: limit-order run exited `0` with `4` succeeded strategies and `0` trades; first market-order retry failed on `entry_pricing.price_side`; repaired `price_side=other` retry exited `0`, again `4` succeeded strategies and `0` trades.
- `102611` YF NQ signal-plumbing diagnostic: initial and first market retry failed, probe exited `0`, final `price_side=other` retry exited `0`; `ProviderYfNqSignalPlumbingDiagnostic` produced `0` trades.
- `102728` Yahoo NQ dense AQ: TOMAC exited `0`, `3` succeeded strategies, `0` failed, and `0` trades.
- `102812` YF NQ trendpulse tick-precision capture: capture/inspect exits were `0`; `ProviderNqSampledPulse` produced `18` trades, `+0.97%` profit, Sharpe `0.1898`, PF `5.3246`; `ProviderNqTrendPulse` produced `896` trades, `-38.10%` profit, Sharpe `-3.3038`, PF `0.5912`.
- `102828` Board A provider NQ entry wire: probes and TOMAC runs exited `0`, but `ProviderNqEntryWireCanary` and `ProviderNqForcedEntryCanary` both produced `0` trades.
- `102928` BTC tickfix factor: report gate is `provider_btc_tickfix_factor_v1=nonzero_provider_btc_factor_trades_incubation_only_no_promotion`. `ProviderBtcMomentumCross` produced `9` trades, `+2.14%` profit, Sharpe `1.2260`, PF `1.7770`; `ProviderBtcMomentumPulse` produced `57` trades, `-3.61%`; `ProviderBtcTrendPullback` produced `16` trades, `-5.21%`.
- `103010` BTC always-entry canary: final `price_side=other` retry exited `0` and produced `81` BTC/USDT trades, `+4.41%` profit, Sharpe `2.5645`, PF `1.1993`; this is forced always-entry plumbing evidence only, not a strategy acceptance packet.
- `103114` BTC signal-consumption diagnostic: probe exited `0` with `985` rows, `81` entry signals, and `80` exit signals; TOMAC exited `1` on `ConfigurationError: Market entry orders require entry_pricing.price_side = "other"`.

## Decision

- Count these roots once as settled provider/AQ runtime evidence.
- Nonzero trades exist in `102500`, `102812`, `102928`, and `103010`, but none is Board A promotion evidence:
  - `102500` is unprofitable.
  - `102812` has one low-trade weak profitable sample and one high-trade loss.
  - `102928` has one profitable BTC branch below maturity and two losing branches.
  - `103010` is a forced always-entry canary.
- Accepted rows added: `0`.
- Mature rooted branch observations added: `0`.
- Source/control evidence acquired: `false`.
- Explicit selected-history: `false`.
- Canonical merge: `false`.
- Selected-data AutoQuant promotion: `false`.
- Downstream Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion: `false`.
- Strict full objective: `false`.
- Trade usable: `false`.
- Promotion allowed: `false`.
- `update_goal=false`.

## Next

Do not repeat these same zero-trade, canary, forced-entry, or non-mature provider/AQ shapes. The next useful slice remains explicit selected-history approval, real R6/R5/R3 source/control unlock, or a materially different provider-owned branch-specific strategy that creates nonzero mature rooted observations and can then be rerun through Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.

