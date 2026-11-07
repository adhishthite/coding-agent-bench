"""Trading charges.

Brokerage: 0.03% of turnover per order, capped at 20.00 per order.
Transaction tax: 0.1% of turnover, on SELL orders only.
Every charge is rounded with money.to_money.
"""
from decimal import Decimal

from .money import to_money

BROKERAGE_RATE = Decimal("0.003")
BROKERAGE_CAP = Decimal("20.00")
TAX_RATE = Decimal("0.001")


def brokerage(turnover) -> Decimal:
    return to_money(min(Decimal(turnover) * BROKERAGE_RATE, BROKERAGE_CAP))


def transaction_tax(turnover, side: str) -> Decimal:
    if side == "SELL":
        return to_money(Decimal(turnover) * TAX_RATE)
    return to_money(0)


def total_charges(turnover, side: str) -> Decimal:
    return to_money(brokerage(turnover) + transaction_tax(turnover, side))
