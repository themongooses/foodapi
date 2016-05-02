import pymysql.cursors
from flask import Flask

from config import *
from utils import CustomJSONEncoder, DateConverter

app = Flask(__name__)

if os.environ.get("MONGOOSE_SERVER_ENV", "").upper() == "PROD":
    app.config.from_object(ProductionConfig)
elif os.environ.get("MONGOOSE_SERVER_ENV", "").upper() == "TESTING":
    app.config.from_object(TestingConfig)
else:
    app.config.from_object(DevelopmentConfig)

db = pymysql.connect(host=app.config['MYSQL_DB_HOST'],
                     user=app.config['MYSQL_USER_NAME'],
                     password=app.config['MYSQL_PASSWORD'],
                     db=app.config['MYSQL_DB_NAME'],
                     charset='utf8mb4',
                     cursorclass=pymysql.cursors.DictCursor)
# Fix for JSON Encoding datetime.date objects
app.json_encoder = CustomJSONEncoder
app.url_map.converters['date'] = DateConverter

from views import *

if __name__ == '__main__':
    app.run(port=9001, debug=True)
