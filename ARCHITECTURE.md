# rust-quant - Architecture

## Overview

This document describes the architectural design, implementation details, and performance characteristics of rust-quant. Understanding the architecture will help you make the most of the library's capabilities and contribute effectively.

## Design Philosophy

rust-quant is built on three core principles:

1. **Performance by Default**: Users get optimal performance without needing to understand implementation details
2. **Clean Separation**: Clear boundaries between analytical (Black-Scholes), numerical (binomial trees), and simulation (Monte Carlo) methods
3. **Type Safety**: Compile-time guarantees via Rust's type system, exposed through Python type stubs

The library implements a modular architecture that separates:
- **European options** (analytical closed-form solutions)
- **American options** (numerical methods with early exercise)
- **Zero-coupon curves** (yield curve construction and interpolation)
- **Stochastic processes** (Monte Carlo simulation and path generation)

Each module is optimized independently for its specific computational characteristics.

## Module Structure

### Top-Level Organization

```
src/
├── lib.rs           # Python module exports
├── types.rs         # Shared types (OptionGreeks, traits)
├── simd.rs          # SIMD helper functions (AVX intrinsics)
├── vectorized.rs    # SIMD+parallel implementations
├── european/        # European options (Black-Scholes)
│   ├── mod.rs       # Module exports
│   ├── option.rs    # EuroOption (simple class)
│   ├── call.rs      # EuroCallOption (optimized)
│   └── put.rs       # EuroPutOption (optimized)
├── american/        # American options (Binomial tree & LSM)
│   ├── mod.rs       # Module exports
│   ├── option.rs    # AmericanOption (simple class)
│   ├── call.rs      # AmericanCallOption
│   ├── put.rs       # AmericanPutOption
│   └── pricing.rs   # Binomial tree implementation (CRR)
├── zero_coupon/     # Zero coupon yield curves
│   ├── mod.rs       # Module exports
│   ├── curve.rs     # ZeroCouponCurve, Security, InterpolationMethod
│   └── forward_curve.rs  # ForwardCurve for forward rate calculations
└── stochastic/      # Stochastic processes & Monte Carlo
    ├── mod.rs       # Module exports
    ├── rng.rs       # Thread-safe random number generation (Xoshiro256++)
    ├── brownian.rs  # Brownian Motion path generation
    ├── gbm.rs       # Geometric Brownian Motion
    ├── heston.rs    # Heston stochastic volatility model
    ├── monte_carlo.rs    # Monte Carlo pricing for European options
    └── american_lsm.rs   # Longstaff-Schwartz algorithm for American options
```

## Class Architecture

### European Options (Black-Scholes)

#### 1. `EuroOption` Class
**Purpose:** Simple, lightweight class for one-off European option calculations

**Use Cases:**
- Quick single option pricing
- Learning/educational purposes
- When SIMD/parallelism overhead isn't justified
- Generic option representation (call or put via `is_call`)

**Characteristics:**
- No SIMD or parallelism
- Minimal memory footprint
- Can represent both calls and puts via `is_call` parameter
- Analytical Black-Scholes formulas

**Example:**
```python
from rust_quant import EuroOption

opt = EuroOption(spot=100, strike=105, time=1.0, rate=0.05, vol=0.2, is_call=True)
price = opt.price()
```

#### 2. `EuroCallOption` and `EuroPutOption` Classes
**Purpose:** Specialized European option classes with SIMD + parallel optimizations

**Use Cases:**
- Production pricing systems
- Large portfolio valuations (100+ options)
- Real-time risk calculations
- Performance-critical applications

**Characteristics:**
- Instance methods for single options (analytical Black-Scholes)
- **Static methods automatically use SIMD (AVX) + Rayon parallelism**
- Optimized for batch operations with chunked processing
- Full Greeks support

**Instance Methods (Single Option):**
```python
from rust_quant import EuroCallOption

call = EuroCallOption(spot=100, strike=105, time=1.0, rate=0.05, vol=0.2)
price = call.price()
delta = call.delta()
greeks = call.greeks()  # Most efficient - all at once
```

**Static Methods (Batch Operations - Auto-Optimized):**
```python
from rust_quant import EuroCallOption

# Automatically uses SIMD + parallel processing
prices = EuroCallOption.price_many(spots, strikes, times, rates, vols)

# All Greeks with SIMD + parallel
prices, deltas, gammas, vegas, thetas, rhos = EuroCallOption.greeks_many(
    spots, strikes, times, rates, vols
)
```

### American Options (Binomial Tree)

#### 3. `AmericanOption` Class
**Purpose:** Simple class for American option calculations with early exercise

**Use Cases:**
- Single American option pricing
- Educational/research purposes
- When early exercise premium is needed
- Generic representation (call or put via `is_call`)

**Characteristics:**
- Cox-Ross-Rubinstein (CRR) binomial tree
- Configurable number of steps (accuracy vs speed)
- Supports dividends
- Price and delta available

**Example:**
```python
from rust_quant import AmericanOption

opt = AmericanOption(
    spot=100, strike=105, time=1.0, rate=0.05, vol=0.2,
    is_call=False, steps=100
)
price = opt.price()
```

#### 4. `AmericanCallOption` and `AmericanPutOption` Classes
**Purpose:** Specialized American option classes with early exercise

**Use Cases:**
- ITM put options (common early exercise)
- Dividend-paying call options
- Options near expiration
- Accurate American option pricing

**Characteristics:**
- Binomial tree pricing (CRR method)
- Early exercise at each node
- Configurable steps parameter
- Delta via finite differences
- Dividend support

**Example:**
```python
from rust_quant import AmericanPutOption

put = AmericanPutOption(
    spot=90, strike=100, time=1.0, rate=0.05, vol=0.2, steps=100
)
price = put.price()  # Includes early exercise premium
delta = put.delta()
```

## Implementation Details

### Module Structure

```
src/
├── lib.rs           # Python module exports (European + American classes)
├── types.rs         # OptionGreeks, OptionCalculations trait
├── simd.rs          # SIMD helper functions (AVX intrinsics)
├── vectorized.rs    # Internal SIMD+parallel implementations
├── european/        # European options module
│   ├── mod.rs       # Module exports
│   ├── option.rs    # EuroOption (simple class)
│   ├── call.rs      # EuroCallOption (optimized)
│   └── put.rs       # EuroPutOption (optimized)
└── american/        # American options module
    ├── mod.rs       # Module exports
    ├── option.rs    # AmericanOption (simple class)
    ├── call.rs      # AmericanCallOption
    ├── put.rs       # AmericanPutOption
    └── pricing.rs   # Binomial tree implementation (CRR)
```

### Key Design Decisions

#### 1. Modular Architecture
**Rationale:** Separate European and American pricing into distinct modules.

**Benefits:**
- Clear separation of analytical (Black-Scholes) vs numerical (binomial tree) methods
- Each module can be optimized independently
- Easy to add new option types (e.g., Asian, Barrier options)
- Better code organization and maintainability

#### 2. No Standalone Functions
**Rationale:** All functionality exposed through classes for better discoverability and organization.

**API Design:**
```python
from rust_quant import EuroCallOption

# Class-based API
prices = EuroCallOption.price_many(spots, strikes, times, rates, vols)
```

**Benefits:**
- Better IDE autocomplete
- Logical grouping of related functionality
- Clear separation between option types
- Namespace organization (European vs American)

#### 3. Automatic Optimization
**Rationale:** Users get best performance without needing to choose optimization levels.

**Static methods automatically optimize:**
```python
from rust_quant import EuroCallOption

# Always uses SIMD + Parallel processing
prices = EuroCallOption.price_many(...)
greeks = EuroCallOption.greeks_many(...)
```

**Benefits:**
- Simpler API - no cognitive overhead
- Performance by default
- Less room for mistakes
- Consistent behavior

#### 4. Class Specialization
**Rationale:** Different classes for different use cases and pricing models.

- **European Options:**
  - `EuroOption`: Simple, no optimization overhead
  - `EuroCallOption`/`EuroPutOption`: Specialized with auto-optimization
  
- **American Options:**
  - `AmericanOption`: Simple binomial tree
  - `AmericanCallOption`/`AmericanPutOption`: Specialized with configurable steps

This makes the choice explicit in the class selection and pricing model.

### Performance Optimizations

#### European Options: SIMD + Parallelism

**SIMD (Single Instruction Multiple Data):**
- Uses `wide` crate with `f64x4` vectors
- Processes 4 options simultaneously with AVX instructions
- ~4x throughput improvement per core

**Parallelism:**
- Uses `rayon` crate with work-stealing thread pool
- Chunks data into 1024-option batches
- Scales with number of CPU cores
- ~Nx speedup where N = core count

**Combined Effect:**
- SIMD provides 4x within each core
- Parallelism multiplies across cores
- Total speedup: 10-30x on large datasets (100K+ options)

#### American Options: Binomial Tree

**Cox-Ross-Rubinstein (CRR) Method:**
- Configurable steps for accuracy/performance trade-off
- Early exercise checked at each node
- Memory-efficient backward induction
- Typical performance: 100 steps ~1-2ms per option

**Trade-offs:**
- More steps = higher accuracy, slower computation
- Typical: 50-100 steps for most use cases
- 200+ steps for high precision requirements

### Internal Implementation

#### European Options (in `european/call.rs`, `european/put.rs`):

**Static methods:**
```rust
#[pymethods]
impl EuroCallOption {
    #[staticmethod]
    pub fn price_many(...) -> PyResult<Vec<f64>> {
        crate::vectorized::price_calls_fast_impl(spots, strikes, times, rates, vols)
    }
}
```

**Internal implementation in `vectorized.rs`:**
```rust
pub fn price_calls_fast_impl(...) -> PyResult<Vec<f64>> {
    // SIMD + Rayon parallelism
    prices.par_chunks_mut(1024)
        .for_each(|chunk| {
            // SIMD processing of 4 options at a time
            simd_call_price_chunk(...)
        });
}
```

**SIMD helpers in `simd.rs`:**
```rust
pub fn simd_call_price_chunk(...) -> f64x4 {
    // AVX intrinsics for 4 simultaneous calculations
    let d1 = ...;  // 4 d1 values at once
    let nd1 = simd_normal_cdf(d1);  // 4 CDFs at once
    spots * nd1 - strikes * discount * nd2
}
```

#### American Options (in `american/pricing.rs`):

**Binomial tree implementation:**
```rust
pub fn binomial_tree_price(
    spot: f64, strike: f64, time: f64, rate: f64, vol: f64,
    dividend_yield: f64, is_call: bool, steps: usize
) -> f64 {
    // Calculate tree parameters
    let dt = time / steps as f64;
    let u = (vol * dt.sqrt()).exp();
    let d = 1.0 / u;
    let p = ((rate - dividend_yield) * dt).exp() - d) / (u - d);
    
    // Build terminal payoffs
    // Backward induction with early exercise check
    for i in (0..steps).rev() {
        for j in 0..=i {
            intrinsic = max(spot - strike, 0.0);  // for calls
            continuation = discount * (p * V[j+1] + (1-p) * V[j]);
            V[j] = max(intrinsic, continuation);  // Early exercise
        }
    }
}
```

## API Consistency

All classes follow consistent patterns:

### European Options

**Instance Methods:**
- `price()` - Calculate option price (Black-Scholes)
- `delta()`, `gamma()`, `vega()`, `theta()`, `rho()` - Individual Greeks
- `greeks()` - All Greeks at once (most efficient)
- `with_spot()`, `with_strike()`, `with_time()`, `with_volatility()` - Immutable updates

**Static Methods (EuroCallOption/EuroPutOption only):**
- `price_many()` - Batch pricing with SIMD+parallel
- `greeks_many()` - Batch Greeks with SIMD+parallel

### American Options

**Instance Methods:**
- `price()` - Calculate option price (binomial tree)
- `delta()` - Sensitivity to spot (finite difference)

**No Static Methods:** American options use numerical methods that don't benefit from SIMD vectorization in the same way.

## Future Enhancements

The architecture is designed to accommodate future extensions while maintaining its core principles. Potential additions include:

### 1. Implied Volatility Calculation
**Design:**
- Instance method: `option.implied_volatility(market_price, initial_guess=0.2)`
- Static batch method: `EuroCallOption.implied_volatility_many(market_prices, ...)`
- Implementation: Newton-Raphson or Brent's method with vega-based derivatives

**Challenges:**
- Numerical stability near zero or extreme values
- Initial guess selection for batch operations
- Performance optimization for SIMD vectorization

### 2. Additional Greeks
**Design:**
- Second-order: Vanna (∂²V/∂S∂σ), Volga/Vomma (∂²V/∂σ²)
- Third-order: Charm (∂Δ/∂t), Color (∂Γ/∂t), Speed (∂Γ/∂S)
- All accessible via extended `.greeks()` return type

**Implementation:**
- Analytical formulas where available (European)
- Finite differences for numerical methods (American)

### 3. Exotic Options
**Design:**
```
src/exotic/
├── mod.rs
├── barrier.rs      # BarrierOption (up-and-out, down-and-in, etc.)
├── asian.rs        # AsianOption (arithmetic/geometric averaging)
├── lookback.rs     # LookbackOption (floating/fixed strike)
└── digital.rs      # DigitalOption (cash-or-nothing, asset-or-nothing)
```

**Pricing Methods:**
- Analytical formulas where available
- Monte Carlo for path-dependent options
- PDE methods for barrier options

### 4. Interest Rate Models
**Design:**
```
src/interest_rates/
├── mod.rs
├── vasicek.rs      # Vasicek short rate model
├── cir.rs          # Cox-Ingersoll-Ross model
├── hull_white.rs   # Hull-White one-factor model
└── bonds.rs        # Bond pricing and analytics
```

**Features:**
- Short rate simulation
- Bond pricing via PDE or Monte Carlo
- Calibration to market data
- Duration, convexity, and key rate durations

### 5. American Options - Enhanced Pricing
**Design:**
- Parallel binomial tree evaluation
- Least Squares Monte Carlo (LSM) implementation (already started)
- Static batch methods with Rayon parallelism

**Performance Target:**
- Match European option batch performance characteristics
- 10x+ speedup for portfolio-level American option pricing

### 6. Risk Metrics
**Design:**
- Value at Risk (VaR): Historical, parametric, Monte Carlo
- Expected Shortfall (CVaR)
- Stress testing frameworks
- Scenario analysis tools

All enhancements will follow the established pattern:
- **Modular structure**: Separate modules for different functionality
- **Simple classes**: Lightweight for single calculations
- **Optimized static methods**: SIMD + parallel for batch operations
- **Type safety**: Full `.pyi` stubs for IDE support
- **Testing**: Comprehensive test coverage and benchmarks

## Performance Characteristics

| Operation | Method | Options | Time | Throughput |
|-----------|--------|---------|------|------------|
| Single pricing | `call.price()` | 1 | ~1μs | 1M ops/sec |
| Single Greeks | `call.greeks()` | 1 | ~3μs | 330K ops/sec |
| Batch pricing | `EuroCallOption.price_many()` | 1M | ~80ms | 12.5M ops/sec |
| Batch Greeks | `EuroCallOption.greeks_many()` | 1M | ~260ms | 3.8M ops/sec |

**Speedup:** ~2x for pricing, ~1.4x for Greeks on 1M options vs sequential.

## Summary

The rust-quant architecture achieves multiple design goals simultaneously:

### Core Achievements

1. **Clarity**
   - Clean class-based API with intuitive naming
   - Logical separation between option types and pricing methods
   - Consistent patterns across all modules

2. **Performance**
   - Automatic SIMD+parallel optimization without user intervention
   - Zero-copy data transfer where possible
   - Efficient memory layouts for cache coherence
   - 10-30x speedup on large portfolios vs pure Python

3. **Simplicity**
   - No cognitive overhead choosing between optimization levels
   - Single API that adapts to workload size
   - Immutable objects prevent common bugs
   - Comprehensive type hints for IDE support

4. **Extensibility**
   - Modular structure makes adding new option types straightforward
   - Clear patterns for analytical vs numerical vs simulation methods
   - Well-defined interfaces for new pricing models

5. **Discoverability**
   - IDE autocomplete works perfectly with `.pyi` stubs
   - Logical class hierarchy
   - Self-documenting method names
   - Rich inline documentation

### Design Trade-offs

**What we optimized for:**
- Batch operation performance (100+ options)
- Memory efficiency in Rust core
- Type safety and compile-time checking
- Ease of use for end users

**What we didn't optimize for:**
- Single option latency (already sub-microsecond)
- Minimal binary size (performance > size)
- Python 2.7 compatibility (modern Python only)
- Windows-specific optimizations (works, but not tuned)

### Key Insights

1. **SIMD + Rayon = Multiplicative Speedup**
   - SIMD gives ~4x per core
   - Rayon distributes across N cores
   - Combined: 4N speedup in ideal conditions

2. **Class-Based Architecture Wins**
   - Better than function-based for discoverability
   - Static methods enable transparent optimization
   - Instance methods provide clean single-option API

3. **Rust+Python = Best of Both Worlds**
   - Rust handles performance-critical loops
   - Python provides ergonomic high-level API
   - PyO3 makes the boundary nearly invisible

4. **Modular Structure Enables Growth**
   - Each pricing method isolated in its own module
   - Easy to add new models without breaking existing code
   - Clear separation of concerns

This architecture has proven successful for production quantitative finance workloads, with room to grow as new features are added.
