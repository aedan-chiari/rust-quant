import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell
def _():
    import math
    from rust_quant import ForwardCurve, Security, ZeroCouponCurve
    import marimo as mo

    return ForwardCurve, Security, ZeroCouponCurve, math, mo


@app.cell
def _(mo):
    mo.md("""
    # Example 7: Zero Coupon Curve Construction and Usage

    This example demonstrates:
    - Creating a zero-coupon yield curve from market securities
    - Calculating discount factors and zero rates
    - Computing forward rates using ForwardCurve
    - Valuing bonds and cash flows
    - Using batch operations for performance
    """)
    return


@app.cell
def _(Security, ZeroCouponCurve, mo):
    mo.md("## 1. Creating a Zero Coupon Curve from Securities")

    # Create sample zero-coupon bond securities for curve construction
    securities = [
        Security(maturity=0.25, price=98.75, face_value=100.0),  # 3-month
        Security(maturity=0.5, price=97.50, face_value=100.0),  # 6-month
        Security(maturity=1.0, price=95.00, face_value=100.0),  # 1-year
        Security(maturity=2.0, price=90.00, face_value=100.0),  # 2-year
        Security(maturity=5.0, price=78.35, face_value=100.0),  # 5-year
        Security(maturity=10.0, price=61.39, face_value=100.0),  # 10-year
    ]

    curve = ZeroCouponCurve(securities)

    mo.md(f"""
    Curve created with **{curve.size()}** securities

    **Maturities:** {curve.maturities()}

    **Alternative: Create from vectors**
    """)

    # Alternative: Create from vectors
    maturities = [1.0, 2.0, 3.0, 5.0, 7.0, 10.0]
    prices = [95.0, 90.0, 85.5, 78.35, 70.89, 61.39]

    curve_from_vectors = ZeroCouponCurve.from_vectors(maturities, prices)

    mo.md(f"Curve from vectors created with **{curve_from_vectors.size()}** securities")
    return curve, curve_from_vectors, maturities, prices, securities


@app.cell
def _(curve, mo):
    mo.md("## 2. Calculating Discount Factors")

    df_results = []
    for mat in [0.5, 1.0, 2.0, 5.0, 10.0]:
        df_val = curve.discount_factor(mat)
        df_results.append({"Maturity (years)": mat, "Discount Factor": f"{df_val:.6f}"})

    mo.md("**Discount factors for exact maturities:**")
    mo.ui.table(df_results)

    df_interpolated = curve.discount_factor(3.0)
    df_extrapolated = curve.discount_factor(15.0)

    mo.md(f"""
    **With interpolation:**
    - DF(3.0 years) = {df_interpolated:.6f} (interpolated)

    **With extrapolation:**
    - DF(15.0 years) = {df_extrapolated:.6f} (extrapolated)
    """)
    return df_extrapolated, df_interpolated, df_results


@app.cell
def _(curve, math, mo):
    mo.md("## 3. Calculating Zero Rates (Continuously Compounded)")

    zero_rate_results = []
    for mat_zr in [0.25, 0.5, 1.0, 2.0, 5.0, 10.0]:
        zero_rate = curve.zero_rate(mat_zr)
        zero_rate_results.append(
            {"Maturity (years)": mat_zr, "Zero Rate": f"{zero_rate * 100:.4f}%"}
        )

    mo.md("**Zero rates for key maturities:**")
    mo.ui.table(zero_rate_results)

    # Verify relationship: DF(T) = exp(-r(T) * T)
    t_verify = 5.0
    df_verify = curve.discount_factor(t_verify)
    r_verify = curve.zero_rate(t_verify)
    df_calculated = math.exp(-r_verify * t_verify)

    mo.md(f"""
    **Verifying DF = exp(-r*T):**
    - DF({t_verify}) from curve: {df_verify:.6f}
    - DF({t_verify}) calculated: {df_calculated:.6f}
    - Difference: {abs(df_verify - df_calculated):.10f}
    """)
    return df_calculated, df_verify, r_verify, t_verify, zero_rate_results


@app.cell
def _(ForwardCurve, curve, mo):
    mo.md("## 4. Calculating Forward Rates with ForwardCurve")

    # Create a ForwardCurve from the ZeroCouponCurve
    forward_curve = ForwardCurve(curve)

    fwd_results = []
    for t1_fwd in range(1, 5):
        t2_fwd = t1_fwd + 1
        fwd_rate = forward_curve.forward_rate(float(t1_fwd), float(t2_fwd))
        fwd_results.append(
            {"Period": f"f({t1_fwd},{t2_fwd})", "Forward Rate": f"{fwd_rate * 100:.4f}%"}
        )

    mo.md("**Forward rates between consecutive years:**")
    mo.ui.table(fwd_results)

    # Forward rate for a 5-year period starting in 5 years
    fwd_5y5y = forward_curve.forward_rate(5.0, 10.0)

    mo.md(f"""
    **5-year forward rate in 5 years:**
    - f(5,10) = {fwd_5y5y * 100:.4f}%
    """)

    # Instantaneous forward rates
    inst_fwd_results = []
    for t_inst in [1.0, 2.0, 5.0, 10.0]:
        inst_fwd = forward_curve.instantaneous_forward_rate(t_inst)
        inst_fwd_results.append(
            {"Time": f"{t_inst} years", "Instantaneous Forward": f"{inst_fwd * 100:.4f}%"}
        )

    mo.md("**Instantaneous forward rates:**")
    mo.ui.table(inst_fwd_results)
    return (
        forward_curve,
        fwd_5y5y,
        fwd_results,
        inst_fwd_results,
        t_inst,
    )


@app.cell
def _(curve, mo):
    mo.md("## 5. Bond Valuation using the Curve")

    # Price a 5-year bond with 5% annual coupons
    coupon_rate = 0.05
    face_value = 1000.0
    years = 5

    # Annual coupon payments
    cash_flows = [coupon_rate * face_value] * years
    cash_flows[-1] += face_value  # Add principal at maturity
    maturities_bond = [float(i + 1) for i in range(years)]

    bond_price = curve.present_value_many(cash_flows, maturities_bond)

    # Calculate yield to maturity (approximate)
    ytm_approx = (sum(cash_flows) / years) / bond_price

    mo.md(f"""
    **Pricing a 5-year 5% annual coupon bond (face value $1000):**
    - Cash flows: {cash_flows}
    - Maturities: {maturities_bond}
    - **Bond Price:** ${bond_price:.2f}
    - **Approximate YTM:** {ytm_approx * 100:.2f}%
    """)
    return (
        bond_price,
        cash_flows,
        coupon_rate,
        face_value,
        maturities_bond,
        years,
        ytm_approx,
    )


@app.cell
def _(curve, mo):
    mo.md("## 6. Present Value of Cash Flows")

    # Value a series of irregular cash flows
    cash_flows_irregular = [100.0, 150.0, 200.0, 250.0, 1000.0]
    maturities_irregular = [0.5, 1.5, 3.0, 5.0, 7.0]

    pv = curve.present_value_many(cash_flows_irregular, maturities_irregular)

    mo.md(f"""
    **Valuing irregular cash flows:**
    - Cash flows: {cash_flows_irregular}
    - Maturities: {maturities_irregular}
    - **Total PV:** ${pv:.2f}
    """)

    # Individual PV calculation for verification
    pv_breakdown = []
    total_pv = 0.0
    for cf, t in zip(cash_flows_irregular, maturities_irregular, strict=True):
        pv_single = curve.present_value(cf, t)
        total_pv += pv_single
        pv_breakdown.append(
            {"Cash Flow": f"${cf}", "Maturity": f"{t} years", "PV": f"${pv_single:.2f}"}
        )

    mo.md("**Individual present values:**")
    mo.ui.table(pv_breakdown)

    mo.md(f"**Sum:** ${total_pv:.2f} (should match ${pv:.2f})")
    return (
        cash_flows_irregular,
        maturities_irregular,
        pv,
        pv_breakdown,
        pv_single,
        total_pv,
    )


@app.cell
def _(ZeroCouponCurve, curve, forward_curve, mo):
    mo.md("## 7. Batch Operations for Multiple Calculations")

    # Calculate discount factors for many maturities at once
    test_maturities = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0, 10.0]

    mo.md("**Batch discount factor calculation:**")
    discount_factors_batch = ZeroCouponCurve.discount_factors_many(curve, test_maturities)

    df_batch_results = []
    for t_batch, df_batch in zip(test_maturities, discount_factors_batch, strict=True):
        df_batch_results.append({"Maturity": f"{t_batch} years", "DF": f"{df_batch:.6f}"})

    mo.ui.table(df_batch_results)

    mo.md("**Batch zero rate calculation:**")
    zero_rates_batch = ZeroCouponCurve.zero_rates_many(curve, test_maturities)

    zr_batch_results = []
    for t_zr, r_zr in zip(test_maturities, zero_rates_batch, strict=True):
        zr_batch_results.append({"Maturity": f"{t_zr} years", "Rate": f"{r_zr * 100:.4f}%"})

    mo.ui.table(zr_batch_results)

    mo.md("**Batch forward rate calculation (using ForwardCurve):**")
    start_maturities = [1.0, 2.0, 3.0, 5.0]
    end_maturities = [2.0, 3.0, 5.0, 10.0]

    forward_rates_batch = forward_curve.forward_rates_many(start_maturities, end_maturities)

    fwd_batch_results = []
    for t1_batch, t2_batch, f_batch in zip(
        start_maturities, end_maturities, forward_rates_batch, strict=True
    ):
        fwd_batch_results.append(
            {"Period": f"f({t1_batch:.1f},{t2_batch:.1f})", "Forward Rate": f"{f_batch * 100:.4f}%"}
        )

    mo.ui.table(fwd_batch_results)
    return (
        df_batch_results,
        discount_factors_batch,
        end_maturities,
        forward_rates_batch,
        fwd_batch_results,
        start_maturities,
        test_maturities,
        zero_rates_batch,
        zr_batch_results,
    )


@app.cell
def _(curve, mo):
    mo.md("## 8. Yield Curve Shape Analysis")

    # Analyze curve shape by comparing short, medium, and long rates
    rate_3m = curve.zero_rate(0.25)
    rate_2y = curve.zero_rate(2.0)
    rate_10y = curve.zero_rate(10.0)

    # Determine curve shape
    if rate_10y > rate_2y > rate_3m:
        shape = "Normal (upward sloping)"
    elif rate_10y < rate_2y < rate_3m:
        shape = "Inverted (downward sloping)"
    else:
        shape = "Humped or irregular"

    # Calculate curve steepness (10Y - 2Y spread)
    steepness = (rate_10y - rate_2y) * 100

    mo.md(f"""
    **Spot rates:**
    - 3-month: {rate_3m * 100:.4f}%
    - 2-year: {rate_2y * 100:.4f}%
    - 10-year: {rate_10y * 100:.4f}%

    **Yield curve shape:** {shape}

    **Curve steepness (10Y-2Y):** {steepness:.2f} basis points
    """)
    return rate_10y, rate_2y, rate_3m, shape, steepness


@app.cell
def _(mo):
    mo.md("""
    ## Summary

    - ✓ Zero-coupon curves built from securities (bootstrap)
    - ✓ Discount factors and zero rates calculated
    - ✓ Forward rates computed using ForwardCurve (separate from zero curve)
    - ✓ Bond valuation and cash flow PV calculation
    - ✓ Batch operations for high performance
    - ✓ Multiple interpolation methods (log-linear, linear, cubic)

    **Key Takeaways:**
    - Build curves from market zero-coupon bond prices
    - Calculate discount factors with automatic interpolation
    - Choose from 3 interpolation methods (log-linear is default)
    - Compute zero rates and forward rates
    - Value bonds and cash flow streams
    - Use batch operations for high-performance calculations
    - Analyze yield curve shape and dynamics
    """)
    return


if __name__ == "__main__":
    app.run()
