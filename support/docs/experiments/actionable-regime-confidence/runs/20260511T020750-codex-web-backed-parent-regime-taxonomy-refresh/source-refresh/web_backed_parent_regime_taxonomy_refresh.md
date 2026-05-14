# Web-Backed Parent Regime Taxonomy Refresh

Run id: `20260511T020750+0800-codex-web-backed-parent-regime-taxonomy-refresh`

This source refresh answers the user correction that recent high-confidence labels are child regimes or signatures, not parent/root regimes.

## Source Readback

- Pagan and Sossounov's bull/bear cycle framework supports a top-level split around sustained market advances and declines rather than treating every trend or expansion signature as its own root. Source: `https://doi.org/10.1002/jae.664`.
- Maheu and McCurdy's bull/bear regime-switching work and later component work support separating ordinary bull/bear state from finer components such as corrections, rallies, and volatility substructure. Sources: `https://doi.org/10.1080/07350015.2000.10524851`, `https://doi.org/10.1198/jbes.2009.06134`.
- `hidden-regime` is useful implementation provenance because its public GitHub framing uses `Bull`, `Bear`, `Sideways`, and event/crisis-style regime examples rather than promoting every feature signature to a root. Source: `https://github.com/hidden-regime/hidden-regime`.
- `hmmlearn` remains a suitable implementation primitive for hidden state probabilities, but it does not define the business taxonomy. Source: `https://github.com/hmmlearn/hmmlearn`.
- `ruptures` and change-point detection support segment-boundary evidence. They do not by themselves prove whether a segment is bull, bear, sideways, crisis, or manipulation. Source: `https://github.com/deepcharles/ruptures`.
- Market manipulation literature and datasets support a separate direct-input-gated manipulation class or overlay. `Spoofing`, `layering`, `wash trading`, `pump-and-dump`, and quote-stuffing-like signatures are child mechanisms, not accepted roots without direct labels. Sources: `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4525036`, `https://doi.org/10.3386/w30783`, `https://data.mendeley.com/datasets/4hyxfwzpgg/3`, `https://github.com/niuniu-zhang/nft_wash_trading`.

## Locked Parent Classes

The active Board A parent axis remains:

| Emitted root | User-facing alias | Child / feature evidence allowed | Root gate note |
|---|---|---|---|
| `Bull` | bull expansion / bull market expansion | `BullExpansion`, `TrendExpansion`, positive persistence, risk-on breadth, provider agreement | child evidence must be reissued through a calibrated `Bull` target |
| `Bear` | bear expansion / ordinary bear market | `BearExpansion`, signed negative persistence, risk-off breadth, provider agreement | must stay separate from `Crisis` |
| `Sideways` | consolidation / range / chop | `Consolidation`, `RangeConsolidation`, compression, low directional persistence | child evidence must be reissued through a calibrated `Sideways` target |
| `Crisis` | stress / crash / abnormal market | `CrisisStress`, `ExtremeStress`, tail volatility, liquidity cliff, credit/rates stress | prior accepted active root is still only `Crisis` |
| `Manipulation` | manipulation root or overlay | event-confirmed pump/dump, spoofing/layering, wash trading, direct L2/L3/MBO/order-lifecycle fields | cannot be accepted from OHLCV or unlabeled L2 signatures |
| `UnknownOrMixed` | residual | none | required residual only; not a trade/release regime |

## Other Candidate Big Classes

These should be watched, but not activated as root gates without a downstream consumer contract:

- `TransitionRecovery`: useful as an overlay/phase between roots; not a release root yet.
- `BubbleEuphoria`: possible large parent in longer-horizon equity/crypto work; for current Board A it stays under `Bull` or `UnknownOrMixed` until separately labeled.
- `LiquidityStress`: important risk axis, but usually an overlay on `Crisis`, `Sideways`, or `Manipulation`.
- `SectorRotation` / `CrossAssetRotation`: useful context axis; not currently a Board A root.

## Engineering Decision

- Do not reopen RootTaxonomyV3/V4 as active roots.
- Do not count `BullExpansion`, `BearExpansion`, `Consolidation`, `CrisisStress`, `TransitionRecovery`, or direct L2 signatures as root completion.
- Keep the emitted root set exactly `Bull`, `Bear`, `Sideways`, `Crisis`, direct-input-gated `Manipulation`, plus residual `UnknownOrMixed`.
- Current accepted active root remains `Crisis` only.
- Missing active roots remain `Bull`, `Bear`, `Sideways`, and `Manipulation`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Fresh calibration rerun: false.
- Trade usable: false.

Next action: acquire row-level labeled/direct manipulation data, or a credentialed exact-date direct L2/L3/order-lifecycle export matched to labeled events, before rerunning the unchanged `Manipulation` gate. In parallel planning, the next `Bull`/`Bear`/`Sideways` attempts must use the locked parent target names and keep child signatures as predictors only.
