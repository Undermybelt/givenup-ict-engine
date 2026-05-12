# Sapienza Pump/Dump Schema Fit v1

Source: `https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset`
Source commit: `d71250d4cb055dde2d415c8cba38a0dcd6eb6e16`

## Decision

`sapienza_pumpdump_schema_fit_v1=scoped_pumpdump_schema_ready_not_strict_manipulation_closure`

- Ready pump/dump row-intake candidate schema: `true`.
- Can materialize scoped pump/dump positive/control package: `true`.
- Ready spoofing/layering intake source: `false`.
- Full direct Manipulation species coverage: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Schema Fit

| Required field | Fit | Source columns | Notes |
|---|---|---|---|
| event_id_or_source_row_id | ready_derived_for_pumpdump | feature_file,pump_index,symbol,date + pump_telegram source row ordinal via nearest event join | All checked positive feature rows join to a Binance pump event within 180 seconds, but the native feature key is a build-local pump_index rather than an immutable upstream event id. |
| timestamp_session_window | ready_for_pumpdump | date,feature_file granularity,pump_telegram date/hour | Feature timestamps are UTC exchange windows; market session is crypto 24x7 and window size is encoded as 5S, 15S, or 25S. |
| symbol_market_venue | ready_for_pumpdump | symbol,pump_telegram exchange,README pair contract | Feature rows carry symbols; source event table and README constrain the checked labeled feature package to Binance SYM/BTC crypto pairs. |
| direct_label_or_species | ready_scoped_to_pumpdump | gt,pump_telegram event context | gt=1/gt=0 supports a direct pump/dump species package only; it is not a spoofing/layering, quote-stuffing, pinging, bear-raid, or painting-tape label source. |
| matched_negative_group_or_controls | ready_scoped_to_pumpdump | feature_file,pump_index,gt | Each positive pump_index has same-schema gt=0 rows in the same feature file and event window group. |
| provenance_hash | ready | source commit plus SHA256 of source CSV/GZ files | The artifact records compact source hashes only; raw rows stay in /tmp. |
| spoofing_layering_positive_rows | missing | N/A | No order-book layering/spoofing lifecycle labels are present in this source package. |
| full_direct_manipulation_species_coverage | missing | N/A | The package covers pump/dump only and does not cover quote stuffing, pinging, bear raid, or painting tape. |

## Feature File Readiness

| File | Rows | gt=1 | gt=0 | Positive pump indices | Positive indices with controls | Event join matches <=180s | Date min | Date max |
|---|---:|---:|---:|---:|---:|---:|---|---|
| features_5S.csv.gz | 821307 | 317 | 820990 | 317 | 317 | 317 | 2018-01-02 18:14:40 | 2021-01-19 16:58:25 |
| features_15S.csv.gz | 584104 | 317 | 583787 | 317 | 317 | 317 | 2018-01-02 18:14:30 | 2021-01-19 16:58:15 |
| features_25S.csv.gz | 482157 | 317 | 481840 | 317 | 317 | 317 | 2018-01-02 18:14:35 | 2021-01-19 16:58:20 |

## Board A Impact

This source can support a bounded direct pump/dump positive/control row-intake package because it exposes event timestamps, symbols, Binance venue context, source `gt` labels, same-schema `gt=0` controls, and provenance hashes.

It does not close the current strict direct `Manipulation` blocker: no spoofing/layering positives are present, and the source does not cover quote stuffing, pinging, bear raid, or painting tape. No raw source rows were committed.
