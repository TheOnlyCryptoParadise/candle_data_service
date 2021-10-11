![CryptoParadise](https://circleci.com/gh/TheOnlyCryptoParadise/candle_data_service.svg?style=svg)
## Run this project to add to the database single candle for each selected currency pair and ticker

## How to run:
1. clone infra repo and run `docker-compose up` insie localstack directory.
2. wait until all localstack services are ready
3. run `docker-compose up` inside this directory to start **candle_data_service**. Server will start on `localhost:5000`
<!-- 1. Run docker-compose.yaml file to create localstack
`docker-compose up`
2. Set environmental variables
    - `export AWS_SECRET_ACCESS_KEY=test`
    - `export AWS_ACCESS_KEY_ID=test`
   - `export FLASK_APP=candle_data_service`
   - `export FLASK_ENV=development`
3. Create virtual environment
`python -m venv env`
4. Go to virtual environment
`source env/bin/activate`
5. Install all necessary packages using requirements.txt
`python -m pip install -r requirements.txt`
6. Run flask application
   `flask run`
7. Open http://127.0.0.1:5000/ -->

## Endpoint /candles and request's parameters:

API is documented usin openapi in `openapi.yaml`. 

You can view available endpoints using Swagger UI:

Go to https://petstore.swagger.io/#/ and paste url to raw file in explore bar: https://raw.githubusercontent.com/TheOnlyCryptoParadise/candle_data_service/dev/openapi.yaml
