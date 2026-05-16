use crate::types::{Direction, KalmanParams, KalmanState};
use ndarray::{Array1, Array2};

/// Standard Kalman Filter for price denoising
/// State: [price, velocity]
/// Observation: [price]
pub struct KalmanFilter {
    pub params: KalmanParams,
    pub state: KalmanState,
}

impl KalmanFilter {
    /// Initialize Kalman Filter
    pub fn new(
        initial_price: f64,
        process_noise_price: f64,
        process_noise_vel: f64,
        measurement_noise: f64,
    ) -> Self {
        // State transition matrix F
        let f = Array2::from_shape_vec((2, 2), vec![1.0, 1.0, 0.0, 1.0]).unwrap();

        // Observation matrix H
        let h = Array2::from_shape_vec((1, 2), vec![1.0, 0.0]).unwrap();

        // Process noise covariance Q
        let q = Array2::from_shape_vec(
            (2, 2),
            vec![process_noise_price, 0.0, 0.0, process_noise_vel],
        )
        .unwrap();

        // Measurement noise covariance R
        let r = Array2::from_shape_vec((1, 1), vec![measurement_noise]).unwrap();

        // Initial state
        let x = Array1::from_vec(vec![initial_price, 0.0]);
        let p = Array2::from_shape_vec((2, 2), vec![1.0, 0.0, 0.0, 1.0]).unwrap();

        Self {
            params: KalmanParams { f, h, q, r },
            state: KalmanState { x, p },
        }
    }

    /// Predict step
    /// x_pred = F * x
    /// P_pred = F * P * F^T + Q
    pub fn predict(&mut self) {
        // Closed-form predict for the fixed 2-state model [price, velocity].
        let price = self.state.x[0];
        let velocity = self.state.x[1];
        self.state.x[0] = price + velocity;
        self.state.x[1] = velocity;

        let p00 = self.state.p[[0, 0]];
        let p01 = self.state.p[[0, 1]];
        let p10 = self.state.p[[1, 0]];
        let p11 = self.state.p[[1, 1]];
        let q00 = self.params.q[[0, 0]];
        let q11 = self.params.q[[1, 1]];

        self.state.p[[0, 0]] = p00 + p01 + p10 + p11 + q00;
        self.state.p[[0, 1]] = p01 + p11;
        self.state.p[[1, 0]] = p10 + p11;
        self.state.p[[1, 1]] = p11 + q11;
    }

    /// Update step with measurement
    /// K = P_pred * H^T * (H * P_pred * H^T + R)^{-1}
    /// x = x_pred + K * (z - H * x_pred)
    /// P = (I - K * H) * P_pred
    pub fn update(&mut self, measurement: f64) {
        // Closed-form update for scalar observation z = price.
        let y = measurement - self.state.x[0];
        let s = self.state.p[[0, 0]] + self.params.r[[0, 0]];

        let (k0, k1) = if s.abs() > 1e-10 {
            (self.state.p[[0, 0]] / s, self.state.p[[1, 0]] / s)
        } else {
            (0.0, 0.0)
        };

        self.state.x[0] += k0 * y;
        self.state.x[1] += k1 * y;

        let p00 = self.state.p[[0, 0]];
        let p01 = self.state.p[[0, 1]];
        let p11 = self.state.p[[1, 1]];

        let new_p00 = (1.0 - k0) * p00;
        let new_p01 = (1.0 - k0) * p01;
        let new_p11 = p11 - k1 * p01;

        self.state.p[[0, 0]] = new_p00;
        self.state.p[[0, 1]] = new_p01;
        self.state.p[[1, 0]] = new_p01;
        self.state.p[[1, 1]] = new_p11;
    }

    /// Complete step: predict + update
    /// Returns (denoised_price, velocity, uncertainty)
    pub fn step(&mut self, measurement: f64) -> (f64, f64, f64) {
        self.predict();
        self.update(measurement);

        let denoised_price = self.state.x[0];
        let velocity = self.state.x[1];
        let uncertainty = self.state.p[[0, 0]].sqrt();

        (denoised_price, velocity, uncertainty)
    }

    /// Smooth entire price series
    pub fn smooth_series(&mut self, prices: &[f64]) -> Vec<(f64, f64, f64)> {
        let mut results = Vec::with_capacity(prices.len());

        for &price in prices {
            results.push(self.step(price));
        }

        results
    }

    /// Get current trend direction
    pub fn trend_direction(&self) -> Direction {
        let velocity = self.state.x[1];
        if velocity > 0.0 {
            Direction::Bull
        } else if velocity < 0.0 {
            Direction::Bear
        } else {
            Direction::Neutral
        }
    }

    /// Get current denoised price
    pub fn current_price(&self) -> f64 {
        self.state.x[0]
    }

    /// Get current velocity
    pub fn current_velocity(&self) -> f64 {
        self.state.x[1]
    }

    /// Pseudo-inverse for 1x1 matrix (simplified)
    pub(crate) fn pseudo_inverse(&self, m: &Array2<f64>) -> Array2<f64> {
        if m.shape() == [1, 1] {
            let val = if m[[0, 0]].abs() > 1e-10 {
                1.0 / m[[0, 0]]
            } else {
                0.0
            };
            Array2::from_shape_vec((1, 1), vec![val]).unwrap()
        } else {
            // For larger matrices, use a more sophisticated approach
            // This is a simplified version
            let det = m[[0, 0]] * m[[1, 1]] - m[[0, 1]] * m[[1, 0]];
            if det.abs() < 1e-10 {
                Array2::zeros(m.raw_dim())
            } else {
                let inv_det = 1.0 / det;
                Array2::from_shape_vec(
                    (2, 2),
                    vec![
                        m[[1, 1]] * inv_det,
                        -m[[0, 1]] * inv_det,
                        -m[[1, 0]] * inv_det,
                        m[[0, 0]] * inv_det,
                    ],
                )
                .unwrap()
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::KalmanFilter;
    use ndarray::{Array1, Array2};

    fn reference_smooth_series(prices: &[f64]) -> Vec<(f64, f64, f64)> {
        let f = Array2::from_shape_vec((2, 2), vec![1.0, 1.0, 0.0, 1.0]).unwrap();
        let h = Array2::from_shape_vec((1, 2), vec![1.0, 0.0]).unwrap();
        let q = Array2::from_shape_vec((2, 2), vec![1e-3, 0.0, 0.0, 1e-4]).unwrap();
        let r = Array2::from_shape_vec((1, 1), vec![1e-2]).unwrap();
        let mut x = Array1::from_vec(vec![prices[0], 0.0]);
        let mut p = Array2::from_shape_vec((2, 2), vec![1.0, 0.0, 0.0, 1.0]).unwrap();
        let mut out = Vec::with_capacity(prices.len());

        for &measurement in prices {
            x = f.dot(&x);
            let fp = f.dot(&p);
            p = fp.dot(&f.t()) + &q;

            let z = Array1::from_vec(vec![measurement]);
            let hx = h.dot(&x);
            let y = &z - &hx;
            let hp = h.dot(&p);
            let s = hp.dot(&h.t()) + &r;
            let pht = p.dot(&h.t());
            let s_inv = if s[[0, 0]].abs() > 1e-10 {
                Array2::from_shape_vec((1, 1), vec![1.0 / s[[0, 0]]]).unwrap()
            } else {
                Array2::zeros((1, 1))
            };
            let k = pht.dot(&s_inv);
            x = &x + k.dot(&y);
            let kh = k.dot(&h);
            let i = Array2::<f64>::eye(2);
            p = (&i - &kh).dot(&p);

            out.push((x[0], x[1], p[[0, 0]].sqrt()));
        }

        out
    }

    #[test]
    fn smooth_series_matches_reference_matrix_math() {
        let prices = vec![100.0, 100.5, 99.8, 101.2, 100.9, 102.0];
        let mut filter = KalmanFilter::new(prices[0], 1e-3, 1e-4, 1e-2);

        let actual = filter.smooth_series(&prices);
        let expected = reference_smooth_series(&prices);

        assert_eq!(actual.len(), expected.len());
        for (actual_step, expected_step) in actual.iter().zip(expected.iter()) {
            assert!((actual_step.0 - expected_step.0).abs() < 1e-9);
            assert!((actual_step.1 - expected_step.1).abs() < 1e-9);
            assert!((actual_step.2 - expected_step.2).abs() < 1e-9);
        }
    }
}
