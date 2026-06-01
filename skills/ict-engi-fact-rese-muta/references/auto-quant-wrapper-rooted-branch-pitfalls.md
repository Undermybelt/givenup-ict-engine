# Auto-Quant wrapper and rooted-branch template pitfalls

Session learning from ict-engine profitability-factor training.

## Problem class
When converting a prior Auto-Quant experiment script into a new rooted profitability-factor lane, wrapper reuse can silently break before factor evaluation if the original script encodes branch parsing assumptions.

## Durable lessons

1. `importlib.util.module_from_spec()` plus dataclasses needs `sys.modules` registration before `exec_module()`.

Correct pattern:

```python
spec = importlib.util.spec_from_file_location('template_module', TEMPLATE)
assert spec is not None and spec.loader is not None
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)
```

Without `sys.modules[spec.name] = runner`, dataclass processing can fail with:

```text
AttributeError: 'NoneType' object has no attribute '__dict__'
```

2. Do not reuse an overlay template unless its branch parser matches the new branch grammar.

A script that indexes `PARTS[7]` / `PARTS[8]` expects at least nine ` -> ` segments. A newly scoped independent root such as:

```text
US -> equity_etf -> QQQ -> 5m -> Trend -> SessionLiquidity -> factor
```

will crash with `IndexError` if the template still expects:

```text
market -> product -> symbol -> timeframe -> main_regime -> sub_regime -> base_profit_factor -> overlay_profit_factor -> probe
```

Prefer either:
- rewrite the template parser to name fields by schema, not fixed offsets; or
- supply the full expected branch shape explicitly and label the final segment as a Gate-1 probe, not hidden promotion.

3. If a `1m` root fails cost density but a `5m` sibling survives cost stress, make the `5m` candidate an independent rooted lane. Do not treat it as an overlay rescuing the failed `1m` branch.

Correct transition:

```text
1m root failed -> stop downstream for 1m
5m sibling positive -> new branch root: market/product/symbol/5m/main_regime/sub_regime/profit_factor
```

4. Keep final verdicts tied to cost-stressed origin lane.
Positive `5m` or `1h` context rows do not open Pre-Bayes/BBN/CatBoost/execution-tree for a failed `1m` origin. Conversely, a valid `5m` branch must be rerun under its own timeframe root before downstream handoff.

5. Patch every imported downstream owner, including nested shared bases.

Wrapper stacks often look like `new_wrapper -> prior_wrapper -> template_wrapper -> shared_base`. It is not enough for the top wrapper and one immediate imported module to show the new `SYMBOL`, `SOURCE`, `ROOT`, `AQ_SYMBOL`, and branch path. If `module.module.base` or another command/logging owner still has the older lane identity, future command construction or terminal readback can silently drift back to the previous branch.

Before running a downstream wrapper, add a focused identity test that walks all command-facing targets and asserts the new lane fields:

```python
for target in (module, module.module, module.module.module, module.module.module.base):
    assert target.SYMBOL == EXPECTED_SYMBOL
    assert target.AQ_SYMBOL == EXPECTED_AQ_SYMBOL
    assert EXPECTED_SOURCE_SLUG in target.SOURCE.as_posix()
    assert EXPECTED_ROOT_SLUG in target.ROOT.as_posix()
```

The NET/5m `soft_transition_stability_v1` repair exposed this exact trap: live argv was later corrected, but the nested shared base initially retained `YF_AI_SECURITY_NET5M_PDA_SEQUENCE_CONSISTENCY_LIGHT_DOWNSTREAM` and the old PDA-sequence source root. Treat a passing top-level identity test as insufficient until nested base identity is covered.

6. For wrapper stacks that import a prior factor wrapper and then monkey-patch
   functions, capture the imported function before assigning the override, and
   run the generic base owner if the prior wrapper's `main()` hardcodes provider
   fields.

The MYM/1m Qstick wrapper initially did:

```python
def strategy_source(...):
    return qstick.strategy_source(...)
qstick.strategy_source = strategy_source
raise SystemExit(qstick.main())
```

That first recursed, and after the recursion fix the prior wrapper's `main()`
still produced MYM branch labels with MNQ provider/path rows. The valid repair
was to save `template_strategy_source = qstick.strategy_source`, set the nested
base provider globals (`ROOT_SYMBOL`, `EXCHANGE`, `CONTRACT_FILE_TOKEN`,
`SOURCE_DATA`, etc.), assign both `qstick.*` and `base.*` material functions, and
call `base.main()`. A focused test must assert both the generated strategy ID
and the provider globals before any AQ run. Treat any run with branch/provider
mismatch as invalid evidence even if AQ exits `0`.

7. When a downstream wrapper generates a full cleaned MTF ladder from a short
   provider window, do not leave undersized sibling intervals visible to
   `analyze` auto-fill.

The M2K/1m RVOL/PDA consistency-floor wrapper generated
`1m/5m/15m/30m/1h/4h/1d`, but the derived `1d` leg had only 9 bars while
analyze feature construction required at least 29 candles. Passing explicit
non-`1d` `--data-ltf/--data-mtf/--data-htf` paths was not enough: because the
paths lived under the same cleaned root, sibling auto-discovery still loaded
`cleaned-1d` and failed before PDA/transition evidence.

Correct repair pattern:

```python
full_root = ROOT / "data/cleaned-mtf"
analyze_root = ROOT / "data/cleaned-mtf-analyze-valid"
manifest = materialize_valid_analyze_mtf_subset(full_root, analyze_root, market)
analyze_ltf = manifest["selected_paths"]["ltf"]  # usually cleaned 1m
analyze_mtf = manifest["selected_paths"]["mtf"]  # valid context frame
analyze_htf = manifest["selected_paths"]["htf"]  # highest valid frame
```

Keep the full ladder for evidence, but physically exclude insufficient legs from
the analyze-visible subset and record them in a manifest such as:

```json
{"insufficient": {"1d": {"bars": 9, "min_required": 29}}}
```

If the wrapper imports and reuses a base module, rebind every derived run-root
path after changing `ROOT`, including secondary roots like `ANALYZE_MTF_ROOT`.
Add a focused identity test that asserts all command-facing paths start with
the wrapper's final `ROOT`; otherwise the run can finish with terminal metrics
in one root while analyze-valid subset artifacts were written into the old base
run root.

8. Do not let a prep packet or test suite point at a child Auto-Quant wrapper
   that exists only as a transient runtime artifact under `/tmp` or
   `/private/tmp`.

The balanced TOMAC `PredicateDensityExpansion` repair exposed this trap: the
prep packet, workdoc, and unittest surfaces all expected
`run_tomac_tod_balanced_structure_ict_predicate_density_expansion_autoquant_loop_v1.py`
and its matching prep wrapper, but those files were missing from the checked-in
repo while a live run root had already generated strategy files from an
in-memory/transient path. The result was a false sense of continuity:

- active runtime could continue from a live `/private/tmp` root
- repo tests failed with `FileNotFoundError`
- future relaunch/takeover work had no durable source file to load

Correct repair pattern:

- check in the child prep wrapper and child Auto-Quant wrapper at the repo path
  named by the prep packet before treating the branch as reusable
- add focused tests that import the exact repo wrapper path, not a copied
  runtime path
- keep the wrapper's `TARGET_FACTOR_ID`, `FAMILY`, env-root keys, and branch
  path aligned with the prep packet and claim surface

Treat any lane where the repo packet points to a nonexistent wrapper as
prep-incomplete even if a live `/tmp` run root already exists.

## Future checklist
- Before running a wrapper script, inspect fixed branch-index use (`PARTS[n]`).
- Confirm `sys.modules` registration for importlib wrappers that load dataclass modules.
- Confirm every imported command-facing owner, including nested `.base` modules, has the new `SYMBOL`, `AQ_SYMBOL`, `SOURCE`, `ROOT`, `STATE`, `CMD`, `CHECKS`, `SUMMARIES`, `MATERIALS`, `MODEL_DIR`, `SCORES`, `BRANCH_PATH`, and `PARTS`.
- If a reused wrapper has its own `main()`, inspect whether it hardcodes provider
  rows, copied filenames, source manifests, summary titles, or decisions; if so,
  route through the generic base owner or write a local `main()` instead of
  calling the prior wrapper's `main()`.
- For generated MTF ladders, count bars per interval before analyze. Keep
  undersized intervals in evidence only; feed analyze from a root that excludes
  them and records `insufficient` explicitly.
- When a prep packet/workdoc/test names a child AQ wrapper, verify the exact
  repo file exists before launch or takeover. A live `/tmp` strategy file is
  not a substitute for the checked-in wrapper source.
- Write `branch_path` with market/product/symbol/timeframe/regime/profit-factor fields first-class.
- Run Gate 1 and cost stress per timeframe root before any downstream admission.
