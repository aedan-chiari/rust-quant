# rust-quant

**Fast options pricing and yield curve library written in Rust, usable from Python.**

Price options and build yield curves instantly - optimized to price thousands of options in milliseconds.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

## What It Does

- **Options Pricing**: European and American options with Black-Scholes and binomial trees
- **Greeks**: Delta, Gamma, Vega, Theta, Rho for risk management
- **Yield Curves**: Build interest rate curves from bond prices with multiple interpolation methods
- **Batch Processing**: Price thousands of options at once (very fast)

## Installation

### Quick Setup with uv

This project uses [uv](https://docs.astral.sh/uv/) - a fast Python package manager that handles everything.

```bash
# 1. Install uv (if you don't have it)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install Rust (needed to build the library)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 3. Clone and setup
git clone https://github.com/aedan-chiari/rust-quant.git
cd rust-quant

# 4. Let uv do everything (creates venv, installs deps, builds Rust code)
uv sync
```

That's it! `uv sync` automatically:
- Creates a Python virtual environment
- Installs all Python dependencies
- Compiles the Rust extension
- Installs the library

### Verify Installation

```bash
# Run a quick test
uv run python -c "from rust_quant import EuroCallOption; print(EuroCallOption(100,100,1,0.05,0.2).price())"
# Should print: 10.450583572185565
```

### Using the Library

```bash
# Run Python scripts with uv
uv run python examples/01_basic_single_option.py

# Or activate the virtual environment
source .venv/bin/activate  # macOS/Linux
python examples/01_basic_single_option.py
```

## Usage Examples

### Options Pricing

```python
from rust_quant import EuroCallOption

# Price a European call option
call = EuroCallOption(
    spot=100.0,           # Stock price
    strike=105.0,         # Strike price
    time_to_expiry=1.0,   # 1 year
    risk_free_rate=0.05,  # 5%
    volatility=0.2        # 20% volatility
)

print(f"Price: ${call.price():.2f}")
print(f"Delta: {call.delta():.4f}")

# Price many options at once (fast batch processing)
spots = [100.0] * 100000
strikes = [95.0] * 100000  
times = [1.0] * 100000
rates = [0.05] * 100000
vols = [0.2] * 100000

prices = EuroCallOption.price_many(spots, strikes, times, rates, vols)
```

### American Options

```python
from rust_quant import AmericanPutOption

# American options can be exercised early
put = AmericanPutOption(
    spot=100.0,
    strike=110.0,
    time_to_expiry=1.0,
    risk_free_rate=0.05,
    volatility=0.3,
    steps=100  # Tree steps (more = more accurate)
)

print(f"American Put: ${put.price():.2f}")
```

### Yield Curves

```python
from rust_quant import Security, ZeroCouponCurve

# Build a yield curve from bond prices
securities = [
    Security(maturity=1.0, price=95.0),   # 1-year bond
    Security(maturity=2.0, price=90.0),   # 2-year bond
    Security(maturity=5.0, price=80.0),   # 5-year bond
]

curve = ZeroCouponCurve(securities)

# Extract interest rates
rate_1y = curve.zero_rate(1.0)
rate_5y = curve.zero_rate(5.0)
print(f"1Y rate: {rate_1y * 100:.2f}%")
print(f"5Y rate: {rate_5y * 100:.2f}%")

# Get discount factors for pricing
discount_1y = curve.discount_factor(1.0)
discount_5y = curve.discount_factor(5.0)
```

## Why It's Fast

- **Written in Rust**: No Python overhead, compiled to native code
- **SIMD**: Uses CPU vector instructions to process 4 options at once
- **Parallel**: Spreads work across all CPU cores automatically
- **Memory Efficient**: No allocations in hot loops

**Benchmark**: Price 100,000 options
- Pure Python: ~5 seconds
- This library: ~50 milliseconds (100x faster)

## Examples Folder

See `examples/` for complete working examples:
- `01_basic_single_option.py` - Options pricing basics
- `02_multiple_options_vectorized.py` - Batch pricing
- `05_american_options_example.py` - American options
- `07_zero_coupon_curve.py` - Yield curves

## License

MIT
