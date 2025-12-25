"""Example 6: Batch Pricing for American Options.

This example demonstrates:
- Pricing multiple American options at once using static methods
- Calculating Greeks for multiple American options simultaneously
- Performance comparison: batch vs individual pricing
- Comparison with European option batch pricing
"""

import logging
import time

from rust_quant import AmericanCallOption, AmericanPutOption, EuroCallOption

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


def create_sample_parameters() -> tuple[
    list[float],
    list[float],
    list[float],
    list[float],
    list[float],
    list[float],
]:
    """Create sample option parameters for batch pricing.

    Returns:
        Tuple of (spots, strikes, times, rates, volatilities, dividend_yields)

    """
    spots = [95.0, 100.0, 105.0, 110.0, 115.0]
    strikes = [100.0] * 5  # All have same strike
    times = [1.0] * 5  # All expire in 1 year
    rates = [0.05] * 5  # All use 5% risk-free rate
    vols = [0.2] * 5  # All have 20% volatility
    dividend_yields = [0.0] * 5  # No dividends

    return spots, strikes, times, rates, vols, dividend_yields


def get_moneyness(spot: float, strike: float) -> str:
    """Determine the moneyness of an option.

    Args:
        spot: Current spot price
        strike: Strike price

    Returns:
        String indicating moneyness: "OTM", "ATM", or "ITM"

    """
    if spot < strike:
        return "OTM"
    if spot > strike:
        return "ITM"
    return "ATM"


def demonstrate_batch_call_pricing() -> None:
    """Demonstrate pricing multiple American call options using batch methods."""
    print_subsection_header("1. Pricing Multiple American Call Options")

    spots, strikes, times, rates, vols, dividend_yields = create_sample_parameters()
    steps: int = 100

    logger.info("\nPricing %s American call options with different spot prices:", len(spots))
    logger.info("Using: AmericanCallOption.price_many() - Rayon parallel pricing\n")

    # Use static method to price all at once (parallelized with Rayon)
    prices: list[float] = AmericanCallOption.price_many(
        spots,
        strikes,
        times,
        rates,
        vols,
        dividend_yields,
        steps,
    )

    logger.info("%s %s %s %s", "Spot Price", "Call Price", "Intrinsic", "Moneyness")
    logger.info("-" * 65)
    for spot, price in zip(spots, prices, strict=True):
        intrinsic: float = max(0, spot - 100.0)
        moneyness: str = get_moneyness(spot, 100.0)
        logger.info("$%s $%s $%s %s", spot, price, intrinsic, moneyness)


def demonstrate_batch_greeks() -> None:
    """Calculate Greeks for multiple American options using batch methods."""
    print_subsection_header("2. Calculating Greeks for Multiple American Options")

    spots, strikes, times, rates, vols, dividend_yields = create_sample_parameters()
    steps: int = 100

    logger.info("Using: AmericanCallOption.greeks_many() - parallel Greeks calculation\n")

    prices, deltas, gammas, vegas, _thetas, _rhos = AmericanCallOption.greeks_many(
        spots,
        strikes,
        times,
        rates,
        vols,
        dividend_yields,
        steps,
    )

    logger.info("%s %s %s %s %s", "Spot", "Price", "Delta", "Gamma", "Vega")
    logger.info("-" * 60)
    for i in range(len(spots)):
        logger.info(
            "$%-7.2f $%-9.4f %-10.4f %-10.4f %-10.4f",
            spots[i],
            prices[i],
            deltas[i],
            gammas[i],
            vegas[i],
        )


def demonstrate_batch_put_pricing() -> None:
    """Demonstrate pricing multiple American put options."""
    print_subsection_header("3. American Put Options (Same API)")

    spots, strikes, times, rates, vols, dividend_yields = create_sample_parameters()
    steps: int = 100

    put_prices: list[float] = AmericanPutOption.price_many(
        spots,
        strikes,
        times,
        rates,
        vols,
        dividend_yields,
        steps,
    )

    logger.info(
        "%-12s %-12s %-12s %s",
        "Spot Price",
        "Put Price",
        "Intrinsic",
        "Early Exercise Premium",
    )
    logger.info("-" * 75)
    for spot, price in zip(spots, put_prices, strict=True):
        intrinsic: float = max(0, 100.0 - spot)
        time_value: float = price - intrinsic
        logger.info("$%s $%s $%s $%s", spot, price, intrinsic, time_value)


def compare_batch_vs_individual_performance() -> None:
    """Compare performance of batch pricing vs individual pricing."""
    print_subsection_header("4. Performance Comparison")

    # Create larger dataset
    n: int = 1000
    large_spots: list[float] = [95.0 + (i * 30.0 / n) for i in range(n)]
    large_strikes: list[float] = [100.0] * n
    large_times: list[float] = [1.0] * n
    large_rates: list[float] = [0.05] * n
    large_vols: list[float] = [0.2] * n
    large_dividends: list[float] = [0.0] * n
    steps: int = 100

    logger.info("\nPricing %s American call options...\n", n)

    # Batch pricing
    start: float = time.time()
    batch_prices: list[float] = AmericanCallOption.price_many(
        large_spots,
        large_strikes,
        large_times,
        large_rates,
        large_vols,
        large_dividends,
        steps,
    )
    batch_time: float = time.time() - start

    # Individual pricing
    start = time.time()
    individual_prices: list[float] = []
    for i in range(n):
        opt = AmericanCallOption(
            large_spots[i],
            large_strikes[i],
            large_times[i],
            large_rates[i],
            large_vols[i],
            large_dividends[i],
            steps,
        )
        individual_prices.append(opt.price())
    individual_time: float = time.time() - start

    logger.info("Batch pricing (Rayon):     %.4f seconds", batch_time)
    logger.info("Individual pricing:        %.4f seconds", individual_time)
    logger.info("Speedup:                   %.4fx", individual_time / batch_time)
    logger.info("Per-option (batch):        %.4f ms", batch_time / n * 1000)
    logger.info("Per-option (individual):   %.4f ms", individual_time / n * 1000)

    # Verify results match
    max_diff: float = max(abs(b - i) for b, i in zip(batch_prices, individual_prices, strict=True))
    logger.info("\nMaximum price difference:  %.4f (should be ~0)", max_diff)


def compare_american_vs_european_batch() -> None:
    """Compare American vs European option batch pricing."""
    print_subsection_header("5. American vs European Options (No Dividends)")

    spots, strikes, times, rates, vols, dividend_yields = create_sample_parameters()
    steps: int = 100

    logger.info("\nWithout dividends, American calls equal European calls:")
    logger.info("(Early exercise is never optimal for calls without dividends)\n")

    american_call_prices: list[float] = AmericanCallOption.price_many(
        spots,
        strikes,
        times,
        rates,
        vols,
        dividend_yields,
        steps,
    )
    european_call_prices: list[float] = EuroCallOption.price_many(
        spots,
        strikes,
        times,
        rates,
        vols,
    )

    logger.info("%s %s %s %s", "Spot", "American Call", "European Call", "Difference")
    logger.info("-" * 60)
    for i in range(len(spots)):
        diff: float = american_call_prices[i] - european_call_prices[i]
        logger.info(
            "$%-7.2f $%-14.4f $%-14.4f $%-10.4f",
            spots[i],
            american_call_prices[i],
            european_call_prices[i],
            diff,
        )

    logger.info("\n\nFor puts, American options have early exercise premium:")

    american_put_prices: list[float] = AmericanPutOption.price_many(
        spots,
        strikes,
        times,
        rates,
        vols,
        dividend_yields,
        steps,
    )

    logger.info("%s %s %s %s", "Spot", "American Put", "Intrinsic", "Time Value")
    logger.info("-" * 60)
    for i in range(len(spots)):
        intrinsic: float = max(0, strikes[i] - spots[i])
        time_value: float = american_put_prices[i] - intrinsic
        logger.info(
            "$%-7.2f $%-14.4f $%-14.2f $%-10.4f",
            spots[i],
            american_put_prices[i],
            intrinsic,
            time_value,
        )


def demonstrate_dividend_effect_batch() -> None:
    """Demonstrate the effect of dividends on American call options using batch pricing."""
    print_subsection_header("6. Effect of Dividends on American Call Options")

    spots, strikes, times, rates, vols, _ = create_sample_parameters()
    steps: int = 100

    logger.info("\nWith dividends, American calls can have early exercise value:\n")

    # High dividend yield case
    high_dividends: list[float] = [0.08] * 5  # 8% dividend yield

    american_no_div: list[float] = AmericanCallOption.price_many(
        spots,
        strikes,
        times,
        rates,
        vols,
        [0.0] * 5,
        steps,
    )
    american_with_div: list[float] = AmericanCallOption.price_many(
        spots,
        strikes,
        times,
        rates,
        vols,
        high_dividends,
        steps,
    )

    logger.info("%s %s %s %s", "Spot", "No Dividend", "8% Dividend", "Difference")
    logger.info("-" * 60)
    for i in range(len(spots)):
        diff: float = american_no_div[i] - american_with_div[i]
        logger.info(
            "$%-7.2f $%-14.4f $%-14.4f $%-10.4f",
            spots[i],
            american_no_div[i],
            american_with_div[i],
            diff,
        )

    logger.info("\nNote: Dividends reduce call values as they lower expected stock price.")


def print_summary() -> None:
    """Print a summary of the batch pricing examples."""
    logger.info("\n%s", "=" * 70)
    logger.info("Summary:")
    logger.info("=" * 70)
    logger.info("✓ American options support parallel batch pricing via Rayon")
    logger.info("✓ Same API as European options: price_many() and greeks_many()")
    logger.info("✓ Significant speedup for pricing many options")
    logger.info("✓ American puts always have early exercise premium")
    logger.info("✓ American calls equal European calls (no dividends)")
    logger.info("✓ Dividends create early exercise value for American calls")
    logger.info("=" * 70)


def main() -> None:
    """Run all batch pricing examples."""
    print_section_header("Example 6: Batch Pricing for American Options")

    demonstrate_batch_call_pricing()
    demonstrate_batch_greeks()
    demonstrate_batch_put_pricing()
    compare_batch_vs_individual_performance()
    compare_american_vs_european_batch()
    demonstrate_dividend_effect_batch()
    print_summary()


if __name__ == "__main__":
    main()
