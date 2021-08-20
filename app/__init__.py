from flask import Flask

app = Flask(__name__)
app.config.from_pyfile('config.py')

from app.settings import SettingsManager, S3SettingsDAO
settingsDAO = None
if app.config['SETTINGS_DATA_PROVIDER'] == "S3":
    settingsDAO = S3SettingsDAO(app.config['S3_BUCKET_NAME'], app.config["S3_OBJECT_NAME"])
settingsManager = SettingsManager(settingsDAO)

from app import routes
from app.DynamoDb import DynamoDb
from app.candleDAO import DynamoDbCandleDAO

candleDAO = None
if app.config['DATA_SOURCE_PROVIDER'] == "DynamoDB":
    db = DynamoDb() # TODO no need to create on every request
    candleDAO = DynamoDbCandleDAO(db)


