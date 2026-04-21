pub mod backtest_compare;
pub mod backtest_request;
pub mod backtest_result;

pub use backtest_compare::{
    build_backtest_compare_report, build_duration_sizing_delta_surface,
    build_oos_quality_delta_surface, build_research_compare_report,
    build_shrink_on_off_comparison_summary, compare_backtest_results, BacktestCompareReport,
};
pub use backtest_request::{build_backtest_request, BacktestRequest, BacktestRequestInput};
pub use backtest_result::{
    build_backtest_result_artifact, BacktestResultArtifact, BacktestResultArtifactInput,
};
