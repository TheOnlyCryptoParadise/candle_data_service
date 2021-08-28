import boto3
import botocore.exceptions
import time
done = False
fail_counter = 0
while not done:
    try:
        s3 = boto3.client('s3',region_name="localhost", endpoint_url="http://localhost:4566")
        s3.create_bucket(Bucket="crp-agh-settings")
        s3.upload_file("DEVsettings.json", "crp-agh-settings", "candle_data_service")
        print("created")
        done = True
    except botocore.exceptions.EndpointConnectionError as e:
        print("FAIL... retry in 5s")
        fail_counter +=1
        if fail_counter > 5:
            print("attempt limit exceeded... aborting")
            done = True
        time.sleep(5)