use crate::european::{EuroCallOption, EuroPutOption};
use crate::types::OptionGreeks;
use pyo3::prelude::*;

/// Generic European Option class for simple one-off calculations.
///
/// This class is designed for occasional single-option pricing. For batch operations,
/// use EuroCallOption or EuroPutOption classes which have optimized static methods.
#[pyclass]
#[derive(Clone, Debug)]
pub struct EuroOption {
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
}

#[pymethods]
impl EuroOption {
    /// Create a generic European option.
    ///
    /// Args:
    ///     spot: Current price of the underlying asset
    ///     strike: Strike price of the option
    ///     time_to_expiry: Time to expiration in years
    ///     risk_free_rate: Risk-free interest rate (as decimal, e.g., 0.05 for 5%)
    ///     volatility: Volatility of the underlying asset (as decimal, e.g., 0.2 for 20%)
    ///     is_call: True for call option, False for put option (default: True)
    ///     dividend_yield: Continuous dividend yield (as decimal, e.g., 0.02 for 2%, default 0.0)
    #[new]
    #[pyo3(signature = (spot, strike, time_to_expiry, risk_free_rate, volatility, is_call=true, dividend_yield=0.0))]
    fn new(
        spot: f64,
        strike: f64,
        time_to_expiry: f64,
        risk_free_rate: f64,
        volatility: f64,
        is_call: bool,
        dividend_yield: f64,
    ) -> Self {
        EuroOption {
            spot,
            strike,
            time_to_expiry,
            risk_free_rate,
            volatility,
            is_call,
            dividend_yield,
        }
    }

    /// Calculate the Black-Scholes option price.
    fn price(&self) -> f64 {
        if self.is_call {
            EuroCallOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
            )
            .price()
        } else {
            EuroPutOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
            )
            .price()
        }
    }

    /// Calculate delta: sensitivity to underlying price change.
    fn delta(&self) -> f64 {
        if self.is_call {
            EuroCallOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
            )
            .delta()
        } else {
            EuroPutOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
            )
            .delta()
        }
    }

    /// Calculate gamma: rate of change of delta.
    fn gamma(&self) -> f64 {
        if self.is_call {
            EuroCallOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
            )
            .gamma()
        } else {
            EuroPutOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
            )
            .gamma()
        }
    }

    /// Calculate vega: sensitivity to volatility change.
    fn vega(&self) -> f64 {
        if self.is_call {
            EuroCallOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
            )
            .vega()
        } else {
            EuroPutOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
            )
            .vega()
        }
    }

    /// Calculate theta: time decay per day.
    fn theta(&self) -> f64 {
        if self.is_call {
            EuroCallOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
            )
            .theta()
        } else {
            EuroPutOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
            )
            .theta()
        }
    }

    /// Calculate rho: sensitivity to interest rate change.
    fn rho(&self) -> f64 {
        if self.is_call {
            EuroCallOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
            )
            .rho()
        } else {
            EuroPutOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
            )
            .rho()
        }
    }

    /// Calculate all Greeks and price in a single efficient call.
    fn greeks(&self) -> OptionGreeks {
        if self.is_call {
            EuroCallOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
            )
            .greeks()
        } else {
            EuroPutOption::new(
                self.spot,
                self.strike,
                self.time_to_expiry,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
            )
            .greeks()
        }
    }

    /// Create new option with different spot price (immutable update).
    fn with_spot(&self, new_spot: f64) -> Self {
        EuroOption {
            spot: new_spot,
            ..self.clone()
        }
    }

    /// Create new option with different volatility (immutable update).
    fn with_volatility(&self, new_volatility: f64) -> Self {
        EuroOption {
            volatility: new_volatility,
            ..self.clone()
        }
    }

    /// Create new option with different time to expiry (immutable update).
    fn with_time(&self, new_time: f64) -> Self {
        EuroOption {
            time_to_expiry: new_time,
            ..self.clone()
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "EuroOption(spot={:.2}, strike={:.2}, time={:.2}, rate={:.4}, vol={:.4}, div={:.4}, type={})",
            self.spot, self.strike, self.time_to_expiry, self.risk_free_rate, self.volatility, self.dividend_yield,
            if self.is_call { "CALL" } else { "PUT" }
        )
    }
}
