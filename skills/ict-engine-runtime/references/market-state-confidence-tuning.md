# 市场状态分类器置信度调优记录

## 调优迭代历史

| 版本 | 平均置信度 | 高置信比例 | 可交易比例 | 主要改进 |
|------|-----------|-----------|-----------|----------|
| v1 | 44.76% | 0% | 3.12% | 初始版本 |
| v2 | 53.05% | 0% | 41.67% | 降低趋势阈值 |
| v3 | 56.10% | 0% | 62.50% | 流动性基础置信度 |
| v4 | 54.36% | 0% | 58.33% | 结构权重优化 |
| v5 | 60.06% | 4.17% | 75% | 基础置信度 0.15 |
| **v6** | **61.26%** | **4.17%** | **79.17%** | 极端状态阈值收紧 |

## 最优配置参数（v6）

### 增强聚合器配置

```rust
EnhancedAggregationConfig {
    extreme_min_confidence: 0.65,   // 极端状态要求高置信
    trend_min_confidence: 0.50,     // 趋势扩展要求中等置信
    reversal_min_confidence: 0.50,  // 反转酝酿要求中等置信
    consistency_weight: 0.30,       // 一致性贡献30%
    price_direction_window: 20,     // 20 根 K 线判断方向
    price_direction_threshold: 2.0, // 2% 涨跌幅阈值
}
```

### 加权置信度公式

```rust
// 基础置信度避免过低综合置信度（v6: 提升到 0.20）
let base_confidence = 0.20;
let weighted_conf = vol_conf * 0.15 + liq_conf * 0.10 + struct_conf * 0.50 + behav_conf * 0.25;
let base_conf = base_confidence + weighted_conf * 0.80;

// 应用一致性加成
let overall_conf = base_conf * 0.70 + consistency * 0.30;
```

### 极端状态检测阈值（v6 收紧）

```rust
// 危机波动：阈值 0.75（原 0.65）
if matches!(vol, VolatilityRegime::CrisisVol) && vol_conf > 0.75 {
    return true;
}

// 流动性枯竭：阈值 0.80（原 0.65）
if matches!(liq, LiquidityRegime::ThinLiquidity) && liq_conf > 0.80 {
    return true;
}

// 行为恐慌 + 危机波动：阈值 0.70
if matches!(behav, Capitulation | FOMO)
    && matches!(vol, CrisisVol)
    && behav_conf > 0.70
    && vol_conf > 0.70 {
    return true;
}
```

### 流动性置信度改进

```rust
// 添加基础置信度，避免中间值置信度过低
let base_confidence = 0.3;
let deviation_confidence = (liq_score - 0.5).abs() * 1.4;
let confidence = (base_confidence + deviation_confidence).min(1.0);
```

### 波动率置信度改进

```rust
// 添加基础置信度
let base_confidence = 0.35;
let percentile_confidence = if matches!(regime, CrisisVol | LowVol) {
    (percentile.abs() - 0.5).abs() * 1.5
} else {
    0.3 + (percentile - 0.5).abs()
};
let confidence = (base_confidence + percentile_confidence * 0.5 + clustering_score * 0.25).min(1.0);
```

## 一致性计算改进

### 问题

原版一致性计算采用"全有全无"模式，导致中间值得分过低（0-0.4），无法有效提升置信度。

### 解决方案

引入部分匹配得分：

```rust
// 检查 4：行为极端或趋势结构与价格方向一致
match (behav, price_dir, struct_regime) {
    // 完全匹配 → 1.0
    (FOMO, Bullish, _) | (Capitulation, Bearish, _)
    | (_, Bullish | Bearish, Trending) => consistency_score += 1.0,
    // 部分匹配 → 0.5
    (_, Bullish | Bearish, _) => consistency_score += 0.5,
    // 默认得分 → 0.2
    _ => consistency_score += 0.2,
}

// 检查 5：流动性枯竭 + 极端波动
if ThinLiquidity && (CrisisVol | ElevatedVol) {
    consistency_score += 1.0;
} else if ThinLiquidity || (CrisisVol | ElevatedVol) {
    consistency_score += 0.4;  // 部分得分
}
```

## 关键发现

### 结构权重最重要

趋势识别核心是结构（ADX），将权重提高到 50% 显著改善分类质量。

### 基础置信度必要性

各维度分类器在中间值时置信度过低（接近 0），需要基础置信度兜底。

### 一致性部分得分

避免"全有全无"模式，部分匹配也能贡献得分，提升整体置信度。

### 极端状态阈值收紧

流动性基础置信度提升后，需收紧极端状态阈值（0.65→0.75/0.80），避免误判。

## 主大类分布（v6）

```
TrendExpansion:     41.7%  # 趋势扩展识别良好
RangeConsolidation: 41.7%  # 震荡整理覆盖均衡
ExtremeStress:      16.7%  # 极端状态误判减少（原 41.7%）
```

## 次小类分布（v6）

```
WideRange:              25.0%
BullTrendExhaustion:    16.7%
BullTrendAcceleration:  16.7%
LiquidityCrunch:        12.5%
TightRange:             12.5%
其他（共16种）：        共 16.6%
```

## 验证命令

```bash
# 使用模拟数据验证
./target/debug/ict-engine validate-market-state \
  --data /tmp/market_state_validation_data_v2.json \
  --window-size 100 --step-size 50
```

## 待改进

- 高置信比例（≥0.75）仅 4.17%，目标 30%+
- 需真实市场数据验证参数（NQ/ES 等）
- 多品种/多周期验证
