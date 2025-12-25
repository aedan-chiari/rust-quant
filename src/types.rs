use pyo3::prelude::*;

/// Container for option price and all Greeks.
#[pyclass]
#[derive(Clone, Debug)]
pub struct OptionGreeks {
    #[pyo3(get)]
    pub price: f64,
    #[pyo3(get)]
    pub delta: f64,
    #[pyo3(get)]
    pub gamma: f64,
    #[pyo3(get)]
    pub vega: f64,
    #[pyo3(get)]
    pub theta: f64,
    #[pyo3(get)]
    pub rho: f64,
}

#[pymethods]
impl OptionGreeks {
    fn __repr__(&self) -> String {
        format!(
            "OptionGreeks(price={:.4}, delta={:.4}, gamma={:.4}, vega={:.4}, theta={:.4}, rho={:.4})",
            self.price, self.delta, self.gamma, self.vega, self.theta, self.rho
        )
    }
}

// Shared trait for option calculations
pub trait OptionCalculations {
    fn get_params(&self) -> (f64, f64, f64, f64, f64, f64);

    fn d1(&self) -> f64 {
        let (spot, strike, time, rate, vol, div_yield) = self.get_params();
        ((spot / strike).ln() + (rate - div_yield + 0.5 * vol * vol) * time) / (vol * time.sqrt())
    }

    fn d2(&self) -> f64 {
        let (_, _, time, _, vol, _) = self.get_params();
        self.d1() - vol * time.sqrt()
    }

    fn standard_normal_pdf(&self, x: f64) -> f64 {
        (-0.5 * x * x).exp() / (2.0 * std::f64::consts::PI).sqrt()
    }

    fn gamma(&self) -> f64 {
        let (spot, _, time, _, vol, div_yield) = self.get_params();
        let d1 = self.d1();
        let pdf = self.standard_normal_pdf(d1);
        (-div_yield * time).exp() * pdf / (spot * vol * time.sqrt())
    }

    fn vega(&self) -> f64 {
        let (spot, _, time, _, _, div_yield) = self.get_params();
        let d1 = self.d1();
        let pdf = self.standard_normal_pdf(d1);
        spot * (-div_yield * time).exp() * time.sqrt() * pdf / 100.0
    }
}
