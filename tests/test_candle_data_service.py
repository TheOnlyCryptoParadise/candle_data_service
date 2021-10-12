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

    assert "200" in rv.status
    assert len(rv.get_json()['data']) == 0

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
        "exchanges":{
            "binance": {
                "pairs": [
                    "BTC/USDT",
                    "ETH/USDT"
                ],
                "candle_sizes": ["15m"]
            }},
        "last_n_candles" : 10
        }

    rv = client.post("/currencyPairLiveInfo", json=request_body)

    assert "200" in rv.status
    assert type(rv.get_json()['BTC/USDT']['last']) is float
    assert type(rv.get_json()['ETH/USDT']['last']) is float

