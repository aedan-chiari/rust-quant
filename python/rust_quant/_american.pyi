from ._types import OptionGreeks

class AmericanCallOption:
    spot: float
    strike: float
    time_to_expiry: float
    risk_free_rate: float
    volatility: float
    dividend_yield: float
    steps: int

    def __init__(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float,
        volatility: float,
        dividend_yield: float = 0.0,
        steps: int = 100,
    ) -> None: ...
    def price(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def vega(self) -> float: ...
    def theta(self) -> float: ...
    def rho(self) -> float: ...
    def greeks(self) -> OptionGreeks: ...
    def with_spot(self, new_spot: float) -> AmericanCallOption: ...
    def with_strike(self, new_strike: float) -> AmericanCallOption: ...
    def with_time(self, new_time: float) -> AmericanCallOption: ...
    def with_volatility(self, new_volatility: float) -> AmericanCallOption: ...
    def with_steps(self, new_steps: int) -> AmericanCallOption: ...
    @staticmethod
    def price_many(
        spots: list[float],
        strikes: list[float],
        times: list[float],
        rates: list[float],
        vols: list[float],
        dividend_yields: list[float],
        steps: int,
    ) -> list[float]: ...
    @staticmethod
    def greeks_many(
        spots: list[float],
        strikes: list[float],
        times: list[float],
        rates: list[float],
        vols: list[float],
        dividend_yields: list[float],
        steps: int,
    ) -> tuple[list[float], list[float], list[float], list[float], list[float], list[float]]: ...
    def price_lsm(self, num_paths: int = 50000, num_steps: int = 50) -> float: ...

class AmericanPutOption:
    spot: float
    strike: float
    time_to_expiry: float
    risk_free_rate: float
    volatility: float
    dividend_yield: float
    steps: int

    def __init__(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float,
        volatility: float,
        dividend_yield: float = 0.0,
        steps: int = 100,
    ) -> None: ...
    def price(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def vega(self) -> float: ...
    def theta(self) -> float: ...
    def rho(self) -> float: ...
    def greeks(self) -> OptionGreeks: ...
    def with_spot(self, new_spot: float) -> AmericanPutOption: ...
    def with_strike(self, new_strike: float) -> AmericanPutOption: ...
    def with_time(self, new_time: float) -> AmericanPutOption: ...
    def with_volatility(self, new_volatility: float) -> AmericanPutOption: ...
    def with_steps(self, new_steps: int) -> AmericanPutOption: ...
    @staticmethod
    def price_many(
        spots: list[float],
        strikes: list[float],
        times: list[float],
        rates: list[float],
        vols: list[float],
        dividend_yields: list[float],
        steps: int,
    ) -> list[float]: ...
    @staticmethod
    def greeks_many(
        spots: list[float],
        strikes: list[float],
        times: list[float],
        rates: list[float],
        vols: list[float],
        dividend_yields: list[float],
        steps: int,
    ) -> tuple[
        list[float],
        list[float],
        list[float],
        list[float],
        list[float],
        list[float],
    ]: ...
    def price_lsm(self, num_paths: int = 50000, num_steps: int = 50) -> float: ...

class AmericanOption:
    spot: float
    strike: float
    time_to_expiry: float
    risk_free_rate: float
    volatility: float
    is_call: bool
    dividend_yield: float
    steps: int

    def __init__(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float,
        volatility: float,
        is_call: bool = True,
        dividend_yield: float = 0.0,
        steps: int = 100,
    ) -> None: ...
    def price(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def vega(self) -> float: ...
    def theta(self) -> float: ...
    def rho(self) -> float: ...
    def with_spot(self, new_spot: float) -> AmericanOption: ...
    def with_time(self, new_time: float) -> AmericanOption: ...
    def with_volatility(self, new_volatility: float) -> AmericanOption: ...
    def with_steps(self, new_steps: int) -> AmericanOption: ...

__all__ = ["AmericanCallOption", "AmericanOption", "AmericanPutOption"]
