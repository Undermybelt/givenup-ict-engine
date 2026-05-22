# ICT Engine Consumer Quickstart

This is the public, zero-config entry path. Use `/tmp/...` for trial state so
the repo stays clean. Demo output is evidence that the loop is inspectable; it
is not trade-readiness evidence.

## Flow 1: Demo Loop

Use this when you want a fast first run with bundled candles.

```bash
cargo run --quiet -- provider-status --compact
cargo run --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --human
cargo run --quiet -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-first-run --human
cargo run --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --refresh --agent
cargo run --quiet -- pre-bayes-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --refresh --output-format json
cargo run --quiet -- policy-training-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --output-format agent
```

Equivalent repeatable smoke gate:

```bash
support/scripts/smoke_acceptance.sh
```

Expected result: provider readiness is visible, `analyze --demo` writes workflow
state, `workflow-status --agent` exposes the current regime posterior and next
step, `pre-bayes-status` exposes evidence quality, and `policy-training-status`
keeps training/admission pending unless real outcome history exists.

## Flow 2: Public Data Readiness

Use this before a live/public-data run. The public live path depends on the
current network and provider response, so check provider readiness first.

```bash
cargo run --quiet -- provider-status --domain live_runtime --agent
cargo run --quiet -- provider-status --domain market_data --agent
```

For built-in futures keys, the live command shape is:

```bash
cargo run --quiet -- analyze-live --symbol NQ --state-dir /tmp/ict-engine-live-nq --human
```

If this fails or stalls, do not treat it as strategy evidence. Record the exact
provider error and return to `provider-status --domain live_runtime --agent`.

## Flow 3: Local Cleaned Data

Use this when you already have cleaned candle JSON files. Keep state outside the
repo unless you intentionally want persistent learning history.

```bash
cargo run --quiet -- analyze \
  --symbol MY_SYMBOL \
  --data-htf /tmp/my-data/1d.json \
  --data-mtf /tmp/my-data/1h.json \
  --data-ltf /tmp/my-data/15m.json \
  --state-dir /tmp/ict-engine-local-data \
  --human
```

Then inspect the generated state:

```bash
cargo run --quiet -- workflow-status --symbol MY_SYMBOL --state-dir /tmp/ict-engine-local-data --refresh --agent
cargo run --quiet -- pre-bayes-status --symbol MY_SYMBOL --state-dir /tmp/ict-engine-local-data --refresh --output-format json
```

## Reading The Result

- `observe` means the system has evidence to inspect, not permission to trade.
- Training or ranker readiness must come from `policy-training-status`.
- Public output must not require private profiles, private datasets, API keys, or
  maintainer-local paths.
- Agent code should read structured fields, not display strings.
