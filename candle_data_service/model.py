from os import pardir
import flask
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class Exchange(BaseModel):
    name: str
    ticker_settings: Dict[str, List[str]]

class GetCandlesRequest(BaseModel):
    exchange: str
    currency_pair: str
    candle_size: str
    time_start: Optional[int]
    time_end: Optional[int]
    last_n_candles: Optional[int]

class DownloadExchangeInfo(BaseModel):
    name: str
    pairs: List[str]
    candle_sizes: List[str]

class DownloadCandlesRequest(BaseModel):
    exchanges: List[DownloadExchangeInfo]
    last_n_candles: Optional[int]

class Candle(BaseModel):
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: int

class GetCandleResponse(BaseModel):
    data: List[Candle]

class Settings(BaseModel):
    exchanges: List[Exchange]
