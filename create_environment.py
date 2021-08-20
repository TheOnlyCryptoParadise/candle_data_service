import boto3
s3 = boto3.client('s3',region_name="localhost", endpoint_url="http://localhost:4566")
s3.create_bucket(Bucket="crp-agh-settings")
s3.upload_file("DEVsettings.json", "crp-agh-settings", "candle_data_service")