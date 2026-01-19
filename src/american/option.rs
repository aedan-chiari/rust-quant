use crate::american::pricing::binomial_tree_price;
use crate::american::{AmericanCallOption, AmericanPutOption};
use pyo3::prelude::*;

/// Generic American Option class for simple one-off calculations.
///
/// This class can represent either calls or puts using the is_call parameter.
/// Uses binomial tree pricing for early exercise capability.
#[pyclass]
#[derive(Clone, Debug)]
pub struct AmericanOption {
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
    is_call: bool,
    #[pyo3(get)]
    dividend_yield: f64,
    #[pyo3(get)]
    steps: usize,
}

#[pymethods]
impl AmericanOption {
    /// Create a generic American option.
    ///
    /// Args:
    ///     spot: Current price of the underlying asset
    ///     strike: Strike price of the option
    ///     time_to_expiry: Time to expiration in years
    ///     risk_free_rate: Risk-free interest rate (as decimal, e.g., 0.05 for 5%)
    ///     volatility: Volatility of the underlying asset (as decimal, e.g., 0.2 for 20%)
    ///     is_call: True for call option, False for put option (default: True)
    ///     dividend_yield: Continuous dividend yield (as decimal, e.g., 0.02 for 2%, default 0.0)
    ///     steps: Number of steps in binomial tree (default 100)
    #[new]
    #[pyo3(signature = (spot, strike, time_to_expiry, risk_free_rate, volatility, is_call=true, dividend_yield=0.0, steps=100))]
    fn new(
        spot: f64,
        strike: f64,
        time_to_expiry: f64,
        risk_free_rate: f64,
        volatility: f64,
        is_call: bool,
        dividend_yield: f64,
        steps: usize,
    ) -> Self {
        AmericanOption {
            spot,
            strike,
            time_to_expiry,
            risk_free_rate,
            volatility,
            is_call,
            dividend_yield,
            steps,
        }
    }

    /// Calculate the American option price using binomial tree.
    fn price(&self) -> f64 {
        binomial_tree_price(
            self.spot,
            self.strike,
            self.time_to_expiry,
            self.risk_free_rate,
            self.volatility,
            self.dividend_yield,
            self.is_call,
            self.steps,
        )
    }

    /// Calculate delta using finite difference method.
    fn delta(&self) -> f64 {
        if self.is_call {
            AmericanCallOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
                self.steps,
            )
            .delta()
        } else {
            AmericanPutOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
                self.steps,
            )
            .delta()
        }
    }

    /// Calculate gamma using finite difference method.
    fn gamma(&self) -> f64 {
        if self.is_call {
            AmericanCallOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
                self.steps,
            )
            .gamma()
        } else {
            AmericanPutOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
                self.steps,
            )
            .gamma()
        }
    }

    /// Calculate vega using finite difference method.
    fn vega(&self) -> f64 {
        if self.is_call {
            AmericanCallOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
                self.steps,
            )
            .vega()
        } else {
            AmericanPutOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
                self.steps,
            )
            .vega()
        }
    }

    /// Calculate theta using finite difference method (per day).
    fn theta(&self) -> f64 {
        if self.is_call {
            AmericanCallOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
                self.steps,
            )
            .theta()
        } else {
            AmericanPutOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
                self.steps,
            )
            .theta()
        }
    }

    /// Calculate rho using finite difference method.
    fn rho(&self) -> f64 {
        if self.is_call {
            AmericanCallOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
                self.steps,
            )
            .rho()
        } else {
            AmericanPutOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
                self.steps,
            )
            .rho()
        }
    }

    /// Create new option with different spot price (immutable update).
    fn with_spot(&self, new_spot: f64) -> Self {
        AmericanOption {
            spot: new_spot,
            ..self.clone()
        }
    }

    /// Create new option with different volatility (immutable update).
    fn with_volatility(&self, new_volatility: f64) -> Self {
        AmericanOption {
            volatility: new_volatility,
            ..self.clone()
        }
    }

    /// Create new option with different time to expiry (immutable update).
    fn with_time(&self, new_time: f64) -> Self {
        AmericanOption {
            time_to_expiry: new_time,
            ..self.clone()
        }
    }

    /// Create new option with different number of binomial tree steps (immutable update).
    fn with_steps(&self, new_steps: usize) -> Self {
        AmericanOption {
            steps: new_steps,
            ..self.clone()
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "AmericanOption(spot={:.2}, strike={:.2}, time={:.2}, rate={:.4}, vol={:.4}, div={:.4}, type={}, steps={})",
            self.spot, self.strike, self.time_to_expiry, self.risk_free_rate, self.volatility, self.dividend_yield,
            if self.is_call { "CALL" } else { "PUT" },
            self.steps
        )
    }
}
