from app.candleDAO import CandleDAO
from app import app, settingsManager
import json
from app import model
from app import candleDAO
from flask import request


def _get_settings_gen():

    with open("DEVsettings.json") as settings_file:
        return model.Settings(**json.load(settings_file))


def _get_candles_from_database(req: model.CandlesRequest):



    return model.CandleResponse(data=candleDAO.get_candles(req))
    
    
    return model.CandleResponse(data=[
        model.Candle(
            
                open=123.1,
                high=124.1,
                low=125.1,
                close=126.1,
                timestamp=123456789,
                volume=127.1
            
        )
    ])

@app.route("/")
@app.route("/index")
def index():
    return "Hello, World!"


@app.route("/settings", methods=["GET"])
def get_settings():

    settings = settingsManager.get()

    return settings.dict()


@app.route("/settings", methods=["PUT"])
def put_settings():
    settingsManager.set_dict_settings(request.get_json())
    return {"result": 200, "msg": "OK"}

@app.route("/candles", methods=["GET"])
def get_candles():
    options = model.CandlesRequest(**request.args)

    data = _get_candles_from_database(options)
    return  data.dict()

