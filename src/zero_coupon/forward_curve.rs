use pyo3::prelude::*;
use rayon::prelude::*;

use super::curve::ZeroCouponCurve;

/// Forward curve derived from a zero-coupon yield curve.
///
/// This class provides forward rate calculations based on an underlying
/// zero-coupon curve. It's a lightweight wrapper that references the base
/// curve without duplicating data.
///
/// Forward rates represent the interest rate between two future dates,
/// implied by the current zero-coupon curve.
#[pyclass]
#[derive(Debug)]
pub struct ForwardCurve {
    // Reference to the underlying zero coupon curve
    // In Python, this will hold a reference to the curve object
    #[pyo3(get)]
    pub base_curve: Py<ZeroCouponCurve>,
}

#[pymethods]
impl ForwardCurve {
    /// Create a ForwardCurve from a ZeroCouponCurve.
    ///
    /// Args:
    ///     base_curve: The underlying zero-coupon yield curve
    ///
    /// Examples:
    ///     >>> # Create zero-coupon curve
    ///     >>> zc_curve = ZeroCouponCurve(securities)
    ///     >>>
    ///     >>> # Create forward curve
    ///     >>> fwd_curve = ForwardCurve(zc_curve)
    #[new]
    pub fn new(base_curve: Py<ZeroCouponCurve>) -> Self {
        ForwardCurve { base_curve }
    }

    /// Calculate the instantaneous forward rate at a given time.
    ///
    /// The instantaneous forward rate f(t) is defined as:
    /// f(t) = -d(ln DF(t))/dt = r(t) + t * dr(t)/dt
    ///
    /// Approximated using finite differences with a small time step.
    ///
    /// Args:
    ///     t: Time point for the instantaneous forward rate
    ///     dt: Small time step for finite difference (default: 0.0001)
    ///
    /// Returns:
    ///     The instantaneous forward rate
    ///
    /// Raises:
    ///     ValueError: If t is negative
    ///
    /// Examples:
    ///     >>> # Instantaneous forward rate at 2 years
    ///     >>> inst_fwd = fwd_curve.instantaneous_forward_rate(2.0)
    #[pyo3(signature = (t, dt=None))]
    pub fn instantaneous_forward_rate(&self, py: Python, t: f64, dt: Option<f64>) -> PyResult<f64> {
        let dt = dt.unwrap_or(0.0001);

        if t < 0.0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Time must be non-negative",
            ));
        }

        let curve = self.base_curve.borrow(py);

        // For t close to 0, use forward rate approximation
        if t < dt {
            let df1 = curve.discount_factor(dt)?;
            let df2 = curve.discount_factor(2.0 * dt)?;
            return Ok((df1 / df2).ln() / dt);
        }

        // Use central difference for better accuracy
        let df_minus = curve.discount_factor(t - dt)?;
        let df_plus = curve.discount_factor(t + dt)?;

        Ok((df_minus / df_plus).ln() / (2.0 * dt))
    }

    /// Calculate the forward rate between two maturities.
    ///
    /// The forward rate f(t1, t2) is the rate that applies between
    /// times t1 and t2, implied by the current zero-coupon curve.
    ///
    /// Formula: f(t1, t2) = [ln(DF(t1)) - ln(DF(t2))] / (t2 - t1)
    ///
    /// Args:
    ///     t1: Start time
    ///     t2: End time (must be > t1)
    ///
    /// Returns:
    ///     The forward rate between t1 and t2
    ///
    /// Raises:
    ///     ValueError: If t2 <= t1 or either is negative
    ///
    /// Examples:
    ///     >>> # 1-year forward rate starting in 2 years (2y1y)
    ///     >>> fwd = fwd_curve.forward_rate(2.0, 3.0)
    pub fn forward_rate(&self, py: Python, t1: f64, t2: f64) -> PyResult<f64> {
        if t1 < 0.0 || t2 < 0.0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Maturities must be non-negative",
            ));
        }

        if t2 <= t1 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Second maturity must be greater than first maturity",
            ));
        }

        let curve = self.base_curve.borrow(py);
        let df1 = curve.discount_factor(t1)?;
        let df2 = curve.discount_factor(t2)?;

        Ok((df1 / df2).ln() / (t2 - t1))
    }

    /// Calculate forward rates for multiple time periods in parallel.
    ///
    /// Uses Rayon parallelism for large datasets (>100 points).
    ///
    /// Args:
    ///     start_times: List of start times
    ///     end_times: List of end times
    ///
    /// Returns:
    ///     List of forward rates for each period
    ///
    /// Raises:
    ///     ValueError: If lists have different lengths
    ///
    /// Examples:
    ///     >>> # Calculate multiple forward rates
    ///     >>> fwds = fwd_curve.forward_rates_many(
    ///     ...     start_times=[1.0, 2.0, 5.0],
    ///     ...     end_times=[2.0, 3.0, 10.0]
    ///     ... )
    pub fn forward_rates_many(
        &self,
        py: Python,
        start_times: Vec<f64>,
        end_times: Vec<f64>,
    ) -> PyResult<Vec<f64>> {
        if start_times.len() != end_times.len() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Start and end times must have same length",
            ));
        }

        // Release GIL for parallel computation
        py.allow_threads(|| {
            if start_times.len() > 100 {
                // Use parallel processing for large datasets
                start_times
                    .par_iter()
                    .zip(end_times.par_iter())
                    .map(|(&t1, &t2)| Python::with_gil(|py| self.forward_rate(py, t1, t2)))
                    .collect()
            } else {
                // Sequential for small datasets
                start_times
                    .iter()
                    .zip(end_times.iter())
                    .map(|(&t1, &t2)| Python::with_gil(|py| self.forward_rate(py, t1, t2)))
                    .collect()
            }
        })
    }

    /// Generate a forward rate term structure.
    ///
    /// Creates a series of consecutive forward rates (e.g., 1y1y, 2y1y, 3y1y...).
    ///
    /// Args:
    ///     start: Starting time
    ///     end: Ending time
    ///     step: Time step between forward rates
    ///
    /// Returns:
    ///     Tuple of (time_points, forward_rates)
    ///
    /// Raises:
    ///     ValueError: If parameters are invalid (start < 0, end <= start, step <= 0)
    ///
    /// Examples:
    ///     >>> # Generate 1-year forward rates from 0 to 10 years
    ///     >>> times, rates = fwd_curve.term_structure(0.0, 10.0, 1.0)
    ///     >>>
    ///     >>> # This gives: 0y1y, 1y1y, 2y1y, ..., 9y1y
    ///     >>> for t, r in zip(times, rates):
    ///     ...     print(f"{t}y1y: {r*100:.2f}%")
    pub fn term_structure(
        &self,
        py: Python,
        start: f64,
        end: f64,
        step: f64,
    ) -> PyResult<(Vec<f64>, Vec<f64>)> {
        if start < 0.0 || end <= start || step <= 0.0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Invalid parameters: need 0 <= start < end and step > 0",
            ));
        }

        let mut times = Vec::new();
        let mut rates = Vec::new();

        let mut t1 = start;
        while t1 < end {
            let t2 = (t1 + step).min(end);
            times.push(t1);
            rates.push(self.forward_rate(py, t1, t2)?);
            t1 += step;
        }

        Ok((times, rates))
    }

    /// Calculate the forward discount factor between two times.
    ///
    /// The forward discount factor represents the value today of $1
    /// to be paid at time t2, given that we're at time t1.
    ///
    /// Formula: FDF(t1, t2) = DF(t2) / DF(t1)
    ///
    /// Args:
    ///     t1: Start time
    ///     t2: End time (must be > t1)
    ///
    /// Returns:
    ///     Forward discount factor
    ///
    /// Raises:
    ///     ValueError: If t2 <= t1
    ///
    /// Examples:
    ///     >>> # Forward discount factor from year 2 to year 5
    ///     >>> fdf = fwd_curve.forward_discount_factor(2.0, 5.0)
    pub fn forward_discount_factor(&self, py: Python, t1: f64, t2: f64) -> PyResult<f64> {
        if t2 <= t1 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Second maturity must be greater than first maturity",
            ));
        }

        let curve = self.base_curve.borrow(py);
        let df1 = curve.discount_factor(t1)?;
        let df2 = curve.discount_factor(t2)?;

        Ok(df2 / df1)
    }

    /// Calculate forward price of a zero-coupon bond.
    ///
    /// Calculates the forward price at time t1 for a zero-coupon bond
    /// maturing at time t2.
    ///
    /// Args:
    ///     t1: Forward date (when price is determined)
    ///     t2: Bond maturity
    ///     face_value: Face value of the bond (default: 100.0)
    ///
    /// Returns:
    ///     Forward price
    ///
    /// Examples:
    ///     >>> # Forward price at year 2 for a bond maturing at year 5
    ///     >>> fwd_price = fwd_curve.forward_bond_price(2.0, 5.0, face_value=100.0)
    #[pyo3(signature = (t1, t2, face_value=None))]
    pub fn forward_bond_price(
        &self,
        py: Python,
        t1: f64,
        t2: f64,
        face_value: Option<f64>,
    ) -> PyResult<f64> {
        let face_value = face_value.unwrap_or(100.0);
        let fdf = self.forward_discount_factor(py, t1, t2)?;
        Ok(face_value * fdf)
    }

    /// Get the underlying zero-coupon curve.
    ///
    /// Returns:
    ///     The base ZeroCouponCurve object
    pub fn get_base_curve(&self, py: Python) -> Py<ZeroCouponCurve> {
        self.base_curve.clone_ref(py)
    }

    fn __repr__(&self) -> String {
        "ForwardCurve(base_curve=ZeroCouponCurve(...))".to_string()
    }

    fn __str__(&self) -> String {
        self.__repr__()
    }
}
