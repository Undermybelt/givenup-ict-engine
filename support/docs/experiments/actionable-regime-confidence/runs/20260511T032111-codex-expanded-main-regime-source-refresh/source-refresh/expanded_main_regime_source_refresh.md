# Expanded Main-Regime Source Refresh

Run id: `20260511T032111+0800-codex-expanded-main-regime-source-refresh`

Purpose: reopen Board A's root-regime taxonomy after the latest user correction. This is source research only. It does not accept any new 95% root and does not relax any calibration gate.

## Correction

The previous active axis (`Bull`, `Bear`, `Sideways`, `Crisis`, direct-input `Manipulation`) is too coarse for the downstream decision surface. It turns the real market-phase classes into parent aliases and pushes operationally distinct roots into child labels.

The active root taxonomy should be:

| Root key | Operational meaning | Evidence style required before acceptance |
|---|---|---|
| `BullExpansion` | persistent upward / risk-on expansion, not a generic trend feature | positive drift, breadth, persistence, risk-on confirmation, cross-market validation, chronological calibration |
| `BearExpansion` | persistent downside / risk-off expansion, separate from crash/stress | negative drift, drawdown expansion, downside breadth, credit/vol confirmation, chronological calibration |
| `SidewaysConsolidation` | range / chop / compression / failed-break behavior where directional systems should be suppressed or resized | low directional drift, range persistence, compression, false-break or mean-reversion evidence, cross-timeframe validation |
| `Manipulation` | pump/dump, spoofing/layering, wash trading, quote/order-lifecycle engineering, or equivalent direct market-abuse state/overlay | labeled event data, tick/trade tape, L2/L3 order book, order add/cancel/replace lifecycle, or event/social/on-chain evidence; OHLCV proxies fail closed |
| `CrisisStress` | crash, high-volatility stress, covariance/correlation break, liquidity cliff | tail/drawdown/vol/covariance/liquidity stress evidence; not ordinary `BearExpansion` |
| `UnknownOrMixed` | low-confidence, overlapping, or mixed evidence | residual abstain bucket only |

Candidate add-on roots that deserve schema preflight before activation:

- `TransitionRecovery` / `AccumulationDistribution`
- `BubbleEuphoria` / blow-off
- `VolatilityDislocation`
- `LiquidityDrought`
- `CrossAssetRotation`

These are not accepted or required completion roots yet. They become active only if the preflight proves separability, support, and a downstream action difference.

## Source Takeaways

- Classical bull/bear market-dating work treats bull and bear as primary market states, so `BullExpansion` and `BearExpansion` should not be demoted to generic trend subfeatures.
- HMM/Markov-switching research supports persistent hidden-state probabilities and label relabeling, but the HMM state is evidence, not the root label itself.
- Change-point methods and directional-change/event-based methods are boundary and timing evidence. They do not by themselves define the root.
- Sideways/consolidation belongs as an operational root when the allowed action differs from directional expansion.
- Manipulation is a different behavioral mechanism from expansion or consolidation. It must remain direct-input-gated because OHLCV liquidity proxies cannot prove market abuse.
- Crisis/stress remains a root because volatility/covariance/liquidity breaks can dominate sizing and abstain decisions regardless of signed direction.

## Source Inventory

Market-state and regime-switching:

- Pagan and Sossounov, "A Simple Framework for Analysing Bull and Bear Markets": `https://ideas.repec.org/a/jae/japmet/v18y2003i1p23-46.html`
- Maheu and McCurdy, "Identifying Bull and Bear Markets in Stock Returns": `https://doi.org/10.2307/1392140`
- Guidolin and Timmermann, "Economic Implications of Bull and Bear Regimes in UK Stock and Bond Returns": `https://doi.org/10.1111/j.1468-0297.2004.00962.x`
- Hamilton 1989 Markov-switching foundation: `https://doi.org/10.2307/1912559`
- Ang and Bekaert 2002 regime-switching allocation: `https://doi.org/10.1093/rfs/15.4.1137`
- Oelschlager and Adam, "Detecting bearish and bullish markets in financial time series using hierarchical hidden Markov models": `https://arxiv.org/abs/2007.14874`
- `hmmlearn`: `https://github.com/hmmlearn/hmmlearn`
- `hidden-regime`: `https://github.com/hidden-regime/hidden-regime`

Segmentation, sideways, and boundaries:

- Truong, Oudre, and Vayatis 2020 change-point review: `https://doi.org/10.1016/j.sigpro.2019.107299`
- `ruptures`: `https://github.com/deepcharles/ruptures`
- Directional-change regime strategy: `https://arxiv.org/abs/2309.15383`

Manipulation and direct market-abuse evidence:

- Xu and Livshits, "The Anatomy of a Cryptocurrency Pump-and-Dump Scheme": `https://arxiv.org/abs/1811.10109`
- Kamps and Kleinberg, "To the moon: defining and detecting cryptocurrency pump-and-dumps": `https://doi.org/10.1186/s40163-018-0093-5`
- `Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency`: `https://github.com/Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency`
- `SystemsLab-Sapienza/pump-and-dump-dataset`: `https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset`
- Do and Putnins, "Detecting Layering and Spoofing in Markets": `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4525036`
- Montgomery, "Spoofing, Market Manipulation, and the Limit-Order Book": `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2780579`
- "Learning the Spoofability of Limit Order Books With Interpretable Probabilistic Neural Networks": `https://arxiv.org/abs/2504.15908`

## Board Impact

- The current `Bull` / `Bear` / `Sideways` gates become coarse-alias negative evidence, not the final active taxonomy.
- Existing accepted subtype packets remain `sub_regime_evidence_only`; they can feed the root classifier but cannot complete roots by themselves.
- Prior accepted `Crisis` evidence is preserved only as `CrisisStress` provenance until the new expanded-root contract is reissued explicitly.
- `Manipulation` stays direct-input-gated; Bayi-Hu/SystemLab/Mendeley negative evidence remains useful but does not lower the gate.

## Next Action

Materialize an expanded-root target schema and crosswalk, then rerun unchanged chronological 95% gates for `BullExpansion`, `BearExpansion`, `SidewaysConsolidation`, `CrisisStress`, and direct-input-gated `Manipulation`. Run add-on root preflight separately before expanding the completion contract.

Gate result: `blocked_taxonomy_refresh_only_no_new_95`.

Thresholds relaxed: false. Runtime code changed: false. Fresh calibration rerun: false. Trade usable: false.
