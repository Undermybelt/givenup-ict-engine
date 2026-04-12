use super::glossary_map::humanize_term;

#[derive(Debug, Clone, Default)]
pub struct HumanAnalyzeReport {
    pub basic_price_structure_analysis: String,
    pub technical_price_analysis: String,
    pub smt_correlation_analysis: String,
    pub regime_bayes_analysis: String,
    pub trade_plan: String,
}

impl HumanAnalyzeReport {
    pub fn render(&self) -> String {
        [
            format!("基本价格结构分析\n{}", self.basic_price_structure_analysis),
            format!("技术面价格分析\n{}", self.technical_price_analysis),
            format!("SMT相关性分析\n{}", self.smt_correlation_analysis),
            format!("Regime分类结合贝叶斯分析并给推测概率\n{}", self.regime_bayes_analysis),
            format!("交易计划\n{}", self.trade_plan),
        ]
        .join("\n\n")
    }
}

pub fn build_human_analyze_report(
    basic_price_structure_analysis: impl Into<String>,
    technical_price_analysis: impl Into<String>,
    smt_correlation_analysis: impl Into<String>,
    regime_bayes_analysis: impl Into<String>,
    trade_plan: impl Into<String>,
) -> HumanAnalyzeReport {
    HumanAnalyzeReport {
        basic_price_structure_analysis: humanize_term(&basic_price_structure_analysis.into()),
        technical_price_analysis: humanize_term(&technical_price_analysis.into()),
        smt_correlation_analysis: humanize_term(&smt_correlation_analysis.into()),
        regime_bayes_analysis: humanize_term(&regime_bayes_analysis.into()),
        trade_plan: humanize_term(&trade_plan.into()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn human_report_renders_five_sections() {
        let report = build_human_analyze_report("a", "b", "c", "d", "e");
        let rendered = report.render();
        assert!(rendered.contains("基本价格结构分析"));
        assert!(rendered.contains("交易计划"));
    }
}
