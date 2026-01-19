/// Monte Carlo pricing for European options using simulated paths
///
/// Provides Monte Carlo estimation for option prices as an alternative to
/// Black-Scholes analytical formulas. Useful for:
/// - Validating analytical results
/// - Pricing complex payoffs
/// - Path-dependent options
/// - Comparison with stochastic volatility models
use pyo3::prelude::*;
use rayon::prelude::*;

use super::gbm::GeometricBrownianMotion;
use super::heston::HestonProcess;

/// Monte Carlo pricing for European call option using GBM
///
/// # Arguments
/// * `spot` - Initial stock price
/// * `strike` - Strike price
/// * `risk_free_rate` - Risk-free rate (as decimal)
/// * `volatility` - Volatility (as decimal)
/// * `time_to_expiry` - Time to expiration in years
/// * `num_paths` - Number of Monte Carlo paths (higher = more accurate)
/// * `num_steps` - Number of time steps per path (can be 1 for European)
///
/// # Returns
/// Option price estimate via Monte Carlo
pub fn european_call_mc(
    spot: f64,
    strike: f64,
    risk_free_rate: f64,
    volatility: f64,
    time_to_expiry: f64,
    num_paths: usize,
    num_steps: usize,
) -> f64 {
    let gbm =
        GeometricBrownianMotion::new(spot, risk_free_rate, volatility, time_to_expiry, num_steps);

    // Get terminal prices in parallel
    let terminal_prices = gbm.terminal_prices(num_paths);

    // Compute average payoff
    let avg_payoff: f64 = terminal_prices
        .par_iter()
        .map(|&s| (s - strike).max(0.0))
        .sum::<f64>()
        / num_paths as f64;

    // Discount to present value
    avg_payoff * (-risk_free_rate * time_to_expiry).exp()
}

/// Monte Carlo pricing for European put option using GBM
pub fn european_put_mc(
    spot: f64,
    strike: f64,
    risk_free_rate: f64,
    volatility: f64,
    time_to_expiry: f64,
    num_paths: usize,
    num_steps: usize,
) -> f64 {
    let gbm =
        GeometricBrownianMotion::new(spot, risk_free_rate, volatility, time_to_expiry, num_steps);

    let terminal_prices = gbm.terminal_prices(num_paths);

    let avg_payoff: f64 = terminal_prices
        .par_iter()
        .map(|&s| (strike - s).max(0.0))
        .sum::<f64>()
        / num_paths as f64;

    avg_payoff * (-risk_free_rate * time_to_expiry).exp()
}

/// Monte Carlo pricing for European call with antithetic variance reduction
pub fn european_call_mc_antithetic(
    spot: f64,
    strike: f64,
    risk_free_rate: f64,
    volatility: f64,
    time_to_expiry: f64,
    num_paths: usize,
    num_steps: usize,
) -> f64 {
    let gbm =
        GeometricBrownianMotion::new(spot, risk_free_rate, volatility, time_to_expiry, num_steps);

    // Generate pairs of antithetic paths
    let avg_payoff: f64 = (0..num_paths)
        .into_par_iter()
        .map(|_| {
            let (path1, path2) = gbm.generate_antithetic_paths();
            let s1 = *path1.last().unwrap();
            let s2 = *path2.last().unwrap();
            let payoff1 = (s1 - strike).max(0.0);
            let payoff2 = (s2 - strike).max(0.0);
            (payoff1 + payoff2) / 2.0 // Average the antithetic pair
        })
        .sum::<f64>()
        / num_paths as f64;

    avg_payoff * (-risk_free_rate * time_to_expiry).exp()
}

/// Monte Carlo pricing for European put with antithetic variance reduction
pub fn european_put_mc_antithetic(
    spot: f64,
    strike: f64,
    risk_free_rate: f64,
    volatility: f64,
    time_to_expiry: f64,
    num_paths: usize,
    num_steps: usize,
) -> f64 {
    let gbm =
        GeometricBrownianMotion::new(spot, risk_free_rate, volatility, time_to_expiry, num_steps);

    let avg_payoff: f64 = (0..num_paths)
        .into_par_iter()
        .map(|_| {
            let (path1, path2) = gbm.generate_antithetic_paths();
            let s1 = *path1.last().unwrap();
            let s2 = *path2.last().unwrap();
            let payoff1 = (strike - s1).max(0.0);
            let payoff2 = (strike - s2).max(0.0);
            (payoff1 + payoff2) / 2.0
        })
        .sum::<f64>()
        / num_paths as f64;

    avg_payoff * (-risk_free_rate * time_to_expiry).exp()
}

/// Monte Carlo pricing for European call using Heston stochastic volatility
pub fn european_call_heston(
    spot: f64,
    strike: f64,
    risk_free_rate: f64,
    initial_variance: f64,
    kappa: f64,
    theta: f64,
    vol_of_vol: f64,
    correlation: f64,
    time_to_expiry: f64,
    num_paths: usize,
    num_steps: usize,
) -> f64 {
    let heston = HestonProcess::new(
        spot,
        initial_variance,
        risk_free_rate,
        kappa,
        theta,
        vol_of_vol,
        correlation,
        time_to_expiry,
        num_steps,
    );

    let terminal_prices = heston.terminal_prices(num_paths);

    let avg_payoff: f64 = terminal_prices
        .par_iter()
        .map(|&s| (s - strike).max(0.0))
        .sum::<f64>()
        / num_paths as f64;

    avg_payoff * (-risk_free_rate * time_to_expiry).exp()
}

/// Monte Carlo pricing for European put using Heston stochastic volatility
pub fn european_put_heston(
    spot: f64,
    strike: f64,
    risk_free_rate: f64,
    initial_variance: f64,
    kappa: f64,
    theta: f64,
    vol_of_vol: f64,
    correlation: f64,
    time_to_expiry: f64,
    num_paths: usize,
    num_steps: usize,
) -> f64 {
    let heston = HestonProcess::new(
        spot,
        initial_variance,
        risk_free_rate,
        kappa,
        theta,
        vol_of_vol,
        correlation,
        time_to_expiry,
        num_steps,
    );

    let terminal_prices = heston.terminal_prices(num_paths);

    let avg_payoff: f64 = terminal_prices
        .par_iter()
        .map(|&s| (strike - s).max(0.0))
        .sum::<f64>()
        / num_paths as f64;

    avg_payoff * (-risk_free_rate * time_to_expiry).exp()
}

/// Calculate Monte Carlo standard error
///
/// Estimates the standard error of a Monte Carlo simulation, which indicates
/// the precision of the estimate. Lower standard error means higher confidence.
///
/// The standard error decreases as 1/√N where N is the number of samples.
/// To halve the standard error, you need 4x more paths.
///
/// # Arguments
/// * `values` - Vector of simulated values (e.g., option payoffs or prices)
///
/// # Returns
/// Standard error of the mean
///
/// # Formula
/// SE = σ / √N where σ is the sample standard deviation and N is sample size
///
/// # Example Usage (Python)
/// ```python
/// from rust_quant import monte_carlo_standard_error
///
/// # Run MC simulation multiple times to assess convergence
/// prices = [call.price_monte_carlo(10000) for _ in range(100)]
/// se = monte_carlo_standard_error(prices)
/// mean_price = sum(prices) / len(prices)
///
/// print(f"Price estimate: ${mean_price:.4f} ± ${1.96*se:.4f} (95% CI)")
/// ```
#[pyfunction]
pub fn monte_carlo_standard_error(values: Vec<f64>) -> f64 {
    let n = values.len() as f64;
    if n <= 1.0 {
        return 0.0;
    }
    let mean = values.iter().sum::<f64>() / n;
    let variance = values.iter().map(|&x| (x - mean).powi(2)).sum::<f64>() / (n - 1.0);
    (variance / n).sqrt()
}
