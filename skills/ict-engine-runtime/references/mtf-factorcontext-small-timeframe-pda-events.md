# MTF / FactorContext 小周期 PDA event 透传

## 触发场景

用户审计因子迭代到实战建议闭环，特别问：滤波、regime 主/子分类、BBN 节点证据、CatBoost/path-ranker、执行树各节点证据是否完整。若发现 `structure_ict` 或 factor research/backtest 只吃 H4/D1/W1 PDA events，应按本参考补小周期链路。

## 本次学到的闭环缺口

旧链路常见状态：
- MTF 输入有 `1m/5m/15m/1h/4h/1d`，但缺 `30m`。
- `StructureIctContextEvents` 已能构造或接近构造小周期 events，但 `FactorContext` 只注入 `h4_events/d1_events/w1_events`。
- `factor-research`、`factor-backtest`、baseline mutation metrics、`analyze` native frames、factor pipeline debug 等调用点容易漏新字段。
- `cargo check` 只覆盖 bin/lib；`cargo test` 会暴露测试模块里的旧 struct literal 和旧函数签名调用。

## 实现清单

1. 扩 `ResolvedMultiTimeframeInputs` 支持 `30m`：
   - 常量/顺序中加入 `30m`
   - `resolve_multi_timeframe_inputs(...)` 签名加入 `data_30m`
   - 所有调用点补第 8 个参数，测试也要补
2. 扩 `AnalyzeNativeFrames`：
   - 增 `m30: Option<&[Candle]>`
   - `analyze`、`analyze-live`、测试里的 struct literal 全补 `m30`
3. 扩 `StructureIctContextEvents`：
   - `m1_events/m5_events/m15_events/m30_events/h1_events/h4_events/d1_events/w1_events`
   - 从 resolved MTF 或 native frames 构造 PDA timeline
4. 扩 `FactorContext` 与 consumer：
   - 加 `m1_events/m5_events/m15_events/m30_events/h1_events`
   - `collect_structure_ict_setup_matches` 参数和所有测试调用同步
5. 透传调用点：
   - `factor_research_runtime.rs`
   - `factor_backtest_runtime.rs`
   - baseline mutation metrics input
   - `main.rs` analyze path
   - `factor_pipeline_debug.rs`
   - `research_debug_command.rs`
   - `factor_research_command.rs`
   - `application/factor_lifecycle/*`
   - `application/regime/multi_timeframe_training.rs`
6. CLI 参数：
   - FactorResearch / FactorAutoresearch / FactorBacktest / FactorPipelineDebug 增 `--data-30m`

## 验证顺序

先编译面：
```bash
cargo check
```

再跑定向 bin 测试，避免 workspace integration tests 因外部长测卡死：
```bash
cargo test --bin ict-engine multi_timeframe -- --nocapture
```

若下一步用 `./target/debug/ict-engine` 做 CLI 实跑，必须先刷新普通二进制：
```bash
cargo build
```
`cargo check` 和 `cargo test --bin` 不保证 `target/debug/ict-engine` 已包含最新改动；否则会误判 report 仍缺新字段。

如需全量过滤测试，注意：
```bash
cargo test multi_timeframe -- --nocapture
```
可能会跑到 integration tests（例如 `tests/sparse_select`）并长时间卡住；若主 bin 测试已过，可记录为外部测试超时，不要误判为本补丁失败。

## cleaned-30m 实跑验收

用真实或隔离样本跑 `factor-research` / `factor-backtest`，验两类字符串都出现在 JSON 任意层：
```text
multi_timeframe_source=explicit covered_intervals=1m,5m,15m,30m,1h,4h,1d
structure_ict_pda_context_events=m1:<n>|m5:<n>|m15:<n>|m30:<n>|h1:<n>|h4:<n>|d1:<n>|w1:<n>
```

若样本太平，PDA 计数可能全 0；这只证明字段透出，不证明小周期 PDA 被实际消费。为验证非零证据，造一个隔离 synthetic OHLC 样本（只放 `/tmp/...`），通过交替 gap/impulse 强制产生 FVG/OB，再复制到 `cleaned-1m/5m/15m/30m/1h/4h/1d`。验收时应看到类似：
```text
structure_ict_pda_context_events=m1:239|m5:239|m15:239|m30:239|h1:239|h4:239|d1:239|w1:0
```

## 断言更新

若 MTF interval 顺序加入 `30m`，旧断言：
```text
covered_intervals=1m,5m,15m,1h,4h,1d
```
应更新为：
```text
covered_intervals=1m,5m,15m,30m,1h,4h,1d
```

## Rustfmt / 脏工作树坑

- `cargo fmt --check` 可能暴露大量既存 rustfmt drift，涉及非本轮文件。
- 不要为了通过 fmt 盲目格式化全仓，除非用户同意接受无关格式化 diff。
- 用户明确偏好：只格式化本轮触碰的 Rust 文件；若要全仓 `cargo fmt`，先确认。
- 提交前跑 `git status --short` 与 `git diff --stat`，只 stage 本轮自有文件；多 agent 并行时避开其它 agent 的格式漂移/脏改。
- 外部脏改若只是 rustfmt drift（例如非本轮文件换行），保留未提交并在最终说明。
- 若工具轮数耗尽，最终汇报应明确：`cargo check` 通过、定向 bin 测试通过、全量过滤测试或 fmt 的阻塞点。