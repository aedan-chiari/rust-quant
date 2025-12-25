"""Example 7: Zero Coupon Curve Construction and Usage.

This example demonstrates:
- Creating a zero-coupon yield curve from market securities
- Calculating discount factors and zero rates
- Computing forward rates using ForwardCurve
- Valuing bonds and cash flows
- Using batch operations for performance
"""

import logging
import math

from rust_quant import ForwardCurve, Security, ZeroCouponCurve

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


def create_sample_securities() -> list[Security]:
    """Create sample zero-coupon bond securities for curve construction.

    Returns:
        List of Security objects representing market zero-coupon bonds

    """
    return [
        Security(maturity=0.25, price=98.75, face_value=100.0),  # 3-month
        Security(maturity=0.5, price=97.50, face_value=100.0),  # 6-month
        Security(maturity=1.0, price=95.00, face_value=100.0),  # 1-year
        Security(maturity=2.0, price=90.00, face_value=100.0),  # 2-year
        Security(maturity=5.0, price=78.35, face_value=100.0),  # 5-year
        Security(maturity=10.0, price=61.39, face_value=100.0),  # 10-year
    ]


def demonstrate_curve_construction() -> ZeroCouponCurve:
    """Demonstrate creating a zero-coupon curve from securities.

    Returns:
        Constructed ZeroCouponCurve object

    """
    print_subsection_header("1. Creating a Zero Coupon Curve from Securities")

    securities: list[Security] = create_sample_securities()
    curve = ZeroCouponCurve(securities)

    logger.info("Curve created with %s securities", curve.size())
    logger.info("Maturities: %s", curve.maturities())

    # Alternative: Create from vectors
    logger.info("\nAlternative: Create curve from vectors")
    maturities: list[float] = [1.0, 2.0, 3.0, 5.0, 7.0, 10.0]
    prices: list[float] = [95.0, 90.0, 85.5, 78.35, 70.89, 61.39]

    curve_from_vectors = ZeroCouponCurve.from_vectors(maturities, prices)
    logger.info("Curve created with %s securities from vectors", curve_from_vectors.size())

    return curve


def demonstrate_discount_factors(curve: ZeroCouponCurve) -> None:
    """Calculate and display discount factors at various maturities.

    Args:
        curve: ZeroCouponCurve object to use for calculations

    """
    print_subsection_header("2. Calculating Discount Factors")

    logger.info("\nDiscount factors for exact maturities:")
    for maturity in [0.5, 1.0, 2.0, 5.0, 10.0]:
        df: float = curve.discount_factor(maturity)
        logger.info("  DF(%s years) = %.6f", maturity, df)

    logger.info("\nDiscount factor with interpolation:")
    df_interpolated: float = curve.discount_factor(3.0)
    logger.info("  DF(3.0 years) = %.6f (interpolated)", df_interpolated)

    logger.info("\nDiscount factor with extrapolation:")
    df_extrapolated: float = curve.discount_factor(15.0)
    logger.info("  DF(15.0 years) = %.6f (extrapolated)", df_extrapolated)


def demonstrate_zero_rates(curve: ZeroCouponCurve) -> None:
    """Calculate and display zero rates (continuously compounded).

    Args:
        curve: ZeroCouponCurve object to use for calculations

    """
    print_subsection_header("3. Calculating Zero Rates (Continuously Compounded)")

    logger.info("\nZero rates for key maturities:")
    for maturity in [0.25, 0.5, 1.0, 2.0, 5.0, 10.0]:
        zero_rate: float = curve.zero_rate(maturity)
        logger.info("  r(%s years) = %.4f%%", maturity, zero_rate * 100)

    # Verify relationship: DF(T) = exp(-r(T) * T)
    logger.info("\nVerifying DF = exp(-r*T):")
    t: float = 5.0
    df: float = curve.discount_factor(t)
    r: float = curve.zero_rate(t)
    df_calculated: float = math.exp(-r * t)
    logger.info("  DF(%s) from curve:    %.6f", t, df)
    logger.info("  DF(%s) calculated:    %.6f", t, df_calculated)
    logger.info("  Difference:            %.10f", abs(df - df_calculated))


def demonstrate_forward_rates(curve: ZeroCouponCurve) -> ForwardCurve:
    """Calculate and display forward rates using ForwardCurve.

    Args:
        curve: ZeroCouponCurve object to use for forward rate calculations

    Returns:
        ForwardCurve object

    """
    print_subsection_header("4. Calculating Forward Rates with ForwardCurve")

    # Create a ForwardCurve from the ZeroCouponCurve
    forward_curve = ForwardCurve(curve)

    logger.info("\nForward rates between consecutive years:")
    for t1 in range(1, 5):
        t2: int = t1 + 1
        fwd_rate: float = forward_curve.forward_rate(float(t1), float(t2))
        logger.info("  f(%s,%s) = %.4f%%", t1, t2, fwd_rate * 100)

    # Forward rate for a 5-year period starting in 5 years
    fwd_5y5y: float = forward_curve.forward_rate(5.0, 10.0)
    logger.info("\n5-year forward rate in 5 years:")
    logger.info("  f(5,10) = %.4f%%", fwd_5y5y * 100)

    # Instantaneous forward rates
    logger.info("\nInstantaneous forward rates at key points:")
    for t in [1.0, 2.0, 5.0, 10.0]:
        inst_fwd: float = forward_curve.instantaneous_forward_rate(t)
        logger.info("  f(instant @ %s) = %.4f%%", t, inst_fwd * 100)

    # Forward rate term structure
    logger.info("\nForward rate term structure (1-year forwards):")
    times, rates = forward_curve.term_structure(0.0, 10.0, 1.0)
    for t, r in zip(times[:5], rates[:5], strict=True):  # Show first 5
        logger.info("  %.0fy1y forward: %.4f%%", t, r * 100)

    return forward_curve


def demonstrate_bond_valuation(curve: ZeroCouponCurve) -> float:
    """Value a coupon bond using the yield curve.

    Args:
        curve: ZeroCouponCurve object to use for bond valuation

    Returns:
        Bond price

    """
    print_subsection_header("5. Bond Valuation using the Curve")

    # Price a 5-year bond with 5% annual coupons
    logger.info("\nPricing a 5-year 5% annual coupon bond (face value $1000):")
    coupon_rate: float = 0.05
    face_value: float = 1000.0
    years: int = 5

    # Annual coupon payments
    cash_flows: list[float] = [coupon_rate * face_value] * years
    cash_flows[-1] += face_value  # Add principal at maturity
    maturities_bond: list[float] = [float(i + 1) for i in range(years)]

    bond_price: float = curve.present_value_many(cash_flows, maturities_bond)

    logger.info("  Cash flows: %s", cash_flows)
    logger.info("  Maturities: %s", maturities_bond)
    logger.info("  Bond Price: $%.2f", bond_price)

    # Calculate yield to maturity (approximate)
    ytm_approx: float = (sum(cash_flows) / years) / bond_price
    logger.info("  Approximate YTM: %.2f%%", ytm_approx * 100)

    return bond_price


def demonstrate_present_value(curve: ZeroCouponCurve) -> None:
    """Calculate present value of irregular cash flows.

    Args:
        curve: ZeroCouponCurve object to use for PV calculations

    """
    print_subsection_header("6. Present Value of Cash Flows")

    # Value a series of irregular cash flows
    logger.info("\nValuing irregular cash flows:")
    cash_flows_irregular: list[float] = [100.0, 150.0, 200.0, 250.0, 1000.0]
    maturities_irregular: list[float] = [0.5, 1.5, 3.0, 5.0, 7.0]

    pv: float = curve.present_value_many(cash_flows_irregular, maturities_irregular)

    logger.info("  Cash flows: %s", cash_flows_irregular)
    logger.info("  Maturities: %s", maturities_irregular)
    logger.info("  Total PV:   $%.2f", pv)

    # Individual PV calculation for verification
    logger.info("\n  Individual present values:")
    total_pv: float = 0.0
    for cf, t in zip(cash_flows_irregular, maturities_irregular, strict=True):
        pv_single: float = curve.present_value(cf, t)
        total_pv += pv_single
        logger.info("    $%s at %s years -> PV = $%s", cf, t, pv_single)
    logger.info("  Sum: $%.2f (should match $%.2f)", total_pv, pv)


def demonstrate_batch_operations(curve: ZeroCouponCurve, forward_curve: ForwardCurve) -> None:
    """Demonstrate batch operations for high-performance calculations.

    Args:
        curve: ZeroCouponCurve object
        forward_curve: ForwardCurve object

    """
    print_subsection_header("7. Batch Operations for Multiple Calculations")

    # Calculate discount factors for many maturities at once
    test_maturities: list[float] = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0, 10.0]

    logger.info("\nBatch discount factor calculation:")
    discount_factors_batch: list[float] = ZeroCouponCurve.discount_factors_many(
        curve,
        test_maturities,
    )

    for t, df in zip(test_maturities, discount_factors_batch, strict=True):
        logger.info("  t=%s years: DF = %.6f", t, df)

    logger.info("\nBatch zero rate calculation:")
    zero_rates_batch: list[float] = ZeroCouponCurve.zero_rates_many(curve, test_maturities)

    for t, r in zip(test_maturities, zero_rates_batch, strict=True):
        logger.info("  t=%s years: r = %.4f%%", t, r * 100)

    logger.info("\nBatch forward rate calculation (using ForwardCurve):")
    start_maturities: list[float] = [1.0, 2.0, 3.0, 5.0]
    end_maturities: list[float] = [2.0, 3.0, 5.0, 10.0]

    forward_rates_batch: list[float] = forward_curve.forward_rates_many(
        start_maturities,
        end_maturities,
    )

    for t1, t2, f in zip(start_maturities, end_maturities, forward_rates_batch, strict=True):
        logger.info("  f(%.1f,%.1f) = %.4f%%", t1, t2, f * 100)


def analyze_curve_shape(curve: ZeroCouponCurve) -> None:
    """Analyze the shape of the yield curve.

    Args:
        curve: ZeroCouponCurve object to analyze

    """
    print_subsection_header("8. Yield Curve Shape Analysis")

    # Analyze curve shape by comparing short, medium, and long rates
    rate_3m: float = curve.zero_rate(0.25)
    rate_2y: float = curve.zero_rate(2.0)
    rate_10y: float = curve.zero_rate(10.0)

    logger.info("\nSpot rates:")
    logger.info("  3-month:  %.4f%%", rate_3m * 100)
    logger.info("  2-year:   %.4f%%", rate_2y * 100)
    logger.info("  10-year:  %.4f%%", rate_10y * 100)

    # Determine curve shape
    if rate_10y > rate_2y > rate_3m:
        shape: str = "Normal (upward sloping)"
    elif rate_10y < rate_2y < rate_3m:
        shape = "Inverted (downward sloping)"
    else:
        shape = "Humped or irregular"

    logger.info("\nYield curve shape: %s", shape)

    # Calculate curve steepness (10Y - 2Y spread)
    steepness: float = (rate_10y - rate_2y) * 100
    logger.info("Curve steepness (10Y-2Y): %.2f basis points", steepness)


def demonstrate_dynamic_updates(curve: ZeroCouponCurve) -> None:
    """Demonstrate adding new securities to an existing curve.

    Args:
        curve: ZeroCouponCurve object to update

    """
    print_subsection_header("9. Adding New Securities to the Curve")

    logger.info("Current curve size: %s securities", curve.size())

    # Add a new 15-year security
    new_security = Security(maturity=15.0, price=55.0, face_value=100.0)
    curve.add_security(new_security)

    logger.info("After adding 15-year security: %s securities", curve.size())
    logger.info("New maturities: %s", curve.maturities())

    df_15y: float = curve.discount_factor(15.0)
    rate_15y: float = curve.zero_rate(15.0)
    logger.info("\n15-year discount factor: %.6f", df_15y)
    logger.info("15-year zero rate: %.4f%%", rate_15y * 100)


def calculate_bond_duration(
    bond_price: float,
    cash_flows: list[float],
    maturities: list[float],
    curve: ZeroCouponCurve,
) -> tuple[float, float]:
    """Calculate Macaulay and modified duration for a bond.

    Args:
        bond_price: Price of the bond
        cash_flows: List of cash flows
        maturities: List of cash flow maturities
        curve: ZeroCouponCurve object for discounting

    Returns:
        Tuple of (macaulay_duration, modified_duration)

    """
    weighted_time: float = 0.0
    for cf, t in zip(cash_flows, maturities, strict=True):
        pv_cf: float = curve.present_value(cf, t)
        weighted_time += t * pv_cf

    duration: float = weighted_time / bond_price

    # Modified duration (approximate)
    dy: float = 0.0001
    bond_price_up: float = 0.0
    for cf, t in zip(cash_flows, maturities, strict=True):
        df: float = math.exp(-(curve.zero_rate(t) + dy) * t)
        bond_price_up += cf * df

    modified_duration: float = -(bond_price_up - bond_price) / (bond_price * dy)

    return duration, modified_duration


def demonstrate_duration_calculation(curve: ZeroCouponCurve) -> None:
    """Demonstrate Macaulay duration calculation for a bond.

    Args:
        curve: ZeroCouponCurve object

    """
    print_subsection_header("10. Calculating Macaulay Duration")

    # Calculate duration for the 5-year 5% coupon bond priced earlier
    logger.info("\nMacaulay Duration for 5-year 5% coupon bond:")

    coupon_rate: float = 0.05
    face_value: float = 1000.0
    years: int = 5

    cash_flows: list[float] = [coupon_rate * face_value] * years
    cash_flows[-1] += face_value
    maturities_bond: list[float] = [float(i + 1) for i in range(years)]

    bond_price: float = curve.present_value_many(cash_flows, maturities_bond)
    duration, modified_duration = calculate_bond_duration(
        bond_price,
        cash_flows,
        maturities_bond,
        curve,
    )

    logger.info("  Bond Price: $%.2f", bond_price)
    logger.info("  Duration:   %.4f years", duration)
    logger.info("  Modified Duration: %.4f", modified_duration)


def compare_interpolation_methods() -> None:
    """Compare different interpolation methods for yield curves."""
    print_subsection_header("11. Comparing Interpolation Methods")

    # Create simple curve for demonstration
    securities_interp: list[Security] = [
        Security(maturity=1.0, price=95.0),
        Security(maturity=2.0, price=90.0),
        Security(maturity=3.0, price=85.0),
    ]

    logger.info("\nCreating curves with different interpolation methods:")

    # Log-linear (default, industry standard)
    curve_log_linear = ZeroCouponCurve(securities_interp)  # Default
    logger.info("  Default: %s", curve_log_linear.get_interpolation_method())

    # Linear interpolation
    curve_linear = ZeroCouponCurve(securities_interp, interpolation="linear")
    logger.info("  Linear: %s", curve_linear.get_interpolation_method())

    # Cubic spline
    curve_cubic = ZeroCouponCurve(securities_interp, interpolation="cubic")
    logger.info("  Cubic: %s", curve_cubic.get_interpolation_method())

    # Compare interpolated values at 1.5 years
    t: float = 1.5
    df_log_linear: float = curve_log_linear.discount_factor(t)
    df_linear: float = curve_linear.discount_factor(t)
    df_cubic: float = curve_cubic.discount_factor(t)

    logger.info("\nDiscount factors at %s years:", t)
    logger.info("  Log-linear (piecewise constant forwards): %.6f", df_log_linear)
    logger.info("  Linear (simple):                          %.6f", df_linear)
    logger.info("  Cubic (smooth):                           %.6f", df_cubic)

    # Show forward rate behavior
    fwd_curve_log = ForwardCurve(curve_log_linear)
    fwd_1_15_log: float = fwd_curve_log.forward_rate(1.0, 1.5)
    fwd_15_2_log: float = fwd_curve_log.forward_rate(1.5, 2.0)

    logger.info("\nForward rates with log-linear (should be constant in interval):")
    logger.info("  f(1.0, 1.5) = %.4f%%", fwd_1_15_log * 100)
    logger.info("  f(1.5, 2.0) = %.4f%%", fwd_15_2_log * 100)
    logger.info("  Difference:  %.2f basis points", abs(fwd_1_15_log - fwd_15_2_log) * 10000)

    logger.info("\nWhich method to use?")
    logger.info("  • Log-linear: Industry standard, piecewise constant forwards")
    logger.info("  • Linear: Simple and fast, good for general purposes")
    logger.info("  • Cubic: Smooth curves, use when smoothness is critical")


def print_summary() -> None:
    """Print a summary of the zero-coupon curve examples."""
    logger.info("\n%s", "=" * 70)
    logger.info("Summary:")
    logger.info("=" * 70)
    logger.info("✓ Zero-coupon curves built from securities (bootstrap)")
    logger.info("✓ Discount factors and zero rates calculated")
    logger.info("✓ Forward rates computed using ForwardCurve (separate from zero curve)")
    logger.info("✓ Bond valuation and cash flow PV calculation")
    logger.info("✓ Batch operations for high performance")
    logger.info("✓ Multiple interpolation methods (log-linear, linear, cubic)")
    logger.info("=" * 70)

    logger.info("\n%s", "=" * 70)
    logger.info("Summary:")
    logger.info("  • Build curves from market zero-coupon bond prices")
    logger.info("  • Calculate discount factors with automatic interpolation")
    logger.info("  • Choose from 3 interpolation methods (log-linear is default)")
    logger.info("  • Compute zero rates and forward rates")
    logger.info("  • Value bonds and cash flow streams")
    logger.info("  • Use batch operations for high-performance calculations")
    logger.info("  • Analyze yield curve shape and dynamics")
    logger.info("=" * 70)


def main() -> None:
    """Run all zero-coupon curve examples."""
    print_section_header("Example 7: Zero Coupon Curve Construction and Usage")

    curve = demonstrate_curve_construction()
    demonstrate_discount_factors(curve)
    demonstrate_zero_rates(curve)
    forward_curve = demonstrate_forward_rates(curve)
    demonstrate_bond_valuation(curve)
    demonstrate_present_value(curve)
    demonstrate_batch_operations(curve, forward_curve)
    analyze_curve_shape(curve)
    demonstrate_dynamic_updates(curve)
    demonstrate_duration_calculation(curve)
    compare_interpolation_methods()
    print_summary()


if __name__ == "__main__":
    main()
