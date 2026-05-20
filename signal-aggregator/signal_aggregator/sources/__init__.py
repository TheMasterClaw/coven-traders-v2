"""Intel source implementations."""

from signal_aggregator.sources.onchain import OnChainSource
from signal_aggregator.sources.social import SocialSource
from signal_aggregator.sources.news import NewsSource
from signal_aggregator.sources.technical import TechnicalSource
from signal_aggregator.sources.prediction_market import PredictionMarketSource
from signal_aggregator.sources.arbitrage import ArbitrageSource

__all__ = [
    "OnChainSource",
    "SocialSource",
    "NewsSource",
    "TechnicalSource",
    "PredictionMarketSource",
    "ArbitrageSource",
]