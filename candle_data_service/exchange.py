"""Interface for performing queries against exchange API's
"""

import re
import sys
import time
from datetime import datetime, timedelta, timezone
import logging
from flask import current_app, g
import ccxt.async_support as ccxt
import asyncio
#from tenacity import retry, retry_if_exception_type, stop_after_attempt



class ExchangeInterface():

    def __init__(self, exchange_name):
        self.logger = logging.getLogger().getChild(__name__)

        self.ccxt_exchange = getattr(ccxt, exchange_name)({
                "enableRateLimit": True
            })

            # sets up api permissions for user if given
        if self.ccxt_exchange:
            self.logger.debug("loaded exchange %s", exchange_name)
        else:
            self.logger.error("Unable to load exchange %s", exchange_name)

    async def get_historical_data(self, market_pair, time_unit, start_date=None, max_periods=50000):
        """Get historical OHLCV for a symbol pair

        Decorators:
            retry

        Args:
            market_pair (str): Contains the symbol pair to operate on i.e. BURST/BTC
            exchange (str): Contains the exchange to fetch the historical data from.
            time_unit (str): A string specifying the ccxt time unit i.e. 5m or 1d.
            start_date (int, optional): Timestamp in milliseconds.
            max_periods (int, optional): Defaults to 100. Maximum number of time periods
              back to fetch data for.

        Returns:
            list: Contains a list of lists which contain timestamp, open, high, low, close, volume.
        """
        if max_periods > 10000:
            self.logger.warning(f"you asked for: {max_periods} Are you insane!?")
        historical_data = None
        if start_date:
            historical_data = []
            since = start_date
            while(max_periods > len(historical_data)):
                current_limit = max_periods - len(historical_data)
                if current_limit > 1000:
                    current_limit = 1000
                self.logger.debug(f"downloading {current_limit} candles at once")
                historical_data.extend(await self.ccxt_exchange.fetch_ohlcv(
                    market_pair,
                    timeframe=time_unit,
                    since=int(since*1000),
                    limit=int(current_limit)
                ))
                since += candle_size_to_seconds(time_unit)*current_limit
        else:
            historical_data = []
            now = datetime.utcnow().timestamp()
            since = now - candle_size_to_seconds(time_unit)*max_periods
            while(max_periods > len(historical_data)):
                current_limit = max_periods - len(historical_data)
                if current_limit > 1000:
                    current_limit = 1000
                self.logger.debug(f"downloading {current_limit} candles at once")
                historical_data.extend(await self.ccxt_exchange.fetch_ohlcv(
                    market_pair,
                    timeframe=time_unit,
                    since=int(since*1000),
                    limit=int(current_limit)
                ))
                since += candle_size_to_seconds(time_unit)*current_limit

        if not historical_data:
            raise ValueError(
                'No historical data provided returned by exchange.')
        # Sort by timestamp in ascending order
        historical_data.sort(key=lambda d: d[0])
        if len(historical_data) != max_periods:
            self.logger.warning(f"downloaded data size is different from asked data {len(historical_data)} != {max_periods}")
        self.logger.debug(f"downloaded {len(historical_data)} overall")
        await asyncio.sleep(self.ccxt_exchange.rateLimit / 1000)

        return (market_pair, time_unit, historical_data)

    async def get_latest(self, market_pairs):
        data = await self.ccxt_exchange.fetchTickers(market_pairs)
        return data

    async def close(self):
        return await self.ccxt_exchange.close()

    async def get_markets(self):
        markets = await self.ccxt_exchange.load_markets()
        return list(markets.keys())

def get_exchange(exchange_name) -> ExchangeInterface:
    if "exchanges" not in g:
        g.exchanges = {}
        g.exchanges[exchange_name] = ExchangeInterface("binance")
        
    elif exchange_name not in g.exchanges:
        g.exchanges[exchange_name] = ExchangeInterface("binance")

        
    return g.exchanges[exchange_name]
    
def candle_size_to_seconds(cs):
    num = int(cs[:-1])
    s = cs[-1]
    if s == "m":
        return num * 60
    elif s == "h":
        return num * 3600
    elif s == "d":
        return num * 3600 * 24
    elif s == "w":
        return num * 3600 * 24 * 7
    elif s == "M":
        return num * 3600 * 24 * 30

async def close_exchange_all(e=None):
    exchanges = g.pop("exchanges", None)

    if exchanges is not None:
        for v in exchanges.values():
            await v.close() # TODO not one bye one but parallel
    else:
        logging.warning("exchange was None while closing")


