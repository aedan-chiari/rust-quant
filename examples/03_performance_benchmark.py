"""Example 3: Performance Benchmark (European Options).

This example demonstrates:
- Performance of SIMD+Parallel optimized EuroCallOption/EuroPutOption static methods
- Scaling behavior with different dataset sizes
- When to use single vs batch operations
"""

import logging
import time

from rust_quant import EuroCallOption, EuroPutOption

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def benchmark_pricing(n_options: int) -> None:
    """Benchmark European option pricing performance at different scales."""
    logger.info("\n%s", "=" * 70)
    logger.info("Dataset Size: %s options", n_options)
    logger.info("%s", "=" * 70)

    # Generate test data
    spots = [100.0 + i * 0.01 for i in range(n_options)]
    strikes = [105.0] * n_options
    times = [1.0] * n_options
    rates = [0.05] * n_options
    vols = [0.2] * n_options

    # Warm up
    _ = EuroCallOption.price_many(spots[:100], strikes[:100], times[:100], rates[:100], vols[:100])

    # --------------------------------------------------------------------------
    # European Call Option Pricing
    # --------------------------------------------------------------------------
    logger.info("\nEuropean Call Option Pricing (SIMD + Parallel):")

    start = time.perf_counter()
    _prices = EuroCallOption.price_many(spots, strikes, times, rates, vols)
    elapsed = time.perf_counter() - start

    logger.info("  Time:     %s ms", elapsed * 1000)
    logger.info("  Rate:     %s options/sec", n_options / elapsed)
    logger.info("  Per opt:  %s μs", elapsed / n_options * 1e6)

    # --------------------------------------------------------------------------
    # Greeks Calculation
    # --------------------------------------------------------------------------
    logger.info("\nGreeks Calculation (SIMD + Parallel, all 6 values):")

    start = time.perf_counter()
    _greeks = EuroCallOption.greeks_many(spots, strikes, times, rates, vols)
    elapsed_greeks = time.perf_counter() - start

    logger.info("  Time:     %s ms", elapsed_greeks * 1000)
    logger.info("  Rate:     %s options/sec", n_options / elapsed_greeks)
    logger.info("  Per opt:  %s μs", elapsed_greeks / n_options * 1e6)

    # --------------------------------------------------------------------------
    # Put Options
    # --------------------------------------------------------------------------
    logger.info("\nPut Option Pricing (SIMD + Parallel):")

    start = time.perf_counter()
    _prices_put = EuroPutOption.price_many(spots, strikes, times, rates, vols)
    elapsed_put = time.perf_counter() - start

    logger.info("  Time:     %s ms", elapsed_put * 1000)
    logger.info("  Rate:     %s options/sec", n_options / elapsed_put)
    logger.info("  Per opt:  %s μs", elapsed_put / n_options * 1e6)

    # --------------------------------------------------------------------------
    # Single Option Comparison (for small datasets)
    # --------------------------------------------------------------------------
    if n_options <= 10_000:
        logger.info("\nSingle Object Creation (for comparison):")

        n_sample = min(1000, n_options)
        start = time.perf_counter()
        for i in range(n_sample):
            opt = EuroCallOption(spots[i], strikes[i], times[i], rates[i], vols[i])
            _ = opt.price()
        elapsed_single = time.perf_counter() - start

        logger.info("  Time:     %s ms (for %s options)", elapsed_single * 1000, n_sample)
        logger.info("  Rate:     %s options/sec", n_sample / elapsed_single)
        logger.info("  Per opt:  %s μs", elapsed_single / n_sample * 1e6)

        speedup = (elapsed_single / n_sample) / (elapsed / n_options)
        logger.info("\n  Vectorized speedup: %.4fx faster per option", speedup)


def main() -> None:
    logger.info("=" * 70)
    logger.info("Performance Benchmark: Option Pricing")
    logger.info("SIMD + Parallel Optimized EuroCallOption/EuroPutOption Static Methods")
    logger.info("=" * 70)

    logger.info("""
Two performance levels available:

1. Single Option Objects (Convenience & Flexibility)
   - opt = EuroCallOption(spot, strike, time, rate, vol)
   - opt.price(), opt.delta(), opt.greeks()
   - Best for: Analyzing individual options, interactive use
   - Speed: ~1-10 μs per option

2. Vectorized SIMD + Parallel (Maximum Performance)
   - EuroCallOption.price_many(spots, strikes, times, rates, vols)
   - EuroCallOption.greeks_many(...)
   - Best for: Pricing grids, risk analysis, batch calculations
   - Speed: ~0.1-1 μs per option (10-100x faster)
   - Uses: SIMD intrinsics (4x parallelism) + Rayon thread pool
    """)

    # Test different sizes
    sizes = [1_000, 10_000, 100_000, 1_000_000]

    for size in sizes:
        benchmark_pricing(size)

    logger.info("\n%s", "=" * 70)
    logger.info("Benchmark Complete!")
    logger.info("%s", "=" * 70)

    # --------------------------------------------------------------------------
    # Recommendations
    # --------------------------------------------------------------------------
    logger.info("""
Recommendations:

Dataset Size         Recommended Method                     Expected Performance
------------         ------------------                     --------------------
1 option             EuroCallOption(...).price()               ~1-10 μs
< 100 options        EuroCallOption.price_many()               < 1ms
100 - 10,000         EuroCallOption.price_many()               1-10ms
10,000 - 100,000     EuroCallOption.price_many()               10-50ms
100,000+             EuroCallOption.price_many()               50-200ms

Key Takeaways:
• Always use EuroCallOption.price_many() / EuroPutOption.price_many() for batch operations
• The static methods use SIMD intrinsics and parallel processing automatically
• Speedup increases with dataset size (parallelization overhead amortized)
• For single options, create once and reuse (call .price(), .delta(), .greeks() multiple times)
    """)

    # --------------------------------------------------------------------------
    # Quick Usage Example
    # --------------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("Quick Usage Example:")
    logger.info("=" * 70)

    spots = [95.0, 100.0, 105.0, 110.0, 115.0]
    strikes = [100.0] * 5
    times = [1.0] * 5
    rates = [0.05] * 5
    vols = [0.2] * 5

    # Batch pricing with SIMD + Parallel
    prices = EuroCallOption.price_many(spots, strikes, times, rates, vols)

    logger.info("\nPricing 5 options with EuroCallOption.price_many():")
    logger.info("%s %s %s", "Spot", "Strike", "Price")
    logger.info("-" * 30)
    for spot, price in zip(spots, prices, strict=True):
        logger.info("$%s $%s $%s", spot, 100.00, price)

    # Single option pricing
    logger.info("\nSingle option with instance methods:")
    call = EuroCallOption(100.0, 105.0, 1.0, 0.05, 0.2)
    greeks = call.greeks()
    logger.info("  Price:  $%.4f", greeks.price)
    logger.info("  Delta:  %.4f", greeks.delta)
    logger.info("  Gamma:  %.4f", greeks.gamma)

    logger.info("\n%s", "=" * 70)


if __name__ == "__main__":
    main()
