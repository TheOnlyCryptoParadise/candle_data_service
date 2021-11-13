from os import pardir
import flask
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class Exchange(BaseModel):
    name: str
    ticker_settings: Dict[str, List[str]]

class DownloadSettingsRequest(BaseModel):
    exchanges: Dict[str, Dict[str, List[str]]]

class CandlesRequest(BaseModel):
    exchange: str
    currency_pair: str
    candle_size: str
    time_start: Optional[int]
    time_end: Optional[int]
    last_n_candles: Optional[int]
    download_on_demand : bool = True

class DownloadExchangeInfo(BaseModel):
    name: str
    pairs: List[str]
    candle_sizes: List[str]

class DownloadCandlesRequest(BaseModel):
    exchanges: List[DownloadExchangeInfo]
    last_n_candles: Optional[int]
    time_start: Optional[int]
    time_end: Optional[int]
    
class CurrencyLiveInfoExchange(BaseModel):
    name: str
    pairs: List[str]

class CurrencyLiveInfoRequest(BaseModel):
    exchanges: List[CurrencyLiveInfoExchange]

class Candle(BaseModel):
    open: float
    high: float
    low: float
    close: float
    volume: float
    time: int

class CandleResponse(BaseModel):
    data: List[Candle]

class Settings(BaseModel):
    exchanges: List[Exchange]

class LivePriceExchangesRequest(BaseModel):
    name: str
    pairs: List[str]

class LivePriceRequest(BaseModel):
    exchanges: List[LivePriceExchangesRequest]
