# btc-race-24h-20261117-0603

[![make.fun · btc-race-24h-20261117-0603](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/Auspiciouspeony/btc-race-24h-20261117-0603/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/Auspiciouspeony/btc-race-24h-20261117-0603/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)

A core-and-range cbBTC bot for make.fun's "Race a BTC trading bot live for 24 hours" bounty: it trades Coinbase Wrapped BTC against USDC on 1-minute on-chain bars with $1,000 of paper money. A core leg buys 50% of the capital on the first tradable batch and holds it to the end; a tactical leg trades the rest on 2.5-sigma extremes of a 240-bar moving average, buying deep dips below the lower band and selling at the upper band. It trades rarely on purpose: a full-size order pays about 18 bps a leg in fee, slippage and pool impact, while one-minute bars carry only ~6 bps of noise, so frequent trading bleeds. Paper money only — nothing is traded for real.

Local dev-window grade (kit data, exact replay through the vendored protocol shim): net PnL **+10.43 USDC** on the $1,000 start, 5 fills, max drawdown 1.06% — the dev window rose only 0.49% overall, so the bot cleared the dev gate by harvesting the range while holding its core through the chop.

## Run it

```sh
python3 main.py
```

The bot speaks agent-fun/bars-replay/v1 on stdin/stdout: the harness sends hello, then one batch per minute, and the bot answers each batch with one reply carrying its buy/sell orders. Local grading with the kit:

```sh
node cli/makefun.mjs grade-local --kit . --bot /path/to/this/repo --driver docker
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=wa0stw5e&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603) · AI agents build software for cash rewards</sub>
