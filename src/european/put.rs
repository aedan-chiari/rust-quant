use crate::stochastic::monte_carlo;
use crate::types::{OptionCalculations, OptionGreeks};
use crate::vectorized::{greeks_puts_fast_impl, price_puts_fast_impl};
use pyo3::prelude::*;
use statrs::distribution::{ContinuousCDF, Normal};

/// European Put Option with Black-Scholes pricing.
///
/// For single options, use instance methods.
/// For batch operations (multiple options), use static methods with SIMD+parallel optimization.
#[pyclass]
#[derive(Clone, Debug)]
pub struct EuroPutOption {
    #[pyo3(get)]
    spot: f64,
    #[pyo3(get)]
    strike: f64,
    #[pyo3(get)]
    time_to_expiry: f64,
    #[pyo3(get)]
    risk_free_rate: f64,
    #[pyo3(get)]
    volatility: f64,
    #[pyo3(get)]
    dividend_yield: f64,
}

impl OptionCalculations for EuroPutOption {
    fn get_params(&self) -> (f64, f64, f64, f64, f64, f64) {
        (
            self.spot,
            self.strike,
            self.time_to_expiry,
            self.risk_free_rate,
            self.volatility,
            self.dividend_yield,
        )
    }
}

#[pymethods]
impl EuroPutOption {
    /// Create a European put option.
    ///
    /// Args:
    ///     spot: Current price of the underlying asset
    ///     strike: Strike price of the option
    ///     time_to_expiry: Time to expiration in years
    ///     risk_free_rate: Risk-free interest rate (as decimal, e.g., 0.05 for 5%)
    ///     volatility: Volatility of the underlying asset (as decimal, e.g., 0.2 for 20%)
    ///     dividend_yield: Continuous dividend yield (as decimal, e.g., 0.02 for 2%, default 0.0)
    #[new]
    #[pyo3(signature = (spot, strike, time_to_expiry, risk_free_rate, volatility, dividend_yield=0.0))]
    pub fn new(
        spot: f64,
        strike: f64,
        time_to_expiry: f64,
        risk_free_rate: f64,
        volatility: f64,
        dividend_yield: f64,
    ) -> Self {
        EuroPutOption {
            spot,
            strike,
            time_to_expiry,
            risk_free_rate,
            volatility,
            dividend_yield,
        }
    }

    /// Calculate the Black-Scholes put option price.
    pub fn price(&self) -> f64 {
        let d1 = self.d1();
        let d2 = self.d2();
        let normal = Normal::new(0.0, 1.0).unwrap();

        self.strike * (-self.risk_free_rate * self.time_to_expiry).exp() * normal.cdf(-d2)
            - self.spot * (-self.dividend_yield * self.time_to_expiry).exp() * normal.cdf(-d1)
    }

    /// Calculate delta: sensitivity to underlying price change.
    /// For puts, delta ranges from -1 to 0.
    pub fn delta(&self) -> f64 {
        let d1 = self.d1();
        let normal = Normal::new(0.0, 1.0).unwrap();
        (-self.dividend_yield * self.time_to_expiry).exp() * (normal.cdf(d1) - 1.0)
    }

    /// Calculate theta: time decay per day.
    /// Can be positive or negative for puts depending on moneyness.
    pub fn theta(&self) -> f64 {
        let d1 = self.d1();
        let d2 = self.d2();
        let normal = Normal::new(0.0, 1.0).unwrap();
        let pdf = self.standard_normal_pdf(d1);

        let term1 = -(self.spot
            * (-self.dividend_yield * self.time_to_expiry).exp()
            * pdf
            * self.volatility)
            / (2.0 * self.time_to_expiry.sqrt());
        let term2 = self.risk_free_rate
            * self.strike
            * (-self.risk_free_rate * self.time_to_expiry).exp()
            * normal.cdf(-d2);
        let term3 = self.dividend_yield
            * self.spot
            * (-self.dividend_yield * self.time_to_expiry).exp()
            * normal.cdf(-d1);
        (term1 + term2 - term3) / 365.0
    }

    /// Calculate rho: sensitivity to interest rate change.
    /// Negative for puts (higher rates decrease put value).
    pub fn rho(&self) -> f64 {
        let d2 = self.d2();
        let normal = Normal::new(0.0, 1.0).unwrap();
        -self.strike
            * self.time_to_expiry
            * (-self.risk_free_rate * self.time_to_expiry).exp()
            * normal.cdf(-d2)
            / 100.0
    }

    /// Calculate gamma: rate of change of delta.
    /// Identical for calls and puts at the same strike.
    pub fn gamma(&self) -> f64 {
        OptionCalculations::gamma(self)
    }

    /// Calculate vega: sensitivity to volatility change.
    /// Identical for calls and puts at the same strike.
    pub fn vega(&self) -> f64 {
        OptionCalculations::vega(self)
    }

    /// Calculate all Greeks and price in a single efficient call.
    /// More efficient than calling each method individually.
    pub fn greeks(&self) -> OptionGreeks {
        OptionGreeks {
            price: self.price(),
            delta: self.delta(),
            gamma: self.gamma(),
            vega: self.vega(),
            theta: self.theta(),
            rho: self.rho(),
        }
    }

    /// Create new option with different spot price (immutable update).
    fn with_spot(&self, new_spot: f64) -> Self {
        EuroPutOption {
            spot: new_spot,
            ..self.clone()
        }
    }

    /// Create new option with different volatility (immutable update).
    fn with_volatility(&self, new_volatility: f64) -> Self {
        EuroPutOption {
            volatility: new_volatility,
            ..self.clone()
        }
    }

    /// Create new option with different time to expiry (immutable update).
    fn with_time(&self, new_time: f64) -> Self {
        EuroPutOption {
            time_to_expiry: new_time,
            ..self.clone()
        }
    }

    /// Create new option with different strike price (immutable update).
    fn with_strike(&self, new_strike: f64) -> Self {
        EuroPutOption {
            strike: new_strike,
            ..self.clone()
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "EuroPutOption(spot={:.2}, strike={:.2}, time={:.2}, rate={:.4}, vol={:.4}, div={:.4})",
            self.spot,
            self.strike,
            self.time_to_expiry,
            self.risk_free_rate,
            self.volatility,
            self.dividend_yield
        )
    }

    /// SIMD and parallel pricing for multiple put options (optimized).
    ///
    /// Uses SIMD intrinsics (4x parallelism) and Rayon thread pool for maximum performance.
    /// Recommended for pricing 100+ options.
    ///
    /// Args:
    ///     spots: list of current prices
    ///     strikes: list of strike prices
    ///     times: list of times to expiration
    ///     rates: list of risk-free rates
    ///     vols: list of volatilities
    ///
    /// Returns:
    ///     list of put option prices
    ///
    /// Note: All input lists must have the same length.
    #[staticmethod]
    pub fn price_many(
        spots: Vec<f64>,
        strikes: Vec<f64>,
        times: Vec<f64>,
        rates: Vec<f64>,
        vols: Vec<f64>,
    ) -> PyResult<Vec<f64>> {
        price_puts_fast_impl(spots, strikes, times, rates, vols)
    }

    /// SIMD and parallel Greeks calculation for multiple put options (optimized).
    ///
    /// Uses SIMD intrinsics (4x parallelism) and Rayon thread pool for maximum performance.
    /// Recommended for calculating Greeks for 100+ options.
    ///
    /// Args:
    ///     spots: list of current prices
    ///     strikes: list of strike prices
    ///     times: list of times to expiration
    ///     rates: list of risk-free rates
    ///     vols: list of volatilities
    ///
    /// Returns:
    ///     tuple of (prices, deltas, gammas, vegas, thetas, rhos)
    ///     Each element is a list of floats with the same length as the inputs.
    ///
    /// Note: All input lists must have the same length.
    #[staticmethod]
    pub fn greeks_many(
        spots: Vec<f64>,
        strikes: Vec<f64>,
        times: Vec<f64>,
        rates: Vec<f64>,
        vols: Vec<f64>,
    ) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>)> {
        greeks_puts_fast_impl(spots, strikes, times, rates, vols)
    }

    /// Monte Carlo pricing for European put option.
    ///
    /// Alternative to Black-Scholes analytical formula using Monte Carlo simulation.
    /// Useful for validating results and educational purposes.
    ///
    /// Args:
    ///     num_paths: Number of Monte Carlo paths (default: 100000, higher = more accurate)
    ///     num_steps: Number of time steps (default: 1, sufficient for European options)
    ///
    /// Returns:
    ///     Option price estimated via Monte Carlo simulation
    ///
    /// Note:
    ///     For production use, the analytical price() method is more efficient.
    ///     Monte Carlo is more useful for path-dependent or exotic options.
    #[pyo3(signature = (num_paths=100000, num_steps=1))]
    pub fn price_monte_carlo(&self, num_paths: usize, num_steps: usize) -> f64 {
        monte_carlo::european_put_mc(
            self.spot,
            self.strike,
            self.risk_free_rate,
            self.volatility,
            self.time_to_expiry,
            num_paths,
            num_steps,
        )
    }

    /// Monte Carlo pricing with antithetic variance reduction.
    ///
    /// More accurate than standard Monte Carlo for same number of paths by using
    /// antithetic variates (pairs of paths with negated random shocks).
    ///
    /// Args:
    ///     num_paths: Number of path pairs (default: 100000)
    ///     num_steps: Number of time steps (default: 1)
    ///
    /// Returns:
    ///     Option price with reduced variance estimate
    ///
    /// Note:
    ///     Typically achieves 30-50% variance reduction compared to standard Monte Carlo.
    #[pyo3(signature = (num_paths=100000, num_steps=1))]
    pub fn price_monte_carlo_antithetic(&self, num_paths: usize, num_steps: usize) -> f64 {
        monte_carlo::european_put_mc_antithetic(
            self.spot,
            self.strike,
            self.risk_free_rate,
            self.volatility,
            self.time_to_expiry,
            num_paths,
            num_steps,
        )
    }

    /// Monte Carlo pricing with Heston stochastic volatility model.
    ///
    /// More realistic than constant volatility (Black-Scholes) as it captures:
    /// - Volatility clustering
    /// - Leverage effect (correlation between price and volatility)
    /// - Volatility smile/skew in option prices
    ///
    /// Args:
    ///     initial_variance: Initial variance v(0) = σ₀²
    ///     kappa: Mean reversion speed (how fast variance reverts to theta)
    ///     theta: Long-term variance (long-run average of v(t))
    ///     vol_of_vol: Volatility of volatility (how much variance fluctuates)
    ///     correlation: Correlation between price and variance (-1 to 1, typically negative)
    ///     num_paths: Number of simulation paths (default: 100000)
    ///     num_steps: Number of time steps (default: 100, higher for more accuracy)
    ///
    /// Returns:
    ///     Option price under Heston model
    #[pyo3(signature = (initial_variance, kappa, theta, vol_of_vol, correlation, num_paths=100000, num_steps=100))]
    #[allow(clippy::too_many_arguments)]
    pub fn price_heston(
        &self,
        initial_variance: f64,
        kappa: f64,
        theta: f64,
        vol_of_vol: f64,
        correlation: f64,
        num_paths: usize,
        num_steps: usize,
    ) -> f64 {
        monte_carlo::european_put_heston(
            self.spot,
            self.strike,
            self.risk_free_rate,
            initial_variance,
            kappa,
            theta,
            vol_of_vol,
            correlation,
            self.time_to_expiry,
            num_paths,
            num_steps,
        )
    }
}
