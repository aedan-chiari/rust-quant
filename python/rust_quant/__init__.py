"""Rust-Quant: High-performance quantitative finance library.

Built with Rust (PyO3) for fast derivatives pricing and financial calculations.
"""

# This file tells Python that this directory is a package.
# The actual implementation is in the Rust extension module.
from rust_quant.rust_quant import (
    AmericanCallOption,
    AmericanOption,
    AmericanPutOption,
    BrownianMotion,
    EuroCallOption,
    EuroOption,
    EuroPutOption,
    ForwardCurve,
    GeometricBrownianMotion,
    HestonProcess,
    OptionGreeks,
    Security,
    StochasticRng,
    ZeroCouponCurve,
    monte_carlo_standard_error,
)

__all__ = [
    "AmericanCallOption",
    "AmericanOption",
    "AmericanPutOption",
    "BrownianMotion",
    "EuroCallOption",
    "EuroOption",
    "EuroPutOption",
    "ForwardCurve",
    "GeometricBrownianMotion",
    "HestonProcess",
    "OptionGreeks",
    "Security",
    "StochasticRng",
    "ZeroCouponCurve",
    "monte_carlo_standard_error",
]
