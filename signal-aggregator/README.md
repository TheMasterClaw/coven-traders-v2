# Signal Aggregator — Coven Traders

Multi-source intel pipeline that collects trading signals from:

- **On-chain** — DEX liquidity, whale moves (DexScreener, Etherscan)
- **Social** — Fear & Greed index, X/Twitter sentiment stubs
- **News** — CryptoCompare headlines
- **Technical** — RSI + EMA crossovers via Binance OHLCV
- **Prediction Markets** — Polymarket implied probabilities
- **Arbitrage** — Cross-market price spreads (Binance, Coinbase, DEX)

All signals are normalized to a common `Signal` schema and published to Redis pub/sub on channel `coven:signals`.

## Quick Start

```bash
cd ~/covenant/agora-coven-traders/signal-aggregator
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run the aggregator

```bash
python -m signal_aggregator
```

### Run tests

```bash
pytest -v
```

## Architecture

```
signal_aggregator/
  __init__.py
  schema.py              # Normalized Signal model
  config.py              # Env-based config loader
  aggregator.py          # Async orchestrator + Redis pub/sub
  sources/
    base.py              # Abstract BaseSource
    onchain.py           # OnChainSource
    social.py            # SocialSource
    news.py              # NewsSource
    technical.py         # TechnicalSource
    prediction_market.py # PredictionMarketSource
    arbitrage.py         # ArbitrageSource
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | localhost | Redis host |
| `REDIS_PORT` | 6379 | Redis port |
| `REDIS_CHANNEL` | coven:signals | Pub/sub channel |
| `{SOURCE}_ENABLED` | true | Enable/disable a source |
| `{SOURCE}_POLL_INTERVAL_SEC` | 30.0 | Polling interval |
| `{SOURCE}_API_KEY` | — | API key for the source |

## License

MIT — Agora Agents Hackathon 2026
