"""
Coven Traders — Signal Aggregator
Multi-source intel pipeline for AI disciple trading agents.
"""

__version__ = "0.1.0"
__all__ = ["Signal", "SignalSource", "SignalType", "SignalAggregator"]

from .schema import Signal, SignalSource, SignalType
from .aggregator import SignalAggregator