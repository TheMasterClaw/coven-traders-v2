"""CLI entrypoint for the Signal Aggregator."""

import asyncio
import logging
import signal as sys_signal

from signal_aggregator.aggregator import SignalAggregator
from signal_aggregator.config import AggregatorConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


async def main():
    aggregator = SignalAggregator(AggregatorConfig.from_env())
    loop = asyncio.get_running_loop()
    for sig in (sys_signal.SIGINT, sys_signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(aggregator.stop()))
    await aggregator.start()
    # Keep running until interrupted
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
