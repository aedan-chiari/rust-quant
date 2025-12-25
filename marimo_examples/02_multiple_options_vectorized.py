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
    # Example 2: Vectorized Pricing for Multiple European Options

    This example demonstrates:
    - Pricing multiple European options at once using static methods
    - Calculating Greeks for multiple options simultaneously
    - Performance comparison: vectorized vs individual pricing
    """)
    return


@app.cell
def _(EuroCallOption, mo):
    mo.md("## 1. Pricing Multiple European Call Options")

    # Define parameters for 5 options with different spot prices
    spots = [95.0, 100.0, 105.0, 110.0, 115.0]
    strikes = [100.0] * 5  # All have same strike
    times = [1.0] * 5  # All expire in 1 year
    rates = [0.05] * 5  # All use 5% risk-free rate
    vols = [0.2] * 5  # All have 20% volatility

    # Use static method to price all at once
    prices = EuroCallOption.price_many(spots, strikes, times, rates, vols)

    # Create table data
    price_data = []
    for spot, price in zip(spots, prices, strict=True):
        if spot < 100:
            moneyness = "OTM (Out of the Money)"
        elif spot > 100:
            moneyness = "ITM (In the Money)"
        else:
            moneyness = "ATM (At the Money)"
        price_data.append(
            {"Spot Price": f"${spot:.2f}", "Call Price": f"${price:.4f}", "Moneyness": moneyness}
        )

    mo.md(f"""
    Using `EuroCallOption.price_many()` - static method

    Pricing **{len(spots)}** European options with different spot prices:
    """)

    mo.ui.table(price_data)
    return rates, spots, strikes, times, vols


@app.cell
def _(EuroCallOption, mo, rates, spots, strikes, times, vols):
    mo.md("## 2. Calculating Greeks for Multiple Options")

    mo.md("Using `EuroCallOption.greeks_many()` - static method")

    greeks_prices, deltas, gammas, vegas, thetas, rhos = EuroCallOption.greeks_many(
        spots, strikes, times, rates, vols
    )

    greeks_data = []
    for idx in range(len(spots)):
        greeks_data.append(
            {
                "Spot": f"${spots[idx]:.2f}",
                "Price": f"${greeks_prices[idx]:.4f}",
                "Delta": f"{deltas[idx]:.4f}",
                "Gamma": f"{gammas[idx]:.4f}",
                "Vega": f"{vegas[idx]:.4f}",
            },
        )

    mo.ui.table(greeks_data)
    return (greeks_prices,)


@app.cell
def _(EuroPutOption, greeks_prices, mo, rates, spots, strikes, times, vols):
    mo.md("## 3. Put Options (Same API)")

    put_prices = EuroPutOption.price_many(spots, strikes, times, rates, vols)

    put_data = []
    for j in range(len(spots)):
        put_data.append(
            {
                "Spot Price": f"${spots[j]:.2f}",
                "Put Price": f"${put_prices[j]:.4f}",
                "Call Price": f"${greeks_prices[j]:.4f}",
            }
        )

    mo.ui.table(put_data)
    return


@app.cell
def _(EuroCallOption, mo, time):
    mo.md("## 4. Performance: Vectorized vs Individual")

    n_options = 1000

    # Generate test data
    test_spots = [100.0 + k * 0.1 for k in range(n_options)]
    test_strikes = [105.0] * n_options
    test_times = [1.0] * n_options
    test_rates = [0.05] * n_options
    test_vols = [0.2] * n_options

    # Method 1: Vectorized using static method
    start = time.perf_counter()
    vec_prices = EuroCallOption.price_many(
        test_spots, test_strikes, test_times, test_rates, test_vols
    )
    vec_time = time.perf_counter() - start

    # Method 2: Individual option objects (for comparison, only 100 options)
    start = time.perf_counter()
    ind_prices = []
    for m in range(min(100, n_options)):
        opt = EuroCallOption(
            test_spots[m],
            test_strikes[m],
            test_times[m],
            test_rates[m],
            test_vols[m],
        )
        ind_prices.append(opt.price())
    ind_time = time.perf_counter() - start

    speedup = (ind_time / 100) / (vec_time / n_options)

    mo.md(f"""
    **Vectorized (EuroCallOption.price_many):**
    - Time: {vec_time * 1000:.4f}ms
    - Rate: {n_options / vec_time:.0f} options/sec

    **Individual objects (100 options):**
    - Time: {ind_time * 1000:.4f}ms
    - Rate: {100 / ind_time:.0f} options/sec

    **Speedup: {speedup:.2f}x faster per option**
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## 5. When to Use Each Approach

    **Single Option (Instance Methods):**
    - When analyzing ONE specific option
    - When you need to call multiple Greeks on the same option
    - Example: `call = EuroCallOption(...); call.delta(); call.gamma()`

    **Vectorized (Static Methods):**
    - When pricing MANY options at once
    - When building a pricing grid or surface
    - Example: `EuroCallOption.price_many(spots, strikes, times, rates, vols)`

    **Best Practice:**
    - Create single option objects once and reuse them
    - Use vectorized methods for bulk calculations
    - Use `.greeks()` when you need multiple Greeks for one option
    """)
    return


if __name__ == "__main__":
    app.run()
