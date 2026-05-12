# Expanded Parent Regime Source Refresh

Run id: `20260511T022136+0800-codex-expanded-parent-regime-source-refresh`

Purpose: respond to the user correction that recent high-confidence labels were too narrow. This refresh searched papers and GitHub sources again and separates root/display classes from child signatures and implementation methods.

## Source Readback

- Pagan and Sossounov support treating sustained bull and bear markets as a top-level cycle frame rather than promoting every trend signature to a separate root. Source: `https://doi.org/10.1002/jae.664`.
- Lunde and Timmermann add duration-dependence evidence for bull/bear stock-price states, reinforcing that `Bull` and `Bear` should be parent states with their own persistence/duration logic. Source: `https://doi.org/10.1198/073500104000000136`.
- Maheu and McCurdy's component framing shows why bull corrections and bear rallies belong below the parent bull/bear state instead of becoming new active roots. Source: `https://doi.org/10.1080/07350015.2012.680412`.
- "Bull, bear or any other states in US stock market?" is direct prior art for not forcing a two-state taxonomy; extra parent states or residual states can be valid when evidence supports them. Source: `https://doi.org/10.1016/j.econmod.2014.09.020`.
- Recent crypto high-frequency work using regime labels including bull, bear, sideways, and crash reinforces that `Sideways/Consolidation` and `Crisis/Crash` should not be collapsed into ordinary bull/bear states. Source: `https://doi.org/10.1007/s10690-026-09589-z`.
- Hamilton-style Markov switching, `hmmlearn`, change-point detection, `ruptures`, and directional-change indicators are implementation mechanisms for hidden-state probability and boundary timing, not final taxonomy names. Sources: `https://doi.org/10.2307/1912559`, `https://github.com/hmmlearn/hmmlearn`, `https://doi.org/10.1016/j.sigpro.2019.107299`, `https://github.com/deepcharles/ruptures`, `https://doi.org/10.1109/tetci.2017.2775235`.
- GitHub implementation provenance such as `hidden-regime` supports using readable regime outputs like bull/bear/sideways/event-style states, but repo examples do not replace Board A calibration gates. Source: `https://github.com/hidden-regime/hidden-regime`.
- Manipulation needs a separate direct-evidence root or overlay. Candidate mechanisms include pump/dump events, wash trading, spoofing/layering, quote-stuffing-like order-book behavior, and order-lifecycle anomalies. Current public source paths include Bayi-Hu pump/dump event/message labels and Mendeley/NFT wash-trading data. Sources: `https://github.com/Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency`, `https://data.mendeley.com/datasets/4hyxfwzpgg`, `https://github.com/niuniu-zhang/nft_wash_trading`, `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4525036`.

## Corrected Parent/Display Contract

The active Board A emitted parent keys stay compact, but their display names should reflect the user's corrected framing:

| Emitted parent key | Display/root wording | Child evidence allowed | Acceptance note |
|---|---|---|---|
| `Bull` | `BullExpansion` / bull-market expansion | trend expansion, positive persistence, risk-on breadth, cross-provider confirmation | child rules must be reissued through calibrated `Bull` target |
| `Bear` | `BearExpansion` / bear-market expansion | negative persistence, risk-off breadth, bear rallies/corrections as substructure | must stay separate from `Crisis` |
| `Sideways` | `Consolidation` / range / chop | range compression, low directional persistence, balanced volatility | child `RangeConsolidation` packet is context only until the parent gate passes |
| `Crisis` | `Crash` / crisis stress / abnormal stress | tail volatility, liquidity cliff, credit/rates stress, extreme range expansion | prior accepted active root remains only `Crisis` |
| `Manipulation` | manipulation root or overlay | pump/dump, wash trading, spoofing/layering, quote stuffing, direct order lifecycle anomalies | cannot be accepted from OHLCV proxies or unlabeled L2 signatures |
| `UnknownOrMixed` | residual / mixed state | none | residual only; not a release/trade regime |

This means the user-facing main categories can be `BullExpansion`, `BearExpansion`, `Manipulation`, `Consolidation`, and `Crisis/CrashStress`, while the machine contract still emits `Bull`, `Bear`, `Sideways`, `Crisis`, and direct-input-gated `Manipulation`.

## Other Big-Class Watchlist

These are credible large axes from the search, but they are not activated Board A release gates until a downstream consumer contract requests them and they pass unchanged calibration:

- `TransitionRecovery`: recovery / post-stress transition / accumulation-distribution phase.
- `BubbleEuphoria`: extended bull with reflexive speculative excess, especially crypto/equity.
- `LiquidityStress`: cross-root stress overlay, often attached to `Crisis`, `Sideways`, or `Manipulation`.
- `Rotation`: sector/cross-asset/venue rotation; useful context axis, not a single trade root.
- `VolatilityRegime`: low/high volatility state; useful feature axis, not sufficient root semantics by itself.

## Engineering Decision

- Do not count `TrendExpansion`, `RangeConsolidation`, `ThinLiquidity`, `SessionLiquidityCoreViable`, `BullExpansion`, `BearExpansion`, `Consolidation`, `CrisisStress`, `TransitionRecovery`, or L2 signatures as root acceptance by name alone.
- Do allow `BullExpansion`, `BearExpansion`, and `Consolidation` as display/root wording for the active parent keys `Bull`, `Bear`, and `Sideways`.
- Keep `Manipulation` direct-input-gated. OHLCV proxy lanes remain `proxy_only_low_confidence` or `missing_required_inputs`.
- Current accepted active root remains `Crisis` only.
- Missing active roots remain `Bull`, `Bear`, `Sideways`, and `Manipulation`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Fresh calibration rerun: false.
- Trade usable: false.

Next action: run the unchanged `Manipulation` gate on row-level labeled Mendeley wash-trading CSVs without committing raw data, or add explicit negative controls/aligned market features to the Bayi-Hu event windows.
