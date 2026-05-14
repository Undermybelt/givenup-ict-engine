# Local Direct And Panel Readback

Run id: `20260511T012720+0800-codex-local-direct-and-panel-readback`

Purpose: re-read local market-data artifacts after the MainRegimeV2 axis restoration and decide whether any newly found local data can close the active Board A blockers.

Active axis:
- `Bull`
- `Bear`
- `Sideways`
- `Crisis`
- direct-input-gated `Manipulation`
- residual `UnknownOrMixed`

Decision:
- Runtime code changed: false.
- Thresholds relaxed: false.
- Fresh calibration rerun: false.
- Long GC/NQ 1m OHLCV data exists and is useful only as future signed-direction/sideways panel input.
- Local Databento/Nautilus MBO files exist, but they are short fixture windows or single-instrument holiday samples without enough cross-period/cross-context calibration support.
- No qualifying direct `Manipulation` calibration input set was found.

