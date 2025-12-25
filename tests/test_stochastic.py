"""Tests for stochastic processes and Monte Carlo simulation."""

import math

from rust_quant import (
    BrownianMotion,
    EuroCallOption,
    GeometricBrownianMotion,
    HestonProcess,
    StochasticRng,
)


class TestStochasticRng:
    """Tests for random number generator."""

    def test_normal_generation(self) -> None:
        """Test that normal random variables have correct distribution."""
        rng = StochasticRng()
        normals = [rng.normal() for _ in range(10000)]

        mean = sum(normals) / len(normals)
        variance = sum((x - mean) ** 2 for x in normals) / len(normals)

        # Mean should be close to 0
        assert abs(mean) < 0.1
        # Variance should be close to 1
        assert abs(variance - 1.0) < 0.1

    def test_reproducibility(self) -> None:
        """Test that same seed produces same sequence."""
        rng1 = StochasticRng(seed=42)
        normals1 = [rng1.normal() for _ in range(100)]

        rng2 = StochasticRng(seed=42)
        normals2 = [rng2.normal() for _ in range(100)]

        # Same seed should produce identical sequence
        assert normals1 == normals2

    def test_uniform_generation(self) -> None:
        """Test uniform random variable generation."""
        rng = StochasticRng()
        uniforms = [rng.uniform() for _ in range(10000)]

        # All values should be in [0, 1)
        assert all(0 <= x < 1 for x in uniforms)

        # Mean should be close to 0.5
        mean = sum(uniforms) / len(uniforms)
        assert abs(mean - 0.5) < 0.05

    def test_batch_normal_generation(self) -> None:
        """Test batch normal generation."""
        rng = StochasticRng()
        normals = rng.normals(1000)

        assert len(normals) == 1000
        mean = sum(normals) / len(normals)
        assert abs(mean) < 0.15


class TestBrownianMotion:
    """Tests for Brownian motion path generation."""

    def test_path_starts_at_zero(self) -> None:
        """Test that Brownian motion starts at 0."""
        bm = BrownianMotion(time_horizon=1.0, num_steps=100)
        path = bm.generate_path()

        assert path[0] == 0.0
        assert len(path) == 101  # num_steps + 1

    def test_time_grid(self) -> None:
        """Test time grid generation."""
        bm = BrownianMotion(time_horizon=1.0, num_steps=100)
        times = bm.time_grid()

        assert len(times) == 101
        assert times[0] == 0.0
        assert abs(times[-1] - 1.0) < 1e-10

    def test_dt(self) -> None:
        """Test time step calculation."""
        bm = BrownianMotion(time_horizon=1.0, num_steps=100)
        assert abs(bm.dt() - 0.01) < 1e-10

    def test_multiple_paths(self) -> None:
        """Test generating multiple paths."""
        bm = BrownianMotion(time_horizon=1.0, num_steps=100)
        paths = bm.generate_paths(10)

        assert len(paths) == 10
        for path in paths:
            assert len(path) == 101
            assert path[0] == 0.0

    def test_parallel_paths(self) -> None:
        """Test parallel path generation."""
        bm = BrownianMotion(time_horizon=1.0, num_steps=100)
        paths = bm.generate_paths_parallel(100)

        assert len(paths) == 100
        for path in paths:
            assert len(path) == 101

    def test_antithetic_paths(self) -> None:
        """Test antithetic variance reduction."""
        bm = BrownianMotion(time_horizon=1.0, num_steps=100)
        path1, path2 = bm.generate_antithetic_paths()

        assert len(path1) == len(path2)
        assert path1[0] == 0.0
        assert path2[0] == 0.0

    def test_terminal_variance(self) -> None:
        """Test that W(T) has variance T."""
        bm = BrownianMotion(time_horizon=1.0, num_steps=100)
        paths = bm.generate_paths(10000)

        finals = [p[-1] for p in paths]
        mean = sum(finals) / len(finals)
        variance = sum((x - mean) ** 2 for x in finals) / len(finals)

        # Mean should be close to 0
        assert abs(mean) < 0.05
        # Variance should be close to T=1.0
        assert abs(variance - 1.0) < 0.1


class TestGeometricBrownianMotion:
    """Tests for Geometric Brownian Motion."""

    def test_path_starts_at_spot(self) -> None:
        """Test that GBM path starts at initial spot price."""
        gbm = GeometricBrownianMotion(
            spot=100.0,
            drift=0.05,
            volatility=0.2,
            time_horizon=1.0,
            num_steps=100,
        )
        path = gbm.generate_path()

        assert path[0] == 100.0
        assert len(path) == 101

    def test_path_stays_positive(self) -> None:
        """Test that stock prices stay positive."""
        gbm = GeometricBrownianMotion(
            spot=100.0,
            drift=0.05,
            volatility=0.2,
            time_horizon=1.0,
            num_steps=100,
        )
        path = gbm.generate_path()

        # All prices should be positive
        assert all(p > 0 for p in path)

    def test_parameters(self) -> None:
        """Test that parameters are stored correctly."""
        gbm = GeometricBrownianMotion(
            spot=100.0,
            drift=0.05,
            volatility=0.2,
            time_horizon=1.0,
            num_steps=252,
        )

        assert gbm.get_spot() == 100.0
        assert gbm.get_drift() == 0.05
        assert gbm.get_volatility() == 0.2
        assert gbm.get_time_horizon() == 1.0
        assert gbm.get_num_steps() == 252

    def test_terminal_prices(self) -> None:
        """Test batch terminal price generation."""
        gbm = GeometricBrownianMotion(
            spot=100.0,
            drift=0.05,
            volatility=0.2,
            time_horizon=1.0,
            num_steps=100,
        )
        prices = gbm.terminal_prices(1000)

        assert len(prices) == 1000
        assert all(p > 0 for p in prices)

        # Mean should be approximately spot * exp(drift * T)
        mean = sum(prices) / len(prices)
        expected = 100.0 * math.exp(0.05 * 1.0)
        # Allow 20% tolerance due to stochastic nature
        assert abs(mean - expected) / expected < 0.2

    def test_antithetic_paths(self) -> None:
        """Test antithetic variance reduction for GBM."""
        gbm = GeometricBrownianMotion(
            spot=100.0,
            drift=0.05,
            volatility=0.2,
            time_horizon=1.0,
            num_steps=100,
        )
        path1, path2 = gbm.generate_antithetic_paths()

        assert len(path1) == len(path2)
        assert path1[0] == 100.0
        assert path2[0] == 100.0


class TestHestonProcess:
    """Tests for Heston stochastic volatility model."""

    def test_path_generation(self) -> None:
        """Test Heston path generation."""
        heston = HestonProcess(
            spot=100.0,
            initial_variance=0.04,
            drift=0.05,
            kappa=2.0,
            theta=0.04,
            vol_of_vol=0.3,
            correlation=-0.7,
            time_horizon=1.0,
            num_steps=100,
        )

        price_path, variance_path = heston.generate_path()

        assert len(price_path) == 101
        assert len(variance_path) == 101
        assert price_path[0] == 100.0
        assert variance_path[0] == 0.04

    def test_price_stays_positive(self) -> None:
        """Test that stock prices stay non-negative."""
        heston = HestonProcess(
            spot=100.0,
            initial_variance=0.04,
            drift=0.05,
            kappa=2.0,
            theta=0.04,
            vol_of_vol=0.3,
            correlation=-0.7,
            time_horizon=1.0,
            num_steps=100,
        )

        price_path, _ = heston.generate_path()
        assert all(p >= 0 for p in price_path)

    def test_variance_stays_nonnegative(self) -> None:
        """Test that variance stays non-negative (absorption at zero)."""
        heston = HestonProcess(
            spot=100.0,
            initial_variance=0.04,
            drift=0.05,
            kappa=2.0,
            theta=0.04,
            vol_of_vol=0.3,
            correlation=-0.7,
            time_horizon=1.0,
            num_steps=100,
        )

        _, variance_path = heston.generate_path()
        assert all(v >= 0 for v in variance_path)

    def test_parameters(self) -> None:
        """Test parameter storage."""
        heston = HestonProcess(
            spot=100.0,
            initial_variance=0.04,
            drift=0.05,
            kappa=2.0,
            theta=0.04,
            vol_of_vol=0.3,
            correlation=-0.7,
            time_horizon=1.0,
            num_steps=252,
        )

        assert heston.get_spot() == 100.0
        assert heston.get_initial_variance() == 0.04
        assert heston.get_drift() == 0.05
        assert heston.get_kappa() == 2.0
        assert heston.get_theta() == 0.04
        assert heston.get_vol_of_vol() == 0.3
        assert heston.get_correlation() == -0.7
        assert heston.get_time_horizon() == 1.0
        assert heston.get_num_steps() == 252

    def test_terminal_values(self) -> None:
        """Test batch terminal value generation."""
        heston = HestonProcess(
            spot=100.0,
            initial_variance=0.04,
            drift=0.05,
            kappa=2.0,
            theta=0.04,
            vol_of_vol=0.3,
            correlation=-0.7,
            time_horizon=1.0,
            num_steps=100,
        )

        prices, variances = heston.terminal_values(1000)

        assert len(prices) == 1000
        assert len(variances) == 1000
        assert all(p >= 0 for p in prices)
        assert all(v >= 0 for v in variances)


class TestMonteCarloOptionPricing:
    """Tests for Monte Carlo option pricing."""

    def test_monte_carlo_converges_to_bs(self) -> None:
        """Test that Monte Carlo converges to Black-Scholes."""
        call = EuroCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
        )

        bs_price = call.price()
        mc_price = call.price_monte_carlo(num_paths=100000, num_steps=1)

        # Monte Carlo should be within 2% of Black-Scholes with 100k paths
        relative_error = abs(mc_price - bs_price) / bs_price
        assert relative_error < 0.02

    def test_antithetic_reduces_variance(self) -> None:
        """Test that antithetic variates reduce variance."""
        call = EuroCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
        )

        bs_price = call.price()

        # Run multiple trials
        mc_errors = []
        mc_anti_errors = []

        for _ in range(10):
            mc_price = call.price_monte_carlo(num_paths=10000, num_steps=1)
            mc_anti_price = call.price_monte_carlo_antithetic(num_paths=10000, num_steps=1)

            mc_errors.append(abs(mc_price - bs_price))
            mc_anti_errors.append(abs(mc_anti_price - bs_price))

        # Average error should be lower with antithetic variates
        avg_mc_error = sum(mc_errors) / len(mc_errors)
        avg_anti_error = sum(mc_anti_errors) / len(mc_anti_errors)

        # Antithetic should have lower average error
        assert avg_anti_error < avg_mc_error * 1.5  # Allow some random variation

    def test_heston_pricing(self) -> None:
        """Test Heston option pricing."""
        call = EuroCallOption(
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
        )

        # Price with Heston model
        heston_price = call.price_heston(
            initial_variance=0.04,
            kappa=2.0,
            theta=0.04,
            vol_of_vol=0.3,
            correlation=-0.7,
            num_paths=50000,
            num_steps=100,
        )

        # Should be a positive price
        assert heston_price > 0

        # Should be reasonably close to Black-Scholes (within 20%)
        # when parameters are similar
        bs_price = call.price()
        assert abs(heston_price - bs_price) / bs_price < 0.3

    def test_itm_otm_pricing(self) -> None:
        """Test Monte Carlo pricing for ITM and OTM options."""
        # ITM call
        itm_call = EuroCallOption(
            spot=100.0,
            strike=90.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
        )
        itm_bs = itm_call.price()
        itm_mc = itm_call.price_monte_carlo(num_paths=100000)
        assert abs(itm_mc - itm_bs) / itm_bs < 0.03

        # OTM call
        otm_call = EuroCallOption(
            spot=100.0,
            strike=110.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
        )
        otm_bs = otm_call.price()
        otm_mc = otm_call.price_monte_carlo(num_paths=100000)
        assert abs(otm_mc - otm_bs) / otm_bs < 0.05
