# Development Guide

This guide is for contributors who want to develop, extend, or modify rust-quant. It covers the development workflow, project structure, coding standards, and best practices.

## Table of Contents

- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Adding New Features](#adding-new-features)
- [Testing](#testing)
- [Performance Optimization](#performance-optimization)
- [API Design Principles](#api-design-principles)
- [Common Issues](#common-issues)
- [Release Checklist](#release-checklist)

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
│   └── american/                 # American options module
│       ├── mod.rs                # Module exports
│       ├── option.rs             # AmericanOption (simple class)
│       ├── call.rs               # AmericanCallOption
│       ├── put.rs                # AmericanPutOption
│       └── pricing.rs            # Binomial tree implementation
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
│   └── README.md                 # Examples documentation
├── tests/                        # Python test suite
│   ├── test_european_options.py  # European options tests
│   └── test_american_options.py  # American options tests
├── Cargo.toml                    # Rust dependencies and config
├── pyproject.toml                # Python project metadata
├── README.md                     # Main documentation
├── ARCHITECTURE.md               # Architecture documentation
├── GETTING_STARTED.md            # Getting started guide
├── DEVELOPMENT.md                # This file
└── .gitignore                    # Git ignore rules
```

## Development Workflow

### Initial Setup

Follow these steps to set up your development environment:

#### 1. Install Prerequisites

**Install Rust** (if not already installed):
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env  # Reload PATH
```

**Install uv** (modern Python package manager):
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 2. Clone and Setup

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/rust-quant.git
cd rust-quant

# Set up development environment (creates venv, installs deps, builds extension)
uv sync

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows
```

That's it! `uv sync` handles:
- Creating a virtual environment
- Installing Python dependencies
- Installing maturin
- Building the Rust extension
- Installing the package in editable mode

#### 3. Verify Setup

```bash
# Run tests to verify everything works
pytest tests/ -v
cargo test

# Try an example
uv run python examples/01_basic_single_option.py
```

### Building

After making changes to Rust code, you need to rebuild the extension:

```bash
# Development build (faster compile, less optimized)
maturin develop

# Release build (slower compile, fully optimized - use for benchmarking)
maturin develop --release

# Build wheel for distribution (places wheel in target/wheels/)
maturin build --release
```

**When to rebuild:**
- ✅ After modifying any `.rs` file in `src/`
- ✅ After modifying `Cargo.toml`
- ❌ After modifying Python files (`.py`, `.pyi`) - no rebuild needed
- ❌ After modifying documentation files

**Pro tip:** Use `--release` when benchmarking or profiling. Development builds are 5-10x slower.

### Testing

rust-quant has comprehensive test coverage across both Rust and Python:

```bash
# Run all Python tests with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_european_options.py -v

# Run specific test function
pytest tests/test_european_options.py::test_call_price -v

# Run with coverage report
pytest tests/ --cov=rust_quant --cov-report=html

# Run Rust unit tests
cargo test

# Run Rust tests with output
cargo test -- --nocapture

# Run Rust benchmarks (requires nightly Rust)
cargo +nightly bench

# Test all examples (smoke test)
for f in examples/0*.py; do uv run python "$f" || exit 1; done

# Type check Python code (if mypy installed)
mypy examples/ tests/
```

**Test Philosophy:**
- Unit tests for individual functions
- Integration tests for end-to-end workflows
- Numerical accuracy tests against known values
- Performance regression tests

### Code Quality

Maintain consistent code quality with these tools:

```bash
# ============= Rust =============

# Format Rust code (required before commit)
cargo fmt

# Check formatting without modifying files
cargo fmt -- --check

# Lint Rust code (catches common mistakes)
cargo clippy

# Strict linting (treat warnings as errors)
cargo clippy -- -D warnings

# ============= Python =============

# Format Python code with ruff
ruff format .

# Check formatting without modifying
ruff format --check .

# Lint Python code
ruff check .

# Fix auto-fixable lint issues
ruff check --fix .

# Type check Python (if mypy installed)
mypy examples/ tests/

# ============= All =============

# Run all quality checks (pre-commit script)
cargo fmt --check && \
cargo clippy -- -D warnings && \
ruff format --check . && \
ruff check . && \
pytest tests/ -v && \
cargo test
```

**CI/CD:** All pull requests must pass these checks in GitHub Actions.

## Architecture

### Rust Layer

**Module Structure:**
- `src/lib.rs` - Python module definition and exports
- `src/types.rs` - Shared types (OptionGreeks) and traits (OptionCalculations)
- `src/simd.rs` - SIMD-optimized helper functions (AVX intrinsics)
- `src/vectorized.rs` - Internal SIMD+parallel implementation functions
- `src/european/` - European options module
  - `mod.rs` - Module exports
  - `option.rs` - EuroOption (simple class)
  - `call.rs` - EuroCallOption (with SIMD+parallel static methods)
  - `put.rs` - EuroPutOption (with SIMD+parallel static methods)
- `src/american/` - American options module
  - `mod.rs` - Module exports
  - `option.rs` - AmericanOption (simple class)
  - `call.rs` - AmericanCallOption
  - `put.rs` - AmericanPutOption
  - `pricing.rs` - Binomial tree implementation (CRR method)

**Core Types:**

**European Options (`src/european/`):**
- `EuroCallOption` - European call with Black-Scholes pricing
  - Instance methods: `.price()`, `.delta()`, `.gamma()`, `.vega()`, `.theta()`, `.rho()`, `.greeks()`
  - **Static methods (SIMD+Parallel)**: `.price_many()`, `.greeks_many()`
  - Immutable updates: `.with_spot()`, `.with_volatility()`, `.with_time()`, `.with_strike()`
- `EuroPutOption` - European put (same API as EuroCallOption)
- `EuroOption` - Simple class for one-off calculations (no SIMD/parallelism overhead)

**American Options (`src/american/`):**
- `AmericanCallOption` - American call with binomial tree pricing
  - Instance methods: `.price()`, `.delta()`
  - Configurable steps parameter for accuracy/performance trade-off
- `AmericanPutOption` - American put (same API as AmericanCallOption)
- `AmericanOption` - Simple class for one-off American option calculations

**Shared Types (`src/types.rs`):**
- `OptionGreeks` - Container for all Greeks and price
- `OptionCalculations` - Trait for shared calculations (d1, d2, gamma, vega, pdf)

**Internal Implementation (`src/vectorized.rs`):**
- `price_calls_fast_impl()` / `price_puts_fast_impl()` - SIMD + Parallel pricing
- `greeks_calls_fast_impl()` / `greeks_puts_fast_impl()` - SIMD + Parallel Greeks
- These are NOT exported to Python - only used internally by European option static methods

**Binomial Tree (`src/american/pricing.rs`):**
- `binomial_tree_price()` - CRR binomial tree with early exercise
- `binomial_tree_delta()` - Delta via finite differences
- Configurable steps for accuracy/performance balance

**Performance Features:**
- SIMD via `wide` crate (f64x4 for AVX2)
- Parallelism via `rayon` crate (work-stealing thread pool)
- Chunk size optimization (1024 options per chunk)
- Release profile with LTO and opt-level 3

### Modular Architecture

**Design Philosophy:**
- **European Options**: Analytical pricing (Black-Scholes), SIMD+parallel optimization
- **European Options**: Analytical pricing (Black-Scholes), SIMD+parallel optimization
- **American Options**: Numerical pricing (binomial tree), early exercise support
- **Modular structure**: Separate modules for different option types
- **No standalone functions**: Everything goes through classes for better discoverability

### Python Layer

**Type Stubs (`python/rust_quant/rust_quant.pyi`):**
- Provides IDE autocomplete and type checking
- Documents all classes, methods, and functions
- Must be kept in sync with Rust implementation
- Automatically installed with the package via `python-source = "python"` in `pyproject.toml`

**Examples (`examples/`):**
- Demonstrate different usage patterns
- Serve as integration tests
- Show performance characteristics
- Numbered for progressive learning

**Tests (`tests/`):**
- `test_european_options.py` - European option tests
- `test_american_options.py` - American option tests

## Adding New Features

### 1. Adding to Existing Option Classes

**For European option instance methods** - Edit `src/european/call.rs` or `put.rs`:

```rust
#[pymethods]
impl EuroCallOption {
    pub fn new_method(&self, param: f64) -> f64 {
        // Implementation for single option
        param * self.spot
    }
}
```

**For European option static methods (batch operations)** - Edit `src/european/call.rs`:

```rust
#[pymethods]
impl EuroCallOption {
    #[staticmethod]
    pub fn new_batch_method(params: Vec<f64>) -> PyResult<Vec<f64>> {
        // Call internal implementation from vectorized.rs
        crate::vectorized::new_batch_method_impl(params)
    }
}
```

Then implement in `src/vectorized.rs`:
```rust
pub fn new_batch_method_impl(params: Vec<f64>) -> PyResult<Vec<f64>> {
    // SIMD + parallel implementation
    Ok(params.par_iter().map(|x| x * 2.0).collect())
}
```

**For American option methods** - Edit `src/american/call.rs` or `put.rs`:

```rust
#[pymethods]
impl AmericanCallOption {
    pub fn new_analysis(&self) -> f64 {
        // Implementation using binomial tree or other numerical method
        self.price() / self.spot
    }
}
```

**Note:** Do NOT add #[pyfunction] exports - all functionality goes through classes.

### 2. Update Type Stubs

**For European options** - Edit `python/rust_quant/rust_quant.pyi`:

```python
class EuroCallOption:
    # ... existing methods ...

    def new_method(self, param: float) -> float:
        """Description of the method."""
        ...
```

**For static methods**:

```python
class EuroCallOption:
    # ... existing methods ...
    
    @staticmethod
    def new_batch_method(params: List[float]) -> List[float]:
        """
        Description of the batch operation.
        Uses SIMD + parallel processing for optimal performance.
        """
        ...
```

### 3. Add Example

Create or update file in `examples/`:

```python
from rust_quant import EuroCallOption, AmericanPutOption

# Single European option usage
option = EuroCallOption(100.0, 105.0, 1.0, 0.05, 0.2)
result = option.new_method(42.0)
print(f"Result: {result}")

# Batch operation usage (European options only)
params = [1.0, 2.0, 3.0, 4.0, 5.0]
results = EuroCallOption.new_batch_method(params)
print(f"Batch results: {results}")

# American option usage
american = AmericanPutOption(
    spot=100.0, strike=105.0, time=1.0, rate=0.05, vol=0.2, steps=100
)
price = american.price()
```

### 4. Add Tests

Add tests in `tests/test_european_options.py` or `tests/test_american_options.py`:

```python
import pytest
from rust_quant import EuroCallOption, AmericanPutOption

def test_new_european_method():
    call = EuroCallOption(100.0, 105.0, 1.0, 0.05, 0.2)
    result = call.new_method(42.0)
    assert isinstance(result, float)
    assert result > 0.0

def test_new_american_method():
    put = AmericanPutOption(
        spot=100.0, strike=105.0, time=1.0,
        rate=0.05, vol=0.2, steps=100
    )
    result = put.new_analysis()
    assert isinstance(result, float)
```

### 5. Update Documentation

- Update `README.md` with API documentation
- Add example to appropriate section
- Update `ARCHITECTURE.md` if needed
- Update this guide if adding new module structure

### 6. Test

```bash
# Build and test
maturin develop --release
uv run python examples/your_example.py

# Run Python tests
pytest tests/

# Run Rust tests
cargo test
```

## Adding New Option Types

### Creating a New Module (e.g., Exotic Options)

1. **Create module directory**: `src/exotic/`
2. **Add module files**:
   - `mod.rs` - Module exports
   - `barrier.rs`, `asian.rs`, etc. - Option implementations
   - `pricing.rs` - Shared pricing logic

3. **Update `src/lib.rs`**:
```rust
mod exotic;
use exotic::{BarrierOption, AsianOption};

#[pymodule]
fn rust_quant(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // ... existing exports ...
    m.add_class::<BarrierOption>()?;
    m.add_class::<AsianOption>()?;
    Ok(())
}
```

4. **Update `python/rust_quant/__init__.py`**:
```python
from rust_quant.rust_quant import (
    # ... existing imports ...
    BarrierOption,
    AsianOption,
)

__all__ = [
    # ... existing exports ...
    "BarrierOption",
    "AsianOption",
]
```

5. **Add type stubs** to `python/rust_quant/rust_quant.pyi`

6. **Add tests** in `tests/test_exotic_options.py`

7. **Add examples** in `examples/06_exotic_options_example.py`

## Performance Optimization

### Profiling

```bash
# Profile Rust code
cargo build --release
cargo flamegraph --bin your_test

# Profile Python code
python -m cProfile -o profile.stats examples/03_performance_benchmark.py
python -m pstats profile.stats
```

### Optimization Tips

1. **Use static methods** for large datasets (100+ options) - European options only
2. **Batch operations** instead of loops when possible
3. **Pre-allocate arrays** in Python before passing to Rust
4. **Use release builds** for benchmarking
5. **Consider chunk sizes** for parallel operations (default: 1024)
6. **Choose right class**: 
   - `EuroOption`/`AmericanOption` for one-off calculations
   - `EuroCallOption`/`EuroPutOption` for batch operations
   - `AmericanCallOption`/`AmericanPutOption` for early exercise

## API Design Principles

1. **Modular Architecture**
   - Separate modules for different option types
   - Clear distinction between analytical and numerical methods
   - Easy to extend with new option types

2. **Class-Based Architecture**
   - All functionality exposed through classes
   - No standalone module functions
   - Better discoverability and organization

3. **Separation of Concerns**
   - Simple classes: `EuroOption`, `AmericanOption`
   - Optimized classes: `EuroCallOption`, `EuroPutOption`, etc.
   - Static methods for batch operations (European only)

4. **Consistent API**
   - Instance methods for single options: `.price()`, `.delta()`, etc.
   - Static methods for batches: `.price_many()`, `.greeks_many()` (European only)
   - All static methods automatically use SIMD+parallel processing

5. **Immutability**
   - Options are immutable once created
   - Use `.with_*()` methods to create new options with modified parameters
   - Enables functional-style scenario analysis

6. **Performance by Default**
   - Static methods automatically optimize with SIMD and parallelism
   - No need for separate `_fast` functions
   - Users get best performance without thinking about it

## Common Issues

### Build Failures

**Issue:** `pyo3` version mismatch
**Solution:** Update `Cargo.toml` to use compatible versions

**Issue:** Missing SIMD support
**Solution:** Ensure target CPU supports AVX2 (most modern CPUs since 2013)

**Issue:** Conda environment conflicts
**Solution:** `unset CONDA_PREFIX` before activating venv

### Performance Issues

**Issue:** Need to price many European options quickly
**Solution:** Use static methods: `EuroCallOption.price_many()` or `EuroCallOption.greeks_many()` (automatically use SIMD+parallel)

**Issue:** American options are slow
**Solution:** Reduce `steps` parameter (e.g., 50-100 instead of 200+) for faster computation at slight accuracy cost

**Issue:** Not using all cores
**Solution:** Check Rayon thread pool size. Static methods automatically parallelize (European options only).

### Type Checking Issues

**Issue:** IDE doesn't recognize types (e.g., "EuroCallOption is not a known attribute")
**Solution:**
1. Make sure `python-source = "python"` is in `pyproject.toml`
2. Ensure `.pyi` file is in `python/rust_quant/` directory
3. Rebuild: `maturin develop --release`
4. Restart your IDE/language server

**Issue:** Type stubs out of sync with Rust code
**Solution:** Update `python/rust_quant/rust_quant.pyi` to match Rust implementation

## Release Checklist

Before releasing a new version:

1. **Update version numbers**
   - `Cargo.toml`: `version = "x.y.z"`
   - `pyproject.toml`: `version = "x.y.z"`

2. **Run all tests**
   ```bash
   cargo test
   pytest tests/ -v
   ```

3. **Run all examples**
   ```bash
   for f in examples/*.py; do python "$f" || exit 1; done
   ```

4. **Check code quality**
   ```bash
   cargo fmt -- --check
   cargo clippy
   ruff format --check
   ```

5. **Build wheels**
   ```bash
   maturin build --release
   ```

6. **Test installation from wheel**
   ```bash
   uv venv test_env
   source test_env/bin/activate
   uv pip install target/wheels/rust_quant-*.whl
   python -c "import rust_quant; print(rust_quant.EuroCallOption(100, 100, 1, 0.05, 0.2).price())"
   deactivate
   rm -rf test_env
   ```

7. **Update documentation**
   - Update README.md with new features
   - Update ARCHITECTURE.md if design changed
   - Update this DEVELOPMENT.md if workflow changed

8. **Create release**
   - Tag in git: `git tag v x.y.z`
   - Push tags: `git push --tags`
   - Create GitHub release with changelog

## Resources

- **PyO3**: https://pyo3.rs/
- **Maturin**: https://github.com/PyO3/maturin
- **uv**: https://docs.astral.sh/uv/
- **Rayon**: https://github.com/rayon-rs/rayon
- **wide**: https://github.com/Lokathor/wide
- **Black-Scholes Model**: https://en.wikipedia.org/wiki/Black%E2%80%93Scholes_model
- **Binomial Options Pricing**: https://en.wikipedia.org/wiki/Binomial_options_pricing_model
1. Ensure you've run `maturin develop` after modifying type stubs
2. Reload VS Code window: Cmd+Shift+P > "Developer: Reload Window"
3. Restart Python language server: Cmd+Shift+P > "Python: Restart Language Server"
4. Verify correct interpreter is selected (should be from `.venv`)

**Issue:** Type stub changes not appearing
**Solution:** Run `unset CONDA_PREFIX && source .venv/bin/activate && maturin develop --release` to reinstall

## Release Checklist

- [ ] All tests pass (`cargo test`)
- [ ] Code is formatted (`cargo fmt`)
- [ ] No clippy warnings (`cargo clippy`)
- [ ] Examples run successfully
- [ ] Benchmark shows expected performance
- [ ] Documentation is updated
- [ ] Version bumped in `Cargo.toml` and `pyproject.toml`
- [ ] Type stubs are up to date
- [ ] Build wheel (`maturin build --release`)
- [ ] Test wheel installation

## Resources

- [PyO3 Documentation](https://pyo3.rs/)
- [Maturin Guide](https://maturin.rs/)
- [Rayon Documentation](https://docs.rs/rayon/)
- [SIMD in Rust](https://rust-lang.github.io/packed_simd/)
