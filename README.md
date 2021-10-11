<!-- (CryptoParadise)[https://circleci.com/gh/TheOnlyCryptoParadise/candle_data_service.svg?style=svg] -->
## Run this project to add to the database single candle for each selected currency pair and ticker

## How to run:
1. Run docker-compose.yaml file to create localstack
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
7. Open http://127.0.0.1:5000/

## Endpoint /candles and request's parameters:
 - exchange: Binance/ Bitbay
 - currency_pair: e.g BTC_USDT
 - ticker: 1m / 1h
 - optional paramters:
   - last_n_candles: number > 0 
   - time_start, time_end : unix timestamp e.g 1633521240000

