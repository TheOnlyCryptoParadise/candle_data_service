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
import mariadb


class CandleDAO(ABC):
    @abstractmethod
    def get_candles(self, request: model.CandlesRequest) -> List[model.Candle]:
        pass
    
    @abstractmethod
    def get_available_data(self):
        pass
    
    @abstractmethod
    def put_candles(self, candle_data):
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

    def get_candles(self, request: model.CandlesRequest) -> List[model.Candle]:
        # TODO add exchange in name of table
        # table_name = request.exchange + "_" + request.currency_pair.replace("/","_") + "_" + request.candle_size
        table_name = request.currency_pair.replace("/", "_") + "_" + request.candle_size
        request.currency_pair = request.currency_pair.replace("_", "/")
        self.logger.debug("getting from %s", table_name)
        table = self.db.Table(
            table_name
        )  # TODO add exchange name to table in candle_getter also
        response = None
        if request.time_start and request.time_end:
            response = table.query(
                KeyConditionExpression=Key("timestamp").between(
                    request.time_start, request.time_end
                )
            )
        elif request.last_n_candles:
            # TODO pagination
            response = table.scan(
                Limit=request.last_n_candles,  # TODO ScanIndexForward???
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
            table_name = candle_record[0].replace("/", "_") + "_" + candle_record[1]
            table = self.db.Table(table_name)
            try:
                table.load()
            except:
                self._create_table(table_name)
                table = self.db.Table(table_name)
            for candle in candle_record[2]:
                table.put_item(
                    Item={
                        "timestamp": Decimal(str(candle[0])),
                        "open": Decimal(str(candle[1])),
                        "high": Decimal(str(candle[2])),
                        "low": Decimal(str(candle[3])),
                        "close": Decimal(str(candle[4])),
                        "volume": Decimal(str(candle[5])),
                    }
                )

    def _create_table(self, name):
        self.logger.debug("create table %s", name)
        table = self.db.create_table(
            TableName=name,
            KeySchema=[
                {"AttributeName": "timestamp", "KeyType": "HASH"}  # Partition key
            ],
            AttributeDefinitions=[{"AttributeName": "timestamp", "AttributeType": "N"}],
            ProvisionedThroughput={"ReadCapacityUnits": 10, "WriteCapacityUnits": 10},
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

    def get_table_list(self):

        response = list(map(lambda t: t.name, self.db.tables.all()))
        return response

    def _get_first_and_last_item(self, table_name):
        table = self.db.Table(table_name)

        first = table.scan(
            Limit=1,  # TODO ScanIndexForward???
        )
        last = table.scan(
            Limit=1,
        )

    def get_available_data(self):
        tables = self.get_table_list()
        result = {"exchanges": {"binance": {"currency_pairs": {}}}}
        for table in tables:
            table = table.split("_")
            currency_pair = table[0] + "_" + table[1]
            if currency_pair in result["exchanges"]["binance"]["currency_pairs"]:
                result["exchanges"]["binance"]["currency_pairs"][currency_pair].append(
                    table[2]
                )
            else:
                result["exchanges"]["binance"]["currency_pairs"][currency_pair] = []

        return result


class MariaDBCandleDAO(CandleDAO):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # self.logger.setLevel(logging.DEBUG)
        # sh = logging.StreamHandler()
        # sh.setLevel(logging.DEBUG)
        # self.logger.addHandler(sh)
        self.logger.debug("MariDB instantiated")
        self.conn = mariadb.connect(
            host=current_app.config["MARIADB_HOST"],
            port=int(current_app.config["MARIADB_PORT"]),
            user=current_app.config["MARIADB_USER"],
            password=current_app.config["MARIADB_PASSWORD"],
            database=current_app.config["MARIADB_DB_NAME"],
        )

    def get_candles(self, request: model.CandlesRequest) -> List[model.Candle]:
        # TODO add exchange in name of table
        # table_name = request.exchange + "_" + request.currency_pair.replace("/","_") + "_" + request.candle_size
        cursor = self.conn.cursor()

        query_last_n_candles = """SELECT c.timestamp,
                    cp.ticker,
                    c.candle_size,
                    c.open,
                    c.high,
                    c.low,
                    c.close,
                    c.volume
                FROM candles c
                    INNER join currency_pairs cp
                WHERE cp.ticker = ?
                    and c.candle_size = ? order by timestamp asc limit ?;
                """
        query_timestamps = """SELECT c.timestamp,
                    cp.ticker,
                    c.candle_size,
                    c.open,
                    c.high,
                    c.low,
                    c.close,
                    c.volume
                FROM candles c
                    INNER join currency_pairs cp
                WHERE FROM_UNIXTIME(?) <= c.timestamp
                    and c.timestamp <= FROM_UNIXTIME(?)
                    and cp.ticker = ?
                    and c.candle_size = ?
                order by timestamp asc;
                """

        response = None
        if request.time_start and request.time_end:
            cursor.execute(query_timestamps, (request.time_start, request.time_end, request.currency_pair, request.candle_size))
        elif request.last_n_candles:
            cursor.execute(query_last_n_candles, (request.currency_pair, request.candle_size, request.last_n_candles))
        else:
            raise ValueError("wrong request")
        response = cursor.fetchall()
        response = [
            model.Candle(
                open=r[3],
                high=r[4],
                low=r[5],
                close=r[6],
                volume=r[7],
                time=r[0].timestamp(),
            )
            for r in response
        ]
        cursor.close()
        return response        

    def put_candles(self, candle_data):
        self.logger.info("sending candle_data all length %d to mariadb", len(candle_data))

        cursor = self.conn.cursor()
        for candle_record in candle_data:
            # tables = cursor.execute("SHOW TABLES")
            cursor.execute(
                "SELECT id FROM currency_pairs WHERE ticker=?", (candle_record[0],)
            )
            currency_pair_id = cursor.next()
            if currency_pair_id == None:
                currency_pair_id = self._create_currency_pair(candle_record[0], cursor)
            else:
                currency_pair_id = currency_pair_id[0]

            cursor.execute(
                "SELECT id FROM exchanges WHERE name=?", ("binance",)
            )  # TODO hardcoded binance
            exchange_id = cursor.next()
            if exchange_id == None:
                raise ValueError("exchange not in database")
            else:
                exchange_id = exchange_id[0]

            data_for_query = []
            for candle in candle_record[2]:
                data_for_query.append(
                    (
                        exchange_id,  # exchange
                        currency_pair_id,  # currency_pair
                        candle_record[1],  # candle_size
                        candle[0] / 1000,  # timestamp
                        candle[1],  # open
                        candle[2],  # high
                        candle[3],  # low
                        candle[4],  # close
                        candle[5],  # volume
                    )
                )

            query = "INSERT INTO candles (exchange, currency_pair, candle_size, timestamp,open,high,low,close,volume) VALUES(?, ?, ?, FROM_UNIXTIME(?), ?, ?, ?, ?, ?)"
            self.logger.info(f"put {len(data_for_query)} records")

            #cursor.executemany(query, data_for_query) #TODO handle duplicate entries
            for data in data_for_query:
                try:
                    cursor.execute(query, data)
                except mariadb.IntegrityError:
                    self.logger.info(f"duplicate key for {data}")

        cursor.close()
        self.conn.commit()

    def _create_currency_pair(self, name, cursor):
        self.logger.info("create currency_pair %s", name)
        cursor.execute("INSERT INTO currency_pairs (ticker) VALUES (?)", (name,))
        return cursor.lastrowid


    def get_available_data(self):
        cursor = self.conn.cursor()


        query = """SELECT 
                    e.name,
                    cp.ticker,
                    c.candle_size,
                    COUNT(c.timestamp),
                    MAX(UNIX_TIMESTAMP(c.timestamp)),
                    MIN(UNIX_TIMESTAMP(c.timestamp))
                    FROM candles c
                    inner  join currency_pairs cp on c.currency_pair = cp.id
                    inner  join exchanges e on c.exchange = e.id
                    group by c.exchange, cp.ticker, c.candle_size;
                """
        
        result = {}
        cursor.execute(query)
        values = cursor.fetchall()
        for rec in values:
            if rec[0] not in result:
                result[rec[0]] = {}
            if rec[1] not in result[rec[0]]:
                result[rec[0]][rec[1]] = {}
            if rec[2] not in result[rec[0]][rec[1]]:
                result[rec[0]][rec[1]][rec[2]] = []

            result[rec[0]][rec[1]][rec[2]].append({"no_candles": rec[3], "time_end": rec[4], "time_start": rec[5]})

        cursor.close()
        return result


def get_candleDAO():

    if "candleDAO" not in g:
        candleDAO = None
        if current_app.config["DATA_SOURCE_PROVIDER"] == "DynamoDB":
            db = DynamoDb()  # TODO no need to create on every request
            candleDAO = DynamoDbCandleDAO(db)
        elif current_app.config["DATA_SOURCE_PROVIDER"] == "MariaDB":
            candleDAO = MariaDBCandleDAO()
        assert candleDAO != None, "no candleDAO configured"
        g.candleDAO = candleDAO
    return g.candleDAO
