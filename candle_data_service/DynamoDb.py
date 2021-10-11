import boto3
from botocore.exceptions import ClientError
from flask import current_app

class DynamoDb:

    def __init__(self):
        
        self.dynamodb = boto3.resource('dynamodb', region_name=current_app.config["DYNAMODB_REGION"], endpoint_url=current_app.config["DYNAMODB_ENDPOINT_URL"])
