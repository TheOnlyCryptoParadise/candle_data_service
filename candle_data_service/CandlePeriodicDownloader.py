from datetime import datetime
import threading
import pydantic
from typing import Dict, Tuple, List
import asyncio
import ccxt
from candle_data_service.RabbitWrapper import get_candle_q
from .exchange import ExchangeInterface, candle_size_to_seconds
from .candleDAO import get_candleDAO_no_g
import time
import logging
from flask import Blueprint
import ccxt

# example:
#     ex = {
#         "binance": {
#             "15m": [
#                 "BTC/USDT"
#             ]
#         }
#     }

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class DownloadSettings(pydantic.BaseModel):
    exchanges: Dict[str, Dict[str, List[str]]]


class CandlePeriodicDownloader(metaclass=Singleton):
    def __init__(self, download_settings: DownloadSettings = None,  time_interval=60):
        self.time_interval = time_interval
        if download_settings == None:
           download_settings = DownloadSettings(exchanges={
                "binance": {
                    "1m": [
                        "BTC/USDT",
                        "LINK/USDT"
                    ],
                    "5m": [
                        "ETH/USDT",
                        "DOT/USDT"
                    ]
                }
            })
        self.download_settings = download_settings
        self.logger = logging.getLogger(__name__)
        
        

        # self.logger.setLevel(logging.DEBUG) # TODO
        # sh = logging.StreamHandler()
        # sh.setLevel(logging.DEBUG)
        # self.logger.addHandler(sh)
        self.candle_q = get_candle_q()

        self.candle_DAO = get_candleDAO_no_g()
        self.time_interval_lock = threading.Lock()
        self.settings_lock = threading.Lock()
        self.exs_objs = {}
        self.reference_counters = {}
        self._ref_cnt_from_settings(download_settings)
        self.main_loop_thread = threading.Thread(target=self.main_loop, daemon=True)
        self.main_loop_thread.start()
        # self.main_loop()
    def main_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.init_exchanges()
        loops_cnt = 0
        try:
            while True:
                try:
                    self.logger.info("starting download loop")
                    start_time = time.time()
                    self.settings_lock.acquire()
                    self.logger.debug("settings lock acquaired")
                    
                    candles = self.loop.run_until_complete(self.async_download_coroutine(loops_cnt))
                    
                    end_time = time.time()
                    self.settings_lock.release()
                    self.logger.debug("settings lock released")
                    self.logger.debug(candles)
                    self.candle_DAO.put_candles(candles)

                    self.candle_q.publish_candles(candles)

                    self.logger.info("download loop ended")
                    
                    execution_time =  (end_time - start_time)
                    self.logger.info(f"execution took {execution_time}s")
                    
                    self.time_interval_lock.acquire()
                    current_time_interval = self.time_interval
                    self.time_interval_lock.release()
                    
                    loops_cnt +=1
                    
                    if current_time_interval > execution_time:
                        time.sleep(current_time_interval - execution_time)
                except ccxt.RequestTimeout as e:
                    self.logger.warning("ccxt to exchagne - request timeout")
        except KeyboardInterrupt:
            self.loop.run_until_complete(self.close_all_exchanges())
            self.loop.close()

    async def close_all_exchanges(self):
        self.logger.info("closing all exchanges")
        for ex in self.exs_objs.values():
            await ex.close()

    def set_time_interval(self, time_interval):
        try:
            self.time_interval_lock.acquire()
            self.time_interval = time_interval
        finally:
            self.settings_lock.release()      

    def set_settings(self, download_settings: DownloadSettings):
        try:
            self.settings_lock.acquire()
            self.download_settings = download_settings
        finally:
            self.settings_lock.release()

    def addSubscriber(self, sub_setting):
        try:
            self.settings_lock.acquire()

            self.logger.info("add subscriber")
            settings = sub_setting["exchanges"]
            for ex in settings.keys():
                for c_size in settings[ex].keys():
                    for pair in settings[ex][c_size]:
                        self.logger.debug(f"add subscription for pair {pair}{c_size} in {ex}")
                        if not c_size in self.download_settings.exchanges[ex]:
                            self.download_settings.exchanges[ex][c_size] = []
                        if not pair in self.download_settings.exchanges[ex][c_size]:
                            self.download_settings.exchanges[ex][c_size].append(pair)

                        record_id = self._id_from_candle_setting(ex,pair,c_size)
                        if not record_id in self.reference_counters:
                            self.reference_counters[record_id] = 1
                        else:
                            self.reference_counters[record_id] += 1



        finally:
            self.settings_lock.release()

    def removeSubscriber(self, sub_setting):
        try:
            self.settings_lock.acquire()
            
            self.logger.info("remove subscriber")
            settings = sub_setting['exchanges']

            for ex in settings.keys():
                for c_size in settings[ex].keys():
                    for pair in settings[ex][c_size]:
                        record_id = self._id_from_candle_setting(ex,pair,c_size)
                        if not record_id in self.reference_counters or self.reference_counters[record_id] == 0:
                            raise ValueError("no subscription for that candle")
                        self.reference_counters[record_id] -= 1
                        
                        if self.reference_counters[record_id] == 0:
                            self.download_settings.exchanges[ex][c_size].remove(pair)
        finally:
            self.settings_lock.release()


    def _ref_cnt_from_settings(self, settings):
        try:
            self.settings_lock.acquire()
            self.logger.info("setting reference_counters from settings")
            settings = dict(settings)
            for ex in settings.keys():
                for c_size in settings[ex].keys():
                    for pair in settings[ex][c_size]:
                        self.reference_counters[self._id_from_candle_setting(ex,pair,c_size)] = 1
        finally:
            self.settings_lock.release()

    def _id_from_candle_setting(self, ex, pair, c_size):
        return ex + "_" + pair + "_" + c_size

    def init_exchanges(self):
        self.time_interval_lock.acquire()
        for ex_name in self.download_settings.exchanges.keys():
            self.exs_objs[ex_name] = ExchangeInterface(ex_name)
        self.time_interval_lock.release()



    def prepare_async_operations(self, loops_cnt):
        async_reqs = []
        for ex_name in self.download_settings.exchanges.keys():
            ex = self.download_settings.exchanges[ex_name]
            for candle_size in ex.keys():
                candle_size_in_m = candle_size_to_seconds(candle_size) / 60
                if loops_cnt % candle_size_in_m == 0:
                    for pair in ex[candle_size]:
                        self.logger.debug(f"downloading {ex_name}-{pair}-{candle_size} - loops_cnt: {loops_cnt}")
                        async_reqs.append(
                            asyncio.create_task(
                                self.exs_objs[ex_name].get_historical_data(
                                    pair, candle_size, max_periods=1
                                )
                            )
                        )
                else:
                    self.logger.debug(f"skipping {candle_size} - loops_cnt: {loops_cnt}")
        return async_reqs
    
    async def async_download_coroutine(self, loops_cnt):
        async_reqs = self.prepare_async_operations(loops_cnt)
        candle_data = []
        if len(async_reqs) > 0:
            finished_tasks, pending = await asyncio.wait(async_reqs)
            candle_data = [task.result() for task in finished_tasks]
        else:
            candle_data = []
        return candle_data



# candles_periodic_downloader = Blueprint("candles_periodic_downloader", "candles_periodic_downloader")
# dw = CandlePeriodicDownloader(60, DownloadSettings(exs={}))

# dw = CandlePeriodicDownloader(60, DownloadSettings(exchanges=))


if __name__ == '__main__':
    time.sleep(120)
    pass
    # dw = CandlePeriodicDownloader(60, DownloadSettings(exs={
    #     "binance": {
    #         "1m": [
    #             "BTC/USDT",
    #             "LINK/USDT"
    #         ],
    #         "5m": [
    #             "ETH/USDT",
    #             "DOT/USDT"
    #         ]
    #     }
    # }))