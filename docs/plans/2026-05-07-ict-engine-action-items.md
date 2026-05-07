# ICT-Engine 应做事项 — 2026-05-07

> 综合因子迭代与运行时闭环两条线，基于当前进展提取的下一步行动清单。

---

## 核心流水线（必须理解并执行）

**因子迭代 → 滤波 → BBN 证据 → CatBoost → 执行树**

```
┌─────────────────┐
│   因子迭代       │  ← Auto-Quant / 外部因子库
│  (Factor Iter)  │  ← 论文 / 开源仓库借用
└────────┬────────┘
         ▼
┌─────────────────┐
│    滤波节点      │  ← regime_filter.rs
│  (Filter Node)  │  ← HMM / 变点 / 波动率状态
└────────┬────────┘
         ▼
┌─────────────────┐
│   BBN 证据节点   │  ← bbn/evidence.rs
│  (Evidence)     │  ← qqq_hv / nq_vs_200d / vix3m / vvix_over_vix
└────────┬────────┘
         ▼
┌─────────────────┐
│   CatBoost      │  ← policy-training
│  (Path Ranking) │  ← structural_path_ranking
└────────┬────────┘
         ▼
┌─────────────────┐
│    执行树节点    │  ← execution_tree.rs
│  (Exec Tree)    │  ← block_crowded / wait_for_reversion / fill_viable
└─────────────────┘
```

**迭代不理想时的应对**：
- 去论文库（arXiv / SSRN / 期刊）找相关因子/滤波/分类器设计
- 去 GitHub 找开源仓库，挪用经过验证的实现
- 不要闭门造车；站在已有研究肩膀上

---

## 多维度覆盖要求（强制性）

### 多品种

每次因子迭代必须覆盖：
- 指数期货：NQ, ES, YM, RTY
- ETF 代理：SPY, QQQ, IWM, DIA
- 商品/金属：GC, CL, XAU
- 外汇：EUR, GBP, JPY
- 个股：AAPL, MSFT, NVDA, TSLA
- 加密：BTC/USDT, ETH/USDT, SOL/USDT, BNB/USDT, AVAX/USDT

### 多市场

跨市场验证必须包含至少 3 个不同市场类别：
- 美股指数
- 商品
- 外汇
- 加密

### 多时间周期

完整周期阶梯：
- `1m` → `5m` → `15m` → `1h` → `4h` → `1d` → `1w` → `1M`

每个因子必须声明：
- 基础执行周期
- 上下文共振栈
- 共振结果：aligned / contradicted / neutral / missing

### 多共振

低周期触发必须检查高周期共振：
- `1m` base: check `5m`, `15m`, `1h`, `4h`
- `5m` base: check `15m`, `1h`, `4h`, `1d`
- `15m` base: check `1h`, `4h`, `1d`
- `1h` base: check `4h`, `1d`, `1w`
- `4h` base: check `1d`, `1w`, `1M`
- `1d` base: check `1w`, `1M`

---

## 市场形态现状与扩展需求

### 当前仓库已有形态

**大类 (Envelope)**：
```rust
MarketRegimeEnvelope:
  - Expansion      // 扩展
  - Pullback       // 回调
  - ReversalAttempt // 反转尝试
  - Consolidation  // 整理
```

**子类 (Class + FootprintChainRegime)**：
```rust
MarketRegimeClass:
  - Continuation        // 延续
  - CountertrendPullback // 逆势回调
  - Reversal           // 反转
  - Consolidation      // 整理

FootprintChainRegime:
  - BullExpansionSecondLeg
  - BullExpansionToBearExpansion
  - BearExpansionToBullExpansion
  - BearExpansionSecondLeg
  - FailedBullExpansion
  - FailedBearExpansion
  - RangeLiquidityReversion
```

**分割状态**：
```rust
SegmentedRegimeState:
  - BearishExpansion
  - BullishExpansion
  - Consolidation
```

**总结**：4 大类 + 4 子类 + 7 足迹链状态 + 3 分割状态

### 需要补充的市场形态

当前形态偏"价格方向"，缺少：

**波动率状态**：
- [ ] LowVol / NormalVol / ElevatedVol / CrisisVol
- [ ] Vol Clustering / Vol Mean-Reversion
- [ ] Vol Term-Structure (Contango / Backwardation)

**流动性状态**：
- [ ] HighLiquidity / NormalLiquidity / ThinLiquidity
- [ ] Session-based: Killzone / Off-hours / Transition

**市场结构状态**：
- [ ] Trending / Mean-Reverting / Ranging
- [ ] Breakout / Breakdown / Continuation
- [ ] Accumulation / Markup / Distribution / Markdown (Wyckoff)

**投资者行为状态**：
- [ ] Crowding / Exhaustion / FOMO / Capitulation
- [ ] Risk-On / Risk-Off / Neutral

**论文/开源来源**：
- [ ] 搜索 "market regime classification" + "hidden markov model"
- [ ] 搜索 "volatility regime" + "change point detection"
- [ ] 搜索 "liquidity regime" + "market microstructure"
- [ ] 搜索 "Wyckoff cycle" + "phase detection"
- [ ] GitHub: `regime-detection`, `market-state-classifier`, `volatility-clustering`

---

## 已完成里程碑

### 市场状态分类模块 (2026-05-07 新增)

- `src/market_state/mod.rs` — 聚合分类器
- `src/market_state/volatility.rs` — 波动率状态分类器
- `src/market_state/liquidity.rs` — 流动性状态分类器
- `src/market_state/structure.rs` — 市场结构状态分类器
- `src/market_state/behavior.rs` — 投资者行为状态分类器
- `src/market_state/config.rs` — 热插拔配置
- `src/market_state/filter.rs` — 市场状态滤波器（2026-05-07 新增）

**特性**：
- 零配置：默认参数直接可用
- 热插拔：通过 `MarketStateConfig` 覆盖阈值
- Token 友好：简洁输出
- 无污染：不修改现有代码
- 高置信度：基于统计学阈值

**主大类**：
```rust
PrimaryMarketRegime:
  - TrendExpansion      // 趋势扩展
  - RangeConsolidation  // 震荡整理
  - ExtremeStress       // 极端状态
  - ReversalBrewing     // 反转酝酿
```

**次小类**：
```rust
SecondaryMarketRegime:
  - BullTrendAcceleration / BearTrendAcceleration
  - BullTrendExhaustion / BearTrendExhaustion
  - TightRange / WideRange
  - Accumulation / Distribution
  - VolatilitySpike / LiquidityCrunch
  - PanicSelling / PanicBuying
  - TrendFatigue / SentimentExtreme
```

**维度分类器**：
- 波动率：LowVol / NormalVol / ElevatedVol / CrisisVol
- 流动性：HighLiquidity / NormalLiquidity / ThinLiquidity
- 结构：Trending / MeanReverting / Ranging / Accumulation / Distribution
- 行为：Crowding / Exhaustion / FOMO / Capitulation / RiskOn / RiskOff

**滤波器特性**：
- `MarketStateFilter`：基于市场状态的交易许可判断
- `FactorFilterDeclaration`：因子声明允许进入的滤波状态
- 自动阻断：危机波动率 / 流动性枯竭 / 投资者投降 / 极端状态
- 仓位调整：FOMO 降仓 30%，高波动降仓 15%
- 状态变更检测：主大类 / 波动率 / 流动性变更事件

**用法**：
```rust
use ict_engine::market_state::{MarketStateClassifier, MarketStateConfig, MarketStateFilter};

// 零配置
let classifier = MarketStateClassifier::new();
let snapshot = classifier.classify(&candles);

// 热插拔配置
let config = MarketStateConfig::load(Path::new("market_state_config.json"))?;
let classifier = MarketStateClassifier::with_config(config);

// 滤波器
let mut filter = MarketStateFilter::new();
let result = filter.filter(&candles);
if !result.allowed {
    println!("Blocked: {:?}", result.block_reason);
}

// 因子滤波声明
let trend_decl = FactorFilterDeclaration::trend_factor("my_trend_factor");
let is_allowed = trend_decl.is_allowed(&result);
```

### VRP V2 因子闭环 (Slice 129-130)

- VRPCompression_V2_NQ_15m：815 trades / Sharpe 3.329 / DD -3.70% (8Y)
- `auto-quant-results-import`：成功
- `auto-quant-prior-init`：CPT 更新 (win=277, loss=538)
- `auto-quant-ingest-real-trades`：815 条反馈记录已入库
- 执行树：branch=transition_guardrail, execution_score=0.580
- 状态：**已接受为可部署候选**

### CatBoost 外部训练器实现 (2026-05-07)

- `scripts/auto_quant_external/pandas_path_ranker_trainer.py` — 核心训练器
- `scripts/auto_quant_external/path_ranker_integration.py` — 一键集成脚本
- `scripts/auto_quant_external/user_weights_template.json` — 热插拔权重模板

**特性**：
- 零配置：默认行为可直接运行
- 热插拔：用户可通过 `user_weights.json` 自定义权重
- Token 友好：输出简洁
- 无污染：不修改仓库代码
- 用户特定数据：VRP V2 相关特征（qqq_hv/nq_vs_200d/vix3m/vvix_over_vix 等）
- 回退机制：当 VRP V2 特征缺失时，使用 `structural_baseline_score` 或 `current_posterior`

**已验证流程**：
```bash
# 生成 scores.csv
python scripts/auto_quant_external/pandas_path_ranker_trainer.py \
  --apply --target-csv <target.csv> --output-scores scores.csv

# 应用到运行时
./target/debug/ict-engine apply-structural-path-ranking-external-scores \
  --symbol NQ --state-dir <dir> --scores-file scores.csv

# 注册训练器
./target/debug/ict-engine register-structural-path-ranking-trainer-artifact \
  --symbol NQ --state-dir <dir> --artifact-uri file://model.json \
  --model-family catboost --score-column raw_path_score
```

### VRP V2.5 BBN 条件过滤 (Slice 121-128)

- BBN 分类器：OOS macro_F1 ~0.20（方向）至 0.25（波动率状态）
- 反直觉发现：VRP V2 边缘集中在"适度不确定"状态
- V2.5d (仅 pred_class∈{flat,down})：6Y Sharpe 5.13 / DD -1.55% (NQ 5m)
- **V2 baseline 仍是最可靠的跨状态可部署版本**

### 跨市场验证 (Slice 111-124)

- NQ / SPY / IWM / GLD：正向
- DIA：V2 可用，V2.5d 在纯牛年消失
- 结论：V2 跨市场可用；V2.5d 是条件性 sleeve

---

## 当前置顶

### ~~0. 先补市场形态（因子迭代之前）~~

**目标**：扩展市场形态覆盖，从 4 大类扩展到更丰富的状态空间

**已完成**：
- [x] 实现波动率状态分类器（LowVol/NormalVol/ElevatedVol/CrisisVol）
- [x] 实现流动性状态分类器（HighLiquidity/NormalLiquidity/ThinLiquidity）
- [x] 实现市场结构状态分类器（Trending/MeanReverting/Ranging/Accumulation/Distribution）
- [x] 实现投资者行为状态分类器（Crowding/Exhaustion/FOMO/Capitulation/RiskOn/RiskOff）
- [x] 设计主大类（TrendExpansion/RangeConsolidation/ExtremeStress/ReversalBrewing）
- [x] 设计次小类（16 个细分状态）
- [x] 创建热插拔配置模板（MarketStateConfig + Profile）

### 1. 因子迭代 → 滤波节点

**目标**：迭代因子后，必须通过滤波层

**当前状态**：
- [x] 创建 MarketStateFilter 滤波器
- [x] 创建 FactorFilterDeclaration 因子滤波声明
- [x] 实现波动率状态滤波：LowVol / ElevatedVol / CrisisVol
- [x] 实现流动性状态滤波：Killzone / Off-hours
- [x] 实现行为状态滤波：Capitulation 阻断 / FOMO 仓位调整
- [x] 实现主大类状态滤波：ExtremeStress 强制平仓

**滤波类型**：
- [x] regime_filter.rs：当前 HMM/波动率状态过滤
- [x] 波动率状态滤波：LowVol / ElevatedVol / CrisisVol
- [x] 流动性状态滤波：Killzone / Off-hours
- [ ] 多周期共振滤波：低周期与高周期一致/矛盾

**验收标准**：
- [x] 每个因子必须声明"允许进入的滤波状态"（FactorFilterDeclaration）
- [x] 滤波状态变更必须触发因子启用/禁用（MarketStateFilter.filter()）

### 2. 滤波 → BBN 证据节点

**目标**：滤波后的因子信号成为 BBN 的证据节点

**BBN 节点**：
- [ ] `qqq_hv_level`：QQQ 历史波动率水平
- [ ] `nq_vs_200d_pct`：NQ 相对 200 日均线位置
- [ ] `vix3m_level`：VIX3M 水平
- [ ] `qqq_hv_pct_rank_252`：QQQ HV 252 日百分位
- [ ] `vvix_over_vix`：VVIX/VIX 比率

**验收标准**：
- [ ] 每个因子必须映射到至少 1 个 BBN 证据节点
- [ ] BBN 后验概率更新必须可追溯

### 3. BBN → CatBoost 路径排名

**目标**：BBN 后验作为 CatBoost 输入，输出路径排名

**当前状态**：
- [x] `export-structural-path-ranking-target`：已实现
- [x] `policy-training-status`：已实现
- [x] CatBoost 外部训练器：**已实现**（2026-05-07 新增）

**已实现的外部训练器**：
- `scripts/auto_quant_external/pandas_path_ranker_trainer.py` — 核心训练器
- `scripts/auto_quant_external/path_ranker_integration.py` — 一键集成脚本
- `scripts/auto_quant_external/user_weights_template.json` — 用户可编辑权重模板（热插拔）

**特性**：
- 零配置：默认行为可直接运行
- 热插拔：用户可通过 `user_weights.json` 自定义权重
- Token 友好：输出简洁
- 无污染：不修改仓库代码
- 用户特定数据：VRP V2 相关特征（qqq_hv/nq_vs_200d/vix3m/vvix_over_vix 等）

**用法**：
```bash
# 完整流程：导出 target → 训练 → 应用
python scripts/auto_quant_external/path_ranker_integration.py \
  --state-dir /tmp/vrp-v2-runtime-closure --symbol NQ

# 训练后应用到运行时
./target/debug/ict-engine apply-structural-path-ranking-external-scores \
  --symbol NQ --state-dir /tmp/vrp-v2-runtime-closure \
  --scores-file /tmp/vrp-v2-runtime-closure/NQ/policy_training/scores.csv
```

### 4. CatBoost → 执行树节点

**目标**：CatBoost 排名成为执行树决策输入

**执行树分支**：
- `block_crowded`：拥挤阻断
- `wait_for_reversion`：等待回归
- `fill_viable`：填充可行
- `transition_guardrail`：转换护栏

**验收标准**：
- [ ] CatBoost 排名必须影响执行树分支选择
- [ ] 执行树 trace 必须包含 CatBoost 贡献记录

---

## 因子迭代顺序（市场形态补完后）

按优先级：

1. **Family A: Structure/Setup Quality** — 最高杠杆
2. **Family D: Stretch/Reversion Feasibility** — 当 `wait_for_reversion` 持续
3. **Family E: Crowding/Herding** — 当 `block_crowded` 持续
4. **Family G: Options/Dealer** — 仅当有可复用数据
5. **Family F: Spectral Rhythm** — 仅当有真实谱证据
6. **Family H: Session/Liquidity** — 当执行可行性与会话相关
7. **Family B: Directionality** — 在 A 稳定后
8. **Family C: Cross-Market** — 当配对数据可用

**迭代不理想时的应对**：
- [ ] 去 arXiv 搜索：`trading factor` + `machine learning`
- [ ] 去 GitHub 搜索：`trading strategy` + `factor library`
- [ ] 搜索：`momentum factor` / `mean reversion factor` / `volatility risk premium`
- [ ] 搜索：`ICT trading` + `smart money concepts` + `factor`

---

## 禁止事项

- [ ] 将当前 Rust 因子注册表视为最终因子宇宙
- [ ] 要求 repo 运行时代码变更才能编写新因子家族
- [ ] 将 `trade_count < 10` 视为因子证据
- [ ] 仅因回测良好而晋升制度因子（必须通过分类器指标）
- [ ] 在制度分类足够好之前选择交易因子
- [ ] 仅因独立 Sharpe 最高而晋升高相关因子
- [ ] 跳过滤波/BBN/CatBoost 直接进入执行树
- [ ] 在无重放、时间对齐数据情况下声称 IV/gamma 已验证
- [ ] 单品种单周期就声称因子有效

---

## 阻塞项

### ~~市场形态覆盖不足~~

- ~~阻塞：当前仅 4 大类，缺少波动率/流动性/结构状态~~
- ~~解决：搜索论文/开源仓库补充~~
- **已解决**（2026-05-07）：市场状态分类模块已实现，包含 4 主大类 + 16 次小类

### ~~CatBoost 外部训练器缺失~~

- ~~阻塞：路径排名需要外部训练器~~
- ~~解决：借用开源训练器或自行构建~~
- **已解决**（2026-05-07）：训练器已实现，见 `scripts/auto_quant_external/pandas_path_ranker_trainer.py`

### Provider 覆盖不完整

- 阻塞：未跨完整市场/周期矩阵预算
- 解决：先缓存/本地数据，再在预算内填充

---

## 验证清单

每次因子迭代：

- [ ] 多品种：至少 3 个市场类别
- [ ] 多周期：基础周期 + 共振栈
- [ ] 进入滤波：声明允许状态
- [ ] 进入 BBN：映射证据节点
- [ ] 进入 CatBoost：路径排名可追溯
- [ ] 进入执行树：trace 记录完整
- [ ] 迭代不理想时：已搜索论文/开源
- [ ] 交易密度桶：invalid / anecdotal / probe_only / thin / dense
- [ ] 每家族独立 `/tmp/...` 状态目录

---

## 联系文档

- 因子迭代权威 board：`docs/plans/2026-05-05-execution-tree-factor-auto-quant-todo.md`
- 因子后运行时闭环 board：`docs/plans/2026-05-07-auto-quant-post-factor-runtime-closure-todo.md`
- VRP V2 状态目录：`/tmp/vrp-v2-runtime-closure/`
- 市场形态定义：`src/factor_lab/pda_prior.rs`
- 分割状态：`src/data/regime_segmentation.rs`
