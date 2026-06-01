# Trade-Usable Root Cause And Repair - 2026-05-31

- owner: `codex`
- route_alias: `sd/ict-engi-fact-rese-muta`
- repo: `ict-engine`
- branch: `main`
- status: `active / not complete`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Current Update - 2026-05-31T11:51+0800

最新 compact audit:

```bash
python3 support/scripts/factor_claim_terminalization_audit.py --compact
```

结果：`status=pass`，`active_claims=0`，`live_factor_processes=0`，
`promotion_allowed_true=0`，`trade_usable_true=0`，
`same_tree_practical_closure=null`。

repo-native IBKR accepted-feedback preflight also跑过：

- readback:
  `/tmp/ict-engine-nq-compound-repo-readback-preflight-20260531T114632+0800/checks/ibkr_execution_readback.json`
- result: IB Gateway paper port `4002` reachable, `readonly=true`,
  `execution_rows_total=0`, `rows_with_commission_report=0`
- conversion summary:
  `/tmp/ict-engine-nq-compound-repo-readback-preflight-20260531T114632+0800/summaries/accepted_feedback_conversion_summary.json`
- result: `accepted_feedback_rows=0`,
  `terminal_decision=accepted_execution_feedback_missing`

## Current Hard Answer

当前没有可实战因子。最新实测说明“没有实战因子”不是由历史
claim 债务或当前运行位造成的：

```bash
python3 support/scripts/factor_claim_terminalization_audit.py --compact
```

结果：`status=pass`，`active_claims=0`，`live_factor_processes=0`，
`promotion_allowed_true=0`，`trade_usable_true=0`，
`same_tree_practical_closure=null`。

期间出现过新的 no-runtime/code-only claim 和短暂 foreign runtime；分类已
修复并等 guard 清空后重新实测。它们不改变根因：实战计数仍然是 0，
canonical same-tree practical closure 仍然不存在。

硬原因是没有任何一个因子同时证明：

1. ETH/full retained session 覆盖和 `rth_filter_applied=false`。
2. 产品级已验证真实成本，而不是固定 bps 权威。
3. Gate 1 经济性、密度、分段/年份稳定性。
4. provider / Auto-Quant / Pre-Bayes / BBN workflow / path-ranker /
   execution-tree / feedback-update / policy-training 同根闭环。
5. accepted paper/live/broker execution feedback，而不是 backtest 或 simulated
   label。
6. canonical `same_tree_practical_closure` 由
   `support/scripts/research/same_tree_practical_closure.py` 验证通过。

## Root Causes

| ID | 漏洞 / 原因 | 当前证据 | 修复 |
|---|---|---|---|
| R1 | practical closure 证据不存在 | compact audit `same_tree_practical_closure=null` | 只接受 canonical same-tree packet，不用 claim 计数冒充 |
| R2 | accepted broker/paper feedback 缺口 | NQ compound 先前 IBKR readback 转换为 `accepted_feedback_rows=0`；当前文档里引用的 `/tmp/.../ibkr_paper_execution_readback.py` 不存在 | 新增 repo 内 `support/scripts/research/ibkr_execution_readback.py`，只读 `reqExecutions`，输出可复现 readback JSON |
| R3 | 最强候选仍停留在非实战层 | NQ compound Gate 1 经济性强但 lifecycle 曾有 `exact_branch_survived=false`、`execution_candidate_actionable=false`、`path_ranker_score_used_by_execution_tree=false`、accepted feedback 空 | 先跑 accepted feedback preflight；空则停止，不再跑 lifecycle 假装有反馈 |
| R4 | 新鲜本地候选未进 exact-AQ/downstream | ETH OTE local candidate 有成本/密度/年份证据，但仍是 local retained-cache screen | 若 NQ feedback 仍为空，创建 exact-AQ/provider/downstream lane |
| R5 | 旧文档容易把“下一步脚本”当作现成工具 | `/tmp` readback 脚本不存在，导致步骤不可复现 | 把工具沉到 repo、manifest、SCRIPTS，并加测试 |
| R6 | done-definition 不是完成证明 | `done_definition_audit.py --compact --practical-admission-source-timeout-seconds 300` 轻量面 `status=pass`，但 heavy gates 全部 skipped；tracked practical-admission 违规为 0，未跟踪 wrapper 债务仍漂移在 quarantine | 不把轻量 audit 当完成；需要 heavy gates 和 runtime 证据后才能 claim completion |

## Current Repair Slice

代码改动目标：

- 新增 `support/scripts/research/ibkr_execution_readback.py`。
- 加测试 `support/scripts/research/tests/test_ibkr_execution_readback.py`。
- 加固 `real_trade_feedback_labels.py`：IBKR readback 行如果明确缺少
  `broker_fill_evidence` 或 `commission_report_present`，不能转成 accepted
  feedback。
- 更新 `support/scripts/SCRIPTS.md` 和 `support/scripts/script_manifest.json`。

不做：

- 不放宽 trade_usable / promotion gate。
- 不把本地 screen、zero-fee AQ、simulated/backtest feedback 当实战。
- 不重置或清理共享 dirty worktree。

## Next Commands

验证补丁：

```bash
python3 -m unittest support.scripts.research.tests.test_ibkr_execution_readback -v
python3 -m unittest support.scripts.research.tests.test_real_trade_feedback_labels -v
python3 support/scripts/check_script_manifest.py
```

若 compact audit 仍清空，再跑只读 IBKR execution readback：

```bash
STAMP=$(date +%Y%m%dT%H%M%S+0800)
ROOT=/tmp/ict-engine-nq-compound-accepted-feedback-runtime-${STAMP}
mkdir -p "$ROOT/checks"

python3 support/scripts/research/ibkr_execution_readback.py \
  --symbol NQ \
  --sec-type FUT \
  --exchange CME \
  --output "$ROOT/checks/ibkr_execution_readback.json"

python3 support/scripts/research/real_trade_feedback_labels.py \
  --ibkr-execution-readback-json "$ROOT/checks/ibkr_execution_readback.json" \
  --ibkr-contract-symbol NQ \
  --output-jsonl "$ROOT/checks/accepted_feedback.jsonl" \
  --summary-json "$ROOT/summaries/accepted_feedback_conversion_summary.json" \
  --metrics-json "$ROOT/checks/accepted_feedback_conversion_metrics.json" \
  --symbol TOMAC_NQ_COMPOUND_TREND_RRR_CHOPFILTER_V1 \
  --strategy-name nq_compound_trend_rrr_chopfilter_v1 \
  --factor-id nq_compound_trend_rrr_chopfilter_v1 \
  --branch-path 'TrendExpansion -> HtfTrendRegime -> ChopFilter -> MomentumResonance -> CompoundTrendRrrBreadth -> nq_compound_trend_rrr_chopfilter_v1' \
  --auto-quant-run-id "ibkr-paper-execution-readback-${STAMP}" \
  --feedback-source auto_quant_real_trades:paper_execution_feedback:nq_compound_trend_rrr_chopfilter_v1
```

如果 `accepted_feedback.jsonl` 为空，NQ compound 不能进入 practical
lifecycle。下一步转向 ETH OTE exact-AQ/downstream。

## Verification Log

- `python3 -m unittest support.scripts.research.tests.test_ibkr_execution_readback -v`
  passed: `Ran 3 tests ... OK`.
- `python3 -m unittest support.scripts.research.tests.test_real_trade_feedback_labels -v`
  passed: `Ran 11 tests ... OK`.
- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  passed: `Ran 120 tests ... OK`.
- `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure -v`
  passed: `Ran 22 tests ... OK`.
- `python3 support/scripts/check_script_manifest.py` passed:
  `script_manifest status=pass`.
- `git diff --check` passed for the touched script/test/doc surfaces.
- Focused practical-admission source scan on the touched readback/converter and
  NQ compound lifecycle wrapper returned no violations.
- Tracked wrapper scan with
  `downstream_practical_admission_source_check.py --tracked-run-wrappers --jobs 8`
  returned `files=49 violations=0`.
- Full lightweight done-definition with 300s practical-admission timeout
  returned `status=pass` but `completion_ready=false` because heavy gates were
  skipped. It also reported untracked practical-admission quarantine drift
  (`untracked_violating_files=222`, `untracked_violation_count=461`) that must
  not be used as release or practical evidence.

## Current Stop Condition

NQ compound has a confirmed accepted-feedback blocker. The paper gateway is
reachable, but there are zero NQ execution rows to convert, so this branch must
not enter practical lifecycle from current evidence. Continue factor mining on a
separate exact-AQ/downstream lane only after same-turn compact audit/process
guards are clear.

Concrete 11:55 evidence:

- run root:
  `/tmp/ict-engine-nq-compound-accepted-feedback-runtime-20260531T115343+0800`
- `checks/ibkr_execution_readback.json`: `readonly=true`, `port=4002`,
  `execution_rows_total=0`, `rows_with_commission_report=0`
- `checks/accepted_feedback_summary.json`:
  `status=no_accepted_execution_feedback_rows`,
  `accepted_feedback_rows=0`, `broker_fill_evidence_rows=0`,
  `broker_realized_rows=0`,
  `terminal_decision=accepted_execution_feedback_missing`
- `workdoc.md` and `summaries/terminal_summary.json` record
  `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`, and
  `same_tree_practical_closure=null`

After this read-only preflight, compact claim audit reported a foreign live
factor process for
`/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`;
do not start the ETH OTE exact-AQ/downstream lane until that runtime clears in a
fresh same-turn audit.

## 2026-05-31 11:54 +0800 Follow-Up

Repo-native NQ accepted-feedback readback was re-run after the guard cleared:

- Readback:
  `/tmp/ict-engine-nq-compound-repo-readback-preflight-20260531T113923+0800/checks/ibkr_execution_readback.json`
  returned `execution_rows_total=0`.
- Conversion:
  `/tmp/ict-engine-nq-compound-repo-readback-preflight-20260531T113923+0800/summaries/accepted_feedback_summary.json`
  returned `accepted_feedback_rows=0`,
  `accepted_execution_feedback_ready=false`,
  `terminal_decision=accepted_execution_feedback_missing`.

ETH/full-session OTE reacceleration exact-AQ was launched by a sibling runtime
after claim/process guards cleared:

- Run root:
  `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-exact-aqlaunch-20260531T114456+0800`
- Result: `exit=0`, `aq_trade_count=2422`,
  `aq_total_profit_pct=32.16157362622999`,
  `aq_profit_factor=1.0796046672902377`.
- Practical status remains false:
  `promotion_allowed=false`, `trade_usable=false`, `same_tree_practical_closure=null`.
- Hard blockers: exact-AQ rows are simulated/backtest material, not accepted
  paper/live/broker feedback; downstream lifecycle was not launched; Freqtrade
  reported `48.30%` missing-data fillup on the synthetic futures feed.

Downstream prep was then generated fail-closed from the exact AQ export:

- Run root:
  `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-downstream-prep-20260531T115000+0800`
- Terminal packet:
  `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-downstream-prep-20260531T115000+0800/checks/terminal_metrics.json`
- It wrote `2422` rejected simulated-backtest feedback rows and a lifecycle
  command plan, while keeping `accepted_execution_feedback=false`,
  `promotion_allowed=false`, `trade_usable=false`, and
  `same_tree_practical_closure=null`.

Current runtime blocker: compact audit saw a separate live AQ process under
`/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`.
Do not launch additional provider/AQ/IBKR/lifecycle work until the compact audit
and focused process scan are clear in the same turn.

## 2026-05-31 12:04 +0800 Refresh

The same TSMOM AQ runtime is still live:

- PID: `68325`
- command: `run_tomac_index_futures_clean_aq_v1.py`
- run root:
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`
- elapsed at check: about 10 minutes
- current artifacts: `workdoc.md` and `checks/pre_aq_claim_collision_audit.exit`
  only; no terminal AQ summary yet

Fresh coordinated objective snapshot at
`/tmp/ict-engine-goal-20260531T120446+0800-current-head-bc0f7beb` still reports
`trade_usable_true=0`, `promotion_allowed_true=0`, and
`same_tree_practical_closure=null`. Do not launch NQ/ETH OTE/provider/downstream
work while this runtime is active.

## 2026-05-31 12:32 +0800 OTE Repair Prep

Fresh readback kept `trade_usable_true=0`, `promotion_allowed_true=0`, and
`same_tree_practical_closure=null`.

TSMOM low-turnover AQ terminalized fail-closed under:

- `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`

Readback across `1d`, `1h`, `30m`, `15m`, and `4h` found
`survivors_instrument_cost=[]`, `downstream_allowed=false`,
`promotion_allowed=false`, and `trade_usable=false`.

OTE exact-AQ was reclassified from its same-root instrument-cost readback:

- exact root:
  `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-exact-aqlaunch-20260531T120650+0800`
- decision:
  `exact_aq_cost_positive_but_pf_split_year_instability_fail_closed`
- blockers: PF below `1.10`, first chronological third negative, and 2022
  negative after fee-only instrument-cost readback.

No practical flag changed. The only new candidate is a repair hypothesis, built
from the exact-AQ trade export and kept fail-closed:

- new factor_id:
  `tomac_nq_15m_eth_trend_ote_reacceleration_long_qualityreclaim_calendar_guard_exact_aq_v1`
- repair guard: exclude Tuesday entries and UTC hour `12` entries
- offline trade-export approximation after fee-only readback:
  `n=1858`, density `1.195/session`, net `55.068%`, PF proxy `1.198`,
  chronological thirds `16.556 / 20.855 / 17.657`, years `5/5` positive
- this is not promotion evidence; it must be rerun through exact-AQ and then
  downstream/feedback/same-tree closure.
- projection artifact:
  `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-calendar-guard-exact-aqprep-20260531T122840+0800/checks/calendar_guard_trade_export_projection.json`
- compact projection artifact:
  `support/docs/experiments/actionable-regime-confidence/runs/20260531T122840+0800-codex-tomac-eth-trend-ote-reacceleration-calendar-guard-exact-aqprep-v1/checks/calendar_guard_trade_export_projection.json`

No-launch packet:

- run root:
  `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-calendar-guard-exact-aqprep-20260531T122840+0800`
- compact root:
  `support/docs/experiments/actionable-regime-confidence/runs/20260531T122840+0800-codex-tomac-eth-trend-ote-reacceleration-calendar-guard-exact-aqprep-v1`
- claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T122840+0800-codex-tomac-eth-trend-ote-reacceleration-exact-aqprep.claim`
- status: `prepared_no_launch`
- `provider_or_aq_launched=false`, `promotion_allowed=false`,
  `trade_usable=false`, `update_goal=false`

Code/tests changed to make the repair reproducible:

- `support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_eth_trend_ote_reacceleration_exact_aqprep_v1.py`
- `support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_eth_trend_ote_reacceleration_exact_aqprep_v1.py`
- verification:
  `python3 -m py_compile ...` passed
- verification:
  `python3 support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_eth_trend_ote_reacceleration_exact_aqprep_v1.py -v`
  passed, `10` tests

Current launch blocker:

- compact audit `status=needs_attention`
- fresh active claim without live process:
  `20260531T122333+0800-codex-ehlers-autocorr-periodogram-cycle-regime-30m-exact-aq.claim`

Next legal step after compact audit and focused `ps` both clear:

```bash
python3 support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_eth_trend_ote_reacceleration_exact_aqprep_v1.py \
  --root /tmp/ict-engine-tomac-eth-trend-ote-reacceleration-calendar-guard-exact-aqlaunch-<STAMP> \
  --compact-root support/docs/experiments/actionable-regime-confidence/runs/<STAMP>-codex-tomac-eth-trend-ote-reacceleration-calendar-guard-exact-aqlaunch-v1 \
  --calendar-repair-guard \
  --launch \
  --write-claim \
  --timeout 1800
```

Stop fail-closed if exact-AQ still misses PF/split/year stability or if
accepted paper/live/broker feedback and canonical same-tree practical closure
remain absent.

## 2026-05-31 12:20 +0800 Refresh

The TSMOM AQ runtime under
`/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`
exited and compact audit cleared:

- compact_audit_status: `pass`
- live_factor_processes: `0`
- active_claims: `0`
- promotion_allowed_true: `0`
- trade_usable_true: `0`
- same_tree_practical_closure: `null`

TSMOM remained non-practical. Final 30m AQ gate:

- `trade_count=940`
- `raw_total_profit_pct=-1.23`
- `instrument_cost_total_profit_pct=-6.321667`
- `survives_instrument_cost=false`
- `density_target_1_to_3_per_day=false`
- `gate1_survivor=false`
- `promotion_allowed=false`
- `trade_usable=false`

Earlier same-root 1h/4h/1d readbacks also failed instrument-cost survival:
1h was only `raw_total_profit_pct=1.55` and
`instrument_cost_total_profit_pct=-2.20375`; 4h and 1d were gross-negative.

Repo-native NQ compound accepted-feedback preflight was rerun in this turn:

- run root:
  `/tmp/ict-engine-nq-compound-accepted-feedback-runtime-20260531T122028+0800`
- readback: `checks/ibkr_execution_readback.json`
- result: IB Gateway paper port `4002` reachable, readonly readback,
  `execution_rows_total=0`
- conversion: `summaries/accepted_feedback_summary.json`
- result: `accepted_feedback_rows=0`,
  `broker_fill_evidence_rows=0`,
  `terminal_decision=accepted_execution_feedback_missing`

Decision: NQ compound must not enter practical lifecycle from current evidence.
The next repair path is a separate candidate lane, not gate relaxation or
simulated-feedback relabeling.

## 2026-05-31 12:22 +0800 Refresh

Current hard count is still zero:

- `promotion_allowed_true=0`
- `trade_usable_true=0`
- `same_tree_practical_closure=null`

TSMOM vol-scaled low-turnover AQ produced more negative evidence, not a
practical candidate. The same root
`/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`
now has gate summaries for `1d`, `1h`, `4h`, and `30m`; each command exited 0
and each gate packet reports:

- `decision=observation_no_autoquant_survivor_yet`
- `survivors_instrument_cost=[]`
- `cost_gate_authority=instrument_cost`
- `promotion_allowed=false`
- `trade_usable=false`

NQ compound accepted-feedback readback was refreshed with repo-native
diagnostic fields after adding raw/filter counts to
`support/scripts/research/ibkr_execution_readback.py`:

- run root:
  `/tmp/ict-engine-nq-compound-accepted-feedback-refresh-20260531T122128+0800`
- `raw_execution_rows_total=0`
- `rows_after_local_filters=0`
- `rows_filtered_without_commission_report=0`
- `execution_rows_total=0`
- `rows_with_commission_report=0`
- `accepted_feedback_rows=0`
- `terminal_decision=accepted_execution_feedback_missing`

This removes the ambiguity between "IBKR rows were filtered out for missing
commissionReport" and "no matching NQ executions exist". The current blocker is
the latter.

Immediately after that read-only refresh, another TSMOM 15m AQ process appeared
under the same root:

- PID: `11741`
- child: `run_tomac.py`
- command root:
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`
- command shape: `--reuse-clean --aq-smoke-timeframe 15m`

Do not start new provider/AQ/IBKR/lifecycle work while that process remains
live. Continue with readback/source-level work only, or wait for a fresh compact
audit to return `status=pass`.

The 15m AQ process then terminalized cleanly and stayed negative:

- `trade_count=874`
- `total_profit_pct=-16.85`
- `profit_factor=0.8794`
- gate summary:
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800/summaries/autoquant_clean_15m_gate.json`
- `decision=observation_no_autoquant_survivor_yet`
- `survivors_instrument_cost=[]`
- `promotion_allowed=false`
- `trade_usable=false`

Fresh compact audit after that returned `status=pass`, `live_factor_processes=0`,
`promotion_allowed_true=0`, `trade_usable_true=0`, and
`same_tree_practical_closure=null`.

Source search found no existing accepted feedback artifact to reuse for the NQ
or ETH/full-session candidates. The repo has ingestion/readback paths for
accepted paper/live/broker feedback, but no current IBKR paper execution rows
and no existing accepted-feedback JSONL that can legally close the practical
gate. There is also no existing repo order-placement/paper-order producer to run
without a separate human confirmation; current IBKR helper surfaces are
read-only.

## 2026-05-31 12:24 +0800 Audit Guard Repair

The collision guard had a real false-clear hole around clean-AQ TOMAC roots:
terminalized `summary.json` / `checks/*.exit` artifacts were treated as enough
to drop a matching wrapper process, even when the exit file was older than the
currently running process. That can make `compact audit` report
`live_factor_processes=0` while `ps` still shows a live wrapper.

Repair slice:

- canonical owner:
  `support/scripts/factor_claim_terminalization_audit.py`
- regression tests:
  `support/scripts/tests/test_factor_claim_terminalization_audit.py`
- fixed behavior: terminalized clean-AQ roots are still suppressible when the
  wrapper has no descendants and its exit artifact is current, but a newer live
  wrapper whose exit file predates the process remains a live blocker.
- verification:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  passed `122` tests.
- same-turn runtime proof after the fix:
  `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  now reports `status=needs_attention`, `live_factor_processes=1`, and surfaces
  PID `11741` under
  `/tmp/ict-engine-tomac-tsmom-vol-scaled-low-turnover-aq-20260531T115002+0800`;
  focused `ps` independently shows the same wrapper plus child `run_tomac.py`.

This guard repair does not create a practical factor. It prevents false launch
clearance while the existing TSMOM 15m AQ process is still live.

## 2026-05-31 12:27 +0800 Final Current-State Readback

Fresh compact audit before handoff:

- `status=needs_attention`
- `active_claims=1`
- `live_factor_processes=0`
- `promotion_allowed_true=0`
- `trade_usable_true=0`
- `same_tree_practical_closure=null`

The blocker is a fresh active claim without a live process:

- claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T122333+0800-codex-ehlers-autocorr-periodogram-cycle-regime-30m-exact-aq.claim`
- agent: `codex-ehlers-cycle-regime-exact-aq-20260531T122333+0800`
- scope: Board B guarded exact-AQ launch for Ehlers autocorrelation-periodogram
  cycle-regime NQ 30m ETH/full-session candidate
- age at audit: 3 minutes

Do not take over this claim or launch a sibling provider/AQ/lifecycle lane while
it is fresh. The current hard answer remains: no practical factor exists yet,
because no candidate has both strict ETH/full-session cost-surviving economics
and accepted paper/live/broker execution feedback plus validated same-tree
practical closure.

## 2026-05-31 12:48 +0800 Guarded Continuation

Fresh routing/readback was repeated before any launch. Current compact audit is
still blocked by one fresh active no-launch prep claim:

- claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T124304+0800-codex-realized-jump-bipower-state-filter-prep.claim`
- scope: Board B no-launch exact-AQ material prep for realized jump bipower
  state filter NQ ETH/full-session independent timeframe fanout
- latest audit shape: `status=needs_attention`, `active_claims=1`,
  `live_factor_processes=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, `same_tree_practical_closure=null`

Do not take over or launch sibling provider/AQ/IBKR/lifecycle work while that
claim remains fresh. It is only minutes old and has no terminal decision.

The OTE calendar-guard exact-AQ launch packet was revalidated without launching
runtime:

- `python3 -m py_compile support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_eth_trend_ote_reacceleration_exact_aqprep_v1.py support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_eth_trend_ote_reacceleration_exact_aqprep_v1.py`
  passed
- `python3 support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_eth_trend_ote_reacceleration_exact_aqprep_v1.py -v`
  passed `10` tests
- claim remains terminal no-launch:
  `status=terminalized_wrapper_prep_no_launch`,
  `decision=prepared_no_launch_awaiting_collision_free_exact_aq`
- projection remains candidate-only:
  `trade_count=1858`, density `1.194855/session`, fee-only PF `1.198304`,
  fee-only total `55.067792%`, chronological thirds all positive, years `5/5`
  positive, but `promotion_allowed=false`, `trade_usable=false`, and
  `same_tree_practical_closure=null`

Next legal launch command after a same-turn compact audit and focused process
scan both clear:

```bash
STAMP=$(date +%Y%m%dT%H%M%S+0800)
python3 support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_eth_trend_ote_reacceleration_exact_aqprep_v1.py \
  --root /tmp/ict-engine-tomac-eth-trend-ote-reacceleration-calendar-guard-exact-aqlaunch-${STAMP} \
  --compact-root support/docs/experiments/actionable-regime-confidence/runs/${STAMP}-codex-tomac-eth-trend-ote-reacceleration-calendar-guard-exact-aqlaunch-v1 \
  --calendar-repair-guard \
  --launch \
  --write-claim \
  --timeout 1800
```

Waiting-window source intake was kept read-only. A duplicate check for the
source-backed `nq_session_halfday_mim_v1` reserve found it is already prepared
and wrapper-ready under:

- `support/docs/experiments/actionable-regime-confidence/20260530T080325+0800-codex-nq-session-halfday-mim-source-prep.md`
- `support/docs/experiments/actionable-regime-confidence/20260530T082524+0800-codex-nq-session-halfday-mim-wrapper-ready.md`
- `support/docs/experiments/actionable-regime-confidence/20260530T082917+0800-codex-nq-session-halfday-mim-launch-ready-no-launch.md`

Do not reopen this branch unchanged while the fresh realized-jump/bipower claim
is active. It remains a backup launch-ready candidate only after guard clearance
and exact duplicate/negative readback.

## 2026-05-31 12:57 +0800 OTE Calendar-Guard Exact-AQ Readback

After compact audit cleared (`active_claims=0`, `live_factor_processes=0`) and
no focused `run_tomac`/AutoQuant/Freqtrade/fetch/IBKR runtime owner was present,
the OTE calendar-guard exact-AQ was launched:

- run root:
  `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-calendar-guard-exact-aqlaunch-20260531T125157+0800`
- compact root:
  `support/docs/experiments/actionable-regime-confidence/runs/20260531T125157+0800-codex-tomac-eth-trend-ote-reacceleration-calendar-guard-exact-aqlaunch-v1`
- exact-AQ result: `exit=0`, `trade_count=1943`, raw total `51.85%`,
  raw PF `1.148699`, max drawdown `15.5913%`
- Freqtrade warning still present: `48.30%` missing-data fillup on the synthetic
  NQ futures feed.

Post-run verified NQ instrument-cost readback:

- readback:
  `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-calendar-guard-exact-aqlaunch-20260531T125157+0800/checks/exact_aq_instrument_cost_readback.json`
- compact copy:
  `support/docs/experiments/actionable-regime-confidence/runs/20260531T125157+0800-codex-tomac-eth-trend-ote-reacceleration-calendar-guard-exact-aqlaunch-v1/checks/exact_aq_instrument_cost_readback.json`
- fee-only total: `42.364653%`
- fee-only PF: `1.140089`
- fee-plus-assumed-slippage total: `33.415695%`
- fee-plus-assumed-slippage PF: `1.111866`
- chronological thirds fee-only: `6.099439 / 20.119886 / 16.145329`
- years fee-only:
  `2021=13.813027`, `2022=-7.969077`, `2023=13.014373`,
  `2024=11.176544`, `2025=12.329786`

Terminal decision:
`exact_aq_fail_closed_after_instrument_cost_readback`.
The repair improved PF and split stability, but 2022 remains negative after
verified NQ fee-only instrument-cost readback. Keep
`downstream_allowed=false`, `promotion_allowed=false`, `trade_usable=false`,
`update_goal=false`, and `same_tree_practical_closure=null`. Do not launch
downstream lifecycle or accepted-feedback conversion from this root.

## 2026-05-31 13:02 +0800 Gate Repair Readback

The gate-repair side is now better covered, but the factor side is still not
trade-usable.

- Done-definition full proof:
  `/tmp/ict-engine-done-definition-heavy-20260531T-codex-closedloop-final.json`
  returned `completion_ready=true`, `pass_count=11`, `skip_count=0`.
- Fixed-bps source authority is now in done-definition and objective closure:
  tracked violations are `0`; untracked fixed-bps debt remains quarantined and
  cannot count as real-cost proof.
- Prior-AQ readback in the TOMAC clean-AQ wrapper fails closed for practical
  flags; old `promotion_allowed`, `trade_usable`, and `update_goal` values are
  retained only as `prior_gate_*` telemetry.
- Exact-AQ repair root
  `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-calendar-guard-exact-aqlaunch-20260531T125313+0800`
  stayed `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`,
  and `same_tree_practical_closure=null`.
- Current compact audit is blocked by a live TSMOM 5m AQ process, with no active
  claim and no practical flags:
  `live_factor_processes=1`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, `same_tree_practical_closure=null`.

Therefore the root cause remains: no current candidate has both accepted
paper/live/broker execution feedback and validated same-tree practical closure.

## 2026-05-31 13:18 +0800 Latest Hard Readback

Fresh compact audit is clear but still proves zero practical factors:

- compact_audit_status: `pass`
- active_claims: `0`
- live_factor_processes: `0`
- promotion_allowed_true: `0`
- trade_usable_true: `0`
- same_tree_practical_closure: `null`

Focused process scan showed only unrelated objective/done-definition/release
audit commands, not a TOMAC/AQ/IBKR/fetch/paper factor runtime owner.

The latest OTE calendar-guard exact-AQ root is:

- `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-calendar-guard-exact-aqlaunch-20260531T125313+0800`

Exact-AQ / instrument-cost readback:

- factor_id:
  `tomac_nq_15m_eth_trend_ote_reacceleration_long_qualityreclaim_calendar_guard_exact_aq_v1`
- trade_count: `1943`
- gross_total_profit_pct: `45.056778`
- gross_profit_factor: `1.14973`
- fee_only_instrument_cost_total_profit_pct: `42.364653`
- fee_only_instrument_cost_profit_factor: `1.140089`
- fee_plus_assumed_slippage_total_profit_pct: `33.390902`
- fee_plus_assumed_slippage_profit_factor: `1.108617`
- trades_per_session: `1.249518`
- chronological_thirds_fee_only_pct:
  `6.099439 / 20.119886 / 16.145329`
- year_fee_only_total_profit_pct:
  `2021=13.813027`, `2022=-7.969077`, `2023=13.014373`,
  `2024=11.176544`, `2025=12.329786`
- years_fee_only_positive: `4/5`
- decision: `exact_aq_fail_closed_after_instrument_cost_readback`
- practical flags: `promotion_allowed=false`, `trade_usable=false`,
  `update_goal=false`, `same_tree_practical_closure=null`

This candidate is no longer blocked by density or PF after real NQ fee-only
instrument cost; it is blocked by year stability, specifically negative 2022,
and by the still-missing accepted execution-feedback / same-tree closure chain.

Downstream prep from that exact-AQ export was intentionally no-launch /
fail-closed:

- root:
  `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-calendar-guard-downstream-prep-20260531T130527+0800`
- status: `simulated_feedback_downstream_prep_fail_closed`
- decision:
  `no_launch_simulated_backtest_feedback_not_practical_execution_feedback`
- rejected simulated/backtest feedback rows: `1943`
- feedback source:
  `auto_quant_real_trades:simulated_backtest:tomac_nq_15m_eth_trend_ote_reacceleration_long_qualityreclaim_calendar_guard_exact_aq_v1`
- broker_fill_evidence_rows: `0`
- broker_realized_feedback_rows: `0`
- market_data_provenance.status: `blocked_for_practical_promotion`
- return_sanity/status blocker: `blocked_missing_data_fillup_warning`
- practical flags: `accepted_execution_feedback=false`,
  `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`,
  `same_tree_practical_closure=null`

Accepted-feedback readback for the OTE branch also failed closed:

- root:
  `/tmp/ict-engine-ote-calendar-guard-accepted-feedback-readback-20260531T130652+0800`
- IBKR readback:
  `execution_rows_total=0`, `rows_with_commission_report=0`
- accepted conversion:
  `status=no_accepted_execution_feedback_rows`,
  `accepted_feedback_rows=0`,
  `accepted_execution_feedback_ready=false`,
  `broker_fill_evidence_rows=0`,
  `broker_realized_rows=0`,
  `terminal_decision=accepted_execution_feedback_missing`

Current root cause, in one line: there are profitable/cost-positive exact-AQ
shapes, but none has the complete practical tuple of all-year stability,
accepted paper/live/broker execution feedback, validated market-data provenance,
and canonical same-tree practical closure.

Next repair direction: do not launch downstream from the current OTE
calendar-guard root. Either repair the OTE 2022 regime slice without loosening
cost/density/session gates, or pivot to a different ETH/full-session candidate
that already satisfies cost, density, and year stability before spending
downstream lifecycle runtime.

## 2026-05-31 13:28 +0800 Fixed-Hold OTE Readback

Fresh compact audit before this slice was blocked by a foreign live runtime:

- run root:
  `/tmp/ict-engine-vhf-chop-trend-reacceleration-exact-aqprep-20260531T132517+0800`
- live PIDs at focused process scan: `14772`, `17236`
- compact audit:
  `status=needs_attention`, `active_claims=1`, `live_factor_processes=1`,
  `promotion_allowed_true=0`, `trade_usable_true=0`,
  `same_tree_practical_closure=null`

So no provider/AQ/IBKR/paper/live/downstream lifecycle was launched by this
continuation. Non-colliding verification was completed:

- `python3 -m py_compile
  support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_eth_trend_ote_reacceleration_exact_aqprep_v1.py`
  passed
- `python3
  support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_eth_trend_ote_reacceleration_exact_aqprep_v1.py
  -v` passed `12` tests, including the
  `--fixed-hold-only-exit` identity and exit-signal-disable contracts
- `python3
  support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_eth_trend_ote_reacceleration_downstream_prep_v1.py
  -v` passed `8` tests

The current strongest OTE repair is the fixed-hold-only exact-AQ root:

- run root:
  `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-calendar-fixedhold-exact-aqlaunch-20260531T131548+0800`
- compact root:
  `support/docs/experiments/actionable-regime-confidence/runs/20260531T131548+0800-codex-tomac-eth-trend-ote-reacceleration-calendar-fixedhold-exact-aqlaunch-v2`
- factor_id:
  `tomac_nq_15m_eth_trend_ote_reacceleration_long_qualityreclaim_calendar_fixedhold_exact_aq_v1`
- exact-AQ raw: `1721` trades, raw `+90.58%`, PF `1.2324`
- verified NQ fee-only instrument-cost readback:
  `+66.160966%`, PF `1.218802`
- fee-plus-assumed-slippage readback:
  `+58.224443%`, PF `1.190216`
- trades_per_session: `1.106752`
- chronological thirds fee-only:
  `21.882371 / 23.221998 / 21.056597`
- year fee-only totals:
  `2021=13.679586`, `2022=1.973768`, `2023=22.622629`,
  `2024=9.495287`, `2025=18.389696`
- years_fee_only_positive: `5/5`
- instrument-cost decision:
  `exact_aq_cost_year_stable_needs_downstream_and_accepted_feedback`

This repairs the prior OTE 2022 failure without relaxing cost, density, or ETH
session scope, but it is still not a practical factor. Current hard blockers:

- Freqtrade still reports `48.30%` missing-data fillup on the synthetic NQ
  futures feed, so practical market-data provenance is blocked.
- The trade export is simulated exact-AQ backtest evidence, not accepted
  paper/live/broker execution feedback.
- No downstream lifecycle was launched in this blocked runtime window.
- No canonical same-tree practical closure packet exists.

Downstream prep was written as a no-launch, fail-closed packet only:

- root:
  `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-calendar-fixedhold-downstream-prep-20260531T132645+0800`
- compact root:
  `support/docs/experiments/actionable-regime-confidence/runs/20260531T132645+0800-codex-tomac-eth-trend-ote-reacceleration-calendar-fixedhold-downstream-prep-v1`
- status: `simulated_feedback_downstream_prep_fail_closed`
- rejected simulated/backtest feedback rows: `1721`
- feedback source:
  `auto_quant_real_trades:simulated_backtest:tomac_nq_15m_eth_trend_ote_reacceleration_long_qualityreclaim_calendar_fixedhold_exact_aq_v1`
- broker_fill_evidence_rows: `0`
- broker_realized_feedback_rows: `0`
- practical flags:
  `accepted_execution_feedback=false`, `promotion_allowed=false`,
  `trade_usable=false`, `update_goal=false`,
  `same_tree_practical_closure=null`

Next legal step after same-turn compact audit and focused process scan both
clear: run accepted paper/broker feedback readback and then a real downstream
lifecycle replay for the fixed-hold root. Do not call it `trade_usable=true`
unless market-data provenance, accepted execution feedback, lifecycle tuple,
and canonical same-tree practical closure all pass from the same rooted branch.

## 2026-05-31 13:26 +0800 Fixed-Hold OTE Repair Readback

Fresh hard count remains zero:

- `promotion_allowed_true=0`
- `trade_usable_true=0`
- `same_tree_practical_closure=null`

Root cause refinement:

- The 12:57 OTE calendar-guard exact-AQ failed because 2022 stayed negative
  after verified NQ instrument-cost readback.
- `year_2022_failure_attribution.json` showed the damage came from the
  `exit_signal` path: 2022 `exit_signal` trades were `-96.357504%` fee-only,
  while `fixed_hold_18_bars` trades were `+88.388427%` fee-only.
- First fixed-hold launch exposed a wrapper bug: setting
  `use_exit_signal=false` also disabled Freqtrade `custom_exit`, so positions
  held until stoploss/force_exit and produced only `5` trades. That root is
  invalid as factor evidence and is retained only as implementation-bug
  evidence:
  `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-calendar-fixedhold-exact-aqlaunch-20260531T131051+0800`.

Wrapper repair:

- file:
  `support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_eth_trend_ote_reacceleration_exact_aqprep_v1.py`
- test:
  `support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_eth_trend_ote_reacceleration_exact_aqprep_v1.py`
- fix: add `--fixed-hold-only-exit`; keep Freqtrade
  `use_exit_signal=true` so `custom_exit` runs, but omit the trend-break
  `exit_raw` block for fixed-hold variants.
- verification:
  `python3 -m py_compile ...` passed.
- verification:
  `python3 support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_eth_trend_ote_reacceleration_exact_aqprep_v1.py -v`
  passed `12` tests.

Valid fixed-hold exact-AQ root:

- root:
  `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-calendar-fixedhold-exact-aqlaunch-20260531T131548+0800`
- compact root:
  `support/docs/experiments/actionable-regime-confidence/runs/20260531T131548+0800-codex-tomac-eth-trend-ote-reacceleration-calendar-fixedhold-exact-aqlaunch-v2`
- factor_id:
  `tomac_nq_15m_eth_trend_ote_reacceleration_long_qualityreclaim_calendar_fixedhold_exact_aq_v1`
- exact-AQ result: `exit=0`, `trade_count=1721`, raw total `90.58%`,
  raw PF `1.2324`, max drawdown `16.55%`
- Freqtrade missing-data fillup warning remains present: `48.30%`.
- fixed-hold semantics verified from trade export:
  `exit_reason_counts={"fixed_hold_18_bars": 1721}`,
  `min_trade_duration_minutes=270`, `max_trade_duration_minutes=270`.

Post-run verified NQ instrument-cost readback:

- readback:
  `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-calendar-fixedhold-exact-aqlaunch-20260531T131548+0800/checks/exact_aq_instrument_cost_readback.json`
- compact copy:
  `support/docs/experiments/actionable-regime-confidence/runs/20260531T131548+0800-codex-tomac-eth-trend-ote-reacceleration-calendar-fixedhold-exact-aqlaunch-v2/checks/exact_aq_instrument_cost_readback.json`
- fee-plus-assumed-slippage total: `58.224443%`
- fee-plus-assumed-slippage PF: `1.190216`
- chronological thirds fee-plus-assumed-slippage:
  `18.818906 / 20.219373 / 19.186165`
- years fee-plus-assumed-slippage:
  `2021=11.800932`, `2022=0.030506`, `2023=20.770078`,
  `2024=8.205313`, `2025=17.417615`
- decision:
  `exact_aq_cost_survivor_needs_downstream_and_accepted_feedback`
- `downstream_allowed=true` for no-launch prep / next lifecycle only.
- practical flags remain `promotion_allowed=false`, `trade_usable=false`,
  `update_goal=false`, `same_tree_practical_closure=null`.

Downstream no-launch prep from the fixed-hold export:

- root:
  `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-calendar-fixedhold-downstream-prep-20260531T132514+0800`
- compact root:
  `support/docs/experiments/actionable-regime-confidence/runs/20260531T132514+0800-codex-tomac-eth-trend-ote-reacceleration-calendar-fixedhold-downstream-prep-v1`
- status: `simulated_feedback_downstream_prep_fail_closed`
- rejected simulated/backtest feedback rows: `1721`
- practical flags remain `promotion_allowed=false`, `trade_usable=false`,
  `update_goal=false`.

Current blocker after this repair:

- compact audit at 13:26 returned `status=needs_attention`.
- live runtime owner:
  `/tmp/ict-engine-vhf-chop-trend-reacceleration-exact-aqprep-20260531T132517+0800`
  with `process_count=2`.
- fresh active claim without live process:
  `20260531T132450+0800-codex-medrv-minrv-30m-stabletrend-exact-aq.claim`.
- Do not run IBKR accepted-feedback readback or downstream lifecycle runtime
  until a fresh compact audit and focused process scan are clear.

13:34 guard cleared again:

- compact audit: `status=pass`, `active_claims=0`,
  `live_factor_processes=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, `same_tree_practical_closure=null`.

Fixed-hold OTE accepted-feedback readback:

- root:
  `/tmp/ict-engine-ote-fixedhold-accepted-feedback-readback-20260531T133442+0800`
- IBKR readback:
  `readonly=true`, `port=4002`, `raw_execution_rows_total=0`,
  `rows_after_local_filters=0`, `execution_rows_total=0`,
  `rows_with_commission_report=0`.
- accepted conversion:
  `status=no_accepted_execution_feedback_rows`,
  `accepted_feedback_rows=0`,
  `accepted_execution_feedback_ready=false`,
  `broker_fill_evidence_rows=0`, `broker_realized_rows=0`,
  `terminal_decision=accepted_execution_feedback_missing`.

13:36 final compact audit stayed clear but still zero practical:

- compact audit: `status=pass`, `active_claims=0`,
  `live_factor_processes=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, `same_tree_practical_closure=null`.

13:38 verification refresh found a new foreign runtime after the accepted
feedback readback:

- compact audit: `status=needs_attention`
- live runtime root:
  `/tmp/ict-engine-rsrs-high-low-regression-trend-admission-local-screen-20260531T131755+0800`
- PID: `32378`
- active_claims: `0`
- promotion_allowed_true: `0`
- trade_usable_true: `0`
- same_tree_practical_closure: `null`
- next action: wait for that local-screen runtime to exit before launching more
  AQ/provider/IBKR/downstream work.

13:39 final refresh cleared the transient runtime:

- compact audit: `status=pass`, `active_claims=0`,
  `live_factor_processes=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, `same_tree_practical_closure=null`.

Hard answer is still no practical factor. The fixed-hold OTE repair is now the
closest current candidate because it has ETH/full-session coverage,
cost-surviving exact-AQ economics, density, all-positive chronological thirds,
and all-positive years after verified NQ cost. It is still not trade-usable
because current IBKR paper/broker readback has zero accepted execution rows,
canonical same-tree practical closure is missing, and the Freqtrade `48.30%`
missing-data fillup warning remains unresolved.

## 2026-05-31 13:28 +0800 Fixedhold Repair Candidate

The OTE 2022 blocker was narrowed to the early exit path. Exact-AQ trade-export
readback for the calendar-guard root showed `exit_signal` rows were negative
while fixed-hold exits carried the edge, including in 2022. A fixedhold child
was already launched by a sibling runtime and read back locally without starting
new AQ/IBKR/provider work in this slice.

Best fixedhold exact-AQ root:

- `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-calendar-fixedhold-exact-aqlaunch-20260531T131548+0800`
- compact root:
  `support/docs/experiments/actionable-regime-confidence/runs/20260531T131548+0800-codex-tomac-eth-trend-ote-reacceleration-calendar-fixedhold-exact-aqlaunch-v2`
- factor_id:
  `tomac_nq_15m_eth_trend_ote_reacceleration_long_qualityreclaim_calendar_fixedhold_exact_aq_v1`
- exact-AQ result: `trade_count=1721`, raw Freqtrade total `90.58%`,
  raw PF `1.23`, max drawdown `16.55%`
- terminal practical flags remained false:
  `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`,
  `same_tree_practical_closure=null`
- Earlier fixedhold root
  `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-calendar-fixedhold-exact-aqlaunch-20260531T131051+0800`
  had stale strategy source behavior (`use_exit_signal=false`) and only `5`
  trades with multi-hundred-day holds. Treat the `13:15:48` v2 root above as
  the valid fixedhold readback because it preserved `use_exit_signal=true`,
  `use_custom_exit=true`, disabled `exit_long`, and used custom fixed
  `18`-bar exits as covered by the wrapper tests.

Fresh local instrument-cost readback added:

- `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-calendar-fixedhold-exact-aqlaunch-20260531T131548+0800/checks/exact_aq_instrument_cost_readback.json`
- compact copy:
  `support/docs/experiments/actionable-regime-confidence/runs/20260531T131548+0800-codex-tomac-eth-trend-ote-reacceleration-calendar-fixedhold-exact-aqlaunch-v2/checks/exact_aq_instrument_cost_readback.json`
- trade_count: `1721`
- trades_per_session: `1.106752`
- gross_total_profit_pct: `68.541922`
- fee_only_instrument_cost_total_profit_pct: `66.160966`
- fee_only_instrument_cost_profit_factor: `1.218802`
- chronological_thirds_fee_only_pct:
  `21.882371 / 23.221998 / 21.056597`
- year_fee_only_total_profit_pct:
  `2021=13.679586`, `2022=1.973768`, `2023=22.622629`,
  `2024=9.495287`, `2025=18.389696`
- years_fee_only_positive: `5/5`
- decision:
  `exact_aq_cost_year_stable_needs_downstream_and_accepted_feedback`

This repairs the previous OTE economics/year-stability blocker without relaxing
session, cost, density, or PF gates. It is now the best known candidate for the
next practical chain attempt, but it is still not trade-usable.

No-launch downstream prep was written from the fixedhold exact-AQ export:

- root:
  `/tmp/ict-engine-tomac-eth-trend-ote-reacceleration-calendar-fixedhold-downstream-prep-20260531T132603+0800`
- compact root:
  `support/docs/experiments/actionable-regime-confidence/runs/20260531T132603+0800-codex-tomac-eth-trend-ote-reacceleration-calendar-fixedhold-downstream-prep-v1`
- claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T132603+0800-codex-tomac-eth-trend-ote-fixedhold-downstream-prep.claim`
- status: `simulated_feedback_downstream_prep_fail_closed`
- decision:
  `no_launch_simulated_backtest_feedback_not_practical_execution_feedback`
- rejected feedback rows: `1721`
- feedback source:
  `auto_quant_real_trades:simulated_backtest:tomac_nq_15m_eth_trend_ote_reacceleration_long_qualityreclaim_calendar_fixedhold_exact_aq_v1`
- broker_fill_evidence_rows: `0`
- broker_realized_feedback_rows: `0`
- market_data_provenance.status: `blocked_for_practical_promotion`
- return_sanity blocker:
  `blocked_missing_data_fillup_warning` with `missing_data_fillup_pct=48.3`
- practical flags: `promotion_allowed=false`, `trade_usable=false`,
  `update_goal=false`, `same_tree_practical_closure=null`

Current live blocker:

- compact audit after the fixedhold readback first reported a live MedRV/MinRV
  NQ 1h exact-AQ owner:
  `/tmp/ict-engine-medrv-minrv-1h-stabletrend-exact-aqlaunch-20260531T131918+0800`.
  A later refresh showed that owner terminalized and a new live VHF/CHOP NQ
  exact-AQ owner took the slot:
  `/tmp/ict-engine-vhf-chop-trend-reacceleration-exact-aqprep-20260531T132517+0800`
- `live_factor_processes=1`, `active_claims=1`,
  `promotion_allowed_true=0`, `trade_usable_true=0`,
  `same_tree_practical_closure=null`

Do not launch fixedhold downstream lifecycle, IBKR readback, paper/sim, or
provider work until the MedRV/MinRV runtime terminalizes and a same-turn compact
audit plus focused process scan both clear. The next legal heavy step is to
run the fixedhold same-root practical lifecycle only if accepted paper/live/
broker execution feedback can be provided or acquired without relabeling
simulated backtest rows.

After the live factor runtime cleared, a fixedhold accepted-feedback readback
was run read-only against IBKR paper gateway:

- root:
  `/tmp/ict-engine-ote-fixedhold-accepted-feedback-readback-20260531T133630+0800`
- readback:
  `/tmp/ict-engine-ote-fixedhold-accepted-feedback-readback-20260531T133630+0800/checks/ibkr_execution_readback.json`
- conversion:
  `/tmp/ict-engine-ote-fixedhold-accepted-feedback-readback-20260531T133630+0800/summaries/accepted_feedback_summary.json`
- IBKR result: auto-selected paper port `4002`, `readonly=true`,
  `raw_execution_rows_total=0`, `rows_after_local_filters=0`,
  `execution_rows_total=0`, `rows_with_commission_report=0`
- accepted conversion result:
  `status=no_accepted_execution_feedback_rows`,
  `accepted_feedback_rows=0`,
  `accepted_execution_feedback_ready=false`,
  `broker_fill_evidence_rows=0`,
  `broker_realized_rows=0`,
  `terminal_decision=accepted_execution_feedback_missing`

This is now the precise blocker for fixedhold practicalization: economics,
density, session scope, and year stability are repaired, but there is no
accepted paper/live/broker execution row to feed the same-tree lifecycle.
Do not fabricate that row from exact-AQ or simulated feedback.

Final same-turn guard readback after the IBKR readback:

- compact audit status: `needs_attention`
- live runtime root:
  `/tmp/ict-engine-rsrs-high-low-regression-trend-admission-local-screen-20260531T131755+0800`
- `live_factor_processes=1`, `active_claims=0`
- `promotion_allowed_true=0`, `trade_usable_true=0`,
  `same_tree_practical_closure=null`

Do not start another fixedhold lifecycle / provider / IBKR / AutoQuant command
until this RSRS local-screen owner exits and the compact audit returns `pass`
again.

Focused verification after this update:

- `python3 -m py_compile ...run_tomac_eth_trend_ote_reacceleration_exact_aqprep_v1.py ...test_tomac_eth_trend_ote_reacceleration_exact_aqprep_v1.py ...run_tomac_eth_trend_ote_reacceleration_downstream_prep_v1.py ...test_tomac_eth_trend_ote_reacceleration_downstream_prep_v1.py`
  passed.
- `python3 support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_eth_trend_ote_reacceleration_exact_aqprep_v1.py -v`
  passed `12` tests.
- `python3 support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_eth_trend_ote_reacceleration_downstream_prep_v1.py -v`
  passed `8` tests.
- `git diff --check -- <OTE wrapper/test/downstream/doc slice>` passed.

## 2026-05-31 14:40 +0800 OTE Accepted-Feedback Guard Repair

Current hard count remains unchanged:

- compact audit:
  `status=pass`, `active_claims=0`, `live_factor_processes=0`,
  `promotion_allowed_true=0`, `trade_usable_true=0`,
  `same_tree_practical_closure=null`
- objective snapshot:
  `/tmp/ict-engine-ote-fixedhold-accepted-feedback-repair-20260531T135232+0800/objective_snapshot_after_guard/objective_closure_snapshot.json`
  returned `completion_proven=false` and
  `same_tree_practical_closure_unproven`

Fixed OTE downstream wrapper behavior:

- files:
  `support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_eth_trend_ote_reacceleration_downstream_prep_v1.py`
  and
  `support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_eth_trend_ote_reacceleration_downstream_prep_v1.py`
- new guard behavior:
  - compact claim audit must pass before driver execution
  - accepted feedback file must have rows
  - accepted source must be delimiter-bound paper/live/broker execution feedback
  - every row must have `broker_realized=true` and `broker_fill_evidence=true`
  - otherwise provider/downstream launch is refused and practical flags stay false

Real fixedhold guard run:

- root:
  `/tmp/ict-engine-ote-fixedhold-accepted-feedback-repair-20260531T135232+0800/downstream_guard`
- command result:
  wrapper exited `4`
- terminal:
  `downstream_guard/checks/terminal_metrics.json`
- status:
  `accepted_execution_feedback_missing`
- accepted feedback:
  `rows=0`, blocker `accepted feedback file has zero rows`
- launch:
  `provider_or_downstream_launched=false`, `command_results=[]`
- flags:
  `promotion_allowed=false`, `trade_usable=false`,
  `same_tree_practical_closure=null`

Terminalized the active `/tmp` repair packet:

- workdoc:
  `/tmp/ict-engine-ote-fixedhold-accepted-feedback-repair-20260531T135232+0800/workdoc.md`
- claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T135232+0800-codex-ote-fixedhold-accepted-feedback-repair.claim`
- terminal decision:
  `accepted_execution_feedback_missing`

Verification:

- RED observed:
  `test_execute_driver_*` failed because the OTE wrapper had no
  `load_claim_audit` / driver guard surface.
- GREEN:
  `python3 support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_eth_trend_ote_reacceleration_downstream_prep_v1.py -v`
  passed `13` tests.
- Guard regression:
  `python3 -m unittest support.scripts.research.tests.test_real_trade_feedback_labels support.scripts.research.tests.test_same_tree_practical_closure -v`
  passed `36` tests.
- Syntax:
  `python3 -m py_compile` passed for the OTE wrapper and test.

Precise root cause after this slice:

The strongest known OTE fixedhold candidate has repaired economics, cost,
density, session, and year-stability evidence, but it still has no accepted
paper/live/broker execution feedback. The current IBKR paper account readback
has zero paired execution+commission rows, so the same-tree lifecycle cannot
legitimately produce `trade_usable=true`. No code path may fill that gap with
exact-AQ/Freqtrade backtest rows.

## 2026-05-31 15:07 +0800 Paper-Feedback Producer Repair

Hard count remains unchanged:

- `promotion_allowed_true=0`
- `trade_usable_true=0`
- `same_tree_practical_closure=null`

New repair completed:

- added `support/scripts/research/ibkr_paper_roundtrip_smoke.py`
- added `support/scripts/research/tests/test_ibkr_paper_roundtrip_smoke.py`
- updated `support/scripts/SCRIPTS.md`
- updated `support/scripts/script_manifest.json`
- fixed `support/scripts/research/same_tree_practical_closure.py` so
  unstructured prose alone cannot prove retained non-RTH/session coverage.

Why this was needed:

- repo had a read-only IBKR execution readback and converter, but no guarded
  paper-only execution producer.
- without an actual paper/live/broker execution roundtrip, accepted feedback
  stays empty and `trade_usable=true` cannot be legally produced.

Safety / tests:

- paper bridge default is dry-run and never places orders.
- live ports `7496/4001` are rejected.
- non-DU/DF accounts are rejected.
- execution requires `--execute-paper-roundtrip`,
  `--i-understand-paper-orders`, and an exact futures contract.
- every bridge terminal packet keeps `promotion_allowed=false`,
  `trade_usable=false`, `update_goal=false`, and
  `same_tree_practical_closure=null`.

Verification:

```bash
python3 -m unittest support.scripts.research.tests.test_ibkr_paper_roundtrip_smoke -v
python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure -v
python3 -m unittest support.scripts.research.tests.test_ibkr_paper_roundtrip_smoke support.scripts.research.tests.test_ibkr_execution_readback support.scripts.research.tests.test_real_trade_feedback_labels -v
python3 support/scripts/check_script_manifest.py
python3 -m py_compile support/scripts/research/ibkr_paper_roundtrip_smoke.py support/scripts/research/same_tree_practical_closure.py support/scripts/research/tests/test_ibkr_paper_roundtrip_smoke.py support/scripts/research/tests/test_same_tree_practical_closure.py
```

All passed.

Runtime evidence:

- dry-run packet:
  `/tmp/ict-engine-ote-fixedhold-paper-feedback-practicalization-20260531T144910+0800/paper_bridge_dry_run/checks/terminal_metrics.json`
- connect preflight:
  `/tmp/ict-engine-ote-fixedhold-paper-feedback-practicalization-20260531T144910+0800/paper_bridge_connect_preflight/checks/terminal_metrics.json`
- result: connected to IBKR paper account `DUN189136`; no order placed.

Protected NQM6 paper attempt:

- root:
  `/tmp/ict-engine-ote-fixedhold-paper-feedback-practicalization-20260531T144910+0800/paper_roundtrip_attempt_NQM6`
- contract qualified as `NQM6`, `conId=750150196`, expiry `20260618`.
- IBKR warned the order would not reach the exchange until
  `2026-05-31 17:00:00 US/Central`.
- terminal status: `paper_entry_not_filled`.
- cancel/open-order audit:
  `/tmp/ict-engine-ote-fixedhold-paper-feedback-practicalization-20260531T144910+0800/checks/paper_order_cancel_audit.json`
  returned `matched_after_cancel=[]` and `nq_positions=[]`.

Post-attempt accepted-feedback readback:

- readback:
  `/tmp/ict-engine-ote-fixedhold-paper-feedback-practicalization-20260531T144910+0800/post_paper_attempt_readback/checks/ibkr_execution_readback.json`
- conversion:
  `/tmp/ict-engine-ote-fixedhold-paper-feedback-practicalization-20260531T144910+0800/post_paper_attempt_readback/summaries/accepted_feedback_summary.json`
- result: `execution_rows_total=0`, `accepted_feedback_rows=0`,
  `accepted_execution_feedback_ready=false`,
  `terminal_decision=accepted_execution_feedback_missing`.

Terminal decision:

- status: `terminalized_market_closed_no_accepted_execution_feedback`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

Final objective snapshot:

- `/tmp/ict-engine-ote-fixedhold-paper-feedback-practicalization-20260531T144910+0800/objective_snapshot_after_paper_bridge/objective_closure_snapshot.json`
- `completion_proven=false`
- `same_tree_practical_closure_unproven`
- factor closure child audit: `status=pass`, `active_claims=0`,
  `live_factor_processes=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, `same_tree_practical_closure=null`

Next legal practicalization step is time/execution dependent, not compute
dependent: when NQ paper trading is open, run the guarded paper-only roundtrip
again, convert the resulting `reqExecutions` readback, and only then run the
fixedhold downstream practical lifecycle. If the accepted-feedback JSONL is
still empty or lacks broker fill evidence, stop fail-closed again.

## 2026-05-31 15:42 +0800 Same-Turn Paper Retry

Current compact guard before the retry cleared:

- `status=pass`
- `active_claims=0`
- `live_factor_processes=0`
- `promotion_allowed_true=0`
- `trade_usable_true=0`
- `same_tree_practical_closure=null`

Continuation workdoc and claim:

- workdoc:
  `/tmp/ict-engine-ote-fixedhold-paper-feedback-continuation-20260531T153500+0800/workdoc.md`
- claim:
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T153500+0800-codex-ote-fixedhold-paper-feedback-continuation.claim`

Read-only paper preflight and execution readback:

- connect packet:
  `/tmp/ict-engine-ote-fixedhold-paper-feedback-continuation-20260531T153500+0800/connect_preflight/checks/terminal_metrics.json`
- result: IBKR paper port `4002` connected to paper account `DUN189136`; no
  order placed.
- pre-retry readback:
  `/tmp/ict-engine-ote-fixedhold-paper-feedback-continuation-20260531T153500+0800/accepted_feedback_readback/checks/ibkr_execution_readback.json`
- pre-retry conversion:
  `/tmp/ict-engine-ote-fixedhold-paper-feedback-continuation-20260531T153500+0800/accepted_feedback_readback/summaries/accepted_feedback_summary.json`
- result: `execution_rows_total=0`, `accepted_feedback_rows=0`,
  `terminal_decision=accepted_execution_feedback_missing`.

Protected paper-only NQM6 retry:

- command shape: paper port `4002`, exact local symbol `NQM6`, `quantity=1`,
  `tif=IOC`, explicit paper-order confirmation.
- root:
  `/tmp/ict-engine-ote-fixedhold-paper-feedback-continuation-20260531T153500+0800/paper_roundtrip_retry_NQM6`
- result: `status=paper_entry_not_filled`, exit `4`.
- IBKR warning: the order will not reach the exchange until
  `2026-05-31 17:00:00 US/Central`.

Safety readback after retry:

- open-order/position audit:
  `/tmp/ict-engine-ote-fixedhold-paper-feedback-continuation-20260531T153500+0800/checks/paper_order_cancel_audit.json`
- result: `matched_before_cancel=0`, `matched_after_cancel=[]`,
  `nq_positions=[]`.
- post-retry readback:
  `/tmp/ict-engine-ote-fixedhold-paper-feedback-continuation-20260531T153500+0800/post_paper_retry_readback/checks/ibkr_execution_readback.json`
- post-retry conversion:
  `/tmp/ict-engine-ote-fixedhold-paper-feedback-continuation-20260531T153500+0800/post_paper_retry_readback/summaries/accepted_feedback_summary.json`
- result: `execution_rows_total=0`, `accepted_feedback_rows=0`,
  `broker_fill_evidence_rows=0`, `broker_realized_rows=0`,
  `terminal_decision=accepted_execution_feedback_missing`.

Terminal decision stays unchanged:

- `status=terminalized_market_closed_no_accepted_execution_feedback`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
- `same_tree_practical_closure=null`

This confirms the root cause with current evidence: the closest fixedhold OTE
candidate is blocked by accepted paper/live/broker execution feedback, and this
specific block is wall-clock/exchange-session dependent, not compute-dependent.
Do not launch downstream practical lifecycle from this root.
