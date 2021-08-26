from flask import Flask
import os

def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_pyfile('config.py')
    if test_config is not None:
        app.config.update(test_config)


    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass


    # from app.settings import
    from app.routes import main_routes
    app.register_blueprint(main_routes)
    return app