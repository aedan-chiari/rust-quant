# Getting Started with rust-quant

This comprehensive guide will walk you through installation, setup, and your first steps with rust-quant - a high-performance quantitative finance library for derivatives pricing, yield curve construction, and stochastic simulation.

## What is rust-quant?

rust-quant is a production-grade Python library with a Rust core, designed for:
- **Option pricing**: European and American options with complete Greeks
- **Yield curves**: Zero-coupon curve construction with multiple interpolation methods
- **Stochastic simulation**: Monte Carlo pricing with GBM and Heston models
- **High performance**: 10-30x faster than pure Python on large portfolios

This project uses **[uv](https://docs.astral.sh/uv/)** - a modern, blazing-fast Python package manager.

## Prerequisites

Before you begin, install:

1. **uv** - Modern Python package manager
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Or with pip (if you must)
   pip install uv
   ```

2. **Rust** - Required for building the Rust extensions
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

## Installation

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/aedan-chiari/rust-quant.git
cd rust-quant

# Install everything (creates venv, installs all dependencies, builds Rust extension)
uv sync
```

That's it! `uv sync` automatically:
- Creates a virtual environment (`.venv/`)
- Installs all Python dependencies from `pyproject.toml`
- Builds and installs the Rust extension with maturin

### Activate the Environment

```bash
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows
```

## First Steps

### 1. Verify Installation

```bash
python -c "import rust_quant; print('✓ Installation successful')"
```

### 2. Run Your First Example

```python
# Save as test_option.py
from rust_quant import EuroCallOption

# Create an at-the-money European call option
call = EuroCallOption(
    spot=100.0,           # Stock price: $100
    strike=100.0,         # Strike price: $100
    time_to_expiry=1.0,   # 1 year to expiration
    risk_free_rate=0.05,  # 5% interest rate
    volatility=0.2        # 20% volatility
)

# Calculate price and Greeks
print(f"Call Price: ${call.price():.4f}")
print(f"Delta: {call.delta():.4f}")
print(f"Gamma: {call.gamma():.4f}")
print(f"Vega: {call.vega():.4f}")
print(f"Theta: {call.theta():.4f}")
print(f"Rho: {call.rho():.4f}")
```

Run it:
```bash
uv run python test_option.py
```

Expected output:
```
Call Price: $10.4506
Delta: 0.6368
Gamma: 0.0198
Vega: 0.3967
Theta: -0.0172
Rho: 0.4620
```

### 3. Explore the Examples

```bash
# Basic European option usage
uv run python examples/01_basic_single_option.py

# Vectorized batch processing
uv run python examples/02_multiple_options_vectorized.py

# Performance benchmarks
uv run python examples/03_performance_benchmark.py

# Dividend yield examples
uv run python examples/04_dividend_yield_example.py

# American options with early exercise
uv run python examples/05_american_options_example.py
```

## Common Tasks

### Adding Dependencies

```bash
# Use uv to add Python dependencies
uv pip install <package-name>

# For development dependencies
uv pip install --dev <package-name>
```

### Running Tests

```bash
# Python tests
pytest tests/

# Rust tests
cargo test

# Run all tests
pytest tests/ -v && cargo test
```

### Rebuilding After Changes

```bash
# After modifying Rust code
maturin develop --release

# After modifying Python code (no rebuild needed)
# Just run your Python code normally
```

### Code Formatting

```bash
# Format Rust code
cargo fmt

# Format Python code
ruff format

# Check formatting without changes
cargo fmt -- --check
ruff format --check
```

## Project Workflow

### For Users (Just Using the Library)

```bash
# One-time setup
uv sync

# Use the library (uv run automatically uses the virtual environment)
uv run python your_script.py
```

### For Contributors (Developing the Library)

```bash
# Initial setup
uv sync
source .venv/bin/activate

# Development cycle
maturin develop --release  # After Rust changes
cargo fmt                  # Format Rust code
ruff format               # Format Python code
pytest tests/             # Test Python
cargo test                # Test Rust
```

## Troubleshooting

### "uv: command not found"

Make sure uv is installed and in your PATH:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Restart your terminal or run:
source ~/.bashrc  # or ~/.zshrc
```

### "cargo: command not found"

Install Rust:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
# Restart your terminal
```

### Import Error After Installing

Make sure you've run `uv sync`:
```bash
uv sync
```

### "Module not found" for Examples

Make sure you're in the project root:
```bash
uv run python examples/01_basic_single_option.py
```

## Next Steps

Now that you've successfully installed rust-quant, here's your learning path:

### 1. Run the Examples (In Order)

The examples are numbered for progressive learning:

```bash
# Start with basics
uv run python examples/01_basic_single_option.py

# Learn vectorized operations
uv run python examples/02_multiple_options_vectorized.py

# Understand performance
uv run python examples/03_performance_benchmark.py

# Explore dividends
uv run python examples/04_dividend_yield_example.py

# American options
uv run python examples/05_american_options_example.py

# Zero-coupon curves
uv run python examples/07_zero_coupon_curve.py

# Monte Carlo & stochastic processes
uv run python examples/08_monte_carlo_paths.py
```

### 2. Read the Documentation

- **[README.md](README.md)**: Complete API reference and usage examples
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Design philosophy and performance characteristics
- **[DEVELOPMENT.md](DEVELOPMENT.md)**: Contributing guide and development workflow
- **[examples/README.md](examples/README.md)**: Detailed explanation of each example

### 3. Explore Interactive Notebooks

If you prefer interactive exploration, check out the Marimo notebooks:

```bash
# Install marimo first
uv pip install marimo

# Run interactive notebook
marimo run marimo_examples/01_basic_single_option.py

# Or edit it
marimo edit marimo_examples/01_basic_single_option.py
```

### 4. Try Real-World Scenarios

Create your own pricing scripts:

```python
# portfolio_analysis.py
from rust_quant import EuroCallOption, EuroPutOption

# Your portfolio
portfolio = [
    EuroCallOption(100, 105, 0.5, 0.05, 0.2),
    EuroPutOption(100, 95, 0.5, 0.05, 0.2),
    # ... more options
]

# Calculate total portfolio Greeks
total_delta = sum(opt.delta() for opt in portfolio)
total_gamma = sum(opt.gamma() for opt in portfolio)
total_vega = sum(opt.vega() for opt in portfolio)

print(f"Portfolio Delta: {total_delta:.4f}")
print(f"Portfolio Gamma: {total_gamma:.4f}")
print(f"Portfolio Vega: {total_vega:.4f}")
```

### 5. Performance Benchmarking

See how fast rust-quant is on your machine:

```bash
uv run python examples/03_performance_benchmark.py
```

This will show you timing comparisons for different dataset sizes.

## Understanding the Library

### European vs American Options

- **European Options**: Can only be exercised at expiration
  - Use `EuroCallOption`, `EuroPutOption`, or `EuroOption`
  - Priced using Black-Scholes analytical formulas
  - Very fast computation
  - Full Greeks available

- **American Options**: Can be exercised at any time before expiration
  - Use `AmericanCallOption`, `AmericanPutOption`, or `AmericanOption`
  - Priced using binomial tree (CRR method)
  - Slower than European (numerical method)
  - Includes early exercise premium

### When to Use Each Class

- **EuroOption / AmericanOption**: Simple calculations, learning, one-off pricing
- **EuroCallOption / EuroPutOption**: Production systems, batch processing, SIMD optimization
- **AmericanCallOption / AmericanPutOption**: Early exercise needed (e.g., ITM puts)

## Why uv?

This project uses **uv** instead of `pip` for several compelling reasons:

### Performance
- **10-100x faster** dependency resolution and installation
- Written in Rust for maximum speed
- Parallel downloads and installs
- Smart caching mechanisms

### Reliability
- **Better dependency resolution** - avoids version conflicts more reliably
- Reproducible builds with lock files
- Consistent environments across machines

### Compatibility
- **Drop-in replacement** for pip/pip-tools
- Uses standard virtual environment format (`.venv/`)
- Works with all existing PyPI packages
- Compatible with existing `requirements.txt` and `pyproject.toml`

### Modern Features
- Built-in virtual environment management
- Automatic Python version detection
- Project scaffolding and management
- Maintained by Astral (creators of ruff)

### Developer Experience
```bash
# Old way (pip)
python -m venv .venv
source .venv/bin/activate
pip install -e .
# ... wait 30 seconds ...

# New way (uv)
uv sync
# ... done in 3 seconds! ✨
```

For more information, visit [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)

## Getting Help

### Common Questions

**Q: Can I use pip instead of uv?**
A: While technically possible, it's not recommended. All documentation assumes `uv`, and you may encounter issues.

**Q: How do I update dependencies?**
A: Run `uv sync --upgrade` to update all dependencies to their latest compatible versions.

**Q: The library builds slowly on first install. Why?**
A: The Rust extension is compiled with optimizations enabled. This is a one-time cost (1-2 minutes). Subsequent installs use the cached build.

**Q: Can I use this in production?**
A: Yes! The library is designed for production use with comprehensive testing, benchmarks, and stable APIs.

**Q: Where can I find more examples?**
A: Check the `examples/` directory for Python scripts and `marimo_examples/` for interactive notebooks.

### Getting Support

- **Documentation**: Start with [README.md](README.md) and [ARCHITECTURE.md](ARCHITECTURE.md)
- **Examples**: See `examples/` directory for working code
- **Issues**: Report bugs at [GitHub Issues](https://github.com/aedan-chiari/rust-quant/issues)
- **Questions**: Use [GitHub Discussions](https://github.com/aedan-chiari/rust-quant/discussions)

## Quick Reference

### Common Commands

```bash
# Install/update the library
uv sync

# Run a Python script
uv run python your_script.py

# Run examples
uv run python examples/01_basic_single_option.py

# Run tests
pytest tests/ -v

# Rebuild Rust after changes (for contributors)
maturin develop --release

# Format code (for contributors)
cargo fmt && ruff format .
```

### Key Concepts

- **European Options**: Analytical Black-Scholes pricing (fast)
- **American Options**: Binomial tree pricing (slower but handles early exercise)
- **Vectorized Operations**: Use `*_many()` static methods for 10-30x speedup
- **Immutable API**: Use `with_*()` methods for scenario analysis
- **Type Safety**: Full `.pyi` stubs for perfect IDE support

You're now ready to start using rust-quant! Begin with the examples and explore the documentation as needed.
