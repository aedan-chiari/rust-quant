import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell
def _():
    import time
    from rust_quant import EuroCallOption, EuroPutOption
    import marimo as mo

    return EuroCallOption, EuroPutOption, mo, time


@app.cell
def _(mo):
    mo.md("""
    # Example 3: Performance Benchmark (European Options)

    This example demonstrates:
    - Performance of SIMD+Parallel optimized EuroCallOption/EuroPutOption static methods
    - Scaling behavior with different dataset sizes
    - When to use single vs batch operations
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Performance Levels Available

    **1. Single Option Objects (Convenience & Flexibility)**
    - `opt = EuroCallOption(spot, strike, time, rate, vol)`
    - `opt.price()`, `opt.delta()`, `opt.greeks()`
    - Best for: Analyzing individual options, interactive use
    - Speed: ~1-10 μs per option

    **2. Vectorized SIMD + Parallel (Maximum Performance)**
    - `EuroCallOption.price_many(spots, strikes, times, rates, vols)`
    - `EuroCallOption.greeks_many(...)`
    - Best for: Pricing grids, risk analysis, batch calculations
    - Speed: ~0.1-1 μs per option (10-100x faster)
    - Uses: SIMD intrinsics (4x parallelism) + Rayon thread pool
    """)
    return


@app.cell
def _(mo):
    # Dataset size selector
    size_slider = mo.ui.slider(
        start=1000, stop=100000, step=1000, value=10000, label="Number of options to benchmark"
    )
    mo.md(f"""
    ## Benchmark Configuration

    {size_slider}
    """)
    return (size_slider,)


@app.cell
def _(EuroCallOption, EuroPutOption, mo, size_slider, time):
    n_options = size_slider.value

    # Generate test data
    spots = [100.0 + idx * 0.01 for idx in range(n_options)]
    strikes = [105.0] * n_options
    times_list = [1.0] * n_options
    rates = [0.05] * n_options
    vols = [0.2] * n_options

    # Warm up
    _ = EuroCallOption.price_many(
        spots[:100], strikes[:100], times_list[:100], rates[:100], vols[:100]
    )

    # European Call Option Pricing
    start = time.perf_counter()
    prices = EuroCallOption.price_many(spots, strikes, times_list, rates, vols)
    elapsed_call = time.perf_counter() - start

    # Greeks Calculation
    start = time.perf_counter()
    greeks_results = EuroCallOption.greeks_many(spots, strikes, times_list, rates, vols)
    elapsed_greeks = time.perf_counter() - start

    # Put Options
    start = time.perf_counter()
    prices_put = EuroPutOption.price_many(spots, strikes, times_list, rates, vols)
    elapsed_put = time.perf_counter() - start

    mo.md(f"""
    ## Benchmark Results: {n_options:,} options

    ### European Call Option Pricing (SIMD + Parallel)
    - **Time:** {elapsed_call * 1000:.2f} ms
    - **Rate:** {n_options / elapsed_call:,.0f} options/sec
    - **Per option:** {elapsed_call / n_options * 1e6:.3f} μs

    ### Greeks Calculation (SIMD + Parallel, all 6 values)
    - **Time:** {elapsed_greeks * 1000:.2f} ms
    - **Rate:** {n_options / elapsed_greeks:,.0f} options/sec
    - **Per option:** {elapsed_greeks / n_options * 1e6:.3f} μs

    ### Put Option Pricing (SIMD + Parallel)
    - **Time:** {elapsed_put * 1000:.2f} ms
    - **Rate:** {n_options / elapsed_put:,.0f} options/sec
    - **Per option:** {elapsed_put / n_options * 1e6:.3f} μs
    """)
    return (
        elapsed_call,
        elapsed_greeks,
        elapsed_put,
        greeks_results,
        n_options,
        prices,
        prices_put,
        rates,
        spots,
        strikes,
        times_list,
        vols,
    )


@app.cell
def _(EuroCallOption, mo, n_options, spots, strikes, time, times_list, rates, vols, elapsed_call):
    # Single Option Comparison (for datasets <= 10,000)
    if n_options <= 10000:
        n_sample = min(1000, n_options)
        start_single = time.perf_counter()
        for i in range(n_sample):
            opt = EuroCallOption(spots[i], strikes[i], times_list[i], rates[i], vols[i])
            _ = opt.price()
        elapsed_single = time.perf_counter() - start_single

        speedup = (elapsed_single / n_sample) / (elapsed_call / n_options)

        mo.md(f"""
        ## Single Object Creation (for comparison)

        - **Time:** {elapsed_single * 1000:.2f} ms (for {n_sample} options)
        - **Rate:** {n_sample / elapsed_single:,.0f} options/sec
        - **Per option:** {elapsed_single / n_sample * 1e6:.3f} μs

        **Vectorized speedup: {speedup:.2f}x faster per option**
        """)
    else:
        mo.md("## Single Object Comparison\n\nSkipped for large datasets (>10,000 options)")
    return


@app.cell
def _(EuroCallOption, mo):
    mo.md("## Quick Usage Example")

    # Example data
    example_spots = [95.0, 100.0, 105.0, 110.0, 115.0]
    example_strikes = [100.0] * 5
    example_times = [1.0] * 5
    example_rates = [0.05] * 5
    example_vols = [0.2] * 5

    # Batch pricing with SIMD + Parallel
    example_prices = EuroCallOption.price_many(
        example_spots, example_strikes, example_times, example_rates, example_vols
    )

    pricing_data = []
    for spot, strike, price in zip(example_spots, example_strikes, example_prices, strict=True):
        pricing_data.append(
            {"Spot": f"${spot:.2f}", "Strike": f"${strike:.2f}", "Price": f"${price:.4f}"}
        )

    mo.md("**Pricing 5 options with `EuroCallOption.price_many()`:**")
    mo.ui.table(pricing_data)
    return (
        example_prices,
        example_rates,
        example_spots,
        example_strikes,
        example_times,
        example_vols,
        pricing_data,
    )


@app.cell
def _(EuroCallOption, mo):
    mo.md("**Single option with instance methods:**")

    single_call = EuroCallOption(100.0, 105.0, 1.0, 0.05, 0.2)
    single_greeks = single_call.greeks()

    mo.md(f"""
    - Price: ${single_greeks.price:.4f}
    - Delta: {single_greeks.delta:.4f}
    - Gamma: {single_greeks.gamma:.4f}
    """)
    return single_call, single_greeks


@app.cell
def _(mo):
    mo.md("""
    ## Recommendations

    | Dataset Size | Recommended Method | Expected Performance |
    |--------------|-------------------|---------------------|
    | 1 option | `EuroCallOption(...).price()` | ~1-10 μs |
    | < 100 options | `EuroCallOption.price_many()` | < 1ms |
    | 100 - 10,000 | `EuroCallOption.price_many()` | 1-10ms |
    | 10,000 - 100,000 | `EuroCallOption.price_many()` | 10-50ms |
    | 100,000+ | `EuroCallOption.price_many()` | 50-200ms |

    ### Key Takeaways:
    - Always use `EuroCallOption.price_many()` / `EuroPutOption.price_many()` for batch operations
    - The static methods use SIMD intrinsics and parallel processing automatically
    - Speedup increases with dataset size (parallelization overhead amortized)
    - For single options, create once and reuse (call `.price()`, `.delta()`, `.greeks()` multiple times)
    """)
    return


if __name__ == "__main__":
    app.run()
