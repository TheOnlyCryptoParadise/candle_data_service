from botocore import endpoint
from app import model
from typing import List
from abc import ABC, abstractmethod
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import json 
from flask import g
from flask import current_app

class SettingsDAO(ABC):

    @abstractmethod
    def get_settings(self) -> List[model.Candle]:
        pass

    def set_settings(self, settings_data: model.Settings):
        pass

# TODO more efficient serialization

class S3SettingsDAO(SettingsDAO):

    def __init__(self, bucket_name, object_name):
        if "S3_ENDPOINT_URL" in current_app.config:
            self.s3_client = boto3.client('s3', endpoint_url=current_app.config["S3_ENDPOINT_URL"])
        else:
            self.s3_client = boto3.client('s3')
        self.bucket_name = bucket_name
        self.object_name = object_name

    def get_settings(self) -> List[model.Candle]:
        self.s3_client.download_file(self.bucket_name, self.object_name, 'tmp-settings.json')
        with open("tmp-settings.json") as settings_file:
            return model.Settings(**json.load(settings_file))        

    def set_settings(self, settings_data: model.Settings):
        # Upload the file
        with open("tmp-settings.json", "w") as settings_file:
            json.dump(settings_data.dict(), settings_file)
        response = self.s3_client.upload_file("tmp-settings.json", self.bucket_name, self.object_name)
        

class SettingsManager:

    def __init__(self, settingsDAO: SettingsDAO):
        self.settingsDAO = settingsDAO
        self.cached_settings = settingsDAO.get_settings()
    def get(self):
        return self.cached_settings

    def set_dict_settings(self, sett_dict: dict):
        self.cached_settings = model.Settings(**sett_dict)
        self.settingsDAO.set_settings(self.cached_settings)




def get_settingsManager():
    if "settingsManager" not in g:
        settingsDAO = None
        if current_app.config['SETTINGS_DATA_PROVIDER'] == "S3":
            settingsDAO = S3SettingsDAO(current_app.config['S3_BUCKET_NAME'], current_app.config["S3_OBJECT_NAME"])
        
        g.settingsManager = SettingsManager(settingsDAO)

    return g.settingsManager