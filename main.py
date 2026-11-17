"""Range-and-core BTC bot for make.fun btc-race-24h-20261117-0603.

Strategy (fresh design, backtested on the published 24h dev window):
  * Core leg: buy 50% of the $1,000 paper capital in CBBTC on the first
    tradable batch and hold it to the end. This keeps BTC beta on through
    the race and guarantees at least one trade.
  * Tactical leg: with the other 50%, trade the range. Keep a 240-bar
    simple moving average of closes and its standard deviation. Buy all
    remaining cash when the latest close falls below SMA240 - 2.5 sigma
    (a deep dip versus the slow average) and sell exactly the tactical
    quantity when the close reaches SMA240 + 2.5 sigma (the opposite band).
    At most one tactical position at a time; the core is never sold.

Why this shape: on the dev window a full-size $1,000 order pays about
18 bps a leg (4 bps fee + 2 bps slippage + ~12 bps of pool impact), so
frequent trading bleeds. One-minute bars move ~6 bps of noise. The bot
therefore trades rarely (a handful of round trips per day), only on
2.5-sigma extremes, and holds through the noise in between.

Protocol: agent-fun/bars-replay/v1. The bot reads one JSON line per
minute (hello, then a batch per bar, then done) on stdin and answers
each batch with one reply echoing its seq and the orders decided on
that bar. Orders fill at the next bar's open. The vendored
vendor/makefun_bars.py shim owns the wire; this file only decides.

Determinism: every decision is a pure function of the closes seen so
far. No clock, no environment, no randomness, no network, no files
outside the repository. Two runs on the same bars emit identical orders.
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
CORE_FRACTION = 0.5          # share of cash the core leg buys on entry
LOOKBACK = 240               # bars for the slow average and its spread
BAND_SIGMA = 2.5             # buy below mean - k*sd, sell above mean + k*sd
MAX_SLIPPAGE_BPS = 100       # 1%: bounds the move from the latest close
MIN_NOTIONAL = 1_000_000     # $1 in quote units (6 decimals)


def band(closes):
    """(mean, lower, upper) of the last LOOKBACK closes, or None."""
    if len(closes) < LOOKBACK:
        return None
    window = closes[-LOOKBACK:]
    mean = sum(window) / LOOKBACK
    var = sum((c - mean) ** 2 for c in window) / LOOKBACK
    sd = math.sqrt(var)
    if sd == 0:
        # A perfectly flat window has no range to trade; hold.
        return None
    return mean, mean - BAND_SIGMA * sd, mean + BAND_SIGMA * sd


class Bot:
    def __init__(self):
        self.closes = []        # raw close ints, one per batch, in order
        self.core_qty = None    # base qty bought by the core leg (never sold)

    def on_batch(self, state, batch):
        # Warm-up batches are history only: orders decided on them are
        # rejected, so decide nothing until the scored window starts.
        if state.warming_up:
            self.closes.append(state.close(SYMBOL))
            return []
        close = state.close(SYMBOL)
        if close is None:
            return []
        self.closes.append(close)
        holding = state.positions.get(SYMBOL)
        qty = holding.qty if holding else 0

        # Core leg: first tradable batch with no position buys half the cash.
        if self.core_qty is None and qty == 0:
            amount = int(state.cash * CORE_FRACTION)
            if amount >= MIN_NOTIONAL:
                return [{"side": "buy", "symbol": SYMBOL,
                         "notional_quote_units": amount,
                         "max_slippage_bps": MAX_SLIPPAGE_BPS}]
            return []
        # The core buy has filled once a position shows up; remember its size.
        if self.core_qty is None and qty > 0:
            self.core_qty = qty
            return []

        tactical_qty = qty - self.core_qty
        b = band(self.closes)
        if b is None:
            return []
        _, lower, upper = b
        if tactical_qty <= 0 and state.cash >= MIN_NOTIONAL and close < lower:
            return [{"side": "buy", "symbol": SYMBOL,
                     "notional_quote_units": state.cash,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        if tactical_qty > 0 and close >= upper:
            return [{"side": "sell", "symbol": SYMBOL,
                     "qty": tactical_qty,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []


makefun_bars.run(Bot().on_batch)
