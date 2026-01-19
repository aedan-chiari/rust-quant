use pyo3::prelude::*;
use rayon::prelude::*;
use wide::f64x4;

use crate::european::{EuroCallOption, EuroPutOption};
use crate::simd::{
    simd_call_greeks_chunk, simd_call_price_chunk, simd_put_greeks_chunk, simd_put_price_chunk,
};

// SIMD + Parallel implementation functions for use by EuroCallOption/EuroPutOption static methods

/// Fast scalar normal CDF using Hart's approximation (1968) - accurate to 7.5e-8
/// Inline to avoid function call overhead in tight loops
#[inline]
fn scalar_normal_cdf(x: f64) -> f64 {
    if x < 0.0 {
        return 1.0 - scalar_normal_cdf(-x);
    }

    let t = 1.0 / (1.0 + 0.2316419 * x);
    let poly = t
        * (0.319381530
            + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))));
    let inv_sqrt_2pi = 0.3989422804014327;
    let exp_term = (-0.5 * x * x).exp();
    let pdf = inv_sqrt_2pi * exp_term;

    1.0 - pdf * poly
}

/// Inline Black-Scholes call option price calculation (scalar)
/// Optimized for remainder handling - no object allocation
#[inline]
fn black_scholes_call_scalar(spot: f64, strike: f64, time: f64, rate: f64, vol: f64) -> f64 {
    let ln_s_k = (spot / strike).ln();
    let vol_squared_half = vol * vol * 0.5;
    let numerator = ln_s_k + (rate + vol_squared_half) * time;
    let vol_sqrt_t = vol * time.sqrt();
    let d1 = numerator / vol_sqrt_t;
    let d2 = d1 - vol_sqrt_t;

    let nd1 = scalar_normal_cdf(d1);
    let nd2 = scalar_normal_cdf(d2);
    let discount = (-rate * time).exp();

    spot * nd1 - strike * discount * nd2
}

/// Inline Black-Scholes put option price calculation (scalar)
/// Optimized for remainder handling - no object allocation
#[inline]
fn black_scholes_put_scalar(spot: f64, strike: f64, time: f64, rate: f64, vol: f64) -> f64 {
    let ln_s_k = (spot / strike).ln();
    let vol_squared_half = vol * vol * 0.5;
    let numerator = ln_s_k + (rate + vol_squared_half) * time;
    let vol_sqrt_t = vol * time.sqrt();
    let d1 = numerator / vol_sqrt_t;
    let d2 = d1 - vol_sqrt_t;

    let nd1 = scalar_normal_cdf(-d1);
    let nd2 = scalar_normal_cdf(-d2);
    let discount = (-rate * time).exp();

    strike * discount * nd2 - spot * nd1
}

/// SIMD and parallel pricing for multiple call options (optimized)
pub fn price_calls_fast_impl(
    spots: Vec<f64>,
    strikes: Vec<f64>,
    times: Vec<f64>,
    rates: Vec<f64>,
    vols: Vec<f64>,
) -> PyResult<Vec<f64>> {
    let len = spots.len();
    if strikes.len() != len || times.len() != len || rates.len() != len || vols.len() != len {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "All input arrays must have the same length",
        ));
    }

    let chunk_size = 1024;
    let mut prices = vec![0.0; len];

    prices
        .par_chunks_mut(chunk_size)
        .enumerate()
        .for_each(|(chunk_idx, price_chunk)| {
            let start = chunk_idx * chunk_size;
            let end = (start + price_chunk.len()).min(len);
            let local_len = end - start;

            // Process 4 options at a time with SIMD
            let simd_count = local_len / 4;
            for i in 0..simd_count {
                let idx = start + i * 4;
                let spot_simd =
                    f64x4::new([spots[idx], spots[idx + 1], spots[idx + 2], spots[idx + 3]]);
                let strike_simd = f64x4::new([
                    strikes[idx],
                    strikes[idx + 1],
                    strikes[idx + 2],
                    strikes[idx + 3],
                ]);
                let time_simd =
                    f64x4::new([times[idx], times[idx + 1], times[idx + 2], times[idx + 3]]);
                let rate_simd =
                    f64x4::new([rates[idx], rates[idx + 1], rates[idx + 2], rates[idx + 3]]);
                let vol_simd = f64x4::new([vols[idx], vols[idx + 1], vols[idx + 2], vols[idx + 3]]);

                let result =
                    simd_call_price_chunk(spot_simd, strike_simd, time_simd, rate_simd, vol_simd);
                let result_array = result.to_array();

                price_chunk[i * 4] = result_array[0];
                price_chunk[i * 4 + 1] = result_array[1];
                price_chunk[i * 4 + 2] = result_array[2];
                price_chunk[i * 4 + 3] = result_array[3];
            }

            // Handle remaining elements (< 4) with inline scalar calculation
            for i in (simd_count * 4)..local_len {
                let idx = start + i;
                price_chunk[i] = black_scholes_call_scalar(
                    spots[idx],
                    strikes[idx],
                    times[idx],
                    rates[idx],
                    vols[idx],
                );
            }
        });

    Ok(prices)
}

/// SIMD and parallel pricing for multiple put options (optimized)
pub fn price_puts_fast_impl(
    spots: Vec<f64>,
    strikes: Vec<f64>,
    times: Vec<f64>,
    rates: Vec<f64>,
    vols: Vec<f64>,
) -> PyResult<Vec<f64>> {
    let len = spots.len();
    if strikes.len() != len || times.len() != len || rates.len() != len || vols.len() != len {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "All input arrays must have the same length",
        ));
    }

    let chunk_size = 1024;
    let mut prices = vec![0.0; len];

    prices
        .par_chunks_mut(chunk_size)
        .enumerate()
        .for_each(|(chunk_idx, price_chunk)| {
            let start = chunk_idx * chunk_size;
            let end = (start + price_chunk.len()).min(len);
            let local_len = end - start;

            let simd_count = local_len / 4;
            for i in 0..simd_count {
                let idx = start + i * 4;
                let spot_simd =
                    f64x4::new([spots[idx], spots[idx + 1], spots[idx + 2], spots[idx + 3]]);
                let strike_simd = f64x4::new([
                    strikes[idx],
                    strikes[idx + 1],
                    strikes[idx + 2],
                    strikes[idx + 3],
                ]);
                let time_simd =
                    f64x4::new([times[idx], times[idx + 1], times[idx + 2], times[idx + 3]]);
                let rate_simd =
                    f64x4::new([rates[idx], rates[idx + 1], rates[idx + 2], rates[idx + 3]]);
                let vol_simd = f64x4::new([vols[idx], vols[idx + 1], vols[idx + 2], vols[idx + 3]]);

                let result =
                    simd_put_price_chunk(spot_simd, strike_simd, time_simd, rate_simd, vol_simd);
                let result_array = result.to_array();

                price_chunk[i * 4] = result_array[0];
                price_chunk[i * 4 + 1] = result_array[1];
                price_chunk[i * 4 + 2] = result_array[2];
                price_chunk[i * 4 + 3] = result_array[3];
            }

            // Handle remaining elements (< 4) with inline scalar calculation
            for i in (simd_count * 4)..local_len {
                let idx = start + i;
                price_chunk[i] = black_scholes_put_scalar(
                    spots[idx],
                    strikes[idx],
                    times[idx],
                    rates[idx],
                    vols[idx],
                );
            }
        });

    Ok(prices)
}

/// SIMD and parallel Greeks calculation for multiple call options (optimized)
pub fn greeks_calls_fast_impl(
    spots: Vec<f64>,
    strikes: Vec<f64>,
    times: Vec<f64>,
    rates: Vec<f64>,
    vols: Vec<f64>,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>)> {
    let len = spots.len();
    if strikes.len() != len || times.len() != len || rates.len() != len || vols.len() != len {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "All input arrays must have the same length",
        ));
    }

    let chunk_size = 1024;
    let mut prices = vec![0.0; len];
    let mut deltas = vec![0.0; len];
    let mut gammas = vec![0.0; len];
    let mut vegas = vec![0.0; len];
    let mut thetas = vec![0.0; len];
    let mut rhos = vec![0.0; len];

    let results: Vec<_> = (0..len)
        .step_by(chunk_size)
        .collect::<Vec<_>>()
        .par_iter()
        .map(|&start| {
            let end = (start + chunk_size).min(len);
            let local_len = end - start;

            let mut local_prices = vec![0.0; local_len];
            let mut local_deltas = vec![0.0; local_len];
            let mut local_gammas = vec![0.0; local_len];
            let mut local_vegas = vec![0.0; local_len];
            let mut local_thetas = vec![0.0; local_len];
            let mut local_rhos = vec![0.0; local_len];

            // Process 4 options at a time with SIMD
            let simd_count = local_len / 4;
            for i in 0..simd_count {
                let idx = start + i * 4;
                let spot_simd =
                    f64x4::new([spots[idx], spots[idx + 1], spots[idx + 2], spots[idx + 3]]);
                let strike_simd = f64x4::new([
                    strikes[idx],
                    strikes[idx + 1],
                    strikes[idx + 2],
                    strikes[idx + 3],
                ]);
                let time_simd =
                    f64x4::new([times[idx], times[idx + 1], times[idx + 2], times[idx + 3]]);
                let rate_simd =
                    f64x4::new([rates[idx], rates[idx + 1], rates[idx + 2], rates[idx + 3]]);
                let vol_simd = f64x4::new([vols[idx], vols[idx + 1], vols[idx + 2], vols[idx + 3]]);

                let (p, d, g, v, t, r) =
                    simd_call_greeks_chunk(spot_simd, strike_simd, time_simd, rate_simd, vol_simd);

                let p_arr = p.to_array();
                let d_arr = d.to_array();
                let g_arr = g.to_array();
                let v_arr = v.to_array();
                let t_arr = t.to_array();
                let r_arr = r.to_array();

                for j in 0..4 {
                    local_prices[i * 4 + j] = p_arr[j];
                    local_deltas[i * 4 + j] = d_arr[j];
                    local_gammas[i * 4 + j] = g_arr[j];
                    local_vegas[i * 4 + j] = v_arr[j];
                    local_thetas[i * 4 + j] = t_arr[j];
                    local_rhos[i * 4 + j] = r_arr[j];
                }
            }

            // Handle remaining elements (< 4) with scalar code
            for i in (simd_count * 4)..local_len {
                let idx = start + i;
                let option = EuroCallOption::new(
                    spots[idx],
                    strikes[idx],
                    times[idx],
                    rates[idx],
                    vols[idx],
                    0.0,
                );
                let greeks = option.greeks();
                local_prices[i] = greeks.price;
                local_deltas[i] = greeks.delta;
                local_gammas[i] = greeks.gamma;
                local_vegas[i] = greeks.vega;
                local_thetas[i] = greeks.theta;
                local_rhos[i] = greeks.rho;
            }

            (
                start,
                local_prices,
                local_deltas,
                local_gammas,
                local_vegas,
                local_thetas,
                local_rhos,
            )
        })
        .collect();

    // Collect results
    for (start, local_prices, local_deltas, local_gammas, local_vegas, local_thetas, local_rhos) in
        results
    {
        let end = start + local_prices.len();
        prices[start..end].copy_from_slice(&local_prices);
        deltas[start..end].copy_from_slice(&local_deltas);
        gammas[start..end].copy_from_slice(&local_gammas);
        vegas[start..end].copy_from_slice(&local_vegas);
        thetas[start..end].copy_from_slice(&local_thetas);
        rhos[start..end].copy_from_slice(&local_rhos);
    }

    Ok((prices, deltas, gammas, vegas, thetas, rhos))
}

/// SIMD and parallel Greeks calculation for multiple put options (optimized)
pub fn greeks_puts_fast_impl(
    spots: Vec<f64>,
    strikes: Vec<f64>,
    times: Vec<f64>,
    rates: Vec<f64>,
    vols: Vec<f64>,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>)> {
    let len = spots.len();
    if strikes.len() != len || times.len() != len || rates.len() != len || vols.len() != len {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "All input arrays must have the same length",
        ));
    }

    let chunk_size = 1024;
    let mut prices = vec![0.0; len];
    let mut deltas = vec![0.0; len];
    let mut gammas = vec![0.0; len];
    let mut vegas = vec![0.0; len];
    let mut thetas = vec![0.0; len];
    let mut rhos = vec![0.0; len];

    let results: Vec<_> = (0..len)
        .step_by(chunk_size)
        .collect::<Vec<_>>()
        .par_iter()
        .map(|&start| {
            let end = (start + chunk_size).min(len);
            let local_len = end - start;

            let mut local_prices = vec![0.0; local_len];
            let mut local_deltas = vec![0.0; local_len];
            let mut local_gammas = vec![0.0; local_len];
            let mut local_vegas = vec![0.0; local_len];
            let mut local_thetas = vec![0.0; local_len];
            let mut local_rhos = vec![0.0; local_len];

            // Process 4 options at a time with SIMD
            let simd_count = local_len / 4;
            for i in 0..simd_count {
                let idx = start + i * 4;
                let spot_simd =
                    f64x4::new([spots[idx], spots[idx + 1], spots[idx + 2], spots[idx + 3]]);
                let strike_simd = f64x4::new([
                    strikes[idx],
                    strikes[idx + 1],
                    strikes[idx + 2],
                    strikes[idx + 3],
                ]);
                let time_simd =
                    f64x4::new([times[idx], times[idx + 1], times[idx + 2], times[idx + 3]]);
                let rate_simd =
                    f64x4::new([rates[idx], rates[idx + 1], rates[idx + 2], rates[idx + 3]]);
                let vol_simd = f64x4::new([vols[idx], vols[idx + 1], vols[idx + 2], vols[idx + 3]]);

                let (p, d, g, v, t, r) =
                    simd_put_greeks_chunk(spot_simd, strike_simd, time_simd, rate_simd, vol_simd);

                let p_arr = p.to_array();
                let d_arr = d.to_array();
                let g_arr = g.to_array();
                let v_arr = v.to_array();
                let t_arr = t.to_array();
                let r_arr = r.to_array();

                for j in 0..4 {
                    local_prices[i * 4 + j] = p_arr[j];
                    local_deltas[i * 4 + j] = d_arr[j];
                    local_gammas[i * 4 + j] = g_arr[j];
                    local_vegas[i * 4 + j] = v_arr[j];
                    local_thetas[i * 4 + j] = t_arr[j];
                    local_rhos[i * 4 + j] = r_arr[j];
                }
            }

            // Handle remaining elements (< 4) with scalar code
            for i in (simd_count * 4)..local_len {
                let idx = start + i;
                let option = EuroPutOption::new(
                    spots[idx],
                    strikes[idx],
                    times[idx],
                    rates[idx],
                    vols[idx],
                    0.0,
                );
                let greeks = option.greeks();
                local_prices[i] = greeks.price;
                local_deltas[i] = greeks.delta;
                local_gammas[i] = greeks.gamma;
                local_vegas[i] = greeks.vega;
                local_thetas[i] = greeks.theta;
                local_rhos[i] = greeks.rho;
            }

            (
                start,
                local_prices,
                local_deltas,
                local_gammas,
                local_vegas,
                local_thetas,
                local_rhos,
            )
        })
        .collect();

    // Collect results
    for (start, local_prices, local_deltas, local_gammas, local_vegas, local_thetas, local_rhos) in
        results
    {
        let end = start + local_prices.len();
        prices[start..end].copy_from_slice(&local_prices);
        deltas[start..end].copy_from_slice(&local_deltas);
        gammas[start..end].copy_from_slice(&local_gammas);
        vegas[start..end].copy_from_slice(&local_vegas);
        thetas[start..end].copy_from_slice(&local_thetas);
        rhos[start..end].copy_from_slice(&local_rhos);
    }

    Ok((prices, deltas, gammas, vegas, thetas, rhos))
}
