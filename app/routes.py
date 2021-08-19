from app import app
import json
from app import model
from flask import request
from app.DynamoDb import DynamoDb
from app.candleDAO import DynamoDbCandleDAO

def _get_settings_gen():

    with open("DEVsettings.json") as settings_file:
        return model.Settings(**json.load(settings_file))


def get_candles_from_database(req: model.GetCandlesRequest):

    db = DynamoDb() # TODO no need to create on every request
    candleDAO = DynamoDbCandleDAO(db)


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


@app.route("/")
@app.route("/index")
def index():
    return "Hello, World!"


@app.route("/settings", methods=["GET"])
def get_settings():

    settings = _get_settings_gen()

    return settings.dict()


@app.route("/settings", methods=["PUT"])
def put_settings():
    raise NotImplementedError()
    return "OK"


@app.route("/candles", methods=["GET"])
def get_candles():
    options = model.GetCandlesRequest(**request.args)

    data = get_candles_from_database(options)
    return  data.dict()

