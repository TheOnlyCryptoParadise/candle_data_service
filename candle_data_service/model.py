import flask
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
from decimal import Decimal


class Exchange(BaseModel):
    name: str
    ticker_settings: Dict[str, List[str]]


class GetCandlesRequest(BaseModel):
    exchange: str
    currency_pair: str
    ticker: str
    time_start: Optional[int]
    time_end: Optional[int]
    last_n_candles: Optional[int]


class Candle(BaseModel):
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: float
    time: int


class GetCandleResponse(BaseModel):
    data: List[Candle]


class Settings(BaseModel):
    exchanges: List[Exchange]
