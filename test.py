import pymysql
from config import Config
from entities import *

db = pymysql.connect(host=Config.MYSQL_DB_HOST,
                     user=Config.MYSQL_USER_NAME,
                     password=Config.MYSQL_PASSWORD,
                     db='mongoose',
                     charset='utf8mb4',
                     cursorclass=pymysql.cursors.DictCursor)