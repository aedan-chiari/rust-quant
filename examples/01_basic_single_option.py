"""Example 1: Basic European Option Pricing.

This example demonstrates:
- Creating EuroCallOption and EuroPutOption objects
- Calculating price and individual Greeks
- Calculating all Greeks at once (more efficient)
- Using immutable update methods (with_spot, with_volatility, etc.)
"""

import logging
import math

from rust_quant import EuroCallOption, EuroPutOption

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def create_basic_options() -> tuple[EuroCallOption, EuroPutOption]:
    """Create and demonstrate basic European call and put options."""
    logger.info("\n1. Creating European Options")
    logger.info("-" * 70)

    # Create a European call option
    call = EuroCallOption(
        spot=100.0,  # Current stock price
        strike=105.0,  # Strike price
        time_to_expiry=1.0,  # Time to expiration (years)
        risk_free_rate=0.05,  # Risk-free interest rate (5%)
        volatility=0.2,  # Volatility (20%)
    )

    logger.info("European Call Option: %s", call)
    logger.info("  Price:  $%.4f", call.price())

    # Create a European put option with same parameters
    put = EuroPutOption(100.0, 105.0, 1.0, 0.05, 0.2)
    logger.info("\nEuropean Put Option: %s", put)
    logger.info("  Price:  $%.4f", put.price())

    return call, put


def demonstrate_individual_greeks(call: EuroCallOption) -> None:
    """Calculate and display individual Greeks for an option."""
    logger.info("\n\n2. Calculating Individual Greeks")
    logger.info("-" * 70)
    logger.info("Note: We reuse the same 'call' object - no wasteful re-creation!\n")

    logger.info("Delta (Δ):  %.4f  - Sensitivity to underlying price", call.delta())
    logger.info("Gamma (Γ):  %.4f  - Rate of change of delta", call.gamma())
    logger.info("Vega (ν):   %.4f   - Sensitivity to volatility", call.vega())
    logger.info("Theta (θ):  %.4f  - Time decay", call.theta())
    logger.info("Rho (ρ):    %.4f   - Sensitivity to interest rate", call.rho())


def demonstrate_greeks_all_at_once(call: EuroCallOption) -> None:
    """Calculate all Greeks at once for efficiency."""
    logger.info("\n\n3. Calculate All Greeks at Once (Recommended)")
    logger.info("-" * 70)

    greeks = call.greeks()
    logger.info("All Greeks: %s\n", greeks)
    logger.info("  Price:  $%.4f", greeks.price)
    logger.info("  Delta:  %.4f", greeks.delta)
    logger.info("  Gamma:  %.4f", greeks.gamma)
    logger.info("  Vega:   %.4f", greeks.vega)
    logger.info("  Theta:  %.4f", greeks.theta)
    logger.info("  Rho:    %.4f", greeks.rho)


def demonstrate_scenario_analysis(call: EuroCallOption) -> None:
    """Demonstrate immutable updates for scenario analysis."""
    logger.info("\n\n4. Scenario Analysis with Immutable Updates")
    logger.info("-" * 70)

    logger.info("\nOriginal option:")
    logger.info("  Spot: $%.4f, Price: $%.4f", call.spot, call.price())

    # Create new option with different spot price
    higher_spot = call.with_spot(110.0)
    logger.info("\nHigher spot ($110):")
    logger.info("  Spot: $%.4f, Price: $%.4f", higher_spot.spot, higher_spot.price())

    # Create new option with higher volatility
    higher_vol = call.with_volatility(0.3)
    logger.info("\nHigher volatility (30%):")
    logger.info("  Vol: %.4f, Price: $%.4f", higher_vol.volatility, higher_vol.price())

    # Create new option with less time
    less_time = call.with_time(0.5)
    logger.info("\nLess time (0.5 years):")
    logger.info("  Time: %.4fyr, Price: $%.4f", less_time.time_to_expiry, less_time.price())

    logger.info("\nOriginal option unchanged:")
    logger.info("  %s", call)


def verify_put_call_parity(call: EuroCallOption, put: EuroPutOption) -> None:
    """Verify put-call parity relationship."""
    logger.info("\n\n5. Put-Call Parity Verification")
    logger.info("-" * 70)
    logger.info("Formula: C - P = S - K·e^(-rT)\n")

    call_price = call.price()
    put_price = put.price()
    parity_lhs = call_price - put_price
    parity_rhs = call.spot - call.strike * math.exp(-call.risk_free_rate * call.time_to_expiry)
    difference = abs(parity_lhs - parity_rhs)

    logger.info("  Call Price:  $%.4f", call_price)
    logger.info("  Put Price:   $%.4f", put_price)
    logger.info("  C - P:       %s", parity_lhs)
    logger.info("  S - K·e^(-rT): %s", parity_rhs)
    logger.info("  Difference:  %s %s", difference, "✓ PASS" if difference < 0.01 else "✗ FAIL")


def main() -> None:
    """Run all demonstrations for basic European option pricing."""
    logger.info("=" * 70)
    logger.info("Example 1: Basic European Option Pricing")
    logger.info("=" * 70)

    # Create options
    call, put = create_basic_options()

    # Demonstrate different features
    demonstrate_individual_greeks(call)
    demonstrate_greeks_all_at_once(call)
    demonstrate_scenario_analysis(call)
    verify_put_call_parity(call, put)

    # Summary
    logger.info("\n%s", "=" * 70)
    logger.info("Summary:")
    logger.info("  • Create option objects once and reuse them")
    logger.info("  • Use .greeks() to get all values efficiently")
    logger.info("  • Use .with_*() methods for scenario analysis")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
