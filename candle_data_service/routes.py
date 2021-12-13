from asyncio.tasks import current_task
import json
import re
from candle_data_service import model
from flask import request
from candle_data_service import exchange
from candle_data_service import candleDAO
from candle_data_service.candleDAO import get_candleDAO
from candle_data_service.settings import get_settingsManager
from flask import Blueprint
from datetime import datetime
import werkzeug.exceptions
from pydantic import ValidationError
import botocore.exceptions
import asyncio
import math
import logging
import ccxt
from .CandlePeriodicDownloader import CandlePeriodicDownloader, DownloadSettings
from candle_data_service.exchange import (
    get_exchange,
    close_exchange_all,
    ExchangeInterface,
)

main_routes = Blueprint("main_routes", "main_routes")
route_logger = logging.getLogger('route_logger')


def _get_settings_gen():

    with open("DEVsettings.json") as settings_file:
        return model.Settings(**json.load(settings_file))


def _get_available_candles():

    candleDAO = get_candleDAO()
    return candleDAO.get_available_data()


def _get_candles_from_database(req: model.CandlesRequest):

    pass


@main_routes.errorhandler(ValidationError)
def bad_request_handler(e):
    # return "bad request!", 400
    return str(e), 400
@main_routes.errorhandler(ccxt.BaseError)
def bad_request_handler(e):
    # return "bad request!", 400
    return str(e), 400

# @main_routes.errorhandler(ValueError)
# def bad_request_handler(e):
#     # return "bad request!", 400
#     return str(e), 400

# @main_routes.errorhandler(KeyError)
# def bad_request_handler(e):
#     # return "bad request!", 400
#     return str(e), 400


@main_routes.errorhandler(botocore.exceptions.ClientError)
def botocore_exception_hanlder(e):
    # return "internal error", 500
    return str(e), 500


@main_routes.route("/")
@main_routes.route("/index")
def index():
    return "Hello, World!"


@main_routes.route("/downloadSettings", methods=["GET"])
def get_settings():
    dw = CandlePeriodicDownloader()

    settings = dw.download_settings

    return settings.dict(), 200

@main_routes.route("/subscribeCandles", methods=["POST"])
def subscribe_candles():
    dw = CandlePeriodicDownloader()
    dw.addSubscriber(request.get_json())
    return {"result": 200, "msg": "OK"}

@main_routes.route("/unsubscribeCandles", methods=["POST"])
def unsubscribe_candles():
    dw = CandlePeriodicDownloader()
    dw.removeSubscriber(request.get_json())
    return {"result": 200, "msg": "OK"}


@main_routes.route("/downloadSettings", methods=["PUT"])
def put_settings():
    settings = DownloadSettings(**request.get_json())
    dw = CandlePeriodicDownloader()
    dw.set_settings(settings)
    return {"result": 200, "msg": "OK"}


def _candle_size_to_seconds(cs):
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


@main_routes.route("/candles", methods=["GET"])
async def get_candles():
    options = model.CandlesRequest(**request.args)
    options.currency_pair = options.currency_pair.replace("_", "/")
    route_logger.debug(options)
    try:
        
        candleDAO = get_candleDAO()
        if options.download_on_demand:
            try:
                available = candleDAO.get_available_data()
                available = available[options.exchange][options.currency_pair][
                    options.candle_size
                ]
                current_time_start = available[0]['time_start']
                current_time_end = available[0]['time_end']+_candle_size_to_seconds(options.candle_size)
                current_no_candles = available[0]['no_candles']
                candle_in_sec = _candle_size_to_seconds(options.candle_size)
                route_logger.debug(available[0])
                if options.last_n_candles != None:
                    now = datetime.now().timestamp()
                    delta = now - current_time_end # TODO not only 0
                    print(delta)
                    print(now)
                    print(current_time_end)
                    if current_no_candles < options.last_n_candles:
                        request_data = model.DownloadCandlesRequest(
                            exchanges=[
                                model.DownloadExchangeInfo(
                                    name=options.exchange,
                                    pairs=[options.currency_pair],
                                    candle_sizes=[options.candle_size],
                                )
                            ],
                            last_n_candles=options.last_n_candles,
                        )
                        await download_candles_data(request_data)                        
                    elif delta > candle_in_sec:
                        possible_candles = math.floor(delta / candle_in_sec)
                        route_logger.info(f"new candles possible: {possible_candles}")
                        request_data = model.DownloadCandlesRequest(
                            exchanges=[
                                model.DownloadExchangeInfo(
                                    name=options.exchange,
                                    pairs=[options.currency_pair],
                                    candle_sizes=[options.candle_size],
                                )
                            ],
                            last_n_candles=possible_candles,
                        )
                        await download_candles_data(request_data)
                elif options.time_start != None and options.time_end != None:


                    time_start_delta = current_time_start - options.time_start
                    time_end_delta = options.time_end - current_time_end
                    route_logger.debug(f"tsdelta{time_start_delta} te{time_end_delta/3600}")
                    if time_start_delta > 1.0*candle_in_sec:
                        request_data = model.DownloadCandlesRequest(
                            exchanges=[
                                model.DownloadExchangeInfo(
                                    name=options.exchange,
                                    pairs=[options.currency_pair],
                                    candle_sizes=[options.candle_size],
                                )
                            ],
                            time_start=options.time_start,
                            time_end=current_time_start
                        )  
                        await download_candles_data(request_data)
                    if time_end_delta > 1.0*candle_in_sec:
                        request_data = model.DownloadCandlesRequest(
                            exchanges=[
                                model.DownloadExchangeInfo(
                                    name=options.exchange,
                                    pairs=[options.currency_pair],
                                    candle_sizes=[options.candle_size],
                                )
                            ],
                            time_start=current_time_end,
                            time_end=options.time_end
                        )  
                        await download_candles_data(request_data)

            except KeyError:
                route_logger.info("KeyError downloading all")
                request_data = None
                if options.last_n_candles:
                    request_data = model.DownloadCandlesRequest(
                        exchanges=[
                            model.DownloadExchangeInfo(
                                name=options.exchange,
                                pairs=[options.currency_pair],
                                candle_sizes=[options.candle_size],
                            )
                        ],
                        last_n_candles=options.last_n_candles,
                    )  
                else:
                    request_data = model.DownloadCandlesRequest(
                        exchanges=[
                            model.DownloadExchangeInfo(
                                name=options.exchange,
                                pairs=[options.currency_pair],
                                candle_sizes=[options.candle_size],
                            )
                        ],
                        time_start=options.time_start,
                        time_end=options.time_end                        
                    )                    
                await download_candles_data(request_data)
                

        return model.CandleResponse(data=candleDAO.get_candles(options)).dict()

    except botocore.exceptions.ClientError as e:
        print(dir(e))
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            return model.CandleResponse(data=[]).dict()
        raise e



@main_routes.route("/availableCandles", methods=["GET"])
def get_available_candles():
    # options = model.CandlesRequest(**request.args)
    try:
        data = _get_available_candles()
        return {"data": data}
    except botocore.exceptions.ClientError as e:
        print(dir(e))
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            return model.CandleResponse(data=[]).dict()
        raise e


# TODO make fault tolerant and exceptions
@main_routes.route(
    "/currencyPairLiveInfo", methods=["POST"]
)  # TODO add request schema validation
async def get_current_prices():
    request_data = model.CurrencyLiveInfoRequest(**dict(request.get_json()))

    result = []
    for exchange_req in request_data.exchanges:
        exchange_name = exchange_req.name
        exchange = get_exchange(exchange_name)
        result.append(
            {
                "name": exchange_req.name,
                "data": await exchange.get_latest(exchange_req.pairs),
            }
        )

    await close_exchange_all()
    return {"data": result}, 200


@main_routes.route("/downloadCandles", methods=["POST"])
async def download_candles_route():
    request_data = model.DownloadCandlesRequest(**dict(request.get_json()))

    await download_candles_data(request_data)

    return {"msg": "success"}, 200

@main_routes.route("/availableMarkets", methods=["GET"])
async def available_markets():
    ex = get_exchange(request.args['exchange'])
    markets = await ex.get_markets()
    await close_exchange_all()
    return {'data': markets}, 200

@main_routes.route("/availableCurrencies", methods=["GET"])
async def available_currencies():
    ex = get_exchange(request.args['exchange'])
    markets = await ex.get_markets()
    await close_exchange_all()
    pairs = set()
    for pair in markets:
        pair = pair.split("/")[0]
        pairs.add(pair)
    
    markets = list(pairs)
    return {'data': markets}, 200

async def download_candles_data(request_data: model.DownloadCandlesRequest):
    async_reqs = []
    try:

        # Configure and run configured behaviour.
        for exchange in request_data.exchanges:
            for pair in exchange.pairs:
                for candle_size in exchange.candle_sizes:
                    if request_data.last_n_candles:
                        route_logger.info(f"download latest {request_data.last_n_candles} candles ")
                        async_reqs.append(
                            asyncio.create_task(
                                get_exchange(exchange.name).get_historical_data(
                                    pair, candle_size, max_periods=request_data.last_n_candles
                                )
                            )
                        )
                    else:
                        time_delta = request_data.time_end - request_data.time_start
                        missing_candles = math.floor(time_delta / _candle_size_to_seconds(candle_size))
                        route_logger.info(f"download {missing_candles} candles from {request_data.time_start}")
                        async_reqs.append(
                            asyncio.create_task(
                                get_exchange(exchange.name).get_historical_data(
                                    pair, candle_size, start_date=request_data.time_start , max_periods=missing_candles
                                )
                            )
                        )                        

        finished_tasks, pending = await asyncio.wait(async_reqs)
        candle_data = [task.result() for task in finished_tasks]

        candleDAO = get_candleDAO()
        candleDAO.put_candles(candle_data)

        return candle_data
        # loop.close()
    finally:
        await close_exchange_all()

