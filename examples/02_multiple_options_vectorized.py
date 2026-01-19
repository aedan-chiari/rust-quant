"""Example 2: Vectorized Pricing for Multiple European Options.

This example demonstrates:
- Pricing multiple European options at once using static methods
- Calculating Greeks for multiple options simultaneously
- Performance comparison: vectorized vs individual pricing
"""

import logging
import time

from rust_quant import EuroCallOption, EuroPutOption

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def demonstrate_vectorized_pricing() -> tuple[
    list[float],
    list[float],
    list[float],
    list[float],
    list[float],
]:
    """Price multiple European call options using static methods."""
    logger.info("\n1. Pricing Multiple European Call Options")
    logger.info("-" * 70)

    # Define parameters for 5 options with different spot prices
    spots = [95.0, 100.0, 105.0, 110.0, 115.0]
    strikes = [100.0] * 5  # All have same strike
    times = [1.0] * 5  # All expire in 1 year
    rates = [0.05] * 5  # All use 5% risk-free rate
    vols = [0.2] * 5  # All have 20% volatility

    logger.info("\nPricing %s European options with different spot prices:", len(spots))
    logger.info("Using: EuroCallOption.price_many() - static method\n")

    # Use static method to price all at once
    prices = EuroCallOption.price_many(spots, strikes, times, rates, vols)

    logger.info("%s %s %s", "Spot Price", "Call Price", "Moneyness")
    logger.info("-" * 50)
    for spot, price in zip(spots, prices, strict=True):
        if spot < 100:
            moneyness = "OTM (Out of the Money)"
        elif spot > 100:
            moneyness = "ITM (In the Money)"
        else:
            moneyness = "ATM (At the Money)"
        logger.info("$%s $%s %s", spot, price, moneyness)

    return spots, strikes, times, rates, vols


def demonstrate_vectorized_greeks(
    spots: list[float],
    strikes: list[float],
    times: list[float],
    rates: list[float],
    vols: list[float],
) -> list[float]:
    """Calculate Greeks for multiple options simultaneously."""
    logger.info("\n\n2. Calculating Greeks for Multiple Options")
    logger.info("-" * 70)

    logger.info("Using: EuroCallOption.greeks_many() - static method\n")

    prices, deltas, gammas, vegas, _thetas, _rhos = EuroCallOption.greeks_many(
        spots,
        strikes,
        times,
        rates,
        vols,
    )

    logger.info("%s %s %s %s %s", "Spot", "Price", "Delta", "Gamma", "Vega")
    logger.info("-" * 60)
    for i in range(len(spots)):
        logger.info(
            "$%7.2f $%9.4f %10.4f %10.4f %10.4f",
            spots[i],
            prices[i],
            deltas[i],
            gammas[i],
            vegas[i],
        )

    return prices


def demonstrate_put_options(
    spots: list[float],
    strikes: list[float],
    times: list[float],
    rates: list[float],
    vols: list[float],
    call_prices: list[float],
) -> None:
    """Demonstrate put option pricing with same API."""
    logger.info("\n\n3. Put Options (Same API)")
    logger.info("-" * 70)

    put_prices = EuroPutOption.price_many(spots, strikes, times, rates, vols)

    logger.info("%s %s %s", "Spot Price", "Put Price", "Call Price")
    logger.info("-" * 50)
    for i, spot in enumerate(spots):
        logger.info("$%s $%s $%s", spot, put_prices[i], call_prices[i])


def compare_performance() -> None:
    """Compare vectorized vs individual pricing performance."""
    logger.info("\n\n4. Performance: Vectorized vs Individual")
    logger.info("-" * 70)

    n_options = 1000
    logger.info("\nPricing %s options...\n", n_options)

    # Generate test data
    test_spots = [100.0 + i * 0.1 for i in range(n_options)]
    test_strikes = [105.0] * n_options
    test_times = [1.0] * n_options
    test_rates = [0.05] * n_options
    test_vols = [0.2] * n_options

    # Method 1: Vectorized using static method
    start = time.perf_counter()
    _vec_prices = EuroCallOption.price_many(
        test_spots,
        test_strikes,
        test_times,
        test_rates,
        test_vols,
    )
    vec_time = time.perf_counter() - start

    logger.info("Vectorized (EuroCallOption.price_many):")
    logger.info("  Time: %.4fms", vec_time * 1000)
    logger.info("  Rate: %s options/sec", n_options / vec_time)

    # Method 2: Individual option objects (for comparison, only 100 options)
    start = time.perf_counter()
    ind_prices = []
    for i in range(min(100, n_options)):
        opt = EuroCallOption(
            test_spots[i],
            test_strikes[i],
            test_times[i],
            test_rates[i],
            test_vols[i],
        )
        ind_prices.append(opt.price())
    ind_time = time.perf_counter() - start

    logger.info("\nIndividual objects (100 options):")
    logger.info("  Time: %.4fms", ind_time * 1000)
    logger.info("  Rate: %s options/sec", 100 / ind_time)

    logger.info("\nSpeedup: %.4fx faster per option", (ind_time / 100) / (vec_time / n_options))


def show_usage_guidelines() -> None:
    """Display when to use each approach."""
    logger.info("\n\n5. When to Use Each Approach")
    logger.info("-" * 70)

    logger.info("""
Single Option (Instance Methods):
  • When analyzing ONE specific option
  • When you need to call multiple Greeks on the same option
  • Example: call = EuroCallOption(...); call.delta(); call.gamma()

Vectorized (Static Methods):
  • When pricing MANY options at once
  • When building a pricing grid or surface
  • Example: EuroCallOption.price_many(spots, strikes, times, rates, vols)

Best Practice:
  • Create single option objects once and reuse them
  • Use vectorized methods for bulk calculations
  • Use .greeks() when you need multiple Greeks for one option
""")


def main() -> None:
    """Run all demonstrations for vectorized option pricing."""
    logger.info("=" * 70)
    logger.info("Example 2: Vectorized Pricing for Multiple European Options")
    logger.info("=" * 70)

    # Demonstrate different features
    spots, strikes, times, rates, vols = demonstrate_vectorized_pricing()
    call_prices = demonstrate_vectorized_greeks(spots, strikes, times, rates, vols)
    demonstrate_put_options(spots, strikes, times, rates, vols, call_prices)
    compare_performance()
    show_usage_guidelines()

    logger.info("=" * 70)


if __name__ == "__main__":
    main()
