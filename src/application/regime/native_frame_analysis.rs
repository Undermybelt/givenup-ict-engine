use anyhow::Result;
use std::collections::HashMap;

use crate::analyze_builder_types::AnalyzeNativeFrames;
use crate::application::regime::native_frame_weight;
use crate::config::build_frame_features;
use crate::config::FrameFeatures;
use crate::hmm::{ForwardBackward, Viterbi};
use crate::types::{Candle, HMMParams, RegimeProbs};

#[derive(Clone)]
pub struct NativeFrameComputation {
    pub weight: f64,
    pub features: FrameFeatures,
    pub regime_probs: RegimeProbs,
    pub log_likelihood: f64,
    pub viterbi_log_likelihood: f64,
}

pub fn native_frame_computations(
    params: &HMMParams,
    native_frames: AnalyzeNativeFrames<'_>,
) -> Result<Vec<NativeFrameComputation>> {
    native_frame_computations_with_feature_cache(params, native_frames, &HashMap::new())
}

pub fn native_frame_computations_with_feature_cache(
    params: &HMMParams,
    native_frames: AnalyzeNativeFrames<'_>,
    feature_cache: &HashMap<(usize, usize), FrameFeatures>,
) -> Result<Vec<NativeFrameComputation>> {
    let mut signals = Vec::new();
    for (interval, candles) in [
        ("1d", native_frames.d1),
        ("4h", native_frames.h4),
        ("1h", native_frames.h1),
        ("15m", native_frames.m15),
        ("5m", native_frames.m5),
        ("1m", native_frames.m1),
    ] {
        let Some(candles) = candles else {
            continue;
        };
        let features = feature_cache
            .get(&frame_cache_key(candles))
            .cloned()
            .unwrap_or(build_frame_features(candles)?);
        let (log_alpha, log_likelihood) = ForwardBackward::forward(&features.observations, params);
        let log_beta = ForwardBackward::backward(&features.observations, params);
        let gamma = ForwardBackward::compute_gamma(&log_alpha, &log_beta, log_likelihood);
        let (_, viterbi_log_likelihood) = Viterbi::decode(&features.observations, params);
        signals.push(NativeFrameComputation {
            weight: native_frame_weight(interval),
            regime_probs: regime_probs_from_log_gamma(gamma.last())?,
            log_likelihood,
            viterbi_log_likelihood,
            features,
        });
    }
    Ok(signals)
}

pub fn frame_cache_key(candles: &[Candle]) -> (usize, usize) {
    (candles.as_ptr() as usize, candles.len())
}

fn regime_probs_from_log_gamma(log_gamma: Option<&Vec<f64>>) -> Result<RegimeProbs> {
    let log_gamma =
        log_gamma.ok_or_else(|| anyhow::anyhow!("missing HMM posterior probabilities"))?;
    if log_gamma.len() < 3 {
        anyhow::bail!("expected 3 HMM states, got {}", log_gamma.len());
    }

    let accumulation = log_gamma[0].exp();
    let manipulation_expansion = log_gamma[1].exp();
    let distribution = log_gamma[2].exp();
    let sum = accumulation + manipulation_expansion + distribution;
    if sum <= f64::EPSILON {
        anyhow::bail!("invalid HMM posterior: probabilities sum to zero");
    }

    Ok(RegimeProbs {
        accumulation: accumulation / sum,
        manipulation_expansion: manipulation_expansion / sum,
        distribution: distribution / sum,
    })
}

#[cfg(test)]
mod tests {
    use super::{frame_cache_key, native_frame_computations_with_feature_cache};
    use crate::analyze_builder_types::AnalyzeNativeFrames;
    use crate::config::build_frame_features;
    use crate::types::{Candle, HMMParams};
    use chrono::{Duration, Utc};
    use std::collections::HashMap;

    fn sample_candles(len: usize) -> Vec<Candle> {
        let start = Utc::now();
        (0..len)
            .map(|idx| {
                let base = 100.0 + idx as f64 * 0.25;
                Candle {
                    timestamp: start + Duration::minutes(idx as i64),
                    open: base,
                    high: base + 0.4,
                    low: base - 0.4,
                    close: base + 0.1,
                    volume: 1_000.0 + idx as f64,
                }
            })
            .collect()
    }

    #[test]
    fn native_frame_computations_reuse_cached_features_for_same_slice() {
        let candles = sample_candles(64);
        let built = build_frame_features(&candles).unwrap();
        let obs_dim = built.observations[0].len();
        let params = HMMParams::new_3state(obs_dim);

        let mut cached = built.clone();
        cached.regime_label = "cached-regime".to_string();
        cached.liquidity_label = "cached-liquidity".to_string();

        let mut feature_cache = HashMap::new();
        feature_cache.insert(frame_cache_key(&candles), cached);

        let signals = native_frame_computations_with_feature_cache(
            &params,
            AnalyzeNativeFrames {
                h1: Some(&candles),
                ..Default::default()
            },
            &feature_cache,
        )
        .unwrap();

        assert_eq!(signals.len(), 1);
        assert_eq!(signals[0].features.regime_label, "cached-regime");
        assert_eq!(signals[0].features.liquidity_label, "cached-liquidity");
    }
}
