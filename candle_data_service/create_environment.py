from os import pardir
import boto3
import botocore.exceptions
import time
import mariadb
from os import environ, path
from dotenv import load_dotenv

from candle_data_service import config

import argparse
# done = False
# fail_counter = 0
# while not done:
#     try:
#         s3 = boto3.client('s3',region_name="localhost", endpoint_url="http://localhost:4566")
#         s3.create_bucket(Bucket="crp-agh-settings")
#         # s3.upload_file("DEVsettings.json", "crp-agh-settings", "candle_data_service")
#         print("created")
#         done = True
#     except botocore.exceptions.EndpointConnectionError as e:
#         print("FAIL... retry in 5s")
#         fail_counter +=1
#         if fail_counter > 5:
#             print("attempt limit exceeded... aborting")
#             done = True
#         time.sleep(5)

# client = boto3.client('rds')
# client.create_db_instance(DBName="candle_data_service", DBInstanceIdentifier='candle_data_service', )
basedir = path.abspath(path.dirname(__file__))

def create_tables(conn):
    with open(path.join(basedir, "database_create.sql"), encoding='utf-8') as file:


        cursor = conn.cursor()
        cursor.execute("show tables")
        tables = cursor.fetchall()
        if len(tables) > 0:
            print("already created")
            return


        queries = file.read().split(";")[:-1]
        for q in queries:
            cursor.execute(q)
        cursor.close()
        print("tables created")
def delete_tables(conn):
    cursor = conn.cursor()
    cursor.execute("show tables")
    tables = cursor.fetchall()
    for table in tables:
        print(table[0])
        cursor.execute(f"drop table {table[0]}")
    cursor.close()


if __name__ == "__main__":

    attempt_cnt = 0
    connected = False
    while attempt_cnt < int(config.DB_CONNECTION_ATTEMPTS) and connected == False:
        try:
            print("connecting to database...")
            conn = mariadb.connect(
                host=config.MARIADB_HOST,
                port=int(config.MARIADB_PORT),
                user=config.MARIADB_USER,
                password=config.MARIADB_PASSWORD,
                database=config.MARIADB_DB_NAME)
            connected = True
        except mariadb.Error:
            print(f"connection attempt {attempt_cnt} failed...retrying in 10s")
            attempt_cnt +=1
            time.sleep(10)
    print("connected to database")


# cursor.execute("SELECT id FROM currency_pairs WHERE ticker='BTC_USDT'") # TODO hardcoded binance
# exchange_id = None
# if cursor.rowcount == 0:
#     raise ValueError("exchange not in database")
# else:
#     exchange_id = cursor.fetchone()[0]
# print(exchange_id)

# create_tables()


    parser = argparse.ArgumentParser()
    parser.add_argument("--clean-database", dest='clean', action="store_true")
    args = parser.parse_args()

    if args.clean:
        delete_tables(conn)
    else:
        create_tables(conn)

    conn.close()