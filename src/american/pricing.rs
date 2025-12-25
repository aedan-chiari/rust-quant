/// Shared American option pricing logic using binomial tree model
pub fn binomial_tree_price(
    spot: f64,
    strike: f64,
    time_to_expiry: f64,
    risk_free_rate: f64,
    volatility: f64,
    dividend_yield: f64,
    is_call: bool,
    steps: usize,
) -> f64 {
    let dt = time_to_expiry / steps as f64;
    let u = (volatility * dt.sqrt()).exp();
    let d = 1.0 / u;
    let a = ((risk_free_rate - dividend_yield) * dt).exp();
    let p = (a - d) / (u - d);
    let discount = (-risk_free_rate * dt).exp();

    // Pre-compute powers of u and d for O(1) lookup instead of O(log n) computation
    let mut u_powers = vec![1.0; steps + 1];
    let mut d_powers = vec![1.0; steps + 1];
    for i in 1..=steps {
        u_powers[i] = u_powers[i - 1] * u;
        d_powers[i] = d_powers[i - 1] * d;
    }

    // Initialize asset prices at maturity
    let mut prices = vec![0.0; steps + 1];
    for i in 0..=steps {
        let s_t = spot * u_powers[i] * d_powers[steps - i];
        prices[i] = if is_call {
            (s_t - strike).max(0.0)
        } else {
            (strike - s_t).max(0.0)
        };
    }

    // Backward induction
    for step in (0..steps).rev() {
        for i in 0..=step {
            let s_t = spot * u_powers[i] * d_powers[step - i];
            let hold_value = discount * (p * prices[i + 1] + (1.0 - p) * prices[i]);
            let exercise_value = if is_call {
                (s_t - strike).max(0.0)
            } else {
                (strike - s_t).max(0.0)
            };
            prices[i] = hold_value.max(exercise_value);
        }
    }

    prices[0]
}
