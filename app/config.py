"""Flask configuration."""
from os import environ, path
from dotenv import load_dotenv

FLASK_ENV = environ.get('FLASK_ENV', 'development')

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '../.env'))

if FLASK_ENV == 'development':
    load_dotenv(path.join(basedir, '../.dev.env'))


TEST_DEBUG=environ.get('TEST_DEBUG')
DATA_SOURCE_PROVIDER=environ.get('DATA_SOURCE_PROVIDER')
SETTINGS_DATA_PROVIDER=environ.get('SETTINGS_DATA_PROVIDER')
S3_BUCKET_NAME=environ.get('S3_BUCKET_NAME')
S3_OBJECT_NAME=environ.get('S3_OBJECT_NAME')
S3_ENDPOINT_URL=environ.get('S3_ENDPOINT_URL')


#TESTING = True
#DEBUG = True
#SECRET_KEY = environ.get('SECRET_KEY')