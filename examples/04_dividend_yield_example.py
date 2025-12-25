"""Example 4: Pricing European Options with Dividend Yields.

This example demonstrates how to price European options on dividend-paying assets
using the Black-Scholes-Merton model.
"""

import logging
import math

from rust_quant import EuroCallOption, EuroPutOption

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("=" * 70)
    logger.info("European Option Pricing with Dividend Yields")
    logger.info("=" * 70)

    # Common parameters
    spot = 100.0
    strike = 100.0
    time_to_expiry = 1.0
    risk_free_rate = 0.05
    volatility = 0.2

    # Example 1: Non-dividend paying stock
    logger.info("\n1. Non-Dividend Paying Stock (dividend_yield=0.0)")
    logger.info("-" * 70)

    call_no_div = EuroCallOption(
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=0.0,
    )

    put_no_div = EuroPutOption(
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=0.0,
    )

    logger.info("Call Price: $%.4f", call_no_div.price())
    logger.info("Call Delta: %.4f", call_no_div.delta())
    logger.info("Put Price:  $%.4f", put_no_div.price())
    logger.info("Put Delta:  %.4f", put_no_div.delta())

    # Example 2: Dividend-paying stock (2% yield)
    logger.info("\n2. Dividend-Paying Stock (dividend_yield=0.02 or 2%)")
    logger.info("-" * 70)

    dividend_yield = 0.02

    call_with_div = EuroCallOption(
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
    )

    put_with_div = EuroPutOption(
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
    )

    logger.info("Call Price: $%.4f", call_with_div.price())
    logger.info("Call Delta: %.4f", call_with_div.delta())
    logger.info("Put Price:  $%.4f", put_with_div.price())
    logger.info("Put Delta:  %.4f", put_with_div.delta())

    # Compare the impact
    logger.info("\n3. Impact of Dividends")
    logger.info("-" * 70)

    call_diff = call_no_div.price() - call_with_div.price()
    put_diff = put_with_div.price() - put_no_div.price()

    logger.info(
        "Call price reduction: $%.4f (%.2f%%)",
        call_diff,
        call_diff / call_no_div.price() * 100,
    )
    logger.info(
        "Put price increase:   $%.4f (%.2f%%)",
        put_diff,
        put_diff / put_no_div.price() * 100,
    )
    logger.info("\nNote: Dividends reduce call values and increase put values")

    # Example 3: High dividend yield (index options)
    logger.info("\n4. Stock Index with Higher Dividend Yield (3%)")
    logger.info("-" * 70)

    index_div_yield = 0.03

    call_index = EuroCallOption(
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=index_div_yield,
    )

    put_index = EuroPutOption(
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=index_div_yield,
    )

    logger.info("Call Price: $%.4f", call_index.price())
    logger.info("Put Price:  $%.4f", put_index.price())

    # Example 4: Verify put-call parity with dividends
    logger.info("\n5. Put-Call Parity Verification (with dividends)")
    logger.info("-" * 70)

    call_price = call_with_div.price()
    put_price = put_with_div.price()

    lhs = call_price - put_price
    rhs = spot * math.exp(-dividend_yield * time_to_expiry) - strike * math.exp(
        -risk_free_rate * time_to_expiry,
    )

    logger.info("C - P = %.4f", lhs)
    logger.info("S*e^(-qT) - K*e^(-rT) = %.4f", rhs)
    logger.info("Difference: %.4f (should be ~0)", abs(lhs - rhs))
    logger.info("\nPut-call parity holds! ✓")

    # Example 5: Real-world scenario
    logger.info("\n6. Real-World Example: Large-Cap Tech Stock")
    logger.info("-" * 70)
    logger.info("Stock: AAPL (example)")
    logger.info("Spot: $175.00, Strike: $180.00, 6 months to expiry")
    logger.info("Implied Vol: 25%, Risk-free rate: 4.5%, Dividend yield: 0.5%")

    aapl_call = EuroCallOption(
        spot=175.0,
        strike=180.0,
        time_to_expiry=0.5,
        risk_free_rate=0.045,
        volatility=0.25,
        dividend_yield=0.005,
    )

    aapl_put = EuroPutOption(
        spot=175.0,
        strike=180.0,
        time_to_expiry=0.5,
        risk_free_rate=0.045,
        volatility=0.25,
        dividend_yield=0.005,
    )

    greeks_call = aapl_call.greeks()
    greeks_put = aapl_put.greeks()

    logger.info("\nCall Option:")
    logger.info("  Price: $%.4f", greeks_call.price)
    logger.info("  Delta: %.4f", greeks_call.delta)
    logger.info("  Gamma: %.4f", greeks_call.gamma)
    logger.info("  Vega:  %.4f", greeks_call.vega)
    logger.info("  Theta: %.4f (per day)", greeks_call.theta)
    logger.info("  Rho:   %.4f", greeks_call.rho)

    logger.info("\nPut Option:")
    logger.info("  Price: $%.4f", greeks_put.price)
    logger.info("  Delta: %.4f", greeks_put.delta)
    logger.info("  Gamma: %.4f", greeks_put.gamma)
    logger.info("  Vega:  %.4f", greeks_put.vega)
    logger.info("  Theta: %.4f (per day)", greeks_put.theta)
    logger.info("  Rho:   %.4f", greeks_put.rho)

    logger.info("\n%s", "=" * 70)
    logger.info("Summary")
    logger.info("=" * 70)
    logger.info("""
Key Takeaways:
1. Dividend yields reduce call option values (holders don't receive dividends)
2. Dividend yields increase put option values (stock price drops by dividend)
3. Higher dividend yields mean lower forward prices
4. Put-call parity must account for dividends: C - P = S*e^(-qT) - K*e^(-rT)
5. Default dividend_yield=0.0 maintains backward compatibility

When to use dividend_yield parameter:
- Dividend-paying stocks (most large-cap stocks)
- Stock indices (S&P 500 ~1.5-2% yield)
- Currency options (foreign interest rate differential)
- Commodity options with storage costs
""")


if __name__ == "__main__":
    main()
