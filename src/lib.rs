use pyo3::prelude::*;

// Shared modules (types, SIMD, vectorized operations)
mod simd;
mod types;
mod vectorized;

// European options module
mod european;

// American options module
mod american;

// Zero coupon curve module
mod zero_coupon;

// Stochastic processes module
mod stochastic;

use american::{AmericanCallOption, AmericanOption, AmericanPutOption};
use european::{EuroCallOption, EuroOption, EuroPutOption};
use stochastic::{
    monte_carlo::monte_carlo_standard_error, BrownianMotion, GeometricBrownianMotion,
    HestonProcess, StochasticRng,
};
use types::OptionGreeks;
use zero_coupon::{ForwardCurve, InterpolationMethod, Security, ZeroCouponCurve};

/// A Python module implemented in Rust for high-performance option pricing
///
/// This module provides object-oriented option pricing classes:
///
/// European Options (Black-Scholes):
/// - EuroOption: Simple class for one-off European option calculations
/// - EuroCallOption: European call with SIMD+parallel batch operations
/// - EuroPutOption: European put with SIMD+parallel batch operations
///
/// American Options (Binomial Tree):
/// - AmericanOption: Simple class for American options
/// - AmericanCallOption: American call with early exercise
/// - AmericanPutOption: American put with early exercise
///
/// Zero Coupon Curves:
/// - ZeroCouponCurve: Yield curve construction from securities
/// - ForwardCurve: Forward rate calculations from zero-coupon curve
/// - Security: Represents a zero-coupon bond
///
/// Data Types:
/// - OptionGreeks: Container for option price and all Greeks
#[pymodule]
fn rust_quant(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // European options
    m.add_class::<EuroOption>()?;
    m.add_class::<EuroCallOption>()?;
    m.add_class::<EuroPutOption>()?;

    // American options
    m.add_class::<AmericanOption>()?;
    m.add_class::<AmericanCallOption>()?;
    m.add_class::<AmericanPutOption>()?;

    // Zero coupon curves
    m.add_class::<Security>()?;
    m.add_class::<ZeroCouponCurve>()?;
    m.add_class::<ForwardCurve>()?;
    m.add_class::<InterpolationMethod>()?;

    // Stochastic processes
    m.add_class::<StochasticRng>()?;
    m.add_class::<BrownianMotion>()?;
    m.add_class::<GeometricBrownianMotion>()?;
    m.add_class::<HestonProcess>()?;

    // Monte Carlo utilities
    m.add_function(wrap_pyfunction!(monte_carlo_standard_error, m)?)?;

    // Data types
    m.add_class::<OptionGreeks>()?;
    Ok(())
}
