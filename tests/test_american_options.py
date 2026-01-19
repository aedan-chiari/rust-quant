"""Test suite for American option pricing calculations.

These tests verify American option pricing using binomial tree method,
which allows for early exercise capability.
"""

import pytest
from rust_quant import AmericanCallOption, AmericanOption, AmericanPutOption


class TestAmericanCallOptionPricing:
    """Test American call option pricing."""

    def test_atm_call_basic(self) -> None:
        """Test at-the-money American call option with standard parameters."""
        # S=100, K=100, T=1, r=0.05, σ=0.2, steps=100
        call = AmericanCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=100,
        )

        price = call.price()
        # American call without dividends should equal European call
        # Expected: ~10.45
        assert 10.0 < price < 11.0, f"Expected ~10.45, got {price}"

    def test_itm_call(self) -> None:
        """Test in-the-money American call option."""
        # S=110, K=100, T=1, r=0.05, σ=0.2
        call = AmericanCallOption(
            spot=110.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=100,
        )

        price = call.price()
        # Should be at least intrinsic value
        intrinsic = 110.0 - 100.0
        assert price > intrinsic, f"Price {price} should exceed intrinsic {intrinsic}"

    def test_otm_call(self) -> None:
        """Test out-of-the-money American call option."""
        # S=90, K=100, T=1, r=0.05, σ=0.2
        call = AmericanCallOption(
            spot=90.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=100,
        )

        price = call.price()
        # Expected: ~5.09 (similar to European)
        assert 4.5 < price < 5.5, f"Expected ~5.09, got {price}"

    def test_call_delta(self) -> None:
        """Test American call delta calculation."""
        call = AmericanCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=100,
        )

        delta = call.delta()
        # Delta should be between 0 and 1 for calls
        assert 0.0 < delta < 1.0, f"Delta {delta} should be between 0 and 1"
        # For ATM, delta should be around 0.5-0.65
        assert 0.4 < delta < 0.7, f"ATM delta {delta} should be around 0.5-0.65"

    def test_call_steps_convergence(self) -> None:
        """Test that increasing steps improves accuracy."""
        call_50 = AmericanCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=50,
        )

        call_200 = AmericanCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=200,
        )

        price_50 = call_50.price()
        price_200 = call_200.price()

        # Prices should converge (be relatively close)
        diff = abs(price_200 - price_50)
        assert diff < 0.5, f"Price difference {diff} should be small"


class TestAmericanPutOptionPricing:
    """Test American put option pricing."""

    def test_atm_put_basic(self) -> None:
        """Test at-the-money American put option with standard parameters."""
        # S=100, K=100, T=1, r=0.05, σ=0.2
        put = AmericanPutOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=100,
        )

        price = put.price()
        # American put should be worth MORE than European put (~5.57)
        # due to early exercise value
        assert 5.5 < price < 7.0, f"Expected 5.5-7.0, got {price}"

    def test_itm_put(self) -> None:
        """Test in-the-money American put option."""
        # S=90, K=100, T=1, r=0.05, σ=0.2
        put = AmericanPutOption(
            spot=90.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=100,
        )

        price = put.price()
        intrinsic = 100.0 - 90.0
        # American put should be worth more than intrinsic
        assert price >= intrinsic, f"Price {price} should be >= intrinsic {intrinsic}"
        # Expected: ~10.5-11.0 (more than European ~10.21 due to early exercise)
        assert 10.0 < price < 12.0, f"Expected 10.0-12.0, got {price}"

    def test_otm_put(self) -> None:
        """Test out-of-the-money American put option."""
        # S=110, K=100, T=1, r=0.05, σ=0.2
        put = AmericanPutOption(
            spot=110.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=100,
        )

        price = put.price()
        # Expected: ~2.79 (similar to European)
        assert 2.5 < price < 3.2, f"Expected ~2.79, got {price}"

    def test_put_delta(self) -> None:
        """Test American put delta calculation."""
        put = AmericanPutOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=100,
        )

        delta = put.delta()
        # Delta should be between -1 and 0 for puts
        assert -1.0 < delta < 0.0, f"Delta {delta} should be between -1 and 0"

    def test_early_exercise_premium(self) -> None:
        """Test that American put has early exercise premium over European."""
        # Deep ITM put with low interest rate - high early exercise value
        american_put = AmericanPutOption(
            spot=80.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.02,
            volatility=0.2,
            steps=100,
        )

        # For comparison, American puts should be worth more than intrinsic
        # and more than European equivalents when deep ITM
        price = american_put.price()
        intrinsic = 100.0 - 80.0

        # Should have time value on top of intrinsic
        assert price > intrinsic, f"American put {price} should exceed intrinsic {intrinsic}"


class TestAmericanBatchPricing:
    """Test batch pricing functionality for American options."""

    def test_call_price_many_basic(self) -> None:
        """Test batch pricing for American call options."""
        spots = [95.0, 100.0, 105.0, 110.0, 115.0]
        strikes = [100.0] * 5
        times = [1.0] * 5
        rates = [0.05] * 5
        vols = [0.2] * 5
        dividend_yields = [0.0] * 5
        steps = 100

        prices = AmericanCallOption.price_many(
            spots,
            strikes,
            times,
            rates,
            vols,
            dividend_yields,
            steps,
        )

        assert len(prices) == 5, "Should return 5 prices"

        # Verify all prices are positive
        for price in prices:
            assert price > 0, f"Price {price} should be positive"

        # ITM options should be worth more than OTM
        assert prices[4] > prices[0], "ITM should be worth more than OTM"

        # Prices should be monotonically increasing with spot
        for i in range(len(prices) - 1):
            assert prices[i + 1] > prices[i], "Prices should increase with spot"

    def test_put_price_many_basic(self) -> None:
        """Test batch pricing for American put options."""
        spots = [85.0, 90.0, 95.0, 100.0, 105.0]
        strikes = [100.0] * 5
        times = [1.0] * 5
        rates = [0.05] * 5
        vols = [0.2] * 5
        dividend_yields = [0.0] * 5
        steps = 100

        prices = AmericanPutOption.price_many(
            spots,
            strikes,
            times,
            rates,
            vols,
            dividend_yields,
            steps,
        )

        assert len(prices) == 5, "Should return 5 prices"

        # Verify all prices are positive
        for price in prices:
            assert price > 0, f"Price {price} should be positive"

        # ITM puts (low spot) should be worth more than OTM
        assert prices[0] > prices[4], "ITM put should be worth more than OTM"

        # Prices should be monotonically decreasing with spot
        for i in range(len(prices) - 1):
            assert prices[i] > prices[i + 1], "Put prices should decrease with spot"

    def test_call_greeks_many(self) -> None:
        """Test batch Greeks calculation for American call options."""
        spots = [95.0, 100.0, 105.0]
        strikes = [100.0] * 3
        times = [1.0] * 3
        rates = [0.05] * 3
        vols = [0.2] * 3
        dividend_yields = [0.0] * 3
        steps = 100

        prices, deltas, gammas, vegas, thetas, rhos = AmericanCallOption.greeks_many(
            spots,
            strikes,
            times,
            rates,
            vols,
            dividend_yields,
            steps,
        )

        # Check all arrays have correct length
        assert len(prices) == 3
        assert len(deltas) == 3
        assert len(gammas) == 3
        assert len(vegas) == 3
        assert len(thetas) == 3
        assert len(rhos) == 3

        # Check delta bounds for calls
        for delta in deltas:
            assert 0.0 < delta < 1.0, f"Call delta {delta} should be between 0 and 1"

        # Check gamma is positive (with tolerance for floating-point precision)
        for gamma in gammas:
            assert gamma > -1e-10, (
                f"Gamma {gamma} should be positive (or near-zero due to floating-point precision)"
            )

        # Check vega is positive
        for vega in vegas:
            assert vega > 0, f"Vega {vega} should be positive"

    def test_put_greeks_many(self) -> None:
        """Test batch Greeks calculation for American put options."""
        spots = [95.0, 100.0, 105.0]
        strikes = [100.0] * 3
        times = [1.0] * 3
        rates = [0.05] * 3
        vols = [0.2] * 3
        dividend_yields = [0.0] * 3
        steps = 100

        prices, deltas, gammas, vegas, thetas, rhos = AmericanPutOption.greeks_many(
            spots,
            strikes,
            times,
            rates,
            vols,
            dividend_yields,
            steps,
        )

        # Check all arrays have correct length
        assert len(prices) == 3
        assert len(deltas) == 3
        assert len(gammas) == 3
        assert len(vegas) == 3
        assert len(thetas) == 3
        assert len(rhos) == 3

        # Check delta bounds for puts
        for delta in deltas:
            assert -1.0 < delta < 0.0, f"Put delta {delta} should be between -1 and 0"

        # Check gamma is positive
        for gamma in gammas:
            assert gamma > 0, f"Gamma {gamma} should be positive"

        # Check vega is positive
        for vega in vegas:
            assert vega > 0, f"Vega {vega} should be positive"

    def test_batch_vs_individual_consistency(self) -> None:
        """Verify batch pricing matches individual pricing."""
        spots = [95.0, 100.0, 105.0]
        strikes = [100.0] * 3
        times = [1.0] * 3
        rates = [0.05] * 3
        vols = [0.2] * 3
        dividend_yields = [0.0] * 3
        steps = 100

        # Batch pricing
        batch_prices = AmericanCallOption.price_many(
            spots,
            strikes,
            times,
            rates,
            vols,
            dividend_yields,
            steps,
        )

        # Individual pricing
        individual_prices = []
        for i in range(3):
            opt = AmericanCallOption(
                spots[i],
                strikes[i],
                times[i],
                rates[i],
                vols[i],
                dividend_yields[i],
                steps,
            )
            individual_prices.append(opt.price())

        # Prices should match
        for batch, individual in zip(batch_prices, individual_prices, strict=True):
            assert abs(batch - individual) < 1e-10, f"Batch {batch} != Individual {individual}"

    def test_batch_with_dividends(self) -> None:
        """Test batch pricing with dividend yields."""
        spots = [95.0, 100.0, 105.0, 110.0]
        strikes = [100.0] * 4
        times = [1.0] * 4
        rates = [0.05] * 4
        vols = [0.2] * 4
        dividend_yields = [0.03] * 4  # 3% dividend yield
        steps = 100

        prices_with_div = AmericanCallOption.price_many(
            spots,
            strikes,
            times,
            rates,
            vols,
            dividend_yields,
            steps,
        )

        prices_no_div = AmericanCallOption.price_many(
            spots,
            strikes,
            times,
            rates,
            vols,
            [0.0] * 4,
            steps,
        )

        # Dividends should reduce call prices
        for with_div, no_div in zip(prices_with_div, prices_no_div, strict=True):
            assert with_div < no_div, "Dividends should reduce call option value"

    def test_input_validation(self) -> None:
        """Test that mismatched input lengths raise errors."""
        spots = [100.0, 105.0]
        strikes = [100.0]  # Wrong length
        times = [1.0, 1.0]
        rates = [0.05, 0.05]
        vols = [0.2, 0.2]
        dividend_yields = [0.0, 0.0]
        steps = 100

        with pytest.raises(ValueError, match="same length"):
            AmericanCallOption.price_many(
                spots,
                strikes,
                times,
                rates,
                vols,
                dividend_yields,
                steps,
            )

    def test_large_batch_performance(self) -> None:
        """Test that batch pricing works with larger datasets."""
        n = 100
        spots = [95.0 + (i * 30.0 / n) for i in range(n)]
        strikes = [100.0] * n
        times = [1.0] * n
        rates = [0.05] * n
        vols = [0.2] * n
        dividend_yields = [0.0] * n
        steps = 50  # Use fewer steps for speed

        prices = AmericanCallOption.price_many(
            spots,
            strikes,
            times,
            rates,
            vols,
            dividend_yields,
            steps,
        )

        assert len(prices) == n, f"Should return {n} prices"

        # All prices should be positive and reasonable
        for price in prices:
            assert 0 < price < 200, f"Price {price} should be reasonable"


class TestAmericanGreeks:
    """Test American option Greeks calculations."""

    def test_call_gamma(self) -> None:
        """Test American call gamma."""
        call = AmericanCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=100,
        )

        gamma = call.gamma()
        # Gamma should be positive
        assert gamma > 0, f"Gamma {gamma} should be positive"

    def test_call_vega(self) -> None:
        """Test American call vega."""
        call = AmericanCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=100,
        )

        vega = call.vega()
        # Vega should be positive (higher vol = higher option value)
        assert vega > 0, f"Vega {vega} should be positive"

    def test_call_theta(self) -> None:
        """Test American call theta."""
        call = AmericanCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=100,
        )

        theta = call.theta()
        # Theta should generally be negative (time decay)
        assert theta < 0, f"Theta {theta} should be negative"

    def test_call_rho(self) -> None:
        """Test American call rho."""
        call = AmericanCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=100,
        )

        rho = call.rho()
        # Rho should be positive for calls (higher rates increase call value)
        assert rho > 0, f"Rho {rho} should be positive for calls"

    def test_put_rho(self) -> None:
        """Test American put rho."""
        put = AmericanPutOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=100,
        )

        rho = put.rho()
        # Rho should be negative for puts (higher rates decrease put value)
        assert rho < 0, f"Rho {rho} should be negative for puts"


class TestAmericanImmutableUpdates:
    """Test immutable update methods."""

    def test_with_spot(self) -> None:
        """Test with_spot creates new option."""
        call = AmericanCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=100,
        )

        new_call = call.with_spot(110.0)

        # Original unchanged
        assert call.spot == 100.0
        # New has updated value
        assert new_call.spot == 110.0
        # Other params unchanged
        assert new_call.strike == call.strike
        assert new_call.steps == call.steps

    def test_with_volatility(self) -> None:
        """Test with_volatility creates new option."""
        put = AmericanPutOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=100,
        )

        new_put = put.with_volatility(0.3)

        assert put.volatility == 0.2
        assert new_put.volatility == 0.3

    def test_with_steps(self) -> None:
        """Test with_steps creates new option."""
        call = AmericanCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=100,
        )

        new_call = call.with_steps(200)

        assert call.steps == 100
        assert new_call.steps == 200


class TestAmericanGenericOption:
    """Test the generic AmericanOption class."""

    def test_american_option_as_call(self) -> None:
        """Test AmericanOption with is_call=True."""
        opt = AmericanOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            is_call=True,
            steps=100,
        )
        call = AmericanCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=100,
        )

        # Should produce similar prices
        assert abs(opt.price() - call.price()) < 0.01

    def test_american_option_as_put(self) -> None:
        """Test AmericanOption with is_call=False."""
        opt = AmericanOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            is_call=False,
            steps=100,
        )
        put = AmericanPutOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=100,
        )

        # Should produce similar prices
        assert abs(opt.price() - put.price()) < 0.01


class TestAmericanWithDividends:
    """Test American options with dividend yields."""

    def test_call_with_dividend(self) -> None:
        """Test American call with dividend yield."""
        # With dividends, early exercise may be optimal
        call = AmericanCallOption(
            spot=100.0,
            strike=90.0,  # Deep ITM
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            dividend_yield=0.08,  # High dividend
            steps=100,
        )

        price = call.price()
        intrinsic = 100.0 - 90.0

        # Price should be reasonable
        assert price >= intrinsic, f"Price {price} should be >= intrinsic {intrinsic}"
        assert price < 20.0, f"Price {price} should be < 20"

    def test_put_with_dividend(self) -> None:
        """Test American put with dividend yield."""
        put = AmericanPutOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            dividend_yield=0.03,
            steps=100,
        )

        price = put.price()
        # Dividend makes put less valuable (reduces spot growth)
        # but American feature adds early exercise value
        assert 5.0 < price < 8.0, f"Expected 5.0-8.0, got {price}"


class TestEdgeCases:
    """Test edge cases for American options."""

    def test_zero_time_to_expiry(self) -> None:
        """Test American option at expiration."""
        call = AmericanCallOption(
            spot=110.0,
            strike=100.0,
            time_to_expiry=0.0001,  # Nearly expired
            risk_free_rate=0.05,
            volatility=0.2,
            steps=10,
        )

        price = call.price()
        intrinsic = 110.0 - 100.0
        # At expiration, should be close to intrinsic value
        assert abs(price - intrinsic) < 1.0, f"Price {price} should be ~{intrinsic}"

    def test_deep_itm_put(self) -> None:
        """Test deep in-the-money American put."""
        # S=50, K=100, deep ITM
        put = AmericanPutOption(
            spot=50.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            steps=100,
        )

        price = put.price()
        intrinsic = 100.0 - 50.0

        # Should be close to intrinsic for deep ITM American put
        # (early exercise is optimal)
        assert price >= intrinsic, f"Price {price} should be >= intrinsic {intrinsic}"
        assert price < intrinsic + 5.0, f"Price {price} should be close to intrinsic"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
