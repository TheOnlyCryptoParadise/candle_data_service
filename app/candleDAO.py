from app import model
from typing import List
from abc import ABC, abstractclassmethod, abstractmethod
from app.DynamoDb import DynamoDb
import boto3
from boto3.dynamodb.conditions import Key, Attr


class CandleDAO(ABC):

    @abstractmethod
    def get_candles(self, request: model.CandlesRequest) -> List[model.Candle]:
        pass


# TODO more efficient serialization

class DynamoDbCandleDAO(CandleDAO):

    def __init__(self, db: DynamoDb):
        self.db = db.dynamodb
        pass

    def get_candles(self, request: model.CandlesRequest) -> List[model.Candle]:
        table = self.db.Table(f"{request.currency_pair}") # TODO add exchange name to table in candle_getter also
        response = None
        if request.time_start and request.time_end:
            response = table.query(
                KeyConditionExpression=
                    Key('ticker').eq(request.ticker) & Key('timestamp').between(request.time_start, request.time_end)
            )
        elif request.last_n_candles:
            response = table.query(KeyConditionExpression=Key('ticker').eq(request.ticker), ScanIndexForward=False, Limit=request.last_n_candles)
        else:
            raise ValueError("wrong request")

        print(response['Items'])
        response = [model.Candle(open=c['open'], high=c['high'], low=c['low'], close=c['close'], volume=c['volume'], timestamp=c['timestamp']) for c in response["Items"]]
        return response