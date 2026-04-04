use super::forward_backward::ForwardBackward;
use crate::types::HMMParams;

/// Baum-Welch EM algorithm for HMM training
pub struct BaumWelch;

impl BaumWelch {
    /// Train HMM using Baum-Welch algorithm
    pub fn fit(
        observations: &[Vec<f64>],
        initial_params: &HMMParams,
        max_iter: usize,
        tolerance: f64,
    ) -> HMMParams {
        let mut params = initial_params.clone();
        let mut prev_ll = f64::NEG_INFINITY;

        for _ in 0..max_iter {
            // E-step
            let (log_alpha, ll) = ForwardBackward::forward(observations, &params);
            let log_beta = ForwardBackward::backward(observations, &params);
            let gamma = ForwardBackward::compute_gamma(&log_alpha, &log_beta, ll);
            let log_xi =
                ForwardBackward::compute_xi(&log_alpha, &log_beta, observations, &params, ll);

            // M-step: update parameters
            let k = params.n_states;
            let d = observations[0].len();
            let t = observations.len();

            // Update initial probabilities
            for state in 0..k {
                params.initial_probs[state] = gamma[0][state].exp();
            }

            // Update transition matrix
            for i in 0..k {
                let gamma_sum_i: f64 = (0..t - 1).map(|tt| gamma[tt][i].exp()).sum();

                for j in 0..k {
                    let xi_sum: f64 = (0..t - 1).map(|tt| log_xi[tt][i][j].exp()).sum();
                    params.transition[i][j] = xi_sum / gamma_sum_i.max(1e-30);
                }
            }

            // Update emission parameters
            for state in 0..k {
                let gamma_sum: f64 = (0..t).map(|tt| gamma[tt][state].exp()).sum();
                let gamma_sum_safe = gamma_sum.max(1e-30);

                for dim in 0..d {
                    // Mean
                    let weighted_sum: f64 = (0..t)
                        .map(|tt| gamma[tt][state].exp() * observations[tt][dim])
                        .sum();
                    params.emission_means[state][dim] = weighted_sum / gamma_sum_safe;

                    // Standard deviation
                    let var_sum: f64 = (0..t)
                        .map(|tt| {
                            let diff = observations[tt][dim] - params.emission_means[state][dim];
                            gamma[tt][state].exp() * diff * diff
                        })
                        .sum();
                    params.emission_stds[state][dim] = (var_sum / gamma_sum_safe).sqrt().max(1e-10);
                }
            }

            // Check convergence
            if (ll - prev_ll).abs() < tolerance {
                break;
            }
            prev_ll = ll;
        }

        params
    }
}
