"""Test suite for European option pricing calculations.

These tests compare our implementation against known correct Black-Scholes values
from academic literature and standard financial calculators.
"""

import math

import pytest
from rust_quant import EuroCallOption, EuroOption, EuroPutOption


class TestCallOptionPricing:
    """Test call option pricing against known reference values."""

    def test_atm_call_basic(self) -> None:
        """Test at-the-money call option with standard parameters."""
        # Reference: Hull's "Options, Futures, and Other Derivatives"
        # S=100, K=100, T=1, r=0.05, σ=0.2
        call = EuroCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
        )

        price = call.price()
        # Expected: ~10.45 (from Black-Scholes formula)
        assert abs(price - 10.4506) < 0.01, f"Expected ~10.45, got {price}"

    def test_itm_call(self) -> None:
        """Test in-the-money call option."""
        # S=110, K=100, T=1, r=0.05, σ=0.2
        call = EuroCallOption(
            spot=110.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
        )

        price = call.price()
        # Expected: ~17.66
        assert abs(price - 17.663) < 0.01, f"Expected ~17.66, got {price}"

    def test_otm_call(self) -> None:
        """Test out-of-the-money call option."""
        # S=90, K=100, T=1, r=0.05, σ=0.2
        call = EuroCallOption(
            spot=90.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
        )

        price = call.price()
        # Expected: ~5.09
        assert abs(price - 5.091) < 0.01, f"Expected ~5.09, got {price}"

    def test_high_volatility_call(self) -> None:
        """Test call with high volatility."""
        # S=100, K=100, T=1, r=0.05, σ=0.4
        call = EuroCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.4,
        )

        price = call.price()
        # Expected: ~18.02
        assert abs(price - 18.023) < 0.01, f"Expected ~18.02, got {price}"

    def test_short_expiry_call(self) -> None:
        """Test call with short time to expiration."""
        # S=100, K=100, T=0.25, r=0.05, σ=0.2
        call = EuroCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.2,
        )

        price = call.price()
        # Expected: ~4.61
        assert abs(price - 4.615) < 0.01, f"Expected ~4.61, got {price}"


class TestEuroPutOptionPricing:
    """Test put option pricing against known reference values."""

    def test_atm_put_basic(self) -> None:
        """Test at-the-money put option with standard parameters."""
        # S=100, K=100, T=1, r=0.05, σ=0.2
        put = EuroPutOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
        )

        price = put.price()
        # Expected: ~5.57 (from Black-Scholes formula)
        assert abs(price - 5.5735) < 0.01, f"Expected ~5.57, got {price}"

    def test_itm_put(self) -> None:
        """Test in-the-money put option."""
        # S=90, K=100, T=1, r=0.05, σ=0.2
        put = EuroPutOption(
            spot=90.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
        )

        price = put.price()
        # Expected: ~10.21
        assert abs(price - 10.214) < 0.01, f"Expected ~10.21, got {price}"

    def test_otm_put(self) -> None:
        """Test out-of-the-money put option."""
        # S=110, K=100, T=1, r=0.05, σ=0.2
        put = EuroPutOption(
            spot=110.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
        )

        price = put.price()
        # Expected: ~2.79
        assert abs(price - 2.786) < 0.01, f"Expected ~2.79, got {price}"

    def test_put_call_parity(self) -> None:
        """Test put-call parity: C - P = S - K*e^(-rT)."""
        S, K, T, r, sigma = 100.0, 100.0, 1.0, 0.05, 0.2

        call = EuroCallOption(
            spot=S,
            strike=K,
            time_to_expiry=T,
            risk_free_rate=r,
            volatility=sigma,
        )
        put = EuroPutOption(spot=S, strike=K, time_to_expiry=T, risk_free_rate=r, volatility=sigma)

        call_price = call.price()
        put_price = put.price()

        lhs = call_price - put_price
        rhs = S - K * math.exp(-r * T)

        assert abs(lhs - rhs) < 0.01, f"Put-call parity violated: {lhs} != {rhs}"


class TestGreeks:
    """Test option Greeks calculations."""

    def test_call_delta(self) -> None:
        """Test call option delta."""
        # S=100, K=100, T=1, r=0.05, σ=0.2
        call = EuroCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
        )

        delta = call.delta()
        # Expected: ~0.637 (N(d1) for ATM call)
        assert 0.60 < delta < 0.65, f"Expected delta ~0.637, got {delta}"

    def test_put_delta(self) -> None:
        """Test put option delta."""
        # S=100, K=100, T=1, r=0.05, σ=0.2
        put = EuroPutOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
        )

        delta = put.delta()
        # Expected: ~-0.363 (N(d1) - 1 for ATM put)
        assert -0.40 < delta < -0.35, f"Expected delta ~-0.363, got {delta}"

    def test_gamma_symmetry(self) -> None:
        """Test that call and put gamma are equal."""
        S, K, T, r, sigma = 100.0, 100.0, 1.0, 0.05, 0.2

        call = EuroCallOption(
            spot=S,
            strike=K,
            time_to_expiry=T,
            risk_free_rate=r,
            volatility=sigma,
        )
        put = EuroPutOption(spot=S, strike=K, time_to_expiry=T, risk_free_rate=r, volatility=sigma)

        call_gamma = call.gamma()
        put_gamma = put.gamma()

        # Gamma should be identical for calls and puts
        assert abs(call_gamma - put_gamma) < 0.0001, (
            f"Gamma mismatch: call={call_gamma}, put={put_gamma}"
        )

    def test_vega_symmetry(self) -> None:
        """Test that call and put vega are equal."""
        S, K, T, r, sigma = 100.0, 100.0, 1.0, 0.05, 0.2

        call = EuroCallOption(
            spot=S,
            strike=K,
            time_to_expiry=T,
            risk_free_rate=r,
            volatility=sigma,
        )
        put = EuroPutOption(spot=S, strike=K, time_to_expiry=T, risk_free_rate=r, volatility=sigma)

        call_vega = call.vega()
        put_vega = put.vega()

        # Vega should be identical for calls and puts
        assert abs(call_vega - put_vega) < 0.0001, (
            f"Vega mismatch: call={call_vega}, put={put_vega}"
        )

    def test_call_theta_negative(self) -> None:
        """Test that call theta is negative (time decay)."""
        call = EuroCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
        )

        theta = call.theta()
        # Theta should be negative for long options
        assert theta < 0, f"Expected negative theta, got {theta}"

    def test_call_rho_positive(self) -> None:
        """Test that call rho is positive."""
        call = EuroCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
        )

        rho = call.rho()
        # Call rho should be positive (benefits from higher rates)
        assert rho > 0, f"Expected positive rho, got {rho}"

    def test_put_rho_negative(self) -> None:
        """Test that put rho is negative."""
        put = EuroPutOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
        )

        rho = put.rho()
        # Put rho should be negative (hurt by higher rates)
        assert rho < 0, f"Expected negative rho, got {rho}"


class TestVectorizedOperations:
    """Test vectorized pricing for multiple options."""

    def test_vectorized_call_pricing(self) -> None:
        """Test that vectorized pricing matches individual pricing."""
        spots = [100.0, 105.0, 95.0]
        strikes = [100.0, 100.0, 100.0]
        times = [1.0, 1.0, 1.0]
        rates = [0.05, 0.05, 0.05]
        vols = [0.2, 0.2, 0.2]

        # Vectorized pricing
        vec_prices = EuroCallOption.price_many(spots, strikes, times, rates, vols)

        # Individual pricing
        ind_prices = [
            EuroCallOption(s, k, t, r, v).price()
            for s, k, t, r, v in zip(spots, strikes, times, rates, vols, strict=True)
        ]

        for vec_p, ind_p in zip(vec_prices, ind_prices, strict=True):
            assert abs(vec_p - ind_p) < 0.0001, (
                f"Vectorized price {vec_p} != individual price {ind_p}"
            )

    def test_vectorized_put_pricing(self) -> None:
        """Test that vectorized put pricing matches individual pricing."""
        spots = [100.0, 105.0, 95.0]
        strikes = [100.0, 100.0, 100.0]
        times = [1.0, 1.0, 1.0]
        rates = [0.05, 0.05, 0.05]
        vols = [0.2, 0.2, 0.2]

        # Vectorized pricing
        vec_prices = EuroPutOption.price_many(spots, strikes, times, rates, vols)

        # Individual pricing
        ind_prices = [
            EuroPutOption(s, k, t, r, v).price()
            for s, k, t, r, v in zip(spots, strikes, times, rates, vols, strict=True)
        ]

        for vec_p, ind_p in zip(vec_prices, ind_prices, strict=True):
            assert abs(vec_p - ind_p) < 0.0001, (
                f"Vectorized price {vec_p} != individual price {ind_p}"
            )

    def test_vectorized_greeks(self) -> None:
        """Test that vectorized Greeks match individual Greeks."""
        spots = [100.0, 110.0]
        strikes = [100.0, 100.0]
        times = [1.0, 1.0]
        rates = [0.05, 0.05]
        vols = [0.2, 0.2]

        # Vectorized Greeks
        prices, deltas, gammas, vegas, thetas, rhos = EuroCallOption.greeks_many(
            spots,
            strikes,
            times,
            rates,
            vols,
        )

        # Individual Greeks
        for i, (s, k, t, r, v) in enumerate(
            zip(spots, strikes, times, rates, vols, strict=True),
        ):
            call = EuroCallOption(s, k, t, r, v)
            greeks = call.greeks()

            assert abs(prices[i] - greeks.price) < 0.0001
            assert abs(deltas[i] - greeks.delta) < 0.0001
            assert abs(gammas[i] - greeks.gamma) < 0.0001
            assert abs(vegas[i] - greeks.vega) < 0.0001
            assert abs(thetas[i] - greeks.theta) < 0.0001
            assert abs(rhos[i] - greeks.rho) < 0.0001

    def test_large_batch_consistency(self) -> None:
        """Test consistency with larger batches (tests SIMD code path)."""
        n = 1000
        spots = [100.0 + i * 0.1 for i in range(n)]
        strikes = [100.0] * n
        times = [1.0] * n
        rates = [0.05] * n
        vols = [0.2] * n

        vec_prices = EuroCallOption.price_many(spots, strikes, times, rates, vols)

        # Spot check a few values
        for i in [0, 100, 500, 999]:
            call = EuroCallOption(spots[i], strikes[i], times[i], rates[i], vols[i])
            ind_price = call.price()
            assert abs(vec_prices[i] - ind_price) < 0.0001, (
                f"Mismatch at index {i}: {vec_prices[i]} != {ind_price}"
            )


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_time_to_expiry(self) -> None:
        """Test option at expiration."""
        # Call at expiration should be max(S-K, 0)
        call = EuroCallOption(
            spot=110.0,
            strike=100.0,
            time_to_expiry=0.0001,
            risk_free_rate=0.05,
            volatility=0.2,
        )
        price = call.price()
        intrinsic = max(110.0 - 100.0, 0.0)
        assert abs(price - intrinsic) < 0.5, f"Expected ~{intrinsic}, got {price}"

    def test_deep_itm_call(self) -> None:
        """Test deep in-the-money call."""
        # S=200, K=100, deep ITM
        call = EuroCallOption(
            spot=200.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
        )
        price = call.price()
        # Should be close to intrinsic value + carrying cost
        assert price > 100.0, f"Deep ITM call should be > 100, got {price}"

    def test_deep_otm_call(self) -> None:
        """Test deep out-of-the-money call."""
        # S=50, K=100, deep OTM
        call = EuroCallOption(
            spot=50.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
        )
        price = call.price()
        # Should be very small
        assert price < 1.0, f"Deep OTM call should be < 1, got {price}"

    def test_zero_volatility(self) -> None:
        """Test with zero volatility (deterministic case)."""
        # With σ=0, option value should approach intrinsic
        call = EuroCallOption(
            spot=110.0,
            strike=100.0,
            time_to_expiry=0.0001,
            risk_free_rate=0.05,
            volatility=0.0001,
        )
        price = call.price()
        intrinsic = 110.0 - 100.0
        assert abs(price - intrinsic) < 0.5, (
            f"Zero vol should give ~intrinsic {intrinsic}, got {price}"
        )


class TestGenericOption:
    """Test the generic Option class."""

    def test_option_as_call(self) -> None:
        """Test Option class with is_call=True."""
        opt = EuroOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            is_call=True,
        )
        call = EuroCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
        )

        assert abs(opt.price() - call.price()) < 0.0001
        assert abs(opt.delta() - call.delta()) < 0.0001

    def test_option_as_put(self) -> None:
        """Test Option class with is_call=False."""
        opt = EuroOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            is_call=False,
        )
        put = EuroPutOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
        )

        assert abs(opt.price() - put.price()) < 0.0001
        assert abs(opt.delta() - put.delta()) < 0.0001


class TestDividendYield:
    """Test options with dividend yields."""

    def test_call_with_dividend(self) -> None:
        """Test that dividend yield reduces call option price."""
        # Without dividend
        call_no_div = EuroCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            dividend_yield=0.0,
        )

        # With 2% dividend yield
        call_with_div = EuroCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            dividend_yield=0.02,
        )

        # Dividend should reduce call value
        assert call_with_div.price() < call_no_div.price(), (
            f"Call with dividend ({call_with_div.price()}) should be less than "
            f"without ({call_no_div.price()})"
        )

    def test_put_with_dividend(self) -> None:
        """Test that dividend yield increases put option price."""
        # Without dividend
        put_no_div = EuroPutOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            dividend_yield=0.0,
        )

        # With 2% dividend yield
        put_with_div = EuroPutOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            dividend_yield=0.02,
        )

        # Dividend should increase put value
        assert put_with_div.price() > put_no_div.price(), (
            f"Put with dividend ({put_with_div.price()}) should be greater than "
            f"without ({put_no_div.price()})"
        )

    def test_put_call_parity_with_dividend(self) -> None:
        """Test put-call parity with dividend: C - P = S*e^(-qT) - K*e^(-rT)."""
        S, K, T, r, sigma, q = 100.0, 100.0, 1.0, 0.05, 0.2, 0.02

        call = EuroCallOption(
            spot=S,
            strike=K,
            time_to_expiry=T,
            risk_free_rate=r,
            volatility=sigma,
            dividend_yield=q,
        )
        put = EuroPutOption(
            spot=S,
            strike=K,
            time_to_expiry=T,
            risk_free_rate=r,
            volatility=sigma,
            dividend_yield=q,
        )

        call_price = call.price()
        put_price = put.price()

        lhs = call_price - put_price
        rhs = S * math.exp(-q * T) - K * math.exp(-r * T)

        assert abs(lhs - rhs) < 0.01, f"Put-call parity with dividend violated: {lhs} != {rhs}"

    def test_call_delta_with_dividend(self) -> None:
        """Test that dividend reduces call delta."""
        # Without dividend
        call_no_div = EuroCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            dividend_yield=0.0,
        )

        # With dividend
        call_with_div = EuroCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            dividend_yield=0.02,
        )

        # Dividend should reduce call delta
        assert call_with_div.delta() < call_no_div.delta(), (
            "Call delta with dividend should be less than without"
        )

    def test_high_dividend_yield(self) -> None:
        """Test option with high dividend yield (e.g., 5%)."""
        call = EuroCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            dividend_yield=0.05,
        )
        put = EuroPutOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            dividend_yield=0.05,
        )

        # Should produce reasonable prices
        assert 0 < call.price() < 100, f"Call price {call.price()} seems unreasonable"
        assert 0 < put.price() < 100, f"Put price {put.price()} seems unreasonable"

        # With equal risk-free rate and dividend yield, ATM call and put should be similar
        assert abs(call.price() - put.price()) < 5.0, (
            "With r=q, ATM call and put should be similar in value"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
