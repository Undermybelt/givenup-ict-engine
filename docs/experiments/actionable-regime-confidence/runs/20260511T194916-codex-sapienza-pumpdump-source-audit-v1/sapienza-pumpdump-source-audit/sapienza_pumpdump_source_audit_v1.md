# Sapienza Pump/Dump Source Audit v1

Source: `https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset`
Source commit: `d71250d4cb055dde2d415c8cba38a0dcd6eb6e16`

## Decision

`sapienza_pumpdump_source_audit_v1=pumpdump_positive_control_candidate_not_spoofing_layering_intake`

- Pump event rows: `1110`.
- Group rows: `13`.
- Ready pump/dump positive/control candidate: `true`.
- Ready spoofing/layering intake source: `false`.
- Full direct Manipulation species coverage: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Feature File Readback

| File | Rows | gt=1 | gt=0 | Symbols | Pump indices | Positive pump indices with gt=0 controls | Date min | Date max |
|---|---:|---:|---:|---:|---:|---:|---|---|
| features_15S.csv.gz | 584104 | 317 | 583787 | 85 | 327 | 317 | 2018-01-02 18:14:30 | 2021-01-19 16:58:15 |
| features_25S.csv.gz | 482157 | 317 | 481840 | 85 | 327 | 317 | 2018-01-02 18:14:35 | 2021-01-19 16:58:20 |
| features_5S.csv.gz | 821307 | 317 | 820990 | 85 | 327 | 317 | 2018-01-02 18:14:40 | 2021-01-19 16:58:25 |

## Board A Impact

This source is better than positive-only event windows for the Telegram pump/dump slice because it exposes source-labeled `gt` rows and same-schema `gt=0` rows around Binance pump events.

It still cannot close the current strict direct `Manipulation` intake blocker because the missing intake contract is for spoofing/layering positives plus matched normal controls, and full direct species coverage still lacks quote stuffing, pinging, bear raid, and painting-tape rows.

Raw source rows remain only under `/tmp`; this repo stores the compact audit and counts.
