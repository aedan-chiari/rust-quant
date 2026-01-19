import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell
def _():
    from rust_quant import (
        AmericanCallOption,
        AmericanPutOption,
        EuroCallOption,
        EuroPutOption,
    )
    import marimo as mo

    return (
        AmericanCallOption,
        AmericanPutOption,
        EuroCallOption,
        EuroPutOption,
        mo,
    )


@app.cell
def _(mo):
    mo.md("""
    # Example 5: American Option Pricing

    This example demonstrates:
    - Creating AmericanCallOption and AmericanPutOption objects
    - Understanding early exercise premium
    - Comparing American vs European options
    - Effect of binomial tree steps on accuracy
    - Pricing with dividend yields
    """)
    return


@app.cell
def _(AmericanCallOption, AmericanPutOption, mo):
    mo.md("## 1. Basic American Option Pricing")

    # Create American call and put options
    american_call = AmericanCallOption(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
        steps=100,  # Number of binomial tree steps
    )

    american_put = AmericanPutOption(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
        steps=100,
    )

    mo.md(f"""
    - **American Call Price:** ${american_call.price():.4f}
    - **American Call Delta:** {american_call.delta():.4f}
    - **American Put Price:** ${american_put.price():.4f}
    - **American Put Delta:** {american_put.delta():.4f}
    """)
    return american_call, american_put


@app.cell
def _(AmericanPutOption, EuroCallOption, EuroPutOption, mo):
    mo.md("""
    ## 2. Early Exercise Premium (American vs European)

    American options allow early exercise, making them worth more than European options (especially puts).
    """)

    # Compare American and European puts (ITM scenario)
    spot_itm = 90.0  # In-the-money for puts
    strike_itm = 100.0

    american_put_itm = AmericanPutOption(
        spot=spot_itm,
        strike=strike_itm,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
        steps=100,
    )

    european_put_itm = EuroPutOption(
        spot=spot_itm,
        strike=strike_itm,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
    )

    american_price = american_put_itm.price()
    european_price = european_put_itm.price()
    intrinsic = strike_itm - spot_itm
    early_premium = american_price - european_price

    mo.md(f"""
    **In-the-Money Put Comparison:**
    - Spot Price: ${spot_itm:.2f}
    - Strike Price: ${strike_itm:.2f}
    - Intrinsic Value: ${intrinsic:.4f} (K - S)

    - **European Put Price:** ${european_price:.4f}
    - **American Put Price:** ${american_price:.4f}
    - **Early Exercise Premium:** ${early_premium:.4f} ({early_premium / european_price * 100:.2f}%)
    """)
    return (
        american_price,
        american_put_itm,
        early_premium,
        european_price,
        european_put_itm,
        intrinsic,
        spot_itm,
        strike_itm,
    )


@app.cell
def _(AmericanCallOption, EuroCallOption, mo, spot_itm, strike_itm):
    # For calls without dividends, American ≈ European
    american_call_itm = AmericanCallOption(
        spot=spot_itm,
        strike=strike_itm,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
        steps=100,
    )
    european_call_itm = EuroCallOption(
        spot=spot_itm,
        strike=strike_itm,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
    )

    mo.md(f"""
    **Without dividends, American calls ≈ European calls:**
    - American Call: ${american_call_itm.price():.4f}
    - European Call: ${european_call_itm.price():.4f}
    """)
    return american_call_itm, european_call_itm


@app.cell
def _(AmericanPutOption, mo):
    mo.md("""
    ## 3. Effect of Binomial Tree Steps on Accuracy

    More steps = higher accuracy but slower computation
    """)

    spot_conv = 100.0
    strike_conv = 100.0

    convergence_results = []
    for steps in [25, 50, 100, 200]:
        american_conv = AmericanPutOption(
            spot=spot_conv,
            strike=strike_conv,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=steps,
        )
        convergence_results.append({"Steps": steps, "Price": f"${american_conv.price():.4f}"})

    mo.md("**Note:** Prices converge as steps increase")
    mo.ui.table(convergence_results)
    return convergence_results, spot_conv, steps, strike_conv


@app.cell
def _(AmericanCallOption, mo):
    mo.md("""
    ## 4. American Options with Dividend Yields

    Dividends make early exercise more attractive for puts,
    and can make early exercise optimal for calls.
    """)

    spot_div = 100.0
    strike_div = 90.0  # Deep ITM call
    dividend_yield = 0.08  # High 8% dividend

    # Without dividend
    american_call_no_div = AmericanCallOption(
        spot=spot_div,
        strike=strike_div,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
        dividend_yield=0.0,
        steps=100,
    )

    # With high dividend
    american_call_with_div = AmericanCallOption(
        spot=spot_div,
        strike=strike_div,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
        dividend_yield=dividend_yield,
        steps=100,
    )

    no_div_price = american_call_no_div.price()
    with_div_price = american_call_with_div.price()

    mo.md(f"""
    **Deep ITM American Call (S=${spot_div}, K=${strike_div}):**
    - No Dividend (q=0.0): ${no_div_price:.4f}
    - With Dividend (q=0.08): ${with_div_price:.4f}
    - Difference: ${no_div_price - with_div_price:.4f}

    **Note:** High dividends reduce call value (stock price drops on ex-div date)
    """)
    return (
        american_call_no_div,
        american_call_with_div,
        dividend_yield,
        no_div_price,
        spot_div,
        strike_div,
        with_div_price,
    )


@app.cell
def _(AmericanCallOption, mo):
    mo.md("""
    ## 5. American Option Greeks

    Greeks are calculated using finite difference methods
    """)

    american_greeks_opt = AmericanCallOption(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
        steps=100,
    )

    greeks_am = american_greeks_opt.greeks()

    mo.md(f"""
    - **Option Price:** ${greeks_am.price:.4f}
    - **Delta (Δ):** {greeks_am.delta:.4f} - Price sensitivity to spot
    - **Gamma (Γ):** {greeks_am.gamma:.4f} - Rate of change of delta
    - **Vega (ν):** {greeks_am.vega:.4f} - Sensitivity to volatility
    - **Theta (Θ):** {greeks_am.theta:.4f} - Time decay
    - **Rho (ρ):** {greeks_am.rho:.4f} - Interest rate sensitivity
    """)
    return american_greeks_opt, greeks_am


@app.cell
def _(AmericanPutOption, mo):
    mo.md("""
    ## 6. Immutable Update Methods

    Create new option instances with updated parameters
    """)

    base_option = AmericanPutOption(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
        steps=100,
    )

    # Create new options with different spot prices
    option_95 = base_option.with_spot(95.0)
    option_105 = base_option.with_spot(105.0)

    # Update volatility
    high_vol_option = base_option.with_volatility(0.4)

    # Update number of steps
    precise_option = base_option.with_steps(200)

    mo.md(f"""
    - **Base option (S=100):** ${base_option.price():.4f}
    - **With spot=95 (ITM):** ${option_95.price():.4f}
    - **With spot=105 (OTM):** ${option_105.price():.4f}
    - **With volatility=0.4:** ${high_vol_option.price():.4f}
    - **With 200 steps (more accurate):** ${precise_option.price():.4f}
    """)
    return base_option, high_vol_option, option_105, option_95, precise_option


@app.cell
def _(mo):
    mo.md("""
    ## Summary

    American options provide flexibility through early exercise,
    making them particularly valuable for dividend-paying stocks
    and in-the-money put positions.
    """)
    return


if __name__ == "__main__":
    app.run()
