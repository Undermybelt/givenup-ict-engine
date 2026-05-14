# NDX Source Label Availability Probe v1

Run ID: `20260511T140846+0800-codex-ndx-source-label-availability-probe-v1`

This probe checks whether NQ=F can be unblocked with a Nasdaq-100-grade source-label relation. It treats local ^NDX/NDX price files as price-only evidence, not source labels.

## Result

- Source panel has ^NDX/NDX source labels: `false`.
- Local NDX price-only files found: `3`.
- Local NDX source-label files found: `0`.
- Prior ^IXIC near-proxy rejection found: `true`.
- Accepted rows added: `0`.
- Full objective achieved: `false`.
- Runtime code changed: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.
- Gate result: `ndx_source_label_availability_probe_v1_no_ndx_source_label_ixic_proxy_rejected`.

## Local File Classification

| Path | Exists | Rows | Classification | Columns |
|---|---:|---:|---|---|
| `/private/tmp/ict-crosswalk-tracking-source-attachment-v1/_NDX_1d.csv` | `true` | 2282 | `price_only_not_source_label` | `date,close` |
| `/private/tmp/ict-crosswalk-tracking-probe-20260511T1355/_NDX_1d.csv` | `true` | 2282 | `price_only_not_source_label` | `date,^NDX` |
| `/private/tmp/ict-engine-ibkr-probe/ndx.1d.10y.csv` | `true` | 2513 | `price_only_not_source_label` | `ts,open,high,low,close,volume,wap,count` |

## Decision

- NQ=F remains blocked for accepted source-label crosswalk attachment.
- The available source panel has `^IXIC` but not `^NDX`; prior artifacts rejected `^IXIC` as a near-underlying proxy for `^NDX`, `QQQ`, and `NQ=F`.
- Local ^NDX/NDX files are price bars only, so they cannot be used as MainRegimeV2 source labels.

## Next

- Acquire a Nasdaq-100-grade source-label panel for `^NDX`/`NDX`, or get explicit owner approval that `^IXIC` source labels are acceptable for `NQ=F`.
