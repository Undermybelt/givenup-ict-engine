use serde::{Deserialize, Serialize};

/// State persistence types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PersistedState {
    pub hmm_params: Option<crate::types::HMMParams>,
    pub cascade_config: Option<crate::bayesian::CascadeConfig>,
    pub beta_learner: Option<crate::bayesian::CascadeBetaLearner>,
    pub sv_params: Option<SVParams>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SVParams {
    pub mu: f64,
    pub phi: f64,
    pub sigma_eta: f64,
}

impl Default for PersistedState {
    fn default() -> Self {
        Self {
            hmm_params: None,
            cascade_config: None,
            beta_learner: None,
            sv_params: None,
        }
    }
}
