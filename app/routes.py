import json
from app import model
from flask import request
from app.candleDAO import get_candleDAO
from app.settings import get_settingsManager
from flask import Blueprint

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

    data = _get_candles_from_database(options)
    return  data.dict()

