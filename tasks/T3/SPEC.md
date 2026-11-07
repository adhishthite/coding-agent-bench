# Spec: realized_pnl_report(trades)

Implement `realized_pnl_report(trades)` in `portfolio/report.py`.

## Input
A list of trades. Each trade is a dict:
`{"date": "YYYY-MM-DD", "symbol": str, "side": "BUY" or "SELL", "qty": int, "price": number or str}`

## Rules
1. Process trades in date order. Trades on the same date keep their input order.
2. Use `portfolio.lots.Ledger` for FIFO matching.
3. For each SELL: net P&L = gross realized P&L from `Ledger.sell` minus `total_charges(qty x price, "SELL")`.
4. Charges on BUY trades are NOT part of realized P&L.
5. Group net P&L by `(symbol, "YYYY-MM")` of the SELL date. Only groups with at least one SELL appear.
6. Every value is rounded with `money.to_money`.
7. Return a dict. Keys are in order: symbol A-Z, then month oldest first.
8. A side other than "BUY" or "SELL" raises `ValueError`.
