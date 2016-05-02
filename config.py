import os


class Config(object):
    ORACLE_SERVICE_NAME = os.environ.get("ORACLE_SERVICE_NAME", "ORCL")
    ORACLE_USER_NAME = os.environ.get("ORACLE_USER_NAME", "foo")
    ORACLE_PASSWORD = os.environ.get("ORACLE_PASSWORD", "bar")
    ORACLE_DB_HOST = os.environ.get("ORACLE_DB_HOST", "localhost")
    MYSQL_USER_NAME = os.environ.get("MYSQL_USER_NAME", 'foo')
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", 'bar')
    MYSQL_DB_HOST = os.environ.get("MYSQL_DB_HOST", 'localhost')
    MYSQL_DB_PORT = os.environ.get("MYSQL_DB_PORT", 3306)
    MYSQL_DB_NAME = os.environ.get("MYSQL_DB_NAME", 'mongoose')
    SECRET_KEY = os.environ.get('APP_SECRET', 'S00p3rs3cr3t')


class TestingConfig(Config):
    pass


class DevelopmentConfig(Config):
    pass


class ProductionConfig(Config):
    pass
