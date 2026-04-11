use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ParticleBeliefSummary {
    pub particle_count: usize,
    pub effective_sample_size: f64,
    pub dominant_regime: String,
}

pub fn bootstrap_particle_summary(regime: &str) -> ParticleBeliefSummary {
    ParticleBeliefSummary {
        particle_count: 64,
        effective_sample_size: 48.0,
        dominant_regime: regime.to_string(),
    }
}
