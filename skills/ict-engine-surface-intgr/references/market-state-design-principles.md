# 市场状态分类模块设计原则

## 背景

用户明确要求："我比较在意的还是市场状态分类。主大类跟次小类之类的。毕竟我们后面的准确率完全都是靠他提供的。置信度尽可能高好吧。"

市场状态分类是 ict-engine 后续所有准确率的基础，必须遵循严格的设计原则。

## 核心设计原则（强制性）

### 1. 零配置（Zero Configuration）
- **要求**：默认参数直接可用，无需用户配置
- **实现模式**：
  ```rust
  impl Default for ModuleConfig {
      fn default() -> Self {
          Self {
              // 基于统计学的保守默认值
              history_window: 252,  // 一年交易日
              min_samples: 30,      // 最小样本数
              threshold: 0.75,      // 高置信度阈值
          }
      }
  }

  pub struct Module {
      config: ModuleConfig,
  }

  impl Module {
      pub fn new() -> Self {
          Self::with_config(ModuleConfig::default())
      }
  }
  ```
- **验收标准**：
  - ✅ `Module::new()` 无参数调用即可工作
  - ✅ 默认参数基于历史统计，非随意拍脑袋
  - ✅ 默认参数保守，宁可漏过不可误报

### 2. 热插拔（Hot-Swappable）
- **要求**：用户可选择性覆盖配置，不修改代码
- **实现模式**：
  ```rust
  impl Module {
      pub fn with_config(config: ModuleConfig) -> Self {
          Self { config }
      }
  }

  // 用户使用
  let custom_config = ModuleConfig {
      history_window: 500,  // 自定义窗口
      ..Default::default()  // 其他保持默认
  };
  let module = Module::with_config(custom_config);
  ```
- **验收标准**：
  - ✅ 提供 `with_config()` 构造函数
  - ✅ 配置结构体实现 `Serialize` + `Deserialize`
  - ✅ 支持部分覆盖（通过 `..Default::default()`）

### 3. Token 友好（Token-Friendly）
- **要求**：输出简洁，避免冗余信息
- **实现模式**：
  ```rust
  pub struct ValidationResult {
      // 完整字段用于调试
      pub raw_confidence: f64,
      pub calibrated_confidence: f64,
      pub confidence_level: ConfidenceLevel,
      pub samples_available: usize,
      // ...
  }

  impl ValidationResult {
      /// Token 友好的摘要输出
      pub fn summary(&self) -> String {
          format!(
              "confidence={:.2}%({}) samples={} calibrated={}",
              self.calibrated_confidence * 100.0,
              self.confidence_level.as_str(),
              self.samples_available,
              self.calibration_applied
          )
      }
  }
  ```
- **验收标准**：
  - ✅ 所有结果类型提供 `summary()` 方法
  - ✅ 摘要输出单行，关键信息前置
  - ✅ 完整字段保留用于调试，但不强制输出

### 4. 高置信度（High Confidence）
- **要求**：基于历史统计学阈值，而非单次判断
- **实现模式**：
  ```rust
  pub struct ConfidenceValidator {
      history: VecDeque<HistorySample>,  // 滚动窗口
      regime_stats: HashMap<String, RegimeStats>,  // 各状态统计
  }

  impl ConfidenceValidator {
      pub fn validate(&mut self, snapshot: &MarketStateSnapshot) -> ValidationResult {
          let stats = self.regime_stats.entry(regime_key).or_default();

          // 基于历史统计校准
          let calibrated = if stats.has_sufficient_samples(min_samples) {
              stats.calibrated_confidence(raw, calibration_factor)
          } else {
              raw  // 样本不足时保守使用原始值
          };

          ValidationResult { calibrated, ... }
      }

      pub fn record_outcome(&mut self, snapshot: &MarketStateSnapshot, outcome: bool) {
          // 记录实际结果，用于后续校准
      }
  }
  ```
- **验收标准**：
  - ✅ 使用滚动窗口历史统计
  - ✅ 自适应校准：实际成功率 vs 原始置信度
  - ✅ 最小样本数门槛（如 30 样本）
  - ✅ 置信度分级：High / Medium / Low / VeryLow
  - ✅ 可交易性判定：仅 High/Medium 可交易

### 5. 无污染（No Pollution）
- **要求**：不修改现有代码，新模块独立
- **实现模式**：
  ```rust
  // 新模块独立文件
  // src/market_state/confidence_validation.rs

  // 仅在 mod.rs 中添加导出
  pub mod confidence_validation;
  pub use confidence_validation::{
      ConfidenceValidator, ValidationResult, ...
  };
  ```
- **验收标准**：
  - ✅ 新模块独立文件
  - ✅ 不修改现有模块内部逻辑
  - ✅ 通过 `pub use` 导出公共 API

### 6. 无负债（No Technical Debt）
- **要求**：代码质量高，测试覆盖完整
- **实现模式**：
  ```rust
  #[cfg(test)]
  mod tests {
      use super::*;

      #[test]
      fn validator_classifies_confidence_levels() {
          // 测试置信度分级
      }

      #[test]
      fn calibration_adjusts_confidence() {
          // 测试校准逻辑
      }

      #[test]
      fn rolling_accuracy_tracker_works() {
          // 测试滚动准确率
      }
  }
  ```
- **验收标准**：
  - ✅ 单元测试覆盖核心逻辑
  - ✅ 测试用例覆盖边界情况
  - ✅ 代码通过 `cargo fmt` 和 `cargo clippy`

## 实际应用案例

### 置信度验证模块（2026-05-07）

**文件**：`src/market_state/confidence_validation.rs`

**设计决策**：
- **零配置**：`ConfidenceValidator::new()` 使用默认参数（252 天窗口，30 最小样本）
- **热插拔**：`ConfidenceValidator::with_config(custom)` 支持自定义配置
- **Token 友好**：`ValidationResult::summary()` 输出 `"confidence=75.3%(high) samples=120 calibrated=true"`
- **高置信度**：
  - 历史回测验证：滚动窗口统计
  - 自适应校准：实际成功率 vs 原始置信度
  - 置信度分级：High(≥0.75) / Medium(≥0.55) / Low(≥0.35) / VeryLow(<0.35)
  - 可交易性判定：仅 High/Medium 可交易
- **无污染**：独立模块，不修改现有代码
- **无负债**：完整单元测试覆盖

**权衡**：
- 需要历史样本积累（最小 30 样本）
- 冷启动阶段置信度较低
- 解决：默认参数保守，用户可调整

## 常见陷阱

### 陷阱 1：默认参数随意拍脑袋
❌ **错误**：
```rust
impl Default for Config {
    fn default() -> Self {
        Self {
            threshold: 0.5,  // 随意选择
        }
    }
}
```

✅ **正确**：
```rust
impl Default for Config {
    fn default() -> Self {
        Self {
            // 基于历史统计：75% 置信度对应 80% 实际成功率
            high_confidence_threshold: 0.75,
            // 基于统计学：30 样本达到 95% 置信区间
            min_samples: 30,
        }
    }
}
```

### 陷阱 2：输出冗余信息
❌ **错误**：
```rust
println!("Validation Result:");
println!("  Raw Confidence: {}", result.raw_confidence);
println!("  Calibrated Confidence: {}", result.calibrated_confidence);
println!("  Confidence Level: {:?}", result.confidence_level);
println!("  Samples Available: {}", result.samples_available);
println!("  Calibration Applied: {}", result.calibration_applied);
```

✅ **正确**：
```rust
println!("{}", result.summary());
// → "confidence=75.3%(high) samples=120 calibrated=true"
```

### 陷阱 3：单次判断代替历史统计
❌ **错误**：
```rust
fn validate(&self, snapshot: &MarketStateSnapshot) -> ValidationResult {
    // 直接使用原始置信度，无历史验证
    ValidationResult {
        calibrated_confidence: snapshot.overall_confidence,
        ...
    }
}
```

✅ **正确**：
```rust
fn validate(&mut self, snapshot: &MarketStateSnapshot) -> ValidationResult {
    let stats = self.regime_stats.entry(regime_key).or_default();

    // 基于历史统计校准
    let calibrated = if stats.has_sufficient_samples(self.config.min_samples) {
        stats.calibrated_confidence(snapshot.overall_confidence, self.config.calibration_factor)
    } else {
        snapshot.overall_confidence  // 样本不足时保守
    };

    ValidationResult { calibrated, ... }
}
```

### 陷阱 4：修改现有代码
❌ **错误**：
```rust
// 在现有模块中直接添加新逻辑
impl MarketStateClassifier {
    pub fn classify(&self, candles: &[Candle]) -> MarketStateSnapshot {
        // ... 现有逻辑

        // 直接添加置信度验证（污染现有代码）
        let validated = self.validate_confidence(&snapshot);
        // ...
    }
}
```

✅ **正确**：
```rust
// 新模块独立
// src/market_state/confidence_validation.rs
pub struct ConfidenceValidator { ... }

// 用户在外部组合使用
let classifier = MarketStateClassifier::new();
let validator = ConfidenceValidator::new();

let snapshot = classifier.classify(&candles);
let validation = validator.validate(&snapshot);
```

## 工作流

1. **设计阶段**：
   - 明确模块职责
   - 确定默认参数（基于统计学，非拍脑袋）
   - 设计配置结构体（支持热插拔）
   - 设计输出格式（Token 友好）

2. **实现阶段**：
   - 创建独立模块文件
   - 实现 `Default` trait
   - 实现 `with_config()` 构造函数
   - 实现 `summary()` 方法
   - 添加单元测试

3. **集成阶段**：
   - 在 `mod.rs` 中添加模块声明
   - 通过 `pub use` 导出公共 API
   - 更新文档

4. **验证阶段**：
   - `cargo fmt --all`
   - `cargo check`
   - `cargo test`
   - 编写使用示例

## 验收清单

- [ ] 零配置：`Module::new()` 无参数调用可工作
- [ ] 热插拔：提供 `with_config()` 构造函数
- [ ] Token 友好：提供 `summary()` 方法
- [ ] 高置信度：基于历史统计学阈值
- [ ] 无污染：独立模块，不修改现有代码
- [ ] 无负债：完整单元测试覆盖
- [ ] 文档更新：更新 TODO 文档和设计决策记录

## 相关文档

- 市场状态分类模块：`src/market_state/mod.rs`
- 置信度验证模块：`src/market_state/confidence_validation.rs`
- BBN 证据映射模块：`src/market_state/evidence_mapping.rs`
- 执行树集成模块：`src/market_state/execution_integration.rs`
- TODO 文档：`docs/plans/2026-05-07-ict-engine-action-items.md`
