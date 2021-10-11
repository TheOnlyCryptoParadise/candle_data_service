import json
from candle_data_service import model
from flask import request
from candle_data_service import exchange
from candle_data_service.candleDAO import get_candleDAO
from candle_data_service.settings import get_settingsManager
from flask import Blueprint
import werkzeug.exceptions
from pydantic import ValidationError
import botocore.exceptions
import asyncio
from candle_data_service.exchange import get_exchange, close_exchange_all, ExchangeInterface

main_routes = Blueprint('main_routes','main_routes')


def _get_settings_gen():

    with open("DEVsettings.json") as settings_file:
        return model.Settings(**json.load(settings_file))


def _get_candles_from_database(req: model.GetCandlesRequest):


    candleDAO = get_candleDAO()
    return model.GetCandleResponse(data=candleDAO.get_candles(req))
    
    
    return model.GetCandleResponse(data=[
        model.Candle(
            
                open=123.1,
                high=124.1,
                low=125.1,
                close=126.1,
                timestamp=123456789,
                volume=127.1
            
        )
    ])

@main_routes.errorhandler(ValidationError)
def bad_request_handler(e):
    return 'bad request!', 400

@main_routes.errorhandler(botocore.exceptions.ClientError)
def botocore_exception_hanlder(e):
    return "internal error", 500


@main_routes.route("/")
@main_routes.route("/index")
def index():
    return "Hello, World!"


@main_routes.route("/settings", methods=["GET"])
def get_settings():

    settings = get_settingsManager().get()

    return settings.dict()


@main_routes.route("/settings", methods=["PUT"])
def put_settings():
    get_settingsManager().set_dict_settings(request.get_json())
    return {"result": 200, "msg": "OK"}
 
@main_routes.route("/candles", methods=["GET"])
def get_candles():
    options = model.GetCandlesRequest(**request.args)
    try:
        data = _get_candles_from_database(options)    
        return  data.dict()
    except botocore.exceptions.ClientError as e:
        print(dir(e))
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            return model.GetCandleResponse(data=[]).dict()
        raise e

#TODO make fault tolerant and exceptions
@main_routes.route("/currencyPairLiveInfo", methods=["POST"]) # TODO add request schema validation
async def get_current_prices():
    currencies = dict(request.get_json()['exchanges'])
    exchange_name = list(currencies.keys())[0]
    exchange = get_exchange(exchange_name)
    result  = await exchange.get_latest(currencies[exchange_name]['pairs'])
    
    await close_exchange_all()
    return result, 200
    

@main_routes.route("/downloadCandles", methods=["POST"])
async def download_candles_route():
    request_data = model.DownloadCandlesRequest(**dict(request.get_json()))

    candle_data = await download_candles(request_data)
    candleDAO = get_candleDAO()
    candleDAO.put_candles(candle_data)

    # loop.close()
    await close_exchange_all()

    return { 'msg': 'success'}, 200


async def download_candles(request_data : model.DownloadCandlesRequest):
    async_reqs = []
    # Configure and run configured behaviour.
    for exchange in request_data.exchanges:
        for pair in exchange.pairs:
            for candle_size in exchange.candle_sizes:
                async_reqs.append(asyncio.create_task(get_exchange(exchange.name).get_historical_data(pair, candle_size, max_periods=5)))


    finished_tasks, pending = await asyncio.wait(async_reqs)
    candle_data = [task.result() for task in finished_tasks]   
    return candle_data