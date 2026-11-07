"""Position ledger with FIFO lot matching.

A buy adds a lot. A sell consumes the OLDEST lots first (FIFO).
sell() returns the gross realized P&L: sum of (sell price - lot price) x qty.
Selling more than the held quantity raises ValueError and changes nothing.
"""
from dataclasses import dataclass, field
from decimal import Decimal

from .money import to_money


@dataclass
class Lot:
    qty: int
    price: Decimal


@dataclass
class Ledger:
    lots: dict = field(default_factory=dict)

    def buy(self, symbol: str, qty: int, price) -> None:
        if qty <= 0:
            raise ValueError("qty must be positive")
        self.lots.setdefault(symbol, []).append(Lot(qty, Decimal(str(price))))

    def position(self, symbol: str) -> int:
        return sum(lot.qty for lot in self.lots.get(symbol, []))

    def sell(self, symbol: str, qty: int, price) -> Decimal:
        if qty <= 0:
            raise ValueError("qty must be positive")
        if qty > self.position(symbol):
            raise ValueError("cannot sell more than held")
        price = Decimal(str(price))
        lots = self.lots[symbol]
        pnl = Decimal(0)
        remaining = qty
        while remaining:
            lot = lots[-1]
            take = min(remaining, lot.qty)
            pnl += (price - lot.price) * take
            lot.qty -= take
            remaining -= take
            if lot.qty == 0:
                lots.pop()
        return to_money(pnl)
