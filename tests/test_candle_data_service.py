import os
import tempfile

import pytest

from app import create_app
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


def test_empty_db(client):
    """Start with a blank database."""

    rv = client.get('/settings')
    assert len(rv.get_data()) > 0


def test_put_settings(client):
    rv = client.put("/settings", json={"exchanges": [{"name": "Binance", "ticker_settings": {"1m": ["ETH/USDT"]} }]})
    assert rv.get_json()['msg'] == "OK"
    
def test_put_get_settings(client):
    settings_dict = {"exchanges": [{"name": "Binance", "ticker_settings": {"5m": ["BNB/USDT"]} }]}
    rv = client.put("/settings", json=settings_dict)
    assert rv.get_json()['msg'] == "OK"

    rvg = client.get("/settings")
    assert rvg.get_json() == settings_dict
