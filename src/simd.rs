use wide::{f64x4, CmpLt};

/// SIMD Normal CDF using Hart's approximation (1968) - accurate to 7.5e-8
#[inline]
pub fn simd_normal_cdf(x: f64x4) -> f64x4 {
    let zero = f64x4::splat(0.0);
    let one = f64x4::splat(1.0);
    let half = f64x4::splat(0.5);

    let abs_x = x.abs();
    let t = one / (one + f64x4::splat(0.2316419) * abs_x);

    // Polynomial coefficients
    let b1 = f64x4::splat(0.319381530);
    let b2 = f64x4::splat(-0.356563782);
    let b3 = f64x4::splat(1.781477937);
    let b4 = f64x4::splat(-1.821255978);
    let b5 = f64x4::splat(1.330274429);

    let poly = t * (b1 + t * (b2 + t * (b3 + t * (b4 + t * b5))));

    // Standard normal PDF at x
    let inv_sqrt_2pi = f64x4::splat(0.3989422804014327);
    let exp_term = (-abs_x * abs_x * half).exp();
    let pdf = inv_sqrt_2pi * exp_term;

    let cdf = one - pdf * poly;

    // Handle negative values: N(-x) = 1 - N(x)
    let is_negative = x.cmp_lt(zero);
    is_negative.blend(one - cdf, cdf)
}

/// SIMD Call option price calculation
#[inline]
pub fn simd_call_price_chunk(
    spots: f64x4,
    strikes: f64x4,
    times: f64x4,
    rates: f64x4,
    vols: f64x4,
) -> f64x4 {
    let half = f64x4::splat(0.5);

    // Calculate d1
    let ln_s_k = (spots / strikes).ln();
    let vol_squared_half = vols * vols * half;
    let numerator = ln_s_k + (rates + vol_squared_half) * times;
    let vol_sqrt_t = vols * times.sqrt();
    let d1 = numerator / vol_sqrt_t;

    // Calculate d2
    let d2 = d1 - vol_sqrt_t;

    // Calculate price
    let nd1 = simd_normal_cdf(d1);
    let nd2 = simd_normal_cdf(d2);
    let discount = (-rates * times).exp();

    spots * nd1 - strikes * discount * nd2
}

/// SIMD Put option price calculation
#[inline]
pub fn simd_put_price_chunk(
    spots: f64x4,
    strikes: f64x4,
    times: f64x4,
    rates: f64x4,
    vols: f64x4,
) -> f64x4 {
    let half = f64x4::splat(0.5);

    // Calculate d1
    let ln_s_k = (spots / strikes).ln();
    let vol_squared_half = vols * vols * half;
    let numerator = ln_s_k + (rates + vol_squared_half) * times;
    let vol_sqrt_t = vols * times.sqrt();
    let d1 = numerator / vol_sqrt_t;

    // Calculate d2
    let d2 = d1 - vol_sqrt_t;

    // Calculate price using N(-d2) and N(-d1)
    let n_minus_d1 = simd_normal_cdf(-d1);
    let n_minus_d2 = simd_normal_cdf(-d2);
    let discount = (-rates * times).exp();

    strikes * discount * n_minus_d2 - spots * n_minus_d1
}

/// SIMD Call option Greeks calculation
#[inline]
pub fn simd_call_greeks_chunk(
    spots: f64x4,
    strikes: f64x4,
    times: f64x4,
    rates: f64x4,
    vols: f64x4,
) -> (f64x4, f64x4, f64x4, f64x4, f64x4, f64x4) {
    let half = f64x4::splat(0.5);
    let inv_sqrt_2pi = f64x4::splat(0.3989422804014327);
    let days_per_year = f64x4::splat(365.0);
    let hundred = f64x4::splat(100.0);

    // Calculate d1 and d2
    let ln_s_k = (spots / strikes).ln();
    let vol_squared_half = vols * vols * half;
    let numerator = ln_s_k + (rates + vol_squared_half) * times;
    let vol_sqrt_t = vols * times.sqrt();
    let d1 = numerator / vol_sqrt_t;
    let d2 = d1 - vol_sqrt_t;

    // Calculate CDFs and PDF
    let nd1 = simd_normal_cdf(d1);
    let nd2 = simd_normal_cdf(d2);
    let discount = (-rates * times).exp();
    let pdf_d1 = inv_sqrt_2pi * (-(d1 * d1) * half).exp();

    // Price
    let price = spots * nd1 - strikes * discount * nd2;

    // Delta
    let delta = nd1;

    // Gamma
    let gamma = pdf_d1 / (spots * vols * times.sqrt());

    // Vega
    let vega = spots * times.sqrt() * pdf_d1 / hundred;

    // Theta
    let term1 = -(spots * pdf_d1 * vols) / (f64x4::splat(2.0) * times.sqrt());
    let term2 = rates * strikes * discount * nd2;
    let theta = (term1 - term2) / days_per_year;

    // Rho
    let rho = strikes * times * discount * nd2 / hundred;

    (price, delta, gamma, vega, theta, rho)
}

/// SIMD Put option Greeks calculation
#[inline]
pub fn simd_put_greeks_chunk(
    spots: f64x4,
    strikes: f64x4,
    times: f64x4,
    rates: f64x4,
    vols: f64x4,
) -> (f64x4, f64x4, f64x4, f64x4, f64x4, f64x4) {
    let half = f64x4::splat(0.5);
    let one = f64x4::splat(1.0);
    let inv_sqrt_2pi = f64x4::splat(0.3989422804014327);
    let days_per_year = f64x4::splat(365.0);
    let hundred = f64x4::splat(100.0);

    // Calculate d1 and d2
    let ln_s_k = (spots / strikes).ln();
    let vol_squared_half = vols * vols * half;
    let numerator = ln_s_k + (rates + vol_squared_half) * times;
    let vol_sqrt_t = vols * times.sqrt();
    let d1 = numerator / vol_sqrt_t;
    let d2 = d1 - vol_sqrt_t;

    // Calculate CDFs and PDF
    let n_minus_d1 = simd_normal_cdf(-d1);
    let n_minus_d2 = simd_normal_cdf(-d2);
    let discount = (-rates * times).exp();
    let pdf_d1 = inv_sqrt_2pi * (-(d1 * d1) * half).exp();

    // Price
    let price = strikes * discount * n_minus_d2 - spots * n_minus_d1;

    // Delta (N(d1) - 1 for puts)
    let delta = simd_normal_cdf(d1) - one;

    // Gamma (same for calls and puts)
    let gamma = pdf_d1 / (spots * vols * times.sqrt());

    // Vega (same for calls and puts)
    let vega = spots * times.sqrt() * pdf_d1 / hundred;

    // Theta
    let term1 = -(spots * pdf_d1 * vols) / (f64x4::splat(2.0) * times.sqrt());
    let term2 = rates * strikes * discount * n_minus_d2;
    let theta = (term1 + term2) / days_per_year;

    // Rho
    let rho = -strikes * times * discount * n_minus_d2 / hundred;

    (price, delta, gamma, vega, theta, rho)
}
