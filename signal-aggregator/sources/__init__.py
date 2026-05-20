"""Signal sources package."""

from .base import BaseSource
from .onchain import OnChainSource
from .social import SocialSource
from .news import NewsSource
from .technical import TechnicalSource
from .prediction import PredictionSource
from .cross_market import CrossMarketSource

__all__ = [
    "BaseSource",
    "OnChainSource",
    "SocialSource",
    "NewsSource",
    "TechnicalSource",
    "PredictionSource",
    "CrossMarketSource",
]
