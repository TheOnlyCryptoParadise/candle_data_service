import logging
import pika
from flask import current_app, g
import logging

from pika.spec import Exchange
from candle_data_service.candle_pb2 import Candle


class RabbitWrapper:
    def __init__(self):
        # rabbit_hostname = "localhost"  # TODO current_app.config["RABBIT_HOSTNAME"]
        rabbit_hostname = current_app.config["RABBIT_HOSTNAME"]
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(rabbit_hostname)
        )
        self.channel = self.connection.channel()
        self.logger = logging.getLogger(__name__)
        self.exchange_name = current_app.config["RABBIT_CANDLES_EXCHANGE_NAME"]
        self.exchange = self.channel.exchange_declare(self.exchange_name, "direct")

    def publish_candles(self, candle_data):
        for candle_record in candle_data:
            pair = candle_record[0]
            candle_size = candle_record[1]
            candles = candle_record[2]
            self.logger.info(f"put {len(candles)} candles for {pair}{candle_size} to exchange")
            routing_key = pair.replace("/", "_") + "_" + candle_size
            for c in candles:
                candle = Candle(
                    exchange="binance",
                    pair=pair,
                    size=candle_size,
                    timestamp=c[0],
                    open=c[1],
                    high=c[2],
                    low=c[3],
                    close=c[4],
                    volume=c[5]
                )
                self.logger.debug(f"publish candle {pair}{candle_size} - {candle}")
                self.channel.basic_publish(
                    exchange=self.exchange_name,
                    routing_key=routing_key,
                    body=candle.SerializeToString(),
                )

def get_candle_q():

    if "candle_q" not in g:
        g.candle_q = RabbitWrapper()
    return g.candle_q

def get_rabbit_no_g():
    return RabbitWrapper()

if __name__ == "__main__":
    rbw = RabbitWrapper()
    logging.basicConfig(level=logging.INFO)
    rbw.publish_candles([("ETH/USDT", "15m", [[234, 234234, 234, 444, 555,222]])])
    rbw.publish_candles([("BTC/USDT", "15m", [[234, 234234, 234, 444, 555,222]])])
    rbw.publish_candles([("XLM/USDT", "5m", [[234, 234234, 234, 444, 555,222]])])
