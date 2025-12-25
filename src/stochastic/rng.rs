use pyo3::prelude::*;
use rand::SeedableRng;
use rand_xoshiro::Xoshiro256PlusPlus;
use statrs::distribution::{ContinuousCDF, Normal};
use std::cell::RefCell;

thread_local! {
    static RNG: RefCell<Xoshiro256PlusPlus> = RefCell::new(Xoshiro256PlusPlus::from_entropy());
}

/// Thread-safe random number generator for stochastic simulations.
///
/// Uses Xoshiro256++ algorithm for high-quality, fast random number generation.
/// Thread-local storage ensures thread safety in parallel Monte Carlo simulations.
#[pyclass]
#[derive(Clone)]
pub struct StochasticRng {
    seed: Option<u64>,
}

#[pymethods]
impl StochasticRng {
    /// Create a new RNG with optional seed for reproducibility.
    ///
    /// Args:
    ///     seed: Optional seed for reproducible random numbers (default: None for entropy-based)
    ///
    /// Examples:
    ///     ```python
    ///     # Random seed (non-reproducible)
    ///     rng = StochasticRng()
    ///
    ///     # Fixed seed (reproducible)
    ///     rng = StochasticRng(seed=42)
    ///     ```
    #[new]
    #[pyo3(signature = (seed=None))]
    pub fn new(seed: Option<u64>) -> Self {
        if let Some(s) = seed {
            RNG.with(|rng| {
                *rng.borrow_mut() = Xoshiro256PlusPlus::seed_from_u64(s);
            });
        }
        StochasticRng { seed }
    }

    /// Generate a single standard normal random variable (mean=0, std=1).
    pub fn normal(&self) -> f64 {
        generate_normal()
    }

    /// Generate multiple standard normal random variables.
    ///
    /// Args:
    ///     n: Number of random variables to generate
    ///
    /// Returns:
    ///     Vector of n standard normal random variables
    pub fn normals(&self, n: usize) -> Vec<f64> {
        generate_normals(n)
    }

    /// Generate a uniform random variable in [0, 1).
    pub fn uniform(&self) -> f64 {
        generate_uniform()
    }

    /// Get the seed used (if any).
    pub fn get_seed(&self) -> Option<u64> {
        self.seed
    }
}

/// Generate a single standard normal random variable
pub fn generate_normal() -> f64 {
    RNG.with(|rng| {
        let u: f64 = rand::Rng::gen(&mut *rng.borrow_mut());
        let normal = Normal::new(0.0, 1.0).unwrap();
        normal.inverse_cdf(u)
    })
}

/// Generate multiple standard normal random variables (optimized batch generation)
pub fn generate_normals(n: usize) -> Vec<f64> {
    let mut result = Vec::with_capacity(n);
    RNG.with(|rng| {
        let normal = Normal::new(0.0, 1.0).unwrap();
        let mut rng_mut = rng.borrow_mut();
        for _ in 0..n {
            let u: f64 = rand::Rng::gen(&mut *rng_mut);
            result.push(normal.inverse_cdf(u));
        }
    });
    result
}

/// Generate a uniform random variable in [0, 1)
pub fn generate_uniform() -> f64 {
    RNG.with(|rng| rand::Rng::gen(&mut *rng.borrow_mut()))
}

/// Generate correlated normal random variables
///
/// # Arguments
/// * `n` - Number of random variables
/// * `correlation` - Correlation coefficient between -1 and 1
///
/// # Returns
/// Tuple of (Z1, Z2) where Z1 and Z2 are correlated normals
pub fn generate_correlated_normals(n: usize, correlation: f64) -> (Vec<f64>, Vec<f64>) {
    assert!(
        correlation >= -1.0 && correlation <= 1.0,
        "Correlation must be between -1 and 1"
    );

    let z1 = generate_normals(n);
    let z2_independent = generate_normals(n);

    // Cholesky decomposition for 2D case: Z2 = ρ*Z1 + √(1-ρ²)*Z2_independent
    let sqrt_term = (1.0 - correlation * correlation).sqrt();

    let z2: Vec<f64> = z1
        .iter()
        .zip(z2_independent.iter())
        .map(|(z1_val, z2_ind)| correlation * z1_val + sqrt_term * z2_ind)
        .collect();

    (z1, z2)
}
