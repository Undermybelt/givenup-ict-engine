# 市场状态分类器参考

## 模块位置

`src/market_state/` — 独立模块，无外部依赖污染。

## 文件结构

```
src/market_state/
├── mod.rs           — 聚合分类器 + PrimaryMarketRegime + SecondaryMarketRegime
├── volatility.rs    — VolatilityRegime + VolatilityClassifier
├── liquidity.rs     — LiquidityRegime + LiquidityClassifier + SessionState
├── structure.rs     — MarketStructureRegime + MarketStructureClassifier
├── behavior.rs      — InvestorBehaviorRegime + InvestorBehaviorClassifier
└── config.rs        — MarketStateConfig + MarketStateProfile + UserWeightsTemplate
```

## 置信度计算

**最优公式（v5 调优后）**：

```rust
// 综合置信度
let base_confidence = 0.15;
let weighted_conf = vol_conf * 0.15 + liq_conf * 0.10 + struct_conf * 0.50 + behav_conf * 0.25;
let base_conf = base_confidence + weighted_conf * 0.85;
let overall_conf = base_conf * 0.70 + consistency * 0.30;
```

| 分类器 | 置信度来源 | 基础置信度 |
|--------|-----------|-----------|
| 波动率 | 基础(0.35) + 百分位(0.5) + 聚类(0.25) | 0.35 |
| 流动性 | 基础(0.3) + 偏离(×1.4) | 0.30 |
| 结构 | ADX/50 或 Wyckoff 分数 | 0 |
| 行为 | RSI 极端程度 + 动能衰减 | 0 |

**关键改进**：
- 各维度添加基础置信度，避免中间值得分过低
- 结构权重提高到 50%（趋势识别核心）
- 一致性采用部分匹配得分（非全有全无）

## 聚合权重（默认）

```json
{
  "volatility": 0.30,
  "liquidity": 0.20,
  "structure": 0.30,
  "behavior": 0.20
}
```

## 预设 Profile

| Profile | 用途 | 特点 |
|---------|------|------|
| default | 均衡配置 | 各维度权重均等 |
| trend_trading | 趋势交易 | 结构权重 0.40 |
| volatility_trading | 波动率交易 | 波动率权重 0.40 |
| reversal_trading | 反转交易 | 行为阈值放宽 |
| risk_control | 风险控制 | 更早触发极端警告 |

## 聚合逻辑优先级

1. **CrisisVol + 高置信** → ExtremeStress
2. **ThinLiquidity + 高置信** → ExtremeStress + LiquidityCrunch
3. **Exhaustion/Crowding + MeanReverting/Ranging** → ReversalBrewing
4. **Trending + 高流动性** → TrendExpansion
5. **Accumulation/Distribution** → RangeConsolidation
6. **默认** → RangeConsolidation + TightRange/WideRange

## 技术指标依赖

| 指标 | 周期 | 用途 |
|------|------|------|
| ATR | 14 | 波动率分类 |
| RSI | 14 | 行为极端检测 |
| ADX | 14 | 趋势强度 |
| MA | 20 | 均值偏离 |
| 百分位窗口 | 252 | 历史分位 |

## 扩展点

- 通过 `MarketStateConfig` 覆盖任何阈值
- 通过 `UserWeightsTemplate` 仅调整权重
- 各分类器可独立禁用
- 支持会话状态叠加（Killzone/Transition/OffHours）

## 与滤波层集成

滤波节点可基于 `MarketStateSnapshot.primary_regime` 决定是否允许因子进入：

```rust
match snapshot.primary_regime {
    PrimaryMarketRegime::ExtremeStress => FilterDecision::Block,
    PrimaryMarketRegime::TrendExpansion if factor.is_trend_following() => FilterDecision::Allow,
    _ => FilterDecision::Neutral,
}
```
