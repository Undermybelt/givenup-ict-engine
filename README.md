# ICT Engine - ICT Expansion Trading Engine (•̀ᴗ•́)و

English first. 中文在后。

A probability-driven Rust CLI for ICT-style market analysis, research, feedback learning, and workflow tracking.

## Overview

This repository is a Rust implementation of an ICT-oriented trading analysis engine. It combines:

- **ICT structure analysis** - market structure, liquidity, imbalance, expansion context
- **Probabilistic decision layers** - HMM, Bayesian fusion, gated trade reasoning
- **Research / feedback workflow** - factor research, update feedback, artifact tracking
- **Workflow visibility** - workflow snapshots, agent prompts, next-command guidance

---

# 中文简介 (✿◠‿◠)

基于 ICT (Inner Circle Trader) 思路的概率交易分析引擎，核心是：分析、研究、反馈回灌、工作流追踪。

## 项目概述

本项目是一个 Rust CLI 交易研究引擎，结合了：

- **ICT 结构分析** - 市场结构、流动性、失衡、扩张上下文
- **概率决策层** - HMM、贝叶斯融合、带门控的交易推断
- **研究 / 反馈工作流** - 因子研究、结果回灌、artifact 追踪
- **工作流可见性** - workflow snapshot、agent prompts、下一步命令建议

## 目录结构

```
src/
├── main.rs                 # CLI入口
├── lib.rs
├── types.rs                # 全局共享类型
│
├── data/                   # 数据加载
│   ├── candle.rs          # OHLCV结构体
│   └── loader.rs          # JSON/CSV加载
│
├── indicators/             # 技术指标
│   ├── atr.rs             # ATR (Wilder)
│   ├── rsi.rs             # RSI (Wilder)
│   ├── adx.rs             # ADX
│   ├── ema.rs             # EMA
│   ├── bollinger.rs       # 布林带
│   └── macd.rs            # MACD
│
├── ict/                    # ICT结构检测
│   ├── swing.rs           # Swing Point检测
│   ├── pda.rs             # PDA连续序列
│   ├── liquidity.rs       # 流动性池 + 清扫
│   ├── fvg.rs             # Fair Value Gap
│   ├── ob.rs              # Order Block
│   ├── cisd.rs            # CISD
│   ├── rb.rs              # RB/Pinbar
│   ├── bos_choch.rs       # BOS / CHoCH
│   └── expansion.rs       # 扩张综合确认
│
├── kalman/                 # 卡尔曼滤波
│   ├── filter.rs          # 标准卡尔曼滤波
│   └── smoother.rs        # RTS平滑器
│
├── sv/                     # 随机波动率
│   ├── model.rs           # SV模型
│   └── particle_filter.rs # 粒子滤波估计器
│
├── hmm/                    # 隐马尔可夫模型
│   ├── forward_backward.rs # 前向-后向算法
│   ├── baum_welch.rs       # EM训练
│   ├── viterbi.rs          # 最优状态路径
│   └── observation.rs      # 观测向量构建
│
├── gp/                     # 高斯过程
│   ├── kernels.rs         # 核函数
│   └── regression.rs      # 高斯过程回归
│
├── hawkes/                 # Hawkes过程
│   ├── process.rs         # Hawkes过程拟合
│   └── sweep_detector.rs  # 基于Hawkes的清扫检测
│
├── bvar/                   # 贝叶斯VAR
│   └── model.rs           # 贝叶斯VAR模型
│
├── bayesian/               # 贝叶斯决策
│   ├── cascade.rs         # 7层级联决策树
│   ├── fusion.rs          # 多信号贝叶斯融合
│   ├── beta_learner.rs    # Beta在线学习
│   └── premium_discount.rs # Premium/Discount判定
│
├── mcmc/                   # MCMC采样
│   ├── metropolis_hastings.rs # MH采样器
│   └── calibration.rs     # LR校准
│
├── smt/                    # SMT分析
│   ├── cointegration.rs   # 协整检验
│   ├── divergence.rs      # 跨品种背离
│   └── correlation.rs     # 滚动相关性
│
├── factors/                # 因子系统
│   ├── registry.rs        # 因子注册表
│   ├── ic_calculator.rs   # IC/IR计算
│   ├── regime_conditional.rs # Regime条件评估
│   └── weight_updater.rs  # 权重更新
│
├── planner/                # 交易计划
│   ├── kelly.rs           # 凯利公式
│   ├── risk.rs            # ATR止损止盈
│   ├── ote.rs             # Optimal Trade Entry
│   └── trade_plan.rs      # 交易计划生成
│
├── state/                  # 状态持久化
│   ├── persistence.rs     # JSON读写
│   └── db.rs              # SQLite (可选)
│
├── backtest/               # 回测引擎
│   ├── engine.rs          # 回测引擎
│   ├── metrics.rs         # Sharpe/MaxDD/WinRate
│   └── regime_split.rs    # Regime条件回测
│
└── python_bridge/          # Python集成
    └── timesfm.rs         # TimesFM调用桥接
```

## Build

```bash
cargo build --release
```

## Usage

### 查看命令面

```bash
cargo run -- --help
cargo run -- analyze --help
```

### 分析市场

```bash
ict-engine analyze \
  --symbol NQ \
  --data-htf data/NQ_4h.json \
  --data-mtf data/NQ_1h.json \
  --data-ltf data/NQ_15m.json
```

当前 analyze 输出除 `report` 外，还会包含：
- `compact_report`
- `agent_report`
- `human_report`
- `belief_shadow_policy`
- `belief_policy_lineage`

### 训练HMM

```bash
ict-engine train \
  --symbol NQ \
  --data data/NQ_1h_historical.json \
  --epochs 200
```

### 因子研究

```bash
ict-engine factor-research \
  --symbol NQ \
  --data data/NQ_1h_historical.json \
  --objective generic
```

当前 factor-research 输出会包含：
- `report`
- `reflection_bundle`
- `factor_lifecycle`

### 结果回灌

```bash
ict-engine update \
  --symbol NQ \
  --outcome win \
  --entry-signal medium
```

当前 update 输出会包含：
- `report`
- `reflection_bundle`

### 工作流状态

```bash
ict-engine workflow-status \
  --symbol NQ
```

### 历史数据复用规则

当前工作流已改为：
- 若 agent 要复用历史数据去跑 `factor-research` 或 `factor-backtest`
- 即使系统已记录路径，也必须先问用户“这次用哪份数据”
- 因此推荐命令会进入硬门禁：
  - `ready = false`
  - `missing_inputs` 包含 `user_selected_historical_data`
  - `recorded_data_paths` 会列出已知候选路径

详细 smoke / acceptance 流见：
- `docs/smoke-acceptance.md`

## 核心功能

1. **ICT结构检测**
   - Swing Point检测
   - PDA连续序列
   - 流动性池和清扫
   - Fair Value Gap
   - Order Block
   - CISD (Change in State of Delivery)
   - Rejection Block/Pinbar
   - BOS/CHoCH

2. **统计模型**
   - 卡尔曼滤波 (价格去噪)
   - 随机波动率 + 粒子滤波
   - HMM regime检测
   - 高斯过程回归
   - Hawkes过程 (事件聚类)
   - 贝叶斯VAR (多品种联动)

3. **贝叶斯决策**
   - 7层级联决策树
   - 多信号融合
   - Beta在线学习
   - Premium/Discount判定

4. **风险管理**
   - 凯利公式仓位计算
   - ATR动态止损止盈
   - OTE区域定位

5. **TimesFM集成**
   - 通过Python桥接调用TimesFM预测
   - 零样本时间序列预测
   - 分位数预测区间

## 数据源

支持从market-analysis技能获取数据：
- Tradecat API
- Yahoo Finance
- CCXT (加密货币)
- OpenBB

## 输出格式

JSON格式输出，包含：
- Regime概率
- Cascade决策树结果
- ICT结构统计
- 交易计划 (如有信号)
- TimesFM预测 (可选)

## 依赖

- Rust 1.76+
- Python 3.10+ (用于TimesFM)
- TimesFM包 (`pip install timesfm[torch]`)

## 许可证

MIT License
