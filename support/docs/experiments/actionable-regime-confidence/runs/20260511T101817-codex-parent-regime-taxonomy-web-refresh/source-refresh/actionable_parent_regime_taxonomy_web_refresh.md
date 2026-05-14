# Actionable Parent Regime Taxonomy Web Refresh

Loop id: `20260511T101817+0800-codex-parent-regime-taxonomy-web-refresh`

Purpose: refresh the parent regime taxonomy after the latest user correction that earlier labels were still child/sub-regimes and that the parent layer should include bull expansion, bear expansion, manipulation, consolidation, and possibly other large classes.

## Decision

Active candidate taxonomy is reopened as `ActionableRegimeRootV7`.

Mandatory parent roots:
- `BullExpansion`: directional upside expansion / markup regime.
- `BearExpansion`: directional downside expansion / markdown regime.
- `ConsolidationBalance`: range, balance, compression, accumulation/distribution, or non-directional regime where continuation logic should not be assumed.
- `CrisisDislocation`: high-volatility, jump, liquidity, correlation, or structural-break stress that should not be collapsed into ordinary bearish expansion.
- `ManipulationIntegrityEvent`: top-level market-integrity event class for pump-and-dump, spoofing/layering, wash trading, self-trade, and related direct manipulation evidence.

Watchlist root:
- `TransitionRotation`: accumulation/distribution, macro rotation, or pre-breakout/reversal transition. Promote only if source labels and downstream action differences cannot be represented by `ConsolidationBalance` or `CrisisDislocation`.

Residual: `UnknownOrMixed`.

## Source Rationale

Bull/bear cycle work, including Pagan and Sossounov's bull/bear framework, supports directional market-cycle roots but does not by itself distinguish expansion from a weak non-expansion bull/bear label: `https://ideas.repec.org/a/jae/japmet/v18y2003i1p23-46.html`.

HMM/Markov-switching tooling such as `hmmlearn` is useful for posterior probabilities, persistence, entropy, and walk-forward relabeling, but model state ids remain method outputs, not independent parent labels: `https://github.com/hmmlearn/hmmlearn`.

Change-point tooling such as `ruptures` supports boundary timing and structural-break detection, which is useful for `CrisisDislocation` and transition evidence. It still needs economic labeling and calibration before becoming a regime root packet: `https://github.com/deepcharles/ruptures`.

Jump-model tooling supports separating discontinuous stress/jump behavior from ordinary trend states. That argues for keeping `CrisisDislocation` as a parent candidate rather than forcing all downside stress into `BearExpansion`: `https://github.com/Yizhan-Oliver-Shu/jump-models`.

Manipulation evidence is a different evidence family from OHLCV price-root regimes. Crypto pump-and-dump literature and datasets expose event-centered rows such as symbol, event time, exchange, and group, so `ManipulationIntegrityEvent` should be a parent gating class but must still require direct positive/negative rows: `https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset`, `https://link.springer.com/article/10.1186/s40163-018-0093-5`.

Regulator/SRO manipulation surfaces such as FINRA's potential manipulation report support treating manipulation as market-integrity evidence, but report/catalog pages are not row-level labels by themselves: `https://www.finra.org/compliance-tools/report-center/cross-market-equities-supervision/potential-manipulation-report`.

The `Persdre/EX-Graph` Dune wash-trade CSV is useful as provenance for direct wash-trade positives, but the sampled CSV has `nft_name`, `token_id`, `tx_hash`, `from_addr`, and `to_addr` without timestamp or negative controls, so it remains a candidate until a formal gate is run: `https://github.com/Persdre/EX-Graph`.

## Compatibility Crosswalk

Old `MainRegimeV2` labels are now compatibility inputs, not final roots:
- `Bull` can feed `BullExpansion` only after expansion/trend participation validation.
- `Bear` can feed `BearExpansion` only after expansion/trend participation validation.
- `Sideways` can feed `ConsolidationBalance`.
- `Crisis` can feed `CrisisDislocation`.
- Prior `Manipulation` overlays can feed `ManipulationIntegrityEvent` only with direct timestamped rows/windows and negative controls.

## Gate Result

- Accepted 95 roots added: `0`.
- Accepted direct manipulation rows added: `0`.
- Runtime code changed: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.
- Gate result: `taxonomy_reopened_to_ActionableRegimeRootV7_web_sources_only_no_new_95`.

Next action: materialize an `ActionableRegimeRootV7` schema/crosswalk and then acquire/calibrate source labels separately for `BullExpansion`, `BearExpansion`, `ConsolidationBalance`, `CrisisDislocation`, and direct `ManipulationIntegrityEvent`.
