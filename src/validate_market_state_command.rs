//! Market State Validation Command

use anyhow::{Context, Result};

use ict_engine::data::load_candles;
use ict_engine::market_state::{
    MarketStateClassifier, MarketStateConfig, MarketStateProfile, MarketStateValidator,
    ValidationConfig,
};

pub struct ValidateMarketStateInput {
    pub data_path: String,
    pub window_size: usize,
    pub step_size: usize,
    pub verbose: bool,
    pub enhanced: bool,
    pub config_path: Option<String>,
    pub profile: Option<String>,
}

pub fn validate_market_state_shell(input: ValidateMarketStateInput) -> Result<()> {
    println!("=== Market State Classification Validation ===\n");

    if input.window_size == 0 {
        anyhow::bail!("window-size must be greater than 0");
    }
    if input.step_size == 0 {
        anyhow::bail!("step-size must be greater than 0");
    }
    if input.config_path.is_some() && input.profile.is_some() {
        anyhow::bail!("use only one of --config or --profile");
    }

    println!("Loading data from: {}", input.data_path);
    let candles = load_candles(&input.data_path)
        .with_context(|| format!("failed to load candles from {}", input.data_path))?;
    println!("Loaded {} candles\n", candles.len());

    if candles.len() < input.window_size {
        anyhow::bail!(
            "Not enough candles: {} < {}",
            candles.len(),
            input.window_size
        );
    }

    let config = if let Some(ref profile_name_or_path) = input.config_path {
        let path = std::path::Path::new(profile_name_or_path);
        MarketStateConfig::load(path).with_context(|| {
            format!("failed to load market-state config from {}", path.display())
        })?
    } else if let Some(ref profile_name) = input.profile {
        let profile = match profile_name.as_str() {
            "default" => MarketStateProfile::default_profile(),
            "trend_trading" => MarketStateProfile::trend_trading_profile(),
            "volatility_trading" => MarketStateProfile::volatility_trading_profile(),
            "reversal_trading" => MarketStateProfile::reversal_trading_profile(),
            "risk_control" => MarketStateProfile::risk_control_profile(),
            other => anyhow::bail!(
                "unknown market-state profile: {} (use default, trend_trading, volatility_trading, reversal_trading, or risk_control)",
                other
            ),
        };
        MarketStateConfig::from_profile(&profile)
    } else {
        MarketStateConfig::default()
    };

    let classifier =
        MarketStateClassifier::with_config(config).with_enhanced_aggregation(input.enhanced);

    println!(
        "Classifier: {} aggregation\n",
        if input.enhanced { "Enhanced" } else { "Basic" }
    );

    let config = ValidationConfig {
        min_window_size: input.window_size,
        step_size: input.step_size,
        verbose: input.verbose,
    };
    let validator = MarketStateValidator::with_classifier(classifier, config);

    println!("Running validation...");
    println!(
        "  Window: {} | Step: {} | Windows: ~{}\n",
        input.window_size,
        input.step_size,
        (candles.len() - input.window_size) / input.step_size
    );

    let result = validator.validate(&candles);
    let report = validator.generate_report(&result);
    println!("{}", report);

    Ok(())
}
