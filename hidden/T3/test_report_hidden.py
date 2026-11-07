import unittest
from decimal import Decimal

from portfolio.report import realized_pnl_report


class HiddenReportTest(unittest.TestCase):
    def test_unsorted_input_and_fifo(self):
        trades = [
            {"date": "2026-02-10", "symbol": "ABC", "side": "SELL", "qty": 10, "price": 130},
            {"date": "2026-01-02", "symbol": "ABC", "side": "BUY", "qty": 10, "price": 100},
            {"date": "2026-01-03", "symbol": "ABC", "side": "BUY", "qty": 10, "price": 120},
        ]
        # FIFO gross 300.00; turnover 1300 -> 0.39 + 1.30 = 1.69
        self.assertEqual(realized_pnl_report(trades), {("ABC", "2026-02"): Decimal("298.31")})

    def test_grouping_and_key_order(self):
        trades = [
            {"date": "2026-01-01", "symbol": "XYZ", "side": "BUY", "qty": 4, "price": 50},
            {"date": "2026-01-01", "symbol": "ABC", "side": "BUY", "qty": 4, "price": 10},
            {"date": "2026-03-15", "symbol": "XYZ", "side": "SELL", "qty": 2, "price": 60},
            {"date": "2026-01-20", "symbol": "XYZ", "side": "SELL", "qty": 1, "price": 40},
            {"date": "2026-01-25", "symbol": "XYZ", "side": "SELL", "qty": 1, "price": 55},
            {"date": "2026-02-01", "symbol": "ABC", "side": "SELL", "qty": 4, "price": 12},
        ]
        report = realized_pnl_report(trades)
        self.assertEqual(list(report), [("ABC", "2026-02"), ("XYZ", "2026-01"), ("XYZ", "2026-03")])
        # ABC: gross 8.00; turnover 48 -> 0.01 + 0.05 = 0.06 -> 7.94
        self.assertEqual(report[("ABC", "2026-02")], Decimal("7.94"))
        # XYZ Jan: (-10 - 0.01 - 0.04) + (5 - 0.02 - 0.06) = -10.05 + 4.92 = -5.13
        self.assertEqual(report[("XYZ", "2026-01")], Decimal("-5.13"))
        # XYZ Mar: gross 20.00; turnover 120 -> 0.04 + 0.12 = 0.16 -> 19.84
        self.assertEqual(report[("XYZ", "2026-03")], Decimal("19.84"))

    def test_buy_charges_excluded(self):
        trades = [
            {"date": "2026-01-01", "symbol": "ABC", "side": "BUY", "qty": 1000, "price": 1000},
            {"date": "2026-01-02", "symbol": "ABC", "side": "SELL", "qty": 1000, "price": 1000},
        ]
        # gross 0; turnover 1,000,000 -> brokerage cap 20.00 + tax 1000.00
        self.assertEqual(realized_pnl_report(trades), {("ABC", "2026-01"): Decimal("-1020.00")})

    def test_invalid_side(self):
        with self.assertRaises(ValueError):
            realized_pnl_report([{"date": "2026-01-01", "symbol": "A", "side": "HOLD", "qty": 1, "price": 1}])


if __name__ == "__main__":
    unittest.main()
