from ._types import OptionGreeks

class EuroCallOption:
    spot: float
    strike: float
    time_to_expiry: float
    risk_free_rate: float
    volatility: float
    dividend_yield: float

    def __init__(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float,
        volatility: float,
        dividend_yield: float = 0.0,
    ) -> None: ...
    def price(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def vega(self) -> float: ...
    def theta(self) -> float: ...
    def rho(self) -> float: ...
    def greeks(self) -> OptionGreeks: ...
    def with_spot(self, new_spot: float) -> EuroCallOption: ...
    def with_strike(self, new_strike: float) -> EuroCallOption: ...
    def with_time(self, new_time: float) -> EuroCallOption: ...
    def with_volatility(self, new_volatility: float) -> EuroCallOption: ...
    @staticmethod
    def price_many(
        spots: list[float],
        strikes: list[float],
        times: list[float],
        rates: list[float],
        vols: list[float],
    ) -> list[float]: ...
    @staticmethod
    def greeks_many(
        spots: list[float],
        strikes: list[float],
        times: list[float],
        rates: list[float],
        vols: list[float],
    ) -> tuple[list[float], list[float], list[float], list[float], list[float], list[float]]: ...
    def price_monte_carlo(self, num_paths: int = 100000, num_steps: int = 1) -> float: ...
    def price_monte_carlo_antithetic(
        self,
        num_paths: int = 100000,
        num_steps: int = 1,
    ) -> float: ...
    def price_heston(
        self,
        initial_variance: float,
        kappa: float,
        theta: float,
        vol_of_vol: float,
        correlation: float,
        num_paths: int = 100000,
        num_steps: int = 100,
    ) -> float: ...

class EuroPutOption:
    spot: float
    strike: float
    time_to_expiry: float
    risk_free_rate: float
    volatility: float
    dividend_yield: float

    def __init__(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float,
        volatility: float,
        dividend_yield: float = 0.0,
    ) -> None: ...
    def price(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def vega(self) -> float: ...
    def theta(self) -> float: ...
    def rho(self) -> float: ...
    def greeks(self) -> OptionGreeks: ...
    def with_spot(self, new_spot: float) -> EuroPutOption: ...
    def with_strike(self, new_strike: float) -> EuroPutOption: ...
    def with_time(self, new_time: float) -> EuroPutOption: ...
    def with_volatility(self, new_volatility: float) -> EuroPutOption: ...
    @staticmethod
    def price_many(
        spots: list[float],
        strikes: list[float],
        times: list[float],
        rates: list[float],
        vols: list[float],
    ) -> list[float]: ...
    @staticmethod
    def greeks_many(
        spots: list[float],
        strikes: list[float],
        times: list[float],
        rates: list[float],
        vols: list[float],
    ) -> tuple[list[float], list[float], list[float], list[float], list[float], list[float]]: ...
    def price_monte_carlo(self, num_paths: int = 100000, num_steps: int = 1) -> float: ...
    def price_monte_carlo_antithetic(
        self,
        num_paths: int = 100000,
        num_steps: int = 1,
    ) -> float: ...
    def price_heston(
        self,
        initial_variance: float,
        kappa: float,
        theta: float,
        vol_of_vol: float,
        correlation: float,
        num_paths: int = 100000,
        num_steps: int = 100,
    ) -> float: ...

class EuroOption:
    spot: float
    strike: float
    time_to_expiry: float
    risk_free_rate: float
    volatility: float
    is_call: bool
    dividend_yield: float

    def __init__(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float,
        volatility: float,
        is_call: bool = True,
        dividend_yield: float = 0.0,
    ) -> None: ...
    def price(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def vega(self) -> float: ...
    def theta(self) -> float: ...
    def rho(self) -> float: ...
    def greeks(self) -> OptionGreeks: ...
    def with_spot(self, new_spot: float) -> EuroOption: ...
    def with_time(self, new_time: float) -> EuroOption: ...
    def with_volatility(self, new_volatility: float) -> EuroOption: ...

__all__ = ["EuroCallOption", "EuroOption", "EuroPutOption"]
