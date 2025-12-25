"""Test suite for Zero Coupon Curve calculations.

These tests verify the curve construction, interpolation, and discount factor calculations
from zero-coupon bond securities.
"""

import math

import pytest
from rust_quant import ForwardCurve, Security, ZeroCouponCurve


class TestSecurityCreation:
    """Test Security object creation and properties."""

    def test_security_basic(self) -> None:
        """Test basic security creation."""
        sec = Security(maturity=1.0, price=95.0, face_value=100.0)
        assert sec.maturity == 1.0
        assert sec.price == 95.0
        assert sec.face_value == 100.0

    def test_security_default_face_value(self) -> None:
        """Test security creation with default face value."""
        sec = Security(maturity=2.0, price=90.0)
        assert sec.maturity == 2.0
        assert sec.price == 90.0
        assert sec.face_value == 100.0


class TestCurveConstruction:
    """Test zero coupon curve construction methods."""

    def test_curve_from_zero_coupon_securities(self) -> None:
        """Test curve construction from zero-coupon security objects."""
        securities = [
            Security(maturity=0.5, price=97.5, face_value=100.0),
            Security(maturity=1.0, price=95.0, face_value=100.0),
            Security(maturity=2.0, price=90.0, face_value=100.0),
        ]

        curve = ZeroCouponCurve(securities)
        assert curve.size() == 3
        assert len(curve.maturities()) == 3

    def test_curve_from_coupon_bearing_bonds(self) -> None:
        """Test curve construction from coupon-bearing bonds."""
        # Create mix of zero-coupon and coupon-bearing bonds
        securities = [
            Security(maturity=0.5, price=97.5, face_value=100.0),  # Zero-coupon
            Security(
                maturity=1.0,
                price=97.0,
                face_value=100.0,
                coupon_rate=0.03,
                frequency=2,
            ),  # 3% semi-annual
            Security(
                maturity=2.0,
                price=98.0,
                face_value=100.0,
                coupon_rate=0.05,
                frequency=2,
            ),  # 5% semi-annual
        ]

        curve = ZeroCouponCurve(securities)
        assert curve.size() == 3

        # Verify discount factors are calculated
        df_05 = curve.discount_factor(0.5)
        df_1 = curve.discount_factor(1.0)
        df_2 = curve.discount_factor(2.0)

        # All discount factors should be positive and less than 1
        assert 0 < df_05 < 1
        assert 0 < df_1 < 1
        assert 0 < df_2 < 1

        # Discount factors should decrease with maturity
        assert df_05 > df_1 > df_2

    def test_curve_from_vectors(self) -> None:
        """Test curve construction from vectors."""
        maturities = [1.0, 2.0, 3.0]
        prices = [95.0, 90.0, 85.0]

        curve = ZeroCouponCurve.from_vectors(maturities, prices)
        assert curve.size() == 3

    def test_curve_from_vectors_with_face_values(self) -> None:
        """Test curve construction with custom face values."""
        maturities = [1.0, 2.0]
        prices = [95.0, 180.0]
        face_values = [100.0, 200.0]

        curve = ZeroCouponCurve.from_vectors(maturities, prices, face_values)

        # Both should give same discount factor of 0.9
        df1 = curve.discount_factor(1.0)
        df2 = curve.discount_factor(2.0)

        assert abs(df1 - 0.95) < 1e-10
        assert abs(df2 - 0.90) < 1e-10

    def test_curve_sorted_maturities(self) -> None:
        """Test that curve sorts securities by maturity."""
        securities = [
            Security(maturity=2.0, price=90.0),
            Security(maturity=0.5, price=97.5),
            Security(maturity=1.0, price=95.0),
        ]

        curve = ZeroCouponCurve(securities)
        maturities = curve.maturities()

        # Should be sorted
        assert maturities == [0.5, 1.0, 2.0]


class TestDiscountFactors:
    """Test discount factor calculations."""

    def test_discount_factor_exact_match(self) -> None:
        """Test discount factor for exact maturity match."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
        ]

        curve = ZeroCouponCurve(securities)

        # Exact matches
        df1 = curve.discount_factor(1.0)
        df2 = curve.discount_factor(2.0)

        assert abs(df1 - 0.95) < 1e-10
        assert abs(df2 - 0.90) < 1e-10

    def test_discount_factor_interpolation(self) -> None:
        """Test linear interpolation between maturities."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
        ]

        curve = ZeroCouponCurve(securities)

        # Interpolate at midpoint
        df_mid = curve.discount_factor(1.5)

        # Should be between 0.90 and 0.95
        assert 0.90 < df_mid < 0.95

    def test_discount_factor_zero_maturity(self) -> None:
        """Test that DF(0) = 1.0."""
        securities = [Security(maturity=1.0, price=95.0)]
        curve = ZeroCouponCurve(securities)

        df = curve.discount_factor(0.0)
        assert df == 1.0

    def test_discount_factor_extrapolation(self) -> None:
        """Test extrapolation beyond curve."""
        securities = [Security(maturity=1.0, price=95.0)]
        curve = ZeroCouponCurve(securities)

        # Extrapolate to 2 years using flat rate
        df2 = curve.discount_factor(2.0)

        # Should use flat extrapolation: DF(2) = DF(1)^2
        rate1 = curve.zero_rate(1.0)
        expected_df2 = math.exp(-rate1 * 2.0)

        assert abs(df2 - expected_df2) < 1e-10

    def test_discount_factors_batch(self) -> None:
        """Test batch discount factor calculation."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
        ]

        curve = ZeroCouponCurve(securities)
        dfs = curve.discount_factors()

        assert len(dfs) == 2
        assert abs(dfs[0] - 0.95) < 1e-10
        assert abs(dfs[1] - 0.90) < 1e-10


class TestZeroRates:
    """Test zero rate calculations."""

    def test_zero_rate_calculation(self) -> None:
        """Test zero rate calculation from discount factor."""
        securities = [Security(maturity=1.0, price=95.0)]
        curve = ZeroCouponCurve(securities)

        rate = curve.zero_rate(1.0)

        # r = -ln(0.95) / 1.0 ≈ 0.05129
        expected_rate = -math.log(0.95)
        assert abs(rate - expected_rate) < 1e-10

    def test_zero_rate_zero_maturity(self) -> None:
        """Test that zero rate at maturity 0 is 0."""
        securities = [Security(maturity=1.0, price=95.0)]
        curve = ZeroCouponCurve(securities)

        rate = curve.zero_rate(0.0)
        assert rate == 0.0

    def test_zero_rates_batch(self) -> None:
        """Test batch zero rate calculation."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
        ]

        curve = ZeroCouponCurve(securities)
        rates = curve.zero_rates()

        assert len(rates) == 2
        assert rates[0] > 0.0
        assert rates[1] > 0.0

        # Zero rates should match individually calculated rates
        r1 = -math.log(0.95) / 1.0
        r2 = -math.log(0.90) / 2.0

        assert abs(rates[0] - r1) < 1e-10
        assert abs(rates[1] - r2) < 1e-10


class TestForwardRates:
    """Test forward rate calculations using ForwardCurve."""

    def test_forward_rate_calculation(self) -> None:
        """Test forward rate between two maturities."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
        ]

        curve = ZeroCouponCurve(securities)
        fwd_curve = ForwardCurve(curve)

        # Forward rate from year 1 to year 2
        fwd = fwd_curve.forward_rate(1.0, 2.0)

        # Should be positive
        assert fwd > 0.0

        # Verify: f(1,2) = ln(DF(1)/DF(2))
        df1 = curve.discount_factor(1.0)
        df2 = curve.discount_factor(2.0)
        expected_fwd = math.log(df1 / df2)

        assert abs(fwd - expected_fwd) < 1e-10

    def test_forward_rate_consistency(self) -> None:
        """Test that forward rates are consistent with zero rates."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
        ]

        curve = ZeroCouponCurve(securities)
        fwd_curve = ForwardCurve(curve)

        r1 = curve.zero_rate(1.0)
        r2 = curve.zero_rate(2.0)
        f_12 = fwd_curve.forward_rate(1.0, 2.0)

        # Relationship: r2 * 2 = r1 * 1 + f_12 * 1
        # So: f_12 = r2 * 2 - r1
        expected_fwd = r2 * 2.0 - r1 * 1.0

        assert abs(f_12 - expected_fwd) < 1e-10

    def test_forward_rates_many(self) -> None:
        """Test batch forward rate calculation."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
            Security(maturity=3.0, price=85.0),
        ]

        curve = ZeroCouponCurve(securities)
        fwd_curve = ForwardCurve(curve)

        start_times = [1.0, 2.0]
        end_times = [2.0, 3.0]

        fwds = fwd_curve.forward_rates_many(start_times, end_times)

        assert len(fwds) == 2
        assert fwds[0] > 0.0
        assert fwds[1] > 0.0

    def test_instantaneous_forward_rate(self) -> None:
        """Test instantaneous forward rate calculation."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
            Security(maturity=5.0, price=78.0),
        ]

        curve = ZeroCouponCurve(securities)
        fwd_curve = ForwardCurve(curve)

        # Calculate instantaneous forward rate at 2 years
        inst_fwd = fwd_curve.instantaneous_forward_rate(2.0)

        # Should be positive for normal curve
        assert inst_fwd > 0.0

    def test_forward_discount_factor(self) -> None:
        """Test forward discount factor calculation."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
        ]

        curve = ZeroCouponCurve(securities)
        fwd_curve = ForwardCurve(curve)

        # Forward discount factor from year 1 to year 2
        fdf = fwd_curve.forward_discount_factor(1.0, 2.0)

        # Should equal DF(2) / DF(1)
        df1 = curve.discount_factor(1.0)
        df2 = curve.discount_factor(2.0)
        expected_fdf = df2 / df1

        assert abs(fdf - expected_fdf) < 1e-10

    def test_forward_bond_price(self) -> None:
        """Test forward bond price calculation."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
        ]

        curve = ZeroCouponCurve(securities)
        fwd_curve = ForwardCurve(curve)

        # Forward price at year 1 for bond maturing at year 2
        fwd_price = fwd_curve.forward_bond_price(1.0, 2.0, face_value=100.0)

        # Should equal face_value * FDF(1, 2)
        fdf = fwd_curve.forward_discount_factor(1.0, 2.0)
        expected_price = 100.0 * fdf

        assert abs(fwd_price - expected_price) < 1e-10

    def test_term_structure(self) -> None:
        """Test forward rate term structure generation."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
            Security(maturity=5.0, price=78.0),
        ]

        curve = ZeroCouponCurve(securities)
        fwd_curve = ForwardCurve(curve)

        # Generate 1-year forward rates from 0 to 5 years
        times, rates = fwd_curve.term_structure(0.0, 5.0, 1.0)

        assert len(times) == 5
        assert len(rates) == 5

        # All rates should be positive
        for rate in rates:
            assert rate > 0.0

        # Times should be [0, 1, 2, 3, 4]
        assert times == [0.0, 1.0, 2.0, 3.0, 4.0]

    def test_get_base_curve(self) -> None:
        """Test that we can retrieve the base curve."""
        securities = [Security(maturity=1.0, price=95.0)]
        curve = ZeroCouponCurve(securities)
        fwd_curve = ForwardCurve(curve)

        base = fwd_curve.get_base_curve()
        assert base.size() == curve.size()
        assert base.maturities() == curve.maturities()


class TestPresentValue:
    """Test present value calculations."""

    def test_present_value_single(self) -> None:
        """Test present value of a single cash flow."""
        securities = [Security(maturity=1.0, price=95.0)]
        curve = ZeroCouponCurve(securities)

        pv = curve.present_value(100.0, 1.0)

        # PV of 100 at 1 year with DF=0.95 should be 95
        assert abs(pv - 95.0) < 1e-10

    def test_present_value_multiple(self) -> None:
        """Test present value of multiple cash flows."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
        ]

        curve = ZeroCouponCurve(securities)

        cash_flows = [100.0, 100.0]
        maturities = [1.0, 2.0]

        pv = curve.present_value_many(cash_flows, maturities)

        # Should be 100*0.95 + 100*0.90 = 185
        assert abs(pv - 185.0) < 1e-10

    def test_present_value_bond_pricing(self) -> None:
        """Test pricing a coupon bond using PV calculation."""
        # Build curve from zero-coupon bonds
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
        ]

        curve = ZeroCouponCurve(securities)

        # Price a 2-year 5% annual coupon bond with face value 100
        # Cash flows: 5 at year 1, 105 at year 2
        cash_flows = [5.0, 105.0]
        maturities = [1.0, 2.0]

        bond_price = curve.present_value_many(cash_flows, maturities)

        # Should be 5*0.95 + 105*0.90 = 4.75 + 94.5 = 99.25
        expected_price = 5.0 * 0.95 + 105.0 * 0.90
        assert abs(bond_price - expected_price) < 1e-10


class TestCurveModification:
    """Test adding securities to existing curves."""

    def test_add_security(self) -> None:
        """Test adding a new security to the curve."""
        securities = [Security(maturity=1.0, price=95.0)]
        curve = ZeroCouponCurve(securities)

        assert curve.size() == 1

        curve.add_security(Security(maturity=2.0, price=90.0))

        assert curve.size() == 2

        # New security should be accessible
        df2 = curve.discount_factor(2.0)
        assert abs(df2 - 0.90) < 1e-10


class TestBatchOperations:
    """Test batch/vectorized operations for performance."""

    def test_discount_factors_many(self) -> None:
        """Test batch discount factor calculation."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
            Security(maturity=3.0, price=85.0),
        ]

        curve = ZeroCouponCurve(securities)
        maturities = [1.0, 1.5, 2.0, 2.5, 3.0]

        dfs = ZeroCouponCurve.discount_factors_many(curve, maturities)

        assert len(dfs) == 5

        # Verify against individual calculations
        for i, t in enumerate(maturities):
            df_individual = curve.discount_factor(t)
            assert abs(dfs[i] - df_individual) < 1e-10

    def test_zero_rates_many(self) -> None:
        """Test batch zero rate calculation."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
        ]

        curve = ZeroCouponCurve(securities)
        maturities = [1.0, 1.5, 2.0]

        rates = ZeroCouponCurve.zero_rates_many(curve, maturities)

        assert len(rates) == 3

        # Verify against individual calculations
        for i, t in enumerate(maturities):
            rate_individual = curve.zero_rate(t)
            assert abs(rates[i] - rate_individual) < 1e-10

    def test_large_batch_consistency(self) -> None:
        """Test consistency with large batches (parallel processing)."""
        # Create a curve with many points
        n_securities = 20
        maturities_sec = [i * 0.5 for i in range(1, n_securities + 1)]
        prices_sec = [100.0 * (0.95**t) for t in maturities_sec]

        curve = ZeroCouponCurve.from_vectors(maturities_sec, prices_sec)

        # Test with 200+ points to trigger parallel processing
        test_maturities = [i * 0.1 for i in range(1, 201)]

        dfs = ZeroCouponCurve.discount_factors_many(curve, test_maturities)

        # Spot check some values
        for i in [0, 50, 100, 150, 199]:
            df_individual = curve.discount_factor(test_maturities[i])
            assert abs(dfs[i] - df_individual) < 1e-10


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_negative_maturity_error(self) -> None:
        """Test that negative maturity raises error."""
        securities = [Security(maturity=1.0, price=95.0)]
        curve = ZeroCouponCurve(securities)

        with pytest.raises(Exception, match="non-negative"):
            curve.discount_factor(-1.0)

    def test_invalid_forward_rate_error(self) -> None:
        """Test that invalid forward rate raises error."""
        securities = [Security(maturity=1.0, price=95.0)]
        curve = ZeroCouponCurve(securities)
        fwd_curve = ForwardCurve(curve)

        # t2 must be > t1
        with pytest.raises(Exception, match="greater than"):
            fwd_curve.forward_rate(2.0, 1.0)

    def test_mismatched_vector_lengths(self) -> None:
        """Test error when vector lengths don't match."""
        with pytest.raises(Exception, match="same length"):
            ZeroCouponCurve.from_vectors([1.0, 2.0], [95.0])

    def test_empty_curve(self) -> None:
        """Test curve with no securities."""
        curve = ZeroCouponCurve([])

        assert curve.size() == 0

        # Should handle gracefully or raise error
        with pytest.raises((ValueError, RuntimeError)):
            curve.discount_factor(1.0)


class TestCouponBondBootstrapping:
    """Test bootstrapping from coupon-bearing bonds."""

    def test_simple_coupon_bond_bootstrap(self) -> None:
        """Test bootstrapping with a single coupon bond."""
        # Start with a zero-coupon bond to anchor the curve
        securities = [
            Security(maturity=1.0, price=95.0, face_value=100.0),  # Zero-coupon
            # Add a 2-year bond with 5% annual coupons
            Security(maturity=2.0, price=98.0, face_value=100.0, coupon_rate=0.05, frequency=1),
        ]

        curve = ZeroCouponCurve(securities)

        # Calculate what the 2-year discount factor should be
        # Price = Coupon * DF(1) + (Coupon + Face) * DF(2)
        # 98 = 5 * 0.95 + 105 * DF(2)
        # DF(2) = (98 - 4.75) / 105 = 0.8881
        df2 = curve.discount_factor(2.0)

        expected_df2 = (98.0 - 5.0 * 0.95) / 105.0
        assert abs(df2 - expected_df2) < 0.01

    def test_semi_annual_coupon_bond(self) -> None:
        """Test bootstrapping with semi-annual coupon bonds."""
        securities = [
            Security(maturity=0.5, price=97.5, face_value=100.0),  # 6-month zero
            # 1-year bond with 4% coupon (semi-annual)
            Security(maturity=1.0, price=99.0, face_value=100.0, coupon_rate=0.04, frequency=2),
        ]

        curve = ZeroCouponCurve(securities)

        # Check that we can get discount factors for all payment dates
        df_05 = curve.discount_factor(0.5)
        df_1 = curve.discount_factor(1.0)

        assert 0.9 < df_05 < 1.0
        assert 0.8 < df_1 < 1.0
        assert df_05 > df_1  # Monotonically decreasing

    def test_mixed_bond_portfolio(self) -> None:
        """Test bootstrapping with mix of zero-coupon and coupon bonds."""
        securities = [
            Security(maturity=0.5, price=97.5, face_value=100.0),  # Zero-coupon
            Security(
                maturity=1.0,
                price=96.0,
                face_value=100.0,
                coupon_rate=0.02,
                frequency=2,
            ),  # 2% semi
            Security(maturity=1.5, price=95.0, face_value=100.0),  # Zero-coupon
            Security(
                maturity=2.0,
                price=97.0,
                face_value=100.0,
                coupon_rate=0.04,
                frequency=2,
            ),  # 4% semi
            Security(
                maturity=3.0,
                price=98.5,
                face_value=100.0,
                coupon_rate=0.06,
                frequency=1,
            ),  # 6% annual
        ]

        curve = ZeroCouponCurve(securities)

        assert curve.size() == 5

        # Verify we can calculate rates across the whole curve
        rates = curve.zero_rates()
        assert len(rates) == 5

        # All rates should be positive
        for rate in rates:
            assert rate > 0

    def test_quarterly_coupon_bond(self) -> None:
        """Test bootstrapping with quarterly coupon payments."""
        securities = [
            Security(maturity=0.25, price=98.75, face_value=100.0),  # 3-month zero
            # 1-year bond with 4% coupon (quarterly)
            Security(maturity=1.0, price=99.5, face_value=100.0, coupon_rate=0.04, frequency=4),
        ]

        curve = ZeroCouponCurve(securities)

        # Should be able to get discount factors for quarterly dates
        df_025 = curve.discount_factor(0.25)
        df_050 = curve.discount_factor(0.50)
        df_075 = curve.discount_factor(0.75)
        df_100 = curve.discount_factor(1.00)

        # Check monotonicity
        assert df_025 > df_050 > df_075 > df_100


class TestRealWorldScenarios:
    """Test realistic financial scenarios."""

    def test_us_treasury_curve(self) -> None:
        """Test with realistic US Treasury yields."""
        # Approximate US Treasury prices (normalized to $100 face)
        # Based on historical yields: 1Y≈5%, 2Y≈5.2%, 5Y≈5.5%, 10Y≈6%
        securities = [
            Security(maturity=1.0, price=95.24),  # ~5% yield
            Security(maturity=2.0, price=90.48),  # ~5.2% yield
            Security(maturity=5.0, price=76.51),  # ~5.5% yield
            Security(maturity=10.0, price=55.37),  # ~6% yield
        ]

        curve = ZeroCouponCurve(securities)

        # Verify yield curve is upward sloping
        r1 = curve.zero_rate(1.0)
        r2 = curve.zero_rate(2.0)
        r5 = curve.zero_rate(5.0)
        r10 = curve.zero_rate(10.0)

        assert r1 < r2 < r5 < r10, "Yield curve should be upward sloping"

    def test_realistic_treasury_curve_with_coupons(self) -> None:
        """Test with realistic Treasury curve including coupon bonds."""
        # Realistic US Treasury securities (prices approximate)
        securities = [
            # Bills (zero-coupon)
            Security(maturity=0.25, price=98.75, face_value=100.0),  # 3-month bill
            Security(maturity=0.5, price=97.50, face_value=100.0),  # 6-month bill
            # Notes (coupon-bearing, semi-annual)
            Security(
                maturity=2.0,
                price=98.0,
                face_value=100.0,
                coupon_rate=0.045,
                frequency=2,
            ),  # 2-year note
            Security(
                maturity=5.0,
                price=95.0,
                face_value=100.0,
                coupon_rate=0.048,
                frequency=2,
            ),  # 5-year note
            Security(
                maturity=10.0,
                price=92.0,
                face_value=100.0,
                coupon_rate=0.050,
                frequency=2,
            ),  # 10-year note
        ]

        curve = ZeroCouponCurve(securities)

        # Verify we get a reasonable yield curve
        rates = {
            0.25: curve.zero_rate(0.25),
            0.5: curve.zero_rate(0.5),
            2.0: curve.zero_rate(2.0),
            5.0: curve.zero_rate(5.0),
            10.0: curve.zero_rate(10.0),
        }

        # All rates should be positive and reasonable (between 0% and 20%)
        for maturity, rate in rates.items():
            assert 0 < rate < 0.20, f"Rate at {maturity}Y seems unrealistic: {rate * 100:.2f}%"

        # Verify generally upward sloping (normal curve)
        assert rates[0.25] < rates[10.0], "Long rates should exceed short rates"

    def test_inverted_yield_curve(self) -> None:
        """Test with inverted yield curve scenario."""
        # Inverted curve: short rates > long rates
        securities = [
            Security(maturity=1.0, price=95.0),  # ~5.13% yield
            Security(maturity=2.0, price=91.0),  # ~4.85% yield
            Security(maturity=5.0, price=80.0),  # ~4.47% yield
        ]

        curve = ZeroCouponCurve(securities)

        # Verify rates decrease (inverted)
        r1 = curve.zero_rate(1.0)
        _r2 = curve.zero_rate(2.0)
        r5 = curve.zero_rate(5.0)

        # Short-term rates should be higher
        assert r1 > r5, "Inverted curve: short rates > long rates"

    def test_corporate_bond_valuation(self) -> None:
        """Test valuing a corporate bond using the curve."""
        # Build risk-free curve
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
            Security(maturity=3.0, price=85.0),
        ]

        curve = ZeroCouponCurve(securities)

        # Price a 3-year corporate bond with 6% annual coupons
        # (Simplified - real pricing would add credit spread)
        cash_flows = [6.0, 6.0, 106.0]
        maturities = [1.0, 2.0, 3.0]

        bond_value = curve.present_value_many(cash_flows, maturities)

        # Should be positive and reasonable
        assert 80.0 < bond_value < 120.0

        # With these discount rates, should be close to par + premium
        expected = 6.0 * 0.95 + 6.0 * 0.90 + 106.0 * 0.85
        assert abs(bond_value - expected) < 1e-10


class TestInterpolationAccuracy:
    """Test interpolation accuracy and methods."""

    def test_linear_interpolation(self) -> None:
        """Test that linear interpolation is used between points."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=3.0, price=85.0),
        ]

        curve = ZeroCouponCurve(securities)

        # Interpolate at midpoint
        df2 = curve.discount_factor(2.0)

        # Linear interpolation of discount factors: (0.95 + 0.85) / 2 = 0.90
        df1 = curve.discount_factor(1.0)
        df3 = curve.discount_factor(3.0)
        expected_df2 = (df1 + df3) / 2

        assert abs(df2 - expected_df2) < 0.01  # Linear interpolation of DFs

    def test_interpolation_monotonicity(self) -> None:
        """Test that interpolated values maintain monotonicity."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
            Security(maturity=3.0, price=85.0),
        ]

        curve = ZeroCouponCurve(securities)

        # Interpolate between all points
        test_maturities = [i * 0.1 for i in range(10, 31)]

        prev_df = None
        for t in test_maturities:
            df = curve.discount_factor(t)

            if prev_df is not None:
                # Discount factors should decrease with maturity
                assert df <= prev_df, f"DF not monotonic at t={t}: {df} > {prev_df}"

            prev_df = df


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
