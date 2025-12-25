/// Longstaff-Schwartz Monte Carlo algorithm for American options
///
/// The LSM algorithm prices American options by:
/// 1. Simulating forward paths
/// 2. Working backwards in time
/// 3. Using regression to estimate continuation value
/// 4. Comparing exercise vs continuation at each step
///
/// Reference: Longstaff & Schwartz (2001), "Valuing American Options by Simulation"
use rayon::prelude::*;

use super::gbm::GeometricBrownianMotion;

/// Longstaff-Schwartz pricing for American call option
///
/// # Arguments
/// * `spot` - Initial stock price
/// * `strike` - Strike price
/// * `risk_free_rate` - Risk-free rate
/// * `volatility` - Volatility
/// * `time_to_expiry` - Time to expiration
/// * `num_paths` - Number of simulation paths
/// * `num_steps` - Number of time steps (more = better early exercise detection)
///
/// # Returns
/// American call option price
pub fn american_call_lsm(
    spot: f64,
    strike: f64,
    risk_free_rate: f64,
    volatility: f64,
    time_to_expiry: f64,
    num_paths: usize,
    num_steps: usize,
) -> f64 {
    // Generate stock price paths
    let gbm =
        GeometricBrownianMotion::new(spot, risk_free_rate, volatility, time_to_expiry, num_steps);

    let paths = gbm.generate_paths_parallel(num_paths);
    let dt = time_to_expiry / num_steps as f64;
    let discount_factor = (-risk_free_rate * dt).exp();

    // Cash flow matrix: when option is exercised, what's the payoff?
    let mut cash_flows = vec![vec![0.0; num_steps + 1]; num_paths];

    // Terminal payoffs (always can exercise at maturity)
    for i in 0..num_paths {
        let terminal_price = paths[i][num_steps];
        cash_flows[i][num_steps] = (terminal_price - strike).max(0.0);
    }

    // Work backwards through time
    for t in (1..num_steps).rev() {
        // Find paths where option is in-the-money (early exercise possible)
        let itm_paths: Vec<usize> = (0..num_paths).filter(|&i| paths[i][t] > strike).collect();

        if itm_paths.is_empty() {
            continue; // No early exercise opportunity
        }

        // Extract stock prices and continuation values for ITM paths
        let x: Vec<f64> = itm_paths.iter().map(|&i| paths[i][t]).collect();
        let y: Vec<f64> = itm_paths
            .iter()
            .map(|&i| {
                // Discounted future cash flow (continuation value)
                let mut future_cf = 0.0;
                for s in (t + 1)..=num_steps {
                    if cash_flows[i][s] > 0.0 {
                        future_cf = cash_flows[i][s] * discount_factor.powi((s - t) as i32);
                        break;
                    }
                }
                future_cf
            })
            .collect();

        // Polynomial regression: E[continuation] = a + b*S + c*S^2
        let continuation_values = polynomial_regression(&x, &y);

        // Early exercise decision
        for (idx, &path_idx) in itm_paths.iter().enumerate() {
            let intrinsic = paths[path_idx][t] - strike;
            let continuation = continuation_values[idx];

            if intrinsic > continuation {
                // Exercise now
                cash_flows[path_idx][t] = intrinsic;
                // Zero out future cash flows (already exercised)
                for s in (t + 1)..=num_steps {
                    cash_flows[path_idx][s] = 0.0;
                }
            }
        }
    }

    // Discount cash flows to present value
    let option_value: f64 = (0..num_paths)
        .into_par_iter()
        .map(|i| {
            for t in 0..=num_steps {
                if cash_flows[i][t] > 0.0 {
                    return cash_flows[i][t] * (-risk_free_rate * t as f64 * dt).exp();
                }
            }
            0.0
        })
        .sum::<f64>()
        / num_paths as f64;

    option_value
}

/// Longstaff-Schwartz pricing for American put option
pub fn american_put_lsm(
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

    let paths = gbm.generate_paths_parallel(num_paths);
    let dt = time_to_expiry / num_steps as f64;
    let discount_factor = (-risk_free_rate * dt).exp();

    let mut cash_flows = vec![vec![0.0; num_steps + 1]; num_paths];

    // Terminal payoffs
    for i in 0..num_paths {
        let terminal_price = paths[i][num_steps];
        cash_flows[i][num_steps] = (strike - terminal_price).max(0.0);
    }

    // Work backwards
    for t in (1..num_steps).rev() {
        // ITM for puts: S < K
        let itm_paths: Vec<usize> = (0..num_paths).filter(|&i| paths[i][t] < strike).collect();

        if itm_paths.is_empty() {
            continue;
        }

        let x: Vec<f64> = itm_paths.iter().map(|&i| paths[i][t]).collect();
        let y: Vec<f64> = itm_paths
            .iter()
            .map(|&i| {
                let mut future_cf = 0.0;
                for s in (t + 1)..=num_steps {
                    if cash_flows[i][s] > 0.0 {
                        future_cf = cash_flows[i][s] * discount_factor.powi((s - t) as i32);
                        break;
                    }
                }
                future_cf
            })
            .collect();

        let continuation_values = polynomial_regression(&x, &y);

        for (idx, &path_idx) in itm_paths.iter().enumerate() {
            let intrinsic = strike - paths[path_idx][t];
            let continuation = continuation_values[idx];

            if intrinsic > continuation {
                cash_flows[path_idx][t] = intrinsic;
                for s in (t + 1)..=num_steps {
                    cash_flows[path_idx][s] = 0.0;
                }
            }
        }
    }

    let option_value: f64 = (0..num_paths)
        .into_par_iter()
        .map(|i| {
            for t in 0..=num_steps {
                if cash_flows[i][t] > 0.0 {
                    return cash_flows[i][t] * (-risk_free_rate * t as f64 * dt).exp();
                }
            }
            0.0
        })
        .sum::<f64>()
        / num_paths as f64;

    option_value
}

/// Polynomial regression: fit E[Y] = a + b*X + c*X^2
///
/// Uses least squares to estimate continuation value as function of stock price
fn polynomial_regression(x: &[f64], y: &[f64]) -> Vec<f64> {
    let n = x.len() as f64;

    if x.is_empty() {
        return vec![];
    }

    // Compute sums for normal equations
    let sum_x: f64 = x.iter().sum();
    let sum_y: f64 = y.iter().sum();
    let sum_x2: f64 = x.iter().map(|&xi| xi * xi).sum();
    let sum_x3: f64 = x.iter().map(|&xi| xi * xi * xi).sum();
    let sum_x4: f64 = x.iter().map(|&xi| xi * xi * xi * xi).sum();
    let sum_xy: f64 = x.iter().zip(y.iter()).map(|(&xi, &yi)| xi * yi).sum();
    let sum_x2y: f64 = x.iter().zip(y.iter()).map(|(&xi, &yi)| xi * xi * yi).sum();

    // Normal equations matrix (3x3)
    // [n    sum_x   sum_x2 ] [a]   [sum_y  ]
    // [sum_x sum_x2 sum_x3 ] [b] = [sum_xy ]
    // [sum_x2 sum_x3 sum_x4] [c]   [sum_x2y]

    // Solve using Cramer's rule (for 3x3 system)
    let det = n * (sum_x2 * sum_x4 - sum_x3 * sum_x3) - sum_x * (sum_x * sum_x4 - sum_x2 * sum_x3)
        + sum_x2 * (sum_x * sum_x3 - sum_x2 * sum_x2);

    if det.abs() < 1e-10 {
        // Singular matrix - fall back to mean
        let mean_y = sum_y / n;
        return vec![mean_y; x.len()];
    }

    let det_a = sum_y * (sum_x2 * sum_x4 - sum_x3 * sum_x3)
        - sum_x * (sum_xy * sum_x4 - sum_x2y * sum_x3)
        + sum_x2 * (sum_xy * sum_x3 - sum_x2y * sum_x2);

    let det_b = n * (sum_xy * sum_x4 - sum_x2y * sum_x3)
        - sum_y * (sum_x * sum_x4 - sum_x2 * sum_x3)
        + sum_x2 * (sum_x * sum_x2y - sum_xy * sum_x2);

    let det_c = n * (sum_x2 * sum_x2y - sum_x3 * sum_xy)
        - sum_x * (sum_x * sum_x2y - sum_x2 * sum_xy)
        + sum_y * (sum_x * sum_x3 - sum_x2 * sum_x2);

    let a = det_a / det;
    let b = det_b / det;
    let c = det_c / det;

    // Evaluate polynomial at each x value
    x.iter().map(|&xi| a + b * xi + c * xi * xi).collect()
}
