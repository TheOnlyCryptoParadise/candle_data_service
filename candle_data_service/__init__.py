from flask import Flask
from flask_cors import CORS
import os


from .CandlePeriodicDownloader import CandlePeriodicDownloader, DownloadSettings

from .KinesisPuller import KinesisPuller

def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=False)
    CORS(app) # TODO 
    app.config.from_pyfile("config.py")
    if test_config is not None:
        app.config.update(test_config)

    with app.app_context():
        CandlePeriodicDownloader()
        KinesisPuller()

    

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # TODO Settings and temp file problem
    from candle_data_service.settings import S3SettingsDAO, SettingsManager

    # from app.settings import
    from candle_data_service.routes import main_routes

    app.register_blueprint(main_routes)
    return app
