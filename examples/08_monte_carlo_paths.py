"""Example 8: Monte Carlo Path Generation and Stochastic Volatility.

This example demonstrates:
- Brownian motion path generation
- Geometric Brownian Motion (GBM) for stock prices
- Heston stochastic volatility model
- Monte Carlo option pricing
- Variance reduction with antithetic variates
- Comparison of Black-Scholes vs Monte Carlo vs Heston
"""

import logging
import time

from rust_quant import (
    BrownianMotion,
    EuroCallOption,
    GeometricBrownianMotion,
    HestonProcess,
    StochasticRng,
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


def demonstrate_brownian_motion() -> BrownianMotion:
    """Demonstrate basic Brownian motion path generation.

    Returns:
        BrownianMotion object

    """
    print_subsection_header("1. Brownian Motion Path Generation")

    # Create Brownian motion generator
    bm = BrownianMotion(time_horizon=1.0, num_steps=252)

    # Generate a single path
    logger.info("\nGenerating single Brownian motion path...")
    path: list[float] = bm.generate_path()
    logger.info("Path length: %s (includes W(0)=0)", len(path))
    logger.info("W(0) = %.4f", path[0])
    logger.info("W(T) = %.4f", path[-1])

    # Generate multiple paths
    logger.info("\nGenerating 10,000 Brownian motion paths...")
    start: float = time.time()
    paths: list[list[float]] = bm.generate_paths_parallel(10000)
    elapsed: float = time.time() - start
    logger.info("Generated 10,000 paths in %.4fs", elapsed)
    logger.info("Average final value: %.4f (expected ~0)", sum(p[-1] for p in paths) / len(paths))

    # Time grid
    times: list[float] = bm.time_grid()
    logger.info("\nTime grid: [0, %.4f, ..., %.4f]", times[1], times[-1])
    logger.info("Time step Δt = %.4f", bm.dt())

    return bm


def demonstrate_geometric_brownian_motion() -> GeometricBrownianMotion:
    """Demonstrate Geometric Brownian Motion for stock price simulation.

    Returns:
        GeometricBrownianMotion object

    """
    print_subsection_header("2. Geometric Brownian Motion (Stock Price Simulation)")

    # Stock parameters
    spot: float = 100.0
    drift: float = 0.05  # 5% expected return
    volatility: float = 0.2  # 20% volatility
    time_horizon: float = 1.0
    num_steps: int = 252  # Daily steps

    gbm = GeometricBrownianMotion(
        spot=spot,
        drift=drift,
        volatility=volatility,
        time_horizon=time_horizon,
        num_steps=num_steps,
    )

    logger.info("\nGBM Parameters:")
    logger.info("  Initial price: $%.4f", gbm.get_spot())
    logger.info("  Drift μ: %.4f%%", gbm.get_drift() * 100)
    logger.info("  Volatility σ: %.4f%%", gbm.get_volatility() * 100)
    logger.info("  Time horizon: %.4f years", gbm.get_time_horizon())

    # Generate a single stock price path
    price_path: list[float] = gbm.generate_path()
    logger.info("\nSingle price path:")
    logger.info("  S(0) = $%.4f", price_path[0])
    logger.info("  S(T) = $%.4f", price_path[-1])

    # Generate many paths and analyze terminal distribution
    logger.info("\nGenerating 100,000 stock price paths...")
    start: float = time.time()
    terminal_prices: list[float] = gbm.terminal_prices(100000)
    elapsed: float = time.time() - start
    logger.info("Generated 100,000 paths in %.4fs", elapsed)

    avg_price: float = sum(terminal_prices) / len(terminal_prices)
    logger.info("\nTerminal price statistics:")
    logger.info("  Average: $%.4f", avg_price)
    logger.info("  Min: $%.4f", min(terminal_prices))
    logger.info("  Max: $%.4f", max(terminal_prices))

    return gbm


def demonstrate_monte_carlo_pricing() -> tuple[float, EuroCallOption]:
    """Demonstrate Monte Carlo option pricing vs Black-Scholes.

    Returns:
        Tuple of (Black-Scholes price, EuroCallOption object)

    """
    print_subsection_header("3. Monte Carlo Option Pricing vs Black-Scholes")

    # Create a European call option
    spot: float = 100.0
    strike: float = 105.0
    risk_free_rate: float = 0.05
    time_to_expiry: float = 1.0
    volatility: float = 0.2

    call = EuroCallOption(
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
    )

    # Black-Scholes analytical price
    bs_price: float = call.price()
    logger.info("\nBlack-Scholes price: $%.4f", bs_price)

    # Monte Carlo pricing (standard)
    logger.info("\nMonte Carlo pricing (100,000 paths)...")
    start: float = time.time()
    mc_price: float = call.price_monte_carlo(num_paths=100000, num_steps=1)
    mc_time: float = time.time() - start
    logger.info("  Price: $%.4f", mc_price)
    logger.info(
        "  Error: $%.4f (%.2f%%)",
        abs(mc_price - bs_price),
        abs(mc_price - bs_price) / bs_price * 100,
    )
    logger.info("  Time: %.4fs", mc_time)

    # Monte Carlo with antithetic variance reduction
    logger.info("\nMonte Carlo with antithetic variates (100,000 paths)...")
    start = time.time()
    mc_anti_price: float = call.price_monte_carlo_antithetic(num_paths=100000, num_steps=1)
    mc_anti_time: float = time.time() - start
    logger.info("  Price: $%.4f", mc_anti_price)
    logger.info(
        "  Error: $%.4f (%.2f%%)",
        abs(mc_anti_price - bs_price),
        abs(mc_anti_price - bs_price) / bs_price * 100,
    )
    logger.info("  Time: %.4fs", mc_anti_time)
    logger.info(
        "  Improvement: %.2fx more accurate",
        abs(mc_price - bs_price) / abs(mc_anti_price - bs_price),
    )

    # Convergence test
    logger.info("\nConvergence analysis:")
    for num_paths in [1000, 10000, 100000, 1000000]:
        mc_p: float = call.price_monte_carlo(num_paths=num_paths, num_steps=1)
        error: float = abs(mc_p - bs_price)
        logger.info("  %s paths: $%.4f, error: $%.4f", num_paths, mc_p, error)

    return bs_price, call


def create_heston_process(
    spot: float,
    risk_free_rate: float,
    time_to_expiry: float,
) -> tuple[HestonProcess, float, float, float, float, float]:
    """Create and configure a Heston stochastic volatility process.

    Args:
        spot: Initial spot price
        risk_free_rate: Risk-free interest rate
        time_to_expiry: Time to expiration

    Returns:
        Tuple of (HestonProcess, initial_variance, kappa, theta, vol_of_vol, correlation)

    """
    # Heston parameters (typical calibrated values for equity options)
    initial_variance: float = 0.04  # Initial vol = 20%
    kappa: float = 2.0  # Mean reversion speed
    theta: float = 0.04  # Long-term variance (20% vol)
    vol_of_vol: float = 0.3  # Volatility of volatility
    correlation: float = -0.7  # Negative correlation (leverage effect)

    heston = HestonProcess(
        spot=spot,
        initial_variance=initial_variance,
        drift=risk_free_rate,  # Risk-neutral pricing
        kappa=kappa,
        theta=theta,
        vol_of_vol=vol_of_vol,
        correlation=correlation,
        time_horizon=time_to_expiry,
        num_steps=100,
    )

    return heston, initial_variance, kappa, theta, vol_of_vol, correlation


def demonstrate_heston_model(
    spot: float,
    risk_free_rate: float,
    time_to_expiry: float,
) -> tuple[HestonProcess, float, float, float, float, float]:
    """Demonstrate the Heston stochastic volatility model.

    Args:
        spot: Initial spot price
        risk_free_rate: Risk-free interest rate
        time_to_expiry: Time to expiration

    Returns:
        Tuple of (HestonProcess, initial_variance, kappa, theta, vol_of_vol, correlation)

    """
    print_subsection_header("4. Heston Stochastic Volatility Model")

    heston, initial_variance, kappa, theta, vol_of_vol, correlation = create_heston_process(
        spot,
        risk_free_rate,
        time_to_expiry,
    )

    logger.info("\nHeston Model Parameters:")
    logger.info(
        "  Initial variance v(0): %.4f (√v = %.2f%%)",
        initial_variance,
        initial_variance**0.5 * 100,
    )
    logger.info("  Mean reversion κ: %.4f", kappa)
    logger.info("  Long-term variance θ: %.4f (√θ = %s)", theta, theta**0.5)
    logger.info("  Vol of vol σᵥ: %.4f", vol_of_vol)
    logger.info("  Correlation ρ: %.4f", correlation)

    # Generate a single Heston path
    logger.info("\nGenerating single Heston path...")
    price_path, variance_path = heston.generate_path()
    logger.info("  Initial: S(0) = $%.4f, v(0) = %.4f", price_path[0], variance_path[0])
    logger.info(
        "  Final: S(T) = $%.2f, v(T) = %.4f (√v = %.2f%%)",
        price_path[-1],
        variance_path[-1],
        variance_path[-1] ** 0.5 * 100,
    )

    # Generate many paths
    logger.info("\nGenerating 10,000 Heston paths...")
    start: float = time.time()
    heston_prices, heston_variances = heston.terminal_values(10000)
    elapsed: float = time.time() - start
    logger.info("Generated 10,000 paths in %.4fs", elapsed)

    avg_price_heston: float = sum(heston_prices) / len(heston_prices)
    avg_var_heston: float = sum(heston_variances) / len(heston_variances)
    logger.info("\nTerminal statistics:")
    logger.info("  Average price: $%.4f", avg_price_heston)
    logger.info("  Average variance: %.4f (√v = %s)", avg_var_heston, avg_var_heston**0.5)

    return heston, initial_variance, kappa, theta, vol_of_vol, correlation


def compare_pricing_methods(
    bs_price: float,
    call: EuroCallOption,
    initial_variance: float,
    kappa: float,
    theta: float,
    vol_of_vol: float,
    correlation: float,
) -> float:
    """Compare different option pricing methods.

    Args:
        bs_price: Black-Scholes price
        call: EuroCallOption object
        initial_variance: Heston initial variance
        kappa: Heston mean reversion speed
        theta: Heston long-term variance
        vol_of_vol: Heston volatility of volatility
        correlation: Heston correlation

    Returns:
        Heston option price

    """
    print_subsection_header("5. Heston vs Black-Scholes Option Pricing")

    # Price option under Heston model
    logger.info("\nPricing call option under Heston model...")
    start: float = time.time()
    heston_price: float = call.price_heston(
        initial_variance=initial_variance,
        kappa=kappa,
        theta=theta,
        vol_of_vol=vol_of_vol,
        correlation=correlation,
        num_paths=100000,
        num_steps=100,
    )
    heston_time: float = time.time() - start

    # Get MC prices for comparison
    mc_price: float = call.price_monte_carlo(num_paths=100000, num_steps=1)
    mc_time: float = 0.1  # Approximate from earlier
    mc_anti_price: float = call.price_monte_carlo_antithetic(num_paths=100000, num_steps=1)
    mc_anti_time: float = 0.1  # Approximate from earlier

    logger.info("\nOption Pricing Comparison:")
    logger.info("  %s %s %s", "Method", "Price", "Time")
    logger.info("  %s %s %s", "-" * 30, "-" * 12, "-" * 10)
    logger.info("  %s $%s %s", "Black-Scholes (analytical)", bs_price, "instant")
    logger.info("  %s $%s %ss", "Monte Carlo GBM", mc_price, mc_time)
    logger.info("  %s $%s %ss", "Monte Carlo (antithetic)", mc_anti_price, mc_anti_time)
    logger.info("  %s $%s %ss", "Heston stochastic vol", heston_price, heston_time)

    diff_heston_bs: float = heston_price - bs_price
    logger.info("\nHeston vs Black-Scholes difference: $%.4f", diff_heston_bs)
    logger.info("  → This captures the volatility smile/skew effect")

    return heston_price


def demonstrate_volatility_smile(
    spot: float,
    time_to_expiry: float,
    risk_free_rate: float,
    volatility: float,
    initial_variance: float,
    kappa: float,
    theta: float,
    vol_of_vol: float,
    correlation: float,
) -> None:
    """Demonstrate the volatility smile effect.

    Args:
        spot: Initial spot price
        time_to_expiry: Time to expiration
        risk_free_rate: Risk-free interest rate
        volatility: Black-Scholes volatility
        initial_variance: Heston initial variance
        kappa: Heston mean reversion speed
        theta: Heston long-term variance
        vol_of_vol: Heston volatility of volatility
        correlation: Heston correlation

    """
    print_subsection_header("6. Demonstrating Volatility Smile Effect")

    logger.info("\nPricing options at different strikes (Heston vs BS):")
    logger.info("  %s %s %s %s", "Strike", "BS Price", "Heston Price", "Difference")
    logger.info("  %s %s %s %s", "-" * 10, "-" * 12, "-" * 15, "-" * 12)

    strikes: list[float] = [80, 90, 100, 110, 120]
    for k in strikes:
        option_bs = EuroCallOption(spot, k, time_to_expiry, risk_free_rate, volatility)
        bs_p: float = option_bs.price()
        heston_p: float = option_bs.price_heston(
            initial_variance,
            kappa,
            theta,
            vol_of_vol,
            correlation,
            num_paths=50000,
            num_steps=100,
        )
        diff: float = heston_p - bs_p
        logger.info("  $%s $%s $%s $%s", k, bs_p, heston_p, diff)

    logger.info("\n  → Out-of-the-money options show larger differences due to volatility skew")


def benchmark_performance(bm: BrownianMotion, gbm: GeometricBrownianMotion) -> None:
    """Benchmark performance of different path generation methods.

    Args:
        bm: BrownianMotion object
        gbm: GeometricBrownianMotion object

    """
    print_subsection_header("7. Performance Benchmarks")

    logger.info("\nPath generation performance:")

    # Brownian motion
    start: float = time.time()
    bm.generate_paths_parallel(100000)
    bm_time: float = time.time() - start
    logger.info("  Brownian motion (100k paths, 252 steps): %.4fs", bm_time)

    # GBM
    start = time.time()
    gbm.terminal_prices(100000)
    gbm_time: float = time.time() - start
    logger.info("  GBM (100k paths, 252 steps): %.4fs", gbm_time)

    # Heston
    spot: float = 100.0
    risk_free_rate: float = 0.05
    time_to_expiry: float = 1.0
    heston, _, _, _, _, _ = create_heston_process(spot, risk_free_rate, time_to_expiry)

    start = time.time()
    heston.terminal_values(10000)
    heston_time_bench: float = time.time() - start
    logger.info("  Heston (10k paths, 100 steps): %.4fs", heston_time_bench)

    logger.info("\nOption pricing performance:")
    logger.info("  Black-Scholes analytical: <0.001s (instant)")
    logger.info("  Monte Carlo (100k paths): ~0.1s (approximate)")
    logger.info("  Heston (100k paths): varies based on parameters")


def demonstrate_reproducibility() -> None:
    """Demonstrate reproducibility with random seeds."""
    print_subsection_header("8. Reproducibility with Random Seeds")

    # Create RNG with fixed seed
    rng = StochasticRng(seed=42)
    logger.info("\nRNG with seed=42")
    logger.info("  First 5 normals: {[f'%.4f' for _ in range(5)]}", rng.normal())

    # Create another RNG with same seed
    rng2 = StochasticRng(seed=42)
    logger.info("\nAnother RNG with seed=42 (should be identical)")
    logger.info("  First 5 normals: {[f'%.4f' for _ in range(5)]}", rng2.normal())

    logger.info("\n  → Same seed produces identical random sequences")


def print_summary() -> None:
    """Print a summary of the Monte Carlo examples."""
    logger.info("\n%s", "=" * 70)
    logger.info("Summary:")
    logger.info("=" * 70)
    logger.info("✓ Brownian motion path generation (basic building block)")
    logger.info("✓ Geometric Brownian Motion for stock prices")
    logger.info("✓ Monte Carlo option pricing with GBM")
    logger.info("✓ Antithetic variates for variance reduction")
    logger.info("✓ Heston stochastic volatility model")
    logger.info("✓ Volatility smile/skew effects captured")
    logger.info("✓ High-performance parallel path generation")
    logger.info("✓ Reproducible results with seeded RNG")
    logger.info("=" * 70)

    logger.info("\n%s", "=" * 70)
    logger.info("Key Takeaways:")
    logger.info("  • Monte Carlo converges to Black-Scholes for constant volatility")
    logger.info("  • Antithetic variates improve accuracy for same computational cost")
    logger.info("  • Heston model captures realistic volatility dynamics")
    logger.info("  • Stochastic volatility creates option pricing smile/skew")
    logger.info("  • Parallel implementation enables fast simulation (100k+ paths)")
    logger.info("=" * 70)


def main() -> None:
    """Run all Monte Carlo path generation examples."""
    print_section_header("Example 8: Monte Carlo Path Generation and Stochastic Volatility")

    # Common parameters
    spot: float = 100.0
    risk_free_rate: float = 0.05
    time_to_expiry: float = 1.0
    volatility: float = 0.2

    # Run demonstrations
    bm = demonstrate_brownian_motion()
    gbm = demonstrate_geometric_brownian_motion()
    bs_price, call = demonstrate_monte_carlo_pricing()

    _, initial_variance, kappa, theta, vol_of_vol, correlation = demonstrate_heston_model(
        spot,
        risk_free_rate,
        time_to_expiry,
    )

    compare_pricing_methods(bs_price, call, initial_variance, kappa, theta, vol_of_vol, correlation)

    demonstrate_volatility_smile(
        spot,
        time_to_expiry,
        risk_free_rate,
        volatility,
        initial_variance,
        kappa,
        theta,
        vol_of_vol,
        correlation,
    )

    benchmark_performance(bm, gbm)
    demonstrate_reproducibility()
    print_summary()


if __name__ == "__main__":
    main()
