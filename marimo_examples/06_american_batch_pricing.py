import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell
def _():
    import time
    from rust_quant import AmericanCallOption, AmericanPutOption, EuroCallOption
    import marimo as mo

    return AmericanCallOption, AmericanPutOption, EuroCallOption, mo, time


@app.cell
def _(mo):
    mo.md("""
    # Example 6: Batch Pricing for American Options

    This example demonstrates:
    - Pricing multiple American options at once using static methods
    - Calculating Greeks for multiple American options simultaneously
    - Performance comparison: batch vs individual pricing
    - Comparison with European option batch pricing
    """)
    return


@app.cell
def _(AmericanCallOption, mo):
    mo.md("## 1. Pricing Multiple American Call Options")

    # Create sample parameters
    spots = [95.0, 100.0, 105.0, 110.0, 115.0]
    strikes = [100.0] * 5  # All have same strike
    times = [1.0] * 5  # All expire in 1 year
    rates = [0.05] * 5  # All use 5% risk-free rate
    vols = [0.2] * 5  # All have 20% volatility
    dividend_yields = [0.0] * 5  # No dividends
    steps = 100

    mo.md(f"""
    Using `AmericanCallOption.price_many()` - Rayon parallel pricing

    Pricing **{len(spots)}** American call options with different spot prices:
    """)

    # Use static method to price all at once (parallelized with Rayon)
    prices = AmericanCallOption.price_many(
        spots, strikes, times, rates, vols, dividend_yields, steps
    )

    pricing_table = []
    for s, p in zip(spots, prices, strict=True):
        intrinsic_val = max(0, s - 100.0)
        moneyness = "OTM" if s < 100 else ("ITM" if s > 100 else "ATM")
        pricing_table.append(
            {
                "Spot Price": f"${s:.2f}",
                "Call Price": f"${p:.4f}",
                "Intrinsic": f"${intrinsic_val:.2f}",
                "Moneyness": moneyness,
            }
        )

    mo.ui.table(pricing_table)
    return (
        dividend_yields,
        prices,
        pricing_table,
        rates,
        spots,
        steps,
        strikes,
        times,
        vols,
    )


@app.cell
def _(
    AmericanCallOption,
    dividend_yields,
    mo,
    rates,
    spots,
    steps,
    strikes,
    times,
    vols,
):
    mo.md("## 2. Calculating Greeks for Multiple American Options")

    mo.md("Using `AmericanCallOption.greeks_many()` - parallel Greeks calculation")

    greeks_prices, deltas, gammas, vegas, thetas, rhos = AmericanCallOption.greeks_many(
        spots, strikes, times, rates, vols, dividend_yields, steps
    )

    greeks_table = []
    for idx in range(len(spots)):
        greeks_table.append(
            {
                "Spot": f"${spots[idx]:.2f}",
                "Price": f"${greeks_prices[idx]:.4f}",
                "Delta": f"{deltas[idx]:.4f}",
                "Gamma": f"{gammas[idx]:.4f}",
                "Vega": f"{vegas[idx]:.4f}",
            }
        )

    mo.ui.table(greeks_table)
    return deltas, gammas, greeks_prices, greeks_table, rhos, thetas, vegas


@app.cell
def _(
    AmericanPutOption,
    dividend_yields,
    mo,
    rates,
    spots,
    steps,
    strikes,
    times,
    vols,
):
    mo.md("## 3. American Put Options (Same API)")

    put_prices = AmericanPutOption.price_many(
        spots, strikes, times, rates, vols, dividend_yields, steps
    )

    put_table = []
    for s_put, p_put in zip(spots, put_prices, strict=True):
        intrinsic_put = max(0, 100.0 - s_put)
        time_value_put = p_put - intrinsic_put
        put_table.append(
            {
                "Spot Price": f"${s_put:.2f}",
                "Put Price": f"${p_put:.4f}",
                "Intrinsic": f"${intrinsic_put:.2f}",
                "Early Exercise Premium": f"${time_value_put:.4f}",
            }
        )

    mo.ui.table(put_table)
    return put_prices, put_table


@app.cell
def _(AmericanCallOption, mo, time):
    mo.md("## 4. Performance Comparison")

    # Create larger dataset
    n = 1000
    large_spots = [95.0 + (j * 30.0 / n) for j in range(n)]
    large_strikes = [100.0] * n
    large_times = [1.0] * n
    large_rates = [0.05] * n
    large_vols = [0.2] * n
    large_dividends = [0.0] * n
    perf_steps = 100

    mo.md(f"Pricing **{n}** American call options...")

    # Batch pricing
    start = time.time()
    batch_prices = AmericanCallOption.price_many(
        large_spots,
        large_strikes,
        large_times,
        large_rates,
        large_vols,
        large_dividends,
        perf_steps,
    )
    batch_time = time.time() - start

    # Individual pricing
    start = time.time()
    individual_prices = []
    for k in range(n):
        opt = AmericanCallOption(
            large_spots[k],
            large_strikes[k],
            large_times[k],
            large_rates[k],
            large_vols[k],
            large_dividends[k],
            perf_steps,
        )
        individual_prices.append(opt.price())
    individual_time = time.time() - start

    # Verify results match
    max_diff = max(abs(b - i) for b, i in zip(batch_prices, individual_prices, strict=True))

    mo.md(f"""
    - **Batch pricing (Rayon):** {batch_time:.4f} seconds
    - **Individual pricing:** {individual_time:.4f} seconds
    - **Speedup:** {individual_time / batch_time:.2f}x
    - **Per-option (batch):** {batch_time / n * 1000:.3f} ms
    - **Per-option (individual):** {individual_time / n * 1000:.3f} ms

    **Maximum price difference:** {max_diff:.6f} (should be ~0)
    """)
    return (
        batch_prices,
        batch_time,
        individual_prices,
        individual_time,
        large_dividends,
        large_rates,
        large_spots,
        large_strikes,
        large_times,
        large_vols,
        max_diff,
        n,
        perf_steps,
    )


@app.cell
def _(
    AmericanCallOption,
    AmericanPutOption,
    EuroCallOption,
    dividend_yields,
    mo,
    rates,
    spots,
    steps,
    strikes,
    times,
    vols,
):
    mo.md("""
    ## 5. American vs European Options (No Dividends)

    Without dividends, American calls equal European calls:
    (Early exercise is never optimal for calls without dividends)
    """)

    american_call_prices = AmericanCallOption.price_many(
        spots, strikes, times, rates, vols, dividend_yields, steps
    )
    european_call_prices = EuroCallOption.price_many(spots, strikes, times, rates, vols)

    comparison_table = []
    for m in range(len(spots)):
        diff_call = american_call_prices[m] - european_call_prices[m]
        comparison_table.append(
            {
                "Spot": f"${spots[m]:.2f}",
                "American Call": f"${american_call_prices[m]:.4f}",
                "European Call": f"${european_call_prices[m]:.4f}",
                "Difference": f"${diff_call:.6f}",
            }
        )

    mo.ui.table(comparison_table)

    mo.md("**For puts, American options have early exercise premium:**")

    american_put_prices = AmericanPutOption.price_many(
        spots, strikes, times, rates, vols, dividend_yields, steps
    )

    put_comparison_table = []
    for n_idx in range(len(spots)):
        intrinsic_comp = max(0, strikes[n_idx] - spots[n_idx])
        time_value_comp = american_put_prices[n_idx] - intrinsic_comp
        put_comparison_table.append(
            {
                "Spot": f"${spots[n_idx]:.2f}",
                "American Put": f"${american_put_prices[n_idx]:.4f}",
                "Intrinsic": f"${intrinsic_comp:.2f}",
                "Time Value": f"${time_value_comp:.4f}",
            }
        )

    mo.ui.table(put_comparison_table)
    return (
        american_call_prices,
        american_put_prices,
        comparison_table,
        european_call_prices,
        put_comparison_table,
    )


@app.cell
def _(AmericanCallOption, mo, rates, spots, steps, strikes, times, vols):
    mo.md("""
    ## 6. Effect of Dividends on American Call Options

    With dividends, American calls can have early exercise value:
    """)

    # High dividend yield case
    high_dividends = [0.08] * 5  # 8% dividend yield

    american_no_div = AmericanCallOption.price_many(
        spots, strikes, times, rates, vols, [0.0] * 5, steps
    )
    american_with_div = AmericanCallOption.price_many(
        spots, strikes, times, rates, vols, high_dividends, steps
    )

    dividend_table = []
    for q in range(len(spots)):
        diff_div = american_no_div[q] - american_with_div[q]
        dividend_table.append(
            {
                "Spot": f"${spots[q]:.2f}",
                "No Dividend": f"${american_no_div[q]:.4f}",
                "8% Dividend": f"${american_with_div[q]:.4f}",
                "Difference": f"${diff_div:.4f}",
            }
        )

    mo.ui.table(dividend_table)

    mo.md("**Note:** Dividends reduce call values as they lower expected stock price.")
    return american_no_div, american_with_div, dividend_table, high_dividends


@app.cell
def _(mo):
    mo.md("""
    ## Summary

    - ✓ American options support parallel batch pricing via Rayon
    - ✓ Same API as European options: `price_many()` and `greeks_many()`
    - ✓ Significant speedup for pricing many options
    - ✓ American puts always have early exercise premium
    - ✓ American calls equal European calls (no dividends)
    - ✓ Dividends create early exercise value for American calls
    """)
    return


if __name__ == "__main__":
    app.run()
