"""Example 5: American Option Pricing.

This example demonstrates:
- Creating AmericanCallOption and AmericanPutOption objects
- Understanding early exercise premium
- Comparing American vs European options
- Effect of binomial tree steps on accuracy
- Pricing with dividend yields
"""

import logging

from rust_quant import (
    AmericanCallOption,
    AmericanPutOption,
    EuroCallOption,
    EuroPutOption,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def print_section_header(title: str, char: str = "=") -> None:
    """Print a formatted section header."""
    logger.info("\n%s", char * 70)
    logger.info(title)
    logger.info("%s", char * 70)


def print_subsection_header(title: str) -> None:
    """Print a formatted subsection header."""
    logger.info("\n\n%s", title)
    logger.info("-" * 70)


def demonstrate_basic_american_pricing() -> None:
    """Demonstrate basic American option pricing for calls and puts."""
    print_subsection_header("1. Basic American Option Pricing")

    # Create American call and put options
    american_call = AmericanCallOption(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
        steps=100,  # Number of binomial tree steps
    )

    american_put = AmericanPutOption(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
        steps=100,
    )

    logger.info("American Call Price: $%.4f", american_call.price())
    logger.info("American Call Delta:  %.4f", american_call.delta())
    logger.info("\nAmerican Put Price:  $%.4f", american_put.price())
    logger.info("American Put Delta:   %.4f", american_put.delta())


def compare_american_vs_european() -> None:
    """Compare American vs European option pricing to show early exercise premium."""
    print_subsection_header("2. Early Exercise Premium (American vs European)")
    logger.info("American options allow early exercise, making them worth more")
    logger.info("than European options (especially puts).\n")

    # Compare American and European puts (ITM scenario)
    spot: float = 90.0  # In-the-money for puts
    strike: float = 100.0

    american_put = AmericanPutOption(
        spot=spot,
        strike=strike,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
        steps=100,
    )

    european_put = EuroPutOption(
        spot=spot,
        strike=strike,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
    )

    american_price: float = american_put.price()
    european_price: float = european_put.price()
    intrinsic: float = strike - spot
    early_premium: float = american_price - european_price

    logger.info("Spot Price:           $%.4f", spot)
    logger.info("Strike Price:         $%.4f", strike)
    logger.info("Intrinsic Value:      $%.4f (K - S)", intrinsic)
    logger.info("\nEuropean Put Price:   $%.4f", european_price)
    logger.info("American Put Price:   $%.4f", american_price)
    pct = early_premium / european_price * 100
    logger.info(
        "Early Exercise Premium: $%.4f (%.2f%%)",
        early_premium,
        pct,
    )

    # For calls without dividends, American ≈ European
    american_call = AmericanCallOption(
        spot=spot,
        strike=strike,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
        steps=100,
    )
    european_call = EuroCallOption(
        spot=spot,
        strike=strike,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
    )

    logger.info("\nWithout dividends, American calls ≈ European calls:")
    logger.info("American Call: $%.4f", american_call.price())
    logger.info("European Call: $%.4f", european_call.price())


def analyze_binomial_tree_convergence() -> None:
    """Analyze the effect of binomial tree steps on pricing accuracy."""
    print_subsection_header("3. Effect of Binomial Tree Steps on Accuracy")
    logger.info("More steps = higher accuracy but slower computation\n")

    spot: float = 100.0
    strike: float = 100.0

    for steps in [25, 50, 100, 200]:
        american = AmericanPutOption(
            spot=spot,
            strike=strike,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=steps,
        )
        logger.info("Steps: %s  →  Price: $%.4f", steps, american.price())

    logger.info("\nNote: Prices converge as steps increase")


def demonstrate_dividend_effect() -> None:
    """Demonstrate the effect of dividend yields on American options."""
    print_subsection_header("4. American Options with Dividend Yields")
    logger.info("Dividends make early exercise more attractive for puts,")
    logger.info("and can make early exercise optimal for calls.\n")

    spot: float = 100.0
    strike: float = 90.0  # Deep ITM call
    dividend_yield: float = 0.08  # High 8% dividend

    # Without dividend
    american_call_no_div = AmericanCallOption(
        spot=spot,
        strike=strike,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
        dividend_yield=0.0,
        steps=100,
    )

    # With high dividend
    american_call_with_div = AmericanCallOption(
        spot=spot,
        strike=strike,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
        dividend_yield=dividend_yield,
        steps=100,
    )

    no_div_price: float = american_call_no_div.price()
    with_div_price: float = american_call_with_div.price()

    logger.info("Deep ITM American Call (S=$%s, K=$%s):", spot, strike)
    logger.info("  No Dividend (q=0.0):    $%.4f", no_div_price)
    logger.info("  With Dividend (q=0.08): $%.4f", with_div_price)
    logger.info("  Difference:             $%.4f", no_div_price - with_div_price)
    logger.info("\nHigh dividends reduce call value (stock price drops on ex-div date)")


def calculate_american_greeks() -> None:
    """Calculate and display Greeks for American options."""
    print_subsection_header("5. American Option Greeks")
    logger.info("Greeks are calculated using finite difference methods\n")

    american_call = AmericanCallOption(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
        steps=100,
    )

    greeks = american_call.greeks()

    logger.info("Option Price: $%.4f", greeks.price)
    logger.info("Delta (Δ):    %.4f  - Price sensitivity to spot", greeks.delta)
    logger.info("Gamma (Γ):    %.4f  - Rate of change of delta", greeks.gamma)
    logger.info("Vega (ν):     %.4f   - Sensitivity to volatility", greeks.vega)
    logger.info("Theta (Θ):    %.4f  - Time decay", greeks.theta)
    logger.info("Rho (ρ):      %.4f    - Interest rate sensitivity", greeks.rho)


def demonstrate_immutable_updates() -> None:
    """Demonstrate immutable update methods for creating new option instances."""
    print_subsection_header("6. Immutable Update Methods")
    logger.info("Create new option instances with updated parameters\n")

    base_option = AmericanPutOption(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
        steps=100,
    )

    logger.info("Base option (S=100):      $%.4f", base_option.price())

    # Create new options with different spot prices
    option_95 = base_option.with_spot(95.0)
    option_105 = base_option.with_spot(105.0)

    logger.info("With spot=95 (ITM):       $%.4f", option_95.price())
    logger.info("With spot=105 (OTM):      $%.4f", option_105.price())

    # Update volatility
    high_vol_option = base_option.with_volatility(0.4)
    logger.info("\nWith volatility=0.4:      $%.4f", high_vol_option.price())

    # Update number of steps
    precise_option = base_option.with_steps(200)
    logger.info("With 200 steps (more accurate): $%.4f", precise_option.price())


def print_summary() -> None:
    """Print a summary of the example."""
    logger.info("\n%s", "=" * 70)
    logger.info("American options provide flexibility through early exercise,")
    logger.info("making them particularly valuable for dividend-paying stocks")
    logger.info("and in-the-money put positions.")
    logger.info("=" * 70)


def main() -> None:
    """Run all American option pricing examples."""
    print_section_header("Example 5: American Option Pricing")

    demonstrate_basic_american_pricing()
    compare_american_vs_european()
    analyze_binomial_tree_convergence()
    demonstrate_dividend_effect()
    calculate_american_greeks()
    demonstrate_immutable_updates()
    print_summary()


if __name__ == "__main__":
    main()
