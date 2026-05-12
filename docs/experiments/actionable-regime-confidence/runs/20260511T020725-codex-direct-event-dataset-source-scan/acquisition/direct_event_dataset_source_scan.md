# Direct Event Dataset Source Scan

Run id: `20260511T020725+0800-codex-direct-event-dataset-source-scan`

## Purpose

Find directly downloadable row-level event/social/on-chain or direct L2/L3/order-lifecycle datasets that could support the active MainRegimeV2 direct-input-gated `Manipulation` root. This is an acquisition scan only; it does not run a calibration gate.

## Sources Checked

| Source | Local result | Gate usability |
|---|---|---|
| `Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency` (`https://github.com/Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency`) | Directly downloadable cleaned P&D event log found. Probe counted 1,335 event rows across 14 exchanges and 277 coins; Binance contributed 1,003 events. `label.txt` has 5,146 manual message labels and `pred_pump_message.csv` has 36,696 positive pump-message rows. | strongest new candidate; still needs unchanged chronological `Manipulation` gate with explicit negatives and/or aligned market features |
| `SystemsLab-Sapienza/gme-pump-xrp-telegram` (`https://github.com/SystemsLab-Sapienza/gme-pump-xrp-telegram`) | Raw Telegram group corpus found with 120 `messages*.html` files plus media. | context only until a structured event label table is extracted |
| `cakcora/chartalist` (`https://github.com/cakcora/chartalist`) | README and dataloader list IDEX/EtherDelta anomaly datasets, but direct CSV URL probes returned the website HTML shell instead of CSV row data. Dataloader metadata lists transaction columns, not an explicit manipulation label. | not gate-ready |
| `Jananigaekwad/Group-3-Wash-Trading-Case-Study-for-ERC20-Token` (`https://github.com/Jananigaekwad/Group-3-Wash-Trading-Case-Study-for-ERC20-Token`) | Direct normalized ERC20 transaction CSV found, but sampled columns did not include an explicit wash-trade label and the README frames unsupervised anomaly detection. | not gate-ready |
| `dianxiang-sun/rug_pull_dataset` (`https://github.com/dianxiang-sun/rug_pull_dataset`) | Direct CSV incident dataset found; README documents 2,391 validated DeFi rug-pull incidents from 2020-2023. | adjacent on-chain fraud context only; not an exchange/order-flow manipulation event ledger for this gate |

## Result

- Strongest new acquisition path: `Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency`.
- Directly downloadable candidate source found: yes.
- Accepted 95 `Manipulation`: false.
- Fresh calibration rerun: false.
- Runtime code changed: false.
- Thresholds relaxed: false.

This improves the next action from "find any accessible source" to "run an unchanged event/social gate on the Bayi-Hu source." It does not complete the board because the source has not yet been transformed into a chronological calibration/test evidence packet with explicit negative controls or aligned market features.

## Next

Create a bounded `Manipulation` event/social gate from the Bayi-Hu cleaned P&D event log and message-label files. The gate must use chronological splits, must not relax thresholds, and must keep `Manipulation` fail-closed unless held-out evidence reaches the required 95% calibrated standard.

