import pymysql.cursors
from flask import Flask

from config import *
from utils import CustomJSONEncoder, DateConverter

# Initialize the app object
app = Flask(__name__)

# To load different environment configurations based on
# objects defined in config.py, set MONGOOSE_SERVER_ENV
# as an environment variable that Python can read
# at initial app load
if os.environ.get("MONGOOSE_SERVER_ENV", "").upper() == "PROD":
    app.config.from_object(ProductionConfig)
elif os.environ.get("MONGOOSE_SERVER_ENV", "").upper() == "TESTING":
    app.config.from_object(TestingConfig)
else:
    app.config.from_object(DevelopmentConfig)

# Fix for JSON Encoding datetime.date objects
app.json_encoder = CustomJSONEncoder
# Add a date url parameter type
app.url_map.converters['date'] = DateConverter


# Connect to the database
@app.before_request
def check_db_connection():
    g.db = pymysql.connect(host=app.config['MYSQL_DB_HOST'],
                           user=app.config['MYSQL_USER_NAME'],
                           password=app.config['MYSQL_PASSWORD'],
                           db=app.config['MYSQL_DB_NAME'],
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


# Views (routes) imported here and not at the top
# to resolve the circular dependency where the
# route decorator depends on the app object
from views import *

# Run this file from the console to enable debugging.
# This is completely unsafe for a production environment
# and should only be done in a testing or development environment
# or as a last resort for fixing an issue in production
if __name__ == '__main__':
    app.run(port=9001, debug=True)
