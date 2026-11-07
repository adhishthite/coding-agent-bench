import unittest
from decimal import Decimal

from portfolio.report import realized_pnl_report


class ReportTest(unittest.TestCase):
    def test_single_round_trip(self):
        trades = [
            {"date": "2026-01-05", "symbol": "ABC", "side": "BUY", "qty": 10, "price": 100},
            {"date": "2026-01-20", "symbol": "ABC", "side": "SELL", "qty": 10, "price": 110},
        ]
        # gross 100.00; sell turnover 1100 -> brokerage 0.33 + tax 1.10 = 1.43
        self.assertEqual(realized_pnl_report(trades), {("ABC", "2026-01"): Decimal("98.57")})

    def test_no_sells(self):
        trades = [{"date": "2026-01-05", "symbol": "ABC", "side": "BUY", "qty": 1, "price": 10}]
        self.assertEqual(realized_pnl_report(trades), {})


if __name__ == "__main__":
    unittest.main()
