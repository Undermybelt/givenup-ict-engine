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
