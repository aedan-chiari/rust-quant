use pyo3::prelude::*;
use rayon::prelude::*;

use super::rng::generate_correlated_normals;

/// Heston stochastic volatility model.
///
/// Models stock prices with stochastic volatility using coupled SDEs:
///     dS(t) = μ S(t) dt + √v(t) S(t) dW₁(t)
///     dv(t) = κ(θ - v(t)) dt + σᵥ √v(t) dW₂(t)
///
/// where:
///     - S(t): stock price
///     - v(t): variance (volatility squared)
///     - μ: drift rate
///     - κ: mean reversion speed
///     - θ: long-term variance
///     - σᵥ: volatility of volatility
///     - ρ: correlation between W₁ and W₂
///
/// More realistic than constant volatility (Black-Scholes) as it captures:
///     - Volatility clustering
///     - Leverage effect (correlation between price and volatility)
///     - Volatility smile/skew in option prices
#[pyclass]
#[derive(Clone)]
pub struct HestonProcess {
    /// Initial stock price S(0)
    spot: f64,
    /// Initial variance v(0)
    initial_variance: f64,
    /// Drift rate μ (typically risk-free rate)
    drift: f64,
    /// Mean reversion speed κ
    kappa: f64,
    /// Long-term variance θ
    theta: f64,
    /// Volatility of volatility σᵥ
    vol_of_vol: f64,
    /// Correlation ρ between price and variance Brownian motions
    correlation: f64,
    /// Time horizon T
    time_horizon: f64,
    /// Number of time steps
    num_steps: usize,
}

#[pymethods]
impl HestonProcess {
    /// Create a new Heston process path generator.
    ///
    /// Args:
    ///     spot: Initial stock price S(0)
    ///     initial_variance: Initial variance v(0) = σ₀²
    ///     drift: Drift rate μ (use risk_free_rate for risk-neutral pricing)
    ///     kappa: Mean reversion speed κ (how fast variance reverts to θ)
    ///     theta: Long-term variance θ (long-run average of v(t))
    ///     vol_of_vol: Volatility of volatility σᵥ (how much variance fluctuates)
    ///     correlation: Correlation ρ between price and variance (-1 to 1)
    ///     time_horizon: Time horizon T in years
    ///     num_steps: Number of discrete time steps
    ///
    /// Examples:
    ///     ```python
    ///     # Typical calibrated parameters for equity options
    ///     heston = HestonProcess(
    ///         spot=100.0,
    ///         initial_variance=0.04,    # Initial vol = 20%
    ///         drift=0.05,
    ///         kappa=2.0,                # Mean reversion speed
    ///         theta=0.04,               # Long-term vol = 20%
    ///         vol_of_vol=0.3,           # Volatility of volatility
    ///         correlation=-0.7,         # Negative correlation (leverage effect)
    ///         time_horizon=1.0,
    ///         num_steps=252
    ///     )
    ///     ```
    #[new]
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        spot: f64,
        initial_variance: f64,
        drift: f64,
        kappa: f64,
        theta: f64,
        vol_of_vol: f64,
        correlation: f64,
        time_horizon: f64,
        num_steps: usize,
    ) -> Self {
        assert!(spot > 0.0, "spot must be positive");
        assert!(
            initial_variance >= 0.0,
            "initial_variance must be non-negative"
        );
        assert!(kappa > 0.0, "kappa must be positive");
        assert!(theta >= 0.0, "theta must be non-negative");
        assert!(vol_of_vol >= 0.0, "vol_of_vol must be non-negative");
        assert!(
            correlation >= -1.0 && correlation <= 1.0,
            "correlation must be between -1 and 1"
        );
        assert!(time_horizon > 0.0, "time_horizon must be positive");
        assert!(num_steps > 0, "num_steps must be positive");

        // Feller condition check (for variance to stay positive)
        // 2κθ ≥ σᵥ²
        let feller = 2.0 * kappa * theta;
        let vol_sq = vol_of_vol * vol_of_vol;
        if feller < vol_sq {
            eprintln!(
                "Warning: Feller condition not satisfied (2κθ = {:.4} < σᵥ² = {:.4}). Variance may become negative.",
                feller, vol_sq
            );
        }

        HestonProcess {
            spot,
            initial_variance,
            drift,
            kappa,
            theta,
            vol_of_vol,
            correlation,
            time_horizon,
            num_steps,
        }
    }

    /// Generate a single path (price and variance).
    ///
    /// Returns:
    ///     Tuple of (price_path, variance_path) where each is a vector of values.
    ///     Uses Euler-Maruyama discretization with absorption at zero for variance.
    pub fn generate_path(&self) -> (Vec<f64>, Vec<f64>) {
        self.generate_path_impl()
    }

    /// Generate multiple independent paths.
    ///
    /// Args:
    ///     num_paths: Number of paths to generate
    ///
    /// Returns:
    ///     Vector of tuples (price_path, variance_path)
    pub fn generate_paths(&self, num_paths: usize) -> Vec<(Vec<f64>, Vec<f64>)> {
        (0..num_paths).map(|_| self.generate_path_impl()).collect()
    }

    /// Generate multiple paths in parallel (optimized).
    ///
    /// Args:
    ///     num_paths: Number of paths to generate
    ///
    /// Returns:
    ///     Vector of tuples (price_path, variance_path)
    pub fn generate_paths_parallel(&self, num_paths: usize) -> Vec<(Vec<f64>, Vec<f64>)> {
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

    /// Get terminal prices from multiple paths.
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
                let (price_path, _) = self.generate_path_impl();
                *price_path.last().unwrap()
            })
            .collect()
    }

    /// Get terminal prices and variances.
    ///
    /// Args:
    ///     num_paths: Number of paths
    ///
    /// Returns:
    ///     Tuple of (terminal_prices, terminal_variances)
    pub fn terminal_values(&self, num_paths: usize) -> (Vec<f64>, Vec<f64>) {
        let paths: Vec<(Vec<f64>, Vec<f64>)> = (0..num_paths)
            .into_par_iter()
            .map(|_| self.generate_path_impl())
            .collect();

        let prices: Vec<f64> = paths.iter().map(|(p, _)| *p.last().unwrap()).collect();
        let variances: Vec<f64> = paths.iter().map(|(_, v)| *v.last().unwrap()).collect();

        (prices, variances)
    }

    /// Get initial spot price.
    pub fn get_spot(&self) -> f64 {
        self.spot
    }

    /// Get initial variance.
    pub fn get_initial_variance(&self) -> f64 {
        self.initial_variance
    }

    /// Get drift rate.
    pub fn get_drift(&self) -> f64 {
        self.drift
    }

    /// Get mean reversion speed.
    pub fn get_kappa(&self) -> f64 {
        self.kappa
    }

    /// Get long-term variance.
    pub fn get_theta(&self) -> f64 {
        self.theta
    }

    /// Get volatility of volatility.
    pub fn get_vol_of_vol(&self) -> f64 {
        self.vol_of_vol
    }

    /// Get correlation.
    pub fn get_correlation(&self) -> f64 {
        self.correlation
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

impl HestonProcess {
    /// Internal path generation using Euler-Maruyama scheme
    ///
    /// Optimized implementation with:
    /// - Absorption at zero for variance (max(v, 0))
    /// - Correlated Brownian motions
    /// - Efficient memory allocation
    fn generate_path_impl(&self) -> (Vec<f64>, Vec<f64>) {
        let dt = self.time_horizon / self.num_steps as f64;
        let dt_sqrt = dt.sqrt();

        // Generate correlated random variables
        let (z1, z2) = generate_correlated_normals(self.num_steps, self.correlation);

        let mut price_path = Vec::with_capacity(self.num_steps + 1);
        let mut variance_path = Vec::with_capacity(self.num_steps + 1);

        price_path.push(self.spot);
        variance_path.push(self.initial_variance);

        let mut s = self.spot;
        let mut v = self.initial_variance;

        for i in 0..self.num_steps {
            // Ensure variance stays non-negative (absorption at zero)
            v = v.max(0.0);

            let sqrt_v = v.sqrt();

            // Variance process: dv = κ(θ - v)dt + σᵥ√v dW₂
            let dv =
                self.kappa * (self.theta - v) * dt + self.vol_of_vol * sqrt_v * dt_sqrt * z2[i];
            v += dv;

            // Absorb variance at zero after update
            v = v.max(0.0);

            // Price process: dS = μS dt + √v S dW₁
            let ds = self.drift * s * dt + sqrt_v * s * dt_sqrt * z1[i];
            s += ds;

            // Ensure price stays positive
            s = s.max(0.0);

            price_path.push(s);
            variance_path.push(v);
        }

        (price_path, variance_path)
    }
}
