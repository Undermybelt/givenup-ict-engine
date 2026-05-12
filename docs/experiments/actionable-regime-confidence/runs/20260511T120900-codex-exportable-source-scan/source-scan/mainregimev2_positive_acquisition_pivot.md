# MainRegimeV2 Positive Acquisition Pivot

Run ID: `20260511T120900+0800-codex-exportable-source-scan`

This loop changes direction. Broad public searches for prepackaged `market regime dataset` files are producing mostly negative audits. The useful path is now a source-window label factory:

1. Use primary dated windows where they exist.
2. Keep compact window seeds in repo.
3. Require explicit owner-approved projection before applying a window to another instrument, provider, or timeframe.
4. Run attachability against the missing-slot matrix only after that crosswalk exists.

## Root Shape

- `Bull`: directional expansion root.
- `Bear`: directional contraction root.
- `Sideways`: non-trending/range-bound root, not a Bull/Bear child.
- `Crisis`: stress/dislocation root, allowed to come from official macro or market-crash windows if the crosswalk is explicit.
- `Manipulation`: direct market-integrity event/order-flow/order-lifecycle/social/on-chain class or overlay, not an OHLCV child.
- `UnknownOrMixed`: residual.

## Positive Seeds

`Bull` and `Bear`: Yardeni's S&P 500 bull/bear market tables provide dated S&P 500 windows. The PDF states bull markets are gains between bear markets defined as declines of 20% or more, and it gives dated 2000+ bull/bear windows.

`Crisis`: NBER business-cycle dates provide official US peak-to-trough contraction windows and machine-readable source links. These are macro crisis/stress windows, not direct market drawdown labels.

`Sideways`: Fidelity's range-trading education page is useful only for semantic grounding: markets can be trending or non-trending/sideways. It does not provide dated windows. Sideways therefore needs either a dated source or an owner-approved adjudication protocol.

## Seed Window Table

See `source_window_seed_v1.csv`.

Counts:
- `Bull`: `4` S&P 500 windows.
- `Bear`: `4` S&P 500 windows.
- `Crisis`: `3` NBER contraction windows since 2000.
- `Sideways`: `0` dated windows.
- `Manipulation`: `0` new direct rows in this pivot.

## What This Fixes

This stops treating every loop as a fresh web-search lottery. The next useful loop is not another negative source scan. It should take `source_window_seed_v1.csv`, ask for or apply explicit crosswalk rules, then run attachability:

- SPX/Yardeni source window -> exact `^GSPC` / SPY / ES only if approved.
- NBER crisis window -> US macro stress context only if approved.
- Sideways -> fail closed until a dated source or adjudication protocol exists.
- Manipulation -> continue direct event/order-lifecycle rows, separate from price roots.

## Gate

No 95% confidence gate is claimed by this pivot. It is a positive acquisition contract, not a model acceptance run.

Safety:
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.

## Sources

- Yardeni Research, S&P 500 Bull/Bear tables: `https://yardeni.com/wp-content/uploads/BullBearTables.pdf`
- Yardeni chart page: `https://www.yardeni.com/charts/us-stock-market/stock-market-historical-trends/bull-bear-markets-corrections`
- NBER business-cycle chronology: `https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions`
- Pagan and Sossounov bull/bear framework DOI: `https://doi.org/10.1002/jae.664`
- Fidelity range trading / sideways grounding: `https://www.fidelity.com/learning-center/trading-investing/trading/range-trading`
