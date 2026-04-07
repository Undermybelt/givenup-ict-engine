# Agent Handoff Prompt

你现在接手维护 `/Users/thrill3r/projects-ict-engine/ict-engine`。

你的身份不是报告型顾问，而是继续推进这个项目成为一个完整闭环系统的执行 agent。你必须沿着正式链路工作，不要绕过项目内已经建立的结构化对象。

## 1. 当前主目标

当前最优先目标不是泛化市场预测，而是：

- 在 MVP 试运行阶段
- 用现有因子
- 更准确地区分 `bull expansion` / `bear expansion`
- 并把 ICT 概念里的 manipulation 正式建模为：
  `liquidity sweep -> displacement`
- 然后让这些因子正式服务：
  `PreBayesEvidenceFilter -> PreBayesEntryQualityBridge -> BBN -> analyze/analyze-live`

如果你后续继续因子迭代，必须优先服务这条链：

`expansion-sop / factor-research(expansion_manipulation) -> selected factor -> PreBayesEvidenceFilter -> PreBayesEntryQualityBridge -> BBN -> analyze/analyze-live -> artifact -> update`

## 2. 不可破坏的 guardrails

- 不要绕过 `PreBayesEvidenceFilter`
- 不要把 raw factor labels 直接塞进 BBN
- 不要把 `expansion-sop` 当成独立实验，它必须服务 `analyze` 主链
- 因子只是 evidence，不是硬触发器
- `PreBayesEvidencePolicy` 必须保持版本化，不要回到散落阈值
- `PreBayesEntryQualityBridge` 是正式桥，不要回到临时向量
- 新增结构必须进入：
  `report`
  `run ledger`
  `workflow snapshot`
  `workflow-status`
  `prompt`
  `action plan`
  `context bundle`
- 每轮改动后必须保证：
  `cargo fmt`
  `cargo check`
  `cargo test`

## 3. 当前已经完成的核心工作

### 3.1 六周期正式主链

项目现在已经不是 3-frame 临时分析器，而是正式支持：

- `1m`
- `5m`
- `15m`
- `1h`
- `4h`
- `1d`

六周期已经正式进入：

- `clean-futures`
- `futures-sop`
- `expansion-sop`
- `factor-research`
- `factor-backtest`
- `train`
- `analyze`
- `analyze-live`
- `PreBayesEvidenceFilter`
- `PreBayesEntryQualityBridge`
- `BBN entry_quality`
- `artifact`
- `artifact-diff`
- `artifact-lineage`
- `update`

不是解释层，而是正式证据层。

### 3.2 PreBayes / Bridge / Artifact / Update 闭环

已完成并正式落地的对象包括：

- `PreBayesEvidencePolicy`
- `PreBayesEvidenceFilter`
- `PreBayesEntryQualityBridge`
- `PendingUpdateArtifact`
- `ExecutionCandidateArtifact`
- `ResearchRunRecord`
- `BacktestRunRecord`
- `AnalyzeRunRecord`
- `UpdateRunRecord`
- `WorkflowSnapshot`
- `AgentPromptPack`
- `AgentActionPlan`
- `AgentContextBundle`

`update` 已能消费 analyze artifact 内嵌或回查得到的：

- pre-bayes filter
- bridge
- multi-timeframe summary

并把它们回流进 workflow snapshot / prompt / context。

### 3.3 新 session agent bootstrap

新 session agent 不需要靠 README 猜。项目内已有：

- `workflow-status --phase agent-bootstrap`
- concretized `recommended_commands`
- latest workflow snapshot
- artifact lineage / diff
- pre-bayes / bridge / six-timeframe resonance 结构化输出

## 4. 当前因子研究链的关键状态

### 4.1 `structure_ict` 已被正式增强

`structure_ict` 已不再只看：

- expansion
- BOS / latest break
- CISD
- FVG
- OB

它现在还正式加入了 ICT manipulation 相关信号：

- recent liquidity sweep
- confirmed post-sweep displacement
- unconfirmed sweep noise suppression
- opposing sweep penalty

关键代码锚点：

- [src/factor_lab/factor_definition.rs](/Users/thrill3r/projects-ict-engine/ict-engine/src/factor_lab/factor_definition.rs#L136)
- [src/factor_lab/factor_definition.rs](/Users/thrill3r/projects-ict-engine/ict-engine/src/factor_lab/factor_definition.rs#L186)
- [src/factor_lab/factor_definition.rs](/Users/thrill3r/projects-ict-engine/ict-engine/src/factor_lab/factor_definition.rs#L295)
- [src/factor_lab/factor_definition.rs](/Users/thrill3r/projects-ict-engine/ict-engine/src/factor_lab/factor_definition.rs#L427)
- [src/factor_lab/factor_definition.rs](/Users/thrill3r/projects-ict-engine/ict-engine/src/factor_lab/factor_definition.rs#L648)

### 4.2 `factor-research` 已支持正式 objective

`factor-research` 现在支持：

- `generic`
- `expansion_manipulation`

这不是临时脚本，而是正式接进了：

- report
- run ledger
- workflow snapshot
- prompt
- recommended command

关键代码锚点：

- [src/main.rs](/Users/thrill3r/projects-ict-engine/ict-engine/src/main.rs#L498)
- [src/main.rs](/Users/thrill3r/projects-ict-engine/ict-engine/src/main.rs#L9773)
- [src/main.rs](/Users/thrill3r/projects-ict-engine/ict-engine/src/main.rs#L10721)
- [src/main.rs](/Users/thrill3r/projects-ict-engine/ict-engine/src/main.rs#L7777)
- [src/factor_lab/research.rs](/Users/thrill3r/projects-ict-engine/ict-engine/src/factor_lab/research.rs#L23)
- [src/state/types.rs](/Users/thrill3r/projects-ict-engine/ict-engine/src/state/types.rs#L1085)

### 4.3 mutation 评估链已经修正

之前 mutation 评估有几个误伤点，已经修掉：

- baseline 现在按同 objective 比较
- baseline 现在按同 target factor 比较
- baseline 现在复用当前 `learning_state`
- baseline 现在也走正式 feedback / learning 路径
- `expansion_manipulation` 不再被 generic aggregate return 主导
- `observe_only` 不再被当成绝对否决，而是看相对 baseline 是否退化

关键代码锚点：

- [src/main.rs](/Users/thrill3r/projects-ict-engine/ict-engine/src/main.rs#L11282)
- [src/main.rs](/Users/thrill3r/projects-ict-engine/ict-engine/src/main.rs#L11410)
- [src/main.rs](/Users/thrill3r/projects-ict-engine/ict-engine/src/main.rs#L11575)
- [src/main.rs](/Users/thrill3r/projects-ict-engine/ict-engine/src/main.rs#L3677)

## 5. 已验证的实际结果

本机数据环境：

- TOMAC root:
  `/Users/thrill3r/Downloads/Tomac`
- cleaned multi-timeframe root:
  `/Users/thrill3r/Downloads/Tomac/ict-cleaned-mtf`
- 常用 NQ 15m 数据:
  `/Users/thrill3r/Downloads/Tomac/ict-cleaned-mtf/cleaned-15m/nq.continuous-15m.json`

### 5.1 generic vs expansion_manipulation

同一份 NQ 15m 数据上：

- `generic`:
  `best_factor = volatility_mean_reversion`
  `structure_ict ≈ 0.2675 / replace / F`
- `expansion_manipulation`:
  `best_factor = structure_ict`
  `structure_ict ≈ 0.7700 / tune / B`

说明：

- generic 目标会压掉当前真正对 bull/bear expansion 有用的因子
- `expansion_manipulation` 目标已经能把 `structure_ict` 正式提到第一名

### 5.2 当前真实结论

在公平修复后的 mutation 评估下：

- 之前的 `v2` mutation 被拒绝，不再是因为错误的 gate 绝对否决
- 它现在被拒绝的真实原因是：
  `best_factor_composite_regressed`
- 后续试的 `v4` 原子 mutation 也被公平拒绝
- 这说明当前默认 `structure_ict` 在这组目标和当前样本上已经接近局部最优

换句话说：

- 现在的系统已经能正确拒绝坏 mutation
- 不是继续“盲调参数一定会出更优”
- 下一步更需要 debug 能力和更细标签，而不是乱改 sweep 参数

## 6. 你接手后第一优先级

### P0

补一个正式的 `factor-pipeline-debug` 或等价命令，至少能对指定：

- symbol / market
- data path
- factor name
- objective

直接输出：

- latest signal
- factor diagnostics
- raw pre-bayes labels
- filtered pre-bayes labels
- evidence_quality_score
- gating_status
- soft evidence divergence
- bridge gap
- selected entry quality
- six-timeframe resonance

当前最大缺口不是“没评分”，而是缺一个一等公民的结构化 debug 入口。

### P1

把 `expansion_manipulation` 正式升成 SOP 层的一等目标，不要只停在 `factor-research`。

优先考虑：

- `futures-sop --objective expansion_manipulation`
或
- 让 `expansion-sop` 输出更强的 next-step mutation/debug command

### P2

如果还继续做 `structure_ict` 迭代：

- 不要优先再动 `lookback` / `expansion_threshold`
- 先做能解释当前 latest sample 为什么 `tune` 而不是 `keep` 的 debug
- 再决定是否需要：
  market-specific parameter fork
  或
  更细的 manipulation / expansion 标签

## 7. 明确不要做的事

- 不要为了让 mutation “被接受” 去放松正式 gate
- 不要把 `observe_only` 人工改成 pass
- 不要把 research objective 再退回 generic-only
- 不要因为 `structure_ict` 当前是第一名，就跳过 PreBayes / Bridge / BBN
- 不要一上来发明全新因子，先把现有因子的 debug / trace / mutation 链做扎实

## 8. 推荐接手命令

先确认系统仍是全绿：

```bash
cargo fmt
cargo check
cargo test
```

重跑当前正式 research 基线：

```bash
cargo run -- factor-research \
  --symbol NQ \
  --data /Users/thrill3r/Downloads/Tomac/ict-cleaned-mtf/cleaned-15m/nq.continuous-15m.json \
  --objective expansion_manipulation \
  --state-dir /tmp/ict-handoff-expansion-state
```

如果继续 mutation，对比必须仍使用 `expansion_manipulation`：

```bash
cargo run -- factor-research \
  --symbol NQ \
  --data /Users/thrill3r/Downloads/Tomac/ict-cleaned-mtf/cleaned-15m/nq.continuous-15m.json \
  --objective expansion_manipulation \
  --mutation-spec /tmp/<spec>.json \
  --emit-mutation-evaluation \
  --state-dir /tmp/ict-handoff-mutation-state
```

## 9. 我对你接手后的期望进展

理想进展不是“再试 20 个 mutation”，而是：

1. 在不破坏正式链路的前提下，补出 `factor-pipeline-debug`
2. 让 agent 能一眼看见当前 `structure_ict` latest sample 到底卡在什么证据面
3. 把 `expansion_manipulation` 升成 SOP 层正式目标
4. 给出一个明确结论：
   - 要么找到一个真正优于当前默认 `structure_ict` 的 mutation
   - 要么正式证明当前默认参数已是局部最优，并把后续工作转向标签/market fork/debug 能力

如果你只能做一件事，优先做 `factor-pipeline-debug`。

这会比继续盲调 sweep 参数更值钱。
