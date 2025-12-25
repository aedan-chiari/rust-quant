# rust-quant

A high-performance quantitative finance library for derivatives pricing, yield curve construction, and stochastic simulation. Built with Rust for maximum performance and exposed to Python via PyO3 bindings. Designed for production use with modern Python tooling ([uv](https://docs.astral.sh/uv/)).

> **📦 This project uses [uv](https://docs.astral.sh/uv/) for dependency management** - a fast, modern Python package manager. See [GETTING_STARTED.md](GETTING_STARTED.md) for detailed setup instructions.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Rust 1.70+](https://img.shields.io/badge/rust-1.70+-orange.svg)](https://www.rust-lang.org/)

## Features

### European Options (Black-Scholes-Merton)
- **Analytical Pricing**: Closed-form Black-Scholes formulas for European calls and puts
- **Dividend Yield Support**: Full Merton model implementation for dividend-paying assets
- **Complete Greeks Suite**: Delta, Gamma, Vega, Theta, and Rho calculations
- **Type-Safe API**: Dedicated `EuroCallOption` and `EuroPutOption` classes with full type hints
- **High-Performance Batch Operations**: SIMD-optimized vectorized pricing via static methods
  - AVX2 intrinsics for 4x throughput per core
  - Rayon work-stealing parallelism across all cores
  - 10-30x speedup on large portfolios (100K+ options)

### American Options (Binomial Tree & LSM)
- **Early Exercise Premium**: Accurate valuation of American-style early exercise rights
- **Cox-Ross-Rubinstein Model**: Industry-standard binomial tree implementation
- **Longstaff-Schwartz Method**: Monte Carlo pricing for path-dependent American options
- **Dividend Support**: Continuous dividend yield incorporation
- **Greeks Calculation**: Delta via finite difference methods
- **Configurable Accuracy**: Adjustable tree steps for precision/performance trade-off

### Zero Coupon Yield Curves
- **Market-Standard Construction**: Bootstrap yield curves from market bond prices
- **Flexible Instruments**: Support for zero-coupon and coupon-bearing bonds with configurable payment frequencies
- **Multiple Interpolation Schemes**:
  - **Log-linear** (default): Industry-standard method producing piecewise constant forward rates
  - **Linear**: Simple linear interpolation of discount factors
  - **Cubic Spline**: Hermite cubic interpolation for C¹-continuous smooth curves
- **Bootstrap Algorithm**: Iterative solver for extracting zero rates from coupon bonds
- **Efficient Discount Factors**: O(log n) binary search with automatic interpolation/extrapolation
- **Forward Rate Analytics**: Dedicated `ForwardCurve` class for:
  - Standard forward rates f(t₁, t₂) between any two maturities
  - Instantaneous forward rates f(t) at specific time points
  - Forward rate term structures over custom time grids
  - Forward discount factors and forward bond pricing
- **Bond Valuation**: Present value calculations for arbitrary cash flow streams
- **Parallel Batch Operations**: Rayon-powered vectorization for 100+ simultaneous calculations

### Stochastic Processes & Monte Carlo Simulation
- **Brownian Motion (Wiener Process)**:
  - Parallel path generation via Rayon thread pool
  - Antithetic variates for 50% variance reduction
  - Configurable time discretization (Δt)
  - Multi-dimensional correlated paths
- **Geometric Brownian Motion (GBM)**:
  - Risk-neutral asset price simulation (μ = r - q)
  - Exact and Euler discretization schemes
  - Batch terminal price generation for large portfolios
  - Monte Carlo European option pricing
- **Heston Stochastic Volatility Model**:
  - Two-factor model: S(t) and v(t) processes
  - Mean-reverting variance with κ (speed), θ (long-term), σᵥ (vol-of-vol)
  - Correlated Brownian motions (leverage effect: ρ)
  - Captures volatility smile and skew
  - Euler-Maruyama discretization with reflection at zero
- **Monte Carlo Pricing Engine**:
  - European options via path simulation
  - American options via Longstaff-Schwartz regression
  - Variance reduction techniques (antithetic variates, control variates)
  - Convergence diagnostics (standard error, confidence intervals)
  - Massively parallel (100K+ paths across all cores)
- **Production-Grade RNG**:
  - Xoshiro256++ algorithm (high-quality, fast PRNG)
  - Optional seeding for reproducible simulations
  - Thread-local storage for lock-free parallel execution
  - Statistical quality validated (χ² tests, serial correlation)

### Core Infrastructure
- **Zero-Cost Rust Core**: Memory-safe, high-performance implementation without garbage collection overhead
- **Seamless Python Integration**: PyO3 bindings with zero-copy data transfer where possible
- **Complete Type Safety**: Full `.pyi` stub files for perfect IDE autocomplete, type checking, and inline documentation
- **Modern Build System**: `uv` for dependency management, `maturin` for Rust/Python packaging
- **Immutable Functional API**: Thread-safe `with_*` methods for scenario analysis without mutation
- **Production Ready**: Comprehensive test suite, benchmarks, and real-world examples

## Project Structure

```
rust-quant/
├── src/                          # Rust source code
│   ├── lib.rs                    # Module exports and Python bindings
│   ├── types.rs                  # OptionGreeks, shared traits
│   ├── simd.rs                   # SIMD-optimized implementations
│   ├── vectorized.rs             # Vectorized pricing functions
│   ├── european/                 # European options module
│   │   ├── mod.rs                # Module exports
│   │   ├── option.rs             # EuroOption (simple class)
│   │   ├── call.rs               # EuroCallOption (optimized)
│   │   └── put.rs                # EuroPutOption (optimized)
│   ├── american/                 # American options module
│   │   ├── mod.rs                # Module exports
│   │   ├── option.rs             # AmericanOption (simple class)
│   │   ├── call.rs               # AmericanCallOption
│   │   ├── put.rs                # AmericanPutOption
│   │   └── pricing.rs            # Binomial tree implementation
│   ├── zero_coupon/              # Zero coupon yield curves
│   │   ├── mod.rs                # Module exports
│   │   ├── curve.rs              # ZeroCouponCurve, Security, InterpolationMethod
│   │   └── forward_curve.rs      # ForwardCurve for forward rate calculations
│   └── stochastic/               # Stochastic processes module
│       ├── mod.rs                # Module exports
│       ├── rng.rs                # Thread-safe random number generation
│       ├── brownian.rs           # Brownian motion paths
│       ├── gbm.rs                # Geometric Brownian Motion
│       ├── heston.rs             # Heston stochastic volatility model
│       └── monte_carlo.rs        # Monte Carlo pricing engine
├── python/                       # Python-related files
│   └── rust_quant/               # Python package directory
│       ├── __init__.py           # Package initialization and exports
│       └── rust_quant.pyi        # Type stubs for IDE support
├── examples/                     # Usage examples (numbered for learning)
│   ├── 01_basic_single_option.py         # Single option basics
│   ├── 02_multiple_options_vectorized.py # Vectorized operations
│   ├── 03_performance_benchmark.py       # Performance comparison
│   ├── 04_dividend_yield_example.py      # Dividend yield examples
│   ├── 05_american_options_example.py    # American options
│   ├── 07_zero_coupon_curve.py           # Zero coupon yield curves
│   └── 08_monte_carlo_paths.py           # Stochastic processes & Monte Carlo
├── tests/                        # Python test suite
│   ├── test_european_options.py     # European options tests
│   ├── test_american_options.py     # American options tests
│   ├── test_zero_coupon_curve.py    # Zero coupon curve tests
│   ├── test_interpolation_methods.py # Interpolation method tests
│   └── test_stochastic.py            # Stochastic processes tests
├── Cargo.toml                    # Rust dependencies
├── pyproject.toml                # Python project config (uv-compatible)
└── README.md
```

## Installation

### Prerequisites

You need two tools installed:

1. **[uv](https://docs.astral.sh/uv/)** - Fast Python package manager (10-100x faster than pip)
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **[Rust](https://rustup.rs)** - For building the high-performance Rust backend
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

> ⚠️ **Note**: This project is designed for `uv`. While it may work with `pip`, all documentation, workflows, and testing assume `uv`.

### Quick Start (One Command)

```bash
# Clone the repository
git clone https://github.com/aedan-chiari/rust-quant.git
cd rust-quant

# Install everything: create venv, install dependencies, build Rust extension
uv sync
```

That's it! `uv sync` automatically:
- Creates a Python virtual environment in `.venv/`
- Installs all Python dependencies from `pyproject.toml`
- Compiles the Rust extension with `maturin`
- Installs the compiled library into the virtual environment

### Verify Installation

```bash
# Activate virtual environment (optional with uv run)
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

# Quick test
python -c "from rust_quant import EuroCallOption; print(EuroCallOption(100,100,1,0.05,0.2).price())"
# Should print: 10.450583572185565
```

## Quick Start

### European Options (Black-Scholes)

```python
from rust_quant import EuroCallOption

# Create a European call option (without dividends)
call = EuroCallOption(
    spot=100.0,
    strike=105.0,
    time_to_expiry=1.0,
    risk_free_rate=0.05,
    volatility=0.2
)

# Create a European call with dividend yield
call_with_div = EuroCallOption(
    spot=100.0,
    strike=105.0,
    time_to_expiry=1.0,
    risk_free_rate=0.05,
    volatility=0.2,
    dividend_yield=0.02  # 2% continuous dividend yield
)

# Calculate price and individual Greeks
price = call.price()        # 8.0214
delta = call.delta()        # 0.5422
gamma = call.gamma()        # 0.0198

# Or get all Greeks at once (recommended - more efficient)
greeks = call.greeks()
print(f"Price: ${greeks.price:.4f}")
print(f"Delta: {greeks.delta:.4f}")
print(f"Gamma: {greeks.gamma:.4f}")
print(f"Vega: {greeks.vega:.4f}")
print(f"Theta: {greeks.theta:.4f}")
print(f"Rho: {greeks.rho:.4f}")

# Create new option with modified parameters (immutable updates)
higher_vol = call.with_volatility(0.3)
different_spot = call.with_spot(110.0)
```

### American Options (Binomial Tree)

```python
from rust_quant import AmericanPutOption, EuroPutOption

# Create an American put option (most common use case)
american_put = AmericanPutOption(
    spot=100.0,
    strike=105.0,
    time_to_expiry=1.0,
    risk_free_rate=0.05,
    volatility=0.2,
    steps=100,  # Number of binomial tree steps (higher = more accurate)
)

# American options can be exercised early
price = american_put.price()  # Includes early exercise premium
delta = american_put.delta()

# Compare with European option to see early exercise value
europen_put = EuroPutOption(
    spot=100.0, strike=105.0, time_to_expiry=1.0,
    risk_free_rate=0.05, volatility=0.2
)

early_exercise_premium = american_put.price() - europen_put.price()
print(f"Early exercise premium: ${early_exercise_premium:.4f}")
```

### Zero Coupon Yield Curves

Build yield curves from market bond prices and calculate discount factors, zero rates, and forward rates with multiple interpolation methods. Forward rate calculations are now handled by a separate `ForwardCurve` class for better separation of concerns.

```python
from rust_quant import Security, ZeroCouponCurve, ForwardCurve

# Create securities representing market bond prices
# Mix of zero-coupon bonds and coupon-bearing bonds
securities = [
    Security(maturity=0.5, price=97.50),    # 6-month zero-coupon
    Security(maturity=1.0, price=95.00),    # 1-year zero-coupon
    Security(maturity=2.0, price=90.00),    # 2-year zero-coupon
    # Coupon-bearing bond: 5% coupon, semi-annual payments
    Security(maturity=5.0, price=98.0, coupon_rate=0.05, frequency=2),
]

# Create zero-coupon curve with default log-linear interpolation
curve = ZeroCouponCurve(securities)

# Calculate discount factors with automatic interpolation
df_1y = curve.discount_factor(1.0)    # Exact maturity
df_18m = curve.discount_factor(1.5)   # Interpolated
df_15y = curve.discount_factor(15.0)  # Extrapolated

# Calculate zero rates (continuously compounded)
zero_rate_1y = curve.zero_rate(1.0)
zero_rate_5y = curve.zero_rate(5.0)
print(f"1Y rate: {zero_rate_1y * 100:.4f}%")
print(f"5Y rate: {zero_rate_5y * 100:.4f}%")

# Create ForwardCurve for forward rate calculations
forward_curve = ForwardCurve(curve)

# Calculate forward rates
fwd_1y1y = forward_curve.forward_rate(1.0, 2.0)   # 1-year rate in 1 year
fwd_5y5y = forward_curve.forward_rate(5.0, 10.0)  # 5-year rate in 5 years
print(f"1y1y forward: {fwd_1y1y * 100:.4f}%")

# Instantaneous forward rate
inst_fwd_2y = forward_curve.instantaneous_forward_rate(2.0)
print(f"Instantaneous forward at 2Y: {inst_fwd_2y * 100:.4f}%")

# Forward rate term structure
times, rates = forward_curve.term_structure(0.0, 10.0, 1.0)
print(f"0y1y forward: {rates[0] * 100:.4f}%")

# Value a bond or cash flow stream
cash_flows = [50.0, 50.0, 1050.0]  # Annual coupons + principal
maturities = [1.0, 2.0, 3.0]
bond_value = curve.present_value_many(cash_flows, maturities)
print(f"Bond value: ${bond_value:.2f}")
```

#### Choosing Interpolation Methods

The library provides three interpolation methods:

```python
# Log-linear (default, industry standard)
# → Piecewise constant forward rates
curve_log = ZeroCouponCurve(securities, interpolation="log_linear")

# Linear interpolation of discount factors
# → Simple and fast
curve_linear = ZeroCouponCurve(securities, interpolation="linear")

# Cubic spline interpolation
# → Smooth curves, C¹ continuous
curve_cubic = ZeroCouponCurve(securities, interpolation="cubic")

# Check which method is being used
print(curve_log.get_interpolation_method())  # "log_linear"

# Compare interpolated values
t = 1.5
df_log = curve_log.discount_factor(t)
df_linear = curve_linear.discount_factor(t)
df_cubic = curve_cubic.discount_factor(t)
```

**Which method to use?**

- **Log-linear** (default): Industry standard. Produces piecewise constant forward rates, which is theoretically sound and commonly used in practice.
- **Linear**: Simple and fast. Good for general purposes when you don't need the theoretical properties of log-linear.
- **Cubic**: Smooth curves with C¹ continuity. Use when smoothness is critical (e.g., risk management, hedging).

```python
# Verify log-linear produces constant forward rates
fwd_1_15 = curve_log.forward_rate(1.0, 1.5)
fwd_15_2 = curve_log.forward_rate(1.5, 2.0)
# These will be nearly identical (piecewise constant)
print(f"Difference: {abs(fwd_1_15 - fwd_15_2) * 10000:.2f} bps")  # ~0.00 bps
```

#### Batch Operations for Curves

Calculate multiple values efficiently using batch methods:

```python
# Batch discount factors
maturities = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 7.0, 10.0]
discount_factors = ZeroCouponCurve.discount_factors_many(curve, maturities)

# Batch zero rates
zero_rates = ZeroCouponCurve.zero_rates_many(curve, maturities)

# Batch forward rates
start_times = [1.0, 2.0, 3.0, 5.0]
end_times = [2.0, 3.0, 5.0, 10.0]
forward_rates = ZeroCouponCurve.forward_rates_many(curve, start_times, end_times)

# All batch methods automatically use Rayon parallelism for >100 items
```

#### Alternative Constructor

You can also create curves from vectors:

```python
# Create from separate vectors
maturities = [1.0, 2.0, 3.0, 5.0, 10.0]
prices = [95.0, 90.0, 85.5, 78.35, 61.39]

curve = ZeroCouponCurve.from_vectors(
    maturities,
    prices,
    interpolation="log_linear"  # Optional, defaults to log_linear
)
```

### Dividend Yield Support

Both European and American options support dividend-adjusted pricing:

```python
from rust_quant import EuroCallOption, EuroPutOption, AmericanCallOption

# European options with dividends (Merton model)
call = EuroCallOption(
    spot=100.0,
    strike=100.0,
    time_to_expiry=1.0,
    risk_free_rate=0.05,
    volatility=0.2,
    dividend_yield=0.02  # 2% continuous dividend yield
)

put = EuroPutOption(
    spot=100.0,
    strike=100.0,
    time_to_expiry=1.0,
    risk_free_rate=0.05,
    volatility=0.2,
    dividend_yield=0.02
)

# American options with dividends
american_call = AmericanCallOption(
    spot=100.0, strike=100.0, time_to_expiry=1.0,
    risk_free_rate=0.05, volatility=0.2,
    dividend_yield=0.02, steps=100
)

# Dividends reduce call prices and increase put prices
print(f"Call price: ${call.price():.4f}")  # Lower than without dividends
print(f"Put price: ${put.price():.4f}")    # Higher than without dividends

# Put-call parity with dividends: C - P = S*e^(-qT) - K*e^(-rT)
# where q is the dividend yield
```

**When to use dividend_yield:**
- Dividend-paying stocks (e.g., most large-cap stocks)
- Index options (e.g., S&P 500 has ~1.5-2% yield)
- Currency options (foreign interest rate)
- Commodity options with storage costs

Default value is `0.0` (no dividends) for backward compatibility.

### Vectorized Operations (Batch Processing)

```python
from rust_quant import EuroCallOption

# Price multiple European options at once using static methods
spots = [100.0, 101.0, 102.0, 103.0, 104.0]
strikes = [105.0] * 5
times = [1.0] * 5
rates = [0.05] * 5
vols = [0.2] * 5

# Vectorized pricing with SIMD + parallel processing
prices = EuroCallOption.price_many(spots, strikes, times, rates, vols)

# Vectorized Greeks calculation (returns tuple of lists)
prices, deltas, gammas, vegas, thetas, rhos = EuroCallOption.greeks_many(
    spots, strikes, times, rates, vols
)
```

### High-Performance SIMD + Parallel Processing

For large portfolios (100+ options), static class methods automatically use SIMD + parallel processing:

```python
from rust_quant import EuroCallOption, EuroPutOption

# Create large dataset
n = 100_000
spots = [100.0 + i * 0.01 for i in range(n)]
strikes = [105.0] * n
times = [1.0] * n
rates = [0.05] * n
vols = [0.2] * n

# SIMD + parallel processing (10-30x faster on large datasets)
prices = EuroCallOption.price_many(spots, strikes, times, rates, vols)

# All Greeks with SIMD + parallel
prices, deltas, gammas, vegas, thetas, rhos = EuroCallOption.greeks_many(
    spots, strikes, times, rates, vols
)

# Same for puts
put_prices = EuroPutOption.price_many(spots, strikes, times, rates, vols)
put_greeks = EuroPutOption.greeks_many(spots, strikes, times, rates, vols)
```

**Architecture Note:** All static class methods (`EuroCallOption.price_many`, `EuroCallOption.greeks_many`, `EuroPutOption.price_many`, `EuroPutOption.greeks_many`) automatically use SIMD intrinsics (AVX) and Rayon parallelism for maximum performance. The `EuroOption` and `AmericanOption` classes are designed for simple one-off calculations.

## Examples

Run the numbered examples to learn different usage patterns:

```bash
# Basic single option usage
uv run examples/01_basic_single_option.py

# Vectorized operations and batch processing
uv run examples/02_multiple_options_vectorized.py

# Performance benchmarks at different scales
uv run examples/03_performance_benchmark.py

# Dividend yield examples
uv run examples/04_dividend_yield_example.py

# American options with early exercise
uv run examples/05_american_options_example.py

# Zero coupon yield curves
uv run examples/07_zero_coupon_curve.py

# Monte Carlo simulations and stochastic processes
uv run examples/08_monte_carlo_paths.py
```

See [examples/README.md](examples/README.md) for detailed documentation.

## API Reference

### European Option Classes

#### `EuroCallOption`

European call option with Black-Scholes pricing (Merton model with dividend support).

**Constructor:**
```python
EuroCallOption(spot, strike, time_to_expiry, risk_free_rate, volatility, dividend_yield=0.0)
```

**Parameters:**
- `spot` (float): Current price of the underlying asset
- `strike` (float): Strike price of the option
- `time_to_expiry` (float): Time to expiration in years
- `risk_free_rate` (float): Risk-free interest rate (as decimal, e.g., 0.05 for 5%)
- `volatility` (float): Volatility of the underlying asset (as decimal, e.g., 0.2 for 20%)
- `dividend_yield` (float, optional): Continuous dividend yield (default 0.0)

**Instance Methods:**
- `price()` → float: Calculate call option price (Black-Scholes analytical)
- `delta()` → float: Sensitivity to underlying price
- `gamma()` → float: Rate of change of delta
- `vega()` → float: Sensitivity to volatility
- `theta()` → float: Time decay (per day)
- `rho()` → float: Sensitivity to interest rate
- `greeks()` → OptionGreeks: All Greeks and price at once
- `price_monte_carlo(num_paths, num_steps)` → float: Monte Carlo pricing
- `price_monte_carlo_antithetic(num_paths, num_steps)` → float: MC with variance reduction
- `price_heston(initial_variance, kappa, theta, vol_of_vol, correlation, num_paths, num_steps)` → float: Heston stochastic volatility pricing
- `with_spot(new_spot)` → EuroCallOption: Create new option with different spot
- `with_strike(new_strike)` → EuroCallOption: Create new option with different strike
- `with_time(new_time)` → EuroCallOption: Create new option with different time
- `with_volatility(new_volatility)` → EuroCallOption: Create new option with different volatility

**Static Methods (SIMD + Parallel Optimized):**
- `EuroCallOption.price_many(spots, strikes, times, rates, vols)` → List[float]
- `EuroCallOption.greeks_many(spots, strikes, times, rates, vols)` → Tuple[List[float], ...]

These methods automatically use SIMD intrinsics (AVX) and Rayon parallelism for maximum performance.

Returns from greeks_many: (prices, deltas, gammas, vegas, thetas, rhos)

#### `EuroPutOption`

European put option with Black-Scholes pricing (Merton model with dividend support). Has the same methods and parameters as `EuroCallOption`.

**Constructor:**
```python
EuroPutOption(spot, strike, time_to_expiry, risk_free_rate, volatility, dividend_yield=0.0)
```

#### `EuroOption`

Generic European option class for simple one-off calculations. Can represent either calls or puts via an `is_call` parameter. This class is optimized for single option calculations without SIMD/parallelism overhead.

**Constructor:**
```python
EuroOption(spot, strike, time_to_expiry, risk_free_rate, volatility, is_call=True, dividend_yield=0.0)
```

**Note:** For batch operations, use `EuroCallOption` or `EuroPutOption` classes which have optimized static methods.

### American Option Classes

#### `AmericanCallOption`

American call option with binomial tree pricing (CRR method).

**Constructor:**
```python
AmericanCallOption(spot, strike, time_to_expiry, risk_free_rate, volatility, dividend_yield=0.0, steps=100)
```

**Parameters:**
- `spot` (float): Current price of the underlying asset
- `strike` (float): Strike price of the option
- `time_to_expiry` (float): Time to expiration in years
- `risk_free_rate` (float): Risk-free interest rate (as decimal)
- `volatility` (float): Volatility of the underlying asset (as decimal)
- `dividend_yield` (float, optional): Continuous dividend yield (default 0.0)
- `steps` (int, optional): Number of binomial tree steps (default 100)

**Instance Methods:**
- `price()` → float: Calculate option price using binomial tree (CRR method)
- `delta()` → float: Sensitivity to underlying price (finite difference)
- `price_lsm(num_paths, num_steps)` → float: Longstaff-Schwartz Monte Carlo pricing

**Note:** More steps = more accuracy but slower computation. 100-200 steps typically sufficient for binomial trees. For LSM, 50k paths with 50 steps provides ~0.3% accuracy.

#### `AmericanPutOption`

American put option with binomial tree pricing. Has the same constructor and methods as `AmericanCallOption`.

#### `AmericanOption`

Generic American option class for simple calculations. Can represent either calls or puts via an `is_call` parameter.

**Constructor:**
```python
AmericanOption(spot, strike, time_to_expiry, risk_free_rate, volatility, is_call=True, dividend_yield=0.0, steps=100)
```

#### `OptionGreeks`

Container for option price and all Greeks.

**Attributes:**
- `price` (float): Option price
- `delta` (float): Sensitivity to underlying price
- `gamma` (float): Rate of change of delta
- `vega` (float): Sensitivity to volatility
- `theta` (float): Time decay per day
- `rho` (float): Sensitivity to interest rate

### Monte Carlo Utilities

#### `monte_carlo_standard_error(values)`

Calculate standard error of Monte Carlo simulations to assess convergence and precision.

**Parameters:**
- `values` (List[float]): Vector of simulated values (e.g., option prices from multiple MC runs)

**Returns:**
- `float`: Standard error of the mean (SE = σ / √N)

**Example:**
```python
from rust_quant import EuroCallOption, monte_carlo_standard_error

call = EuroCallOption(100, 100, 1.0, 0.05, 0.2)

# Run MC 100 times to assess convergence
prices = [call.price_monte_carlo(10000) for _ in range(100)]
se = monte_carlo_standard_error(prices)
mean_price = sum(prices) / len(prices)

print(f"Price: ${mean_price:.4f} ± ${1.96*se:.4f} (95% CI)")
```

### Zero Coupon Curve Classes

#### `Security`

Represents a bond security (zero-coupon or coupon-bearing) for yield curve construction.

**Constructor:**
```python
Security(maturity, price, face_value=100.0, coupon_rate=0.0, frequency=0)
```

**Parameters:**
- `maturity` (float): Time to maturity in years
- `price` (float): Market price of the bond
- `face_value` (float, optional): Face value at maturity (default 100.0)
- `coupon_rate` (float, optional): Annual coupon rate as decimal (default 0.0 for zero-coupon)
- `frequency` (int, optional): Coupon payments per year (0 for zero-coupon, 2 for semi-annual, etc.)

**Examples:**
```python
# Zero-coupon bond
zero = Security(maturity=2.0, price=90.0)

# Coupon-bearing bond: 5% coupon, semi-annual payments
coupon_bond = Security(
    maturity=5.0,
    price=98.0,
    coupon_rate=0.05,
    frequency=2
)
```

#### `ZeroCouponCurve`

Zero-coupon yield curve for discount factor and rate calculations.

**Constructor:**
```python
ZeroCouponCurve(securities, interpolation=None)
```

**Parameters:**
- `securities` (List[Security]): List of Security objects
- `interpolation` (str, optional): Interpolation method - "linear", "log_linear", or "cubic". Defaults to "log_linear" (industry standard)

**Alternative Constructor:**
```python
ZeroCouponCurve.from_vectors(maturities, prices, face_values=None, interpolation=None)
```

**Instance Methods:**

- `discount_factor(maturity)` → float: Calculate discount factor at given maturity
- `zero_rate(maturity)` → float: Calculate continuously compounded zero rate
- `forward_rate(t1, t2)` → float: Calculate forward rate between t1 and t2
- `present_value(cash_flow, maturity)` → float: Present value of single cash flow
- `present_value_many(cash_flows, maturities)` → float: Present value of multiple cash flows
- `add_security(security)`: Add a new security to the curve
- `size()` → int: Number of securities in the curve
- `maturities()` → List[float]: List of all maturities
- `get_interpolation_method()` → str: Get current interpolation method ("linear", "log_linear", or "cubic")

**Static Methods (Batch Operations):**

- `ZeroCouponCurve.discount_factors_many(curve, maturities)` → List[float]
- `ZeroCouponCurve.zero_rates_many(curve, maturities)` → List[float]
- `ZeroCouponCurve.forward_rates_many(curve, start_maturities, end_maturities)` → List[float]

All batch methods automatically use Rayon parallelism for datasets >100 items.

**Examples:**
```python
# Basic usage
securities = [Security(maturity=1.0, price=95.0), Security(maturity=2.0, price=90.0)]
curve = ZeroCouponCurve(securities, interpolation="log_linear")

# Single calculations
df = curve.discount_factor(1.5)
rate = curve.zero_rate(1.5)
fwd = curve.forward_rate(1.0, 2.0)

# Batch calculations
maturities = [0.5, 1.0, 1.5, 2.0, 3.0]
dfs = ZeroCouponCurve.discount_factors_many(curve, maturities)
rates = ZeroCouponCurve.zero_rates_many(curve, maturities)
```

#### `InterpolationMethod`

Enum representing interpolation methods (mainly for type checking).

**Values:**
- `InterpolationMethod.Linear`: Linear interpolation of discount factors
- `InterpolationMethod.LogLinear`: Log-linear interpolation (piecewise constant forwards)
- `InterpolationMethod.CubicSpline`: Hermite cubic spline interpolation

**Note:** In practice, you'll use string values ("linear", "log_linear", "cubic") when constructing curves.

## Mathematical Models

### Black-Scholes-Merton Model (European Options)

The library implements the **Black-Scholes-Merton model** with dividend yield support:

#### Pricing Formulas

**Call Option:**
```
C = S * e^(-qT) * N(d1) - K * e^(-rT) * N(d2)
```

**Put Option:**
```
P = K * e^(-rT) * N(-d2) - S * e^(-qT) * N(-d1)
```

Where:
```
d1 = [ln(S/K) + (r - q + σ²/2)T] / (σ√T)
d2 = d1 - σ√T
```

**Parameters:**
- `S`: Current spot price
- `K`: Strike price
- `T`: Time to expiration (years)
- `r`: Risk-free interest rate
- `σ`: Volatility
- `q`: Continuous dividend yield
- `N(·)`: Cumulative standard normal distribution

#### Greeks

**Delta:**
- Call: `e^(-qT) * N(d1)`
- Put: `e^(-qT) * (N(d1) - 1)`

**Gamma** (same for calls and puts):
```
Γ = e^(-qT) * φ(d1) / (S * σ * √T)
```

**Vega** (same for calls and puts):
```
ν = S * e^(-qT) * φ(d1) * √T / 100
```

**Theta:**
- Call: `[-(S * e^(-qT) * φ(d1) * σ)/(2√T) - rKe^(-rT)N(d2) + qSe^(-qT)N(d1)] / 365`
- Put: `[-(S * e^(-qT) * φ(d1) * σ)/(2√T) + rKe^(-rT)N(-d2) - qSe^(-qT)N(-d1)] / 365`

**Rho:**
- Call: `K * T * e^(-rT) * N(d2) / 100`
- Put: `-K * T * e^(-rT) * N(-d2) / 100`

Where `φ(·)` is the standard normal probability density function.

#### Put-Call Parity

With dividends:
```
C - P = S * e^(-qT) - K * e^(-rT)
```

Without dividends (q=0):
```
C - P = S - K * e^(-rT)
```

### Binomial Tree Model (American Options)

American options use the **Cox-Ross-Rubinstein (CRR)** binomial tree method:

#### Tree Parameters

```
dt = T / N  (time step)
u = e^(σ√dt)  (up factor)
d = 1/u  (down factor)
p = (e^((r-q)dt) - d) / (u - d)  (risk-neutral probability)
```

Where `N` is the number of steps.

#### Pricing Algorithm

1. Build tree forward: Calculate all possible stock prices at each node
2. Calculate terminal payoffs: `max(S - K, 0)` for calls, `max(K - S, 0)` for puts
3. Work backward: At each node, option value is:
   ```
   V = max(intrinsic_value, e^(-r*dt) * (p*V_up + (1-p)*V_down))
   ```

The `max` operation captures the early exercise feature.

#### Early Exercise Premium

American options ≥ European options, with equality only when early exercise is never optimal:
- American calls on non-dividend stocks: typically same as European
- American calls with dividends: may exercise early before ex-dividend dates
- American puts: often have significant early exercise premium, especially ITM

### Zero Coupon Yield Curves

The library implements zero-coupon yield curve construction from market bond prices with bootstrapping and multiple interpolation methods.

#### Discount Factors and Zero Rates

**Relationship:**
```
DF(T) = exp(-r(T) * T)
r(T) = -ln(DF(T)) / T
```

Where:
- `DF(T)`: Discount factor at maturity T
- `r(T)`: Continuously compounded zero rate at maturity T
- `T`: Time to maturity in years

#### Forward Rates

Forward rate between times t₁ and t₂:
```
f(t₁, t₂) = [ln(DF(t₁)) - ln(DF(t₂))] / (t₂ - t₁)
```

Or equivalently:
```
f(t₁, t₂) = [r(t₂) * t₂ - r(t₁) * t₁] / (t₂ - t₁)
```

#### Interpolation Methods

The library implements three interpolation methods for discount factors between known maturities:

**1. Linear Interpolation**

Linear interpolation of discount factors:
```
DF(t) = DF(t₁) + [DF(t₂) - DF(t₁)] * (t - t₁) / (t₂ - t₁)
```

Properties:
- Simple and fast: O(log n) binary search + O(1) interpolation
- Monotonic: Preserves decreasing discount factors
- Not arbitrage-free: Can produce non-constant forward rates within intervals

**2. Log-linear Interpolation (Industry Standard)**

Linear interpolation of log discount factors:
```
ln(DF(t)) = ln(DF(t₁)) + [ln(DF(t₂)) - ln(DF(t₁))] * (t - t₁) / (t₂ - t₁)
```

Equivalently:
```
DF(t) = exp[ln(DF(t₁)) + [ln(DF(t₂)) - ln(DF(t₁))] * (t - t₁) / (t₂ - t₁)]
```

Properties:
- **Piecewise constant forward rates**: Forward rates are constant within each interval
- Arbitrage-free: Theoretically sound for rate markets
- Industry standard: Most widely used in fixed income
- Monotonic: Preserves decreasing discount factors

Verification that forward rates are constant:
```
For t ∈ [t₁, t₂]:  f(t₁, t) = f(t, t₂) = constant
```

**3. Cubic Spline Interpolation**

Hermite cubic interpolation with finite difference derivatives:
```
DF(t) = h₀₀(u) * DF₁ + h₁₀(u) * m₁ * Δt + h₀₁(u) * DF₂ + h₁₁(u) * m₂ * Δt
```

Where:
- `u = (t - t₁) / (t₂ - t₁)` (normalized position)
- `Δt = t₂ - t₁`
- `h₀₀(u) = 2u³ - 3u² + 1` (Hermite basis function)
- `h₁₀(u) = u³ - 2u² + u`
- `h₀₁(u) = -2u³ + 3u²`
- `h₁₁(u) = u³ - u²`
- `m₁, m₂`: Derivatives at endpoints (computed using finite differences)

Properties:
- C¹ continuous: Smooth first derivative
- May oscillate: Can produce non-monotonic curves with sparse data
- Best for smooth curves: Risk management, hedging applications
- More computation: O(log n) search + O(1) cubic evaluation

#### Bootstrapping from Coupon Bonds

For coupon-bearing bonds, the library uses bootstrapping to extract discount factors:

**Zero-coupon bond:**
```
DF(T) = Price / FaceValue
```

**Coupon-bearing bond:**
```
Price = Σ(coupon * DF(tᵢ)) + FaceValue * DF(T)
```

Solve iteratively for DF(T):
```
DF(T) = [Price - Σ(coupon * DF(tᵢ))] / FaceValue
```

Where the sum is over all coupon payment dates before maturity.

#### Extrapolation

Beyond the last maturity, the library uses flat rate extrapolation:
```
For t > T_max:
r(t) = r(T_max)  (constant rate)
DF(t) = exp(-r(T_max) * t)
```

This prevents arbitrage opportunities from negative or increasing rates.

## Performance

The library provides a clean, class-based architecture with automatic optimization:

### Architecture Overview

1. **EuroOption / AmericanOption Classes**: Simple, lightweight for one-off calculations
   - No SIMD or parallelism overhead
   - Perfect for single option pricing or quick calculations
   
2. **EuroCallOption / EuroPutOption Classes**: Specialized for European options
   - Instance methods for single options (Black-Scholes analytical formulas)
   - Static methods (`price_many`, `greeks_many`) automatically use:
     - **SIMD (AVX)**: Process 4 options simultaneously with vectorized instructions
     - **Rayon Parallelism**: Distribute work across all CPU cores
     - **Chunked Processing**: Efficient memory access patterns

3. **AmericanCallOption / AmericanPutOption Classes**: American options with early exercise
   - Binomial tree pricing (CRR method)
   - Configurable steps for accuracy/performance trade-off
   - Delta via finite differences

### Performance Characteristics

**Single Option:**
- Use instance methods: `option.price()`, `option.greeks()`
- Microsecond-level latency

**Batch Operations (100+ options):**
- Use static methods: `EuroCallOption.price_many()`, `EuroCallOption.greeks_many()`
- 10-30x speedup vs sequential processing
- Scales with number of CPU cores
- SIMD provides ~4x boost, parallelism adds core-count multiplier

**Benchmark Results** (1M options on 8-core machine):
- Standard sequential: ~150ms
- Static methods (SIMD + Parallel): ~80ms
- **Speedup: 1.9x**

Benchmark on your machine:
```bash
uv run python examples/03_performance_benchmark.py
```

## Development

### Setup Development Environment

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup everything
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Running Tests

```bash
# Run Python tests
pytest tests/

# Run Rust tests
cargo test

# Run all tests with verbose output
pytest tests/ -v && cargo test
```

### Code Quality

```bash
# Format Rust code
cargo fmt

# Lint Rust code
cargo clippy

# Format Python code
ruff format

# Check formatting
cargo fmt -- --check
ruff format --check
```

### Building for Production

```bash
# Build optimized release wheel
maturin build --release

# The wheel will be in target/wheels/
# Install with: uv pip install target/wheels/rust_quant-*.whl
```

## Architecture

- **Rust Core**: High-performance Black-Scholes implementation with SIMD intrinsics
- **PyO3 Bindings**: Zero-cost abstractions for Python integration
- **Type Safety**: Full `.pyi` stubs for IDE support and type checking
- **Immutability**: All option modifications create new instances
- **Performance**: Release builds with LTO and aggressive optimizations

## License

MIT

## Contributing

Contributions are welcome! This project follows strict quality standards to maintain production-grade code.

### Requirements for Pull Requests

Before submitting, ensure:
- **✅ Use `uv`** for all Python dependency management (no `pip`)
- **✅ Code formatting**: `cargo fmt` (Rust) and `ruff format` (Python)
- **✅ All tests pass**: `pytest tests/ -v && cargo test`
- **✅ No linter warnings**: `cargo clippy -- -D warnings`
- **✅ Type stubs updated**: If adding new classes/methods, update `.pyi` files
- **✅ Examples provided**: New features should include example usage
- **✅ Benchmarks**: Performance-critical code should include benchmarks
- **✅ Documentation**: Update relevant `.md` files

### Contribution Workflow

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/rust-quant.git
cd rust-quant

# 2. Set up development environment
uv sync
source .venv/bin/activate  # macOS/Linux

# 3. Create a feature branch
git checkout -b feature/your-feature-name

# 4. Make your changes
# - Edit Rust code in src/
# - Edit Python code in python/
# - Add/update tests in tests/
# - Add examples to examples/

# 5. Rebuild Rust extension after changes
maturin develop --release

# 6. Format code
cargo fmt
ruff format .

# 7. Run linters
cargo clippy -- -D warnings

# 8. Run all tests
pytest tests/ -v
cargo test

# 9. Run examples to verify
uv run python examples/01_basic_single_option.py

# 10. Commit and push
git add .
git commit -m "feat: your descriptive commit message"
git push origin feature/your-feature-name

# 11. Open a pull request on GitHub
```

### Areas for Contribution

We welcome contributions in these areas:
- **New option types**: Barrier, Asian, Lookback options
- **More Greeks**: Vanna, Volga, charm, color
- **Implied volatility**: Newton-Raphson solver
- **Interest rate models**: Vasicek, Cox-Ingersoll-Ross, Hull-White
- **Performance optimizations**: SIMD improvements, better parallelism
- **Documentation**: Tutorials, examples, API docs
- **Testing**: Edge cases, numerical accuracy validation
- **Benchmarking**: More comprehensive performance tests

### Code Style Guidelines

**Rust:**
- Follow standard Rust naming conventions
- Use `rustfmt` defaults
- Document public APIs with `///` doc comments
- Keep functions small and focused
- Prefer immutability where possible

**Python:**
- Follow PEP 8 via `ruff`
- Type hints for all public APIs
- Docstrings in Google style
- Keep examples self-contained and runnable

### Questions or Issues?

- **Bugs**: Open an issue with a minimal reproducible example
- **Feature requests**: Open an issue describing the use case
- **Questions**: Start a discussion on GitHub Discussions
