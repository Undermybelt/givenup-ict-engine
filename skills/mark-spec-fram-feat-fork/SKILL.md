---
name: mark-spec-fram-feat-fork
description: Add and validate market-specific frame-feature label forks in ict-engine when raw pre-Bayes labels are wrong even though factor signal quality is strong.
---

When to use
- A latest-sample debug run shows strong factor signal but raw pre-Bayes labels are clearly mismatched with multi-timeframe evidence.
- Example pattern: latest signal is bullish with strong HTF alignment, but raw build_frame_features labels still come out bear/hostile and force observe_only.
- Use especially in ~/projects-ict-engine/ict-engine for structure_ict / expansion_manipulation work.

Workflow
1. Prove the issue is upstream labeling, not factor weakness.
   - Run factor-pipeline-debug first.
   - Check latest_signal, raw_pre_bayes_labels, filtered_pre_bayes_labels, gating_status, and raw_label_trace.
   - If factor signal is still strong but raw regime/liquidity are wrong, treat build_frame_features as the target surface instead of blindly mutating factor params.

2. Add a narrow market-aware fork at the frame-feature layer.
   - Extend FrameFeatures with:
     - market: Option<String>
   - Keep build_frame_features(candles) as the baseline generic builder.
   - Add:
     - infer_market_from_symbol(symbol: &str) -> String
     - build_frame_features_for_market(candles: &[Candle], market: Option<&str>) -> Result<FrameFeatures>
   - In the market-aware wrapper, call the generic builder first, then overwrite only the labels that need market-specific handling.

3. Start with pragmatic heuristics, not broad rewrites.
   - For NQ, the successful pattern was:
     - if sweep_count > fvg_count * 2, set regime_label = "range"
     - if base liquidity_label == "hostile" and sweep_count > 0 and fvg_count > 0, set liquidity_label = "neutral"
   - Preserve the original counts/evidence so the debug report still shows why the relabel happened.

4. Wire only the paths that need market-aware labels first.
   - The important production/debug surfaces were the expansion factor pipeline builders:
     - build_expansion_factor_pipeline_report(...)
     - build_expansion_factor_pipeline_report_from_registry(...)
   - Pass symbol-derived market via infer_market_from_symbol(symbol), not factor_name.
   - Avoid global replacement based on factor_name; factor_name like structure_ict is not the market.

4.5. Once frame-feature and pre-bayes market forks exist, do not stop at labels if the product goal is market-specific trading behavior.
   - Extend the Symbol surface itself if coverage is incomplete.
     - In this repo, the next necessary step after NQ/ES/YM was adding `GC/CL` to `Symbol`, `parse_symbol(...)`, and trade-plan symbol parsing.
   - Group symbols into reusable market families instead of hard-coding per-symbol behavior everywhere:
     - `NQ/ES/YM -> futures_index`
     - `GC -> metals`
     - `CL -> energy`
   - Keep symbol-level heuristics in `build_frame_features_for_market(...)`, but shift belief/gate/report behavior to market-family policy so later symbols can inherit the right regime behavior cheaply.
   - The reusable sequence that worked was:
     1. expand `Symbol`
     2. patch every symbol parser/caller
     3. add missing frame-feature overrides (`YM`, `GC` here)
     4. expand pre-bayes market overrides (`NQ/YM/GC` here)
     5. inject `market_category` and `market_behavior_profile` into canonical belief packet evidence
     6. only then make posterior/gate/strategy/temporal surfaces market-family aware
     7. make exact/shadow belief node posteriors family-aware too (entry_quality, trade_outcome, risk_posture, market-profile node, shadow family weights)
     8. expose `market_family`, `market_behavior_profile`, and `selected_market_subgraph` on report surfaces and human-facing output
     9. if backtest/history is unnecessary for a symbol, prefer proving the path with `analyze-live` instead of blocking on cleaned historical data
     10. once online defaults are known, make `analyze-live --symbol <SYM>` auto-infer `futures_symbol/spot_symbol/options_symbol/spot_kind`
   - For this repo, reusable live defaults discovered were:
     - `GC -> GC=F / GLD / GLD / etf`
     - `CL -> CL=F / USO / USO / etf`
     - `NQ -> NQ=F / QQQ / QQQ / equity`
     - `ES -> ES=F / SPY / SPY / equity`
     - `YM -> YM=F / DIA / DIA / equity`

5. Expect collateral compile fixes after signature changes.
5. Expect collateral compile fixes after signature changes.
   - In this repo, once objective/pipeline helpers changed, dependent call sites needed cleanup.
   - Typical fixes included:
     - passing symbol into apply_expansion_manipulation_objective(...)
     - threading symbol through build_factor_mutation_metric_set(...)
     - using report.workflow_snapshot.symbol where only a report object is available
     - extending AnalyzeBuildContext with `symbol: &str` so analyze/backtest paths can derive market-specific policy
     - updating all AnalyzeBuildContext construction sites after adding the new field
     - adding `None`/`Some(market)` to every build_pre_bayes_evidence_filter(...) test and call site after the market arg was introduced
   - Re-run cargo check after each batch instead of stacking many edits blindly.

6. Validate with both tests and real data.
   - Add at least one focused unit test around build_frame_features_for_market.
   - If pre-Bayes filter now accepts market, update legacy tests/callers to pass `None` explicitly so cargo test failures are resolved quickly.
   - Then run:
     - cargo fmt
     - cargo check
     - cargo test
     - cargo run -- factor-pipeline-debug --symbol NQ --data <private-tomac-data-cache>/ict-cleaned-mtf/cleaned-15m/nq.continuous-15m.json --factor structure_ict --objective expansion_manipulation

7. Push market-family semantics through canonical belief, not just frame labels.
   - Once `market_category` and `market_behavior_profile` exist in packet evidence, make the canonical belief path consume them directly.
   - The reusable sequence that worked here was:
     - extend `RegimePosterior` with `market_family` and `market_behavior_profile`
     - extend `RegimeGateDecision` with `market_family`
     - derive posterior from the belief packet, not only from a generic pre-bayes filter
     - change `selected_subgraph` from `<regime>_subgraph` to `<market_family>_<regime>_subgraph` when family is known
   - In this repo, practical family behavior was:
     - `metals` -> add stress bias
     - `energy` -> add transition + stress bias
     - `futures_index` -> preserve baseline trend path

8. Carry market-family behavior into downstream belief/report surfaces.
   - Do not stop at posterior/gate.
   - Also thread market-family into:
     - `StrategyRecommendation`
     - `ParticleBeliefSummary`
     - `BeliefReportPacket`
     - human-facing analyze output
   - Useful reusable fields were:
     - `market_family`
     - `market_behavior_profile`
     - `selected_market_subgraph`
   - In this repo, strategy sizing was reduced for `energy`, lightly reduced for `metals`, and left baseline for `futures_index`.
   - `bootstrap_particle_summary(...)` also became family-aware:
     - `energy` -> larger particle budget / ESS
     - `metals` -> medium uplift
     - `futures_index` -> baseline
   - `belief_posteriors` and shadow/sampling outputs can safely carry compact market-weight hints such as:
     - `market_family_weight`
     - `shadow_market_family_weight`

9. Expose market-family conclusions in final product surfaces so the change is inspectable.
   - Add explicit report fields, not only hidden internal behavior.
   - In this repo, useful surfacing points were:
     - `BeliefReportPacket.market_family`
     - `BeliefReportPacket.market_behavior_profile`
     - `BeliefReportPacket.selected_market_subgraph`
     - analyze JSON top-level `market_family_summary`
     - human report string including `market_family=... market_profile=... subgraph=...`
   - This matters because otherwise the architecture changes are real but invisible to downstream users/agents.

10. Validate code-path success separately from data-path success.
   - After market-family code lands, inspect the local cleaned-data roots before assuming a symbol is runnable.
   - In this repo, the critical findings were:
     - repo-local `state/` initially existed only for `NQ`
     - repo-local `data/` did not exist
     - analyze via `--data-root` hard-requires `cleaned-1d`, `cleaned-1h`, and `cleaned-15m`
   - Therefore a 15m-only root will fail analyze even if 15m data exists.
   - Check the exact root shape first using filesystem commands; do not assume sibling intervals exist.

11. For commodities, map practical local aliases before blocking on perfect symbol purity.
   - In this environment, gold cleaned files existed as `xau.continuous-*`, while product symbol support was added as `GC`.
   - A pragmatic bridge that worked was:
     - build a temporary clean root with copied files renamed from `xau.continuous-{15m,1h,1d}.json` to `gc.continuous-{15m,1h,1d}.json`
     - run `analyze --symbol GC --data-root <temp-root> --market gc --state-dir <repo-state>`
   - This is acceptable for pipeline validation when the market family is what matters and no true GC-cleaned set is present yet.
   - Record clearly that this validates code-path and state generation, not final data purity.

12. Treat missing `CL` data as a data-source blocker, not a code blocker — unless live analysis is acceptable.
   - In this repo, after full-code integration:
     - `GC` could be validated by aliasing `xau` data
     - `CL` still could not run on local historical roots because no local `cl/wti/crude` cleaned data was found
   - But if the user does not need backtest/history for that symbol, do not block on cleaned inputs.
   - Prefer proving the path with `analyze-live`:
     - `ict-engine analyze-live --symbol GC --futures-symbol GC=F --spot-symbol GLD --options-symbol GLD --spot-kind etf ...`
     - `ict-engine analyze-live --symbol CL --futures-symbol CL=F --spot-symbol USO --options-symbol USO --spot-kind etf ...`
   - This successfully generated `state/GC` and `state/CL` and verified:
     - `GC -> metals`
     - `CL -> energy`
   - Once these defaults are known, push them into the command surface so users no longer need to pass the full live tuple every time.

13. Make `analyze-live` auto-infer market defaults from `--symbol` when the mappings are stable.
   - In this repo, a reusable implementation pattern was:
     - change `AnalyzeLive` CLI fields from required `String` to optional `Option<String>` for:
       - `futures_symbol`
       - `spot_symbol`
       - `options_symbol`
       - `spot_kind`
     - in `analyze_live_command(...)`, derive defaults from `symbol.to_ascii_uppercase()`
     - fill missing args from the inferred tuple and only error if no mapping exists
   - Validated default tuples were:
     - `NQ -> NQ=F / QQQ / QQQ / equity`
     - `ES -> ES=F / SPY / SPY / equity`
     - `YM -> YM=F / DIA / DIA / equity`
     - `GC -> GC=F / GLD / GLD / etf`
     - `CL -> CL=F / USO / USO / etf`
   - After this patch, the command surface simplified to:
     - `ict-engine analyze-live --symbol GC`
     - `ict-engine analyze-live --symbol CL`
   - Also verify the generated help text changes from requiring explicit futures/spot args to:
     - `Usage: ict-engine analyze-live [OPTIONS] --symbol <SYMBOL>`

14. Human-facing market-specific productization should not stop at the regime block.
   - Once market-family routing works, the raw labels are still too mechanical for product use.
   - In this repo, the useful next productization step was to rewrite the first three human-report blocks as family-aware prose:
     - `metals`
       - price action: emphasize defensive liquidity and waiting for the post-sweep return to trend
       - technicals: emphasize mean-reversion then secondary confirmation
       - SMT: say correlation is only supportive; own-symbol liquidity reaction dominates
     - `energy`
       - price action: emphasize shock risk, false breaks, violent reversals
       - technicals: note indicators can be exaggerated by volatility and need rhythm confirmation
       - SMT: reduce confidence when related markets diverge because volatility often spreads across the complex
   - Keep the original machine label appended as `原始标签=...` so debugging remains possible.
   - Example validated outputs were:
     - `金属结构偏向：偏多，但不宜追。这类盘先看流动性是否被扫完，再等回到顺势一侧；原始标签=...`
     - `能源结构偏向：空头占优，但随时防剧烈反抽。这类盘最怕突发冲击，先防假突破和急反转；原始标签=...`

15. In giant repeated output blocks, patch both analyze and analyze-live together only when the match is exact and verified.
   - In this repo, the human report assembly existed in more than one near-identical block.
   - Safe pattern:
     - first patch one exact full block with unique function context (e.g. `fn emit_analyze_output`)
     - then patch the second block via `replace_all=true` only after confirming the full string really matches both occurrences
   - If live refresh fails during verification, distinguish code success from source instability.
   - Here, code changes were correct, but live validation temporarily failed due to upstream Yahoo timeout/parse errors, not because the human-report patch was wrong.

16. For Yahoo/OpenBB-backed live fetches, a minimal retry loop can be worth adding before more invasive fallback work.
   - In this repo, a simple 3-attempt retry with short sleep around the blocking chart request materially reduced transient failures.
   - Keep it local to the request site first; do not over-generalize retry abstractions prematurely.
   - Verification should include refreshing fresh live JSON after the retry patch, not only `cargo check`.

13. Route no-superior-mutation outcomes away from blind global tuning.
   - When evaluating expansion_manipulation mutations, treat this case explicitly:
     - score_delta <= 0.0
     - and no pre_bayes_gate_regressed
   - Add a dedicated failure tag such as:
     - no_superior_mutation_found
   - Then route action-plan state changes to reflect the real conclusion instead of a generic rejection.
   - The useful state mapping in ict-engine was:
     - factor_mutation_evaluation -> near_local_optimum
     - factor_mutation_focus -> pivot_to_label_refinement_or_market_specific_fork
   - Also extend recommended_mutation_directions_from_failure_tags(...) so this outcome produces guidance that says:
     - stop blind global tuning
     - treat the default as near-local-optimum unless stronger evidence appears
     - shift the next cycle to label refinement or market-specific fork validation

14. For post-stagnation factor-autoresearch, jump clusters must be real spec surfaces, not empty labels.
   - A reusable failure pattern in ict-engine was:
     - repeated `best_factor_composite_regressed`
     - plus `no_superior_mutation_found`
   - A useful first repair was adding a forced jump-template path instead of continuing `structure_ict:next:next...` narrow drift.
   - The forced jump spec should carry at least:
     - `cluster_jump`
     - `cluster_jump_cycle`
     - `available_clusters`
     - `market_specific_fork`
   - Persist `cluster_jump_cycle` in the generated spec itself so the next autoresearch iteration can rotate families instead of resetting to the first cluster.

15. Do not keep every cluster on `structure_ict` if the cluster semantics imply another factor family.
   - The important ict-engine-specific lesson was:
     - `displacement_fvg_cluster` -> keep `base_factor = structure_ict`
     - `mss_bos_cluster` -> keep `base_factor = structure_ict`
     - `premium_discount_ote_cluster` -> keep `base_factor = structure_ict`
     - `smt_cluster` -> switch `base_factor = cross_market_smt`
   - Otherwise SMT becomes only a renamed hint on the old factor and the loop never actually explores the SMT factor family.

16. Give each post-stagnation cluster its own real parameter map.
   - In ict-engine, the reusable v1 cluster-specific overrides were:
     - `displacement_fvg_cluster`
       - `post_sweep_displacement_weight = 1.35`
       - `sweep_weight = 1.10`
       - `unconfirmed_sweep_weight = 0.45`
       - `expansion_threshold = 1.05`
     - `mss_bos_cluster`
       - `lookback = 10.0`
       - `expansion_threshold = 1.18`
       - `sweep_return_bars = 5.0`
       - `opposing_sweep_penalty = 1.25`
     - `premium_discount_ote_cluster`
       - `lookback = 14.0`
       - `expansion_threshold = 0.92`
       - `sweep_recency_bars = 8.0`
       - `sweep_return_bars = 6.0`
     - `smt_cluster`
       - `base_factor = cross_market_smt`
       - `lookback = 24.0`
       - `sweep_atr_multiplier = 0.60`
       - `sweep_weight = 0.72`
       - `opposing_sweep_penalty = 1.05`
   - This is still only a spec-surface improvement, not proof of trading value, but it prevents fake cluster diversity.

17. Validate cluster rotation from persisted attempt history, not only from final summary JSON.
   - A real failure mode encountered was background/long-running autoresearch ending without a final stdout summary or with truncated `/tmp/*.json` output.
   - The durable verification path was reading:
     - `state_<...>/NQ/factor_autoresearch_attempts.json`
   - Confirm actual rotation by checking successive attempts for:
     - `candidate_mutation_spec.direction_hints.cluster_jump`
     - `candidate_mutation_spec.direction_hints.cluster_jump_cycle`
   - In the validated run, attempts rotated as:
     - `mss_bos_cluster` -> cycle 2
     - `premium_discount_ote_cluster` -> cycle 3
     - `smt_cluster` -> cycle 4
     - `displacement_fvg_cluster` -> cycle 5
   - This is the correct proof that the controller stopped narrow same-family looping, even if every attempt was still discarded.


10. Productize latest-sample debug into SOP outputs when handoff/agent guidance depends on the full chain.
   - If the real need is not just standalone `factor-pipeline-debug` but making SOP outputs agent-ready, embed the latest-sample debug directly in the SOP report structs.
   - In this repo, the reusable pattern was:
     - add `recommended_global_pipeline_debug: Option<FactorPipelineDebugReport>` to both `FuturesSopReport` and `ExpansionSopReport`
     - mark with `#[serde(skip_serializing_if = "Option::is_none")]`
     - populate it from the market whose `best_factor` matches `recommended_global_factor` and whose pipeline is present
   - Reuse `build_factor_pipeline_debug_report(...)` rather than building a second ad-hoc summary.

11. Add an explicit pipeline verdict layer rather than forcing downstream agents to infer gate state manually.
   - Extend `FactorPipelineDebugReport` with `pipeline_verdict: String`.
   - A practical verdict mapping used successfully here:
     - `pass_hard` and bridge probability gap >= 0.20 -> `clear_through_pre_bayes_and_bridge`
     - `pass_neutralized` -> `pre_bayes_pass_but_bridge_needs_confirmation`
     - `observe_only` -> `blocked_at_pre_bayes_gate`
     - anything else -> `pipeline_unclear`
   - Keep the raw fields too; verdict is a shortcut, not a replacement for evidence.

12. Preserve or store multi-timeframe context explicitly when embedding debug outside the standalone command path.
   - Standalone `factor-pipeline-debug` rebuilds multi-timeframe summary from CLI inputs, but SOP embedding may not have that context available later.
   - In this repo, `FuturesSopMarketReport` already carried `multi_timeframe_summary`, but `ExpansionMarketReport` did not.
   - Fix by adding `multi_timeframe_summary: Vec<String>` to `ExpansionMarketReport` and storing it at construction time, then pass `&market.multi_timeframe_summary` into `build_factor_pipeline_debug_report(...)`.
   - Do not guess nonexistent fields on `ExpansionBbnSupport`; compile first and inspect structs.

13. After adding report fields, patch test fixture initializers immediately.
   - Rust test fixtures constructing report structs will fail on missing fields even when production code is correct.
   - After adding embedded debug/report fields, update existing unit-test initializers with `recommended_global_pipeline_debug: None` or the appropriate fixture.
   - This was required here for `FuturesSopReport` and `ExpansionSopReport` test initializers before `cargo test` would pass.


14. Prefer compact native commands over skills/MCP first when token reduction is the actual objective.
   - In ict-engine, the cheapest path was not more prompt engineering; it was adding low-token CLI surfaces that expose only decision-critical state.
   - Implement compact commands/views in this order:
     - `factor-pipeline-debug --compact`
     - `next-action`
     - `research-compact`
     - `market-fork-status`
   - Keep full JSON reports for persistence, but expose compact views for agent consumption.

15. Design compact outputs around fields an agent can act on immediately.
   - `factor-pipeline-debug --compact` should include only:
     - `gating_status`
     - `evidence_quality_score`
     - `raw_pre_bayes_labels`
     - `filtered_pre_bayes_labels`
     - `direction_conflict`
     - `selected_entry_quality`
     - `bridge_gap`
     - `market_specific_applied`
     - `pipeline_verdict`
   - `next-action` should include only:
     - `current_focus_phase`
     - `current_focus_reason`
     - `blocking_stage`
     - `blocking_status`
     - `blocking_reason`
     - `next_command`
     - top `pending_actions`
     - top `risk_flags`
   - `research-compact` should include only:
     - `objective`
     - `best_factor`
     - `recommended_next_command`
     - top `top_factor_actions`
     - compact `family_decisions`
   - `market-fork-status` should include only:
     - `market_specific_fork`
     - compact `structure_ict` score/action
     - `pre_bayes_gate_status`
     - `next_command`

16. Use existing persisted state instead of recomputing or re-reading huge objects.
   - `next-action` should read the latest `WorkflowSnapshot` and compress it.
   - `research-compact` and `market-fork-status` should read the latest `ResearchRunRecord` from persisted state files.
   - Avoid feeding `AgentPromptPack`, full `WorkflowSnapshot`, lineage history, or full artifacts back into the model when compact state is enough.

17. Verify token reduction with serialized-size tests, not just intuition.
   - Add tests asserting the compact JSON stays small enough to be useful.
   - The successful pattern here was checking serialized byte length thresholds for compact views rather than hand-waving about “smaller output”.


19. README and router behavior must make compact-first onboarding obvious.
   - If agent onboarding pain shows README still points to old heavy paths, move compact-first entrypoints to the front:
     - `next-action`
     - `research-compact`
     - `market-fork-status`
     - `pre-bayes-compact`
     - `artifact-gate-compact`
     - `factor-pipeline-debug --compact`
   - `scripts/compact_router.py` should have a real `--help` path, not only a JSON usage error on missing args.
   - Empty-state commands should prefer actionable guidance over giant null-filled JSON.


21. Separate internal compact evidence from human-facing output.
   - In ict-engine, internal routing should keep using compact commands and layered debug state.
   - But human-facing answers should be translated into five explicit sections:
     - 基本价格结构分析
     - 技术面价格分析
     - SMT相关性分析
     - Regime分类结合贝叶斯分析并给推测概率
     - 交易计划
   - Do not expose raw internal terms like `pre_bayes_gate`, `structure_ict verdict`, or `market_specific_fork` directly to end users unless they explicitly ask for internals.

22. Enforce the five-block human format at the project prompt/guidance layer first.
   - A low-risk first landing is to patch `src/agent/prompts.rs` so `AgentPromptPack.workflow` instructs agents to keep internal evidence compact but answer humans in exactly the five readable sections above.
   - This improves downstream agent behavior immediately, even before all CLI output surfaces are refactored.

23. When wiring five-block output into analyze/analyze-live, avoid invasive edits to the giant assembly chain.
   - The safe path is:
     - add a dedicated formatter like `build_human_output(&AnalyzeReport) -> String`
     - populate it only at the final output layer
     - do not deeply rewrite the existing analyze assembly while debugging unrelated pipeline work
   - This matters because `src/main.rs` is large and tightly coupled; directly splicing the formatter into the analyze construction path can easily break unrelated assembly code.

24. For layered pipeline debug, add explicit layer objects rather than relying only on raw traces.
   - Extend `FactorPipelineDebugReport` with higher-level objects such as:
     - `feature_derivation`
     - `label_policy`
   - These should summarize:
     - market
     - regime/liquidity labels
     - counts/evidence summaries
     - raw vs filtered assignments
     - gating status and rationale
   - Keep raw trace fields too; the new layers are for clarity, not replacement.

Pitfalls
- Do not infer market from factor_name; use symbol.
- Do not assume a previously patched struct field actually exists; verify FrameFeatures definition before compiling.
- A naive test may fail because sample data does not guarantee sweeps/FVG counts; assert conditionally on the baseline counts/labels instead of forcing nonexistent conditions.
- In this environment, read_file snapshots and local file reality can diverge; when the codebase seems inconsistent, prefer shell/fs verification.
- Graphify rebuild may be blocked by permissions. If you already know it is blocked, do not retry blindly.
- For EML/nonlinear fusion PoCs, do not promote a global regime reclassifier first. Prefer a local gate/multiplier inside an already-identified regime, with true sweep/rejection features rather than loose proxies like price_range + volume_spike.
- When backtest trade records lack excursion fields (`max_runup`, `max_drawdown`), do not invent precision labels from unavailable data. Either add the fields in the backtest model or use an explicitly weaker proxy and label it as such.
- In trading PoCs, improvement in sample redistribution alone is not evidence of value. If expansion buckets grow but reversal precision/win rate do not improve, treat the nonlinear branch as failed and stop early.

Verification notes
- For the validated NQ case, raw labels became range/neutral and resonance became aligned while structure_ict remained the active factor.
- This confirmed the bottleneck was label derivation, not factor weakness.
