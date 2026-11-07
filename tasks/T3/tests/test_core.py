import unittest
from decimal import Decimal

from portfolio.money import to_money
from portfolio.fees import brokerage, transaction_tax, total_charges
from portfolio.lots import Ledger


class MoneyTest(unittest.TestCase):
    def test_round_half_up(self):
        self.assertEqual(to_money("2.665"), Decimal("2.67"))
        self.assertEqual(to_money("2.675"), Decimal("2.68"))

    def test_float_input(self):
        self.assertEqual(to_money(0.1), Decimal("0.10"))


class FeesTest(unittest.TestCase):
    def test_brokerage_percentage(self):
        self.assertEqual(brokerage(10000), Decimal("3.00"))

    def test_brokerage_cap(self):
        self.assertEqual(brokerage(1000000), Decimal("20.00"))

    def test_tax_sell_only(self):
        self.assertEqual(transaction_tax(10000, "BUY"), Decimal("0.00"))
        self.assertEqual(transaction_tax(10000, "SELL"), Decimal("10.00"))

    def test_total_charges_sell(self):
        self.assertEqual(total_charges(10000, "SELL"), Decimal("13.00"))


class LedgerTest(unittest.TestCase):
    def test_single_lot(self):
        led = Ledger()
        led.buy("ABC", 10, 100)
        self.assertEqual(led.sell("ABC", 4, 110), Decimal("40.00"))
        self.assertEqual(led.position("ABC"), 6)

    def test_fifo_order(self):
        led = Ledger()
        led.buy("ABC", 10, 100)
        led.buy("ABC", 10, 120)
        # FIFO: the 10 @ 100 lot is sold first.
        self.assertEqual(led.sell("ABC", 10, 130), Decimal("300.00"))

    def test_fifo_across_lots(self):
        led = Ledger()
        led.buy("ABC", 5, 100)
        led.buy("ABC", 5, 120)
        self.assertEqual(led.sell("ABC", 8, 130), Decimal("180.00"))
        self.assertEqual(led.position("ABC"), 2)

    def test_oversell(self):
        led = Ledger()
        led.buy("ABC", 5, 100)
        with self.assertRaises(ValueError):
            led.sell("ABC", 6, 100)
        self.assertEqual(led.position("ABC"), 5)


if __name__ == "__main__":
    unittest.main()
