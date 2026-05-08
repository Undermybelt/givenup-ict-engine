//! Market State Validation Command

use anyhow::{Context, Result};

use ict_engine::data::load_candles;
use ict_engine::market_state::{MarketStateClassifier, MarketStateValidator, ValidationConfig};

pub struct ValidateMarketStateInput {
    pub data_path: String,
    pub window_size: usize,
    pub step_size: usize,
    pub verbose: bool,
    pub enhanced: bool,
}

pub fn validate_market_state_shell(input: ValidateMarketStateInput) -> Result<()> {
    println!("=== Market State Classification Validation ===\n");

    if input.window_size == 0 {
        anyhow::bail!("window-size must be greater than 0");
    }
    if input.step_size == 0 {
        anyhow::bail!("step-size must be greater than 0");
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

    let classifier = MarketStateClassifier::new().with_enhanced_aggregation(input.enhanced);

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
