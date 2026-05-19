# Factor Hotplug Examples

These examples are optional inputs. A clean checkout does not load them unless
the operator explicitly copies one into a state directory or points
`ICT_ENGINE_FACTOR_HOTPLUG_CONFIG` at it.

## Detector GA Search Bundle

`detector-ga-search-v1.yaml` selects candle-only detector columns that can be
handed to Auto-Quant or another GA/search admission tool as feature names:

- `vi_mitigation_pct`
- `fvg_mitigation_pct`
- `ob_mitigation_pct`
- `liquidity_pool_subtype`
- `sweep_quality`

Example opt-in flow:

```bash
STATE_DIR=/tmp/ict-engine-detector-ga-demo
mkdir -p "$STATE_DIR"
cp support/examples/factor_hotplug/detector-ga-search-v1.yaml \
  "$STATE_DIR/factor_hotplug.yaml"
```

Runtime helpers read that state-dir config and write the sanitized manifest to:

```text
<state-dir>/auto-quant/ga_optimizer/detector_feature_manifest.json
```

The manifest is an admission/search artifact only. It does not promote a
strategy to trading execution; downstream Pre-Bayes, BBN, path-ranker,
cost/slippage, and execution-tree gates still decide whether a candidate can be
used beyond observation.

The same config can be selected without copying by setting:

```bash
ICT_ENGINE_FACTOR_HOTPLUG_CONFIG=support/examples/factor_hotplug/detector-ga-search-v1.yaml
```

Use that environment variable only for an explicit run. Leaving it unset keeps
the zero-config default path unchanged.
