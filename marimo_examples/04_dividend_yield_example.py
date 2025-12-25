import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell
def _():
    import math
    from rust_quant import EuroCallOption, EuroPutOption
    import marimo as mo

    return EuroCallOption, EuroPutOption, math, mo


@app.cell
def _(mo):
    mo.md("""
    # Example 4: Pricing European Options with Dividend Yields

    This example demonstrates how to price European options on dividend-paying assets
    using the Black-Scholes-Merton model.
    """)
    return


@app.cell
def _(EuroCallOption, EuroPutOption, mo):
    mo.md("## 1. Non-Dividend Paying Stock (dividend_yield=0.0)")

    # Common parameters
    spot = 100.0
    strike = 100.0
    time_to_expiry = 1.0
    risk_free_rate = 0.05
    volatility = 0.2

    call_no_div = EuroCallOption(
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=0.0,
    )

    put_no_div = EuroPutOption(
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=0.0,
    )

    mo.md(f"""
    - Call Price: ${call_no_div.price():.4f}
    - Call Delta: {call_no_div.delta():.4f}
    - Put Price: ${put_no_div.price():.4f}
    - Put Delta: {put_no_div.delta():.4f}
    """)
    return (
        call_no_div,
        put_no_div,
        risk_free_rate,
        spot,
        strike,
        time_to_expiry,
        volatility,
    )


@app.cell
def _(
    EuroCallOption,
    EuroPutOption,
    mo,
    risk_free_rate,
    spot,
    strike,
    time_to_expiry,
    volatility,
):
    mo.md("## 2. Dividend-Paying Stock (dividend_yield=0.02 or 2%)")

    dividend_yield = 0.02

    call_with_div = EuroCallOption(
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
    )

    put_with_div = EuroPutOption(
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
    )

    mo.md(f"""
    - Call Price: ${call_with_div.price():.4f}
    - Call Delta: {call_with_div.delta():.4f}
    - Put Price: ${put_with_div.price():.4f}
    - Put Delta: {put_with_div.delta():.4f}
    """)
    return call_with_div, dividend_yield, put_with_div


@app.cell
def _(call_no_div, call_with_div, mo, put_no_div, put_with_div):
    mo.md("## 3. Impact of Dividends")

    call_diff = call_no_div.price() - call_with_div.price()
    put_diff = put_with_div.price() - put_no_div.price()

    mo.md(f"""
    - **Call price reduction:** ${call_diff:.4f} ({call_diff / call_no_div.price() * 100:.2f}%)
    - **Put price increase:** ${put_diff:.4f} ({put_diff / put_no_div.price() * 100:.2f}%)

    **Note:** Dividends reduce call values and increase put values
    """)
    return call_diff, put_diff


@app.cell
def _(
    EuroCallOption,
    EuroPutOption,
    mo,
    risk_free_rate,
    spot,
    strike,
    time_to_expiry,
    volatility,
):
    mo.md("## 4. Stock Index with Higher Dividend Yield (3%)")

    index_div_yield = 0.03

    call_index = EuroCallOption(
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=index_div_yield,
    )

    put_index = EuroPutOption(
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=index_div_yield,
    )

    mo.md(f"""
    - Call Price: ${call_index.price():.4f}
    - Put Price: ${put_index.price():.4f}
    """)
    return call_index, index_div_yield, put_index


@app.cell
def _(
    call_with_div,
    dividend_yield,
    math,
    mo,
    put_with_div,
    risk_free_rate,
    spot,
    strike,
    time_to_expiry,
):
    mo.md("## 5. Put-Call Parity Verification (with dividends)")

    call_price = call_with_div.price()
    put_price = put_with_div.price()

    lhs = call_price - put_price
    rhs = spot * math.exp(-dividend_yield * time_to_expiry) - strike * math.exp(
        -risk_free_rate * time_to_expiry
    )

    mo.md(f"""
    - C - P = {lhs:.4f}
    - S*e^(-qT) - K*e^(-rT) = {rhs:.4f}
    - Difference: {abs(lhs - rhs):.4f} (should be ~0)

    **Put-call parity holds! ✓**
    """)
    return call_price, lhs, put_price, rhs


@app.cell
def _(EuroCallOption, EuroPutOption, mo):
    mo.md("""
    ## 6. Real-World Example: Large-Cap Tech Stock

    **Stock:** AAPL (example)
    - Spot: $175.00, Strike: $180.00, 6 months to expiry
    - Implied Vol: 25%, Risk-free rate: 4.5%, Dividend yield: 0.5%
    """)

    aapl_call = EuroCallOption(
        spot=175.0,
        strike=180.0,
        time_to_expiry=0.5,
        risk_free_rate=0.045,
        volatility=0.25,
        dividend_yield=0.005,
    )

    aapl_put = EuroPutOption(
        spot=175.0,
        strike=180.0,
        time_to_expiry=0.5,
        risk_free_rate=0.045,
        volatility=0.25,
        dividend_yield=0.005,
    )

    greeks_call = aapl_call.greeks()
    greeks_put = aapl_put.greeks()

    mo.md(f"""
    **Call Option:**
    - Price: ${greeks_call.price:.4f}
    - Delta: {greeks_call.delta:.4f}
    - Gamma: {greeks_call.gamma:.4f}
    - Vega: {greeks_call.vega:.4f}
    - Theta: {greeks_call.theta:.4f} (per day)
    - Rho: {greeks_call.rho:.4f}

    **Put Option:**
    - Price: ${greeks_put.price:.4f}
    - Delta: {greeks_put.delta:.4f}
    - Gamma: {greeks_put.gamma:.4f}
    - Vega: {greeks_put.vega:.4f}
    - Theta: {greeks_put.theta:.4f} (per day)
    - Rho: {greeks_put.rho:.4f}
    """)
    return aapl_call, aapl_put, greeks_call, greeks_put


@app.cell
def _(mo):
    mo.md("""
    ## Summary

    **Key Takeaways:**
    1. Dividend yields reduce call option values (holders don't receive dividends)
    2. Dividend yields increase put option values (stock price drops by dividend)
    3. Higher dividend yields mean lower forward prices
    4. Put-call parity must account for dividends: C - P = S*e^(-qT) - K*e^(-rT)
    5. Default dividend_yield=0.0 maintains backward compatibility

    **When to use dividend_yield parameter:**
    - Dividend-paying stocks (most large-cap stocks)
    - Stock indices (S&P 500 ~1.5-2% yield)
    - Currency options (foreign interest rate differential)
    - Commodity options with storage costs
    """)
    return


if __name__ == "__main__":
    app.run()
