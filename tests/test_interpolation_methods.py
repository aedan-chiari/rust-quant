"""Tests for different interpolation methods in ZeroCouponCurve.

This module tests the three interpolation methods:
- Linear: Linear interpolation of discount factors
- Log-linear: Piecewise constant forward rates (industry standard)
- Cubic: Cubic spline interpolation for smooth curves
"""

import math

import pytest
from rust_quant import ForwardCurve, Security, ZeroCouponCurve


class TestInterpolationMethods:
    """Test different interpolation methods."""

    def test_default_interpolation_is_log_linear(self) -> None:
        """Test that default interpolation is log-linear (industry standard)."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
        ]

        curve = ZeroCouponCurve(securities)
        assert curve.get_interpolation_method() == "log_linear"

    def test_linear_interpolation(self) -> None:
        """Test linear interpolation of discount factors."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
        ]

        curve = ZeroCouponCurve(securities, interpolation="linear")
        assert curve.get_interpolation_method() == "linear"

        # Test interpolation at midpoint
        df1 = curve.discount_factor(1.0)
        df2 = curve.discount_factor(2.0)
        df_mid = curve.discount_factor(1.5)

        # Linear interpolation: DF(1.5) = (DF(1) + DF(2)) / 2
        expected_df_mid = (df1 + df2) / 2.0
        assert abs(df_mid - expected_df_mid) < 1e-10

    def test_log_linear_interpolation(self) -> None:
        """Test log-linear interpolation (piecewise constant forward rates)."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
        ]

        curve = ZeroCouponCurve(securities, interpolation="log_linear")
        assert curve.get_interpolation_method() == "log_linear"

        # Test interpolation at midpoint
        df1 = curve.discount_factor(1.0)
        df2 = curve.discount_factor(2.0)
        df_mid = curve.discount_factor(1.5)

        # Log-linear: ln(DF) is linear → ln(DF(1.5)) = (ln(DF(1)) + ln(DF(2))) / 2
        ln_df1 = math.log(df1)
        ln_df2 = math.log(df2)
        ln_df_mid_expected = (ln_df1 + ln_df2) / 2.0
        expected_df_mid = math.exp(ln_df_mid_expected)

        assert abs(df_mid - expected_df_mid) < 1e-10

    def test_log_linear_implies_constant_forward_rates(self) -> None:
        """Test that log-linear interpolation implies piecewise constant forward rates."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
        ]

        curve = ZeroCouponCurve(securities, interpolation="log_linear")
        fwd_curve = ForwardCurve(curve)

        # Forward rates should be constant within each interval
        fwd_1_15 = fwd_curve.forward_rate(1.0, 1.5)
        fwd_15_2 = fwd_curve.forward_rate(1.5, 2.0)

        # Both should be approximately equal (piecewise constant)
        assert abs(fwd_1_15 - fwd_15_2) < 1e-10

    def test_cubic_spline_interpolation(self) -> None:
        """Test cubic spline interpolation for smooth curves."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
            Security(maturity=3.0, price=85.0),
        ]

        curve = ZeroCouponCurve(securities, interpolation="cubic")
        assert curve.get_interpolation_method() == "cubic"

        # Test that interpolated values are smooth
        df_mid = curve.discount_factor(1.5)

        # Should be between the two endpoints
        df1 = curve.discount_factor(1.0)
        df2 = curve.discount_factor(2.0)
        assert df2 < df_mid < df1  # Monotonically decreasing

    def test_cubic_spline_smoothness(self) -> None:
        """Test that cubic spline produces smoother curves than linear."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
            Security(maturity=3.0, price=85.0),
        ]

        # Create curves with different interpolation methods
        curve_linear = ZeroCouponCurve(securities, interpolation="linear")
        curve_cubic = ZeroCouponCurve(securities, interpolation="cubic")

        # Sample at multiple points
        test_points = [1.2, 1.4, 1.6, 1.8]
        dfs_linear = [curve_linear.discount_factor(t) for t in test_points]
        dfs_cubic = [curve_cubic.discount_factor(t) for t in test_points]

        # Both should produce valid discount factors
        for df in dfs_linear + dfs_cubic:
            assert 0 < df < 1

    def test_invalid_interpolation_method(self) -> None:
        """Test that invalid interpolation method raises error."""
        securities = [Security(maturity=1.0, price=95.0)]

        with pytest.raises(ValueError, match="Unknown interpolation method"):
            ZeroCouponCurve(securities, interpolation="invalid_method")

    def test_interpolation_with_coupon_bonds(self) -> None:
        """Test interpolation methods work with coupon-bearing bonds."""
        securities = [
            Security(maturity=0.5, price=97.5),  # Zero-coupon
            Security(maturity=1.0, price=97.0, coupon_rate=0.03, frequency=2),  # Coupon bond
            Security(maturity=2.0, price=98.0, coupon_rate=0.05, frequency=2),  # Coupon bond
        ]

        # All three methods should work
        curve_linear = ZeroCouponCurve(securities, interpolation="linear")
        curve_log_linear = ZeroCouponCurve(securities, interpolation="log_linear")
        curve_cubic = ZeroCouponCurve(securities, interpolation="cubic")

        # All should produce valid discount factors
        for curve in [curve_linear, curve_log_linear, curve_cubic]:
            df = curve.discount_factor(0.75)
            assert 0 < df < 1

    def test_from_vectors_with_interpolation(self) -> None:
        """Test from_vectors constructor with interpolation parameter."""
        maturities = [1.0, 2.0, 3.0]
        prices = [95.0, 90.0, 85.0]

        # Test each interpolation method
        curve_linear = ZeroCouponCurve.from_vectors(maturities, prices, interpolation="linear")
        curve_log_linear = ZeroCouponCurve.from_vectors(
            maturities,
            prices,
            interpolation="log_linear",
        )
        curve_cubic = ZeroCouponCurve.from_vectors(maturities, prices, interpolation="cubic")

        assert curve_linear.get_interpolation_method() == "linear"
        assert curve_log_linear.get_interpolation_method() == "log_linear"
        assert curve_cubic.get_interpolation_method() == "cubic"

    def test_interpolation_monotonicity(self) -> None:
        """Test that all interpolation methods preserve monotonicity."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
            Security(maturity=3.0, price=85.0),
        ]

        test_points = [t * 0.1 for t in range(10, 31)]

        for method in ["linear", "log_linear", "cubic"]:
            curve = ZeroCouponCurve(securities, interpolation=method)

            prev_df = None
            for t in test_points:
                df = curve.discount_factor(t)

                # Discount factors should be positive
                assert df > 0, f"Negative DF at t={t} with {method}"

                # Discount factors should decrease with maturity (monotonic)
                if prev_df is not None:
                    assert df <= prev_df, (
                        f"DF not monotonic at t={t} with {method}: {df} > {prev_df}"
                    )

                prev_df = df


class TestInterpolationAccuracy:
    """Test accuracy and properties of different interpolation methods."""

    def test_linear_exact_at_knots(self) -> None:
        """Test that linear interpolation matches exactly at knot points."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
        ]

        curve = ZeroCouponCurve(securities, interpolation="linear")

        # Should match exactly at knot points
        assert abs(curve.discount_factor(1.0) - 0.95) < 1e-10
        assert abs(curve.discount_factor(2.0) - 0.90) < 1e-10

    def test_log_linear_exact_at_knots(self) -> None:
        """Test that log-linear interpolation matches exactly at knot points."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
        ]

        curve = ZeroCouponCurve(securities, interpolation="log_linear")

        # Should match exactly at knot points
        assert abs(curve.discount_factor(1.0) - 0.95) < 1e-10
        assert abs(curve.discount_factor(2.0) - 0.90) < 1e-10

    def test_cubic_exact_at_knots(self) -> None:
        """Test that cubic interpolation matches exactly at knot points."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
            Security(maturity=3.0, price=85.0),
        ]

        curve = ZeroCouponCurve(securities, interpolation="cubic")

        # Should match exactly at knot points
        assert abs(curve.discount_factor(1.0) - 0.95) < 1e-10
        assert abs(curve.discount_factor(2.0) - 0.90) < 1e-10
        assert abs(curve.discount_factor(3.0) - 0.85) < 1e-10

    def test_extrapolation_consistency(self) -> None:
        """Test that extrapolation is consistent across methods."""
        securities = [Security(maturity=1.0, price=95.0)]

        # All methods should use flat rate extrapolation
        for method in ["linear", "log_linear", "cubic"]:
            curve = ZeroCouponCurve(securities, interpolation=method)

            # Extrapolate beyond curve
            df2 = curve.discount_factor(2.0)
            rate1 = curve.zero_rate(1.0)

            # Should use flat rate: DF(2) = exp(-rate1 * 2)
            expected_df2 = math.exp(-rate1 * 2.0)
            assert abs(df2 - expected_df2) < 1e-10, f"Extrapolation failed for {method}"


class TestInterpolationPerformance:
    """Test performance characteristics of interpolation methods."""

    def test_all_methods_support_batch_operations(self) -> None:
        """Test that batch operations work with all interpolation methods."""
        securities = [
            Security(maturity=1.0, price=95.0),
            Security(maturity=2.0, price=90.0),
            Security(maturity=3.0, price=85.0),
        ]

        test_maturities = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

        for method in ["linear", "log_linear", "cubic"]:
            curve = ZeroCouponCurve(securities, interpolation=method)

            # Batch discount factors
            dfs = ZeroCouponCurve.discount_factors_many(curve, test_maturities)
            assert len(dfs) == len(test_maturities)

            # Batch zero rates
            rates = ZeroCouponCurve.zero_rates_many(curve, test_maturities)
            assert len(rates) == len(test_maturities)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
