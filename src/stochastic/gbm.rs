use pyo3::prelude::*;
use rayon::prelude::*;

use super::rng::generate_normals;

/// Geometric Brownian Motion path generator for stock prices.
///
/// Models stock prices using the stochastic differential equation:
///     dS(t) = μ S(t) dt + σ S(t) dW(t)
///
/// Solution (Ito's lemma):
///     S(t) = S(0) * exp[(μ - σ²/2)t + σW(t)]
#[pyclass]
#[derive(Clone)]
pub struct GeometricBrownianMotion {
    /// Initial stock price S(0)
    spot: f64,
    /// Drift rate μ (typically risk-free rate for risk-neutral pricing)
    drift: f64,
    /// Volatility σ
    volatility: f64,
    /// Time horizon T
    time_horizon: f64,
    /// Number of time steps
    num_steps: usize,
}

#[pymethods]
impl GeometricBrownianMotion {
    /// Create a new GBM path generator.
    ///
    /// Args:
    ///     spot: Initial stock price S(0)
    ///     drift: Drift rate μ (use risk_free_rate for risk-neutral pricing)
    ///     volatility: Volatility σ (annual, as decimal e.g., 0.2 for 20%)
    ///     time_horizon: Time horizon T in years
    ///     num_steps: Number of discrete time steps
    ///
    /// Examples:
    ///     ```python
    ///     # Stock starting at $100, 5% drift, 20% vol, 1 year, daily steps
    ///     gbm = GeometricBrownianMotion(
    ///         spot=100.0,
    ///         drift=0.05,
    ///         volatility=0.2,
    ///         time_horizon=1.0,
    ///         num_steps=252
    ///     )
    ///     ```
    #[new]
    pub fn new(
        spot: f64,
        drift: f64,
        volatility: f64,
        time_horizon: f64,
        num_steps: usize,
    ) -> Self {
        assert!(spot > 0.0, "spot must be positive");
        assert!(volatility >= 0.0, "volatility must be non-negative");
        assert!(time_horizon > 0.0, "time_horizon must be positive");
        assert!(num_steps > 0, "num_steps must be positive");

        GeometricBrownianMotion {
            spot,
            drift,
            volatility,
            time_horizon,
            num_steps,
        }
    }

    /// Generate a single stock price path.
    ///
    /// Returns:
    ///     Vector of S(t) values at each time step (length = num_steps + 1)
    pub fn generate_path(&self) -> Vec<f64> {
        self.generate_path_impl()
    }

    /// Generate multiple independent stock price paths.
    ///
    /// Args:
    ///     num_paths: Number of independent paths to generate
    ///
    /// Returns:
    ///     Vector of paths, each containing stock prices at each time step
    pub fn generate_paths(&self, num_paths: usize) -> Vec<Vec<f64>> {
        (0..num_paths).map(|_| self.generate_path_impl()).collect()
    }

    /// Generate multiple paths in parallel (optimized for Monte Carlo).
    ///
    /// Args:
    ///     num_paths: Number of paths to generate
    ///
    /// Returns:
    ///     Vector of paths (parallel generation for speed)
    ///
    /// Performance:
    ///     Recommended for num_paths > 100. Uses Rayon for multi-core execution.
    pub fn generate_paths_parallel(&self, num_paths: usize) -> Vec<Vec<f64>> {
        (0..num_paths)
            .into_par_iter()
            .map(|_| self.generate_path_impl())
            .collect()
    }

    /// Get time grid.
    pub fn time_grid(&self) -> Vec<f64> {
        let dt = self.time_horizon / self.num_steps as f64;
        (0..=self.num_steps).map(|i| i as f64 * dt).collect()
    }

    /// Get time step size.
    pub fn dt(&self) -> f64 {
        self.time_horizon / self.num_steps as f64
    }

    /// Generate antithetic paths for variance reduction.
    ///
    /// Returns:
    ///     Tuple of (path, antithetic_path)
    pub fn generate_antithetic_paths(&self) -> (Vec<f64>, Vec<f64>) {
        let dt = self.time_horizon / self.num_steps as f64;
        let dt_sqrt = dt.sqrt();
        let increments = generate_normals(self.num_steps);

        // Drift term: (μ - σ²/2) * Δt
        let drift_term = (self.drift - 0.5 * self.volatility * self.volatility) * dt;
        let vol_term = self.volatility * dt_sqrt;

        let mut path = Vec::with_capacity(self.num_steps + 1);
        let mut antithetic_path = Vec::with_capacity(self.num_steps + 1);

        path.push(self.spot);
        antithetic_path.push(self.spot);

        let mut s = self.spot;
        let mut s_anti = self.spot;

        for &z in increments.iter() {
            // S(t+Δt) = S(t) * exp[(μ - σ²/2)Δt + σ√Δt * Z]
            s *= (drift_term + vol_term * z).exp();
            s_anti *= (drift_term + vol_term * (-z)).exp(); // Antithetic

            path.push(s);
            antithetic_path.push(s_anti);
        }

        (path, antithetic_path)
    }

    /// Get final prices from multiple paths.
    ///
    /// Args:
    ///     num_paths: Number of paths to simulate
    ///
    /// Returns:
    ///     Vector of terminal stock prices S(T)
    pub fn terminal_prices(&self, num_paths: usize) -> Vec<f64> {
        (0..num_paths)
            .into_par_iter()
            .map(|_| {
                let path = self.generate_path_impl();
                *path.last().unwrap()
            })
            .collect()
    }

    /// Get initial spot price.
    pub fn get_spot(&self) -> f64 {
        self.spot
    }

    /// Get drift rate.
    pub fn get_drift(&self) -> f64 {
        self.drift
    }

    /// Get volatility.
    pub fn get_volatility(&self) -> f64 {
        self.volatility
    }

    /// Get time horizon.
    pub fn get_time_horizon(&self) -> f64 {
        self.time_horizon
    }

    /// Get number of steps.
    pub fn get_num_steps(&self) -> usize {
        self.num_steps
    }
}

impl GeometricBrownianMotion {
    /// Internal path generation implementation
    fn generate_path_impl(&self) -> Vec<f64> {
        let dt = self.time_horizon / self.num_steps as f64;
        let dt_sqrt = dt.sqrt();
        let increments = generate_normals(self.num_steps);

        // Drift term: (μ - σ²/2) * Δt
        let drift_term = (self.drift - 0.5 * self.volatility * self.volatility) * dt;
        let vol_term = self.volatility * dt_sqrt;

        let mut path = Vec::with_capacity(self.num_steps + 1);
        path.push(self.spot);

        let mut s = self.spot;
        for &z in increments.iter() {
            // S(t+Δt) = S(t) * exp[(μ - σ²/2)Δt + σ√Δt * Z]
            s *= (drift_term + vol_term * z).exp();
            path.push(s);
        }

        path
    }
}
