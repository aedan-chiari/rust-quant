import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell
def _():
    """Import required libraries"""
    import math
    from rust_quant import EuroCallOption, EuroPutOption
    import marimo as mo

    return EuroCallOption, EuroPutOption, math, mo


@app.cell
def _(mo):
    mo.md("""
    # Example 1: Basic European Option Pricing

    This example demonstrates:
    - Creating EuroCallOption and EuroPutOption objects
    - Calculating price and individual Greeks
    - Calculating all Greeks at once (more efficient)
    - Using immutable update methods (with_spot, with_volatility, etc.)
    """)
    return


@app.cell
def _(EuroCallOption, EuroPutOption, mo):
    mo.md("## 1. Creating European Options")

    # Create a European call option
    call = EuroCallOption(
        spot=100.0,  # Current stock price
        strike=105.0,  # Strike price
        time_to_expiry=1.0,  # Time to expiration (years)
        risk_free_rate=0.05,  # Risk-free interest rate (5%)
        volatility=0.2,  # Volatility (20%)
    )

    # Create a European put option with same parameters
    put = EuroPutOption(100.0, 105.0, 1.0, 0.05, 0.2)

    mo.md(f"""
    **European Call Option:**
    - Spot: ${call.spot}
    - Strike: ${call.strike}
    - Time to Expiry: {call.time_to_expiry} years
    - Risk-free Rate: {call.risk_free_rate * 100}%
    - Volatility: {call.volatility * 100}%
    - **Price: ${call.price():.4f}**

    **European Put Option:**
    - **Price: ${put.price():.4f}**
    """)
    return call, put


@app.cell
def _(call, mo):
    mo.md("""
    ## 2. Calculating Individual Greeks

    Note: We reuse the same 'call' object - no wasteful re-creation!
    """)

    greeks_individual = {
        "Delta (Δ)": (call.delta(), "Sensitivity to underlying price"),
        "Gamma (Γ)": (call.gamma(), "Rate of change of delta"),
        "Vega (ν)": (call.vega(), "Sensitivity to volatility"),
        "Theta (θ)": (call.theta(), "Time decay"),
        "Rho (ρ)": (call.rho(), "Sensitivity to interest rate"),
    }

    mo.md(
        "**Individual Greeks:**\n\n"
        + "\n".join(
            [
                f"- **{name}**: {value:.4f} - {desc}"
                for name, (value, desc) in greeks_individual.items()
            ]
        )
    )
    return


@app.cell
def _(call, mo):
    mo.md("""
    ## 3. Calculate All Greeks at Once (Recommended)

    More efficient than calling individual methods.
    """)

    greeks = call.greeks()

    mo.md(f"""
    **All Greeks:**
    - Price: ${greeks.price:.4f}
    - Delta: {greeks.delta:.4f}
    - Gamma: {greeks.gamma:.4f}
    - Vega: {greeks.vega:.4f}
    - Theta: {greeks.theta:.4f}
    - Rho: {greeks.rho:.4f}
    """)
    return


@app.cell
def _(call, mo):
    mo.md("""
    ## 4. Scenario Analysis with Immutable Updates

    The `with_*()` methods create new option objects without modifying the original.
    """)

    # Create new options with different parameters
    higher_spot = call.with_spot(110.0)
    higher_vol = call.with_volatility(0.3)
    less_time = call.with_time(0.5)

    mo.md(f"""
    **Original Option:**
    - Spot: ${call.spot:.2f}, Price: ${call.price():.4f}

    **Higher Spot ($110):**
    - Spot: ${higher_spot.spot:.2f}, Price: ${higher_spot.price():.4f}

    **Higher Volatility (30%):**
    - Vol: {higher_vol.volatility:.2f}, Price: ${higher_vol.price():.4f}

    **Less Time (0.5 years):**
    - Time: {less_time.time_to_expiry:.2f}yr, Price: ${less_time.price():.4f}

    **Original option unchanged:** `{call}`
    """)
    return


@app.cell
def _(call, math, mo, put):
    mo.md("""
    ## 5. Put-Call Parity Verification

    Formula: C - P = S - K·e^(-rT)
    """)

    call_price = call.price()
    put_price = put.price()
    parity_lhs = call_price - put_price
    parity_rhs = call.spot - call.strike * math.exp(-call.risk_free_rate * call.time_to_expiry)
    difference = abs(parity_lhs - parity_rhs)

    mo.md(f"""
    - Call Price: ${call_price:.4f}
    - Put Price: ${put_price:.4f}
    - C - P: {parity_lhs:.4f}
    - S - K·e^(-rT): {parity_rhs:.4f}
    - Difference: {difference:.6f} {"✓ PASS" if difference < 0.01 else "✗ FAIL"}
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Summary

    - ✓ Create option objects once and reuse them
    - ✓ Use `.greeks()` to get all values efficiently
    - ✓ Use `.with_*()` methods for scenario analysis
    """)
    return


if __name__ == "__main__":
    app.run()
