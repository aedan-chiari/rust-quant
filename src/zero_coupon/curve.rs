use pyo3::prelude::*;
use rayon::prelude::*;

/// Represents a bond security (either zero-coupon or coupon-bearing).
///
/// Can represent both zero-coupon bonds (coupon_rate=0 or frequency=0) and
/// coupon-bearing bonds with annual, semi-annual, or quarterly payments.
#[pyclass]
#[derive(Clone, Debug)]
pub struct Security {
    #[pyo3(get)]
    pub maturity: f64,
    #[pyo3(get)]
    pub price: f64,
    #[pyo3(get)]
    pub face_value: f64,
    #[pyo3(get)]
    pub coupon_rate: f64,
    #[pyo3(get)]
    pub frequency: usize, // Coupon frequency per year (0=zero-coupon, 1=annual, 2=semi-annual, 4=quarterly)
}

#[pymethods]
impl Security {
    /// Create a bond security.
    ///
    /// Args:
    ///     maturity: Time to maturity in years
    ///     price: Current market price of the bond
    ///     face_value: Face/par value of the bond (default 100.0)
    ///     coupon_rate: Annual coupon rate as decimal (e.g., 0.05 for 5%, default 0.0)
    ///     frequency: Coupon payment frequency per year (0=zero-coupon, 1=annual,
    ///                2=semi-annual, 4=quarterly, default 0)
    ///
    /// Examples:
    ///     >>> # Zero-coupon bond
    ///     >>> Security(maturity=1.0, price=95.0)
    ///     >>>
    ///     >>> # 5% semi-annual coupon bond
    ///     >>> Security(maturity=2.0, price=98.0, coupon_rate=0.05, frequency=2)
    #[new]
    #[pyo3(signature = (maturity, price, face_value=100.0, coupon_rate=0.0, frequency=0))]
    pub fn new(
        maturity: f64,
        price: f64,
        face_value: f64,
        coupon_rate: f64,
        frequency: usize,
    ) -> Self {
        Security {
            maturity,
            price,
            face_value,
            coupon_rate,
            frequency,
        }
    }

    /// Check if this is a zero-coupon bond (no coupons).
    pub fn is_zero_coupon(&self) -> bool {
        self.coupon_rate == 0.0 || self.frequency == 0
    }

    fn __repr__(&self) -> String {
        if self.is_zero_coupon() {
            format!(
                "Security(maturity={:.4}, price={:.4}, face_value={:.4})",
                self.maturity, self.price, self.face_value
            )
        } else {
            format!(
                "Security(maturity={:.4}, price={:.4}, coupon={:.4}, face={:.4}, freq={})",
                self.maturity, self.price, self.coupon_rate, self.face_value, self.frequency
            )
        }
    }
}

/// Interpolation method for yield curve calculations.
///
/// This enum defines the interpolation methods available for calculating
/// discount factors between known maturities on a zero-coupon curve.
#[pyclass(eq, eq_int)]
#[derive(Clone, Debug, PartialEq)]
pub enum InterpolationMethod {
    /// Linear interpolation of discount factors.
    ///
    /// Simple and fast interpolation that connects points with straight lines.
    /// Suitable for general purposes where smoothness is not critical.
    Linear,
    /// Log-linear interpolation (piecewise constant forward rates).
    ///
    /// Industry standard interpolation method. Interpolates ln(DF) linearly,
    /// which implies constant forward rates between maturities. This is the
    /// default method used by most financial institutions.
    LogLinear,
    /// Cubic spline interpolation using Hermite polynomials.
    ///
    /// Provides smooth, C¹ continuous curves. Use when smoothness is critical
    /// and you want to avoid oscillations. May not preserve monotonicity.
    CubicSpline,
}

/// Zero-coupon yield curve constructed from securities outstanding.
///
/// Builds a zero-coupon yield curve from market prices of bonds (either
/// zero-coupon or coupon-bearing). Supports:
/// - Bootstrapping from mixed zero-coupon and coupon-bearing bonds
/// - Discount factor calculation with multiple interpolation methods
/// - Zero rate (spot rate) calculation
/// - Forward rate calculation
/// - Present value calculations
/// - High-performance batch operations with Rayon parallelism
///
/// Interpolation Methods:
/// - **log_linear** (default, industry standard): Piecewise constant forward rates
/// - **linear**: Linear interpolation of discount factors
/// - **cubic**: Cubic spline interpolation for smooth curves
#[pyclass]
#[derive(Clone, Debug)]
pub struct ZeroCouponCurve {
    #[pyo3(get)]
    securities: Vec<Security>,

    // Pre-sorted maturities for binary search
    maturities: Vec<f64>,

    // Cached discount factors (aligned with maturities)
    discount_factors: Vec<f64>,

    // Cached zero rates (aligned with maturities)
    zero_rates: Vec<f64>,

    // Interpolation method
    interpolation_method: InterpolationMethod,
}

impl ZeroCouponCurve {
    /// Linear interpolation between two points (inlined for performance)
    #[inline(always)]
    fn linear_interpolate(x: f64, x1: f64, y1: f64, x2: f64, y2: f64) -> f64 {
        y1 + (y2 - y1) * (x - x1) / (x2 - x1)
    }

    /// Log-linear interpolation (piecewise constant forward rates)
    /// This interpolates ln(DF) linearly, which implies constant forward rates
    #[inline(always)]
    fn log_linear_interpolate(t: f64, t1: f64, df1: f64, t2: f64, df2: f64) -> f64 {
        let ln_df1 = df1.ln();
        let ln_df2 = df2.ln();
        let ln_df_t = Self::linear_interpolate(t, t1, ln_df1, t2, ln_df2);
        ln_df_t.exp()
    }

    /// Cubic spline interpolation for discount factors
    /// Uses natural cubic spline (second derivatives = 0 at endpoints)
    fn cubic_spline_interpolate(&self, t: f64, idx1: usize, idx2: usize) -> f64 {
        // For simplicity, we'll use Hermite interpolation (locally cubic)
        // This is simpler than full natural splines but still C1 continuous
        let t1 = self.maturities[idx1];
        let t2 = self.maturities[idx2];
        let df1 = self.discount_factors[idx1];
        let df2 = self.discount_factors[idx2];

        // Estimate derivatives at endpoints using finite differences
        let derivative1 = if idx1 > 0 {
            let t0 = self.maturities[idx1 - 1];
            let df0 = self.discount_factors[idx1 - 1];
            (df1 - df0) / (t1 - t0)
        } else if idx2 + 1 < self.maturities.len() {
            // Forward difference
            let t3 = self.maturities[idx2 + 1];
            let _df3 = self.discount_factors[idx2 + 1];
            (df2 - df1) / (t2 - t1).max((t3 - t2) / 2.0)
        } else {
            (df2 - df1) / (t2 - t1)
        };

        let derivative2 = if idx2 + 1 < self.maturities.len() {
            let t3 = self.maturities[idx2 + 1];
            let df3 = self.discount_factors[idx2 + 1];
            (df3 - df2) / (t3 - t2)
        } else if idx1 > 0 {
            // Backward difference
            let t0 = self.maturities[idx1 - 1];
            let _df0 = self.discount_factors[idx1 - 1];
            (df2 - df1) / (t2 - t1).max((t1 - t0) / 2.0)
        } else {
            (df2 - df1) / (t2 - t1)
        };

        // Hermite interpolation
        let h = t2 - t1;
        let s = (t - t1) / h;
        let s2 = s * s;
        let s3 = s2 * s;

        // Hermite basis functions
        let h00 = 2.0 * s3 - 3.0 * s2 + 1.0;
        let h10 = s3 - 2.0 * s2 + s;
        let h01 = -2.0 * s3 + 3.0 * s2;
        let h11 = s3 - s2;

        h00 * df1 + h10 * h * derivative1 + h01 * df2 + h11 * h * derivative2
    }

    /// Interpolate discount factor using the selected method
    fn interpolate_df(
        &self,
        t: f64,
        t1: f64,
        df1: f64,
        t2: f64,
        df2: f64,
        idx1: usize,
        idx2: usize,
    ) -> f64 {
        match self.interpolation_method {
            InterpolationMethod::Linear => Self::linear_interpolate(t, t1, df1, t2, df2),
            InterpolationMethod::LogLinear => Self::log_linear_interpolate(t, t1, df1, t2, df2),
            InterpolationMethod::CubicSpline => self.cubic_spline_interpolate(t, idx1, idx2),
        }
    }

    /// Bootstrap the curve to calculate discount factors and zero rates
    /// Handles both zero-coupon and coupon-bearing bonds
    fn bootstrap(&mut self) {
        // Sort securities by maturity
        self.securities.sort_by(|a, b| {
            a.maturity
                .partial_cmp(&b.maturity)
                .unwrap_or(std::cmp::Ordering::Equal)
        });

        // Pre-allocate vectors with exact capacity
        let n = self.securities.len();
        self.maturities = Vec::with_capacity(n);
        self.discount_factors = Vec::with_capacity(n);
        self.zero_rates = Vec::with_capacity(n);

        // Bootstrap each security sequentially
        for security in &self.securities {
            let discount_factor = if security.is_zero_coupon() {
                // For zero-coupon bonds: DF(T) = Price / Face_Value
                security.price / security.face_value
            } else {
                // For coupon-bearing bonds: solve for DF(T) using already-computed DFs
                let coupon_payment =
                    security.coupon_rate * security.face_value / security.frequency as f64;
                let periods = (security.maturity * security.frequency as f64).round() as usize;

                // Calculate present value of all coupon payments except the last one
                let mut pv_coupons = 0.0;

                for i in 1..periods {
                    let t = i as f64 / security.frequency as f64;

                    // Interpolate discount factor at this time point
                    if let Some(df) = self.interpolate_discount_factor(t) {
                        pv_coupons += coupon_payment * df;
                    }
                }

                // Final cash flow includes last coupon + principal
                let final_cash_flow = coupon_payment + security.face_value;

                // Solve for discount factor: Price = PV(coupons) + DF(T) * final_cash_flow
                (security.price - pv_coupons) / final_cash_flow
            };

            // Zero rate: r(T) = -ln(DF(T)) / T
            let zero_rate = if security.maturity > 0.0 {
                -discount_factor.ln() / security.maturity
            } else {
                0.0
            };

            self.maturities.push(security.maturity);
            self.discount_factors.push(discount_factor);
            self.zero_rates.push(zero_rate);
        }
    }

    /// Interpolate discount factor during bootstrap (internal helper)
    fn interpolate_discount_factor(&self, maturity: f64) -> Option<f64> {
        if self.maturities.is_empty() {
            return None;
        }

        // Find position for interpolation using binary search
        match self.maturities.binary_search_by(|&m| {
            m.partial_cmp(&maturity)
                .unwrap_or(std::cmp::Ordering::Equal)
        }) {
            Ok(idx) => Some(self.discount_factors[idx]),
            Err(idx) => {
                if idx == 0 {
                    // Extrapolate before first point
                    let t1 = self.maturities[0];
                    let df1 = self.discount_factors[0];
                    let zero_rate = -df1.ln() / t1;
                    Some((-zero_rate * maturity).exp())
                } else if idx >= self.maturities.len() {
                    // Extrapolate beyond last point
                    let t1 = self.maturities[self.maturities.len() - 1];
                    let df1 = self.discount_factors[self.maturities.len() - 1];
                    let zero_rate = -df1.ln() / t1;
                    Some((-zero_rate * maturity).exp())
                } else {
                    // Interpolate between idx-1 and idx
                    let t1 = self.maturities[idx - 1];
                    let df1 = self.discount_factors[idx - 1];
                    let t2 = self.maturities[idx];
                    let df2 = self.discount_factors[idx];
                    Some(self.interpolate_df(maturity, t1, df1, t2, df2, idx - 1, idx))
                }
            }
        }
    }

    /// Binary search to find the index for interpolation
    #[inline]
    fn find_bracket(&self, maturity: f64) -> Result<usize, usize> {
        self.maturities.binary_search_by(|&m| {
            m.partial_cmp(&maturity)
                .unwrap_or(std::cmp::Ordering::Equal)
        })
    }
}

#[pymethods]
impl ZeroCouponCurve {
    /// Create a zero-coupon curve from a list of securities.
    ///
    /// The curve automatically bootstraps zero rates from both zero-coupon
    /// and coupon-bearing bonds using iterative bootstrapping.
    ///
    /// Args:
    ///     securities: list of Security objects (can mix zero-coupon and coupon bonds)
    ///     interpolation: Interpolation method ('linear', 'log_linear', 'cubic').
    ///                   Defaults to 'log_linear' (industry standard).
    ///
    /// Raises:
    ///     ValueError: If interpolation method is invalid
    ///
    /// Examples:
    ///     >>> # Default log-linear interpolation (piecewise constant forwards)
    ///     >>> curve = ZeroCouponCurve(securities)
    ///     >>>
    ///     >>> # Linear interpolation of discount factors
    ///     >>> curve = ZeroCouponCurve(securities, interpolation='linear')
    ///     >>>
    ///     >>> # Cubic spline for smooth curves
    ///     >>> curve = ZeroCouponCurve(securities, interpolation='cubic')
    #[new]
    #[pyo3(signature = (securities, interpolation=None))]
    pub fn new(securities: Vec<Security>, interpolation: Option<&str>) -> PyResult<Self> {
        let interpolation_method = match interpolation {
            Some("linear") => InterpolationMethod::Linear,
            Some("log_linear") | Some("loglinear") => InterpolationMethod::LogLinear,
            Some("cubic") | Some("cubic_spline") => InterpolationMethod::CubicSpline,
            None => InterpolationMethod::LogLinear, // Default: industry standard
            Some(other) => {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "Unknown interpolation method '{}'. Use 'linear', 'log_linear', or 'cubic'",
                    other
                )))
            }
        };

        let mut curve = ZeroCouponCurve {
            securities,
            maturities: Vec::new(),
            discount_factors: Vec::new(),
            zero_rates: Vec::new(),
            interpolation_method,
        };
        curve.bootstrap();
        Ok(curve)
    }

    /// Add a new security to the curve and re-bootstrap.
    ///
    /// The curve is automatically re-bootstrapped after adding the security.
    ///
    /// Args:
    ///     security: Security object to add
    ///
    /// Examples:
    ///     >>> curve.add_security(Security(maturity=5.0, price=75.0))
    pub fn add_security(&mut self, security: Security) {
        self.securities.push(security);
        self.bootstrap();
    }

    /// Get the discount factor for a given maturity.
    ///
    /// Uses binary search with O(log n) lookup. Automatically interpolates
    /// between known maturities using the configured interpolation method.
    ///
    /// Args:
    ///     maturity: Time to maturity in years (must be >= 0)
    ///
    /// Returns:
    ///     Discount factor at the given maturity
    ///
    /// Raises:
    ///     ValueError: If maturity is negative
    ///
    /// Examples:
    ///     >>> df = curve.discount_factor(1.5)  # Interpolated using curve's method
    pub fn discount_factor(&self, maturity: f64) -> PyResult<f64> {
        if maturity < 0.0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Maturity must be non-negative",
            ));
        }

        if maturity == 0.0 {
            return Ok(1.0);
        }

        if self.maturities.is_empty() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "No securities available for interpolation",
            ));
        }

        // Use binary search to find position
        match self.find_bracket(maturity) {
            Ok(idx) => {
                // Exact match found
                Ok(self.discount_factors[idx])
            }
            Err(idx) => {
                // Need to interpolate
                if idx == 0 {
                    // Extrapolate before first point
                    let t1 = self.maturities[0];
                    let df1 = self.discount_factors[0];
                    let zero_rate = -df1.ln() / t1;
                    Ok((-zero_rate * maturity).exp())
                } else if idx >= self.maturities.len() {
                    // Extrapolate beyond last point
                    let t1 = self.maturities[self.maturities.len() - 1];
                    let df1 = self.discount_factors[self.maturities.len() - 1];
                    let zero_rate = -df1.ln() / t1;
                    Ok((-zero_rate * maturity).exp())
                } else {
                    // Interpolate between idx-1 and idx
                    let t1 = self.maturities[idx - 1];
                    let df1 = self.discount_factors[idx - 1];
                    let t2 = self.maturities[idx];
                    let df2 = self.discount_factors[idx];
                    Ok(self.interpolate_df(maturity, t1, df1, t2, df2, idx - 1, idx))
                }
            }
        }
    }

    /// Get the current interpolation method being used.
    ///
    /// Returns:
    ///     String identifier: 'linear', 'log_linear', or 'cubic'
    ///
    /// Examples:
    ///     >>> method = curve.get_interpolation_method()
    ///     >>> print(f"Using {method} interpolation")
    pub fn get_interpolation_method(&self) -> String {
        match self.interpolation_method {
            InterpolationMethod::Linear => "linear".to_string(),
            InterpolationMethod::LogLinear => "log_linear".to_string(),
            InterpolationMethod::CubicSpline => "cubic".to_string(),
        }
    }

    /// Get the continuously compounded zero rate for a given maturity.
    ///
    /// Calculated as: r(T) = -ln(DF(T)) / T
    ///
    /// Args:
    ///     maturity: Time to maturity in years (must be >= 0)
    ///
    /// Returns:
    ///     Continuously compounded zero rate (annualized)
    ///
    /// Examples:
    ///     >>> rate = curve.zero_rate(2.0)  # Returns rate as decimal (e.g., 0.05 for 5%)
    pub fn zero_rate(&self, maturity: f64) -> PyResult<f64> {
        if maturity < 0.0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Maturity must be non-negative",
            ));
        }

        if maturity == 0.0 {
            return Ok(0.0);
        }

        let df = self.discount_factor(maturity)?;
        Ok(-df.ln() / maturity)
    }

    /// Get all maturities in the curve (sorted).
    ///
    /// Returns:
    ///     list of maturities in ascending order
    pub fn maturities(&self) -> Vec<f64> {
        self.maturities.clone()
    }

    /// Get zero rates for all securities in the curve.
    ///
    /// Returns:
    ///     list of zero rates corresponding to each security's maturity
    pub fn zero_rates(&self) -> PyResult<Vec<f64>> {
        Ok(self.zero_rates.clone())
    }

    /// Get discount factors for all securities in the curve.
    ///
    /// Returns:
    ///     list of discount factors corresponding to each security's maturity
    pub fn discount_factors(&self) -> PyResult<Vec<f64>> {
        Ok(self.discount_factors.clone())
    }

    /// Calculate present value of a single cash flow.
    ///
    /// Args:
    ///     cash_flow: Amount of the cash flow
    ///     maturity: Time to the cash flow in years
    ///
    /// Returns:
    ///     Present value = cash_flow * DF(maturity)
    ///
    /// Examples:
    ///     >>> pv = curve.present_value(100.0, 2.0)  # PV of $100 in 2 years
    pub fn present_value(&self, cash_flow: f64, maturity: f64) -> PyResult<f64> {
        let df = self.discount_factor(maturity)?;
        Ok(cash_flow * df)
    }

    /// Calculate present value of multiple cash flows.
    ///
    /// Uses parallel processing for large datasets (>100 cash flows).
    ///
    /// Args:
    ///     cash_flows: list of cash flow amounts
    ///     maturities: list of corresponding maturities
    ///
    /// Returns:
    ///     Total present value of all cash flows
    ///
    /// Raises:
    ///     ValueError: If lists have different lengths
    ///
    /// Examples:
    ///     >>> # Value a bond with annual $5 coupons and $100 principal
    ///     >>> pv = curve.present_value_many([5, 5, 105], [1, 2, 3])
    pub fn present_value_many(&self, cash_flows: Vec<f64>, maturities: Vec<f64>) -> PyResult<f64> {
        if cash_flows.len() != maturities.len() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Cash flows and maturities must have same length",
            ));
        }

        // Use parallel processing for large datasets
        if cash_flows.len() > 100 {
            let pv: Result<f64, PyErr> = cash_flows
                .par_iter()
                .zip(maturities.par_iter())
                .map(|(cf, t)| self.discount_factor(*t).map(|df| cf * df))
                .try_reduce(|| 0.0, |a, b| Ok(a + b));
            pv
        } else {
            let mut pv = 0.0;
            for (cf, t) in cash_flows.iter().zip(maturities.iter()) {
                let df = self.discount_factor(*t)?;
                pv += cf * df;
            }
            Ok(pv)
        }
    }

    /// Get the number of securities in the curve.
    ///
    /// Returns:
    ///     Number of securities
    pub fn size(&self) -> usize {
        self.securities.len()
    }

    fn with_security(&self, security: Security) -> Self {
        let mut new_curve = self.clone();
        new_curve.add_security(security);
        new_curve
    }

    fn __repr__(&self) -> String {
        format!(
            "ZeroCouponCurve(securities={}, maturities={:?})",
            self.securities.len(),
            self.maturities()
        )
    }

    /// Build a curve from parallel vectors (convenience method for zero-coupon bonds).
    ///
    /// Args:
    ///     maturities: list of maturities in years
    ///     prices: list of bond prices
    ///     face_values: Optional list of face values (default: 100 for all)
    ///     interpolation: Interpolation method ('linear', 'log_linear', 'cubic').
    ///                   Defaults to 'log_linear' (industry standard).
    ///
    /// Returns:
    ///     ZeroCouponCurve constructed from the vectors
    ///
    /// Raises:
    ///     ValueError: If vector lengths don't match or interpolation method is invalid
    ///
    /// Examples:
    ///     >>> # Default log-linear interpolation
    ///     >>> curve = ZeroCouponCurve.from_vectors(
    ///     ...     maturities=[1.0, 2.0, 5.0],
    ///     ...     prices=[95.0, 90.0, 78.0]
    ///     ... )
    ///     >>>
    ///     >>> # With custom interpolation
    ///     >>> curve = ZeroCouponCurve.from_vectors(
    ///     ...     maturities=[1.0, 2.0, 5.0],
    ///     ...     prices=[95.0, 90.0, 78.0],
    ///     ...     interpolation='linear'
    ///     ... )
    #[staticmethod]
    #[pyo3(signature = (maturities, prices, face_values=None, interpolation=None))]
    pub fn from_vectors(
        maturities: Vec<f64>,
        prices: Vec<f64>,
        face_values: Option<Vec<f64>>,
        interpolation: Option<&str>,
    ) -> PyResult<Self> {
        if maturities.len() != prices.len() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Maturities and prices must have same length",
            ));
        }

        let face_vals = match face_values {
            Some(fv) => {
                if fv.len() != maturities.len() {
                    return Err(pyo3::exceptions::PyValueError::new_err(
                        "Face values must have same length as maturities",
                    ));
                }
                fv
            }
            None => vec![100.0; maturities.len()],
        };

        let securities: Vec<Security> = maturities
            .iter()
            .zip(prices.iter())
            .zip(face_vals.iter())
            .map(|((&mat, &price), &fv)| Security::new(mat, price, fv, 0.0, 0))
            .collect();

        ZeroCouponCurve::new(securities, interpolation)
    }

    /// Batch discount factor calculation with Rayon parallelism.
    ///
    /// Automatically uses parallel processing for large datasets (>100 points).
    ///
    /// Args:
    ///     curve: ZeroCouponCurve to use
    ///     maturities: list of maturities to calculate discount factors for
    ///
    /// Returns:
    ///     list of discount factors
    ///
    /// Examples:
    ///     >>> dfs = ZeroCouponCurve.discount_factors_many(curve, [0.5, 1.0, 1.5, 2.0])
    #[staticmethod]
    pub fn discount_factors_many(
        curve: &ZeroCouponCurve,
        maturities: Vec<f64>,
    ) -> PyResult<Vec<f64>> {
        if maturities.len() > 100 {
            maturities
                .par_iter()
                .map(|&t| curve.discount_factor(t))
                .collect()
        } else {
            maturities
                .iter()
                .map(|&t| curve.discount_factor(t))
                .collect()
        }
    }

    /// Batch zero rate calculation with Rayon parallelism.
    ///
    /// Automatically uses parallel processing for large datasets (>100 points).
    ///
    /// Args:
    ///     curve: ZeroCouponCurve to use
    ///     maturities: list of maturities to calculate zero rates for
    ///
    /// Returns:
    ///     list of zero rates
    ///
    /// Examples:
    ///     >>> rates = ZeroCouponCurve.zero_rates_many(curve, [1.0, 2.0, 5.0, 10.0])
    #[staticmethod]
    pub fn zero_rates_many(curve: &ZeroCouponCurve, maturities: Vec<f64>) -> PyResult<Vec<f64>> {
        if maturities.len() > 100 {
            maturities.par_iter().map(|&t| curve.zero_rate(t)).collect()
        } else {
            maturities.iter().map(|&t| curve.zero_rate(t)).collect()
        }
    }
}
