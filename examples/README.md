# rust-quant Examples

This directory contains comprehensive, real-world examples demonstrating the full capabilities of the rust-quant library. Each example is self-contained, well-documented, and designed for progressive learning.

## Quick Start

### Prerequisites

Make sure you've installed rust-quant:

```bash
# From project root
uv sync
```

That's it! You don't even need to activate the virtual environment thanks to `uv run`.

### Running Examples

```bash
# Run any example with uv run (recommended)
uv run python examples/01_basic_single_option.py

# Or activate the environment first
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate      # Windows
python examples/01_basic_single_option.py
```

## Examples Overview

Run the examples in order to learn the library:

### 1. Basic Single Option ([01_basic_single_option.py](01_basic_single_option.py))

**Learn the fundamentals of option pricing**

This example covers:
- Creating `EuroCallOption` and `EuroPutOption` objects
- Calculating option price using Black-Scholes formula
- Computing individual Greeks: Delta, Gamma, Vega, Theta, Rho
- Using `.greeks()` to get all values efficiently (recommended)
- Immutable updates with `.with_*()` methods for scenario analysis
- Comparing call vs put option characteristics

**Key Concepts:**
- European options can only be exercised at expiration
- Greeks measure sensitivity to different market factors
- Immutable API enables safe scenario analysis

**Expected Output:**
```
Call Price: $8.0214
Delta: 0.5422
Gamma: 0.0198
Vega: 0.3967
Theta: -0.0172
Rho: 0.4620
```

**Run:** `uv run python examples/01_basic_single_option.py`

### 2. Multiple Options Vectorized ([02_multiple_options_vectorized.py](02_multiple_options_vectorized.py))

**Scale up to portfolio-level pricing**

This example demonstrates:
- Using static methods: `EuroCallOption.price_many()` and `EuroCallOption.greeks_many()`
- Pricing multiple options simultaneously with SIMD+parallel optimization
- Batch calculation of all Greeks for option portfolios
- Performance comparison: vectorized vs individual pricing
- Working with portfolio-level risk metrics

**Key Concepts:**
- Static methods automatically use SIMD (AVX2) and parallel processing
- 10-30x faster than individual pricing for 100+ options
- Same API for both single and batch operations

**Performance:**
- 1,000 options: < 1ms
- 10,000 options: ~10ms
- 100,000 options: ~80ms

**Run:** `uv run python examples/02_multiple_options_vectorized.py`

### 3. Performance Benchmark (`03_performance_benchmark.py`)

Understand performance characteristics:
- Standard vectorized vs SIMD+Parallel implementations
- Scaling from 1,000 to 1,000,000 options
- When to use each optimization level

**Run:** `uv run examples/03_performance_benchmark.py`

### 4. Dividend Yield Examples (`04_dividend_yield_example.py`)

Learn dividend yield support:
- Pricing options on dividend-paying stocks
- Impact of dividends on call and put prices
- Put-call parity with dividends
- Real-world scenarios

**Run:** `uv run examples/04_dividend_yield_example.py`

### 5. American Options (`05_american_options_example.py`)

Explore American-style options:
- Early exercise capability and premium
- Binomial tree pricing method
- Comparing American vs European options
- Dividend effects on early exercise

**Run:** `uv run examples/05_american_options_example.py`

### 6. American Batch Pricing (`06_american_batch_pricing.py`)

Scale American option pricing:
- Parallel batch pricing with Rayon
- `AmericanCallOption.price_many()` and `greeks_many()`
- Performance comparison: batch vs individual
- Dividend effects on batch pricing

**Run:** `uv run examples/06_american_batch_pricing.py`

### 7. Zero Coupon Curve (`07_zero_coupon_curve.py`)

Yield curve construction and analysis:
- Building zero-coupon curves from bonds
- Discount factors and zero rates
- Forward rate calculations
- Present value computations

**Run:** `uv run examples/07_zero_coupon_curve.py`

### 8. Monte Carlo Path Generation (`08_monte_carlo_paths.py`)

Stochastic simulation and option pricing:
- Brownian Motion and Geometric Brownian Motion paths
- Monte Carlo option pricing with variance reduction
- Heston stochastic volatility model
- Performance benchmarking and convergence analysis

**Run:** `uv run examples/08_monte_carlo_paths.py`

## Quick Start

```python
from rust_quant import EuroCallOption

# Single option
call = EuroCallOption(
    spot=100.0,
    strike=105.0,
    time_to_expiry=1.0,
    risk_free_rate=0.05,
    volatility=0.2
)

# Get price and Greeks
price = call.price()
delta = call.delta()
greeks = call.greeks()  # All at once (efficient!)

# Multiple options (vectorized)
spots = [95.0, 100.0, 105.0, 110.0, 115.0]
strikes = [100.0] * 5
times = [1.0] * 5
rates = [0.05] * 5
vols = [0.2] * 5

prices = EuroCallOption.price_many(spots, strikes, times, rates, vols)
\`\`\`

## API Summary

### For Single Options

\`\`\`python
from rust_quant import EuroCallOption

# Create once, reuse many times
call = EuroCallOption(spot, strike, time, rate, vol)

# Calculate individual values
call.price()
call.delta()
call.gamma()
call.vega()
call.theta()
call.rho()

# Get all Greeks at once (recommended)
greeks = call.greeks()

# Scenario analysis
higher_spot = call.with_spot(110.0)
higher_vol = call.with_volatility(0.3)
\`\`\`

### For Multiple Options

\`\`\`python
from rust_quant import EuroCallOption

# Static methods (SIMD + parallel, fastest for large datasets)
prices = EuroCallOption.price_many(spots, strikes, times, rates, vols)
results = EuroCallOption.greeks_many(spots, strikes, times, rates, vols)
\`\`\`

## Learning Path

We recommend following this progression:

1. **Start Here**: Example 01 - Learn basic single option pricing
2. **Scale Up**: Example 02 - Understand vectorized operations
3. **Performance**: Example 03 - See the performance benefits
4. **Dividends**: Example 04 - Learn dividend-adjusted pricing
5. **American Options**: Example 05 - Understand early exercise
6. **Yield Curves**: Example 07 - Master fixed income pricing
7. **Simulation**: Example 08 - Explore Monte Carlo methods

## Performance Guide

### Choosing the Right Approach

| Portfolio Size | Recommended Method | Expected Time | Use Case |
|----------------|-------------------|---------------|----------|
| 1-10 options | Instance methods | < 1ms | Interactive analysis, learning |
| 10-100 options | `.price_many()` | < 1ms | Small portfolios |
| 100-10K options | `.price_many()` | 1-10ms | Medium portfolios |
| 10K-100K options | `.price_many()` | 10-80ms | Large portfolios |
| 100K+ options | `.price_many()` | 80-200ms | Very large portfolios, risk systems |

### Performance Tips

1. **Always use static methods for batch operations**: `EuroCallOption.price_many()` is 10-30x faster than looping
2. **Use `.greeks()` instead of individual calls**: Computing all Greeks at once is more efficient
3. **American options are slower**: Binomial tree methods take ~1-2ms per option
4. **Release builds matter**: Development builds are 5-10x slower than release builds

## Example Output

All examples produce detailed output showing:
- Input parameters
- Calculated values (prices, Greeks, etc.)
- Performance metrics (timing, throughput)
- Interpretation and analysis

The output is formatted for readability with clear section headers and aligned columns.

## Extending the Examples

Feel free to modify these examples for your own learning:

```python
# Experiment with different parameters
spot_prices = [90, 95, 100, 105, 110]  # Different spot prices
strikes = [100]  # Single strike
maturities = [0.25, 0.5, 1.0, 2.0]  # Different expirations
volatilities = [0.1, 0.2, 0.3, 0.4]  # Volatility surface

# Price across all combinations
for spot in spot_prices:
    for maturity in maturities:
        for vol in volatilities:
            call = EuroCallOption(spot, 100, maturity, 0.05, vol)
            print(f"S={spot}, T={maturity}, σ={vol}: ${call.price():.4f}")
```

## Getting Help

- **Inline documentation**: Each example has detailed comments explaining the code
- **API reference**: See [README.md](../README.md) for complete API documentation
- **Architecture**: Read [ARCHITECTURE.md](../ARCHITECTURE.md) for design details
- **Issues**: Report problems at [GitHub Issues](https://github.com/aedan-chiari/rust-quant/issues)
- **Questions**: Ask in [GitHub Discussions](https://github.com/aedan-chiari/rust-quant/discussions)

## Interactive Exploration

Prefer interactive notebooks? Check out the [marimo_examples/](../marimo_examples/) directory for Jupyter-like reactive notebooks with sliders and real-time updates.

```bash
# Install marimo
uv pip install marimo

# Run interactive version
marimo run marimo_examples/01_basic_single_option.py
```

Happy exploring!
