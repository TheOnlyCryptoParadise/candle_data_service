import os
import tempfile

import pytest

from candle_data_service import create_app
# from flaskr.db import init_db


@pytest.fixture
def client():
    # db_fd, db_path = tempfile.mkstemp()
    app = create_app({'TESTING': True})

    with app.test_client() as client:
        # with app.app_context():
            # init_db()
        yield client

    # os.close(db_fd)
    # os.unlink(db_path)


# def test_empty_db(client):
#     """Start with a blank database."""

#     rv = client.get('/settings')
#     assert len(rv.get_data()) > 0


# def test_put_settings(client):
#     rv = client.put("/settings", json={"exchanges": [{"name": "Binance", "ticker_settings": {"1m": ["ETH/USDT"]} }]})
#     assert rv.get_json()['msg'] == "OK"
    
# def test_put_get_settings(client):
#     settings_dict = {"exchanges": [{"name": "Binance", "ticker_settings": {"5m": ["BNB/USDT"]} }]}
#     rv = client.put("/settings", json=settings_dict)
#     assert rv.get_json()['msg'] == "OK"

#     rvg = client.get("/settings")
#     assert rvg.get_json() == settings_dict

# def test_wrong_put_settings(client):
#     settings_dict = {"exchanges": [{"name": "Binance", "tickersss_settings": {"5m": ["BNB/USDT"]} }]}
#     rv = client.put("/settings", json=settings_dict)
#     assert "400" in rv.status

# def test_wrong_put_settings2(client):
#     settings_dict = {"exchanges": [{"name": "Binance"}]}
#     rv = client.put("/settings", json=settings_dict)
#     assert "400" in rv.status

def test_get_no_table_candles(client):
    # TODO reset databases
    args = {
        "exchange": "binance",
        "currency_pair": "ETsssH_USDT",
        "candle_size": "15m",
        "last_n_candles": 10
        }
    rv = client.get("/candles", query_string=args)

    assert "400" in rv.status
    # assert len(rv.get_json()['data']) == 0

def test_get_wrong_request_candles(client):
    # TODO reset databases
    args = {
        "exchange": "binance",
        "cursrency_pair": "ETsssH/USDT",
        "last_n_candles": 10
        }
    rv = client.get("/candles", query_string=args)

    assert "400" in rv.status


def test_get_current_prices(client):
    # TODO reset databases
    request_body = {
        "exchanges":[
            {
                "name": "binance",
                "pairs": [
                    "BTC/USDT",
                    "ETH/USDT"
                ],
                "candle_sizes": ["15m"]
            }],
        "last_n_candles" : 10
        }

    rv = client.post("/currencyPairLiveInfo", json=request_body)

    assert "200" in rv.status
    assert type(rv.get_json()['data'][0]['data']["BTC/USDT"]['last']) is float
    assert type(rv.get_json()['data'][0]['data']['ETH/USDT']['last']) is float

def test_download_candles(client):
    request_body = {
        "exchanges": [{
            "name": "binance",
            "pairs": [ "BTC/USDT", "ETH/USDT"],
            "candle_sizes": ["1m", "5m", "1h"]
        }],
        "last_n_candles": 5
    }
    rv = client.post("/downloadCandles", json=request_body)
    assert "200" in rv.status

def test_duplicate_keys(client):
    request_body = {
        "exchanges": [{
            "name": "binance",
            "pairs": [ "DOT/USDT"],
            "candle_sizes": ["4h"]
        }],
        "last_n_candles": 5
    }
    rv1 = client.post("/downloadCandles", json=request_body)

    request_body = {
        "exchanges": [{
            "name": "binance",
            "pairs": [ "DOT/USDT"],
            "candle_sizes": ["4h"]
        }],
        "last_n_candles": 6
    }
    rv2 = client.post("/downloadCandles", json=request_body)
    args = {
        "exchange": "binance",
        "currency_pair": "DOT/USDT",
        "candle_size": "4h",
        "last_n_candles": 10
    }
    rv3 = client.get("/candles", query_string=args)
    assert "200" in rv1.status
    assert "200" in rv2.status
    assert "200" in rv3.status
    assert len(rv3.get_json()['data']) == 6

def test_download_and_get_candles(client):
    request_body = {
        "exchanges": [{
            "name": "binance",
            "pairs": [ "LINK/USDT"],
            "candle_sizes": ["1m"]
        }],
        "last_n_candles": 10
    }
    rv1 = client.post("/downloadCandles", json=request_body)

    args = {
        "exchange": "binance",
        "currency_pair": "LINK/USDT",
        "candle_size": "1m",
        "last_n_candles": 5
    }
    rv2 = client.get("/candles", query_string=args)
    assert "200" in rv1.status
    assert "200" in rv2.status
    assert len(rv2.get_json()['data']) == 5
    assert type(rv2.get_json()['data'][0]['open']) is float
    assert type(rv2.get_json()['data'][0]['high']) is float
    assert type(rv2.get_json()['data'][0]['low']) is float
    assert type(rv2.get_json()['data'][0]['close']) is float
    assert type(rv2.get_json()['data'][0]['volume']) is float

def test_get_available_data(client):
    request_body = {
        "exchanges": [{
            "name": "binance",
            "pairs": [ "XRP/USDT"],
            "candle_sizes": ["1h"]
        }],
        "last_n_candles": 10
    }
    rv1 = client.post("/downloadCandles", json=request_body)

    rv2 = client.get("/availableCandles")

    assert "200" in rv1.status
    assert "200" in rv2.status
    assert rv2.get_json()['data']['binance']['XRP/USDT']["1h"][0]['no_candles'] == 10
    assert type(rv2.get_json()['data']['binance']['XRP/USDT']["1h"][0]['time_start']) is int
    assert type(rv2.get_json()['data']['binance']['XRP/USDT']["1h"][0]['time_end']) is int

def test_get_candles_time_start_end(client):
    request_body = {
        "exchanges": [{
            "name": "binance",
            "pairs": [ "ATOM/USDT"],
            "candle_sizes": ["1h"]
        }],
        "time_start": 1634822085,
        "time_end": 1634908485
    }
    rv1 = client.post("/downloadCandles", json=request_body)
    rv2 = client.get("/availableCandles")

    request_body['time_end'] = 1634912085
    rv3 = client.post("/downloadCandles", json=request_body)

    rv4 = client.get("/availableCandles")
    assert "200" in rv1.status
    assert "200" in rv2.status
    assert "200" in rv3.status
    assert "200" in rv4.status
    assert rv2.get_json()['data']['binance']['ATOM/USDT']["1h"][0]['no_candles'] == 24
    assert rv4.get_json()['data']['binance']['ATOM/USDT']["1h"][0]['no_candles'] == 25
    assert type(rv2.get_json()['data']['binance']['XRP/USDT']["1h"][0]['time_start']) is int
    assert type(rv2.get_json()['data']['binance']['XRP/USDT']["1h"][0]['time_end']) is int

def test_available_markets(client):
    args = {
        "exchange": "binance",
    }
    rv = client.get("/availableMarkets", query_string=args)
    assert "200" in rv.status
    assert type(rv.get_json()['data'][0]) is str
    assert type(rv.get_json()['data'][1]) is str
    assert type(rv.get_json()['data'][2]) is str