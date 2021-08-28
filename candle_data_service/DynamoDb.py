import boto3
from botocore.exceptions import ClientError

class DynamoDb:

    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name="localhost", endpoint_url="http://localhost:4566")
