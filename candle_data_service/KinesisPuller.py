from candle_data_service.kinesis.consumer import KinesisConsumer
from candle_data_service import config
import logging
import time
import threading
import boto3
from candle_data_service.RabbitWrapper import get_candle_q


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class KinesisPuller(metaclass=Singleton):

    def __init__(self):
        self._logger = logging.getLogger().getChild(__name__)

        if not config.KINESIS_ENABLED:
            return

        self.kinesis = KinesisConsumer(stream_name=config.KINESIS_STREAM_NAME, endpoint_url=config.KINESIS_ENDPOINT)
        self.kinesis_thread = threading.Thread(target=self.consume, daemon=True)
        self.kinesis_thread.start()
        self._logger.info(f"kinesis initialized")
        # self.candle_q = get_candle_q()


    def consume(self):
        self._logger.info("start consuming")
        for mess in self.kinesis:
            self._logger.debug(f"record {mess}")



if __name__ == '__main__':
    kinesis = KinesisPuller()
    kinesis.kinesis_thread.join()
