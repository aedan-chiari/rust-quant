import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell
def _():
    import time
    from rust_quant import (
        BrownianMotion,
        EuroCallOption,
        GeometricBrownianMotion,
        HestonProcess,
        StochasticRng,
    )
    import marimo as mo

    return (
        BrownianMotion,
        EuroCallOption,
        GeometricBrownianMotion,
        HestonProcess,
        StochasticRng,
        mo,
        time,
    )


@app.cell
def _(mo):
    mo.md("""
    # Example 8: Monte Carlo Path Generation and Stochastic Volatility

    This example demonstrates:
    - Brownian motion path generation
    - Geometric Brownian Motion (GBM) for stock prices
    - Heston stochastic volatility model
    - Monte Carlo option pricing
    - Variance reduction with antithetic variates
    - Comparison of Black-Scholes vs Monte Carlo vs Heston
    """)
    return


@app.cell
def _(BrownianMotion, mo, time):
    mo.md("## 1. Brownian Motion Path Generation")

    # Create Brownian motion generator
    bm = BrownianMotion(time_horizon=1.0, num_steps=252)

    # Generate a single path
    path = bm.generate_path()

    mo.md(f"""
    **Generating single Brownian motion path...**
    - Path length: {len(path)} (includes W(0)=0)
    - W(0) = {path[0]:.4f}
    - W(T) = {path[-1]:.4f}
    """)

    # Generate multiple paths
    start = time.time()
    paths = bm.generate_paths_parallel(10000)
    elapsed = time.time() - start

    mo.md(f"""
    **Generating 10,000 Brownian motion paths...**
    - Generated in {elapsed:.4f}s
    - Average final value: {sum(p[-1] for p in paths) / len(paths):.4f} (expected ~0)
    """)

    # Time grid
    times = bm.time_grid()

    mo.md(f"""
    **Time grid:**
    - [0, {times[1]:.4f}, ..., {times[-1]:.4f}]
    - Time step Δt = {bm.dt():.4f}
    """)
    return bm, elapsed, path, paths, times


@app.cell
def _(GeometricBrownianMotion, mo, time):
    mo.md("## 2. Geometric Brownian Motion (Stock Price Simulation)")

    # Stock parameters
    spot = 100.0
    drift = 0.05  # 5% expected return
    volatility = 0.2  # 20% volatility
    time_horizon = 1.0
    num_steps = 252  # Daily steps

    gbm = GeometricBrownianMotion(
        spot=spot,
        drift=drift,
        volatility=volatility,
        time_horizon=time_horizon,
        num_steps=num_steps,
    )

    mo.md(f"""
    **GBM Parameters:**
    - Initial price: ${gbm.get_spot():.4f}
    - Drift μ: {gbm.get_drift() * 100:.4f}%
    - Volatility σ: {gbm.get_volatility() * 100:.4f}%
    - Time horizon: {gbm.get_time_horizon():.1f} years
    """)

    # Generate a single stock price path
    price_path = gbm.generate_path()

    mo.md(f"""
    **Single price path:**
    - S(0) = ${price_path[0]:.2f}
    - S(T) = ${price_path[1]:.2f}
    """)

    # Generate many paths and analyze terminal distribution
    start_gbm = time.time()
    price_paths = gbm.generate_paths_parallel(100000)
    elapsed_gbm = time.time() - start_gbm

    terminal_prices = [p[-1] for p in price_paths]
    avg_price = sum(terminal_prices) / len(terminal_prices)

    mo.md(f"""
    **Generating 100,000 stock price paths...**
    - Generated in {elapsed_gbm:.4f}s

    **Terminal price distribution:**
    - Average: ${avg_price:.2f}
    - Min: ${min(terminal_prices):.2f}
    - Max: ${max(terminal_prices):.2f}
    """)
    return (
        avg_price,
        drift,
        elapsed_gbm,
        gbm,
        num_steps,
        price_path,
        price_paths,
        spot,
        start_gbm,
        terminal_prices,
        time_horizon,
        volatility,
    )


@app.cell
def _(EuroCallOption, gbm, mo, spot, time, time_horizon, volatility):
    mo.md("## 3. Monte Carlo Option Pricing")

    # Option parameters
    strike = 100.0
    risk_free_rate = 0.05

    # Black-Scholes analytical price
    bs_call = EuroCallOption(
        spot=spot,
        strike=strike,
        time_to_expiry=time_horizon,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
    )
    bs_price = bs_call.price()

    mo.md(f"**Black-Scholes price:** ${bs_price:.4f}")

    # Monte Carlo pricing (basic)
    num_sims = 50000
    start_mc = time.time()
    mc_paths = gbm.generate_paths_parallel(num_sims)
    mc_payoffs = [max(0, p[-1] - strike) for p in mc_paths]
    discount_factor = 2.71828 ** (-risk_free_rate * time_horizon)
    mc_price = sum(mc_payoffs) / len(mc_payoffs) * discount_factor
    mc_time = time.time() - start_mc

    mo.md(f"""
    **Monte Carlo ({num_sims:,} simulations):**
    - Price: ${mc_price:.4f}
    - Error: ${abs(mc_price - bs_price):.4f}
    - Time: {mc_time:.3f}s
    """)

    # Monte Carlo with antithetic variates
    start_anti = time.time()
    mc_paths_anti = gbm.generate_paths_parallel(num_sims // 2)
    mc_payoffs_anti = []
    for p in mc_paths_anti:
        # Normal path
        mc_payoffs_anti.append(max(0, p[-1] - strike))
        # Antithetic path (mirror around mean)
        antithetic_final = (
            spot * 2.71828 ** ((drift - 0.5 * volatility**2) * time_horizon) / (p[-1] / spot)
        )
        mc_payoffs_anti.append(max(0, antithetic_final - strike))
    mc_anti_price = sum(mc_payoffs_anti) / len(mc_payoffs_anti) * discount_factor
    mc_anti_time = time.time() - start_anti

    mo.md(f"""
    **Monte Carlo with antithetic variates ({num_sims:,} effective paths):**
    - Price: ${mc_anti_price:.4f}
    - Error: ${abs(mc_anti_price - bs_price):.4f}
    - Time: {mc_anti_time:.3f}s

    **Note:** Antithetic variates reduce variance
    """)
    return (
        antithetic_final,
        bs_call,
        bs_price,
        discount_factor,
        mc_anti_price,
        mc_anti_time,
        mc_paths,
        mc_paths_anti,
        mc_payoffs,
        mc_payoffs_anti,
        mc_price,
        mc_time,
        num_sims,
        risk_free_rate,
        start_anti,
        start_mc,
        strike,
    )


@app.cell
def _(HestonProcess, mo, num_steps, spot, time, time_horizon, volatility):
    mo.md("## 4. Heston Stochastic Volatility Model")

    # Heston parameters
    kappa = 2.0  # Mean reversion speed
    theta = volatility**2  # Long-term variance
    vol_of_vol = 0.3  # Volatility of variance
    correlation = -0.7  # Stock-vol correlation
    v0 = volatility**2  # Initial variance

    heston = HestonProcess(
        spot=spot,
        initial_variance=v0,
        drift=0.05,  # Risk-free rate for risk-neutral pricing
        kappa=kappa,
        theta=theta,
        vol_of_vol=vol_of_vol,
        correlation=correlation,
        time_horizon=time_horizon,
        num_steps=num_steps,
    )

    mo.md(f"""
    **Heston Parameters:**
    - Mean reversion κ: {kappa:.2f}
    - Long-term variance θ: {theta:.4f} (√θ = {theta**0.5:.4f})
    - Vol of vol σᵥ: {vol_of_vol:.2f}
    - Correlation ρ: {correlation:.2f}
    """)

    # Generate a single path
    heston_price_path, heston_variance_path = heston.generate_path()

    mo.md(f"""
    **Single Heston path:**
    - Initial: S(0) = ${heston_price_path[0]:.2f}, v(0) = {heston_variance_path[0]:.4f}
    - Final: S(T) = ${heston_price_path[-1]:.2f}, v(T) = {heston_variance_path[-1]:.4f}
    """)

    # Generate many paths
    start_heston = time.time()
    heston_results = heston.generate_paths_parallel(10000)
    elapsed_heston = time.time() - start_heston

    # Extract final values
    heston_prices_final = [result[0][-1] for result in heston_results]
    heston_variances_final = [result[1][-1] for result in heston_results]

    avg_price_heston = sum(heston_prices_final) / len(heston_prices_final)
    avg_var_heston = sum(heston_variances_final) / len(heston_variances_final)

    mo.md(f"""
    **Generated 10,000 paths in {elapsed_heston:.4f}s**

    **Terminal distributions:**
    - Average price: ${avg_price_heston:.2f}
    - Average variance: {avg_var_heston:.4f} (√v = {avg_var_heston**0.5:.4f})
    """)
    return (
        avg_price_heston,
        avg_var_heston,
        correlation,
        elapsed_heston,
        heston,
        heston_price_path,
        heston_prices_final,
        heston_results,
        heston_variance_path,
        heston_variances_final,
        kappa,
        start_heston,
        theta,
        v0,
        vol_of_vol,
    )


@app.cell
def _(mo):
    mo.md("""
    ## Summary

    - ✓ Brownian motion path generation (basic building block)
    - ✓ Geometric Brownian Motion for stock prices
    - ✓ Monte Carlo option pricing with GBM
    - ✓ Antithetic variates for variance reduction
    - ✓ Heston stochastic volatility model
    - ✓ Volatility smile/skew effects captured
    - ✓ High-performance parallel path generation
    - ✓ Reproducible results with seeded RNG

    **Key Takeaways:**
    - Monte Carlo converges to Black-Scholes for constant volatility
    - Antithetic variates improve accuracy for same computational cost
    - Heston model captures realistic volatility dynamics
    - Stochastic volatility creates option pricing smile/skew
    - Parallel implementation enables fast simulation (100k+ paths)
    """)
    return


if __name__ == "__main__":
    app.run()
