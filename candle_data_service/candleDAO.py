from candle_data_service import model
from typing import List
from abc import ABC, abstractclassmethod, abstractmethod
from candle_data_service.DynamoDb import DynamoDb
import boto3
from boto3.dynamodb.conditions import Key, Attr
from flask import current_app, g
from decimal import Decimal
import json
import logging
import time


class CandleDAO(ABC):
    @abstractmethod
    def get_candles(self, request: model.GetCandlesRequest) -> List[model.Candle]:
        pass


# TODO more efficient serialization


class DynamoDbCandleDAO(CandleDAO):
    def __init__(self, db: DynamoDb):
        self.db = db.dynamodb
        self.logger = logging.getLogger(__name__)

        # self.logger.setLevel(logging.DEBUG)
        # strh = logging.StreamHandler()
        # strh.setLevel(logging.DEBUG)
        # self.logger.addHandler(strh)
        pass

    def get_candles(self, request: model.GetCandlesRequest) -> List[model.Candle]:
        #TODO add exchange in name of table
        # table_name = request.exchange + "_" + request.currency_pair.replace("/","_") + "_" + request.candle_size
        table_name = request.currency_pair.replace("/","_") + "_" + request.candle_size
        self.logger.debug("getting from %s", table_name)
        table = self.db.Table(
            table_name
        )  # TODO add exchange name to table in candle_getter also
        response = None
        if request.time_start and request.time_end:
            response = table.query(
                KeyConditionExpression=Key("timestamp").between(request.time_start, request.time_end)
            )
        elif request.last_n_candles:
            # TODO pagination
            response = table.scan(
                Limit=request.last_n_candles, #TODO ScanIndexForward???
            )
        else:
            raise ValueError("wrong request")

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

    def put_candles(self, candle_data):
        self.logger.info("sending candle_data %d to dynamodb", len(candle_data))
        for candle_record in candle_data:
            self.logger.debug(f"put item {candle_record}")
            table_name = candle_record[0].replace("/","_") + "_" + candle_record[1]
            table = self.db.Table(table_name)
            try:
                table.load()
            except:
                self._create_table(table_name)
                table = self.db.Table(table_name)
            for candle in candle_record[2]:
                table.put_item(
                    Item={
                        'timestamp' : Decimal(str(candle[0])),
                        'open' : Decimal(str(candle[1])),
                        'high' : Decimal(str(candle[2])),
                        'low' : Decimal(str(candle[3])),
                        'close' : Decimal(str(candle[4])),
                        'volume' : Decimal(str(candle[5]))
                    }
                )
    def _create_table(self, name):
        self.logger.debug("create table %s", name)
        table = self.db.create_table(
            TableName=name,
            KeySchema=[
                {
                    'AttributeName': 'timestamp',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'timestamp',
                    'AttributeType': 'N'
                }                                             
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
        time.sleep(8)
        return table

    def clean_tables(self):
        self.logger.info("cleaning all tables")
        tables = [i.name for i in list(self.dynamodb.tables.all())]
        for table_name in tables:
            self.logger.info("delete %s", table_name)
            table = self.dynamodb.Table(table_name)
            table.delete()


def get_candleDAO():

    if "candleDAO" not in g:

        candleDAO = None
        if current_app.config["DATA_SOURCE_PROVIDER"] == "DynamoDB":
            db = DynamoDb()  # TODO no need to create on every request
            candleDAO = DynamoDbCandleDAO(db)
        assert candleDAO != None, "no candleDAO configured"
        g.candleDAO = candleDAO
    return g.candleDAO
