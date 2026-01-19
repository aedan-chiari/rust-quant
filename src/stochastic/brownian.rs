use pyo3::prelude::*;
use rayon::prelude::*;

use super::rng::generate_normals;

/// Brownian Motion (Wiener Process) path generator.
///
/// Generates sample paths of standard Brownian motion W(t) with properties:
/// - W(0) = 0
/// - W(t) - W(s) ~ N(0, t-s) for t > s
/// - Independent increments
/// - Continuous paths
#[pyclass]
#[derive(Clone)]
pub struct BrownianMotion {
    /// Time horizon (final time T)
    time_horizon: f64,
    /// Number of time steps
    num_steps: usize,
}

#[pymethods]
impl BrownianMotion {
    /// Create a new Brownian Motion path generator.
    ///
    /// Args:
    ///     time_horizon: Final time T (e.g., 1.0 for 1 year)
    ///     num_steps: Number of discrete time steps (higher = more accurate)
    ///
    /// Examples:
    ///     ```python
    ///     # Generate daily paths for 1 year (252 trading days)
    ///     bm = BrownianMotion(time_horizon=1.0, num_steps=252)
    ///     path = bm.generate_path()
    ///     ```
    #[new]
    pub fn new(time_horizon: f64, num_steps: usize) -> Self {
        assert!(time_horizon > 0.0, "time_horizon must be positive");
        assert!(num_steps > 0, "num_steps must be positive");

        BrownianMotion {
            time_horizon,
            num_steps,
        }
    }

    /// Generate a single Brownian motion path.
    ///
    /// Returns:
    ///     Vector of W(t) values at each time step (length = num_steps + 1, includes W(0)=0)
    pub fn generate_path(&self) -> Vec<f64> {
        self.generate_path_impl()
    }

    /// Generate multiple independent Brownian motion paths.
    ///
    /// Args:
    ///     num_paths: Number of independent paths to generate
    ///
    /// Returns:
    ///     Vector of paths, where each path is a vector of W(t) values.
    ///     Outer vector length = num_paths, inner vector length = num_steps + 1
    pub fn generate_paths(&self, num_paths: usize) -> Vec<Vec<f64>> {
        (0..num_paths).map(|_| self.generate_path_impl()).collect()
    }

    /// Generate multiple paths in parallel (optimized for large simulations).
    ///
    /// Args:
    ///     num_paths: Number of independent paths to generate
    ///
    /// Returns:
    ///     Vector of paths (parallelized generation for speed)
    ///
    /// Performance:
    ///     Uses Rayon for parallel generation. Recommended for num_paths > 100.
    pub fn generate_paths_parallel(&self, num_paths: usize) -> Vec<Vec<f64>> {
        (0..num_paths)
            .into_par_iter()
            .map(|_| self.generate_path_impl())
            .collect()
    }

    /// Get time grid for the paths.
    ///
    /// Returns:
    ///     Vector of time points [0, Δt, 2Δt, ..., T]
    pub fn time_grid(&self) -> Vec<f64> {
        let dt = self.time_horizon / self.num_steps as f64;
        (0..=self.num_steps).map(|i| i as f64 * dt).collect()
    }

    /// Get time step size Δt.
    pub fn dt(&self) -> f64 {
        self.time_horizon / self.num_steps as f64
    }

    /// Get time horizon T.
    pub fn get_time_horizon(&self) -> f64 {
        self.time_horizon
    }

    /// Get number of steps.
    pub fn get_num_steps(&self) -> usize {
        self.num_steps
    }

    /// Generate path with antithetic variates (variance reduction).
    ///
    /// Returns:
    ///     Tuple of (path, antithetic_path) where antithetic uses -Z instead of Z.
    ///     Averaging these two paths reduces variance in Monte Carlo estimation.
    pub fn generate_antithetic_paths(&self) -> (Vec<f64>, Vec<f64>) {
        let dt_sqrt = (self.time_horizon / self.num_steps as f64).sqrt();
        let increments = generate_normals(self.num_steps);

        let mut path = Vec::with_capacity(self.num_steps + 1);
        let mut antithetic_path = Vec::with_capacity(self.num_steps + 1);

        path.push(0.0);
        antithetic_path.push(0.0);

        let mut w = 0.0;
        let mut w_anti = 0.0;

        for &z in increments.iter() {
            w += dt_sqrt * z;
            w_anti += dt_sqrt * (-z); // Antithetic: negate the increment

            path.push(w);
            antithetic_path.push(w_anti);
        }

        (path, antithetic_path)
    }
}

impl BrownianMotion {
    /// Internal implementation of path generation
    fn generate_path_impl(&self) -> Vec<f64> {
        let dt_sqrt = (self.time_horizon / self.num_steps as f64).sqrt();
        let increments = generate_normals(self.num_steps);

        let mut path = Vec::with_capacity(self.num_steps + 1);
        path.push(0.0); // W(0) = 0

        let mut w = 0.0;
        for &z in increments.iter() {
            w += dt_sqrt * z;
            path.push(w);
        }

        path
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_brownian_path_starts_at_zero() {
        let bm = BrownianMotion::new(1.0, 100);
        let path = bm.generate_path();

        assert_eq!(path[0], 0.0, "Brownian motion should start at 0");
        assert_eq!(path.len(), 101, "Path length should be num_steps + 1");
    }

    #[test]
    fn test_time_grid() {
        let bm = BrownianMotion::new(1.0, 100);
        let times = bm.time_grid();

        assert_eq!(times.len(), 101);
        assert_eq!(times[0], 0.0);
        assert!((times[100] - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_dt() {
        let bm = BrownianMotion::new(1.0, 100);
        assert!((bm.dt() - 0.01).abs() < 1e-10);
    }

    #[test]
    fn test_multiple_paths() {
        let bm = BrownianMotion::new(1.0, 100);
        let paths = bm.generate_paths(10);

        assert_eq!(paths.len(), 10);
        for path in paths.iter() {
            assert_eq!(path.len(), 101);
            assert_eq!(path[0], 0.0);
        }
    }

    #[test]
    fn test_parallel_paths() {
        let bm = BrownianMotion::new(1.0, 100);
        let paths = bm.generate_paths_parallel(100);

        assert_eq!(paths.len(), 100);
        for path in paths.iter() {
            assert_eq!(path.len(), 101);
            assert_eq!(path[0], 0.0);
        }
    }

    #[test]
    fn test_antithetic_variates() {
        let bm = BrownianMotion::new(1.0, 100);
        let (path1, path2) = bm.generate_antithetic_paths();

        assert_eq!(path1[0], 0.0);
        assert_eq!(path2[0], 0.0);
        assert_eq!(path1.len(), path2.len());

        // Antithetic paths should have opposite signs (roughly)
        let sum_final = path1[100] + path2[100];
        assert!(
            sum_final.abs() < path1[100].abs(),
            "Antithetic paths should partially cancel"
        );
    }

    #[test]
    fn test_increments_variance() {
        let bm = BrownianMotion::new(1.0, 100);
        let paths = bm.generate_paths(10000);

        // Check that final values W(T) have variance ≈ T = 1.0
        let finals: Vec<f64> = paths.iter().map(|p| *p.last().unwrap()).collect();
        let mean: f64 = finals.iter().sum::<f64>() / finals.len() as f64;
        let variance: f64 =
            finals.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / finals.len() as f64;

        assert!(mean.abs() < 0.05, "Mean of W(T) should be ~0, got {}", mean);
        assert!(
            (variance - 1.0).abs() < 0.1,
            "Variance of W(T) should be ~T=1.0, got {}",
            variance
        );
    }
}
