# PumpOlymp Source Audit

Run ID: `20260511T110514+0800-codex-pumpolymp-source-audit`

## Scope

This audit checks whether the public `hnghiem-nlp/Pump_and_Dump_Crypto` repo materializes direct pump/dump event labels and same-venue negative controls for Board A `Manipulation` accounting.

## Readback

- Published blob count: `37`.
- Published data-like files: `0`.
- References external `allPumps_20200201.json`: `true`.
- Event fields seen in notebooks: `channelLink`, `channelTitle`, `currency`, `duration`, `exchange`, `priceBeforePump`, `signalTime`.
- Materialized positive event JSON in public repo: `false`.
- Materialized same-asset/venue negative controls in public repo: `false`.

## Notebook Scan

- `Final_Analysis/Final_Mod_0_Format_Pump_Data.ipynb`: hit_count `15`, error `None`
- `General_Analysis/Mod_0_All_Historical_Pump_Analysis.ipynb`: hit_count `15`, error `None`
- `General_Analysis/Mod_1_Acquire_Data_for_Pumps.ipynb`: hit_count `6`, error `None`
- `Before_Pump_Analysis/Mod_1_Download_pumped_coin_historical_data.ipynb`: hit_count `3`, error `None`

## Decision

- Accepted parent-root slots added: `0`.
- Accepted direct `Manipulation` rows added: `0`.
- Gate result: `blocked_pumpolymp_repo_code_only_event_json_not_published`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.

The repository is a useful acquisition lead, but it publishes notebooks/code rather than the replayable event-label table required by Board A. Do not count it unless the PumpOlymp export is supplied or independently reachable with row-level timestamps and controls.
