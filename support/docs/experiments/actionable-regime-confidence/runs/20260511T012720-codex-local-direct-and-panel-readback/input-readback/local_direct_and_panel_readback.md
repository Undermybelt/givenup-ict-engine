# Local Direct And Panel Readback

Run id: `20260511T012720+0800-codex-local-direct-and-panel-readback`

## Result

- Active axis: MainRegimeV2, not RootTaxonomyV3.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Fresh calibration rerun: false.
- Prior accepted root remains `Crisis` only.
- Missing roots remain `Bull`, `Bear`, `Sideways`, and direct-input-gated `Manipulation`.

## Local Panel Found

`/Users/thrill3r/Downloads/Tomac/gc future 2021-2025` contains long Databento-derived GC/NQ 1m OHLCV material:

| File | Evidence | Use |
|---|---:|---|
| `gc_201101_202604.csv` | 5,327,113 lines including header, GC continuous 1m OHLCV from 2011-01-02 through 2026-04-14 | candidate future panel for signed `Bull` / `Bear` and `Sideways` features |
| `databento.rar:nq_201101_202604.csv` | 5,164,048 lines including header, NQ continuous 1m OHLCV | candidate future panel for signed `Bull` / `Bear` and `Sideways` features |
| `glbx-mdp3-20210106-20260105.ohlcv-1m.csv` | 5,333,533 lines including header, Databento `GLBX.MDP3`, schema `ohlcv-1m`, symbol request `GC.FUT` | candidate future panel only |

This is not direct `Manipulation` evidence because it has no tick/order-flow/L2/L3/order-lifecycle fields.

## Direct Data Readback

Local Databento/Nautilus MBO files exist:

| File | Directness | Support State |
|---|---|---|
| `esh4-glbx-mdp3-20231224.mbo.dbn.zst` | GLBX.MDP3 market-by-order / L3 sample | single-instrument short-window support insufficient |
| `esh4-glbx-mdp3-20231225.mbo.dbn.zst` | GLBX.MDP3 market-by-order / L3 sample | single-instrument holiday sample support insufficient |
| `orderbooks_mbo_2024-05-08T00-00-00_2024-05-08T00-00-02.dbn.zst` | GLBX.MDP3 market-by-order / L3 sample | two-second fixture window support insufficient |

`zstdcat` confirms DBN payloads with `GLBX.MDP3` and ESH4/ESM4 strings. A transient `uv --with databento` decode attempt failed on a PyPI TLS handshake, so this run did not produce row-level DBN dataframes. That does not change the gate decision: the local MBO candidates are too narrow for a 95% manipulation calibration gate unless broader historical labels and cross-context coverage are added.

## Decision

No qualifying direct `Manipulation` calibration input set was found. Do not rerun a manipulation 95% gate from these inputs.

The GC/NQ OHLCV archive should be treated as a useful future panel for `Bull`, `Bear`, and `Sideways` feature work, not as a manipulation proxy and not as acceptance evidence by itself.

