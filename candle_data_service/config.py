"""Flask configuration."""
from os import environ, path
from dotenv import load_dotenv
from logging.config import dictConfig
import logging
import yaml

try:
    with open("configs/logging_config.yml") as log_config_file:
        log_config = yaml.safe_load(log_config_file)
        dictConfig(log_config)
        logging.getLogger().info("from file logging configuration")
except FileNotFoundError as e:
    dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s]:%(name)s:%(module)s:%(levelname)s: %(message)s",
                }
            },
            "handlers": {
                "wsgi": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "default",
                }
            },
            'root': {
                'level': 'INFO',
                'handlers': ['wsgi']
            },        
            "loggers": {

                "werkzeug": {"level": "INFO"},
                "route_logger": {"level": "DEBUG"},
                "candle_data_service.candleDAO" : {"level": "INFO" },
                "candle_data_service.CandlePeriodicDownloader" : {"level": "DEBUG" },
                "candle_data_service.RabbitWrapper" : {"level": "INFO" }
            },
        }
    )
    logging.getLogger().info("default logging configuration")


FLASK_ENV = environ.get('FLASK_ENV', 'development')

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.main.env'))

if FLASK_ENV == 'development':
    logging.getLogger().info("MODE DEVELOPMENT")
    load_dotenv(path.join(basedir, '.dev.env'))


TESTING=bool(environ.get('TESTING', "False"))
DATA_SOURCE_PROVIDER=environ.get('DATA_SOURCE_PROVIDER')
SETTINGS_DATA_PROVIDER=environ.get('SETTINGS_DATA_PROVIDER')
S3_BUCKET_NAME=environ.get('S3_BUCKET_NAME')
S3_OBJECT_NAME=environ.get('S3_OBJECT_NAME')
S3_ENDPOINT_URL=environ.get('S3_ENDPOINT_URL')

DYNAMODB_ENDPOINT_URL=environ.get('DYNAMODB_ENDPOINT_URL')
DYNAMODB_REGION=environ.get('DYNAMODB_REGION')

MARIADB_HOST=environ.get('MARIADB_HOST')
MARIADB_PORT=environ.get('MARIADB_PORT')
MARIADB_USER=environ.get('MARIADB_USER')
MARIADB_PASSWORD=environ.get('MARIADB_PASSWORD')
MARIADB_DB_NAME=environ.get('MARIADB_DB_NAME')
RABBIT_HOSTNAME=environ.get("RABBIT_HOSTNAME")
RABBIT_CANDLES_EXCHANGE_NAME=environ.get("RABBIT_CANDLES_EXCHANGE_NAME")

#TESTING = True
#DEBUG = True
#SECRET_KEY = environ.get('SECRET_KEY')