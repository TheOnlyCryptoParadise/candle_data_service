from candle_data_service import model
from typing import List
from abc import ABC, abstractclassmethod, abstractmethod
from candle_data_service.DynamoDb import DynamoDb
import boto3
from boto3.dynamodb.conditions import Key, Attr
from flask import current_app, g


class CandleDAO(ABC):
    @abstractmethod
    def get_candles(self, request: model.GetCandlesRequest) -> List[model.Candle]:
        pass


# TODO more efficient serialization


class DynamoDbCandleDAO(CandleDAO):
    def __init__(self, db: DynamoDb):
        self.db = db.dynamodb
        pass

    def get_candles(self, request: model.GetCandlesRequest) -> List[model.Candle]:
        table = self.db.Table(
            f"{request.currency_pair}"
        )  # TODO add exchange name to table in candle_getter also
        response = None
        if request.time_start and request.time_end:
            response = table.query(
                KeyConditionExpression=Key("ticker").eq(request.ticker)
                & Key("timestamp").between(request.time_start, request.time_end)
            )
        elif request.last_n_candles:
            response = table.query(
                KeyConditionExpression=Key("ticker").eq(request.ticker),
                ScanIndexForward=True,
                Limit=request.last_n_candles,
            )
        else:
            raise ValueError("wrong request")

        print(response["Items"])
        response = [
            model.Candle(
                open=c["open"],
                high=c["high"],
                low=c["low"],
                close=c["close"],
                volume=c["volume"],
                time=c["timestamp"],
            )
            for c in response["Items"]
        ]
        return response


def get_candleDAO():

    if "candleDAO" not in g:

        candleDAO = None
        if current_app.config["DATA_SOURCE_PROVIDER"] == "DynamoDB":
            db = DynamoDb()  # TODO no need to create on every request
            candleDAO = DynamoDbCandleDAO(db)
        assert candleDAO != None, "no candleDAO configured"
        g.candleDAO = candleDAO
    return g.candleDAO
