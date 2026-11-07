"""Money helpers. All amounts are Decimal rupees with 2 decimal places."""
from decimal import Decimal, ROUND_HALF_EVEN

PAISA = Decimal("0.01")


def to_money(value) -> Decimal:
    """Convert a number or string to money.

    Rule: round to 2 decimal places, with halves rounded UP
    (for example 2.665 -> 2.67). Floats are converted through str()
    so that 0.1 stays 0.10.
    """
    if isinstance(value, float):
        value = str(value)
    return Decimal(value).quantize(PAISA, rounding=ROUND_HALF_EVEN)
